# Ricerca: Normalizzazione del Testo per NER in Documenti Legali

**Data:** 2026-01-27
**Autor:** AlexAlves87
**Tipo:** Revisione della Letteratura Accademica
**Stato:** Completato

---

## 1. Riepilogo Esecutivo

Questa ricerca analizza le migliori pratiche per la normalizzazione del testo nelle pipeline NER, con enfasi su:
1. Normalizzazione Unicode (fullwidth, zero-width, omoglifi)
2. Correzione di artefatti OCR
3. Integrazione con modelli transformer

### Scoperte Principali

| Scoperta | Fonte | Impatto |
|----------|-------|---------|
| NFKC normalizza fullwidth → ASCII automaticamente | UAX #15 Standard Unicode | Alto |
| I caratteri zero-width (U+200B-U+200F) devono essere rimossi esplicitamente | Consorzio Unicode | Alto |
| Neuroni sensibili all'OCR esistono nei transformer e possono essere modulati | arXiv:2409.16934 (ICADL 2024) | Medio |
| Il preprocessing deve corrispondere al pre-addestramento del modello | Best practices 2024 | Critico |
| NFKC distrugge informazioni in script complessi (arabo, ebraico) | UAX #15 | Basso (non si applica allo spagnolo) |

---

## 2. Metodologia

### 2.1 Fonti Consultate

| Fonte | Tipo | Anno | Rilevanza |
|-------|------|------|-----------|
| UAX #15 Standard Unicode | Specifica | 2024 | Standard Unicode |
| arXiv:2409.16934 | Paper (ICADL 2024) | 2024 | Neuroni sensibili all'OCR |
| TACL Neural OCR Post-Hoc | Paper accademico | 2021 | Correzione OCR neurale |
| Brenndoerfer NLP Guide | Tutorial tecnico | 2024 | Best practices industriali |
| Promptfoo Security | Articolo tecnico | 2024 | Evasione Unicode in AI |

### 2.2 Criteri di Ricerca

- "text normalization NER preprocessing Unicode OCR"
- "Unicode normalization NLP NER fullwidth characters zero-width space"
- "OCR post-correction NER robustness neural network ACL EMNLP"

---

## 3. Risultati

### 3.1 Forme di Normalizzazione Unicode

