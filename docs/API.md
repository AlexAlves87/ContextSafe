# ContextSafe - API Reference

Complete REST API documentation for ContextSafe v0.1.0.

## Table of Contents

1. [Base URL](#base-url)
2. [Authentication](#authentication)
3. [Error Handling](#error-handling)
4. [Projects](#projects)
5. [Documents](#documents)
6. [Detection](#detection)
7. [Anonymization](#anonymization)
8. [Glossary](#glossary)
9. [Export](#export)
10. [WebSocket](#websocket)
11. [Health & Metrics](#health--metrics)

---

## Base URL

```
http://localhost:8000/api/v1
```

**Production:**
```
https://your-domain.com/api/v1
```

---

## Authentication

**Current version (v0.1.0):** No authentication required (local deployment only).

**Future versions:** Will support JWT-based authentication:

```http
Authorization: Bearer <jwt_token>
```

---

## Error Handling

All errors follow **RFC 7807 Problem Details** format:

### Error Response Schema

```json
{
  "type": "/errors/<error-type>",
  "title": "Error Title",
  "status": 400,
  "detail": "Human-readable error description",
  "instance": "/api/v1/resource/123"
}
```

### Common Error Codes

| Status | Type | Description |
|--------|------|-------------|
| 400 | `/errors/validation-error` | Invalid request parameters |
| 404 | `/errors/not-found` | Resource not found |
| 409 | `/errors/conflict` | Resource conflict (duplicate, already exists) |
| 422 | `/errors/unprocessable` | Semantic error (e.g., document not ready) |
| 500 | `/errors/internal-error` | Internal server error |
| 502 | `/errors/external-service-error` | External service (LLM, OCR) failure |
| 503 | `/errors/service-unavailable` | Service temporarily unavailable |

### Example Error Response

```json
{
  "type": "/errors/document-not-found",
  "title": "Document Not Found",
  "status": 404,
  "detail": "The document with ID 'abc-123' was not found.",
  "instance": "/api/v1/documents/abc-123"
}
```

### Validation Error Response

```json
{
  "type": "/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "Request validation failed",
  "errors": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Projects

### Create Project

Creates a new anonymization project.

```http
POST /api/v1/projects
Content-Type: application/json
```

**Request Body:**

```json
{
  "name": "Project Name",
  "description": "Optional project description",
  "default_anonymization_level": "INTERMEDIATE"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Project name (1-200 chars) |
| `description` | string | No | Project description |
| `default_anonymization_level` | enum | Yes | `BASIC`, `INTERMEDIATE`, or `ADVANCED` |

**Response:** `201 Created`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Project Name",
  "description": "Optional project description",
  "default_anonymization_level": "INTERMEDIATE",
  "created_at": "2024-01-11T10:30:00Z",
  "document_count": 0
}
```

**Errors:**

- `400` - Invalid request (validation error)
- `409` - Project with same name already exists

---

### Get Project

Retrieves project details by ID.

```http
GET /api/v1/projects/{project_id}
```

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Project Name",
  "description": "Optional project description",
  "default_anonymization_level": "INTERMEDIATE",
  "created_at": "2024-01-11T10:30:00Z",
  "document_count": 5
}
```

**Errors:**

- `404` - Project not found

---

### Update Project

Updates project metadata.

```http
PUT /api/v1/projects/{project_id}
Content-Type: application/json
```

**Request Body:**

```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "default_anonymization_level": "ADVANCED"
}
```

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Updated Name",
  "description": "Updated description",
  "default_anonymization_level": "ADVANCED",
  "created_at": "2024-01-11T10:30:00Z",
  "document_count": 5
}
```

**Errors:**

- `404` - Project not found
- `400` - Validation error

---

### Delete Project

Deletes a project and all associated documents.

```http
DELETE /api/v1/projects/{project_id}
```

**Response:** `204 No Content`

**Errors:**

- `404` - Project not found

---

### List Projects

Lists all projects with pagination.

```http
GET /api/v1/projects?limit=100&offset=0
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 100 | Page size (1-1000) |
| `offset` | integer | 0 | Page offset |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Project 1",
      "description": "Description",
      "default_anonymization_level": "INTERMEDIATE",
      "created_at": "2024-01-11T10:30:00Z",
      "document_count": 5
    }
  ],
  "total": 10
}
```

---

## Documents

### Upload Document

Uploads a new document to a project.

```http
POST /api/v1/documents?project_id={project_id}
Content-Type: multipart/form-data
```

**Form Data:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | Document file (PDF, DOCX, PNG, JPG) |
| `project_id` | UUID | Yes | Target project ID |

**Example (curl):**

```bash
curl -X POST "http://localhost:8000/api/v1/documents?project_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "file=@document.pdf"
```

**Response:** `201 Created`

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "state": "PENDING",
  "created_at": "2024-01-11T10:35:00Z",
  "updated_at": "2024-01-11T10:35:00Z"
}
```

**Errors:**

- `400` - File too large (max 10MB), invalid format
- `409` - Duplicate document
- `422` - Validation error

**Supported Formats:**

- PDF (`.pdf`)
- Word (`.docx`)
- Images (`.png`, `.jpg`, `.jpeg`) - requires OCR

---

### Get Document

Retrieves document metadata.

```http
GET /api/v1/documents/{document_id}
```

**Response:** `200 OK`

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "state": "DETECTION_COMPLETE",
  "created_at": "2024-01-11T10:35:00Z",
  "updated_at": "2024-01-11T10:40:00Z"
}
```

**Document States:**

- `PENDING` - Uploaded, not processed
- `PROCESSING` - Being processed
- `DETECTION_COMPLETE` - PII detection finished
- `ANONYMIZATION_COMPLETE` - Anonymization finished
- `ERROR` - Processing failed

**Errors:**

- `404` - Document not found

---

### Delete Document

Deletes a document and all associated data.

```http
DELETE /api/v1/documents/{document_id}
```

**Response:** `204 No Content`

**Errors:**

- `404` - Document not found

---

### List Documents

Lists all documents in a project.

```http
GET /api/v1/documents?project_id={project_id}&limit=100&offset=0
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `project_id` | UUID | Yes | - | Filter by project |
| `limit` | integer | No | 100 | Page size (1-1000) |
| `offset` | integer | No | 0 | Page offset |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "project_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "document.pdf",
      "state": "DETECTION_COMPLETE",
      "created_at": "2024-01-11T10:35:00Z",
      "updated_at": "2024-01-11T10:40:00Z"
    }
  ],
  "total": 5,
  "limit": 100,
  "offset": 0
}
```

---

## Detection

### Detect PII

Runs PII detection on a document.

```http
POST /api/v1/documents/{document_id}/detect
Content-Type: application/json
```

**Request Body (optional):**

```json
{
  "confidence_threshold": 0.75,
  "categories": ["FULL_NAME", "EMAIL", "PHONE", "DNI"]
}
```

**Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `confidence_threshold` | float | No | 0.75 | Minimum confidence (0.0-1.0) |
| `categories` | array | No | all | PII categories to detect |

**Response:** `200 OK`

```json
{
  "document_id": "660e8400-e29b-41d4-a716-446655440001",
  "entities_found": 42,
  "entities": [
    {
      "text": "Juan Pérez",
      "category": "FULL_NAME",
      "confidence": 0.95,
      "position": {
        "start": 120,
        "end": 130
      }
    },
    {
      "text": "12345678A",
      "category": "DNI",
      "confidence": 0.99,
      "position": {
        "start": 250,
        "end": 259
      }
    }
  ],
  "detection_completed_at": "2024-01-11T10:40:00Z"
}
```

**PII Categories:**

| Category | Examples |
|----------|----------|
| `FULL_NAME` | Juan Pérez, María García |
| `EMAIL` | juan@example.com |
| `PHONE` | +34 600 123 456, 900123456 |
| `DNI` | 12345678A |
| `NIE` | X1234567A |
| `PASSPORT` | AAA123456 |
| `SSN` | 12-3456789-0 |
| `ADDRESS` | Calle Mayor 123, Madrid |
| `BANK_ACCOUNT` | ES79 2100 0813 6101 2345 6789 |
| `CREDIT_CARD` | 4532-1234-5678-9010 |
| `IP_ADDRESS` | 192.168.1.1 |
| `DATE_OF_BIRTH` | 15/03/1980 |
| `LICENSE_PLATE` | 1234 ABC |

**Errors:**

- `404` - Document not found
- `409` - Detection already in progress
- `422` - Document not ready (still uploading)

---

### Get Detection Results

Retrieves cached detection results.

```http
GET /api/v1/documents/{document_id}/detection-results
```

**Response:** `200 OK`

Same schema as `POST /detect` response.

**Errors:**

- `404` - Document not found or not yet detected

---

## Anonymization

### Anonymize Document

Generates anonymized version of document.

```http
POST /api/v1/documents/{document_id}/anonymize
Content-Type: application/json
```

**Request Body (optional):**

```json
{
  "level": "INTERMEDIATE",
  "preserve_structure": true
}
```

**Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `level` | enum | No | Project default | `BASIC`, `INTERMEDIATE`, `ADVANCED` |
| `preserve_structure` | boolean | No | true | Preserve document formatting |

**Anonymization Levels:**

| Level | Description | Example |
|-------|-------------|---------|
| `BASIC` | Simple masking | `Juan Pérez` → `****** *****` |
| `INTERMEDIATE` | Consistent aliases | `Juan Pérez` → `PERSONA-001` |
| `ADVANCED` | Contextual aliases | `Juan Pérez` → `Alice Johnson` |

**Response:** `200 OK`

```json
{
  "document_id": "660e8400-e29b-41d4-a716-446655440001",
  "level": "INTERMEDIATE",
  "anonymized_content": "<base64-encoded-pdf>",
  "entities_replaced": 42,
  "glossary_entries": 15,
  "completed_at": "2024-01-11T10:45:00Z"
}
```

**Errors:**

- `404` - Document not found
- `409` - Anonymization already in progress
- `422` - No PII detected (run detection first)

---

### Get Anonymized Content

Retrieves cached anonymized document.

```http
GET /api/v1/documents/{document_id}/anonymized
```

**Response:** `200 OK`

Same schema as `POST /anonymize` response.

**Errors:**

- `404` - Document not found
- `422` - Document not anonymized yet

---

## Glossary

### Get Project Glossary

Retrieves alias mappings for entire project.

```http
GET /api/v1/projects/{project_id}/glossary
```

**Response:** `200 OK`

```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "entries": [
    {
      "alias": "PERSONA-001",
      "category": "FULL_NAME",
      "first_seen_at": "2024-01-11T10:40:00Z",
      "occurrence_count": 12
    },
    {
      "alias": "EMAIL-001",
      "category": "EMAIL",
      "first_seen_at": "2024-01-11T10:40:00Z",
      "occurrence_count": 5
    }
  ],
  "total_entries": 15
}
```

**Note:** Original PII values are **never returned** via API for security reasons. They are only visible in exported glossary files.

**Errors:**

- `404` - Project not found

---

### Get Document Glossary

Retrieves alias mappings for specific document.

```http
GET /api/v1/documents/{document_id}/glossary
```

**Response:** `200 OK`

Same schema as project glossary, filtered to document entities.

**Errors:**

- `404` - Document not found

---

## Export

### Export Anonymized Document

Downloads anonymized document in requested format.

```http
POST /api/v1/documents/{document_id}/export?format=pdf
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `format` | enum | No | `txt` | Export format |

**Supported Formats:**

- `pdf` - PDF document
- `docx` - Word document
- `txt` - Plain text
- `json` - JSON with metadata
- `csv` - CSV (for tabular data)

**Response:** `200 OK`

```
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="document_anonymized.pdf"

<binary file content>
```

**Errors:**

- `404` - Document not found
- `422` - Document not anonymized yet

**Example (curl):**

```bash
curl -X POST "http://localhost:8000/api/v1/documents/{document_id}/export?format=pdf" \
  -o anonymized.pdf
```

---

### Export Glossary

Downloads project glossary as CSV/JSON.

```http
GET /api/v1/projects/{project_id}/export/glossary?format=csv
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `format` | enum | No | `csv` | Export format (`csv` or `json`) |

**Response:** `200 OK`

```
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="glossary.csv"

alias,original,category,first_seen,occurrences
PERSONA-001,Juan Pérez,FULL_NAME,2024-01-11T10:40:00Z,12
EMAIL-001,juan@example.com,EMAIL,2024-01-11T10:40:00Z,5
```

**Errors:**

- `404` - Project not found

---

## WebSocket

### Progress Updates

Subscribe to real-time progress updates for long-running operations.

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/progress');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(update);
};

// Send subscription message
ws.send(JSON.stringify({
  action: 'subscribe',
  document_id: '660e8400-e29b-41d4-a716-446655440001'
}));
```

**Progress Update Message:**

```json
{
  "type": "progress",
  "document_id": "660e8400-e29b-41d4-a716-446655440001",
  "operation": "detection",
  "progress": 45.5,
  "status": "processing",
  "message": "Processing page 3 of 10",
  "timestamp": "2024-01-11T10:41:00Z"
}
```

**Completion Message:**

```json
{
  "type": "complete",
  "document_id": "660e8400-e29b-41d4-a716-446655440001",
  "operation": "detection",
  "status": "success",
  "result": {
    "entities_found": 42
  },
  "timestamp": "2024-01-11T10:42:00Z"
}
```

**Error Message:**

```json
{
  "type": "error",
  "document_id": "660e8400-e29b-41d4-a716-446655440001",
  "operation": "detection",
  "status": "error",
  "error": {
    "type": "/errors/llm-error",
    "detail": "LLM service unavailable"
  },
  "timestamp": "2024-01-11T10:42:00Z"
}
```

---

## Health & Metrics

### Health Check

Returns service health status.

```http
GET /health
```

**Response:** `200 OK` (healthy) or `503 Service Unavailable` (unhealthy)

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

**Unhealthy Response:**

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
    "LLM model file not found"
  ]
}
```

---

### Prometheus Metrics

Exposes Prometheus-compatible metrics.

```http
GET /metrics
```

**Response:** `200 OK`

```
# HELP contextsafe_documents_processed_total Total documents processed
# TYPE contextsafe_documents_processed_total counter
contextsafe_documents_processed_total{status="success"} 142
contextsafe_documents_processed_total{status="error"} 3

# HELP contextsafe_entities_detected_total Total PII entities detected
# TYPE contextsafe_entities_detected_total counter
contextsafe_entities_detected_total{category="FULL_NAME"} 450
contextsafe_entities_detected_total{category="EMAIL"} 320

# HELP contextsafe_llm_inference_duration_seconds LLM inference duration
# TYPE contextsafe_llm_inference_duration_seconds histogram
contextsafe_llm_inference_duration_seconds_bucket{le="1.0"} 50
contextsafe_llm_inference_duration_seconds_bucket{le="5.0"} 120
contextsafe_llm_inference_duration_seconds_bucket{le="+Inf"} 142
```

---

## Interactive Documentation

ContextSafe provides interactive API documentation via Swagger UI:

**Swagger UI:** http://localhost:8000/docs

**ReDoc:** http://localhost:8000/redoc

---

## Rate Limits

**Current version (v0.1.0):** No rate limits (local deployment).

**Future versions:**
- 100 requests/minute per IP
- 10 concurrent document processing operations

---

## Changelog

### v0.1.0 (2024-01-11)

- Initial API release
- Project management endpoints
- Document upload and processing
- PII detection (13 categories)
- Anonymization (3 levels)
- Glossary management
- Export functionality
- WebSocket progress updates

