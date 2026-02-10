# Baseline Accademico: Valutazione con Standard SemEval 2013

**Data:** 03-02-2026
**Autor:** AlexAlves87
**Modello:** legal_ner_v2 (RoBERTalex fine-tuned)
**Standard:** SemEval 2013 Task 9

---

## 1. Riepilogo Esecutivo

Questa valutazione stabilisce il **baseline reale** del modello utilizzando standard accademici (modalità strict SemEval 2013), sostituendo i risultati precedenti che utilizzavano il matching lenient.

### Confronto v1 vs v2

| Metrica | v1 (lenient) | v2 (strict) | Differenza |
|---------|--------------|-------------|------------|
| **Pass Rate** | 54.3% | **28.6%** | **-25.7pp** |
| **F1-Score** | 0.784 | **0.464** | **-0.320** |
| F1 (parziale) | - | 0.632 | - |

### Conclusione Principale

> **I risultati precedenti (F1=0.784, 54.3%) erano GONFIATI.**
> Il baseline reale con standard accademici è **F1=0.464, 28.6% pass rate**.

---

## 2. Metodologia

### 2.1 Disegno Sperimentale

| Aspetto | Specifica |
|---------|-----------|
| Modello valutato | `legal_ner_v2` (RoBERTalex fine-tuned) |
| Framework | PyTorch 2.0+, Transformers |
| Hardware | CUDA (GPU) |
| Standard di valutazione | SemEval 2013 Task 9 |
| Modalità principale | Strict (confine + tipo esatti) |

### 2.2 Dataset di Valutazione

| Categoria | Test | Scopo |
|-----------|------|-------|
| edge_case | 9 | Condizioni limite (nomi lunghi, formati varianti) |
| adversarial | 8 | Casi progettati per confondere (negazioni, esempi) |
| ocr_corruption | 5 | Simulazione di errori OCR |
| unicode_evasion | 3 | Tentativi di evasione con caratteri Unicode |
| real_world | 10 | Estratti di documenti legali reali |
| **Totale** | **35** | - |

### 2.3 Metriche Utilizzate

Secondo SemEval 2013 Task 9:

| Metrica | Definizione |
|---------|-------------|
| COR | Corretto: confine E tipo esatti |
| INC | Incorretto: confine esatto, tipo incorretto |
| PAR | Parziale: confine sovrapposto, qualsiasi tipo |
| MIS | Mancante: entità gold non rilevata (FN) |
| SPU | Spurio: rilevamento senza corrispondenza gold (FP) |

**Formule:**
- Precisione (strict) = COR / (COR + INC + PAR + SPU)
- Richiamo (strict) = COR / (COR + INC + PAR + MIS)
- F1 (strict) = 2 × P × R / (P + R)

### 2.4 Riproducibilità

```bash
# Ambiente
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Dipendenze
pip install nervaluate  # Opzionale, metriche implementate manualmente

# Esecuzione
python scripts/evaluate/test_ner_predictor_adversarial_v2.py

# Output
# - Console: Risultati per test con COR/INC/PAR/MIS/SPU
# - Report: docs/reports/YYYY-MM-DD_adversarial_v2_academic_rN.md
```

### 2.5 Differenza con Valutazione v1

| Aspetto | v1 (lenient) | v2 (strict) |
|---------|--------------|-------------|
| Matching | Contenimento + 80% sovrapposizione caratteri | Confine esatto normalizzato |
| Tipo | Richiesto | Richiesto |
| Metriche | TP/FP/FN | COR/INC/PAR/MIS/SPU |
| Standard | Personalizzato | SemEval 2013 Task 9 |

---

## 3. Risultati

### 3.1 Conteggi SemEval 2013

| Metrica | Valore | Descrizione |
|---------|--------|-------------|
| **COR** | 29 | Corretti (confine + tipo esatti) |
| **INC** | 0 | Confine corretto, tipo incorretto |
| **PAR** | 21 | Corrispondenza parziale (solo sovrapposizione) |
| **MIS** | 17 | Persi (FN) |
| **SPU** | 8 | Spuri (FP) |
| **POS** | 67 | Totale gold (COR+INC+PAR+MIS) |
| **ACT** | 58 | Totale sistema (COR+INC+PAR+SPU) |

### 3.2 Interpretazione

```
                    ┌─────────────────────────────────┐
                    │     GOLD: 67 entità             │
                    │                                 │
  ┌─────────────────┼─────────────────┐               │
  │                 │    COR: 29      │               │
  │   SISTEMA: 58   │  (43% di gold)  │   MIS: 17     │
  │                 │                 │   (25%)       │
  │    SPU: 8       │    PAR: 21      │               │
  │    (14%)        │   (31% overlap) │               │
  └─────────────────┴─────────────────┴───────────────┘
```

**Analisi:**
- Solo **43%** delle entità gold vengono rilevate con confine esatto
- **31%** vengono rilevate con sovrapposizione parziale (v1 le contava come corrette)
- **25%** vengono perse completamente
- **14%** dei rilevamenti sono falsi positivi

### 3.3 Formule Applicate

**Modalità Strict:**
```
Precisione = COR / ACT = 29 / 58 = 0.500
Richiamo = COR / POS = 29 / 67 = 0.433
F1 = 2 * P * R / (P + R) = 0.464
```

**Modalità Parziale:**
```
Precisione = (COR + 0.5*PAR) / ACT = (29 + 10.5) / 58 = 0.681
Richiamo = (COR + 0.5*PAR) / POS = (29 + 10.5) / 67 = 0.590
F1 = 2 * P * R / (P + R) = 0.632
```

