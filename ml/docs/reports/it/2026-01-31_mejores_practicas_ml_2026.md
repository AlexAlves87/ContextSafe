# Ricerca: Best Practices ML 2025-2026 per NER-PII Legale

**Data:** 31-01-2026
**Autor:** AlexAlves87
**Obiettivo:** Identificare tecniche all'avanguardia applicabili al pipeline NER-PII di ContextSafe
**Ambito:** Letteratura di primo piano (ICLR, EMNLP, NeurIPS, NAACL, Nature) pubblicata nel 2025-2026

---

## 1. Riepilogo Esecutivo

Revisione sistematica della letteratura recente (2025-2026) nell'apprendimento automatico applicato al Named Entity Recognition (NER) e al rilevamento di PII. Vengono identificati **8 progressi significativi** rispetto alle pratiche documentate nel nostro precedente rapporto (2026-01-30_investigacion_finetuning_legal_xlm_r), con un impatto diretto sulla strategia di addestramento di Legal-XLM-RoBERTa per ContextSafe.

### Risultati Principali

| # | Tecnica | Fonte | Impatto per ContextSafe |
|---|---------|-------|-------------------------|
| 1 | LoRA/QLoRA con rank alto (128-256) su tutti i livelli | Unsloth, COLING 2025 | Riduce la VRAM da 16GB a ~4GB senza perdita di F1 |
| 2 | RandLoRA (full-rank PEFT) | ICLR 2025 | Elimina il plateau del LoRA standard |
| 3 | Knowledge Distillation multi-prospettiva | IGI Global 2025 | +2.5-5.8% F1 con dati limitati |
| 4 | Generazione sintetica LLM per NER | EMNLP 2025 | Bootstrap per lingue senza corpus annotato |
| 5 | GLiNER zero-shot PII | NAACL 2024 + aggiornamenti 2025 | Baseline 81% F1 senza addestramento |
| 6 | NER Ibrido (transformer + regole) | Nature Sci. Reports 2025 | 94.7% precisione in documenti finanziari |
| 7 | RECAP (regex + LLM contestuale) | NeurIPS 2025 | +82% su NER fine-tuned, +17% su zero-shot |
| 8 | DAPT selettivo (non universale) | ICLR 2025 | DAPT non migliora sempre; richiede valutazione previa |

### Diagnosi: Stato Attuale vs Stato dell'Arte

| Capacità | ContextSafe Attuale | Stato dell'Arte 2026 | Gap |
|----------|---------------------|----------------------|-----|
| Fine-tuning | Full FT pianificato | LoRA/RandLoRA (PEFT) | **Alto** |
| Dati di addestramento | Solo gold labels | Gold + sintetici (LLM) | **Alto** |
| Pipeline NER | Ibrido (regex+ML) | RECAP (regex+LLM contestuale) | Medio |
| Zero-shot baseline | Non stabilito | GLiNER ~81% F1 | **Alto** |
| DAPT | Pianificato universale | Selettivo (valutare prima) | Medio |
| Inferenza | ONNX INT8 pianificato | LoRA adapters + quantizzazione | Basso |
| Valutazione | SemEval entity-level | + adversarial + cross-lingual | Medio |
| Modello legale spagnolo | Nessuna baseline | MEL (XLM-R-large, 82% F1) | **Alto** |

---

## 2. Metodologia di Revisione

### 2.1 Criteri di Inclusione

| Criterio | Valore |
|----------|--------|
| Periodo | Gennaio 2025 - Febbraio 2026 |
| Sedi | ICLR, EMNLP, NeurIPS, NAACL, ACL, Nature, ArXiv (pre-print con citazioni) |
| Rilevanza | NER, PII, PEFT, DAPT, NLP legale, multilingue |
| Lingue | Multilingue (con enfasi sullo spagnolo) |

### 2.2 Ricerche Effettuate

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

## 3. Risultati per Area Tematica

### 3.1 Parameter-Efficient Fine-Tuning (PEFT)

#### 3.1.1 LoRA/QLoRA: Configurazioni Ottimali 2025-2026

La letteratura recente consolida le migliori pratiche per LoRA applicato a NER:

