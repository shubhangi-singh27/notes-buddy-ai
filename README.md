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

### 🔹 Hybrid Search (Phase 1)
- Combines:
  - Vector similarity (pgvector)
  - Keyword-based matching (BM25-style / PostgreSQL search)
- Improves retrieval for:
  - Exact terms
  - Definitions
  - Acronyms

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

## 🏁 Current Status — Phase 1 (Feature Complete, Evaluation Pending)

### 🔹 Advanced Retrieval Pipeline (Phase 1)

The system now uses a multi-step retrieval pipeline:

1. Query embedding (OpenAI)
2. Hybrid retrieval:
   - Vector similarity (pgvector)
   - Keyword-based matching (PostgreSQL search)
3. Chunk reranking:
   - Improves relevance ordering of retrieved chunks
4. Context compression:
   - Reduces token usage before sending to LLM

Intended improvements:

- Better answer accuracy
- Lower token usage
- Improved handling of exact-match queries (formulas, acronyms)

Note: These improvements are not yet fully benchmarked due to limited dataset size.

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

### ⚠️ Known Gaps

- Retrieval quality not yet benchmarked
- No offline evaluation pipeline
- Chunking still fixed-size (not semantic)
- Large document ingestion can timeout

### Next steps include:

- AWS S3 storage for uploaded files  
- OCR for handwriting  
- Production deployment (Gunicorn + Nginx)
- API rate limiting and API key pooling

---

# ⭐ Author
**Shubhangi Singh**  
Backend Developer | Django | Python | AI Integrations