# Valutazione Avversaria - NER Legale Spagnolo

**Data:** 2026-01-21
**Modello:** legal_ner_v2
**Test:** 35

---

## Riepilogo Esecutivo

| Metrica | Valore |
|-----|-----|
| Test Totali | 35 |
| Superati | 19 (54.3%) |
| Falliti | 16 (45.7%) |

### Per Categoria

| Categoria | Superati | Totale | Tasso |
|-----|-----|-----|-----|
| adversarial | 5 | 8 | 62.5% |
| edge_case | 6 | 9 | 66.7% |
| ocr_corruption | 2 | 5 | 40.0% |
| real_world | 5 | 10 | 50.0% |
| unicode_evasion | 1 | 3 | 33.3% |

### Per Difficoltà

| Difficoltà | Superati | Totale | Tasso |
|-----|-----|-----|-----|
| easy | 4 | 4 | 100.0% |
| medium | 9 | 12 | 75.0% |
| hard | 6 | 19 | 31.6% |

---

## Risultati Dettagliati

### CASI LIMITE (EDGE CASE)

#### single_letter_name [PASS]

**Difficoltà:** medium

**Testo:**
```
El demandante J. García presentó recurso.
```

**Atteso (1):**
- `J. García` → PERSON

**Rilevato (1):**
- `J. García` → PERSON

**Risultato:** 1 corretti, 0 persi, 0 falsi positivi

**Note:** Pattern iniziale + cognome

---

#### very_long_name [PASS]

**Difficoltà:** hard

**Testo:**
```
Compareció Don José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón.
```

**Atteso (1):**
- `José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón` → PERSON

**Rilevato (1):**
- `Don José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón` → PERSON

**Risultato:** 1 corretti, 0 persi, 0 falsi positivi

**Note:** Nome nobiliare composto con particelle

---

#### dni_without_letter [PASS]

**Difficoltà:** medium

**Testo:**
```
DNI número 12345678 (pendiente de verificación).
```

**Atteso (1):**
- `12345678` → DNI_NIE

**Rilevato (1):**
- `12345678` → DNI_NIE

**Risultato:** 1 corretti, 0 persi, 0 falsi positivi

**Note:** DNI senza lettera di controllo

---

#### dni_with_spaces [FAIL]

**Difficoltà:** hard

**Testo:**
```
Su documento de identidad es 12 345 678 Z.
```

**Atteso (1):**
- `12 345 678 Z` → DNI_NIE

**Rilevato (3):**
- `12` → DNI_NIE
- `3` → NSS
- `45 678 Z` → DNI_NIE

**Risultato:** 1 corretti, 0 persi, 2 falsi positivi

**Note:** DNI con spazi interni

---

#### iban_with_spaces [PASS]

**Difficoltà:** easy

**Testo:**
```
Transferir a ES91 2100 0418 4502 0005 1332.
```

**Atteso (1):**
- `ES91 2100 0418 4502 0005 1332` → IBAN

**Rilevato (2):**
- `ES91 2100 0418 4502 000` → IBAN
- `5 1332` → CADASTRAL_REF

**Risultato:** 1 corretti, 0 persi, 1 falsi positivi

**Note:** Formato IBAN standard con spazi

---

#### phone_international [FAIL]

**Difficoltà:** medium

**Testo:**
```
Contacto: +34 612 345 678 o 0034612345678.
```

**Atteso (2):**
- `+34 612 345 678` → PHONE
- `0034612345678` → PHONE

**Rilevato (1):**
- `+34 612 345 678` → PHONE

**Risultato:** 1 corretti, 1 persi, 0 falsi positivi

**Note:** Formati telefonici internazionali

---

#### date_roman_numerals [FAIL]

**Difficoltà:** hard

**Testo:**
```
Otorgado el día XV de marzo del año MMXXIV.
```

**Atteso (1):**
- `XV de marzo del año MMXXIV` → DATE

**Rilevato (0):**
- (nessuna entità)

**Risultato:** 0 corretti, 1 persi, 0 falsi positivi

**Note:** Data con numeri romani (stile notarile)

---

#### date_ordinal [PASS]

**Difficoltà:** medium

**Testo:**
```
El primero de enero de dos mil veinticuatro.
```

**Atteso (1):**
- `primero de enero de dos mil veinticuatro` → DATE

**Rilevato (2):**
- `El` → DATE
- `primero de enero de dos mil veinticuatro` → DATE

