# Adversarial Evaluation - Spanish Legal NER

**Date:** 2026-01-21
**Model:** legal_ner_v2
**Tests:** 35

---

## Executive Summary

| Metric | Value |
|---------|-------|
| Total Tests | 35 |
| Passed | 19 (54.3%) |
| Failed | 16 (45.7%) |

### By Category

| Category | Passed | Total | Rate |
|-----------|---------|-------|------|
| adversarial | 5 | 8 | 62.5% |
| edge_case | 6 | 9 | 66.7% |
| ocr_corruption | 2 | 5 | 40.0% |
| real_world | 5 | 10 | 50.0% |
| unicode_evasion | 1 | 3 | 33.3% |

### By Difficulty

| Difficulty | Passed | Total | Rate |
|------------|---------|-------|------|
| easy | 4 | 4 | 100.0% |
| medium | 9 | 12 | 75.0% |
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

**Detected (3):**
- `12` → DNI_NIE
- `3` → NSS
- `45 678 Z` → DNI_NIE

**Result:** 1 correct, 0 missed, 2 false positives

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
- `ES91 2100 0418 4502 000` → IBAN
- `5 1332` → CADASTRAL_REF

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
- `+34 612 345 678` → PHONE

**Result:** 1 correct, 1 missed, 0 false positives

**Notes:** International phone formats

---

#### date_roman_numerals [FAIL]

**Difficulty:** hard

**Text:**
```
Otorgado el día XV de marzo del año MMXXIV.
```

**Expected (1):**
- `XV de marzo del año MMXXIV` → DATE

**Detected (0):**
- (no entities)

**Result:** 0 correct, 1 missed, 0 false positives

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

**Detected (2):**
- `El` → DATE
- `primero de enero de dos mil veinticuatro` → DATE

**Result:** 1 correct, 0 missed, 1 false positives

**Notes:** Fully written out date

---

#### address_floor_door [PASS]

**Difficulty:** medium

**Text:**
```
Domicilio en Calle Mayor 15, 3º B, 28001 Madrid.
```

**Expected (3):**
- `Calle Mayor 15, 3º B` → ADDRESS
- `28001` → POSTAL_CODE
- `Madrid` → LOCATION

**Detected (3):**
- `Calle Mayor 15, 3º B` → ADDRESS
- `28` → POSTAL_CODE
- `Madrid` → LOCATION

**Result:** 3 correct, 0 missed, 0 false positives

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
- (no entities)

**Detected (0):**
- (no entities)

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
- (no entities)

**Detected (1):**
- `12345678X` → DNI_NIE

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
- (no entities)

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
- (no entities)

**Detected (5):**
- `Ley` → ECLI
- `15` → PROFESSIONAL_ID
- `/` → ECLI
- `2022` → PROFESSIONAL_ID
- `,` → ECLI

**Result:** 0 correct, 0 missed, 5 false positives

**Notes:** Date in legal reference - not standalone PII

---

#### numbers_not_dni [PASS]

**Difficulty:** medium

**Text:**
```
El expediente 12345678 consta de 9 folios.
```

**Expected (0):**
- (no entities)

**Detected (1):**
- `12345678` → PROFESSIONAL_ID

**Result:** 0 correct, 0 missed, 1 false positives

**Notes:** 8-digit number that is NOT a DNI (file number)

---

#### mixed_languages [PASS]

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
- `UK123456789` → DNI_NIE
- `Madrid` → LOCATION

**Result:** 3 correct, 0 missed, 0 false positives

**Notes:** English name and foreign passport

---

### OCR CORRUPTION

#### ocr_letter_substitution [PASS]

**Difficulty:** medium

**Text:**
```
DNl 12345678Z perteneciente a María García.
```

**Expected (2):**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Detected (2):**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Result:** 2 correct, 0 missed, 0 false positives

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

**Detected (0):**
- (no entities)

**Result:** 0 correct, 1 missed, 0 false positives

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

**Detected (1):**
- `DonJoséGarcíaLópezcon` → PERSON

**Result:** 1 correct, 1 missed, 0 false positives

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

**Detected (0):**
- (no entities)

**Result:** 0 correct, 2 missed, 0 false positives

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
- `12345678` → DNI_NIE
- `María` → PERSON

**Result:** 2 correct, 0 missed, 0 false positives

**Notes:** Cyrillic Х (U+0425) instead of Latin X

---

#### zero_width_space [FAIL]

**Difficulty:** hard

**Text:**
```
DNI 123​456​78Z de María García.
```

**Expected (2):**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Detected (3):**
- `123​456​78Z` → DNI_NIE
- `de` → PERSON
- `María García` → PERSON

**Result:** 2 correct, 0 missed, 1 false positives

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

**Detected (0):**
- (no entities)

**Result:** 0 correct, 2 missed, 0 false positives

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

**Detected (3):**
- `Sevilla` → LOCATION
- `JOSÉ GARCÍA LÓPEZ` → PERSON
- `Sevilla` → LOCATION

**Result:** 3 correct, 1 missed, 0 false positives

**Notes:** Standard notarial deed header

---

#### testament_comparecencia [PASS]

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

**Detected (5):**
- `Doña MARÍA ANTONIA FERNÁNDEZ RUIZ` → PERSON
- `Córdoba` → LOCATION
- `Madrid` → LOCATION
- `Calle Alcalá número 123, piso 4º, puerta B,` → ADDRESS
- `12345678-Z` → DNI_NIE

**Result:** 5 correct, 0 missed, 0 false positives

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

**Detected (5):**
- `Nº 123/2024` → PROFESSIONAL_ID
- `Madrid` → LOCATION
- `Sala Primera del Tribunal Supremo` → ORGANIZATION
- `D. ANTONIO PÉREZ MARTÍNEZ` → PERSON
- `D. CARLOS SÁNCHEZ GÓMEZ` → PERSON

**Result:** 3 correct, 1 missed, 2 false positives

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

**Detected (2):**
- `IBAN ES12 0049 1234 5012 3456 7890` → IBAN
- `CONSTRUCCIONES PÉREZ, S.A.,` → ORGANIZATION

**Result:** 2 correct, 1 missed, 0 false positives

**Notes:** Bank transfer clause

---

#### cadastral_reference [PASS]

**Difficulty:** medium

**Text:**
```
Finca registral número 12345 del Registro de la Propiedad de Málaga, con referencia catastral 1234567AB1234S0001AB.
```

**Expected (2):**
- `Málaga` → LOCATION
- `1234567AB1234S0001AB` → CADASTRAL_REF

**Detected (2):**
- `Málaga` → LOCATION
- `1234567AB1234S0001AB` → CADASTRAL_REF

**Result:** 2 correct, 0 missed, 0 false positives

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

**Detected (2):**
- `Abogado D. LUIS SÁNCHEZ` → PERSON
- `Colegio de Procuradores de Madrid` → ORGANIZATION

**Result:** 1 correct, 3 missed, 1 false positives

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

**Detected (3):**
- `Tribunal Supremo` → ORGANIZATION
- `(ECLI:ES:TS:2023:1234),` → ECLI
- `ECLI:ES:AN:2024:567` → ECLI

**Result:** 2 correct, 0 missed, 1 false positives

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
- `matrícula 1234 ABC` → LICENSE_PLATE
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

**Detected (2):**
- `28` → DNI_NIE
- `1234567890` → NSS

**Result:** 1 correct, 0 missed, 1 false positives

**Notes:** Social security number in employment context

---


## Conclusions

### Model Strengths

(Analyze passed tests and patterns)

### Identified Weaknesses

(Analyze failed tests and patterns)

### Recommendations

1. (Based on results)

---

