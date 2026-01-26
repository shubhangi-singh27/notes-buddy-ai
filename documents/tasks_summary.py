import logging
import re
import os
from celery import shared_task
from django.utils import timezone
from openai import OpenAI

from django.conf import settings
from documents.models import Document, SummaryHistory

logger = logging.getLogger("summary")

openai_api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)

client = OpenAI(api_key=openai_api_key)

def clean_summary_text(text):
    """Remove redundant heading keywords and formatting from summary text"""
    if not text:
        return text

    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)

    patterns_to_remove = [
        r'^\s*\*\*?Very\s:?\s*\*\*?\s*',
        r'^\s*Very\s:?\s*',
        r'^s*\*\*?Short\s+[Ss]ummary\s*:?\s*\*\*?\s*',
        r'^\s*Short\s+[Ss]ummary\s*:?\s*',
        r'^\s*\*\*?[Dd]etailed\s+[Ss]ummary\s*:?\s*\*\*?\s*',
        r'^\s*[Dd]etailed\s+[Ss]ummary\s*:?\s*',
        r'^\s*\*\*?[Ss]ummary\s*:?\s*\*\*?\s*',
        r'^\s*[Ss]ummary\s*:?\s*',
        r'Very\s+',
        r'[Dd]etailed\s+[Ss]ummary',
    ]

    cleaned = text
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE | re.IGNORECASE)

    cleaned = cleaned.strip().lstrip(':').lstrip('-').strip()

    return cleaned

@shared_task
def generate_summary_task(document_id, request_id=None):
    if request_id:
        from notes_buddy.core.middleware import _request_id
        _request_id.value = request_id

    try:
        doc = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        logger.error(f"[Summary Task] Document {document_id} not found")
        return False

    if not doc.extracted_text or len(doc.extracted_text.strip()) < 20:
        logger.error(f"[Summary Task] Document {document_id} has no extracted text to summarize")
        return False

    logger.info(f"[Summary Task] Generating summary for {doc.original_file_name}...")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a notes summarizer AI. Produce clean, readable summaries."
                },
                {
                    "role": "user",
                    "content": f"""Summarize the following document at 2 levels:
                    1. A very short summary (3-4 sentences) - no heading, just the summary text
                    2. A detailed summary (5-6 bullet points) - no heading, just the summary text

                    Do not include any headings, labels, or prefixes like "Short Summary:" or "Detailed Summary:", etc. Just provide the summary content directly.
                    
                    Document Text:
                    {doc.extracted_text[:15000]}
                    """
                }
            ],
            max_tokens=600,
            temperature=0.4,
        )
        msg = response.choices[0].message

        if isinstance(msg.content, str):
            full_output = msg.content
        else:
            full_output = "".join(block.text for block in msg.content if hasattr(block, "text"))


        if "Detailed Summary" in full_output or "detailed_summary" in full_output:
            match = re.search(r'[Dd]etailed [Ss]ummary[:\s]*', full_output)
            if match:
                split_pos = match.end()
                short = clean_summary_text(full_output[:split_pos])
                detailed = clean_summary_text(full_output[split_pos:])
            else:
                short = clean_summary_text(full_output[:300])
                detailed = clean_summary_text(full_output)
        else:
            short = clean_summary_text(full_output[:300])
            detailed = clean_summary_text(full_output)

        if doc.summary_generated_at:
            SummaryHistory.objects.create(
                document=doc,
                short_summary=doc.short_summary,
                detailed_summary=doc.detailed_summary
            )

        doc.short_summary = short
        doc.detailed_summary = detailed
        doc.summary_generated_at = timezone.now()
        doc.save(update_fields=["short_summary", "detailed_summary", "summary_generated_at"])

        logger.info(f"[Summary Task] Summary generated for {doc.original_file_name}")
        return True

    except Exception as e:
        logger.exception(f"[Summary Task] Error generating summary for {doc.original_file_name}: {e}")
        return False