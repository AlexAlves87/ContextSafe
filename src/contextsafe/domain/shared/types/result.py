"""
Result type for Railway-Oriented Programming.

Provides Ok and Err types for explicit error handling without exceptions.
Follows the Result pattern from Rust/functional programming.

Traceability:
- Pattern: Railway-Oriented Programming
- Standard: consolidated_standards.yaml#imports.components.Result
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")


@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    """Success case of Result."""

    value: T

    def is_ok(self) -> bool:
        """Check if result is Ok."""
        return True

    def is_err(self) -> bool:
        """Check if result is Err."""
        return False

    def unwrap(self) -> T:
        """Get the value. Safe to call after is_ok() check."""
        return self.value

    def unwrap_or(self, default: T) -> T:
        """Get the value or return default."""
        return self.value

    def map(self, fn: Callable[[T], U]) -> Ok[U]:
        """Apply function to the value."""
        return Ok(fn(self.value))

    def map_err(self, fn: Callable[[E], U]) -> Ok[T]:
        """No-op for Ok, returns self."""
        return self  # type: ignore[return-value]

    def and_then(self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        """Chain operations that return Result."""
        return fn(self.value)


@dataclass(frozen=True, slots=True)
class Err(Generic[E]):
    """Error case of Result."""

    error: E

    def is_ok(self) -> bool:
        """Check if result is Ok."""
        return False

    def is_err(self) -> bool:
        """Check if result is Err."""
        return True

    def unwrap(self) -> None:
        """Raises ValueError. Use unwrap_err() for errors."""
        raise ValueError(f"Called unwrap on Err: {self.error}")

    def unwrap_err(self) -> E:
        """Get the error value."""
        return self.error

    def unwrap_or(self, default: T) -> T:
        """Return the default value."""
        return default

    def map(self, fn: Callable[[T], U]) -> Err[E]:
        """No-op for Err, returns self."""
        return self

    def map_err(self, fn: Callable[[E], U]) -> Err[U]:
        """Apply function to the error."""
        return Err(fn(self.error))

    def and_then(self, fn: Callable[[T], Result[U, E]]) -> Err[E]:
        """No-op for Err, returns self."""
        return self


# Type alias for Result
Result = Union[Ok[T], Err[E]]


def is_ok(result: Result[T, E]) -> bool:
    """Check if a result is Ok."""
    return isinstance(result, Ok)


def is_err(result: Result[T, E]) -> bool:
    """Check if a result is Err."""
    return isinstance(result, Err)
