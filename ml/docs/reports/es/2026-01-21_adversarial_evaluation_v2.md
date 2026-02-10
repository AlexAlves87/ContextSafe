# Evaluación Adversarial - NER Legal Español

**Fecha:** 2026-01-21
**Modelo:** legal_ner_v2
**Tests:** 35

---

## Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Tests totales | 35 |
| Pasados | 19 (54.3%) |
| Fallados | 16 (45.7%) |

### Por Categoría

| Categoría | Pasados | Total | Tasa |
|-----------|---------|-------|------|
| adversarial | 5 | 8 | 62.5% |
| edge_case | 6 | 9 | 66.7% |
| ocr_corruption | 2 | 5 | 40.0% |
| real_world | 5 | 10 | 50.0% |
| unicode_evasion | 1 | 3 | 33.3% |

### Por Dificultad

| Dificultad | Pasados | Total | Tasa |
|------------|---------|-------|------|
| easy | 4 | 4 | 100.0% |
| medium | 9 | 12 | 75.0% |
| hard | 6 | 19 | 31.6% |

---

## Resultados Detallados

### EDGE CASE

#### single_letter_name [PASS]

**Dificultad:** medium

**Texto:**
```
El demandante J. García presentó recurso.
```

**Esperado (1):**
- `J. García` → PERSON

**Detectado (1):**
- `J. García` → PERSON

**Resultado:** 1 correctos, 0 perdidos, 0 falsos positivos

**Notas:** Initial + surname pattern

---

#### very_long_name [PASS]

**Dificultad:** hard

**Texto:**
```
Compareció Don José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón.
```

**Esperado (1):**
- `José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón` → PERSON

**Detectado (1):**
- `Don José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón` → PERSON

**Resultado:** 1 correctos, 0 perdidos, 0 falsos positivos

**Notas:** Compound noble name with particles

---

#### dni_without_letter [PASS]

**Dificultad:** medium

**Texto:**
```
DNI número 12345678 (pendiente de verificación).
```

**Esperado (1):**
- `12345678` → DNI_NIE

**Detectado (1):**
- `12345678` → DNI_NIE

**Resultado:** 1 correctos, 0 perdidos, 0 falsos positivos

**Notas:** DNI missing control letter

---

#### dni_with_spaces [FAIL]

**Dificultad:** hard

**Texto:**
```
Su documento de identidad es 12 345 678 Z.
```

**Esperado (1):**
- `12 345 678 Z` → DNI_NIE

**Detectado (3):**
- `12` → DNI_NIE
- `3` → NSS
- `45 678 Z` → DNI_NIE

**Resultado:** 1 correctos, 0 perdidos, 2 falsos positivos

**Notas:** DNI with internal spaces

---

#### iban_with_spaces [PASS]

**Dificultad:** easy

**Texto:**
```
Transferir a ES91 2100 0418 4502 0005 1332.
```

**Esperado (1):**
- `ES91 2100 0418 4502 0005 1332` → IBAN

**Detectado (2):**
- `ES91 2100 0418 4502 000` → IBAN
- `5 1332` → CADASTRAL_REF

**Resultado:** 1 correctos, 0 perdidos, 1 falsos positivos

**Notas:** Standard IBAN format with spaces

---

#### phone_international [FAIL]

**Dificultad:** medium

**Texto:**
```
Contacto: +34 612 345 678 o 0034612345678.
```

**Esperado (2):**
- `+34 612 345 678` → PHONE
- `0034612345678` → PHONE

**Detectado (1):**
- `+34 612 345 678` → PHONE

**Resultado:** 1 correctos, 1 perdidos, 0 falsos positivos

**Notas:** International phone formats

---

#### date_roman_numerals [FAIL]

**Dificultad:** hard

**Texto:**
```
Otorgado el día XV de marzo del año MMXXIV.
```

**Esperado (1):**
- `XV de marzo del año MMXXIV` → DATE

**Detectado (0):**
- (ninguna entidad)

**Resultado:** 0 correctos, 1 perdidos, 0 falsos positivos

**Notas:** Date with Roman numerals (notarial style)

---

#### date_ordinal [PASS]

**Dificultad:** medium

**Texto:**
```
El primero de enero de dos mil veinticuatro.
```

**Esperado (1):**
- `primero de enero de dos mil veinticuatro` → DATE

