# Adversarial Evaluation - Spanish Legal NER

**Date:** 2026-01-20
**Model:** legal_ner_v1
**Tests:** 35

---

## Executive Summary

| Metric | Value |
|---------|-------|
| Total tests | 35 |
| Passed | 16 (45.7%) |
| Failed | 19 (54.3%) |

### By Category

| Category | Passed | Total | Rate |
|-----------|---------|-------|------|
| adversarial | 4 | 8 | 50.0% |
| edge_case | 6 | 9 | 66.7% |
| ocr_corruption | 1 | 5 | 20.0% |
| real_world | 3 | 10 | 30.0% |
| unicode_evasion | 2 | 3 | 66.7% |

### By Difficulty

| Difficulty | Passed | Total | Rate |
|------------|---------|-------|------|
| easy | 4 | 4 | 100.0% |
| medium | 6 | 12 | 50.0% |
| hard | 6 | 19 | 31.6% |

---

## Detailed Results

### EDGE CASE

#### single_letter_name [PASS]

**Difficulty:** medium

**Text:**
```
El demandante J. García presentó recurso.
```

**Expected (1):**
- `J. García` → PERSON

**Detected (1):**
- `J. García` → PERSON

**Result:** 1 correct, 0 missed, 0 false positives

**Notes:** Initial + surname pattern

---

#### very_long_name [PASS]

**Difficulty:** hard

**Text:**
```
Compareció Don José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón.
```

**Expected (1):**
- `José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón` → PERSON

**Detected (1):**
- `Don José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón` → PERSON

**Result:** 1 correct, 0 missed, 0 false positives

**Notes:** Compound noble name with particles

---

#### dni_without_letter [PASS]

**Difficulty:** medium

**Text:**
```
DNI número 12345678 (pendiente de verificación).
```

**Expected (1):**
- `12345678` → DNI_NIE

**Detected (1):**
- `12345678` → DNI_NIE

**Result:** 1 correct, 0 missed, 0 false positives

**Notes:** DNI missing control letter

---

#### dni_with_spaces [FAIL]

**Difficulty:** hard

**Text:**
```
Su documento de identidad es 12 345 678 Z.
```

**Expected (1):**
- `12 345 678 Z` → DNI_NIE

**Detected (2):**
- `12` → CADASTRAL_REF
- `345 678 Z` → NSS

**Result:** 0 correct, 1 missed, 2 false positives

**Notes:** DNI with internal spaces

---

#### iban_with_spaces [PASS]

**Difficulty:** easy

**Text:**
```
Transferir a ES91 2100 0418 4502 0005 1332.
```

**Expected (1):**
- `ES91 2100 0418 4502 0005 1332` → IBAN

**Detected (2):**
- `ES91 21` → IBAN
- `00 0418 4502 0005 1332` → CADASTRAL_REF

**Result:** 1 correct, 0 missed, 1 false positives

**Notes:** Standard IBAN format with spaces

---

#### phone_international [FAIL]

**Difficulty:** medium

**Text:**
```
Contacto: +34 612 345 678 o 0034612345678.
```

**Expected (2):**
- `+34 612 345 678` → PHONE
- `0034612345678` → PHONE

**Detected (1):**
- `+34 612 345 678 o 0034612345678` → PHONE

**Result:** 1 correct, 1 missed, 0 false positives

**Notes:** International phone formats

---

#### date_roman_numerals [PASS]

**Difficulty:** hard

**Text:**
```
Otorgado el día XV de marzo del año MMXXIV.
```

**Expected (1):**
- `XV de marzo del año MMXXIV` → DATE

**Detected (1):**
- `día XV de marzo del año MMXXIV` → DATE

**Result:** 1 correct, 0 missed, 0 false positives

**Notes:** Date with Roman numerals (notarial style)

---

#### date_ordinal [PASS]

**Difficulty:** medium

**Text:**
```
El primero de enero de dos mil veinticuatro.
```

**Expected (1):**
- `primero de enero de dos mil veinticuatro` → DATE

**Detected (1):**
- `El primero de enero de dos mil veinticuatro` → DATE

**Result:** 1 correct, 0 missed, 0 false positives

**Notes:** Fully written out date

---

#### address_floor_door [FAIL]

**Difficulty:** medium

**Text:**
```
Domicilio en Calle Mayor 15, 3º B, 28001 Madrid.
```

