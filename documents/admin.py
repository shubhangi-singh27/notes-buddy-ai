from django.contrib import admin
from .models import Document, DocumentChunk, SummaryHistory

class SummaryHistoryInline(admin.TabularInline):
    model = SummaryHistory
    extra = 0
    readonly_fields = ['short_summary', 'detailed_summary', 'created_at']
    ordering = ['-created_at']

class DocumentChunkInline(admin.TabularInline):
    model = DocumentChunk
    extra = 0
    fields = ('chunk_index', 'text_preview', 'has_embedding')
    readonly_fields = ('chunk_index', 'text_preview', 'has_embedding')

    def text_preview(self, obj):
        return (obj.text[:80] + "...") if obj.text else ""
    text_preview.short_description = "Preview"

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "original_file_name",
        "user",
        "status",
        "created_at",
        "chunk_count",
        "extracted_text_length"
    )
    list_filter = ("status", "created_at")
    search_fields = ("original_file_name", "user__username")
    readonly_fields = (
        "original_file_name",
        "file",
        "status",
        "created_at",
        "extracted_text_preview",
        "short_summary",
        "detailed_summary",
        "summary_generated_at",
    )

    inlines = [DocumentChunkInline]

    def extracted_text_preview(self, obj):
        if not obj.extracted_text:
            return ""

        return obj.extracted_text[:300] + "..."

    extracted_text_preview.short_description = "Extracted Text Preview"

    def chunk_count(self, obj):
        return obj.chunks.count()

    chunk_count.short_description = "Chunk Count"

    def extracted_text_length(self, obj):
        return len(obj.extracted_text or "")

    extracted_text_length.short_description = "Extracted Text Length"

@admin.register(SummaryHistory)
class SummaryHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "document",
        "created_at",
        "short_preview"
    )

    ordering = ['-created_at']

    def short_preview(self, obj):
        return (obj.short_summary[:80] + "...") if obj.short_summary else ""