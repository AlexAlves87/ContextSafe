# Forschung: Best Practices für PII-Erkennungspipelines

**Datum:** 2026-01-16
**Autor:** AlexAlves87
**Typ:** Literaturübersicht
**Status:** Abgeschlossen

---

## Zusammenfassung

Diese Forschung analysiert den Stand der Technik bei der Erkennung von PII (Personally Identifiable Information) mit Fokus auf spanische Rechtsdokumente. Aktuelle akademische Arbeiten (2024-2025) und Produktions-Frameworks wurden überprüft, um Best Practices in Vorverarbeitung, Pipeline-Architektur und Nachverarbeitung zu identifizieren.

**Hauptergebnis:** Die optimale Architektur ist **hybrid** (Regex → NER → Validierung), nicht reines NER mit Nachverarbeitung. Darüber hinaus verbessert die Injektion von OCR-Rauschen (30%) während des Trainings die Robustheit erheblich.

---

## Methodik

### Konsultierte Quellen

| Quelle | Typ | Jahr | Relevanz |
|--------|------|-----|------------|
| PMC12214779 | Akademisches Paper | 2025 | Hybrid NLP-ML für finanzielle PII |
| arXiv 2401.10825v3 | Umfrage | 2024 | NER Stand der Technik |
| Microsoft Presidio | Framework | 2024 | Industrie Best Practices |
| Presidio Research | Toolbox | 2024 | Erkennungs-Evaluierung |

### Suchkriterien

- "NER preprocessing postprocessing best practices 2024"
- "Spanish legal documents PII detection"
- "Hybrid rule-based NLP machine learning PII"
- "Presidio pipeline architecture"

---

## Ergebnisse

### 1. Optimale Pipeline-Architektur

#### 1.1 Verarbeitungsreihenfolge (Presidio)

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Text     │ → │   Regex     │ → │   NLP NER   │ → │  Checksum   │ → │  Threshold  │
│    (OCR)    │    │  Matchers   │    │   Model     │    │ Validation  │    │   Filter    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

**Quelle:** Microsoft Presidio Dokumentation

**Begründung:**
> "Presidio uses its regex matcher to identify matching entities first. Then Natural Language Processing based NER model is used to detect PII autonomously. When possible, a checksum is used to validate the identified PIIs."

#### 1.2 Pipeline-Komponenten

| Komponente | Funktion | Implementierung |
|------------|---------|----------------|
| **Regex Matchers** | Erkennung strukturierter Muster (DNI, IBAN, Telefon) | Ausführung VOR NER |
| **NLP NER** | Erkennung kontextueller Entitäten (Namen, Adressen) | Transformer-Modell |
| **Checksum Validation** | Validierung der Integrität von Identifikatoren | DNI mod-23, IBAN mod-97 |
| **Context Enhancement** | Verbesserung der Zuverlässigkeit durch lexikalischen Kontext | LemmaContextAwareEnhancer |
| **Threshold Filter** | Filtern nach Konfidenz-Score | Konfigurierbar (z.B. 0.7) |

### 2. Vorverarbeitung

#### 2.1 Textnormalisierung

**Quelle:** PMC12214779 (Hybrid NLP-ML)

| Technik | Beschreibung | Anwendbarkeit |
|---------|-------------|---------------|
| Tokenisierung | Aufteilung in diskrete Einheiten | Universell |
| Positionsmarkierung | Zeichen-Ebene Positionsmarkierung | Für Span Recovery |
| Unicode Normalisierung | Fullwidth → ASCII, Zero-Width Entfernung | Hoch für OCR |
| Abkürzungsnormalisierung | D.N.I. → DNI | Hoch für Spanisch |

#### 2.2 Rausch-Injektion (KRITISCH)

**Quelle:** PMC12214779

> "To better simulate real-world document anomalies, data preprocessing adds minor random noise like punctuation removal and text normalization."

