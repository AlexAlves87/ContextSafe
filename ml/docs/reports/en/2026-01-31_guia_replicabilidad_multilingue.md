# Replicability Guide: Multilingual NER-PII Pipeline

**Date:** 2026-01-31
**Author:** AlexAlves87
**Project:** ContextSafe ML - Multilingual Expansion
**Version:** 1.0.0

---

## 1. Executive Summary

This document describes how to replicate ContextSafe's hybrid NER-PII pipeline (Spanish legal, F1 0.788) for other European languages. The approach is **modular**: each component adapts to the target language while maintaining the proven architecture.

### Lesson Learned (LoRA experiment)

| Approach | Adversarial F1 | Verdict |
|----------|----------------|---------|
| Pure LoRA fine-tuning | 0.016 | ❌ Severe overfitting |
| Hybrid Pipeline (5 elements) | **0.788** | ✅ Generalizes well |

> **Conclusion:** Fine-tuning transformers without the hybrid pipeline does not generalize to adversarial cases. The 5 post-processing elements are **essential**.

---

## 2. Pipeline Architecture (Language-Agnostic)

```
┌─────────────────────────────────────────────────────────────────┐
│                     HYBRID NER-PII PIPELINE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input Text                                                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [1] TextNormalizer                     │ ← Language-agnostic  │
│  │     - Unicode NFKC                     │                      │
│  │     - Homoglyphs (Cyrillic→Latin)      │                      │
│  │     - Zero-width removal               │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [NER] Transformer LegalBERT            │ ← ADAPT PER LANGUAGE │
│  │     - ES: RoBERTa-BNE CAPITEL NER      │                      │
│  │     - EN: Legal-BERT                   │                      │
│  │     - FR: JuriBERT                     │                      │
│  │     - IT: Italian-Legal-BERT           │                      │
│  │     - PT: Legal-BERTimbau              │                      │
│  │     - DE: German-Legal-BERT            │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [2] Checksum Validators                │ ← ADAPT PER COUNTRY  │
│  │     - Verification algorithms          │                      │
│  │     - Confidence adjustment            │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [3] Regex Patterns                     │ ← ADAPT PER COUNTRY  │
│  │     - National IDs                     │                      │
│  │     - Formats with spaces/dashes       │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [4] Date Patterns                      │ ← ADAPT PER LANGUAGE │
│  │     - Months in local language         │                      │
│  │     - Legal/notarial formats           │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [5] Boundary Refinement                │ ← ADAPT PER LANGUAGE │
│  │     - Honorific prefixes               │                      │
│  │     - Organization suffixes            │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  Final Entities                                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Components by Adaptation Type

| Component | Adaptation | Effort |
|-----------|------------|--------|
| TextNormalizer | None (universal) | 0 |
| Transformer NER | Change base model | Low |
| Checksum Validators | Algorithms per country | Medium |
| Regex Patterns | Patterns per country | High |
| Date Patterns | Months/formats per language | Medium |
| Boundary Refinement | Prefixes/suffixes per language | Medium |

---

## 3. Recommended Base Models by Language

### 3.1 Monolingual Models (Maximum Performance)

| Language | Model | HuggingFace | Params | Corpus |
|----------|-------|-------------|--------|--------|
| 🇪🇸 Spanish | RoBERTa-BNE CAPITEL NER | `PlanTL-GOB-ES/roberta-base-bne-capitel-ner` | 125M | BNE + CAPITEL NER |
| 🇬🇧 English | Legal-BERT | `nlpaueb/legal-bert-base-uncased` | 110M | 12GB legal |
| 🇫🇷 French | JuriBERT | `dascim/juribert-base` | 110M | Légifrance |
| 🇮🇹 Italian | Italian-Legal-BERT | `dlicari/Italian-Legal-BERT` | 110M | Giurisprudenza |
| 🇵🇹 Portuguese | Legal-BERTimbau | `rufimelo/Legal-BERTimbau-base` | 110M | 30K docs |
| 🇩🇪 German | German-Legal-BERT | `elenanereiss/bert-german-legal` | 110M | Bundesrecht |

### 3.2 Multilingual Model (Fast Deployment)

| Model | HuggingFace | Params | Languages |
|-------|-------------|--------|-----------|
| Legal-XLM-RoBERTa | `joelniklaus/legal-xlm-roberta-large` | 355M | 24 languages |

**Trade-off:**
- Monolingual: +2-5% F1, requires model per language
- Multilingual: Single model, slightly lower performance

---

## 4. Adaptations by Country

### 4.1 Spain (Implemented ✅)

#### National Identifiers

| Type | Format | Checksum | Regex |
|------|--------|----------|-------|
| DNI | 8 digits + letter | mod 23 | `\d{8}[A-Z]` |
| NIE | X/Y/Z + 7 digits + letter | mod 23 | `[XYZ]\d{7}[A-Z]` |
| CIF | Letter + 7 digits + control | sum even/odd | `[A-W]\d{7}[0-9A-J]` |
| IBAN | ES + 22 characters | ISO 13616 mod 97 | `ES\d{2}[\d\s]{20}` |
| NSS | 12 digits | mod 97 | `\d{12}` |
| License Plate | 4 digits + 3 letters | none | `\d{4}[BCDFGHJKLMNPRSTVWXYZ]{3}` |

#### Honorific Prefixes

```python
PREFIXES_ES = [
    "Don", "Doña", "D.", "Dña.", "D.ª",
    "Sr.", "Sra.", "Srta.",
    "Ilmo.", "Ilma.", "Excmo.", "Excma.",
]
```

#### Months

```python
MONTHS_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]
```

---

### 4.2 France 🇫🇷

#### National Identifiers

| Type | Format | Checksum | Regex |
|------|--------|----------|-------|
| NIR (Sécu) | 15 digits | mod 97 | `[12]\d{2}(0[1-9]|1[0-2])\d{2}\d{3}\d{3}\d{2}` |
| SIRET | 14 digits | Luhn | `\d{14}` |
| SIREN | 9 digits | Luhn | `\d{9}` |
| IBAN | FR + 25 characters | ISO 13616 | `FR\d{2}[\d\s]{23}` |
| Carte ID | 12 characters | none | `[A-Z0-9]{12}` |

#### Honorific Prefixes

```python
PREFIXES_FR = [
    "Monsieur", "Madame", "Mademoiselle",
    "M.", "Mme", "Mlle",
    "Maître", "Me", "Me.",
    "Docteur", "Dr", "Dr.",
]
```

#### Months

```python
MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
]
```

#### Organization Suffixes

```python
ORG_SUFFIXES_FR = [
    "S.A.", "SA", "S.A.S.", "SAS", "S.A.R.L.", "SARL",
    "S.C.I.", "SCI", "E.U.R.L.", "EURL", "S.N.C.", "SNC",
]
```

---

### 4.3 Italy 🇮🇹

#### National Identifiers

| Type | Format | Checksum | Regex |
|------|--------|----------|-------|
| Codice Fiscale | 16 characters | special mod 26 | `[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]` |
| Partita IVA | 11 digits | Luhn variant | `\d{11}` |
| IBAN | IT + 25 characters | ISO 13616 | `IT\d{2}[A-Z][\d\s]{22}` |
| Carta Identità | 2 letters + 7 digits | none | `[A-Z]{2}\d{7}` |

#### Codice Fiscale Checksum

```python
def validate_codice_fiscale(cf: str) -> bool:
    """Mod 26 algorithm with special values for even/odd positions."""
    ODD_VALUES = {'0': 1, '1': 0, '2': 5, ...}  # Full table
    EVEN_VALUES = {'0': 0, '1': 1, '2': 2, ...}
    # Sum odd positions with ODD_VALUES, even with EVEN_VALUES
    # Control letter = chr(ord('A') + total % 26)
