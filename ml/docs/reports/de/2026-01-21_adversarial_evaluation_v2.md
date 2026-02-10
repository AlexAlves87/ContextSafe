# Adversarielle Evaluierung - Spanisches Rechts-NER

**Datum:** 2026-01-21
**Modell:** legal_ner_v2
**Tests:** 35

---

## Zusammenfassung

| Metrik | Wert |
|---------|-------|
| Gesamttests | 35 |
| Bestanden | 19 (54.3%) |
| Fehlgeschlagen | 16 (45.7%) |

### Nach Kategorie

| Kategorie | Bestanden | Gesamt | Rate |
|-----------|---------|-------|------|
| adversarial | 5 | 8 | 62.5% |
| edge_case | 6 | 9 | 66.7% |
| ocr_corruption | 2 | 5 | 40.0% |
| real_world | 5 | 10 | 50.0% |
| unicode_evasion | 1 | 3 | 33.3% |

### Nach Schwierigkeit

| Schwierigkeit | Bestanden | Gesamt | Rate |
|------------|---------|-------|------|
| easy | 4 | 4 | 100.0% |
| medium | 9 | 12 | 75.0% |
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

**Erkannt (3):**
- `12` → DNI_NIE
- `3` → NSS
- `45 678 Z` → DNI_NIE

**Ergebnis:** 1 richtig, 0 verpasst, 2 falsch positiv

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
- `ES91 2100 0418 4502 000` → IBAN
- `5 1332` → CADASTRAL_REF

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
- `+34 612 345 678` → PHONE

**Ergebnis:** 1 richtig, 1 verpasst, 0 falsch positiv

**Notizen:** Internationale Telefonformate

---

#### date_roman_numerals [FAIL]

**Schwierigkeit:** hard

**Text:**
```
Otorgado el día XV de marzo del año MMXXIV.
```

**Erwartet (1):**
- `XV de marzo del año MMXXIV` → DATE

**Erkannt (0):**
- (keine Entitäten)

**Ergebnis:** 0 richtig, 1 verpasst, 0 falsch positiv

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

**Erkannt (2):**
- `El` → DATE
- `primero de enero de dos mil veinticuatro` → DATE

**Ergebnis:** 1 richtig, 0 verpasst, 1 falsch positiv

**Notizen:** Vollständig ausgeschriebenes Datum

---

#### address_floor_door [PASS]

**Schwierigkeit:** medium

**Text:**
```
Domicilio en Calle Mayor 15, 3º B, 28001 Madrid.
```

**Erwartet (3):**
- `Calle Mayor 15, 3º B` → ADDRESS
- `28001` → POSTAL_CODE
- `Madrid` → LOCATION

**Erkannt (3):**
- `Calle Mayor 15, 3º B` → ADDRESS
- `28` → POSTAL_CODE
- `Madrid` → LOCATION

**Ergebnis:** 3 richtig, 0 verpasst, 0 falsch positiv

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
- `12345678X` → DNI_NIE

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

**Erkannt (5):**
- `Ley` → ECLI
- `15` → PROFESSIONAL_ID
- `/` → ECLI
- `2022` → PROFESSIONAL_ID
- `,` → ECLI

**Ergebnis:** 0 richtig, 0 verpasst, 5 falsch positiv

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

**Erkannt (1):**
- `12345678` → PROFESSIONAL_ID

**Ergebnis:** 0 richtig, 0 verpasst, 1 falsch positiv

**Notizen:** 8-stellige Nummer, die KEIN DNI ist (Aktenzeichen)

---

#### mixed_languages [PASS]

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
- `UK123456789` → DNI_NIE
- `Madrid` → LOCATION

**Ergebnis:** 3 richtig, 0 verpasst, 0 falsch positiv

**Notizen:** Englischer Name und ausländischer Pass

---

### OCR CORRUPTION

#### ocr_letter_substitution [PASS]

**Schwierigkeit:** medium

**Text:**
```
DNl 12345678Z perteneciente a María García.
```

**Erwartet (2):**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Erkannt (2):**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Ergebnis:** 2 richtig, 0 verpasst, 0 falsch positiv

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

**Erkannt (0):**
- (keine Entitäten)

**Ergebnis:** 0 richtig, 1 verpasst, 0 falsch positiv

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

**Erkannt (1):**
- `DonJoséGarcíaLópezcon` → PERSON

