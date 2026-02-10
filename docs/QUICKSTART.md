# ContextSafe - Quick Start Guide

This guide will help you get ContextSafe up and running in under 10 minutes.

## Prerequisites

Before you begin, ensure you have the following installed:

### Required

- **Python 3.11 or higher**
  ```bash
  python --version  # Should show 3.11.x or higher
  ```

- **Poetry 1.7+** (Python dependency manager)
  ```bash
  # Install via pip
  pip install poetry

  # Or via official installer
  curl -sSL https://install.python-poetry.org | python3 -
  ```

- **Tesseract OCR** (for image processing)
  ```bash
  # Ubuntu/Debian
  sudo apt-get update
  sudo apt-get install tesseract-ocr tesseract-ocr-spa

  # macOS
  brew install tesseract tesseract-lang

  # Verify installation
  tesseract --version
  ```

### Optional (Recommended)

- **Docker & Docker Compose** (for containerized deployment)
  ```bash
  docker --version
  docker compose version
  ```

- **GPU with CUDA support** (for faster LLM inference)
  - NVIDIA GPU with CUDA 11.8+ drivers
  - Significantly improves processing speed

## Installation

### Option 1: Local Development Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/AlexAlves87/ContextSafe.git
cd contextsafe
```

#### 2. Install Dependencies

```bash
# Install Python dependencies
make install-dev

# Download spaCy Spanish model
poetry run python -m spacy download es_core_news_lg

# Install frontend dependencies (if using UI)
make install-frontend
```

#### 3. Download LLM Model

Download a GGUF quantized model for local LLM inference:

```bash
# Create models directory
mkdir -p models

# Download Mistral-7B-v0.3 (Q4_K_M quantization, ~4GB)
wget https://huggingface.co/TheBloke/Mistral-7B-v0.3-GGUF/resolve/main/mistral-7b-v0.3.Q4_K_M.gguf \
  -O models/mistral-7b-v0.3.Q4_K_M.gguf
```

**Alternative models:**
- **Smaller (2GB):** `mistral-7b-v0.3.Q2_K.gguf` - Faster but less accurate
- **Larger (7GB):** `mistral-7b-v0.3.Q5_K_M.gguf` - Slower but more accurate

#### 4. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration (use your favorite editor)
nano .env
```

**Minimal required configuration:**

```bash
# .env
DATABASE_KEY=your_secure_32_char_encryption_key_here
LLM_MODEL_PATH=models/mistral-7b-v0.3.Q4_K_M.gguf

# Optional: Enable GPU acceleration (if available)
LLM_N_GPU_LAYERS=35  # Adjust based on your GPU VRAM
```

#### 5. Start the Application

```bash
# Start backend API (port 8000)
make dev

# In another terminal: Start frontend (port 5173)
make dev-frontend
```

The application will be available at:
- **API:** http://localhost:8000
- **Frontend:** http://localhost:5173
- **API Docs:** http://localhost:8000/docs

### Option 2: Docker Setup

#### 1. Clone and Configure

```bash
git clone https://github.com/AlexAlves87/ContextSafe.git
cd contextsafe

# Copy and edit environment file
cp .env.example .env
nano .env
```

#### 2. Download LLM Model

```bash
mkdir -p models
wget https://huggingface.co/TheBloke/Mistral-7B-v0.3-GGUF/resolve/main/mistral-7b-v0.3.Q4_K_M.gguf \
  -O models/mistral-7b-v0.3.Q4_K_M.gguf
```

#### 3. Build and Start

```bash
# Build images
make docker-build

# Start all services (API, Ollama, Frontend)
make docker-up

# View logs
make docker-logs
```

The application will be available at:
- **API:** http://localhost:8000
- **Frontend:** http://localhost:5173

To stop:

```bash
make docker-down
```

## First Document Processing

### Using the API (CLI)

#### 1. Create a Project

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Project",
    "description": "My first anonymization project",
    "default_anonymization_level": "INTERMEDIATE"
  }'
```

**Response:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "Test Project",
  "description": "My first anonymization project",
  "default_anonymization_level": "INTERMEDIATE",
  "created_at": "2024-01-11T10:30:00Z",
  "document_count": 0
}
```

Save the `id` for the next steps.

#### 2. Upload a Document

