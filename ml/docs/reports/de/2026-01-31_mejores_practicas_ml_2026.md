# Forschung: ML Best Practices 2025-2026 für Legal NER-PII

**Datum:** 31.01.2026
**Autor:** AlexAlves87
**Ziel:** Identifizierung modernster Techniken, die auf die NER-PII-Pipeline von ContextSafe anwendbar sind
**Umfang:** Erstklassige Literatur (ICLR, EMNLP, NeurIPS, NAACL, Nature), veröffentlicht 2025-2026

---

## 1. Management-Zusammenfassung

Systematische Übersicht der aktuellen Literatur (2025-2026) im Bereich maschinelles Lernen angewendet auf Named Entity Recognition (NER) und PII-Erkennung. Es werden **8 signifikante Fortschritte** im Vergleich zu den in unserem vorherigen Bericht (2026-01-30_investigacion_finetuning_legal_xlm_r) dokumentierten Praktiken identifiziert, mit direkten Auswirkungen auf die Trainingsstrategie von Legal-XLM-RoBERTa für ContextSafe.

### Haupterkenntnisse

| # | Technik | Quelle | Auswirkung für ContextSafe |
|---|---------|--------|----------------------------|
| 1 | LoRA/QLoRA mit hohem Rank (128-256) auf allen Schichten | Unsloth, COLING 2025 | Reduziert VRAM von 16GB auf ~4GB ohne F1-Verlust |
| 2 | RandLoRA (full-rank PEFT) | ICLR 2025 | Eliminiert das Standard-LoRA-Plateau |
| 3 | Multi-Perspective Knowledge Distillation | IGI Global 2025 | +2.5-5.8% F1 mit begrenzten Daten |
| 4 | Synthetische LLM-Generierung für NER | EMNLP 2025 | Bootstrap für Sprachen ohne annotiertes Korpus |
| 5 | GLiNER Zero-Shot PII | NAACL 2024 + Updates 2025 | Baseline 81% F1 ohne Training |
| 6 | Hybride NER (Transformer + Regeln) | Nature Sci. Reports 2025 | 94.7% Genauigkeit in Finanzdokumenten |
| 7 | RECAP (Regex + kontextuelles LLM) | NeurIPS 2025 | +82% gegenüber feinabgestimmtem NER, +17% gegenüber Zero-Shot |
| 8 | Selektives DAPT (nicht universell) | ICLR 2025 | DAPT verbessert nicht immer; erfordert vorherige Evaluierung |

### Diagnose: Aktueller Stand vs. Stand der Technik

| Fähigkeit | ContextSafe Aktuell | Stand der Technik 2026 | Lücke |
|-----------|---------------------|------------------------|-------|
| Fine-Tuning | Full FT geplant | LoRA/RandLoRA (PEFT) | **Hoch** |
| Trainingsdaten | Nur Gold-Labels | Gold + Synthetisch (LLM) | **Hoch** |
| NER-Pipeline | Hybrid (Regex+ML) | RECAP (Regex+kontext. LLM) | Mittel |
| Zero-Shot Baseline | Nicht etabliert | GLiNER ~81% F1 | **Hoch** |
| DAPT | Geplant universell | Selektiv (vorher evaluieren) | Mittel |
| Inferenz | ONNX INT8 geplant | LoRA-Adapter + Quantisierung | Niedrig |
| Evaluierung | SemEval Entity-Level | + Adversarial + Cross-Lingual | Mittel |
| Spanisches Legal-Modell | Keine Baseline | MEL (XLM-R-large, 82% F1) | **Hoch** |

---

## 2. Überprüfungsmethodik

### 2.1 Einschlusskriterien

| Kriterium | Wert |
|-----------|------|
| Zeitraum | Januar 2025 - Februar 2026 |
| Venues | ICLR, EMNLP, NeurIPS, NAACL, ACL, Nature, ArXiv (Preprint mit Zitaten) |
| Relevanz | NER, PII, PEFT, DAPT, Legal NLP, Multilingual |
| Sprachen | Multilingual (mit Schwerpunkt auf Spanisch) |

### 2.2 Durchgeführte Suchen

1. "LoRA QLoRA NER fine-tuning 2025 2026 best practices"
2. "knowledge distillation LLM small model NER 2025"
3. "ICL-APT in-context learning augmented pretraining 2025"
4. "Continual Pre-Training is (not) What You Need 2025 legal"
5. "GLiNER zero-shot NER PII detection 2025 2026"
6. "EMNLP 2025 LLM data generation NER multilingual"
7. "hybrid NER transformer rules PII detection 2025"
8. "RandLoRA ICLR 2025 full rank"
9. "MEL legal Spanish language model 2025"

---

