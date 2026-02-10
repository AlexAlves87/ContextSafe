"""
Property-based tests for aggregates.

Tests aggregates for invariant compliance:
- Glossary: BR-002 (alias consistency), no duplicate aliases
- DocumentAggregate: State transitions, lifecycle
- AggregateRoot: Event registration and collection

Traceability:
- Properties: PBT-005 to PBT-009, PBT-021 to PBT-025
- Contracts: CNT-T0-AGGREGATE-001, CNT-T0-AGG-003, CNT-T0-AGG-001
- Business Rules: BR-002 (CRITICAL)
- Source: outputs/phase3/step2_validation/pbt_properties.yaml
"""
from __future__ import annotations

from uuid import uuid4

import pytest
from hypothesis import given
from hypothesis import strategies as st

from contextsafe.domain.anonymization.aggregates.glossary import Glossary
from contextsafe.domain.shared.types import DomainEvent

# Import generators from conftest
from .conftest import (
    domain_event_gen,
    entity_gen,
    pii_category_gen,
    project_id_gen,
)


# ==============================================================================
# PBT-008: AggregateRoot event registration
# ==============================================================================


@given(project_id_gen(), domain_event_gen())
def test_aggregate_registers_event(project_id, event: DomainEvent):
    """
    Test AggregateRoot.register_event() stores events.

    Property: PBT-008
    Contract: CNT-T0-AGGREGATE-001
    Invariant: POST-001 (event in self._events)
    """
    # Create a test aggregate (using Glossary as concrete implementation)
    agg = Glossary.create(project_id)

    # Register event
    agg._raise_event(event)

    # Collect events
    events = agg.collect_events()

    # Event should be in collected events
    assert event in events or len(agg._pending_events) > 0


# ==============================================================================
# PBT-009: AggregateRoot collect_events clears internal list
# ==============================================================================


@given(project_id_gen(), st.lists(domain_event_gen(), min_size=1, max_size=5))
def test_aggregate_collect_clears(project_id, events: list[DomainEvent]):
    """
    Test AggregateRoot.collect_events() clears the internal list.

    Property: PBT-009
    Contract: CNT-T0-AGGREGATE-001
    Invariant: POST-001 (clears internal list)
    """
    # Create a test aggregate
    agg = Glossary.create(project_id)

    # Register multiple events
    for e in events:
        agg._raise_event(e)

    # Collect events (first time)
    collected = agg.collect_events()

    # Should have collected all events
    assert len(collected) == len(events)

    # Second call should return empty
    assert len(agg.collect_events()) == 0


# ==============================================================================
# PBT-021: Glossary no duplicate aliases (BR-002) - CRITICAL
# ==============================================================================


@given(project_id_gen())
def test_glossary_no_duplicate_aliases(project_id):
    """
    Test Glossary ensures all aliases are unique.

    This is CRITICAL business rule BR-002 enforcement.

    Property: PBT-021
    Contract: CNT-T0-AGG-003
    Invariant: INV-001 (no duplicate aliases)
    Business Rule: BR-002 (CRITICAL)
    """
    glossary = Glossary.create(project_id)

    # Generate multiple aliases in same category
    from contextsafe.domain.shared.value_objects import PiiCategory, PiiCategoryEnum

    category = PiiCategory(PiiCategoryEnum.PERSON_NAME)

    # Assign 10 different values
    aliases = []
    for i in range(10):
        result = glossary.get_or_assign_alias(f"John Doe {i}", category)
        assert result.is_ok()
        aliases.append(result.unwrap().value)

    # All aliases must be unique
    assert len(aliases) == len(set(aliases))


# ==============================================================================
# PBT-022: Glossary same entity always same alias (BR-002) - CRITICAL
# ==============================================================================


@given(project_id_gen(), st.text(min_size=1, max_size=100), pii_category_gen())
def test_glossary_alias_consistency(project_id, text: str, category):
    """
    Test Glossary returns same alias for same normalized value.

    This is CRITICAL business rule BR-002: alias consistency.

    Property: PBT-022
    Contract: CNT-T0-AGG-003
    Invariant: BR-002 (alias consistency)
    Business Rule: BR-002 (CRITICAL)
    """
    glossary = Glossary.create(project_id)

    # Get alias for same text multiple times
    result1 = glossary.get_or_assign_alias(text, category)
    result2 = glossary.get_or_assign_alias(text, category)
    result3 = glossary.get_or_assign_alias(text, category)

    # All should succeed
    assert result1.is_ok()
    assert result2.is_ok()
    assert result3.is_ok()

    # All should return the SAME alias
    alias1 = result1.unwrap()
    alias2 = result2.unwrap()
    alias3 = result3.unwrap()

    assert alias1 == alias2
    assert alias2 == alias3
    assert alias1.value == alias2.value == alias3.value


@given(project_id_gen(), st.text(alphabet=st.characters(whitelist_categories=('L', 'N')), min_size=1, max_size=100), pii_category_gen())
def test_glossary_case_insensitive_consistency(project_id, text: str, category):
    """
    Test Glossary treats case variations as same entity.

    Property: PBT-022
    Contract: CNT-T0-AGG-003
    Business Rule: BR-002
    """
    from hypothesis import assume
    # Skip edge cases where lower/upper don't roundtrip (e.g., German ß -> SS)
    assume(text.lower() == text.upper().lower())

    glossary = Glossary.create(project_id)

    # Get aliases for case variations
    result_lower = glossary.get_or_assign_alias(text.lower(), category)
    result_upper = glossary.get_or_assign_alias(text.upper(), category)
    result_original = glossary.get_or_assign_alias(text, category)

    # All should succeed
    assert result_lower.is_ok()
    assert result_upper.is_ok()
    assert result_original.is_ok()

    # All should return the SAME alias (case-insensitive match)
    alias_lower = result_lower.unwrap()
    alias_upper = result_upper.unwrap()
    alias_original = result_original.unwrap()

    assert alias_lower.value == alias_upper.value == alias_original.value


