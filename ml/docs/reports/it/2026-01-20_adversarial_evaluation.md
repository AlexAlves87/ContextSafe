# Valutazione Avversaria - NER Legale Spagnolo

**Data:** 2026-01-20
**Modello:** legal_ner_v1
**Test:** 35

---

## Riepilogo Esecutivo

| Metrica | Valore |
|---------|-------|
| Totale Test | 35 |
| Superati | 16 (45.7%) |
| Falliti | 19 (54.3%) |

### Per Categoria

| Categoria | Superati | Totale | Tasso |
|-----------|---------|-------|------|
| adversarial | 4 | 8 | 50.0% |
| edge_case | 6 | 9 | 66.7% |
| ocr_corruption | 1 | 5 | 20.0% |
| real_world | 3 | 10 | 30.0% |
| unicode_evasion | 2 | 3 | 66.7% |

### Per Difficoltà

| Difficoltà | Superati | Totale | Tasso |
|------------|---------|-------|------|
| easy | 4 | 4 | 100.0% |
| medium | 6 | 12 | 50.0% |
| hard | 6 | 19 | 31.6% |

---

## Risultati Dettagliati

### CASO LIMITE

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

**Note:** Pattern Iniziale + Cognome

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

**Note:** Nome nobile composto con particelle

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

**Rilevato (2):**
- `12` → CADASTRAL_REF
- `345 678 Z` → NSS

**Risultato:** 0 corretti, 1 persi, 2 falsi positivi

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
- `ES91 21` → IBAN
- `00 0418 4502 0005 1332` → CADASTRAL_REF

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
- `+34 612 345 678 o 0034612345678` → PHONE

**Risultato:** 1 corretti, 1 persi, 0 falsi positivi

**Note:** Formati telefonici internazionali

---

#### date_roman_numerals [PASS]

**Difficoltà:** hard

**Testo:**
```
Otorgado el día XV de marzo del año MMXXIV.
```

**Atteso (1):**
- `XV de marzo del año MMXXIV` → DATE

**Rilevato (1):**
- `día XV de marzo del año MMXXIV` → DATE

**Risultato:** 1 corretti, 0 persi, 0 falsi positivi

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

**Rilevato (1):**
- `El primero de enero de dos mil veinticuatro` → DATE

**Risultato:** 1 corretti, 0 persi, 0 falsi positivi

**Note:** Data scritta interamente a lettere

---

#### address_floor_door [FAIL]

**Difficoltà:** medium

**Testo:**
```
Domicilio en Calle Mayor 15, 3º B, 28001 Madrid.
```

**Atteso (3):**
- `Calle Mayor 15, 3º B` → ADDRESS
- `28001` → POSTAL_CODE
- `Madrid` → LOCATION

**Rilevato (1):**
- `Calle Mayor 15, 3º B, 28001 Madrid` → ADDRESS

**Risultato:** 1 corretti, 2 persi, 0 falsi positivi

**Note:** Indirizzo con piano e porta

---

### AVVERSARIO

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
- `12345678X` → LICENSE_PLATE

**Risultato:** 0 corretti, 0 persi, 1 falsi positivi

**Note:** Contesto di esempio/illustrativo dovrebbe essere ignorato

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

**Note:** Cognome nel nome aziendale - dovrebbe essere ORG non PERSON

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

**Note:** Luogo con prefisso tipo persona (San)

---

#### date_in_reference [FAIL]

**Difficoltà:** hard

**Testo:**
```
Según la Ley 15/2022, de 12 de julio, reguladora...
```

**Atteso (0):**
- (nessuna entità)

**Rilevato (3):**
- `Ley 15/` → ECLI
- `2022` → LICENSE_PLATE
- `, de 12 de julio` → ECLI

**Risultato:** 0 corretti, 0 persi, 3 falsi positivi

**Note:** Data in riferimento legale - non PII autonomo

---

#### numbers_not_dni [PASS]

**Difficoltà:** medium

**Testo:**
```
El expediente 12345678 consta de 9 folios.
```

**Atteso (0):**
- (nessuna entità)

**Rilevato (0):**
- (nessuna entità)