**Empfohlene Implementierung:**
```python
# 30% Rauschwahrscheinlichkeit pro Probe
noise_probability = 0.30

# Rauschtypen:
# - Zufällige Entfernung von Satzzeichen
# - OCR-Zeichenersetzung (l↔I, 0↔O)
# - Kollaps/Erweiterung von Leerzeichen
# - Akzentverlust
```

**Auswirkung:** Verbessert die Robustheit gegenüber echten gescannten Dokumenten.

### 3. Modellarchitektur

#### 3.1 NER Stand der Technik (2024)

**Quelle:** arXiv 2401.10825v3

| Architektur | Eigenschaften | F1 Benchmark |
|--------------|-----------------|--------------|
| DeBERTa | Entwirrte Aufmerksamkeit + verbesserter Masken-Decoder | SOTA |
| RoBERTa + CRF | Transformer + Sequenzkohärenz | +4-13% vs Basis |
| BERT + BiLSTM | Kontextuell + sequentielles Modellieren | Robust |
| GLiNER | Globale Aufmerksamkeit für entfernte Entitäten | Innovativ |

#### 3.2 CRF-Layer

**Quelle:** arXiv Survey

> "Applying CRF provides a robust method for NER by ensuring coherent label sequences and modeling dependencies between adjacent labels."

**Vorteil:** Verhindert ungültige Sequenzen wie `B-PERSON I-LOCATION`.

### 4. Nachverarbeitung

#### 4.1 Prüfsummenvalidierung

**Quelle:** Presidio Best Practices

| Typ | Algorithmus | Beispiel |
|------|-----------|---------|
| Spanischer DNI | Buchstabe = "TRWAGMYFPDXBNJZSQVHLCKE"[num % 23] | 12345678Z |
| Spanischer NIE | Präfix X=0, Y=1, Z=2 + DNI Algorithmus | X1234567L |
| IBAN | ISO 7064 Mod 97-10 | ES9121000418450200051332 |
| Spanischer NSS | Mod 97 auf ersten 10 Ziffern | 281234567890 |
| Kreditkarte | Luhn-Algorithmus | 4111111111111111 |

#### 4.2 Kontextbewusste Verbesserung

**Quelle:** Presidio LemmaContextAwareEnhancer

> "The ContextAwareEnhancer is a module that enhances the detection of entities by using the context of the text. It can improve detection of entities that are dependent on context."

**Implementierung:**
- Suche nach Schlüsselwörtern im Fenster von ±N Token
- Erhöhung/Verringerung des Scores basierend auf Kontext
- Beispiel: "DNI" in der Nähe einer Nummer erhöht DNI_NIE Konfidenz

#### 4.3 Schwellenwert-Filterung

**Quelle:** Presidio Tuning Guide

> "Adjust confidence thresholds on ML recognizers to balance missed cases versus over-masking."

**Empfehlung:**
- Hoher Schwellenwert (0.8+): Weniger False Positives, mehr False Negatives
- Niedriger Schwellenwert (0.5-0.6): Mehr Abdeckung, mehr Rauschen
- Initialer Pilot zur Kalibrierung

### 5. Benchmark-Ergebnisse

#### 5.1 Hybrid NLP-ML (PMC12214779)

| Metrik | Wert |
|---------|-------|
| Präzision | 94.7% |
| Recall | 89.4% |
| F1-Score | 91.1% |
| Genauigkeit (Real-World) | 93.0% |

**Erfolgsfaktoren:**
1. Diverse Trainingsdaten (variierte Vorlagen)
2. Leichtgewichtiges Framework (spaCy vs schwere Transformer)
3. Ausgewogene Metriken (Präzision ≈ Recall)
4. Kontextwahrende Anonymisierung

#### 5.2 Presidio Tuning

**Quelle:** Presidio Research Notebook 5

> "Notebook 5 in presidio-research shows how one can configure Presidio to detect PII much more accurately, and boost the F-score by ~30%."

---

## Gap-Analyse

### Vergleich: Aktuelle Implementierung vs Best Practices

