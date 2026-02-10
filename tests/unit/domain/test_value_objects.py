"""
Unit tests for domain value objects.

Tests all value objects in contextsafe.domain.shared.value_objects:
- DocumentId, ProjectId, EntityId
- ConfidenceScore
- TextSpan
- Alias
- PiiCategory
- AnonymizationLevel
- DocumentState
"""
import pytest
from uuid import uuid4

from contextsafe.domain.shared.value_objects import (
    Alias,
    ConfidenceScore,
    DocumentId,
    DocumentState,
    EntityId,
    PiiCategory,
    ProjectId,
    TextSpan,
    AnonymizationLevel,
)
from contextsafe.domain.shared.value_objects.pii_category import (
    PERSON_NAME,
    EMAIL,
    PiiCategoryEnum,
)
from contextsafe.domain.shared.value_objects.document_state import (
    PENDING,
    INGESTED,
    DETECTING,
    DETECTED,
    ANONYMIZING,
    ANONYMIZED,
    FAILED,
    DocumentStateEnum,
)
from contextsafe.domain.shared.value_objects.anonymization_level import (
    BASIC,
    INTERMEDIATE,
    ADVANCED,
    AnonymizationLevelEnum,
)
from contextsafe.domain.shared.errors import (
    InvalidIdError,
    InvalidScoreError,
    InvalidSpanError,
    InvalidAliasError,
    InvalidCategoryError,
    InvalidLevelError,
    InvalidStateError,
)


# ═══════════════════════════════════════════════════════════════════════════════
# ID VALUE OBJECTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestDocumentId:
    """Test DocumentId value object."""

    def test_create_valid_id(self):
        """Test creating a valid DocumentId."""
        valid_uuid = str(uuid4())
        result = DocumentId.create(valid_uuid)

        assert result.is_ok()
        doc_id = result.unwrap()
        assert doc_id.value == valid_uuid
        assert str(doc_id) == valid_uuid

    def test_create_rejects_empty(self):
        """Test that empty string is rejected."""
        result = DocumentId.create("")

        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, InvalidIdError)

    def test_create_rejects_whitespace(self):
        """Test that whitespace-only string is rejected."""
        result = DocumentId.create("   ")

        assert result.is_err()
        assert isinstance(result.unwrap_err(), InvalidIdError)

    def test_create_rejects_invalid_uuid(self):
        """Test that invalid UUID format is rejected."""
        result = DocumentId.create("not-a-uuid")

        assert result.is_err()
        assert isinstance(result.unwrap_err(), InvalidIdError)

    def test_equality(self):
        """Test DocumentId equality."""
        uuid_str = str(uuid4())
        id1 = DocumentId.create(uuid_str).unwrap()
        id2 = DocumentId.create(uuid_str).unwrap()
        id3 = DocumentId.create(str(uuid4())).unwrap()

        assert id1 == id2
        assert id1 != id3

    def test_hash(self):
        """Test DocumentId can be used in sets/dicts."""
        uuid_str = str(uuid4())
        id1 = DocumentId.create(uuid_str).unwrap()
        id2 = DocumentId.create(uuid_str).unwrap()

        id_set = {id1, id2}
        assert len(id_set) == 1


class TestProjectId:
    """Test ProjectId value object."""

    def test_create_valid_id(self):
        """Test creating a valid ProjectId."""
        valid_uuid = str(uuid4())
        result = ProjectId.create(valid_uuid)

        assert result.is_ok()
        assert result.unwrap().value == valid_uuid

    def test_create_rejects_invalid(self):
        """Test that invalid UUID is rejected."""
        result = ProjectId.create("invalid")

        assert result.is_err()
        assert isinstance(result.unwrap_err(), InvalidIdError)


class TestEntityId:
    """Test EntityId value object."""

    def test_create_valid_id(self):
        """Test creating a valid EntityId."""
        valid_uuid = str(uuid4())
        result = EntityId.create(valid_uuid)

        assert result.is_ok()
        assert result.unwrap().value == valid_uuid


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIDENCE SCORE
# ═══════════════════════════════════════════════════════════════════════════════


