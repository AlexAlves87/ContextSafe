# Adversarielle Evaluierung - Spanisches Rechts-NER

**Datum:** 2026-01-20
**Modell:** legal_ner_v1
**Tests:** 35

---

## Zusammenfassung

| Metrik | Wert |
|---------|-------|
| Gesamttests | 35 |
| Bestanden | 16 (45.7%) |
| Fehlgeschlagen | 19 (54.3%) |

### Nach Kategorie

| Kategorie | Bestanden | Gesamt | Rate |
|-----------|---------|-------|------|
| adversarial | 4 | 8 | 50.0% |
| edge_case | 6 | 9 | 66.7% |
| ocr_corruption | 1 | 5 | 20.0% |
| real_world | 3 | 10 | 30.0% |
| unicode_evasion | 2 | 3 | 66.7% |

### Nach Schwierigkeit

| Schwierigkeit | Bestanden | Gesamt | Rate |
|------------|---------|-------|------|
| easy | 4 | 4 | 100.0% |
| medium | 6 | 12 | 50.0% |
| hard | 6 | 19 | 31.6% |

---

## Detaillierte Ergebnisse

### EDGE CASE

#### single_letter_name [PASS]

**Schwierigkeit:** medium

**Text:**
```
El demandante J. García presentó recurso.
```

**Erwartet (1):**
- `J. García` → PERSON

**Erkannt (1):**
- `J. García` → PERSON

**Ergebnis:** 1 richtig, 0 verpasst, 0 falsch positiv

**Notizen:** Initial + Nachname Muster

---

#### very_long_name [PASS]

**Schwierigkeit:** hard

**Text:**
```
Compareció Don José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón.
```

**Erwartet (1):**
- `José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón` → PERSON

**Erkannt (1):**
- `Don José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón` → PERSON

**Ergebnis:** 1 richtig, 0 verpasst, 0 falsch positiv

**Notizen:** Zusammengesetzter adeliger Name mit Partikeln

---

#### dni_without_letter [PASS]

**Schwierigkeit:** medium

**Text:**
```
DNI número 12345678 (pendiente de verificación).
```

**Erwartet (1):**
- `12345678` → DNI_NIE

**Erkannt (1):**
- `12345678` → DNI_NIE

**Ergebnis:** 1 richtig, 0 verpasst, 0 falsch positiv

**Notizen:** DNI ohne Kontrollbuchstabe

---

#### dni_with_spaces [FAIL]

**Schwierigkeit:** hard

**Text:**
```
Su documento de identidad es 12 345 678 Z.
```

**Erwartet (1):**
- `12 345 678 Z` → DNI_NIE

**Erkannt (2):**
- `12` → CADASTRAL_REF
- `345 678 Z` → NSS

**Ergebnis:** 0 richtig, 1 verpasst, 2 falsch positiv

**Notizen:** DNI mit internen Leerzeichen

---

#### iban_with_spaces [PASS]

**Schwierigkeit:** easy

**Text:**
```
Transferir a ES91 2100 0418 4502 0005 1332.
```

**Erwartet (1):**
- `ES91 2100 0418 4502 0005 1332` → IBAN

**Erkannt (2):**
- `ES91 21` → IBAN
- `00 0418 4502 0005 1332` → CADASTRAL_REF

**Ergebnis:** 1 richtig, 0 verpasst, 1 falsch positiv

**Notizen:** Standard IBAN-Format mit Leerzeichen

---

#### phone_international [FAIL]

**Schwierigkeit:** medium

**Text:**
```
Contacto: +34 612 345 678 o 0034612345678.
```

**Erwartet (2):**
- `+34 612 345 678` → PHONE
- `0034612345678` → PHONE

**Erkannt (1):**
- `+34 612 345 678 o 0034612345678` → PHONE

**Ergebnis:** 1 richtig, 1 verpasst, 0 falsch positiv

**Notizen:** Internationale Telefonformate

---

#### date_roman_numerals [PASS]

**Schwierigkeit:** hard

**Text:**
```
Otorgado el día XV de marzo del año MMXXIV.
```

**Erwartet (1):**
- `XV de marzo del año MMXXIV` → DATE

**Erkannt (1):**
- `día XV de marzo del año MMXXIV` → DATE

**Ergebnis:** 1 richtig, 0 verpasst, 0 falsch positiv

**Notizen:** Datum mit römischen Ziffern (notarieller Stil)

---

#### date_ordinal [PASS]

