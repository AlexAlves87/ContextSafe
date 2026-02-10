# Investigação: Modelos BERT Legais Multilingues

**Data:** 29-01-2026
**Autor:** AlexAlves87
**Objetivo:** Avaliar modelos BERT legais para expansão multilingue do ContextSafe
**Idiomas Alvo:** Inglês, Francês, Italiano, Português, Alemão

---

## 1. Resumo Executivo

Análise de modelos BERT pré-treinados em domínios legais para determinar viabilidade da expansão multilingue do sistema NER-PII do ContextSafe.

### Modelos Avaliados

| Modelo | Idioma | Corpus | Tamanho | HuggingFace |
|--------|--------|--------|---------|-------------|
| Legal-BERT | Inglês | 12GB textos legais | 110M params | `nlpaueb/legal-bert-base-uncased` |
| JuriBERT | Francês | 6.3GB Légifrance | 110M params | `dascim/juribert-base` |
| Italian-Legal-BERT | Italiano | 3.7GB direito civil | 110M params | `dlicari/Italian-Legal-BERT` |
| Legal-BERTimbau | Português | 30K docs legais | 110M params | `rufimelo/Legal-BERTimbau-base` |
| Legal-XLM-R | Multilingue | 689GB (24 idiomas) | 355M params | `joelniklaus/legal-xlm-roberta-large` |

### Conclusão Principal

> **Legal-XLM-R é a opção mais viável** para expansão multilingue imediata.
> Cobre 24 idiomas incluindo espanhol, com um único modelo.
> Para máximo desempenho por idioma, considerar fine-tuning de modelos monolingues.

---

## 2. Análise por Modelo

### 2.1 Legal-BERT (Inglês)

