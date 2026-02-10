# Forschung: Best Practices für Adversarielle NER-Evaluierung

**Datum:** 2026-01-17
**Ziel:** Fundierung der Methodik für adversarielle Evaluierung vor der Implementierung von Skripten

---

## 1. Zusammenfassung

Die aktuelle akademische Literatur (2024-2025) legt fest, dass die adversarielle Evaluierung von NER-Modellen Folgendes berücksichtigen muss:

1. **Echtes vs. Simuliertes Rauschen** - Echtes Rauschen ist signifikant schwieriger als simuliertes.
2. **Evaluierung auf Entitätsebene** - Nicht auf Token-Ebene.
3. **Mehrere Störungskategorien** - OCR, Unicode, Kontext, Format.
4. **Standardmetriken** - seqeval mit F1, Präzision, Recall pro Entitätstyp.

---

## 2. Konsultierte Quellen

### 2.1 NoiseBench (Mai 2024)

**Quelle:** [NoiseBench: Benchmarking the Impact of Real Label Noise on NER](https://arxiv.org/abs/2405.07609)

**Wichtige Erkenntnisse:**
- Echtes Rauschen (menschliche Fehler, Crowdsourcing, LLM) ist **signifikant schwieriger** als simuliertes Rauschen.
- State-of-the-Art Modelle "bleiben weit hinter ihrer theoretisch erreichbaren Obergrenze zurück".
- 6 Arten von echtem Rauschen sollten evaluiert werden: Expertenfehler, Crowdsourcing-Fehler, automatische Annotationsfehler, LLM-Fehler.

**Anwendung auf unser Projekt:**
- Unsere Tests beinhalten echtes OCR-Rauschen (l/I, 0/O Verwechslung) ✓
- Wir sollten Tests mit automatischen Annotationsfehlern hinzufügen.

### 2.2 Context-Aware Adversarial Training for NER (MIT TACL)

**Quelle:** [Context-aware Adversarial Training for Name Regularity Bias](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00386/102846)

**Wichtige Erkenntnisse:**
- NER-Modelle zeigen "Name Regularity Bias" - sie verlassen sich zu sehr auf den Namen und nicht auf den Kontext.
- Fine-tuned BERT übertrifft LSTM-CRF in Bias-Tests signifikant.
- Adversarielles Training mit lernbaren Rauschvektoren verbessert die kontextuelle Fähigkeit.

**Anwendung auf unser Projekt:**
- Unsere Tests `negation_dni`, `example_dni`, `fictional_person` evaluieren kontextuelle Fähigkeiten ✓
- Das Modell v2 (mit Rauschen trainiert) sollte robuster sein.

### 2.3 OCR Impact on NER (HAL Science)

**Quelle:** [Assessing and Minimizing the Impact of OCR Quality on NER](https://hal.science/hal-03026931/document)

**Wichtige Erkenntnisse:**
- OCR-Rauschen verursacht einen Verlust von ~10 F1-Punkten (72% vs 82% bei sauberem Text).
- Sollte mit "verschiedenen Stufen und Arten von OCR-Rauschen" evaluiert werden.
- Erste systematische Studie zum Einfluss von OCR auf mehrsprachiges NER.

**Anwendung auf unser Projekt:**
- Unsere OCR-Tests (5 Fälle) sind unzureichend - Literatur empfiehlt mehr Stufen.
- Realistisches Ziel: ~10 Punkte Verschlechterung bei OCR akzeptieren.

### 2.4 seqeval - Standardmetriken

**Quelle:** [seqeval - Sequence Labeling Evaluation](https://github.com/chakki-works/seqeval)

**Wichtige Erkenntnisse:**
- Evaluierung auf **Entitäts**-Ebene, nicht Token.
- Metriken: Präzision, Recall, F1 nach Typ und Makro/Mikro-Durchschnitt.
- Strict vs Lenient Modus für Matching.

**Anwendung auf unser Projekt:**
- Unser Skript verwendet Fuzzy-Matching mit ±5 Zeichen Toleranz (geeignet).
- Wir müssen Metriken nach Entitätstyp melden, nicht nur bestanden/nicht bestanden.

### 2.5 Enterprise Robustness Benchmark (2025)

**Quelle:** [Evaluating Robustness of LLMs in Enterprise Applications](https://arxiv.org/html/2601.06341)

**Wichtige Erkenntnisse:**
- Geringfügige Störungen können die Leistung um bis zu **40 Prozentpunkte** reduzieren.
- Evaluiert werden muss: Textbearbeitungen, Formatänderungen, mehrsprachige Eingaben, Positionsvariationen.
- Modelle mit 4B-120B Parametern zeigen alle Schwachstellen.

**Anwendung auf unser Projekt:**
- Unsere Tests decken Textbearbeitungen und Formatierung ab ✓
- Wir müssen mehrsprachige Tests berücksichtigen (ausländische Namen).

---

## 3. Taxonomie adversarieller Tests (Literatur)

| Kategorie | Unterkategorie | Beispiel | Unsere Abdeckung |
|-----------|----------------|----------|------------------|
| **Label Noise** | Expertenfehler | Falsche Annotation | ❌ N/A (Inferenz) |
| | Crowdsourcing | Inkonsistenzen | ❌ N/A (Inferenz) |
| | LLM-Fehler | Halluzinationen | ❌ N/A (Inferenz) |
| **Input Noise** | OCR-Korruption | l/I, 0/O, Leerzeichen | ✅ 5 Tests |
| | Unicode-Evasion | Kyrillisch, Fullwidth | ✅ 3 Tests |
| | Formatvariation | D.N.I. vs DNI | ✅ Enthalten |
| **Kontext** | Negation | "NICHT DNI haben" | ✅ 1 Test |
| | Beispiel/Illustrativ | "Beispiel: 12345678X" | ✅ 1 Test |
| | Fiktional | Don Quijote | ✅ 1 Test |
| | Gesetzliche Referenzen | Gesetz 15/2022 | ✅ 1 Test |
| **Edge Cases** | Lange Entitäten | Adlige Namen | ✅ 1 Test |
| | Kurze Entitäten | J. García | ✅ 1 Test |
| | Leerzeichen-Entitäten | IBAN mit Leerzeichen | ✅ 2 Tests |
| **Real World** | Dokumentmuster | Notariell, gerichtlich | ✅ 10 Tests |

---

## 4. Empfohlene Metriken

### 4.1 Primärmetriken (seqeval)

| Metrik | Beschreibung | Verwendung |
|---------|-------------|-----|
| **F1 Makro** | Durchschnitt F1 pro Entitätstyp | Hauptmetrik |
| **F1 Mikro** | Globales F1 (alle Entitäten) | Sekundärmetrik |
| **Präzision** | TP / (TP + FP) | Auswertung Falsch Positive |
| **Recall** | TP / (TP + FN) | Auswertung verpasster Entitäten |

### 4.2 Adversarielle Metriken

| Metrik | Beschreibung | Ziel |
|---------|-------------|----------|
| **Pass Rate** | Tests bestanden / Gesamt | ≥70% |
| **OCR Degradation** | F1_clean - F1_ocr | ≤10 Punkte |
| **Kontext-Sensitivität** | % korrekte Kontexttests | ≥80% |
| **FP Rate** | Falsch Positive / Erkennungen | ≤15% |

---

## 5. Identifizierte Lücken in unserem Skript

| Lücke | Schweregrad | Maßnahme |
|-------|-------------|----------|
| Kein Bericht von F1/Präzision/Recall nach Typ | Mittel | seqeval-Metriken hinzufügen |
| Wenige OCR-Tests (5) vs empfohlen (10+) | Mittel | In nächster Iteration erweitern |
| Keine Bewertung der Degradation vs Baseline | Hoch | Vergleich mit sauberen Tests |
| Keine mehrsprachigen Tests | Niedrig | Ausländische Namen hinzufügen |

---

## 6. Empfehlungen für unser Skript

### 6.1 Sofortige Verbesserungen

1. **seqeval-Metriken hinzufügen** - Präzision, Recall, F1 pro Entitätstyp.
2. **Degradation berechnen** - Vergleich mit sauberer Version jedes Tests.
3. **FP-Rate melden** - Falsch Positive als separate Metrik.

### 6.2 Zukünftige Verbesserungen

1. OCR-Tests auf 10+ Fälle mit verschiedenen Korruptionsstufen erweitern.
2. Tests mit ausländischen Namen hinzufügen (John Smith, Mohammed Ali).
3. NoiseBench-artige Evaluierung mit abgestufterm Rauschen implementieren.

---

## 7. Fazit

Das aktuelle Skript deckt die Hauptkategorien der adversariellen Evaluierung laut Literatur ab, muss aber:

1. **Metriken verbessern** - seqeval für F1/P/R nach Typ verwenden.
2. **OCR erweitern** - Mehr Korruptionsstufen.
3. **Degradation berechnen** - vs saubere Baseline.

**Das aktuelle Skript ist GÜLTIG für die initiale Evaluierung**, muss aber iteriert werden, um akademischen Best Practices vollständig zu entsprechen.

---

## Referenzen

1. [NoiseBench: Benchmarking the Impact of Real Label Noise on NER](https://arxiv.org/abs/2405.07609) - ICLR 2024
2. [Context-aware Adversarial Training for Name Regularity Bias](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00386/102846) - MIT TACL
3. [Assessing and Minimizing the Impact of OCR Quality on NER](https://hal.science/hal-03026931/document) - HAL Science
4. [seqeval - Sequence Labeling Evaluation](https://github.com/chakki-works/seqeval) - GitHub
5. [Evaluating Robustness of LLMs in Enterprise Applications](https://arxiv.org/html/2601.06341) - arXiv 2025
6. [nervaluate - Entity-level NER Evaluation](https://github.com/MantisAI/nervaluate) - Based on SemEval'13

---

**Autor:** AlexAlves87
**Datum:** 2026-01-17
