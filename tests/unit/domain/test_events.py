"""
Unit tests for domain events.

Tests:
- DocumentIngested
- PiiDetected
- AliasAssigned
- DocumentAnonymized
"""
import pytest
from datetime import datetime
from uuid import uuid4

from contextsafe.domain.shared.events import (
    DocumentIngested,
    PiiDetected,
    AliasAssigned,
    DocumentAnonymized,
)


# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENT INGESTED EVENT
# ═══════════════════════════════════════════════════════════════════════════════


class TestDocumentIngested:
    """Test DocumentIngested event."""

    def test_create_event(self):
        """Test creating a DocumentIngested event."""
        # Arrange
        doc_id = str(uuid4())
        project_id = str(uuid4())
        correlation_id = str(uuid4())

        # Act
        event = DocumentIngested.create(
            document_id=doc_id,
            project_id=project_id,
            filename="test.txt",
            text_length=1000,
            format_detected="text/plain",
            correlation_id=correlation_id,
        )

        # Assert
        assert event.document_id == doc_id
        assert event.project_id == project_id
        assert event.filename == "test.txt"
        assert event.text_length == 1000
        assert event.format_detected == "text/plain"
        assert event.correlation_id == correlation_id
        assert event.event_id != ""  # auto-generated
        assert isinstance(event.occurred_at, datetime)

    def test_event_is_immutable(self):
        """Test that event is immutable."""
        # Arrange
        event = DocumentIngested.create(
            document_id=str(uuid4()),
            project_id=str(uuid4()),
            filename="test.txt",
            text_length=100,
            format_detected="text/plain",
        )

        # Act & Assert
        with pytest.raises(Exception):  # FrozenInstanceError
            event.document_id = "new-id"  # type: ignore

    def test_to_dict(self):
        """Test converting event to dictionary."""
        # Arrange
        doc_id = str(uuid4())
        project_id = str(uuid4())
        event = DocumentIngested.create(
            document_id=doc_id,
            project_id=project_id,
            filename="test.txt",
            text_length=1000,
            format_detected="text/plain",
        )

        # Act
        event_dict = event.to_dict()

        # Assert
        assert event_dict["document_id"] == doc_id
        assert event_dict["project_id"] == project_id
        assert event_dict["filename"] == "test.txt"
        assert event_dict["text_length"] == 1000
        assert event_dict["format_detected"] == "text/plain"
        assert "event_id" in event_dict
        assert "occurred_at" in event_dict

    def test_unique_event_ids(self):
        """Test that each event gets a unique ID."""
        # Arrange & Act
        event1 = DocumentIngested.create(
            document_id=str(uuid4()),
            project_id=str(uuid4()),
            filename="test1.txt",
            text_length=100,
            format_detected="text/plain",
        )
        event2 = DocumentIngested.create(
            document_id=str(uuid4()),
            project_id=str(uuid4()),
            filename="test2.txt",
            text_length=200,
            format_detected="text/plain",
        )

        # Assert
        assert event1.event_id != event2.event_id


# ═══════════════════════════════════════════════════════════════════════════════
# PII DETECTED EVENT
# ═══════════════════════════════════════════════════════════════════════════════


class TestPiiDetected:
    """Test PiiDetected event."""

    def test_create_event(self):
        """Test creating a PiiDetected event."""
        # Arrange
        doc_id = str(uuid4())
        project_id = str(uuid4())
        entities_by_category = {
            "PERSON_NAME": 5,
            "EMAIL": 3,
            "PHONE": 2,
        }

        # Act
        event = PiiDetected.create(
            document_id=doc_id,
            project_id=project_id,
            total_entities=10,
            entities_by_category=entities_by_category,
            low_confidence_count=2,
            processing_time_ms=500,
        )

        # Assert
        assert event.document_id == doc_id
        assert event.project_id == project_id
        assert event.total_entities == 10
        assert event.entities_by_category == entities_by_category
        assert event.low_confidence_count == 2
        assert event.processing_time_ms == 500

    def test_event_is_immutable(self):
        """Test that event is immutable."""
        # Arrange
        event = PiiDetected.create(
            document_id=str(uuid4()),
            project_id=str(uuid4()),
            total_entities=5,
            entities_by_category={"PERSON_NAME": 5},
        )

        # Act & Assert
        with pytest.raises(Exception):  # FrozenInstanceError
            event.total_entities = 10  # type: ignore

    def test_to_dict(self):
        """Test converting event to dictionary."""
        # Arrange
        doc_id = str(uuid4())
        project_id = str(uuid4())
        entities_by_category = {"PERSON_NAME": 5, "EMAIL": 3}
        event = PiiDetected.create(
            document_id=doc_id,
            project_id=project_id,
            total_entities=8,
            entities_by_category=entities_by_category,
            low_confidence_count=1,
        )

        # Act
        event_dict = event.to_dict()

        # Assert
        assert event_dict["document_id"] == doc_id
        assert event_dict["total_entities"] == 8
        assert event_dict["entities_by_category"] == entities_by_category
        assert event_dict["low_confidence_count"] == 1

    def test_empty_entities_by_category(self):
        """Test event with no entities detected."""
        # Arrange & Act
        event = PiiDetected.create(
            document_id=str(uuid4()),
            project_id=str(uuid4()),
            total_entities=0,
            entities_by_category={},
        )

        # Assert
        assert event.total_entities == 0
        assert event.entities_by_category == {}


