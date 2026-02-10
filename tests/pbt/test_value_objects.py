"""
Property-based tests for value objects.

Tests all value objects for invariant compliance:
- DocumentId, ProjectId, EntityId (UUIDs)
- ConfidenceScore (0.0 to 1.0 range)
- TextSpan (valid ranges)
- Alias (non-empty, pattern matching)

Traceability:
- Properties: PBT-012 to PBT-020
- Contracts: CNT-T0-VO-001 to CNT-T0-VO-009
- Source: outputs/phase3/step2_validation/pbt_properties.yaml
"""
from __future__ import annotations

import re
from uuid import UUID

import icontract
import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

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

# Import generators from conftest
from .conftest import (
    alias_gen,
    confidence_score_gen,
    document_id_gen,
    entity_id_gen,
    pii_category_gen,
    project_id_gen,
    text_span_gen,
)


# ==============================================================================
# PBT-012: DocumentId is UUID
# ==============================================================================


@given(document_id_gen())
def test_document_id_is_uuid(doc_id: DocumentId):
    """
    Test DocumentId always contains a valid UUID string.

    Property: PBT-012
    Contract: CNT-T0-VO-001
    Invariant: INV-001 (value is valid UUID format)
    """
    # DocumentId.value is a string that must be valid UUID format
    assert isinstance(doc_id.value, str)
    assert doc_id.value is not None
    # Verify it can be parsed as UUID
    UUID(doc_id.value)


@given(document_id_gen(), document_id_gen())
def test_document_id_equality(doc_id1: DocumentId, doc_id2: DocumentId):
    """
    Test DocumentId equality is based on UUID value.

    Property: PBT-012
    Contract: CNT-T0-VO-001
    """
    if doc_id1.value == doc_id2.value:
        assert doc_id1 == doc_id2
    else:
        assert doc_id1 != doc_id2


# ==============================================================================
# PBT-013: ProjectId is UUID
# ==============================================================================


@given(project_id_gen())
def test_project_id_is_uuid(proj_id: ProjectId):
    """
    Test ProjectId always contains a valid UUID string.

    Property: PBT-013
    Contract: CNT-T0-VO-002
    Invariant: INV-001 (value is valid UUID format)
    """
    # ProjectId.value is a string that must be valid UUID format
    assert isinstance(proj_id.value, str)
    assert proj_id.value is not None
    # Verify it can be parsed as UUID
    UUID(proj_id.value)


@given(project_id_gen(), project_id_gen())
def test_project_id_equality(proj_id1: ProjectId, proj_id2: ProjectId):
    """
    Test ProjectId equality is based on UUID value.

    Property: PBT-013
    Contract: CNT-T0-VO-002
    """
    if proj_id1.value == proj_id2.value:
        assert proj_id1 == proj_id2
    else:
        assert proj_id1 != proj_id2


# ==============================================================================
# PBT-014: EntityId is valid UUID
# ==============================================================================


@given(entity_id_gen())
def test_entity_id_is_valid(entity_id: EntityId):
    """
    Test EntityId always contains a valid UUID string.

    Property: PBT-014
    Contract: CNT-T0-VO-003
    """
    assert isinstance(entity_id.value, str)
    assert entity_id.value is not None
    # Verify it can be parsed as UUID
    UUID(entity_id.value)


@given(entity_id_gen(), entity_id_gen())
def test_entity_id_equality(entity_id1: EntityId, entity_id2: EntityId):
    """
    Test EntityId equality is based on value.

    Property: PBT-014
    Contract: CNT-T0-VO-003
    """
    if entity_id1.value == entity_id2.value:
        assert entity_id1 == entity_id2
    else:
        assert entity_id1 != entity_id2


@given(entity_id_gen())
def test_entity_id_str_representation(entity_id: EntityId):
    """
    Test EntityId string representation matches value.

    Property: PBT-014
    Contract: CNT-T0-VO-003
    """
    assert str(entity_id) == entity_id.value


# ==============================================================================
# PBT-015: ConfidenceScore in range [0.0, 1.0]
# ==============================================================================


@given(confidence_score_gen())
def test_confidence_score_in_range(score: ConfidenceScore):
    """
    Test ConfidenceScore value is always between 0.0 and 1.0.

    Property: PBT-015
    Contract: CNT-T0-VO-007
    Invariant: INV-001 (0.0 <= value <= 1.0)
    """
    assert 0.0 <= score.value <= 1.0


@given(confidence_score_gen())
def test_confidence_score_not_nan(score: ConfidenceScore):
    """
    Test ConfidenceScore is never NaN or infinity.

    Property: PBT-015
    Contract: CNT-T0-VO-007
    """
    import math
    assert not math.isnan(score.value)
    assert not math.isinf(score.value)


