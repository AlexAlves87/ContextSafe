# Fix Anonymization Audit Errors — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 4 anonymization errors found in audit: bare-name omission, date omission, platform misclassification, and replacement spacing.

**Architecture:** All fixes stay within existing hexagonal architecture. Fix 1 extends the anonymization use case (BC-003). Fixes 2-3 modify infrastructure NLP adapters. Fix 4 patches the replacement algorithm in the use case.

**Tech Stack:** Python 3.12, pytest, asyncio, regex, frozen dataclasses

---

## Context: Pipeline Architecture (Critical)

The **production** pipeline uses `CompositeNerAdapter([RoBERTa, SpaCy, Regex])` — NOT `HybridNerAdapter`. See `container.py:144-148`. The composite runs all 3 adapters in parallel and merges via weighted voting (Regex=5, RoBERTa=2, SpaCy=1).

**Key Files:**
- Detection: `src/contextsafe/infrastructure/nlp/composite_adapter.py`
- Regex patterns: `src/contextsafe/infrastructure/nlp/regex_adapter.py`
- Anonymization: `src/contextsafe/application/use_cases/generate_anonymized/generate_anonymized.py`
- Glossary: `src/contextsafe/domain/anonymization/aggregates/glossary.py`
- Normalization: `src/contextsafe/domain/anonymization/services/normalization.py`
- Levels: `src/contextsafe/domain/shared/value_objects/anonymization_level.py`
- Categories: `src/contextsafe/domain/shared/value_objects/pii_category.py`

---

## Task 1: Whitespace boundary preservation in replacement (Error 5)

**Root Cause:** `generate_anonymized.py:183` does `text[:start] + alias + text[end:]` without checking if the alias butts up against an adjacent word character, producing "Persona_002ya".

**Files:**
- Modify: `src/contextsafe/application/use_cases/generate_anonymized/generate_anonymized.py:182-183`
- Test: `tests/unit/application/test_generate_anonymized.py` (create)

### Step 1: Write the failing test

Create `tests/unit/application/test_generate_anonymized.py`:

```python
"""Tests for whitespace boundary preservation in anonymization replacement."""

import pytest


class TestReplacementWhitespace:
    """Tests that replacement preserves word boundaries."""

    def test_alias_preserves_trailing_space(self):
        """Replacing entity should not merge alias with next word."""
        # Simulate: "WhatsApp ya había..." where "WhatsApp" at [0:8]
        text = "WhatsApp ya había notificado"
        entity_start = 0
        entity_end = 8
        alias_value = "Persona_002"

        # Current (buggy) replacement:
        result_buggy = text[:entity_start] + alias_value + text[entity_end:]
        assert result_buggy == "Persona_002 ya había notificado"  # Should pass if space exists at text[8]

    def test_alias_needs_space_when_touching_word(self):
        """If entity end lands on a word char (no space), a space must be inserted."""
        # Simulate: entity span captured trailing space, so text[end] is a letter
        text = "contactó por WhatsAppya en diciembre"
        entity_start = 13
        entity_end = 21  # "WhatsApp" but end=21 is 'y' of "ya"... no, let me rethink

        # The real scenario: entity span is [13:21] = "WhatsApp" (8 chars)
        # text[21] = 'y' — NO space between entity end and next word
        # This happens when regex match captured "WhatsApp" followed by a non-space terminator
        text = "contactó por WhatsAppya en diciembre"
        alias_value = "Plataforma_001"

        # The fix should insert a space
        new_text = _replace_with_boundary_check(text, entity_start, entity_end, alias_value)
        assert " ya " in new_text or new_text[entity_start + len(alias_value)] == " "


def _replace_with_boundary_check(text: str, start: int, end: int, alias: str) -> str:
    """Reference implementation for the fix."""
    after = text[end:end + 1] if end < len(text) else ""
    needs_space = after.isalnum()
    return text[:start] + alias + (" " if needs_space else "") + text[end:]
```

### Step 2: Run test to verify it fails

Run: `cd /home/alexalves87/projects/ContextSafe_repo/ContextSafe-main && python -m pytest tests/unit/application/test_generate_anonymized.py -v`
Expected: Tests define the behavior we need.

### Step 3: Implement the fix

In `src/contextsafe/application/use_cases/generate_anonymized/generate_anonymized.py`, replace line 183:

