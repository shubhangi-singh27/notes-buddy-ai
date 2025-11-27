from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .services.search_engine import embed_query, search_similar_chunks, generate_answer

class SemanticSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q")
        if not query:
            return Response({"error": "Missing query params ?q="}, status=400)

        vector = embed_query(query)

        results = search_similar_chunks(request.user, vector)

        return Response({
            "query": query,
            "results": results
        })

class AnswerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question = request.data.get("question")

        if not question:
            return Response({"error": "Missing question"}, status=400)

        query_vector = embed_query(question)

        chunks = search_similar_chunks(
            user = request.user, 
            query_vector = query_vector,
            top_k = 3
        )

        result = generate_answer(chunks, question)

        return Response({
            "question": question,
            "answer": result["answer"],
            "sources": result["sources"],
            "num_chunks_used": len(chunks)
        })