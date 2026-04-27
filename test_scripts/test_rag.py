import os
import time
from datetime import datetime
from openpyxl import Workbook
from numpy import dot
from numpy.linalg import norm

import os
import sys

# Project root = parent of scripts/
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "notes_buddy.settings")
os.environ["testRun"] = "1"
django.setup()

from django.contrib.auth.models import User
from search.services.search_engine import (
    embed_query,
    search_similar_chunks,
    rerank_chunks,
    generate_answer
)
from search.services.query_rewrite import rewrite_query
from search.services.context_compression import compress_context

RUN_ID = "run_reranked"
SYSTEM_VERSION = "baseline_v2"

TEST_QUERIES = [
    "tcp",
    "democracy",
    "deadlock",
    "India",
    "elections",
    "different types of operating systems",
    "media in democracy",
    "freedom on speech",
    "religion",
    "VM",
    "Cloud deployment"
]

TOP_K = 10

RESULTS_DIR = os.path.join(ROOT, "results_v2")

def format_chunks(chunks):
    if not chunks:
        return

    formatted = []

    for c in chunks:
        preview = c["text"][:150].replace("\n", " ")
        formatted.append(
            f"[{c['document_name']} | {c['chunk_index']} | {round(c['similarity'], 3)} | {preview}"
        )

    return " || ".join(formatted)

def compute_score_stats(chunks, key):
    vals = [float(c.get(key, 0.0)) for c in chunks]

    if not vals:
        return 0.0, 0.0
    
    sum_vals = 0
    gt_zero = 0
    for i in range(len(vals)):
        sum_vals += vals[i]
        gt_zero += 1 if vals[i] > 0 else 0

    if gt_zero == 0:
        return (0.0, max(vals))

    return round(sum_vals/gt_zero, 4), round(max(vals), 4)

def compute_similarity_metrics(chunks):
    if not chunks:
        return 0, 0

    sims = [c['similarity'] for c in chunks]
    avg = sum(sims)/len(sims)
    top = max(sims)

    return round(avg, 3), round(top, 3)

def run_query(user, question):
    start_time = time.time()

    rewritten_question = question # rewrite_query(question)

    query_vector = embed_query(rewritten_question)

    retrieved = search_similar_chunks(
        user=user,
        query_vector=query_vector,
        question=question,
        top_k=TOP_K,
        vector_limit=20,
        fts_limit=20
    )

    reranked = None
    compressed = None
    total_tokens_before = None
    total_tokens_after = None
    reranked = rerank_chunks(rewritten_question, retrieved)

    # compressed, total_tokens_before, total_tokens_after = compress_context(retrieved, rewritten_question, query_vector)
    # compressed, total_tokens_before, total_tokens_after = compress_context(reranked, rewritten_question, query_vector)
    
    # result = generate_answer(retrieved, rewritten_question)
    result = generate_answer(reranked, rewritten_question)
    # result = generate_answer(compressed, rewritten_question)

    latency = round(time.time() - start_time, 2)

    return {
        "question": question,
        "rewritten_question": rewritten_question,
        "retrieved": retrieved,
        "answer": result["answer"],
        "sources": result["sources"],
        "latency": latency,
        "compressed": compressed if compressed else None,
        "total_tokens_before": total_tokens_before if total_tokens_before else None,
        "total_tokens_after": total_tokens_after if total_tokens_after else None,
        "reranked": reranked if reranked else None,
    }

def write_to_excel(user, rows):
    wb = Workbook()
    ws = wb.active
    ws.title = "RAG Test Results"

    headers = [
        "run_id",
        "timestamp",
        "system_version",

        "question",
        "rewritten_question",
        
        "retrieved_chunks",
        "reranked_chunks",
        "compressed_chunks",
        "total_tokens_before",
        "total_tokens_after",
        "num_retrieved",
        "num_reranked",

        "vector_score_avg",
        # "vector_score_top",
        "fts_score_avg",
        #"fts_score_top",
        "rrf_rank_avg",
        # "rrf_rank_top",

        "answer",
        "sources",

        "latency_total",

        # manual fields
        "chunk_score",
        "source_relevance",
        "answer_quality",
        "failure_type",
        "notes"
    ]

    ws.append(headers)

    os.makedirs(RESULTS_DIR, exist_ok=True)

    filename = f"{RUN_ID}_{SYSTEM_VERSION}_{user}.xlsx"
    filepath = os.path.join(RESULTS_DIR, filename)

    for row in rows:
        ws.append(row)

        wb.save(filepath)

        print(f"\nSaved results to {filename}")


def main():
    username = "social_science"
    user = User.objects.get(username=username)

    if not user:
        print("No user found")
        return

    rows = []

    for q in TEST_QUERIES:
        print(f"\nRunning query: {q}")

        result = run_query(user, q)

        retrieved = result["retrieved"]
        reranked = result["reranked"]
        compressed = result["compressed"] if result["compressed"] else None

        vector_score_avg, vector_score_top = compute_score_stats(reranked, "vector_score")
        fts_score_avg, fts_score_top = compute_score_stats(reranked, "fts_score")
        rrf_rank_avg, rrf_rank_top = compute_score_stats(reranked, "similarity")

        row = [
            RUN_ID,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            SYSTEM_VERSION,

            result["question"],
            result["rewritten_question"],

            format_chunks(retrieved),
            format_chunks(reranked) if reranked else None,
            format_chunks(compressed) if compressed else None,
            result["total_tokens_before"] if result["total_tokens_before"] else None,
            result["total_tokens_after"] if result["total_tokens_after"] else None,
            len(retrieved),
            len(reranked) if reranked else 0,

            vector_score_avg,
            # vector_top_sim,
            fts_score_avg,
            # fts_top_sim,
            rrf_rank_avg,
            # top_rrf_rank

            result["answer"],
            ", ".join(f"{s['document_name']}#chunk{s['chunk_index']}" for s in result["sources"]),

            result["latency"],

            # manual fields
            "",
            "",
            "",
            "",
            ""
        ]

        rows.append(row)

    write_to_excel(user,rows)

if __name__ == "__main__":
    main()