class TestConfidenceScore:
    """Test ConfidenceScore value object."""

    def test_create_valid_score(self):
        """Test creating a valid confidence score."""
        result = ConfidenceScore.create(0.85)

        assert result.is_ok()
        score = result.unwrap()
        assert score.value == 0.85

    def test_create_rejects_negative(self):
        """Test that negative scores are rejected."""
        result = ConfidenceScore.create(-0.1)

        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, InvalidScoreError)

    def test_create_rejects_above_one(self):
        """Test that scores > 1.0 are rejected."""
        result = ConfidenceScore.create(1.5)

        assert result.is_err()
        assert isinstance(result.unwrap_err(), InvalidScoreError)

    def test_boundary_values(self):
        """Test boundary values 0.0 and 1.0."""
        zero = ConfidenceScore.create(0.0).unwrap()
        one = ConfidenceScore.create(1.0).unwrap()

        assert zero.value == 0.0
        assert one.value == 1.0

    def test_full_factory(self):
        """Test full() factory method."""
        score = ConfidenceScore.full()

        assert score.value == 1.0
        assert not score.needs_review

    def test_zero_factory(self):
        """Test zero() factory method."""
        score = ConfidenceScore.zero()

        assert score.value == 0.0
        assert score.needs_review

    def test_needs_review_below_threshold(self):
        """Test needs_review for scores below threshold."""
        low_score = ConfidenceScore(0.5)
        high_score = ConfidenceScore(0.95)

        assert low_score.needs_review is True
        assert high_score.needs_review is False

    def test_is_high_confidence(self):
        """Test is_high_confidence property."""
        high = ConfidenceScore(0.95)
        medium = ConfidenceScore(0.85)

        assert high.is_high_confidence is True
        assert medium.is_high_confidence is False

    def test_percentage(self):
        """Test percentage property."""
        score = ConfidenceScore(0.856)

        assert score.percentage == 85

    def test_string_representation(self):
        """Test string representation."""
        score = ConfidenceScore(0.75)

        assert str(score) == "75%"

    def test_comparison_operators(self):
        """Test comparison operators."""
        low = ConfidenceScore(0.5)
        medium = ConfidenceScore(0.7)
        high = ConfidenceScore(0.9)

        assert low < medium < high
        assert high > medium > low
        assert low <= ConfidenceScore(0.5)
        assert high >= ConfidenceScore(0.9)

    def test_equality_with_tolerance(self):
        """Test equality uses tolerance for floating point."""
        score1 = ConfidenceScore(0.85)
        score2 = ConfidenceScore(0.850001)

        assert score1 == score2


# ═══════════════════════════════════════════════════════════════════════════════
# TEXT SPAN
# ═══════════════════════════════════════════════════════════════════════════════


class TestTextSpan:
    """Test TextSpan value object."""

    def test_create_valid_span(self):
        """Test creating a valid text span."""
        result = TextSpan.create(0, 10, "John Smith")

        assert result.is_ok()
        span = result.unwrap()
        assert span.start == 0
        assert span.end == 10
        assert span.text == "John Smith"

    def test_create_rejects_negative_start(self):
        """Test that negative start is rejected."""
        result = TextSpan.create(-1, 5, "text")

        assert result.is_err()
        assert isinstance(result.unwrap_err(), InvalidSpanError)

    def test_create_rejects_end_before_start(self):
        """Test that end <= start is rejected."""
        result = TextSpan.create(10, 5, "text")

        assert result.is_err()
        assert isinstance(result.unwrap_err(), InvalidSpanError)

    def test_create_rejects_end_equals_start(self):
        """Test that end == start is rejected."""
        result = TextSpan.create(5, 5, "")

        assert result.is_err()
        assert isinstance(result.unwrap_err(), InvalidSpanError)

    def test_create_rejects_mismatched_length(self):
        """Test that text length must match span length."""
        result = TextSpan.create(0, 10, "short")

        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, InvalidSpanError)

    def test_length_property(self):
        """Test length property."""
        span = TextSpan.create(5, 15, "0123456789").unwrap()

        assert span.length == 10

    def test_contains_position(self):
        """Test contains method."""
        span = TextSpan.create(10, 20, "0123456789").unwrap()

        assert span.contains(10) is True
        assert span.contains(15) is True
        assert span.contains(19) is True
        assert span.contains(20) is False
        assert span.contains(9) is False

    def test_overlaps(self):
        """Test overlaps method."""
        span1 = TextSpan.create(0, 10, "0123456789").unwrap()
        span2 = TextSpan.create(5, 15, "0123456789").unwrap()
        span3 = TextSpan.create(15, 25, "0123456789").unwrap()

        assert span1.overlaps(span2) is True
        assert span2.overlaps(span1) is True
        assert span1.overlaps(span3) is False
        assert span3.overlaps(span1) is False

    def test_shift(self):
        """Test shift method."""
        span = TextSpan.create(0, 10, "John Smith").unwrap()
        shifted_result = span.shift(5)

        assert shifted_result.is_ok()
        shifted = shifted_result.unwrap()
        assert shifted.start == 5
        assert shifted.end == 15
        assert shifted.text == "John Smith"

    def test_shift_negative_causes_invalid(self):
        """Test that shifting to negative position fails."""
        span = TextSpan.create(5, 10, "12345").unwrap()
        result = span.shift(-10)

        assert result.is_err()

    def test_string_representation(self):
        """Test string representation."""
        span = TextSpan.create(0, 10, "John Smith").unwrap()

        assert str(span) == "[0:10] 'John Smith'"

    def test_comparison(self):
        """Test comparison by start position."""
        span1 = TextSpan.create(0, 5, "12345").unwrap()
        span2 = TextSpan.create(10, 15, "12345").unwrap()

        assert span1 < span2