**Schwierigkeit:** medium

**Text:**
```
El primero de enero de dos mil veinticuatro.
```

**Erwartet (1):**
- `primero de enero de dos mil veinticuatro` → DATE

**Erkannt (1):**
- `El primero de enero de dos mil veinticuatro` → DATE

**Ergebnis:** 1 richtig, 0 verpasst, 0 falsch positiv

**Notizen:** Vollständig ausgeschriebenes Datum

---

#### address_floor_door [FAIL]

**Schwierigkeit:** medium

**Text:**
```
Domicilio en Calle Mayor 15, 3º B, 28001 Madrid.
```

**Erwartet (3):**
- `Calle Mayor 15, 3º B` → ADDRESS
- `28001` → POSTAL_CODE
- `Madrid` → LOCATION

**Erkannt (1):**
- `Calle Mayor 15, 3º B, 28001 Madrid` → ADDRESS

**Ergebnis:** 1 richtig, 2 verpasst, 0 falsch positiv

**Notizen:** Adresse mit Etage und Tür

---

### ADVERSARIAL

#### negation_dni [PASS]

**Schwierigkeit:** hard

**Text:**
```
El interesado manifiesta NO tener DNI ni NIE.
```

**Erwartet (0):**
- (keine Entitäten)

**Erkannt (0):**
- (keine Entitäten)

**Ergebnis:** 0 richtig, 0 verpasst, 0 falsch positiv

**Notizen:** Sollte KEINE PII erkennen - Negationskontext

---

#### example_dni [FAIL]

**Schwierigkeit:** hard

**Text:**
```
El formato del DNI es 12345678X (ejemplo ilustrativo).
```

**Erwartet (0):**
- (keine Entitäten)

**Erkannt (1):**
- `12345678X` → LICENSE_PLATE

**Ergebnis:** 0 richtig, 0 verpasst, 1 falsch positiv

**Notizen:** Beispiel/illustrativer Kontext sollte ignoriert werden

---

#### fictional_person [FAIL]

**Schwierigkeit:** hard

**Text:**
```
Como dijo Don Quijote de la Mancha en su célebre obra.
```

**Erwartet (0):**
- (keine Entitäten)

**Erkannt (1):**
- `Don Quijote de la Mancha` → PERSON

**Ergebnis:** 0 richtig, 0 verpasst, 1 falsch positiv

**Notizen:** Fiktiver/literarischer Charakter - keine PII

---

#### organization_as_person [PASS]

**Schwierigkeit:** medium

**Text:**
```
García y Asociados, S.L. interpone demanda.
```

**Erwartet (1):**
- `García y Asociados, S.L.` → ORGANIZATION

**Erkannt (1):**
- `García y Asociados, S.L.` → ORGANIZATION

**Ergebnis:** 1 richtig, 0 verpasst, 0 falsch positiv

**Notizen:** Nachname im Firmennamen - sollte ORG sein, nicht PERSON

---

#### location_as_person [PASS]

**Schwierigkeit:** hard

**Text:**
```
El municipio de San Fernando del Valle de Catamarca.
```

**Erwartet (1):**
- `San Fernando del Valle de Catamarca` → LOCATION

**Erkannt (1):**
- `San Fernando del Valle de Catamarca` → LOCATION

**Ergebnis:** 1 richtig, 0 verpasst, 0 falsch positiv

**Notizen:** Ort mit personenähnlichem Präfix (San)

---

#### date_in_reference [FAIL]

**Schwierigkeit:** hard

**Text:**
```
Según la Ley 15/2022, de 12 de julio, reguladora...
```

**Erwartet (0):**
- (keine Entitäten)

**Erkannt (3):**
- `Ley 15/` → ECLI
- `2022` → LICENSE_PLATE
- `, de 12 de julio` → ECLI

**Ergebnis:** 0 richtig, 0 verpasst, 3 falsch positiv

**Notizen:** Datum in gesetzlicher Referenz - keine eigenständige PII

---

#### numbers_not_dni [PASS]

**Schwierigkeit:** medium

**Text:**
```
El expediente 12345678 consta de 9 folios.
```

**Erwartet (0):**
- (keine Entitäten)

**Erkannt (0):**
- (keine Entitäten)

**Ergebnis:** 0 richtig, 0 verpasst, 0 falsch positiv

**Notizen:** 8-stellige Nummer, die KEIN DNI ist (Aktenzeichen)

---

#### mixed_languages [FAIL]

**Schwierigkeit:** hard

