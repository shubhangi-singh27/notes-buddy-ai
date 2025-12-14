from rest_framework import serializers
from documents.models import Document, DocumentChunk
from documents.utils.extract_text import extract_text, save_extracted_text

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


class DocumentListSerializer(serializers.ModelSerializer):
    num_chunk = serializers.SerializerMethodField()
    size_kb = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id",
            "original_file_name",
            "status",
            "num_chunk",
            "size_kb",
            "created_at",
        ]

    def get_num_chunk(self, obj):
        from documents.models import DocumentChunk
        return DocumentChunk.objects.filter(document=obj).count()

    def get_size_kb(self, obj):
        try:
            return round(obj.file.size / 1024, 2)
        except:
            return None


class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = ['id', 'chunk_index', 'text', 'has_embedding']


class DocumentDetailSerializer(serializers.ModelSerializer):
    chunks = DocumentChunkSerializer(many=True, read_only=True)

    class Meta:
        model = Document
        fields = [
            'id', 
            'original_file_name', 
            'status', 
            'created_at', 
            'extracted_text', 
            'short_summary', 
            'detailed_summary', 
            'chunks'
        ]