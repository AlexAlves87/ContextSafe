# Forschung: Lücken im Hybriden NER-PII-Pipeline

**Datum:** 30.01.2026
**Autor:** AlexAlves87
**Ziel:** Analyse kritischer Lücken in der hybriden Pipeline basierend auf akademischer Literatur von 2024-2026
**Version:** 2.0.0 (umgeschrieben mit akademischer Grundlage)

---

## 1. Zusammenfassung

Es wurden fünf Lücken in der hybriden NER-PII-Pipeline von ContextSafe identifiziert. Für jede Lücke wurde eine Überprüfung der akademischen Literatur in erstklassigen Quellen (ACL, EMNLP, COLING, NAACL, TACL, Nature Scientific Reports, Springer, arXiv) durchgeführt. Die vorgeschlagenen Empfehlungen basieren auf veröffentlichten Beweisen, nicht auf Intuition.

| Lücke | Priorität | Überprüfte Paper | Hauptempfehlung |
|-------|-----------|------------------|-----------------|
| Merge-Strategie | **HOCH** | 7 | 3-Phasen-Pipeline (RECAP) + Priorität nach Typ |
| Konfidenz-Kalibrierung | **HOCH** | 5 | Conformal Prediction + BRB für Regex |
| Vergleichender Benchmark | **MITTEL** | 3 | nervaluate (SemEval'13) mit Partial Matching |
| Latenz/Speicher | **MITTEL** | 4 | ONNX Runtime + INT8 Quantisierung |
| Gazetteers | **NIEDRIG** | 5 | GAIN-Style Integration als Post-Filter |

---

## 2. Überprüfte Literatur

| Paper/System | Ort/Quelle | Jahr | Relevante Erkenntnis |
|--------------|------------|------|----------------------|
| RECAP: Hybrid PII Detection | arXiv 2510.07551 | 2025 | 3-Phasen-Pipeline: Erkennung → Multi-Label-Disambiguierung → Span-Konsolidierung |
| Hybrid rule-based NLP + ML for PII (Mishra et al.) | Nature Scientific Reports | 2025 | F1 0.911 bei Finanzdokumenten, Merge Overlaps durch min(start)/max(end) |
| Conformal Prediction for NER | arXiv 2601.16999 | 2026 | Vorhersagemengen mit Abdeckungsgarantien ≥95%, stratifizierte Kalibrierung |
| JCLB: Contrastive Learning + BRB | Springer Cybersecurity | 2024 | Belief Rule Base weist Regex gelernte Konfidenz zu, D-CMA-ES optimiert Parameter |
| CMiNER | Expert Systems with Applications | 2025 | Konfidenzschätzer auf Entitätsebene für verrauschte Daten |
| B2NER | COLING 2025 | 2025 | Einheitlicher NER-Benchmark, 54 Datensätze, LoRA-Adapter ≤50MB, übertrifft GPT-4 |
| nervaluate (SemEval'13 Task 9) | GitHub/MantisAI | 2024 | COR/INC/PAR/MIS/SPU-Metriken mit Partial Matching |
| T2-NER | TACL | 2023 | 2-stufiges Span-basiertes Framework für überlappende und diskontinuierliche Entitäten |
| GNNer | ACL SRW 2022 | 2022 | Graph Neural Networks zur Reduzierung überlappender Spans |
| GAIN: Gazetteer-Adapted Integration | SemEval-2022 | 2022 | KL-Divergenz zur Anpassung des Gazetteer-Netzwerks an das Sprachmodell, 1. Platz in 3 Tracks |
| Presidio | Microsoft Open Source | 2025 | `_remove_duplicates`: höchste Konfidenz gewinnt, Containment → größerer Span |
| Soft Gazetteers | ACL 2020 | 2020 | Sprachübergreifendes Entity Linking für Gazetteers in ressourcenarmen Sprachen |
| SPLR (span-based nested NER) | J. Supercomputing | 2025 | F1 87.5 auf ACE2005 mit Prior Knowledge Function |
| HuggingFace Optimum + ONNX | MarkTechPost/HuggingFace | 2025 | Benchmark PyTorch vs ONNX Runtime vs quantisiertes INT8 |
| PyDeID | PHI De-identification | 2025 | Regex + spaCy NER, F1 87.9% bei klinischen Notizen, 0.48s/Notiz |

---

## 3. Lücke 1: Merge-Strategie (HOCH)

### 3.1 Problem

Wenn Transformer-NER und Regex dieselbe Entität mit unterschiedlichen Grenzen oder Typen erkennen, welche soll bevorzugt werden?

```
Text: "Don José García mit DNI 12 345 678 Z"

NER erkennt:   "José García mit DNI 12 345 678" (PERSON erweitert, teilweise)
Regex erkennt: "12 345 678 Z" (DNI_NIE, vollständig)
```

### 3.2 Stand der Technik

#### 3.2.1 RECAP Framework (arXiv 2510.07551, 2025)

Das aktuellste und vollständigste Framework für hybride PII-Zusammenführung implementiert **drei Phasen**:

1.  **Phase I - Basiserkennung:** Regex für strukturierte PII (IDs, Telefone) + LLM für unstrukturierte (Namen, Adressen). Erzeugt Multi-Labels, Überlappungen und False Positives.

2.  **Phase II - Multi-Label-Disambiguierung:** Bei Entitäten mit mehreren Labels werden Text, Span und Kandidatenlabels an ein LLM mit kontextbezogenem Prompt übergeben, das das korrekte Label auswählt.

3.  **Phase III - Konsolidierung:** Zwei Filter:
    *   **Deterministische Überlappungsauflösung:** Entitäten mit niedrigerer Priorität, die vollständig in längeren Spans enthalten sind, werden entfernt.
    *   **Kontextbezogenes Filtern von False Positives:** Kurze numerische Sequenzen werden mit dem Kontext des umgebenden Satzes verifiziert.

**Ergebnis:** Durchschnittlicher F1 0.657 über 13 Regionen, übertrifft reines NER (0.360) um 82% und Zero-Shot-LLM (0.558) um 17%.

#### 3.2.2 Microsoft Presidio (2025)

Presidio implementiert `__remove_duplicates()` mit einfachen Regeln:
*   **Höchster Konfidenz-Score gewinnt** bei überlappenden Erkennungen
*   **Containment:** Wenn eine PII in einer anderen enthalten ist, wird der **längste Text** verwendet
*   **Partielle Schnittmenge:** Beide werden verkettet zurückgegeben
*   Keine Priorität nach Typ, nur nach Score

#### 3.2.3 Mishra et al. (Nature Scientific Reports, 2025)

Für Finanzdokumente, Zusammenführung von Überlappungen:
*   `start = min(start1, start2)`
*   `end = max(end1, end2)`
*   Überlappung wird zu einer einzigen konsolidierten Entität zusammengeführt

**Einschränkung:** Unterscheidet keine Typen — nutzlos, wenn NER PERSON und Regex DNI im selben Span erkennt.

#### 3.2.4 T2-NER (TACL, 2023)

2-stufiges Span-basiertes Framework:
1.  Extraktion aller Entity-Spans (überlappend und flach)
2.  Klassifizierung von Span-Paaren zur Auflösung von Diskontinuitäten

**Anwendbare Erkenntnis:** Die Trennung der Span-Erkennung von ihrer Klassifizierung ermöglicht eine modulare Behandlung von Überlappungen.

#### 3.2.5 GNNer (ACL Student Research Workshop, 2022)

Verwendet Graph Neural Networks zur Reduzierung überlappender Spans in Span-basiertem NER. Kandidaten-Spans sind Knoten in einem Graphen, und GNN lernt, überlappende zu entfernen.

**Anwendbare Erkenntnis:** Überlappung ist nicht immer ein Fehler — verschachtelte Entitäten (Name in Adresse) sind legitim.

### 3.3 Aktuelle Implementierung von ContextSafe

Datei: `scripts/inference/ner_predictor.py`, Methode `_merge_regex_detections()`

```python
# Aktuelle Strategie (Zeilen 430-443):
for ner_ent in ner_entities:
    replaced = False
    for match in regex_matches:
        if overlaps(match, ner_ent):
            if regex_len > ner_len * 1.2:  # Regex 20% länger
                replaced = True
                break
    if not replaced:
        ner_to_keep.append(ner_ent)
```

**Aktuelle Regel:** Wenn Regex ≥20% länger ist als NER und eine Überlappung besteht → Regex bevorzugen.

### 3.4 Vergleichende Analyse

| System | Strategie | Behandelt Nested | Nutzt Typ | Nutzt Konfidenz |
|--------|-----------|------------------|-----------|-----------------|
| RECAP | 3 Phasen + LLM | ✅ | ✅ | Implizit |
| Presidio | Höchster Score | ❌ | ❌ | ✅ |
| Mishra et al. | min/max merge | ❌ | ❌ | ❌ |
| ContextSafe aktuell | Längerer Regex gewinnt | ❌ | ❌ | ❌ |
| **Vorschlag** | **Typ-Priorität + Validierung** | **✅** | **✅** | **✅** |

### 3.5 Evidenzbasierte Empfehlung

Inspiriert von RECAP (3 Phasen), aber ohne Abhängigkeit von LLM (unsere Anforderung ist CPU-Inferenz ohne LLM), schlagen wir vor:

**Phase 1: Unabhängige Erkennung**
*   Transformer-NER erkennt semantische Entitäten (PERSON, ORGANIZATION, LOCATION)
*   Regex erkennt strukturelle Entitäten (DNI, IBAN, PHONE, DATE)

**Phase 2: Überlappungsauflösung nach Typ-Priorität**

Basierend auf RECAP-Evidenz (Regex überragt bei strukturierter PII, NER bei semantischer):

```python
MERGE_PRIORITY = {
    # Typ → (Priorität, bevorzugte_Quelle)
    # Regex mit Checksumme = maximale Konfidenz (Evidenz: Mishra et al. 2025)
    "DNI_NIE": (10, "regex"),      # Überprüfbare Checksumme
    "IBAN": (10, "regex"),         # Überprüfbare Checksumme
    "NSS": (10, "regex"),          # Überprüfbare Checksumme
    "PHONE": (8, "regex"),         # Gut definiertes Format
    "POSTAL_CODE": (8, "regex"),   # Exakt 5 Ziffern
    "LICENSE_PLATE": (8, "regex"), # Gut definiertes Format
    # NER überragt bei semantischen Entitäten (RECAP, PyDeID)
    "DATE": (6, "any"),            # Beide gültig
    "PERSON": (4, "ner"),          # NER besser mit Kontext
    "ORGANIZATION": (4, "ner"),    # NER besser mit Kontext
    "LOCATION": (4, "ner"),        # NER besser mit Kontext
    "ADDRESS": (4, "ner"),         # NER besser mit Kontext
}
```

**Phase 3: Konsolidierung**
*   **Enthaltene** Entitäten unterschiedlichen Typs: beide behalten (legitim verschachtelt, wie in GNNer)
*   **Enthaltene** Entitäten gleichen Typs: die spezifischste bevorzugen (bevorzugte Quelle)
*   **Partielle** Überlappung: Typ mit höherer Priorität bevorzugen
*   Keine Überlappung: beide behalten

| Situation | Regel | Evidenz |
|-----------|-------|---------|
| Keine Überlappung | Beide behalten | Standard |
| Überlappung, diff. Typen | Höhere Priorität gewinnt | RECAP Phase III |
| Containment, diff. Typen | Beide behalten (nested) | GNNer, T2-NER |
| Containment, gleicher Typ | Bevorzugte Quelle laut Tabelle | Presidio (größerer Span) |
| Partielle Überlappung, gleicher Typ | Höhere Konfidenz gewinnt | Presidio |

---

## 4. Lücke 2: Konfidenz-Kalibrierung (HOCH)

### 4.1 Problem

Regex gibt feste Konfidenz (0.95) zurück, NER gibt Softmax-Wahrscheinlichkeit zurück. Sie sind nicht direkt vergleichbar.

### 4.2 Stand der Technik

#### 4.2.1 Conformal Prediction für NER (arXiv 2601.16999, Januar 2026)

**Neuestes und relevantestes Paper.** Führt Framework ein, um **Vorhersagemengen** mit Abdeckungsgarantien zu erstellen:

*   Bei gegebenem Konfidenzniveau `1-α` werden Vorhersagemengen generiert, die garantiert das korrekte Label enthalten
*   Verwendet **Non-Conformity Scores**:
    *   `nc1`: `1 - P̂(y|x)` — basierend auf Wahrscheinlichkeit, bestraft niedrige Konfidenz
    *   `nc2`: kumulative Wahrscheinlichkeit in rangierten Sequenzen
    *   `nc3`: basierend auf Rang, erzeugt Mengen fester Größe

**Wichtige Erkenntnisse:**
*   `nc1` übertrifft `nc2` (das "extrem große" Mengen erzeugt) deutlich
*   **Längenstratifizierte Kalibrierung** korrigiert systematische Fehlkalibrierung in langen Sequenzen
*   **Sprachkalibrierung** verbessert die Abdeckung (Englisch: 93.82% → 96.24% nach Stratifizierung)
*   Šidák-Korrektur für mehrere Entitäten: Konfidenz pro Entität = `(1-α)^(1/s)` für `s` Entitäten

**Anwendbarkeit auf ContextSafe:** Längenstratifizierte Kalibrierung ist direkt anwendbar. Lange Texte (Verträge) können systematisch andere Scores haben als kurze Texte.

#### 4.2.2 JCLB: Belief Rule Base (Springer Cybersecurity, 2024)

Führt einen Ansatz ein, um **Regex-Regeln Konfidenz auf gelernte Weise zuzuweisen**:

*   Regex-Regeln werden als **Belief Rule Base (BRB)** formalisiert
*   Jede Regel hat **Belief Degrees**, die durch D-CMA-ES optimiert werden
*   Die BRB filtert Entitätskategorien und bewertet deren Richtigkeit gleichzeitig
*   BRB-Parameter werden gegen Trainingsdaten optimiert

**Wichtige Erkenntnis:** Regex-Regeln sollten KEINE feste Konfidenz haben. Ihre Konfidenz muss gelernt/gegen reale Daten kalibriert werden.

#### 4.2.3 CMiNER (Expert Systems with Applications, 2025)

Entwirft **Konfidenzschätzer auf Entitätsebene**, die:
*   Die anfängliche Qualität verrauschter Datensätze bewerten
*   Während des Trainings durch Anpassung der Gewichte assistieren

**Anwendbare Erkenntnis:** Konfidenz auf Entitätsebene (nicht Token) ist nützlicher für Merge-Entscheidungen.

#### 4.2.4 Conf-MPU (Zhou et al., 2022)

Token-level binäre Klassifizierung zur Vorhersage der Wahrscheinlichkeit, dass jedes Token eine Entität ist, dann Verwendung von Konfidenz-Scores zur Risikoschätzung.

**Anwendbare Erkenntnis:** Die Trennung von "Ist das eine Entität?" und "Welcher Typ?" ermöglicht eine Kalibrierung in zwei Stufen.

### 4.3 Aktuelle Implementierung von ContextSafe

```python
# Regex-Muster (spanish_id_patterns.py):
RegexMatch(..., confidence=0.95)  # Hardcodierter fester Wert

# NER-Modell:
confidence = softmax(logits).max()  # Reale Wahrscheinlichkeit [0.5-0.99]

# Checksummen-Anpassung (ner_predictor.py, Zeilen 473-485):
if is_valid:
    final_confidence = min(match.confidence * 1.1, 0.99)
elif checksum_conf < 0.5:
    final_confidence = match.confidence * 0.5
```

### 4.4 Problemanalyse

| Quelle | Konfidenz | Kalibriert | Problem |
|--------|-----------|------------|---------|
| NER Softmax | 0.50-0.99 | ✅ | Kann bei langen Texten fehlkalibriert sein (CP 2026) |
| Regex ohne Checksumme | 0.95 fest | ❌ | Überkonfidenz bei mehrdeutigen Matches |
| Regex mit gültiger Checksumme | 0.99 | ⚠️ | Angemessen für IDs mit Checksumme |
| Regex mit ungültiger Checksumme | 0.475 | ✅ | Angemessene Bestrafung |

### 4.5 Evidenzbasierte Empfehlung

#### Stufe 1: Basiskonfidenz differenziert nach Typ (inspiriert von JCLB/BRB)

Keine feste Konfidenz verwenden. Zuweisung einer **Basiskonfidenz** entsprechend dem verfügbaren Validierungslevel:

```python
REGEX_BASE_CONFIDENCE = {
    # Mit überprüfbarer Checksumme (maximale Konfidenz, Mishra et al. 2025)
    "DNI_NIE":  {"checksum_valid": 0.98, "checksum_invalid": 0.35, "format_only": 0.70},
    "IBAN":     {"checksum_valid": 0.99, "checksum_invalid": 0.30, "format_only": 0.65},
    "NSS":      {"checksum_valid": 0.95, "checksum_invalid": 0.35, "format_only": 0.65},

    # Ohne Checksumme, mit gut definiertem Format
    "PHONE":         {"with_prefix": 0.90, "without_prefix": 0.75},
    "POSTAL_CODE":   {"valid_province": 0.85, "format_only": 0.70},
    "LICENSE_PLATE": {"modern_format": 0.90, "old_format": 0.80},

    # Mehrdeutig
    "DATE":  {"full_textual": 0.85, "partial": 0.60, "ambiguous": 0.50},
    "EMAIL": {"standard": 0.95},
}
```

**Begründung:** JCLB hat gezeigt, dass Regelkonfidenz gelernt/differenziert sein sollte, nicht fest. Ohne Zugang zu Trainingsdaten zur Optimierung der BRB (wie D-CMA-ES in JCLB) verwenden wir Heuristiken basierend auf dem verfügbaren Validierungslevel (Checksumme > Format > einfacher Match).

#### Stufe 2: Stratifizierte Kalibrierung (inspiriert von CP 2026)

Für Transformer-NER eine Kalibrierung nach Textlänge in Betracht ziehen:
*   Kurze Texte (1-10 Tokens): Minimaer Konfidenzschwellenwert 0.60
*   Mittlere Texte (11-50 Tokens): Schwellenwert 0.50
*   Lange Texte (51+ Tokens): Schwellenwert 0.45

**Begründung:** Das Conformal Prediction Paper (2026) hat gezeigt, dass lange Texte eine systematisch unterschiedliche Abdeckung haben. Eine Stratifizierung nach Länge korrigiert diese Fehlkalibrierung.

#### Stufe 3: Operativer Konfidenzschwellenwert

Basierend auf RECAP und PyDeID:
*   **≥0.80:** Automatische Anonymisierung
*   **0.50-0.79:** Anonymisierung mit "Review"-Flag
*   **<0.50:** Nicht anonymisieren, als "zweifelhaft" melden

---

## 5. Lücke 3: Vergleichender Benchmark (MITTEL)

### 5.1 Stand der Technik bei der NER-Evaluierung

#### 5.1.1 Metriken: seqeval vs nervaluate

| Framework | Typ | Partial Match | Level | Standard |
|-----------|-----|---------------|-------|----------|
| **seqeval** | Strict Entity-Level | ❌ | Vollständige Entität | CoNLL Eval |
| **nervaluate** | Multi-Szenario | ✅ | COR/INC/PAR/MIS/SPU | SemEval'13 Task 9 |

**seqeval** (CoNLL Standard):
*   Precision, Recall, F1 auf Ebene der vollständigen Entität
*   Nur exakter Match: korrekter Typ UND vollständiger Span
*   Micro/Macro Average pro Typ

**nervaluate** (SemEval'13 Task 9):
*   4 Szenarien: strict, exact, partial, type
*   5 Kategorien: COR (korrekt), INC (falscher Typ), PAR (partieller Span), MIS (verpasst), SPU (unecht)
*   Partial Matching: `Precision = (COR + 0.5 × PAR) / ACT`

**Empfehlung:** **Beide** Metriken verwenden. seqeval für Vergleichbarkeit mit der Literatur (CoNLL), nervaluate für feinere Fehleranalyse.

#### 5.1.2 B2NER Benchmark (COLING 2025)

*   54 Datensätze, 400+ Entitätstypen, 6 Sprachen
*   Einheitlicher Benchmark für Open NER
*   LoRA-Adapter ≤50MB übertreffen GPT-4 um 6.8-12.0 F1

**Anwendbarkeit:** B2NER bestätigt, dass LoRA für spezialisiertes NER machbar ist, aber Qualitätsdaten (54 verfeinerte Datensätze) erfordert.

### 5.2 Verfügbare ContextSafe-Daten

| Konfiguration | F1 Strict | Pass Rate | Quelle |
|---------------|-----------|-----------|--------|
| Nur NER (legal_ner_v2 base) | 0.464 | 28.6% | Baseline |
| NER + Normalizer | 0.492 | 34.3% | ML Cycle |
| NER + Regex | 0.543 | 45.7% | ML Cycle |
| **Volle Pipeline (5 Elem)** | **0.788** | **60.0%** | ML Cycle |
| LoRA Fine-Tuning pur | 0.016 | 5.7% | Exp. 2026-02-04 |
| GLiNER Zero-Shot | 0.325 | 11.4% | Exp. 2026-02-04 |

### 5.3 Ausstehender Benchmark

| Test | Metrik | Status |
|------|--------|--------|
| Evaluierung mit nervaluate (Partial Matching) | COR/INC/PAR/MIS/SPU | Ausstehend |
| Nur Regex (ohne NER) | F1 Strict + Partial | Ausstehend |
| NER + Checksumme (ohne Regex-Muster) | F1 Strict + Partial | Ausstehend |
| Aufschlüsselung nach Entitätstyp | F1 pro Typ | Ausstehend |

### 5.4 Empfehlung

Erstellung eines Skripts `scripts/evaluate/benchmark_nervaluate.py`, das:
1.  Die volle Pipeline gegen das Adversarial Test Set ausführt
2.  seqeval-Metriken berichtet (Strict, für Vergleichbarkeit)
3.  nervaluate-Metriken berichtet (4 Szenarien, für Fehleranalyse)
4.  Nach Entitätstyp aufschlüsselt
5.  Ablationen vergleicht (nur NER, nur Regex, Hybrid)

---

## 6. Lücke 4: Latenz/Speicher (MITTEL)

### 6.1 Ziel

| Metrik | Ziel | Begründung |
|--------|------|------------|
| Latenz | <500ms pro A4-Seite (~600 Tokens) | Reaktive UX |
| Speicher | <2GB Modell im RAM | Deployment auf 16GB |
| Durchsatz | >10 Seiten/Sekunde (Batch) | Massenverarbeitung |

### 6.2 Stand der Technik bei Inferenzoptimierung

#### 6.2.1 ONNX Runtime + Quantisierung (HuggingFace Optimum, 2025)

HuggingFace Optimum ermöglicht:
*   Export nach ONNX
*   Graph-Optimierung (Operator-Fusion, Eliminierung redundanter Knoten)
*   INT8-Quantisierung (dynamisch oder statisch)
*   Integriertes Benchmarking: PyTorch vs torch.compile vs ONNX vs ONNX quantisiert

**Gemeldete Ergebnisse:**
*   TensorRT-Optimiert: bis zu 432 Infernzen/Sekunde (ResNet-50, nicht NER)
*   ONNX Runtime: typischerweise 2-4x Speedup gegenüber Vanilla PyTorch auf CPU

#### 6.2.2 PyDeID (2025)

Hybrides Regex + spaCy NER System zur De-Identifizierung:
*   **0.48 Sekunden/Notiz** vs 6.38 Sekunden/Notiz des Basissystems
*   Faktor 13x Speedup mit optimiertem Regex + NER
*   F1 87.9% mit der schnellen Pipeline

**Direkte Anwendbarkeit:** PyDeID zeigt, dass eine hybride Regex+NER-Pipeline 1 Dokument in <0.5s verarbeiten kann.

#### 6.2.3 Transformer-Optimierungs-Pipeline

```
PyTorch FP32 → ONNX Export → Graph-Optimierung → INT8 Quantisierung
    Baseline        2x             2-3x              3-4x
```

### 6.3 Theoretische Schätzung für ContextSafe

| Komponente | CPU (PyTorch) | CPU (ONNX INT8) | Speicher |
|------------|---------------|-----------------|----------|
| TextNormalizer | <1ms | <1ms | ~0 |
| NER (RoBERTa-BNE ~125M) | ~200-400ms | ~50-100ms | ~500MB → ~200MB |
| Checksummen-Validatoren | <1ms | <1ms | ~0 |
| Regex-Muster | <5ms | <5ms | ~0 |
| Datums-Muster | <2ms | <2ms | ~0 |
| Grenzverfeinerung | <1ms | <1ms | ~0 |
| **Gesamt** | **~210-410ms** | **~60-110ms** | **~500MB → ~200MB** |

**Fazit:** Mit ONNX INT8 sollte das Ziel <500ms/Seite mit großem Spielraum erreicht werden.

### 6.4 Empfehlung

1.  **Zuerst messen** der aktuellen Latenz mit PyTorch (Skript `benchmark_latency.py`)
2.  **Wenn <500ms auf CPU erfüllt sind**: dokumentieren und ONNX-Optimierung zurückstellen
3.  **Wenn nicht erfüllt**: Export ONNX + INT8 Quantisierung (priorisieren)
4.  **Prozess dokumentieren** für Replizierbarkeit in anderen Sprachen

---

## 7. Lücke 5: Gazetteers (NIEDRIG)

### 7.1 Stand der Technik

#### 7.1.1 GAIN: Gazetteer-Adapted Integration Network (SemEval-2022)

*   **KL-Divergenz-Anpassung:** Gazetteer-Netzwerk passt sich dem Sprachmodell an und minimiert KL-Divergenz
*   **2 Stufen:** Erst Anpassung des Gazetteers an das Modell, dann Training von überwachtem NER
*   **Ergebnis:** 1. Platz in 3 Tracks (Chinesisch, Code-mixed, Bangla), 2. Platz in 10 Tracks
*   **Erkenntnis:** Gazetteers sind am nützlichsten, wenn sie als zusätzliches Feature integriert werden, nicht als direkter Lookup

#### 7.1.2 Gazetteer-Enhanced Attentive Neural Networks (EMNLP 2019)

*   Hilfsnetzwerk kodiert "Namensregelmäßigkeit" nur unter Verwendung von Gazetteers
*   Wird in das Haupt-NER für bessere Erkennung integriert
*   **Reduziert Trainingsdatenanforderungen** signifikant

#### 7.1.3 Soft Gazetteers für Low-Resource NER (ACL 2020)

*   In Sprachen ohne erschöpfende Gazetteers Cross-Lingual Entity Linking verwenden
*   Wikipedia als Wissensquelle
*   Experimentiert in 4 ressourcenarmen Sprachen

#### 7.1.4 Reduzierung von Spurious Matching

*   Rohe Gazetteers erzeugen **viele False Positives** (unechtes Matching)
*   Filtern nach "Entitätspopularität" verbessert F1 um +3.70%
*   **Saubere Gazetteers > Vollständige Gazetteers**

### 7.2 Verfügbare Gazetteers in ContextSafe

| Gazetteer | Einträge | Quelle | In Pipeline |
|-----------|----------|--------|-------------|
| Nachnamen | 27.251 | INE | ❌ |
| Männernamen | 550 | INE | ❌ |
| Frauennamen | 550 | INE | ❌ |
| Archaische Namen | 6.010 | Generiert | ❌ |
| Gemeinden | 8.115 | INE | ❌ |
| Postleitzahlen | 11.051 | INE | ❌ |

### 7.3 Evidenzbasierte Empfehlung

**Gazetteers nicht in die Kern-Pipeline integrieren** aus folgenden literaturbasierten Gründen:

1.  **Spurious Matching** (EMNLP 2019): Ohne Popularitätsfilterung erzeugen Gazetteers False Positives
2.  **Pipeline funktioniert bereits** (F1 0.788): Der Grenznutzen von Gazetteers ist gering
3.  **Komplexität der Replizierbarkeit:** Gazetteers sind sprachspezifisch, jede Sprache benötigt unterschiedliche Quellen

**Empfohlene Nutzung als Post-Filter:**
*   **Namensvalidierung:** Wenn NER PERSON erkennt, prüfen ob Name/Nachname im Gazetteer ist → Konfidenz +0.05 erhöhen
*   **PLZ-Validierung:** Wenn Regex POSTAL_CODE 28001 erkennt, prüfen ob dies einer realen Gemeinde entspricht → Konfidenz +0.10 erhöhen
*   **NICHT zur Erkennung verwenden:** Nicht direkt nach Gazetteer-Namen im Text suchen (Risiko von Spurious Matching)

---

## 8. Aktionsplan

### 8.1 Sofortige Maßnahmen (Hohe Priorität)

| Maßnahme | Akademische Basis | Datei |
|----------|-------------------|-------|
| 3-Phasen-Merge-Strategie implementieren | RECAP (2025) | `ner_predictor.py` |
| Feste 0.95 Konfidenz bei Regex entfernen | JCLB/BRB (2024) | `spanish_id_patterns.py` |
| Prioritätstabelle nach Typ hinzufügen | RECAP, Presidio | `ner_predictor.py` |

### 8.2 Verbesserungsmaßnahmen (Mittlere Priorität)

| Maßnahme | Akademische Basis | Datei |
|----------|-------------------|-------|
| Evaluierung mit nervaluate (Partial Matching) | SemEval'13 Task 9 | `benchmark_nervaluate.py` |
| Latenz-Benchmark erstellen | PyDeID (2025) | `benchmark_latency.py` |
| Kalibrierung nach Länge dokumentieren | CP NER (2026) | Replicability Guide |

### 8.3 Zurückgestellte Maßnahmen (Niedrige Priorität)

| Maßnahme | Akademische Basis | Datei |
|----------|-------------------|-------|
| Gazetteers als Post-Filter | GAIN (2022) | `ner_predictor.py` |
| Export ONNX + INT8 | HuggingFace Optimum | `scripts/export/` |

---

## 9. Schlussfolgerungen

### 9.1 Wichtigste Forschungsergebnisse

1.  **Hybride Pipeline ist SOTA für PII** — RECAP (2025), PyDeID (2025) und Mishra et al. (2025) bestätigen, dass Regex + NER jede Komponente einzeln übertrifft.

2.  **Regex-Konfidenz sollte nicht fest sein** — JCLB (2024) zeigte, dass die Zuweisung gelernter Konfidenz zu Regeln die Leistung signifikant verbessert.

3.  **Kalibrierung nach Textlänge ist wichtig** — Conformal Prediction (2026) zeigte systematische Fehlkalibrierung in langen Sequenzen.

4.  **nervaluate ergänzt seqeval** — SemEval'13 Task 9 bietet Metriken für Partial Matching, die Grenzfehler erfassen, die seqeval ignoriert.

5.  **ONNX INT8 ist machbar für <500ms Latenz** — PyDeID zeigte <0.5s/Dokument mit optimierter hybrider Pipeline.

### 9.2 Status der evaluierten Modelle

| Modell | Evaluierung | Adversarial F1 | Status |
|--------|-------------|----------------|--------|
| **RoBERTa-BNE CAPITEL NER** (`legal_ner_v2`) | Volle 5-Elemente-Pipeline | **0.788** | **AKTIV** |
| GLiNER-PII (Zero-Shot) | Evaluiert an 35 Adversarial Tests | 0.325 | Verworfen (unterlegen) |
| LoRA Legal-XLM-R-base (`lora_ner_v1`) | Evaluiert an 35 Adversarial Tests | 0.016 | Verworfen (Overfitting) |
| MEL (Spanisches Juristisches Modell) | Untersucht | N/A (keine NER-Version) | Verworfen |
| Legal-XLM-R-base (joelniklaus) | Untersucht für mehrsprachig | N/A | Ausstehend für zukünftige Erweiterung |

> **Hinweis:** Das Basismodell der Pipeline ist `roberta-base-bne-capitel-ner` (RoBERTa-BNE, ~125M Parameter, Vocab 50.262),
> feinabgestimmt mit synthetischen Daten v3 (30% Rauschinjektion). Es ist **NICHT** XLM-RoBERTa.

### 9.3 Empfehlungen für Replizierbarkeit

Für die Replikation in anderen Sprachen sind die Adapter:

| Komponente | Spanien (ES) | Frankreich (FR) | Italien (IT) | Anpassung |
|------------|--------------|-----------------|--------------|-----------|
| NER-Modell | RoBERTa-BNE CAPITEL | JuriBERT/CamemBERT | Legal-BERT-IT | Fine-Tune NER pro Sprache |
| Multilinguales NER (Alternative) | Legal-XLM-R | Legal-XLM-R | Legal-XLM-R | Einziges multilinguales Modell |
| Regex-Muster | DNI/NIE, IBAN ES | CNI, IBAN FR | CF, IBAN IT | Neue Regex-Datei |
| Checksummen-Validatoren | mod-23 (DNI) | mod-97 (IBAN) | Codice Fiscale | Neuer Validator |
| Merge-Prioritäten | Tabelle 3.5 | Gleiche Struktur | Gleiche Struktur | Typen anpassen |
| Konfidenz-Kalibrierung | Tabelle 4.5 | Gleiche Struktur | Gleiche Struktur | Kalibrieren nach lokalem Typ |
| Gazetteers | INE | INSEE | ISTAT | Nationale Quellen |

---

**Generiert von:** AlexAlves87
**Datum:** 30.01.2026
**Version:** 2.0.0 — Umgeschrieben mit akademischer Forschung (v1.0 fehlte die Grundlage)