**Text:**
```
Mr. John Smith, con pasaporte UK123456789, residente en Madrid.
```

**Erwartet (3):**
- `John Smith` → PERSON
- `UK123456789` → DNI_NIE
- `Madrid` → LOCATION

**Erkannt (3):**
- `Mr. John Smith` → PERSON
- `UK123456789` → NSS
- `Madrid` → LOCATION

**Ergebnis:** 2 richtig, 1 verpasst, 1 falsch positiv

**Notizen:** Englischer Name und ausländischer Pass

---

### OCR CORRUPTION

#### ocr_letter_substitution [FAIL]

**Schwierigkeit:** medium

**Text:**
```
DNl 12345678Z perteneciente a María García.
```

**Erwartet (2):**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Erkannt (4):**
- `DN` → CADASTRAL_REF
- `l 12345678` → NSS
- `Z` → CADASTRAL_REF
- `María García` → PERSON

**Ergebnis:** 1 richtig, 1 verpasst, 3 falsch positiv

**Notizen:** OCR verwechselte I mit l

---

#### ocr_zero_o_confusion [FAIL]

**Schwierigkeit:** hard

**Text:**
```
IBAN ES91 21O0 0418 45O2 OOO5 1332.
```

**Erwartet (1):**
- `ES91 21O0 0418 45O2 OOO5 1332` → IBAN

**Erkannt (1):**
- `IBAN ES91 21O0 0418 45O2 OOO5 1332` → CADASTRAL_REF

**Ergebnis:** 0 richtig, 1 verpasst, 1 falsch positiv

**Notizen:** OCR verwechselte 0 mit O

---

#### ocr_missing_spaces [FAIL]

**Schwierigkeit:** hard

**Text:**
```
DonJoséGarcíaLópezconDNI12345678X.
```

**Erwartet (2):**
- `JoséGarcíaLópez` → PERSON
- `12345678X` → DNI_NIE

**Erkannt (2):**
- `DonJoséGarcíaLópezcon` → PERSON
- `DNI12345678X` → CADASTRAL_REF

**Ergebnis:** 1 richtig, 1 verpasst, 1 falsch positiv

**Notizen:** OCR hat alle Leerzeichen verloren

---

#### ocr_extra_spaces [FAIL]

**Schwierigkeit:** hard

**Text:**
```
D N I  1 2 3 4 5 6 7 8 Z  de  M a r í a.
```

**Erwartet (2):**
- `1 2 3 4 5 6 7 8 Z` → DNI_NIE
- `M a r í a` → PERSON

**Erkannt (2):**
- `D N I  1 2 3 4 5 6 7 8 Z` → CADASTRAL_REF
- `M` → LOCATION

**Ergebnis:** 0 richtig, 2 verpasst, 2 falsch positiv

**Notizen:** OCR hat zusätzliche Leerzeichen eingefügt

---

#### ocr_accent_loss [PASS]

**Schwierigkeit:** easy

**Text:**
```
Jose Maria Garcia Lopez, vecino de Malaga.
```

**Erwartet (2):**
- `Jose Maria Garcia Lopez` → PERSON
- `Malaga` → LOCATION

**Erkannt (2):**
- `Jose Maria Garcia Lopez` → PERSON
- `Malaga` → LOCATION

**Ergebnis:** 2 richtig, 0 verpasst, 0 falsch positiv

**Notizen:** OCR hat Akzente verloren (häufig)

---

### UNICODE EVASION

#### cyrillic_o [PASS]

**Schwierigkeit:** hard

**Text:**
```
DNI 12345678Х pertenece a María.
```

**Erwartet (2):**
- `12345678Х` → DNI_NIE
- `María` → PERSON

**Erkannt (2):**
- `12345678Х` → DNI_NIE
- `María` → PERSON

**Ergebnis:** 2 richtig, 0 verpasst, 0 falsch positiv

**Notizen:** Kyrillisches Х (U+0425) anstelle von Lateinischem X

---

#### zero_width_space [PASS]

**Schwierigkeit:** hard

**Text:**
```
DNI 123​456​78Z de María García.
```

**Erwartet (2):**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Erkannt (2):**
- `123​456​78Z` → DNI_NIE
- `María García` → PERSON

**Ergebnis:** 2 richtig, 0 verpasst, 0 falsch positiv

**Notizen:** Zero-width spaces eingefügt (U+200B)

---

#### fullwidth_numbers [FAIL]

**Schwierigkeit:** hard

