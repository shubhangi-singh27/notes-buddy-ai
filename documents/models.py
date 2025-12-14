import os
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from pgvector.django import VectorField

class Document(models.Model):
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('extracted', 'Extracted'),
        ('chunked', 'Chunked'),
        ('embedded', 'Embedded'),
        ('ready', 'Ready')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='documents/')
    original_file_name = models.CharField(max_length=255)
    text_content = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    extracted_text = models.TextField(blank=True, null=True)
    file_type = models.CharField(max_length=20, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    short_summary = models.TextField(blank=True, null=True)
    detailed_summary = models.TextField(blank=True, null=True)
    summary_generated_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.original_file_name}: {self.status}"

    def extracted_text_path(self):
        folder = os.path.join(settings.MEDIA_ROOT, "documents", str(self.id))
        return os.path.join(folder, "extracted_text.txt")


class DocumentChunk(models.Model):
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.CASCADE,
        related_name="chunks"
    )
    chunk_index = models.IntegerField()
    text = models.TextField()

    embedding = VectorField(dimensions=1536, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('document', 'chunk_index')
        ordering = ['chunk_index']

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.original_file_name}"

    @property
    def has_embedding(self):
        return self.embedding is not None

class SummaryHistory(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="summary_history")
    short_summary = models.TextField(blank=True, null=True)
    detailed_summary = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Summary for {self.document.original_file_name}"