**Expected (3):**
- `Calle Mayor 15, 3º B` → ADDRESS
- `28001` → POSTAL_CODE
- `Madrid` → LOCATION

**Detected (1):**
- `Calle Mayor 15, 3º B, 28001 Madrid` → ADDRESS

**Result:** 1 correct, 2 missed, 0 false positives

**Notes:** Address with floor and door

---

### ADVERSARIAL

#### negation_dni [PASS]

**Difficulty:** hard

**Text:**
```
El interesado manifiesta NO tener DNI ni NIE.
```

**Expected (0):**
- (no entity)

**Detected (0):**
- (no entity)

**Result:** 0 correct, 0 missed, 0 false positives

**Notes:** Should NOT detect PII - negation context

---

#### example_dni [FAIL]

**Difficulty:** hard

**Text:**
```
El formato del DNI es 12345678X (ejemplo ilustrativo).
```

**Expected (0):**
- (no entity)

**Detected (1):**
- `12345678X` → LICENSE_PLATE

**Result:** 0 correct, 0 missed, 1 false positives

**Notes:** Example/illustrative context should be ignored

---

#### fictional_person [FAIL]

**Difficulty:** hard

**Text:**
```
Como dijo Don Quijote de la Mancha en su célebre obra.
```

**Expected (0):**
- (no entity)

**Detected (1):**
- `Don Quijote de la Mancha` → PERSON

**Result:** 0 correct, 0 missed, 1 false positives

**Notes:** Fictional/literary character - not PII

---

#### organization_as_person [PASS]

**Difficulty:** medium

**Text:**
```
García y Asociados, S.L. interpone demanda.
```

**Expected (1):**
- `García y Asociados, S.L.` → ORGANIZATION

**Detected (1):**
- `García y Asociados, S.L.` → ORGANIZATION

**Result:** 1 correct, 0 missed, 0 false positives

**Notes:** Surname in company name - should be ORG not PERSON

---

#### location_as_person [PASS]

**Difficulty:** hard

**Text:**
```
El municipio de San Fernando del Valle de Catamarca.
```

**Expected (1):**
- `San Fernando del Valle de Catamarca` → LOCATION

**Detected (1):**
- `San Fernando del Valle de Catamarca` → LOCATION

**Result:** 1 correct, 0 missed, 0 false positives

**Notes:** Location with person-like prefix (San)

---

#### date_in_reference [FAIL]

**Difficulty:** hard

**Text:**
```
Según la Ley 15/2022, de 12 de julio, reguladora...
```

**Expected (0):**
- (no entity)

**Detected (3):**
- `Ley 15/` → ECLI
- `2022` → LICENSE_PLATE
- `, de 12 de julio` → ECLI

**Result:** 0 correct, 0 missed, 3 false positives

**Notes:** Date in legal reference - not standalone PII

---

#### numbers_not_dni [PASS]

**Difficulty:** medium

**Text:**
```
El expediente 12345678 consta de 9 folios.
```

**Expected (0):**
- (no entity)

**Detected (0):**
- (no entity)

**Result:** 0 correct, 0 missed, 0 false positives

**Notes:** 8-digit number that is NOT a DNI (expediente)

---

#### mixed_languages [FAIL]

**Difficulty:** hard

**Text:**
```
Mr. John Smith, con pasaporte UK123456789, residente en Madrid.
```

**Expected (3):**
- `John Smith` → PERSON
- `UK123456789` → DNI_NIE
- `Madrid` → LOCATION

**Detected (3):**
- `Mr. John Smith` → PERSON
- `UK123456789` → NSS
- `Madrid` → LOCATION

**Result:** 2 correct, 1 missed, 1 false positives

**Notes:** English name and foreign passport

---

### OCR CORRUPTION

#### ocr_letter_substitution [FAIL]

**Difficulty:** medium

**Text:**
```
DNl 12345678Z perteneciente a María García.
```

**Expected (2):**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Detected (4):**
- `DN` → CADASTRAL_REF
- `l 12345678` → NSS
- `Z` → CADASTRAL_REF
- `María García` → PERSON

**Result:** 1 correct, 1 missed, 3 false positives

**Notes:** OCR confused I with l

---

#### ocr_zero_o_confusion [FAIL]

**Difficulty:** hard

**Text:**
```
IBAN ES91 21O0 0418 45O2 OOO5 1332.
```

**Expected (1):**
- `ES91 21O0 0418 45O2 OOO5 1332` → IBAN

