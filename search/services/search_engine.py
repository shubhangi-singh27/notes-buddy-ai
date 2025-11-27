import os
import logging
from openai import OpenAI
from django.conf import settings
from documents.models import DocumentChunk
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

def search_similar_chunks(user, query_vector, top_k=5):
    if not isinstance(query_vector, list) or len(query_vector) != 1536:
        raise ValueError("Query vector must be python list of length 1536")

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
            ORDER BY dc.embedding <=> %s::vector
            LIMIT %s;
            """,
            [query_vector, user.id, query_vector, top_k]
        )

        rows = cursor.fetchall()

    results = []
    for row in rows:
        results.append({
            "chunk_id": row[0],
            "document_id": row[1],
            "document_name": row[2],
            "chunk_index": row[3],
            "text": row[4],
            "similarity": row[5]
        })

    return results

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

        sources = [
            {
                "document_name": c["document_name"],
                "chunk_index": c["chunk_index"]
            }
            for c in retreived_chunks
        ]

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