# Confronto: Modello v1 vs v2 (Addestramento con Rumore)

**Data:** 2026-01-22
**Autor:** AlexAlves87
**Tipo:** Analisi Comparativa
**Stato:** Completato

---

## Riepilogo Esecutivo

| Metrica | v1 | v2 | Variazione |
|---------|-----|-----|--------|
| Tasso di Successo Adversarial | 45.7% (16/35) | 54.3% (19/35) | **+8.6 pp** |
| F1 Test Sintetico | 99.87% | 100% | +0.13 pp |
| Dataset | v2 (pulito) | v3 (30% rumore) | - |

**Conclusione:** L'iniezione di rumore OCR durante l'addestramento ha migliorato la robustezza del modello di +8.6 punti percentuali nei test avversari.

---

## Metodologia

### Differenze di Addestramento

| Aspetto | v1 | v2 |
|---------|-----|-----|
| Dataset | `ner_dataset_v2` | `ner_dataset_v3` |
| Iniezione rumore | 0% | 30% |
| Tipi di rumore | - | l↔I, 0↔O, accenti, spazi |
| Iperparametri | Identici | Identici |
| Modello base | roberta-bne-capitel-ner | roberta-bne-capitel-ner |

### Test Avversari (35 casi)

| Categoria | Test |
|-----------|-------|
| edge_case | 9 |
| adversarial | 8 |
| ocr_corruption | 5 |
| unicode_evasion | 3 |
| real_world | 10 |

---

## Risultati per Categoria

### Confronto Tasso di Successo

| Categoria | v1 | v2 | Miglioramento |
|-----------|-----|-----|--------|
| edge_case | 55.6% (5/9) | 66.7% (6/9) | +11.1 pp |
| adversarial | 37.5% (3/8) | 62.5% (5/8) | **+25.0 pp** |
| ocr_corruption | 20.0% (1/5) | 40.0% (2/5) | **+20.0 pp** |
| unicode_evasion | 33.3% (1/3) | 33.3% (1/3) | 0 pp |
| real_world | 60.0% (6/10) | 50.0% (5/10) | -10.0 pp |

### Analisi per Categoria

**Miglioramenti Significativi (+20 pp o più):**
- **adversarial**: +25 pp - Migliore discriminazione del contesto (negazione, esempi)
- **ocr_corruption**: +20 pp - Il rumore nell'addestramento ha aiutato direttamente

**Nessun Cambiamento:**
- **unicode_evasion**: 33.3% - Richiede normalizzazione del testo, non solo addestramento

**Regressione:**
- **real_world**: -10 pp - Possibile overfitting al rumore, meno robustezza a pattern complessi

---

## Dettaglio dei Test Cambiati

### Test SUPERATI in v2 (precedentemente FALLITI)

| Test | Categoria | Nota |
|------|-----------|------|
| `ocr_letter_substitution` | ocr_corruption | DNl → DNI (l vs I) |
| `ocr_accent_loss` | ocr_corruption | José → Jose |
| `negation_dni` | adversarial | "NO tener DNI" - non rileva più PII |
| `organization_as_person` | adversarial | García y Asociados → ORG |
| `location_as_person` | adversarial | San Fernando → LOCATION |

### Test FALLITI in v2 (precedentemente SUPERATI)

| Test | Categoria | Nota |
|------|-----------|------|
| `notarial_header` | real_world | Possibile regressione nelle date scritte |
| `judicial_sentence_header` | real_world | Possibile regressione nei nomi maiuscoli |

---

## Conclusioni

### Scoperte Principali

1. **L'addestramento con rumore funziona**: +8.6 pp miglioramento globale, specialmente in OCR e avversario
2. **Il rumore specifico conta**: l↔I, accenti migliorati, ma 0↔O e spazi falliscono ancora
3. **Compromesso osservato**: Guadagnata robustezza al rumore ma persa un po' di precisione in pattern complessi

### Limitazioni dell'Approccio

1. **Rumore insufficiente per 0↔O**: IBAN con O invece di 0 fallisce ancora
2. **Normalizzazione necessaria**: L'evasione Unicode richiede pre-elaborazione, non solo addestramento
3. **Complessità del mondo reale**: I documenti complessi richiedono più dati di addestramento

### Raccomandazioni

| Priorità | Azione | Impatto Previsto |
|-----------|--------|------------------|
| ALTA | Aggiungere normalizzazione Unicode nella pre-elaborazione | +10% unicode_evasion |
| ALTA | Più varietà di rumore 0↔O nell'addestramento | +5-10% ocr_corruption |
| MEDIA | Più esempi real_world nel dataset | Recuperare -10% real_world |
| MEDIA | Pipeline ibrida (Regex → NER → Validazione) | +15-20% secondo letteratura |

---

## Prossimi Passi

1. **Implementare pipeline ibrida** secondo ricerca PMC12214779
2. **Aggiungere text_normalizer.py** come pre-elaborazione prima dell'inferenza
3. **Espandere dataset** con più esempi di documenti reali
4. **Valutare layer CRF** per migliorare la coerenza delle sequenze

---

## File Correlati

- `docs/reports/2026-01-20_adversarial_evaluation.md` - Valutazione v1
- `docs/reports/2026-01-21_adversarial_evaluation_v2.md` - Valutazione v2
- `docs/reports/2026-01-16_investigacion_pipeline_pii.md` - Best practices
- `scripts/preprocess/inject_ocr_noise.py` - Script iniezione rumore

---

**Data:** 2026-01-22