**Ergebnis:** 1 richtig, 1 verpasst, 0 falsch positiv

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

**Erkannt (0):**
- (keine Entitäten)

**Ergebnis:** 0 richtig, 2 verpasst, 0 falsch positiv

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
- `12345678` → DNI_NIE
- `María` → PERSON

**Ergebnis:** 2 richtig, 0 verpasst, 0 falsch positiv

**Notizen:** Kyrillisches Х (U+0425) anstelle von Lateinischem X

---

#### zero_width_space [FAIL]

**Schwierigkeit:** hard

**Text:**
```
DNI 123​456​78Z de María García.
```

**Erwartet (2):**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Erkannt (3):**
- `123​456​78Z` → DNI_NIE
- `de` → PERSON
- `María García` → PERSON

**Ergebnis:** 2 richtig, 0 verpasst, 1 falsch positiv

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

**Erkannt (0):**
- (keine Entitäten)

**Ergebnis:** 0 richtig, 2 verpasst, 0 falsch positiv

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

**Erkannt (3):**
- `Sevilla` → LOCATION
- `JOSÉ GARCÍA LÓPEZ` → PERSON
- `Sevilla` → LOCATION

**Ergebnis:** 3 richtig, 1 verpasst, 0 falsch positiv

**Notizen:** Standardmäßiger notarieller Urkundenkopf

---

#### testament_comparecencia [PASS]

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

**Erkannt (5):**
- `Doña MARÍA ANTONIA FERNÁNDEZ RUIZ` → PERSON
- `Córdoba` → LOCATION
- `Madrid` → LOCATION
- `Calle Alcalá número 123, piso 4º, puerta B,` → ADDRESS
- `12345678-Z` → DNI_NIE

**Ergebnis:** 5 richtig, 0 verpasst, 0 falsch positiv

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

**Erkannt (5):**
- `Nº 123/2024` → PROFESSIONAL_ID
- `Madrid` → LOCATION
- `Sala Primera del Tribunal Supremo` → ORGANIZATION
- `D. ANTONIO PÉREZ MARTÍNEZ` → PERSON
- `D. CARLOS SÁNCHEZ GÓMEZ` → PERSON

**Ergebnis:** 3 richtig, 1 verpasst, 2 falsch positiv

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

**Erkannt (2):**
- `IBAN ES12 0049 1234 5012 3456 7890` → IBAN
- `CONSTRUCCIONES PÉREZ, S.A.,` → ORGANIZATION

**Ergebnis:** 2 richtig, 1 verpasst, 0 falsch positiv

**Notizen:** Banküberweisungsklausel

---

#### cadastral_reference [PASS]

**Schwierigkeit:** medium

**Text:**
```
Finca registral número 12345 del Registro de la Propiedad de Málaga, con referencia catastral 1234567AB1234S0001AB.
```

**Erwartet (2):**
- `Málaga` → LOCATION
- `1234567AB1234S0001AB` → CADASTRAL_REF

**Erkannt (2):**
- `Málaga` → LOCATION
- `1234567AB1234S0001AB` → CADASTRAL_REF

**Ergebnis:** 2 richtig, 0 verpasst, 0 falsch positiv

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

**Erkannt (2):**
- `Abogado D. LUIS SÁNCHEZ` → PERSON
- `Colegio de Procuradores de Madrid` → ORGANIZATION

**Ergebnis:** 1 richtig, 3 verpasst, 1 falsch positiv

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

**Erkannt (3):**
- `Tribunal Supremo` → ORGANIZATION
- `(ECLI:ES:TS:2023:1234),` → ECLI
- `ECLI:ES:AN:2024:567` → ECLI

**Ergebnis:** 2 richtig, 0 verpasst, 1 falsch positiv

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
- `matrícula 1234 ABC` → LICENSE_PLATE
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

**Erkannt (2):**
- `28` → DNI_NIE
- `1234567890` → NSS

**Ergebnis:** 1 richtig, 0 verpasst, 1 falsch positiv

**Notizen:** Sozialversicherungsnummer im Beschäftigungskontext

---


## Schlussfolgerungen

### Stärken des Modells

(Analysieren Sie bestandene Tests und Muster)

### Identifizierte Schwächen

(Analysieren Sie fehlgeschlagene Tests und Muster)

### Empfehlungen

1. (Basierend auf den Ergebnissen)

---

**Automatisch generiert von:** `scripts/adversarial/evaluate_adversarial.py`