## 3. Ergebnisse nach Themenbereich

### 3.1 Parameter-Efficient Fine-Tuning (PEFT)

#### 3.1.1 LoRA/QLoRA: Optimale Konfigurationen 2025-2026

Die aktuelle Literatur konsolidiert Best Practices für LoRA angewendet auf NER:

| Hyperparameter | Empfohlener Wert | Quelle |
|----------------|------------------|--------|
| Rank (r) | 128-256 | Unsloth Docs, Medical NER Studien |
| Alpha (α) | 2×r (256-512) | Heuristik empirisch validiert |
| Target Modules | Attention **+ MLP** (alle Schichten) | Databricks, Lightning AI |
| Lernrate | 2e-4 (Start), Bereich 5e-6 bis 2e-4 | Unsloth, Medium/QuarkAndCode |
| Epochen | 1-3 (Overfitting-Risiko >3) | Konsens mehrerer Quellen |
| Dropout | 0.05 (spezialisierte Domänen) | Medical NER Studien |

**Jüngste empirische Evidenz:**

| Paper | Modell | Aufgabe | F1 | Venue |
|-------|--------|---------|----|-------|
| B2NER | LoRA Adapter ≤50MB | Universal NER (15 Datasets, 6 Sprachen) | +6.8-12.0 F1 vs GPT-4 | COLING 2025 |
| LLaMA-3-8B Financial NER | LoRA r=128 | Financial NER | 0.894 Micro-F1 | ArXiv Jan 2026 |
| Military IE | GRPO + LoRA | Information Extraction | +48.8% absolutes F1 | 2025 |

**LoRA vs QLoRA Entscheidung:**
- **LoRA**: Etwas höhere Geschwindigkeit, ~0.5% genauer, 4× mehr VRAM
- **QLoRA**: Verwenden, wenn VRAM < 8GB oder Modell > 1B Parameter
- **Für Legal-XLM-RoBERTa-base (184M)**: LoRA ist auf RTX 5060 Ti 16GB machbar

#### 3.1.2 RandLoRA: Full-Rank PEFT

**Paper:** "RandLoRA: Full-Rank Parameter-Efficient Fine-Tuning of Large Models"
**Venue:** ICLR 2025 (ArXiv: 2502.00987)

**Gelöstes Problem:**
Standard-LoRA produziert Low-Rank-Updates, was die Repräsentationskapazität einschränkt. Eine Erhöhung des Ranks (r) schließt die Lücke zum Full Fine-Tuning nicht: Es existiert ein *Leistungsplateau*.

**Innovation:**
- Generiert **nicht-trainierbare** zufällige Low-Rank-Matrizen (linear unabhängige Basen)
- Lernt nur **diagonale Skalierungskoeffizienten**
- Linearkombination erzeugt **Full-Rank**-Updates
- Gleiche Anzahl trainierbarer Parameter wie LoRA, aber ohne Rank-Beschränkung

**Ergebnisse:**

| Modell | Aufgabe | LoRA | RandLoRA | Full FT |
|--------|---------|------|----------|---------|
| DinoV2 | Vision | 85.2 | 87.1 | 87.4 |
| CLIP | Vision-Sprache | 78.6 | 81.3 | 82.0 |
| Llama3-8B | Reasoning | 71.2 | 73.8 | 74.1 |

**Implikation:** RandLoRA schließt >90% der Lücke LoRA→Full FT mit denselben trainierbaren Parametern.

### 3.2 Knowledge Distillation (LLM → Kleines Modell)

#### 3.2.1 Multi-Perspective Distillation für NER

**Paper:** "Multi-Perspective Knowledge Distillation of LLM for NER"
**Quelle:** IGI Global Scientific Publishing, 2025

**Pipeline:**
1. **Teacher:** Qwen14B (14B Parameter)
2. **Generierung:** Chain-of-Thought (CoT) zur Generierung von Zwischenüberlegungen zu Entitäten
3. **Alignment:** Multi-perspektivisches Wissen (Entitätstyp, Kontext, Grenzen)
4. **Student:** Kleines NER-Modell mit DoRA (LoRA-Variante)

**Ergebnisse über Stand der Technik:**

| Metrik | Verbesserung |
|--------|--------------|
| Precision | +3.46% |
| Recall | +5.79% |
| F1-Score | +2.54% |

**Zusätzliche Fähigkeit:** Starke Leistung bei Few-Shot (begrenzte Daten).

#### 3.2.2 Anwendung auf ContextSafe