**Risultato:** 0 corretti, 0 persi, 0 falsi positivi

**Note:** Numero di 8 cifre che NON è un DNI (numero pratica)

---

#### mixed_languages [FAIL]

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
- `UK123456789` → NSS
- `Madrid` → LOCATION

**Risultato:** 2 corretti, 1 persi, 1 falsi positivi

**Note:** Nome inglese e passaporto straniero

---

### CORRUZIONE OCR

#### ocr_letter_substitution [FAIL]

**Difficoltà:** medium

**Testo:**
```
DNl 12345678Z perteneciente a María García.
```

**Atteso (2):**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Rilevato (4):**
- `DN` → CADASTRAL_REF
- `l 12345678` → NSS
- `Z` → CADASTRAL_REF
- `María García` → PERSON

**Risultato:** 1 corretti, 1 persi, 3 falsi positivi

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

**Rilevato (1):**
- `IBAN ES91 21O0 0418 45O2 OOO5 1332` → CADASTRAL_REF

**Risultato:** 0 corretti, 1 persi, 1 falsi positivi

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

**Rilevato (2):**
- `DonJoséGarcíaLópezcon` → PERSON
- `DNI12345678X` → CADASTRAL_REF

**Risultato:** 1 corretti, 1 persi, 1 falsi positivi

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

**Rilevato (2):**
- `D N I  1 2 3 4 5 6 7 8 Z` → CADASTRAL_REF
- `M` → LOCATION

**Risultato:** 0 corretti, 2 persi, 2 falsi positivi

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
- `12345678Х` → DNI_NIE
- `María` → PERSON

**Risultato:** 2 corretti, 0 persi, 0 falsi positivi

**Note:** Cirillico Х (U+0425) invece di Latino X

---

#### zero_width_space [PASS]

**Difficoltà:** hard

**Testo:**
```
DNI 123​456​78Z de María García.
```

**Atteso (2):**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Rilevato (2):**
- `123​456​78Z` → DNI_NIE
- `María García` → PERSON

**Risultato:** 2 corretti, 0 persi, 0 falsi positivi

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

**Rilevato (1):**
- `María` → LOCATION

**Risultato:** 0 corretti, 2 persi, 1 falsi positivi

**Note:** Cifre a larghezza intera (U+FF11-U+FF19)

---

### MONDO REALE

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

**Rilevato (4):**
- `NÚMERO MIL DOSCIENTOS TREINTA Y CUATRO.-` → DATE
- `Sevilla` → LOCATION
- `JOSÉ GARCÍA LÓPEZ` → PERSON
- `Ilustre Colegio de Sevilla` → ORGANIZATION

**Risultato:** 2 corretti, 2 persi, 2 falsi positivi

**Note:** Intestazione standard atto notarile

---

#### testament_comparecencia [FAIL]

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

**Rilevato (10):**
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

**Risultato:** 5 corretti, 0 persi, 5 falsi positivi

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

**Rilevato (8):**
- `ENCIA Nº 123` → PROFESSIONAL_ID
- `/2024.` → NSS
- `Madrid` → LOCATION
- `diez de enero de dos mil veinticuatro` → DATE
- `Sala Primera del Tribunal Supremo` → ORGANIZATION
- `D. ANTONIO PÉREZ MARTÍNEZ` → PERSON
- `Procur` → PERSON
- `D. CARLOS SÁNCHEZ GÓMEZ` → PERSON

**Risultato:** 4 corretti, 0 persi, 4 falsi positivi

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

**Note:** Clausola parti del contratto

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

**Rilevato (9):**
- `IB` → NSS
- `AN` → NSS
- `ES12 0049 1234 5012 3456 7890` → NSS
- `CONSTRUCCIONES PÉREZ, S.A.,` → ORGANIZATION
- `A` → DNI_NIE
- `-` → DNI_NIE
- `98765` → NSS
- `4` → DNI_NIE
- `32` → NSS

**Risultato:** 2 corretti, 1 persi, 7 falsi positivi

**Note:** Clausola bonifico bancario

---

#### cadastral_reference [FAIL]

**Difficoltà:** medium

