from documents.models import Document, DocumentChunk
from documents.utils.extract_text import extract_text, save_extracted_text
from documents.utils.chunking import chunk_text
from documents.utils.embeddings import embed_texts
from celery import shared_task
import logging

@shared_task
def process_document(document_id):
    logger.info(f"[process_document] Started for document {document_id}")
    try:
        doc = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        logger.error(f"Document with id {document_id} does not exist")
        return

    file_path = doc.file.path
    logger.info(f"[process_document] Extracting text from: {file_path}")

    try:
        # Extract text from the document
        text = extract_text(file_path)
        logger.info(f"[extract] Text extracted ({len(text)} chars)")

        save_extracted_text(doc, text)
        logger.info(f"[extract] Saved extracted text to file")

        doc.extracted_text = text
        doc.status = "extracted"
        doc.save()

        # Delete existing chunks for this document
        DocumentChunk.objects.filter(document=doc).delete()

        # Chunk the text
        chunks = chunk_text(text, max_tokens=500, overlap=50)
        logger.info(f"[chunk] Created {len(chunks)} chunks")

        for idx, chunk in enumerate(chunks):
            DocumentChunk.objects.create(
                document=doc,
                chunk_index=idx,
                text=chunk,
                embedding=None,
            )

        print(f"Created {len(chunks)} chunks for {doc.original_file_name}")

        # Generate embeddings for the chunks
        logger.info(f"[process_document] Triggering embedding task for doc {document_id}")
        generate_embeddings_task.delay(document_id)

        logger.info(f"[process_document] Completed: {document_id}")

        return {"status": "success", "document_id": doc.id}

    except Exception as e:
        logger.exception(f"Error processing document {doc.original_file_name}: {e}")
        doc.status = "error"
        doc.save()
        return {"status": "failed", "document_id": doc.id}

@shared_task
def generate_embeddings_task(document_id):
    logger.info(f"[embedding] Started for doc {document_id}")
    try:
        chunks = DocumentChunk.objects.filter(document_id=document_id).order_by("chunk_index")
        texts = [c.text for c in chunks]

        logger.info(f"[embedding] Found {len(texts)} chunks to embed")

        if not texts:
            logger.warning(f"[embedding] No chunks found for doc {document_id}")
            return False

        vectors = embed_texts(texts)
        logger.info(f"[embedding] Embeddings generated successfully")

        for chunk, vector in zip(chunks, vectors):
            chunk.embedding = vector
            chunk.save(update_fields=["embedding"])


        logger.info(f"[embedding] Saved all embeddings for doc {document_id}")
        return True

    except Exception as e:
        logger.exception(f"Embedding generation failed for document {document_id}: {e}")
        return False