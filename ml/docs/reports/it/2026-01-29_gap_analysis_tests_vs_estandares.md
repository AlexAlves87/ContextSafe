# Analisi dei Gap: Test Attuali vs Standard Accademici

**Data:** 2026-01-29
**Autor:** AlexAlves87
**File analizzato:** `scripts/evaluate/test_ner_predictor_adversarial.py`

---

## 1. Riepilogo dei Gap

| Aspetto | Standard Accademico | Implementazione Attuale | Severità |
|---------|---------------------|-------------------------|----------|
| Modalità di valutazione | Strict (SemEval 2013) | Lenient (custom) | **CRITICO** |
| 4 Modalità SemEval | strict, exact, partial, type | Solo 1 modalità custom | ALTA |
| Libreria metriche | seqeval o nervaluate | Implementazione custom | ALTA |
| Metriche dettagliate | COR/INC/PAR/MIS/SPU | Solo TP/FP/FN | MEDIA |
| Metriche per tipo | F1 per PERSON, DNI, ecc. | Solo F1 aggregato | MEDIA |
| Riferimento NoiseBench | EMNLP 2024 | "ICLR 2024" (errore) | BASSA |
| Documentazione modalità | Esplicita nel report | Non documentata | MEDIA |

---

## 2. Analisi Dettagliata

### 2.1 CRITICO: Modalità di Matching Non è Strict

**Codice Attuale (righe 458-493):**

```python
def entities_match(expected: dict, detected: dict, tolerance: int = 5) -> bool:
    # Type must match
    if expected["type"] != detected["type"]:
        return False

    # Containment (detected contains expected or vice versa)
    if exp_text in det_text or det_text in exp_text:
        return True

    # Length difference tolerance
    if abs(len(exp_text) - len(det_text)) <= tolerance:
        # Check character overlap
        common = sum(1 for c in exp_text if c in det_text)
        if common >= len(exp_text) * 0.8:
            return True
```

**Problemi:**
1. Permette **containment** (Se "José García" è in "Don José García López", conta come match)
2. Permette **80% sovrapposizione caratteri** (non confine esatto)
3. Permette **tolleranza di 5 caratteri** in lunghezza

**Standard SemEval Strict:**
> "Corrispondenza esatta della stringa di superficie del confine E corrispondenza del tipo di entità"

**Impatto:** I risultati attuali (F1=0.784, 54.3% pass) potrebbero essere **GONFIATI** perché le corrispondenze parziali sono accettate come corrette.

### 2.2 ALTA: Non Usa seqeval o nervaluate

**Standard:** Usare librerie validate contro conlleval.

**Attuale:** Implementazione metriche custom.

**Rischio:** Le metriche custom potrebbero non essere comparabili con la letteratura accademica.

### 2.3 ALTA: Solo Una Modalità di Valutazione

**SemEval 2013 definisce 4 modalità:**

| Modalità | Confine | Tipo | Uso |
|----------|---------|------|-----|
| **strict** | Esatto | Esatto | Principale, rigoroso |
| exact | Esatto | Ignorato | Analisi confine |
| partial | Sovrapposizione | Ignorato | Analisi indulgente |
| type | Sovrapposizione | Esatto | Analisi classificazione |

**Attuale:** Solo una modalità custom (simile a partial/lenient).

**Impatto:** Non possiamo separare errori di confine da errori di tipo.

### 2.4 MEDIA: No Metriche COR/INC/PAR/MIS/SPU

**SemEval 2013:**
- **COR**: Correct (confine E tipo esatti)
- **INC**: Incorrect (confine esatto, tipo errato)
- **PAR**: Partial (confine con sovrapposizione)
- **MIS**: Missing (FN)
- **SPU**: Spurious (FP)

**Attuale:** Solo TP/FP/FN (non distingue INC da PAR).

### 2.5 MEDIA: No Metriche per Tipo di Entità

**Standard:** Riportare F1 per ogni tipo (PERSON, DNI_NIE, IBAN, ecc.)

**Attuale:** Solo F1 aggregato.

**Impatto:** Non sappiamo quali tipi di entità performano peggio.

### 2.6 BASSA: Errore di Riferimento

**Riga 10:** `NoiseBench (ICLR 2024)`

**Corretto:** `NoiseBench (EMNLP 2024)`

---

## 3. Impatto sui Risultati Riportati

### 3.1 Stima della Differenza Strict vs Lenient

Basato sulla letteratura, la modalità strict produce tipicamente **5-15% meno F1** rispetto a lenient:

| Metrica | Attuale (lenient) | Stimato (strict) |
|---------|-------------------|------------------|
| F1 | 0.784 | 0.67-0.73 |
| Pass rate | 54.3% | 40-48% |

**I risultati attuali sono ottimistici.**

### 3.2 Test Affetti da Matching Lenient

Test dove il matching lenient accetta come corretto ciò che strict rifiuterebbe:

| Test | Situazione | Impatto |
|------|------------|---------|
| `very_long_name` | Nome lungo, confine esatto? | Possibile |
| `address_floor_door` | Indirizzo complesso | Possibile |
| `testament_comparecencia` | Entità multiple | Alto |
| `judicial_sentence_header` | Date testuali | Alto |

---

## 4. Piano di Correzione

### 4.1 Modifiche Richieste

1. **Implementare modalità strict** (priorità CRITICA)
   - Confine deve essere esatto (normalizzato)
   - Tipo deve essere esatto

2. **Aggiungere nervaluate** (priorità ALTA)
   ```bash
   pip install nervaluate
   ```

3. **Riportare 4 modalità** (priorità ALTA)
   - strict (principale)
   - exact
   - partial
   - type

4. **Aggiungere metriche per tipo** (priorità MEDIA)

5. **Correggere riferimento NoiseBench** (priorità BASSA)

### 4.2 Strategia di Migrazione

Per mantenere comparabilità con risultati precedenti:

1. Eseguire con **entrambe le modalità** (lenient E strict)
2. Riportare **entrambe** nella documentazione
3. Usare **strict come metrica principale** in futuro
4. Documentare differenza per baseline

---

## 5. Nuovo Script Proposto

Creare `test_ner_predictor_adversarial_v2.py` con:

1. Modalità strict come default
2. Integrazione con nervaluate
3. Metriche COR/INC/PAR/MIS/SPU
4. F1 per tipo di entità
5. Opzione modalità legacy per confronto

---

## 6. Conclusioni

**I risultati attuali (F1=0.784, 54.3% pass) non sono comparabili con la letteratura accademica** perché:

1. Usano matching lenient, non strict
2. Non usano librerie standard (seqeval, nervaluate)
3. Non riportano metriche granulari (per tipo, COR/INC/PAR)

**Azione Immediata:** Prima di procedere con integrazione di TextNormalizer, dobbiamo:

1. Creare script v2 con standard accademici
2. Ri-stabilire baseline con modalità strict
3. POI valutare impatto miglioramento

---

**Generato da:** AlexAlves87
**Data:** 2026-01-29
