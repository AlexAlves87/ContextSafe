"""
Shared fixtures for domain unit tests.

This module provides pytest fixtures and test utilities
for testing domain layer components.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from contextsafe.domain.document_processing.entities.document import Document
    from contextsafe.domain.project_management.aggregates.project import Project


# =============================================================================
# ID Fixtures
# =============================================================================

@pytest.fixture
def random_uuid():
    """Generate a random UUID for testing."""
    return uuid4()


@pytest.fixture
def document_id(random_uuid):
    """Generate a document ID."""
    try:
        from contextsafe.domain.document_processing.value_objects import DocumentId
        return DocumentId(random_uuid)
    except ImportError:
        return random_uuid


@pytest.fixture
def project_id(random_uuid):
    """Generate a project ID."""
    try:
        from contextsafe.domain.project_management.value_objects import ProjectId
        return ProjectId(random_uuid)
    except ImportError:
        return random_uuid


# =============================================================================
# Value Object Fixtures
# =============================================================================

@pytest.fixture
def valid_confidence_score():
    """Create a valid confidence score."""
    try:
        from contextsafe.domain.shared.value_objects import ConfidenceScore
        return ConfidenceScore(0.85)
    except ImportError:
        return 0.85


@pytest.fixture
def low_confidence_score():
    """Create a low confidence score."""
    try:
        from contextsafe.domain.shared.value_objects import ConfidenceScore
        return ConfidenceScore(0.3)
    except ImportError:
        return 0.3


@pytest.fixture
def text_span():
    """Create a sample text span."""
    try:
        from contextsafe.domain.shared.value_objects import TextSpan
        return TextSpan(start=10, end=20, text="Juan García")
    except ImportError:
        return {"start": 10, "end": 20, "text": "Juan García"}


@pytest.fixture
def pii_category():
    """Create a PII category."""
    try:
        from contextsafe.domain.shared.value_objects import PiiCategory
        return PiiCategory("PERSON_NAME")
    except ImportError:
        return "PERSON_NAME"


@pytest.fixture
def alias():
    """Create a sample alias."""
    try:
        from contextsafe.domain.shared.value_objects import Alias
        return Alias("[PERSONA_001]")
    except ImportError:
        return "[PERSONA_001]"


# =============================================================================
# Entity Fixtures
# =============================================================================

@pytest.fixture
def sample_document(document_id, project_id):
    """Create a sample document for testing."""
    try:
        from contextsafe.domain.document_processing.entities.document import Document
        return Document.create(
            document_id=document_id,
            project_id=project_id,
            filename="test_document.txt",
            content="Juan García trabaja en Acme Corp ubicada en Madrid.",
            mime_type="text/plain",
        )
    except ImportError:
        return {
            "id": document_id,
            "project_id": project_id,
            "filename": "test_document.txt",
            "content": "Juan García trabaja en Acme Corp ubicada en Madrid.",
            "mime_type": "text/plain",
        }


@pytest.fixture
def sample_detection_result(document_id, text_span, pii_category, valid_confidence_score):
    """Create a sample detection result."""
    try:
        from contextsafe.domain.entity_detection.entities.detection_result import (
            DetectionResult,
        )
        return DetectionResult.create(
            document_id=document_id,
            span=text_span,
            category=pii_category,
            confidence=valid_confidence_score,
            source="spacy",
        )
    except ImportError:
        return {
            "document_id": document_id,
            "span": text_span,
            "category": pii_category,
            "confidence": valid_confidence_score,
            "source": "spacy",
        }


# =============================================================================
# Aggregate Fixtures
# =============================================================================

@pytest.fixture
def empty_glossary(project_id):
    """Create an empty glossary."""
    try:
        from contextsafe.domain.anonymization.aggregates.glossary import Glossary
        return Glossary.create(project_id)
    except ImportError:
        return {"project_id": project_id, "entries": {}}


@pytest.fixture
def glossary_with_entries(project_id, pii_category):
    """Create a glossary with some entries."""
    try:
        from contextsafe.domain.anonymization.aggregates.glossary import Glossary
        glossary = Glossary.create(project_id)
        glossary.get_or_create_alias("juan garcía", pii_category)
        glossary.get_or_create_alias("acme corp", pii_category)
        return glossary
    except ImportError:
        return {
            "project_id": project_id,
            "entries": {
                "juan garcía": "[PERSONA_001]",
                "acme corp": "[PERSONA_002]",
            },
        }


@pytest.fixture
def sample_project(project_id):
    """Create a sample project."""
    try:
        from contextsafe.domain.project_management.aggregates.project import Project
        return Project.create(
            project_id=project_id,
            name="Test Project",
            description="A test project for unit tests",
        )
    except ImportError:
        return {
            "id": project_id,
            "name": "Test Project",
            "description": "A test project for unit tests",
        }


# =============================================================================
# Event Fixtures
# =============================================================================

@pytest.fixture
def document_ingested_event(document_id, project_id):
    """Create a DocumentIngested event."""
    try:
        from contextsafe.domain.document_processing.events import DocumentIngested
        return DocumentIngested(
            document_id=document_id,
            project_id=project_id,
            filename="test.txt",
            occurred_at=datetime.utcnow(),
        )
    except ImportError:
        return {
            "type": "DocumentIngested",
            "document_id": document_id,
            "project_id": project_id,
            "filename": "test.txt",
            "occurred_at": datetime.utcnow(),
        }


@pytest.fixture
def pii_detected_event(document_id):
    """Create a PiiDetected event."""
    try:
        from contextsafe.domain.entity_detection.events import PiiDetected
        return PiiDetected(
            document_id=document_id,
            entity_count=5,
            categories=["PERSON_NAME", "ORGANIZATION"],
            occurred_at=datetime.utcnow(),
        )
    except ImportError:
        return {
            "type": "PiiDetected",
            "document_id": document_id,
            "entity_count": 5,
            "categories": ["PERSON_NAME", "ORGANIZATION"],
            "occurred_at": datetime.utcnow(),
        }


# =============================================================================
# Result Fixtures
# =============================================================================

@pytest.fixture
def ok_result():
    """Create an Ok result."""
    try:
        from contextsafe.domain.shared.result import Ok
        return Ok(value="success")
    except ImportError:
        return {"ok": True, "value": "success"}


@pytest.fixture
def err_result():
    """Create an Err result."""
    try:
        from contextsafe.domain.shared.result import Err
        from contextsafe.domain.shared.errors import ValidationError
        return Err(error=ValidationError("Invalid input"))
    except ImportError:
        return {"ok": False, "error": "Invalid input"}


# =============================================================================
# Helper Functions
# =============================================================================

def make_detection_results(document_id, count: int = 5):
    """Generate multiple detection results for testing."""
    results = []
    categories = ["PERSON_NAME", "ORGANIZATION", "ADDRESS", "PHONE", "EMAIL"]

    try:
        from contextsafe.domain.entity_detection.entities.detection_result import (
            DetectionResult,
        )
        from contextsafe.domain.shared.value_objects import (
            ConfidenceScore,
            PiiCategory,
            TextSpan,
        )

        for i in range(count):
            result = DetectionResult.create(
                document_id=document_id,
                span=TextSpan(start=i * 20, end=i * 20 + 10, text=f"Entity_{i}"),
                category=PiiCategory(categories[i % len(categories)]),
                confidence=ConfidenceScore(0.8 + (i * 0.02)),
                source="test",
            )
            results.append(result)
    except ImportError:
        for i in range(count):
            results.append({
                "document_id": document_id,
                "span": {"start": i * 20, "end": i * 20 + 10, "text": f"Entity_{i}"},
                "category": categories[i % len(categories)],
                "confidence": 0.8 + (i * 0.02),
                "source": "test",
            })

    return results
