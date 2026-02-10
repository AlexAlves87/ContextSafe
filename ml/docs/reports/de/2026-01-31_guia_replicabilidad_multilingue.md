# Reproduzierbarkeits-Leitfaden: Multilinguale NER-PII-Pipeline

**Datum:** 31.01.2026
**Autor:** AlexAlves87
**Projekt:** ContextSafe ML - Multilinguale Expansion
**Version:** 1.0.0

---

## 1. Management-Zusammenfassung

Dieses Dokument beschreibt, wie die hybride NER-PII-Pipeline von ContextSafe (Spanisch Legal, F1 0.788) für andere europäische Sprachen repliziert werden kann. Der Ansatz ist **modular**: Jede Komponente wird an die Zielsprache angepasst, während die bewährte Architektur beibehalten wird.

### Gelernte Lektion (LoRA-Experiment)

| Ansatz | Adversarial F1 | Urteil |
|--------|----------------|--------|
| Reines LoRA-Fine-Tuning | 0.016 | ❌ Schweres Overfitting |
| Hybride Pipeline (5 Elemente) | **0.788** | ✅ Generalisiert gut |

> **Schlussfolgerung:** Das Fine-Tuning von Transformern ohne die hybride Pipeline generalisiert nicht auf adversarische Fälle. Die 5 Elemente der Nachbearbeitung sind **essenziell**.

---

## 2. Pipeline-Architektur (Sprachunabhängig)

