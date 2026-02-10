# ContextSafe - Rollback & Recovery Procedures

This guide provides step-by-step procedures for rolling back deployments and recovering from failures.

## Table of Contents

1. [Version Tracking](#version-tracking)
2. [Rollback Scenarios](#rollback-scenarios)
3. [Database Rollback](#database-rollback)
4. [Container Rollback](#container-rollback)
5. [Data Recovery](#data-recovery)
6. [Troubleshooting](#troubleshooting)

---

## Version Tracking

### Container Image Tagging

All Docker images are tagged with version and git commit SHA:

```bash
# Image naming convention
contextsafe/api:0.1.0
contextsafe/api:0.1.0-abc1234
contextsafe/api:latest

# View current running version
docker inspect contextsafe-api | jq '.[0].Config.Labels.version'

# List all available versions
docker images contextsafe/api --format "table {{.Tag}}\t{{.CreatedAt}}"
```

### Deployment History Log

Maintain a deployment log in `deployments/history.log`:

```bash
# Format: DATE | VERSION | GIT_SHA | DEPLOYED_BY | STATUS
2024-01-11 10:30:00 | 0.1.0 | abc1234 | admin | SUCCESS
2024-01-10 15:20:00 | 0.0.9 | def5678 | admin | SUCCESS
2024-01-09 09:00:00 | 0.0.8 | ghi9012 | admin | ROLLED_BACK
```

### Database Migration Tracking

```bash
# View current database version
docker exec contextsafe-api alembic current

# View migration history
docker exec contextsafe-api alembic history
```

---

## Rollback Scenarios

### Scenario 1: Application Crash After Deployment

**Symptoms:**
- API returns 500 errors
- Health check fails
- Container restarts continuously

**Rollback Strategy:** Container rollback to previous version

**Procedure:** See [Container Rollback](#container-rollback)

---

### Scenario 2: Database Corruption

**Symptoms:**
- Database locked errors
- Data inconsistencies
- SQLite integrity check failures

**Rollback Strategy:** Restore from backup

**Procedure:** See [Database Restore from Backup](#database-restore-from-backup)

---

### Scenario 3: Bad Migration

**Symptoms:**
- Application fails to start after migration
- "Column not found" errors
- Data loss in specific tables

**Rollback Strategy:** Downgrade database migration

**Procedure:** See [Database Migration Rollback](#database-migration-rollback)

---

### Scenario 4: Configuration Error

**Symptoms:**
- LLM model not loading
- External service connections failing
- Permission errors

**Rollback Strategy:** Restore previous `.env` configuration

**Procedure:** See [Configuration Rollback](#configuration-rollback)

---

## Database Rollback

### Database Migration Rollback

#### 1. Identify Current Migration

```bash
# Show current migration
docker exec contextsafe-api alembic current

# Example output:
# abc123 (head)
```

#### 2. View Migration History

```bash
# Show last 5 migrations
docker exec contextsafe-api alembic history -n 5

# Example output:
# abc123 -> def456 (head), add_glossary_table
# ghi789 -> abc123, add_document_status
# jkl012 -> ghi789, initial_schema
```

#### 3. Downgrade Migration

```bash
# Stop the API (to prevent concurrent writes)
docker compose -f docker/docker-compose.yml stop api

# Downgrade to previous version
docker compose -f docker/docker-compose.yml run --rm api alembic downgrade -1

# Or downgrade to specific revision
docker compose -f docker/docker-compose.yml run --rm api alembic downgrade abc123

# Verify downgrade
docker compose -f docker/docker-compose.yml run --rm api alembic current

# Restart API
docker compose -f docker/docker-compose.yml start api
```

#### 4. Verify Application

```bash
# Check health
curl http://localhost:8000/health

# Check logs
docker compose -f docker/docker-compose.yml logs -f api
```

---

### Database Restore from Backup

#### 1. Stop the Application

```bash
# Stop all services
docker compose -f docker/docker-compose.yml down

# This ensures no writes during restore
```

#### 2. Locate Backup

```bash
# List available backups
ls -lh /backups/contextsafe/

# Example output:
# -rw-r--r-- 1 root root 45M Jan 11 02:00 contextsafe-20240111-020000.db
# -rw-r--r-- 1 root root 44M Jan 10 02:00 contextsafe-20240110-020000.db
# -rw-r--r-- 1 root root 43M Jan 09 02:00 contextsafe-20240109-020000.db

# Choose the backup to restore (e.g., yesterday's backup)
BACKUP_FILE=/backups/contextsafe/contextsafe-20240110-020000.db
```

#### 3. Verify Backup Integrity

```bash
# If backup is encrypted, decrypt first
gpg --decrypt ${BACKUP_FILE}.gpg > ${BACKUP_FILE}

# Check SQLite integrity
sqlite3 ${BACKUP_FILE} "PRAGMA integrity_check;"

# Expected output: ok
```

#### 4. Restore Database

```bash
# Backup current database (in case rollback fails)
docker cp contextsafe-api:/app/data/contextsafe.db /tmp/contextsafe-current-$(date +%Y%m%d).db

# Copy backup into container
docker cp ${BACKUP_FILE} contextsafe-api:/app/data/contextsafe.db

# Set correct permissions
docker exec contextsafe-api chown contextsafe:contextsafe /app/data/contextsafe.db
docker exec contextsafe-api chmod 600 /app/data/contextsafe.db
```

#### 5. Start and Verify

```bash
# Start services
docker compose -f docker/docker-compose.yml up -d

# Wait for health check
sleep 10

# Verify health
curl http://localhost:8000/health

# Verify data (example: check project count)
curl http://localhost:8000/api/v1/projects | jq '.total'
```

#### 6. If Restore Fails

```bash
# Stop services
docker compose -f docker/docker-compose.yml down

# Restore the "current" backup
docker cp /tmp/contextsafe-current-$(date +%Y%m%d).db contextsafe-api:/app/data/contextsafe.db

# Restart
docker compose -f docker/docker-compose.yml up -d
```

---

## Container Rollback

### Rollback to Previous Image

#### 1. Identify Current Version

```bash
# Check running container image
docker inspect contextsafe-api --format='{{.Config.Image}}'

# Example output: contextsafe/api:0.1.0-abc1234
```

#### 2. Identify Previous Version

```bash
# List deployment history
cat deployments/history.log | tail -5

# Or list Docker images
docker images contextsafe/api
```

#### 3. Update docker-compose.yml

```bash
# Edit docker-compose.yml
nano docker/docker-compose.yml

# Change image version:
services:
  api:
    image: contextsafe/api:0.0.9-def5678  # Previous version
```

#### 4. Deploy Previous Version

```bash
# Pull previous image (if not cached)
docker pull contextsafe/api:0.0.9-def5678

# Stop current containers
docker compose -f docker/docker-compose.yml down

# Start with previous version
docker compose -f docker/docker-compose.yml up -d

# Verify
docker ps | grep contextsafe-api
```

#### 5. Monitor Logs

```bash
# Watch logs for errors
docker compose -f docker/docker-compose.yml logs -f api

# Check health
curl http://localhost:8000/health
```

---

### Quick Rollback Script

Save this as `scripts/rollback.sh`:

```bash
#!/bin/bash
set -e

# Usage: ./rollback.sh 0.0.9-def5678

TARGET_VERSION=${1}

if [ -z "$TARGET_VERSION" ]; then
  echo "Usage: $0 <version>"
  echo "Example: $0 0.0.9-def5678"
  exit 1
fi

echo "🔄 Rolling back to version: ${TARGET_VERSION}"

# Backup current database
echo "📦 Backing up current database..."
docker cp contextsafe-api:/app/data/contextsafe.db /tmp/contextsafe-pre-rollback-$(date +%Y%m%d-%H%M%S).db

# Stop services
echo "🛑 Stopping services..."
docker compose -f docker/docker-compose.yml down

# Update image version
echo "🏷️  Updating image version..."
sed -i "s|image: contextsafe/api:.*|image: contextsafe/api:${TARGET_VERSION}|" docker/docker-compose.yml

# Start services
echo "🚀 Starting services with version ${TARGET_VERSION}..."
docker compose -f docker/docker-compose.yml up -d

# Wait for health check
echo "⏳ Waiting for health check..."
sleep 15

# Verify
if curl -sf http://localhost:8000/health > /dev/null; then
  echo "✅ Rollback successful! Version ${TARGET_VERSION} is healthy."
  echo "$(date +%Y-%m-%d\ %H:%M:%S) | ${TARGET_VERSION} | ROLLBACK | $(whoami) | SUCCESS" >> deployments/history.log
else
  echo "❌ Rollback failed! Health check did not pass."
  echo "$(date +%Y-%m-%d\ %H:%M:%S) | ${TARGET_VERSION} | ROLLBACK | $(whoami) | FAILED" >> deployments/history.log
  exit 1
fi
```

**Usage:**

```bash
chmod +x scripts/rollback.sh
./scripts/rollback.sh 0.0.9-def5678
```

---

## Data Recovery

### Recover Deleted Project

If a project was accidentally deleted:

#### 1. Check Database Backup

```bash
# Restore database to temporary location
cp /backups/contextsafe/contextsafe-20240110-020000.db /tmp/restore.db

# Query deleted project
sqlite3 /tmp/restore.db "SELECT * FROM projects WHERE id='<project_id>';"
```

#### 2. Export Project Data

```bash
# Export project and related documents
sqlite3 /tmp/restore.db <<EOF
.mode csv
.headers on
.output /tmp/project_export.csv
SELECT * FROM projects WHERE id='<project_id>';
.output /tmp/documents_export.csv
SELECT * FROM documents WHERE project_id='<project_id>';
.output /tmp/glossary_export.csv
SELECT * FROM glossary_entries WHERE project_id='<project_id>';
EOF
```

#### 3. Import into Current Database

```bash
# Import via API or direct database insert
docker exec -i contextsafe-api sqlite3 /app/data/contextsafe.db <<EOF
BEGIN TRANSACTION;
-- Insert project
INSERT INTO projects VALUES (...);
-- Insert documents
INSERT INTO documents VALUES (...);
-- Insert glossary entries
INSERT INTO glossary_entries VALUES (...);
COMMIT;
EOF
```

---

### Recover Corrupted Document

If a document file is corrupted:

#### 1. Locate Document in Backup

```bash
# Documents are stored in /app/data/documents/<project_id>/<document_id>
BACKUP_DIR=/backups/contextsafe/data-20240110

# Find document
find ${BACKUP_DIR} -name "<document_id>.*"
```

#### 2. Restore Document File

```bash
# Copy from backup
docker cp ${BACKUP_DIR}/documents/<project_id>/<document_id>.pdf \
  contextsafe-api:/app/data/documents/<project_id>/<document_id>.pdf

# Set permissions
docker exec contextsafe-api chown contextsafe:contextsafe \
  /app/data/documents/<project_id>/<document_id>.pdf
```

---

### Configuration Rollback

If a configuration change caused issues:

#### 1. Restore Previous .env

```bash
# Backup current config
cp .env.production .env.production.backup-$(date +%Y%m%d)

# Restore from version control (if tracked)
git checkout HEAD~1 -- .env.production

# Or restore from manual backup
cp .env.production.20240110 .env.production
```

#### 2. Restart Services

```bash
# Reload configuration
docker compose -f docker/docker-compose.yml down
docker compose -f docker/docker-compose.yml up -d --force-recreate
```

#### 3. Verify

```bash
# Check environment variables are loaded
docker exec contextsafe-api env | grep -E "LLM_|DATABASE_"

# Check health
curl http://localhost:8000/health
```

---

## Troubleshooting

### Issue: Rollback Stuck on Health Check

**Symptoms:**
- Container starts but health check never passes
- Logs show "Waiting for health check..."

**Solution:**

```bash
# Check detailed logs
docker compose -f docker/docker-compose.yml logs api | tail -100

# Common causes:
# 1. Database file locked
#    → Stop all containers, restart
# 2. LLM model missing
#    → Verify LLM_MODEL_PATH and file exists
# 3. Port conflict
#    → Check: sudo netstat -tlnp | grep 8000
```

---

### Issue: Database Migration Downgrade Fails

**Symptoms:**
- Error: "Can't downgrade, would delete data"

**Solution:**

```bash
# Manual downgrade requires backup first
docker exec contextsafe-api sqlite3 /app/data/contextsafe.db \
  ".dump <table_name>" > /tmp/table_backup.sql

# Drop table manually
docker exec contextsafe-api sqlite3 /app/data/contextsafe.db \
  "DROP TABLE <table_name>;"

# Re-run downgrade
docker exec contextsafe-api alembic downgrade -1

# If needed, restore data
docker exec -i contextsafe-api sqlite3 /app/data/contextsafe.db < /tmp/table_backup.sql
```

---

### Issue: Restored Database Shows Wrong Data

**Symptoms:**
- Old data visible after restore
- Recent projects missing

**Solution:**

```bash
# Verify correct backup was used
docker exec contextsafe-api sqlite3 /app/data/contextsafe.db \
  "SELECT created_at FROM projects ORDER BY created_at DESC LIMIT 5;"

# If incorrect, restore again from correct backup
# (See Database Restore from Backup section)

# Check file timestamp
docker exec contextsafe-api stat /app/data/contextsafe.db
```

---

### Issue: Container Won't Start After Rollback

**Symptoms:**
- Container exits immediately
- Error: "No such file or directory"

**Solution:**

```bash
# Check container logs
docker logs contextsafe-api --tail 50

# Common causes:
# 1. Volume mount missing
docker volume ls | grep contextsafe

# 2. Permissions wrong
docker exec contextsafe-api ls -la /app/data

# 3. Missing dependency (model, config)
docker exec contextsafe-api ls -la /app/models
```

---

## Rollback Checklist

Before performing a rollback:

- [ ] Identify the target version to rollback to
- [ ] Backup current database (`docker cp ...`)
- [ ] Backup current configuration (`.env.production`)
- [ ] Document the reason for rollback
- [ ] Notify stakeholders (if production)
- [ ] Stop incoming traffic (if using load balancer)
- [ ] Perform rollback steps
- [ ] Verify health check passes
- [ ] Verify sample API request works
- [ ] Check logs for errors
- [ ] Restore traffic
- [ ] Update deployment history log
- [ ] Investigate root cause

---

## Emergency Contacts

In case of critical failures:

- **On-Call Engineer:** [contact info]
- **Database Admin:** [contact info]
- **Infrastructure Team:** [contact info]

## Escalation Path

1. Attempt automated rollback (`scripts/rollback.sh`)
2. If failed, attempt manual rollback (this guide)
3. If still failed, restore from backup
4. If data loss, contact Database Admin
5. If infrastructure issue, contact Infrastructure Team