**Testo:**
```
Finca registral número 12345 del Registro de la Propiedad de Málaga, con referencia catastral 1234567AB1234S0001AB.
```

**Atteso (2):**
- `Málaga` → LOCATION
- `1234567AB1234S0001AB` → CADASTRAL_REF

**Rilevato (5):**
- `número 12345 del Registro de la` → PROFESSIONAL_ID
- `Propiedad` → ORGANIZATION
- `de` → PROFESSIONAL_ID
- `Málaga` → ORGANIZATION
- `1234567AB1234S0001AB` → CADASTRAL_REF

**Risultato:** 1 corretti, 1 persi, 4 falsi positivi

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

**Rilevato (3):**
- `Abogado D. LUIS SÁNCHEZ` → PERSON
- `Procur` → PERSON
- `Colegio de Procuradores de Madrid` → ORGANIZATION

**Risultato:** 1 corretti, 3 persi, 2 falsi positivi

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

**Rilevato (4):**
- `Tribunal Supremo` → ORGANIZATION
- `(ECLI:ES:TS:2023:1234),` → ECLI
- `E` → ECLI
- `CLI:ES:AN:2024:567` → ECLI

**Risultato:** 2 corretti, 0 persi, 2 falsi positivi

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
- `modelo Ibiza, matrícula 1234 ABC` → LICENSE_PLATE
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

**Rilevato (3):**
- `Seguridad Social` → ORGANIZATION
- `281234567890` → NSS
- `Régimen General` → ORGANIZATION

**Risultato:** 1 corretti, 0 persi, 2 falsi positivi

**Note:** Numero previdenza sociale nel contesto lavorativo

---


## Metodologia

### Progettazione Test

35 casi di test sono stati progettati raggruppati in 5 categorie secondo la tassonomia definita nelle linee guida del progetto:

| Categoria | Test | Obiettivo |
|-----------|-------|----------|
| edge_case | 9 | Condizioni limite (nomi corti, formati insoliti) |
| adversarial | 8 | Casi progettati per confondere (negazioni, esempi, finzione) |
| ocr_corruption | 5 | Simulazione errori di scansione (l/I, 0/O, spazi) |
| unicode_evasion | 3 | Caratteri simili (Cirillico, larghezza intera, larghezza zero) |
| real_world | 10 | Pattern reali da documenti legali spagnoli |

### Criteri di Valutazione

- **PASS (easy/medium):** Tutte le entità attese rilevate
- **PASS (hard):** Tutte le entità rilevate E zero falsi positivi
- **Matching:** Corrispondenza fuzzy con tolleranza ±2 caratteri e 80% similarità

### Riproducibilità

```bash
cd ml
source .venv/bin/activate
python scripts/adversarial/evaluate_adversarial.py
```

---

## Analisi Errori

### Errore 1: Frammentazione Entità Composte

**Pattern:** Sequenze con punteggiatura interna si frammentano in modo errato.

**Esempio:**
```
Input: "con D.N.I. número 12345678-Z"
Atteso: 12345678-Z → DNI_NIE
Rilevato: D → PROFESSIONAL_ID, .N → IBAN, . → PROFESSIONAL_ID, I → IBAN, . → PROFESSIONAL_ID, 12345678-Z → DNI_NIE
```

**Causa:** Il modello non ha visto pattern con punteggiatura variabile nell'addestramento sintetico.

**Soluzione proposta:** Regex pre-processo per normalizzare `D.N.I.`, `N.I.F.`, `C.I.F.` → `DNI`, `NIF`, `CIF`.

---

### Errore 2: Confusione Tipo in Sequenze Numeriche

**Pattern:** Lunghe sequenze numeriche classificate come tipo errato.

**Esempio:**
```
Input: "IBAN ES12 0049 1234 5012 3456 7890"
Atteso: ES12 0049 1234 5012 3456 7890 → IBAN
Rilevato: ES12 0049 1234 5012 3456 7890 → NSS
```

**Causa:** Sovrapposizione pattern numerici tra IBAN (24 caratteri), NSS (12 cifre), CADASTRAL_REF (20 caratteri).

**Soluzione proposta:** Post-processo con validazione formato specifico per tipo.

