# Ricerca: Modelli BERT Legali Multilingue

**Data:** 2026-01-29
**Autor:** AlexAlves87
**Obiettivo:** Valutare i modelli BERT legali per l'espansione multilingue di ContextSafe
**Lingue Target:** Inglese, Francese, Italiano, Portoghese, Tedesco

---

## 1. Riepilogo Esecutivo

Analisi dei modelli BERT pre-addestrati in domini legali per determinare la fattibilità dell'espansione multilingue del sistema NER-PII di ContextSafe.

### Modelli Valutati

| Modello | Lingua | Corpus | Dimensione | HuggingFace |
|---------|--------|--------|------------|-------------|
| Legal-BERT | Inglese | 12GB testi legali | 110M params | `nlpaueb/legal-bert-base-uncased` |
| JuriBERT | Francese | 6.3GB Légifrance | 110M params | `dascim/juribert-base` |
| Italian-Legal-BERT | Italiano | 3.7GB diritto civile | 110M params | `dlicari/Italian-Legal-BERT` |
| Legal-BERTimbau | Portoghese | 30K doc legali | 110M params | `rufimelo/Legal-BERTimbau-base` |
| Legal-XLM-R | Multilingue | 689GB (24 lingue) | 355M params | `joelniklaus/legal-xlm-roberta-large` |

### Conclusione Principale

> **Legal-XLM-R è l'opzione più praticabile** per un'espansione multilingue immediata.
> Copre 24 lingue incluso lo spagnolo, con un solo modello.
> Per le massime prestazioni per lingua, considerare il fine-tuning di modelli monolingua.

---

## 2. Analisi per Modello

### 2.1 Legal-BERT (Inglese)

