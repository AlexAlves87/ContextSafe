# Valutazione di Impatto: Text Normalizer

**Data:** 04-02-2026
**Autor:** AlexAlves87
**Componente:** `TextNormalizer` (Normalizzazione Unicode/OCR)
**Standard:** SemEval 2013 Task 9 (modalità strict)

---

## 1. Riepilogo Esecutivo

Valutazione dell'impatto dell'integrazione del `TextNormalizer` nel pipeline NER per migliorare la robustezza contro caratteri Unicode e artefatti OCR.

### Risultati

| Metrica | Baseline | +Normalizer | Delta | Variazione |
|---------|----------|-------------|-------|------------|
| **Pass Rate (strict)** | 28.6% | **34.3%** | **+5.7pp** | +20% relativo |
| **F1 (strict)** | 0.464 | **0.492** | **+0.028** | +6% relativo |
| F1 (parziale) | 0.632 | 0.659 | +0.027 | +4.3% relativo |
| COR | 29 | 31 | +2 | Più rilevamenti esatti |
| MIS | 17 | 15 | -2 | Meno entità perse |
| SPU | 8 | 7 | -1 | Meno falsi positivi |

### Conclusione

> **Il TextNormalizer migliora significativamente la robustezza del modello NER.**
> Pass rate +5.7pp, F1 +0.028. Due test di evasione Unicode ora passano.

---

## 2. Metodologia

### 2.1 Disegno Sperimentale

| Aspetto | Specifica |
|---------|-----------|
| Variabile Indipendente | TextNormalizer (ON/OFF) |
| Variabile Dipendente | Metriche SemEval 2013 |
| Modello | legal_ner_v2 (RoBERTalex) |
| Dataset | 35 test adversarial |
| Standard | SemEval 2013 Task 9 (strict) |

### 2.2 Componente Valutato

**File:** `scripts/inference/ner_predictor.py` → funzione `normalize_text_for_ner()`

**Operazioni Applicate:**
1. Rimozione caratteri zero-width (U+200B-U+200F, U+2060-U+206F, U+FEFF)
2. Normalizzazione NFKC (fullwidth → ASCII)
3. Mappatura omoglifi (Cirillico → Latino)
4. Normalizzazione spazi (NBSP → spazio, collasso multipli)
5. Rimozione trattini morbidi

### 2.3 Riproducibilità

```bash
# Ambiente
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Esecuzione
python scripts/evaluate/test_ner_predictor_adversarial_v2.py

# Output: docs/reports/YYYY-MM-DD_adversarial_v2_academic_rN.md
```

---

## 3. Risultati

### 3.1 Confronto Dettagliato per Metrica SemEval

| Metrica | Baseline | +Normalizer | Delta |
|---------|----------|-------------|-------|
| COR (Corretto) | 29 | 31 | **+2** |
| INC (Incorretto) | 0 | 0 | 0 |
| PAR (Parziale) | 21 | 21 | 0 |
| MIS (Perso) | 17 | 15 | **-2** |
| SPU (Spurio) | 8 | 7 | **-1** |
| POS (Possibile) | 67 | 67 | 0 |
| ACT (Attuale) | 58 | 59 | +1 |

### 3.2 Test Migliorati

| Test | Baseline | +Normalizer | Miglioramento |
|------|----------|-------------|---------------|
| `cyrillic_o` | ❌ COR:1 PAR:1 | ✅ COR:2 | **Mappatura omoglifi funziona** |
| `zero_width_space` | ❌ COR:2 SPU:1 | ✅ COR:2 SPU:0 | **Rimozione zero-width funziona** |
| `fullwidth_numbers` | ❌ MIS:2 | ❌ COR:1 MIS:1 | Miglioramento parziale (+1 COR) |

### 3.3 Test Senza Cambiamenti Significativi