**Risultato:** 1 corretti, 0 persi, 1 falsi positivi

**Note:** Data scritta completamente in lettere

---

#### address_floor_door [PASS]

**Difficoltà:** medium

**Testo:**
```
Domicilio en Calle Mayor 15, 3º B, 28001 Madrid.
```

**Atteso (3):**
- `Calle Mayor 15, 3º B` → ADDRESS
- `28001` → POSTAL_CODE
- `Madrid` → LOCATION

**Rilevato (3):**
- `Calle Mayor 15, 3º B` → ADDRESS
- `28` → POSTAL_CODE
- `Madrid` → LOCATION

**Risultato:** 3 corretti, 0 persi, 0 falsi positivi

**Note:** Indirizzo con piano e porta

---

### ADVERSARIAL

#### negation_dni [PASS]

**Difficoltà:** hard

**Testo:**
```
El interesado manifiesta NO tener DNI ni NIE.
```

**Atteso (0):**
- (nessuna entità)

**Rilevato (0):**
- (nessuna entità)

**Risultato:** 0 corretti, 0 persi, 0 falsi positivi

**Note:** NON dovrebbe rilevare PII - contesto di negazione

---

#### example_dni [FAIL]

**Difficoltà:** hard

**Testo:**
```
El formato del DNI es 12345678X (ejemplo ilustrativo).
```

**Atteso (0):**
- (nessuna entità)

**Rilevato (1):**
- `12345678X` → DNI_NIE

**Risultato:** 0 corretti, 0 persi, 1 falsi positivi

**Note:** Esempio/contesto illustrativo dovrebbe essere ignorato

---

#### fictional_person [FAIL]

**Difficoltà:** hard

**Testo:**
```
Como dijo Don Quijote de la Mancha en su célebre obra.
```

**Atteso (0):**
- (nessuna entità)

**Rilevato (1):**
- `Don Quijote de la Mancha` → PERSON

**Risultato:** 0 corretti, 0 persi, 1 falsi positivi

**Note:** Personaggio fittizio/letterario - non PII

---

#### organization_as_person [PASS]

**Difficoltà:** medium

**Testo:**
```
García y Asociados, S.L. interpone demanda.
```

**Atteso (1):**
- `García y Asociados, S.L.` → ORGANIZATION

**Rilevato (1):**
- `García y Asociados, S.L.` → ORGANIZATION

**Risultato:** 1 corretti, 0 persi, 0 falsi positivi

**Note:** Cognome nel nome dell'azienda - dovrebbe essere ORG non PERSON

---

#### location_as_person [PASS]

**Difficoltà:** hard

**Testo:**
```
El municipio de San Fernando del Valle de Catamarca.
```

**Atteso (1):**
- `San Fernando del Valle de Catamarca` → LOCATION

**Rilevato (1):**
- `San Fernando del Valle de Catamarca` → LOCATION

**Risultato:** 1 corretti, 0 persi, 0 falsi positivi

**Note:** Luogo con prefisso simile a persona (San)

---

#### date_in_reference [FAIL]

**Difficoltà:** hard

**Testo:**
```
Según la Ley 15/2022, de 12 de julio, reguladora...
```

**Atteso (0):**
- (nessuna entità)

**Rilevato (5):**
- `Ley` → ECLI
- `15` → PROFESSIONAL_ID
- `/` → ECLI
- `2022` → PROFESSIONAL_ID
- `,` → ECLI

**Risultato:** 0 corretti, 0 persi, 5 falsi positivi

**Note:** Data in riferimento legale - non PII autonoma

---

#### numbers_not_dni [PASS]

**Difficoltà:** medium

**Testo:**
```
El expediente 12345678 consta de 9 folios.
```

**Atteso (0):**
- (nessuna entità)

**Rilevato (1):**
- `12345678` → PROFESSIONAL_ID

**Risultato:** 0 corretti, 0 persi, 1 falsi positivi

**Note:** Numero a 8 cifre che NON è un DNI (fascicolo)

---

#### mixed_languages [PASS]

**Difficoltà:** hard

**Testo:**
```
Mr. John Smith, con pasaporte UK123456789, residente en Madrid.
```

**Atteso (3):**
- `John Smith` → PERSON
- `UK123456789` → DNI_NIE
- `Madrid` → LOCATION

