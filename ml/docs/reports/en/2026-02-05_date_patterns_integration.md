# Date Patterns - Integration Test

**Date:** 2026-02-05
**Author:** AlexAlves87
**Component:** `scripts/preprocess/spanish_date_patterns.py` integrated into pipeline
**Standard:** TIMEX3 for temporal expressions

---

## 1. Executive Summary

Integration of regex patterns for Spanish textual dates that complement NER detection.

### Results

| Test Suite | Result |
|------------|--------|
| Standalone tests | 14/14 (100%) |
| Integration tests | 9/9 (100%) |
| Adversarial (improvement) | +2.9pp pass rate |

### Conclusion

> **Date patterns add value primarily for Roman numerals.**
> The NER model already detects most textual dates.
> Total accumulated improvement: Pass rate +20pp, F1 +0.081 from baseline.

---

## 2. Methodology

### 2.1 Implemented Patterns (10 total)

| Pattern | Example | Confidence |
|---------|---------|------------|
| `date_roman_full` | XV de marzo del año MMXXIV | 0.95 |
| `date_roman_day_written_year` | XV de marzo de dos mil... | 0.90 |
| `date_written_full` | quince de marzo de dos mil... | 0.95 |
| `date_ordinal_full` | primero de enero de dos mil... | 0.95 |
| `date_written_day_numeric_year` | quince de marzo de 2024 | 0.90 |
| `date_ordinal_numeric_year` | primero de enero de 2024 | 0.90 |
| `date_a_written` | a veinte de abril de dos mil... | 0.90 |
| `date_el_dia_written` | el día quince de marzo de... | 0.90 |
| `date_numeric_standard` | 15 de marzo de 2024 | 0.85 |
| `date_formal_legal` | día 15 del mes de marzo del año 2024 | 0.90 |

### 2.2 Integration

Date patterns were integrated into `spanish_id_patterns.py`:

```python
# In find_matches():
if DATE_PATTERNS_AVAILABLE and (entity_types is None or "DATE" in entity_types):
    date_matches = find_date_matches(text)
    for dm in date_matches:
        matches.append(RegexMatch(
            text=dm.text,
            entity_type="DATE",
            ...
        ))
```

### 2.3 Reproducibility

```bash
# Environment
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Standalone test
python scripts/preprocess/spanish_date_patterns.py

# Integration test
python scripts/evaluate/test_date_integration.py

# Full adversarial test
python scripts/evaluate/test_ner_predictor_adversarial_v2.py
```

---

## 3. Results

### 3.1 Integration Tests (9/9)

| Test | Text | Source | Result |
|------|------|--------|--------|
| roman_full | XV de marzo del año MMXXIV | **regex** | ✅ |
| ordinal_full | primero de enero de dos mil... | ner | ✅ |
| notarial_date | quince de marzo de dos mil... | ner | ✅ |
| testament_date | diez de enero de dos mil... | ner | ✅ |
| written_full | veintiocho de febrero de... | ner | ✅ |
| numeric_standard | 15 de marzo de 2024 | ner | ✅ |
| multiple_dates | uno de enero...diciembre... | ner | ✅ |
| date_roman_numerals | XV de marzo del año MMXXIV | **regex** | ✅ |
| date_ordinal | primero de enero de... | ner | ✅ |

### 3.2 Key Observation

**The NER model already detects most textual dates.** The regex adds value only for:
- **Roman numerals** (XV, MMXXIV) - not in model vocabulary

### 3.3 Impact on Adversarial Tests

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Pass Rate | 45.7% | **48.6%** | **+2.9pp** |
| F1 (strict) | 0.543 | **0.545** | +0.002 |
| F1 (partial) | 0.690 | **0.705** | +0.015 |
| COR | 35 | **36** | **+1** |
| MIS | 12 | **9** | **-3** |
| PAR | 19 | 21 | +2 |

---

## 4. Total Accumulated Progress

### 4.1 Integrated Elements

| Element | Standalone | Integration | Main Impact |
|---------|------------|-------------|-------------|
| 1. TextNormalizer | 15/15 | ✅ | Unicode evasion |
| 2. Checksum | 23/24 | ✅ | Confidence adjustment |
| 3. Regex IDs | 22/22 | ✅ | Spaced identifiers |
| 4. Date Patterns | 14/14 | ✅ | Roman numerals |

### 4.2 Total Metrics

| Metric | Baseline | Current | Improvement | Goal | Gap |
|--------|----------|---------|-------------|------|-----|
| **Pass Rate** | 28.6% | **48.6%** | **+20pp** | ≥70% | -21.4pp |
| **F1 (strict)** | 0.464 | **0.545** | **+0.081** | ≥0.70 | -0.155 |
| COR | 29 | 36 | +7 | - | - |
| MIS | 17 | 9 | -8 | - | - |
| SPU | 8 | 7 | -1 | - | - |
| PAR | 21 | 21 | 0 | - | - |

### 4.3 Visual Progress

```
Pass Rate:
Baseline   [████████░░░░░░░░░░░░░░░░░░░░░░░░░░░] 28.6%
Actual     [█████████████████░░░░░░░░░░░░░░░░░░] 48.6%
Goal       [████████████████████████████░░░░░░░] 70.0%

F1 (strict):
Baseline   [████████████████░░░░░░░░░░░░░░░░░░░] 0.464
Actual     [███████████████████░░░░░░░░░░░░░░░░] 0.545
Goal       [████████████████████████████░░░░░░░] 0.700
```

---

## 5. Conclusions and Future Work

### 5.1 Conclusions

1. **Significant progress**: +20pp pass rate, +0.081 F1 from baseline
2. **MIS drastically reduced**: 17 → 9 (-8 missed entities)
3. **Hybrid pipeline works**: NER + Regex + Checksum complement each other
4. **NER model is robust for dates**: Only needs regex for Roman numerals

### 5.2 Remaining Gap

| To reach goal | Need |
|---------------|------|
| Pass rate 70% | +21.4pp more |
| F1 0.70 | +0.155 more |
| Equivalent to | ~8-10 additional COR |

### 5.3 Potential Next Steps

| Priority | Improvement | Estimated Impact |
|----------|-------------|------------------|
| HIGH | Boundary refinement (PAR→COR) | +5-6 COR |
| MEDIUM | Model data augmentation | +3-4 COR |
| MEDIUM | Correct CIF classification | +1 COR |
| LOW | Improve phone_intl detection | +1 COR |

---

## 6. References

1. **Standalone tests:** `scripts/preprocess/spanish_date_patterns.py`
2. **Integration tests:** `scripts/evaluate/test_date_integration.py`
3. **TIMEX3:** ISO-TimeML annotation standard
4. **HeidelTime/SUTime:** Reference temporal taggers

---

**Date:** 2026-02-05