```

#### Honorific Prefixes

```python
PREFIXES_IT = [
    "Signor", "Signora", "Signorina",
    "Sig.", "Sig.ra", "Sig.na",
    "Dott.", "Dott.ssa", "Avv.", "Ing.",
    "On.", "Sen.", "Onorevole",
]
```

#### Months

```python
MONTHS_IT = [
    "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"
]
```

---

### 4.4 Portugal 🇵🇹

#### National Identifiers

| Type | Format | Checksum | Regex |
|------|--------|----------|-------|
| NIF | 9 digits | mod 11 | `[123568]\d{8}` |
| CC (Cartão Cidadão) | 8 digits + 1 letter + 2 digits | mod 11 + letter | `\d{8}[A-Z]\d{2}` |
| NISS | 11 digits | mod 10 | `\d{11}` |
| IBAN | PT + 23 characters | ISO 13616 | `PT\d{2}[\d\s]{21}` |

#### NIF Portugal Checksum

```python
def validate_nif_pt(nif: str) -> bool:
    """Mod 11 algorithm with decreasing weights."""
    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(d) * w for d, w in zip(nif[:8], weights))
    control = 11 - (total % 11)
    if control >= 10:
        control = 0
    return int(nif[8]) == control
```

#### Honorific Prefixes

```python
PREFIXES_PT = [
    "Senhor", "Senhora", "Sr.", "Sra.", "Srª",
    "Dom", "Dona", "D.",
    "Doutor", "Doutora", "Dr.", "Dra.",
    "Exmo.", "Exma.",
]
```

---

### 4.5 Germany 🇩🇪

#### National Identifiers

| Type | Format | Checksum | Regex |
|------|--------|----------|-------|
| Steuer-ID | 11 digits | ISO 7064 mod 11-10 | `\d{11}` |
| Personalausweis | 10 characters | special mod 10 | `[A-Z0-9]{10}` |
| IBAN | DE + 20 characters | ISO 13616 | `DE\d{2}[\d\s]{18}` |
| Handelsregister | HRA/HRB + number | none | `HR[AB]\s?\d+` |

#### Honorific Prefixes

```python
PREFIXES_DE = [
    "Herr", "Frau",
    "Dr.", "Prof.", "Prof. Dr.",
    "Rechtsanwalt", "RA", "Notar",
]
```

#### Months

```python
MONTHS_DE = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember"
]
```

---

### 4.6 United Kingdom 🇬🇧

#### National Identifiers

| Type | Format | Checksum | Regex |
|------|--------|----------|-------|
| NI Number | 2 letters + 6 digits + letter | none verifiable | `[A-Z]{2}\d{6}[A-D]` |
| Company Number | 8 characters | none | `[A-Z]{2}\d{6}|[\d]{8}` |
| IBAN | GB + 22 characters | ISO 13616 | `GB\d{2}[A-Z]{4}[\d\s]{14}` |
| Passport | 9 digits | none | `\d{9}` |

#### Honorific Prefixes

```python
PREFIXES_EN = [
    "Mr", "Mr.", "Mrs", "Mrs.", "Ms", "Ms.", "Miss",
    "Dr", "Dr.", "Prof", "Prof.",
    "Sir", "Dame", "Lord", "Lady",
    "The Honourable", "Hon.",
]
```

---

## 5. Implementation Checklist per Language

### Phase 1: Preparation (1-2 days)

- [ ] **Select base model** from table 3.1
- [ ] **Download model** to `models/pretrained/{model}/`
- [ ] **Verify loading** with test script
- [ ] **Define PII categories** relevant for the country

### Phase 2: Checksum Validators (2-3 days)

- [ ] **Research validation algorithms** for the country
- [ ] **Implement validators** in `scripts/preprocess/{country}_validators.py`
- [ ] **Create unit tests** (minimum 20 cases per type)
- [ ] **Document algorithms** with official references

### Phase 3: Regex Patterns (3-5 days)

- [ ] **Collect official formats** of country IDs
- [ ] **Implement patterns** in `scripts/preprocess/{country}_id_patterns.py`
- [ ] **Include variants** with spaces, dashes, dots
- [ ] **Tests with real examples** (anonymized)

### Phase 4: Date Patterns (1-2 days)

- [ ] **Translate months** to target language
- [ ] **Adapt formats** local legal/notarial
- [ ] **Implement** in `scripts/preprocess/{country}_date_patterns.py`
- [ ] **Tests with real dates** from legal documents

### Phase 5: Boundary Refinement (1-2 days)

- [ ] **Compile list** of honorific prefixes
- [ ] **Compile list** of organization suffixes
- [ ] **Implement** in `scripts/preprocess/{country}_boundary_refinement.py`
- [ ] **Tests with real names/orgs**

### Phase 6: Gazetteers (2-4 days)

- [ ] Frequent **First Names** (INE equivalent)
- [ ] Frequent **Surnames**
- [ ] **Municipalities/Cities**
- [ ] Known **Organizations** (companies, institutions)

### Phase 7: Adversarial Test Set (2-3 days)

- [ ] **Create 30-40 cases** specific to the language:
  - Edge cases (unusual formats)
  - Adversarial (negations, examples, fiction)
  - OCR corruption
  - Unicode evasion (already covered)
  - Real world (typical legal documents)
- [ ] **Define expected entities** for each case
- [ ] **Run SemEval evaluation**

### Phase 8: Integration (1-2 days)

- [ ] **Integrate components** in `ner_predictor_{lang}.py`
- [ ] **Run adversarial test set**
- [ ] **Adjust** until F1 ≥ 0.70
- [ ] **Document results**

---

## 6. Total Effort Estimation

| Language | Model | IDs Complexity | Est. Effort |
|----------|-------|----------------|-------------|
| 🇫🇷 French | JuriBERT | Medium (NIR, SIRET) | 2-3 weeks |
| 🇮🇹 Italian | Italian-Legal-BERT | High (Codice Fiscale) | 3-4 weeks |
| 🇵🇹 Portuguese | Legal-BERTimbau | Medium (NIF, CC) | 2-3 weeks |
| 🇩🇪 German | German-Legal-BERT | Medium (Steuer-ID) | 2-3 weeks |
| 🇬🇧 English | Legal-BERT | Low (NI Number) | 1-2 weeks |

**Total for 5 languages:** 10-15 weeks (1 developer)
**With parallelization (2-3 devs):** 4-6 weeks

---

## 7. File Structure by Language

```
ml/
├── scripts/
│   ├── preprocess/
│   │   ├── spanish_id_patterns.py      # ✅ Implemented
│   │   ├── spanish_date_patterns.py    # ✅ Implemented
│   │   ├── boundary_refinement.py      # ✅ Implemented (adapt)
│   │   │
│   │   ├── french_id_patterns.py       # To implement
│   │   ├── french_date_patterns.py
│   │   ├── french_validators.py
│   │   │
│   │   ├── italian_id_patterns.py      # To implement
│   │   ├── italian_date_patterns.py
│   │   ├── italian_validators.py
│   │   │
│   │   └── ... (per language)
│   │
│   ├── inference/
│   │   ├── ner_predictor.py            # ✅ Spanish
│   │   ├── ner_predictor_fr.py         # To implement
│   │   ├── ner_predictor_it.py
│   │   └── ...
│   │
│   └── evaluate/
│       ├── test_ner_predictor_adversarial_v2.py  # ✅ Spanish
│       ├── adversarial_tests_fr.py               # To implement
│       └── ...
│
├── gazetteers/
│   ├── es/                             # ✅ Implemented
│   │   ├── nombres.json
│   │   ├── apellidos.json
│   │   └── municipios.json
│   │
│   ├── fr/                             # To implement
│   ├── it/
│   ├── pt/
│   ├── de/
│   └── en/
│
└── models/
    └── pretrained/
        ├── legal-xlm-roberta-base/     # ✅ Downloaded
        ├── juribert-base/              # To download
        ├── italian-legal-bert/
        └── ...
