# Research: Multilingual Legal BERT Models

**Date:** 2026-01-29
**Author:** AlexAlves87
**Objective:** Evaluate legal BERT models for multilingual expansion of ContextSafe
**Target Languages:** English, French, Italian, Portuguese, German

---

## 1. Executive Summary

Analysis of BERT models pre-trained in legal domains to determine feasibility of multilingual expansion of ContextSafe's NER-PII system.

### Evaluated Models

| Model | Language | Corpus | Size | HuggingFace |
|-------|----------|--------|------|-------------|
| Legal-BERT | English | 12GB legal texts | 110M params | `nlpaueb/legal-bert-base-uncased` |
| JuriBERT | French | 6.3GB Légifrance | 110M params | `dascim/juribert-base` |
| Italian-Legal-BERT | Italian | 3.7GB civil law | 110M params | `dlicari/Italian-Legal-BERT` |
| Legal-BERTimbau | Portuguese | 30K docs legales | 110M params | `rufimelo/Legal-BERTimbau-base` |
| Legal-XLM-R | Multilingual | 689GB (24 languages) | 355M params | `joelniklaus/legal-xlm-roberta-large` |

### Main Conclusion

> **Legal-XLM-R is the most viable option** for immediate multilingual expansion.
> It covers 24 languages including Spanish, with a single model.
> For maximum performance per language, consider fine-tuning monolingual models.

---

## 2. Analysis by Model

### 2.1 Legal-BERT (English)

