from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .tasks import process_document
from .serializers import DocumentUploadSerializer


class DocumentUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DocumentUploadSerializer(
            data=request.data, 
            context={'request': request}
        )

        if serializer.is_valid():
            doc = serializer.save()

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