**Detectado (2):**
- `El` → DATE
- `primero de enero de dos mil veinticuatro` → DATE

**Resultado:** 1 correctos, 0 perdidos, 1 falsos positivos

**Notas:** Fully written out date

---

#### address_floor_door [PASS]

**Dificultad:** medium

**Texto:**
```
Domicilio en Calle Mayor 15, 3º B, 28001 Madrid.
```

**Esperado (3):**
- `Calle Mayor 15, 3º B` → ADDRESS
- `28001` → POSTAL_CODE
- `Madrid` → LOCATION

**Detectado (3):**
- `Calle Mayor 15, 3º B` → ADDRESS
- `28` → POSTAL_CODE
- `Madrid` → LOCATION

**Resultado:** 3 correctos, 0 perdidos, 0 falsos positivos

**Notas:** Address with floor and door

---

### ADVERSARIAL

#### negation_dni [PASS]

**Dificultad:** hard

**Texto:**
```
El interesado manifiesta NO tener DNI ni NIE.
```

**Esperado (0):**
- (ninguna entidad)

**Detectado (0):**
- (ninguna entidad)

**Resultado:** 0 correctos, 0 perdidos, 0 falsos positivos

**Notas:** Should NOT detect PII - negation context

---

#### example_dni [FAIL]

**Dificultad:** hard

**Texto:**
```
El formato del DNI es 12345678X (ejemplo ilustrativo).
```

**Esperado (0):**
- (ninguna entidad)

**Detectado (1):**
- `12345678X` → DNI_NIE

**Resultado:** 0 correctos, 0 perdidos, 1 falsos positivos

**Notas:** Example/illustrative context should be ignored

---

#### fictional_person [FAIL]

**Dificultad:** hard

**Texto:**
```
Como dijo Don Quijote de la Mancha en su célebre obra.
```

**Esperado (0):**
- (ninguna entidad)

**Detectado (1):**
- `Don Quijote de la Mancha` → PERSON

**Resultado:** 0 correctos, 0 perdidos, 1 falsos positivos

**Notas:** Fictional/literary character - not PII

---

#### organization_as_person [PASS]

**Dificultad:** medium

**Texto:**
```
García y Asociados, S.L. interpone demanda.
```

**Esperado (1):**
- `García y Asociados, S.L.` → ORGANIZATION

**Detectado (1):**
- `García y Asociados, S.L.` → ORGANIZATION

**Resultado:** 1 correctos, 0 perdidos, 0 falsos positivos

**Notas:** Surname in company name - should be ORG not PERSON

---

#### location_as_person [PASS]

**Dificultad:** hard

**Texto:**
```
El municipio de San Fernando del Valle de Catamarca.
```

**Esperado (1):**
- `San Fernando del Valle de Catamarca` → LOCATION

**Detectado (1):**
- `San Fernando del Valle de Catamarca` → LOCATION

**Resultado:** 1 correctos, 0 perdidos, 0 falsos positivos

**Notas:** Location with person-like prefix (San)

---

#### date_in_reference [FAIL]

**Dificultad:** hard

**Texto:**
```
Según la Ley 15/2022, de 12 de julio, reguladora...
```

**Esperado (0):**
- (ninguna entidad)

**Detectado (5):**
- `Ley` → ECLI
- `15` → PROFESSIONAL_ID
- `/` → ECLI
- `2022` → PROFESSIONAL_ID
- `,` → ECLI

**Resultado:** 0 correctos, 0 perdidos, 5 falsos positivos

**Notas:** Date in legal reference - not standalone PII

---

#### numbers_not_dni [PASS]

**Dificultad:** medium

**Texto:**
```
El expediente 12345678 consta de 9 folios.
```

**Esperado (0):**
- (ninguna entidad)

**Detectado (1):**
- `12345678` → PROFESSIONAL_ID

**Resultado:** 0 correctos, 0 perdidos, 1 falsos positivos

**Notas:** 8-digit number that is NOT a DNI (expediente)

---

#### mixed_languages [PASS]

**Dificultad:** hard

**Texto:**
```
Mr. John Smith, con pasaporte UK123456789, residente en Madrid.
```

**Esperado (3):**
- `John Smith` → PERSON
- `UK123456789` → DNI_NIE
- `Madrid` → LOCATION

