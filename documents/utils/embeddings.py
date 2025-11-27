import os
import time
import logging
from typing import List

from openai import OpenAI
from django.conf import settings
from django.db import transaction

from documents.models import DocumentChunk

logger = logging.getLogger(__name__)

OPENAI_MODEL = "text-embedding-3-small"
BATCH_SIZE = 32

openai_api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)
client = OpenAI(api_key=openai_api_key)

def embed_texts(texts: List[str]) -> List[List[float]]:
    if not openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    resp = client.embeddings.create(model=OPENAI_MODEL, input=texts)

    embeddings = [item.embedding for item in resp.data]
    return embeddings