| Iperparametro | Valore Raccomandato | Fonte |
|---------------|---------------------|-------|
| Rank (r) | 128-256 | Documentazione Unsloth, Studi NER medici |
| Alpha (α) | 2×r (256-512) | Euristica validata empiricamente |
| Moduli target | Attenzione **+ MLP** (tutti i livelli) | Databricks, Lightning AI |
| Learning rate | 2e-4 (inizio), range 5e-6 a 2e-4 | Unsloth, Medium/QuarkAndCode |
| Epochs | 1-3 (rischio overfitting >3) | Consenso fonti multiple |
| Dropout | 0.05 (domini specializzati) | Studi NER medici |

**Evidenza empirica recente:**

| Paper | Modello | Task | F1 | Sede |
|-------|---------|------|----|------|
| B2NER | LoRA adapters ≤50MB | NER universale (15 dataset, 6 lingue) | +6.8-12.0 F1 vs GPT-4 | COLING 2025 |
| LLaMA-3-8B Financial NER | LoRA r=128 | NER finanziario | 0.894 micro-F1 | ArXiv Gen 2026 |
| Military IE | GRPO + LoRA | Estrazione Informazioni | +48.8% F1 assoluto | 2025 |

**Decisione LoRA vs QLoRA:**
- **LoRA**: Velocità leggermente superiore, ~0.5% più preciso, 4× più VRAM
- **QLoRA**: Usare quando VRAM < 8GB o modello > 1B parametri
- **Per Legal-XLM-RoBERTa-base (184M)**: LoRA è fattibile su RTX 5060 Ti 16GB

#### 3.1.2 RandLoRA: PEFT a Rango Completo

**Paper:** "RandLoRA: Full-Rank Parameter-Efficient Fine-Tuning of Large Models"
**Sede:** ICLR 2025 (ArXiv: 2502.00987)

**Problema risolto:**
LoRA standard produce aggiornamenti di basso rango, limitando la capacità di rappresentazione. Aumentare il rango (r) non colma il divario con il full fine-tuning: esiste un *plateau* di prestazioni.

**Innovazione:**
- Genera matrici casuali di basso rango **non addestrabili** (basi linearmente indipendenti)
- Apprende solo **coefficienti diagonali** di scalatura
- La combinazione lineare produce aggiornamenti di **rango completo**
- Stessa quantità di parametri addestrabili di LoRA, ma senza restrizione di rango

**Risultati:**

| Modello | Task | LoRA | RandLoRA | Full FT |
|---------|------|------|----------|---------|
| DinoV2 | Visione | 85.2 | 87.1 | 87.4 |
| CLIP | Visione-linguaggio | 78.6 | 81.3 | 82.0 |
| Llama3-8B | Ragionamento | 71.2 | 73.8 | 74.1 |

**Implicazione:** RandLoRA chiude >90% del gap LoRA→Full FT con gli stessi parametri addestrabili.

### 3.2 Knowledge Distillation (LLM → Modello Piccolo)

#### 3.2.1 Distillazione Multi-Prospettiva per NER

**Paper:** "Multi-Perspective Knowledge Distillation of LLM for NER"
**Fonte:** IGI Global Scientific Publishing, 2025

**Pipeline:**
1. **Insegnante:** Qwen14B (14B parametri)
2. **Generazione:** Chain-of-Thought (CoT) per generare ragionamento intermedio sulle entità
3. **Allineamento:** Conoscenza multi-prospettiva (tipo di entità, contesto, confini)
4. **Studente:** Piccolo modello NER con DoRA (variante di LoRA)

**Risultati sullo stato dell'arte:**

| Metrica | Miglioramento |
|---------|---------------|
| Precisione | +3.46% |
| Richiamo | +5.79% |
| F1-score | +2.54% |

**Capacità aggiuntiva:** Prestazioni forti in few-shot (dati limitati).

#### 3.2.2 Applicazione a ContextSafe

Pipeline proposta:
```
GPT-4 / Llama-3-70B (insegnante)
    ↓ Genera annotazioni PII con ragionamento CoT
    ↓ Su testi legali spagnoli non annotati
Legal-XLM-RoBERTa-base (studente)
    ↓ Fine-tune con DoRA/LoRA
    ↓ Usando dati generati + gold labels
Modello PII dispiegabile (~400MB ONNX)
```

### 3.3 Generazione Sintetica di Dati con LLM