```

---

## 8. References

### 8.1 Papers and Documentation

| Resource | URL | Use |
|----------|-----|-----|
| Legal-BERT Paper | aclanthology.org/2020.findings-emnlp.261 | Architecture |
| JuriBERT Paper | aclanthology.org/2021.nllp-1.9 | French legal |
| SemEval 2013 Task 9 | aclweb.org/anthology/S13-2013 | Evaluation metrics |
| ISO 13616 (IBAN) | iso.org/standard/81090.html | IBAN Checksum |

### 8.2 Gazetteer Sources by Country

| Country | Names | Municipalities | IDs |
|---------|-------|----------------|-----|
| 🇪🇸 Spain | INE | INE | BOE |
| 🇫🇷 France | INSEE | INSEE | Légifrance |
| 🇮🇹 Italy | ISTAT | ISTAT | Normattiva |
| 🇵🇹 Portugal | INE-PT | INE-PT | DRE |
| 🇩🇪 Germany | Statistisches Bundesamt | - | Bundesrecht |
| 🇬🇧 UK | ONS | ONS | legislation.gov.uk |

---

## 9. Lessons Learned (ContextSafe ES)

### 9.1 What worked

1.  **Hybrid pipeline > Pure ML**: Transformers alone do not generalize to adversarial cases
2.  **Regex for variable formats**: DNI with spaces, IBAN with groups
3.  **Checksum validation**: Reduces false positives significantly
4.  **Boundary refinement**: Converts PAR→COR (16 cases corrected)
5.  **Adversarial test set**: Detects problems before production

### 9.2 What did NOT work

1.  **LoRA fine-tuning without pipeline**: 0.016 F1 on adversarial (overfitting)
2.  **GLiNER zero-shot**: 0.325 F1 (does not know Spanish formats)
3.  **Relying only on dev set metrics**: 0.989 dev vs 0.016 adversarial

### 9.3 Recommendations

1.  **Always create adversarial test set** before declaring "ready"
2.  **Implement checksum validators** for all IDs with mathematical verification
3.  **Invest in quality gazetteers** (names, municipalities)
4.  **Document each element** with standalone tests

---

## 10. Next Steps

1.  **Prioritize language** according to market demand
2.  **Download base model** of selected language
3.  **Adapt components** following this checklist
4.  **Create specific adversarial test set**
5.  **Iterate until F1 ≥ 0.70** on adversarial

---

**Date:** 2026-01-31
**Version:** 1.0.0