---

### Errore 3: Falsi Positivi in Riferimenti Legali

**Pattern:** Numeri in contesto legale (leggi, numeri pratica, protocolli) rilevati come PII.

**Esempio:**
```
Input: "Según la Ley 15/2022, de 12 de julio"
Atteso: (nessuna entità)
Rilevato: Ley 15/ → ECLI, 2022 → LICENSE_PLATE, de 12 de julio → ECLI
```

**Causa:** Pattern `\d+/\d{4}` e date appaiono in contesto legale, non come PII.

**Soluzione proposta:** Post-processo per escludere pattern `Ley \d+/\d{4}`, `Real Decreto`, `expediente \d+`.

---

### Errore 4: Vulnerabilità ad Errori OCR

**Pattern:** Tipiche confusioni OCR (l/I, 0/O, spazi) rompono rilevamento.

**Esempio:**
```
Input: "DNl 12345678Z" (l minuscola invece di I)
Atteso: 12345678Z → DNI_NIE
Rilevato: DN → CADASTRAL_REF, l 12345678 → NSS, Z → CADASTRAL_REF
```

**Causa:** Il modello addestrato solo con testo pulito, non con varianti OCR.

**Soluzione proposta:** Pre-processo con normalizzazione OCR:
- `DNl` → `DNI`
- `0` ↔ `O` in contesto numerico
- Collasso spazi in pattern noti

---

### Errore 5: Cecità Contestuale

**Pattern:** Modello non distingue menzioni illustrative da dati reali.

**Esempio:**
```
Input: "El formato del DNI es 12345678X (ejemplo ilustrativo)"
Atteso: (nessuna entità - è un esempio)
Rilevato: 12345678X → LICENSE_PLATE
```

**Causa:** Modello non ha accesso al contesto semantico ("esempio", "formato", "illustrativo").

**Soluzione proposta:** Post-processo con rilevamento contesto:
- Escludere se "ejemplo", "formato", "illustrativo" appare in finestra ±10 token
- Richiede analisi più sofisticata (parzialmente risolvibile con regex)

---

### Errore 6: Entità Fittizie Rilevate

**Pattern:** Personaggi letterari/fittizi rilevati come persone reali.

**Esempio:**
```
Input: "Como dijo Don Quijote de la Mancha"
Atteso: (nessuna entità - personaggio fittizio)
Rilevato: Don Quijote de la Mancha → PERSON
```

**Causa:** Modello non ha lista di personaggi fittizi noti.

**Soluzione proposta:** Post-processo con gazzettino esclusione (personaggi fittizi, figure pubbliche storiche).

---

## Classificazione Soluzioni

### Risolvibile con Regex (Pre-processo)

| Problema | Regex | Esempio |
|----------|-------|---------|
| Normalizzare D.N.I. | `D\.?\s*N\.?\s*I\.?` → `DNI` | `D.N.I.` → `DNI` |
| Normalizzare N.I.F. | `N\.?\s*I\.?\s*F\.?` → `NIF` | `N.I.F.` → `NIF` |
| Collasso spazi in DNI | `(\d)\s+(\d)` → `\1\2` | `12 345 678` → `12345678` |
| Larghezza intera → ASCII | `[\uFF10-\uFF19]` → `[0-9]` | `１２３` → `123` |
| Rimozione larghezza zero | `[\u200b\u200c\u200d]` → `` | invisibile → rimosso |
| OCR l/I in DNI | `DN[lI1]` → `DNI` | `DNl` → `DNI` |
| OCR 0/O in IBAN | `[0O]` normalizzazione contestuale | `21O0` → `2100` |

### Risolvibile con Regex (Post-processo)

| Problema | Regex/Validazione | Azione |
|----------|------------------|--------|
| Ley X/YYYY | `Ley\s+\d+/\d{4}` | Escludere entità se match |
| Numero pratica | `expediente\s+\d+` | Escludere entità |
| Protocollo NÚMERO | `NÚMERO\s+[A-Z\s]+\.-` | Escludere se rilevato come DATE |
| Checksum DNI | Validare lettera mod-23 | Rifiutare se invalido |
| Checksum IBAN | Validare cifre controllo | Rifiutare se invalido |
| Checksum NSS | Validare mod-97 | Rifiutare se invalido |
| Formato targa | `\d{4}\s?[A-Z]{3}` | Rifiutare se no match |
| Contesto esempio | `(ejemplo\|ilustrativo\|formato)` vicino | Escludere entità |

