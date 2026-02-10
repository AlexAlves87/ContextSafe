# Investigación: Modelos BERT Legales Multilingües

**Fecha:** 2026-01-29
**Autor:** AlexAlves87
**Objetivo:** Evaluar modelos BERT legales para expansión multilingüe de ContextSafe
**Idiomas objetivo:** Inglés, Francés, Italiano, Portugués, Alemán

---

## 1. Resumen Ejecutivo

Análisis de modelos BERT pre-entrenados en dominios legales para determinar viabilidad de expansión multilingüe del sistema NER-PII de ContextSafe.

### Modelos Evaluados

| Modelo | Idioma | Corpus | Tamaño | HuggingFace |
|--------|--------|--------|--------|-------------|
| Legal-BERT | Inglés | 12GB legal texts | 110M params | `nlpaueb/legal-bert-base-uncased` |
| JuriBERT | Francés | 6.3GB Légifrance | 110M params | `dascim/juribert-base` |
| Italian-Legal-BERT | Italiano | 3.7GB civil law | 110M params | `dlicari/Italian-Legal-BERT` |
| Legal-BERTimbau | Portugués | 30K docs legales | 110M params | `rufimelo/Legal-BERTimbau-base` |
| Legal-XLM-R | Multilingüe | 689GB (24 idiomas) | 355M params | `joelniklaus/legal-xlm-roberta-large` |

### Conclusión Principal

> **Legal-XLM-R es la opción más viable** para expansión multilingüe inmediata.
> Cubre 24 idiomas incluyendo español, con un solo modelo.
> Para máximo rendimiento por idioma, considerar fine-tuning de modelos monolingües.

---

## 2. Análisis por Modelo

### 2.1 Legal-BERT (Inglés)