**Detected (1):**
- `IBAN ES91 21O0 0418 45O2 OOO5 1332` → CADASTRAL_REF

**Result:** 0 correct, 1 missed, 1 false positives

**Notes:** OCR confused 0 with O

---

#### ocr_missing_spaces [FAIL]

**Difficulty:** hard

**Text:**
```
DonJoséGarcíaLópezconDNI12345678X.
```

**Expected (2):**
- `JoséGarcíaLópez` → PERSON
- `12345678X` → DNI_NIE

**Detected (2):**
- `DonJoséGarcíaLópezcon` → PERSON
- `DNI12345678X` → CADASTRAL_REF

**Result:** 1 correct, 1 missed, 1 false positives

**Notes:** OCR lost all spaces

---

#### ocr_extra_spaces [FAIL]

**Difficulty:** hard

**Text:**
```
D N I  1 2 3 4 5 6 7 8 Z  de  M a r í a.
```

**Expected (2):**
- `1 2 3 4 5 6 7 8 Z` → DNI_NIE
- `M a r í a` → PERSON

**Detected (2):**
- `D N I  1 2 3 4 5 6 7 8 Z` → CADASTRAL_REF
- `M` → LOCATION

**Result:** 0 correct, 2 missed, 2 false positives

**Notes:** OCR added extra spaces

---

#### ocr_accent_loss [PASS]

**Difficulty:** easy

**Text:**
```
Jose Maria Garcia Lopez, vecino de Malaga.
```

**Expected (2):**
- `Jose Maria Garcia Lopez` → PERSON
- `Malaga` → LOCATION

**Detected (2):**
- `Jose Maria Garcia Lopez` → PERSON
- `Malaga` → LOCATION

**Result:** 2 correct, 0 missed, 0 false positives

**Notes:** OCR lost accents (common)

---

### UNICODE EVASION

#### cyrillic_o [PASS]

**Difficulty:** hard

**Text:**
```
DNI 12345678Х pertenece a María.
```

**Expected (2):**
- `12345678Х` → DNI_NIE
- `María` → PERSON

**Detected (2):**
- `12345678Х` → DNI_NIE
- `María` → PERSON

**Result:** 2 correct, 0 missed, 0 false positives

**Notes:** Cyrillic Х (U+0425) instead of Latin X

---

#### zero_width_space [PASS]

**Difficulty:** hard

**Text:**
```
DNI 123​456​78Z de María García.
```

**Expected (2):**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Detected (2):**
- `123​456​78Z` → DNI_NIE
- `María García` → PERSON

**Result:** 2 correct, 0 missed, 0 false positives

**Notes:** Zero-width spaces inserted (U+200B)

---

#### fullwidth_numbers [FAIL]

**Difficulty:** hard

**Text:**
```
DNI １２３４５６７８Z de María.
```

**Expected (2):**
- `１２３４５６７８Z` → DNI_NIE
- `María` → PERSON

**Detected (1):**
- `María` → LOCATION

**Result:** 0 correct, 2 missed, 1 false positives

**Notes:** Fullwidth digits (U+FF11-U+FF19)

---

### REAL WORLD

#### notarial_header [FAIL]

**Difficulty:** medium

**Text:**
```
NÚMERO MIL DOSCIENTOS TREINTA Y CUATRO.- En la ciudad de Sevilla, a quince de marzo de dos mil veinticuatro, ante mí, JOSÉ GARCÍA LÓPEZ, Notario del Ilustre Colegio de Sevilla.
```

**Expected (4):**
- `Sevilla` → LOCATION
- `quince de marzo de dos mil veinticuatro` → DATE
- `JOSÉ GARCÍA LÓPEZ` → PERSON
- `Sevilla` → LOCATION

**Detected (4):**
- `NÚMERO MIL DOSCIENTOS TREINTA Y CUATRO.-` → DATE
- `Sevilla` → LOCATION
- `JOSÉ GARCÍA LÓPEZ` → PERSON
- `Ilustre Colegio de Sevilla` → ORGANIZATION

**Result:** 2 correct, 2 missed, 2 false positives

**Notes:** Standard notarial deed header

---

#### testament_comparecencia [FAIL]

**Difficulty:** hard

**Text:**
```
COMPARECE: Doña MARÍA ANTONIA FERNÁNDEZ RUIZ, mayor de edad, viuda, natural de Córdoba, vecina de Madrid, con domicilio en Calle Alcalá número 123, piso 4º, puerta B, y con D.N.I. número 12345678-Z.
```