# ═══════════════════════════════════════════════════════════════════════════════
# ALIAS ASSIGNED EVENT
# ═══════════════════════════════════════════════════════════════════════════════


class TestAliasAssigned:
    """Test AliasAssigned event."""

    def test_create_event(self):
        """Test creating an AliasAssigned event."""
        # Arrange
        project_id = str(uuid4())
        entity_id = str(uuid4())

        # Act
        event = AliasAssigned.create(
            project_id=project_id,
            entity_id=entity_id,
            original_value="John Smith",
            alias="Persona_1",
            category="PERSON_NAME",
        )

        # Assert
        assert event.project_id == project_id
        assert event.entity_id == entity_id
        assert event.original_value == "John Smith"
        assert event.alias == "Persona_1"
        assert event.category == "PERSON_NAME"

    def test_event_is_immutable(self):
        """Test that event is immutable."""
        # Arrange
        event = AliasAssigned.create(
            project_id=str(uuid4()),
            entity_id=str(uuid4()),
            original_value="John",
            alias="Persona_1",
            category="PERSON_NAME",
        )

        # Act & Assert
        with pytest.raises(Exception):
            event.alias = "Persona_2"  # type: ignore

    def test_to_dict(self):
        """Test converting event to dictionary."""
        # Arrange
        event = AliasAssigned.create(
            project_id=str(uuid4()),
            entity_id=str(uuid4()),
            original_value="john@example.com",
            alias="Email_1",
            category="EMAIL",
        )

        # Act
        event_dict = event.to_dict()

        # Assert
        assert event_dict["original_value"] == "john@example.com"
        assert event_dict["alias"] == "Email_1"
        assert event_dict["category"] == "EMAIL"


# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENT ANONYMIZED EVENT
# ═══════════════════════════════════════════════════════════════════════════════


class TestDocumentAnonymized:
    """Test DocumentAnonymized event."""

    def test_create_event(self):
        """Test creating a DocumentAnonymized event."""
        # Arrange
        doc_id = str(uuid4())
        project_id = str(uuid4())

        # Act
        event = DocumentAnonymized.create(
            document_id=doc_id,
            project_id=project_id,
            anonymization_level="INTERMEDIATE",
            entities_replaced=10,
            processing_time_ms=300,
        )

        # Assert
        assert event.document_id == doc_id
        assert event.project_id == project_id
        assert event.anonymization_level == "INTERMEDIATE"
        assert event.entities_replaced == 10
        assert event.processing_time_ms == 300

    def test_event_is_immutable(self):
        """Test that event is immutable."""
        # Arrange
        event = DocumentAnonymized.create(
            document_id=str(uuid4()),
            project_id=str(uuid4()),
            anonymization_level="BASIC",
            entities_replaced=5,
        )

        # Act & Assert
        with pytest.raises(Exception):
            event.entities_replaced = 10  # type: ignore

    def test_to_dict(self):
        """Test converting event to dictionary."""
        # Arrange
        doc_id = str(uuid4())
        project_id = str(uuid4())
        event = DocumentAnonymized.create(
            document_id=doc_id,
            project_id=project_id,
            anonymization_level="ADVANCED",
            entities_replaced=15,
            processing_time_ms=500,
        )

        # Act
        event_dict = event.to_dict()

        # Assert
        assert event_dict["document_id"] == doc_id
        assert event_dict["project_id"] == project_id
        assert event_dict["anonymization_level"] == "ADVANCED"
        assert event_dict["entities_replaced"] == 15
        assert event_dict["processing_time_ms"] == 500


# ═══════════════════════════════════════════════════════════════════════════════
# EVENT CORRELATION
# ═══════════════════════════════════════════════════════════════════════════════


class TestEventCorrelation:
    """Test event correlation and causation."""

    def test_correlation_id_propagation(self):
        """Test that correlation ID can be propagated across events."""
        # Arrange
        correlation_id = str(uuid4())
        doc_id = str(uuid4())
        project_id = str(uuid4())

        # Act - Create a chain of events with same correlation_id
        event1 = DocumentIngested.create(
            document_id=doc_id,
            project_id=project_id,
            filename="test.txt",
            text_length=100,
            format_detected="text/plain",
            correlation_id=correlation_id,
        )

        event2 = PiiDetected.create(
            document_id=doc_id,
            project_id=project_id,
            total_entities=5,
            entities_by_category={"PERSON_NAME": 5},
            correlation_id=correlation_id,
        )

        event3 = DocumentAnonymized.create(
            document_id=doc_id,
            project_id=project_id,
            anonymization_level="BASIC",
            entities_replaced=5,
            correlation_id=correlation_id,
        )

        # Assert - All events share the same correlation_id
        assert event1.correlation_id == correlation_id
        assert event2.correlation_id == correlation_id
        assert event3.correlation_id == correlation_id

        # But each has unique event_id
        assert event1.event_id != event2.event_id
        assert event2.event_id != event3.event_id
