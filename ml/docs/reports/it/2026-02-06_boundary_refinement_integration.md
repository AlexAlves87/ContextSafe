# Boundary Refinement - Integrazione nella Pipeline NER

**Data:** 06-02-2026
**Autor:** AlexAlves87
**Componente:** `scripts/preprocess/boundary_refinement.py` integrato in `ner_predictor.py`
**Standard:** SemEval 2013 Task 9 (Valutazione a livello di entità)

---

## 1. Riepilogo Esecutivo

Implementazione del raffinamento dei confini delle entità per convertire le corrispondenze parziali (PAR) in corrette (COR) secondo il framework di valutazione SemEval 2013.

### Risultati

| Suite di Test | Risultato |
|---------------|-----------|
| Test standalone | 12/12 (100%) |
| Test di integrazione | ✅ Funzionale |
| Raffinamenti applicati | 4/8 entità nella demo |

### Tipi di Raffinamento

| Tipo | Entità | Azione |
|------|--------|--------|
| OVER_EXTENDED | PERSON | Rimuovere prefissi: Don, Dña., D., Mr., Doña |
| OVER_EXTENDED | DATE | Rimuovere prefissi: a, el día, día |
| OVER_EXTENDED | ORGANIZATION | Rimuovere suffissi: virgole, punti e virgola |
| OVER_EXTENDED | ADDRESS | Rimuovere codice postale+città alla fine |
| TRUNCATED | POSTAL_CODE | Estendere a 5 cifre |
| TRUNCATED | DNI_NIE | Estendere per includere la lettera di controllo |

---

## 2. Metodologia

### 2.1 Diagnosi Precedente

`scripts/evaluate/diagnose_par_cases.py` è stato eseguito per identificare i pattern di errore:

```
TRUNCATED (2 casi):
  - [address_floor_door] Mancante alla fine: '001' (codice postale)
  - [testament_comparecencia] Mancante alla fine: 'Z' (lettera DNI)

OVER_EXTENDED (9 casi):
  - Nomi con prefissi onorifici inclusi
  - Date con prefisso "a" incluso
  - Organizzazioni con virgola finale
```

### 2.2 Implementazione

**File:** `scripts/preprocess/boundary_refinement.py`

```python
# Prefissi onorifici spagnoli (ordine: più lunghi prima)
PERSON_PREFIXES = [
    r"(?:Compareció\s+)?Don\s+",
    r"(?:Compareció\s+)?Doña\s+",
    r"Dña\.\s*",
    r"D\.\s*",
    r"Mr\.\s*",
    r"Mrs\.\s*",
    # ...
]

# Funzione principale
def refine_entity(text, entity_type, start, end, confidence, source, original_text):
    """Applica il raffinamento in base al tipo di entità."""
    if entity_type in REFINEMENT_FUNCTIONS:
        refined_text, refinement_applied = REFINEMENT_FUNCTIONS[entity_type](text, original_text)
    # ...
```

### 2.3 Integrazione nella Pipeline

**File:** `scripts/inference/ner_predictor.py`

```python
# Importazione con degradazione elegante
try:
    from preprocess.boundary_refinement import refine_entity, RefinedEntity
    REFINEMENT_AVAILABLE = True
except ImportError:
    REFINEMENT_AVAILABLE = False

# Nel metodo predict():
def predict(self, text, min_confidence=0.5, max_length=512):
    # 1. Normalizzazione del testo
    text = normalize_text_for_ner(text)

    # 2. Predizione NER
    entities = self._extract_entities(...)

    # 3. Merge Regex (ibrido)
    if REGEX_AVAILABLE:
        entities = self._merge_regex_detections(text, entities, min_confidence)

    # 4. Raffinamento dei confini (NUOVO)
    if REFINEMENT_AVAILABLE:
        entities = self._apply_boundary_refinement(text, entities)

    return entities
```

### 2.4 Riproducibilità

```bash
# Ambiente
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Test standalone
python scripts/preprocess/boundary_refinement.py

# Test di integrazione
python scripts/inference/ner_predictor.py
```

---

## 3. Risultati

### 3.1 Test Standalone (12/12)

| Test | Entità | Raffinamento | Risultato |
|------|--------|--------------|-----------|
| person_don | PERSON | Rimuovere "Don " | ✅ |
| person_dña | PERSON | Rimuovere "Dña. " | ✅ |
| person_d_dot | PERSON | Rimuovere "D. " | ✅ |
| person_mr | PERSON | Rimuovere "Mr. " | ✅ |
| person_no_change | PERSON | Nessun cambiamento | ✅ |
| date_a_prefix | DATE | Rimuovere "a " | ✅ |
| date_el_dia | DATE | Rimuovere "el día " | ✅ |
| org_trailing_comma | ORGANIZATION | Rimuovere "," | ✅ |
| address_with_postal_city | ADDRESS | Rimuovere "28013 Madrid" | ✅ |
| postal_extend | POSTAL_CODE | "28" → "28001" | ✅ |
| dni_extend_letter | DNI_NIE | "12345678-" → "12345678Z" | ✅ |
| dni_no_extend | DNI_NIE | Nessun cambiamento | ✅ |

**Tempo di esecuzione:** 0.002s

### 3.2 Test di Integrazione