**Expected (5):**
- `MARÍA ANTONIA FERNÁNDEZ RUIZ` → PERSON
- `Córdoba` → LOCATION
- `Madrid` → LOCATION
- `Calle Alcalá número 123, piso 4º, puerta B` → ADDRESS
- `12345678-Z` → DNI_NIE

**Detected (10):**
- `Doña MARÍA ANTONIA FERNÁNDEZ RUIZ` → PERSON
- `Córdoba` → LOCATION
- `Madrid` → LOCATION
- `Calle Alcalá número 123, piso 4º, puerta B,` → ADDRESS
- `D` → PROFESSIONAL_ID
- `.N` → IBAN
- `.` → PROFESSIONAL_ID
- `I` → IBAN
- `.` → PROFESSIONAL_ID
- `12345678-Z` → DNI_NIE

**Result:** 5 correct, 0 missed, 5 false positives

**Notes:** Testament appearance clause

---

#### judicial_sentence_header [FAIL]

**Difficulty:** hard

**Text:**
```
SENTENCIA Nº 123/2024. En Madrid, a diez de enero de dos mil veinticuatro. Vistos por la Sala Primera del Tribunal Supremo los recursos interpuestos por D. ANTONIO PÉREZ MARTÍNEZ, representado por el Procurador D. CARLOS SÁNCHEZ GÓMEZ.
```

**Expected (4):**
- `Madrid` → LOCATION
- `diez de enero de dos mil veinticuatro` → DATE
- `ANTONIO PÉREZ MARTÍNEZ` → PERSON
- `CARLOS SÁNCHEZ GÓMEZ` → PERSON

**Detected (8):**
- `ENCIA Nº 123` → PROFESSIONAL_ID
- `/2024.` → NSS
- `Madrid` → LOCATION
- `diez de enero de dos mil veinticuatro` → DATE
- `Sala Primera del Tribunal Supremo` → ORGANIZATION
- `D. ANTONIO PÉREZ MARTÍNEZ` → PERSON
- `Procur` → PERSON
- `D. CARLOS SÁNCHEZ GÓMEZ` → PERSON

**Result:** 4 correct, 0 missed, 4 false positives

**Notes:** Supreme Court sentence header

---

#### contract_parties [FAIL]

**Difficulty:** hard

**Text:**
```
De una parte, INMOBILIARIA GARCÍA, S.L., con CIF B-12345678, domiciliada en Plaza Mayor 1, 28013 Madrid, representada por D. PEDRO GARCÍA LÓPEZ. De otra parte, Dña. ANA MARTÍNEZ RUIZ, con NIF 87654321-X.
```

**Expected (8):**
- `INMOBILIARIA GARCÍA, S.L.` → ORGANIZATION
- `B-12345678` → DNI_NIE
- `Plaza Mayor 1` → ADDRESS
- `28013` → POSTAL_CODE
- `Madrid` → LOCATION
- `PEDRO GARCÍA LÓPEZ` → PERSON
- `ANA MARTÍNEZ RUIZ` → PERSON
- `87654321-X` → DNI_NIE

**Detected (6):**
- `INMOBILIARIA GARCÍA, S.L.,` → ORGANIZATION
- `B-12345678` → DNI_NIE
- `Plaza Mayor 1, 28013 Madrid` → ADDRESS
- `D. PEDRO GARCÍA LÓPEZ` → PERSON
- `Dña. ANA MARTÍNEZ RUIZ` → PERSON
- `87654321-X` → DNI_NIE

**Result:** 6 correct, 2 missed, 0 false positives

**Notes:** Contract parties clause

---

#### bank_account_clause [FAIL]

**Difficulty:** medium

**Text:**
```
El pago se efectuará mediante transferencia a la cuenta IBAN ES12 0049 1234 5012 3456 7890 titularidad de CONSTRUCCIONES PÉREZ, S.A., con CIF A-98765432.
```

**Expected (3):**
- `ES12 0049 1234 5012 3456 7890` → IBAN
- `CONSTRUCCIONES PÉREZ, S.A.` → ORGANIZATION
- `A-98765432` → DNI_NIE