### Richiede Modello/NLP (Non Regex)

| Problema | Soluzione Necessaria |
|----------|-------------------|
| Personaggi fittizi | Gazzettino esclusione + NER specifico |
| Troncamento OCR ("Procur") | Migliore tokenizzazione o modello robusto |
| Profonda ambiguità semantica | Fine-tuning con esempi negativi |

---

## Conclusioni

### Punti di Forza Modello

1. **Pattern puliti:** 100% accuratezza in test facili con formato standard
2. **Nomi composti:** Rileva correttamente nomi nobili lunghi ("José María de la Santísima Trinidad...")
3. **Negazione semplice:** Riconosce "NON avere DNI" e non rileva falsi positivi
4. **Discriminazione ORG/PERSON:** Distingue "García y Asociados, S.L." come organizzazione
5. **Luoghi con prefisso:** "San Fernando del Valle" correttamente come LOCATION
6. **Parziale robustezza Unicode:** Resiste a Cirillico e spazi larghezza zero

### Debolezze Identificate

1. **Overfitting a dati sintetici:** 99.87% F1 in test → 45.7% in adversarial
2. **Fragilità a OCR:** 80% fallimento in categoria ocr_corruption
3. **Esplosione falsi positivi:** In testi complessi genera 5-10 rilevamenti spuri
4. **Confusione tipo numerico:** IBAN ↔ NSS ↔ CADASTRAL_REF
5. **Cecità contestuale:** Non distingue esempi, riferimenti legali, finzione

### Metriche Chiave

| Metrica | Valore | Obiettivo | Stato |
|---------|-------|----------|--------|
| F1 sintetico | 99.87% | ≥85% | ✅ Superato |
| F1 adversarial (stimato) | ~45% | ≥70% | ❌ Non Raggiunto |
| Tasso falsi positivi | Alto | Basso | ❌ Critico |
| Robustezza OCR | 20% | ≥80% | ❌ Critico |

---

## Lavoro Futuro

### Priorità ALTA (Implementare Immediatamente)

1. **Pipeline Pre/Post-processo**
   - Creare `scripts/inference/text_normalizer.py` (pre-processo)
   - Creare `scripts/inference/entity_validator.py` (post-processo)
   - Integrare in pipeline inferenza

2. **Validazione Checksum**
   - DNI: lettera = "TRWAGMYFPDXBNJZSQVHLCKE"[numero % 23]
   - IBAN: cifre controllo valide
   - NSS: validazione mod-97

3. **Gazzettini Esclusione**
   - Personaggi fittizi noti
   - Pattern legali (Ley, RD, numero pratica)

### Priorità MEDIA (Prossima Iterazione)

4. **Aumento Dati**
   - Aggiungere esempi con errori OCR al dataset
   - Aggiungere esempi negativi (numeri che NON sono PII)
   - Aggiungere contesti "esempio illustrativo"

5. **Ri-addestramento**
   - Con dataset aumentato
   - Valutare layer CRF (+4-13% F1 secondo letteratura)

### Priorità BASSA (Futuro)

6. **Dati Reali Annotati**
   - Ottenere documenti legali reali anonimizzati
   - Annotazione manuale gold standard

---

## Riferimenti

1. **Modello base:** PlanTL-GOB-ES/roberta-base-bne-capitel-ner
2. **Metodologia avversaria:** linee guida del progetto, sezione 4 (Testing Avversario)
3. **Validazione DNI:** BOE - Algoritmo lettera NIF
4. **Validazione IBAN:** ISO 13616 - International Bank Account Number
5. **seqeval:** Framework valutazione NER (entity-level)

---

**Generato da:** `scripts/adversarial/evaluate_adversarial.py`
**Data:** 2026-01-20
**Versione:** 1.0