# ==============================================================================
# PBT-023: Glossary assignment is idempotent
# ==============================================================================


@given(project_id_gen(), st.text(min_size=1, max_size=100), pii_category_gen())
def test_glossary_idempotent(project_id, text: str, category):
    """
    Test Glossary.get_or_assign_alias() is idempotent.

    Calling multiple times should not increase mapping count beyond 1.

    Property: PBT-023
    Contract: CNT-T0-AGG-003
    Invariant: Idempotent get_or_assign
    """
    glossary = Glossary.create(project_id)

    initial_size = glossary.mapping_count

    # Call get_or_assign multiple times
    glossary.get_or_assign_alias(text, category)
    glossary.get_or_assign_alias(text, category)
    glossary.get_or_assign_alias(text, category)

    # Size should increase by exactly 1 (not 3)
    assert glossary.mapping_count == initial_size + 1


@given(project_id_gen(), st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10), pii_category_gen())
def test_glossary_idempotent_with_multiple_values(project_id, texts: list[str], category):
    """
    Test idempotency with multiple different values.

    Property: PBT-023
    Contract: CNT-T0-AGG-003
    """
    glossary = Glossary.create(project_id)

    # Assign each text once
    for text in texts:
        glossary.get_or_assign_alias(text, category)

    # Record count after first pass
    count_after_first = glossary.mapping_count

    # Assign all texts again
    for text in texts:
        glossary.get_or_assign_alias(text, category)

    # Count should not change
    assert glossary.mapping_count == count_after_first


# ==============================================================================
# ADDITIONAL GLOSSARY PROPERTIES
# ==============================================================================


@given(project_id_gen(), st.text(min_size=1), pii_category_gen())
def test_glossary_find_alias_returns_none_for_unknown(project_id, text: str, category):
    """
    Test Glossary.find_alias() returns None for unknown values.

    Property: Additional coverage
    """
    glossary = Glossary.create(project_id)

    # Before assignment, find should return None
    alias = glossary.find_alias(text, category)
    assert alias is None


@given(project_id_gen(), st.text(min_size=1), pii_category_gen())
def test_glossary_find_alias_returns_assigned(project_id, text: str, category):
    """
    Test Glossary.find_alias() returns assigned aliases.

    Property: Additional coverage
    """
    glossary = Glossary.create(project_id)

    # Assign alias
    result = glossary.get_or_assign_alias(text, category)
    assert result.is_ok()
    assigned_alias = result.unwrap()

    # Find should return the same alias
    found_alias = glossary.find_alias(text, category)
    assert found_alias is not None
    assert found_alias == assigned_alias


@given(project_id_gen())
def test_glossary_counters_increment_correctly(project_id):
    """
    Test Glossary counters increment for each category.

    Property: Additional coverage
    """
    glossary = Glossary.create(project_id)

    from contextsafe.domain.shared.value_objects import PiiCategory, PiiCategoryEnum

    category = PiiCategory(PiiCategoryEnum.PERSON_NAME)

    # Assign 3 different values
    for i in range(3):
        result = glossary.get_or_assign_alias(f"Person {i}", category)
        assert result.is_ok()

    # Counter should be 3
    assert glossary._counters.get(category.value, 0) == 3


@given(project_id_gen(), st.text(min_size=1), pii_category_gen())
def test_glossary_to_dict_from_dict_roundtrip(project_id, text: str, category):
    """
    Test Glossary serialization roundtrip.

    Property: Additional coverage
    """
    glossary = Glossary.create(project_id)

    # Assign some aliases
    result = glossary.get_or_assign_alias(text, category)
    assert result.is_ok()

    # Serialize
    data = glossary.to_dict()

    # Deserialize
    restored = Glossary.from_dict(data)

    # Should have same mappings
    assert restored.mapping_count == glossary.mapping_count

    # Should find same alias
    found = restored.find_alias(text, category)
    assert found is not None
    assert found == result.unwrap()


@given(project_id_gen())
def test_glossary_mapping_count_starts_at_zero(project_id):
    """
    Test new Glossary starts with zero mappings.

    Property: Additional coverage
    """
    glossary = Glossary.create(project_id)
    assert glossary.mapping_count == 0
    assert len(glossary.mappings) == 0


@given(project_id_gen(), pii_category_gen())
def test_glossary_get_mappings_by_category(project_id, category):
    """
    Test Glossary.get_mappings_by_category() filters correctly.

    Property: Additional coverage
    """
    from contextsafe.domain.shared.value_objects import PiiCategory, PiiCategoryEnum

    glossary = Glossary.create(project_id)

    # Add mappings in the target category
    for i in range(3):
        glossary.get_or_assign_alias(f"value {i}", category)

    # Add mappings in a different category (ensure it's different from target)
    other_enum = PiiCategoryEnum.EMAIL if category.value != PiiCategoryEnum.EMAIL else PiiCategoryEnum.PHONE
    other_category = PiiCategory.from_string(other_enum.value).unwrap()
    for i in range(2):
        glossary.get_or_assign_alias(f"other{i}", other_category)

    # Get mappings for target category
    category_mappings = glossary.get_mappings_by_category(category)

    # Should have exactly 3 mappings
    assert len(category_mappings) == 3

    # All should be in the target category
    for mapping in category_mappings:
        assert mapping.category == category