Lo standard Unicode (UAX #15) definisce 4 forme di normalizzazione:

| Forma | Nome | Descrizione | Uso in NER |
|-------|------|-------------|------------|
| **NFC** | Composizione Canonica | Compone caratteri (é = e + ´) | Standard |
| **NFD** | Decomposizione Canonica | Decompone caratteri | Ricerca |
| **NFKC** | Composizione di Compatibilità | NFC + compatibilità | **Raccomandato per NER** |
| **NFKD** | Decomposizione di Compatibilità | NFD + compatibilità | Analisi |

**Fonte:** [UAX #15: Unicode Normalization Forms](https://unicode.org/reports/tr15/)

#### 3.1.1 NFKC per Normalizzazione Entità

NFKC è la forma raccomandata per NER perché:

```
Fullwidth:  １２３４５６７８ → 12345678
Superscript: ² → 2
Fractions:   ½ → 1/2
Roman:       Ⅳ → IV
Ligatures:   ﬁ → fi
```

**Avvertenza:** NFKC distrugge informazioni in script complessi (arabo, ebraico, devanagari) dove i caratteri di controllo sono semanticamente rilevanti. Per lo spagnolo legale, questo non è un problema.

### 3.2 Caratteri Invisibili Problematici

**Fonte:** [The Invisible Threat: Zero-Width Unicode Characters](https://www.promptfoo.dev/blog/invisible-unicode-threats/)

| Codepoint | Nome | Problema | Azione |
|-----------|------|----------|--------|
| U+200B | Zero Width Space | Rompe la tokenizzazione | Rimuovere |
| U+200C | Zero Width Non-Joiner | Separa caratteri uniti | Rimuovere |
| U+200D | Zero Width Joiner | Unisce caratteri separati | Rimuovere |
| U+200E | Left-to-Right Mark | Confonde direzione testo | Rimuovere |
| U+200F | Right-to-Left Mark | Confonde direzione testo | Rimuovere |
| U+FEFF | BOM / Zero Width No-Break | Artefatto di encoding | Rimuovere |
| U+00A0 | Non-Breaking Space | Non rilevato da isspace() | → spazio normale |
| U+00AD | Soft Hyphen | Trattino invisibile | Rimuovere |

**Impatto su NER:**
- DNI `123​456​78Z` (con U+200B) non corrisponde a regex `\d{8}[A-Z]`
- Il tokenizzatore divide la parola in più token
- Il modello non riconosce l'entità

### 3.3 Omoglifi ed Evasione

**Fonte:** [Invisible Unicode Tricks Bypass AI Detection](https://justdone.com/blog/ai/invisible-unicode-tricks)

| Latino | Cirillico | Visivo | Codice |
|--------|-----------|--------|--------|
| A | А | Identico | U+0041 vs U+0410 |
| B | В | Identico | U+0042 vs U+0412 |
| E | Е | Identico | U+0045 vs U+0415 |
| O | О | Identico | U+004F vs U+041E |
| X | Х | Identico | U+0058 vs U+0425 |

**Impatto su NER:**
- DNI `12345678Х` (Cirillico) non corrisponde a regex con `[A-Z]`
- Il modello potrebbe non riconoscere come DNI valido

**Soluzione:** Normalizzare omoglifi latini comuni prima di NER.

### 3.4 Neuroni Sensibili all'OCR nei Transformer

**Fonte:** [Investigating OCR-Sensitive Neurons](https://arxiv.org/abs/2409.16934) (ICADL 2024)

#### Scoperte del Paper

1. **I transformer hanno neuroni sensibili all'OCR:**
   - Identificati tramite analisi dei pattern di attivazione
   - Rispondono diversamente a testo pulito vs corrotto

2. **Livelli critici identificati:**
   - Llama 2: Livelli 0-2, 11-13, 23-28
   - Mistral: Livelli 29-31

3. **Soluzione proposta:**
   - Neutralizzare neuroni sensibili all'OCR
   - Migliora le prestazioni NER su documenti storici

#### Applicazione a ContextSafe

Per il nostro modello RoBERTa fine-tuned:
- La normalizzazione del testo PRIMA dell'inferenza è più pratica
- Neutralizzare i neuroni richiede modifica dell'architettura del modello
- **Raccomandazione:** Pre-elaborazione, non modifica del modello

### 3.5 Errori OCR Comuni e Normalizzazione

**Fonte:** [OCR Data Entry: Preprocessing Text for NLP](https://labelyourdata.com/articles/ocr-data-entry)

| Errore OCR | Pattern | Normalizzazione |
|------------|---------|-----------------|
| l ↔ I ↔ 1 | `DNl`, `DN1` | → `DNI` |
| O ↔ 0 | `2l0O` | Contestuale (numeri) |
| rn ↔ m | `nom` → `nom` | Dizionario |
| S ↔ 5 | `E5123` | Contestuale |
| B ↔ 8 | `B-123` vs `8-123` | Contestuale |

**Strategia raccomandata:**
1. **Pre-elaborazione semplice:** l/I/1 → normalizzare in base al contesto
2. **Post-validazione:** Checksum (DNI, IBAN) rifiutano non validi
3. **Non tentare di correggere tutto:** Meglio rifiutare che inventare

### 3.6 Mancata Corrispondenza Pre-elaborazione-Pre-addestramento

**Fonte:** [Text Preprocessing Guide](https://mbrenndoerfer.com/writing/text-preprocessing-nlp-tokenization-normalization)

> "If you train a model with aggressively preprocessed text but deploy it on minimally preprocessed input, performance will crater."

**Critico per il nostro modello:**
- RoBERTa-BNE è stato pre-addestrato con testo case-sensitive
- NON applicare lowercase
- SÌ applicare normalizzazione Unicode (NFKC)
- SÌ rimuovere caratteri zero-width

---

## 4. Pipeline di Normalizzazione Proposta

### 4.1 Ordine delle Operazioni

```
Testo OCR/Grezzo
    ↓
[1] Rimuovere BOM (U+FEFF)
    ↓
[2] Rimuovere zero-width (U+200B-U+200F, U+2060-U+206F)
    ↓
[3] Normalizzazione NFKC (fullwidth → ASCII)
    ↓
[4] Normalizzare spazi (U+00A0 → spazio, comprimere multipli)
    ↓
[5] Mappatura omoglifi (Cirillico comune → Latino)
    ↓
[6] OCR contestuale (DNl → DNI solo se il contesto indica)
    ↓
Testo Normalizzato → NER
```

### 4.2 Implementazione Python

```python
import unicodedata
import re

# Caratteri da rimuovere
ZERO_WIDTH = re.compile(r'[\u200b-\u200f\u2060-\u206f\ufeff]')

# Omoglifi Cirillico → Latino
HOMOGLYPHS = {
    '\u0410': 'A',  # А → A
    '\u0412': 'B',  # В → B
    '\u0415': 'E',  # Е → E
    '\u041e': 'O',  # О → O
    '\u0421': 'C',  # С → C
    '\u0425': 'X',  # Х → X
    '\u0430': 'a',  # а → a
    '\u0435': 'e',  # е → e
    '\u043e': 'o',  # о → o
    '\u0441': 'c',  # с → c
    '\u0445': 'x',  # х → x
}

def normalize_text(text: str) -> str:
    """
    Normalizza il testo per l'elaborazione NER.

    Applica: NFKC, rimozione zero-width, mappatura omoglifi, normalizzazione spazi.
    NON applica: lowercase (RoBERTa è case-sensitive).
    """
    # 1. Rimuovere BOM e zero-width
    text = ZERO_WIDTH.sub('', text)

    # 2. Normalizzazione NFKC (fullwidth → ASCII)
    text = unicodedata.normalize('NFKC', text)

    # 3. Mappatura omoglifi
    for cyrillic, latin in HOMOGLYPHS.items():
        text = text.replace(cyrillic, latin)

    # 4. Normalizzare spazi (NBSP → spazio, comprimere multipli)
    text = text.replace('\u00a0', ' ')
    text = re.sub(r' +', ' ', text)

    # 5. Rimuovere trattini invisibili
    text = text.replace('\u00ad', '')

    return text.strip()
```

### 4.3 Test di Validazione

| Input | Output Previsto | Test |
|-------|-----------------|------|
| `１２３４５６７８Z` | `12345678Z` | Fullwidth |
| `123​456​78Z` | `12345678Z` | Zero-width |
| `12345678Х` | `12345678X` | Cirillico X |
| `D N I` | `D N I` | Spazi (senza comprimere parole) |
| `María` | `María` | Accenti preservati |

---

## 5. Analisi dei Gap

### 5.1 Confronto: Pratica Attuale vs Best Practices

| Aspetto | Best Practice | Implementazione Attuale | Gap |
|---------|---------------|-------------------------|-----|
| Normalizzazione NFKC | Applicare prima di NER | Non implementato | **CRITICO** |
| Rimozione zero-width | Rimuovere U+200B-F | Non implementato | **CRITICO** |
| Mappatura omoglifi | Cirillico → Latino | Non implementato | ALTO |
| Normalizzazione spazi | NBSP → spazio | Non implementato | MEDIO |
| OCR contestuale | DNl → DNI | Non implementato | MEDIO |
| Preservazione case | NO lowercase | Corretto | ✓ OK |

### 5.2 Impatto Stimato

| Correzione | Sforzo | Impatto su Test |
|------------|--------|-----------------|
| NFKC + zero-width | Basso (10 righe) | `fullwidth_numbers`: PASS |
| Mappatura omoglifi | Basso (tabella) | `cyrillic_o`: PASS (passa già, ma più robusto) |
| Normalizzazione spazi | Basso | Riduce FP in tokenizzazione |
| **Totale** | **~50 righe Python** | **+5-10% pass rate adversarial** |

---

## 6. Conclusioni

### 6.1 Scoperte Principali

1. **NFKC è sufficiente** per normalizzare fullwidth → ASCII senza codice aggiuntivo
2. **Caratteri zero-width** devono essere rimossi esplicitamente (regex semplice)
3. **Omoglifi** richiedono tabella di mappatura (Cirillico → Latino)
4. **NON applicare lowercase** - RoBERTa è case-sensitive
5. **OCR contestuale** è complesso - meglio validare con checksum dopo

### 6.2 Raccomandazione per ContextSafe

**Implementare `scripts/preprocess/text_normalizer.py`** con:
1. Funzione `normalize_text()` come descritto sopra
2. Integrare in pipeline di inferenza PRIMA del tokenizzatore
3. Applicare anche durante generazione dataset di addestramento

**Priorità:** ALTA - Risolverà test `fullwidth_numbers` e migliorerà robustezza generale.

---

## 7. Riferimenti

### Paper Accademici

1. **Investigating OCR-Sensitive Neurons to Improve Entity Recognition in Historical Documents**
   - arXiv:2409.16934, ICADL 2024
   - URL: https://arxiv.org/abs/2409.16934

2. **Neural OCR Post-Hoc Correction of Historical Corpora**
   - TACL, MIT Press
   - URL: https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00379

### Standard e Specifiche

3. **UAX #15: Unicode Normalization Forms**
   - Consorzio Unicode
   - URL: https://unicode.org/reports/tr15/

### Risorse Tecniche

4. **Text Normalization: Unicode Forms, Case Folding & Whitespace Handling for NLP**
   - Michael Brenndoerfer, 2024
   - URL: https://mbrenndoerfer.com/writing/text-normalization-unicode-nlp

5. **The Invisible Threat: How Zero-Width Unicode Characters Can Silently Backdoor Your AI-Generated Code**
   - Promptfoo, 2024
   - URL: https://www.promptfoo.dev/blog/invisible-unicode-threats/

6. **OCR Data Entry: Preprocessing Text for NLP Tasks in 2025**
   - Label Your Data
   - URL: https://labelyourdata.com/articles/ocr-data-entry

7. **Zero-width space - Wikipedia**
   - URL: https://en.wikipedia.org/wiki/Zero-width_space

---

**Tempo di ricerca:** 45 min
**Generato da:** AlexAlves87
**Data:** 2026-01-27
