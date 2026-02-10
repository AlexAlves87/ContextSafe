# Forschung: Mehrsprachige legale BERT-Modelle

**Datum:** 29.01.2026
**Autor:** AlexAlves87
**Ziel:** Evaluierung legaler BERT-Modelle für die mehrsprachige Erweiterung von ContextSafe
**Zielsprachen:** Englisch, Französisch, Italienisch, Portugiesisch, Deutsch

---

## 1. Zusammenfassung

Analyse von BERT-Modellen, die in juristischen Domänen vortrainiert wurden, um die Machbarkeit der mehrsprachigen Erweiterung des NER-PII-Systems von ContextSafe zu bestimmen.

### Evaluierte Modelle

| Modell | Sprache | Korpus | Größe | HuggingFace |
|--------|---------|--------|-------|-------------|
| Legal-BERT | Englisch | 12GB juristische Texte | 110M Params | `nlpaueb/legal-bert-base-uncased` |
| JuriBERT | Französisch | 6.3GB Légifrance | 110M Params | `dascim/juribert-base` |
| Italian-Legal-BERT | Italienisch | 3.7GB Zivilrecht | 110M Params | `dlicari/Italian-Legal-BERT` |
| Legal-BERTimbau | Portugiesisch | 30K juristische Doku. | 110M Params | `rufimelo/Legal-BERTimbau-base` |
| Legal-XLM-R | Mehrsprachig | 689GB (24 Sprachen) | 355M Params | `joelniklaus/legal-xlm-roberta-large` |

### Hauptschlussfolgerung

> **Legal-XLM-R ist die machbarste Option** für eine sofortige mehrsprachige Erweiterung.
> Es deckt 24 Sprachen ab, einschließlich Spanisch, mit einem einzigen Modell.
> Für maximale Leistung pro Sprache sollten monolinguale Modelle mit Fine-Tuning in Betracht gezogen werden.

---

## 2. Analyse nach Modell

### 2.1 Legal-BERT (Englisch)