```
┌─────────────────────────────────────────────────────────────────┐
│                     HYBRIDE NER-PII PIPELINE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Eingabetext                                                     │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [1] TextNormalizer                     │ ← Sprachunabhängig   │
│  │     - Unicode NFKC                     │                      │
│  │     - Homoglypghen (Kyrillisch→Latein) │                      │
│  │     - Entfernung von Nullbreiten       │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [NER] Transformer LegalBERT            │ ← ANPASSUNG PRO SPRACHE │
│  │     - ES: RoBERTa-BNE CAPITEL NER      │                      │
│  │     - EN: Legal-BERT                   │                      │
│  │     - FR: JuriBERT                     │                      │
│  │     - IT: Italian-Legal-BERT           │                      │
│  │     - PT: Legal-BERTimbau              │                      │
│  │     - DE: German-Legal-BERT            │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [2] Checksum Validators                │ ← ANPASSUNG PRO LAND │
│  │     - Verifizierungsalgorithmen        │                      │
│  │     - Konfidenzanpassung               │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [3] Regex Patterns                     │ ← ANPASSUNG PRO LAND │
│  │     - Nationale IDs                    │                      │
│  │     - Formate mit Leerzeichen/Bindestr.│                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [4] Date Patterns                      │ ← ANPASSUNG PRO SPRACHE │
│  │     - Monate in lokaler Sprache        │                      │
│  │     - Rechtliche/notarielle Formate    │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [5] Boundary Refinement                │ ← ANPASSUNG PRO SPRACHE │
│  │     - Höflichkeitspräfixe              │                      │
│  │     - Organisationssuffixe             │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  Finale Entitäten                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Komponenten nach Anpassungstyp

| Komponente | Anpassung | Aufwand |
|------------|-----------|---------|
| TextNormalizer | Keine (universell) | 0 |
| Transformer NER | Basismodell ändern | Gering |
| Checksum Validators | Algorithmen pro Land | Mittel |
| Regex Patterns | Muster pro Land | Hoch |
| Date Patterns | Monate/Formate pro Sprache | Mittel |
| Boundary Refinement | Präfixe/Suffixe pro Sprache | Mittel |

---

## 3. Empfohlene Basismodelle pro Sprache

### 3.1 Monolinguale Modelle (Maximale Leistung)

| Sprache | Modell | HuggingFace | Params | Korpus |
|---------|--------|-------------|--------|--------|
| 🇪🇸 Spanisch | RoBERTa-BNE CAPITEL NER | `PlanTL-GOB-ES/roberta-base-bne-capitel-ner` | 125M | BNE + CAPITEL NER |
| 🇬🇧 Englisch | Legal-BERT | `nlpaueb/legal-bert-base-uncased` | 110M | 12GB Legal |
| 🇫🇷 Französisch | JuriBERT | `dascim/juribert-base` | 110M | Légifrance |
| 🇮🇹 Italienisch | Italian-Legal-BERT | `dlicari/Italian-Legal-BERT` | 110M | Giurisprudenza |
| 🇵🇹 Portugiesisch | Legal-BERTimbau | `rufimelo/Legal-BERTimbau-base` | 110M | 30K Doks |
| 🇩🇪 Deutsch | German-Legal-BERT | `elenanereiss/bert-german-legal` | 110M | Bundesrecht |

### 3.2 Multilinguales Modell (Schnelle Bereitstellung)

| Modell | HuggingFace | Params | Sprachen |
|--------|-------------|--------|----------|
| Legal-XLM-RoBERTa | `joelniklaus/legal-xlm-roberta-large` | 355M | 24 Sprachen |

**Abwägung:**
- Monolingual: +2-5% F1, erfordert Modell pro Sprache
- Multilingual: Ein einziges Modell, etwas geringere Leistung

---

## 4. Anpassungen pro Land

### 4.1 Spanien (Implementiert ✅)

#### Nationale Identifikatoren

| Typ | Format | Checksumme | Regex |
|-----|--------|------------|-------|
| DNI | 8 Ziffern + Buchstabe | mod 23 | `\d{8}[A-Z]` |
| NIE | X/Y/Z + 7 Ziffern + Buchst. | mod 23 | `[XYZ]\d{7}[A-Z]` |
| CIF | Buchstabe + 7 Ziff. + Kontr. | Summe gerade/ungerade | `[A-W]\d{7}[0-9A-J]` |
| IBAN | ES + 22 Zeichen | ISO 13616 mod 97 | `ES\d{2}[\d\s]{20}` |
| NSS | 12 Ziffern | mod 97 | `\d{12}` |
| Kennzeichen | 4 Ziffern + 3 Buchstaben | keine | `\d{4}[BCDFGHJKLMNPRSTVWXYZ]{3}` |

#### Höflichkeitspräfixe

```python
PREFIXES_ES = [
    "Don", "Doña", "D.", "Dña.", "D.ª",
    "Sr.", "Sra.", "Srta.",
    "Ilmo.", "Ilma.", "Excmo.", "Excma.",
]
```

#### Monate

```python
MONTHS_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]
```

---

### 4.2 Frankreich 🇫🇷

#### Nationale Identifikatoren

| Typ | Format | Checksumme | Regex |
|-----|--------|------------|-------|
| NIR (Sécu) | 15 Ziffern | mod 97 | `[12]\d{2}(0[1-9]|1[0-2])\d{2}\d{3}\d{3}\d{2}` |
| SIRET | 14 Ziffern | Luhn | `\d{14}` |
| SIREN | 9 Ziffern | Luhn | `\d{9}` |
| IBAN | FR + 25 Zeichen | ISO 13616 | `FR\d{2}[\d\s]{23}` |
| Carte ID | 12 Zeichen | keine | `[A-Z0-9]{12}` |

#### Höflichkeitspräfixe

```python
PREFIXES_FR = [
    "Monsieur", "Madame", "Mademoiselle",
    "M.", "Mme", "Mlle",
    "Maître", "Me", "Me.",
    "Docteur", "Dr", "Dr.",
]
```

#### Monate

```python
MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
]
```

#### Organisationssuffixe

```python
ORG_SUFFIXES_FR = [
    "S.A.", "SA", "S.A.S.", "SAS", "S.A.R.L.", "SARL",
    "S.C.I.", "SCI", "E.U.R.L.", "EURL", "S.N.C.", "SNC",
]
```

---

### 4.3 Italien 🇮🇹

#### Nationale Identifikatoren

| Typ | Format | Checksumme | Regex |
|-----|--------|------------|-------|
| Codice Fiscale | 16 Zeichen | mod 26 spezial | `[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]` |
| Partita IVA | 11 Ziffern | Luhn Variante | `\d{11}` |
| IBAN | IT + 25 Zeichen | ISO 13616 | `IT\d{2}[A-Z][\d\s]{22}` |
| Carta Identità | 2 Buchstaben + 7 Ziffern | keine | `[A-Z]{2}\d{7}` |

#### Checksumme Codice Fiscale

```python
def validate_codice_fiscale(cf: str) -> bool:
    """Mod 26 Algorithmus mit speziellen Werten für gerade/ungerade Positionen."""
    ODD_VALUES = {'0': 1, '1': 0, '2': 5, ...}  # Volle Tabelle
    EVEN_VALUES = {'0': 0, '1': 1, '2': 2, ...}
    # Summiere ungerade Positionen mit ODD_VALUES, gerade mit EVEN_VALUES
    # Kontrollbuchstabe = chr(ord('A') + total % 26)
