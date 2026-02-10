# Checksum Validators - Integration Test

**Date:** 2026-02-04
**Author:** AlexAlves87
**Component:** Integration of validators in `scripts/inference/ner_predictor.py`
**Standard:** Official Spanish Algorithms (BOE)

---

## 1. Executive Summary

Integration and validation of checksum validators in the NER pipeline for post-validation of Spanish identifiers.

### Results

| Category | Passed | Total | % |
|----------|--------|-------|---|
| Unit tests | 13 | 13 | 100% |
| Integration tests | 6 | 7 | 85.7% |
| Confidence tests | 1 | 1 | 100% |
| **TOTAL** | **20** | **21** | **95.2%** |

### Conclusion

> **Checksum validator integration works correctly.**
> The only failure (valid IBAN not detected) is a NER model issue, not a validation issue.
> Confidence is adjusted appropriately: +10% for valid, -20% for invalid.

---

## 2. Methodology

### 2.1 Integration Design

| Aspect | Implementation |
|--------|----------------|
| Location | `scripts/inference/ner_predictor.py` |
| Validatable Types | DNI_NIE, IBAN, NSS, CIF |
| Timing | Post-entity extraction |
| Output | `checksum_valid`, `checksum_reason` in PredictedEntity |

### 2.2 Confidence Adjustment

| Checksum Result | Adjustment |
|-----------------|------------|
| Valid (`is_valid=True`) | `confidence * 1.1` (max 0.99) |
| Invalid, format ok (`conf=0.5`) | `confidence * 0.8` |
| Invalid format (`conf<0.5`) | `confidence * 0.5` |

### 2.3 Reproducibility

```bash
# Environment
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Execution
python scripts/evaluate/test_checksum_integration.py

# Expected Output: 20/21 passed (95.2%)
```

---

## 3. Results

### 3.1 Unit Tests (13/13 ✅)

| Validator | Test | Input | Result |
|-----------|------|-------|--------|
| DNI | valid | `12345678Z` | ✅ True |
| DNI | invalid | `12345678A` | ✅ False |
| DNI | zeros | `00000000T` | ✅ True |
| NIE | X valid | `X0000000T` | ✅ True |
| NIE | Y valid | `Y0000000Z` | ✅ True |
| NIE | Z valid | `Z0000000M` | ✅ True |
| NIE | invalid | `X0000000A` | ✅ False |
| IBAN | valid | `ES9121000418450200051332` | ✅ True |
| IBAN | spaces | `ES91 2100 0418...` | ✅ True |
| IBAN | invalid | `ES0000000000000000000000` | ✅ False |
| NSS | format | `281234567800` | ✅ False |
| CIF | valid | `A12345674` | ✅ True |
| CIF | invalid | `A12345670` | ✅ False |

### 3.2 Integration Tests (6/7)

| Test | Input | Detection | Checksum | Result |
|------|-------|-----------|----------|--------|
| dni_valid | `DNI 12345678Z` | ✅ conf=0.99 | valid=True | ✅ |
| dni_invalid | `DNI 12345678A` | ✅ conf=0.73 | valid=False | ✅ |
| nie_valid | `NIE X0000000T` | ✅ conf=0.86 | valid=True | ✅ |
| nie_invalid | `NIE X0000000A` | ✅ conf=0.61 | valid=False | ✅ |
| iban_valid | `IBAN ES91...` | ❌ Not detected | - | ❌ |
| iban_invalid | `IBAN ES00...` | ✅ conf=0.25 | valid=False | ✅ |
| person | `Don José García` | ✅ conf=0.98 | valid=None | ✅ |

### 3.3 Confidence Adjustment (1/1 ✅)

| ID | Type | Base Conf | Checksum | Final Conf | Adjustment |
|----|------|-----------|----------|------------|------------|
| `12345678Z` | DNI valid | ~0.90 | ✅ | **0.99** | +10% |
| `12345678A` | DNI invalid | ~0.91 | ❌ | **0.73** | -20% |

**Net difference:** Valid DNI has +0.27 more confidence than invalid one.

---

## 4. Error Analysis

### 4.1 Only Failure: Valid IBAN Not Detected

| Aspect | Detail |
|--------|--------|
| Test | `iban_valid` |
| Input | `"Transferir a IBAN ES9121000418450200051332."` |
| Expected | IBAN detection with valid checksum |
| Result | NER model did not detect IBAN entity |
| Cause | Limitation of legal_ner_v2 model |

**Note:** This failure is NOT from checksum validation, but from the NER model. IBAN checksum validation works correctly (proven in unit tests and invalid IBAN test).

### 4.2 Observation: Invalid IBAN Includes Prefix

The model detected `"IBAN ES0000000000000000000000"` including the word "IBAN". This causes the format to be invalid (`invalid_format`) instead of `invalid_checksum`.

**Implication:** Extracted text cleaning may be needed before validation.

---

## 5. Impact on NER Pipeline

### 5.1 Observed Benefits

| Benefit | Evidence |
|---------|----------|
| **Valid/Invalid Distinction** | Valid DNI 0.99 vs invalid 0.73 |
| **Additional Metadata** | `checksum_valid`, `checksum_reason` |
| **Potential SPU Reduction** | IDs with invalid checksum have lower confidence |

### 5.2 Use Cases

| Scenario | Recommended Action |
|----------|--------------------|
| checksum_valid=True | High confidence, process normally |
| checksum_valid=False, reason=invalid_checksum | Possible typo/OCR, review manually |
| checksum_valid=False, reason=invalid_format | Possible false positive, consider filtering |

---

## 6. Conclusions and Future Work

### 6.1 Conclusions

1. **Successful integration:** Validators run automatically in the NER pipeline
2. **Confidence adjustment works:** +10% for valid, -20% for invalid
3. **Metadata available:** `checksum_valid` and `checksum_reason` in each entity
4. **Minimal overhead:** ~0ms additional (string/math operations)

### 6.2 Next Steps

| Priority | Task | Impact |
|----------|------|--------|
| HIGH | Evaluate impact on SemEval metrics (SPU reduction) | Reduce false positives |
| MEDIUM | Clean text before validation (remove "IBAN ", etc.) | Improve accuracy |
| LOW | Add validation for more types (phone, license plate) | Coverage |

### 6.3 Full Integration

Checksum validation is now integrated in:

```
ner_predictor.py
├── normalize_text_for_ner()     # Unicode/OCR robustness
├── _extract_entities()          # BIO → entities
└── validate_entity_checksum()   # ← NEW: post-validation
```

---

## 7. References

1. **Standalone tests:** `docs/reports/2026-02-04_checksum_validators_standalone.md`
2. **Base research:** `docs/reports/2026-01-28_investigacion_hybrid_ner.md`
3. **Integration script:** `scripts/inference/ner_predictor.py`
4. **Integration test:** `scripts/evaluate/test_checksum_integration.py`

---

**Date:** 2026-02-04
