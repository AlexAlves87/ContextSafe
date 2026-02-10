"""
Unit tests for anonymization service.

Tests alias generation, consistency, and text anonymization.

Traceability:
- Contract: CNT-T3-ANONYMIZATION-ADAPTER-001
- Implementation: anonymization_adapter.py
"""

import pytest

from contextsafe.infrastructure.nlp.anonymization_adapter import (
    InMemoryAnonymizationAdapter,
    ALIAS_PREFIXES,
    get_anonymization_service,
)
from contextsafe.application.ports import NerDetection
from contextsafe.domain.shared.value_objects import (
    PiiCategory,
    ConfidenceScore,
    TextSpan,
)


class TestAliasGeneration:
    """Tests for alias generation functionality."""

    @pytest.fixture
    def adapter(self):
        """Create fresh anonymization adapter for each test."""
        return InMemoryAnonymizationAdapter()

    @pytest.fixture
    def project_id(self):
        return "test-project-123"

    @pytest.mark.asyncio
    async def test_creates_alias_with_correct_prefix(self, adapter, project_id):
        """Should create alias with category-specific prefix."""
        alias = await adapter.get_or_create_alias(
            category="PERSON_NAME",
            original_value="Juan Pérez",
            project_id=project_id,
        )

        assert alias.startswith("Persona_")
        assert alias == "Persona_001"

    @pytest.mark.asyncio
    async def test_sequential_numbering(self, adapter, project_id):
        """Should increment alias numbers sequentially."""
        alias1 = await adapter.get_or_create_alias("PHONE", "+34 666 111 222", project_id)
        alias2 = await adapter.get_or_create_alias("PHONE", "+34 666 333 444", project_id)
        alias3 = await adapter.get_or_create_alias("PHONE", "+34 666 555 666", project_id)

        assert alias1 == "Tel_001"
        assert alias2 == "Tel_002"
        assert alias3 == "Tel_003"

    @pytest.mark.asyncio
    async def test_same_value_returns_same_alias(self, adapter, project_id):
        """Should return same alias for repeated values."""
        value = "juan.perez@email.com"

        alias1 = await adapter.get_or_create_alias("EMAIL", value, project_id)
        alias2 = await adapter.get_or_create_alias("EMAIL", value, project_id)
        alias3 = await adapter.get_or_create_alias("EMAIL", value, project_id)

        assert alias1 == alias2 == alias3 == "Email_001"

    @pytest.mark.asyncio
    async def test_case_insensitive_for_names(self, adapter, project_id):
        """Should treat names as case-insensitive."""
        alias1 = await adapter.get_or_create_alias("PERSON_NAME", "Juan García", project_id)
        alias2 = await adapter.get_or_create_alias("PERSON_NAME", "JUAN GARCÍA", project_id)
        alias3 = await adapter.get_or_create_alias("PERSON_NAME", "juan garcía", project_id)

        assert alias1 == alias2 == alias3 == "Persona_001"

    @pytest.mark.asyncio
    async def test_case_insensitive_for_ids(self, adapter, project_id):
        """Should treat DNI/NIE as case-insensitive (Corrección #5).

        The control letter in Spanish DNI/NIE is case-insensitive in practice.
        "12345678Z" and "12345678z" are the SAME DNI and should get the same alias.
        """
        alias1 = await adapter.get_or_create_alias("DNI", "12345678Z", project_id)
        alias2 = await adapter.get_or_create_alias("DNI", "12345678z", project_id)

        # These should be the SAME (case-insensitive normalization)
        assert alias1 == "DNI_001"
        assert alias2 == "DNI_001"  # Same alias for same DNI

    @pytest.mark.asyncio
    async def test_separate_counters_per_category(self, adapter, project_id):
        """Should maintain separate counters per category."""
        await adapter.get_or_create_alias("PERSON_NAME", "Juan", project_id)
        await adapter.get_or_create_alias("EMAIL", "a@b.com", project_id)
        alias_name = await adapter.get_or_create_alias("PERSON_NAME", "María", project_id)
        alias_email = await adapter.get_or_create_alias("EMAIL", "c@d.com", project_id)

        assert alias_name == "Persona_002"  # Second person
        assert alias_email == "Email_002"   # Second email

    @pytest.mark.asyncio
    async def test_separate_glossaries_per_project(self, adapter):
        """Should maintain separate glossaries per project."""
        alias_p1 = await adapter.get_or_create_alias("PERSON_NAME", "Juan", "project-1")
        alias_p2 = await adapter.get_or_create_alias("PERSON_NAME", "Juan", "project-2")

        # Same value but different projects should get same numbered alias
        # since they start fresh
        assert alias_p1 == "Persona_001"
        assert alias_p2 == "Persona_001"

        # Verify they're in different glossaries
        glossary_p1 = await adapter.get_glossary("project-1")
        glossary_p2 = await adapter.get_glossary("project-2")
        assert "PERSON_NAME" in glossary_p1
        assert "PERSON_NAME" in glossary_p2

    @pytest.mark.asyncio
    async def test_all_category_prefixes(self, adapter, project_id):
        """Should use correct prefix for all categories."""
        for category, expected_prefix in ALIAS_PREFIXES.items():
            alias = await adapter.get_or_create_alias(
                category=category,
                original_value=f"test_{category}",
                project_id=project_id,
            )
            assert alias.startswith(expected_prefix + "_"), \
                f"Category {category} should start with {expected_prefix}_"

    @pytest.mark.asyncio
    async def test_unknown_category_uses_abbreviation(self, adapter, project_id):
        """Should use abbreviated category name for unknown categories."""
        alias = await adapter.get_or_create_alias(
            category="UNKNOWN_TYPE",
            original_value="some value",
            project_id=project_id,
        )

        # Should use first 3 characters
        assert alias == "UNK_001"


