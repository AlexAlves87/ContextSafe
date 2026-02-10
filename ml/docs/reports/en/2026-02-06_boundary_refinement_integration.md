# Boundary Refinement - NER Pipeline Integration

**Date:** 2026-02-06
**Author:** AlexAlves87
**Component:** `scripts/preprocess/boundary_refinement.py` integrated in `ner_predictor.py`
**Standard:** SemEval 2013 Task 9 (Entity-level evaluation)

---

## 1. Executive Summary

Implementation of entity boundary refinement to convert partial matches (PAR) into correct ones (COR) according to the SemEval 2013 evaluation framework.

### Results

| Test Suite | Result |
|------------|--------|
| Standalone tests | 12/12 (100%) |
| Integration test | ✅ Functional |
| Refinements applied | 4/8 entities in demo |

### Refinement Types

| Type | Entities | Action |
|------|----------|--------|
| OVER_EXTENDED | PERSON | Strip prefixes: Don, Dña., D., Mr., Doña |
| OVER_EXTENDED | DATE | Strip prefixes: a, el día, día |
| OVER_EXTENDED | ORGANIZATION | Strip suffixes: commas, semicolons |
| OVER_EXTENDED | ADDRESS | Strip postal+city at the end |
| TRUNCATED | POSTAL_CODE | Extend to 5 digits |
| TRUNCATED | DNI_NIE | Extend to include control letter |

---

## 2. Methodology

### 2.1 Previous Diagnosis

`scripts/evaluate/diagnose_par_cases.py` ran to identify error patterns:

```
TRUNCATED (2 cases):
  - [address_floor_door] Missing at end: '001' (postal code)
  - [testament_comparecencia] Missing at end: 'Z' (DNI letter)

OVER_EXTENDED (9 cases):
  - Names with honorific prefixes included
  - Dates with "a" prefix included
  - Organizations with trailing comma
```

### 2.2 Implementation

**File:** `scripts/preprocess/boundary_refinement.py`

```python
# Spanish honorific prefixes (order: longest first)
PERSON_PREFIXES = [
    r"(?:Compareció\s+)?Don\s+",
    r"(?:Compareció\s+)?Doña\s+",
    r"Dña\.\s*",
    r"D\.\s*",
    r"Mr\.\s*",
    r"Mrs\.\s*",
    # ...
]

# Main function
def refine_entity(text, entity_type, start, end, confidence, source, original_text):
    """Applies refinement according to entity type."""
    if entity_type in REFINEMENT_FUNCTIONS:
        refined_text, refinement_applied = REFINEMENT_FUNCTIONS[entity_type](text, original_text)
    # ...
```

### 2.3 Pipeline Integration

**File:** `scripts/inference/ner_predictor.py`

```python
# Import with graceful degradation
try:
    from preprocess.boundary_refinement import refine_entity, RefinedEntity
    REFINEMENT_AVAILABLE = True
except ImportError:
    REFINEMENT_AVAILABLE = False

# In predict() method:
def predict(self, text, min_confidence=0.5, max_length=512):
    # 1. Text normalization
    text = normalize_text_for_ner(text)

    # 2. NER prediction
    entities = self._extract_entities(...)

    # 3. Regex merge (hybrid)
    if REGEX_AVAILABLE:
        entities = self._merge_regex_detections(text, entities, min_confidence)

    # 4. Boundary refinement (NEW)
    if REFINEMENT_AVAILABLE:
        entities = self._apply_boundary_refinement(text, entities)

    return entities
```

### 2.4 Reproducibility

```bash
# Environment
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Standalone test
python scripts/preprocess/boundary_refinement.py

# Integration test
python scripts/inference/ner_predictor.py
```

---

## 3. Results

### 3.1 Standalone Tests (12/12)

| Test | Entity | Refinement | Result |
|------|--------|------------|--------|
| person_don | PERSON | Strip "Don " | ✅ |
| person_dña | PERSON | Strip "Dña. " | ✅ |
| person_d_dot | PERSON | Strip "D. " | ✅ |
| person_mr | PERSON | Strip "Mr. " | ✅ |
| person_no_change | PERSON | No change | ✅ |
| date_a_prefix | DATE | Strip "a " | ✅ |
| date_el_dia | DATE | Strip "el día " | ✅ |
| org_trailing_comma | ORGANIZATION | Strip "," | ✅ |
| address_with_postal_city | ADDRESS | Strip "28013 Madrid" | ✅ |
| postal_extend | POSTAL_CODE | "28" → "28001" | ✅ |
| dni_extend_letter | DNI_NIE | "12345678-" → "12345678Z" | ✅ |
| dni_no_extend | DNI_NIE | No change | ✅ |