#### 3.3.1 Valutazione Rigorosa (EMNLP 2025)

**Paper:** "A Rigorous Evaluation of LLM Data Generation Strategies for NER"
**Sede:** EMNLP 2025 Main Conference (Paper ID: 2025.emnlp-main.418)

**Disegno sperimentale:**
- **Lingue:** 11 (incluso multilingue)
- **Task:** 3 diversi
- **LLM generatori:** 4 modelli
- **Modelli downstream:** 10 (fine-tuned XLM-R)
- **Metrica:** F1 medio gold vs artificiale

**Scoperte chiave:**

| Scoperta | Evidenza |
|----------|----------|
| Qualità > Quantità | Dataset piccoli, puliti e coerenti superano dataset grandi e rumorosi |
| Il formato conta | JSONL coerente è critico per le prestazioni |
| Efficace per low-resource | Dati sintetici fattibili per lingue senza corpus annotato |
| Paragonabile a gold | In alcune lingue/task, i dati sintetici raggiungono il 90-95% delle prestazioni gold |

#### 3.3.2 Cross-lingual NER Zero-shot (EMNLP 2025)

**Paper:** "Zero-shot Cross-lingual NER via Mitigating Language Difference: An Entity-aligned Translation Perspective"
**Sede:** EMNLP 2025

**Tecnica:** Traduzione allineata alle entità per il trasferimento multilingue. Rilevante per espandere ContextSafe a nuove lingue partendo dal modello spagnolo.

### 3.4 GLiNER: Zero-Shot NER per PII

**Paper:** "GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer"
**Sede:** NAACL 2024 (modelli PII aggiornati settembre 2025, collaborazione Wordcab)

**Architettura:**
- Encoder bidirezionale (BiLM)
- Input: prompt di tipo entità + testo
- Output: estrazione parallela di entità (vantaggio sulla generazione sequenziale di LLM)
- Non richiede categorie predefinite: entità specificate a runtime

**Modelli PII disponibili (2025):**

| Modello | Dimensione | F1 |
|---------|------------|----|
| gliner-pii-edge-v1.0 | ~100MB | ~75% |
| gliner-pii-small-v1.0 | ~200MB | ~78% |
| gliner-pii-base-v1.0 | ~440MB | **80.99%** |
| gliner-pii-large-v1.0 | ~1.3GB | ~80% |

**Integrazione esistente:** GLiNER si integra con Microsoft Presidio (che ContextSafe usa già).

**Rilevanza:**
- **Baseline immediata:** 81% F1 senza addestramento, contro cui misurare il nostro modello fine-tuned
- **Ensemble:** Usare GLiNER per categorie PII rare dove non ci sono dati di addestramento
- **Validazione incrociata:** Confrontare previsioni GLiNER vs Legal-XLM-R per rilevare errori

### 3.5 Approcci Ibridi (Transformer + Regole)

#### 3.5.1 Hybrid NER per PII in Documenti Finanziari

**Paper:** "A hybrid rule-based NLP and machine learning approach for PII detection and anonymization in financial documents"
**Sede:** Nature Scientific Reports, 2025 (DOI: 10.1038/s41598-025-04971-9)

**Risultati:**

| Metrica | Dataset Sintetico | Documenti Reali |
|---------|-------------------|-----------------|
| Precisione | **94.7%** | ~93% |
| Richiamo | 89.4% | ~93% |
| F1-score | 91.1% | ~93% |

**Architettura:** Regole NLP + ML + Custom NER, scalabile.

#### 3.5.2 RECAP: Regex + LLM Contestuale

**Paper:** Presentato a NeurIPS 2025
**Metodologia:** Regex deterministico + LLM context-aware per PII multilingue

**Risultati comparativi:**

| Confronto | Miglioramento RECAP |
|-----------|---------------------|
| vs NER fine-tuned | **+82% F1 ponderato** |
| vs zero-shot LLM | **+17% F1 ponderato** |

**Benchmark:** nervaluate (valutazione a livello di entità)

**Implicazione per ContextSafe:** Il nostro pipeline attuale (Regex + Presidio + RoBERTa) segue già questo pattern ibrido. RECAP convalida che questa architettura è la più efficace secondo l'evidenza del 2025.

### 3.6 Domain Adaptive Pre-Training (DAPT): Revisione Critica