**Detected (9):**
- `IB` → NSS
- `AN` → NSS
- `ES12 0049 1234 5012 3456 7890` → NSS
- `CONSTRUCCIONES PÉREZ, S.A.,` → ORGANIZATION
- `A` → DNI_NIE
- `-` → DNI_NIE
- `98765` → NSS
- `4` → DNI_NIE
- `32` → NSS

**Result:** 2 correct, 1 missed, 7 false positives

**Notes:** Bank transfer clause

---

#### cadastral_reference [FAIL]

**Difficulty:** medium

**Text:**
```
Finca registral número 12345 del Registro de la Propiedad de Málaga, con referencia catastral 1234567AB1234S0001AB.
```

**Expected (2):**
- `Málaga` → LOCATION
- `1234567AB1234S0001AB` → CADASTRAL_REF

**Detected (5):**
- `número 12345 del Registro de la` → PROFESSIONAL_ID
- `Propiedad` → ORGANIZATION
- `de` → PROFESSIONAL_ID
- `Málaga` → ORGANIZATION
- `1234567AB1234S0001AB` → CADASTRAL_REF

**Result:** 1 correct, 1 missed, 4 false positives

**Notes:** Property registration with cadastral reference

---

#### professional_ids [FAIL]

**Difficulty:** hard

**Text:**
```
Interviene el Abogado D. LUIS SÁNCHEZ, colegiado nº 12345 del ICAM, y el Procurador D. MIGUEL TORRES, colegiado nº 67890 del Colegio de Procuradores de Madrid.
```

**Expected (4):**
- `LUIS SÁNCHEZ` → PERSON
- `12345` → PROFESSIONAL_ID
- `MIGUEL TORRES` → PERSON
- `67890` → PROFESSIONAL_ID

**Detected (3):**
- `Abogado D. LUIS SÁNCHEZ` → PERSON
- `Procur` → PERSON
- `Colegio de Procuradores de Madrid` → ORGANIZATION

**Result:** 1 correct, 3 missed, 2 false positives

**Notes:** Professional bar numbers

---

#### ecli_citation [PASS]

**Difficulty:** easy

**Text:**
```
Según doctrina del Tribunal Supremo (ECLI:ES:TS:2023:1234), confirmada en ECLI:ES:AN:2024:567.
```

**Expected (2):**
- `ECLI:ES:TS:2023:1234` → ECLI
- `ECLI:ES:AN:2024:567` → ECLI

**Detected (4):**
- `Tribunal Supremo` → ORGANIZATION
- `(ECLI:ES:TS:2023:1234),` → ECLI
- `E` → ECLI
- `CLI:ES:AN:2024:567` → ECLI

**Result:** 2 correct, 0 missed, 2 false positives

**Notes:** ECLI case citations

---

#### vehicle_clause [PASS]

**Difficulty:** medium

**Text:**
```
El vehículo marca SEAT, modelo Ibiza, matrícula 1234 ABC, propiedad de D. FRANCISCO LÓPEZ.
```

**Expected (2):**
- `1234 ABC` → LICENSE_PLATE
- `FRANCISCO LÓPEZ` → PERSON

**Detected (3):**
- `SEAT` → LICENSE_PLATE
- `modelo Ibiza, matrícula 1234 ABC` → LICENSE_PLATE
- `D. FRANCISCO LÓPEZ` → PERSON

**Result:** 2 correct, 0 missed, 1 false positives

**Notes:** Vehicle description clause

---

#### social_security [PASS]

**Difficulty:** easy

**Text:**
```
Trabajador afiliado a la Seguridad Social con número 281234567890, adscrito al Régimen General.
```

**Expected (1):**
- `281234567890` → NSS

**Detected (3):**
- `Seguridad Social` → ORGANIZATION
- `281234567890` → NSS
- `Régimen General` → ORGANIZATION

**Result:** 1 correct, 0 missed, 2 false positives

**Notes:** Social security number in employment context

---


## Methodology

### Test Design

35 test cases were designed grouped into 5 categories according to the taxonomy defined in the project guidelines:

| Category | Tests | Objective |
|-----------|-------|----------|
| edge_case | 9 | Boundary conditions (short names, unusual formats) |
| adversarial | 8 | Cases designed to confuse (negations, examples, fiction) |
| ocr_corruption | 5 | Scan error simulation (l/I, 0/O, spaces) |
| unicode_evasion | 3 | Similar characters (cyrillic, fullwidth, zero-width) |
| real_world | 10 | Real patterns from Spanish legal documents |