# ==============================================================================
# PBT-016: ConfidenceScore rejects invalid values
# ==============================================================================


@given(st.floats().filter(lambda x: x < 0.0 or x > 1.0))
def test_confidence_score_rejects_invalid(value: float):
    """
    Test ConfidenceScore.create() rejects values outside [0.0, 1.0].

    Property: PBT-016
    Contract: CNT-T0-VO-007
    Invariant: INV-001 enforcement
    """
    import math

    # Skip NaN and infinity (they're technically outside range but special cases)
    assume(not math.isnan(value))
    assume(not math.isinf(value))

    result = ConfidenceScore.create(value)
    assert result.is_err()


@given(st.floats(min_value=-1000.0, max_value=-0.01))
def test_confidence_score_rejects_negative(value: float):
    """
    Test ConfidenceScore.create() rejects negative values.

    Property: PBT-016
    Contract: CNT-T0-VO-007
    """
    result = ConfidenceScore.create(value)
    assert result.is_err()


@given(st.floats(min_value=1.01, max_value=1000.0))
def test_confidence_score_rejects_above_one(value: float):
    """
    Test ConfidenceScore.create() rejects values above 1.0.

    Property: PBT-016
    Contract: CNT-T0-VO-007
    """
    result = ConfidenceScore.create(value)
    assert result.is_err()


# ==============================================================================
# PBT-017: TextSpan has valid range
# ==============================================================================


@given(text_span_gen())
def test_text_span_valid_range(span: TextSpan):
    """
    Test TextSpan always has 0 <= start < end.

    Property: PBT-017
    Contract: CNT-T0-VO-008
    Invariant: INV-001 (0 <= start < end)
    """
    assert 0 <= span.start < span.end


@given(text_span_gen())
def test_text_span_positive_length(span: TextSpan):
    """
    Test TextSpan always has positive length.

    Property: PBT-017
    Contract: CNT-T0-VO-008
    """
    assert span.length > 0
    assert span.length == span.end - span.start


# ==============================================================================
# PBT-018: TextSpan rejects invalid ranges
# ==============================================================================


@given(st.integers(min_value=0, max_value=1000), st.integers(min_value=0, max_value=1000))
def test_text_span_rejects_invalid_ranges(start: int, end: int):
    """
    Test TextSpan.create() rejects start >= end.

    Property: PBT-018
    Contract: CNT-T0-VO-008
    Invariant: INV-001 enforcement
    """
    assume(start >= end)

    result = TextSpan.create(start, end, "dummy")
    assert result.is_err()


@given(st.integers(min_value=-1000, max_value=-1))
def test_text_span_rejects_negative_start(start: int):
    """
    Test TextSpan rejects negative start values.

    Property: PBT-018
    Contract: CNT-T0-VO-008
    """
    end = start + 10

    result = TextSpan.create(start, end, "x" * 10 if end > 0 else "x")
    assert result.is_err()


@given(st.integers(min_value=0, max_value=1000))
def test_text_span_rejects_equal_start_end(value: int):
    """
    Test TextSpan rejects start == end (zero length).

    Property: PBT-018
    Contract: CNT-T0-VO-008
    """
    result = TextSpan.create(value, value, "")
    assert result.is_err()


# ==============================================================================
# PBT-019: Alias value is non-empty
# ==============================================================================


@given(alias_gen())
def test_alias_non_empty(alias: Alias):
    """
    Test Alias value is never empty.

    Property: PBT-019
    Contract: CNT-T0-VO-009
    Invariant: INV-001 (len(value) > 0)
    """
    assert len(alias.value) > 0
    assert alias.value.strip() != ""


@given(alias_gen())
def test_alias_has_category(alias: Alias):
    """
    Test Alias always has a valid PII category.

    Property: PBT-019
    Contract: CNT-T0-VO-009
    """
    assert isinstance(alias.category, PiiCategory)
    assert alias.category.value in list(PiiCategoryEnum)


# ==============================================================================
# PBT-020: Alias pattern matches category
# ==============================================================================


