# Baseline Adversarial Analyse: legal_ner_v2

**Datum:** 2026-01-23
**Autor:** AlexAlves87
**Version:** 1.0.0
**Evaluiertes Modell:** `legal_ner_v2` (RoBERTalex fine-tuned)

---

## 1. Zusammenfassung

Dieses Dokument präsentiert die Ergebnisse der Baseline-Evaluierung des `legal_ner_v2`-Modells zur PII-Erkennung in spanischen Rechtstexten. Ziel ist es, eine Robustheits-Baseline vor der Implementierung von Verbesserungen zu etablieren.

### Haupterkenntnisse

| Metrik | Wert | Interpretation |
|---------|-------|----------------|
| F1-Score (Entity-Level) | **0.784** | Akzeptable Baseline |
| Präzision | 0.845 | Konservatives Modell |
| Recall | 0.731 | Prioritärer Verbesserungsbereich |
| Rausch-Degradation | 0.080 | Innerhalb der erwarteten Schwelle (≤0.10) |
| Test-Pass-Rate | 54.3% (19/35) | Level 4 nicht bestanden |

### Schlussfolgerung

Das Modell **besteht NICHT** die Level-4-Validierung (adversarial). Verbesserungen sind erforderlich in:
1. Input-Normalisierung (Unicode, Leerzeichen)
2. Erkennung spanischer textueller Datumsformate
3. Spezifische Muster für NSS und CIF

---

## 2. Methodik

### 2.1 Experimentelles Design

Es wurden 35 adversariale Testfälle entworfen, verteilt auf 5 Kategorien:

| Kategorie | Tests | Zweck |
|-----------|-------|-----------|
| `edge_case` | 9 | Randbedingungen (lange Namen, Variantenformate) |
| `adversarial` | 8 | Fälle zur Verwirrung (Negationen, Beispiele) |
| `ocr_corruption` | 5 | Simulation von OCR-Fehlern |
| `unicode_evasion` | 3 | Umgehungsversuche mit ähnlichen Zeichen |
| `real_world` | 10 | Auszüge aus echten Rechtsdokumenten |

### 2.2 Schwierigkeitsgrade

| Level | Erfolgskriterien | Tests |
|-------|-------------------|-------|
| `easy` | Alle erwarteten Entitäten erkennen | 4 |
| `medium` | Alle erwarteten Entitäten erkennen | 12 |
| `hard` | Alle Entitäten erkennen UND null False Positives | 19 |

### 2.3 Verwendete Metriken

1. **Entity-Level F1** (seqeval-Stil): Präzision, Recall, F1 berechnet auf voller Entitätsebene, nicht Token.

2. **Overlap Score**: Verhältnis übereinstimmender Zeichen zwischen erwarteter und erkannter Entität (Jaccard über Zeichen).

3. **Rausch-Degradation** (NoiseBench-Stil): F1-Differenz zwischen "sauberen" Kategorien (`edge_case`, `adversarial`, `real_world`) und "verrauschten" (`ocr_corruption`, `unicode_evasion`).

### 2.4 Ausführungsumgebung

| Komponente | Spezifikation |
|------------|----------------|
| Hardware | CUDA (GPU) |
| Modell | `legal_ner_v2` (RoBERTalex) |
| Framework | PyTorch 2.0+, Transformers |
| Ladezeit | 1.6s |
| Evaluierungszeit | 1.5s (35 Tests) |

### 2.5 Reproduzierbarkeit

```bash
cd ml
source .venv/bin/activate
python scripts/evaluate/test_ner_predictor_adversarial.py
```

Das Skript generiert automatisch einen Bericht in `docs/reports/`.

---

## 3. Ergebnisse

### 3.1 Aggregierte Metriken

| Metrik | Wert |
|---------|-------|
| True Positives | 49 |
| False Positives | 9 |
| False Negatives | 18 |
| **Präzision** | 0.845 |
| **Recall** | 0.731 |
| **F1-Score** | 0.784 |
| Mean Overlap Score | 0.935 |

### 3.2 Ergebnisse nach Kategorie

| Kategorie | Pass Rate | TP | FP | FN | F1 |
|-----------|-----------|----|----|----|----|
| adversarial | 75.0% | 5 | 2 | 0 | 0.833 |
| edge_case | 66.7% | 9 | 1 | 3 | 0.818 |
| ocr_corruption | 40.0% | 5 | 0 | 4 | 0.714 |
| real_world | 40.0% | 26 | 5 | 9 | 0.788 |
| unicode_evasion | 33.3% | 4 | 1 | 2 | 0.727 |

