#!/usr/bin/env python3
"""
Entity validator for NER postprocessing.

Validates and filters entities detected by the NER model:
- Checksum validation (DNI, IBAN, NSS)
- Format validation (license plates, phones, ECLI)
- Exclusion patterns (legal references, examples)
- Fragment filtering (too short, incomplete)
- Context detection (illustrative examples)

Usage:
    from scripts.inference.entity_validator import EntityValidator

    validator = EntityValidator()
    validated = validator.validate(entities, original_text)
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ValidationResult(Enum):
    """Result of entity validation."""

    VALID = "valid"
    INVALID_CHECKSUM = "invalid_checksum"
    INVALID_FORMAT = "invalid_format"
    EXCLUDED_PATTERN = "excluded_pattern"
    EXAMPLE_CONTEXT = "example_context"
    TOO_SHORT = "too_short"
    FRAGMENT = "fragment"


@dataclass
class Entity:
    """Detected entity with validation info."""

    text: str
    entity_type: str
    start: int
    end: int
    confidence: float = 1.0
    validation: ValidationResult = ValidationResult.VALID
    validation_note: str = ""


class EntityValidator:
    """
    Validates NER-detected entities using rules and checksums.
    """

    # DNI letter calculation
    DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"

    # NIE prefix mapping for checksum
    NIE_PREFIX_MAP = {'X': 0, 'Y': 1, 'Z': 2}

    # Legal reference patterns to exclude
    LEGAL_EXCLUSION_PATTERNS = [
        # Laws and decrees
        re.compile(r'\bLey\s+\d+/\d{4}', re.IGNORECASE),
        re.compile(r'\bReal\s+Decreto\s+\d+/\d{4}', re.IGNORECASE),
        re.compile(r'\bR\.?D\.?\s+\d+/\d{4}', re.IGNORECASE),
        re.compile(r'\bOrden\s+\w+/\d{4}', re.IGNORECASE),
        # Expedientes and protocols
        re.compile(r'\bexpediente\s+\d+', re.IGNORECASE),
        re.compile(r'\bprotocolo\s+\d+', re.IGNORECASE),
        re.compile(r'\bNÚMERO\s+[A-ZÁÉÍÓÚ\s]+\.-', re.IGNORECASE),
        # Article references
        re.compile(r'\bartículo\s+\d+', re.IGNORECASE),
        re.compile(r'\bart\.\s*\d+', re.IGNORECASE),
    ]

    # Example/illustrative context patterns
    EXAMPLE_CONTEXT_PATTERNS = [
        re.compile(r'\bejemplo\b', re.IGNORECASE),
        re.compile(r'\bilustrativ[oa]\b', re.IGNORECASE),
        re.compile(r'\bformato\b', re.IGNORECASE),
        re.compile(r'\bmodelo\b', re.IGNORECASE),
        re.compile(r'\bplantilla\b', re.IGNORECASE),
        re.compile(r'\bfictici[oa]\b', re.IGNORECASE),
        re.compile(r'\binvent[ao]d[oa]\b', re.IGNORECASE),
    ]

    # Fictional characters to exclude
    FICTIONAL_EXCLUSIONS = {
        'don quijote', 'sancho panza', 'dulcinea', 'rocinante',
        'sherlock holmes', 'harry potter', 'frodo', 'gandalf',
        # Add more as needed
    }

    # Format patterns for validation
    FORMAT_PATTERNS = {
        'DNI_NIE': re.compile(r'^[0-9XYZ]\d{7}[A-Z]$', re.IGNORECASE),
        'IBAN': re.compile(r'^ES\d{22}$', re.IGNORECASE),
        'NSS': re.compile(r'^\d{12}$'),
        'PHONE': re.compile(r'^(\+34|0034)?[6789]\d{8}$'),
        'LICENSE_PLATE': re.compile(r'^\d{4}[A-Z]{3}$', re.IGNORECASE),
        'POSTAL_CODE': re.compile(r'^(0[1-9]|[1-4]\d|5[0-2])\d{3}$'),
        'ECLI': re.compile(r'^ECLI:ES:[A-Z]{2,4}:\d{4}:\d+$', re.IGNORECASE),
        'CADASTRAL_REF': re.compile(r'^\d{7}[A-Z]{2}\d{4}[A-Z]\d{4}[A-Z]{2}$', re.IGNORECASE),
    }

    # Minimum lengths by entity type
    MIN_LENGTHS = {
        'PERSON': 3,
        'ORGANIZATION': 3,
        'LOCATION': 2,
        'ADDRESS': 5,
        'DATE': 4,
        'DNI_NIE': 9,
        'IBAN': 24,
        'NSS': 12,
        'PHONE': 9,
        'LICENSE_PLATE': 7,
        'POSTAL_CODE': 5,
        'ECLI': 15,
        'CADASTRAL_REF': 20,
        'PROFESSIONAL_ID': 3,
    }

    def __init__(self,
                 validate_checksums: bool = True,
                 validate_formats: bool = True,
                 check_exclusions: bool = True,
                 check_context: bool = True,
                 filter_fragments: bool = True,
                 context_window: int = 50):
        """
        Initialize validator.

        Args:
            validate_checksums: Validate DNI/IBAN/NSS checksums
            validate_formats: Validate entity formats with regex
            check_exclusions: Exclude legal reference patterns
            check_context: Check for example/illustrative context
            filter_fragments: Remove too-short fragments
            context_window: Characters to check for context patterns
        """
        self.validate_checksums = validate_checksums
        self.validate_formats = validate_formats
        self.check_exclusions = check_exclusions
        self.check_context = check_context
        self.filter_fragments = filter_fragments
        self.context_window = context_window

    def validate(self, entities: list[dict], text: str) -> list[Entity]:
        """
        Validate a list of entities.

        Args:
            entities: List of {"text": ..., "type": ..., "start": ..., "end": ...}
            text: Original text for context checking

        Returns:
            List of Entity objects with validation results
        """
        validated = []

        for ent in entities:
            entity = Entity(
                text=ent.get('text', ''),
                entity_type=ent.get('type', ent.get('entity_type', '')),
                start=ent.get('start', 0),
                end=ent.get('end', 0),
                confidence=ent.get('confidence', 1.0),
            )

            # Run validation pipeline
            self._validate_entity(entity, text)
            validated.append(entity)

        return validated

    def filter_valid(self, entities: list[dict], text: str) -> list[Entity]:
        """
        Validate and return only valid entities.

        Args:
            entities: List of entity dicts
            text: Original text

        Returns:
            List of valid Entity objects only
        """
        validated = self.validate(entities, text)
        return [e for e in validated if e.validation == ValidationResult.VALID]

    def _validate_entity(self, entity: Entity, text: str) -> None:
        """Run validation pipeline on single entity."""

        # 1. Fragment filtering (too short)
        if self.filter_fragments:
            min_len = self.MIN_LENGTHS.get(entity.entity_type, 2)
            if len(entity.text.strip()) < min_len:
                entity.validation = ValidationResult.TOO_SHORT
                entity.validation_note = f"Length {len(entity.text)} < min {min_len}"
                return

        # 2. Exclusion patterns (legal references)
        if self.check_exclusions:
            if self._is_excluded_pattern(entity, text):
                entity.validation = ValidationResult.EXCLUDED_PATTERN
                return

        # 3. Example context check
        if self.check_context:
            if self._is_example_context(entity, text):
                entity.validation = ValidationResult.EXAMPLE_CONTEXT
                entity.validation_note = "Appears in example/illustrative context"
                return

        # 4. Fictional character check
        if entity.entity_type == 'PERSON':
            if self._is_fictional(entity.text):
                entity.validation = ValidationResult.EXCLUDED_PATTERN
                entity.validation_note = "Fictional character"
                return

        # 5. Format validation
        if self.validate_formats:
            if not self._validate_format(entity):
                return  # validation set inside method

        # 6. Checksum validation
        if self.validate_checksums:
            if not self._validate_checksum(entity):
                return  # validation set inside method

        # Passed all checks
        entity.validation = ValidationResult.VALID

    def _is_excluded_pattern(self, entity: Entity, text: str) -> bool:
        """Check if entity is part of excluded legal pattern."""
        # Get context around entity
        start = max(0, entity.start - 30)
        end = min(len(text), entity.end + 30)
        context = text[start:end]

        for pattern in self.LEGAL_EXCLUSION_PATTERNS:
            if pattern.search(context):
                # Check if entity overlaps with the pattern match
                match = pattern.search(context)
                if match:
                    entity.validation_note = f"Part of legal reference: {match.group()}"
                    return True

        return False

    def _is_example_context(self, entity: Entity, text: str) -> bool:
        """Check if entity appears in example/illustrative context."""
        start = max(0, entity.start - self.context_window)
        end = min(len(text), entity.end + self.context_window)
        context = text[start:end].lower()

        for pattern in self.EXAMPLE_CONTEXT_PATTERNS:
            if pattern.search(context):
                return True

        return False

    def _is_fictional(self, text: str) -> bool:
        """Check if text is a known fictional character."""
        normalized = text.lower().strip()
        return normalized in self.FICTIONAL_EXCLUSIONS

    def _validate_format(self, entity: Entity) -> bool:
        """Validate entity format with regex."""
        entity_type = entity.entity_type

        if entity_type not in self.FORMAT_PATTERNS:
            return True  # No format validation for this type

        pattern = self.FORMAT_PATTERNS[entity_type]
        # Normalize text (remove spaces, etc.)
        normalized = self._normalize_for_validation(entity.text, entity_type)

        if not pattern.match(normalized):
            entity.validation = ValidationResult.INVALID_FORMAT
            entity.validation_note = f"Does not match {entity_type} format"
            return False

        return True

    def _normalize_for_validation(self, text: str, entity_type: str) -> str:
        """Normalize text for format validation."""
        # Remove spaces
        text = re.sub(r'\s+', '', text)
        # Remove common separators
        text = text.replace('-', '').replace('.', '')

        # Type-specific normalization
        if entity_type in ('DNI_NIE', 'IBAN', 'LICENSE_PLATE', 'ECLI'):
            text = text.upper()
        elif entity_type == 'PHONE':
            # Keep only digits and +
            text = re.sub(r'[^\d+]', '', text)

        return text

    def _validate_checksum(self, entity: Entity) -> bool:
        """Validate checksum for DNI/IBAN/NSS."""
        entity_type = entity.entity_type
        text = self._normalize_for_validation(entity.text, entity_type)

        if entity_type == 'DNI_NIE':
            return self._validate_dni_checksum(entity, text)
        elif entity_type == 'IBAN':
            return self._validate_iban_checksum(entity, text)
        elif entity_type == 'NSS':
            return self._validate_nss_checksum(entity, text)

        return True  # No checksum validation for this type

    def _validate_dni_checksum(self, entity: Entity, text: str) -> bool:
        """
        Validate Spanish DNI/NIE checksum.

        DNI: 8 digits + letter
        NIE: X/Y/Z + 7 digits + letter

        Letter = DNI_LETTERS[number % 23]
        """
        if len(text) != 9:
            return True  # Can't validate, assume ok

        try:
            prefix = text[0]
            letter = text[-1].upper()

            if prefix in 'XYZ':
                # NIE: replace prefix with number
                number = int(str(self.NIE_PREFIX_MAP[prefix]) + text[1:-1])
            else:
                # DNI: just the number
                number = int(text[:-1])

            expected_letter = self.DNI_LETTERS[number % 23]

            if letter != expected_letter:
                entity.validation = ValidationResult.INVALID_CHECKSUM
                entity.validation_note = f"DNI letter should be {expected_letter}, got {letter}"
                return False

        except (ValueError, KeyError):
            # Can't parse, assume ok
            pass

        return True

    def _validate_iban_checksum(self, entity: Entity, text: str) -> bool:
        """
        Validate IBAN checksum (ISO 7064 Mod 97-10).

        Spanish IBAN: ES + 2 check digits + 20 digits
        """
        if not text.startswith('ES') or len(text) != 24:
            return True  # Can't validate

        try:
            # Move country code and check digits to end
            rearranged = text[4:] + text[:4]

            # Replace letters with numbers (A=10, B=11, ..., Z=35)
            numeric = ''
            for char in rearranged:
                if char.isdigit():
                    numeric += char
                else:
                    numeric += str(ord(char.upper()) - ord('A') + 10)

            # Valid if mod 97 == 1
            if int(numeric) % 97 != 1:
                entity.validation = ValidationResult.INVALID_CHECKSUM
                entity.validation_note = "Invalid IBAN checksum (mod 97)"
                return False

        except ValueError:
            pass

        return True

    def _validate_nss_checksum(self, entity: Entity, text: str) -> bool:
        """
        Validate Spanish Social Security Number checksum.

        NSS: 12 digits, last 2 are control digits
        Control = first 10 digits mod 97
        """
        if len(text) != 12 or not text.isdigit():
            return True  # Can't validate

        try:
            base = int(text[:10])
            control = int(text[10:])

            expected = base % 97

            if control != expected:
                entity.validation = ValidationResult.INVALID_CHECKSUM
                entity.validation_note = f"NSS control should be {expected:02d}, got {control:02d}"
                return False

        except ValueError:
            pass

        return True


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def validate_entities(entities: list[dict], text: str) -> list[Entity]:
    """
    Validate entities with default settings.

    Args:
        entities: List of entity dicts from NER model
        text: Original text

    Returns:
        List of Entity objects with validation results
    """
    validator = EntityValidator()
    return validator.validate(entities, text)


def filter_valid_entities(entities: list[dict], text: str) -> list[dict]:
    """
    Filter and return only valid entities as dicts.

    Args:
        entities: List of entity dicts from NER model
        text: Original text

    Returns:
        List of valid entity dicts
    """
    validator = EntityValidator()
    valid = validator.filter_valid(entities, text)
    return [
        {
            'text': e.text,
            'type': e.entity_type,
            'start': e.start,
            'end': e.end,
            'confidence': e.confidence,
        }
        for e in valid
    ]


def validate_dni(dni: str) -> tuple[bool, str]:
    """
    Validate a single DNI/NIE.

    Returns:
        Tuple of (is_valid, message)
    """
    validator = EntityValidator()
    entity = Entity(text=dni, entity_type='DNI_NIE', start=0, end=len(dni))
    validator._validate_entity(entity, dni)

    return (
        entity.validation == ValidationResult.VALID,
        entity.validation_note or "Valid"
    )


def validate_iban(iban: str) -> tuple[bool, str]:
    """
    Validate a single IBAN.

    Returns:
        Tuple of (is_valid, message)
    """
    validator = EntityValidator()
    entity = Entity(text=iban, entity_type='IBAN', start=0, end=len(iban))
    validator._validate_entity(entity, iban)

    return (
        entity.validation == ValidationResult.VALID,
        entity.validation_note or "Valid"
    )


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("ENTITY VALIDATOR TEST")
    print("=" * 60)

    # Test DNI validation
    print("\n--- DNI Validation ---")
    test_dnis = [
        "12345678Z",  # Valid
        "12345678A",  # Invalid letter
        "X1234567L",  # Valid NIE
        "Y0000000Z",  # Invalid NIE
    ]
    for dni in test_dnis:
        valid, msg = validate_dni(dni)
        status = "✓" if valid else "✗"
        print(f"  {status} {dni}: {msg}")

    # Test IBAN validation
    print("\n--- IBAN Validation ---")
    test_ibans = [
        "ES9121000418450200051332",  # Valid (example from internet)
        "ES0021000418450200051332",  # Invalid check digits
        "ES6000491500051234567892",  # Valid
    ]
    for iban in test_ibans:
        valid, msg = validate_iban(iban)
        status = "✓" if valid else "✗"
        print(f"  {status} {iban}: {msg}")

    # Test context exclusion
    print("\n--- Context Exclusion ---")
    test_cases = [
        {
            "text": "Según la Ley 15/2022, de 12 de julio",
            "entities": [{"text": "12 de julio", "type": "DATE", "start": 24, "end": 35}],
        },
        {
            "text": "El formato del DNI es 12345678X (ejemplo)",
            "entities": [{"text": "12345678X", "type": "DNI_NIE", "start": 22, "end": 31}],
        },
        {
            "text": "Como dijo Don Quijote de la Mancha",
            "entities": [{"text": "Don Quijote de la Mancha", "type": "PERSON", "start": 10, "end": 34}],
        },
    ]

    validator = EntityValidator()
    for case in test_cases:
        results = validator.validate(case["entities"], case["text"])
        for r in results:
            status = "✓" if r.validation == ValidationResult.VALID else "✗"
            print(f"  {status} '{r.text}' ({r.entity_type}): {r.validation.value}")
            if r.validation_note:
                print(f"      Note: {r.validation_note}")
