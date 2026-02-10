# Evaluación Adversarial - NER Legal Español

**Fecha:** 2026-01-20
**Modelo:** legal_ner_v1
**Tests:** 35

---

## Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Tests totales | 35 |
| Pasados | 16 (45.7%) |
| Fallados | 19 (54.3%) |

### Por Categoría

| Categoría | Pasados | Total | Tasa |
|-----------|---------|-------|------|
| adversarial | 4 | 8 | 50.0% |
| edge_case | 6 | 9 | 66.7% |
| ocr_corruption | 1 | 5 | 20.0% |
| real_world | 3 | 10 | 30.0% |
| unicode_evasion | 2 | 3 | 66.7% |

### Por Dificultad

| Dificultad | Pasados | Total | Tasa |
|------------|---------|-------|------|
| easy | 4 | 4 | 100.0% |
| medium | 6 | 12 | 50.0% |
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

**Detectado (2):**
- `12` → CADASTRAL_REF
- `345 678 Z` → NSS

**Resultado:** 0 correctos, 1 perdidos, 2 falsos positivos

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
- `ES91 21` → IBAN
- `00 0418 4502 0005 1332` → CADASTRAL_REF

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
- `+34 612 345 678 o 0034612345678` → PHONE

**Resultado:** 1 correctos, 1 perdidos, 0 falsos positivos

**Notas:** International phone formats

---

#### date_roman_numerals [PASS]

**Dificultad:** hard

**Texto:**
```
Otorgado el día XV de marzo del año MMXXIV.
```

**Esperado (1):**
- `XV de marzo del año MMXXIV` → DATE

**Detectado (1):**
- `día XV de marzo del año MMXXIV` → DATE

**Resultado:** 1 correctos, 0 perdidos, 0 falsos positivos

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

**Detectado (1):**
- `El primero de enero de dos mil veinticuatro` → DATE

**Resultado:** 1 correctos, 0 perdidos, 0 falsos positivos

**Notas:** Fully written out date

---

#### address_floor_door [FAIL]

**Dificultad:** medium

**Texto:**
```
Domicilio en Calle Mayor 15, 3º B, 28001 Madrid.
```

**Esperado (3):**
- `Calle Mayor 15, 3º B` → ADDRESS
- `28001` → POSTAL_CODE
- `Madrid` → LOCATION

**Detectado (1):**
- `Calle Mayor 15, 3º B, 28001 Madrid` → ADDRESS

**Resultado:** 1 correctos, 2 perdidos, 0 falsos positivos

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
- `12345678X` → LICENSE_PLATE

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

**Detectado (3):**
- `Ley 15/` → ECLI
- `2022` → LICENSE_PLATE
- `, de 12 de julio` → ECLI

**Resultado:** 0 correctos, 0 perdidos, 3 falsos positivos

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

**Detectado (0):**
- (ninguna entidad)

**Resultado:** 0 correctos, 0 perdidos, 0 falsos positivos

**Notas:** 8-digit number that is NOT a DNI (expediente)

---

#### mixed_languages [FAIL]

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
- `UK123456789` → NSS
- `Madrid` → LOCATION

**Resultado:** 2 correctos, 1 perdidos, 1 falsos positivos

**Notas:** English name and foreign passport

---

### OCR CORRUPTION

#### ocr_letter_substitution [FAIL]

**Dificultad:** medium

**Texto:**
```
DNl 12345678Z perteneciente a María García.
```

**Esperado (2):**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Detectado (4):**
- `DN` → CADASTRAL_REF
- `l 12345678` → NSS
- `Z` → CADASTRAL_REF
- `María García` → PERSON

**Resultado:** 1 correctos, 1 perdidos, 3 falsos positivos

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

**Detectado (1):**
- `IBAN ES91 21O0 0418 45O2 OOO5 1332` → CADASTRAL_REF

**Resultado:** 0 correctos, 1 perdidos, 1 falsos positivos

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

**Detectado (2):**
- `DonJoséGarcíaLópezcon` → PERSON
- `DNI12345678X` → CADASTRAL_REF

**Resultado:** 1 correctos, 1 perdidos, 1 falsos positivos

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

**Detectado (2):**
- `D N I  1 2 3 4 5 6 7 8 Z` → CADASTRAL_REF
- `M` → LOCATION

**Resultado:** 0 correctos, 2 perdidos, 2 falsos positivos

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
- `12345678Х` → DNI_NIE
- `María` → PERSON

**Resultado:** 2 correctos, 0 perdidos, 0 falsos positivos

**Notas:** Cyrillic Х (U+0425) instead of Latin X

---

#### zero_width_space [PASS]

**Dificultad:** hard

**Texto:**
```
DNI 123​456​78Z de María García.
```

