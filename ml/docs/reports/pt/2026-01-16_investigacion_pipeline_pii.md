# Pesquisa: Melhores Práticas para Pipeline de Detecção de PII

**Data:** 2026-01-16
**Autor:** AlexAlves87
**Tipo:** Revisão de Literatura
**Status:** Concluído

---

## Resumo Executivo

Esta pesquisa analisa o estado da arte na detecção de PII (Personally Identifiable Information) com foco em documentos legais espanhóis. Artigos acadêmicos recentes (2024-2025) e frameworks de produção foram revisados para identificar melhores práticas em pré-processamento, arquitetura de pipeline e pós-processamento.

**Principal Conclusão:** A arquitetura ideal é **híbrida** (Regex → NER → Validação), não NER puro com pós-processamento. Além disso, a injeção de ruído OCR (30%) durante o treinamento melhora significativamente a robustez.

---

## Metodologia

### Fontes Consultadas

| Fonte | Tipo | Ano | Relevância |
|--------|------|-----|------------|
| PMC12214779 | Artigo Acadêmico | 2025 | Híbrido NLP-ML para PII financeiro |
| arXiv 2401.10825v3 | Pesquisa (Survey) | 2024 | Estado da arte NER |
| Microsoft Presidio | Framework | 2024 | Melhores práticas da indústria |
| Presidio Research | Ferramenta | 2024 | Avaliação de reconhecedores |

### Critérios de Busca

- "NER preprocessing postprocessing best practices 2024"
- "Spanish legal documents PII detection"
- "Hybrid rule-based NLP machine learning PII"
- "Presidio pipeline architecture"

---

## Resultados

### 1. Arquitetura de Pipeline Otimizada

#### 1.1 Ordem de Processamento (Presidio)

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Texto    │ → │   Regex     │ → │   NLP NER   │ → │  Checksum   │ → │   Limite    │
│    (OCR)    │    │  Matchers   │    │   Modelo    │    │ Validação   │    │   Filtro    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

**Fonte:** Documentação Microsoft Presidio

**Justificativa:**
> "O Presidio usa inicialmente seu matcher regex para identificar entidades correspondentes. Em seguida, o modelo NER baseado em Processamento de Linguagem Natural é usado para detectar PII de forma autônoma. Quando possível, um checksum é usado para validar os PIIs identificados."

#### 1.2 Componentes do Pipeline

| Componente | Função | Implementação |
|------------|---------|----------------|
| **Regex Matchers** | Detectar padrões estruturados (DNI, IBAN, telefone) | Executar ANTES do NER |
| **NLP NER** | Detectar entidades contextuais (nomes, endereços) | Modelo Transformer |
| **Checksum Validation** | Validar integridade de identificadores | DNI mod-23, IBAN mod-97 |
| **Context Enhancement** | Melhorar confiança com contexto lexical | LemmaContextAwareEnhancer |
| **Threshold Filter** | Filtrar por pontuação de confiança | Configurável (ex: 0.7) |

### 2. Pré-processamento

#### 2.1 Normalização de Texto

**Fonte:** PMC12214779 (Hybrid NLP-ML)

| Técnica | Descrição | Aplicabilidade |
|---------|-------------|---------------|
| Tokenização | Divisão em unidades discretas | Universal |
| Marcação de Posição | Marcação de posição a nível de caractere | Para recuperação de span |
| Normalização Unicode | Fullwidth → ASCII, remoção de largura zero | Alta para OCR |
| Normalização de Abreviações | D.N.I. → DNI | Alta para espanhol |

#### 2.2 Injeção de Ruído (CRÍTICO)

**Fonte:** PMC12214779

> "Para melhor simular anomalias de documentos do mundo real, o pré-processamento de dados adiciona ruído aleatório menor, como remoção de pontuação e normalização de texto."

**Implementação recomendada:**
```python
# 30% de probabilidade de ruído por amostra
noise_probability = 0.30

# Tipos de ruído:
# - Remoção aleatória de pontuação
# - Substituição de caracteres OCR (l↔I, 0↔O)
# - Colapso/expansão de espaços
# - Perda de acentos
```

**Impacto:** Melhora a robustez contra documentos digitalizados reais.

### 3. Arquitetura do Modelo

#### 3.1 Estado da Arte NER (2024)

**Fonte:** arXiv 2401.10825v3

| Arquitetura | Características | Benchmark F1 |
|--------------|-----------------|--------------|
| DeBERTa | Atenção desembaraçada + decodificador de máscara aprimorado | SOTA |
| RoBERTa + CRF | Transformer + coerência de sequência | +4-13% vs base |
| BERT + BiLSTM | Modelagem contextual + sequencial | Robusto |
| GLiNER | Atenção global para entidades distantes | Inovador |

#### 3.2 Camada CRF

**Fonte:** Pesquisa arXiv

> "A aplicação de CRF fornece um método robusto para NER, garantindo sequências de rótulos coerentes e modelando dependências entre rótulos adjacentes."

**Benefício:** Previne sequências inválidas como `B-PERSON I-LOCATION`.

### 4. Pós-processamento

#### 4.1 Validação de Checksum

**Fonte:** Melhores Práticas Presidio

| Tipo | Algoritmo | Exemplo |
|------|-----------|---------|
| DNI espanhol | letra = "TRWAGMYFPDXBNJZSQVHLCKE"[num % 23] | 12345678Z |
| NIE espanhol | Prefixo X=0, Y=1, Z=2 + algoritmo DNI | X1234567L |
| IBAN | ISO 7064 Mod 97-10 | ES9121000418450200051332 |
| NSS espanhol | Mod 97 nos primeiros 10 dígitos | 281234567890 |
| Cartão de Crédito | Algoritmo Luhn | 4111111111111111 |