**Text:**
```
DNI １２３４５６７８Z de María.
```

**Erwartet (2):**
- `１２３４５６７８Z` → DNI_NIE
- `María` → PERSON

**Erkannt (1):**
- `María` → LOCATION

**Ergebnis:** 0 richtig, 2 verpasst, 1 falsch positiv

**Notizen:** Fullwidth-Ziffern (U+FF11-U+FF19)

---

### REAL WORLD

#### notarial_header [FAIL]

**Schwierigkeit:** medium

**Text:**
```
NÚMERO MIL DOSCIENTOS TREINTA Y CUATRO.- En la ciudad de Sevilla, a quince de marzo de dos mil veinticuatro, ante mí, JOSÉ GARCÍA LÓPEZ, Notario del Ilustre Colegio de Sevilla.
```

**Erwartet (4):**
- `Sevilla` → LOCATION
- `quince de marzo de dos mil veinticuatro` → DATE
- `JOSÉ GARCÍA LÓPEZ` → PERSON
- `Sevilla` → LOCATION

**Erkannt (4):**
- `NÚMERO MIL DOSCIENTOS TREINTA Y CUATRO.-` → DATE
- `Sevilla` → LOCATION
- `JOSÉ GARCÍA LÓPEZ` → PERSON
- `Ilustre Colegio de Sevilla` → ORGANIZATION

**Ergebnis:** 2 richtig, 2 verpasst, 2 falsch positiv

**Notizen:** Standardmäßiger notarieller Urkundenkopf

---

#### testament_comparecencia [FAIL]

**Schwierigkeit:** hard

**Text:**
```
COMPARECE: Doña MARÍA ANTONIA FERNÁNDEZ RUIZ, mayor de edad, viuda, natural de Córdoba, vecina de Madrid, con domicilio en Calle Alcalá número 123, piso 4º, puerta B, y con D.N.I. número 12345678-Z.
```

**Erwartet (5):**
- `MARÍA ANTONIA FERNÁNDEZ RUIZ` → PERSON
- `Córdoba` → LOCATION
- `Madrid` → LOCATION
- `Calle Alcalá número 123, piso 4º, puerta B` → ADDRESS
- `12345678-Z` → DNI_NIE

**Erkannt (10):**
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

**Ergebnis:** 5 richtig, 0 verpasst, 5 falsch positiv

**Notizen:** Klausel über das Erscheinen im Testament

---

#### judicial_sentence_header [FAIL]

**Schwierigkeit:** hard

**Text:**
```
SENTENCIA Nº 123/2024. En Madrid, a diez de enero de dos mil veinticuatro. Vistos por la Sala Primera del Tribunal Supremo los recursos interpuestos por D. ANTONIO PÉREZ MARTÍNEZ, representado por el Procurador D. CARLOS SÁNCHEZ GÓMEZ.
```

**Erwartet (4):**
- `Madrid` → LOCATION
- `diez de enero de dos mil veinticuatro` → DATE
- `ANTONIO PÉREZ MARTÍNEZ` → PERSON
- `CARLOS SÁNCHEZ GÓMEZ` → PERSON

**Erkannt (8):**
- `ENCIA Nº 123` → PROFESSIONAL_ID
- `/2024.` → NSS
- `Madrid` → LOCATION
- `diez de enero de dos mil veinticuatro` → DATE
- `Sala Primera del Tribunal Supremo` → ORGANIZATION
- `D. ANTONIO PÉREZ MARTÍNEZ` → PERSON
- `Procur` → PERSON
- `D. CARLOS SÁNCHEZ GÓMEZ` → PERSON

**Ergebnis:** 4 richtig, 0 verpasst, 4 falsch positiv

**Notizen:** Kopfzeile Urteil des Obersten Gerichtshofs

---

#### contract_parties [FAIL]

**Schwierigkeit:** hard

**Text:**
```
De una parte, INMOBILIARIA GARCÍA, S.L., con CIF B-12345678, domiciliada en Plaza Mayor 1, 28013 Madrid, representada por D. PEDRO GARCÍA LÓPEZ. De otra parte, Dña. ANA MARTÍNEZ RUIZ, con NIF 87654321-X.
```

**Erwartet (8):**
- `INMOBILIARIA GARCÍA, S.L.` → ORGANIZATION
- `B-12345678` → DNI_NIE
- `Plaza Mayor 1` → ADDRESS
- `28013` → POSTAL_CODE
- `Madrid` → LOCATION
- `PEDRO GARCÍA LÓPEZ` → PERSON
- `ANA MARTÍNEZ RUIZ` → PERSON
- `87654321-X` → DNI_NIE

