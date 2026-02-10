# Gap Analysis: Current Tests vs Academic Standards

**Date:** 2026-01-29
**Author:** AlexAlves87
**Analyzed File:** `scripts/evaluate/test_ner_predictor_adversarial.py`

---

## 1. Summary of Gaps

| Aspect | Academic Standard | Current Implementation | Severity |
|--------|-------------------|------------------------|----------|
| Evaluation Mode | Strict (SemEval 2013) | Lenient (custom) | **CRITICAL** |
| 4 SemEval Modes | strict, exact, partial, type | Only 1 custom mode | HIGH |
| Metrics Library | seqeval or nervaluate | Custom implementation | HIGH |
| Detailed Metrics | COR/INC/PAR/MIS/SPU | Only TP/FP/FN | MEDIUM |
| Metrics per Type | F1 per PERSON, DNI, etc. | Only aggregated F1 | MEDIUM |
| NoiseBench Reference | EMNLP 2024 | "ICLR 2024" (error) | LOW |
| Mode Documentation | Explicit in report | Not documented | MEDIUM |

---

## 2. Detailed Analysis

### 2.1 CRITICAL: Matching Mode Is Not Strict

**Current Code (lines 458-493):**

```python
def entities_match(expected: dict, detected: dict, tolerance: int = 5) -> bool:
    # Type must match
    if expected["type"] != detected["type"]:
        return False

    # Containment (detected contains expected or vice versa)
    if exp_text in det_text or det_text in exp_text:
        return True

    # Length difference tolerance
    if abs(len(exp_text) - len(det_text)) <= tolerance:
        # Check character overlap
        common = sum(1 for c in exp_text if c in det_text)
        if common >= len(exp_text) * 0.8:
            return True
```

**Issues:**
1. Allows **containment** (If "José García" is in "Don José García López", it counts as match)
2. Allows **80% character overlap** (not exact boundary)
3. Allows **5 character tolerance** in length

**SemEval Strict Standard:**
> "Exact boundary surface string match AND entity type match"

**Impact:** Current results (F1=0.784, 54.3% pass) could be **INFLATED** because partial matches are accepted as correct.

### 2.2 HIGH: Does Not Use seqeval or nervaluate

**Standard:** Use libraries validated against conlleval.

**Current:** Custom metrics implementation.

**Risk:** Custom metrics may not be comparable with academic literature.

### 2.3 HIGH: Only One Evaluation Mode

**SemEval 2013 defines 4 modes:**

| Mode | Boundary | Type | Usage |
|------|----------|------|-------|
| **strict** | Exact | Exact | Main, rigorous |
| exact | Exact | Ignored | Boundary analysis |
| partial | Overlap | Ignored | Lenient analysis |
| type | Overlap | Exact | Classification analysis |

**Current:** Only one custom mode (similar to partial/lenient).

**Impact:** We cannot separate boundary errors vs type errors.

### 2.4 MEDIUM: No COR/INC/PAR/MIS/SPU Metrics

**SemEval 2013:**
- **COR**: Correct (exact boundary AND type)
- **INC**: Incorrect (exact boundary, incorrect type)
- **PAR**: Partial (boundary with overlap)
- **MIS**: Missing (FN)
- **SPU**: Spurious (FP)

**Current:** Only TP/FP/FN (does not distinguish INC from PAR).

### 2.5 MEDIUM: No Metrics per Entity Type

**Standard:** Report F1 for each type (PERSON, DNI_NIE, IBAN, etc.)

**Current:** Only aggregated F1.

**Impact:** We don't know which entity types perform worse.

### 2.6 LOW: Reference Error

**Line 10:** `NoiseBench (ICLR 2024)`

**Correct:** `NoiseBench (EMNLP 2024)`

---

## 3. Impact on Reported Results

### 3.1 Strict vs Lenient Difference Estimation

Based on literature, strict mode typically produces **5-15% lower F1** than lenient:

| Metric | Current (lenient) | Estimated (strict) |
|--------|-------------------|--------------------|
| F1 | 0.784 | 0.67-0.73 |
| Pass rate | 54.3% | 40-48% |

**Current results are optimistic.**

### 3.2 Tests Affected by Lenient Matching

Tests where lenient matching accepts as correct what strict would reject:

| Test | Situation | Impact |
|------|-----------|--------|
| `very_long_name` | Long name, exact boundary? | Possible |
| `address_floor_door` | Complex address | Possible |
| `testament_comparecencia` | Multiple entities | High |
| `judicial_sentence_header` | Textual dates | High |

---

## 4. Remediation Plan

### 4.1 Required Changes

1. **Implement strict mode** (CRITICAL priority)
   - Boundary must be exact (normalized)
   - Type must be exact

2. **Add nervaluate** (HIGH priority)
   ```bash
   pip install nervaluate
   ```

3. **Report 4 modes** (HIGH priority)
   - strict (main)
   - exact
   - partial
   - type

4. **Add per-type metrics** (MEDIUM priority)

5. **Fix NoiseBench reference** (LOW priority)

### 4.2 Migration Strategy

To maintain comparability with previous results:

1. Run with **both modes** (lenient AND strict)
2. Report **both** in documentation
3. Use **strict as main metric** going forward
4. Document difference for baseline

---

## 5. Proposed New Script

Create `test_ner_predictor_adversarial_v2.py` with:

1. Strict mode by default
2. Integration with nervaluate
3. COR/INC/PAR/MIS/SPU metrics
4. F1 per entity type
5. Legacy mode option for comparison

---

## 6. Conclusions

**Current results (F1=0.784, 54.3% pass) are not comparable with academic literature** because:

1. They use lenient matching, not strict
2. They do not use standard libraries (seqeval, nervaluate)
3. They do not report granular metrics (per type, COR/INC/PAR)

**Immediate Action:** Before proceeding with TextNormalizer integration, we must:

1. Create v2 script with academic standards
2. Re-establish baseline with strict mode
3. THEN evaluate improvement impact

---

**Date:** 2026-01-29
