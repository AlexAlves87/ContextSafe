# Forschung: Akademische Standards für die NER-Bewertung

**Datum:** 2026-01-28
**Autor:** AlexAlves87
**Typ:** Wissenschaftliche Literaturrecherche
**Status:** Abgeschlossen

---

## 1. Zusammenfassung

Diese Forschung dokumentiert die akademischen Standards für die Bewertung von NER-Systemen, mit Schwerpunkt auf:
1. Metriken auf Entitätsebene (SemEval 2013 Task 9)
2. Adversarische Bewertung (RockNER, NoiseBench)
3. Bewertungs-Frameworks (seqeval, nervaluate)
4. Best Practices für Robustheitstests

### Wichtigste Erkenntnisse

| Erkenntnis | Quelle | Auswirkung |
|------------|--------|------------|
| 4 Bewertungsmodi: strict, exact, partial, type | SemEval 2013 | **KRITISCH** |
| seqeval ist der De-facto-Standard für Entity-Level F1 | CoNLL, HuggingFace | Hoch |
| RockNER: Störungen auf Entitäts- + Kontextebene | EMNLP 2021 | Hoch |
| NoiseBench: Echtes Rauschen >> simuliertes Rauschen in Schwierigkeit | EMNLP 2024 | Hoch |
| nervaluate bietet granularere Metriken als seqeval | MantisAI | Mittel |

---

## 2. Methodik

### 2.1 Konsultierte Quellen

| Quelle | Typ | Jahr | Relevanz |
|--------|-----|------|----------|
| SemEval 2013 Task 9 | Shared Task | 2013 | Definition von Metriken |
| RockNER (EMNLP 2021) | ACL Paper | 2021 | Adversarische Bewertung |
| NoiseBench (EMNLP 2024) | ACL Paper | 2024 | Realistisches Rauschen |
| seqeval | Bibliothek | 2018+ | Standardimplementierung |
| nervaluate | Bibliothek | 2020+ | Erweiterte Metriken |
| David Batista Blog | Tutorial | 2018 | Detaillierte Erklärung |

### 2.2 Suchkriterien

- "adversarial NER evaluation benchmark methodology"
- "NER robustness testing framework seqeval entity level"
- "SemEval 2013 task 9 entity level metrics"
- "RockNER adversarial NER EMNLP methodology"
- "NoiseBench NER evaluation realistic noise"

---

## 3. Bewertungsstandards auf Entitätsebene

### 3.1 SemEval 2013 Task 9: Die 4 Bewertungsmodi

**Quelle:** [Named-Entity evaluation metrics based on entity-level](https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/)

Der Standard SemEval 2013 definiert **4 Modi** der Bewertung:

| Modus | Grenze | Typ | Beschreibung |
|-------|--------|-----|--------------|
| **Strict** | Exakt | Exakt | Grenze UND Typ müssen übereinstimmen |
| **Exact** | Exakt | Ignoriert | Nur exakte Grenze |
| **Partial** | Überlappung | Ignoriert | Teilweise Überlappung genügt |
| **Type** | Überlappung | Exakt | Überlappung + korrekter Typ |

#### 3.1.1 Definition der Basismetriken

| Metrik | Definition |
|--------|------------|
| **COR** (Correct) | System und Gold sind identisch |
| **INC** (Incorrect) | System und Gold stimmen nicht überein |
| **PAR** (Partial) | System und Gold haben teilweise Überlappung |
| **MIS** (Missing) | Gold nicht vom System erfasst (FN) |
| **SPU** (Spurious) | System produziert etwas nicht im Gold (FP) |
| **POS** (Possible) | COR + INC + PAR + MIS = Gesamt Gold |
| **ACT** (Actual) | COR + INC + PAR + SPU = Gesamt System |

#### 3.1.2 Berechnungsformeln

**Für exakte Modi (strict, exact):**
```
Precision = COR / ACT
Recall = COR / POS
F1 = 2 * (P * R) / (P + R)
```

**Für partielle Modi (partial, type):**
```
Precision = (COR + 0.5 × PAR) / ACT
Recall = (COR + 0.5 × PAR) / POS
F1 = 2 * (P * R) / (P + R)
```

### 3.2 seqeval: Standardimplementierung

