from rest_framework import serializers
from .models import Document
from .utils.extract_text import extract_text, save_extracted_text

class DocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['file']

    def create(self, validated_data):
        user = self.context['request'].user
        file_obj = validated_data['file']

        doc = Document.objects.create(
            user=user,
            file=file_obj,
            original_file_name=file_obj.name,
            status='uploaded'
        )

        return doc
