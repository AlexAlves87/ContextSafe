# Guida alla Replicabilità: Pipeline NER-PII Multilingue

**Data:** 31-01-2026
**Autor:** AlexAlves87
**Progetto:** ContextSafe ML - Espansione Multilingue
**Versione:** 1.0.0

---

## 1. Riepilogo Esecutivo

Questo documento descrive come replicare il pipeline ibrido NER-PII di ContextSafe (legale spagnolo, F1 0.788) per altre lingue europee. L'approccio è **modulare**: ogni componente viene adattato alla lingua di destinazione mantenendo l'architettura collaudata.

### Lezione Appresa (Esperimento LoRA)

| Approccio | F1 Adversarial | Verdetto |
|-----------|----------------|----------|
| Fine-tuning LoRA puro | 0.016 | ❌ Overfitting grave |
| Pipeline ibrido (5 elementi) | **0.788** | ✅ Generalizza bene |

> **Conclusione:** Il fine-tuning dei transformer senza il pipeline ibrido non generalizza ai casi avversari. I 5 elementi di post-elaborazione sono **essenziali**.

---

## 2. Architettura del Pipeline (Agnostica rispetto alla Lingua)

```
┌─────────────────────────────────────────────────────────────────┐
│                     PIPELINE IBRIDO NER-PII                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Testo input                                                     │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [1] TextNormalizer                     │ ← Agnostico alla Lingua│
│  │     - Unicode NFKC                     │                      │
│  │     - Omoglifi (Cirillico→Latino)      │                      │
│  │     - Rimozione larghezza zero         │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [NER] Transformer LegalBERT            │ ← ADATTARE PER LINGUA│
│  │     - ES: RoBERTa-BNE CAPITEL NER      │                      │
│  │     - EN: Legal-BERT                   │                      │
│  │     - FR: JuriBERT                     │                      │
│  │     - IT: Italian-Legal-BERT           │                      │
│  │     - PT: Legal-BERTimbau              │                      │
│  │     - DE: German-Legal-BERT            │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [2] Checksum Validators                │ ← ADATTARE PER PAESE │
│  │     - Algoritmi di verifica            │                      │
│  │     - Aggiustamento confidenza         │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [3] Regex Patterns                     │ ← ADATTARE PER PAESE │
│  │     - Identificatori Nazionali         │                      │
│  │     - Formati con spazi/trattini       │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [4] Date Patterns                      │ ← ADATTARE PER LINGUA│
│  │     - Mesi in lingua locale            │                      │
│  │     - Formati legali/notarili          │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [5] Boundary Refinement                │ ← ADATTARE PER LINGUA│
│  │     - Prefissi onorifici               │                      │
│  │     - Suffissi organizzazione          │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  Entità finali                                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Componenti per Tipo di Adattamento

| Componente | Adattamento | Sforzo |
|------------|-------------|--------|
| TextNormalizer | Nessuno (universale) | 0 |
| Transformer NER | Cambiare modello base | Basso |
| Checksum Validators | Algoritmi per paese | Medio |
| Regex Patterns | Pattern per paese | Alto |
| Date Patterns | Mesi/formati per lingua | Medio |
| Boundary Refinement | Prefissi/suffissi per lingua | Medio |

---

## 3. Modelli Base Raccomandati per Lingua

### 3.1 Modelli Monolingua (Massime Prestazioni)

| Lingua | Modello | HuggingFace | Params | Corpus |
|--------|---------|-------------|--------|--------|
| 🇪🇸 Spagnolo | RoBERTa-BNE CAPITEL NER | `PlanTL-GOB-ES/roberta-base-bne-capitel-ner` | 125M | BNE + CAPITEL NER |
| 🇬🇧 Inglese | Legal-BERT | `nlpaueb/legal-bert-base-uncased` | 110M | 12GB legale |
| 🇫🇷 Francese | JuriBERT | `dascim/juribert-base` | 110M | Légifrance |
| 🇮🇹 Italiano | Italian-Legal-BERT | `dlicari/Italian-Legal-BERT` | 110M | Giurisprudenza |
| 🇵🇹 Portoghese | Legal-BERTimbau | `rufimelo/Legal-BERTimbau-base` | 110M | 30K doc |
| 🇩🇪 Tedesco | German-Legal-BERT | `elenanereiss/bert-german-legal` | 110M | Bundesrecht |

### 3.2 Modello Multilingua (Distribuzione Rapida)

| Modello | HuggingFace | Params | Lingue |
|---------|-------------|--------|--------|
| Legal-XLM-RoBERTa | `joelniklaus/legal-xlm-roberta-large` | 355M | 24 lingue |

**Compromesso:**
- Monolingua: +2-5% F1, richiede modello per lingua
- Multilingua: Sigolo modello, prestazioni leggermente inferiori

---

## 4. Adattamenti per Paese

### 4.1 Spagna (Implementato ✅)

#### Identificatori Nazionali

| Tipo | Formato | Checksum | Regex |
|------|---------|----------|-------|
| DNI | 8 cifre + lettera | mod 23 | `\d{8}[A-Z]` |
| NIE | X/Y/Z + 7 cifre + lett. | mod 23 | `[XYZ]\d{7}[A-Z]` |
| CIF | Lettera + 7 cifre + contr. | somma pari/dispari | `[A-W]\d{7}[0-9A-J]` |
| IBAN | ES + 22 caratteri | ISO 13616 mod 97 | `ES\d{2}[\d\s]{20}` |
| NSS | 12 cifre | mod 97 | `\d{12}` |
| Targa | 4 cifre + 3 lettere | nessuno | `\d{4}[BCDFGHJKLMNPRSTVWXYZ]{3}` |

#### Prefissi Onorifici

```python
PREFIXES_ES = [
    "Don", "Doña", "D.", "Dña.", "D.ª",
    "Sr.", "Sra.", "Srta.",
    "Ilmo.", "Ilma.", "Excmo.", "Excma.",
]
```

#### Mesi

```python
MONTHS_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]
```

---

### 4.2 Francia 🇫🇷

#### Identificatori Nazionali

| Tipo | Formato | Checksum | Regex |
|------|---------|----------|-------|
| NIR (Sécu) | 15 cifre | mod 97 | `[12]\d{2}(0[1-9]|1[0-2])\d{2}\d{3}\d{3}\d{2}` |
| SIRET | 14 cifre | Luhn | `\d{14}` |
| SIREN | 9 cifre | Luhn | `\d{9}` |
| IBAN | FR + 25 caratteri | ISO 13616 | `FR\d{2}[\d\s]{23}` |
| Carte ID | 12 caratteri | nessuno | `[A-Z0-9]{12}` |

#### Prefissi Onorifici

```python
PREFIXES_FR = [
    "Monsieur", "Madame", "Mademoiselle",
    "M.", "Mme", "Mlle",
    "Maître", "Me", "Me.",
    "Docteur", "Dr", "Dr.",
]
```

#### Mesi

```python
MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
]
```

#### Suffissi Organizzazione

```python
ORG_SUFFIXES_FR = [
    "S.A.", "SA", "S.A.S.", "SAS", "S.A.R.L.", "SARL",
    "S.C.I.", "SCI", "E.U.R.L.", "EURL", "S.N.C.", "SNC",
]
```

---

### 4.3 Italia 🇮🇹

#### Identificatori Nazionali

| Tipo | Formato | Checksum | Regex |
|------|---------|----------|-------|
| Codice Fiscale | 16 caratteri | mod 26 speciale | `[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]` |
| Partita IVA | 11 cifre | Luhn variante | `\d{11}` |
| IBAN | IT + 25 caratteri | ISO 13616 | `IT\d{2}[A-Z][\d\s]{22}` |
| Carta Identità | 2 lettere + 7 cifre | nessuno | `[A-Z]{2}\d{7}` |

#### Checksum Codice Fiscale

```python
def validate_codice_fiscale(cf: str) -> bool:
    """Algoritmo mod 26 con valori speciali per posizioni pari/dispari."""
    ODD_VALUES = {'0': 1, '1': 0, '2': 5, ...}  # Tabella completa
    EVEN_VALUES = {'0': 0, '1': 1, '2': 2, ...}
    # Somma posizioni dispari con ODD_VALUES, pari con EVEN_VALUES
    # Lettera di controllo = chr(ord('A') + total % 26)
