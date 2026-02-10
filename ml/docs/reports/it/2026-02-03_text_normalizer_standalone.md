# Elemento 1: Text Normalizer - Test Isolato

**Data:** 03-02-2026
**Stato:** ✅ COMPLETATO
**Tempo esecuzione:** 0.002s

---

## 1. Riepilogo

| Metrica | Valore |
|---------|--------|
| Test eseguiti | 15 |
| Test superati | 15 |
| Pass rate | 100% |
| Tempo | 0.002s |

## 2. Componente

**File:** `scripts/preprocess/text_normalizer.py`

**Classe principale:** `TextNormalizer`

**Funzionalità:**
- Normalizzazione NFKC (fullwidth → ASCII)
- Rimozione caratteri zero-width (U+200B-U+200F, U+2060-U+206F, U+FEFF)
- Mapping omoglifi Cirillico → Latino (17 caratteri)
- NBSP → spazio + collasso spazi multipli
- Rimozione trattini morbidi (soft hyphen)

**Preserva (critico per NER):**
- Maiuscole/Minuscole (RoBERTa è case-sensitive)
- Accenti spagnoli (María, García, ecc.)
- Punteggiatura legittima

## 3. Test Validati

| Test | Categoria | Descrizione |
|------|-----------|-------------|
| fullwidth_dni | Unicode | `１２３４５６７８Z` → `12345678Z` |
| fullwidth_mixed | Unicode | Lettere e numeri fullwidth |
| zero_width_in_dni | Evasione | Zero-width dentro DNI |
| zero_width_in_name | Evasione | Zero-width nei nomi |
| cyrillic_o_in_dni | Omoglifo | Cirillico О → Latino O |
| cyrillic_mixed | Omoglifo | Testo misto Cirillico/Latino |
| nbsp_in_address | Spazi | NBSP → spazio normale |
| multiple_spaces | Spazi | Collasso spazi multipli |
| soft_hyphen_in_word | OCR | Trattini morbidi rimossi |
| combined_evasion | Combinato | Tecniche multiple combinate |
| preserve_accents | Preserva | Accenti spagnoli intatti |
| preserve_case | Preserva | Case non modificato |
| preserve_punctuation | Preserva | Punteggiatura legale preservata |
| empty_string | Edge | Stringa vuota |
| only_spaces | Edge | Solo spazi |

## 4. Esempio di Diagnostica

**Input:** `DNI: １２​３４​５６​７８Х del Sr. María`

**Output:** `DNI: 12345678X del Sr. María`

**Modifiche applicate:**
1. Removed 3 zero-width characters
2. Applied NFKC normalization
3. Replaced 1 Cyrillic homoglyphs

## 5. Passaggio Successivo

Integrare `TextNormalizer` nel pipeline NER (`CompositeNerAdapter`) e valutare l'impatto sui test adversarial.

---

**Generato da:** AlexAlves87