### 3.3 Ergebnisse nach Schwierigkeit

| Schwierigkeit | Bestanden | Gesamt | Rate |
|------------|---------|-------|------|
| easy | 3 | 4 | 75.0% |
| medium | 9 | 12 | 75.0% |
| hard | 7 | 19 | 36.8% |

### 3.4 Analyse der Rauschresistenz

| Metrik | Wert | Referenz |
|---------|-------|------------|
| F1 (sauberer Text) | 0.800 | - |
| F1 (verrauscht) | 0.720 | - |
| **Degradation** | 0.080 | ≤0.10 (HAL Science) |
| Status | **OK** | Innerhalb der Schwelle |

---

## 4. Fehleranalyse

### 4.1 Fehlertaxonomie

Es wurden 5 wiederkehrende Fehlermuster identifiziert:

#### Muster 1: Datum im spanischen Textformat

| Test | Verpasste Entität |
|------|-----------------|
| `date_roman_numerals` | "XV de marzo del año MMXXIV" |
| `notarial_header` | "quince de marzo de dos mil veinticuatro" |
| `judicial_sentence_header` | "diez de enero de dos mil veinticuatro" |

**Ursache:** Das Modell wurde hauptsächlich mit numerischen Datumsformaten (DD/MM/YYYY) trainiert. Spanische notarielle Daten sind im Trainingskorpus nicht vertreten.

**Auswirkung:** Hoch in notariellen und gerichtlichen Dokumenten, wo dieses Format Standard ist.

#### Muster 2: Extreme OCR-Korruption

| Test | Verpasste Entität |
|------|-----------------|
| `ocr_extra_spaces` | "1 2 3 4 5 6 7 8 Z", "M a r í a" |
| `ocr_missing_spaces` | "12345678X" (in verkettetem Text) |
| `ocr_zero_o_confusion` | "ES91 21O0 0418 45O2 OOO5 1332" |

**Ursache:** Der Tokenizer von RoBERTa kommt mit anomalen Abständen nicht gut zurecht. O/0-Verwechslung bricht IBAN-Regex-Muster.

**Auswirkung:** Mittel. Gescannte Dokumente schlechter Qualität.

#### Muster 3: Unicode Evasion

| Test | Verpasste Entität |
|------|-----------------|
| `fullwidth_numbers` | "１２３４５６７８Z" (U+FF11-U+FF18) |

**Ursache:** Keine Unicode-Normalisierung vor NER. Fullwidth-Ziffern (U+FF10-U+FF19) werden nicht als Zahlen erkannt.

**Auswirkung:** Gering in Produktion, aber kritisch für Sicherheit (absichtliche Umgehung).

#### Muster 4: Spezifische spanische Identifikatoren

| Test | Verpasste Entität |
|------|-----------------|
| `social_security` | "281234567890" (NSS) |
| `bank_account_clause` | "A-98765432" (CIF) |
| `professional_ids` | "12345", "67890" (Kollegialnummern) |

**Ursache:** Seltene Muster im Trainingskorpus. Die spanische NSS hat ein spezifisches Format (12 Ziffern), das nicht gelernt wurde.

**Auswirkung:** Hoch für arbeits- und handelsrechtliche Dokumente.

#### Muster 5: Kontextuelle False Positives

| Test | Falsche Entität |
|------|---------------|
| `example_dni` | "12345678X" (Kontext: "illustratives Beispiel") |
| `fictional_person` | "Don Quijote de la Mancha" |

**Ursache:** Das Modell erkennt Muster ohne semantischen Kontext zu berücksichtigen (Negationen, Beispiele, Fiktion).

**Auswirkung:** Mittel. Verursacht unnötige Anonymisierung.

### 4.2 Verwirrungsmatrix nach Entitätstyp

| Typ | TP | FP | FN | Beobachtung |
|------|----|----|----|----|
| PERSON | 15 | 2 | 2 | Gut, scheitert bei Fiktion |
| DNI_NIE | 8 | 1 | 4 | Scheitert bei Variantenformaten |
| LOCATION | 6 | 0 | 2 | Scheitert bei isolierten PLZ |
| DATE | 3 | 0 | 4 | Scheitert bei Textformat |
| IBAN | 2 | 0 | 1 | Scheitert bei OCR |
| ORGANIZATION | 5 | 2 | 0 | Verwechselt mit Gerichten |
| NSS | 0 | 0 | 1 | Erkennt nicht |
| PROFESSIONAL_ID | 0 | 0 | 2 | Erkennt nicht |
| Andere | 10 | 4 | 2 | - |