```

#### Höflichkeitspräfixe

```python
PREFIXES_IT = [
    "Signor", "Signora", "Signorina",
    "Sig.", "Sig.ra", "Sig.na",
    "Dott.", "Dott.ssa", "Avv.", "Ing.",
    "On.", "Sen.", "Onorevole",
]
```

#### Monate

```python
MONTHS_IT = [
    "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"
]
```

---

### 4.4 Portugal 🇵🇹

#### Nationale Identifikatoren

| Typ | Format | Checksumme | Regex |
|-----|--------|------------|-------|
| NIF | 9 Ziffern | mod 11 | `[123568]\d{8}` |
| CC (Cartão Cidadão) | 8 Ziff. + 1 Buchst. + 2 Ziff. | mod 11 + Buchstabe | `\d{8}[A-Z]\d{2}` |
| NISS | 11 Ziffern | mod 10 | `\d{11}` |
| IBAN | PT + 23 Zeichen | ISO 13616 | `PT\d{2}[\d\s]{21}` |

#### Checksumme NIF Portugal

```python
def validate_nif_pt(nif: str) -> bool:
    """Mod 11 Algorithmus mit abnehmenden Gewichten."""
    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(d) * w for d, w in zip(nif[:8], weights))
    control = 11 - (total % 11)
    if control >= 10:
        control = 0
    return int(nif[8]) == control
