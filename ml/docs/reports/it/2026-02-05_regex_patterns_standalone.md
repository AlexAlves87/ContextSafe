# Pattern Regex per Identificatori Spagnoli - Test Standalone

**Data:** 05-02-2026
**Autor:** AlexAlves87
**Componente:** `scripts/preprocess/spanish_id_patterns.py`
**Standard:** CHPDA (2025) - Approccio ibrido regex+NER

---

## 1. Riepilogo Esecutivo

Implementazione di pattern regex per rilevare identificatori spagnoli con formati varianti (spazi, trattini, punti) che i modelli NER transformer tipicamente non rilevano.

### Risultati

| Metrica | Valore |
|---------|--------|
| **Test Superati** | 22/22 (100%) |
| **Tipi di Entità** | 5 (DNI_NIE, IBAN, NSS, CIF, PHONE) |
| **Pattern Totali** | 25 |
| **Tempo Esecuzione** | 0.003s |

### Conclusione

> **Tutti i pattern funzionano correttamente per formati con spazi e separatori.**
> Questo completa il NER transformer che fallisce in casi come "12 345 678 Z" o "ES91 2100 0418...".

---

## 2. Metodologia

### 2.1 Ricerca Base

| Paper | Approccio | Applicazione |
|-------|-----------|--------------|
| **CHPDA (arXiv 2025)** | Ibrido Regex + AI NER | Riduce falsi positivi |
| **Hybrid ReGex (JCO 2025)** | Pipeline leggero regex + ML | Estrazione dati medici |
| **Legal NLP Survey (2024)** | NER specializzato legale | Pattern normativi |

### 2.2 Pattern Implementati

| Tipo | Pattern | Esempi |
|------|---------|--------|
| **DNI** | 6 | `12345678Z`, `12 345 678 Z`, `12.345.678-Z` |
| **NIE** | 3 | `X1234567Z`, `X 1234567 Z`, `X-1234567-Z` |
| **IBAN** | 3 | `ES9121...`, `ES91 2100 0418...` |
| **NSS** | 3 | `281234567890`, `28/12345678/90` |
| **CIF** | 3 | `A12345674`, `A-1234567-4` |
| **PHONE** | 7 | `612345678`, `612 345 678`, `+34 612...` |

### 2.3 Riproducibilità

```bash
# Ambiente
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Esecuzione
python scripts/preprocess/spanish_id_patterns.py

# Output atteso: 22/22 passed (100.0%)
```

---

## 3. Risultati

### 3.1 Test per Tipo

| Tipo | Test | Superati | Esempi Chiave |
|------|------|----------|---------------|
| DNI | 6 | 6 | Standard, spazi 2-3-3, punti |
| NIE | 3 | 3 | Standard, spazi, trattini |
| IBAN | 2 | 2 | Standard, spazi gruppi 4 |
| NSS | 2 | 2 | Barre, spazi |
| CIF | 2 | 2 | Standard, trattini |
| PHONE | 4 | 4 | Mobile, fisso, internazionale |
| Negativi | 2 | 2 | Rifiuta formati non validi |
| Multi | 1 | 1 | Entità multiple nel testo |

### 3.2 Demo di Rilevamento

| Input | Rilevamento | Normalizzato |
|-------|-------------|--------------|
| `DNI 12 345 678 Z` | ✅ DNI_NIE | `12345678Z` |
| `IBAN ES91 2100 0418 4502 0005 1332` | ✅ IBAN | `ES9121000418450200051332` |
| `NIE X-1234567-Z` | ✅ DNI_NIE | `X1234567Z` |
| `Tel: 612 345 678` | ✅ PHONE | `612345678` |
| `CIF A-1234567-4` | ✅ CIF | `A12345674` |

### 3.3 Struttura Match

```python
@dataclass
class RegexMatch:
    text: str           # "12 345 678 Z"
    entity_type: str    # "DNI_NIE"
    start: int          # 4
    end: int            # 16
    confidence: float   # 0.90
    pattern_name: str   # "dni_spaced_2_3_3"
```

---

## 4. Analisi dei Pattern

### 4.1 Livelli di Confidenza

| Livello | Confidenza | Criterio |
|---------|------------|----------|
| Alta | 0.95 | Formato standard senza ambiguità |
| Media | 0.90 | Formato con separatori validi |
| Bassa | 0.70-0.85 | Formati che possono essere ambigui |

### 4.2 Pattern DNI con Spazi (Problema Originale)

Il test adversarial `dni_with_spaces` falliva perché il NER non rilevava "12 345 678 Z".

**Soluzione Implementata:**
```python
# Pattern per spazi 2-3-3
r'\b(\d{2})\s+(\d{3})\s+(\d{3})\s*([A-Z])\b'
```

Questo pattern rileva:
- `12 345 678 Z` ✅
- `12 345 678Z` ✅ (senza spazio prima della lettera)

### 4.3 Normalizzazione per Checksum

Funzione `normalize_match()` rimuove separatori per validazione:

```python
"12 345 678 Z" → "12345678Z"
"ES91 2100 0418..." → "ES9121000418..."
"X-1234567-Z" → "X1234567Z"
```

---

## 5. Conclusioni e Lavoro Futuro

### 5.1 Conclusioni

1. **25 pattern coprono formati varianti** di identificatori spagnoli
2. **Normalizzazione permette integrazione** con validatori checksum
3. **Confidenza variabile** distingue formati più/meno affidabili
4. **Rilevamento sovrapposizioni** evita duplicati

### 5.2 Integrazione Pipeline

```
Testo Input
       ↓
┌──────────────────────┐
│  1. TextNormalizer   │  Pulizia Unicode/OCR
└──────────────────────┘
       ↓
┌──────────────────────┐
│  2. NER Transformer  │  Predizioni RoBERTalex
└──────────────────────┘
       ↓
┌──────────────────────┐
│  3. Pattern Regex    │  ← NUOVO: rileva spazi
└──────────────────────┘
       ↓
┌──────────────────────┐
│  4. Merge & Dedup    │  Combina NER + Regex
└──────────────────────┘
       ↓
┌──────────────────────┐
│  5. Valid. Checksum  │  Regola confidenza
└──────────────────────┘
       ↓
Entità Finali
```

### 5.3 Impatto Stimato

| Test Adversarial | Prima | Dopo | Miglioramento |
|------------------|-------|------|---------------|
| `dni_with_spaces` | MIS:1 | COR:1 | +1 COR |
| `iban_with_spaces` | PAR:1 | COR:1 | +1 COR |
| `phone_international` | MIS:1 | COR:1 | +1 COR (potenziale) |

**Stima Totale:** +2-3 COR, conversione da MIS e PAR a COR.

---

## 6. Riferimenti

1. **CHPDA (2025):** [arXiv](https://arxiv.org/html/2502.07815v1) - Approccio ibrido regex+NER
2. **Hybrid ReGex (2025):** [JCO](https://ascopubs.org/doi/10.1200/CCI-25-00130) - Estrazione dati medici
3. **Legal NLP Survey (2024):** [arXiv](https://arxiv.org/html/2410.21306v3) - NER per dominio legale

---

**Tempo di esecuzione:** 0.003s
**Generato da:** AlexAlves87
**Data:** 05-02-2026
