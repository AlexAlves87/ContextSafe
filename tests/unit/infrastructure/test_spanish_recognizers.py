"""
Unit tests for Spanish PII recognizers.

Tests DNI, NIE, CIF, NSS, Phone, and IBAN recognizers
with valid and invalid data patterns.

Traceability:
- Contract: CNT-T3-NER-001
- Implementation: spanish_id.py, spanish_phone.py, spanish_iban.py
"""

import pytest


class TestSpanishDNIRecognizer:
    """Tests for DNI recognition and validation."""

    @pytest.fixture
    def recognizer(self):
        from contextsafe.infrastructure.nlp.recognizers.spanish_id import SpanishDNIRecognizer
        return SpanishDNIRecognizer()

    # Valid DNIs with correct checksum
    VALID_DNIS = [
        "12345678Z",  # Standard format
        "00000000T",  # All zeros
        "99999999R",  # All nines
        "12.345.678-Z",  # With separators
        "12 345 678 Z",  # With spaces
    ]

    # Invalid DNIs
    INVALID_DNIS = [
        "12345678A",  # Wrong letter (should be Z)
        "1234567Z",   # Too short
        "123456789Z", # Too long
        "ABCDEFGHI",  # No digits
        "12345678",   # No letter
    ]

    @pytest.mark.parametrize("dni", VALID_DNIS)
    def test_validate_valid_dni(self, recognizer, dni):
        """Valid DNIs should pass validation."""
        result = recognizer.validate_result(dni)
        assert result is True, f"DNI {dni} should be valid"

    @pytest.mark.parametrize("dni", INVALID_DNIS)
    def test_validate_invalid_dni(self, recognizer, dni):
        """Invalid DNIs should fail validation."""
        result = recognizer.validate_result(dni)
        assert result is False, f"DNI {dni} should be invalid"

    def test_dni_checksum_algorithm(self, recognizer):
        """Test the DNI checksum algorithm with known values."""
        # The letter is calculated as: number % 23 -> letter
        # 12345678 % 23 = 14 -> 'Z' (position 14 in TRWAGMYFPDXBNJZSQVHLCKE)
        assert recognizer.validate_result("12345678Z") is True

        # 00000000 % 23 = 0 -> 'T'
        assert recognizer.validate_result("00000000T") is True

        # 00000023 % 23 = 0 -> 'T'
        assert recognizer.validate_result("00000023T") is True


class TestSpanishNIERecognizer:
    """Tests for NIE recognition and validation."""

    @pytest.fixture
    def recognizer(self):
        from contextsafe.infrastructure.nlp.recognizers.spanish_id import SpanishNIERecognizer
        return SpanishNIERecognizer()

    VALID_NIES = [
        "X0000000T",  # X prefix (X=0)
        "Y0000000Z",  # Y prefix (Y=1, so 10000000 % 23 = 11 -> Z)
        "Z0000000M",  # Z prefix (Z=2, so 20000000 % 23 = 9 -> M)
        "X-1234567-L", # With separators
    ]

    INVALID_NIES = [
        "X0000000A",  # Wrong letter
        "A1234567B",  # Invalid prefix
        "X123456A",   # Too short
        "X12345678A", # Too long
    ]

    @pytest.mark.parametrize("nie", VALID_NIES)
    def test_validate_valid_nie(self, recognizer, nie):
        """Valid NIEs should pass validation."""
        result = recognizer.validate_result(nie)
        assert result is True, f"NIE {nie} should be valid"

    @pytest.mark.parametrize("nie", INVALID_NIES)
    def test_validate_invalid_nie(self, recognizer, nie):
        """Invalid NIEs should fail validation."""
        result = recognizer.validate_result(nie)
        assert result is False, f"NIE {nie} should be invalid"


class TestSpanishCIFRecognizer:
    """Tests for CIF recognition."""

    @pytest.fixture
    def recognizer(self):
        from contextsafe.infrastructure.nlp.recognizers.spanish_id import SpanishCIFRecognizer
        return SpanishCIFRecognizer()

    def test_cif_patterns_exist(self, recognizer):
        """CIF recognizer should have patterns defined."""
        assert len(recognizer.patterns) >= 1

    def test_cif_supported_entity(self, recognizer):
        """CIF recognizer should support ES_CIF entity."""
        assert recognizer.supported_entities == ["ES_CIF"]


class TestSpanishNSSRecognizer:
    """Tests for NSS (Social Security Number) recognition."""

    @pytest.fixture
    def recognizer(self):
        from contextsafe.infrastructure.nlp.recognizers.spanish_id import SpanishNSSRecognizer
        return SpanishNSSRecognizer()

    VALID_NSS = [
        "281234567890",    # Province 28 (Madrid)
        "08/12345678/90",  # With separators, province 08 (Barcelona)
        "01-12345678-90",  # Province 01
        "52 12345678 90",  # Province 52 (Melilla, max valid)
    ]

    INVALID_NSS = [
        "00123456789",     # Province 00 invalid
        "53123456789012",  # Province 53 invalid (> 52)
        "281234567",       # Too short
        "28123456789012",  # Too long
    ]

    @pytest.mark.parametrize("nss", VALID_NSS)
    def test_validate_valid_nss(self, recognizer, nss):
        """Valid NSS should pass validation."""
        result = recognizer.validate_result(nss)
        assert result is True, f"NSS {nss} should be valid"

    @pytest.mark.parametrize("nss", INVALID_NSS)
    def test_validate_invalid_nss(self, recognizer, nss):
        """Invalid NSS should fail validation."""
        result = recognizer.validate_result(nss)
        assert result is False, f"NSS {nss} should be invalid"