Vorgeschlagene Pipeline:
```
GPT-4 / Llama-3-70B (Teacher)
    ↓ Generiert PII-Annotationen mit CoT-Reasoning
    ↓ Auf unannotierten spanischen Rechtstexten
Legal-XLM-RoBERTa-base (Student)
    ↓ Fine-Tune mit DoRA/LoRA
    ↓ Nutzung generierter Daten + Gold-Labels
Einsatzfähiges PII-Modell (~400MB ONNX)
```

### 3.3 Synthetische Datengenerierung mit LLMs

#### 3.3.1 Rigorose Evaluierung (EMNLP 2025)

**Paper:** "A Rigorous Evaluation of LLM Data Generation Strategies for NER"
**Venue:** EMNLP 2025 Main Conference (Paper ID: 2025.emnlp-main.418)

**Experimentelles Design:**
- **Sprachen:** 11 (einschließlich multilingual)
- **Aufgaben:** 3 verschiedene
- **Generator-LLMs:** 4 Modelle
- **Downstream-Modelle:** 10 (feinabgestimmtes XLM-R)
- **Metrik:** Durchschnittliches F1 Gold vs. Künstlich

**Haupterkenntnisse:**

| Erkenntnis | Evidenz |
|------------|---------|
| Qualität > Quantität | Kleine, saubere, konsistente Datasets übertreffen große verrauschte |
| Format wichtig | Konsistentes JSONL ist kritisch für die Leistung |
| Effektiv für Low-Resource | Synthetische Daten machbar für Sprachen ohne annotiertes Korpus |
| Vergleichbar mit Gold | In einigen Sprachen/Aufgaben erreichen synthetische Daten 90-95% der Gold-Leistung |

#### 3.3.2 Cross-lingual NER Zero-Shot (EMNLP 2025)

**Paper:** "Zero-shot Cross-lingual NER via Mitigating Language Difference: An Entity-aligned Translation Perspective"
**Venue:** EMNLP 2025

**Technik:** Entitäts-ausgerichtete Übersetzung für sprachübergreifenden Transfer. Relevant für die Expansion von ContextSafe auf neue Sprachen ausgehend vom spanischen Modell.

### 3.4 GLiNER: Zero-Shot NER für PII

**Paper:** "GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer"
**Venue:** NAACL 2024 (PII-Modelle aktualisiert September 2025, Wordcab-Kollaboration)

**Architektur:**
- Bidirektionaler Encoder (BiLM)
- Input: Entitätstyp-Prompts + Text
- Output: Parallele Entitätsextraktion (Vorteil gegenüber sequentieller LLM-Generierung)
- Erfordert keine vordefinierten Kategorien: Entitäten zur Laufzeit spezifiziert

**Verfügbare PII-Modelle (2025):**

| Modell | Größe | F1 |
|--------|-------|----|
| gliner-pii-edge-v1.0 | ~100MB | ~75% |
| gliner-pii-small-v1.0 | ~200MB | ~78% |
| gliner-pii-base-v1.0 | ~440MB | **80.99%** |
| gliner-pii-large-v1.0 | ~1.3GB | ~80% |

**Bestehende Integration:** GLiNER integriert sich mit Microsoft Presidio (das ContextSafe bereits nutzt).

**Relevanz:**
- **Sofortige Baseline:** 81% F1 ohne Training, gegen die unser feinabgestimmtes Modell gemessen werden muss
- **Ensemble:** Nutzung von GLiNER für seltene PII-Kategorien, wo keine Trainingsdaten existieren
- **Kreuzvalidierung:** Vergleich von GLiNER-Vorhersagen vs. Legal-XLM-R zur Fehlererkennung

### 3.5 Hybride Ansätze (Transformer + Regeln)

#### 3.5.1 Hybride NER für PII in Finanzdokumenten

**Paper:** "A hybrid rule-based NLP and machine learning approach for PII detection and anonymization in financial documents"
**Venue:** Nature Scientific Reports, 2025 (DOI: 10.1038/s41598-025-04971-9)

**Ergebnisse:**

| Metrik | Synthetisches Dataset | Echte Dokumente |
|--------|-----------------------|-----------------|
| Precision | **94.7%** | ~93% |
| Recall | 89.4% | ~93% |
| F1-Score | 91.1% | ~93% |

**Architektur:** NLP-Regeln + ML + Custom NER, skalierbar.

#### 3.5.2 RECAP: Regex + Kontextuelles LLM

**Paper:** Präsentiert auf der NeurIPS 2025
**Methodik:** Deterministisches Regex + kontextsensitive LLMs für multilinguale PII

**Vergleichsergebnisse:**

| Vergleich | RECAP Verbesserung |
|-----------|--------------------|
| vs feinabgestimmtes NER | **+82% gewichtetes F1** |
| vs Zero-Shot LLMs | **+17% gewichtetes F1** |

**Benchmark:** nervaluate (Evaluierung auf Entitätsebene)

