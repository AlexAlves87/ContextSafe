# Regex Patterns for Spanish Identifiers - Standalone Test

**Date:** 2026-02-05
**Author:** AlexAlves87
**Component:** `scripts/preprocess/spanish_id_patterns.py`
**Standard:** CHPDA (2025) - Hybrid regex+NER approach

---

## 1. Executive Summary

Implementation of regex patterns to detect Spanish identifiers with variant formats (spaces, dashes, dots) that transformer NER models typically fail to detect.

### Results

| Metric | Value |
|--------|-------|
| **Tests Passed** | 22/22 (100%) |
| **Entity Types** | 5 (DNI_NIE, IBAN, NSS, CIF, PHONE) |
| **Total Patterns** | 25 |

### Conclusion

> **All patterns work correctly for formats with spaces and separators.**
> This complements the transformer NER which fails in cases like "12 345 678 Z" or "ES91 2100 0418...".

---

## 2. Methodology

### 2.1 Base Research

| Paper | Approach | Application |
|-------|----------|-------------|
| **CHPDA (arXiv 2025)** | Hybrid Regex + AI NER | Reduces false positives |
| **Hybrid ReGex (JCO 2025)** | Lightweight regex + ML pipeline | Medical data extraction |
| **Legal NLP Survey (2024)** | Specialized legal NER | Regulatory patterns |

### 2.2 Implemented Patterns

| Type | Patterns | Examples |
|------|----------|----------|
| **DNI** | 6 | `12345678Z`, `12 345 678 Z`, `12.345.678-Z` |
| **NIE** | 3 | `X1234567Z`, `X 1234567 Z`, `X-1234567-Z` |
| **IBAN** | 3 | `ES9121...`, `ES91 2100 0418...` |
| **NSS** | 3 | `281234567890`, `28/12345678/90` |
| **CIF** | 3 | `A12345674`, `A-1234567-4` |
| **PHONE** | 7 | `612345678`, `612 345 678`, `+34 612...` |

### 2.3 Reproducibility

```bash
# Environment
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Execution
python scripts/preprocess/spanish_id_patterns.py

# Expected output: 22/22 passed (100.0%)
```

---

## 3. Results

### 3.1 Tests by Type

| Type | Tests | Passed | Key Examples |
|------|-------|--------|--------------|
| DNI | 6 | 6 | Standard, spaces 2-3-3, dots |
| NIE | 3 | 3 | Standard, spaces, dashes |
| IBAN | 2 | 2 | Standard, spaces groups 4 |
| NSS | 2 | 2 | Slashes, spaces |
| CIF | 2 | 2 | Standard, dashes |
| PHONE | 4 | 4 | Mobile, fixed, international |
| Negatives | 2 | 2 | Rejects invalid formats |
| Multi | 1 | 1 | Multiple entities in text |

### 3.2 Detection Demo

| Input | Detection | Normalized |
|-------|-----------|------------|
| `DNI 12 345 678 Z` | ✅ DNI_NIE | `12345678Z` |
| `IBAN ES91 2100 0418 4502 0005 1332` | ✅ IBAN | `ES9121000418450200051332` |
| `NIE X-1234567-Z` | ✅ DNI_NIE | `X1234567Z` |
| `Tel: 612 345 678` | ✅ PHONE | `612345678` |
| `CIF A-1234567-4` | ✅ CIF | `A12345674` |

### 3.3 Match Structure

```python
@dataclass
class RegexMatch:
    text: str           # "12 345 678 Z"
    entity_type: str    # "DNI_NIE"
    start: int          # 4
    end: int            # 16
    confidence: float   # 0.90
    pattern_name: str   # "dni_spaced_2_3_3"
```

---

## 4. Pattern Analysis

### 4.1 Confidence Levels

| Level | Confidence | Criterion |
|-------|------------|-----------|
| High | 0.95 | Standard format without ambiguity |
| Medium | 0.90 | Format with valid separators |
| Low | 0.70-0.85 | Formats that may be ambiguous |

### 4.2 Spaced DNI Patterns (Original Problem)

The adversarial test `dni_with_spaces` failed because the NER did not detect "12 345 678 Z".

**Implemented Solution:**
```python
# Pattern for spaces 2-3-3
r'\b(\d{2})\s+(\d{3})\s+(\d{3})\s*([A-Z])\b'
```

This pattern detects:
- `12 345 678 Z` ✅
- `12 345 678Z` ✅ (no space before letter)

### 4.3 Normalization for Checksum

`normalize_match()` function removes separators for validation:

```python
"12 345 678 Z" → "12345678Z"
"ES91 2100 0418..." → "ES9121000418..."
"X-1234567-Z" → "X1234567Z"
```

---

## 5. Conclusions and Future Work

### 5.1 Conclusions

1. **25 patterns cover variant formats** of Spanish identifiers
2. **Normalization enables integration** with checksum validators
3. **Variable confidence** distinguishes more/less reliable formats
4. **Overlap detection** avoids duplicates

### 5.2 Pipeline Integration

```
Input Text
       ↓
┌──────────────────────┐
│  1. TextNormalizer   │  Unicode/OCR cleanup
└──────────────────────┘
       ↓
┌──────────────────────┐
│  2. NER Transformer  │  RoBERTalex predictions
└──────────────────────┘
       ↓
┌──────────────────────┐
│  3. Regex Patterns   │  ← NEW: detects spaces
└──────────────────────┘
       ↓
┌──────────────────────┐
│  4. Merge & Dedup    │  Combines NER + Regex
└──────────────────────┘
       ↓
┌──────────────────────┐
│  5. Checksum Valid.  │  Adjusts confidence
└──────────────────────┘
       ↓
Final Entities
```

### 5.3 Estimated Impact

| Adversarial Test | Before | After | Improvement |
|------------------|--------|-------|-------------|
| `dni_with_spaces` | MIS:1 | COR:1 | +1 COR |
| `iban_with_spaces` | PAR:1 | COR:1 | +1 COR |
| `phone_international` | MIS:1 | COR:1 | +1 COR (potential) |

**Total Estimate:** +2-3 COR, conversion from MIS and PAR to COR.

---

## 6. References

1. **CHPDA (2025):** [arXiv](https://arxiv.org/html/2502.07815v1) - Hybrid regex+NER approach
2. **Hybrid ReGex (2025):** [JCO](https://ascopubs.org/doi/10.1200/CCI-25-00130) - Medical data extraction
3. **Legal NLP Survey (2024):** [arXiv](https://arxiv.org/html/2410.21306v3) - NER for legal domain

---

**Date:** 2026-02-05