**Esperado (2):**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Detectado (2):**
- `123​456​78Z` → DNI_NIE
- `María García` → PERSON

**Resultado:** 2 correctos, 0 perdidos, 0 falsos positivos

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

**Detectado (1):**
- `María` → LOCATION

**Resultado:** 0 correctos, 2 perdidos, 1 falsos positivos

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

**Detectado (4):**
- `NÚMERO MIL DOSCIENTOS TREINTA Y CUATRO.-` → DATE
- `Sevilla` → LOCATION
- `JOSÉ GARCÍA LÓPEZ` → PERSON
- `Ilustre Colegio de Sevilla` → ORGANIZATION

**Resultado:** 2 correctos, 2 perdidos, 2 falsos positivos

**Notas:** Standard notarial deed header

---

#### testament_comparecencia [FAIL]

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

**Detectado (10):**
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

**Resultado:** 5 correctos, 0 perdidos, 5 falsos positivos

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

**Detectado (8):**
- `ENCIA Nº 123` → PROFESSIONAL_ID
- `/2024.` → NSS
- `Madrid` → LOCATION
- `diez de enero de dos mil veinticuatro` → DATE
- `Sala Primera del Tribunal Supremo` → ORGANIZATION
- `D. ANTONIO PÉREZ MARTÍNEZ` → PERSON
- `Procur` → PERSON
- `D. CARLOS SÁNCHEZ GÓMEZ` → PERSON

**Resultado:** 4 correctos, 0 perdidos, 4 falsos positivos

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

**Detectado (9):**
- `IB` → NSS
- `AN` → NSS
- `ES12 0049 1234 5012 3456 7890` → NSS
- `CONSTRUCCIONES PÉREZ, S.A.,` → ORGANIZATION
- `A` → DNI_NIE
- `-` → DNI_NIE
- `98765` → NSS
- `4` → DNI_NIE
- `32` → NSS

**Resultado:** 2 correctos, 1 perdidos, 7 falsos positivos

**Notas:** Bank transfer clause

---

#### cadastral_reference [FAIL]

**Dificultad:** medium

**Texto:**
```
Finca registral número 12345 del Registro de la Propiedad de Málaga, con referencia catastral 1234567AB1234S0001AB.
```

**Esperado (2):**
- `Málaga` → LOCATION
- `1234567AB1234S0001AB` → CADASTRAL_REF

**Detectado (5):**
- `número 12345 del Registro de la` → PROFESSIONAL_ID
- `Propiedad` → ORGANIZATION
- `de` → PROFESSIONAL_ID
- `Málaga` → ORGANIZATION
- `1234567AB1234S0001AB` → CADASTRAL_REF

**Resultado:** 1 correctos, 1 perdidos, 4 falsos positivos

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

**Detectado (3):**
- `Abogado D. LUIS SÁNCHEZ` → PERSON
- `Procur` → PERSON
- `Colegio de Procuradores de Madrid` → ORGANIZATION

**Resultado:** 1 correctos, 3 perdidos, 2 falsos positivos

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

**Detectado (4):**
- `Tribunal Supremo` → ORGANIZATION
- `(ECLI:ES:TS:2023:1234),` → ECLI
- `E` → ECLI
- `CLI:ES:AN:2024:567` → ECLI

**Resultado:** 2 correctos, 0 perdidos, 2 falsos positivos

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
- `modelo Ibiza, matrícula 1234 ABC` → LICENSE_PLATE
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

**Detectado (3):**
- `Seguridad Social` → ORGANIZATION
- `281234567890` → NSS
- `Régimen General` → ORGANIZATION

**Resultado:** 1 correctos, 0 perdidos, 2 falsos positivos

**Notas:** Social security number in employment context

---


## Metodología

### Diseño de Tests

Se diseñaron 35 casos de prueba agrupados en 5 categorías según la taxonomía definida en las directrices del proyecto:

| Categoría | Tests | Objetivo |
|-----------|-------|----------|
| edge_case | 9 | Condiciones límite (nombres cortos, formatos inusuales) |
| adversarial | 8 | Casos diseñados para confundir (negaciones, ejemplos, ficción) |
| ocr_corruption | 5 | Simulación de errores de escaneo (l/I, 0/O, espacios) |
| unicode_evasion | 3 | Caracteres similares (cirílico, fullwidth, zero-width) |
| real_world | 10 | Patrones reales de documentos legales españoles |

### Criterios de Evaluación

- **PASS (fácil/medio):** Todas las entidades esperadas detectadas
- **PASS (difícil):** Todas las entidades detectadas Y cero falsos positivos
- **Matching:** Fuzzy match con tolerancia de ±2 caracteres y 80% similitud

### Reproducibilidad

```bash
cd ml
source .venv/bin/activate
python scripts/adversarial/evaluate_adversarial.py
```

