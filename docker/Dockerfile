# ContextSafe - Multi-stage Dockerfile
# ============================================

# ============================================
# STAGE 1: Builder
# ============================================
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.1

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Export requirements (without dev dependencies)
RUN poetry export -f requirements.txt --without-hashes --only main > requirements.txt

# ============================================
# STAGE 2: Runtime
# ============================================
FROM python:3.11-slim AS runtime

# Labels
LABEL maintainer="ContextSafe Team" \
      version="0.1.0" \
      description="ContextSafe - Document Anonymization System"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    APP_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # OCR support
    tesseract-ocr \
    tesseract-ocr-spa \
    tesseract-ocr-eng \
    # PDF processing
    libpoppler-cpp-dev \
    poppler-utils \
    # Image processing
    libgl1-mesa-glx \
    libglib2.0-0 \
    # Health check
    curl \
    # Clean up
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 contextsafe \
    && useradd --uid 1000 --gid contextsafe --shell /bin/bash --create-home contextsafe

# Set work directory
WORKDIR /app

# Copy requirements from builder
COPY --from=builder /app/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download es_core_news_lg

# Copy application code
COPY --chown=contextsafe:contextsafe src/ ./src/

# Create directories for data and models
RUN mkdir -p /app/data /app/models /app/logs \
    && chown -R contextsafe:contextsafe /app

# Switch to non-root user
USER contextsafe

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -sf http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "contextsafe.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