| Test | Stato | Ragione |
|------|-------|---------|
| `ocr_extra_spaces` | ❌ MIS:2 | Richiede normalizzazione spazi dentro entità |
| `ocr_zero_o_confusion` | ❌ MIS:1 | Richiede correzione contestuale OCR O↔0 |
| `dni_with_spaces` | ❌ MIS:1 | Spazi interni in DNI non collassati |

### 3.4 Risultati per Categoria

| Categoria | Baseline Strict | +Normalizer Strict | Delta |
|-----------|-----------------|--------------------|-------|
| adversarial | 75% | 75% | 0 |
| edge_case | 22% | 22% | 0 |
| ocr_corruption | 40% | 40% | 0 |
| real_world | 10% | 10% | 0 |
| **unicode_evasion** | 0% | **67%** | **+67pp** |

**Scoperta Chiave:** L'impatto si concentra su `unicode_evasion` (+67pp), che era l'obiettivo principale.

---

## 4. Analisi degli Errori

### 4.1 Test `fullwidth_numbers` (Miglioramento Parziale)

**Input:** `"DNI １２３４５６７８Z de María."`

**Atteso:**
- `"１２３４５６７８Z"` → DNI_NIE
- `"María"` → PERSON

**Rilevato (con normalizer):**
- `"12345678Z"` → DNI_NIE ✅ (match normalizzato)
- `"María"` → MIS ❌

**Analisi:** Il DNI viene rilevato correttamente dopo NFKC. Il nome "María" viene perso perché il modello non lo rileva (problema del modello, non del normalizer).

### 4.2 Test che Continuano a Fallire

| Test | Problema | Soluzione Richiesta |
|------|----------|---------------------|
| `dni_with_spaces` | "12 345 678 Z" non riconosciuto | Regex per DNI con spazi |
| `date_roman_numerals` | Date con numeri romani | Data augmentation |
| `ocr_zero_o_confusion` | IBAN con O/0 misti | Post-correzione OCR |

---

## 5. Conclusioni e Lavoro Futuro

### 5.1 Conclusioni

1. **TextNormalizer raggiunge il suo obiettivo** per evasione Unicode:
   - `cyrillic_o`: ❌ → ✅
   - `zero_width_space`: ❌ → ✅
   - Categoria `unicode_evasion`: 0% → 67%

2. **Impatto globale moderato ma positivo:**
   - F1 strict: +0.028 (+6%)
   - Pass rate: +5.7pp (+20% relativo)

3. **Non risolve problemi OCR** (previsto):
   - `ocr_extra_spaces`, `ocr_zero_o_confusion` richiedono tecniche aggiuntive

### 5.2 Lavoro Futuro

| Priorità | Miglioramento | Impatto Stimato |
|----------|---------------|-----------------|
| ALTA | Regex per DNI/IBAN con spazi | +2-3 COR |
| ALTA | Validazione checksum (ridurre SPU) | -2-3 SPU |
| MEDIA | Data augmentation per date testuali | +3-4 COR |
| BASSA | Post-correzione OCR (O↔0) | +1-2 COR |

### 5.3 Obiettivo Aggiornato

| Metrica | Prima | Ora | Obiettivo Livello 4 | Gap |
|---------|-------|-----|---------------------|-----|
| F1 (strict) | 0.464 | **0.492** | ≥0.70 | -0.208 |
| Pass rate | 28.6% | **34.3%** | ≥70% | -35.7pp |

---

## 6. Riferimenti

1. **Ricerca base:** `docs/reports/2026-01-27_investigacion_text_normalization.md`
2. **Componente standalone:** `scripts/preprocess/text_normalizer.py`
3. **Integrazione produzione:** `src/contextsafe/infrastructure/nlp/text_normalizer.py`
4. **Forme di Normalizzazione Unicode UAX #15:** https://unicode.org/reports/tr15/

---

**Tempo di valutazione:** 1.3s
**Generato da:** AlexAlves87
**Data:** 04-02-2026