**Quelle:** [seqeval GitHub](https://github.com/chakki-works/seqeval)

seqeval ist das Standard-Framework für die Bewertung von Sequence Labeling, validiert gegen das Perl-Skript `conlleval` von CoNLL-2000.

#### Merkmale

| Feature | Beschreibung |
|---------|--------------|
| Format | CoNLL (BIO/BIOES Tags) |
| Metriken | Precision, Recall, F1 pro Typ und gesamt |
| Standardmodus | Simuliert conlleval (nachsichtig mit B/I) |
| Strict-Modus | Nur exakte Übereinstimmungen |

#### Korrekte Verwendung

```python
from seqeval.metrics import classification_report, f1_score
from seqeval.scheme import IOB2

# Strict-Modus (empfohlen für strenge Bewertung)
f1 = f1_score(y_true, y_pred, mode='strict', scheme=IOB2)
report = classification_report(y_true, y_pred, mode='strict', scheme=IOB2)
```

**WICHTIG:** Der Standardmodus von seqeval ist nachsichtig. Für strenge Bewertung `mode='strict'` verwenden.

### 3.3 nervaluate: Erweiterte Metriken

**Quelle:** [nervaluate GitHub](https://github.com/MantisAI/nervaluate)

nervaluate implementiert alle 4 Modi von SemEval 2013 vollständig.

#### Vorteile gegenüber seqeval

| Aspekt | seqeval | nervaluate |
|--------|---------|------------|
| Modi | 2 (default, strict) | 4 (strict, exact, partial, type) |
| Granularität | Pro Entitätstyp | Pro Typ + pro Szenario |
| Metriken | P/R/F1 | P/R/F1 + COR/INC/PAR/MIS/SPU |

#### Verwendung

```python
from nervaluate import Evaluator

evaluator = Evaluator(true_labels, pred_labels, tags=['PER', 'ORG', 'LOC'])
results, results_per_tag = evaluator.evaluate()

# Zugriff auf Strict-Modus
strict_f1 = results['strict']['f1']

# Zugriff auf detaillierte Metriken
cor = results['strict']['correct']
inc = results['strict']['incorrect']
par = results['partial']['partial']
```

---

## 4. Adversarische Bewertung: Akademische Standards

### 4.1 RockNER (EMNLP 2021)

**Quelle:** [RockNER - ACL Anthology](https://aclanthology.org/2021.emnlp-main.302/)

RockNER schlägt ein systematisches Framework zur Erstellung natürlicher adversarischer Beispiele vor.

#### Taxonomie der Störungen

| Ebene | Methode | Beschreibung |
|-------|---------|--------------|
| **Entity-level** | Wikidata-Ersetzung | Ersetzen von Entitäten durch andere derselben semantischen Klasse |
| **Context-level** | BERT MLM | Generieren von Wortersetzungen mit LM |
| **Kombiniert** | Beide | Beide anwenden für maximale Adversarität |

#### OntoRock Benchmark

- Abgeleitet von OntoNotes
- Wendet systematische Störungen an
- Misst Degradation von F1

#### Wichtigste Erkenntnis

> "Even the best model has a significant performance drop... models seem to memorize in-domain entity patterns instead of reasoning from the context."

### 4.2 NoiseBench (EMNLP 2024)

**Quelle:** [NoiseBench - ACL Anthology](https://aclanthology.org/2024.emnlp-main.1011/)

NoiseBench zeigt, dass simuliertes Rauschen **signifikant einfacher** ist als echtes Rauschen.

#### Arten von echtem Rauschen

| Art | Quelle | Beschreibung |
|-----|--------|--------------|
| Expertenfehler | Experten-Annotatoren | Müdigkeitsfehler, Interpretation |
| Crowdsourcing | Amazon Turk, etc. | Fehler von Nicht-Experten |
| Automatische Annotation | Regex, Heuristiken | Systematische Fehler |
| LLM-Fehler | GPT, etc. | Halluzinationen, Inkonsistenzen |

#### Wichtigste Erkenntnis

> "Real noise is significantly more challenging than simulated noise, and current state-of-the-art models for noise-robust learning fall far short of their theoretically achievable upper bound."

### 4.3 Taxonomie der Störungen für NER

Basierend auf der Literatur werden adversarische Störungen klassifiziert in:

| Kategorie | Beispiele | Papers |
|-----------|-----------|--------|
| **Character-level** | Tippfehler, OCR-Fehler, Homoglyphen | RockNER, NoiseBench |
| **Token-level** | Synonyme, Flexionen | RockNER |
| **Entity-level** | Ersetzung durch ähnliche Entitäten | RockNER |
| **Context-level** | Änderung des umliegenden Kontexts | RockNER |
| **Format-level** | Leerzeichen, Interpunktion, Groß-/Kleinschreibung | NoiseBench |
| **Semantic-level** | Verneinungen, fiktive Beispiele | Custom |

---

## 5. Überprüfung aktueller Tests vs Standards

### 5.1 Aktuelle adversarische Tests

Unser Skript `test_ner_predictor_adversarial.py` hat:

| Kategorie | Tests | Abdeckung |
|-----------|-------|-----------|
| edge_case | 9 | Grenzbedingungen |
| adversarial | 8 | Semantische Verwirrung |
| ocr_corruption | 5 | OCR-Fehler |
| unicode_evasion | 3 | Unicode-Umgehung |
| real_world | 10 | Reale Dokumente |

### 5.2 Identifizierte Lücken

| Lücke | Standard | Aktueller Stand | Schweregrad |
|-------|----------|-----------------|-------------|
| Strict vs Default Modus | seqeval strict | Nicht spezifiziert | **KRITISCH** |
| 4 SemEval Modi | nervaluate | Nur 1 Modus | HOCH |
| Entity-level Störungen | RockNER | Nicht systematisch | HOCH |
| Metriken COR/INC/PAR/MIS/SPU | SemEval 2013 | Nicht berichtet | MITTEL |
| Echtes vs simuliertes Rauschen | NoiseBench | Nur simuliert | MITTEL |
| Context-level Störungen | RockNER | Teilweise | MITTEL |

### 5.3 Aktuelle vs Erforderliche Metriken

| Metrik | Aktuell | Erforderlich | Lücke |
|--------|---------|--------------|-------|
| F1 gesamt | ✅ | ✅ | OK |
| Precision/Recall | ✅ | ✅ | OK |
| F1 pro Entitätstyp | ❌ | ✅ | **FEHLT** |
| Strict-Modus | ❓ | ✅ | **PRÜFEN** |
| COR/INC/PAR/MIS/SPU | ❌ | ✅ | **FEHLT** |
| 4 SemEval Modi | ❌ | ✅ | **FEHLT** |

---

## 6. Verbesserungsempfehlungen

### 6.1 Priorität KRITISCH

1. **Strict-Modus in seqeval überprüfen**
   ```python
   # Ändern von:
   f1 = f1_score(y_true, y_pred)
   # Zu:
   f1 = f1_score(y_true, y_pred, mode='strict', scheme=IOB2)
   ```

2. **Metriken pro Entitätstyp berichten**
   ```python
   report = classification_report(y_true, y_pred, mode='strict')
   ```

### 6.2 Priorität HOCH

3. **Die 4 SemEval Modi implementieren**
   - nervaluate anstelle von (oder zusätzlich zu) seqeval verwenden
   - strict, exact, partial, type berichten

4. **Entity-level Störungen hinzufügen (RockNER style)**
   - Namen durch andere spanische Namen ersetzen
   - IDs durch andere gültige IDs ersetzen
   - Kontext behalten, Entität ändern

### 6.3 Priorität MITTEL

5. **COR/INC/PAR/MIS/SPU berichten**
   - Ermöglicht feinere Fehleranalyse
   - Unterscheidet zwischen Grenzfehlern und Typfehlern

6. **Context-level Störungen hinzufügen**
   - Umliegende Verben/Adjektive ändern
   - BERT/spaCy für natürliche Ersetzungen verwenden

---

## 7. Akademische Bewertungs-Checkliste

### 7.1 Vor dem Berichten von Ergebnissen

- [ ] Bewertungsmodus spezifizieren (strict/default)
- [ ] Standard CoNLL-Format verwenden (BIO/BIOES)
- [ ] F1, Precision, Recall berichten
- [ ] Metriken pro Entitätstyp berichten
- [ ] Verwendete Version von seqeval/nervaluate dokumentieren
- [ ] Konfidenzintervalle einbeziehen, falls Varianz vorhanden

### 7.2 Für adversarische Bewertung

- [ ] Störungen kategorisieren (Character, Token, Entity, Context)
- [ ] Relative Degradation messen (F1_clean - F1_adversarial)
- [ ] Pass-Rate nach Schwierigkeitskategorie berichten
- [ ] Fehleranalyse mit Beispielen einbeziehen
- [ ] Mit Baseline vergleichen (unmodifiziertes Modell)

### 7.3 Für Veröffentlichung/Dokumentation

- [ ] Reproduzierbare Methodik beschreiben
- [ ] Testdatensatz (oder Generator) veröffentlichen
- [ ] Ausführungszeit berichten
- [ ] Statistische Analyse einbeziehen, falls zutreffend

---

## 8. Schlussfolgerungen

### 8.1 Sofortmaßnahmen

1. **Adversarisches Skript überprüfen**, um Strict-Modus zu verifizieren
2. **nervaluate hinzufügen** für vollständige Metriken
3. **Tests neu organisieren** gemäß RockNER-Taxonomie

### 8.2 Auswirkung auf aktuelle Ergebnisse

Die aktuellen Ergebnisse (F1=0.784, 54.3% Pass-Rate) könnten sich ändern, wenn:
- Der Modus nicht strict war (Ergebnisse wären niedriger in strict)
- Metriken pro Typ spezifische Schwächen offenbaren
- Die 4 Modi unterschiedliches Verhalten bei Grenze vs Typ zeigen

---

## 9. Referenzen

### Akademische Arbeiten

1. **RockNER: A Simple Method to Create Adversarial Examples for Evaluating the Robustness of Named Entity Recognition Models**
   - Lin et al., EMNLP 2021
   - URL: https://aclanthology.org/2021.emnlp-main.302/

2. **NoiseBench: Benchmarking the Impact of Real Label Noise on Named Entity Recognition**
   - Merdjanovska et al., EMNLP 2024
   - URL: https://aclanthology.org/2024.emnlp-main.1011/

3. **SemEval-2013 Task 9: Extraction of Drug-Drug Interactions from Biomedical Texts**
   - Segura-Bedmar et al., SemEval 2013
   - Definition von Metriken auf Entitätsebene

### Tools und Bibliotheken

4. **seqeval**
   - URL: https://github.com/chakki-works/seqeval

5. **nervaluate**
   - URL: https://github.com/MantisAI/nervaluate

6. **Named-Entity Evaluation Metrics Based on Entity-Level**
   - David Batista, 2018
   - URL: https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/

---

**Recherchezeit:** 45 Min.
**Generiert von:** AlexAlves87
**Datum:** 2026-01-28