---

### 3.4 Risultati per Categoria

| Categoria | Strict | Lenient | COR | PAR | MIS | SPU |
|-----------|--------|---------|-----|-----|-----|-----|
| adversarial | 75% | 75% | 5 | 1 | 0 | 3 |
| edge_case | 22% | 67% | 6 | 3 | 3 | 1 |
| ocr_corruption | 40% | 40% | 4 | 1 | 4 | 0 |
| real_world | 10% | 50% | 12 | 14 | 8 | 4 |
| unicode_evasion | 0% | 33% | 3 | 1 | 2 | 1 |

**Osservazioni:**
- **real_world**: Maggiore discrepanza strict vs lenient (10% vs 50%) - molti PAR
- **unicode_evasion**: 0% strict - tutti i rilevamenti sono parziali o incorretti
- **adversarial**: Uguale in entrambe le modalità - test di non-rilevamento

---

### 3.5 Risultati per Difficoltà

| Difficoltà | Strict | Lenient |
|------------|--------|---------|
| facile | 50% | 75% |
| medio | 42% | 75% |
| difficile | 16% | 42% |

**Osservazione:** La differenza strict vs lenient aumenta con la difficoltà.

---

## 4. Analisi degli Errori

### 4.1 Corrispondenze Parziali (PAR)

Le 21 corrispondenze parziali rappresentano rilevamenti dove il confine non è esatto:

| Tipo di PAR | Esempi | Causa |
|-------------|--------|-------|
| Nome incompleto | "José María" vs "José María de la Santísima..." | RoBERTa tronca nomi lunghi |
| IBAN con spazi | "ES91 2100..." vs "ES912100..." | Normalizzazione spazi |
| Indirizzo parziale | "Calle Mayor 15" vs "Calle Mayor 15, 3º B" | Confine esclude piano/porta |
| Persona nel contesto | "John Smith" vs "Mr. John Smith" | Prefissi non inclusi |

**Implicazione:** Il modello rileva l'entità ma con confini imprecisi.

---

### 4.2 Test Falliti (Strict)

#### 4.2.1 Per SPU (Falsi Positivi)

| Test | SPU | Entità Spurie |
|------|-----|---------------|
| example_dni | 1 | "12345678X" (contesto esempio) |
| fictional_person | 1 | "Don Quijote de la Mancha" |
| date_ordinal | 1 | "El" |
| zero_width_space | 1 | "de" |
| judicial_sentence_header | 2 | Riferimenti legali |
| professional_ids | 1 | Albo professionale |
| ecli_citation | 1 | Tribunale |

#### 4.2.2 Per MIS (Entità Perse)

| Test | MIS | Entità Perse |
|------|-----|--------------|
| dni_with_spaces | 1 | "12 345 678 Z" |
| phone_international | 1 | "0034612345678" |
| date_roman_numerals | 1 | "XV de marzo del año MMXXIV" |
| ocr_zero_o_confusion | 1 | IBAN con O/0 |
| ocr_extra_spaces | 2 | DNI e nome con spazi |
| fullwidth_numbers | 2 | DNI fullwidth, nome |
| notarial_header | 1 | Data testuale |

---

## 5. Conclusioni e Lavoro Futuro

### 5.1 Priorità di Miglioramento

| Miglioramento | Impatto su COR | Impatto su PAR→COR |
|---------------|----------------|-------------------|
| Normalizzazione testo (Unicode) | +2-4 COR | +2-3 PAR→COR |
| Validazione checksum | Riduce SPU | - |
| Raffinamento confini | - | +10-15 PAR→COR |
| Data augmentation | +3-5 COR | - |

### 5.2 Obiettivo Rivisto

| Metrica | Attuale | Obiettivo Livello 4 |
|---------|---------|---------------------|
| F1 (strict) | 0.464 | **≥ 0.70** |
| Pass rate (strict) | 28.6% | **≥ 70%** |

**Gap da chiudere:** +0.236 F1, +41.4pp pass rate

---

### 5.3 Prossimi Passi

1. **Rivalutare** con TextNormalizer integrato (già preparato)
2. **Implementare** raffinamento confini per ridurre PAR
3. **Aggiungere** validazione checksum per ridurre SPU
4. **Aumentare** dati per date testuali per ridurre MIS

---

### 5.4 Lezioni Apprese

1. **Il matching lenient gonfia significativamente i risultati** (F1 0.784 → 0.464)
2. **PAR è un problema maggiore di MIS** (21 vs 17) - confini imprecisi
3. **I test reali (real_world) hanno più PAR** - documenti complessi
4. **L'evasione Unicode non passa alcun test strict** - area critica

### 5.5 Valore dello Standard Accademico

La valutazione con SemEval 2013 permette:
- Confronto con la letteratura accademica
- Diagnosi granulare (COR/INC/PAR/MIS/SPU)
- Identificazione precisa delle aree di miglioramento
- Misurazione onesta del progresso

---

## 6. Riferimenti

1. **SemEval 2013 Task 9**: Segura-Bedmar et al. "Extraction of Drug-Drug Interactions from Biomedical Texts"
2. **nervaluate**: https://github.com/MantisAI/nervaluate
3. **David Batista Blog**: https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/

---

**Tempo di valutazione:** 1.3s
**Generato da:** AlexAlves87
**Data:** 03-02-2026
