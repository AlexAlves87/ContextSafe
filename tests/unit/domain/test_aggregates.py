"""
Unit tests for domain aggregates.

Tests:
- DocumentAggregate
- Glossary
- Project
"""
import pytest
from uuid import uuid4

from contextsafe.domain.document_processing.aggregates.document_aggregate import (
    DocumentAggregate,
)
from contextsafe.domain.shared.value_objects import (
    AnonymizationLevel,
    DocumentState,
    ProjectId,
)
from contextsafe.domain.shared.value_objects.anonymization_level import BASIC, INTERMEDIATE
from contextsafe.domain.shared.value_objects.document_state import (
    PENDING,
    INGESTED,
    DETECTING,
    DETECTED,
    ANONYMIZING,
    ANONYMIZED,
    FAILED,
)
from contextsafe.domain.shared.errors import DocumentError, StateTransitionError


# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENT AGGREGATE
# ═══════════════════════════════════════════════════════════════════════════════


class TestDocumentAggregate:
    """Test DocumentAggregate."""

    @pytest.fixture
    def project_id(self) -> ProjectId:
        """Create a project ID for testing."""
        return ProjectId.create(str(uuid4())).unwrap()

    @pytest.fixture
    def valid_content(self) -> bytes:
        """Create valid document content."""
        return b"This is a test document with some content."

    @pytest.fixture
    def aggregate(self, project_id: ProjectId, valid_content: bytes) -> DocumentAggregate:
        """Create a document aggregate for testing."""
        return DocumentAggregate.create(
            project_id=project_id,
            content=valid_content,
            filename="test.txt",
        ).unwrap()

    def test_create_valid_aggregate(self, project_id: ProjectId, valid_content: bytes):
        """Test creating a valid document aggregate."""
        # Arrange & Act
        result = DocumentAggregate.create(
            project_id=project_id,
            content=valid_content,
            filename="test.txt",
        )

        # Assert
        assert result.is_ok()
        aggregate = result.unwrap()
        assert aggregate.document.project_id == project_id
        assert aggregate.state == PENDING
        assert aggregate.extracted_text is None
        assert aggregate.anonymized_text is None
        assert aggregate.detection_count == 0

    def test_create_rejects_invalid_document(self, project_id: ProjectId):
        """Test that invalid document creation fails."""
        # Arrange & Act
        result = DocumentAggregate.create(
            project_id=project_id,
            content=b"",  # empty content
            filename="test.txt",
        )

        # Assert
        assert result.is_err()
        assert isinstance(result.unwrap_err(), DocumentError)

    def test_transition_to_valid_state(self, aggregate: DocumentAggregate):
        """Test valid state transition."""
        # Arrange & Act
        result = aggregate.transition_to(INGESTED)

        # Assert
        assert result.is_ok()
        assert aggregate.state == INGESTED

    def test_transition_to_invalid_state_fails(self, aggregate: DocumentAggregate):
        """Test that invalid state transition fails."""
        # Arrange - start in PENDING
        # Act - try to go directly to ANONYMIZED (skipping intermediate states)
        result = aggregate.transition_to(ANONYMIZED)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, StateTransitionError)
        assert aggregate.state == PENDING  # state unchanged

    def test_mark_ingested(self, aggregate: DocumentAggregate):
        """Test marking document as ingested."""
        # Arrange
        extracted_text = "This is the extracted text content."
        initial_version = aggregate.version

        # Act
        result = aggregate.mark_ingested(extracted_text)

        # Assert
        assert result.is_ok()
        assert aggregate.state == INGESTED
        assert aggregate.extracted_text == extracted_text
        assert aggregate.document.extracted_text == extracted_text
        assert aggregate.version == initial_version + 1

    def test_start_detection(self, aggregate: DocumentAggregate):
        """Test starting detection phase."""
        # Arrange
        aggregate.mark_ingested("Test text")

        # Act
        result = aggregate.start_detection()

        # Assert
        assert result.is_ok()
        assert aggregate.state == DETECTING

    def test_complete_detection(self, aggregate: DocumentAggregate):
        """Test completing detection phase."""
        # Arrange
        aggregate.mark_ingested("Test text")
        aggregate.start_detection()
        initial_version = aggregate.version

        # Act
        result = aggregate.complete_detection(detection_count=5)

        # Assert
        assert result.is_ok()
        assert aggregate.state == DETECTED
        assert aggregate.detection_count == 5
        assert aggregate.version == initial_version + 1

    def test_start_anonymization(self, aggregate: DocumentAggregate):
        """Test starting anonymization phase."""
        # Arrange
        aggregate.mark_ingested("Test text")
        aggregate.start_detection()
        aggregate.complete_detection(5)

        # Act
        result = aggregate.start_anonymization(INTERMEDIATE)

        # Assert
        assert result.is_ok()
        assert aggregate.state == ANONYMIZING
        assert aggregate.anonymization_level == INTERMEDIATE

    def test_complete_anonymization(self, aggregate: DocumentAggregate):
        """Test completing anonymization phase."""
        # Arrange
        aggregate.mark_ingested("Test text")
        aggregate.start_detection()
        aggregate.complete_detection(5)
        aggregate.start_anonymization(INTERMEDIATE)
        anonymized_text = "This is anonymized text with Persona_1."
        initial_version = aggregate.version

        # Act
        result = aggregate.complete_anonymization(anonymized_text)

        # Assert
        assert result.is_ok()
        assert aggregate.state == ANONYMIZED
        assert aggregate.anonymized_text == anonymized_text
        assert aggregate.version == initial_version + 1

    def test_fail(self, aggregate: DocumentAggregate):
        """Test marking document as failed."""
        # Arrange
        error_message = "Text extraction failed: Invalid format"
        initial_version = aggregate.version

        # Act
        aggregate.fail(error_message)

        # Assert
        assert aggregate.state == FAILED
        assert aggregate.error_message == error_message
        assert aggregate.version == initial_version + 1

    def test_is_completed_property(self, aggregate: DocumentAggregate):
        """Test is_completed property."""
        # Arrange & Act & Assert
        assert aggregate.is_completed is False

        aggregate.mark_ingested("Test")
        assert aggregate.is_completed is False

        aggregate.start_detection()
        aggregate.complete_detection(5)
        aggregate.start_anonymization(BASIC)
        aggregate.complete_anonymization("Anonymized")

        assert aggregate.is_completed is True

    def test_is_failed_property(self, aggregate: DocumentAggregate):
        """Test is_failed property."""
        # Arrange & Act & Assert
        assert aggregate.is_failed is False

        aggregate.fail("Error occurred")

        assert aggregate.is_failed is True

    def test_can_be_exported_property(self, aggregate: DocumentAggregate):
        """Test can_be_exported property."""
        # Arrange & Act & Assert
        assert aggregate.can_be_exported is False

        # Complete the full workflow
        aggregate.mark_ingested("Test text")
        aggregate.start_detection()
        aggregate.complete_detection(5)
        aggregate.start_anonymization(BASIC)
        aggregate.complete_anonymization("Anonymized text")

        assert aggregate.can_be_exported is True

    def test_full_workflow(self, aggregate: DocumentAggregate):
        """Test complete document processing workflow."""
        # Arrange
        original_text = "John Smith lives in Madrid."
        anonymized_text = "Persona_1 lives in Direccion_1."

        # Act - Execute complete workflow
        # 1. Ingest
        result1 = aggregate.mark_ingested(original_text)
        assert result1.is_ok()
        assert aggregate.state == INGESTED

        # 2. Detect
        result2 = aggregate.start_detection()
        assert result2.is_ok()
        assert aggregate.state == DETECTING

        result3 = aggregate.complete_detection(detection_count=2)
        assert result3.is_ok()
        assert aggregate.state == DETECTED

        # 3. Anonymize
        result4 = aggregate.start_anonymization(BASIC)
        assert result4.is_ok()
        assert aggregate.state == ANONYMIZING

        result5 = aggregate.complete_anonymization(anonymized_text)
        assert result5.is_ok()
        assert aggregate.state == ANONYMIZED

        # Assert - Final state
        assert aggregate.is_completed is True
        assert aggregate.can_be_exported is True
        assert aggregate.extracted_text == original_text
        assert aggregate.anonymized_text == anonymized_text
        assert aggregate.detection_count == 2
        assert aggregate.anonymization_level == BASIC

    def test_to_dict_and_from_dict(self, aggregate: DocumentAggregate):
        """Test serialization round-trip."""
        # Arrange
        aggregate.mark_ingested("Test text")
        aggregate.start_detection()
        aggregate.complete_detection(3)

        # Act
        aggregate_dict = aggregate.to_dict()
        reconstructed = DocumentAggregate.from_dict(aggregate_dict)

        # Assert
        assert reconstructed.id == aggregate.id
        assert reconstructed.state == aggregate.state
        assert reconstructed.extracted_text == aggregate.extracted_text
        assert reconstructed.detection_count == aggregate.detection_count
        assert reconstructed.document.filename == aggregate.document.filename

    def test_version_increments_on_state_changes(self, aggregate: DocumentAggregate):
        """Test that version increments on each state change."""
        # Arrange
        initial_version = aggregate.version

        # Act
        aggregate.mark_ingested("Test")
        v1 = aggregate.version

        aggregate.start_detection()
        v2 = aggregate.version

        aggregate.complete_detection(5)
        v3 = aggregate.version

        # Assert
        assert v1 == initial_version + 1
        assert v2 == v1 + 1
        assert v3 == v2 + 1

    def test_cannot_transition_from_terminal_states(self, aggregate: DocumentAggregate):
        """Test that terminal states (ANONYMIZED, FAILED) cannot transition."""
        # Arrange - Complete the workflow
        aggregate.mark_ingested("Test")
        aggregate.start_detection()
        aggregate.complete_detection(5)
        aggregate.start_anonymization(BASIC)
        aggregate.complete_anonymization("Anonymized")

        # Act - Try to transition from ANONYMIZED
        result = aggregate.transition_to(DETECTING)

        # Assert
        assert result.is_err()
        assert aggregate.state == ANONYMIZED

    def test_failed_state_is_terminal(self, aggregate: DocumentAggregate):
        """Test that FAILED state cannot transition to other states."""
        # Arrange
        aggregate.fail("Error occurred")

        # Act
        result = aggregate.transition_to(INGESTED)

        # Assert
        assert result.is_err()
        assert aggregate.state == FAILED