#### 3.6.1 DAPT Non è Universale

**Paper:** "Continual Pre-Training is (not) What You Need in Domain Adaptation"
**Sede:** ICLR 2025

**Conclusioni chiave:**

| Scenario | DAPT Aiuta? | Evidenza |
|----------|-------------|----------|
| Vocabolario specializzato (legale, medico) | **Sì** | Familiarizza con lo stile legale |
| Ragionamento logico (diritto civile) | **Sì** | Migliora la comprensione delle relazioni |
| Task con dati abbondanti | **Non necessariamente** | Il fine-tuning diretto può essere sufficiente |
| Senza mitigazione della catastrofe | **Dannoso** | Il catastrophic forgetting degrada il generale |

**Mitigazione raccomandata:**
- Livelli adapter / LoRA durante DAPT (no full fine-tuning del backbone)
- Unfreezing graduale
- Valutare PRIMA e DOPO DAPT su benchmark NER-PII

#### 3.6.2 ICL-APT: Alternativa Efficiente

**Concetto:** In-Context Learning Augmented Pre-Training

**Pipeline:**
1. Campionare testi dal corpus target
2. Recuperare documenti simili dal dominio (recupero semantico)
3. Aumentare il contesto con definizioni, abbreviazioni, terminologia
4. Continuare il pre-training con MLM su contesto aumentato

**Vantaggio:** Più efficiente con corpus limitato. Non richiede milioni di documenti come il DAPT tradizionale.

**Applicazione:** Per ogni documento legale spagnolo, recuperare sentenze simili + aggiungere definizioni di categorie PII come contesto di pre-training.

### 3.7 Modelli Legali Spagnoli (Baseline 2025)

#### 3.7.1 MEL (Modelo de Español Legal)

**Paper:** "MEL: Legal Spanish language model"
**Data:** Gennaio 2025 (ArXiv: 2501.16011)

| Aspetto | Dettaglio |
|---------|-----------|
| Base | XLM-RoBERTa-large |
| Dati addestramento | BOE (Gazzetta Ufficiale), testi congresso |
| Task | Classificazione legale, NER |
| F1 macro | ~0.82 (15 etichette) |
| Confronto | Supera xlm-roberta-large, legal-xlm-roberta-large, RoBERTalex |

#### 3.7.2 Corpus 3CEL

**Paper:** "3CEL: a Corpus of Legal Spanish Contract Clauses"
**Data:** Gennaio 2025 (ArXiv: 2501.15990)

Corpus di clausole contrattuali spagnole con annotazioni. Potenzialmente utile come dati di addestramento o valutazione.

---

## 4. Letture Preliminari Obbligatorie

> **IMPORTANTE:** Prima di eseguire qualsiasi fase del piano, il modello deve leggere questi documenti nell'ordine indicato per comprendere il contesto completo del progetto, le decisioni prese e lo stato attuale.

### 4.1 Livello 0: Identità e Regole del Progetto

| # | File | Scopo | Obbligatorio |
|---|------|-------|--------------|
| 0.1 | `ml/README.md` | Regole operative, struttura file, flusso di lavoro | **Sì** |
| 0.2 | `README.md` (radice progetto) | Architettura esagonale, dominio ContextSafe, pipeline NER, livelli anonimizzazione | **Sì** |

### 4.2 Livello 1: Storia del Ciclo ML (leggere in ordine cronologico)

Questi documenti narrano l'evoluzione completa del modello NER v2, dalla baseline allo stato attuale. Senza di essi non si comprende perché sono state prese certe decisioni.