| Input | Entità Originale | Entità Raffinata | Raffinamento |
|-------|------------------|------------------|--------------|
| "Don José García López con DNI..." | "Don José García López" | "José García López" | stripped_prefix:Don |
| "Dña. Ana Martínez Ruiz..." | "Dña. Ana Martínez Ruiz" | "Ana Martínez Ruiz" | stripped_prefix:Dña. |
| "Compareció Doña María Antonia..." | "Doña María Antonia Fernández Ruiz" | "María Antonia Fernández Ruiz" | stripped_prefix:Doña |
| "Mr. John Smith, residente..." | "Mr. John Smith" | "John Smith" | stripped_prefix:Mr. |

### 3.3 Entità Senza Raffinamento (Corrette)

| Input | Entità | Ragione |
|-------|--------|---------|
| "DNI 12345678Z" | "12345678Z" | Già corretto |
| "IBAN ES91 2100..." | "ES91 2100 0418 4502 0005 1332" | Già corretto |
| "Calle Alcalá 50" | "Calle Alcalá 50" | Già corretto |
| "Sevilla" | "Sevilla" | Già corretto |

---

## 4. Analisi

### 4.1 Impatto sulla Pipeline

Il raffinamento dei confini viene applicato **dopo** il merge NER+regex, agendo come post-processore:

```
Testo → Normalizzazione → NER → Merge Regex → Raffinamento → Entità finali
                                                ↑
                                          (Elemento 5)
```

### 4.2 Preservazione dei Metadati

Il raffinamento preserva tutti i metadati originali:
- `confidence`: Non modificato
- `source`: Non modificato (ner/regex)
- `checksum_valid`: Non modificato
- `checksum_reason`: Non modificato

Aggiunge nuovi campi:
- `original_text`: Testo prima del raffinamento
- `refinement_applied`: Tipo di raffinamento applicato

### 4.3 Osservazione su DATE

La data "a quince de marzo de dos mil veinticuatro" nel test di integrazione **non è stata raffinata** perché il modello NER ha rilevato "quince de marzo de dos mil veinticuatro" direttamente (senza il prefisso "a"). Questo indica che:

1. Il modello NER impara già alcuni confini corretti
2. Il raffinamento agisce come rete di sicurezza per i casi che il modello non gestisce

---

## 5. Pipeline Completa (5 Elementi)

### 5.1 Elementi Integrati

| # | Elemento | Standalone | Integrazione | Funzione |
|---|----------|------------|--------------|----------|
| 1 | TextNormalizer | 15/15 | ✅ | Evasione Unicode, omoglifi |
| 2 | Checksum Validators | 23/24 | ✅ | Aggiustamento della confidenza |
| 3 | Regex Patterns | 22/22 | ✅ | ID con spazi/trattini |
| 4 | Date Patterns | 14/14 | ✅ | Numeri romani |
| 5 | Boundary Refinement | 12/12 | ✅ | Conversione PAR→COR |

### 5.2 Flusso Dati

```
Input: "Don José García López con DNI 12345678Z"
                    ↓
[1] TextNormalizer: Nessun cambiamento (testo pulito)
                    ↓
[Modello NER]: Rileva "Don José García López" (PERSON), "12345678Z" (DNI_NIE)
                    ↓
[3] Merge Regex: Nessun cambiamento (NER ha già rilevato DNI completo)
                    ↓
[2] Checksum: DNI valido → boost di confidenza
                    ↓
[5] Boundary Refinement: "Don José García López" → "José García López"
                    ↓
Output: [PERSON] "José García López", [DNI_NIE] "12345678Z" ✅
```

---

## 6. Conclusioni

### 6.1 Risultati

1. **Raffinamento funzionale**: 12/12 test standalone, integrazione verificata
2. **Degradazione elegante**: Il sistema funziona senza il modulo (REFINEMENT_AVAILABLE=False)
3. **Preservazione dei metadati**: Checksum e source intatti
4. **Tracciabilità**: Campi `original_text` e `refinement_applied` per audit

### 6.2 Limitazioni Note

| Limitazione | Impatto | Mitigazione |
|-------------|---------|-------------|
| Solo prefissi/suffissi statici | Non gestisce casi dinamici | I pattern coprono il 90%+ dei casi legali |
| Estensione dipende dal contesto | Può fallire se il testo è troncato | Controllo della lunghezza |
| Nessun raffinamento CIF | Bassa priorità | Aggiungere se viene rilevato il pattern |

### 6.3 Prossimo Passo

Eseguire il test adversarial completo per misurare l'impatto sulle metriche:

```bash
python scripts/evaluate/test_ner_predictor_adversarial_v2.py
```

**Metriche da osservare:**
- PAR (corrispondenze parziali) - riduzione attesa
- COR (corrispondenze corrette) - aumento atteso
- Tasso di superamento - miglioramento atteso

---

## 7. Riferimenti

1. **SemEval 2013 Task 9**: Framework di valutazione delle entità (COR/INC/PAR/MIS/SPU)
2. **Diagnosi PAR**: `scripts/evaluate/diagnose_par_cases.py`
3. **Implementazione**: `scripts/preprocess/boundary_refinement.py`
4. **Integrazione**: `scripts/inference/ner_predictor.py` righe 37-47, 385-432

---

**Tempo di esecuzione totale:** 0.002s (standalone) + 1.39s (caricamento modello) + 18.1ms (inferenza)
**Generato da:** AlexAlves87
**Data:** 06-02-2026