---

## 5. Schlussfolgerungen

### 5.1 Aktueller Status

Das Modell `legal_ner_v2` präsentiert einen **F1 von 0.784** in der adversarialen Evaluierung, mit folgenden Eigenschaften:

- **Stärken:**
  - Hohe Präzision (0.845) - wenige False Positives
  - Gute Rauschresistenz (Degradation 0.080)
  - Exzellent bei zusammengesetzten Namen und Adressen

- **Schwächen:**
  - Unzureichender Recall (0.731) - verpasst Entitäten
  -erkennt spanische textuelle Datumsformate nicht
  - Anfällig für Unicode Evasion (Fullwidth)
  - Erkennt keine NSS oder Kollegialnummern

### 5.2 Validierungslevel

| Level | Status | Kriterien |
|-------|--------|----------|
| Level 1: Unit Tests | ✅ | Individuelle Funktionen |
| Level 2: Integration | ✅ | Komplette Pipeline |
| Level 3: Benchmark | ✅ | F1 > 0.75 |
| **Level 4: Adversarial** | ❌ | Pass Rate < 70% |
| Level 5: Production-like | ⏸️ | Ausstehend |

**Schlussfolgerung:** Das Modell ist **NICHT bereit für die Produktion** gemäß Projektkriterien (Level 4 obligatorisch).

### 5.3 Zukünftige Arbeit

#### HOHE Priorität (geschätzte Auswirkung > 3pts F1)

1. **Unicode-Normalisierung im Preprocessing**
   - Konvertierung von Fullwidth zu ASCII
   - Entfernung von Zero-Width-Zeichen
   - Normalisierung von O/0 in numerischen Kontexten

2. **Augmentierung textueller Daten**
   - Generierung von Varianten: "primero de enero", "XV de marzo"
   - Einbeziehung römischer Ziffern
   - Fine-Tuning mit augmentiertem Korpus

3. **Regex-Muster für NSS/CIF**
   - Hinzufügen zum CompositeNerAdapter
   - NSS: `\d{12}` im Kontext "Seguridad Social"
   - CIF: `[A-Z]-?\d{8}` im Firmenkontext

#### MITTLERE Priorität (geschätzte Auswirkung 1-3pts F1)

4. **OCR-Leerzeichen-Normalisierung**
   - Erkennung und Zusammenfassen übermäßiger Leerzeichen
   - Rekonstruktion fragmentierter Token

5. **Post-Process-Filter für "Beispiel"-Kontexte**
   - Erkennung von Phrasen: "por ejemplo", "ilustrativo", "formato"
   - Unterdrückung von Entitäten in diesen Kontexten

#### NIEDRIGE Priorität (Edge Cases)

6. **Gazetteer fiktiver Charaktere**
   - Don Quijote, Sancho Panza, etc.
   - Post-Process-Filter

7. **Daten mit römischen Ziffern**
   - Spezifischer Regex für alten notariellen Stil

---

## 6. Referenzen

1. **seqeval** - Entity-Level-Evaluierungsmetriken für Sequence Labeling. https://github.com/chakki-works/seqeval

2. **NoiseBench (ICLR 2024)** - Benchmark zur Evaluierung von NLP-Modellen unter realistischen Rauschbedingungen.

3. **HAL Science** - Studie zum OCR-Einfluss bei NER-Aufgaben. Etabliert erwartete Degradation von ~10pts F1.

4. **RoBERTalex** - Spanisches Rechtsdomänen-RoBERTa-Modell. Basis des evaluierten Modells.

5. **Projektrichtlinien v1.0.0** - ML-Vorbereitungsmethodik für ContextSafe.

---

## Anhänge

### A. Testkonfiguration

```yaml
total_tests: 35
categories:
  edge_case: 9
  adversarial: 8
  ocr_corruption: 5
  unicode_evasion: 3
  real_world: 10
difficulty_distribution:
  easy: 4
  medium: 12
  hard: 19
```

### B. Reproduktionsbefehl

```bash
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate
python scripts/evaluate/test_ner_predictor_adversarial.py
```

### C. Generierte Dateien

- Automatischer Bericht: `docs/reports/2026-01-23_adversarial_ner_v2.md`
- Akademische Analyse: `docs/reports/2026-01-23_baseline_adversarial_analysis.md` (dieses Dokument)

---

**Gesamtausführungszeit:** 3.1s (Laden + Evaluierung)
**Generiert von:** AlexAlves87
**Datum:** 2026-01-23