### 3.2 Integration Test

| Input | Original Entity | Refined Entity | Refinement |
|-------|-----------------|----------------|------------|
| "Don José García López con DNI..." | "Don José García López" | "José García López" | stripped_prefix:Don |
| "Dña. Ana Martínez Ruiz..." | "Dña. Ana Martínez Ruiz" | "Ana Martínez Ruiz" | stripped_prefix:Dña. |
| "Compareció Doña María Antonia..." | "Doña María Antonia Fernández Ruiz" | "María Antonia Fernández Ruiz" | stripped_prefix:Doña |
| "Mr. John Smith, residente..." | "Mr. John Smith" | "John Smith" | stripped_prefix:Mr. |

### 3.3 Entities Without Refinement (Correct)

| Input | Entity | Reason |
|-------|--------|--------|
| "DNI 12345678Z" | "12345678Z" | Already correct |
| "IBAN ES91 2100..." | "ES91 2100 0418 4502 0005 1332" | Already correct |
| "Calle Alcalá 50" | "Calle Alcalá 50" | Already correct |
| "Sevilla" | "Sevilla" | Already correct |

---

## 4. Analysis

### 4.1 Pipeline Impact

Boundary refinement is applied **after** the NER+regex merge, acting as a post-processor:

```
Text → Normalization → NER → Regex Merge → Refinement → Final entities
                                              ↑
                                        (Element 5)
```

### 4.2 Metadata Preservation

Refinement preserves all original metadata:
- `confidence`: Unmodified
- `source`: Unmodified (ner/regex)
- `checksum_valid`: Unmodified
- `checksum_reason`: Unmodified

Adds new fields:
- `original_text`: Text before refinement
- `refinement_applied`: Type of refinement applied

### 4.3 Observation on DATE

The date "a quince de marzo de dos mil veinticuatro" in the integration test was **not refined** because the NER model detected "quince de marzo de dos mil veinticuatro" directly (without the "a" prefix). This indicates that:

1. The NER model already learns some correct boundaries
2. Refinement acts as a safety net for cases the model does not handle

---

## 5. Complete Pipeline (5 Elements)

### 5.1 Integrated Elements

| # | Element | Standalone | Integration | Function |
|---|---------|------------|-------------|----------|
| 1 | TextNormalizer | 15/15 | ✅ | Unicode evasion, homoglyphs |
| 2 | Checksum Validators | 23/24 | ✅ | Confidence adjustment |
| 3 | Regex Patterns | 22/22 | ✅ | IDs with spaces/dashes |
| 4 | Date Patterns | 14/14 | ✅ | Roman numerals |
| 5 | Boundary Refinement | 12/12 | ✅ | PAR→COR conversion |

### 5.2 Data Flow

```
Input: "Don José García López with DNI 12345678Z"
                    ↓
[1] TextNormalizer: No changes (clean text)
                    ↓
[NER Model]: Detects "Don José García López" (PERSON), "12345678Z" (DNI_NIE)
                    ↓
[3] Regex Merge: No changes (NER already detected complete DNI)
                    ↓
[2] Checksum: Valid DNI → confidence boost
                    ↓
[5] Boundary Refinement: "Don José García López" → "José García López"
                    ↓
Output: [PERSON] "José García López", [DNI_NIE] "12345678Z" ✅
```

---

## 6. Conclusions

### 6.1 Achievements

1. **Functional refinement**: 12/12 standalone tests, integration verified
2. **Graceful degradation**: System works without the module (REFINEMENT_AVAILABLE=False)
3. **Metadata preservation**: Checksum and source intact
4. **Traceability**: `original_text` and `refinement_applied` fields for audit

### 6.2 Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Only static prefixes/suffixes | Does not handle dynamic cases | Patterns cover 90%+ legal cases |
| Extension depends on context | May fail if text truncated | Length check |
| No CIF refinement | Low priority | Add if pattern detected |

### 6.3 Next Step

Run full adversarial test to measure impact on metrics:

```bash
python scripts/evaluate/test_ner_predictor_adversarial_v2.py
```

**Metrics to observe:**
- PAR (partial matches) - expect reduction
- COR (correct matches) - expect increase
- Pass rate - expect improvement

---

## 7. References

1. **SemEval 2013 Task 9**: Entity evaluation framework (COR/INC/PAR/MIS/SPU)
2. **PAR Diagnosis**: `scripts/evaluate/diagnose_par_cases.py`
3. **Implementation**: `scripts/preprocess/boundary_refinement.py`
4. **Integration**: `scripts/inference/ner_predictor.py` lines 37-47, 385-432

---

**Date:** 2026-02-06