```bash
PROJECT_ID="a1b2c3d4-e5f6-7890-abcd-ef1234567890"

curl -X POST http://localhost:8000/api/v1/projects/${PROJECT_ID}/documents \
  -F "file=@sample-document.pdf"
```

**Response:**
```json
{
  "id": "doc-123",
  "project_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "sample-document.pdf",
  "format": "PDF",
  "status": "UPLOADED",
  "uploaded_at": "2024-01-11T10:31:00Z"
}
```

#### 3. Detect PII

```bash
DOCUMENT_ID="doc-123"

curl -X POST http://localhost:8000/api/v1/projects/${PROJECT_ID}/documents/${DOCUMENT_ID}/detect
```

This process may take 10-60 seconds depending on document size and hardware.

**Response:**
```json
{
  "document_id": "doc-123",
  "status": "DETECTION_COMPLETE",
  "entities_detected": 42,
  "categories": {
    "FULL_NAME": 12,
    "EMAIL": 8,
    "PHONE": 5,
    "DNI": 3,
    ...
  }
}
```

#### 4. Generate Anonymized Document

```bash
curl -X POST http://localhost:8000/api/v1/projects/${PROJECT_ID}/documents/${DOCUMENT_ID}/anonymize \
  -o anonymized-document.pdf
```

The anonymized PDF will be saved to `anonymized-document.pdf`.

#### 5. View Glossary (Alias Mapping)

```bash
curl http://localhost:8000/api/v1/projects/${PROJECT_ID}/glossary
```

**Response:**
```json
{
  "project_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "entries": [
    {
      "original_value": "Juan Perez",
      "alias": "PERSONA-001",
      "category": "FULL_NAME",
      "confidence": 0.95
    },
    {
      "original_value": "juan.perez@example.com",
      "alias": "EMAIL-001",
      "category": "EMAIL",
      "confidence": 0.99
    }
  ]
}
```

### Using the Web UI

1. **Open Browser:** http://localhost:5173

2. **Create Project:**
   - Click "New Project"
   - Enter name and description
   - Select anonymization level (BASIC / INTERMEDIATE / ADVANCED)
   - Click "Create"

3. **Upload Document:**
   - Select your project
   - Click "Upload Document"
   - Choose PDF, DOCX, or image file
   - Wait for upload to complete

4. **Process Document:**
   - Click "Detect PII" button
   - Wait for detection to complete (progress bar shown)
   - Review detected entities in table

5. **Generate Anonymized Version:**
   - Click "Anonymize Document"
   - Download the anonymized file
   - View glossary in the "Glossary" tab

## Verification

### Check API Health

```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "components": {
    "database": "ok",
    "llm": "ok",
    "spacy": "ok"
  }
}
```

### Check GPU Availability (Optional)

```bash
# If using local setup
poetry run python -c "import llama_cpp; print(llama_cpp.llama_supports_gpu_offload())"

# If using Docker
docker exec contextsafe-api python -c "import llama_cpp; print(llama_cpp.llama_supports_gpu_offload())"
```

## Common Issues

### "spaCy model not found"

```bash
# Download the Spanish model
poetry run python -m spacy download es_core_news_lg
```

### "LLM model file not found"

- Verify the model path in `.env` matches the actual file location
- Ensure the model file was downloaded completely (~4GB for Q4_K_M)

### "Tesseract not found"

```bash
# Install Tesseract OCR
sudo apt-get install tesseract-ocr tesseract-ocr-spa  # Linux
brew install tesseract tesseract-lang                # macOS
```

### "Out of memory" during LLM inference

- Reduce `LLM_N_GPU_LAYERS` in `.env` (or set to 0 for CPU-only)
- Use a smaller quantized model (Q2_K instead of Q4_K_M)
- Reduce `LLM_N_CTX` (context window size)

### Port already in use

```bash
# Change ports in .env
API_PORT=8001
FRONTEND_PORT=5174
```

## Next Steps

- **Read DEPLOYMENT.md:** Learn how to deploy to production
- **Read API.md:** Explore all available API endpoints
- **Read TESTING.md:** Run tests and contribute to the project
- **Check logs:** `tail -f logs/contextsafe.log`

## Support

- **Documentation:** `/docs` directory
- **API Reference:** http://localhost:8000/docs
- **Issues:** https://github.com/AlexAlves87/ContextSafe/issues

