"""
Shared Hypothesis generators for property-based tests.

This module provides reusable generators for all domain types
used in ContextSafe property-based testing.

Traceability:
- Source: outputs/phase3/step2_validation/pbt_properties.yaml
- Phase: Phase 4 Step 3 (Verification & Release)
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from hypothesis import strategies as st

from contextsafe.domain.shared.types import DomainEvent, Entity
from contextsafe.domain.shared.value_objects import (
    Alias,
    ConfidenceScore,
    DocumentId,
    EntityId,
    PiiCategory,
    PiiCategoryEnum,
    ProjectId,
    TextSpan,
)


# ==============================================================================
# BASIC GENERATORS
# ==============================================================================


@st.composite
def uuid_gen(draw) -> UUID:
    """Generate random UUIDs."""
    return uuid4()


@st.composite
def document_id_gen(draw) -> DocumentId:
    """Generate random DocumentId value objects."""
    uuid_val = str(uuid4())
    result = DocumentId.create(uuid_val)
    return result.unwrap()


@st.composite
def project_id_gen(draw) -> ProjectId:
    """Generate random ProjectId value objects."""
    uuid_val = str(uuid4())
    result = ProjectId.create(uuid_val)
    return result.unwrap()


@st.composite
def entity_id_gen(draw) -> EntityId:
    """Generate random EntityId value objects."""
    uuid_val = str(uuid4())
    result = EntityId.create(uuid_val)
    return result.unwrap()


# ==============================================================================
# VALUE OBJECT GENERATORS
# ==============================================================================


@st.composite
def confidence_score_gen(draw) -> ConfidenceScore:
    """Generate valid ConfidenceScore (0.0 to 1.0)."""
    value = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    result = ConfidenceScore.create(value)
    return result.unwrap()


@st.composite
def text_span_gen(draw) -> TextSpan:
    """Generate valid TextSpan with start < end and matching text."""
    start = draw(st.integers(min_value=0, max_value=1000))
    length = draw(st.integers(min_value=1, max_value=100))
    end = start + length
    # Generate text matching the span length
    text = draw(st.text(min_size=length, max_size=length))
    result = TextSpan.create(start, end, text)
    return result.unwrap()


@st.composite
def pii_category_gen(draw) -> PiiCategory:
    """Generate random PiiCategory from all available categories."""
    category_enum = draw(st.sampled_from(list(PiiCategoryEnum)))
    result = PiiCategory.from_string(category_enum.value)
    return result.unwrap()


@st.composite
def alias_gen(draw) -> Alias:
    """
    Generate valid Alias value objects.

    Aliases follow the pattern for their category:
    - PERSON_NAME: Persona_N
    - ORGANIZATION: Organizacion_N
    - etc.
    """
    category = draw(pii_category_gen())
    index = draw(st.integers(min_value=1, max_value=9999))

    # Generate alias using factory method
    result = Alias.generate(category, index)
    return result.unwrap()


# ==============================================================================
# ENTITY AND AGGREGATE GENERATORS
# ==============================================================================


@st.composite
def domain_event_gen(draw) -> DomainEvent:
    """Generate base DomainEvent instances."""
    event_id = draw(uuid_gen())
    occurred_at = datetime.now(timezone.utc)

    # Create a concrete subclass for testing
    class TestDomainEvent(DomainEvent):
        """Test event implementation."""
        pass

    return TestDomainEvent(event_id=event_id, occurred_at=occurred_at)


@st.composite
def entity_gen(draw) -> Entity[UUID]:
    """Generate base Entity instances."""
    entity_id = draw(uuid_gen())

    # Create a concrete subclass for testing
    class TestEntity(Entity[UUID]):
        """Test entity implementation."""
        pass

    return TestEntity(id=entity_id)


# ==============================================================================
# RESULT TYPE GENERATORS
# ==============================================================================


@st.composite
def result_int_gen(draw):
    """
    Generate Result[int, str] for testing monad laws.

    Returns either Ok(int) or Err(str).
    """
    from contextsafe.domain.shared.types import Err, Ok

    if draw(st.booleans()):
        return Ok(draw(st.integers()))
    else:
        return Err(draw(st.text(min_size=1)))


@st.composite
def result_str_gen(draw):
    """
    Generate Result[str, str] for testing map operations.

    Returns either Ok(str) or Err(str).
    """
    from contextsafe.domain.shared.types import Err, Ok

    if draw(st.booleans()):
        return Ok(draw(st.text()))
    else:
        return Err(draw(st.text(min_size=1)))


# ==============================================================================
# COMPOSITE GENERATORS FOR COMPLEX SCENARIOS
# ==============================================================================


@st.composite
def pii_entity_data_gen(draw):
    """
    Generate data for PII entity construction.

    Returns dict with: {
        'text': str,
        'category': PiiCategory,
        'span': TextSpan,
        'confidence': ConfidenceScore
    }
    """
    text = draw(st.text(min_size=1, max_size=50))
    category = draw(pii_category_gen())
    span = draw(text_span_gen())
    confidence = draw(confidence_score_gen())

    return {
        'text': text,
        'category': category,
        'span': span,
        'confidence': confidence,
    }


@st.composite
def detection_entities_gen(draw):
    """
    Generate a list of PII entities for detection testing.

    Returns a list of 1-10 entity data dictionaries.
    """
    entities = draw(st.lists(
        pii_entity_data_gen(),
        min_size=1,
        max_size=10
    ))
    return entities


# ==============================================================================
# STRATEGIES EXPORT
# ==============================================================================

# Export all generators as strategies for direct use in tests
uuid_strategy = uuid_gen()
document_id_strategy = document_id_gen()
project_id_strategy = project_id_gen()
entity_id_strategy = entity_id_gen()
confidence_score_strategy = confidence_score_gen()
text_span_strategy = text_span_gen()
pii_category_strategy = pii_category_gen()
alias_strategy = alias_gen()
domain_event_strategy = domain_event_gen()
entity_strategy = entity_gen()
result_int_strategy = result_int_gen()
result_str_strategy = result_str_gen()
pii_entity_data_strategy = pii_entity_data_gen()
detection_entities_strategy = detection_entities_gen()