**Quelle:** [nlpaueb/legal-bert-base-uncased](https://huggingface.co/nlpaueb/legal-bert-base-uncased)

| Aspekt | Detail |
|--------|--------|
| **Architektur** | BERT-base (12 Layer, 768 Hidden, 110M Params) |
| **Korpus** | 12GB englische juristische Texte |
| **Quellen** | Gesetzgebung, Gerichtsfälle, Verträge |
| **Varianten** | Allgemein, CONTRACTS-, EURLEX-, ECHR- |
| **Lizenz** | CC BY-SA 4.0 |

**Stärken:**
- Mehrere spezialisierte Varianten (Verträge, ECHR, EUR-Lex)
- Gut dokumentiert und zitiert (~500 Zitate)
- Übertrifft Vanilla BERT bei rechtlichen Aufgaben

**Einschränkungen:**
- Nur Englisch
- Kein Fine-Tuning für NER out-of-the-box

**Verfügbare Varianten:**
```
nlpaueb/legal-bert-base-uncased      # Allgemein
nlpaueb/legal-bert-small-uncased     # Schneller
casehold/legalbert                   # Harvard Law Korpus (37GB)
pile-of-law/legalbert-large-1.7M-2   # Pile of Law (256GB)
```

**Relevanz für ContextSafe:** Mittel. Nützlich bei Erweiterung auf englische Rechtsdokumente (internationale Verträge, Schiedsverfahren).

---

### 2.2 JuriBERT (Französisch)

**Quelle:** [dascim/juribert-base](https://huggingface.co/dascim/juribert-base)

| Aspekt | Detail |
|--------|--------|
| **Architektur** | BERT (tiny, mini, small, base) |
| **Korpus** | 6.3GB französische juristische Texte |
| **Quellen** | Légifrance + Cour de Cassation |
| **Institution** | École Polytechnique + HEC Paris |
| **Paper** | [NLLP Workshop 2021](https://aclanthology.org/2021.nllp-1.9/) |

**Stärken:**
- Von Grund auf in juristischem Französisch trainiert (kein Fine-Tuning)
- Enthält Dokumente der Cour de Cassation (100K+ Dokumente)
- Mehrere Größen verfügbar (tiny→base)

**Einschränkungen:**
- Nur Französisch
- Kein vortrainiertes NER-Modell

**Verfügbare Varianten:**
```
dascim/juribert-base    # 110M Params
dascim/juribert-small   # Leichter
dascim/juribert-mini    # Noch leichter
dascim/juribert-tiny    # Minimal (für Edge)
```

**Relevanz für ContextSafe:** Hoch für den französischen Markt. Frankreich hat strenge Datenschutzbestimmungen (CNIL + DSGVO).

---

### 2.3 Italian-Legal-BERT (Italienisch)

**Quelle:** [dlicari/Italian-Legal-BERT](https://huggingface.co/dlicari/Italian-Legal-BERT)

| Aspekt | Detail |
|--------|--------|
| **Architektur** | Italienisches BERT-base + zusätzliches Pretraining |
| **Korpus** | 3.7GB Archivio Giurisprudenziale Nazionale |
| **Basis** | bert-base-italian-xxl-cased |
| **Paper** | [KM4Law 2022](https://ceur-ws.org/Vol-3256/km4law3.pdf) |
| **Training** | 4 Epochen, 8.4M Schritte, V100 16GB |

**Stärken:**
- Variante für lange Dokumente (LSG 16K Tokens)
- Destillierte Version verfügbar (3x schneller)
- Evaluiert auf italienischem legalem NER

**Einschränkungen:**
- Korpus hauptsächlich Zivilrecht
- Nur Italienisch

**Verfügbare Varianten:**
```
dlicari/Italian-Legal-BERT          # Basis
dlicari/Italian-Legal-BERT-SC       # Von Grund auf (6.6GB)
dlicari/lsg16k-Italian-Legal-BERT   # Langkontext (16K Tokens)
```

**Relevanz für ContextSafe:** Mittel-hoch. Italien hat einen bedeutenden Notariatsmarkt und strenge Datenschutzbestimmungen.

---

### 2.4 Legal-BERTimbau (Portugiesisch)

**Quelle:** [rufimelo/Legal-BERTimbau-base](https://huggingface.co/rufimelo/Legal-BERTimbau-base)

| Aspekt | Detail |
|--------|--------|
| **Architektur** | BERTimbau + legales Fine-Tuning |
| **Korpus** | 30K portugiesische juristische Dokumente |
| **Basis** | neuralmind/bert-base-portuguese-cased |
| **TSDAE-Variante** | 400K Dokumente, TSDAE-Technik |

**Stärken:**
- Solide Basis (BERTimbau ist SotA auf Portugiesisch)
- Large-Variante verfügbar
- Version für Satzähnlichkeit (TSDAE)

**Einschränkungen:**
- Relativ kleiner Korpus (30K Dokumente vs 6GB+ bei anderen)
- Hauptsächlich brasilianisches Recht

**Verfügbare Varianten:**
```
rufimelo/Legal-BERTimbau-base       # Basis
rufimelo/Legal-BERTimbau-large      # Large
rufimelo/Legal-BERTimbau-large-TSDAE-v5  # Satzähnlichkeit
dominguesm/legal-bert-base-cased-ptbr    # Alternative (STF)
dominguesm/legal-bert-ner-base-cased-ptbr # MIT Fine-Tuning für NER
```

**Verfügbares NER-Modell:** `dominguesm/legal-bert-ner-base-cased-ptbr` hat bereits Fine-Tuning für juristisches NER auf Portugiesisch.

**Relevanz für ContextSafe:** Hoch für den lusophonen Markt (Brasilien + Portugal). Brasilien hat LGPD ähnlich der DSGVO.

---

### 2.5 Legal-XLM-R / MultiLegalPile (Mehrsprachig)

**Quelle:** [joelniklaus/legal-xlm-roberta-large](https://huggingface.co/joelniklaus/legal-xlm-roberta-large)

| Aspekt | Detail |
|--------|--------|
| **Architektur** | XLM-RoBERTa large (355M Params) |
| **Korpus** | MultiLegalPile: 689GB in 24 Sprachen |
| **Sprachen** | DE, EN, ES, FR, IT, PT, NL, PL, RO, + 15 weitere |
| **Benchmark** | LEXTREME (11 Datensätze, 24 Sprachen) |
| **Paper** | [ACL 2024](https://aclanthology.org/2024.acl-long.805/) |

**Abgedeckte Sprachen:**
```
Germanisch:  DE (Deutsch), EN (Englisch), NL (Niederländisch)
Romanisch:   ES (Spanisch), FR (Französisch), IT (Italienisch), PT (Portugiesisch), RO (Rumänisch)
Slawisch:    PL (Polnisch), BG (Bulgarisch), CS (Tschechisch), SK (Slowakisch), SL (Slowenisch), HR (Kroatisch)
Andere:      EL (Griechisch), HU (Ungarisch), FI (Finnisch), LT (Litauisch), LV (Lettisch), GA (Irisch), MT (Maltesisch)
```

**Stärken:**
- **EIN EINZIGES MODELL für 24 Sprachen**
- Enthält natives Spanisch
- 128K BPE Tokenizer für Recht optimiert
- Longformer-Variante für lange Dokumente
- State of the Art im LEXTREME-Benchmark

**Einschränkungen:**
- Großes Modell (355M Params vs 110M für Basismodelle)
- Leistung in einigen Fällen etwas geringer als monolingual

**Verfügbare Varianten:**
```
joelniklaus/legal-xlm-roberta-base   # Basis (110M)
joelniklaus/legal-xlm-roberta-large  # Large (355M) - EMPFOHLEN
joelniklaus/legal-longformer-base    # Langkontext
```

**Relevanz für ContextSafe:** **SEHR HOCH**. Ermöglicht sofortige Erweiterung auf mehrere europäische Sprachen mit einem einzigen Modell.

---

## 3. Vergleich

### 3.1 Relative Leistung

| Modell | Legales NER | Klassifikation | Lange Doku. | Mehrsprachig |
|--------|-------------|----------------|-------------|--------------|
| Legal-BERT (EN) | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ❌ |
| JuriBERT (FR) | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ❌ |
| Italian-Legal-BERT | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ |
| Legal-BERTimbau (PT) | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ❌ |
| **Legal-XLM-R** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### 3.2 Rechenressourcen

| Modell | Parameter | VRAM (Inferenz) | Latenz* |
|--------|-----------|-----------------|---------|
| Legal-BERT base | 110M | ~2GB | ~50ms |
| JuriBERT base | 110M | ~2GB | ~50ms |
| Italian-Legal-BERT | 110M | ~2GB | ~50ms |
| Legal-BERTimbau base | 110M | ~2GB | ~50ms |
| **Legal-XLM-R base** | 110M | ~2GB | ~60ms |
| **Legal-XLM-R large** | 355M | ~4GB | ~120ms |

*Pro 512-Token-Dokument auf GPU

### 3.3 Verfügbarkeit von vortrainiertem NER

| Modell | Fine-tuned NER verfügbar |
|--------|--------------------------|
| Legal-BERT | ❌ Erfordert Fine-Tuning |
| JuriBERT | ❌ Erfordert Fine-Tuning |
| Italian-Legal-BERT | ❌ Erfordert Fine-Tuning |
| Legal-BERTimbau | ✅ `dominguesm/legal-bert-ner-base-cased-ptbr` |
| Legal-XLM-R | ❌ Erfordert Fine-Tuning |

---

## 4. Empfohlene Strategie für ContextSafe

### 4.1 Option A: Einzelnes mehrsprachiges Modell (Empfohlen)

```
Legal-XLM-R large → Fine-tune NER mit mehrsprachigen Daten → Einzelnes Deployment
```

**Vorteile:**
- Ein einziges Modell für alle Sprachen
- Vereinfachte Wartung
- Transfer Learning zwischen Sprachen

**Nachteile:**
- Leistung ~5-10% geringer als monolingual
- Größeres Modell (355M vs 110M)

**Aufwand:** Mittel (1 Fine-Tuning, 1 Deployment)

### 4.2 Option B: Monolinguale Modelle pro Markt

```
ES: RoBERTalex (aktuell)
EN: Legal-BERT → Fine-tune NER
FR: JuriBERT → Fine-tune NER
IT: Italian-Legal-BERT → Fine-tune NER
PT: legal-bert-ner-base-cased-ptbr (existiert bereits)
DE: Legal-XLM-R (Deutsch) → Fine-tune NER
```

**Vorteile:**
- Maximale Leistung pro Sprache
- Kleinere Modelle

**Nachteile:**
- 6 Modelle zu warten
- 6 NER-Datensätze erforderlich
- Komplexes Deployment

**Aufwand:** Hoch (6 Fine-Tunings, 6 Deployments)

### 4.3 Option C: Hybrid (Empfohlen für Skalierung)

```
Phase 1: Legal-XLM-R für alle neuen Sprachen
Phase 2: Fine-tune monolingual für Märkte mit hohem Volumen
```

**Roadmap:**
1. Deployment Legal-XLM-R für EN, FR, IT, PT, DE
2. Überwachung der Metriken pro Sprache
3. Wenn Sprache X >1000 Nutzer/Monat hat → Fine-tune monolingual
4. XLM-R als Fallback behalten

---

## 5. Mehrsprachige legale NER-Datensätze

### 5.1 Verfügbar

| Datensatz | Sprachen | Entitäten | Größe | Quelle |
|-----------|----------|-----------|-------|--------|
| MAPA | 24 | PER, ORG, LOC, DATE | 50K+ | [LEXTREME](https://huggingface.co/datasets/joelito/lextreme) |
| LegalNER-BR | PT | 14 Typen | 10K+ | [HuggingFace](https://huggingface.co/dominguesm) |
| EUR-Lex NER | EN, 23 | ORG, LOC | 100K+ | EUR-Lex |

### 5.2 Zu erstellen (falls Fine-Tuning erforderlich)

Für monolinguales Fine-Tuning müssten NER-Datensätze mit den 13 ContextSafe PII-Kategorien erstellt werden:

| Kategorie | Priorität | Schwierigkeit |
|-----------|-----------|---------------|
| PERSON_NAME | Hoch | Mittel |
| DNI/ID_NACIONAL | Hoch | Variiert nach Land |
| PHONE | Hoch | Einfach (Regex + NER) |
| EMAIL | Hoch | Einfach (Regex) |
| ADDRESS | Hoch | Mittel |
| ORGANIZATION | Hoch | Mittel |
| DATE | Mittel | Einfach |
| IBAN | Mittel | Einfach (Regex) |
| LOCATION | Mittel | Mittel |

---

## 6. Schlussfolgerungen

### 6.1 Wichtigste Erkenntnisse

1. **Legal-XLM-R ist die beste Option** für sofortige mehrsprachige Erweiterung
   - 24 Sprachen mit einem einzigen Modell
   - Beinhaltet Spanisch (validiert Kompatibilität mit aktuellem ContextSafe)
   - State of the Art im LEXTREME-Benchmark

2. **Monolinguale Modelle übertreffen mehrsprachige** um ~5-10%
   - Für Märkte mit hohem Volumen in Betracht ziehen
   - Portugiesisch hat bereits vortrainiertes NER

3. **Trainingskorpus ist wichtig**
   - Italian-Legal-BERT hat Langkontext-Version (16K Tokens)
   - Legal-BERTimbau hat TSDAE-Variante für Ähnlichkeit

4. **Alle erfordern Fine-Tuning** für die 13 PII-Kategorien
   - Außer `legal-bert-ner-base-cased-ptbr` (Portugiesisch)

### 6.2 Abschließende Empfehlung

| Szenario | Empfehlung |
|----------|------------|
| Schnelles mehrsprachiges MVP | Legal-XLM-R large |
| Max Leistung EN | Legal-BERT + Fine-tune |
| Max Leistung FR | JuriBERT + Fine-tune |
| Max Leistung IT | Italian-Legal-BERT + Fine-tune |
| Max Leistung PT | `legal-bert-ner-base-cased-ptbr` (bereit) |
| Max Leistung DE | Legal-XLM-R (Deutsch) + Fine-tune |

### 6.3 Nächste Schritte

| Priorität | Aufgabe | Aufwand |
|-----------|---------|---------|
| 1 | Evaluierung von Legal-XLM-R auf aktuellem spanischen Datensatz | 2-4h |
| 2 | Erstellung eines mehrsprachigen Benchmarks (EN, FR, IT, PT, DE) | 8-16h |
| 3 | Fine-tune Legal-XLM-R für 13 PII-Kategorien | 16-24h |
| 4 | Vergleich vs. monolinguale Modelle | 8-16h |

---

## 7. Referenzen

### 7.1 Papers

1. Chalkidis et al. (2020). "LEGAL-BERT: The Muppets straight out of Law School". [arXiv:2010.02559](https://arxiv.org/abs/2010.02559)
2. Douka et al. (2021). "JuriBERT: A Masked-Language Model Adaptation for French Legal Text". [ACL Anthology](https://aclanthology.org/2021.nllp-1.9/)
3. Licari & Comandè (2022). "ITALIAN-LEGAL-BERT: A Pre-trained Transformer Language Model for Italian Law". [CEUR-WS](https://ceur-ws.org/Vol-3256/km4law3.pdf)
4. Niklaus et al. (2023). "MultiLegalPile: A 689GB Multilingual Legal Corpus". [ACL 2024](https://aclanthology.org/2024.acl-long.805/)
5. Niklaus et al. (2023). "LEXTREME: A Multi-Lingual and Multi-Task Benchmark for the Legal Domain". [arXiv:2301.13126](https://arxiv.org/abs/2301.13126)

### 7.2 HuggingFace Modelle

| Modell | URL |
|--------|-----|
| Legal-BERT | [nlpaueb/legal-bert-base-uncased](https://huggingface.co/nlpaueb/legal-bert-base-uncased) |
| JuriBERT | [dascim/juribert-base](https://huggingface.co/dascim/juribert-base) |
| Italian-Legal-BERT | [dlicari/Italian-Legal-BERT](https://huggingface.co/dlicari/Italian-Legal-BERT) |
| Legal-BERTimbau | [rufimelo/Legal-BERTimbau-base](https://huggingface.co/rufimelo/Legal-BERTimbau-base) |
| Legal-XLM-R | [joelniklaus/legal-xlm-roberta-large](https://huggingface.co/joelniklaus/legal-xlm-roberta-large) |
| Legal-BERT NER PT | [dominguesm/legal-bert-ner-base-cased-ptbr](https://huggingface.co/dominguesm/legal-bert-ner-base-cased-ptbr) |

### 7.3 Datensätze

| Datensatz | URL |
|-----------|-----|
| LEXTREME | [joelito/lextreme](https://huggingface.co/datasets/joelito/lextreme) |
| MultiLegalPile | [joelito/Multi_Legal_Pile](https://huggingface.co/datasets/joelito/Multi_Legal_Pile) |

---

**Recherchezeit:** ~45 Min.
**Generiert von:** AlexAlves87
**Datum:** 29.01.2026
