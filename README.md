# 🧠 Notes Buddy — AI-Powered Personal Knowledge Search

An AI-powered backend system that lets users upload notes (PDF, DOCX, TXT), automatically extract text, chunk it, embed it using OpenAI, store vectors in pgvector, and perform semantic search with GPT-powered answers.

This backend implements a full **RAG (Retrieval Augmented Generation)** pipeline using Django, Celery, Redis, PostgreSQL, and pgvector.

---

## 🚀 Features

### 🔹 File Upload System
- Supports PDF, DOCX, TXT
- Extracts text using PyPDF & python-docx
- Stores extracted content for processing

### 🔹 Asynchronous Processing Pipeline
Powered by **Celery + Redis**:
- Text extraction
- Chunking
- Embedding generation
- Summary generation

### 🔹 Text Chunking
- Fixed-size overlapping chunks (current)
- Stored in PostgreSQL with document linkage

### 🔹 Vector Embeddings (OpenAI)
- Uses `text-embedding-3-small`
- Stored in **pgvector**
- Enables semantic similarity search

### 🔹 Hybrid Search (RRF-Based)

Combines multiple retrieval signals:

- Vector similarity (pgvector)
- Full-text keyword search (PostgreSQL)
- Reciprocal Rank Fusion (RRF) for merging results

This allows:
- Better handling of both semantic queries and exact matches
- More robust retrieval across different query types

Note:
- RRF scores represent rank, not absolute similarity

### 🔹 RAG-based Answer Generation
- Query is embedded
- Top chunks retrieved (hybrid search)
- Context passed to `gpt-4o-mini`
- Returns:
  - Final answer
  - Source references

### 🔹 Source Explainability (UI)
- Hover on source → preview actual chunk
- Makes retrieval transparent and debuggable

### 🔹 Authentication
- JWT-based authentication (SimpleJWT)

### 🔹 Operational Setup
- Fully Dockerized environment
- Runs inside **WSL (Ubuntu)**
- Health check endpoint
- Structured logging

---

## 🏗️ Tech Stack

- **Python 3.12**
- **Django 5**
- **Django Rest Framework**
- **PostgreSQL 16**
- **pgvector 0.5**
- **Redis 7 (Docker)**
- **Celery 5**
- **OpenAI API**
- **PyPDF + python-docx**
- **Docker Engine (WSL2 Ubuntu 24.04)**
- **Docker Compose**
- **uv (Python package manager)**
- **WSL Ubuntu 24.04**

---

## 📁 Project Structure

```
notes_buddy/
├── documents/
├── health/
├── search/
├── users/
├── notes_buddy/  # Django settings
├── manage.py
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

---

# ▶️ Project Setup

## Recommended: Docker Setup (WSL)

The project is designed to run inside **Docker (via WSL2)** for consistency across environments.

---
## 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/notes_buddy.git
cd notes_buddy

cp .env.example .env

```

### Option A: Docker Setup

```bash

docker compose build # First time only

docker compose run web python manage.py migrate # First time only

docker compose up

```

### Option B: Local Setup (Not Recommended for Production Parity)

```bash

uv sync

uv run python manage.py migrate

redis-server --port 6380

uv run celery -A notes_buddy worker --loglevel=info

uv run python manage.py runserver

```

Backend now runs at:

http://127.0.0.1:8000/

Health check:

GET http://localhost:8000/api/health/

---



## 🔍 API Endpoints

### 📤 Upload Document
```
POST /api/documents/upload/
```
Form-data:
```
file: <file.pdf>
```

### 🔎 Semantic Search
```
GET /api/search/?q=what is smm?
```

### 🤖 GPT Answer
```
POST /api/answer/
{
  "query": "Explain Dow Theory"
}
```

---

## 🏁 Current Status — Phase 1 (Retrieval Pipeline Implemented)

### 🔹 Advanced Retrieval Pipeline

The system now implements a multi-stage RAG retrieval pipeline:

1. Query processing:
   - Query rewriting (improves clarity for vague inputs)
   - Query embedding (OpenAI)

2. Hybrid retrieval:
   - Vector similarity (pgvector)
   - Keyword-based search (PostgreSQL full-text search)
   - Fusion using Reciprocal Rank Fusion (RRF)

3. Chunk reranking:
   - LLM-based reranking assigns structured relevance scores to each chunk, enabling stable ranking instead of format-dependent selection

4. Context compression:
   - Heuristic sentence/window-based compression
   - Reduces token usage before LLM call

---

### 🔹 Observed Behavior (Early Evaluation)

With a limited dataset, the system shows:

**Strengths:**
- Cleaner and more structured answers
- Reduced redundancy in responses
- Improved handling of layered technical topics (e.g., virtualization)

**Limitations:**
- Retrieval diversity is limited due to small document base
- Compression may drop low-frequency but important concepts
- Query rewriting can over-constrain broad queries (e.g., forcing definition-style answers)
- System may favor explanatory sentences over structural or analytical content (e.g., definitions vs models)
- Improvements are inconsistent across queries (data-dependent behavior)

---

### 🔹 Key Insight

The system is currently:

> A strong retrieval + summarization pipeline, limited primarily by dataset size rather than architecture.

### 🔹 RAG-based Answer Generation

- Uses `gpt-4o-mini`
- Takes compressed + reranked context
- Returns:
  - Final answer
  - Source references (with hover preview)

### 🔹 Document Readiness

- A document becomes searchable only after embeddings are generated
- Summaries may appear before search is available
- This is due to asynchronous processing

The system supports:

- Full async ingestion pipeline
- Vector embeddings (pgvector)
- Hybrid retrieval (vector + keyword)
- Chunk reranking
- Context compression
- RAG-based answering
- Source explainability (hover preview)
- Dockerized setup (WSL)

---

### ⚠️ Known Limitations

- Small document dataset limits retrieval diversity
- No automated evaluation pipeline (manual analysis used)
- Heuristic compression may trade completeness for clarity
- Query rewriting may narrow query intent in some cases
- Chunking is still fixed-size (not semantic)

These limitations are expected to improve in future phases with:
- larger and more diverse datasets
- improved evaluation and feedback loops

### 📊 Evaluation Approach (Current)

The system is evaluated using:

- Query-by-query comparison of responses
- Analysis of:
  - information coverage
  - redundancy
  - clarity vs completeness tradeoffs
- Logging of:
  - token usage (before/after compression)
  - retrieval metrics
  - selected chunk sources

This is currently manual and will be replaced with automated evaluation in future phases.

### Next Steps

#### Core System Improvements

- Expand dataset with diverse document types and topics
- Build automated evaluation pipeline for retrieval and answer quality
- Improve chunking strategy (semantic chunking)
- Introduce feedback loop for reranking and compression tuning

#### Product & Platform Enhancements

- AWS S3 storage for uploaded files
- OCR support for handwritten and scanned documents
- Production deployment (Gunicorn + Nginx)
- API rate limiting and API key pooling

---

# ⭐ Author
**Shubhangi Singh**  
Backend Developer | Django | Python | AI Integrations