import os
import re
import logging
import json
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

        logger.info(f"Embedded query: {query}")

        return vector
    except Exception as e:
        logger.exception(f"[embed_query] Failed to embed query: {e}")
        raise RuntimeError(f"Failed to embed query: {e}")

def search_similar_chunks(user, query_vector, question, top_k=5, document_id=None, vector_limit=20, fts_limit=20):
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
                1 - (dc.embedding <=> %s::vector) AS similarity,
                dc.embedding
            FROM documents_documentchunk dc
            JOIN documents_document d ON dc.document_id = d.id
            WHERE d.user_id = %s
                AND d.status = 'ready'
                AND dc.embedding IS NOT NULL
                AND (%s IS NULL OR d.id = %s)
            ORDER BY dc.embedding <=> %s::vector
            LIMIT %s;
            """,
            [query_vector, user.id, document_id, document_id, query_vector, vector_limit]
        )

        rows = cursor.fetchall()

        vector_results = [
            {
                "chunk_id": row[0],
                "document_id": row[1],
                "document_name": row[2],
                "chunk_index": row[3],
                "text": row[4],
                "vector_score": float(row[5]),
                "embedding": row[6],
                "fts_score": 0.0
            }
            for row in rows
        ]

        vector_results.sort(key=lambda x: x["vector_score"], reverse=True)

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
        .filter(rank__gte=0.05)
        .order_by("-rank")[:fts_limit]
    )

    fts_results = [
        {
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "document_name": chunk.document.original_file_name,
            "chunk_index": chunk.chunk_index,
            "text": chunk.text,
            "vector_score": 0.0,
            "fts_score": float(chunk.rank),
        }
        for chunk in fts_queryset
    ]
    
    fts_results.sort(key = lambda x: x["fts_score"], reverse=True)

################## Normalize + Merge Results ##################
    if not vector_results:
        return []

    RRF_K = 60

    rrf_scores = {}

    for rank, chunk in enumerate(vector_results):
        cid = chunk["chunk_id"]
        rrf_scores.setdefault(cid, chunk.copy())
        rrf_scores[cid]["rrf_score"] = rrf_scores[cid].get("rrf_score", 0) + (1 / (RRF_K + rank + 1))

    for rank, chunk in enumerate(fts_results):
        cid = chunk["chunk_id"]
        if cid not in rrf_scores:
            rrf_scores[cid] = chunk.copy()
        else:
            rrf_scores[cid]["vector_score"] = max(rrf_scores[cid].get("vector_score"), chunk.get("vector_score", 0.0))    
            rrf_scores[cid]["fts_score"] = max(rrf_scores[cid].get("fts_score", 0.0), chunk.get("fts_score", 0.0))
        
        rrf_scores[cid]["rrf_score"] = rrf_scores[cid].get("rrf_score", 0) + (1 / (RRF_K + rank + 1))

    merged = sorted(rrf_scores.values(), key=lambda x: x["rrf_score"], reverse = True)

    return [
        {
            "chunk_id": c["chunk_id"],
            "document_id": c["document_id"],
            "document_name": c["document_name"],
            "chunk_index": c["chunk_index"],
            "text": c["text"],
            "similarity": c["rrf_score"],
            "vector_score": c.get("vector_score", 0.0),
            "fts_score": c.get("fts_score", 0.0),
        }
        for c in merged[:top_k]
    ]

    return merged[:top_k]

def rerank_chunks(question, chunks, keep_top=8):
    if not chunks:
        return []

    chunks = chunks[:keep_top]

    numbered_chunks = ""
    for i, c in enumerate(chunks):
        text = c["text"][:500]
        numbered_chunks += f"""\nChunk {i}:\n{text}\n"""

    prompt = f"""
You are scoring relevance of context chunks for answering a question.

Question:
{question}

For each chunk, assign a relevance score between 0 and 1.

Scoring guidelines:
- 1.0 = directly answers the question
- 0.7 = contains useful supporting information
- 0.4 = partially relevant
- 0.0 = irrelevant

Return ONLY valid JSON in this format:

[
  {{"chunk_id": 0, "score": 0.9}},
  {{"chunk_id": 1, "score": 0.2}}
]

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

        if not isinstance(content, str):
            content = "".join(
                block.text for block in content if hasattr(block, "text")
            )
        
        clean = content.strip()
        if clean.startswith("```"):
            clean = re.sub(r"^```(?:json)?\s*", "", clean)
            clean = re.sub(r"\s*```$", "", clean)

        parsed = json.loads(clean)

        scored_chunks = []
        for item in parsed:
            idx = item.get("chunk_id")
            score = item.get("score", 0)

            if isinstance(idx, int) and 0 <= idx < len(chunks):
                chunk = chunks[idx].copy()
                chunk["rerank_score"] = score
                scored_chunks.append(chunk)

        if not scored_chunks:
            return chunks[:keep_top]


        scored_chunks.sort(key=lambda x: x["rerank_score"], reverse=True)

        return scored_chunks[:keep_top]
    
    except Exception as e:
        logger.error(f"[rerank] Failed rerank response: {str(e)}")
        return chunks[:keep_top]

def build_prompt(chunks, question):
    context_text = "\n\n".join(
        [f"[{c['document_name']} - (chunk {c['chunk_index']})]: {c['text']}" for c in chunks]
    )

    # logger.info(f"Context: \n {context_text[:1000]}")

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

    logger.info("Calling OpenAI API to generate answer...")
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