### Evaluation Criteria

- **PASS (easy/medium):** All expected entities detected
- **PASS (hard):** All entities detected AND zero false positives
- **Matching:** Fuzzy match with ±2 character tolerance and 80% similarity

### Reproducibility

```bash
cd ml
source .venv/bin/activate
python scripts/adversarial/evaluate_adversarial.py
```

---

## Error Analysis

### Error 1: Compound Entity Fragmentation

**Pattern:** Sequences with internal punctuation are incorrectly split.

**Example:**
```
Input: "con D.N.I. número 12345678-Z"
Expected: 12345678-Z → DNI_NIE
Detected: D → PROFESSIONAL_ID, .N → IBAN, . → PROFESSIONAL_ID, I → IBAN, . → PROFESSIONAL_ID, 12345678-Z → DNI_NIE
```

**Cause:** The model did not see patterns with variable punctuation in synthetic training.

**Proposed Solution:** Regex preprocessing to normalize `D.N.I.`, `N.I.F.`, `C.I.F.` → `DNI`, `NIF`, `CIF`.

---

### Error 2: Type Confusion in Numeric Sequences

**Pattern:** Long numeric sequences classified as incorrect type.

**Example:**
```
Input: "IBAN ES12 0049 1234 5012 3456 7890"
Expected: ES12 0049 1234 5012 3456 7890 → IBAN
Detected: ES12 0049 1234 5012 3456 7890 → NSS
```

**Cause:** Overlap of numeric patterns between IBAN (24 chars), NSS (12 digits), CADASTRAL_REF (20 chars).

**Proposed Solution:** Post-processing with type-specific format validation.

---

### Error 3: False Positives in Legal References

**Pattern:** Numbers in legal context (laws, files, protocols) detected as PII.

**Example:**
```
Input: "Según la Ley 15/2022, de 12 de julio"
Expected: (no entity)
Detected: Ley 15/ → ECLI, 2022 → LICENSE_PLATE, de 12 de julio → ECLI
```

**Cause:** Patterns `\d+/\d{4}` and dates appear in legal context, not as PII.

**Proposed Solution:** Post-processing to exclude patterns `Ley \d+/\d{4}`, `Real Decreto`, `expediente \d+`.

---

### Error 4: OCR Error Vulnerability

**Pattern:** Typical OCR confusions (l/I, 0/O, spaces) break detection.

**Example:**
```
Input: "DNl 12345678Z" (lowercase l instead of I)
Expected: 12345678Z → DNI_NIE
Detected: DN → CADASTRAL_REF, l 12345678 → NSS, Z → CADASTRAL_REF
```

**Cause:** Model trained only with clean text, not OCR variants.

**Proposed Solution:** Pre-processing with OCR normalization:
- `DNl` → `DNI`
- `0` ↔ `O` in numeric context
- Collapsing spaces in known patterns

---

### Error 5: Context Blindness

**Pattern:** Model does not distinguish illustrative mentions from real data.

**Example:**
```
Input: "El formato del DNI es 12345678X (ejemplo ilustrativo)"
Expected: (no entity - is an example)
Detected: 12345678X → LICENSE_PLATE
```

**Cause:** Model does not have access to semantic context ("example", "format", "illustrative").

**Proposed Solution:** Post-processing with context detection:
- Exclude if "ejemplo", "formato", "ilustrativo" appears in ±10 token window
- Requires more sophisticated analysis (partially solvable with regex)

---

### Error 6: Fictional Entities Detected

**Pattern:** Literary/fictional characters detected as real people.

**Example:**
```
Input: "Como dijo Don Quijote de la Mancha"
Expected: (no entity - fictional character)
Detected: Don Quijote de la Mancha → PERSON
```

**Cause:** Model does not have a list of known fictional characters.

**Proposed Solution:** Post-processing with exclusion gazetteer (fictional characters, public historical figures).

---

## Solution Classification

### Solvable with Regex (Preprocessing)

| Problem | Regex | Example |
|----------|-------|---------|
| Normalize D.N.I. | `D\.?\s*N\.?\s*I\.?` → `DNI` | `D.N.I.` → `DNI` |
| Normalize N.I.F. | `N\.?\s*I\.?\s*F\.?` → `NIF` | `N.I.F.` → `NIF` |
| Collapse spaces in DNI | `(\d)\s+(\d)` → `\1\2` | `12 345 678` → `12345678` |
| Fullwidth → ASCII | `[\uFF10-\uFF19]` → `[0-9]` | `１２３` → `123` |
| Zero-width removal | `[\u200b\u200c\u200d]` → `` | invisible → removed |
| OCR l/I in DNI | `DN[lI1]` → `DNI` | `DNl` → `DNI` |
| OCR 0/O in IBAN | `[0O]` contextual normalization | `21O0` → `2100` |