| # | File | Contenuto Chiave |
|---|------|------------------|
| 1.1 | `docs/reports/2026-01-15_estado_proyecto_ner.md` | Stato iniziale del progetto NER, modello v1 vs v2 |
| 1.2 | `docs/reports/2026-01-16_investigacion_pipeline_pii.md` | Ricerca pipeline PII esistenti |
| 1.3 | `docs/reports/2026-01-28_investigacion_hybrid_ner.md` | Decisione architetturale: pipeline ibrida (Regex+ML) |
| 1.4 | `docs/reports/2026-01-28_investigacion_estandares_evaluacion_ner.md` | Adozione SemEval 2013 Task 9 (COR/INC/PAR/MIS/SPU) |
| 1.5 | `docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | **ESSENZIALE** - Ciclo ML completo: 5 elementi integrati, metriche finali (F1 0.788), lezioni apprese |

### 4.3 Livello 2: I 5 Elementi del Pipeline (dettaglio tecnico)

Ogni elemento documenta un miglioramento concreto integrato in `ner_predictor.py`. Leggere se necessario comprendere o modificare il pipeline.

| # | File | Elemento | Impatto |
|---|------|----------|---------|
| 2.1 | `docs/reports/2026-02-04_text_normalizer_impacto.md` | Elem.1: Normalizzazione testo | Rumore OCR → testo pulito |
| 2.2 | `docs/reports/2026-02-04_checksum_validators_standalone.md` | Elem.2: Validazione checksum | DNI, IBAN, NSS con verifica matematica |
| 2.3 | `docs/reports/2026-02-05_regex_patterns_standalone.md` | Elem.3: Pattern regex spagnoli | Targhe, CAP, telefoni |
| 2.4 | `docs/reports/2026-02-05_date_patterns_integration.md` | Elem.4: Date testuali | "12 de enero de 2024" |
| 2.5 | `docs/reports/2026-02-06_boundary_refinement_integration.md` | Elem.5: Raffinamento confini | PAR→COR (16 parziali corretti) |

### 4.4 Livello 3: Investigazioni per la Fase Successiva

Questi rapporti fondano le decisioni del piano di fine-tuning di Legal-XLM-RoBERTa.

| # | File | Contenuto Chiave |
|---|------|------------------|
| 3.1 | `docs/reports/2026-01-29_investigacion_modelos_legales_multilingues.md` | Sondaggio modelli legali: Legal-BERT, JuriBERT, Legal-XLM-R. Giustificazione di Legal-XLM-RoBERTa-base |
| 3.2 | `docs/reports/2026-01-30_investigacion_finetuning_legal_xlm_r.md` | Strategie DAPT, mDAPT, span masking, iperparametri. Piano originale di fine-tuning |
| 3.3 | **Questo documento** (`2026-01-31_mejores_practicas_ml_2026.md`) | Aggiornamento 2025-2026: LoRA, RandLoRA, dati sintetici, GLiNER, DAPT selettivo. **Piano aggiornato** |

### 4.5 Livello 4: Design in Attesa di Implementazione

| # | File | Contenuto Chiave |
|---|------|------------------|
| 4.1 | `docs/plans/2026-02-04_uncertainty_queue_design.md` | Design Human-in-the-Loop: zone di fiducia (HIGH/UNCERTAIN/LOW), coda di revisione, blocco esportazione. **Non implementare in ML**, trasferito al progetto principale |

### 4.6 Livello 5: Codice Attuale (stato del pipeline)

| # | File | Scopo |
|---|------|-------|
| 5.1 | `scripts/inference/ner_predictor.py` | **Pipeline NER Completo** - Integra i 5 elementi, predittore principale |
| 5.2 | `scripts/inference/text_normalizer.py` | Normalizzazione testo (Elem.1) |
| 5.3 | `scripts/inference/entity_validator.py` | Validazione checksum (Elem.2) |
| 5.4 | `scripts/preprocess/boundary_refinement.py` | Raffinamento confini (Elem.5) |
| 5.5 | `scripts/preprocess/checksum_validators.py` | Validatori: DNI, IBAN, NSS, carte |
| 5.6 | `scripts/evaluate/test_ner_predictor_adversarial_v2.py` | Test set adversarial (35 casi, valutazione SemEval) |
| 5.7 | `scripts/download_legal_xlm_roberta.py` | Script download modello base |

### 4.7 Livello 6: Modelli Disponibili

| # | Percorso | Stato |
|---|----------|-------|
| 6.1 | `models/checkpoints/roberta-base-bne-capitel-ner/` | Modello attuale (RoBERTa-BNE CAPITEL NER) |
| 6.2 | `models/legal_ner_v1/` | Modello v1 (deprecato) |
| 6.3 | `models/legal_ner_v2/` | Modello v2 attuale (F1 0.788 con pipeline completo) |
| 6.4 | `models/pretrained/legal-xlm-roberta-base/` | **Legal-XLM-RoBERTa-base scaricato** (184M params, 128K vocab, 1.48GB) |

### 4.8 Ordine di Lettura Raccomandato per Task

| Se il modello deve... | Leggere livelli |
|-----------------------|-----------------|
| Continuare il piano di fine-tuning | 0 → 1.5 → 3.1 → 3.2 → 3.3 (questo doc) |
| Modificare il pipeline NER | 0 → 1.5 → 2.x (elemento rilevante) → 5.1 |
| Valutare baseline (GLiNER, MEL) | 0 → 1.5 → 3.3 (sezione 4.2 Fase 1) → 5.6 |
| Generare dati sintetici | 0 → 1.5 → 3.3 (sezione 3.3) |
| Implementare DAPT | 0 → 3.1 → 3.2 → 3.3 (sezioni 3.6 + 4.2 Fase 4) |
| Implementare Uncertainty Queue | 0 → 4.1 (trasferire al progetto principale) |

### 4.9 Stato Attuale del Progetto (Snapshot 04 Feb 2026)

```
Modello attuale:    legal_ner_v2 (RoBERTa-BNE + 5 elementi pipeline)
F1 strict:          0.788 (SemEval entity-level, test adversarial 35 casi)
Pass rate:          60.0% (lenient 71.4%)
Modello scaricato:  Legal-XLM-RoBERTa-base (184M params, pronto per FT)
Prossimo passo:     Stabilire baseline (GLiNER + MEL) → LoRA fine-tuning
```

---

## 5. Analisi dei Gap e Raccomandazioni

### 5.1 Cosa Ci Manca (Gap Analysis)

| # | Gap Identificato | Priorità | Tecnica Raccomandata | Fonte |
|---|------------------|----------|----------------------|-------|
| **G1** | Nessuna baseline zero-shot | **Critico** | Valutare GLiNER-PII-base sul nostro test set | NAACL 2024 |
| **G2** | Fine-tuning pianificato come Full FT | **Alto** | Migrare a LoRA r=128, α=256, tutti i livelli | COLING 2025, ICLR 2025 |
| **G3** | Solo gold labels per addestramento | **Alto** | Generare dati sintetici con LLM (EMNLP 2025) | EMNLP 2025 |
| **G4** | Nessuna baseline MEL | **Alto** | Valutare MEL sul nostro test set | ArXiv Gen 2025 |
| **G5** | DAPT pianificato senza valutazione previa | **Medio** | Valutare NER prima/dopo DAPT, usare LoRA | ICLR 2025 |
| **G6** | RandLoRA non usato | **Medio** | Se plateau LoRA, migrare a RandLoRA | ICLR 2025 |
| **G7** | Nessuna knowledge distillation | **Medio** | Pipeline teacher(LLM)→student(XLM-R) con CoT | IGI Global 2025 |
| **G8** | Pipeline ibrido senza validazione formale | **Basso** | Benchmark RECAP per convalidare architettura | NeurIPS 2025 |

### 5.2 Raccomandazioni Ordinate

#### Fase 1: Stabilire Baseline (Immediato)

1. **Valutare GLiNER-PII-base** sul nostro test set adversarial
   - F1 atteso: ~81% (benchmark pubblicato)
   - Se supera il nostro modello attuale (F1 0.788): dare priorità all'integrazione
   - Se no: conferma che il nostro pipeline è competitivo

2. **Valutare MEL** (se disponibile) sul nostro test set
   - F1 atteso: ~82% (benchmark pubblicato con 15 etichette)
   - Stabilisce un benchmark legale spagnolo

#### Fase 2: Fine-tuning con PEFT (Ciclo Successivo)

3. **Migrare da Full FT a LoRA**
   - Config: r=128, α=256, target=all_layers, lr=2e-4, epochs=3, dropout=0.05
   - Hardware: RTX 5060 Ti 16GB VRAM è sufficiente
   - Dimensione adapter: ~50MB (vs ~700MB modello completo)

4. **Se plateau con LoRA → RandLoRA**
   - Stessi parametri addestrabili, rango completo
   - Chiude >90% del divario LoRA→Full FT

#### Fase 3: Aumento dei Dati (Parallelo alla Fase 2)

5. **Generare dati sintetici PII con LLM**
   - Insegnante: GPT-4 o Llama-3-70B
   - Formato: CoNLL/JSONL coerente
   - Focus: categorie con pochi esempi (IBAN, NSS, MATRICULA)
   - Validare: confrontare F1 con gold vs gold+sintetico

6. **Knowledge distillation (opzionale)**
   - Solo se persistono dati limitati dopo l'aumento
   - Pipeline: LLM genera ragionamento CoT → studente apprende

#### Fase 4: DAPT Selettivo (Dopo Fase 2-3)

7. **Valutare NER PRIMA DAPT** (baseline)
8. **DAPT con LoRA** (no full backbone FT) su corpus BOE
9. **Valutare NER DOPO DAPT** (confrontare)
10. **Decisione basata sull'evidenza:** se DAPT non migliora >2% F1, scartare

---

## 6. Confronto: Piano Originale vs. Piano Aggiornato

| Aspetto | Piano Originale (Feb 2026) | Piano Aggiornato (Post-Revisione) |
|---------|----------------------------|-----------------------------------|
| Fine-tuning | Full FT | **LoRA r=128 / RandLoRA** |
| Dati | Solo gold labels manuali | **Gold + sintetici LLM** |
| DAPT | Universale, 1-2 epoche | **Selettivo, valutare prima/dopo** |
| Baseline | Nessuna | **GLiNER 81% + MEL 82%** |
| Distillazione | Non considerata | **Opzionale (se dati limitati)** |
| Valutazione | SemEval entity-level | **+ adversarial + cross-lingual** |
| Dimensione adapter | ~700MB (modello completo) | **~50MB (LoRA adapter)** |
| VRAM richiesta | ~8GB (Full FT batch piccolo) | **~4GB (LoRA)** |

---

## 7. Tabella delle Evidenze

| Paper | Sede | Anno | Tecnica | Metrica Chiave | URL |
|-------|------|------|---------|----------------|-----|
| B2NER | COLING | 2025 | LoRA NER universale | +6.8-12.0 F1 vs GPT-4 | github.com/UmeanNever/B2NER |
| RandLoRA | ICLR | 2025 | Full-rank PEFT | >90% gap LoRA→FT chiuso | arxiv.org/abs/2502.00987 |
| Multi-Perspective KD | IGI Global | 2025 | Distillazione NER | +2.54% F1, +5.79% Richiamo | igi-global.com/gateway/article/372672 |
| LLM Data Gen for NER | EMNLP | 2025 | Dati sintetici | 90-95% prestazione gold | aclanthology.org/2025.emnlp-main.418 |
| GLiNER PII | NAACL+updates | 2024-2025 | Zero-shot PII | 80.99% F1 | huggingface.co/knowledgator/gliner-pii-base-v1.0 |
| Hybrid PII Financial | Nature Sci.Rep | 2025 | Regole+ML PII | 94.7% precisione | doi.org/10.1038/s41598-025-04971-9 |
| RECAP | NeurIPS | 2025 | Regex+LLM PII | +82% vs NER fine-tuned | neurips.cc/virtual/2025/122402 |
| CPT is (not) WYNG | ICLR | 2025 | DAPT selettivo | Non migliora uniformemente | openreview.net/pdf?id=rpi9ARgvXc |
| MEL | ArXiv | 2025 | Spagnolo legale | 82% F1 macro (15 etichette) | arxiv.org/html/2501.16011 |
| 3CEL | ArXiv | 2025 | Corpus Spagnolo legale | Benchmark clausole | arxiv.org/html/2501.15990 |
| Financial NER LLaMA-3 | ArXiv | 2026 | LoRA NER Finanziario | 0.894 micro-F1 | arxiv.org/abs/2601.10043 |

---

## 8. Conclusioni

### 8.1 Cambiamenti di Paradigma 2025-2026

1. **PEFT sostituisce Full Fine-Tuning:** LoRA/RandLoRA è ora lo standard per modelli ≤1B parametri. Full FT è giustificato solo se LoRA non converge (raro nei modelli base).

2. **Dati Sintetici LLM sono Fattibili:** EMNLP 2025 dimostra che i dati generati da LLM possono raggiungere il 90-95% delle prestazioni dei dati gold per NER multilingue. Questo risolve il collo di bottiglia dell'annotazione manuale.

3. **DAPT non è un Dogma:** ICLR 2025 dimostra che DAPT può non migliorare e persino danneggiare se il catastrophic forgetting non viene mitigato. Valutare sempre prima e dopo.

4. **Ibrido > Puro ML:** Nature e NeurIPS 2025 confermano che gli approcci ibridi (regole + ML) superano il puro ML per PII. ContextSafe segue già questa architettura.

5. **Zero-shot NER è Competitivo:** GLiNER raggiunge 81% F1 senza addestramento. Qualsiasi modello fine-tuned deve battere significativamente questa soglia per giustificare lo sforzo.

### 8.2 Impatto su ContextSafe

Il pipeline attuale di ContextSafe (Regex + Presidio + RoBERTa) è **architettonicamente allineato** con l'evidenza 2025-2026. I gap principali sono operativi:

- **Non usare Full FT** → LoRA/RandLoRA
- **Non fare affidamento solo su gold labels** → dati sintetici LLM
- **Stabilire baseline** → GLiNER + MEL prima del fine-tuning
- **DAPT selettivo** → valutare, non assumere

### 8.3 Lavoro Futuro

| Task | Priorità | Dipendenza |
|------|----------|------------|
| Valutare GLiNER-PII su test set ContextSafe | Critica | Nessuna |
| Preparare script LoRA fine-tuning (r=128, α=256) | Alta | Modello scaricato (completato) |
| Generare dati sintetici PII con LLM | Alta | Definire categorie target |
| Valutare MEL su test set ContextSafe | Alta | Scaricare modello MEL |
| DAPT selettivo con valutazione pre/post | Media | Corpus BOE disponibile |
| Implementare RandLoRA se plateau | Media | Risultati LoRA |
| Pipeline knowledge distillation | Bassa | Solo se dati insufficienti |

---

## 9. Riferimenti

1. UmeanNever et al. "B2NER: Beyond Boundaries: Learning Universal Entity Taxonomy across Datasets and Languages for Open Named Entity Recognition." COLING 2025. GitHub: github.com/UmeanNever/B2NER

2. Koo et al. "RandLoRA: Full-Rank Parameter-Efficient Fine-Tuning of Large Models." ICLR 2025. ArXiv: 2502.00987

3. "Multi-Perspective Knowledge Distillation of LLM for Named Entity Recognition." IGI Global Scientific Publishing, 2025. igi-global.com/gateway/article/372672

4. "A Rigorous Evaluation of LLM Data Generation Strategies for NER." EMNLP 2025 Main Conference. Paper ID: 2025.emnlp-main.418

5. Urchade Zaratiana et al. "GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer." NAACL 2024. Modelli PII: knowledgator/gliner-pii-base-v1.0 (aggiornato Set 2025).

6. "A hybrid rule-based NLP and machine learning approach for PII detection and anonymization in financial documents." Nature Scientific Reports, 2025. DOI: 10.1038/s41598-025-04971-9

7. "RECAP: Deterministic Regex + Context-Aware LLMs for Multilingual PII Detection." NeurIPS 2025. neurips.cc/virtual/2025/122402

8. "Continual Pre-Training is (not) What You Need in Domain Adaptation." ICLR 2025. openreview.net/pdf?id=rpi9ARgvXc

9. "MEL: Legal Spanish language model." ArXiv, Gennaio 2025. arxiv.org/html/2501.16011

10. "3CEL: a Corpus of Legal Spanish Contract Clauses." ArXiv, Gennaio 2025. arxiv.org/html/2501.15990

11. "Instruction Finetuning LLaMA-3-8B Model Using LoRA for Financial Named Entity Recognition." ArXiv, Gennaio 2026. arxiv.org/abs/2601.10043

12. Unsloth Documentation. "LoRA Fine-tuning Hyperparameters Guide." unsloth.ai/docs (2025).

13. Gretel.ai. "GLiNER Models for PII Detection." gretel.ai/blog (2025).

14. Microsoft Presidio. "Using GLiNER with Presidio." microsoft.github.io/presidio (2025).

---

**Generato da:** AlexAlves87
**Data:** 31-01-2026
**Revisione:** 1.1 (aggiunta sezione 4: Letture Preliminari Obbligatorie)
**Prossimo passo:** Stabilire baseline (GLiNER + MEL) prima di iniziare il fine-tuning