```python
# BEFORE (line 183):
text = text[:entity.start] + alias.value + text[entity.end:]

# AFTER:
after_char = text[entity.end:entity.end + 1] if entity.end < len(text) else ""
space_suffix = " " if after_char.isalnum() else ""
text = text[:entity.start] + alias.value + space_suffix + text[entity.end:]
```

**Why `isalnum()`:** If the next character is a letter or digit, the alias needs separation. If it's a space, punctuation, newline, or end-of-string, no extra space is needed.

### Step 4: Run tests

Run: `python -m pytest tests/unit/application/test_generate_anonymized.py -v`
Expected: PASS

### Step 5: Commit

```bash
git add tests/unit/application/test_generate_anonymized.py src/contextsafe/application/use_cases/generate_anonymized/generate_anonymized.py
git commit -m "fix: preserve whitespace boundaries in alias replacement (Error 5)"
```

---

## Task 2: Platform misclassification — WhatsApp as Persona (Error 3)

**Root Cause:** spaCy's `es_core_news_lg` classifies "WhatsApp" as `PER`. RoBERTa may also misclassify. Regex correctly detects it as `PLATFORM` (0.85), but in weighted voting, 2 sources saying `PERSON_NAME` can outweigh 1 source saying `PLATFORM`. Additionally, `PLATFORM` is NOT included in any anonymization level, so even if correctly classified, it would be skipped.

**Fix strategy (2 parts):**
- **Part A:** Add known platform names to the PERSON_NAME blocklist in `composite_adapter.py` so they can't be classified as persons.
- **Part B:** Add `PLATFORM` to `ADVANCED` anonymization level (and optionally to `INTERMEDIATE` if desired).

**Files:**
- Modify: `src/contextsafe/infrastructure/nlp/composite_adapter.py` (SPANISH_STOPWORDS or new blocklist)
- Modify: `src/contextsafe/domain/shared/value_objects/anonymization_level.py:51-65`
- Test: `tests/unit/infrastructure/test_platform_classification.py` (create)

### Step 1: Write the failing test

Create `tests/unit/infrastructure/test_platform_classification.py`:

```python
"""Tests that platform names are not misclassified as PERSON_NAME."""

import pytest

from contextsafe.infrastructure.nlp.composite_adapter import (
    PLATFORM_NAMES_BLOCKLIST,
)


class TestPlatformBlocklist:
    """Platform names should never be classified as PERSON_NAME."""

    def test_whatsapp_in_blocklist(self):
        assert "whatsapp" in PLATFORM_NAMES_BLOCKLIST

    def test_telegram_in_blocklist(self):
        assert "telegram" in PLATFORM_NAMES_BLOCKLIST

    def test_common_platforms_in_blocklist(self):
        expected = {"whatsapp", "telegram", "signal", "instagram", "facebook",
                    "twitter", "tiktok", "linkedin", "discord", "slack"}
        assert expected.issubset(PLATFORM_NAMES_BLOCKLIST)
```

### Step 2: Run test to verify it fails

Run: `python -m pytest tests/unit/infrastructure/test_platform_classification.py -v`
Expected: FAIL — `PLATFORM_NAMES_BLOCKLIST` does not exist.

### Step 3: Implement Part A — Platform blocklist

In `src/contextsafe/infrastructure/nlp/composite_adapter.py`, add after `COMMON_SHORT_WORDS` (~line 208):

```python
# ============================================================================
# PLATFORM NAMES BLOCKLIST (Error 3 — WhatsApp as Persona)
# Platform/app names that spaCy/RoBERTa misclassify as PERSON_NAME.
# These should ONLY be detected as PLATFORM, never as PERSON_NAME.
# ============================================================================
PLATFORM_NAMES_BLOCKLIST = {
    "whatsapp", "telegram", "signal", "messenger",
    "instagram", "facebook", "twitter", "tiktok",
    "linkedin", "snapchat", "discord", "slack",
    "teams", "skype", "zoom", "wechat", "viber",
    "wallapop", "vinted", "milanuncios", "idealista",
    "fotocasa", "infojobs", "imessage", "facetime",
}
```

Then in `_filter_stopwords()` method (~line 749), add a check for platform names detected as PERSON_NAME. After the `COMMON_SHORT_WORDS` check (before `filtered.append(detection)`), add:

```python
            # Check if platform name misclassified as PERSON_NAME (Error 3)
            if detection.category == PERSON_NAME:
                if value_lower in PLATFORM_NAMES_BLOCKLIST:
                    continue
```

### Step 4: Run test

Run: `python -m pytest tests/unit/infrastructure/test_platform_classification.py -v`
Expected: PASS

### Step 5: Implement Part B — Add PLATFORM to anonymization levels

In `src/contextsafe/domain/shared/value_objects/anonymization_level.py`, add `PLATFORM` to `INTERMEDIATE` and `ADVANCED`:

```python
# Line 39-50: INTERMEDIATE level — add PiiCategoryEnum.PLATFORM
AnonymizationLevelEnum.INTERMEDIATE: frozenset({
    PiiCategoryEnum.PERSON_NAME,
    PiiCategoryEnum.DNI_NIE,
    PiiCategoryEnum.PASSPORT,
    PiiCategoryEnum.PHONE,
    PiiCategoryEnum.EMAIL,
    PiiCategoryEnum.BANK_ACCOUNT,
    PiiCategoryEnum.CREDIT_CARD,
    PiiCategoryEnum.DATE,
    PiiCategoryEnum.SOCIAL_SECURITY,
    PiiCategoryEnum.MEDICAL_RECORD,
    PiiCategoryEnum.PLATFORM,          # NEW: messaging platforms
}),
# Line 51-65: ADVANCED level — add PiiCategoryEnum.PLATFORM
AnonymizationLevelEnum.ADVANCED: frozenset({
    PiiCategoryEnum.PERSON_NAME,
    PiiCategoryEnum.ORGANIZATION,
    PiiCategoryEnum.ADDRESS,
    PiiCategoryEnum.DNI_NIE,
    PiiCategoryEnum.PASSPORT,
    PiiCategoryEnum.PHONE,
    PiiCategoryEnum.EMAIL,
    PiiCategoryEnum.BANK_ACCOUNT,
    PiiCategoryEnum.CREDIT_CARD,
    PiiCategoryEnum.DATE,
    PiiCategoryEnum.MEDICAL_RECORD,
    PiiCategoryEnum.LICENSE_PLATE,
    PiiCategoryEnum.SOCIAL_SECURITY,
    PiiCategoryEnum.PLATFORM,          # NEW: messaging platforms
}),
```

### Step 6: Run full test suite

Run: `python -m pytest tests/ -v --timeout=30`
Expected: All existing tests still pass.

### Step 7: Commit

```bash
git add src/contextsafe/infrastructure/nlp/composite_adapter.py \
        src/contextsafe/domain/shared/value_objects/anonymization_level.py \
        tests/unit/infrastructure/test_platform_classification.py
git commit -m "fix: prevent platform names (WhatsApp) from being classified as PERSON_NAME (Error 3)"
```

---

## Task 3: Glossary-based consistency scan for bare names (Error 1)

**Root Cause:** All regex person-name patterns require a title prefix (D., Dña., Sr., etc.). When the same name appears without a title (e.g., in a table cell), NER misses it. The glossary already knows the name but is never consulted to find undetected occurrences.

**Fix strategy:** Add a **glossary consistency scan** as a new step in `GenerateAnonymized.execute()`. After NER-provided entities are processed, scan the text for substrings matching glossary-known normalized values that weren't already detected. This is a post-replacement pass that catches bare names.

**Architecture fit:** This is in BC-003 (Anonymization), extends the use case without touching detection (BC-002). Uses existing `Glossary.find_alias()` and normalization functions.

**Files:**
- Modify: `src/contextsafe/application/use_cases/generate_anonymized/generate_anonymized.py`
- Modify: `src/contextsafe/domain/anonymization/aggregates/glossary.py` (add helper method)
- Test: `tests/unit/application/test_glossary_consistency_scan.py` (create)

### Step 1: Write the failing test

Create `tests/unit/application/test_glossary_consistency_scan.py`:

```python
"""Tests for glossary-based consistency scan in anonymization."""

import pytest
import re

from contextsafe.domain.anonymization.services.normalization import normalize_pii_value


class TestGlossaryConsistencyScan:
    """The glossary consistency scan should find bare names that NER missed."""

    def test_finds_bare_name_in_text(self):
        """A name known to the glossary should be found even without title prefix."""
        text = "En la tabla consta Rafael Durán Calvente como demandante."
        known_values = {"PERSON_NAME:rafael durán calvente": "Persona_001"}

        # Build search pattern from glossary keys
        matches = []
        for key, alias in known_values.items():
            category, normalized = key.split(":", 1)
            if category != "PERSON_NAME":
                continue
            # Search case-insensitive for the normalized value
            pattern = re.compile(re.escape(normalized), re.IGNORECASE)
            for m in pattern.finditer(text.lower()):
                # Map back to original text positions
                matches.append((m.start(), m.end(), alias))

        assert len(matches) == 1
        assert matches[0][2] == "Persona_001"

    def test_does_not_duplicate_already_replaced_entities(self):
        """Entities already replaced by NER should not be scanned again."""
        text = "D. Persona_001 presentó recurso. Rafael Durán Calvente firmó."
        # After first replacement, "D. Rafael Durán Calvente" is already "D. Persona_001"
        # Only the second bare occurrence should be found
        known_values = {"PERSON_NAME:rafael durán calvente": "Persona_001"}

        matches = []
        for key, alias in known_values.items():
            category, normalized = key.split(":", 1)
            pattern = re.compile(re.escape(normalized), re.IGNORECASE)
            for m in pattern.finditer(text.lower()):
                # Skip if this span overlaps with an already-replaced alias
                span_text = text[m.start():m.end()]
                if "Persona_" in span_text or "Org_" in span_text:
                    continue
                matches.append((m.start(), m.end(), alias))

        assert len(matches) == 1

    def test_handles_table_pipe_format(self):
        """Names in pipe-separated table cells should be found."""
        text = "Nombre | Rol\nRafael Durán Calvente | Demandante"
        known_values = {"PERSON_NAME:rafael durán calvente": "Persona_001"}

        matches = []
        for key, alias in known_values.items():
            category, normalized = key.split(":", 1)
            pattern = re.compile(re.escape(normalized), re.IGNORECASE)
            for m in pattern.finditer(text.lower()):
                matches.append((m.start(), m.end(), alias))

        assert len(matches) == 1
```

### Step 2: Run test to verify it fails/passes

Run: `python -m pytest tests/unit/application/test_glossary_consistency_scan.py -v`
Expected: These tests verify the search algorithm logic. They should PASS (they test the approach, not the integration yet).

### Step 3: Add `get_all_original_values` method to Glossary

In `src/contextsafe/domain/anonymization/aggregates/glossary.py`, add after `get_mappings_by_category` (~line 295):

```python
    def get_searchable_mappings(self) -> list[tuple[str, str, str]]:
        """
        Get all mappings in a format suitable for text search.

        Returns:
            List of (original_value, alias_value, category_str) tuples,
            sorted by original value length descending (longest first
            to avoid partial replacements).
        """
        results = []
        for key, mapping in self._mappings_by_value.items():
            # key format is "CATEGORY:normalized_value"
            parts = key.split(":", 1)
            if len(parts) == 2:
                category_str, normalized = parts
                results.append((
                    mapping.original_value if hasattr(mapping, 'original_value') else normalized,
                    mapping.alias.value,
                    category_str,
                ))
        # Sort longest first to prevent partial matches
        results.sort(key=lambda x: len(x[0]), reverse=True)
        return results
```

### Step 4: Implement the consistency scan in GenerateAnonymized

In `src/contextsafe/application/use_cases/generate_anonymized/generate_anonymized.py`, add a new method and call it after the main replacement loop.

Add import at the top:
```python
import re
from contextsafe.domain.anonymization.services.normalization import normalize_pii_value
```

Add the method to the `GenerateAnonymized` class (after `execute`):

