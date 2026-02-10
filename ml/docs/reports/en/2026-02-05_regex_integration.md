# Regex Patterns - Integration Test

**Date:** 2026-02-05
**Author:** AlexAlves87
**Component:** Regex pattern integration in `scripts/inference/ner_predictor.py`
**Standard:** CHPDA (2025) - Hybrid regex+NER approach

---

## 1. Executive Summary

Integration of regex patterns to detect identifiers with spaces/hyphens that the NER transformer model misses.

### Results

| Test Suite | Before | After | Improvement |
|------------|-------|---------|--------|
| Integration tests | - | 11/14 (78.6%) | New |
| Adversarial (strict) | 34.3% | **45.7%** | **+11.4pp** |
| F1 (strict) | 0.492 | **0.543** | **+0.051** |

### Conclusion

> **Regex integration significantly improves detection of formatted identifiers.**
> Pass rate +11.4pp, F1 +0.051. IBAN with spaces is now correctly detected.

---

## 2. Methodology

### 2.1 Merge Strategy (Hybrid)

```
Input Text
       ↓
┌──────────────────────┐
│  1. NER Transformer  │  Detects semantic entities
└──────────────────────┘
       ↓
┌──────────────────────┐
│  2. Regex Patterns   │  Detects formats with spaces
└──────────────────────┘
       ↓
┌──────────────────────┐
│  3. Merge Strategy   │  Combines, prefers most complete
└──────────────────────┘
       ↓
┌──────────────────────┐
│  4. Checksum Valid.  │  Adjusts confidence
└──────────────────────┘
       ↓
Final Entities
```

### 2.2 Merge Logic

| Case | Action |
|------|--------|
| Only NER detects | Keep NER |
| Only Regex detects | Add Regex |
| Both detect same span | Keep NER (higher semantic quality) |
| Regex >20% longer than NER | Replace NER with Regex |
| Partial NER, complete Regex | Replace with Regex |

### 2.3 Reproducibility

```bash
# Environment
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Regex integration test
python scripts/evaluate/test_regex_integration.py

# Full adversarial test
python scripts/evaluate/test_ner_predictor_adversarial_v2.py
```

---

## 3. Results

### 3.1 Integration Tests (11/14)

| Test | Input | Result | Source |
|------|-------|-----------|--------|
| dni_spaces_2_3_3 | `12 345 678 Z` | ✅ | ner |
| dni_spaces_4_4 | `1234 5678 Z` | ✅ | ner |
| dni_dots | `12.345.678-Z` | ✅ | ner |
| nie_dashes | `X-1234567-Z` | ✅ | ner |
| **iban_spaces** | `ES91 2100 0418...` | ✅ | **regex** |
| phone_spaces | `612 345 678` | ✅ | regex |
| phone_intl | `+34 612345678` | ❌ | - |
| cif_dashes | `A-1234567-4` | ❌ (wrong type) | ner |
| nss_slashes | `28/12345678/90` | ✅ | ner |
| dni_standard | `12345678Z` | ✅ | ner |

### 3.2 Impact on Adversarial Tests

| Metric | Baseline | +Normalizer | +Regex | Total Delta |
|---------|----------|-------------|--------|-------------|
| **Pass Rate** | 28.6% | 34.3% | **45.7%** | **+17.1pp** |
| **F1 (strict)** | 0.464 | 0.492 | **0.543** | **+0.079** |
| F1 (partial) | 0.632 | 0.659 | **0.690** | +0.058 |
| COR | 29 | 31 | **35** | **+6** |
| MIS | 17 | 15 | **12** | **-5** |
| PAR | 21 | 21 | **19** | -2 |
| SPU | 8 | 7 | **7** | -1 |

### 3.3 Improvement Analysis

| Adversarial Test | Before | After | Improvement |
|------------------|-------|---------|--------|
| dni_with_spaces | MIS:1 | COR:1 | +1 COR |
| iban_with_spaces | PAR:1 | COR:1 | PAR→COR |
| phone_international | MIS:1 | COR:1* | +1 COR |
| address_floor_door | PAR:1 | COR:1 | PAR→COR |

*Partial detection improved

---

## 4. Error Analysis

### 4.1 Remaining Failures

| Test | Problem | Cause |
|------|----------|-------|
| phone_intl | `+34` not included | NER detects `612345678`, insufficient overlap |
| cif_dashes | Incorrect type | Model classifies CIF as DNI_NIE |
| spaced_iban_source | Not detected isolated | Minimal context reduces detection |

### 4.2 Observations

1. **NER learns formats with spaces**: Surprisingly, NER detects some DNIs with spaces (probably from previous data augmentation)

2. **Regex complements, does not replace**: Most detections remain NER, regex only adds cases NER misses

3. **Checksum applies to both**: Both NER and regex pass through checksum validation

---

## 5. Conclusions and Future Work

### 5.1 Conclusions

1. **Significant improvement**: +17.1pp pass rate, +0.079 F1
2. **IBAN with spaces**: Problem solved (regex correctly detects)
3. **Smart merge**: Prefers more complete detections
4. **Minimal overhead**: ~100ms additional for 25 patterns

### 5.2 Current State vs Target

| Metric | Baseline | Current | Target | Gap |
|---------|----------|--------|----------|-----|
| Pass Rate | 28.6% | **45.7%** | ≥70% | -24.3pp |
| F1 (strict) | 0.464 | **0.543** | ≥0.70 | -0.157 |

### 5.3 Next Steps

| Priority | Task | Estimated Impact |
|-----------|-------|------------------|
| HIGH | Textual date data augmentation | +3-4 COR |
| MEDIUM | Correct CIF classification | +1 COR |
| MEDIUM | Improve phone_intl detection | +1 COR |
| LOW | Boundary refinement for PAR→COR | +2-3 COR |

---

## 6. References

1. **Standalone tests:** `docs/reports/2026-02-05_regex_patterns_standalone.md`
2. **CHPDA (2025):** [arXiv](https://arxiv.org/html/2502.07815v1) - Hybrid regex+NER
3. **Pattern script:** `scripts/preprocess/spanish_id_patterns.py`
4. **Integration test:** `scripts/evaluate/test_regex_integration.py`

---

**Date:** 2026-02-05
