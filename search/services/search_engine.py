import os
import logging
from openai import OpenAI
from django.conf import settings
from documents.models import DocumentChunk
from django.db import connection
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F
from django.db import connection

logger = logging.getLogger("search")

OPENAI_MODEL = "text-embedding-3-small"

openai_api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)

client = OpenAI(api_key=openai_api_key)

def embed_query(query: str):
    query = query.strip()

    try:
        response = client.embeddings.create(
            model=OPENAI_MODEL,
            input=query
        )
        vector = response.data[0].embedding

        logger.info(f"[embed_query] Embedded query: {query}")

        return vector
    except Exception as e:
        logger.exception(f"[embed_query] Failed to embed query: {e}")
        raise RuntimeError(f"Failed to embed query: {e}")

def search_similar_chunks(user, query_vector, question, top_k=5, document_id=None):
    if not isinstance(query_vector, list) or len(query_vector) != 1536:
        raise ValueError("Query vector must be python list of length 1536")

################## Vector Search ##################

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                dc.id,
                dc.document_id,
                d.original_file_name,
                dc.chunk_index,
                dc.text,
                1 - (dc.embedding <=> %s::vector) AS similarity
            FROM documents_documentchunk dc
            JOIN documents_document d ON dc.document_id = d.id
            WHERE d.user_id = %s
                AND d.status = 'ready'
                AND dc.embedding IS NOT NULL
                AND (%s IS NULL OR d.id = %s)
            ORDER BY dc.embedding <=> %s::vector
            LIMIT %s;
            """,
            [query_vector, user.id, document_id, document_id, query_vector, top_k]
        )

        rows = cursor.fetchall()

        vector_results = {
            row[0]:{
                "chunk_id": row[0],
                "document_id": row[1],
                "document_name": row[2],
                "chunk_index": row[3],
                "text": row[4],
                "vector_score": float(row[5]),
                "fts_score": 0.0
            }
            for row in rows
        }

################## Full Text Search ##################

    ts_query = SearchQuery(question, search_type="plain")

    fts_queryset = (
        DocumentChunk.objects
        .filter(document__user=user, document__status="ready")
        .filter(search_vector=ts_query)
    )

    if document_id:
        fts_queryset = fts_queryset.filter(document_id=document_id)

    fts_queryset = (
        fts_queryset
        .annotate(rank=SearchRank(F("search_vector"), ts_query))
        .order_by("-rank")[:top_k]
    )

    for chunk in fts_queryset:
        if chunk.id in vector_results:
            vector_results[chunk.id]["fts_score"] = float(chunk.rank)
        else:
            vector_results[chunk.id] = {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "document_name": chunk.document.original_file_name,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "vector_score": 0.0,
                "fts_score": float(chunk.rank),
            }

################## Normalize + Merge Results ##################
    if not vector_results:
        return []

    max_vector = max(v["vector_score"] for v in vector_results.values()) or 1
    max_fts = max(v["fts_score"] for v in vector_results.values()) or 1

    merged = []

    for chunk in vector_results.values():
        norm_vector = chunk["vector_score"] / max_vector if max_vector else 0
        norm_fts = chunk["fts_score"] / max_fts if max_fts else 0

        combined_score = 0.6*norm_vector + 0.4*norm_fts

        merged.append({
            "chunk_id": chunk["chunk_id"],
            "document_id": chunk["document_id"],
            "document_name": chunk["document_name"],
            "chunk_index": chunk["chunk_index"],
            "text": chunk["text"],
            "similarity": combined_score,
        })

    merged.sort(key=lambda x: x["similarity"], reverse=True)

    return merged[:top_k]

def rerank_chunks(question, chunks, keep_top=4):
    if not chunks:
        return []

    numbered_chunks = ""
    for i, c in enumerate(chunks):
        numbered_chunks += f"""
        Chunk {i}:
        {c["text"][:800]}
        """

        prompt = f"""
        You are helping select context for answering a question.

        Question:
        {question}

        Below are retrieved text chunks from user's notes.
        Select the MOST relevant chunks for answering the question.

        Return ONLY the chunks numbers in order of usefulness.
        Example output: 2, 5, 1, 0

        Chunks:
        {numbered_chunks}
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )

            content = response.choices[0].message.content
            try:
                indices = [int(x.strip()) for x in content.split(",")]
            except:
                logger.warning("[rerank] Failed to parse rerank response")
                return chunks[:keep_top]

            selected = []
            for idx in indices:
                if 0 <= idx < len(chunks):
                    selected.append(chunks[idx])

            return selected[:keep_top]
        
        except Exception as e:
            logger.error(f"[rerank] Failed rerank response")
            return ""

def build_prompt(chunks, question):
    context_text = "\n\n".join(
        [f"[{c['document_name']} - (chunk {c['chunk_index']})]: {c['text']}" for c in chunks]
    )

    prompt_path = os.path.join(
        settings.BASE_DIR, "search", "prompts", "answer_prompt.txt"
    )
    with open(prompt_path, "r", encoding="utf-8") as f:
        template = f.read()

    system_prompt = template
    user_prompt = f"""
    CONTEXT:
    {context_text}

    QUESTION: {question}
    """

    return system_prompt, user_prompt

def generate_answer(retreived_chunks, question):
    if not retreived_chunks:
        return {
            "answer": "I couldn't find this information in your uploaded notes.",
            "sources": []
        }

    system_prompt, user_prompt = build_prompt(retreived_chunks, question)

    logger.info("[generate_answer] Calling OpenAI API to generate answer...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=300,
            temperature=0.5
        )
        msg = response.choices[0].message
        
        if isinstance(msg.content, str):
            answer = msg.content
        else:
            answer = "".join(
                block.text 
                for block in msg.content 
                if hasattr(block, "text")
            )

        unique_sources = {}
        for c in retreived_chunks:
            unique_sources[c["document_name"]] = True

        sources = [
            {
                "document_name": c["document_name"],
                "chunk_index": c["chunk_index"],
                "text": c.get("text", "")
            }
            for c in retreived_chunks
        ]

        # sources = list(unique_sources.keys())

        return {
            "answer": answer.strip(),
            "sources": sources
        }

    except Exception as e:
        logger.exception(f"[generate_answer] Failed to generate answer: {e}")
        return {
            "answer": "I couldn't generate an answer due to a technical issue.",
            "sources": []
        }