**Erkannt (6):**
- `INMOBILIARIA GARCÍA, S.L.,` → ORGANIZATION
- `B-12345678` → DNI_NIE
- `Plaza Mayor 1, 28013 Madrid` → ADDRESS
- `D. PEDRO GARCÍA LÓPEZ` → PERSON
- `Dña. ANA MARTÍNEZ RUIZ` → PERSON
- `87654321-X` → DNI_NIE

**Ergebnis:** 6 richtig, 2 verpasst, 0 falsch positiv

**Notizen:** Vertragsparteien-Klausel

---

#### bank_account_clause [FAIL]

**Schwierigkeit:** medium

**Text:**
```
El pago se efectuará mediante transferencia a la cuenta IBAN ES12 0049 1234 5012 3456 7890 titularidad de CONSTRUCCIONES PÉREZ, S.A., con CIF A-98765432.
```

**Erwartet (3):**
- `ES12 0049 1234 5012 3456 7890` → IBAN
- `CONSTRUCCIONES PÉREZ, S.A.` → ORGANIZATION
- `A-98765432` → DNI_NIE

**Erkannt (9):**
- `IB` → NSS
- `AN` → NSS
- `ES12 0049 1234 5012 3456 7890` → NSS
- `CONSTRUCCIONES PÉREZ, S.A.,` → ORGANIZATION
- `A` → DNI_NIE
- `-` → DNI_NIE
- `98765` → NSS
- `4` → DNI_NIE
- `32` → NSS

**Ergebnis:** 2 richtig, 1 verpasst, 7 falsch positiv

**Notizen:** Banküberweisungsklausel

---

#### cadastral_reference [FAIL]

**Schwierigkeit:** medium

**Text:**
```
Finca registral número 12345 del Registro de la Propiedad de Málaga, con referencia catastral 1234567AB1234S0001AB.
```

**Erwartet (2):**
- `Málaga` → LOCATION
- `1234567AB1234S0001AB` → CADASTRAL_REF

**Erkannt (5):**
- `número 12345 del Registro de la` → PROFESSIONAL_ID
- `Propiedad` → ORGANIZATION
- `de` → PROFESSIONAL_ID
- `Málaga` → ORGANIZATION
- `1234567AB1234S0001AB` → CADASTRAL_REF

**Ergebnis:** 1 richtig, 1 verpasst, 4 falsch positiv

**Notizen:** Eigentumsregistrierung mit Katasterreferenz

---

#### professional_ids [FAIL]

**Schwierigkeit:** hard

**Text:**
```
Interviene el Abogado D. LUIS SÁNCHEZ, colegiado nº 12345 del ICAM, y el Procurador D. MIGUEL TORRES, colegiado nº 67890 del Colegio de Procuradores de Madrid.
```

**Erwartet (4):**
- `LUIS SÁNCHEZ` → PERSON
- `12345` → PROFESSIONAL_ID
- `MIGUEL TORRES` → PERSON
- `67890` → PROFESSIONAL_ID

**Erkannt (3):**
- `Abogado D. LUIS SÁNCHEZ` → PERSON
- `Procur` → PERSON
- `Colegio de Procuradores de Madrid` → ORGANIZATION

**Ergebnis:** 1 richtig, 3 verpasst, 2 falsch positiv

**Notizen:** Berufsnummern der Anwaltkammer

---

#### ecli_citation [PASS]

**Schwierigkeit:** easy

**Text:**
```
Según doctrina del Tribunal Supremo (ECLI:ES:TS:2023:1234), confirmada en ECLI:ES:AN:2024:567.
```

**Erwartet (2):**
- `ECLI:ES:TS:2023:1234` → ECLI
- `ECLI:ES:AN:2024:567` → ECLI

**Erkannt (4):**
- `Tribunal Supremo` → ORGANIZATION
- `(ECLI:ES:TS:2023:1234),` → ECLI
- `E` → ECLI
- `CLI:ES:AN:2024:567` → ECLI

**Ergebnis:** 2 richtig, 0 verpasst, 2 falsch positiv

**Notizen:** ECLI-Fallzitate

---

#### vehicle_clause [PASS]

**Schwierigkeit:** medium

**Text:**
```
El vehículo marca SEAT, modelo Ibiza, matrícula 1234 ABC, propiedad de D. FRANCISCO LÓPEZ.
```