**Detectado (3):**
- `Mr. John Smith` → PERSON
- `UK123456789` → DNI_NIE
- `Madrid` → LOCATION

**Resultado:** 3 correctos, 0 perdidos, 0 falsos positivos

**Notas:** English name and foreign passport

---

### OCR CORRUPTION

#### ocr_letter_substitution [PASS]

**Dificultad:** medium

**Texto:**
```
DNl 12345678Z perteneciente a María García.
```

**Esperado (2):**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Detectado (2):**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Resultado:** 2 correctos, 0 perdidos, 0 falsos positivos

**Notas:** OCR confused I with l

---

#### ocr_zero_o_confusion [FAIL]

**Dificultad:** hard

**Texto:**
```
IBAN ES91 21O0 0418 45O2 OOO5 1332.
```

**Esperado (1):**
- `ES91 21O0 0418 45O2 OOO5 1332` → IBAN

**Detectado (0):**
- (ninguna entidad)

**Resultado:** 0 correctos, 1 perdidos, 0 falsos positivos

**Notas:** OCR confused 0 with O

---

#### ocr_missing_spaces [FAIL]

**Dificultad:** hard

**Texto:**
```
DonJoséGarcíaLópezconDNI12345678X.
```

**Esperado (2):**
- `JoséGarcíaLópez` → PERSON
- `12345678X` → DNI_NIE

**Detectado (1):**
- `DonJoséGarcíaLópezcon` → PERSON

**Resultado:** 1 correctos, 1 perdidos, 0 falsos positivos

**Notas:** OCR lost all spaces

---

#### ocr_extra_spaces [FAIL]

**Dificultad:** hard

**Texto:**
```
D N I  1 2 3 4 5 6 7 8 Z  de  M a r í a.
```

**Esperado (2):**
- `1 2 3 4 5 6 7 8 Z` → DNI_NIE
- `M a r í a` → PERSON

**Detectado (0):**
- (ninguna entidad)

**Resultado:** 0 correctos, 2 perdidos, 0 falsos positivos

**Notas:** OCR added extra spaces

---

#### ocr_accent_loss [PASS]

**Dificultad:** easy

**Texto:**
```
Jose Maria Garcia Lopez, vecino de Malaga.
```

**Esperado (2):**
- `Jose Maria Garcia Lopez` → PERSON
- `Malaga` → LOCATION

**Detectado (2):**
- `Jose Maria Garcia Lopez` → PERSON
- `Malaga` → LOCATION

**Resultado:** 2 correctos, 0 perdidos, 0 falsos positivos

**Notas:** OCR lost accents (common)

---

### UNICODE EVASION

#### cyrillic_o [PASS]

**Dificultad:** hard

**Texto:**
```
DNI 12345678Х pertenece a María.
```

**Esperado (2):**
- `12345678Х` → DNI_NIE
- `María` → PERSON

**Detectado (2):**
- `12345678` → DNI_NIE
- `María` → PERSON

**Resultado:** 2 correctos, 0 perdidos, 0 falsos positivos

**Notas:** Cyrillic Х (U+0425) instead of Latin X

---

#### zero_width_space [FAIL]

**Dificultad:** hard

**Texto:**
```
DNI 123​456​78Z de María García.
```

**Esperado (2):**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Detectado (3):**
- `123​456​78Z` → DNI_NIE
- `de` → PERSON
- `María García` → PERSON

**Resultado:** 2 correctos, 0 perdidos, 1 falsos positivos

**Notas:** Zero-width spaces inserted (U+200B)

---

#### fullwidth_numbers [FAIL]

**Dificultad:** hard

**Texto:**
```
DNI １２３４５６７８Z de María.
```

**Esperado (2):**
- `１２３４５６７８Z` → DNI_NIE
- `María` → PERSON

**Detectado (0):**
- (ninguna entidad)

**Resultado:** 0 correctos, 2 perdidos, 0 falsos positivos

**Notas:** Fullwidth digits (U+FF11-U+FF19)

---

### REAL WORLD

#### notarial_header [FAIL]

**Dificultad:** medium

**Texto:**
```
NÚMERO MIL DOSCIENTOS TREINTA Y CUATRO.- En la ciudad de Sevilla, a quince de marzo de dos mil veinticuatro, ante mí, JOSÉ GARCÍA LÓPEZ, Notario del Ilustre Colegio de Sevilla.
```

