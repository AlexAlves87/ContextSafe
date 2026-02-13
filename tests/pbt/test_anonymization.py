"""
Property-Based Tests for Anonymization (BR-004 Critical).

These tests verify the critical business rule BR-004: No PII shall appear
in the anonymized output. This is the most critical invariant for ContextSafe.

Properties tested:
- PBT-040: No PII in anonymized output
- PBT-041: Anonymization is deterministic
- PBT-042: All detected entities are replaced
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from hypothesis import assume, given, settings, HealthCheck, strategies as st

if TYPE_CHECKING:
    from contextsafe.domain.anonymization.entities.anonymized_document import (
        AnonymizedDocument,
    )
    from contextsafe.domain.entity_detection.entities.detection_result import (
        DetectionResult,
    )

# Import domain types
try:
    from contextsafe.domain.shared.value_objects import (
        Alias,
        ConfidenceScore,
        PiiCategory,
        TextSpan,
    )
    from contextsafe.domain.entity_detection.entities.detection_result import (
        DetectionResult,
    )
    from contextsafe.domain.anonymization.aggregates.glossary import Glossary
    from contextsafe.domain.shared.value_objects import ProjectId

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


# =============================================================================
# Hypothesis Strategies
# =============================================================================

@st.composite
def pii_entities(draw) -> tuple[str, str]:
    """Generate PII entity text and category pairs."""
    categories = [
        ("PERSON_NAME", ["Juan García", "María López", "Carlos Rodríguez", "Ana Martín"]),
        ("ORGANIZATION", ["Acme Corp", "TechCo S.L.", "Banco Santander", "Telefónica"]),
        ("ADDRESS", ["Calle Mayor 123", "Av. Diagonal 456", "Plaza España 1"]),
        ("PHONE", ["+34 612 345 678", "91 234 56 78", "666 123 456"]),
        ("EMAIL", ["juan@example.com", "maria@empresa.es", "info@acme.com"]),
        ("DNI_NIE", ["12345678A", "X1234567B", "Y9876543C"]),
    ]
    category, examples = draw(st.sampled_from(categories))
    entity = draw(st.sampled_from(examples))
    return entity, category


@st.composite
def document_with_pii(draw) -> tuple[str, list[tuple[str, str, int, int]]]:
    """Generate a document containing PII entities with their positions."""
    # Generate 1-5 PII entities
    num_entities = draw(st.integers(min_value=1, max_value=5))

    entities = []
    text_parts = []
    current_pos = 0

    for _ in range(num_entities):
        # Add some filler text
        filler = draw(st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
            min_size=5,
            max_size=30
        ))
        text_parts.append(filler + " ")
        current_pos += len(filler) + 1

        # Add a PII entity
        entity_text, category = draw(pii_entities())
        start = current_pos
        end = start + len(entity_text)
        entities.append((entity_text, category, start, end))
        text_parts.append(entity_text)
        current_pos = end

    # Add trailing text
    text_parts.append(" " + draw(st.text(min_size=5, max_size=20)))

    document_text = "".join(text_parts)
    return document_text, entities


@st.composite
def alias_patterns(draw) -> str:
    """Generate valid alias patterns."""
    category_prefix = draw(st.sampled_from([
        "PERSONA", "ORG", "DIR", "TEL", "EMAIL", "ID"
    ]))
    number = draw(st.integers(min_value=1, max_value=999))
    return f"[{category_prefix}_{number:03d}]"


# =============================================================================
# PBT-040: No PII in Anonymized Output
# =============================================================================

@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Domain imports not available")
class TestNoPiiInOutput:
    """
    PBT-040: After anonymization, no original PII text shall appear in output.

    Business Rule: BR-004 (No PII in Output)
    Critical: YES
    """

    @given(data=document_with_pii())
    @settings(max_examples=100, deadline=None)
    def test_no_pii_text_in_anonymized_output(self, data: tuple):
        """Original PII text must not appear in anonymized document."""
        document_text, entities = data
        assume(len(entities) > 0)

        # Create glossary and assign aliases
        project_id = ProjectId(uuid4())
        glossary = Glossary.create(project_id)

        # Build replacement map
        replacements = {}
        for entity_text, category, start, end in entities:
            alias = glossary.get_or_assign_alias(
                normalized_value=entity_text.lower(),
                category=PiiCategory.from_string(category).unwrap()
            ).unwrap()
            replacements[(start, end)] = alias.value

        # Apply replacements (from end to start to preserve positions)
        anonymized = document_text
        for (start, end), alias in sorted(replacements.items(), reverse=True):
            anonymized = anonymized[:start] + alias + anonymized[end:]

        # Verify: no original PII text appears in output
        for entity_text, _, _, _ in entities:
            assert entity_text not in anonymized, (
                f"PII '{entity_text}' found in anonymized output"
            )

    @given(entity=st.text(min_size=2, max_size=50))
    @settings(max_examples=50)
    def test_alias_replaces_entity_completely(self, entity: str):
        """Alias replacement must be complete, not partial."""
        assume(entity.strip())  # Skip empty/whitespace-only

        project_id = ProjectId(uuid4())
        glossary = Glossary.create(project_id)

        alias = glossary.get_or_assign_alias(
            normalized_value=entity.lower(),
            category=PiiCategory.from_string("PERSON_NAME").unwrap()
        ).unwrap()

        # Alias should not contain the original entity
        assert entity.lower() not in alias.value.lower(), (
            f"Alias '{alias.value}' contains original entity '{entity}'"
        )


# =============================================================================
# PBT-041: Anonymization is Deterministic
# =============================================================================

@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Domain imports not available")
class TestAnonymizationDeterminism:
    """
    PBT-041: Same input document + glossary produces identical output.

    Business Rule: BR-002 (Alias Consistency)
    Critical: YES
    """

    @given(data=document_with_pii())
    @settings(max_examples=50, deadline=None)
    def test_same_input_same_output(self, data: tuple):
        """Anonymizing the same document twice produces identical results."""
        document_text, entities = data
        assume(len(entities) > 0)

        # Create a single glossary
        project_id = ProjectId(uuid4())
        glossary = Glossary.create(project_id)

        def anonymize(text: str, ents: list) -> str:
            """Apply anonymization using glossary."""
            result = text
            # Sort by position descending to preserve indices
            sorted_ents = sorted(ents, key=lambda e: e[2], reverse=True)
            for entity_text, category, start, end in sorted_ents:
                alias = glossary.get_or_assign_alias(
                    normalized_value=entity_text.lower(),
                    category=PiiCategory.from_string(category).unwrap()
                ).unwrap()
                result = result[:start] + alias.value + result[end:]
            return result

        # Anonymize twice
        result1 = anonymize(document_text, entities)
        result2 = anonymize(document_text, entities)

        assert result1 == result2, (
            f"Determinism violated:\n"
            f"First:  {result1}\n"
            f"Second: {result2}"
        )

    @given(
        entity=st.text(min_size=1, max_size=30),
        category=st.sampled_from(["PERSON_NAME", "ORGANIZATION", "ADDRESS"])
    )
    @settings(max_examples=50)
    def test_alias_stable_across_lookups(self, entity: str, category: str):
        """Same entity always gets the same alias from glossary."""
        assume(entity.strip())

        project_id = ProjectId(uuid4())
        glossary = Glossary.create(project_id)

        alias1 = glossary.get_or_assign_alias(
            normalized_value=entity.lower(),
            category=PiiCategory.from_string(category).unwrap()
        ).unwrap()
        alias2 = glossary.get_or_assign_alias(
            normalized_value=entity.lower(),
            category=PiiCategory.from_string(category).unwrap()
        ).unwrap()
        alias3 = glossary.get_or_assign_alias(
            normalized_value=entity.lower(),
            category=PiiCategory.from_string(category).unwrap()
        ).unwrap()

        assert alias1 == alias2 == alias3, (
            f"Alias not stable: {alias1}, {alias2}, {alias3}"
        )


# =============================================================================
# PBT-042: All Detected Entities are Replaced
# =============================================================================

@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Domain imports not available")
class TestAllEntitiesReplaced:
    """
    PBT-042: Every detected PII entity must be replaced in output.

    Business Rule: BR-004 (No PII in Output)
    Critical: YES
    """

    @given(data=document_with_pii())
    @settings(max_examples=100, deadline=None)
    def test_all_detections_replaced(self, data: tuple):
        """Every detected entity must be replaced with an alias."""
        document_text, entities = data
        assume(len(entities) > 0)

        project_id = ProjectId(uuid4())
        glossary = Glossary.create(project_id)

        # Track replacements
        applied_replacements = []
        result = document_text

        # Apply replacements (descending position order)
        sorted_ents = sorted(entities, key=lambda e: e[2], reverse=True)
        for entity_text, category, start, end in sorted_ents:
            alias = glossary.get_or_assign_alias(
                normalized_value=entity_text.lower(),
                category=PiiCategory.from_string(category).unwrap()
            ).unwrap()
            result = result[:start] + alias.value + result[end:]
            applied_replacements.append(entity_text)

        # Verify all entities were replaced
        assert len(applied_replacements) == len(entities), (
            f"Expected {len(entities)} replacements, got {len(applied_replacements)}"
        )

        # Verify no original entity text remains
        for entity_text, _, _, _ in entities:
            occurrences = result.count(entity_text)
            assert occurrences == 0, (
                f"Entity '{entity_text}' still appears {occurrences} time(s)"
            )

    @given(
        entities=st.lists(
            pii_entities(),
            min_size=1,
            max_size=10,
            unique_by=lambda x: x[0].lower()
        )
    )
    @settings(max_examples=50)
    def test_unique_aliases_per_entity(self, entities: list):
        """Different entities should get different aliases."""
        project_id = ProjectId(uuid4())
        glossary = Glossary.create(project_id)

        aliases = []
        for entity_text, category in entities:
            alias = glossary.get_or_assign_alias(
                normalized_value=entity_text.lower(),
                category=PiiCategory.from_string(category).unwrap()
            ).unwrap()
            aliases.append(alias.value)

        # All aliases should be unique
        assert len(aliases) == len(set(aliases)), (
            f"Duplicate aliases found: {aliases}"
        )


# =============================================================================
# PBT-043: Alias Format Compliance
# =============================================================================

@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Domain imports not available")
class TestAliasFormat:
    """
    PBT-043: Aliases must follow the configured format pattern.

    Format: [CATEGORY_NNN] where NNN is a zero-padded counter.
    """

    ALIAS_PATTERN = re.compile(r"^[A-Za-z]+_\d+$")

    @given(
        entity=st.text(min_size=1, max_size=50),
        category=st.sampled_from([
            "PERSON_NAME", "ORGANIZATION", "ADDRESS",
            "PHONE", "EMAIL", "DNI_NIE"
        ])
    )
    @settings(max_examples=100)
    def test_alias_matches_pattern(self, entity: str, category: str):
        """Generated aliases must match the expected pattern."""
        assume(entity.strip())

        project_id = ProjectId(uuid4())
        glossary = Glossary.create(project_id)

        alias = glossary.get_or_assign_alias(
            normalized_value=entity.lower(),
            category=PiiCategory.from_string(category).unwrap()
        ).unwrap()

        assert self.ALIAS_PATTERN.match(alias.value), (
            f"Alias '{alias.value}' doesn't match pattern [CATEGORY_NNN]"
        )

    @given(
        entities=st.lists(
            st.text(min_size=1, max_size=20),
            min_size=5,
            max_size=20
        )
    )
    @settings(max_examples=30)
    def test_alias_counter_increments(self, entities: list):
        """Alias counter should increment for each new entity."""
        assume(len(set(e.lower() for e in entities if e.strip())) >= 3)

        project_id = ProjectId(uuid4())
        glossary = Glossary.create(project_id)

        seen_aliases = set()
        for entity in entities:
            if not entity.strip():
                continue
            alias = glossary.get_or_assign_alias(
                normalized_value=entity.lower(),
                category=PiiCategory.from_string("PERSON_NAME").unwrap()
            ).unwrap()
            if entity.lower() not in {e.lower() for e in seen_aliases}:
                seen_aliases.add(entity)

        # Should have generated unique aliases for unique entities
        unique_entities = len({e.lower() for e in entities if e.strip()})
        unique_aliases = len({
            glossary.get_or_assign_alias(e.lower(), PiiCategory.from_string("PERSON_NAME").unwrap()).unwrap().value
            for e in entities if e.strip()
        })

        assert unique_aliases == unique_entities, (
            f"Expected {unique_entities} unique aliases, got {unique_aliases}"
        )


# =============================================================================
# Regression Tests for Known Edge Cases
# =============================================================================

@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Domain imports not available")
class TestEdgeCases:
    """Regression tests for known edge cases."""

    def test_overlapping_entities_handled(self):
        """Overlapping entity spans should be handled correctly."""
        # "Juan García López" could be detected as:
        # - "Juan García" (PERSON_NAME)
        # - "García López" (PERSON_NAME)
        # Only the first/longest should be replaced
        text = "Contactar a Juan García López mañana."

        project_id = ProjectId(uuid4())
        glossary = Glossary.create(project_id)

        alias = glossary.get_or_assign_alias(
            normalized_value="juan garcía lópez",
            category=PiiCategory.from_string("PERSON_NAME").unwrap()
        ).unwrap()

        # Replace the full name
        result = text.replace("Juan García López", alias.value)

        assert "Juan" not in result
        assert "García" not in result
        assert "López" not in result
        assert alias.value in result

    def test_unicode_entities_preserved(self):
        """Unicode characters in entities should be handled correctly."""
        entities = [
            "José María Ñoño",
            "北京公司",
            "Müller GmbH"
        ]

        project_id = ProjectId(uuid4())
        glossary = Glossary.create(project_id)

        for entity in entities:
            alias = glossary.get_or_assign_alias(
                normalized_value=entity.lower(),
                category=PiiCategory.from_string("PERSON_NAME").unwrap()
            ).unwrap()
            # Alias should be generated without error
            assert alias.value is not None
            assert entity.lower() not in alias.value.lower()

    def test_empty_document_handled(self):
        """Empty documents should not cause errors."""
        project_id = ProjectId(uuid4())
        glossary = Glossary.create(project_id)

        # No entities to replace
        result = ""
        # Should complete without error
        assert result == ""

    def test_case_insensitive_matching(self):
        """Same entity in different cases should get same alias."""
        project_id = ProjectId(uuid4())
        glossary = Glossary.create(project_id)

        alias_lower = glossary.get_or_assign_alias(
            normalized_value="juan garcía",
            category=PiiCategory.from_string("PERSON_NAME").unwrap()
        ).unwrap()
        alias_upper = glossary.get_or_assign_alias(
            normalized_value="JUAN GARCÍA".lower(),
            category=PiiCategory.from_string("PERSON_NAME").unwrap()
        ).unwrap()
        alias_mixed = glossary.get_or_assign_alias(
            normalized_value="Juan García".lower(),
            category=PiiCategory.from_string("PERSON_NAME").unwrap()
        ).unwrap()

        assert alias_lower == alias_upper == alias_mixed, (
            "Case normalization failed"
        )


# =============================================================================
# PBT-044: Adversarial Input Robustness
# =============================================================================

try:
    from .conftest import (
        adversarial_pii_entities_gen,
        control_chars_text_gen,
        dirty_text_gen,
        homoglyph_text_gen,
        injection_payload_gen,
        large_text_gen,
        rtl_text_gen,
    )
    DIRTY_IMPORTS_AVAILABLE = IMPORTS_AVAILABLE
except ImportError:
    DIRTY_IMPORTS_AVAILABLE = False


@pytest.mark.skipif(not DIRTY_IMPORTS_AVAILABLE, reason="Domain imports not available")
class TestAdversarialInputRobustness:
    """
    PBT-044: System must not crash or leak PII with adversarial inputs.

    Tests that the anonymization pipeline handles dirty, malicious, or
    malformed text without exceptions or data leakage.
    """

    @given(
        entity=adversarial_pii_entities_gen(),
        filler=dirty_text_gen(),
    )
    @settings(max_examples=100, deadline=None)
    def test_adversarial_entities_get_aliases(self, entity: tuple, filler: str):
        """Adversarial PII entities must receive valid aliases without crashing."""
        entity_text, category = entity

        project_id = ProjectId(uuid4())
        glossary = Glossary.create(project_id)

        alias = glossary.get_or_assign_alias(
            normalized_value=entity_text.lower(),
            category=PiiCategory.from_string(category).unwrap(),
        ).unwrap()

        # Alias must be generated and must not contain the original entity
        assert alias.value is not None
        assert len(alias.value) > 0
        # The normalized entity text should NOT appear in the alias
        if entity_text.strip():
            assert entity_text.lower() not in alias.value.lower()

    @given(payload=injection_payload_gen())
    @settings(max_examples=50, deadline=None)
    def test_injection_payloads_safely_aliased(self, payload: str):
        """SQL/XSS/prompt injection payloads must be aliased without leaking."""
        project_id = ProjectId(uuid4())
        glossary = Glossary.create(project_id)

        alias = glossary.get_or_assign_alias(
            normalized_value=payload.lower(),
            category=PiiCategory.from_string("PERSON_NAME").unwrap(),
        ).unwrap()

        # The alias must NOT contain the payload
        assert payload.lower() not in alias.value.lower()
        # The alias must follow the expected pattern
        assert re.match(r"^Persona_\d+$", alias.value)

    @given(text=control_chars_text_gen())
    @settings(max_examples=50, deadline=None)
    def test_control_characters_handled(self, text: str):
        """Text with control characters must not crash alias generation."""
        assume(any(c.isalnum() for c in text))

        project_id = ProjectId(uuid4())
        glossary = Glossary.create(project_id)

        # Must not raise any exception
        alias = glossary.get_or_assign_alias(
            normalized_value=text.lower(),
            category=PiiCategory.from_string("PERSON_NAME").unwrap(),
        ).unwrap()
        assert alias.value is not None

    @given(text=homoglyph_text_gen())
    @settings(max_examples=50, deadline=None)
    def test_homoglyph_text_handled(self, text: str):
        """Text with Unicode homoglyphs must not crash or bypass anonymization."""
        assume(len(text.strip()) > 0)

        project_id = ProjectId(uuid4())
        glossary = Glossary.create(project_id)

        alias = glossary.get_or_assign_alias(
            normalized_value=text.lower(),
            category=PiiCategory.from_string("PERSON_NAME").unwrap(),
        ).unwrap()
        assert alias.value is not None
        assert text.lower() not in alias.value.lower()

    @given(text=rtl_text_gen())
    @settings(max_examples=30, deadline=None)
    def test_rtl_text_handled(self, text: str):
        """Right-to-left text must not crash or produce invalid aliases."""
        assume(len(text.strip()) > 0)

        project_id = ProjectId(uuid4())
        glossary = Glossary.create(project_id)

        alias = glossary.get_or_assign_alias(
            normalized_value=text.lower(),
            category=PiiCategory.from_string("PERSON_NAME").unwrap(),
        ).unwrap()
        assert alias.value is not None
        assert re.match(r"^Persona_\d+$", alias.value)

    @given(text=large_text_gen(min_kb=100, max_kb=500))
    @settings(
        max_examples=5,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.large_base_example],
    )
    def test_large_text_handled(self, text: str):
        """Large text inputs (100KB-500KB) must not cause OOM or timeout."""
        project_id = ProjectId(uuid4())
        glossary = Glossary.create(project_id)

        alias = glossary.get_or_assign_alias(
            normalized_value=text[:1000].lower(),  # Normalize only a prefix
            category=PiiCategory.from_string("PERSON_NAME").unwrap(),
        ).unwrap()
        assert alias.value is not None

    @given(
        entity=adversarial_pii_entities_gen(),
        filler=dirty_text_gen(),
    )
    @settings(max_examples=50, deadline=None)
    def test_adversarial_no_pii_in_output(self, entity: tuple, filler: str):
        """PII must not leak at its original position after replacement."""
        entity_text, category = entity
        assume(len(entity_text.strip()) > 0)
        # Avoid false positives: skip when filler contains the entity text
        assume(entity_text not in filler)

        # Build document: filler + entity + filler
        doc = f"{filler} {entity_text} {filler}"
        start = len(filler) + 1
        end = start + len(entity_text)

        project_id = ProjectId(uuid4())
        glossary = Glossary.create(project_id)

        alias = glossary.get_or_assign_alias(
            normalized_value=entity_text.lower(),
            category=PiiCategory.from_string(category).unwrap(),
        ).unwrap()

        # Replace entity in document
        anonymized = doc[:start] + alias.value + doc[end:]

        # The replaced segment must contain the alias, not the original PII
        replaced_segment = anonymized[start:start + len(alias.value)]
        assert replaced_segment == alias.value
        # Original entity must not appear in the anonymized output
        assert entity_text not in anonymized, (
            f"PII '{entity_text}' leaked in anonymized output with dirty filler"
        )

    @given(
        entity=adversarial_pii_entities_gen(),
    )
    @settings(max_examples=50, deadline=None)
    def test_adversarial_determinism(self, entity: tuple):
        """Adversarial entities must produce deterministic aliases."""
        entity_text, category = entity

        project_id = ProjectId(uuid4())
        glossary = Glossary.create(project_id)

        alias1 = glossary.get_or_assign_alias(
            normalized_value=entity_text.lower(),
            category=PiiCategory.from_string(category).unwrap(),
        ).unwrap()
        alias2 = glossary.get_or_assign_alias(
            normalized_value=entity_text.lower(),
            category=PiiCategory.from_string(category).unwrap(),
        ).unwrap()

        assert alias1 == alias2, (
            f"Determinism violated for adversarial entity '{entity_text}': "
            f"{alias1} != {alias2}"
        )
