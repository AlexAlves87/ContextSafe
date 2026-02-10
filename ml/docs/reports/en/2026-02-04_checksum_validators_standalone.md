# Checksum Validators - Standalone Test

**Date:** 2026-02-04
**Author:** AlexAlves87
**Component:** `scripts/preprocess/checksum_validators.py`
**Standard:** Official Spanish Algorithms (BOE)

---

## 1. Executive Summary

Implementation and standalone validation of checksum validators for Spanish identifiers used in the NER-PII pipeline.

### Results

| Metric | Value |
|--------|-------|
| **Tests Passed** | 23/24 (95.8%) |
| **Implemented Validators** | 5 (DNI, NIE, IBAN, NSS, CIF) |

### Conclusion

> **All validators work correctly according to official algorithms.**
> The only failure (NSS edge case) is an error in the test expectation, not in the validator.

---

## 2. Methodology

### 2.1 Implemented Algorithms

| Identifier | Algorithm | Source |
|------------|-----------|--------|
| **DNI** | `letter = TRWAGMYFPDXBNJZSQVHLCKE[number % 23]` | BOE |
| **NIE** | X→0, Y→1, Z→2, then DNI | BOE |
| **IBAN** | ISO 13616, mod 97 = 1 | ISO 13616 |
| **NSS** | `control = (province + number) % 97` | Social Security |
| **CIF** | Sum even + odd positions with doubling, control = (10 - sum%10) % 10 | BOE |

### 2.2 Validator Structure

Each validator returns a tuple `(is_valid, confidence, reason)`:

| Field | Type | Description |
|-------|------|-------------|
| `is_valid` | bool | True if checksum is correct |
| `confidence` | float | 1.0 (valid), 0.5 (format ok, checksum bad), 0.0 (invalid format) |
| `reason` | str | Description of the result |

### 2.3 Reproducibility

```bash
# Environment
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Execution
python scripts/preprocess/checksum_validators.py

# Expected Output: 23/24 passed (95.8%)
```

---

## 3. Results

### 3.1 Summary by Validator

| Validator | Tests | Passed | Failed |
|-----------|-------|--------|--------|
| DNI | 6 | 6 | 0 |
| NIE | 4 | 4 | 0 |
| DNI_NIE | 2 | 2 | 0 |
| IBAN | 4 | 4 | 0 |
| NSS | 2 | 1 | 1* |
| CIF | 4 | 4 | 0 |
| Edge cases | 2 | 2 | 0 |
| **Total** | **24** | **23** | **1** |

*The failure is an error in the test expectation, not in the validator.

### 3.2 Detailed Tests

#### DNI (6/6 ✅)

| Test | Input | Expected | Result |
|------|-------|----------|--------|
| dni_valid_1 | `12345678Z` | ✅ valid | ✅ |
| dni_valid_2 | `00000000T` | ✅ valid | ✅ |
| dni_valid_spaces | `1234 5678 Z` | ✅ valid | ✅ |
| dni_invalid_letter | `12345678A` | ❌ invalid | ❌ (expected Z) |
| dni_invalid_letter_2 | `00000000A` | ❌ invalid | ❌ (expected T) |
| dni_invalid_format | `1234567Z` | ❌ invalid | ❌ (7 digits) |

#### NIE (4/4 ✅)

| Test | Input | Expected | Result |
|------|-------|----------|--------|
| nie_valid_x | `X0000000T` | ✅ valid | ✅ |
| nie_valid_y | `Y0000000Z` | ✅ valid | ✅ |
| nie_valid_z | `Z0000000M` | ✅ valid | ✅ |
| nie_invalid_letter | `X0000000A` | ❌ invalid | ❌ (expected T) |

#### IBAN (4/4 ✅)

| Test | Input | Expected | Result |
|------|-------|----------|--------|
| iban_valid_es | `ES9121000418450200051332` | ✅ valid | ✅ |
| iban_valid_spaces | `ES91 2100 0418 4502 0005 1332` | ✅ valid | ✅ |
| iban_invalid_check | `ES0021000418450200051332` | ❌ invalid | ❌ (check digits 00) |
| iban_invalid_mod97 | `ES1234567890123456789012` | ❌ invalid | ❌ (mod 97 ≠ 1) |