```

#### Prefissi Onorifici

```python
PREFIXES_IT = [
    "Signor", "Signora", "Signorina",
    "Sig.", "Sig.ra", "Sig.na",
    "Dott.", "Dott.ssa", "Avv.", "Ing.",
    "On.", "Sen.", "Onorevole",
]
```

#### Mesi

```python
MONTHS_IT = [
    "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"
]
```

---

### 4.4 Portogallo 🇵🇹

#### Identificatori Nazionali

| Tipo | Formato | Checksum | Regex |
|------|---------|----------|-------|
| NIF | 9 cifre | mod 11 | `[123568]\d{8}` |
| CC (Cartão Cidadão) | 8 cifre + 1 lett. + 2 cifre | mod 11 + lettera | `\d{8}[A-Z]\d{2}` |
| NISS | 11 cifre | mod 10 | `\d{11}` |
| IBAN | PT + 23 caratteri | ISO 13616 | `PT\d{2}[\d\s]{21}` |

#### Checksum NIF Portogallo

```python
def validate_nif_pt(nif: str) -> bool:
    """Algoritmo mod 11 con pesi decrescenti."""
    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(d) * w for d, w in zip(nif[:8], weights))
    control = 11 - (total % 11)
    if control >= 10:
        control = 0
    return int(nif[8]) == control