class TestSpanishPhoneRecognizer:
    """Tests for Spanish phone number recognition."""

    @pytest.fixture
    def recognizer(self):
        from contextsafe.infrastructure.nlp.recognizers.spanish_phone import SpanishPhoneRecognizer
        return SpanishPhoneRecognizer()

    VALID_PHONES = [
        "+34 612 345 678",   # Mobile with country code
        "+34612345678",      # Mobile compact
        "612 345 678",       # Mobile without country code
        "612345678",         # Mobile compact
        "912 345 678",       # Landline (Madrid)
        "932 345 678",       # Landline (Barcelona)
    ]

    def test_phone_patterns_exist(self, recognizer):
        """Phone recognizer should have patterns defined."""
        assert len(recognizer.patterns) >= 1

    def test_phone_supported_entity(self, recognizer):
        """Phone recognizer should support ES_PHONE entity."""
        assert recognizer.supported_entities == ["ES_PHONE"]


class TestSpanishIBANRecognizer:
    """Tests for Spanish IBAN recognition."""

    @pytest.fixture
    def recognizer(self):
        from contextsafe.infrastructure.nlp.recognizers.spanish_iban import SpanishIBANRecognizer
        return SpanishIBANRecognizer()

    # Valid IBANs (pass MOD-97-10)
    VALID_IBANS = [
        "ES9121000418450200051332",  # Compact
        "ES91 2100 0418 4502 0005 1332",  # With spaces
    ]

    # Invalid IBANs
    INVALID_IBANS = [
        "ES0021000418450200051332",  # Wrong check digits
        "ES91210004184502000513",    # Too short
        "ES91210004184502000513320", # Too long
        "FR9121000418450200051332",  # Not Spanish
        "ESXX21000418450200051332",  # Non-numeric check digits
    ]

    @pytest.mark.parametrize("iban", VALID_IBANS)
    def test_validate_valid_iban(self, recognizer, iban):
        """Valid IBANs should pass validation."""
        result = recognizer.validate_result(iban)
        assert result is True, f"IBAN {iban} should be valid"

    @pytest.mark.parametrize("iban", INVALID_IBANS)
    def test_validate_invalid_iban(self, recognizer, iban):
        """Invalid IBANs should fail validation."""
        result = recognizer.validate_result(iban)
        assert result is False, f"IBAN {iban} should be invalid"

    def test_iban_mod97_algorithm(self, recognizer):
        """Test IBAN MOD-97-10 validation algorithm."""
        # ES91 2100 0418 4502 0005 1332
        # Move ES91 to end: 210004184502000513321428 91
        # E=14, S=28, so: 2100041845020005133214 28 91
        # This number mod 97 should equal 1
        assert recognizer.validate_result("ES9121000418450200051332") is True


class TestRecognizerIntegration:
    """Integration tests for all recognizers together."""

    def test_all_recognizers_can_be_imported(self):
        """All recognizers should be importable."""
        from contextsafe.infrastructure.nlp.recognizers.spanish_id import (
            SpanishDNIRecognizer,
            SpanishNIERecognizer,
            SpanishCIFRecognizer,
            SpanishNSSRecognizer,
        )
        from contextsafe.infrastructure.nlp.recognizers.spanish_phone import SpanishPhoneRecognizer
        from contextsafe.infrastructure.nlp.recognizers.spanish_iban import SpanishIBANRecognizer

        recognizers = [
            SpanishDNIRecognizer(),
            SpanishNIERecognizer(),
            SpanishCIFRecognizer(),
            SpanishNSSRecognizer(),
            SpanishPhoneRecognizer(),
            SpanishIBANRecognizer(),
        ]

        for r in recognizers:
            assert r is not None
            assert len(r.patterns) >= 1

    def test_recognizers_have_spanish_language(self):
        """All recognizers should support Spanish language."""
        from contextsafe.infrastructure.nlp.recognizers.spanish_id import (
            SpanishDNIRecognizer,
            SpanishNIERecognizer,
            SpanishCIFRecognizer,
            SpanishNSSRecognizer,
        )
        from contextsafe.infrastructure.nlp.recognizers.spanish_phone import SpanishPhoneRecognizer
        from contextsafe.infrastructure.nlp.recognizers.spanish_iban import SpanishIBANRecognizer

        recognizers = [
            SpanishDNIRecognizer(),
            SpanishNIERecognizer(),
            SpanishCIFRecognizer(),
            SpanishNSSRecognizer(),
            SpanishPhoneRecognizer(),
            SpanishIBANRecognizer(),
        ]

        for r in recognizers:
            assert r.supported_language == "es", f"{r.__class__.__name__} should support Spanish"