**Implikation für ContextSafe:** Unsere aktuelle Pipeline (Regex + Presidio + RoBERTa) folgt bereits diesem hybriden Muster. RECAP validiert, dass diese Architektur die effektivste nach Evidenzlage 2025 ist.

### 3.6 Domain Adaptive Pre-Training (DAPT): Kritische Prüfung

#### 3.6.1 DAPT ist nicht universell

**Paper:** "Continual Pre-Training is (not) What You Need in Domain Adaptation"
**Venue:** ICLR 2025

**Schlüssel-Schlussfolgerungen:**

| Szenario | Hilft DAPT? | Evidenz |
|----------|-------------|---------|
| Spezialisiertes Vokabular (Recht, Medizin) | **Ja** | Macht mit rechtlichem Stil vertraut |
| Logisches Denken (Zivilrecht) | **Ja** | Verbessert Verständnis von Beziehungen |
| Aufgaben mit vielen Daten | **Nicht unbedingt** | Direktes Fine-Tuning kann ausreichen |
| Ohne Katastrophen-Mitigierung | **Schädlich** | Catastrophic Forgetting verschlechtert Allgemeines |

**Empfohlene Mitigierung:**
- Adapter-Schichten / LoRA während DAPT (kein Full Fine-Tuning des Backbones)
- Graduelles Unfreezing
- Evaluieren VOR und NACH DAPT im NER-PII Benchmark

#### 3.6.2 ICL-APT: Effiziente Alternative

**Konzept:** In-Context Learning Augmented Pre-Training

**Pipeline:**
1. Texte aus Zielkorpus sampeln
2. Ähnliche Dokumente aus Domäne abrufen (Semantisches Retrieval)
3. Kontext mit Definitionen, Abkürzungen, Terminologie erweitern
4. Pre-Training mit MLM auf erweitertem Kontext fortsetzen

**Vorteil:** Effizienter bei begrenztem Korpus. Erfordert keine Millionen von Dokumenten wie traditionelles DAPT.

**Anwendung:** Für jedes spanische Rechtsdokument ähnliche Urteile abrufen + Definitionen von PII-Kategorien als Pre-Training-Kontext hinzufügen.

### 3.7 Spanische Legal-Modelle (Baselines 2025)

#### 3.7.1 MEL (Modelo de Español Legal)

**Paper:** "MEL: Legal Spanish language model"
**Datum:** Januar 2025 (ArXiv: 2501.16011)

| Aspekt | Detail |
|--------|--------|
| Basis | XLM-RoBERTa-large |
| Trainingsdaten | BOE (Boletín Oficial del Estado), Kongresstexte |
| Aufgaben | Rechtliche Klassifikation, NER |
| Macro F1 | ~0.82 (15 Labels) |
| Vergleich | Übertrifft xlm-roberta-large, legal-xlm-roberta-large, RoBERTalex |

#### 3.7.2 3CEL Korpus

**Paper:** "3CEL: a Corpus of Legal Spanish Contract Clauses"
**Datum:** Januar 2025 (ArXiv: 2501.15990)

Korpus spanischer Vertragsklauseln mit Annotationen. Potenziell nützlich als Trainings- oder Evaluierungsdaten.

---

## 4. Obligatorische Vorab-Lektüre

> **WICHTIG:** Vor der Ausführung einer Phase des Plans muss das Modell diese Dokumente in der angegebenen Reihenfolge lesen, um den vollen Projektkontext, getroffene Entscheidungen und den aktuellen Status zu verstehen.

### 4.1 Level 0: Projekt-Identität und Regeln

| # | Datei | Zweck | Obligatorisch |
|---|-------|-------|---------------|
| 0.1 | `ml/README.md` | Operative Regeln, Dateistruktur, Workflow | **Ja** |
| 0.2 | `README.md` (Projektwurzel) | Hexagonale Architektur, ContextSafe-Domäne, NER-Pipeline, Anonymisierungsstufen | **Ja** |

### 4.2 Level 1: ML-Zyklus Historie (in chronologischer Reihenfolge)

Diese Dokumente erzählen die vollständige Evolution des NER v2 Modells, von Baseline bis zum aktuellen Status. Ohne sie wird nicht verstanden, warum bestimmte Entscheidungen getroffen wurden.