**Esperado (4):**
- `Sevilla` → LOCATION
- `quince de marzo de dos mil veinticuatro` → DATE
- `JOSÉ GARCÍA LÓPEZ` → PERSON
- `Sevilla` → LOCATION

**Detectado (3):**
- `Sevilla` → LOCATION
- `JOSÉ GARCÍA LÓPEZ` → PERSON
- `Sevilla` → LOCATION

**Resultado:** 3 correctos, 1 perdidos, 0 falsos positivos

**Notas:** Standard notarial deed header

---

#### testament_comparecencia [PASS]

**Dificultad:** hard

**Texto:**
```
COMPARECE: Doña MARÍA ANTONIA FERNÁNDEZ RUIZ, mayor de edad, viuda, natural de Córdoba, vecina de Madrid, con domicilio en Calle Alcalá número 123, piso 4º, puerta B, y con D.N.I. número 12345678-Z.
```

**Esperado (5):**
- `MARÍA ANTONIA FERNÁNDEZ RUIZ` → PERSON
- `Córdoba` → LOCATION
- `Madrid` → LOCATION
- `Calle Alcalá número 123, piso 4º, puerta B` → ADDRESS
- `12345678-Z` → DNI_NIE

**Detectado (5):**
- `Doña MARÍA ANTONIA FERNÁNDEZ RUIZ` → PERSON
- `Córdoba` → LOCATION
- `Madrid` → LOCATION
- `Calle Alcalá número 123, piso 4º, puerta B,` → ADDRESS
- `12345678-Z` → DNI_NIE

**Resultado:** 5 correctos, 0 perdidos, 0 falsos positivos

**Notas:** Testament appearance clause

---

#### judicial_sentence_header [FAIL]

**Dificultad:** hard

**Texto:**
```
SENTENCIA Nº 123/2024. En Madrid, a diez de enero de dos mil veinticuatro. Vistos por la Sala Primera del Tribunal Supremo los recursos interpuestos por D. ANTONIO PÉREZ MARTÍNEZ, representado por el Procurador D. CARLOS SÁNCHEZ GÓMEZ.
```

**Esperado (4):**
- `Madrid` → LOCATION
- `diez de enero de dos mil veinticuatro` → DATE
- `ANTONIO PÉREZ MARTÍNEZ` → PERSON
- `CARLOS SÁNCHEZ GÓMEZ` → PERSON

**Detectado (5):**
- `Nº 123/2024` → PROFESSIONAL_ID
- `Madrid` → LOCATION
- `Sala Primera del Tribunal Supremo` → ORGANIZATION
- `D. ANTONIO PÉREZ MARTÍNEZ` → PERSON
- `D. CARLOS SÁNCHEZ GÓMEZ` → PERSON

**Resultado:** 3 correctos, 1 perdidos, 2 falsos positivos

**Notas:** Supreme Court sentence header

---

#### contract_parties [FAIL]

**Dificultad:** hard

**Texto:**
```
De una parte, INMOBILIARIA GARCÍA, S.L., con CIF B-12345678, domiciliada en Plaza Mayor 1, 28013 Madrid, representada por D. PEDRO GARCÍA LÓPEZ. De otra parte, Dña. ANA MARTÍNEZ RUIZ, con NIF 87654321-X.
```

**Esperado (8):**
- `INMOBILIARIA GARCÍA, S.L.` → ORGANIZATION
- `B-12345678` → DNI_NIE
- `Plaza Mayor 1` → ADDRESS
- `28013` → POSTAL_CODE
- `Madrid` → LOCATION
- `PEDRO GARCÍA LÓPEZ` → PERSON
- `ANA MARTÍNEZ RUIZ` → PERSON
- `87654321-X` → DNI_NIE

**Detectado (6):**
- `INMOBILIARIA GARCÍA, S.L.,` → ORGANIZATION
- `B-12345678` → DNI_NIE
- `Plaza Mayor 1, 28013 Madrid` → ADDRESS
- `D. PEDRO GARCÍA LÓPEZ` → PERSON
- `Dña. ANA MARTÍNEZ RUIZ` → PERSON
- `87654321-X` → DNI_NIE

**Resultado:** 6 correctos, 2 perdidos, 0 falsos positivos

**Notas:** Contract parties clause

---

#### bank_account_clause [FAIL]

**Dificultad:** medium