**Fonte:** [nlpaueb/legal-bert-base-uncased](https://huggingface.co/nlpaueb/legal-bert-base-uncased)

| Aspeto | Detalhe |
|--------|---------|
| **Arquitetura** | BERT-base (12 layers, 768 hidden, 110M params) |
| **Corpus** | 12GB textos legais ingleses |
| **Fontes** | Legislação, casos judiciais, contratos |
| **Variantes** | Geral, CONTRACTS-, EURLEX-, ECHR- |
| **Licença** | CC BY-SA 4.0 |

**Pontos Fortes:**
- Múltiplas variantes especializadas (contratos, ECHR, EUR-Lex)
- Bem documentado e citado (~500 citações)
- Supera BERT vanilla em tarefas legais

**Limitações:**
- Apenas inglês
- Sem fine-tuning apra NER out-of-the-box

**Variantes Disponíveis:**
```
nlpaueb/legal-bert-base-uncased      # Geral
nlpaueb/legal-bert-small-uncased     # Mais rápido
casehold/legalbert                   # Harvard Law corpus (37GB)
pile-of-law/legalbert-large-1.7M-2   # Pile of Law (256GB)
```

**Relevância para ContextSafe:** Média. Útil se expandir para documentos legais em inglês (contratos internacionais, arbitragem).

---

### 2.2 JuriBERT (Francês)

**Fonte:** [dascim/juribert-base](https://huggingface.co/dascim/juribert-base)

| Aspeto | Detalhe |
|--------|---------|
| **Arquitetura** | BERT (tiny, mini, small, base) |
| **Corpus** | 6.3GB textos legais franceses |
| **Fontes** | Légifrance + Cour de Cassation |
| **Instituição** | École Polytechnique + HEC Paris |
| **Paper** | [NLLP Workshop 2021](https://aclanthology.org/2021.nllp-1.9/) |

**Pontos Fortes:**
- Treinado de raiz em francês legal (sem fine-tuning)
- Inclui documentos da Cour de Cassation (100K+ docs)
- Múltiplos tamanhos disponíveis (tiny→base)

**Limitações:**
- Apenas francês
- Não há modelo NER pré-treinado

**Variantes Disponíveis:**
```
dascim/juribert-base    # 110M params
dascim/juribert-small   # Mais leve
dascim/juribert-mini    # Ainda mais leve
dascim/juribert-tiny    # Mínimo (para edge)
```

**Relevância para ContextSafe:** Alta para mercado francês. França tem regulações estritas de privacidade (CNIL + RGPD).

---

### 2.3 Italian-Legal-BERT (Italiano)

**Fonte:** [dlicari/Italian-Legal-BERT](https://huggingface.co/dlicari/Italian-Legal-BERT)

| Aspeto | Detalhe |
|--------|---------|
| **Arquitetura** | BERT-base italiano + pretraining adicional |
| **Corpus** | 3.7GB Archivio Giurisprudenziale Nazionale |
| **Base** | bert-base-italian-xxl-cased |
| **Paper** | [KM4Law 2022](https://ceur-ws.org/Vol-3256/km4law3.pdf) |
| **Training** | 4 epochs, 8.4M steps, V100 16GB |

**Pontos Fortes:**
- Variante para documentos longos (LSG 16K tokens)
- Versão destilada disponível (3x mais rápida)
- Avaliado em NER legal italiano

**Limitações:**
- Corpus principalmente direito civil
- Apenas italiano

**Variantes Disponíveis:**
```
dlicari/Italian-Legal-BERT          # Base
dlicari/Italian-Legal-BERT-SC       # De raiz (6.6GB)
dlicari/lsg16k-Italian-Legal-BERT   # Long context (16K tokens)
```

**Relevância para ContextSafe:** Média-alta. Itália tem mercado notarial significativo e normativa privacidade estrita.

---

### 2.4 Legal-BERTimbau (Português)

**Fonte:** [rufimelo/Legal-BERTimbau-base](https://huggingface.co/rufimelo/Legal-BERTimbau-base)

| Aspeto | Detalhe |
|--------|---------|
| **Arquitetura** | BERTimbau + fine-tuning legal |
| **Corpus** | 30K documentos legais portugueses |
| **Base** | neuralmind/bert-base-portuguese-cased |
| **Variante TSDAE** | 400K docs, técnica TSDAE |

**Pontos Fortes:**
- Base sólida (BERTimbau é SotA em português)
- Variante large disponível
- Versão para similaridade de frases (TSDAE)

**Limitações:**
- Corpus relativamente pequeno (30K docs vs 6GB+ de outros)
- Principalmente direito brasileiro

**Variantes Disponíveis:**
```
rufimelo/Legal-BERTimbau-base       # Base
rufimelo/Legal-BERTimbau-large      # Large
rufimelo/Legal-BERTimbau-large-TSDAE-v5  # Similaridade de frases
dominguesm/legal-bert-base-cased-ptbr    # Alternativa (STF)
dominguesm/legal-bert-ner-base-cased-ptbr # COM NER fine-tuned
```

**Modelo NER disponível:** `dominguesm/legal-bert-ner-base-cased-ptbr` já tem fine-tuning para NER legal em português.

**Relevância para ContextSafe:** Alta para mercado lusófono (Brasil + Portugal). Brasil tem LGPD similar a RGPD.

---

### 2.5 Legal-XLM-R / MultiLegalPile (Multilingue)

**Fonte:** [joelniklaus/legal-xlm-roberta-large](https://huggingface.co/joelniklaus/legal-xlm-roberta-large)

| Aspeto | Detalhe |
|--------|---------|
| **Arquitetura** | XLM-RoBERTa large (355M params) |
| **Corpus** | MultiLegalPile: 689GB em 24 idiomas |
| **Idiomas** | DE, EN, ES, FR, IT, PT, NL, PL, RO, + 15 mais |
| **Benchmark** | LEXTREME (11 datasets, 24 idiomas) |
| **Paper** | [ACL 2024](https://aclanthology.org/2024.acl-long.805/) |

**Idiomas cobertos:**
```
Germânicos:  DE (alemão), EN (inglês), NL (neerlandês)
Românicos:   ES (espanhol), FR (francês), IT (italiano), PT (português), RO (romeno)
Eslavos:     PL (polaco), BG (búlgaro), CS (checo), SK (eslovaco), SL (esloveno), HR (croata)
Outros:      EL (grego), HU (húngaro), FI (finlandês), LT (lituano), LV (letão), GA (irlandês), MT (maltês)
```

**Pontos Fortes:**
- **UM ÚNICO MODELO para 24 idiomas**
- Inclui espanhol nativo
- Tokenizer de 128K BPEs otimizado para legal
- Variante Longformer para documentos longos
- Estado da arte no benchmark LEXTREME

**Limitações:**
- Modelo grande (355M params vs 110M de modelos base)
- Desempenho ligeiramente inferior a monolingues em alguns casos

**Variantes Disponíveis:**
```
joelniklaus/legal-xlm-roberta-base   # Base (110M)
joelniklaus/legal-xlm-roberta-large  # Large (355M) - RECOMENDADO
joelniklaus/legal-longformer-base    # Long context
```

**Relevância para ContextSafe:** **MUITO ALTA**. Permite expansão imediata a múltiplos idiomas europeus com um único modelo.

---

## 3. Comparativa

### 3.1 Desempenho Relativo

| Modelo | NER Legal | Classificação | Long Docs | Multilingue |
|--------|-----------|---------------|-----------|-------------|
| Legal-BERT (EN) | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ❌ |
| JuriBERT (FR) | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ❌ |
| Italian-Legal-BERT | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ |
| Legal-BERTimbau (PT) | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ❌ |
| **Legal-XLM-R** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### 3.2 Recursos Computacionais

| Modelo | Parâmetros | VRAM (inference) | Latência* |
|--------|------------|------------------|-----------|
| Legal-BERT base | 110M | ~2GB | ~50ms |
| JuriBERT base | 110M | ~2GB | ~50ms |
| Italian-Legal-BERT | 110M | ~2GB | ~50ms |
| Legal-BERTimbau base | 110M | ~2GB | ~50ms |
| **Legal-XLM-R base** | 110M | ~2GB | ~60ms |
| **Legal-XLM-R large** | 355M | ~4GB | ~120ms |

*Por documento de 512 tokens em GPU

### 3.3 Disponibilidade NER Pré-treinado

| Modelo | NER Fine-tuned Disponível |
|--------|---------------------------|
| Legal-BERT | ❌ Requer fine-tuning |
| JuriBERT | ❌ Requer fine-tuning |
| Italian-Legal-BERT | ❌ Requer fine-tuning |
| Legal-BERTimbau | ✅ `dominguesm/legal-bert-ner-base-cased-ptbr` |
| Legal-XLM-R | ❌ Requer fine-tuning |

---

## 4. Estratégia Recomendada para ContextSafe

### 4.1 Opção A: Modelo Único Multilingue (Recomendado)

```
Legal-XLM-R large → Fine-tune NER com dados multilingues → Deploy único
```

**Vantagens:**
- Um só modelo para todos os idiomas
- Manutenção simplificada
- Transfer learning entre idiomas

**Desvantagens:**
- Desempenho ~5-10% inferior a monolingues
- Modelo maior (355M vs 110M)

**Esforço:** Médio (1 fine-tuning, 1 deploy)

### 4.2 Opção B: Modelos Monolingues por Mercado

```
ES: RoBERTalex (atual)
EN: Legal-BERT → Fine-tune NER
FR: JuriBERT → Fine-tune NER
IT: Italian-Legal-BERT → Fine-tune NER
PT: legal-bert-ner-base-cased-ptbr (já existe)
DE: Legal-XLM-R (alemão) → Fine-tune NER
```

**Vantagens:**
- Máximo desempenho por idioma
- Modelos mais pequenos

**Desvantagens:**
- 6 modelos a manter
- 6 datasets NER necessários
- Complexidade de deploy

**Esforço:** Alto (6 fine-tunings, 6 deploys)

### 4.3 Opção C: Híbrido (Recomendado para Escala)

```
Fase 1: Legal-XLM-R para todos os idiomas novos
Fase 2: Fine-tune monolingue para mercados com volume alto
```

**Roadmap:**
1. Deploy Legal-XLM-R para EN, FR, IT, PT, DE
2. Monitorizar métricas por idioma
3. Se idioma X tem >1000 utilizadores/mês → fine-tune monolingue
4. Manter XLM-R como fallback

---

## 5. Datasets NER Legais Multilingues

### 5.1 Disponíveis

| Dataset | Idiomas | Entidades | Tamanho | Fonte |
|---------|---------|-----------|--------|-------|
| MAPA | 24 | PER, ORG, LOC, DATE | 50K+ | [LEXTREME](https://huggingface.co/datasets/joelito/lextreme) |
| LegalNER-BR | PT | 14 tipos | 10K+ | [HuggingFace](https://huggingface.co/dominguesm) |
| EUR-Lex NER | EN, 23 | ORG, LOC | 100K+ | EUR-Lex |

### 5.2 A Criar (se for necessário fine-tuning)

Para fine-tuning de modelos monolingues, seria necessário criar datasets NER com as 13 categorias PII de ContextSafe:

| Categoria | Prioridade | Dificuldade |
|-----------|------------|-------------|
| PERSON_NAME | Alta | Média |
| DNI/ID_NACIONAL | Alta | Varia por país |
| PHONE | Alta | Fácil (regex + NER) |
| EMAIL | Alta | Fácil (regex) |
| ADDRESS | Alta | Média |
| ORGANIZATION | Alta | Média |
| DATE | Média | Fácil |
| IBAN | Média | Fácil (regex) |
| LOCATION | Média | Média |

---

## 6. Conclusões

### 6.1 Descobertas Principais

1. **Legal-XLM-R é a melhor opção** para expansão multilingue imediata
   - 24 idiomas com um único modelo
   - Inclui espanhol (valida compatibilidade com ContextSafe atual)
   - Estado da arte em benchmark LEXTREME

2. **Modelos monolingues superam multilingues** em ~5-10%
   - Considerar para mercados de alto volume
   - Português já tem NER pré-treinado

3. **O corpus de treino importa**
   - Italian-Legal-BERT tem versão long-context (16K tokens)
   - Legal-BERTimbau tem variante TSDAE para similarity

4. **Todos requerem fine-tuning** para as 13 categorias PII
   - Exceto `legal-bert-ner-base-cased-ptbr` (Português)

### 6.2 Recomendação Final

| Cenário | Recomendação |
|---------|--------------|
| MVP multilingue rápido | Legal-XLM-R large |
| Máximo desempenho EN | Legal-BERT + Fine-tune |
| Máximo desempenho FR | JuriBERT + Fine-tune |
| Máximo desempenho IT | Italian-Legal-BERT + Fine-tune |
| Máximo desempenho PT | `legal-bert-ner-base-cased-ptbr` (pronto) |
| Máximo desempenho DE | Legal-XLM-R (Alemão) + Fine-tune |

### 6.3 Próximos Passos

| Prioridade | Tarefa | Esforço |
|------------|--------|---------|
| 1 | Avaliar Legal-XLM-R em dataset espanhol atual | 2-4h |
| 2 | Criar benchmark multilingue (EN, FR, IT, PT, DE) | 8-16h |
| 3 | Fine-tune Legal-XLM-R para 13 categorias PII | 16-24h |
| 4 | Comparar vs modelos monolingues | 8-16h |

---

## 7. Referências

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

**Tempo de investigação:** ~45 min
**Gerado por:** AlexAlves87
**Data:** 29-01-2026