class TestTextAnonymization:
    """Tests for full text anonymization functionality."""

    @pytest.fixture
    def adapter(self):
        return InMemoryAnonymizationAdapter()

    @pytest.fixture
    def project_id(self):
        return "test-project-456"

    def _make_detection(
        self,
        category: str,
        value: str,
        start: int,
        end: int,
        confidence: float = 0.9,
    ) -> NerDetection:
        """Helper to create NerDetection objects."""
        # TextSpan.create returns Result, extract the Ok value
        span_result = TextSpan.create(start, end, value)
        span = span_result.value  # Extract from Ok
        return NerDetection(
            category=PiiCategory(category),
            value=value,
            span=span,
            confidence=ConfidenceScore(confidence),
        )

    @pytest.mark.asyncio
    async def test_empty_text_returns_empty(self, adapter, project_id):
        """Should handle empty text gracefully."""
        result = await adapter.anonymize_text("", [], project_id)

        assert result.original_text == ""
        assert result.anonymized_text == ""
        assert result.replacements == []

    @pytest.mark.asyncio
    async def test_no_detections_returns_original(self, adapter, project_id):
        """Should return original text when no entities detected."""
        text = "This text has no PII data."
        result = await adapter.anonymize_text(text, [], project_id)

        assert result.original_text == text
        assert result.anonymized_text == text
        assert result.replacements == []

    @pytest.mark.asyncio
    async def test_single_entity_replacement(self, adapter, project_id):
        """Should correctly replace a single entity."""
        text = "Contact: juan@email.com for info."
        detections = [
            self._make_detection("EMAIL", "juan@email.com", 9, 23),
        ]

        result = await adapter.anonymize_text(text, detections, project_id)

        assert result.anonymized_text == "Contact: Email_001 for info."
        assert len(result.replacements) == 1
        assert result.replacements[0].original_value == "juan@email.com"
        assert result.replacements[0].alias == "Email_001"

    @pytest.mark.asyncio
    async def test_multiple_entity_replacement(self, adapter, project_id):
        """Should correctly replace multiple entities."""
        text = "Paciente: Juan Pérez, Tel: +34 666 123 456"
        # Positions: Juan Pérez is at 10-20, phone is at 27-42
        detections = [
            self._make_detection("PERSON_NAME", "Juan Pérez", 10, 20),
            self._make_detection("PHONE", "+34 666 123 456", 27, 42),
        ]

        result = await adapter.anonymize_text(text, detections, project_id)

        assert "Persona_001" in result.anonymized_text
        assert "Tel_001" in result.anonymized_text
        assert "Juan Pérez" not in result.anonymized_text
        assert "+34 666 123 456" not in result.anonymized_text

    @pytest.mark.asyncio
    async def test_replacement_maintains_text_structure(self, adapter, project_id):
        """Should maintain text structure after replacement."""
        text = "Name: John, Email: john@test.com, Phone: 123456789"
        detections = [
            self._make_detection("PERSON_NAME", "John", 6, 10),
            self._make_detection("EMAIL", "john@test.com", 19, 32),
            self._make_detection("PHONE", "123456789", 41, 50),
        ]

        result = await adapter.anonymize_text(text, detections, project_id)

        # Verify structure is maintained
        assert result.anonymized_text.startswith("Name: ")
        assert ", Email: " in result.anonymized_text
        assert ", Phone: " in result.anonymized_text

    @pytest.mark.asyncio
    async def test_consistent_replacement_same_entity(self, adapter, project_id):
        """Should use same alias for repeated entity values."""
        text = "Juan called Juan and Juan answered."
        # Same name appears three times
        detections = [
            self._make_detection("PERSON_NAME", "Juan", 0, 4),
            self._make_detection("PERSON_NAME", "Juan", 12, 16),
            self._make_detection("PERSON_NAME", "Juan", 21, 25),
        ]

        result = await adapter.anonymize_text(text, detections, project_id)

        # All "Juan" should be replaced with the same alias
        assert result.anonymized_text.count("Persona_001") == 3
        assert "Juan" not in result.anonymized_text


