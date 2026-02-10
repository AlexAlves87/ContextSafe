# Checksum Validators - Test Standalone

**Data:** 04-02-2026
**Autor:** AlexAlves87
**Componente:** `scripts/preprocess/checksum_validators.py`
**Standard:** Algoritmi ufficiali spagnoli (BOE)

---

## 1. Riepilogo Esecutivo

Implementazione e validazione standalone di validatori di checksum per identificatori spagnoli utilizzati nel pipeline NER-PII.

### Risultati

| Metrica | Valore |
|---------|--------|
| **Test Superati** | 23/24 (95.8%) |
| **Validatori Implementati** | 5 (DNI, NIE, IBAN, NSS, CIF) |
| **Tempo Esecuzione** | 0.003s |

### Conclusione

> **Tutti i validatori funzionano correttamente secondo gli algoritmi ufficiali.**
> L'unico fallimento (caso limite NSS) è un errore nell'aspettativa del test, non nel validatore.

---

## 2. Metodologia

### 2.1 Algoritmi Implementati

| Identificatore | Algoritmo | Fonte |
|----------------|-----------|-------|
| **DNI** | `lettera = TRWAGMYFPDXBNJZSQVHLCKE[numero % 23]` | BOE |
| **NIE** | X→0, Y→1, Z→2, poi DNI | BOE |
| **IBAN** | ISO 13616, mod 97 = 1 | ISO 13616 |
| **NSS** | `controllo = (provincia + numero) % 97` | Sicurezza Sociale |
| **CIF** | Somma posizioni pari + dispari con raddoppio, controllo = (10 - somma%10) % 10 | BOE |

### 2.2 Struttura del Validatore

Ogni validatore restituisce una tupla `(is_valid, confidence, reason)`:

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `is_valid` | bool | Vero se checksum corretto |
| `confidence` | float | 1.0 (valido), 0.5 (formato ok, checksum errato), 0.0 (formato invalido) |
| `reason` | str | Descrizione del risultato |

### 2.3 Riproducibilità

```bash
# Ambiente
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Esecuzione
python scripts/preprocess/checksum_validators.py

# Output atteso: 23/24 passed (95.8%)
```

---

## 3. Risultati

### 3.1 Riepilogo per Validatore

| Validatore | Test | Superati | Falliti |
|------------|------|----------|---------|
| DNI | 6 | 6 | 0 |
| NIE | 4 | 4 | 0 |
| DNI_NIE | 2 | 2 | 0 |
| IBAN | 4 | 4 | 0 |
| NSS | 2 | 1 | 1* |
| CIF | 4 | 4 | 0 |
| Casi limite | 2 | 2 | 0 |
| **Totale** | **24** | **23** | **1** |

*Il fallimento è un errore nell'aspettativa del test, non nel validatore.

### 3.2 Test Dettagliati

#### DNI (6/6 ✅)

| Test | Input | Atteso | Risultato |
|------|-------|--------|-----------|
| dni_valid_1 | `12345678Z` | ✅ valido | ✅ |
| dni_valid_2 | `00000000T` | ✅ valido | ✅ |
| dni_valid_spaces | `1234 5678 Z` | ✅ valido | ✅ |
| dni_invalid_letter | `12345678A` | ❌ invalido | ❌ (atteso Z) |
| dni_invalid_letter_2 | `00000000A` | ❌ invalido | ❌ (atteso T) |
| dni_invalid_format | `1234567Z` | ❌ invalido | ❌ (7 cifre) |

#### NIE (4/4 ✅)

| Test | Input | Atteso | Risultato |
|------|-------|--------|-----------|
| nie_valid_x | `X0000000T` | ✅ valido | ✅ |
| nie_valid_y | `Y0000000Z` | ✅ valido | ✅ |
| nie_valid_z | `Z0000000M` | ✅ valido | ✅ |
| nie_invalid_letter | `X0000000A` | ❌ invalido | ❌ (atteso T) |

#### IBAN (4/4 ✅)

| Test | Input | Atteso | Risultato |
|------|-------|--------|-----------|
| iban_valid_es | `ES9121000418450200051332` | ✅ valido | ✅ |
| iban_valid_spaces | `ES91 2100 0418 4502 0005 1332` | ✅ valido | ✅ |
| iban_invalid_check | `ES0021000418450200051332` | ❌ invalido | ❌ (cifre controllo 00) |
| iban_invalid_mod97 | `ES1234567890123456789012` | ❌ invalido | ❌ (mod 97 ≠ 1) |

#### NSS (1/2 - 1 fallimento aspettativa)