**Fonte:** [nlpaueb/legal-bert-base-uncased](https://huggingface.co/nlpaueb/legal-bert-base-uncased)

| Aspetto | Dettaglio |
|---------|-----------|
| **Architettura** | BERT-base (12 layer, 768 hidden, 110M params) |
| **Corpus** | 12GB testi legali inglesi |
| **Fonti** | Legislazione, sentenze, contratti |
| **Varianti** | Generale, CONTRACTS-, EURLEX-, ECHR- |
| **Licenza** | CC BY-SA 4.0 |

**Punti di Forza:**
- Molteplici varianti specializzate (contratti, CEDU, EUR-Lex)
- Ben documentato e citato (~500 citazioni)
- Supera BERT vanilla nei task legali

**Limitazioni:**
- Solo inglese
- Nessun fine-tuning per NER pronto all'uso

**Varianti Disponibili:**
```
nlpaueb/legal-bert-base-uncased      # Generale
nlpaueb/legal-bert-small-uncased     # Più veloce
casehold/legalbert                   # Corpus Harvard Law (37GB)
pile-of-law/legalbert-large-1.7M-2   # Pile of Law (256GB)
```

**Rilevanza per ContextSafe:** Media. Utile se ci si espande a documenti legali in inglese (contratti internazionali, arbitrato).

---

### 2.2 JuriBERT (Francese)

**Fonte:** [dascim/juribert-base](https://huggingface.co/dascim/juribert-base)

| Aspetto | Dettaglio |
|---------|-----------|
| **Architettura** | BERT (tiny, mini, small, base) |
| **Corpus** | 6.3GB testi legali francesi |
| **Fonti** | Légifrance + Corte di Cassazione |
| **Istituzione** | École Polytechnique + HEC Paris |
| **Paper** | [NLLP Workshop 2021](https://aclanthology.org/2021.nllp-1.9/) |

**Punti di Forza:**
- Addestrato da zero su francese giuridico (no fine-tuning)
- Include documenti della Corte di Cassazione (100K+ doc)
- Molteplici dimensioni disponibili (tiny→base)

**Limitazioni:**
- Solo francese
- Nessun modello NER pre-addestrato

**Varianti Disponibili:**
```
dascim/juribert-base    # 110M params
dascim/juribert-small   # Più leggero
dascim/juribert-mini    # Ancora più leggero
dascim/juribert-tiny    # Minimo (per edge)
```

**Rilevanza per ContextSafe:** Alta per il mercato francese. La Francia ha normative rigide sulla privacy (CNIL + GDPR).

---

### 2.3 Italian-Legal-BERT (Italiano)

**Fonte:** [dlicari/Italian-Legal-BERT](https://huggingface.co/dlicari/Italian-Legal-BERT)

| Aspetto | Dettaglio |
|---------|-----------|
| **Architettura** | BERT-base italiano + pre-training aggiuntivo |
| **Corpus** | 3.7GB Archivio Giurisprudenziale Nazionale |
| **Base** | bert-base-italian-xxl-cased |
| **Paper** | [KM4Law 2022](https://ceur-ws.org/Vol-3256/km4law3.pdf) |
| **Training** | 4 epoche, 8.4M step, V100 16GB |

**Punti di Forza:**
- Variante per documenti lunghi (LSG 16K token)
- Versione distillata disponibile (3x più veloce)
- Valutato su NER legale italiano

**Limitazioni:**
- Corpus principalmente diritto civile
- Solo italiano

**Varianti Disponibili:**
```
dlicari/Italian-Legal-BERT          # Base
dlicari/Italian-Legal-BERT-SC       # Da zero (6.6GB)
dlicari/lsg16k-Italian-Legal-BERT   # Contesto lungo (16K token)
```

**Rilevanza per ContextSafe:** Medio-alta. L'Italia ha un mercato notarile significativo e normative privacy rigide.

---

### 2.4 Legal-BERTimbau (Portoghese)

**Fonte:** [rufimelo/Legal-BERTimbau-base](https://huggingface.co/rufimelo/Legal-BERTimbau-base)

| Aspetto | Dettaglio |
|---------|-----------|
| **Architettura** | BERTimbau + fine-tuning legale |
| **Corpus** | 30K documenti legali portoghesi |
| **Base** | neuralmind/bert-base-portuguese-cased |
| **Variante TSDAE** | 400K doc, tecnica TSDAE |

**Punti di Forza:**
- Base solida (BERTimbau è SotA in portoghese)
- Variante large disponibile
- Versione per similarità frasi (TSDAE)

**Limitazioni:**
- Corpus relativamente piccolo (30K doc vs 6GB+ per altri)
- Principalmente diritto brasiliano

**Varianti Disponibili:**
```
rufimelo/Legal-BERTimbau-base       # Base
rufimelo/Legal-BERTimbau-large      # Large
rufimelo/Legal-BERTimbau-large-TSDAE-v5  # Similarità frasi
dominguesm/legal-bert-base-cased-ptbr    # Alternativa (STF)
dominguesm/legal-bert-ner-base-cased-ptbr # CON fine-tuning NER
```

**Modello NER Disponibile:** `dominguesm/legal-bert-ner-base-cased-ptbr` ha già un fine-tuning per NER legale in portoghese.

**Rilevanza per ContextSafe:** Alta per mercato lusofono (Brasile + Portogallo). Il Brasile ha la LGPD simile al GDPR.

---

### 2.5 Legal-XLM-R / MultiLegalPile (Multilingue)

**Fonte:** [joelniklaus/legal-xlm-roberta-large](https://huggingface.co/joelniklaus/legal-xlm-roberta-large)

| Aspetto | Dettaglio |
|---------|-----------|
| **Architettura** | XLM-RoBERTa large (355M params) |
| **Corpus** | MultiLegalPile: 689GB in 24 lingue |
| **Lingue** | DE, EN, ES, FR, IT, PT, NL, PL, RO, + 15 altre |
| **Benchmark** | LEXTREME (11 dataset, 24 lingue) |
| **Paper** | [ACL 2024](https://aclanthology.org/2024.acl-long.805/) |

**Lingue Coperte:**
```
Germaniche:  DE (tedesco), EN (inglese), NL (olandese)
Romanze:     ES (spagnolo), FR (francese), IT (italiano), PT (portoghese), RO (rumeno)
Slave:       PL (polacco), BG (bulgaro), CS (ceco), SK (slovacco), SL (sloveno), HR (croato)
Altre:       EL (greco), HU (ungherese), FI (finlandese), LT (lituano), LV (lettone), GA (irlandese), MT (maltese)
```

**Punti di Forza:**
- **UN SOLO MODELLO per 24 lingue**
- Include spagnolo nativo
- Tokenizer 128K BPE ottimizzato per legale
- Variante Longformer per documenti lunghi
- Stato dell'arte sul benchmark LEXTREME

**Limitazioni:**
- Modello grande (355M params vs 110M per modelli base)
- Prestazioni leggermente inferiori al monolingua in alcuni casi

**Varianti Disponibili:**
```
joelniklaus/legal-xlm-roberta-base   # Base (110M)
joelniklaus/legal-xlm-roberta-large  # Large (355M) - RACCOMANDATO
joelniklaus/legal-longformer-base    # Contesto lungo
```

**Rilevanza per ContextSafe:** **MOLTO ALTA**. Permette espansione immediata a molteplici lingue europee con un solo modello.

---

## 3. Confronto

### 3.1 Prestazioni Relative

| Modello | NER Legale | Classificazione | Doc Lunghi | Multilingue |
|---------|------------|-----------------|------------|-------------|
| Legal-BERT (EN) | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ❌ |
| JuriBERT (FR) | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ❌ |
| Italian-Legal-BERT | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ |
| Legal-BERTimbau (PT) | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ❌ |
| **Legal-XLM-R** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### 3.2 Risorse Computazionali

| Modello | Parametri | VRAM (inferenza) | Latenza* |
|---------|-----------|------------------|----------|
| Legal-BERT base | 110M | ~2GB | ~50ms |
| JuriBERT base | 110M | ~2GB | ~50ms |
| Italian-Legal-BERT | 110M | ~2GB | ~50ms |
| Legal-BERTimbau base | 110M | ~2GB | ~50ms |
| **Legal-XLM-R base** | 110M | ~2GB | ~60ms |
| **Legal-XLM-R large** | 355M | ~4GB | ~120ms |

*Per documento di 512 token su GPU

### 3.3 Disponibilità NER Pre-addestrato

| Modello | NER Fine-tuned Disponibile |
|---------|----------------------------|
| Legal-BERT | ❌ Richiede fine-tuning |
| JuriBERT | ❌ Richiede fine-tuning |
| Italian-Legal-BERT | ❌ Richiede fine-tuning |
| Legal-BERTimbau | ✅ `dominguesm/legal-bert-ner-base-cased-ptbr` |
| Legal-XLM-R | ❌ Richiede fine-tuning |

---

## 4. Strategia Raccomandata per ContextSafe

### 4.1 Opzione A: Modello Unico Multilingue (Raccomandato)

```
Legal-XLM-R large → Fine-tune NER con dati multilingue → Deploy unico
```

**Vantaggi:**
- Un solo modello per tutte le lingue
- Manutenzione semplificata
- Transfer learning tra le lingue

**Svantaggi:**
- Prestazioni ~5-10% inferiori al monolingua
- Modello più grande (355M vs 110M)

**Sforzo:** Medio (1 fine-tuning, 1 deploy)

### 4.2 Opzione B: Modelli Monolingua per Mercato

```
ES: RoBERTalex (attuale)
EN: Legal-BERT → Fine-tune NER
FR: JuriBERT → Fine-tune NER
IT: Italian-Legal-BERT → Fine-tune NER
PT: legal-bert-ner-base-cased-ptbr (esiste già)
DE: Legal-XLM-R (Tedesco) → Fine-tune NER
```

**Vantaggi:**
- Prestazioni massime per lingua
- Modelli più piccoli

**Svantaggi:**
- 6 modelli da mantenere
- 6 dataset NER necessari
- Complessità di deploy

**Sforzo:** Alto (6 fine-tunings, 6 deploys)

### 4.3 Opzione C: Ibrido (Raccomandato per Scala)

```
Fase 1: Legal-XLM-R per tutte le nuove lingue
Fase 2: Fine-tune monolingua per mercati con volume alto
```

**Roadmap:**
1. Deploy Legal-XLM-R per EN, FR, IT, PT, DE
2. Monitorare metriche per lingua
3. Se lingua X ha >1000 utenti/mese → fine-tune monolingua
4. Mantenere XLM-R come fallback

---

## 5. Dataset NER Legali Multilingue

### 5.1 Disponibili

| Dataset | Lingue | Entità | Dimensione | Fonte |
|---------|--------|--------|------------|-------|
| MAPA | 24 | PER, ORG, LOC, DATE | 50K+ | [LEXTREME](https://huggingface.co/datasets/joelito/lextreme) |
| LegalNER-BR | PT | 14 tipi | 10K+ | [HuggingFace](https://huggingface.co/dominguesm) |
| EUR-Lex NER | EN, 23 | ORG, LOC | 100K+ | EUR-Lex |

### 5.2 Da Creare (se necessario fine-tuning)

Per il fine-tuning monolingua, sarebbero necessari dataset NER con le 13 categorie PII di ContextSafe:

| Categoria | Priorità | Difficoltà |
|-----------|----------|------------|
| PERSON_NAME | Alta | Media |
| DNI/ID_NACIONAL | Alta | Varia per paese |
| PHONE | Alta | Facile (regex + NER) |
| EMAIL | Alta | Facile (regex) |
| ADDRESS | Alta | Media |
| ORGANIZATION | Alta | Media |
| DATE | Media | Facile |
| IBAN | Media | Facile (regex) |
| LOCATION | Media | Media |

---

## 6. Conclusioni

### 6.1 Scoperte Chiave

1. **Legal-XLM-R è la migliore opzione** per l'espansione multilingue immediata
   - 24 lingue con un solo modello
   - Include spagnolo (valida compatibilità con ContextSafe attuale)
   - Stato dell'arte sul benchmark LEXTREME

2. **I modelli monolingua superano i multilingua** di ~5-10%
   - Da considerare per mercati ad alto volume
   - Il portoghese ha già un NER pre-addestrato

3. **Il corpus di addestramento conta**
   - Italian-Legal-BERT ha versione contesto lungo (16K token)
   - Legal-BERTimbau ha variante TSDAE per similarità

4. **Tutti richiedono fine-tuning** per le 13 categorie PII
   - Eccetto `legal-bert-ner-base-cased-ptbr` (Portoghese)

### 6.2 Raccomandazione Finale

| Scenario | Raccomandazione |
|----------|-----------------|
| MVP multilingue rapido | Legal-XLM-R large |
| Max performance EN | Legal-BERT + Fine-tune |
| Max performance FR | JuriBERT + Fine-tune |
| Max performance IT | Italian-Legal-BERT + Fine-tune |
| Max performance PT | `legal-bert-ner-base-cased-ptbr` (pronto) |
| Max performance DE | Legal-XLM-R (Tedesco) + Fine-tune |

### 6.3 Prossimi Passi

| Priorità | Attività | Sforzo |
|----------|----------|--------|
| 1 | Valutare Legal-XLM-R su dataset spagnolo attuale | 2-4h |
| 2 | Creare benchmark multilingue (EN, FR, IT, PT, DE) | 8-16h |
| 3 | Fine-tune Legal-XLM-R per 13 categorie PII | 16-24h |
| 4 | Confrontare vs modelli monolingua | 8-16h |

---

## 7. Riferimenti

### 7.1 Paper

1. Chalkidis et al. (2020). "LEGAL-BERT: The Muppets straight out of Law School". [arXiv:2010.02559](https://arxiv.org/abs/2010.02559)
2. Douka et al. (2021). "JuriBERT: A Masked-Language Model Adaptation for French Legal Text". [ACL Anthology](https://aclanthology.org/2021.nllp-1.9/)
3. Licari & Comandè (2022). "ITALIAN-LEGAL-BERT: A Pre-trained Transformer Language Model for Italian Law". [CEUR-WS](https://ceur-ws.org/Vol-3256/km4law3.pdf)
4. Niklaus et al. (2023). "MultiLegalPile: A 689GB Multilingual Legal Corpus". [ACL 2024](https://aclanthology.org/2024.acl-long.805/)
5. Niklaus et al. (2023). "LEXTREME: A Multi-Lingual and Multi-Task Benchmark for the Legal Domain". [arXiv:2301.13126](https://arxiv.org/abs/2301.13126)

### 7.2 Modelli HuggingFace

| Modello | URL |
|---------|-----|
| Legal-BERT | [nlpaueb/legal-bert-base-uncased](https://huggingface.co/nlpaueb/legal-bert-base-uncased) |
| JuriBERT | [dascim/juribert-base](https://huggingface.co/dascim/juribert-base) |
| Italian-Legal-BERT | [dlicari/Italian-Legal-BERT](https://huggingface.co/dlicari/Italian-Legal-BERT) |
| Legal-BERTimbau | [rufimelo/Legal-BERTimbau-base](https://huggingface.co/rufimelo/Legal-BERTimbau-base) |
| Legal-XLM-R | [joelniklaus/legal-xlm-roberta-large](https://huggingface.co/joelniklaus/legal-xlm-roberta-large) |
| Legal-BERT NER PT | [dominguesm/legal-bert-ner-base-cased-ptbr](https://huggingface.co/dominguesm/legal-bert-ner-base-cased-ptbr) |

### 7.3 Dataset

| Dataset | URL |
|---------|-----|
| LEXTREME | [joelito/lextreme](https://huggingface.co/datasets/joelito/lextreme) |
| MultiLegalPile | [joelito/Multi_Legal_Pile](https://huggingface.co/datasets/joelito/Multi_Legal_Pile) |

---

**Tempo di ricerca:** ~45 min
**Generato da:** AlexAlves87
**Data:** 2026-01-29
