"""
Property-based tests for Result type (monad laws).

Tests the Result[T, E] type for compliance with monad laws:
- Identity law
- Associativity law
- Type preservation

Traceability:
- Properties: PBT-001 to PBT-004
- Contract: CNT-T0-RESULT-001
- Source: outputs/phase3/step2_validation/pbt_properties.yaml
"""
from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from contextsafe.domain.shared.types import Err, Ok, Result

# Import generators from conftest
from .conftest import result_int_gen, result_str_gen


# ==============================================================================
# PBT-001: Result identity law
# ==============================================================================


@given(st.integers())
def test_result_left_identity_law(x: int):
    """
    Test monad left identity law: Ok(x).and_then(f) == f(x).

    Property: PBT-001
    Contract: CNT-T0-RESULT-001
    Invariant: Monad law - identity
    """
    # Define a function that returns Result
    def f(n: int) -> Result[int, str]:
        return Ok(n + 1)

    # Left identity: Ok(x).and_then(f) == f(x)
    lhs = Ok(x).and_then(f)
    rhs = f(x)

    assert lhs == rhs


@given(result_int_gen())
def test_result_right_identity_law(result: Result[int, str]):
    """
    Test monad right identity law: result.and_then(Ok) == result.

    Property: PBT-001
    Contract: CNT-T0-RESULT-001
    Invariant: Monad law - identity
    """
    # Right identity: result.and_then(Ok) == result
    lhs = result.and_then(Ok)
    assert lhs == result


# ==============================================================================
# PBT-002: Result associativity law
# ==============================================================================


@given(st.integers())
def test_result_associativity_law(x: int):
    """
    Test monad associativity law.

    result.and_then(f).and_then(g) == result.and_then(lambda n: f(n).and_then(g))

    Property: PBT-002
    Contract: CNT-T0-RESULT-001
    Invariant: Monad law - associativity
    """
    result: Result[int, str] = Ok(x)

    # Define two functions
    def f(n: int) -> Result[int, str]:
        return Ok(n + 1)

    def g(n: int) -> Result[int, str]:
        return Ok(n * 2)

    # Associativity: (m >>= f) >>= g == m >>= (\x -> f x >>= g)
    lhs = result.and_then(f).and_then(g)
    rhs = result.and_then(lambda n: f(n).and_then(g))

    assert lhs == rhs


@given(st.integers())
def test_result_associativity_with_errors(x: int):
    """
    Test associativity law holds even when intermediate results are Err.

    Property: PBT-002
    Contract: CNT-T0-RESULT-001
    """
    result: Result[int, str] = Ok(x)

    # f returns error for negative numbers
    def f(n: int) -> Result[int, str]:
        if n < 0:
            return Err("negative")
        return Ok(n + 1)

    def g(n: int) -> Result[int, str]:
        return Ok(n * 2)

    # Associativity must hold even with errors
    lhs = result.and_then(f).and_then(g)
    rhs = result.and_then(lambda n: f(n).and_then(g))

    assert lhs == rhs


# ==============================================================================
# PBT-003: Result is_ok and is_err are mutually exclusive
# ==============================================================================


@given(result_int_gen())
def test_result_ok_err_mutually_exclusive(result: Result[int, str]):
    """
    Test that is_ok() and is_err() are mutually exclusive.

    Exactly one must be True.

    Property: PBT-003
    Contract: CNT-T0-RESULT-001
    Invariant: Type definition
    """
    # XOR: exactly one is True
    assert result.is_ok() != result.is_err()

    # More explicitly:
    assert (result.is_ok() and not result.is_err()) or (not result.is_ok() and result.is_err())


@given(st.integers())
def test_ok_is_always_ok(value: int):
    """
    Test Ok is always ok.

    Property: PBT-003
    Contract: CNT-T0-RESULT-001
    """
    result = Ok(value)
    assert result.is_ok()
    assert not result.is_err()


@given(st.text(min_size=1))
def test_err_is_always_err(error: str):
    """
    Test Err is always err.

    Property: PBT-003
    Contract: CNT-T0-RESULT-001
    """
    result: Result[int, str] = Err(error)
    assert result.is_err()
    assert not result.is_ok()


# ==============================================================================
# PBT-004: Result map preserves Ok/Err status
# ==============================================================================


@given(result_int_gen())
def test_result_map_preserves_status(result: Result[int, str]):
    """
    Test that map() preserves Ok/Err status.

    If input is Ok, output is Ok. If input is Err, output is Err.

    Property: PBT-004
    Contract: CNT-T0-RESULT-001
    Invariant: POST-001
    """
    # Define a mapping function
    def double(n: int) -> int:
        return n * 2

    mapped = result.map(double)

    # Status must be preserved
    assert result.is_ok() == mapped.is_ok()
    assert result.is_err() == mapped.is_err()


@given(result_str_gen())
def test_result_map_err_preserves_status(result: Result[str, str]):
    """
    Test that map_err() preserves Ok/Err status.

    Property: PBT-004
    Contract: CNT-T0-RESULT-001
    """
    # Define error mapping function
    def uppercase_error(e: str) -> str:
        return e.upper()

    mapped = result.map_err(uppercase_error)

    # Status must be preserved
    assert result.is_ok() == mapped.is_ok()
    assert result.is_err() == mapped.is_err()


@given(st.integers())
def test_ok_map_applies_function(value: int):
    """
    Test that Ok.map() correctly applies the function to the value.

    Property: PBT-004
    Contract: CNT-T0-RESULT-001
    """
    result = Ok(value)

    def square(n: int) -> int:
        return n * n

    mapped = result.map(square)

    assert mapped.is_ok()
    assert mapped.unwrap() == value * value


@given(st.text(min_size=1))
def test_err_map_ignores_function(error: str):
    """
    Test that Err.map() ignores the function (no-op).

    Property: PBT-004
    Contract: CNT-T0-RESULT-001
    """
    result: Result[int, str] = Err(error)

    def square(n: int) -> int:
        return n * n

    mapped = result.map(square)

    assert mapped.is_err()
    assert mapped.unwrap_err() == error


@given(st.integers())
def test_ok_map_err_is_noop(value: int):
    """
    Test that Ok.map_err() is a no-op (error function not applied).

    Property: PBT-004
    Contract: CNT-T0-RESULT-001
    """
    result: Result[int, str] = Ok(value)

    def uppercase_error(e: str) -> str:
        return e.upper()

    mapped = result.map_err(uppercase_error)

    assert mapped.is_ok()
    assert mapped.unwrap() == value


@given(st.text(min_size=1))
def test_err_map_err_applies_function(error: str):
    """
    Test that Err.map_err() correctly applies the function to the error.

    Property: PBT-004
    Contract: CNT-T0-RESULT-001
    """
    result: Result[int, str] = Err(error)

    def uppercase_error(e: str) -> str:
        return e.upper()

    mapped = result.map_err(uppercase_error)

    assert mapped.is_err()
    assert mapped.unwrap_err() == error.upper()


# ==============================================================================
# ADDITIONAL RESULT PROPERTIES
# ==============================================================================


@given(st.integers(), st.integers())
def test_unwrap_or_returns_value_for_ok(value: int, default: int):
    """
    Test that unwrap_or() returns the value for Ok.

    Property: Additional coverage
    """
    result = Ok(value)
    assert result.unwrap_or(default) == value


@given(st.text(min_size=1), st.integers())
def test_unwrap_or_returns_default_for_err(error: str, default: int):
    """
    Test that unwrap_or() returns the default for Err.

    Property: Additional coverage
    """
    result: Result[int, str] = Err(error)
    assert result.unwrap_or(default) == default
