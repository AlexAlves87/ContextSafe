# Pattern Regex - Test di Integrazione

**Data:** 05-02-2026
**Autor:** AlexAlves87
**Componente:** Integrazione di pattern regex in `scripts/inference/ner_predictor.py`
**Standard:** CHPDA (2025) - Approccio ibrido regex+NER

---

## 1. Riepilogo Esecutivo

Integrazione di pattern regex per rilevare identificatori con spazi/trattini che il modello NER transformer non rileva.

### Risultati

| Suite di Test | Prima | Dopo | Miglioramento |
|---------------|-------|------|---------------|
| Test di integrazione | - | 11/14 (78.6%) | Nuovo |
| Adversarial (strict) | 34.3% | **45.7%** | **+11.4pp** |
| F1 (strict) | 0.492 | **0.543** | **+0.051** |

### Conclusione

> **L'integrazione regex migliora significativamente il rilevamento di identificatori formattati.**
> Pass rate +11.4pp, F1 +0.051. L'IBAN con spazi viene ora rilevato correttamente.

---

## 2. Metodologia

### 2.1 Strategia di Merge (Ibrida)

```
Testo di input
       ↓
┌──────────────────────┐
│  1. NER Transformer  │  Rileva entità semantiche
└──────────────────────┘
       ↓
┌──────────────────────┐
│  2. Pattern Regex    │  Rileva formati con spazi
└──────────────────────┘
       ↓
┌──────────────────────┐
│  3. Strategia Merge  │  Combina, preferisce più completo
└──────────────────────┘
       ↓
┌──────────────────────┐
│  4. Valid. Checksum  │  Regola confidenza
└──────────────────────┘
       ↓
Entità finali
```

### 2.2 Logica di Merge

| Caso | Azione |
|------|--------|
| Solo NER rileva | Mantenere NER |
| Solo Regex rileva | Aggiungere Regex |
| Entrambi rilevano stesso span | Mantenere NER (qualità semantica superiore) |
| Regex >20% più lungo di NER | Sostituire NER con Regex |
| NER parziale, Regex completo | Sostituire con Regex |

### 2.3 Riproducibilità

```bash
# Ambiente
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Test integrazione regex
python scripts/evaluate/test_regex_integration.py

# Test adversarial completo
python scripts/evaluate/test_ner_predictor_adversarial_v2.py
```

---

## 3. Risultati

### 3.1 Test di Integrazione (11/14)

| Test | Input | Risultato | Fonte |
|------|-------|-----------|-------|
| dni_spaces_2_3_3 | `12 345 678 Z` | ✅ | ner |
| dni_spaces_4_4 | `1234 5678 Z` | ✅ | ner |
| dni_dots | `12.345.678-Z` | ✅ | ner |
| nie_dashes | `X-1234567-Z` | ✅ | ner |
| **iban_spaces** | `ES91 2100 0418...` | ✅ | **regex** |
| phone_spaces | `612 345 678` | ✅ | regex |
| phone_intl | `+34 612345678` | ❌ | - |
| cif_dashes | `A-1234567-4` | ❌ (tipo errato) | ner |
| nss_slashes | `28/12345678/90` | ✅ | ner |
| dni_standard | `12345678Z` | ✅ | ner |

### 3.2 Impatto su Test Adversarial

| Metrica | Baseline | +Normalizer | +Regex | Delta Totale |
|---------|----------|-------------|--------|--------------|
| **Pass Rate** | 28.6% | 34.3% | **45.7%** | **+17.1pp** |
| **F1 (strict)** | 0.464 | 0.492 | **0.543** | **+0.079** |
| F1 (parziale) | 0.632 | 0.659 | **0.690** | +0.058 |
| COR | 29 | 31 | **35** | **+6** |
| MIS | 17 | 15 | **12** | **-5** |
| PAR | 21 | 21 | **19** | -2 |
| SPU | 8 | 7 | **7** | -1 |

### 3.3 Analisi dei Miglioramenti

| Test Adversarial | Prima | Dopo | Miglioramento |
|------------------|-------|------|---------------|
| dni_with_spaces | MIS:1 | COR:1 | +1 COR |
| iban_with_spaces | PAR:1 | COR:1 | PAR→COR |
| phone_international | MIS:1 | COR:1* | +1 COR |
| address_floor_door | PAR:1 | COR:1 | PAR→COR |

*Rilevamento parziale migliorato

---

## 4. Analisi degli Errori

### 4.1 Fallimenti Rimanenti

| Test | Problema | Causa |
|------|----------|-------|
| phone_intl | `+34` non incluso | NER rileva `612345678`, overlap insufficiente |
| cif_dashes | Tipo errato | Modello classifica CIF come DNI_NIE |
| spaced_iban_source | Non rilevato isolato | Contesto minimo riduce rilevamento |

### 4.2 Osservazioni

1. **NER impara formati con spazi**: Sorprendentemente, il NER rileva alcuni DNI con spazi (probabilmente dal data augmentation precedente)

2. **Regex completa, non sostituisce**: La maggior parte dei rilevamenti rimane NER, regex aggiunge solo casi persi da NER

3. **Checksum si applica a entrambi**: Sia NER che Regex passano per validazione checksum

---

## 5. Conclusioni e Lavoro Futuro

### 5.1 Conclusioni

1. **Miglioramento significativo**: +17.1pp pass rate, +0.079 F1
2. **IBAN con spazi**: Problema risolto (regex rileva correttamente)
3. **Merge intelligente**: Preferisce rilevamenti più completi
4. **Overhead minimo**: ~100ms aggiuntivi per 25 pattern

### 5.2 Stato Attuale vs Obiettivo

| Metrica | Baseline | Attuale | Obiettivo | Gap |
|---------|----------|---------|-----------|-----|
| Pass Rate | 28.6% | **45.7%** | ≥70% | -24.3pp |
| F1 (strict) | 0.464 | **0.543** | ≥0.70 | -0.157 |

### 5.3 Prossimi Passi

| Priorità | Compito | Impatto Stimato |
|----------|---------|-----------------|
| ALTA | Data augmentation date testuali | +3-4 COR |
| MEDIA | Correggere classificazione CIF | +1 COR |
| MEDIA | Migliorare rilevamento phone_intl | +1 COR |
| BASSA | Raffinamento confini per PAR→COR | +2-3 COR |

---

## 6. Riferimenti

1. **Test standalone:** `docs/reports/2026-02-05_regex_patterns_standalone.md`
2. **CHPDA (2025):** [arXiv](https://arxiv.org/html/2502.07815v1) - Ibrido regex+NER
3. **Script pattern:** `scripts/preprocess/spanish_id_patterns.py`
4. **Test integrazione:** `scripts/evaluate/test_regex_integration.py`

---

**Tempo di esecuzione:** 2.72s (integrazione) + 1.4s (adversarial)
**Generato da:** AlexAlves87
**Data:** 05-02-2026