| Aspekt | Best Practice | Aktuelle Implementierung | Gap |
|---------|---------------|----------------------|-----|
| Pipeline-Reihenfolge | Regex → NER → Validierung | NER → Nachverarbeitung | **KRITISCH** |
| Rausch-Injektion | 30% im Training | 0% | **KRITISCH** |
| CRF-Layer | Über Transformer hinzufügen | Nicht implementiert | MITTEL |
| Konfidenz-Schwellenwert | Filtern nach Score | Nicht implementiert | MITTEL |
| Kontextverbesserung | Lemma-basiert | Teilweise (Regex) | NIEDRIG |
| Prüfsummenvalidierung | DNI, IBAN, NSS | Implementiert | ✓ OK |
| Formatvalidierung | Regex-Muster | Implementiert | ✓ OK |

### Geschätzte Auswirkung von Korrekturen

| Korrektur | Aufwand | Geschätzte F1-Auswirkung |
|------------|----------|---------------------|
| Rausch-Injektion im Datensatz | Niedrig | +10-15% bei OCR |
| Regex-First Pipeline | Mittel | +5-10% Präzision |
| CRF-Layer | Hoch | +4-13% (Literatur) |
| Konfidenz-Schwellenwert | Niedrig | Reduziert FP 20-30% |

---

## Schlussfolgerungen

### Haupterkenntnisse

1. **Hybride Architektur ist überlegen**: Kombination von Regex (strukturierte Muster) mit NER (kontextuell) übertrifft reine Ansätze.

2. **Reihenfolge ist wichtig**: Regex VOR NER, nicht danach. Presidio nutzt diese Reihenfolge designbedingt.

3. **Rauschen im Training ist kritisch**: 30% Injektion von OCR-Fehlern verbessert Robustheit erheblich.

4. **Prüfsummenvalidierung ist Standard**: Validierung strukturierter Identifikatoren (DNI, IBAN) ist universelle Praxis.

5. **CRF verbessert Kohärenz**: Hinzufügen eines CRF-Layers über Transformer verhindert ungültige Sequenzen.

### Empfehlungen

#### HOHE Priorität (Sofort implementieren)

1. **OCR-Rauschen in Datensatz v3 injizieren**
   - 30% der Proben mit simulierten Fehlern
   - Typen: l↔I, 0↔O, Leerzeichen, fehlende Akzente
   - Modell neu trainieren

2. **Pipeline umstrukturieren**
   ```
   VORHER: Text → NER → Nachverarbeitung
   NACHHER: Text → Vorverarbeitung → Regex → NER → Validierung → Filter
   ```

#### MITTLERE Priorität

3. **Konfidenz-Schwellenwert hinzufügen**
   - Filtern von Entitäten mit Score < 0.7
   - Kalibrierung mit Validierungsset

4. **CRF-Layer evaluieren**
   - Untersuchung `transformers` + `pytorch-crf`
   - Benchmark gegen aktuelles Modell

#### NIEDRIGE Priorität

5. **Erweiterte Kontextverbesserung**
   - Implementierung LemmaContextAwareEnhancer
   - Kontext-Gazelleers pro Entitätstyp

---

## Referenzen

1. **PMC12214779** - "A hybrid rule-based NLP and machine learning approach for PII detection and anonymization in financial documents"
   - URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC12214779/
   - Jahr: 2025

2. **arXiv 2401.10825v3** - "Recent Advances in Named Entity Recognition: A Comprehensive Survey and Comparative Study"
   - URL: https://arxiv.org/html/2401.10825v3
   - Jahr: 2024 (aktualisiert 2025)

3. **Microsoft Presidio** - Best Practices for Developing Recognizers
   - URL: https://microsoft.github.io/presidio/analyzer/developing_recognizers/
   - Jahr: 2024

4. **Presidio Research** - Evaluation Toolbox
   - URL: https://github.com/microsoft/presidio-research
   - Jahr: 2024

5. **Nature Scientific Reports** - "A hybrid rule-based NLP and machine learning approach"
   - URL: https://www.nature.com/articles/s41598-025-04971-9
   - Jahr: 2025

---

**Datum:** 2026-01-16
**Version:** 1.0