#### NSS (1/2 - 1 expectation failure)

| Test | Input | Expected | Result | Note |
|------|-------|----------|--------|------|
| nss_valid | `281234567890` | ❌ invalid | ❌ | Correct (random checksum) |
| nss_format_ok | `280000000097` | ✅ valid | ❌ | **Expectation error** |

**Failure Analysis:**
- Input: `280000000097`
- Province: `28`, Number: `00000000`, Control: `97`
- Calculation: `(28 * 10^8 + 0) % 97 = 2800000000 % 97 = 37`
- Expected by test: `97`, Actual: `37`
- **The validator is correct.** The test expectation was incorrect.

#### CIF (4/4 ✅)

| Test | Input | Expected | Result |
|------|-------|----------|--------|
| cif_valid_a | `A12345674` | ✅ valid | ✅ |
| cif_valid_b | `B12345674` | ✅ valid | ✅ |
| cif_invalid | `A12345670` | ❌ invalid | ❌ (expected 4) |

### 3.3 Validation Demo

```
DNI_NIE: '12345678Z'
  ✅ VALID (confidence: 1.0)
  Reason: Valid DNI checksum

DNI_NIE: '12345678A'
  ❌ INVALID (confidence: 0.5)
  Reason: Invalid checksum: expected 'Z', got 'A'

DNI_NIE: 'X0000000T'
  ✅ VALID (confidence: 1.0)
  Reason: Valid NIE checksum

IBAN: 'ES91 2100 0418 4502 0005 1332'
  ✅ VALID (confidence: 1.0)
  Reason: Valid IBAN checksum

CIF: 'A12345674'
  ✅ VALID (confidence: 1.0)
  Reason: Valid CIF checksum (digit)
```

---

## 4. Error Analysis

### 4.1 Only Failure: NSS Edge Case

| Aspect | Detail |
|--------|--------|
| Test | `nss_format_ok` |
| Input | `280000000097` |
| Issue | Test expectation assumed `97` would be valid |
| Reality | `(28 + "00000000") % 97 = 37`, not `97` |
| Action | Correct expectation in test case |

### 4.2 Proposed Correction

```python
# In TEST_CASES, change:
TestCase("nss_format_ok", "280000000097", "NSS", True, "..."),
# To:
TestCase("nss_format_ok", "280000000037", "NSS", True, "NSS with valid control"),
```

Or better, calculate a real valid NSS:
- Province: `28` (Madrid)
- Number: `12345678`
- Control: `(2812345678) % 97 = 2812345678 % 97 = 8`
- Valid NSS: `281234567808`

---

## 5. Conclusions and Future Work

### 5.1 Conclusions

1. **All 5 validators work correctly** according to official algorithms
2. **Return structure (is_valid, confidence, reason)** allows flexible integration
3. **Intermediate confidence level (0.5)** allows distinguishing:
   - Correct format but incorrect checksum → possible typo/OCR
   - Incorrect format → probably not that type of ID

### 5.2 Use in NER Pipeline

| Scenario | Action |
|----------|--------|
| Entity detected + valid checksum | Keep detection (confidence boost) |
| Entity detected + invalid checksum | Reduce confidence or mark as "possible_typo" |
| Entity detected + invalid format | Possible false positive → review |

### 5.3 Next Step

**Integration into NER pipeline for post-validation:**
- Apply validators to entities detected as DNI_NIE, IBAN, NSS, CIF
- Adjust confidence based on validation result
- Reduce SPU (false positives) removing detections with invalid checksums

### 5.4 Estimated Impact

| Metric | Baseline | Estimated | Improvement |
|--------|----------|-----------|-------------|
| SPU | 8 | 5-6 | -2 to -3 |
| F1 (strict) | 0.492 | 0.50-0.52 | +0.01-0.03 |

---

## 6. References

1. **DNI/NIE Algorithm:** BOE - Royal Decree 1553/2005
2. **IBAN Validation:** ISO 13616-1:2020
3. **NSS Format:** Social Security General Treasury
4. **CIF Algorithm:** BOE - Royal Decree 1065/2007
5. **Base research:** `docs/reports/2026-01-28_investigacion_hybrid_ner.md`

---

**Date:** 2026-02-04
