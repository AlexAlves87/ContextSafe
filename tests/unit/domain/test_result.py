"""
Unit tests for Result type (Railway-Oriented Programming).

Tests Ok, Err, and their methods:
- is_ok(), is_err()
- unwrap(), unwrap_err(), unwrap_or()
- map(), map_err()
- and_then() (monadic bind)
"""
import pytest

from contextsafe.domain.shared.types import Ok, Err, is_ok, is_err
from contextsafe.domain.shared.errors import InvalidIdError


class TestOk:
    """Test Ok variant of Result."""

    def test_is_ok_returns_true(self):
        """Test is_ok() returns True for Ok."""
        result = Ok(42)

        assert result.is_ok() is True

    def test_is_err_returns_false(self):
        """Test is_err() returns False for Ok."""
        result = Ok(42)

        assert result.is_err() is False

    def test_unwrap_returns_value(self):
        """Test unwrap() returns the wrapped value."""
        result = Ok(42)

        assert result.unwrap() == 42

    def test_unwrap_or_returns_value(self):
        """Test unwrap_or() returns the wrapped value."""
        result = Ok(42)

        assert result.unwrap_or(0) == 42

    def test_map_transforms_value(self):
        """Test map() applies function to value."""
        result = Ok(10)
        mapped = result.map(lambda x: x * 2)

        assert mapped.is_ok()
        assert mapped.unwrap() == 20

    def test_map_err_returns_self(self):
        """Test map_err() is no-op for Ok."""
        result = Ok(42)
        mapped = result.map_err(lambda e: f"Error: {e}")

        assert mapped.is_ok()
        assert mapped.unwrap() == 42

    def test_and_then_chains_operations(self):
        """Test and_then() chains Result-returning operations."""
        def divide(x: int) -> Ok[float] | Err[str]:
            if x == 0:
                return Err("Division by zero")
            return Ok(100.0 / x)

        result = Ok(10).and_then(divide)

        assert result.is_ok()
        assert result.unwrap() == 10.0

    def test_and_then_propagates_error(self):
        """Test and_then() propagates Err from chained operation."""
        def divide(x: int) -> Ok[float] | Err[str]:
            if x == 0:
                return Err("Division by zero")
            return Ok(100.0 / x)

        result = Ok(0).and_then(divide)

        assert result.is_err()
        assert result.unwrap_err() == "Division by zero"


class TestErr:
    """Test Err variant of Result."""

    def test_is_ok_returns_false(self):
        """Test is_ok() returns False for Err."""
        result = Err("error")

        assert result.is_ok() is False

    def test_is_err_returns_true(self):
        """Test is_err() returns True for Err."""
        result = Err("error")

        assert result.is_err() is True

    def test_unwrap_raises_error(self):
        """Test unwrap() raises ValueError for Err."""
        result = Err("something went wrong")

        with pytest.raises(ValueError, match="something went wrong"):
            result.unwrap()

    def test_unwrap_err_returns_error(self):
        """Test unwrap_err() returns the error value."""
        result = Err("error message")

        assert result.unwrap_err() == "error message"

    def test_unwrap_or_returns_default(self):
        """Test unwrap_or() returns default for Err."""
        result = Err("error")

        assert result.unwrap_or(42) == 42

    def test_map_returns_self(self):
        """Test map() is no-op for Err."""
        result = Err("error")
        mapped = result.map(lambda x: x * 2)

        assert mapped.is_err()
        assert mapped.unwrap_err() == "error"

    def test_map_err_transforms_error(self):
        """Test map_err() applies function to error."""
        result = Err("error")
        mapped = result.map_err(lambda e: f"Wrapped: {e}")

        assert mapped.is_err()
        assert mapped.unwrap_err() == "Wrapped: error"

    def test_and_then_returns_self(self):
        """Test and_then() is no-op for Err."""
        result = Err("error")
        chained = result.and_then(lambda x: Ok(x * 2))

        assert chained.is_err()
        assert chained.unwrap_err() == "error"


class TestResultHelpers:
    """Test module-level Result helper functions."""

    def test_is_ok_function(self):
        """Test is_ok() helper function."""
        ok_result = Ok(42)
        err_result = Err("error")

        assert is_ok(ok_result) is True
        assert is_ok(err_result) is False

    def test_is_err_function(self):
        """Test is_err() helper function."""
        ok_result = Ok(42)
        err_result = Err("error")

        assert is_err(ok_result) is False
        assert is_err(err_result) is True


class TestResultChaining:
    """Test complex Result chaining scenarios."""

    def test_chain_multiple_operations(self):
        """Test chaining multiple Result operations."""
        def parse_int(s: str) -> Ok[int] | Err[str]:
            try:
                return Ok(int(s))
            except ValueError:
                return Err(f"Invalid int: {s}")

        def divide_by_2(x: int) -> Ok[float] | Err[str]:
            return Ok(x / 2.0)

        def check_positive(x: float) -> Ok[float] | Err[str]:
            if x > 0:
                return Ok(x)
            return Err("Not positive")

        # Success path
        result = (
            Ok("100")
            .and_then(parse_int)
            .and_then(divide_by_2)
            .and_then(check_positive)
        )

        assert result.is_ok()
        assert result.unwrap() == 50.0

    def test_chain_fails_early(self):
        """Test that chain fails on first error."""
        def parse_int(s: str) -> Ok[int] | Err[str]:
            try:
                return Ok(int(s))
            except ValueError:
                return Err(f"Invalid int: {s}")

        def divide_by_2(x: int) -> Ok[float] | Err[str]:
            return Ok(x / 2.0)

        # Fails at parse_int
        result = (
            Ok("not-a-number")
            .and_then(parse_int)
            .and_then(divide_by_2)
        )

        assert result.is_err()
        assert "Invalid int" in result.unwrap_err()

    def test_map_chain(self):
        """Test chaining map operations."""
        result = (
            Ok(10)
            .map(lambda x: x * 2)
            .map(lambda x: x + 5)
            .map(lambda x: str(x))
        )

        assert result.is_ok()
        assert result.unwrap() == "25"


class TestResultWithDomainErrors:
    """Test Result integration with domain errors."""

    def test_ok_with_domain_object(self):
        """Test Ok containing domain object."""
        from contextsafe.domain.shared.value_objects import DocumentId
        from uuid import uuid4

        uuid_str = str(uuid4())
        result = DocumentId.create(uuid_str)

        assert result.is_ok()
        doc_id = result.unwrap()
        assert doc_id.value == uuid_str

    def test_err_with_domain_error(self):
        """Test Err containing domain error."""
        from contextsafe.domain.shared.value_objects import DocumentId

        result = DocumentId.create("invalid-uuid")

        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, InvalidIdError)
        assert error.error_code == "ERR-T0-VAL-001"

    def test_chain_domain_operations(self):
        """Test chaining domain operations with Result."""
        from contextsafe.domain.shared.value_objects import DocumentId, ConfidenceScore
        from uuid import uuid4

        # Chain domain object creations
        uuid_str = str(uuid4())

        result = (
            DocumentId.create(uuid_str)
            .map(lambda doc_id: str(doc_id))
            .map(lambda id_str: len(id_str))
        )

        assert result.is_ok()
        assert result.unwrap() == 36  # UUID string length