---

## Análisis de Errores

### Error 1: Fragmentación de Entidades Compuestas

**Patrón:** Secuencias con puntuación interna se fragmentan incorrectamente.

**Ejemplo:**
```
Entrada: "con D.N.I. número 12345678-Z"
Esperado: 12345678-Z → DNI_NIE
Detectado: D → PROFESSIONAL_ID, .N → IBAN, . → PROFESSIONAL_ID, I → IBAN, . → PROFESSIONAL_ID, 12345678-Z → DNI_NIE
```

**Causa:** El modelo no vio patrones con puntuación variable en entrenamiento sintético.

**Solución propuesta:** Preproceso regex para normalizar `D.N.I.`, `N.I.F.`, `C.I.F.` → `DNI`, `NIF`, `CIF`.

---

### Error 2: Confusión de Tipos en Secuencias Numéricas

**Patrón:** Secuencias numéricas largas se clasifican como tipo incorrecto.

**Ejemplo:**
```
Entrada: "IBAN ES12 0049 1234 5012 3456 7890"
Esperado: ES12 0049 1234 5012 3456 7890 → IBAN
Detectado: ES12 0049 1234 5012 3456 7890 → NSS
```

**Causa:** Overlap de patrones numéricos entre IBAN (24 chars), NSS (12 dígitos), CADASTRAL_REF (20 chars).

**Solución propuesta:** Postproceso con validación de formato específico por tipo.

---

### Error 3: Falsos Positivos en Referencias Legales

**Patrón:** Números en contexto legal (leyes, expedientes, protocolos) detectados como PII.

**Ejemplo:**
```
Entrada: "Según la Ley 15/2022, de 12 de julio"
Esperado: (ninguna entidad)
Detectado: Ley 15/ → ECLI, 2022 → LICENSE_PLATE, de 12 de julio → ECLI
```

**Causa:** Patrones `\d+/\d{4}` y fechas aparecen en contexto legal, no como PII.

**Solución propuesta:** Postproceso para excluir patrones `Ley \d+/\d{4}`, `Real Decreto`, `expediente \d+`.

---

### Error 4: Vulnerabilidad a Errores OCR

**Patrón:** Confusiones típicas de OCR (l/I, 0/O, espacios) rompen detección.

**Ejemplo:**
```
Entrada: "DNl 12345678Z" (l minúscula en lugar de I)
Esperado: 12345678Z → DNI_NIE
Detectado: DN → CADASTRAL_REF, l 12345678 → NSS, Z → CADASTRAL_REF
```

**Causa:** El modelo entrenó solo con texto limpio, no con variantes OCR.

**Solución propuesta:** Preproceso con normalización OCR:
- `DNl` → `DNI`
- `0` ↔ `O` en contexto numérico
- Colapso de espacios en patrones conocidos

---

### Error 5: Ceguera Contextual

**Patrón:** El modelo no distingue menciones ilustrativas de datos reales.

**Ejemplo:**
```
Entrada: "El formato del DNI es 12345678X (ejemplo ilustrativo)"
Esperado: (ninguna entidad - es un ejemplo)
Detectado: 12345678X → LICENSE_PLATE
```

**Causa:** El modelo no tiene acceso a contexto semántico ("ejemplo", "formato", "ilustrativo").

**Solución propuesta:** Postproceso con detección de contexto:
- Excluir si aparece "ejemplo", "formato", "ilustrativo" en ventana de ±10 tokens
- Requiere análisis más sofisticado (parcialmente solucionable con regex)

---

### Error 6: Entidades Ficticias Detectadas

**Patrón:** Personajes literarios/ficticios detectados como personas reales.

**Ejemplo:**
```
Entrada: "Como dijo Don Quijote de la Mancha"
Esperado: (ninguna entidad - personaje ficticio)
Detectado: Don Quijote de la Mancha → PERSON
```

**Causa:** El modelo no tiene lista de personajes ficticios conocidos.

**Solución propuesta:** Postproceso con gazetteer de exclusión (personajes ficticios, históricos públicos).

---

## Clasificación de Soluciones

### Solucionable con Regex (Preproceso)

| Problema | Regex | Ejemplo |
|----------|-------|---------|
| Normalizar D.N.I. | `D\.?\s*N\.?\s*I\.?` → `DNI` | `D.N.I.` → `DNI` |
| Normalizar N.I.F. | `N\.?\s*I\.?\s*F\.?` → `NIF` | `N.I.F.` → `NIF` |
| Colapsar espacios en DNI | `(\d)\s+(\d)` → `\1\2` | `12 345 678` → `12345678` |
| Fullwidth → ASCII | `[\uFF10-\uFF19]` → `[0-9]` | `１２３` → `123` |
| Zero-width removal | `[\u200b\u200c\u200d]` → `` | invisible → removed |
| OCR l/I en DNI | `DN[lI1]` → `DNI` | `DNl` → `DNI` |
| OCR 0/O en IBAN | `[0O]` normalización contextual | `21O0` → `2100` |