```

#### Höflichkeitspräfixe

```python
PREFIXES_PT = [
    "Senhor", "Senhora", "Sr.", "Sra.", "Srª",
    "Dom", "Dona", "D.",
    "Doutor", "Doutora", "Dr.", "Dra.",
    "Exmo.", "Exma.",
]
```

---

### 4.5 Deutschland 🇩🇪

#### Nationale Identifikatoren

| Typ | Format | Checksumme | Regex |
|-----|--------|------------|-------|
| Steuer-ID | 11 Ziffern | ISO 7064 mod 11-10 | `\d{11}` |
| Personalausweis | 10 Zeichen | mod 10 spezial | `[A-Z0-9]{10}` |
| IBAN | DE + 20 Zeichen | ISO 13616 | `DE\d{2}[\d\s]{18}` |
| Handelsregister | HRA/HRB + Nummer | keine | `HR[AB]\s?\d+` |

#### Höflichkeitspräfixe

```python
PREFIXES_DE = [
    "Herr", "Frau",
    "Dr.", "Prof.", "Prof. Dr.",
    "Rechtsanwalt", "RA", "Notar",
]
```

#### Monate

```python
MONTHS_DE = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember"
]
```

---

### 4.6 Vereinigtes Königreich 🇬🇧

#### Nationale Identifikatoren

| Typ | Format | Checksumme | Regex |
|-----|--------|------------|-------|
| NI Number | 2 Buchst. + 6 Ziff. + Buchst. | nicht verifizierbar | `[A-Z]{2}\d{6}[A-D]` |
| Company Number | 8 Zeichen | keine | `[A-Z]{2}\d{6}|[\d]{8}` |
| IBAN | GB + 22 Zeichen | ISO 13616 | `GB\d{2}[A-Z]{4}[\d\s]{14}` |
| Reisepass | 9 Ziffern | keine | `\d{9}` |

#### Höflichkeitspräfixe

```python
PREFIXES_EN = [
    "Mr", "Mr.", "Mrs", "Mrs.", "Ms", "Ms.", "Miss",
    "Dr", "Dr.", "Prof", "Prof.",
    "Sir", "Dame", "Lord", "Lady",
    "The Honourable", "Hon.",
]
```

---

## 5. Implementierungs-Checkliste pro Sprache

### Phase 1: Vorbereitung (1-2 Tage)

- [ ] **Basismodell auswählen** aus Tabelle 3.1
- [ ] **Modell herunterladen** nach `models/pretrained/{modell}/`
- [ ] **Laden verifizieren** mit Testskript
- [ ] **PII-Kategorien definieren** relevant für das Land

### Phase 2: Checksum Validators (2-3 Tage)

- [ ] **Validierungsalgorithmen recherchieren** für das Land
- [ ] **Validators implementieren** in `scripts/preprocess/{country}_validators.py`
- [ ] **Unit-Tests erstellen** (mindestens 20 Fälle pro Typ)
- [ ] **Algorithmen dokumentieren** mit offiziellen Referenzen

### Phase 3: Regex Patterns (3-5 Tage)

- [ ] **Offizielle Formate sammeln** von IDs des Landes
- [ ] **Muster implementieren** in `scripts/preprocess/{country}_id_patterns.py`
- [ ] **Varianten einschließen** mit Leerzeichen, Bindestrichen, Punkten
- [ ] **Tests mit echten Beispielen** (anonymisiert)

### Phase 4: Date Patterns (1-2 Tage)

- [ ] **Monate übersetzen** in Zielsprache
- [ ] **Formate anpassen** lokal rechtlich/notariell
- [ ] **Implementieren** in `scripts/preprocess/{country}_date_patterns.py`
- [ ] **Tests mit echten Daten** aus juristischen Dokumenten

### Phase 5: Boundary Refinement (1-2 Tage)

- [ ] **Liste zusammenstellen** von Höflichkeitspräfixen
- [ ] **Liste zusammenstellen** von Organisationssuffixen
- [ ] **Implementieren** in `scripts/preprocess/{country}_boundary_refinement.py`
- [ ] **Tests mit echten Namen/Orgs**

### Phase 6: Gazetteers (2-4 Tage)

- [ ] Häufige **Vornamen** (Äquivalent zu INE)
- [ ] Häufige **Nachnamen**
- [ ] **Gemeinden/Städte**
- [ ] Bekannte **Organisationen** (Unternehmen, Institutionen)

### Phase 7: Adversarial Test Set (2-3 Tage)

- [ ] **30-40 Fälle erstellen** spezifisch für die Sprache:
  - Edge Cases (ungewöhnliche Formate)
  - Adversarial (Verneinungen, Beispiele, Fiktion)
  - OCR-Fehler
  - Unicode-Evasion (bereits abgedeckt)
  - Real World (typische juristische Dokumente)
- [ ] **Erwartete Entitäten definieren** für jeden Fall
- [ ] **SemEval-Evaluierung ausführen**

### Phase 8: Integration (1-2 Tage)

- [ ] **Komponenten integrieren** in `ner_predictor_{lang}.py`
- [ ] **Adversarial Test Set ausführen**
- [ ] **Anpassen** bis F1 ≥ 0.70
- [ ] **Ergebnisse dokumentieren**

---

## 6. Gesamtaufwandsschätzung

| Sprache | Modell | ID-Komplexität | Gesch. Aufwand |
|---------|--------|----------------|----------------|
| 🇫🇷 Französisch | JuriBERT | Mittel (NIR, SIRET) | 2-3 Wochen |
| 🇮🇹 Italienisch | Italian-Legal-BERT | Hoch (Codice Fiscale) | 3-4 Wochen |
| 🇵🇹 Portugiesisch | Legal-BERTimbau | Mittel (NIF, CC) | 2-3 Wochen |
| 🇩🇪 Deutsch | German-Legal-BERT | Mittel (Steuer-ID) | 2-3 Wochen |
| 🇬🇧 Englisch | Legal-BERT | Niedrig (NI Number) | 1-2 Wochen |

**Gesamt für 5 Sprachen:** 10-15 Wochen (1 Entwickler)
**Mit Parallelisierung (2-3 Devs):** 4-6 Wochen

---

## 7. Dateistruktur pro Sprache

```
ml/
├── scripts/
│   ├── preprocess/
│   │   ├── spanish_id_patterns.py      # ✅ Implementiert
│   │   ├── spanish_date_patterns.py    # ✅ Implementiert
│   │   ├── boundary_refinement.py      # ✅ Implementiert (anpassen)
│   │   │
│   │   ├── french_id_patterns.py       # Zu implementieren
│   │   ├── french_date_patterns.py
│   │   ├── french_validators.py
│   │   │
│   │   ├── italian_id_patterns.py      # Zu implementieren
│   │   ├── italian_date_patterns.py
│   │   ├── italian_validators.py
│   │   │
│   │   └── ... (pro Sprache)
│   │
│   ├── inference/
│   │   ├── ner_predictor.py            # ✅ Spanisch
│   │   ├── ner_predictor_fr.py         # Zu implementieren
│   │   ├── ner_predictor_it.py
│   │   └── ...
│   │
│   └── evaluate/
│       ├── test_ner_predictor_adversarial_v2.py  # ✅ Spanisch
│       ├── adversarial_tests_fr.py               # Zu implementieren
│       └── ...
│
├── gazetteers/
│   ├── es/                             # ✅ Implementiert
│   │   ├── nombres.json
│   │   ├── apellidos.json
│   │   └── municipios.json
│   │
│   ├── fr/                             # Zu implementieren
│   ├── it/
│   ├── pt/
│   ├── de/
│   └── en/
│
└── models/
    └── pretrained/
        ├── legal-xlm-roberta-base/     # ✅ Heruntergeladen
        ├── juribert-base/              # Herunterzuladen
        ├── italian-legal-bert/
        └── ...
