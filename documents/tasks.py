from documents.models import Document, DocumentChunk
from documents.utils.extract_text import extract_text, save_extracted_text
from documents.utils.chunking import chunk_text
from documents.utils.embeddings import embed_texts
from documents.tasks_summary import generate_summary_task
from celery import shared_task
import logging
import time
from django.contrib.postgres.search import SearchVector
from billiard.exceptions import SoftTimeLimitExceeded
from django.db.models import Count
from django.contrib.postgres.search import SearchVector

logger = logging.getLogger("documents")

BATCH_SIZE = 100


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=30, retry_kwargs={"max_retries": 3}, soft_time_limit=180,)
def process_document(self, document_id, request_id=None):
    if request_id:
        from notes_buddy.core.middleware import _request_id
        _request_id.value = request_id

    logger.info(f"Started for document {document_id}")
    try:
        doc = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        logger.error(f"Document with id {document_id} does not exist")
        return

    file_path = doc.file.path
    logger.info(f"Extracting text from: {file_path}")

    try:
        # Extract text from the document
        text = extract_text(file_path)
        logger.info(f"Text extracted: {text[:2000]}")
        logger.info(f"Text extracted ({len(text)} chars)")

        save_extracted_text(doc, text)
        logger.info(f"Saved extracted text to file")

        doc.extracted_text = text
        doc.status = "extracted"
        doc.save(update_fields=["extracted_text", "status"])

        # Delete existing chunks for this document
        DocumentChunk.objects.filter(document=doc).delete()

        # Chunk the text
        chunks = chunk_text(text)
        logger.info(f"Created {len(chunks)} chunks")

        # Split chunks into batches
        total_chunks = len(chunks)
        for i in range(0, total_chunks, BATCH_SIZE):
            batch = chunks[i:i+BATCH_SIZE]

            process_chunk_batch.delay(
                document_id=document_id,
                chunks_batch=batch,
                start_index=i,
                request_id=request_id,
            )

        doc.status = "processing_chunks"
        doc.save(update_fields=["total_chunks", "status"])

        return {"status": "embedded", "document_id": doc.id}

    except SoftTimeLimitExceeded:
        logger.warning(f"Soft time limit exceeded for document {document_id}")
        Document.objects.filter(id=document_id).update(status="processing_delayed")
        raise
    
    except Exception as e:
        logger.exception(f"Error processing document {doc.original_file_name}: {e}")
        doc.status = "error"
        doc.save()
        return {"status": "failed", "document_id": doc.id}


@shared_task
def process_chunk_batch(document_id, chunks_batch, start_index, request_id=None):
    if request_id:
        from notes_buddy.core.middleware import _request_id
        _request_id.value = request_id

    logger.info(f"Started for document {document_id} with batch size {len(chunks_batch)} and start index {start_index}")

    # Bulk create chunks
    chunk_objects = [
        DocumentChunk(
            document_id=document_id,
            chunk_index=start_index + idx,
            text=chunk,
            embedding=None
        )
        for idx, chunk in enumerate(chunks_batch)
    ]

    DocumentChunk.objects.bulk_create(chunk_objects, batch_size=BATCH_SIZE)

    texts = [c.text for c in chunk_objects]

    vectors = embed_texts(texts)

    for obj, vector in zip(chunk_objects, vectors):
        obj.embedding = vector

    DocumentChunk.objects.bulk_update(chunk_objects, ["embedding"], batch_size=BATCH_SIZE)
    DocumentChunk.objects.filter(
        document_id=document_id,
        chunk_index__gte=start_index,
        chunk_index__lt=start_index + BATCH_SIZE
    ).update(search_vector=SearchVector("text"))

    total_chunks = DocumentChunk.objects.filter(document_id=document_id).count()

    doc = Document.objects.get(id=document_id)

    processed_chunks = DocumentChunk.objects.filter(
        document_id=document_id, 
        embedding__isnull=False
    ).count() 

    if processed_chunks == total_chunks:
        updated = Document.objects.filter(
            id=document_id
        ).exclude(status="ready").update(status="ready")
        
        if updated:
            doc.status = "ready"
            doc.save(update_fields=["status"])
            logger.info(f"Document {document_id} marked as ready")
            generate_summary_task.delay(document_id, request_id)


# Commented out because we are using process_chunk_batch in order to implement batching
# for large documents

"""@shared_task
def generate_embeddings_task(document_id, request_id=None):
    if request_id:
        from notes_buddy.core.middleware import _request_id
        _request_id.value = request_id

    logger.info(f"[generate_embeddings_task] Started for doc {document_id}")
    try:
        chunks = DocumentChunk.objects.filter(document_id=document_id).order_by("chunk_index")
        texts = [c.text for c in chunks]

        logger.info(f"[generate_embeddings_task] Found {len(texts)} chunks to embed")

        if not texts:
            logger.warning(f"[generate_embeddings_task] No chunks found for doc {document_id}")
            return False

        start = time.time()
        vectors = embed_texts(texts)
        logger.info(f"[generate_embeddings_task] Embeddings generated successfully",
                    extra={
                        "document_id": document_id,
                        "duration": round(time.time() - start, 2),
                        "chunks": len(texts)
                    })

        for chunk, vector in zip(chunks, vectors):
            chunk.embedding = vector
            # chunk.save(update_fields=["embedding"]) # causing softLimit exceeded error

        DocumentChunk.objects.bulk_update(chunks, ["embedding"])

        Document.objects.filter(id=document_id).update(status="embedded")
        logger.info(f"[generate_embeddings_task] Saved all embeddings for doc {document_id} in {round(time.time() - start, 2)} seconds")

        mark_document_ready.delay(document_id, request_id)
        return True

    except Exception as e:
        logger.exception(f"[generate_embeddings_task] Embedding generation failed for document {document_id}: {e}")
        return False"""

# Commented out because we are using process_chunk_batch in order to implement batching
# for large documents
"""@shared_task
def mark_document_ready(document_id, request_id=None):
    Document.objects.filter(id=document_id).update(status="ready")

    logger.info(f"[mark_document_ready] Document {document_id} marked as ready")

    generate_summary_task.delay(document_id, request_id)"""