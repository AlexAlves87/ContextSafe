"""Tests for synthetic data generators in ADVANCED anonymization strategy.

TF-005: DNI/IBAN/NSS generated in ADVANCED level must have mathematically
invalid checksums, so they cannot correspond to real data.
"""
import pytest

from contextsafe.infrastructure.nlp.strategies.synthetic import (
    DNI_LETTERS,
    generate_invalid_dni,
    generate_invalid_nie,
)


def test_synthetic_dni_is_invalid():
    """Generated DNI must have a WRONG control letter."""
    for _ in range(100):
        dni = generate_invalid_dni()
        digits = int(dni[:-1])
        valid_letter = DNI_LETTERS[digits % 23]
        assert dni[-1] != valid_letter, f"Generated valid DNI: {dni}"


def test_synthetic_dni_format():
    """Generated DNI must be 8 digits + 1 letter."""
    dni = generate_invalid_dni()
    assert len(dni) == 9
    assert dni[:-1].isdigit()
    assert dni[-1].isalpha()


def test_synthetic_nie_is_invalid():
    """Generated NIE must have a WRONG control letter."""
    for _ in range(100):
        nie = generate_invalid_nie()
        prefix = nie[0]
        digits = int(nie[1:-1])
        prefix_map = {"X": 0, "Y": 1, "Z": 2}
        full_number = int(f"{prefix_map[prefix]}{digits}")
        valid_letter = DNI_LETTERS[full_number % 23]
        assert nie[-1] != valid_letter, f"Generated valid NIE: {nie}"


def test_synthetic_nie_format():
    """Generated NIE must be X/Y/Z + 7 digits + 1 letter."""
    nie = generate_invalid_nie()
    assert len(nie) == 9
    assert nie[0] in "XYZ"
    assert nie[1:-1].isdigit()
    assert nie[-1].isalpha()