**Rilevato (3):**
- `Mr. John Smith` → PERSON
- `UK123456789` → DNI_NIE
- `Madrid` → LOCATION

**Risultato:** 3 corretti, 0 persi, 0 falsi positivi

**Note:** Nome inglese e passaporto straniero

---

### CORRUZIONE OCR

#### ocr_letter_substitution [PASS]

**Difficoltà:** medium

**Testo:**
```
DNl 12345678Z perteneciente a María García.
```

**Atteso (2):**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Rilevato (2):**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Risultato:** 2 corretti, 0 persi, 0 falsi positivi

**Note:** OCR ha confuso I con l

---

#### ocr_zero_o_confusion [FAIL]

**Difficoltà:** hard

**Testo:**
```
IBAN ES91 21O0 0418 45O2 OOO5 1332.
```

**Atteso (1):**
- `ES91 21O0 0418 45O2 OOO5 1332` → IBAN

**Rilevato (0):**
- (nessuna entità)

**Risultato:** 0 corretti, 1 persi, 0 falsi positivi

**Note:** OCR ha confuso 0 con O

---

#### ocr_missing_spaces [FAIL]

**Difficoltà:** hard

**Testo:**
```
DonJoséGarcíaLópezconDNI12345678X.
```

**Atteso (2):**
- `JoséGarcíaLópez` → PERSON
- `12345678X` → DNI_NIE

**Rilevato (1):**
- `DonJoséGarcíaLópezcon` → PERSON

**Risultato:** 1 corretti, 1 persi, 0 falsi positivi

**Note:** OCR ha perso tutti gli spazi

---

#### ocr_extra_spaces [FAIL]

**Difficoltà:** hard

**Testo:**
```
D N I  1 2 3 4 5 6 7 8 Z  de  M a r í a.
```

**Atteso (2):**
- `1 2 3 4 5 6 7 8 Z` → DNI_NIE
- `M a r í a` → PERSON

**Rilevato (0):**
- (nessuna entità)

**Risultato:** 0 corretti, 2 persi, 0 falsi positivi

**Note:** OCR ha aggiunto spazi extra

---

#### ocr_accent_loss [PASS]

**Difficoltà:** easy

**Testo:**
```
Jose Maria Garcia Lopez, vecino de Malaga.
```

**Atteso (2):**
- `Jose Maria Garcia Lopez` → PERSON
- `Malaga` → LOCATION

**Rilevato (2):**
- `Jose Maria Garcia Lopez` → PERSON
- `Malaga` → LOCATION

**Risultato:** 2 corretti, 0 persi, 0 falsi positivi

**Note:** OCR ha perso gli accenti (comune)

---

### EVASIONE UNICODE

#### cyrillic_o [PASS]

**Difficoltà:** hard

**Testo:**
```
DNI 12345678Х pertenece a María.
```

**Atteso (2):**
- `12345678Х` → DNI_NIE
- `María` → PERSON

**Rilevato (2):**
- `12345678` → DNI_NIE
- `María` → PERSON

**Risultato:** 2 corretti, 0 persi, 0 falsi positivi

**Note:** Х cirillico (U+0425) invece di X latino

---

#### zero_width_space [FAIL]

**Difficoltà:** hard

**Testo:**
```
DNI 123​456​78Z de María García.
```

**Atteso (2):**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Rilevato (3):**
- `123​456​78Z` → DNI_NIE
- `de` → PERSON
- `María García` → PERSON

**Risultato:** 2 corretti, 0 persi, 1 falsi positivi

**Note:** Spazi a larghezza zero inseriti (U+200B)

---

#### fullwidth_numbers [FAIL]

**Difficoltà:** hard

**Testo:**
```
DNI １２３４５６７８Z de María.
```

**Atteso (2):**
- `１２３４５６７８Z` → DNI_NIE
- `María` → PERSON

**Rilevato (0):**
- (nessuna entità)

**Risultato:** 0 corretti, 2 persi, 0 falsi positivi

**Note:** Cifre a larghezza intera (U+FF11-U+FF19)

---

### MONDO REALE (REAL WORLD)

#### notarial_header [FAIL]

**Difficoltà:** medium

**Testo:**
```
NÚMERO MIL DOSCIENTOS TREINTA Y CUATRO.- En la ciudad de Sevilla, a quince de marzo de dos mil veinticuatro, ante mí, JOSÉ GARCÍA LÓPEZ, Notario del Ilustre Colegio de Sevilla.
```