```python
    def _glossary_consistency_scan(
        self,
        text: str,
        glossary: Any,
        replaced_spans: list[tuple[int, int]],
        level: AnonymizationLevel,
    ) -> str:
        """
        Post-replacement scan: find glossary-known values that NER missed.

        Searches the already-partially-anonymized text for occurrences of
        values that exist in the glossary but were not detected by NER.
        This catches bare names in tables, repeated mentions without titles, etc.

        Args:
            text: Text after NER-based replacements
            glossary: The project glossary with known mappings
            replaced_spans: Spans already replaced (to avoid double-processing)
            level: Anonymization level (to filter categories)

        Returns:
            Text with additional replacements applied
        """
        additional_replacements: list[tuple[int, int, str]] = []

        for lookup_key, mapping in glossary._mappings_by_value.items():
            parts = lookup_key.split(":", 1)
            if len(parts) != 2:
                continue
            category_str, normalized_value = parts

            # Check if category is included in this level
            cat_result = PiiCategory.from_string(category_str)
            if cat_result.is_err():
                continue
            category = cat_result.unwrap()
            if not level.includes_category(category.value):
                continue

            # Only scan for categories prone to detection gaps
            if category_str not in ("PERSON_NAME", "ORGANIZATION"):
                continue

            # Skip very short values (< 5 chars) to avoid false matches
            if len(normalized_value) < 5:
                continue

            # Search case-insensitive in the current text
            pattern = re.compile(re.escape(normalized_value), re.IGNORECASE)
            for match in pattern.finditer(text):
                m_start, m_end = match.start(), match.end()

                # Skip if this span overlaps with an already-replaced zone
                # (alias patterns like "Persona_001" should not be re-scanned)
                overlaps = False
                for r_start, r_end in replaced_spans:
                    if m_start < r_end and m_end > r_start:
                        overlaps = True
                        break
                if overlaps:
                    continue

                additional_replacements.append((m_start, m_end, mapping.alias.value))

        # Apply replacements in reverse order (largest offset first)
        additional_replacements.sort(key=lambda x: x[0], reverse=True)
        for start, end, alias_value in additional_replacements:
            after_char = text[end:end + 1] if end < len(text) else ""
            space_suffix = " " if after_char.isalnum() else ""
            text = text[:start] + alias_value + space_suffix + text[end:]

        return text
```

Then in `execute()`, after the main replacement loop (after line 201) and before "10. Complete anonymization" (line 203), add:

```python
        # 9.5 Glossary consistency scan — find values NER missed
        replaced_spans = [
            (entity.start, entity.end) for entity in sorted_entities
            if PiiCategory.from_string(entity.category).is_ok()
            and level.includes_category(PiiCategory.from_string(entity.category).unwrap().value)
        ]
        text = self._glossary_consistency_scan(text, glossary, replaced_spans, level)
```

### Step 5: Run tests

Run: `python -m pytest tests/unit/application/ -v --timeout=30`
Expected: PASS

### Step 6: Run full test suite

Run: `python -m pytest tests/ -v --timeout=30`
Expected: All tests pass.

### Step 7: Commit

```bash
git add src/contextsafe/application/use_cases/generate_anonymized/generate_anonymized.py \
        src/contextsafe/domain/anonymization/aggregates/glossary.py \
        tests/unit/application/test_glossary_consistency_scan.py
git commit -m "feat: add glossary consistency scan to catch bare names missed by NER (Error 1)"
```

---

## Task 4: Date detection robustness (Error 2)

**Root Cause:** Two possible issues:
1. **SpanishDateRecognizer** (Presidio) has a context requirement that silently drops dates without nearby context words — relevant if Presidio is ever used.
2. In the production `CompositeNerAdapter`, the regex adapter DOES detect dates (pattern at line 634), but the weighted voting or false-positive filters may be dropping them.

**Fix strategy:**
- **Part A:** Fix `SpanishDateRecognizer` to not require context words (defensive fix for when Presidio is used).
- **Part B:** Add `_TERM` pipe terminator to regex name patterns so table-formatted text doesn't break other detections.
- **Part C:** Add regression test that verifies dates without context ARE detected.

**Files:**
- Modify: `src/contextsafe/infrastructure/nlp/recognizers/spanish_dates.py:92-106`
- Modify: `src/contextsafe/infrastructure/nlp/regex_adapter.py:149` (add `|` to `_TERM`)
- Test: `tests/unit/infrastructure/test_date_detection.py` (create)

### Step 1: Write the failing test

Create `tests/unit/infrastructure/test_date_detection.py`:

