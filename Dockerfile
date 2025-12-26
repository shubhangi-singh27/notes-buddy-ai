# Base image
FROM python:3.12-slim

# Prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first 
COPY pyproject.toml uv.lock ./

# Explicitly create venv
RUN uv venv .venv

# Tell uv EXACTLY where to install
ENV UV_PROJECT_ENV=/app/.venv

# Install dependencies into virtual environment
RUN uv sync --frozen

# Copy project files
COPY . .

ENV PATH="/app/.venv/bin:$PATH"

# Default command (overridden in docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

