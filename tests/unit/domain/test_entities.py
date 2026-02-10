"""
Unit tests for domain entities.

Tests:
- Document
- DetectionResult
- AliasMapping
- AuditLog
- BatchJob
"""
import pytest
from datetime import datetime
from uuid import uuid4

from contextsafe.domain.document_processing.entities.document import (
    Document,
    MAX_DOCUMENT_SIZE,
    VALID_EXTENSIONS,
)
from contextsafe.domain.entity_detection.entities.detection_result import DetectionResult
from contextsafe.domain.shared.value_objects import (
    ConfidenceScore,
    DocumentId,
    PiiCategory,
    ProjectId,
    TextSpan,
)
from contextsafe.domain.shared.value_objects.pii_category import PERSON_NAME, EMAIL
from contextsafe.domain.shared.errors import (
    DocumentError,
    DocumentSizeError,
    InvalidExtensionError,
    DetectionError,
)


# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENT ENTITY
# ═══════════════════════════════════════════════════════════════════════════════


class TestDocument:
    """Test Document entity."""

    @pytest.fixture
    def project_id(self) -> ProjectId:
        """Create a project ID for testing."""
        return ProjectId.create(str(uuid4())).unwrap()

    @pytest.fixture
    def valid_content(self) -> bytes:
        """Create valid document content."""
        return b"This is a test document with some content."

    def test_create_valid_document(self, project_id: ProjectId, valid_content: bytes):
        """Test creating a valid document."""
        # Arrange & Act
        result = Document.create(
            project_id=project_id,
            content=valid_content,
            filename="test.txt",
        )

        # Assert
        assert result.is_ok()
        doc = result.unwrap()
        assert doc.project_id == project_id
        assert doc.filename == "test.txt"
        assert doc.content == valid_content
        assert doc.extracted_text is None
        assert doc.state.value.value == "PENDING"

    def test_create_rejects_empty_content(self, project_id: ProjectId):
        """Test that empty content is rejected."""
        # Arrange & Act
        result = Document.create(
            project_id=project_id,
            content=b"",
            filename="test.txt",
        )

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, DocumentError)

    def test_create_rejects_oversized_content(self, project_id: ProjectId):
        """Test that content exceeding size limit is rejected."""
        # Arrange
        oversized_content = b"x" * (MAX_DOCUMENT_SIZE + 1)

        # Act
        result = Document.create(
            project_id=project_id,
            content=oversized_content,
            filename="test.txt",
        )

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, DocumentSizeError)

    def test_create_rejects_invalid_extension(self, project_id: ProjectId, valid_content: bytes):
        """Test that invalid file extension is rejected."""
        # Arrange & Act
        result = Document.create(
            project_id=project_id,
            content=valid_content,
            filename="test.xyz",
        )

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, InvalidExtensionError)

    def test_create_accepts_all_valid_extensions(self, project_id: ProjectId, valid_content: bytes):
        """Test that all valid extensions are accepted."""
        # Arrange
        valid_filenames = [
            "test.txt",
            "test.pdf",
            "test.png",
            "test.jpg",
            "test.jpeg",
            "test.docx",
        ]

        # Act & Assert
        for filename in valid_filenames:
            result = Document.create(
                project_id=project_id,
                content=valid_content,
                filename=filename,
            )
            assert result.is_ok(), f"Failed for {filename}"

    def test_extension_property(self, project_id: ProjectId, valid_content: bytes):
        """Test extension property."""
        # Arrange
        doc = Document.create(
            project_id=project_id,
            content=valid_content,
            filename="test.PDF",  # uppercase
        ).unwrap()

        # Act & Assert
        assert doc.extension == ".pdf"  # normalized to lowercase

    def test_is_image_property(self, project_id: ProjectId, valid_content: bytes):
        """Test is_image property."""
        # Arrange
        image_doc = Document.create(
            project_id=project_id,
            content=valid_content,
            filename="test.png",
        ).unwrap()
        text_doc = Document.create(
            project_id=project_id,
            content=valid_content,
            filename="test.txt",
        ).unwrap()

        # Act & Assert
        assert image_doc.is_image is True
        assert text_doc.is_image is False

    def test_is_pdf_property(self, project_id: ProjectId, valid_content: bytes):
        """Test is_pdf property."""
        # Arrange
        pdf_doc = Document.create(
            project_id=project_id,
            content=valid_content,
            filename="test.pdf",
        ).unwrap()
        text_doc = Document.create(
            project_id=project_id,
            content=valid_content,
            filename="test.txt",
        ).unwrap()

        # Act & Assert
        assert pdf_doc.is_pdf is True
        assert text_doc.is_pdf is False

    def test_has_content_property(self, project_id: ProjectId, valid_content: bytes):
        """Test has_content property."""
        # Arrange
        doc = Document.create(
            project_id=project_id,
            content=valid_content,
            filename="test.txt",
        ).unwrap()

        # Act & Assert
        assert doc.has_content is True

    def test_set_extracted_text(self, project_id: ProjectId, valid_content: bytes):
        """Test setting extracted text."""
        # Arrange
        doc = Document.create(
            project_id=project_id,
            content=valid_content,
            filename="test.txt",
        ).unwrap()
        initial_version = doc.version

        # Act
        doc.set_extracted_text("Extracted text content")

        # Assert
        assert doc.extracted_text == "Extracted text content"
        assert doc.has_extracted_text is True
        assert doc.version == initial_version + 1  # version incremented

    def test_create_from_path(self, project_id: ProjectId):
        """Test creating document from path."""
        # Arrange & Act
        result = Document.create_from_path(
            project_id=project_id,
            content_path="/path/to/document.txt",
            filename="document.txt",
        )

        # Assert
        assert result.is_ok()
        doc = result.unwrap()
        assert doc.content_path == "/path/to/document.txt"
        assert doc.content is None
        assert doc.has_content is True

    def test_to_dict_and_from_dict(self, project_id: ProjectId, valid_content: bytes):
        """Test serialization round-trip."""
        # Arrange
        doc = Document.create(
            project_id=project_id,
            content=valid_content,
            filename="test.txt",
            metadata={"key": "value"},
        ).unwrap()
        doc.set_extracted_text("Test text")

        # Act
        doc_dict = doc.to_dict()
        reconstructed = Document.from_dict(doc_dict)

        # Assert
        assert reconstructed.id == doc.id
        assert reconstructed.project_id == doc.project_id
        assert reconstructed.filename == doc.filename
        assert reconstructed.extracted_text == doc.extracted_text
        assert reconstructed.metadata == doc.metadata


