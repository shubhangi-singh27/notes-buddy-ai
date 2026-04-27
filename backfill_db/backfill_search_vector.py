import os
import sys

# Project root = parent of scripts/
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "notes_buddy.settings")
os.environ["testRun"] = "1"
django.setup()

from django.contrib.postgres.search import SearchVector
from documents.models import DocumentChunk

DocumentChunk.objects.update(search_vector=SearchVector("text"))