# ═══════════════════════════════════════════════════════════════════════════════
# PII CATEGORY
# ═══════════════════════════════════════════════════════════════════════════════


class TestPiiCategory:
    """Test PiiCategory value object."""

    def test_from_string_valid(self):
        """Test creating from valid string."""
        result = PiiCategory.from_string("PERSON_NAME")

        assert result.is_ok()
        category = result.unwrap()
        assert category.value == PiiCategoryEnum.PERSON_NAME

    def test_from_string_case_insensitive(self):
        """Test case-insensitive parsing."""
        result = PiiCategory.from_string("person_name")

        assert result.is_ok()
        assert result.unwrap().value == PiiCategoryEnum.PERSON_NAME

    def test_from_string_with_spaces(self):
        """Test parsing with spaces instead of underscores."""
        result = PiiCategory.from_string("PERSON NAME")

        assert result.is_ok()
        assert result.unwrap().value == PiiCategoryEnum.PERSON_NAME

    def test_from_string_with_hyphens(self):
        """Test parsing with hyphens."""
        result = PiiCategory.from_string("PERSON-NAME")

        assert result.is_ok()
        assert result.unwrap().value == PiiCategoryEnum.PERSON_NAME

    def test_from_string_invalid(self):
        """Test invalid category string."""
        result = PiiCategory.from_string("INVALID_CATEGORY")

        assert result.is_err()
        assert isinstance(result.unwrap_err(), InvalidCategoryError)

    def test_alias_pattern(self):
        """Test alias pattern retrieval."""
        category = PERSON_NAME

        assert category.alias_pattern == "Persona_{N}"

    def test_generate_alias(self):
        """Test alias generation."""
        category = EMAIL
        alias = category.generate_alias(5)

        assert alias == "Email_5"

    def test_constants(self):
        """Test predefined category constants."""
        assert PERSON_NAME.value == PiiCategoryEnum.PERSON_NAME
        assert EMAIL.value == PiiCategoryEnum.EMAIL

    def test_string_representation(self):
        """Test string representation."""
        assert str(PERSON_NAME) == "PERSON_NAME"


# ═══════════════════════════════════════════════════════════════════════════════
# ALIAS
# ═══════════════════════════════════════════════════════════════════════════════


class TestAlias:
    """Test Alias value object."""

    def test_create_valid_alias(self):
        """Test creating a valid alias."""
        result = Alias.create("Persona_1", PERSON_NAME)

        assert result.is_ok()
        alias = result.unwrap()
        assert alias.value == "Persona_1"
        assert alias.category == PERSON_NAME

    def test_create_rejects_empty(self):
        """Test that empty string is rejected."""
        result = Alias.create("", PERSON_NAME)

        assert result.is_err()
        assert isinstance(result.unwrap_err(), InvalidAliasError)

    def test_create_rejects_invalid_format(self):
        """Test that invalid format is rejected."""
        result = Alias.create("InvalidFormat", PERSON_NAME)

        assert result.is_err()
        assert isinstance(result.unwrap_err(), InvalidAliasError)

    def test_create_rejects_wrong_prefix(self):
        """Test that wrong category prefix is rejected."""
        result = Alias.create("Email_1", PERSON_NAME)

        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, InvalidAliasError)

    def test_generate_creates_valid_alias(self):
        """Test generate factory method."""
        result = Alias.generate(PERSON_NAME, 5)

        assert result.is_ok()
        alias = result.unwrap()
        assert alias.value == "Persona_5"
        assert alias.category == PERSON_NAME

    def test_generate_rejects_zero_index(self):
        """Test that index must be >= 1."""
        result = Alias.generate(PERSON_NAME, 0)

        assert result.is_err()
        assert isinstance(result.unwrap_err(), InvalidAliasError)

    def test_generate_rejects_negative_index(self):
        """Test that negative index is rejected."""
        result = Alias.generate(PERSON_NAME, -1)

        assert result.is_err()

    def test_string_representation(self):
        """Test string representation."""
        alias = Alias.generate(PERSON_NAME, 1).unwrap()

        assert str(alias) == "Persona_1"

    def test_equality(self):
        """Test alias equality."""
        alias1 = Alias.create("Persona_1", PERSON_NAME).unwrap()
        alias2 = Alias.create("Persona_1", PERSON_NAME).unwrap()
        alias3 = Alias.create("Persona_2", PERSON_NAME).unwrap()

        assert alias1 == alias2
        assert alias1 != alias3


# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENT STATE
# ═══════════════════════════════════════════════════════════════════════════════


class TestDocumentState:
    """Test DocumentState value object."""

    def test_from_string_valid(self):
        """Test creating from valid string."""
        result = DocumentState.from_string("PENDING")

        assert result.is_ok()
        state = result.unwrap()
        assert state.value == DocumentStateEnum.PENDING

    def test_from_string_case_insensitive(self):
        """Test case-insensitive parsing."""
        result = DocumentState.from_string("pending")

        assert result.is_ok()
        assert result.unwrap().value == DocumentStateEnum.PENDING

    def test_from_string_invalid(self):
        """Test invalid state string."""
        result = DocumentState.from_string("INVALID")

        assert result.is_err()
        assert isinstance(result.unwrap_err(), InvalidStateError)

    def test_state_constants(self):
        """Test predefined state constants."""
        assert PENDING.value == DocumentStateEnum.PENDING
        assert INGESTED.value == DocumentStateEnum.INGESTED
        assert DETECTING.value == DocumentStateEnum.DETECTING
        assert DETECTED.value == DocumentStateEnum.DETECTED
        assert ANONYMIZING.value == DocumentStateEnum.ANONYMIZING
        assert ANONYMIZED.value == DocumentStateEnum.ANONYMIZED
        assert FAILED.value == DocumentStateEnum.FAILED

    def test_is_terminal(self):
        """Test terminal state detection."""
        assert PENDING.is_terminal is False
        assert INGESTED.is_terminal is False
        assert DETECTING.is_terminal is False
        assert DETECTED.is_terminal is False
        assert ANONYMIZING.is_terminal is False
        assert ANONYMIZED.is_terminal is True
        assert FAILED.is_terminal is True

    def test_can_transition_to(self):
        """Test valid state transitions."""
        assert PENDING.can_transition_to(INGESTED) is True
        assert INGESTED.can_transition_to(DETECTING) is True
        assert DETECTING.can_transition_to(DETECTED) is True
        assert DETECTED.can_transition_to(ANONYMIZING) is True
        assert ANONYMIZING.can_transition_to(ANONYMIZED) is True
        assert DETECTING.can_transition_to(FAILED) is True

    def test_cannot_transition_from_terminal(self):
        """Test that terminal states cannot transition."""
        assert ANONYMIZED.can_transition_to(DETECTING) is False
        assert FAILED.can_transition_to(PENDING) is False


# ═══════════════════════════════════════════════════════════════════════════════
# ANONYMIZATION LEVEL
# ═══════════════════════════════════════════════════════════════════════════════


class TestAnonymizationLevel:
    """Test AnonymizationLevel value object."""

    def test_from_string_valid(self):
        """Test creating from valid string."""
        result = AnonymizationLevel.from_string("BASIC")

        assert result.is_ok()
        level = result.unwrap()
        assert level.value == AnonymizationLevelEnum.BASIC

    def test_from_string_case_insensitive(self):
        """Test case-insensitive parsing."""
        result = AnonymizationLevel.from_string("intermediate")

        assert result.is_ok()
        assert result.unwrap().value == AnonymizationLevelEnum.INTERMEDIATE

    def test_from_string_invalid(self):
        """Test invalid level string."""
        result = AnonymizationLevel.from_string("ULTRA")

        assert result.is_err()
        assert isinstance(result.unwrap_err(), InvalidLevelError)

    def test_level_constants(self):
        """Test predefined level constants."""
        assert BASIC.value == AnonymizationLevelEnum.BASIC
        assert INTERMEDIATE.value == AnonymizationLevelEnum.INTERMEDIATE
        assert ADVANCED.value == AnonymizationLevelEnum.ADVANCED

    def test_removes_metadata(self):
        """Test metadata removal flag."""
        assert BASIC.removes_metadata is False
        assert INTERMEDIATE.removes_metadata is False
        assert ADVANCED.removes_metadata is True

    def test_requires_audit(self):
        """Test audit requirement flag."""
        assert BASIC.requires_audit is False
        assert INTERMEDIATE.requires_audit is True
        assert ADVANCED.requires_audit is True