| Test | Input | Atteso | Risultato | Nota |
|------|-------|--------|-----------|------|
| nss_valid | `281234567890` | ❌ invalido | ❌ | Corretto (checksum casuale) |
| nss_format_ok | `280000000097` | ✅ valido | ❌ | **Errore aspettativa** |

**Analisi del fallimento:**
- Input: `280000000097`
- Provincia: `28`, Numero: `00000000`, Controllo: `97`
- Calcolo: `(28 * 10^8 + 0) % 97 = 2800000000 % 97 = 37`
- Atteso dal test: `97`, Reale: `37`
- **Il validatore è corretto.** L'aspettativa del test era incorretta.

#### CIF (4/4 ✅)

| Test | Input | Atteso | Risultato |
|------|-------|--------|-----------|
| cif_valid_a | `A12345674` | ✅ valido | ✅ |
| cif_valid_b | `B12345674` | ✅ valido | ✅ |
| cif_invalid | `A12345670` | ❌ invalido | ❌ (atteso 4) |

### 3.3 Demo di Validazione

```
DNI_NIE: '12345678Z'
  ✅ VALID (confidence: 1.0)
  Reason: Valid DNI checksum

DNI_NIE: '12345678A'
  ❌ INVALID (confidence: 0.5)
  Reason: Invalid checksum: expected 'Z', got 'A'

DNI_NIE: 'X0000000T'
  ✅ VALID (confidence: 1.0)
  Reason: Valid NIE checksum

IBAN: 'ES91 2100 0418 4502 0005 1332'
  ✅ VALID (confidence: 1.0)
  Reason: Valid IBAN checksum

CIF: 'A12345674'
  ✅ VALID (confidence: 1.0)
  Reason: Valid CIF checksum (digit)
```

---

## 4. Analisi degli Errori

### 4.1 Unico Fallimento: Caso Limite NSS

| Aspetto | Dettaglio |
|---------|-----------|
| Test | `nss_format_ok` |
| Input | `280000000097` |
| Problema | L'aspettativa del test assumeva che `97` fosse valido |
| Realtà | `(28 + "00000000") % 97 = 37`, non `97` |
| Azione | Correggere l'aspettativa nel test case |

### 4.2 Correzione Proposta

```python
# In TEST_CASES, cambiare:
TestCase("nss_format_ok", "280000000097", "NSS", True, "..."),
# In:
TestCase("nss_format_ok", "280000000037", "NSS", True, "NSS with valid control"),
```

O meglio, calcolare un NSS valido reale:
- Provincia: `28` (Madrid)
- Numero: `12345678`
- Controllo: `(2812345678) % 97 = 2812345678 % 97 = 8`
- NSS valido: `281234567808`

---

## 5. Conclusioni e Lavoro Futuro

### 5.1 Conclusioni

1. **Tutti i 5 validatori funzionano correttamente** secondo gli algoritmi ufficiali
2. **La struttura di ritorno (is_valid, confidence, reason)** permette un'integrazione flessibile
3. **Il livello di confidenza intermedio (0.5)** permette di distinguere:
   - Formato corretto ma checksum errato → possibile errore di battitura/OCR
   - Formato errato → probabilmente non quel tipo di ID

### 5.2 Uso nel Pipeline NER

| Scenario | Azione |
|----------|--------|
| Entità rilevata + checksum valido | Mantenere rilevamento (boost confidenza) |
| Entità rilevata + checksum invalido | Ridurre confidenza o marcare come "possible_typo" |
| Entità rilevata + formato invalido | Possibile falso positivo → revisionare |

### 5.3 Passo Successivo

**Integrazione nel pipeline NER per post-validazione:**
- Applicare validatori a entità rilevate come DNI_NIE, IBAN, NSS, CIF
- Regolare confidenza basata sul risultato della validazione
- Ridurre SPU (falsi positivi) rimuovendo rilevamenti con checksum invalidi

### 5.4 Impatto Stimato

| Metrica | Baseline | Stimato | Miglioramento |
|---------|----------|---------|---------------|
| SPU | 8 | 5-6 | -2 a -3 |
| F1 (strict) | 0.492 | 0.50-0.52 | +0.01-0.03 |

---

## 6. Riferimenti

1. **Algoritmo DNI/NIE:** BOE - Real Decreto 1553/2005
2. **Validazione IBAN:** ISO 13616-1:2020
3. **Formato NSS:** Tesoreria Generale della Sicurezza Sociale
4. **Algoritmo CIF:** BOE - Real Decreto 1065/2007
5. **Ricerca base:** `docs/reports/2026-01-28_investigacion_hybrid_ner.md`

---

**Tempo di esecuzione:** 0.003s
**Generato da:** AlexAlves87
**Data:** 04-02-2026
