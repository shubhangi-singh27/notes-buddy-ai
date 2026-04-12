from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .services.search_engine import embed_query, search_similar_chunks, generate_answer, rerank_chunks
from .services.context_compression import compress_context
from .services.query_rewrite import rewrite_query
import logging

logger = logging.getLogger(__name__)

class SemanticSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q")
        if not query:
            return Response({"error": "Missing query params ?q="}, status=400)

        vector = embed_query(query)

        results = search_similar_chunks(request.user, vector, query)

        return Response({
            "query": query,
            "results": results
        })

class AnswerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question = request.data.get("question")
        document_id = request.data.get("document_id")

        rewritten_question = rewrite_query(question)

        if not question:
            return Response({"error": "Missing question"}, status=400)

        query_vector = embed_query(rewritten_question)

        if document_id:
            retrieved_chunks = search_similar_chunks(
                user=request.user,
                query_vector=query_vector,
                question=question,
                top_k=3,
                document_id=document_id,   # NEW
            )
            reranked_chunks = rerank_chunks(rewritten_question, retrieved_chunks)
        else:
            retrieved_chunks = search_similar_chunks(
                user=request.user,
                query_vector=query_vector,
                question=question,
                top_k=12,
            )
            reranked_chunks = rerank_chunks(rewritten_question, retrieved_chunks)

        # Diversify chunks to avoid using the same document too many times
        diversified = []
        doc_usage = {}

        logger.info(
            f"Retrieved {len(retrieved_chunks)} chunks, kept {len(reranked_chunks)}"
        )

        for chunk in reranked_chunks:
            doc_id = chunk["document_id"]
            used = doc_usage.get(doc_id, 0)

            if used < 2:
                diversified.append(chunk)
                doc_usage[doc_id] = used + 1

            if len(diversified) >= 5:
                break

        chunks = diversified

        compressed_chunks = compress_context(chunks, question, query_vector)

        result = generate_answer(chunks, question)

        return Response({
            "question": question,
            "scope": "document" if document_id else "general",
            "answer": result["answer"],
            "sources": result["sources"],
            "num_chunks_used": len(chunks)
        })