@given(alias_gen())
def test_alias_pattern_matches_category(alias: Alias):
    """
    Test Alias value matches the expected pattern for its category.

    Patterns:
    - PERSON_NAME: Persona_N
    - ORGANIZATION: Organizacion_N
    - ADDRESS: Direccion_N
    - etc.

    Property: PBT-020
    Contract: CNT-T0-VO-009
    Invariant: INV-002 (pattern matches category)
    """
    # Define pattern mapping (must match ALIAS_PATTERNS in pii_category.py)
    pattern_map = {
        PiiCategoryEnum.PERSON_NAME: r'^Persona_\d+$',
        PiiCategoryEnum.ORGANIZATION: r'^Org_\d+$',
        PiiCategoryEnum.ADDRESS: r'^Dir_\d+$',
        PiiCategoryEnum.LOCATION: r'^Lugar_\d+$',
        PiiCategoryEnum.POSTAL_CODE: r'^CP_\d+$',
        PiiCategoryEnum.DNI_NIE: r'^ID_\d+$',
        PiiCategoryEnum.PASSPORT: r'^Pasaporte_\d+$',
        PiiCategoryEnum.PHONE: r'^Tel_\d+$',
        PiiCategoryEnum.EMAIL: r'^Email_\d+$',
        PiiCategoryEnum.BANK_ACCOUNT: r'^Cuenta_\d+$',
        PiiCategoryEnum.IBAN: r'^IBAN_\d+$',
        PiiCategoryEnum.CREDIT_CARD: r'^Tarjeta_\d+$',
        PiiCategoryEnum.DATE: r'^Fecha_\d+$',
        PiiCategoryEnum.MEDICAL_RECORD: r'^HistoriaMedica_\d+$',
        PiiCategoryEnum.LICENSE_PLATE: r'^Matricula_\d+$',
        PiiCategoryEnum.SOCIAL_SECURITY: r'^NSS_\d+$',
        PiiCategoryEnum.PROFESSIONAL_ID: r'^IdProf_\d+$',
        PiiCategoryEnum.CASE_NUMBER: r'^Proc_\d+$',
        PiiCategoryEnum.PLATFORM: r'^Plataforma_\d+$',
        PiiCategoryEnum.IP_ADDRESS: r'^IP_\d+$',
        PiiCategoryEnum.ID_SUPPORT: r'^Soporte_\d+$',
        PiiCategoryEnum.NIG: r'^NIG_\d+$',
        PiiCategoryEnum.ECLI: r'^ECLI_\d+$',
        PiiCategoryEnum.CSV: r'^CSV_\d+$',
        PiiCategoryEnum.HEALTH_ID: r'^CIP_\d+$',
        PiiCategoryEnum.CADASTRAL_REF: r'^RefCat_\d+$',
        PiiCategoryEnum.EMPLOYER_ID: r'^CCC_\d+$',
    }

    # Access the enum value from the PiiCategory wrapper
    category_enum = alias.category.value
    expected_pattern = pattern_map.get(category_enum)
    assert expected_pattern is not None, f"No pattern defined for {category_enum}"
    assert re.match(expected_pattern, alias.value), \
        f"Alias '{alias.value}' does not match pattern {expected_pattern}"


@given(pii_category_gen(), st.integers(min_value=1, max_value=9999))
def test_pii_category_generate_alias(category: PiiCategory, index: int):
    """
    Test PiiCategory.generate_alias() produces valid aliases.

    Property: PBT-020
    Contract: CNT-T0-VO-009
    """
    alias_value = category.generate_alias(index)

    # Verify it's non-empty
    assert len(alias_value) > 0

    # Verify index appears in the alias
    assert str(index) in alias_value


# ==============================================================================
# ADDITIONAL VALUE OBJECT PROPERTIES
# ==============================================================================


@given(confidence_score_gen(), confidence_score_gen())
def test_confidence_score_comparison(score1: ConfidenceScore, score2: ConfidenceScore):
    """
    Test ConfidenceScore comparison operators.

    Property: Additional coverage
    """
    if score1.value < score2.value:
        assert score1 < score2
        assert score1 <= score2
        assert score2 > score1
        assert score2 >= score1
    elif score1.value > score2.value:
        assert score1 > score2
        assert score1 >= score2
        assert score2 < score1
        assert score2 <= score1
    else:
        assert score1 <= score2
        assert score1 >= score2


@given(text_span_gen(), st.integers(min_value=0, max_value=2000))
def test_text_span_contains(span: TextSpan, position: int):
    """
    Test TextSpan.contains() method with a position.

    Property: Additional coverage
    """
    # contains() takes a position (int), not a span
    if span.start <= position < span.end:
        assert span.contains(position)
    else:
        assert not span.contains(position)


@given(alias_gen(), alias_gen())
def test_alias_equality(alias1: Alias, alias2: Alias):
    """
    Test Alias equality is based on value and category.

    Property: Additional coverage
    """
    if alias1.value == alias2.value and alias1.category == alias2.category:
        assert alias1 == alias2
        assert hash(alias1) == hash(alias2)
    else:
        assert alias1 != alias2