**Erwartet (2):**
- `1234 ABC` → LICENSE_PLATE
- `FRANCISCO LÓPEZ` → PERSON

**Erkannt (3):**
- `SEAT` → LICENSE_PLATE
- `modelo Ibiza, matrícula 1234 ABC` → LICENSE_PLATE
- `D. FRANCISCO LÓPEZ` → PERSON

**Ergebnis:** 2 richtig, 0 verpasst, 1 falsch positiv

**Notizen:** Fahrzeugbeschreibungsklausel

---

#### social_security [PASS]

**Schwierigkeit:** easy

**Text:**
```
Trabajador afiliado a la Seguridad Social con número 281234567890, adscrito al Régimen General.
```

**Erwartet (1):**
- `281234567890` → NSS

**Erkannt (3):**
- `Seguridad Social` → ORGANIZATION
- `281234567890` → NSS
- `Régimen General` → ORGANIZATION

**Ergebnis:** 1 richtig, 0 verpasst, 2 falsch positiv

**Notizen:** Sozialversicherungsnummer im Beschäftigungskontext

---


## Methodik

### Testdesign

35 Testfälle wurden entworfen, gruppiert in 5 Kategorien gemäß der in den Projektrichtlinien definierten Taxonomie:

| Kategorie | Tests | Ziel |
|-----------|-------|----------|
| edge_case | 9 | Randbedingungen (kurze Namen, ungewöhnliche Formate) |
| adversarial | 8 | Fälle, die darauf ausgelegt sind zu verwirren (Negationen, Beispiele, Fiktion) |
| ocr_corruption | 5 | Simulation von Scanfehlern (l/I, 0/O, Leerzeichen) |
| unicode_evasion | 3 | Ähnliche Zeichen (Kyrillisch, Fullwidth, Zero-Width) |
| real_world | 10 | Reale Muster aus spanischen Rechtsdokumenten |

### Bewertungskriterien

- **PASS (easy/medium):** Alle erwarteten Entitäten erkannt
- **PASS (hard):** Alle Entitäten erkannt UND null falsch positive Ergebnisse
- **Matching:** Fuzzy Match mit ±2 Zeichen Toleranz und 80% Ähnlichkeit

### Reproduzierbarkeit

```bash
cd ml
source .venv/bin/activate
python scripts/adversarial/evaluate_adversarial.py
```

---

## Fehleranalyse

### Fehler 1: Fragmentierung zusammengesetzter Entitäten

**Muster:** Sequenzen mit interner Interpunktion fragmentieren inkorrekt.

**Beispiel:**
```
Eingabe: "con D.N.I. número 12345678-Z"
Erwartet: 12345678-Z → DNI_NIE
Erkannt: D → PROFESSIONAL_ID, .N → IBAN, . → PROFESSIONAL_ID, I → IBAN, . → PROFESSIONAL_ID, 12345678-Z → DNI_NIE
```

**Ursache:** Das Modell hat keine Muster mit variabler Interpunktion im synthetischen Training gesehen.

**Vorgeschlagene Lösung:** Regex-Vorverarbeitung zur Normalisierung `D.N.I.`, `N.I.F.`, `C.I.F.` → `DNI`, `NIF`, `CIF`.

---

### Fehler 2: Typverwechslung bei numerischen Sequenzen

**Muster:** Lange numerische Sequenzen werden als falscher Typ klassifiziert.

**Beispiel:**
```
Eingabe: "IBAN ES12 0049 1234 5012 3456 7890"
Erwartet: ES12 0049 1234 5012 3456 7890 → IBAN
Erkannt: ES12 0049 1234 5012 3456 7890 → NSS
```

**Ursache:** Überlappung numerischer Muster zwischen IBAN (24 Zeichen), NSS (12 Ziffern), CADASTRAL_REF (20 Zeichen).

**Vorgeschlagene Lösung:** Nachbearbeitung mit typspezifischer Formatvalidierung.

---

### Fehler 3: Falsch Positive in rechtlichen Referenzen

**Muster:** Zahlen im rechtlichen Kontext (Gesetze, Aktenzeichen, Protokolle) als PII erkannt.

**Beispiel:**
```
Eingabe: "Según la Ley 15/2022, de 12 de julio"
Erwartet: (keine Entitäten)
Erkannt: Ley 15/ → ECLI, 2022 → LICENSE_PLATE, de 12 de julio → ECLI
```