**Atteso (4):**
- `Sevilla` → LOCATION
- `quince de marzo de dos mil veinticuatro` → DATE
- `JOSÉ GARCÍA LÓPEZ` → PERSON
- `Sevilla` → LOCATION

**Rilevato (3):**
- `Sevilla` → LOCATION
- `JOSÉ GARCÍA LÓPEZ` → PERSON
- `Sevilla` → LOCATION

**Risultato:** 3 corretti, 1 persi, 0 falsi positivi

**Note:** Intestazione standard atto notarile

---

#### testament_comparecencia [PASS]

**Difficoltà:** hard

**Testo:**
```
COMPARECE: Doña MARÍA ANTONIA FERNÁNDEZ RUIZ, mayor de edad, viuda, natural de Córdoba, vecina de Madrid, con domicilio en Calle Alcalá número 123, piso 4º, puerta B, y con D.N.I. número 12345678-Z.
```

**Atteso (5):**
- `MARÍA ANTONIA FERNÁNDEZ RUIZ` → PERSON
- `Córdoba` → LOCATION
- `Madrid` → LOCATION
- `Calle Alcalá número 123, piso 4º, puerta B` → ADDRESS
- `12345678-Z` → DNI_NIE

**Rilevato (5):**
- `Doña MARÍA ANTONIA FERNÁNDEZ RUIZ` → PERSON
- `Córdoba` → LOCATION
- `Madrid` → LOCATION
- `Calle Alcalá número 123, piso 4º, puerta B,` → ADDRESS
- `12345678-Z` → DNI_NIE

**Risultato:** 5 corretti, 0 persi, 0 falsi positivi

**Note:** Clausola di comparizione testamentaria

---

#### judicial_sentence_header [FAIL]

**Difficoltà:** hard

**Testo:**
```
SENTENCIA Nº 123/2024. En Madrid, a diez de enero de dos mil veinticuatro. Vistos por la Sala Primera del Tribunal Supremo los recursos interpuestos por D. ANTONIO PÉREZ MARTÍNEZ, representado por el Procurador D. CARLOS SÁNCHEZ GÓMEZ.
```

**Atteso (4):**
- `Madrid` → LOCATION
- `diez de enero de dos mil veinticuatro` → DATE
- `ANTONIO PÉREZ MARTÍNEZ` → PERSON
- `CARLOS SÁNCHEZ GÓMEZ` → PERSON

**Rilevato (5):**
- `Nº 123/2024` → PROFESSIONAL_ID
- `Madrid` → LOCATION
- `Sala Primera del Tribunal Supremo` → ORGANIZATION
- `D. ANTONIO PÉREZ MARTÍNEZ` → PERSON
- `D. CARLOS SÁNCHEZ GÓMEZ` → PERSON

**Risultato:** 3 corretti, 1 persi, 2 falsi positivi

**Note:** Intestazione sentenza Corte Suprema

---

#### contract_parties [FAIL]

**Difficoltà:** hard

**Testo:**
```
De una parte, INMOBILIARIA GARCÍA, S.L., con CIF B-12345678, domiciliada en Plaza Mayor 1, 28013 Madrid, representada por D. PEDRO GARCÍA LÓPEZ. De otra parte, Dña. ANA MARTÍNEZ RUIZ, con NIF 87654321-X.
```

**Atteso (8):**
- `INMOBILIARIA GARCÍA, S.L.` → ORGANIZATION
- `B-12345678` → DNI_NIE
- `Plaza Mayor 1` → ADDRESS
- `28013` → POSTAL_CODE
- `Madrid` → LOCATION
- `PEDRO GARCÍA LÓPEZ` → PERSON
- `ANA MARTÍNEZ RUIZ` → PERSON
- `87654321-X` → DNI_NIE

**Rilevato (6):**
- `INMOBILIARIA GARCÍA, S.L.,` → ORGANIZATION
- `B-12345678` → DNI_NIE
- `Plaza Mayor 1, 28013 Madrid` → ADDRESS
- `D. PEDRO GARCÍA LÓPEZ` → PERSON
- `Dña. ANA MARTÍNEZ RUIZ` → PERSON
- `87654321-X` → DNI_NIE

**Risultato:** 6 corretti, 2 persi, 0 falsi positivi

**Note:** Clausola parti contrattuali

---

#### bank_account_clause [FAIL]

**Difficoltà:** medium

