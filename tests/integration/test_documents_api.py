"""
Integration tests for Documents API.

Tests the complete document lifecycle:
- Upload
- Process
- Get entities
- Get anonymized content
- Export

Traceability:
- Contract: CNT-T4-DOCUMENTS-001
- Bindings: UI-BIND-001, UI-BIND-002, UI-BIND-004, UI-BIND-005
"""

import io
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Create test client for the API."""
    from contextsafe.api.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture
def project_id(client):
    """Create a test project and return its ID."""
    response = client.post(
        "/api/v1/projects",
        json={
            "name": "Test Project",
            "description": "Integration test project",
        }
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


class TestDocumentUpload:
    """Tests for document upload functionality."""

    def test_upload_text_document(self, client, project_id):
        """Should successfully upload a text document."""
        content = b"Test document content with some PII data."
        files = {"file": ("test.txt", io.BytesIO(content), "text/plain")}

        response = client.post(
            f"/api/v1/documents?project_id={project_id}",
            files=files,
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["filename"] == "test.txt"
        assert data["state"] == "pending"
        assert "id" in data

    def test_upload_without_project_id(self, client):
        """Should fail when no project_id is provided."""
        content = b"Test content"
        files = {"file": ("test.txt", io.BytesIO(content), "text/plain")}

        response = client.post(
            "/api/v1/documents",
            files=files,
        )

        assert response.status_code == 422  # Validation error

    def test_upload_to_nonexistent_project(self, client):
        """Should fail when project doesn't exist."""
        content = b"Test content"
        files = {"file": ("test.txt", io.BytesIO(content), "text/plain")}

        response = client.post(
            "/api/v1/documents?project_id=00000000-0000-0000-0000-000000000000",
            files=files,
        )

        assert response.status_code == 404