**Ursache:** Muster `\d+/\d{4}` und Daten erscheinen im rechtlichen Kontext, nicht als PII.

**Vorgeschlagene Lösung:** Nachbearbeitung zum Ausschluss von Mustern `Ley \d+/\d{4}`, `Real Decreto`, `expediente \d+`.

---

### Fehler 4: Anfälligkeit für OCR-Fehler

**Muster:** Typische OCR-Verwechslungen (l/I, 0/O, Leerzeichen) brechen die Erkennung.

**Beispiel:**
```
Eingabe: "DNl 12345678Z" (kleines l statt I)
Erwartet: 12345678Z → DNI_NIE
Erkannt: DN → CADASTRAL_REF, l 12345678 → NSS, Z → CADASTRAL_REF
```

**Ursache:** Das Modell wurde nur mit sauberem Text trainiert, nicht mit OCR-Varianten.

**Vorgeschlagene Lösung:** Vorverarbeitung mit OCR-Normalisierung:
- `DNl` → `DNI`
- `0` ↔ `O` im numerischen Kontext
- Leerzeichen in bekannten Mustern kollabieren

---

### Fehler 5: Kontextblindheit

**Muster:** Modell unterscheidet nicht zwischen illustrativen Erwähnungen und realen Daten.

**Beispiel:**
```
Eingabe: "El formato del DNI es 12345678X (ejemplo ilustrativo)"
Erwartet: (keine Entitäten - es ist ein Beispiel)
Erkannt: 12345678X → LICENSE_PLATE
```

**Ursache:** Modell hat keinen Zugriff auf semantischen Kontext ("Beispiel", "Format", "illustrativ").

**Vorgeschlagene Lösung:** Nachbearbeitung mit Kontexterkennung:
- Ausschließen, wenn "ejemplo", "formato", "ilustrativo" im Fenster von ±10 Token erscheint
- Erfordert ausgefeiltere Analyse (teilweise mit Regex lösbar)

---

### Fehler 6: Fiktive Entitäten erkannt

**Muster:** Literarische/fiktive Charaktere als reale Personen erkannt.

**Beispiel:**
```
Eingabe: "Como dijo Don Quijote de la Mancha"
Erwartet: (keine Entitäten - fiktiver Charakter)
Erkannt: Don Quijote de la Mancha → PERSON
```

**Ursache:** Modell hat keine Liste bekannter fiktiver Charaktere.

**Vorgeschlagene Lösung:** Nachbearbeitung mit Ausschluss-Gazetteer (fiktive Charaktere, historische Persönlichkeiten).

---

## Lösungsklassifizierung

### Lösbar mit Regex (Vorverarbeitung)

| Problem | Regex | Beispiel |
|----------|-------|---------|
| D.N.I. normalisieren | `D\.?\s*N\.?\s*I\.?` → `DNI` | `D.N.I.` → `DNI` |
| N.I.F. normalisieren | `N\.?\s*I\.?\s*F\.?` → `NIF` | `N.I.F.` → `NIF` |
| Leerzeichen in DNI kollabieren | `(\d)\s+(\d)` → `\1\2` | `12 345 678` → `12345678` |
| Fullwidth → ASCII | `[\uFF10-\uFF19]` → `[0-9]` | `１２３` → `123` |
| Zero-width entfernen | `[\u200b\u200c\u200d]` → `` | unsichtbar → entfernt |
| OCR l/I in DNI | `DN[lI1]` → `DNI` | `DNl` → `DNI` |
| OCR 0/O in IBAN | `[0O]` kontextuelle Normalisierung | `21O0` → `2100` |

### Lösbar mit Regex (Nachbearbeitung)

| Problem | Regex/Validierung | Aktion |
|----------|------------------|--------|
| Ley X/YYYY | `Ley\s+\d+/\d{4}` | Entität ausschließen, falls Match |
| Aktenzeichen | `expediente\s+\d+` | Entität ausschließen |
| Protokoll NÚMERO | `NÚMERO\s+[A-Z\s]+\.-` | Ausschließen, wenn als DATE erkannt |
| DNI-Prüfsumme | Prüfe Mod-23 Buchstabe | Ablehnen, wenn ungültig |
| IBAN-Prüfsumme | Prüfe Kontrollziffern | Ablehnen, wenn ungültig |
| NSS-Prüfsumme | Prüfe Mod-97 | Ablehnen, wenn ungültig |
| Kennzeichenformat | `\d{4}\s?[A-Z]{3}` | Ablehnen, wenn kein Match |
| Beispielkontext | `(ejemplo\|ilustrativo\|formato)` nahe | Entität ausschließen |

