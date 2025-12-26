from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import status

from documents.models import Document
from documents.serializers.serializers_summary import DocumentSummarySerializer, SummaryRegenerationSerializer
from documents.tasks_summary import generate_summary_task
from notes_buddy.core.middleware import get_request_id

class DocumentSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        document = get_object_or_404(Document, id=document_id, user=request.user)

        serializer = DocumentSummarySerializer(document)
        return Response(serializer.data)

class RegenerateSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(Self, request, document_id):
        serializer = SummaryRegenerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        regenerate_flag = serializer.validated_data.get("regenerate")

        if not regenerate_flag:
            return Response({
                "message": "No action taken. Set regenerate=True to regenerate summary."
            })

        try:
            doc = Document.objects.get(id=document_id, user=request.user)

        except Document.DoesNotExist:
            return Response(
                {"error": "Document not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        request_id = get_request_id()
        generate_summary_task.delay(doc.id, request_id=request_id)

        return Response({
            "message": "Summary regeneration initiated.",
            "document_id": document_id
        }, status=status.HTTP_200_OK)