**Texto:**
```
El pago se efectuará mediante transferencia a la cuenta IBAN ES12 0049 1234 5012 3456 7890 titularidad de CONSTRUCCIONES PÉREZ, S.A., con CIF A-98765432.
```

**Esperado (3):**
- `ES12 0049 1234 5012 3456 7890` → IBAN
- `CONSTRUCCIONES PÉREZ, S.A.` → ORGANIZATION
- `A-98765432` → DNI_NIE

**Detectado (2):**
- `IBAN ES12 0049 1234 5012 3456 7890` → IBAN
- `CONSTRUCCIONES PÉREZ, S.A.,` → ORGANIZATION

**Resultado:** 2 correctos, 1 perdidos, 0 falsos positivos

**Notas:** Bank transfer clause

---

#### cadastral_reference [PASS]

**Dificultad:** medium

**Texto:**
```
Finca registral número 12345 del Registro de la Propiedad de Málaga, con referencia catastral 1234567AB1234S0001AB.
```

**Esperado (2):**
- `Málaga` → LOCATION
- `1234567AB1234S0001AB` → CADASTRAL_REF

**Detectado (2):**
- `Málaga` → LOCATION
- `1234567AB1234S0001AB` → CADASTRAL_REF

**Resultado:** 2 correctos, 0 perdidos, 0 falsos positivos

**Notas:** Property registration with cadastral reference

---

#### professional_ids [FAIL]

**Dificultad:** hard

**Texto:**
```
Interviene el Abogado D. LUIS SÁNCHEZ, colegiado nº 12345 del ICAM, y el Procurador D. MIGUEL TORRES, colegiado nº 67890 del Colegio de Procuradores de Madrid.
```

**Esperado (4):**
- `LUIS SÁNCHEZ` → PERSON
- `12345` → PROFESSIONAL_ID
- `MIGUEL TORRES` → PERSON
- `67890` → PROFESSIONAL_ID

**Detectado (2):**
- `Abogado D. LUIS SÁNCHEZ` → PERSON
- `Colegio de Procuradores de Madrid` → ORGANIZATION

**Resultado:** 1 correctos, 3 perdidos, 1 falsos positivos

**Notas:** Professional bar numbers

---

#### ecli_citation [PASS]

**Dificultad:** easy

**Texto:**
```
Según doctrina del Tribunal Supremo (ECLI:ES:TS:2023:1234), confirmada en ECLI:ES:AN:2024:567.
```

**Esperado (2):**
- `ECLI:ES:TS:2023:1234` → ECLI
- `ECLI:ES:AN:2024:567` → ECLI

**Detectado (3):**
- `Tribunal Supremo` → ORGANIZATION
- `(ECLI:ES:TS:2023:1234),` → ECLI
- `ECLI:ES:AN:2024:567` → ECLI

**Resultado:** 2 correctos, 0 perdidos, 1 falsos positivos

**Notas:** ECLI case citations

---

#### vehicle_clause [PASS]

**Dificultad:** medium

**Texto:**
```
El vehículo marca SEAT, modelo Ibiza, matrícula 1234 ABC, propiedad de D. FRANCISCO LÓPEZ.
```

**Esperado (2):**
- `1234 ABC` → LICENSE_PLATE
- `FRANCISCO LÓPEZ` → PERSON

**Detectado (3):**
- `SEAT` → LICENSE_PLATE
- `matrícula 1234 ABC` → LICENSE_PLATE
- `D. FRANCISCO LÓPEZ` → PERSON

**Resultado:** 2 correctos, 0 perdidos, 1 falsos positivos

**Notas:** Vehicle description clause

---

#### social_security [PASS]

**Dificultad:** easy

**Texto:**
```
Trabajador afiliado a la Seguridad Social con número 281234567890, adscrito al Régimen General.
```

**Esperado (1):**
- `281234567890` → NSS

**Detectado (2):**
- `28` → DNI_NIE
- `1234567890` → NSS

**Resultado:** 1 correctos, 0 perdidos, 1 falsos positivos

**Notas:** Social security number in employment context

---


## Conclusiones

### Fortalezas del Modelo

(Analizar tests pasados y patrones)

### Debilidades Identificadas

(Analizar tests fallados y patrones)

### Recomendaciones

1. (Basadas en los resultados)

---

**Generado automáticamente por:** `scripts/adversarial/evaluate_adversarial.py`