### Erfordert Modell/NLP (Nicht Regex)

| Problem | Benötigte Lösung |
|----------|-------------------|
| Fiktive Charaktere | Ausschluss-Gazetteer + spezifisches NER |
| OCR-Abschneidung ("Procur") | Bessere Tokenisierung oder robustes Modell |
| Tiefe semantische Ambiguität | Fine-Tuning mit negativen Beispielen |

---

## Schlussfolgerungen

### Stärken des Modells

1. **Saubere Muster:** 100% Genauigkeit in einfachen Tests mit Standardformat
2. **Zusammengesetzte Namen:** Erkennt korrekt lange adelige Namen ("José María de la Santísima Trinidad...")
3. **Einfache Negation:** Erkennt "NICHT DNI haben" und erkennt keine falsch positiven Ergebnisse
4. **ORG/PERSON Unterscheidung:** Unterscheidet "García y Asociados, S.L." als Organisation
5. **Orte mit Präfix:** "San Fernando del Valle" korrekt als LOCATION
6. **Partielle Unicode-Robustheit:** Widersteht Kyrillisch und Zero-Width Spaces

### Identifizierte Schwächen

1. **Overfitting auf synthetische Daten:** 99.87% F1 im Test → 45.7% im Adversarial
2. **Fragilität gegenüber OCR:** 80% Ausfall in der Kategorie ocr_corruption
3. **Explosion falsch positiver Ergebnisse:** In komplexen Texten werden 5-10 falsche Erkennungen generiert
4. **Numerische Typverwechslung:** IBAN ↔ NSS ↔ CADASTRAL_REF
5. **Kontextblindheit:** Unterscheidet nicht zwischen Beispielen, rechtlichen Referenzen, Fiktion

### Schlüsselmetriken

| Metrik | Wert | Ziel | Status |
|---------|-------|----------|--------|
| Synthetisches F1 | 99.87% | ≥85% | ✅ Bestanden |
| Adversarielles F1 (geschätzt) | ~45% | ≥70% | ❌ Nicht erreicht |
| Rate falsch positiver Ergebnisse | Hoch | Niedrig | ❌ Kritisch |
| OCR-Robustheit | 20% | ≥80% | ❌ Kritisch |

---

## Zukünftige Arbeit

### HOHE Priorität (Sofort implementieren)

1. **Pre/Post-Processing Pipeline**
   - Erstelle `scripts/inference/text_normalizer.py` (Vorverarbeitung)
   - Erstelle `scripts/inference/entity_validator.py` (Nachbearbeitung)
   - Integration in Inferenz-Pipeline

2. **Prüfsummenvalidierung**
   - DNI: Buchstabe = "TRWAGMYFPDXBNJZSQVHLCKE"[Zahl % 23]
   - IBAN: Gültige Kontrollziffern
   - NSS: Mod-97 Validierung

3. **Ausschluss-Gazetteers**
   - Bekannte fiktive Charaktere
   - Rechtliche Muster (Ley, RD, Aktenzeichen)

### MITTLERE Priorität (Nächste Iteration)

4. **Datenerweiterung**
   - Beispiele mit OCR-Fehlern zum Datensatz hinzufügen
   - Negative Beispiele hinzufügen (Zahlen, die KEINE PII sind)
   - "Illustrative Beispiel"-Kontexte hinzufügen

5. **Nachtraining**
   - Mit erweitertem Datensatz
   - Evaluierung CRF-Layer (+4-13% F1 laut Literatur)

### NIEDRIGE Priorität (Zukunft)

6. **Annotierte reale Daten**
   - Erhalte echte anonymisierte Rechtsdokumente
   - Manuelle Gold-Standard-Annotation

---

## Referenzen

1. **Basis-Modell:** PlanTL-GOB-ES/roberta-base-bne-capitel-ner
2. **Adversarielle Methodik:** Projektrichtlinien, Abschnitt 4 (Adversarial Testing)
3. **DNI-Validierung:** BOE - NIF-Buchstaben-Algorithmus
4. **IBAN-Validierung:** ISO 13616 - International Bank Account Number
5. **seqeval:** NER-Evaluierungs-Framework (entity-level)

---

**Generiert von:** `scripts/adversarial/evaluate_adversarial.py`
**Datum:** 2026-01-20
**Version:** 1.0
