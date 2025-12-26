from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
import os
from django.utils.dateparse import parse_date
from django.db.models import Count
from documents.tasks import process_document
from documents.serializers.serializers import (
    DocumentUploadSerializer,
    DocumentListSerializer,
    DocumentDetailSerializer
)
from documents.models import Document
from notes_buddy.core.middleware import get_request_id


class DocumentUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DocumentUploadSerializer(
            data=request.data, 
            context={'request': request}
        )

        if serializer.is_valid():
            doc = serializer.save()

            request_id = get_request_id()
            process_document.delay(doc.id)

            return Response(
                {
                    "id": doc.id,
                    "filename": doc.original_file_name,
                    "status": doc.status
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DocumentListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get(self, request):
        documents = Document.objects.filter(user=request.user)\
            .annotate(num_chunks=Count('chunks', distinct=True))\
            .order_by('-created_at')

        ##### FILTERS #####
        status_param = request.query_params.get("status")
        if status_param:
            documents = documents.filter(status=status_param)

        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        if date_from:
            parsed = parse_date(date_from)
            if parsed:
                documents = documents.filter(created_at__gte=parsed)

        if date_to:
            parsed = parse_date(date_to)
            if parsed:
                documents = documents.filter(created_at__lte=parsed)

        search = request.query_params.get("search")
        if search:
            documents = documents.filter(original_file_name__icontains=search)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(documents, request)

        if page is not None:
            serializer = DocumentListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = DocumentListSerializer(documents, many=True)
        return Response(serializer.data)

class DocumentDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DocumentDetailSerializer

    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)

class DocumentDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, document_id):
        try:
            doc = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response(
                {"error":"Document not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if doc.file and os.path.exists(doc.file.path):
            os.remove(doc.file.path)

        extracted_path = doc.extracted_text_path()
        if os.path.exists(extracted_path):
            os.remove(extracted_path)
            extracted_folder = os.path.dirname(extracted_path)
            if os.path.exists(extracted_folder) and not os.listdir(extracted_folder):
                os.rmdir(extracted_folder)
                
        folder_path = os.path.dirname(doc.file.path)
        if os.path.exists(folder_path) and not os.listdir(folder_path):
            os.rmdir(folder_path)

        doc.delete()

        return Response(
            {"message":"Document deleted successfully"},
            status=status.HTTP_200_OK
        )