```python
"""Tests for date detection without surrounding context keywords."""

import pytest

from contextsafe.infrastructure.nlp.regex_adapter import RegexNerAdapter


class TestDateDetectionWithoutContext:
    """Dates should be detected even without context keywords like 'fecha' nearby."""

    @pytest.fixture
    def adapter(self):
        return RegexNerAdapter()

    @pytest.mark.asyncio
    async def test_detects_written_date_in_isolation(self, adapter):
        """'4 de diciembre de 2024' should be detected as DATE."""
        text = "Martorell, a 4 de diciembre de 2024."
        detections = await adapter.detect_entities(text)
        date_dets = [d for d in detections if d.category.value == "DATE"]
        assert len(date_dets) >= 1
        assert "4 de diciembre de 2024" in date_dets[0].value

    @pytest.mark.asyncio
    async def test_detects_single_digit_day(self, adapter):
        """Single-digit day '9 de diciembre' should be detected."""
        text = "firmado el 9 de diciembre de 2024 por el Letrado"
        detections = await adapter.detect_entities(text)
        date_dets = [d for d in detections if d.category.value == "DATE"]
        assert len(date_dets) >= 1
        assert "9 de diciembre de 2024" in date_dets[0].value

    @pytest.mark.asyncio
    async def test_detects_date_in_suplico_section(self, adapter):
        """Dates in SUPLICO section should be detected."""
        text = "SUPLICO al Juzgado que desde el 4 de diciembre de 2024 se proceda"
        detections = await adapter.detect_entities(text)
        date_dets = [d for d in detections if d.category.value == "DATE"]
        assert len(date_dets) >= 1
```

### Step 2: Run test to verify

Run: `python -m pytest tests/unit/infrastructure/test_date_detection.py -v`
Expected: If regex patterns are correct, these should PASS already. If they fail, the regex has an issue.

### Step 3: Fix SpanishDateRecognizer context requirement

In `src/contextsafe/infrastructure/nlp/recognizers/spanish_dates.py`, change the constructor to use an empty context by default:

```python
# BEFORE (line 106):
        context = context if context else self.CONTEXT

# AFTER:
        context = context if context is not None else []
```

This makes the recognizer work without requiring context keywords. The `CONTEXT` list is kept as a class constant for documentation and optional use.

### Step 4: Add pipe to regex _TERM terminators

In `src/contextsafe/infrastructure/nlp/regex_adapter.py`, line 149:

```python
# BEFORE:
_TERM = rf'(?={_S0}[,.:;\n>)\]]|{_S}[a-záéíóúñü]|\s*$)'

# AFTER:
_TERM = rf'(?={_S0}[,.:;\n>)\]|]|{_S}[a-záéíóúñü]|\s*$)'
```

Note: Added `|` (pipe character) inside the character class `[,.:;\n>)\]|]`. This allows name patterns to terminate at pipe characters, enabling detection of names in pipe-delimited table text.

### Step 5: Run tests

Run: `python -m pytest tests/unit/infrastructure/test_date_detection.py tests/unit/infrastructure/test_spanish_recognizers.py -v`
Expected: All PASS.

### Step 6: Run full test suite

Run: `python -m pytest tests/ -v --timeout=30`
Expected: No regressions.

### Step 7: Commit

```bash
git add src/contextsafe/infrastructure/nlp/recognizers/spanish_dates.py \
        src/contextsafe/infrastructure/nlp/regex_adapter.py \
        tests/unit/infrastructure/test_date_detection.py
git commit -m "fix: ensure dates detected without context keywords, add pipe to name terminators (Error 2)"
```

---

## Verification

After all 4 tasks, run the full test suite:

```bash
python -m pytest tests/ -v --timeout=60
```

Expected: All tests pass, including the 3 new test files:
- `tests/unit/application/test_generate_anonymized.py`
- `tests/unit/infrastructure/test_platform_classification.py`
- `tests/unit/infrastructure/test_date_detection.py`
- `tests/unit/application/test_glossary_consistency_scan.py`

---

## Summary of Changes

| Error | Fix | File(s) Modified | Risk |
|-------|-----|-----------------|------|
| 5: Spacing | Boundary check after replacement | `generate_anonymized.py` | Low — additive check |
| 3: WhatsApp→Persona | Platform blocklist + PLATFORM in levels | `composite_adapter.py`, `anonymization_level.py` | Low — blocklist only |
| 1: Bare name in table | Glossary consistency scan | `generate_anonymized.py`, `glossary.py` | Medium — new scan pass |
| 2: Dates without context | Remove context requirement, add pipe terminator | `spanish_dates.py`, `regex_adapter.py` | Low — relaxes constraint |
