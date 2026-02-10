# ContextSafe - Production Deployment Guide

This guide covers deploying ContextSafe to production environments with security, scalability, and reliability best practices.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Deployment](#docker-deployment)
3. [Environment Configuration](#environment-configuration)
4. [Database Setup](#database-setup)
5. [LLM Configuration](#llm-configuration)
6. [Security Hardening](#security-hardening)
7. [Monitoring & Observability](#monitoring--observability)
8. [Health Checks](#health-checks)
9. [Scaling Considerations](#scaling-considerations)
10. [Backup & Recovery](#backup--recovery)

---

## Prerequisites

### Infrastructure Requirements

**Minimum (Small Workloads - <10 documents/day):**
- CPU: 4 cores
- RAM: 8GB
- Storage: 50GB SSD
- Network: 100 Mbps

**Recommended (Production - 100+ documents/day):**
- CPU: 8 cores (16 threads)
- RAM: 16GB
- GPU: NVIDIA with 8GB+ VRAM (optional but recommended)
- Storage: 200GB SSD (NVMe preferred)
- Network: 1 Gbps

**Storage Breakdown:**
- OS: ~10GB
- Application: ~5GB
- LLM Models: ~10GB (Mistral-7B Q4_K_M + spaCy)
- Database: ~50GB (grows with documents)
- Logs: ~5GB (rotated)
- Temporary files: ~20GB

### Software Requirements

- Docker Engine 24.0+
- Docker Compose 2.20+
- Linux kernel 5.10+ (for optimal container performance)
- (Optional) NVIDIA Container Toolkit (for GPU support)

### Network Requirements

- **Outbound:** HTTPS (443) for model downloads during setup
- **Inbound:**
  - 8000/tcp (API)
  - 5173/tcp (Frontend)
  - 9090/tcp (Prometheus metrics)

---

## Docker Deployment

### 1. Prepare the Server

```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt-get install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version
```

### 2. Clone and Configure

```bash
# Clone repository
git clone https://github.com/AlexAlves87/ContextSafe.git
cd contextsafe

# Create production environment file
cp .env.example .env.production

# Edit configuration (see Environment Configuration section)
nano .env.production
```

### 3. Download LLM Models

```bash
# Create models directory
mkdir -p models

# Download Mistral-7B-v0.3 (Q4_K_M - 4GB)
wget https://huggingface.co/TheBloke/Mistral-7B-v0.3-GGUF/resolve/main/mistral-7b-v0.3.Q4_K_M.gguf \
  -O models/mistral-7b-v0.3.Q4_K_M.gguf

# Verify download
sha256sum models/mistral-7b-v0.3.Q4_K_M.gguf
```

### 4. Build and Deploy

```bash
# Build Docker images
docker compose -f docker/docker-compose.yml --env-file .env.production build

# Start services in detached mode
docker compose -f docker/docker-compose.yml --env-file .env.production up -d

# Verify all services are running
docker compose -f docker/docker-compose.yml ps
```

**Expected output:**
```
NAME                    STATUS    PORTS
contextsafe-api         healthy   0.0.0.0:8000->8000/tcp
contextsafe-frontend    healthy   0.0.0.0:5173->80/tcp
contextsafe-ollama      healthy   0.0.0.0:11434->11434/tcp
```

### 5. Verify Deployment

```bash
# Check API health
curl http://localhost:8000/health

# Check logs
docker compose -f docker/docker-compose.yml logs -f api

# Stop services (when needed)
docker compose -f docker/docker-compose.yml down
```

---

## Environment Configuration

### Critical Variables

Create `.env.production` with the following configuration:

```bash
# ============================================
# APPLICATION
# ============================================
APP_ENV=production
LOG_LEVEL=warning
DEBUG=false

# ============================================
# API SERVER
# ============================================
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# ============================================
# DATABASE (SQLite + SQLCipher)
# ============================================
DATABASE_URL=sqlite+aiosqlite:///data/contextsafe.db
DATABASE_KEY=<GENERATE_SECURE_32_CHAR_KEY>

# ============================================
# LLM CONFIGURATION
# ============================================
LLM_MODEL_PATH=models/mistral-7b-v0.3.Q4_K_M.gguf
LLM_N_GPU_LAYERS=35           # Set to 0 if no GPU
LLM_N_CTX=4096                # Context window size
LLM_TEMPERATURE=0.7           # Creativity (0.0-1.0)
LLM_MAX_TOKENS=512            # Max tokens per request

# ============================================
# NLP / NER (spaCy)
# ============================================
SPACY_MODEL=es_core_news_lg
NER_CONFIDENCE_THRESHOLD=0.75  # Higher = fewer false positives

# ============================================
# OCR (Tesseract)
# ============================================
TESSERACT_LANG=spa
TESSERACT_PATH=/usr/bin/tesseract

# ============================================
# OBSERVABILITY
# ============================================
METRICS_ENABLED=true
METRICS_PORT=9090
TRACES_ENABLED=false

# ============================================
# SECURITY
# ============================================
# JWT secret (if implementing authentication)
# JWT_SECRET_KEY=<GENERATE_SECURE_SECRET>
# JWT_ALGORITHM=HS256
# JWT_EXPIRATION_HOURS=24
```

### Generate Secure Keys

```bash
# Generate DATABASE_KEY (32 characters)
openssl rand -hex 16

# Generate JWT_SECRET_KEY (64 characters)
openssl rand -hex 32
```

**CRITICAL:** Never commit `.env.production` to version control. Use secrets management.

---

## Database Setup

### SQLite Location and Encryption

ContextSafe uses **SQLite with SQLCipher** for encryption at rest.

#### File Location

```bash
# Database file location (inside Docker volume)
/app/data/contextsafe.db

# Map to host filesystem (optional, for backups)
docker compose -f docker/docker-compose.yml down
nano docker/docker-compose.yml

# Add volume mapping in 'api' service:
volumes:
  - ./db-data:/app/data  # Host directory for database
```

#### Encryption Key Management

**Option 1: Environment Variable (Basic)**

```bash
# In .env.production
DATABASE_KEY=your_32_char_encryption_key_here
```

**Option 2: Docker Secrets (Recommended)**

```yaml
# docker/docker-compose.yml
secrets:
  db_encryption_key:
    file: ./secrets/db_key.txt

services:
  api:
    secrets:
      - db_encryption_key
    environment:
      DATABASE_KEY_FILE: /run/secrets/db_encryption_key
```

```bash
# Create secret
mkdir -p secrets
echo "your_32_char_encryption_key_here" > secrets/db_key.txt
chmod 600 secrets/db_key.txt
```

#### Database Initialization

On first run, the database will be automatically initialized:

```bash
# View initialization logs
docker compose logs api | grep -i "database\|migration"
```

---

## LLM Configuration

### Model Selection

| Model | Size | RAM | GPU VRAM | Speed | Accuracy |
|-------|------|-----|----------|-------|----------|
| Q2_K | 2GB | 4GB | 2GB | Fast | Good |
| Q4_K_M | 4GB | 8GB | 4GB | Medium | Better |
| Q5_K_M | 7GB | 12GB | 6GB | Slow | Best |

**Recommendation:** Q4_K_M for balanced performance/accuracy.

### GPU Acceleration

#### Enable NVIDIA GPU Support

```bash
# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

#### Update docker-compose.yml

```yaml
services:
  api:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

#### Configure GPU Layers

```bash
# In .env.production
LLM_N_GPU_LAYERS=35  # Adjust based on GPU VRAM

# Mistral-7B layer distribution:
# GPU: 8GB VRAM  → LLM_N_GPU_LAYERS=35 (full offload)
# GPU: 6GB VRAM  → LLM_N_GPU_LAYERS=28
# GPU: 4GB VRAM  → LLM_N_GPU_LAYERS=20
# No GPU        → LLM_N_GPU_LAYERS=0 (CPU only)
```

#### Verify GPU Usage

```bash
# Check GPU is detected
docker exec contextsafe-api nvidia-smi

# Monitor GPU usage during inference
watch -n 1 nvidia-smi
```

### Alternative: Ollama Backend

Instead of llama-cpp-python, you can use Ollama:

```bash
# In .env.production
USE_OLLAMA=true
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=mistral:7b

# Pull model into Ollama
docker exec contextsafe-ollama ollama pull mistral:7b
```

---

## Security Hardening

### 1. Network Security

#### Reverse Proxy (Nginx)

```nginx
# /etc/nginx/sites-available/contextsafe
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # API backend
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_read_timeout 86400;
    }

    # Frontend
    location / {
        proxy_pass http://localhost:5173;
        proxy_set_header Host $host;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
}
```

#### Firewall Rules

```bash
# Allow only necessary ports
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp   # HTTP (for Let's Encrypt)
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable

# Block direct access to Docker ports (only via nginx)
sudo iptables -A INPUT -p tcp --dport 8000 -s 127.0.0.1 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8000 -j DROP
```

### 2. Container Security

#### Run as Non-Root User

```dockerfile
# docker/Dockerfile
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 contextsafe
USER contextsafe

# ... rest of Dockerfile
```

#### Read-Only Filesystem

```yaml
# docker/docker-compose.yml
services:
  api:
    read_only: true
    tmpfs:
      - /tmp
      - /app/temp
```

### 3. Secrets Management

Use **Docker Secrets** or **HashiCorp Vault** instead of environment variables:

```yaml
# docker/docker-compose.yml
secrets:
  database_key:
    external: true
  jwt_secret:
    external: true

services:
  api:
    secrets:
      - database_key
      - jwt_secret
```

```bash
# Create secrets
echo "your_db_key" | docker secret create database_key -
echo "your_jwt_secret" | docker secret create jwt_secret -
```

---

## Monitoring & Observability

### Prometheus Metrics

ContextSafe exposes Prometheus metrics at `/metrics`:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'contextsafe'
    static_configs:
      - targets: ['localhost:9090']
```

**Available metrics:**
- `contextsafe_documents_processed_total` - Total documents processed
- `contextsafe_entities_detected_total` - Total PII entities detected
- `contextsafe_llm_inference_duration_seconds` - LLM inference latency
- `contextsafe_api_requests_total` - API request count by endpoint
- `contextsafe_api_request_duration_seconds` - API request latency

### Logging

Logs are written to Docker volumes:

```bash
# View real-time logs
docker compose -f docker/docker-compose.yml logs -f api

# Export logs to host
docker compose -f docker/docker-compose.yml logs api > logs/api-$(date +%Y%m%d).log
```

**Log rotation** is configured via `docker-compose.yml`:

```yaml
services:
  api:
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
        compress: "true"
```

### Structured Logging

All logs use **structured JSON format** (via structlog):

```json
{
  "timestamp": "2024-01-11T10:30:00.123Z",
  "level": "info",
  "event": "document_processed",
  "document_id": "doc-123",
  "entities_detected": 42,
  "duration_ms": 5432
}
```

---

## Health Checks

### Endpoint

```bash
GET /health
```

**Response (healthy):**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2024-01-11T10:30:00Z",
  "components": {
    "database": "ok",
    "llm": "ok",
    "spacy": "ok",
    "tesseract": "ok"
  }
}
```

**Response (unhealthy):**
```json
{
  "status": "unhealthy",
  "version": "0.1.0",
  "timestamp": "2024-01-11T10:30:00Z",
  "components": {
    "database": "ok",
    "llm": "error",
    "spacy": "ok",
    "tesseract": "ok"
  },
  "errors": [
    "LLM model file not found: models/mistral-7b-v0.3.Q4_K_M.gguf"
  ]
}
```

### Docker Health Checks

Configured in `docker-compose.yml`:

```yaml
healthcheck:
  test: ["CMD", "curl", "-sf", "http://localhost:8000/health"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 30s
```

### External Monitoring

Integrate with **UptimeRobot**, **Pingdom**, or **Datadog**:

```bash
# Monitor health endpoint
GET https://your-domain.com/health

# Alert if status != 200 or response contains "unhealthy"
```

---

## Scaling Considerations

### Horizontal Scaling (Multiple API Instances)

```yaml
# docker/docker-compose.yml
services:
  api:
    deploy:
      replicas: 3  # Run 3 instances
```

**Load Balancer (Nginx):**

```nginx
upstream contextsafe_api {
    least_conn;
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}

server {
    location /api {
        proxy_pass http://contextsafe_api;
    }
}
```

### Vertical Scaling (Resource Limits)

```yaml
# docker/docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 16G
        reservations:
          cpus: '2.0'
          memory: 8G
```

### Database Scaling

For high-volume workloads, consider migrating to PostgreSQL:

```bash
# In .env.production
DATABASE_URL=postgresql+asyncpg://user:pass@db-host:5432/contextsafe
DATABASE_ENCRYPTION=pgcrypto  # Use PostgreSQL native encryption
```

### Caching Strategy

Add Redis for caching frequently accessed data:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

```bash
# In .env.production
REDIS_URL=redis://redis:6379/0
CACHE_TTL=3600  # 1 hour
```

---

## Backup & Recovery

### Database Backup

```bash
# Automated daily backup script
#!/bin/bash
BACKUP_DIR=/backups/contextsafe
DATE=$(date +%Y%m%d-%H%M%S)

# Stop writes (optional, ensures consistency)
docker compose -f docker/docker-compose.yml exec api python -c "import signal, os; os.kill(1, signal.SIGUSR1)"

# Copy database file
docker cp contextsafe-api:/app/data/contextsafe.db ${BACKUP_DIR}/contextsafe-${DATE}.db

# Resume writes
docker compose -f docker/docker-compose.yml exec api python -c "import signal, os; os.kill(1, signal.SIGUSR2)"

# Encrypt backup
gpg --encrypt --recipient your@email.com ${BACKUP_DIR}/contextsafe-${DATE}.db

# Upload to S3/B2 (optional)
aws s3 cp ${BACKUP_DIR}/contextsafe-${DATE}.db.gpg s3://your-bucket/backups/

# Cleanup old backups (keep last 30 days)
find ${BACKUP_DIR} -name "contextsafe-*.db*" -mtime +30 -delete
```

### Model Backup

```bash
# Backup LLM models (one-time, models don't change)
tar -czf models-backup.tar.gz models/
aws s3 cp models-backup.tar.gz s3://your-bucket/models/
```

### Restore Procedure

See [ROLLBACK.md](./ROLLBACK.md) for detailed restore procedures.

---

## Troubleshooting

### High Memory Usage

```bash
# Check memory usage
docker stats contextsafe-api

# Reduce LLM context window
LLM_N_CTX=2048  # Instead of 4096

# Enable swap (if not already enabled)
sudo swapon --show
```

### Slow Inference

```bash
# Enable GPU offloading
LLM_N_GPU_LAYERS=35

# Use smaller model
LLM_MODEL_PATH=models/mistral-7b-v0.3.Q2_K.gguf

# Reduce batch size (if implemented)
LLM_BATCH_SIZE=128  # Instead of 512
```

### Container Crashes

```bash
# View crash logs
docker compose -f docker/docker-compose.yml logs --tail 100 api

# Check OOM killer
dmesg | grep -i "killed process"

# Increase memory limits
# (See Vertical Scaling section)
```

---

## Production Checklist

- [ ] Secure DATABASE_KEY generated and stored in secrets manager
- [ ] HTTPS enabled with valid SSL certificate
- [ ] Firewall configured (only ports 80, 443, 22 open)
- [ ] Reverse proxy (Nginx) configured
- [ ] Health checks configured and monitored
- [ ] Prometheus metrics exported
- [ ] Log rotation enabled
- [ ] Automated backups scheduled (daily)
- [ ] Backup restore tested
- [ ] GPU acceleration configured (if available)
- [ ] CORS origins restricted to production domains
- [ ] Debug mode disabled (DEBUG=false)
- [ ] Docker containers run as non-root user
- [ ] Secrets not committed to version control
- [ ] Monitoring alerts configured (disk space, memory, errors)