class TestDocumentProcessing:
    """Tests for document processing functionality."""

    @pytest.fixture
    def uploaded_document(self, client, project_id):
        """Upload a document with PII data for processing tests."""
        content = b"""INFORME CONFIDENCIAL
Paciente: Juan Perez Garcia
DNI: 12345678Z
Telefono: +34 666 123 456
Email: juan.perez@email.com
Direccion: Calle Mayor 123, Madrid
"""
        files = {"file": ("medical_report.txt", io.BytesIO(content), "text/plain")}

        response = client.post(
            f"/api/v1/documents?project_id={project_id}",
            files=files,
        )
        assert response.status_code == 201
        return response.json()["data"]["id"]

    def test_process_document(self, client, uploaded_document):
        """Should start document processing."""
        response = client.post(
            f"/api/v1/documents/{uploaded_document}/process"
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == "processing_started"
        assert data["documentId"] == uploaded_document

    def test_process_nonexistent_document(self, client):
        """Should fail when document doesn't exist."""
        response = client.post(
            "/api/v1/documents/00000000-0000-0000-0000-000000000000/process"
        )

        assert response.status_code == 404


class TestDocumentRetrieval:
    """Tests for document retrieval functionality."""

    @pytest.fixture
    def processed_document(self, client, project_id):
        """Upload and process a document."""
        import time

        content = b"""Paciente: Maria Garcia Lopez
Email: maria@test.com
Telefono: 612345678
"""
        files = {"file": ("patient.txt", io.BytesIO(content), "text/plain")}

        # Upload
        response = client.post(
            f"/api/v1/documents?project_id={project_id}",
            files=files,
        )
        doc_id = response.json()["data"]["id"]

        # Process
        client.post(f"/api/v1/documents/{doc_id}/process")

        # Wait for processing
        time.sleep(2)

        return doc_id

    def test_get_document(self, client, processed_document):
        """Should retrieve document details."""
        response = client.get(f"/api/v1/documents/{processed_document}")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == processed_document
        assert "state" in data
        assert "filename" in data

    def test_get_document_entities(self, client, processed_document):
        """Should retrieve detected entities."""
        response = client.get(f"/api/v1/documents/{processed_document}/entities")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_anonymized_content(self, client, processed_document):
        """Should retrieve anonymized content."""
        response = client.get(f"/api/v1/documents/{processed_document}/anonymized")

        assert response.status_code == 200
        data = response.json()["data"]
        assert "originalText" in data
        assert "anonymizedText" in data


class TestDocumentExport:
    """Tests for document export functionality."""

    @pytest.fixture
    def document_for_export(self, client, project_id):
        """Create a processed document for export tests."""
        import time

        content = b"Simple document for export test."
        files = {"file": ("export_test.txt", io.BytesIO(content), "text/plain")}

        response = client.post(
            f"/api/v1/documents?project_id={project_id}",
            files=files,
        )
        doc_id = response.json()["data"]["id"]

        client.post(f"/api/v1/documents/{doc_id}/process")
        time.sleep(1)

        return doc_id

    def test_export_as_txt(self, client, document_for_export):
        """Should export document as plain text."""
        response = client.post(
            f"/api/v1/documents/{document_for_export}/export?format=txt"
        )

        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")

    def test_export_as_pdf(self, client, document_for_export):
        """Should export document as PDF."""
        response = client.post(
            f"/api/v1/documents/{document_for_export}/export?format=pdf"
        )

        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("content-type", "")
        # Verify PDF magic bytes
        assert response.content.startswith(b"%PDF")

    def test_export_as_docx(self, client, document_for_export):
        """Should export document as DOCX."""
        response = client.post(
            f"/api/v1/documents/{document_for_export}/export?format=docx"
        )

        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "openxmlformats" in content_type or "application/zip" in content_type
        # DOCX files are ZIP archives, verify magic bytes
        assert response.content[:2] == b"PK"

    def test_export_nonexistent_document(self, client):
        """Should fail when document doesn't exist."""
        response = client.post(
            "/api/v1/documents/00000000-0000-0000-0000-000000000000/export?format=txt"
        )

        assert response.status_code == 404


class TestGlossaryExport:
    """Tests for glossary export functionality."""

    @pytest.fixture
    def project_with_glossary(self, client):
        """Create a project with processed documents to generate glossary."""
        import time

        # Create project
        response = client.post(
            "/api/v1/projects",
            json={"name": "Glossary Export Test", "description": "Test project"},
        )
        project_id = response.json()["data"]["id"]

        # Upload and process a document with PII
        content = b"Paciente: Juan Garcia, Email: juan@test.com"
        files = {"file": ("test.txt", io.BytesIO(content), "text/plain")}
        response = client.post(
            f"/api/v1/documents?project_id={project_id}",
            files=files,
        )
        doc_id = response.json()["data"]["id"]

        client.post(f"/api/v1/documents/{doc_id}/process")
        time.sleep(2)

        return project_id

    def test_export_glossary_as_csv(self, client, project_with_glossary):
        """Should export glossary as CSV."""
        response = client.get(
            f"/api/v1/projects/{project_with_glossary}/export/glossary?format=csv"
        )

        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        content = response.content.decode("utf-8")
        assert "Texto Original" in content  # Header
        assert "Alias" in content

    def test_export_glossary_as_json(self, client, project_with_glossary):
        """Should export glossary as JSON."""
        response = client.get(
            f"/api/v1/projects/{project_with_glossary}/export/glossary?format=json"
        )

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
        data = response.json()
        assert "entries" in data
        assert "project_id" in data

    def test_export_glossary_nonexistent_project(self, client):
        """Should fail when project doesn't exist."""
        response = client.get(
            "/api/v1/projects/00000000-0000-0000-0000-000000000000/export/glossary"
        )

        assert response.status_code == 404


class TestBatchProcessing:
    """Tests for batch processing functionality."""

    @pytest.fixture
    def multiple_documents(self, client, project_id):
        """Upload multiple documents for batch processing."""
        doc_ids = []
        for i in range(3):
            content = f"Document {i+1} with patient name Juan{i}".encode()
            files = {"file": (f"batch_{i}.txt", io.BytesIO(content), "text/plain")}

            response = client.post(
                f"/api/v1/documents?project_id={project_id}",
                files=files,
            )
            doc_ids.append(response.json()["data"]["id"])

        return doc_ids, project_id

    def test_process_all_in_project(self, client, multiple_documents):
        """Should process all pending documents in a project."""
        doc_ids, project_id = multiple_documents

        response = client.post(
            f"/api/v1/documents/project/{project_id}/process-all"
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total_started"] == 3
        assert len(data["started"]) == 3

class TestDocumentDeletion:
    """Tests for document deletion functionality."""

    def test_delete_document(self, client, project_id):
        """Should delete a document."""
        # First create a document
        content = b"Document to delete"
        files = {"file": ("to_delete.txt", io.BytesIO(content), "text/plain")}

        response = client.post(
            f"/api/v1/documents?project_id={project_id}",
            files=files,
        )
        doc_id = response.json()["data"]["id"]

        # Delete it
        response = client.delete(f"/api/v1/documents/{doc_id}")
        assert response.status_code == 204

        # Verify it's gone
        response = client.get(f"/api/v1/documents/{doc_id}")
        assert response.status_code == 404

    def test_delete_nonexistent_document(self, client):
        """Should return 404 when deleting nonexistent document."""
        response = client.delete(
            "/api/v1/documents/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404