```

#### Prefissi Onorifici

```python
PREFIXES_PT = [
    "Senhor", "Senhora", "Sr.", "Sra.", "Srª",
    "Dom", "Dona", "D.",
    "Doutor", "Doutora", "Dr.", "Dra.",
    "Exmo.", "Exma.",
]
```

---

### 4.5 Germania 🇩🇪

#### Identificatori Nazionali

| Tipo | Formato | Checksum | Regex |
|------|---------|----------|-------|
| Steuer-ID | 11 cifre | ISO 7064 mod 11-10 | `\d{11}` |
| Personalausweis | 10 caratteri | mod 10 speciale | `[A-Z0-9]{10}` |
| IBAN | DE + 20 caratteri | ISO 13616 | `DE\d{2}[\d\s]{18}` |
| Handelsregister | HRA/HRB + numero | nessuno | `HR[AB]\s?\d+` |

#### Prefissi Onorifici

```python
PREFIXES_DE = [
    "Herr", "Frau",
    "Dr.", "Prof.", "Prof. Dr.",
    "Rechtsanwalt", "RA", "Notar",
]
```

#### Mesi

```python
MONTHS_DE = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember"
]
```

---

### 4.6 Regno Unito 🇬🇧

#### Identificatori Nazionali

| Tipo | Formato | Checksum | Regex |
|------|---------|----------|-------|
| NI Number | 2 lett. + 6 cifre + lett. | non verificabile | `[A-Z]{2}\d{6}[A-D]` |
| Company Number | 8 caratteri | nessuno | `[A-Z]{2}\d{6}|[\d]{8}` |
| IBAN | GB + 22 caratteri | ISO 13616 | `GB\d{2}[A-Z]{4}[\d\s]{14}` |
| Passaporto | 9 cifre | nessuno | `\d{9}` |

#### Prefissi Onorifici

```python
PREFIXES_EN = [
    "Mr", "Mr.", "Mrs", "Mrs.", "Ms", "Ms.", "Miss",
    "Dr", "Dr.", "Prof", "Prof.",
    "Sir", "Dame", "Lord", "Lady",
    "The Honourable", "Hon.",
]
```

---

## 5. Checklist di Implementazione per Lingua

### Fase 1: Preparazione (1-2 giorni)

- [ ] **Selezionare modello base** dalla tabella 3.1
- [ ] **Scaricare modello** in `models/pretrained/{modello}/`
- [ ] **Verificare caricamento** con script di test
- [ ] **Definire categorie PII** rilevanti per il paese

### Fase 2: Checksum Validators (2-3 giorni)

- [ ] **Ricercare algoritmi di validazione** per il paese
- [ ] **Implementare validatori** in `scripts/preprocess/{country}_validators.py`
- [ ] **Creare unit test** (minimo 20 casi per tipo)
- [ ] **Documentare algoritmi** con riferimenti ufficiali

### Fase 3: Regex Patterns (3-5 giorni)

- [ ] **Raccogliere formati ufficiali** di ID del paese
- [ ] **Implementare pattern** in `scripts/preprocess/{country}_id_patterns.py`
- [ ] **Includere varianti** con spazi, trattini, punti
- [ ] **Test con esempi reali** (anonimizzati)

### Fase 4: Date Patterns (1-2 giorni)

- [ ] **Tradurre mesi** nella lingua di destinazione
- [ ] **Adattare formati** legali/notarili locali
- [ ] **Implementare** in `scripts/preprocess/{country}_date_patterns.py`
- [ ] **Test con date reali** da documenti legali

### Fase 5: Boundary Refinement (1-2 giorni)

- [ ] **Compilare lista** di prefissi onorifici
- [ ] **Compilare lista** di suffissi organizzazione
- [ ] **Implementare** in `scripts/preprocess/{country}_boundary_refinement.py`
- [ ] **Test con nomi/org** reali

### Fase 6: Gazzette (2-4 giorni)

- [ ] **Nomi propri frequenti** (equivalente ISTAT)
- [ ] **Cognomi** frequenti
- [ ] **Comuni/città**
- [ ] **Organizzazioni** note (aziende, istituzioni)

### Fase 7: Test Set Adversarial (2-3 giorni)

- [ ] **Creare 30-40 casi** specifici per la lingua:
  - Edge case (formati insoliti)
  - Adversarial (negazioni, esempi, finzione)
  - Corruzione OCR
  - Evasione Unicode (già coperto)
  - Mondo reale (documenti legali tipici)
- [ ] **Definire entità attese** per ogni caso
- [ ] **Eseguire valutazione SemEval**

### Fase 8: Integrazione (1-2 giorni)

- [ ] **Integrare componenti** in `ner_predictor_{lang}.py`
- [ ] **Eseguire test set adversarial**
- [ ] **Adattare** fino a F1 ≥ 0.70
- [ ] **Documentare risultati**

---

## 6. Stima dello Sforzo Totale

| Lingua | Modello | Complessità ID | Sforzo Stimato |
|--------|---------|----------------|----------------|
| 🇫🇷 Francese | JuriBERT | Media (NIR, SIRET) | 2-3 settimane |
| 🇮🇹 Italiano | Italian-Legal-BERT | Alta (Codice Fiscale) | 3-4 settimane |
| 🇵🇹 Portoghese | Legal-BERTimbau | Media (NIF, CC) | 2-3 settimane |
| 🇩🇪 Tedesco | German-Legal-BERT | Media (Steuer-ID) | 2-3 settimane |
| 🇬🇧 Inglese | Legal-BERT | Bassa (NI Number) | 1-2 settimane |

**Totale per 5 lingue:** 10-15 settimane (1 sviluppatore)
**Con parallelizzazione (2-3 dev):** 4-6 settimane

---

## 7. Struttura dei File per Lingua

```
ml/
├── scripts/
│   ├── preprocess/
│   │   ├── spanish_id_patterns.py      # ✅ Implementato
│   │   ├── spanish_date_patterns.py    # ✅ Implementato
│   │   ├── boundary_refinement.py      # ✅ Implementato (adattare)
│   │   │
│   │   ├── french_id_patterns.py       # Da implementare
│   │   ├── french_date_patterns.py
│   │   ├── french_validators.py
│   │   │
│   │   ├── italian_id_patterns.py      # Da implementare
│   │   ├── italian_date_patterns.py
│   │   ├── italian_validators.py
│   │   │
│   │   └── ... (per lingua)
│   │
│   ├── inference/
│   │   ├── ner_predictor.py            # ✅ Spagnolo
│   │   ├── ner_predictor_fr.py         # Da implementare
│   │   ├── ner_predictor_it.py
│   │   └── ...
│   │
│   └── evaluate/
│       ├── test_ner_predictor_adversarial_v2.py  # ✅ Spagnolo
│       ├── adversarial_tests_fr.py               # Da implementare
│       └── ...
│
├── gazetteers/
│   ├── es/                             # ✅ Implementato
│   │   ├── nombres.json
│   │   ├── apellidos.json
│   │   └── municipios.json
│   │
│   ├── fr/                             # Da implementare
│   ├── it/
│   ├── pt/
│   ├── de/
│   └── en/
│
└── models/
    └── pretrained/
        ├── legal-xlm-roberta-base/     # ✅ Scaricato
        ├── juribert-base/              # Da scaricare
        ├── italian-legal-bert/
        └── ...