**Testo:**
```
El pago se efectuará mediante transferencia a la cuenta IBAN ES12 0049 1234 5012 3456 7890 titularidad de CONSTRUCCIONES PÉREZ, S.A., con CIF A-98765432.
```

**Atteso (3):**
- `ES12 0049 1234 5012 3456 7890` → IBAN
- `CONSTRUCCIONES PÉREZ, S.A.` → ORGANIZATION
- `A-98765432` → DNI_NIE

**Rilevato (2):**
- `IBAN ES12 0049 1234 5012 3456 7890` → IBAN
- `CONSTRUCCIONES PÉREZ, S.A.,` → ORGANIZATION

**Risultato:** 2 corretti, 1 persi, 0 falsi positivi

**Note:** Clausola bonifico bancario

---

#### cadastral_reference [PASS]

**Difficoltà:** medium

**Testo:**
```
Finca registral número 12345 del Registro de la Propiedad de Málaga, con referencia catastral 1234567AB1234S0001AB.
```

**Atteso (2):**
- `Málaga` → LOCATION
- `1234567AB1234S0001AB` → CADASTRAL_REF

**Rilevato (2):**
- `Málaga` → LOCATION
- `1234567AB1234S0001AB` → CADASTRAL_REF

**Risultato:** 2 corretti, 0 persi, 0 falsi positivi

**Note:** Registrazione proprietà con riferimento catastale

---

#### professional_ids [FAIL]

**Difficoltà:** hard

**Testo:**
```
Interviene el Abogado D. LUIS SÁNCHEZ, colegiado nº 12345 del ICAM, y el Procurador D. MIGUEL TORRES, colegiado nº 67890 del Colegio de Procuradores de Madrid.
```

**Atteso (4):**
- `LUIS SÁNCHEZ` → PERSON
- `12345` → PROFESSIONAL_ID
- `MIGUEL TORRES` → PERSON
- `67890` → PROFESSIONAL_ID

**Rilevato (2):**
- `Abogado D. LUIS SÁNCHEZ` → PERSON
- `Colegio de Procuradores de Madrid` → ORGANIZATION

**Risultato:** 1 corretti, 3 persi, 1 falsi positivi

**Note:** Numeri albo professionale

---

#### ecli_citation [PASS]

**Difficoltà:** easy

**Testo:**
```
Según doctrina del Tribunal Supremo (ECLI:ES:TS:2023:1234), confirmada en ECLI:ES:AN:2024:567.
```

**Atteso (2):**
- `ECLI:ES:TS:2023:1234` → ECLI
- `ECLI:ES:AN:2024:567` → ECLI

**Rilevato (3):**
- `Tribunal Supremo` → ORGANIZATION
- `(ECLI:ES:TS:2023:1234),` → ECLI
- `ECLI:ES:AN:2024:567` → ECLI

**Risultato:** 2 corretti, 0 persi, 1 falsi positivi

**Note:** Citazioni casi ECLI

---

#### vehicle_clause [PASS]

**Difficoltà:** medium

**Testo:**
```
El vehículo marca SEAT, modelo Ibiza, matrícula 1234 ABC, propiedad de D. FRANCISCO LÓPEZ.
```

**Atteso (2):**
- `1234 ABC` → LICENSE_PLATE
- `FRANCISCO LÓPEZ` → PERSON

**Rilevato (3):**
- `SEAT` → LICENSE_PLATE
- `matrícula 1234 ABC` → LICENSE_PLATE
- `D. FRANCISCO LÓPEZ` → PERSON

**Risultato:** 2 corretti, 0 persi, 1 falsi positivi

**Note:** Clausola descrizione veicolo

---

#### social_security [PASS]

**Difficoltà:** easy

**Testo:**
```
Trabajador afiliado a la Seguridad Social con número 281234567890, adscrito al Régimen General.
```

**Atteso (1):**
- `281234567890` → NSS

**Rilevato (2):**
- `28` → DNI_NIE
- `1234567890` → NSS

**Risultato:** 1 corretti, 0 persi, 1 falsi positivi

**Note:** Numero previdenza sociale in contesto lavorativo

---


## Conclusioni

### Punti di Forza del Modello

(Analizzare test superati e pattern)

### Debolezze Identificate

(Analizzare test falliti e pattern)

### Raccomandazioni

1. (Basate sui risultati)

---

**Generato automaticamente da:** `scripts/adversarial/evaluate_adversarial.py`
