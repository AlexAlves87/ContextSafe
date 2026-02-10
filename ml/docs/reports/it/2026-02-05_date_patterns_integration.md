# Date Patterns - Test di Integrazione

**Data:** 05-02-2026
**Autor:** AlexAlves87
**Componente:** `scripts/preprocess/spanish_date_patterns.py` integrato nel pipeline
**Standard:** TIMEX3 per espressioni temporali

---

## 1. Riepilogo Esecutivo

Integrazione di pattern regex per date testuali spagnole che completano il rilevamento NER.

### Risultati

| Suite di Test | Risultato |
|---------------|-----------|
| Test standalone | 14/14 (100%) |
| Test di integrazione | 9/9 (100%) |
| Adversarial (miglioramento) | +2.9pp pass rate |

### Conclusione

> **I pattern di data aggiungono valore principalmente per i numeri romani.**
> Il modello NER rileva già la maggior parte delle date testuali.
> Miglioramento totale accumulato: Pass rate +20pp, F1 +0.081 dal baseline.

---

## 2. Metodologia

### 2.1 Pattern Implementati (10 totale)

| Pattern | Esempio | Confidenza |
|---------|---------|------------|
| `date_roman_full` | XV de marzo del año MMXXIV | 0.95 |
| `date_roman_day_written_year` | XV de marzo de dos mil... | 0.90 |
| `date_written_full` | quince de marzo de dos mil... | 0.95 |
| `date_ordinal_full` | primero de enero de dos mil... | 0.95 |
| `date_written_day_numeric_year` | quince de marzo de 2024 | 0.90 |
| `date_ordinal_numeric_year` | primero de enero de 2024 | 0.90 |
| `date_a_written` | a veinte de abril de dos mil... | 0.90 |
| `date_el_dia_written` | el día quince de marzo de... | 0.90 |
| `date_numeric_standard` | 15 de marzo de 2024 | 0.85 |
| `date_formal_legal` | día 15 del mes de marzo del año 2024 | 0.90 |

### 2.2 Integrazione

I pattern di data sono stati integrati in `spanish_id_patterns.py`:

```python
# In find_matches():
if DATE_PATTERNS_AVAILABLE and (entity_types is None or "DATE" in entity_types):
    date_matches = find_date_matches(text)
    for dm in date_matches:
        matches.append(RegexMatch(
            text=dm.text,
            entity_type="DATE",
            ...
        ))
```

### 2.3 Riproducibilità

```bash
# Ambiente
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Test standalone
python scripts/preprocess/spanish_date_patterns.py

# Test integrazione
python scripts/evaluate/test_date_integration.py

# Test adversarial completo
python scripts/evaluate/test_ner_predictor_adversarial_v2.py
```

---

## 3. Risultati

### 3.1 Test di Integrazione (9/9)

| Test | Testo | Fonte | Risultato |
|------|-------|-------|-----------|
| roman_full | XV de marzo del año MMXXIV | **regex** | ✅ |
| ordinal_full | primero de enero de dos mil... | ner | ✅ |
| notarial_date | quince de marzo de dos mil... | ner | ✅ |
| testament_date | diez de enero de dos mil... | ner | ✅ |
| written_full | veintiocho de febrero de... | ner | ✅ |
| numeric_standard | 15 de marzo de 2024 | ner | ✅ |
| multiple_dates | uno de enero...diciembre... | ner | ✅ |
| date_roman_numerals | XV de marzo del año MMXXIV | **regex** | ✅ |
| date_ordinal | primero de enero de... | ner | ✅ |

### 3.2 Osservazione Chiave

**Il modello NER rileva già la maggior parte delle date testuali.** Il regex aggiunge valore solo per:
- **Numeri romani** (XV, MMXXIV) - non nel vocabolario del modello

### 3.3 Impatto su Test Adversarial

| Metrica | Prima | Dopo | Delta |
|---------|-------|------|-------|
| Pass Rate | 45.7% | **48.6%** | **+2.9pp** |
| F1 (strict) | 0.543 | **0.545** | +0.002 |
| F1 (partial) | 0.690 | **0.705** | +0.015 |
| COR | 35 | **36** | **+1** |
| MIS | 12 | **9** | **-3** |
| PAR | 19 | 21 | +2 |

---

## 4. Progresso Totale Accumulato

### 4.1 Elementi Integrati

| Elemento | Standalone | Integrazione | Impatto Principale |
|----------|------------|--------------|--------------------|
| 1. TextNormalizer | 15/15 | ✅ | Evasione Unicode |
| 2. Checksum | 23/24 | ✅ | Regolazione confidenza |
| 3. Regex IDs | 22/22 | ✅ | Identificatori spaziati |
| 4. Pattern Data | 14/14 | ✅ | Numeri romani |

### 4.2 Metriche Totali

| Metrica | Baseline | Attuale | Miglioramento | Obiettivo | Gap |
|---------|----------|---------|---------------|-----------|-----|
| **Pass Rate** | 28.6% | **48.6%** | **+20pp** | ≥70% | -21.4pp |
| **F1 (strict)** | 0.464 | **0.545** | **+0.081** | ≥0.70 | -0.155 |
| COR | 29 | 36 | +7 | - | - |
| MIS | 17 | 9 | -8 | - | - |
| SPU | 8 | 7 | -1 | - | - |
| PAR | 21 | 21 | 0 | - | - |

### 4.3 Progresso Visivo

```
Pass Rate:
Baseline   [████████░░░░░░░░░░░░░░░░░░░░░░░░░░░] 28.6%
Attuale    [█████████████████░░░░░░░░░░░░░░░░░░] 48.6%
Obiettivo  [████████████████████████████░░░░░░░] 70.0%

F1 (strict):
Baseline   [████████████████░░░░░░░░░░░░░░░░░░░] 0.464
Attuale    [███████████████████░░░░░░░░░░░░░░░░] 0.545
Obiettivo  [████████████████████████████░░░░░░░] 0.700
```

---

## 5. Conclusioni e Lavoro Futuro

### 5.1 Conclusioni

1. **Progresso significativo**: +20pp pass rate, +0.081 F1 dal baseline
2. **MIS ridotto drasticamente**: 17 → 9 (-8 entità perse)
3. **Pipeline ibrido funziona**: NER + Regex + Checksum si completano a vicenda
4. **Modello NER è robusto per date**: Necessita regex solo per romani

### 5.2 Gap Rimanente

| Per raggiungere obiettivo | Necessario |
|---------------------------|------------|
| Pass rate 70% | +21.4pp in più |
| F1 0.70 | +0.155 in più |
| Equivalente a | ~8-10 COR addizionali |

### 5.3 Prossimi Passi Potenziali

| Priorità | Miglioramento | Impatto Stimato |
|----------|---------------|-----------------|
| ALTA | Raffinamento confini (PAR→COR) | +5-6 COR |
| MEDIA | Data augmentation modello | +3-4 COR |
| MEDIA | Correggere classificazione CIF | +1 COR |
| BASSA | Migliorare rilevamento phone_intl | +1 COR |

---

## 6. Riferimenti

1. **Test standalone:** `scripts/preprocess/spanish_date_patterns.py`
2. **Test integrazione:** `scripts/evaluate/test_date_integration.py`
3. **TIMEX3:** Standard annotazione ISO-TimeML
4. **HeidelTime/SUTime:** Tagger temporali di riferimento

---

**Tempo di esecuzione:** 2.51s (integrazione) + 1.4s (adversarial)
**Generato da:** AlexAlves87
**Data:** 05-02-2026