```

---

## 8. Riferimenti

### 8.1 Paper e Documentazione

| Risorsa | URL | Uso |
|---------|-----|-----|
| Legal-BERT Paper | aclanthology.org/2020.findings-emnlp.261 | Architettura |
| JuriBERT Paper | aclanthology.org/2021.nllp-1.9 | Francese legale |
| SemEval 2013 Task 9 | aclweb.org/anthology/S13-2013 | Metriche valutazione |
| ISO 13616 (IBAN) | iso.org/standard/81090.html | Checksum IBAN |

### 8.2 Fonti di Gazzette per Paese

| Paese | Nomi | Comuni | IDs |
|-------|------|--------|-----|
| 🇪🇸 Spagna | INE | INE | BOE |
| 🇫🇷 Francia | INSEE | INSEE | Légifrance |
| 🇮🇹 Italia | ISTAT | ISTAT | Normattiva |
| 🇵🇹 Portogallo | INE-PT | INE-PT | DRE |
| 🇩🇪 Germania | Statistisches Bundesamt | - | Bundesrecht |
| 🇬🇧 Regno Unito | ONS | ONS | legislation.gov.uk |

---

## 9. Lezioni Apprese (ContextSafe ES)

### 9.1 Cosa ha funzionato

1.  **Pipeline ibrido > ML puro**: I transformer da soli non generalizzano a casi avversari
2.  **Regex per formati variabili**: DNI con spazi, IBAN con gruppi
3.  **Validazione checksum**: Riduce i falsi positivi in modo significativo
4.  **Raffinamento limiti**: Converte PAR→COR (16 casi corretti)
5.  **Test set adversarial**: Rileva problemi prima della produzione

### 9.2 Cosa NON ha funzionato

1.  **Fine-tuning LoRA senza pipeline**: 0.016 F1 in adversarial (overfitting)
2.  **GLiNER zero-shot**: 0.325 F1 (non conosce i formati spagnoli)
3.  **Affidarsi solo alle metriche del dev set**: 0.989 dev vs 0.016 adversarial

### 9.3 Raccomandazioni

1.  **Creare sempre test set adversarial** prima di dichiarare "pronto"
2.  **Implementare validatori checksum** per tutti gli ID con verifica matematica
3.  **Investire in gazzette di qualità** (nomi, comuni)
4.  **Documentare ogni elemento** con test standalone

---

## 10. Prossimi Passi

1.  **Prioritizzare lingua** in base alla domanda di mercato
2.  **Scaricare modello base** della lingua selezionata
3.  **Adattare componenti** seguendo questa checklist
4.  **Creare test set adversarial** specifico
5.  **Iterare fino a F1 ≥ 0.70** in adversarial

---

**Generato da:** AlexAlves87
**Data:** 31-01-2026
**Versione:** 1.0.0