```

---

## 8. Referenzen

### 8.1 Papers und Dokumentation

| Ressource | URL | Verwendung |
|-----------|-----|------------|
| Legal-BERT Paper | aclanthology.org/2020.findings-emnlp.261 | Architektur |
| JuriBERT Paper | aclanthology.org/2021.nllp-1.9 | Französisch Legal |
| SemEval 2013 Task 9 | aclweb.org/anthology/S13-2013 | Evaluierungsmetriken |
| ISO 13616 (IBAN) | iso.org/standard/81090.html | IBAN Checksumme |

### 8.2 Gazetteer-Quellen pro Land

| Land | Namen | Gemeinden | IDs |
|------|-------|-----------|-----|
| 🇪🇸 Spanien | INE | INE | BOE |
| 🇫🇷 Frankreich | INSEE | INSEE | Légifrance |
| 🇮🇹 Italien | ISTAT | ISTAT | Normattiva |
| 🇵🇹 Portugal | INE-PT | INE-PT | DRE |
| 🇩🇪 Deutschland | Statistisches Bundesamt | - | Bundesrecht |
| 🇬🇧 UK | ONS | ONS | legislation.gov.uk |

---

## 9. Gelernte Lektionen (ContextSafe ES)

### 9.1 Was funktioniert hat

1.  **Hybride Pipeline > Reines ML**: Transformer allein generalisieren nicht auf adversarische Fälle
2.  **Regex für variable Formate**: DNI mit Leerzeichen, IBAN mit Gruppen
3.  **Checksummen-Validierung**: Reduziert False Positives signifikant
4.  **Boundary Refinement**: Konvertiert PAR→COR (16 Fälle korrigiert)
5.  **Adversarial Test Set**: Erkennt Probleme vor der Produktion

### 9.2 Was NICHT funktioniert hat

1.  **LoRA Fine-Tuning ohne Pipeline**: 0.016 F1 bei Adversarial (Overfitting)
2.  **GLiNER Zero-Shot**: 0.325 F1 (kennt keine spanischen Formate)
3.  **Verlassen nur auf Dev-Set-Metriken**: 0.989 Dev vs 0.016 Adversarial

### 9.3 Empfehlungen

1.  **Immer Adversarial Test Set erstellen** bevor "fertig" erklärt wird
2.  **Checksummen-Validatoren implementieren** für alle IDs mit mathematischer Verifizierung
3.  **In Qualitäts-Gazetteers investieren** (Namen, Gemeinden)
4.  **Jedes Element dokumentieren** mit Standalone-Tests

---

## 10. Nächste Schritte

1.  **Sprache priorisieren** nach Marktnachfrage
2.  **Basismodell herunterladen** der ausgewählten Sprache
3.  **Komponenten anpassen** gemäß dieser Checkliste
4.  **Spezifisches Adversarial Test Set erstellen**
5.  **Iterieren bis F1 ≥ 0.70** bei Adversarial

---

**Generiert von:** AlexAlves87
**Datum:** 31.01.2026
**Version:** 1.0.0
