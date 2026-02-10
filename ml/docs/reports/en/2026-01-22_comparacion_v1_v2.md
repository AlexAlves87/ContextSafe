# Comparison: Model v1 vs v2 (Noise Training)

**Date:** 2026-01-22
**Author:** AlexAlves87
**Type:** Comparative Analysis
**Status:** Completed

---

## Executive Summary

| Metric | v1 | v2 | Change |
|---------|-----|-----|--------|
| Adversarial Pass Rate | 45.7% (16/35) | 54.3% (19/35) | **+8.6 pp** |
| Synthetic Test F1 | 99.87% | 100% | +0.13 pp |
| Dataset | v2 (clean) | v3 (30% noise) | - |

**Conclusion:** Injecting OCR noise during training improved model robustness by +8.6 percentage points in adversarial tests.

---

## Methodology

### Training Differences

| Aspect | v1 | v2 |
|---------|-----|-----|
| Dataset | `ner_dataset_v2` | `ner_dataset_v3` |
| Noise injection | 0% | 30% |
| Noise types | - | l↔I, 0↔O, accents, spaces |
| Hyperparams | Identical | Identical |
| Base model | roberta-bne-capitel-ner | roberta-bne-capitel-ner |

### Adversarial Tests (35 cases)

| Category | Tests |
|-----------|-------|
| edge_case | 9 |
| adversarial | 8 |
| ocr_corruption | 5 |
| unicode_evasion | 3 |
| real_world | 10 |

---

## Results by Category

### Pass Rate Comparison

| Category | v1 | v2 | Improvement |
|-----------|-----|-----|--------|
| edge_case | 55.6% (5/9) | 66.7% (6/9) | +11.1 pp |
| adversarial | 37.5% (3/8) | 62.5% (5/8) | **+25.0 pp** |
| ocr_corruption | 20.0% (1/5) | 40.0% (2/5) | **+20.0 pp** |
| unicode_evasion | 33.3% (1/3) | 33.3% (1/3) | 0 pp |
| real_world | 60.0% (6/10) | 50.0% (5/10) | -10.0 pp |

### Analysis by Category

**Significant Improvements (+20 pp or more):**
- **adversarial**: +25 pp - Better context discrimination (negation, examples)
- **ocr_corruption**: +20 pp - Training noise helped directly

**No Change:**
- **unicode_evasion**: 33.3% - Requires text normalization, not just training

**Regression:**
- **real_world**: -10 pp - Possible overfitting to noise, less robustness to complex patterns

---

## Details of Changed Tests

### Tests PASSING in v2 (previously FAIL)

| Test | Category | Note |
|------|-----------|------|
| `ocr_letter_substitution` | ocr_corruption | DNl → DNI (l vs I) |
| `ocr_accent_loss` | ocr_corruption | José → Jose |
| `negation_dni` | adversarial | "NO tener DNI" - no longer detects PII |
| `organization_as_person` | adversarial | García y Asociados → ORG |
| `location_as_person` | adversarial | San Fernando → LOCATION |

### Tests FAILING in v2 (previously PASS)

| Test | Category | Note |
|------|-----------|------|
| `notarial_header` | real_world | Possible regression in written dates |
| `judicial_sentence_header` | real_world | Possible regression in uppercase names |

---

## Conclusions

### Main Findings

1. **Noise training works**: +8.6 pp global improvement, especially in OCR and adversarial
2. **Specific noise matters**: l↔I, accents improved, but 0↔O and spaces still failing
3. **Trade-off observed**: Gained robustness to noise but lost some precision in complex patterns

### Approach Limitations

1. **Insufficient noise for 0↔O**: IBAN with O instead of 0 still failing
2. **Normalization needed**: Unicode evasion requires preprocessing, not just training
3. **Real-world complexity**: Complex documents require more training data

### Recommendations

| Priority | Action | Expected Impact |
|-----------|--------|------------------|
| HIGH | Add Unicode normalization in preprocessing | +10% unicode_evasion |
| HIGH | More variety of 0↔O noise in training | +5-10% ocr_corruption |
| MEDIUM | More real_world examples in dataset | Recover -10% real_world |
| MEDIUM | Hybrid pipeline (Regex → NER → Validation) | +15-20% according to literature |

---

## Next Steps

1. **Implement hybrid pipeline** according to research PMC12214779
2. **Add text_normalizer.py** as preprocessing before inference
3. **Expand dataset** with more real document examples
4. **Evaluate CRF layer** to improve sequence coherence

---

## Related Files

- `docs/reports/2026-01-20_adversarial_evaluation.md` - v1 Evaluation
- `docs/reports/2026-01-21_adversarial_evaluation_v2.md` - v2 Evaluation
- `docs/reports/2026-01-16_investigacion_pipeline_pii.md` - Best practices
- `scripts/preprocess/inject_ocr_noise.py` - Noise injection script

---

**Date:** 2026-01-22