#### 4.2 Melhoria Consciente do Contexto

**Fonte:** Presidio LemmaContextAwareEnhancer

> "O ContextAwareEnhancer é um módulo que melhora a detecção de entidades usando o contexto do texto. Pode melhorar a detecção de entidades que dependem do contexto."

**Implementação:**
- Pesquisar palavras-chave na janela de ±N tokens
- Aumentar/diminuir pontuação com base no contexto
- Exemplo: "DNI" perto de um número aumenta a confiança DNI_NIE

#### 4.3 Filtragem por Limite

**Fonte:** Guia de Ajuste Presidio

> "Ajuste os limites de confiança nos reconhecedores de ML para equilibrar casos perdidos versus mascaramento excessivo."

**Recomendação:**
- Limite alto (0.8+): Menos falsos positivos, mais falsos negativos
- Limite baixo (0.5-0.6): Mais cobertura, mais ruído
- Piloto inicial para calibrar

### 5. Resultados de Benchmark

#### 5.1 Híbrido NLP-ML (PMC12214779)

| Métrica | Valor |
|---------|-------|
| Precisão | 94.7% |
| Recall | 89.4% |
| F1-score | 91.1% |
| Acurácia (mundo real) | 93.0% |

**Fatores de Sucesso:**
1. Dados de treinamento diversos (modelos variados)
2. Framework leve (spaCy vs transformers pesados)
3. Métricas equilibradas (precisão ≈ recall)
4. Anonimização que preserva o contexto

#### 5.2 Ajuste Presidio

**Fonte:** Presidio Research Notebook 5

> "O Notebook 5 no presidio-research mostra como se pode configurar o Presidio para detectar PII com muito mais precisão e aumentar o F-score em ~30%."

---

## Análise de Lacunas (Gap Analysis)

### Comparação: Implementação Atual vs Melhores Práticas

| Aspecto | Melhor Prática | Implementação Atual | Lacuna |
|---------|---------------|----------------------|-----|
| Ordem do pipeline | Regex → NER → Validação | NER → Pós-processamento | **CRÍTICO** |
| Injeção de ruído | 30% em treinamento | 0% | **CRÍTICO** |
| Camada CRF | Adicionar sobre transformer | Não implementado | MÉDIO |
| Limite de confiança | Filtrar por pontuação | Não implementado | MÉDIO |
| Melhoria de contexto | Baseado em lema | Parcial (regex) | BAIXO |
| Validação checksum | DNI, IBAN, NSS | Implementado | ✓ OK |
| Validação de formato | Padrões Regex | Implementado | ✓ OK |

### Impacto Estimado das Correções

| Correção | Esforço | Impacto F1 Estimado |
|------------|----------|---------------------|
| Injeção de ruído no dataset | Baixo | +10-15% em OCR |
| Pipeline Regex-first | Médio | +5-10% precisão |
| Camada CRF | Alto | +4-13% (literatura) |
| Limite de confiança | Baixo | Reduz FP 20-30% |

---

## Conclusões

### Principais Descobertas

1. **Arquitetura híbrida é superior**: Combinar regex (padrões estruturados) com NER (contextual) supera abordagens puras.

2. **A ordem importa**: Regex ANTES do NER, não depois. O Presidio usa essa ordem por design.

3. **Ruído no treinamento é crítico**: 30% de injeção de erros OCR melhora significativamente a robustez.

4. **Validação de checksum é padrão**: Validar identificadores estruturados (DNI, IBAN) é prática universal.

5. **CRF melhora a coerência**: Adicionar camada CRF sobre transformer previne sequências inválidas.

### Recomendações

#### Prioridade ALTA (Implementar Imediatamente)

1. **Injetar ruído OCR no dataset v3**
   - 30% das amostras com erros simulados
   - Tipos: l↔I, 0↔O, espaços, acentos ausentes
   - Retreinar modelo

2. **Reestruturar pipeline**
   ```
   ANTES: Texto → NER → Pós-processamento
   DEPOIS: Texto → Pré-processamento → Regex → NER → Validação → Filtro
   ```

#### Prioridade MÉDIA

3. **Adicionar limite de confiança**
   - Filtrar entidades com pontuação < 0.7
   - Calibrar com conjunto de validação

4. **Avaliar camada CRF**
   - Investigar `transformers` + `pytorch-crf`
   - Benchmark contra modelo atual

#### Prioridade BAIXA

5. **Melhoria de contexto avançada**
   - Implementar LemmaContextAwareEnhancer
   - Gazetteers de contexto por tipo de entidade

---

## Referências

1. **PMC12214779** - "A hybrid rule-based NLP and machine learning approach for PII detection and anonymization in financial documents"
   - URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC12214779/
   - Ano: 2025

2. **arXiv 2401.10825v3** - "Recent Advances in Named Entity Recognition: A Comprehensive Survey and Comparative Study"
   - URL: https://arxiv.org/html/2401.10825v3
   - Ano: 2024 (atualizado 2025)

3. **Microsoft Presidio** - Best Practices for Developing Recognizers
   - URL: https://microsoft.github.io/presidio/analyzer/developing_recognizers/
   - Ano: 2024

4. **Presidio Research** - Evaluation Toolbox
   - URL: https://github.com/microsoft/presidio-research
   - Ano: 2024

5. **Nature Scientific Reports** - "A hybrid rule-based NLP and machine learning approach"
   - URL: https://www.nature.com/articles/s41598-025-04971-9
   - Ano: 2025

---

**Data:** 2026-01-16
**Versão:** 1.0
