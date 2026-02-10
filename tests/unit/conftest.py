"""
Shared pytest fixtures for unit tests.

Provides common test data and fixtures for domain and application layer tests.
"""
from typing import Any
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from contextsafe.domain.shared.value_objects import (
    Alias,
    ConfidenceScore,
    DocumentId,
    DocumentState,
    PiiCategory,
    ProjectId,
    TextSpan,
)
from contextsafe.domain.shared.value_objects.pii_category import PERSON_NAME, EMAIL
from contextsafe.domain.shared.value_objects.document_state import PENDING


# ═══════════════════════════════════════════════════════════════════════════════
# VALUE OBJECT FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def valid_uuid() -> str:
    """Generate a valid UUID string."""
    return str(uuid4())


@pytest.fixture
def document_id(valid_uuid: str) -> DocumentId:
    """Create a valid DocumentId."""
    return DocumentId.create(valid_uuid).unwrap()


@pytest.fixture
def project_id(valid_uuid: str) -> ProjectId:
    """Create a valid ProjectId."""
    return ProjectId.create(valid_uuid).unwrap()


@pytest.fixture
def confidence_score() -> ConfidenceScore:
    """Create a high confidence score."""
    return ConfidenceScore.create(0.95).unwrap()


@pytest.fixture
def low_confidence_score() -> ConfidenceScore:
    """Create a low confidence score requiring review."""
    return ConfidenceScore.create(0.5).unwrap()


@pytest.fixture
def text_span() -> TextSpan:
    """Create a valid text span."""
    return TextSpan.create(0, 10, "John Smith").unwrap()


@pytest.fixture
def person_name_category() -> PiiCategory:
    """Create a PERSON_NAME category."""
    return PERSON_NAME


@pytest.fixture
def email_category() -> PiiCategory:
    """Create an EMAIL category."""
    return EMAIL


@pytest.fixture
def valid_alias(person_name_category: PiiCategory) -> Alias:
    """Create a valid alias."""
    return Alias.generate(person_name_category, 1).unwrap()


# ═══════════════════════════════════════════════════════════════════════════════
# MOCK PORT FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_document_repository() -> AsyncMock:
    """Create a mock DocumentRepository."""
    repo = AsyncMock()
    repo.save = AsyncMock()
    repo.find_by_id = AsyncMock()
    repo.find_by_project = AsyncMock()
    return repo


@pytest.fixture
def mock_project_repository() -> AsyncMock:
    """Create a mock ProjectRepository."""
    repo = AsyncMock()
    repo.save = AsyncMock()
    repo.find_by_id = AsyncMock()
    return repo


@pytest.fixture
def mock_glossary_repository() -> AsyncMock:
    """Create a mock GlossaryRepository."""
    repo = AsyncMock()
    repo.save = AsyncMock()
    repo.find_by_id = AsyncMock()
    return repo


@pytest.fixture
def mock_ner_service() -> AsyncMock:
    """Create a mock NER service."""
    service = AsyncMock()
    service.detect_entities = AsyncMock()
    return service


@pytest.fixture
def mock_text_extractor() -> AsyncMock:
    """Create a mock TextExtractor."""
    extractor = AsyncMock()
    extractor.extract = AsyncMock()
    return extractor


@pytest.fixture
def mock_event_publisher() -> AsyncMock:
    """Create a mock EventPublisher."""
    publisher = AsyncMock()
    publisher.publish = AsyncMock()
    return publisher


# ═══════════════════════════════════════════════════════════════════════════════
# SAMPLE DATA FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_document_content() -> bytes:
    """Sample document content for testing."""
    return b"This is a test document with some content."


@pytest.fixture
def sample_extracted_text() -> str:
    """Sample extracted text for testing."""
    return "John Smith lives at 123 Main Street. Email: john@example.com. Phone: 555-0100."


@pytest.fixture
def sample_filename() -> str:
    """Sample filename for testing."""
    return "test_document.txt"


@pytest.fixture
def sample_pdf_filename() -> str:
    """Sample PDF filename for testing."""
    return "test_document.pdf"


@pytest.fixture
def sample_image_filename() -> str:
    """Sample image filename for testing."""
    return "test_document.png"


@pytest.fixture
def invalid_filename() -> str:
    """Invalid filename for testing."""
    return "test_document.xyz"