# ═══════════════════════════════════════════════════════════════════════════════
# DETECTION RESULT ENTITY
# ═══════════════════════════════════════════════════════════════════════════════


class TestDetectionResult:
    """Test DetectionResult entity."""

    @pytest.fixture
    def document_id(self) -> DocumentId:
        """Create a document ID for testing."""
        return DocumentId.create(str(uuid4())).unwrap()

    @pytest.fixture
    def text_span(self) -> TextSpan:
        """Create a text span for testing."""
        return TextSpan.create(0, 10, "John Smith").unwrap()

    def test_create_valid_detection(
        self, document_id: DocumentId, text_span: TextSpan
    ):
        """Test creating a valid detection result."""
        # Arrange
        confidence = ConfidenceScore.create(0.95).unwrap()

        # Act
        result = DetectionResult.create(
            document_id=document_id,
            category=PERSON_NAME,
            value="John Smith",
            span=text_span,
            confidence=confidence,
        )

        # Assert
        assert result.is_ok()
        detection = result.unwrap()
        assert detection.document_id == document_id
        assert detection.category == PERSON_NAME
        assert detection.original_value == "John Smith"
        assert detection.span == text_span
        assert detection.confidence == confidence
        assert detection.normalized_value == "john smith"  # normalized
        assert detection.needs_review is False  # high confidence
        assert detection.reviewed is False

    def test_create_low_confidence_marks_for_review(
        self, document_id: DocumentId, text_span: TextSpan
    ):
        """Test that low confidence detections are marked for review."""
        # Arrange
        low_confidence = ConfidenceScore.create(0.5).unwrap()

        # Act
        result = DetectionResult.create(
            document_id=document_id,
            category=PERSON_NAME,
            value="John Smith",
            span=text_span,
            confidence=low_confidence,
        )

        # Assert
        assert result.is_ok()
        detection = result.unwrap()
        assert detection.needs_review is True
        assert detection.reviewed is False

    def test_mark_reviewed_approved(
        self, document_id: DocumentId, text_span: TextSpan
    ):
        """Test marking detection as reviewed and approved."""
        # Arrange
        low_confidence = ConfidenceScore.create(0.5).unwrap()
        detection = DetectionResult.create(
            document_id=document_id,
            category=PERSON_NAME,
            value="John Smith",
            span=text_span,
            confidence=low_confidence,
        ).unwrap()
        initial_version = detection.version

        # Act
        detection.mark_reviewed(approved=True)

        # Assert
        assert detection.reviewed is True
        assert detection.needs_review is False
        assert detection.version == initial_version + 1

    def test_mark_reviewed_rejected(
        self, document_id: DocumentId, text_span: TextSpan
    ):
        """Test marking detection as reviewed but rejected."""
        # Arrange
        confidence = ConfidenceScore.create(0.95).unwrap()
        detection = DetectionResult.create(
            document_id=document_id,
            category=PERSON_NAME,
            value="John Smith",
            span=text_span,
            confidence=confidence,
        ).unwrap()

        # Act
        detection.mark_reviewed(approved=False)

        # Assert
        assert detection.reviewed is True
        assert detection.needs_review is True

    def test_update_category(
        self, document_id: DocumentId, text_span: TextSpan
    ):
        """Test updating category after review."""
        # Arrange
        confidence = ConfidenceScore.create(0.95).unwrap()
        detection = DetectionResult.create(
            document_id=document_id,
            category=PERSON_NAME,
            value="admin@example.com",
            span=text_span,
            confidence=confidence,
        ).unwrap()
        initial_version = detection.version

        # Act
        detection.update_category(EMAIL)

        # Assert
        assert detection.category == EMAIL
        assert detection.version == initial_version + 1

    def test_is_high_confidence_property(
        self, document_id: DocumentId, text_span: TextSpan
    ):
        """Test is_high_confidence property."""
        # Arrange
        high = DetectionResult.create(
            document_id=document_id,
            category=PERSON_NAME,
            value="John",
            span=text_span,
            confidence=ConfidenceScore.create(0.95).unwrap(),
        ).unwrap()
        low = DetectionResult.create(
            document_id=document_id,
            category=PERSON_NAME,
            value="John",
            span=text_span,
            confidence=ConfidenceScore.create(0.5).unwrap(),
        ).unwrap()

        # Act & Assert
        assert high.is_high_confidence is True
        assert low.is_high_confidence is False

    def test_is_actionable_property(
        self, document_id: DocumentId, text_span: TextSpan
    ):
        """Test is_actionable property."""
        # Arrange
        high_confidence = DetectionResult.create(
            document_id=document_id,
            category=PERSON_NAME,
            value="John",
            span=text_span,
            confidence=ConfidenceScore.create(0.95).unwrap(),
        ).unwrap()

        low_confidence_not_reviewed = DetectionResult.create(
            document_id=document_id,
            category=PERSON_NAME,
            value="John",
            span=text_span,
            confidence=ConfidenceScore.create(0.5).unwrap(),
        ).unwrap()

        low_confidence_reviewed = DetectionResult.create(
            document_id=document_id,
            category=PERSON_NAME,
            value="John",
            span=text_span,
            confidence=ConfidenceScore.create(0.5).unwrap(),
        ).unwrap()
        low_confidence_reviewed.mark_reviewed(approved=True)

        # Act & Assert
        assert high_confidence.is_actionable is True
        assert low_confidence_not_reviewed.is_actionable is False
        assert low_confidence_reviewed.is_actionable is True

    def test_to_dict_and_from_dict(
        self, document_id: DocumentId, text_span: TextSpan
    ):
        """Test serialization round-trip."""
        # Arrange
        confidence = ConfidenceScore.create(0.95).unwrap()
        detection = DetectionResult.create(
            document_id=document_id,
            category=PERSON_NAME,
            value="John Smith",
            span=text_span,
            confidence=confidence,
            metadata={"source": "NER"},
        ).unwrap()

        # Act
        detection_dict = detection.to_dict()
        reconstructed = DetectionResult.from_dict(detection_dict)

        # Assert
        assert reconstructed.id == detection.id
        assert reconstructed.document_id == detection.document_id
        assert reconstructed.category == detection.category
        assert reconstructed.original_value == detection.original_value
        assert reconstructed.confidence.value == detection.confidence.value
        assert reconstructed.metadata == detection.metadata
