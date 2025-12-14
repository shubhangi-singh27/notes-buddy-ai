from rest_framework import serializers
from documents.models import Document

class DocumentSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id",
            "original_file_name",
            "short_summary",
            "detailed_summary",
        ]

class SummaryRegenerationSerializer(serializers.Serializer):
    regenerate = serializers.BooleanField(default=True)