### Solvable with Regex (Post-processing)

| Problem | Regex/Validation | Action |
|----------|------------------|--------|
| Ley X/YYYY | `Ley\s+\d+/\d{4}` | Exclude entity if match |
| Expediente | `expediente\s+\d+` | Exclude entity |
| NÚMERO protocolo | `NÚMERO\s+[A-Z\s]+\.-` | Exclude if detected as DATE |
| DNI checksum | Validate mod-23 letter | Reject if invalid |
| IBAN checksum | Validate control digits | Reject if invalid |
| NSS checksum | Validate mod-97 | Reject if invalid |
| License plate format | `\d{4}\s?[A-Z]{3}` | Reject if no match |
| Example context | `(ejemplo\|ilustrativo\|formato)` nearby | Exclude entity |

### Requires Model/NLP (Not Regex)

| Problem | Necessary Solution |
|----------|-------------------|
| Fictional characters | Exclusion gazetteer + specific NER |
| OCR truncation ("Procur") | Better tokenization or robust model |
| Deep semantic ambiguity | Fine-tuning with negative examples |

---

## Conclusions

### Model Strengths

1. **Clean patterns:** 100% precision in easy tests with standard format
2. **Compound names:** Correctly detects long noble names ("José María de la Santísima Trinidad...")
3. **Simple negation:** Recognizes "NO tener DNI" and does not detect false positives
4. **ORG/PERSON discrimination:** Distinguishes "García y Asociados, S.L." as organization
5. **Locations with prefix:** "San Fernando del Valle" correctly as LOCATION
6. **Partial Unicode robustness:** Resists cyrillic and zero-width spaces

### Identified Weaknesses

1. **Overfitting to synthetic data:** 99.87% F1 on test → 45.7% on adversarial
2. **Fragility to OCR:** 80% failure rate in ocr_corruption category
3. **False positive explosion:** In complex texts generates 5-10 spurious detections
4. **Numeric type confusion:** IBAN ↔ NSS ↔ CADASTRAL_REF
5. **Context blindness:** Does not distinguish examples, legal references, fiction

### Key Metrics

| Metric | Value | Target | Status |
|---------|-------|----------|--------|
| Synthetic F1 | 99.87% | ≥85% | ✅ Passed |
| Adversarial F1 (estimated) | ~45% | ≥70% | ❌ Not reached |
| False positive rate | High | Low | ❌ Critical |
| OCR Robustness | 20% | ≥80% | ❌ Critical |

---

## Future Work

### HIGH Priority (Implement Immediately)

1. **Pre/Post-processing Pipeline**
   - Create `scripts/inference/text_normalizer.py` (preprocessing)
   - Create `scripts/inference/entity_validator.py` (post-processing)
   - Integrate into inference pipeline

2. **Checksum Validation**
   - DNI: letter = "TRWAGMYFPDXBNJZSQVHLCKE"[number % 23]
   - IBAN: valid control digits
   - NSS: mod-97 validation

3. **Exclusion Gazetteers**
   - Known fictional characters
   - Legal patterns (Ley, RD, expediente)

### MEDIUM Priority (Next Iteration)

4. **Data Augmentation**
   - Add examples with OCR errors to dataset
   - Add negative examples (numbers that are NOT PII)
   - Add "illustrative example" contexts

5. **Re-training**
   - With augmented dataset
   - Evaluate CRF layer (+4-13% F1 according to literature)

### LOW Priority (Future)

6. **Annotated Real Data**
   - Obtain anonymized real legal documents
   - Manual gold standard annotation

---

## References

1. **Base model:** PlanTL-GOB-ES/roberta-base-bne-capitel-ner
2. **Adversarial methodology:** project guidelines, section 4 (Adversarial Testing)
3. **DNI validation:** BOE - NIF letter algorithm
4. **IBAN validation:** ISO 13616 - International Bank Account Number
5. **seqeval:** NER evaluation framework (entity-level)

---

**Date:** 2026-01-20
**Version:** 1.0