**Fuente:** [nlpaueb/legal-bert-base-uncased](https://huggingface.co/nlpaueb/legal-bert-base-uncased)

| Aspecto | Detalle |
|---------|---------|
| **Arquitectura** | BERT-base (12 layers, 768 hidden, 110M params) |
| **Corpus** | 12GB textos legales ingleses |
| **Fuentes** | Legislación, casos judiciales, contratos |
| **Variantes** | General, CONTRACTS-, EURLEX-, ECHR- |
| **Licencia** | CC BY-SA 4.0 |

**Fortalezas:**
- Múltiples variantes especializadas (contratos, ECHR, EUR-Lex)
- Bien documentado y citado (~500 citas)
- Supera BERT vanilla en tareas legales

**Limitaciones:**
- Solo inglés
- No incluye fine-tuning para NER out-of-the-box

**Variantes disponibles:**
```
nlpaueb/legal-bert-base-uncased      # General
nlpaueb/legal-bert-small-uncased     # Más rápido
casehold/legalbert                   # Harvard Law corpus (37GB)
pile-of-law/legalbert-large-1.7M-2   # Pile of Law (256GB)
```

**Relevancia para ContextSafe:** Media. Útil si se expande a documentos legales en inglés (contratos internacionales, arbitraje).

---

### 2.2 JuriBERT (Francés)

**Fuente:** [dascim/juribert-base](https://huggingface.co/dascim/juribert-base)

| Aspecto | Detalle |
|---------|---------|
| **Arquitectura** | BERT (tiny, mini, small, base) |
| **Corpus** | 6.3GB textos legales franceses |
| **Fuentes** | Légifrance + Cour de Cassation |
| **Institución** | École Polytechnique + HEC Paris |
| **Paper** | [NLLP Workshop 2021](https://aclanthology.org/2021.nllp-1.9/) |

**Fortalezas:**
- Entrenado desde cero en francés legal (no fine-tuning)
- Incluye documentos de la Cour de Cassation (100K+ docs)
- Múltiples tamaños disponibles (tiny→base)

**Limitaciones:**
- Solo francés
- No hay modelo NER pre-entrenado

**Variantes disponibles:**
```
dascim/juribert-base    # 110M params
dascim/juribert-small   # Más ligero
dascim/juribert-mini    # Aún más ligero
dascim/juribert-tiny    # Mínimo (para edge)
```

**Relevancia para ContextSafe:** Alta para mercado francés. Francia tiene regulaciones estrictas de privacidad (CNIL + RGPD).

---

### 2.3 Italian-Legal-BERT (Italiano)

**Fuente:** [dlicari/Italian-Legal-BERT](https://huggingface.co/dlicari/Italian-Legal-BERT)

| Aspecto | Detalle |
|---------|---------|
| **Arquitectura** | BERT-base italiano + pretraining adicional |
| **Corpus** | 3.7GB Archivio Giurisprudenziale Nazionale |
| **Base** | bert-base-italian-xxl-cased |
| **Paper** | [KM4Law 2022](https://ceur-ws.org/Vol-3256/km4law3.pdf) |
| **Training** | 4 epochs, 8.4M steps, V100 16GB |

**Fortalezas:**
- Variante para documentos largos (LSG 16K tokens)
- Versión destilada disponible (3x más rápida)
- Evaluado en NER legal italiano

**Limitaciones:**
- Corpus principalmente derecho civil
- Solo italiano

**Variantes disponibles:**
```
dlicari/Italian-Legal-BERT          # Base
dlicari/Italian-Legal-BERT-SC       # Desde cero (6.6GB)
dlicari/lsg16k-Italian-Legal-BERT   # Long context (16K tokens)
```

**Relevancia para ContextSafe:** Media-alta. Italia tiene mercado notarial significativo y normativa privacidad estricta.

---

### 2.4 Legal-BERTimbau (Portugués)

**Fuente:** [rufimelo/Legal-BERTimbau-base](https://huggingface.co/rufimelo/Legal-BERTimbau-base)

| Aspecto | Detalle |
|---------|---------|
| **Arquitectura** | BERTimbau + fine-tuning legal |
| **Corpus** | 30K documentos legales portugueses |
| **Base** | neuralmind/bert-base-portuguese-cased |
| **Variante TSDAE** | 400K docs, técnica TSDAE |

**Fortalezas:**
- Base sólida (BERTimbau es SotA en portugués)
- Variante large disponible
- Versión para sentence similarity (TSDAE)

**Limitaciones:**
- Corpus relativamente pequeño (30K docs vs 6GB+ de otros)
- Principalmente derecho brasileño

**Variantes disponibles:**
```
rufimelo/Legal-BERTimbau-base       # Base
rufimelo/Legal-BERTimbau-large      # Large
rufimelo/Legal-BERTimbau-large-TSDAE-v5  # Sentence similarity
dominguesm/legal-bert-base-cased-ptbr    # Alternativa (STF)
dominguesm/legal-bert-ner-base-cased-ptbr # CON NER fine-tuned
```

**Modelo NER disponible:** `dominguesm/legal-bert-ner-base-cased-ptbr` ya tiene fine-tuning para NER legal en portugués.

**Relevancia para ContextSafe:** Alta para mercado lusófono (Brasil + Portugal). Brasil tiene LGPD similar a RGPD.

---

### 2.5 Legal-XLM-R / MultiLegalPile (Multilingüe)

**Fuente:** [joelniklaus/legal-xlm-roberta-large](https://huggingface.co/joelniklaus/legal-xlm-roberta-large)

| Aspecto | Detalle |
|---------|---------|
| **Arquitectura** | XLM-RoBERTa large (355M params) |
| **Corpus** | MultiLegalPile: 689GB en 24 idiomas |
| **Idiomas** | DE, EN, ES, FR, IT, PT, NL, PL, RO, + 15 más |
| **Benchmark** | LEXTREME (11 datasets, 24 idiomas) |
| **Paper** | [ACL 2024](https://aclanthology.org/2024.acl-long.805/) |

**Idiomas cubiertos:**
```
Germánicos:  DE (alemán), EN (inglés), NL (neerlandés)
Romances:    ES (español), FR (francés), IT (italiano), PT (portugués), RO (rumano)
Eslavos:     PL (polaco), BG (búlgaro), CS (checo), SK (eslovaco), SL (esloveno), HR (croata)
Otros:       EL (griego), HU (húngaro), FI (finés), LT (lituano), LV (letón), GA (irlandés), MT (maltés)
```

**Fortalezas:**
- **UN SOLO MODELO para 24 idiomas**
- Incluye español nativo
- Tokenizer de 128K BPEs optimizado para legal
- Variante Longformer para documentos largos
- Estado del arte en LEXTREME benchmark

**Limitaciones:**
- Modelo grande (355M params vs 110M de modelos base)
- Rendimiento ligeramente inferior a monolingües en algunos casos

**Variantes disponibles:**
```
joelniklaus/legal-xlm-roberta-base   # Base (110M)
joelniklaus/legal-xlm-roberta-large  # Large (355M) - RECOMENDADO
joelniklaus/legal-longformer-base    # Long context
```

**Relevancia para ContextSafe:** **MUY ALTA**. Permite expansión inmediata a múltiples idiomas europeos con un solo modelo.

---

## 3. Comparativa

### 3.1 Rendimiento Relativo

| Modelo | NER Legal | Clasificación | Long Docs | Multilingüe |
|--------|-----------|---------------|-----------|-------------|
| Legal-BERT (EN) | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ❌ |
| JuriBERT (FR) | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ❌ |
| Italian-Legal-BERT | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ |
| Legal-BERTimbau (PT) | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ❌ |
| **Legal-XLM-R** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### 3.2 Recursos Computacionales

| Modelo | Parámetros | VRAM (inference) | Latencia* |
|--------|------------|------------------|-----------|
| Legal-BERT base | 110M | ~2GB | ~50ms |
| JuriBERT base | 110M | ~2GB | ~50ms |
| Italian-Legal-BERT | 110M | ~2GB | ~50ms |
| Legal-BERTimbau base | 110M | ~2GB | ~50ms |
| **Legal-XLM-R base** | 110M | ~2GB | ~60ms |
| **Legal-XLM-R large** | 355M | ~4GB | ~120ms |

*Por documento de 512 tokens en GPU

### 3.3 Disponibilidad NER Pre-entrenado

| Modelo | NER Fine-tuned Disponible |
|--------|---------------------------|
| Legal-BERT | ❌ Requiere fine-tuning |
| JuriBERT | ❌ Requiere fine-tuning |
| Italian-Legal-BERT | ❌ Requiere fine-tuning |
| Legal-BERTimbau | ✅ `dominguesm/legal-bert-ner-base-cased-ptbr` |
| Legal-XLM-R | ❌ Requiere fine-tuning |

---

## 4. Estrategia Recomendada para ContextSafe

### 4.1 Opción A: Modelo Único Multilingüe (Recomendado)

```
Legal-XLM-R large → Fine-tune NER con datos multilingües → Deploy único
```

**Ventajas:**
- Un solo modelo para todos los idiomas
- Mantenimiento simplificado
- Transfer learning entre idiomas

**Desventajas:**
- Rendimiento ~5-10% inferior a monolingües
- Modelo más grande (355M vs 110M)

**Esfuerzo:** Medio (1 fine-tuning, 1 deploy)

### 4.2 Opción B: Modelos Monolingües por Mercado

```
ES: RoBERTalex (actual)
EN: Legal-BERT → Fine-tune NER
FR: JuriBERT → Fine-tune NER
IT: Italian-Legal-BERT → Fine-tune NER
PT: legal-bert-ner-base-cased-ptbr (ya existe)
DE: Legal-XLM-R (alemán) → Fine-tune NER
```

**Ventajas:**
- Máximo rendimiento por idioma
- Modelos más pequeños

**Desventajas:**
- 6 modelos a mantener
- 6 datasets NER necesarios
- Complejidad de deploy

**Esfuerzo:** Alto (6 fine-tunings, 6 deploys)

### 4.3 Opción C: Híbrido (Recomendado para Escala)

```
Fase 1: Legal-XLM-R para todos los idiomas nuevos
Fase 2: Fine-tune monolingüe para mercados con volumen alto
```

**Roadmap:**
1. Deploy Legal-XLM-R para EN, FR, IT, PT, DE
2. Monitorear métricas por idioma
3. Si idioma X tiene >1000 usuarios/mes → fine-tune monolingüe
4. Mantener XLM-R como fallback

---

## 5. Datasets NER Legales Multilingües

### 5.1 Disponibles

| Dataset | Idiomas | Entidades | Tamaño | Fuente |
|---------|---------|-----------|--------|--------|
| MAPA | 24 | PER, ORG, LOC, DATE | 50K+ | [LEXTREME](https://huggingface.co/datasets/joelito/lextreme) |
| LegalNER-BR | PT | 14 tipos | 10K+ | [HuggingFace](https://huggingface.co/dominguesm) |
| EUR-Lex NER | EN, 23 | ORG, LOC | 100K+ | EUR-Lex |

### 5.2 A Crear (si se necesita fine-tuning)

Para fine-tuning de modelos monolingües, se necesitaría crear datasets NER con las 13 categorías PII de ContextSafe:

| Categoría | Prioridad | Dificultad |
|-----------|-----------|------------|
| PERSON_NAME | Alta | Media |
| DNI/ID_NACIONAL | Alta | Varía por país |
| PHONE | Alta | Fácil (regex + NER) |
| EMAIL | Alta | Fácil (regex) |
| ADDRESS | Alta | Media |
| ORGANIZATION | Alta | Media |
| DATE | Media | Fácil |
| IBAN | Media | Fácil (regex) |
| LOCATION | Media | Media |

---

## 6. Conclusiones

### 6.1 Hallazgos Principales

1. **Legal-XLM-R es la mejor opción** para expansión multilingüe inmediata
   - 24 idiomas con un solo modelo
   - Incluye español (valida compatibilidad con ContextSafe actual)
   - Estado del arte en benchmark LEXTREME

2. **Modelos monolingües superan a multilingües** en ~5-10%
   - Considerar para mercados de alto volumen
   - Portugués ya tiene NER pre-entrenado

3. **El corpus de entrenamiento importa**
   - Italian-Legal-BERT tiene versión long-context (16K tokens)
   - Legal-BERTimbau tiene variante TSDAE para similarity

4. **Todos requieren fine-tuning** para las 13 categorías PII
   - Excepto `legal-bert-ner-base-cased-ptbr` (portugués)

### 6.2 Recomendación Final

| Escenario | Recomendación |
|-----------|---------------|
| MVP multilingüe rápido | Legal-XLM-R large |
| Máximo rendimiento EN | Legal-BERT + fine-tune |
| Máximo rendimiento FR | JuriBERT + fine-tune |
| Máximo rendimiento IT | Italian-Legal-BERT + fine-tune |
| Máximo rendimiento PT | `legal-bert-ner-base-cased-ptbr` (listo) |
| Máximo rendimiento DE | Legal-XLM-R (alemán) + fine-tune |

### 6.3 Próximos Pasos

| Prioridad | Tarea | Esfuerzo |
|-----------|-------|----------|
| 1 | Evaluar Legal-XLM-R en dataset español actual | 2-4h |
| 2 | Crear benchmark multilingüe (EN, FR, IT, PT, DE) | 8-16h |
| 3 | Fine-tune Legal-XLM-R para 13 categorías PII | 16-24h |
| 4 | Comparar vs modelos monolingües | 8-16h |

---

## 7. Referencias

### 7.1 Papers

1. Chalkidis et al. (2020). "LEGAL-BERT: The Muppets straight out of Law School". [arXiv:2010.02559](https://arxiv.org/abs/2010.02559)
2. Douka et al. (2021). "JuriBERT: A Masked-Language Model Adaptation for French Legal Text". [ACL Anthology](https://aclanthology.org/2021.nllp-1.9/)
3. Licari & Comandè (2022). "ITALIAN-LEGAL-BERT: A Pre-trained Transformer Language Model for Italian Law". [CEUR-WS](https://ceur-ws.org/Vol-3256/km4law3.pdf)
4. Niklaus et al. (2023). "MultiLegalPile: A 689GB Multilingual Legal Corpus". [ACL 2024](https://aclanthology.org/2024.acl-long.805/)
5. Niklaus et al. (2023). "LEXTREME: A Multi-Lingual and Multi-Task Benchmark for the Legal Domain". [arXiv:2301.13126](https://arxiv.org/abs/2301.13126)

### 7.2 Modelos HuggingFace

| Modelo | URL |
|--------|-----|
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

**Tiempo de investigación:** ~45 min
**Generado por:** AlexAlves87
**Fecha:** 2026-01-29
