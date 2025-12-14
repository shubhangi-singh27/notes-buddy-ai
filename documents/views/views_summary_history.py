from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from documents.models import SummaryHistory

class SummaryHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        try:
            doc = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response(
                {"error": "Document not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        history = doc.summary_history.order_by('-created_at')
        serializer = SummaryHistorySerializer(history, many=True)

        return Response({
            "document_id": document_id,
            "file_name": doc.original_file_name,
            "total_versions": history.count(),
            "history": serializer.data
        })