**Source:** [nlpaueb/legal-bert-base-uncased](https://huggingface.co/nlpaueb/legal-bert-base-uncased)

| Aspect | Detail |
|--------|--------|
| **Architecture** | BERT-base (12 layers, 768 hidden, 110M params) |
| **Corpus** | 12GB English legal texts |
| **Sources** | Legislation, court cases, contracts |
| **Variants** | General, CONTRACTS-, EURLEX-, ECHR- |
| **License** | CC BY-SA 4.0 |

**Strengths:**
- Multiple specialized variants (contracts, ECHR, EUR-Lex)
- Well documented and cited (~500 citations)
- Outperforms vanilla BERT in legal tasks

**Limitations:**
- English only
- No out-of-the-box fine-tuning for NER

**Available Variants:**
```
nlpaueb/legal-bert-base-uncased      # General
nlpaueb/legal-bert-small-uncased     # Faster
casehold/legalbert                   # Harvard Law corpus (37GB)
pile-of-law/legalbert-large-1.7M-2   # Pile of Law (256GB)
```

**Relevance for ContextSafe:** Medium. Useful if expanding to English legal documents (international contracts, arbitration).

---

### 2.2 JuriBERT (French)

**Source:** [dascim/juribert-base](https://huggingface.co/dascim/juribert-base)

| Aspect | Detail |
|--------|--------|
| **Architecture** | BERT (tiny, mini, small, base) |
| **Corpus** | 6.3GB French legal texts |
| **Sources** | Légifrance + Cour de Cassation |
| **Institution** | École Polytechnique + HEC Paris |
| **Paper** | [NLLP Workshop 2021](https://aclanthology.org/2021.nllp-1.9/) |

**Strengths:**
- Trained from scratch on legal French (no fine-tuning)
- Includes Cour de Cassation documents (100K+ docs)
- Multiple sizes available (tiny→base)

**Limitations:**
- French only
- No pre-trained NER model

**Available Variants:**
```
dascim/juribert-base    # 110M params
dascim/juribert-small   # Lighter
dascim/juribert-mini    # Even lighter
dascim/juribert-tiny    # Minimal (for edge)
```

**Relevance for ContextSafe:** High for French market. France has strict privacy regulations (CNIL + GDPR).

---

### 2.3 Italian-Legal-BERT (Italian)

**Source:** [dlicari/Italian-Legal-BERT](https://huggingface.co/dlicari/Italian-Legal-BERT)

| Aspect | Detail |
|--------|--------|
| **Architecture** | Italian BERT-base + additional pretraining |
| **Corpus** | 3.7GB Archivio Giurisprudenziale Nazionale |
| **Base** | bert-base-italian-xxl-cased |
| **Paper** | [KM4Law 2022](https://ceur-ws.org/Vol-3256/km4law3.pdf) |
| **Training** | 4 epochs, 8.4M steps, V100 16GB |

**Strengths:**
- Variant for long documents (LSG 16K tokens)
- Distilled version available (3x faster)
- Evaluated on Italian legal NER

**Limitations:**
- Corpus mainly civil law
- Italian only

**Available Variants:**
```
dlicari/Italian-Legal-BERT          # Base
dlicari/Italian-Legal-BERT-SC       # From scratch (6.6GB)
dlicari/lsg16k-Italian-Legal-BERT   # Long context (16K tokens)
```

**Relevance for ContextSafe:** Medium-high. Italy has significant notary market and strict privacy regulations.

---

### 2.4 Legal-BERTimbau (Portuguese)

**Source:** [rufimelo/Legal-BERTimbau-base](https://huggingface.co/rufimelo/Legal-BERTimbau-base)

| Aspect | Detail |
|--------|--------|
| **Architecture** | BERTimbau + legal fine-tuning |
| **Corpus** | 30K Portuguese legal documents |
| **Base** | neuralmind/bert-base-portuguese-cased |
| **TSDAE Variant** | 400K docs, TSDAE technique |

**Strengths:**
- Solid base (BERTimbau is SotA in Portuguese)
- Large variant available
- Version for sentence similarity (TSDAE)

**Limitations:**
- Relatively small corpus (30K docs vs 6GB+ for others)
- Mainly Brazilian law

**Available Variants:**
```
rufimelo/Legal-BERTimbau-base       # Base
rufimelo/Legal-BERTimbau-large      # Large
rufimelo/Legal-BERTimbau-large-TSDAE-v5  # Sentence similarity
dominguesm/legal-bert-base-cased-ptbr    # Alternative (STF)
dominguesm/legal-bert-ner-base-cased-ptbr # WITH fine-tuned NER
```

**Available NER Model:** `dominguesm/legal-bert-ner-base-cased-ptbr` already has fine-tuning for Portuguese legal NER.

**Relevance for ContextSafe:** High for Lusophone market (Brazil + Portugal). Brazil has LGPD similar to GDPR.

---

### 2.5 Legal-XLM-R / MultiLegalPile (Multilingual)

**Source:** [joelniklaus/legal-xlm-roberta-large](https://huggingface.co/joelniklaus/legal-xlm-roberta-large)

| Aspect | Detail |
|--------|--------|
| **Architecture** | XLM-RoBERTa large (355M params) |
| **Corpus** | MultiLegalPile: 689GB in 24 languages |
| **Languages** | DE, EN, ES, FR, IT, PT, NL, PL, RO, + 15 more |
| **Benchmark** | LEXTREME (11 datasets, 24 languages) |
| **Paper** | [ACL 2024](https://aclanthology.org/2024.acl-long.805/) |

**Languages Covered:**
```
Germanic:    DE (German), EN (English), NL (Dutch)
Romance:     ES (Spanish), FR (French), IT (Italian), PT (Portuguese), RO (Romanian)
Slavic:      PL (Polish), BG (Bulgarian), CS (Czech), SK (Slovak), SL (Slovenian), HR (Croatian)
Others:      EL (Greek), HU (Hungarian), FI (Finnish), LT (Lithuanian), LV (Latvian), GA (Irish), MT (Maltese)
```

**Strengths:**
- **ONE SINGLE MODEL for 24 languages**
- Includes native Spanish
- 128K BPE tokenizer optimized for legal
- Longformer variant for long documents
- State of the art on LEXTREME benchmark

**Limitations:**
- Large model (355M params vs 110M for base models)
- Performance slightly lower than monolingual in some cases

**Available Variants:**
```
joelniklaus/legal-xlm-roberta-base   # Base (110M)
joelniklaus/legal-xlm-roberta-large  # Large (355M) - RECOMMENDED
joelniklaus/legal-longformer-base    # Long context
```

**Relevance for ContextSafe:** **VERY HIGH**. Allows immediate expansion to multiple European languages with a single model.

---

## 3. Comparison

### 3.1 Relative Performance

| Model | Legal NER | Classification | Long Docs | Multilingual |
|-------|-----------|----------------|-----------|--------------|
| Legal-BERT (EN) | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ❌ |
| JuriBERT (FR) | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ❌ |
| Italian-Legal-BERT | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ |
| Legal-BERTimbau (PT) | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ❌ |
| **Legal-XLM-R** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### 3.2 Computational Resources

| Model | Parameters | VRAM (inference) | Latency* |
|-------|------------|------------------|----------|
| Legal-BERT base | 110M | ~2GB | ~50ms |
| JuriBERT base | 110M | ~2GB | ~50ms |
| Italian-Legal-BERT | 110M | ~2GB | ~50ms |
| Legal-BERTimbau base | 110M | ~2GB | ~50ms |
| **Legal-XLM-R base** | 110M | ~2GB | ~60ms |
| **Legal-XLM-R large** | 355M | ~4GB | ~120ms |

*Per 512 token document on GPU

### 3.3 Pre-trained NER Availability

| Model | Fine-tuned NER Available |
|-------|--------------------------|
| Legal-BERT | ❌ Requires fine-tuning |
| JuriBERT | ❌ Requires fine-tuning |
| Italian-Legal-BERT | ❌ Requires fine-tuning |
| Legal-BERTimbau | ✅ `dominguesm/legal-bert-ner-base-cased-ptbr` |
| Legal-XLM-R | ❌ Requires fine-tuning |

---

## 4. Recommended Strategy for ContextSafe

### 4.1 Option A: Single Multilingual Model (Recommended)

```
Legal-XLM-R large → Fine-tune NER with multilingual data → Single deploy
```

**Advantages:**
- Single model for all languages
- Simplified maintenance
- Transfer learning between languages

**Disadvantages:**
- Performance ~5-10% lower than monolingual
- Larger model (355M vs 110M)

**Effort:** Medium (1 fine-tuning, 1 deploy)

### 4.2 Option B: Monolingual Models by Market

```
ES: RoBERTalex (current)
EN: Legal-BERT → Fine-tune NER
FR: JuriBERT → Fine-tune NER
IT: Italian-Legal-BERT → Fine-tune NER
PT: legal-bert-ner-base-cased-ptbr (already exists)
DE: Legal-XLM-R (German) → Fine-tune NER
```

**Advantages:**
- Maximum performance per language
- Smaller models

**Disadvantages:**
- 6 models to maintain
- 6 NER datasets needed
- Deploy complexity

**Effort:** High (6 fine-tunings, 6 deploys)

### 4.3 Option C: Hybrid (Recommended for Scale)

```
Phase 1: Legal-XLM-R for all new languages
Phase 2: Fine-tune monolingual for high volume markets
```

**Roadmap:**
1. Deploy Legal-XLM-R for EN, FR, IT, PT, DE
2. Monitor metrics by language
3. If language X has >1000 users/month → fine-tune monolingual
4. Keep XLM-R as fallback

---

## 5. Multilingual Legal NER Datasets

### 5.1 Available

| Dataset | Languages | Entities | Size | Source |
|---------|-----------|----------|------|--------|
| MAPA | 24 | PER, ORG, LOC, DATE | 50K+ | [LEXTREME](https://huggingface.co/datasets/joelito/lextreme) |
| LegalNER-BR | PT | 14 types | 10K+ | [HuggingFace](https://huggingface.co/dominguesm) |
| EUR-Lex NER | EN, 23 | ORG, LOC | 100K+ | EUR-Lex |

### 5.2 To Create (if fine-tuning needed)

For monolingual fine-tuning, NER datasets with the 13 ContextSafe PII categories would need to be created:

| Category | Priority | Difficulty |
|----------|----------|------------|
| PERSON_NAME | High | Medium |
| DNI/ID_NACIONAL | High | Varies by country |
| PHONE | High | Easy (regex + NER) |
| EMAIL | High | Easy (regex) |
| ADDRESS | High | Medium |
| ORGANIZATION | High | Medium |
| DATE | Medium | Easy |
| IBAN | Medium | Easy (regex) |
| LOCATION | Medium | Medium |

---

## 6. Conclusions

### 6.1 Key Findings

1. **Legal-XLM-R is the best option** for immediate multilingual expansion
   - 24 languages with a single model
   - Includes Spanish (validates compatibility with current ContextSafe)
   - State of the art on LEXTREME benchmark

2. **Monolingual models outperform multilingual** by ~5-10%
   - Consider for high volume markets
   - Portuguese already has pre-trained NER

3. **Training corpus matters**
   - Italian-Legal-BERT has long-context version (16K tokens)
   - Legal-BERTimbau has TSDAE variant for similarity

4. **All require fine-tuning** for the 13 PII categories
   - Except `legal-bert-ner-base-cased-ptbr` (Portuguese)

### 6.2 Final Recommendation

| Scenario | Recommendation |
|----------|----------------|
| Quick multilingual MVP | Legal-XLM-R large |
| Max performance EN | Legal-BERT + fine-tune |
| Max performance FR | JuriBERT + fine-tune |
| Max performance IT | Italian-Legal-BERT + fine-tune |
| Max performance PT | `legal-bert-ner-base-cased-ptbr` (ready) |
| Max performance DE | Legal-XLM-R (German) + fine-tune |

### 6.3 Next Steps

| Priority | Task | Effort |
|----------|------|--------|
| 1 | Evaluate Legal-XLM-R on current Spanish dataset | 2-4h |
| 2 | Create multilingual benchmark (EN, FR, IT, PT, DE) | 8-16h |
| 3 | Fine-tune Legal-XLM-R for 13 PII categories | 16-24h |
| 4 | Compare vs monolingual models | 8-16h |

---

## 7. References

### 7.1 Papers

1. Chalkidis et al. (2020). "LEGAL-BERT: The Muppets straight out of Law School". [arXiv:2010.02559](https://arxiv.org/abs/2010.02559)
2. Douka et al. (2021). "JuriBERT: A Masked-Language Model Adaptation for French Legal Text". [ACL Anthology](https://aclanthology.org/2021.nllp-1.9/)
3. Licari & Comandè (2022). "ITALIAN-LEGAL-BERT: A Pre-trained Transformer Language Model for Italian Law". [CEUR-WS](https://ceur-ws.org/Vol-3256/km4law3.pdf)
4. Niklaus et al. (2023). "MultiLegalPile: A 689GB Multilingual Legal Corpus". [ACL 2024](https://aclanthology.org/2024.acl-long.805/)
5. Niklaus et al. (2023). "LEXTREME: A Multi-Lingual and Multi-Task Benchmark for the Legal Domain". [arXiv:2301.13126](https://arxiv.org/abs/2301.13126)

### 7.2 HuggingFace Models

| Model | URL |
|-------|-----|
| Legal-BERT | [nlpaueb/legal-bert-base-uncased](https://huggingface.co/nlpaueb/legal-bert-base-uncased) |
| JuriBERT | [dascim/juribert-base](https://huggingface.co/dascim/juribert-base) |
| Italian-Legal-BERT | [dlicari/Italian-Legal-BERT](https://huggingface.co/dlicari/Italian-Legal-BERT) |
| Legal-BERTimbau | [rufimelo/Legal-BERTimbau-base](https://huggingface.co/rufimelo/Legal-BERTimbau-base) |
| Legal-XLM-R | [joelniklaus/legal-xlm-roberta-large](https://huggingface.co/joelniklaus/legal-xlm-roberta-large) |
| Legal-BERT NER PT | [dominguesm/legal-bert-ner-base-cased-ptbr](https://huggingface.co/dominguesm/legal-bert-ner-base-cased-ptbr) |

### 7.3 Datasets

| Dataset | URL |
|---------|-----|
| LEXTREME | [joelito/lextreme](https://huggingface.co/datasets/joelito/lextreme) |
| MultiLegalPile | [joelito/Multi_Legal_Pile](https://huggingface.co/datasets/joelito/Multi_Legal_Pile) |

---

**Date:** 2026-01-29