| # | Datei | Schlüsselinhalt |
|---|-------|-----------------|
| 1.1 | `docs/reports/2026-01-15_estado_proyecto_ner.md` | Initialer Status des NER-Projekts, v1 vs v2 Modell |
| 1.2 | `docs/reports/2026-01-16_investigacion_pipeline_pii.md` | Untersuchung existierender PII-Pipelines |
| 1.3 | `docs/reports/2026-01-28_investigacion_hybrid_ner.md` | Architekturentscheidung: Hybride Pipeline (Regex+ML) |
| 1.4 | `docs/reports/2026-01-28_investigacion_estandares_evaluacion_ner.md` | Annahme von SemEval 2013 Task 9 (COR/INC/PAR/MIS/SPU) |
| 1.5 | `docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | **ESSENZIELL** - Vollständiger ML-Zyklus: 5 integrierte Elemente, finale Metriken (F1 0.788), gelernte Lektionen |

### 4.3 Level 2: Die 5 Pipeline-Elemente (technisches Detail)

Jedes Element dokumentiert eine konkrete Verbesserung, die in `ner_predictor.py` integriert wurde. Lesen, wenn Verständnis oder Modifikation der Pipeline erforderlich ist.

| # | Datei | Element | Auswirkung |
|---|-------|---------|------------|
| 2.1 | `docs/reports/2026-02-04_text_normalizer_impacto.md` | Elem.1: Textnormalisierung | OCR-Rauschen → sauberer Text |
| 2.2 | `docs/reports/2026-02-04_checksum_validators_standalone.md` | Elem.2: Checksummen-Validierung | DNI, IBAN, NSS mit mathematischer Verifizierung |
| 2.3 | `docs/reports/2026-02-05_regex_patterns_standalone.md` | Elem.3: Spanische Regex-Muster | Kennzeichen, PLZ, Telefone |
| 2.4 | `docs/reports/2026-02-05_date_patterns_integration.md` | Elem.4: Textuelle Daten | "12 de enero de 2024" |
| 2.5 | `docs/reports/2026-02-06_boundary_refinement_integration.md` | Elem.5: Grenzverfeinerung | PAR→COR (16 partielle korrigiert) |

### 4.4 Level 3: Untersuchungen für nächste Phase

Diese Berichte fundieren die Entscheidungen des Fine-Tuning-Plans für Legal-XLM-RoBERTa.

| # | Datei | Schlüsselinhalt |
|---|-------|-----------------|
| 3.1 | `docs/reports/2026-01-29_investigacion_modelos_legales_multilingues.md` | Übersicht rechtlicher Modelle: Legal-BERT, JuriBERT, Legal-XLM-R. Rechtfertigung für Legal-XLM-RoBERTa-base |
| 3.2 | `docs/reports/2026-01-30_investigacion_finetuning_legal_xlm_r.md` | DAPT-Strategien, mDAPT, Span Masking, Hyperparameter. Originaler Fine-Tuning-Plan |
| 3.3 | **Dieses Dokument** (`2026-01-31_mejores_practicas_ml_2026.md`) | Update 2025-2026: LoRA, RandLoRA, synthetische Daten, GLiNER, selektives DAPT. **Aktualisierter Plan** |

### 4.5 Level 4: Ausstehende Design-Implementierungen

| # | Datei | Schlüsselinhalt |
|---|-------|-----------------|
| 4.1 | `docs/plans/2026-02-04_uncertainty_queue_design.md` | Human-in-the-Loop Design: Vertrauenszonen (HIGH/UNCERTAIN/LOW), Review-Queue, Export-Block. **Nicht in ML implementieren**, an Hauptprojekt übertragen |

### 4.6 Level 5: Aktueller Code (Pipeline-Status)

| # | Datei | Zweck |
|---|-------|-------|
| 5.1 | `scripts/inference/ner_predictor.py` | **Vollständige NER-Pipeline** - Integriert 5 Elemente, Haupt-Prädiktor |
| 5.2 | `scripts/inference/text_normalizer.py` | Textnormalisierung (Elem.1) |
| 5.3 | `scripts/inference/entity_validator.py` | Checksummen-Validierung (Elem.2) |
| 5.4 | `scripts/preprocess/boundary_refinement.py` | Grenzverfeinerung (Elem.5) |
| 5.5 | `scripts/preprocess/checksum_validators.py` | Validatoren: DNI, IBAN, NSS, Karten |
| 5.6 | `scripts/evaluate/test_ner_predictor_adversarial_v2.py` | Adversarial Test Set (35 Fälle, SemEval Evaluierung) |
| 5.7 | `scripts/download_legal_xlm_roberta.py` | Basismodell-Download-Skript |

### 4.7 Level 6: Verfügbare Modelle

| # | Pfad | Status |
|---|------|--------|
| 6.1 | `models/checkpoints/roberta-base-bne-capitel-ner/` | Aktuelles Modell (RoBERTa-BNE CAPITEL NER) |
| 6.2 | `models/legal_ner_v1/` | Modell v1 (veraltet) |
| 6.3 | `models/legal_ner_v2/` | Aktuelles v2 Modell (F1 0.788 mit voller Pipeline) |
| 6.4 | `models/pretrained/legal-xlm-roberta-base/` | **Legal-XLM-RoBERTa-base heruntergeladen** (184M Params, 128K Vokabular, 1.48GB) |

### 4.8 Empfohlene Lesereihenfolge nach Aufgabe

| Wenn das Modell... | Level lesen |
|--------------------|-------------|
| Den Fine-Tuning-Plan fortsetzen soll | 0 → 1.5 → 3.1 → 3.2 → 3.3 (dieses Dok) |
| Die NER-Pipeline modifizieren soll | 0 → 1.5 → 2.x (relevantes Element) → 5.1 |
| Baselines evaluieren soll (GLiNER, MEL) | 0 → 1.5 → 3.3 (Abschnitt 4.2 Phase 1) → 5.6 |
| Synthetische Daten generieren soll | 0 → 1.5 → 3.3 (Abschnitt 3.3) |
| DAPT implementieren soll | 0 → 3.1 → 3.2 → 3.3 (Abschnitte 3.6 + 4.2 Phase 4) |
| Uncertainty Queue implementieren soll | 0 → 4.1 (Transfer an Hauptprojekt) |

### 4.9 Aktueller Projektstatus (Snapshot 04. Feb 2026)

```
Aktuelles Modell:       legal_ner_v2 (RoBERTa-BNE + 5 Pipeline-Elemente)
F1 Strict:              0.788 (SemEval Entity-Level, Adversarial Test 35 Fälle)
Pass Rate:              60.0% (Lenient 71.4%)
Heruntergeladenes Rep.: Legal-XLM-RoBERTa-base (184M Params, bereit für FT)
Nächster Schritt:       Baselines etablieren (GLiNER + MEL) → LoRA Fine-Tuning
```

---

## 5. Lückenanalyse und Empfehlungen

### 5.1 Was uns fehlt (Gap Analysis)

| # | Identifizierte Lücke | Priorität | Empfohlene Technik | Quelle |
|---|----------------------|-----------|--------------------|--------|
| **G1** | Keine Zero-Shot Baseline | **Kritisch** | GLiNER-PII-base auf unserem Test-Set evaluieren | NAACL 2024 |
| **G2** | Fine-Tuning als Full FT geplant | **Hoch** | Migration zu LoRA r=128, α=256, alle Schichten | COLING 2025, ICLR 2025 |
| **G3** | Nur Gold-Labels für Training | **Hoch** | Synthetische Daten mit LLM generieren (EMNLP 2025) | EMNLP 2025 |
| **G4** | Keine MEL Baseline | **Hoch** | MEL auf unserem Test-Set evaluieren | ArXiv Jan 2025 |
| **G5** | DAPT ohne vorherige Evaluierung geplant | **Mittel** | NER vor/nach DAPT evaluieren, LoRA nutzen | ICLR 2025 |
| **G6** | RandLoRA nicht genutzt | **Mittel** | Wenn LoRA-Plateau, Migration zu RandLoRA | ICLR 2025 |
| **G7** | Keine Knowledge Distillation | **Mittel** | Pipeline Teacher(LLM)→Student(XLM-R) mit CoT | IGI Global 2025 |
| **G8** | Hybride Pipeline ohne formale Validierung | **Niedrig** | Benchmark RECAP zur Validierung der Architektur | NeurIPS 2025 |

### 5.2 Geordnete Empfehlungen

#### Phase 1: Baselines etablieren (Sofort)

1. **GLiNER-PII-base evaluieren** auf unserem Adversarial Test Set
   - Erwartetes F1: ~81% (veröffentlichter Benchmark)
   - Wenn es unser aktuelles Modell schlägt (F1 0.788): Integration priorisieren
   - Wenn nicht: bestätigt Wettbewerbsfähigkeit unserer Pipeline

2. **MEL evaluieren** (falls verfügbar) auf unserem Test Set
   - Erwartetes F1: ~82% (veröffentlichter Benchmark mit 15 Labels)
   - Etabliert spanische rechtliche Benchmark

#### Phase 2: Fine-Tuning mit PEFT (Nächster Zyklus)

3. **Migration von Full FT zu LoRA**
   - Konfig: r=128, α=256, Target=all_layers, lr=2e-4, Epochen=3, Dropout=0.05
   - Hardware: RTX 5060 Ti 16GB VRAM ist ausreichend
   - Adapter-Größe: ~50MB (vs ~700MB volles Modell)

4. **Wenn Plateau mit LoRA → RandLoRA**
   - Gleiche trainierbare Parameter, Full Rank
   - Schließt >90% der Lücke LoRA→Full FT

#### Phase 3: Datenaugmentierung (Parallel zu Phase 2)

5. **Synthetische PII-Daten mit LLM generieren**
   - Teacher: GPT-4 oder Llama-3-70B
   - Format: Konsistentes CoNLL/JSONL
   - Fokus: Kategorien mit wenigen Beispielen (IBAN, NSS, MATRICULA)
   - Validieren: F1 mit Gold vs Gold+Synthetisch vergleichen

6. **Knowledge Distillation (optional)**
   - Nur wenn begrenzte Daten nach Augmentierung persistieren
   - Pipeline: LLM generiert CoT-Reasoning → Student lernt

#### Phase 4: Selektives DAPT (Nach Phase 2-3)

7. **NER VOR DAPT evaluieren** (Baseline)
8. **DAPT mit LoRA** (nicht Full Backbone FT) auf BOE-Korpus
9. **NER NACH DAPT evaluieren** (Vergleich)
10. **Evidenzbasierte Entscheidung:** Wenn DAPT nicht >2% F1 verbessert, verwerfen

---

## 6. Vergleich: Originalplan vs. Aktualisierter Plan

| Aspekt | Originalplan (Feb 2026) | Aktualisierter Plan (Post-Review) |
|--------|-------------------------|-----------------------------------|
| Fine-Tuning | Full FT | **LoRA r=128 / RandLoRA** |
| Daten | Nur manuelle Gold-Labels | **Gold + Synthetisch LLM** |
| DAPT | Universell, 1-2 Epochen | **Selektiv, vorher/nachher evaluieren** |
| Baseline | Keine | **GLiNER 81% + MEL 82%** |
| Destillation | Nicht betrachtet | **Optional (bei begrenzten Daten)** |
| Evaluierung | SemEval Entity-Level | **+ Adversarial + Cross-Lingual** |
| Adapter-Größe | ~700MB (volles Modell) | **~50MB (LoRA-Adapter)** |
| VRAM erforderlich | ~8GB (Full FT kleiner Batch) | **~4GB (LoRA)** |

---

## 7. Evidenztabelle

| Paper | Venue | Jahr | Technik | Schlüssel-Metrik | URL |
|-------|-------|------|---------|------------------|-----|
| B2NER | COLING | 2025 | LoRA NER Universal | +6.8-12.0 F1 vs GPT-4 | github.com/UmeanNever/B2NER |
| RandLoRA | ICLR | 2025 | Full-Rank PEFT | >90% Lücke LoRA→FT geschlossen | arxiv.org/abs/2502.00987 |
| Multi-Perspective KD | IGI Global | 2025 | Distillation NER | +2.54% F1, +5.79% Recall | igi-global.com/gateway/article/372672 |
| LLM Data Gen for NER | EMNLP | 2025 | Synthetische Daten | 90-95% Gold-Leistung | aclanthology.org/2025.emnlp-main.418 |
| GLiNER PII | NAACL+Updates | 2024-2025 | Zero-Shot PII | 80.99% F1 | huggingface.co/knowledgator/gliner-pii-base-v1.0 |
| Hybrid PII Financial | Nature Sci.Rep | 2025 | Rules+ML PII | 94.7% Precision | doi.org/10.1038/s41598-025-04971-9 |
| RECAP | NeurIPS | 2025 | Regex+LLM PII | +82% vs NER Fine-Tuned | neurips.cc/virtual/2025/122402 |
| CPT is (not) WYNG | ICLR | 2025 | Selektives DAPT | Verbessert nicht einheitlich | openreview.net/pdf?id=rpi9ARgvXc |
| MEL | ArXiv | 2025 | Legal Spanish | 82% Macro F1 (15 Labels) | arxiv.org/html/2501.16011 |
| 3CEL | ArXiv | 2025 | Legal Spanish Corpus | Klauseln Benchmark | arxiv.org/html/2501.15990 |
| Financial NER LLaMA-3 | ArXiv | 2026 | LoRA Financial NER | 0.894 Micro-F1 | arxiv.org/abs/2601.10043 |

---

## 8. Schlussfolgerungen

### 8.1 Paradigmenwechsel 2025-2026

1. **PEFT ersetzt Full Fine-Tuning:** LoRA/RandLoRA ist jetzt der Standard für Modelle ≤1B Parameter. Full FT ist nur gerechtfertigt, wenn LoRA nicht konvergiert (selten bei Basismodellen).

2. **Synthetische LLM-Daten sind machbar:** EMNLP 2025 demonstriert, dass LLM-generierte Daten 90-95% der Gold-Daten-Leistung für multilinguales NER erreichen können. Dies löst den Flaschenhals manueller Annotation.

3. **DAPT ist kein Dogma:** ICLR 2025 zeigt, dass DAPT möglicherweise nicht verbessert und sogar schaden kann, wenn Catastrophic Forgetting nicht gemildert wird. Immer vorher und nachher evaluieren.

4. **Hybrid > Reines ML:** Nature und NeurIPS 2025 bestätigen, dass hybride Ansätze (Regeln + ML) reines ML für PII übertreffen. ContextSafe folgt bereits dieser Architektur.

5. **Zero-Shot NER ist konkurrenzfähig:** GLiNER erreicht 81% F1 ohne Training. Jedes feinabgestimmte Modell muss diese Schwelle signifikant schlagen, um den Aufwand zu rechtfertigen.

### 8.2 Auswirkung auf ContextSafe

Die aktuelle Pipeline von ContextSafe (Regex + Presidio + RoBERTa) ist **architektonisch ausgerichtet** mit der Evidenz 2025-2026. Die Hauptlücken sind operativ:

- **Kein Full FT verwenden** → LoRA/RandLoRA
- **Nicht nur auf Gold-Labels verlassen** → Synthetische LLM-Daten
- **Baselines etablieren** → GLiNER + MEL vor Fine-Tuning
- **Selektives DAPT** → evaluieren, nicht annehmen

### 8.3 Zukünftige Arbeit

| Aufgabe | Priorität | Abhängigkeit |
|---------|-----------|--------------|
| GLiNER-PII auf ContextSafe Test-Set evaluieren | Kritisch | Keine |
| LoRA Fine-Tuning Skript vorbereiten (r=128, α=256) | Hoch | Heruntergeladenes Modell (abgeschlossen) |
| Synthetische PII-Daten mit LLM generieren | Hoch | Zielkategorien definieren |
| MEL auf ContextSafe Test-Set evaluieren | Hoch | MEL-Modell herunterladen |
| Selektives DAPT mit Vorher/Nachher-Evaluierung | Mittel | BOE-Korpus verfügbar |
| RandLoRA implementieren bei Plateau | Mittel | LoRA-Ergebnisse |
| Knowledge Distillation Pipeline | Niedrig | Nur bei unzureichenden Daten |

---

## 9. Referenzen

1. UmeanNever et al. "B2NER: Beyond Boundaries: Learning Universal Entity Taxonomy across Datasets and Languages for Open Named Entity Recognition." COLING 2025. GitHub: github.com/UmeanNever/B2NER

2. Koo et al. "RandLoRA: Full-Rank Parameter-Efficient Fine-Tuning of Large Models." ICLR 2025. ArXiv: 2502.00987

3. "Multi-Perspective Knowledge Distillation of LLM for Named Entity Recognition." IGI Global Scientific Publishing, 2025. igi-global.com/gateway/article/372672

4. "A Rigorous Evaluation of LLM Data Generation Strategies for NER." EMNLP 2025 Main Conference. Paper ID: 2025.emnlp-main.418

5. Urchade Zaratiana et al. "GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer." NAACL 2024. PII Modelle: knowledgator/gliner-pii-base-v1.0 (aktualisiert Sep 2025).

6. "A hybrid rule-based NLP and machine learning approach for PII detection and anonymization in financial documents." Nature Scientific Reports, 2025. DOI: 10.1038/s41598-025-04971-9

7. "RECAP: Deterministic Regex + Context-Aware LLMs for Multilingual PII Detection." NeurIPS 2025. neurips.cc/virtual/2025/122402

8. "Continual Pre-Training is (not) What You Need in Domain Adaptation." ICLR 2025. openreview.net/pdf?id=rpi9ARgvXc

9. "MEL: Legal Spanish language model." ArXiv, Januar 2025. arxiv.org/html/2501.16011

10. "3CEL: a Corpus of Legal Spanish Contract Clauses." ArXiv, Januar 2025. arxiv.org/html/2501.15990

11. "Instruction Finetuning LLaMA-3-8B Model Using LoRA for Financial Named Entity Recognition." ArXiv, Januar 2026. arxiv.org/abs/2601.10043

12. Unsloth Documentation. "LoRA Fine-tuning Hyperparameters Guide." unsloth.ai/docs (2025).

13. Gretel.ai. "GLiNER Models for PII Detection." gretel.ai/blog (2025).

14. Microsoft Presidio. "Using GLiNER with Presidio." microsoft.github.io/presidio (2025).

---

**Generiert von:** AlexAlves87
**Datum:** 31.01.2026
**Revision:** 1.1 (Abschnitt 4: Obligatorische Vorab-Lektüre hinzugefügt)
**Nächster Schritt:** Baselines etablieren (GLiNER + MEL) vor Start des Fine-Tunings