class TestGlossaryManagement:
    """Tests for glossary management functionality."""

    @pytest.fixture
    def adapter(self):
        return InMemoryAnonymizationAdapter()

    @pytest.mark.asyncio
    async def test_get_glossary_returns_copy(self, adapter):
        """Should return a copy, not the actual glossary."""
        project_id = "test-project"
        await adapter.get_or_create_alias("EMAIL", "a@b.com", project_id)

        glossary1 = await adapter.get_glossary(project_id)
        glossary2 = await adapter.get_glossary(project_id)

        # Modify one
        glossary1["EMAIL"]["modified"] = "test"

        # Other should be unaffected
        assert "modified" not in glossary2.get("EMAIL", {})

    @pytest.mark.asyncio
    async def test_clear_project_glossary(self, adapter):
        """Should clear glossary for a specific project."""
        await adapter.get_or_create_alias("EMAIL", "a@b.com", "project-1")
        await adapter.get_or_create_alias("EMAIL", "c@d.com", "project-2")

        adapter.clear_project_glossary("project-1")

        # Project 1 should be empty
        glossary1 = await adapter.get_glossary("project-1")
        assert glossary1 == {}

        # Project 2 should be unaffected
        glossary2 = await adapter.get_glossary("project-2")
        assert "EMAIL" in glossary2


class TestGlobalInstance:
    """Tests for global service instance."""

    def test_get_anonymization_service_returns_instance(self):
        """Should return an anonymization service instance."""
        service = get_anonymization_service()
        assert isinstance(service, InMemoryAnonymizationAdapter)

    def test_get_anonymization_service_returns_same_instance(self):
        """Should return the same instance on repeated calls."""
        service1 = get_anonymization_service()
        service2 = get_anonymization_service()
        assert service1 is service2