### Solucionable con Regex (Postproceso)

| Problema | Regex/Validación | Acción |
|----------|------------------|--------|
| Ley X/YYYY | `Ley\s+\d+/\d{4}` | Excluir entidad si match |
| Expediente | `expediente\s+\d+` | Excluir entidad |
| NÚMERO protocolo | `NÚMERO\s+[A-Z\s]+\.-` | Excluir si detectado como DATE |
| DNI checksum | Validar letra mod-23 | Rechazar si inválido |
| IBAN checksum | Validar dígitos control | Rechazar si inválido |
| NSS checksum | Validar mod-97 | Rechazar si inválido |
| Matrícula formato | `\d{4}\s?[A-Z]{3}` | Rechazar si no match |
| Contexto ejemplo | `(ejemplo\|ilustrativo\|formato)` cerca | Excluir entidad |

### Requiere Modelo/NLP (No Regex)

| Problema | Solución Necesaria |
|----------|-------------------|
| Personajes ficticios | Gazetteer de exclusión + NER específico |
| Truncamiento OCR ("Procur") | Mejor tokenización o modelo robusto |
| Ambigüedad semántica profunda | Fine-tuning con ejemplos negativos |

---

## Conclusiones

### Fortalezas del Modelo

1. **Patrones limpios:** 100% precisión en tests fáciles con formato estándar
2. **Nombres compuestos:** Detecta correctamente nombres nobles largos ("José María de la Santísima Trinidad...")
3. **Negación simple:** Reconoce "NO tener DNI" y no detecta falsos positivos
4. **Discriminación ORG/PERSON:** Distingue "García y Asociados, S.L." como organización
5. **Ubicaciones con prefijo:** "San Fernando del Valle" correctamente como LOCATION
6. **Robustez Unicode parcial:** Resiste cirílico y zero-width spaces

### Debilidades Identificadas

1. **Overfitting a datos sintéticos:** 99.87% F1 en test → 45.7% en adversarial
2. **Fragilidad ante OCR:** 80% de fallos en categoría ocr_corruption
3. **Explosión de falsos positivos:** En textos complejos genera 5-10 detecciones espurias
4. **Confusión de tipos numéricos:** IBAN ↔ NSS ↔ CADASTRAL_REF
5. **Ceguera contextual:** No distingue ejemplos, referencias legales, ficción

### Métricas Clave

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| F1 sintético | 99.87% | ≥85% | ✅ Superado |
| F1 adversarial (estimado) | ~45% | ≥70% | ❌ No alcanzado |
| Tasa falsos positivos | Alta | Baja | ❌ Crítico |
| Robustez OCR | 20% | ≥80% | ❌ Crítico |

---

## Trabajo Futuro

### Prioridad ALTA (Implementar Inmediatamente)

1. **Pipeline Pre/Postproceso**
   - Crear `scripts/inference/text_normalizer.py` (preproceso)
   - Crear `scripts/inference/entity_validator.py` (postproceso)
   - Integrar en pipeline de inferencia

2. **Validación de Checksums**
   - DNI: letra = "TRWAGMYFPDXBNJZSQVHLCKE"[número % 23]
   - IBAN: dígitos control válidos
   - NSS: validación mod-97

3. **Gazetteers de Exclusión**
   - Personajes ficticios conocidos
   - Patrones legales (Ley, RD, expediente)

### Prioridad MEDIA (Siguiente Iteración)

4. **Aumentación de Datos**
   - Añadir ejemplos con errores OCR al dataset
   - Añadir ejemplos negativos (números que NO son PII)
   - Añadir contextos "ejemplo ilustrativo"

5. **Re-entrenamiento**
   - Con dataset aumentado
   - Evaluar CRF layer (+4-13% F1 según literatura)

### Prioridad BAJA (Futuro)

6. **Datos Reales Anotados**
   - Obtener documentos legales reales anonimizados
   - Anotación manual de gold standard

---

## Referencias

1. **Modelo base:** PlanTL-GOB-ES/roberta-base-bne-capitel-ner
2. **Metodología adversarial:** directrices del proyecto, sección 4 (Testing Adversarial)
3. **Validación DNI:** BOE - Algoritmo letra NIF
4. **Validación IBAN:** ISO 13616 - International Bank Account Number
5. **seqeval:** Framework de evaluación NER (entidad-level)

---

**Generado por:** `scripts/adversarial/evaluate_adversarial.py`
**Fecha:** 2026-01-20
**Versión:** 1.0
