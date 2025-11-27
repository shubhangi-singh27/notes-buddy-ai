# 🧠 Notes Buddy — AI-Powered Personal Knowledge Search

An AI-powered backend system that lets users upload notes (PDF, DOCX, TXT), automatically extract text, chunk it, embed it using OpenAI, store vectors in pgvector, and perform semantic search with GPT-powered answers.

This backend implements a full **RAG (Retrieval Augmented Generation)** pipeline using Django, Celery, Redis, PostgreSQL, and pgvector.

---

## 🚀 Features

### 🔹 File Upload System
- Supports PDF, DOCX, TXT
- Extracts text using PyPDF & python-docx
- Saves extracted text in filesystem

### 🔹 Text Processing Pipeline
- Cleans and chunks text  
- Stores chunks in PostgreSQL  
- Each chunk is linked to the document & user

### 🔹 Vector Embedding (OpenAI)
- Embeds all chunks using `text-embedding-3-small`
- Stores embeddings in **pgvector** column
- Search using `<=>` vector similarity operator

### 🔹 Semantic Search
- User asks a question
- System embeds the query
- Retrieves top relevant chunks
- Sends context to GPT (`gpt-4o-mini`)
- Returns final answer + source references

### 🔹 Asynchronous Processing
Powered by **Celery + Redis**:
- Document processing
- Chunk embedding
- Background task queue

### 🔹 Authentication
- Secure JWT authentication using SimpleJWT

---

## 🏗️ Tech Stack

- **Django 5**
- **Django Rest Framework**
- **PostgreSQL 16**
- **pgvector 0.5**
- **Redis 7 (WSL2)**
- **Celery 5**
- **OpenAI API**
- **PyPDF + python-docx**
- **WSL Ubuntu 24.04**

---

## 📁 Project Structure

```
notes_buddy/
├── documents/
├── search/
├── users/
├── notes_buddy/  # Django settings
└── manage.py
```

---

# ▶️ Project Setup

Follow these steps to run the project locally.

---

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/notes_buddy.git
cd notes_buddy

cp .env.example .env

uv sync

uv run python manage.py migrate

redis-server --port 6380

uv run celery -A notes_buddy worker --loglevel=info

uv run python manage.py runserver

```

Backend now runs at:

http://127.0.0.1:8000/

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

## 🏁 Current Status — MVP Completed
This backend currently supports:

- File upload  
- Text extraction  
- Chunking  
- Vector storage  
- Semantic search  
- GPT answering  
- Full async RAG pipeline  

Next steps include:

- React frontend  
- UI for uploaded documents 
- Summaries  
- OCR for handwriting  
- AWS S3 storage for uploaded files  
- Docker deployment  

---

# ⭐ Author
**Shubhangi Singh**  
Backend Developer | Django | Python | AI Integrations