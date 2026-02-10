# Pesquisa: Lacunas no Pipeline Híbrido NER-PII

**Data:** 30-01-2026
**Autor:** AlexAlves87
**Objetivo:** Analisar lacunas críticas no pipeline híbrido com base na literatura acadêmica 2024-2026
**Versão:** 2.0.0 (reescrita com fundamentação acadêmica)

---

## 1. Resumo Executivo

Foram identificadas cinco lacunas no pipeline híbrido NER-PII da ContextSafe. Para cada lacuna, foi conduzida uma revisão da literatura acadêmica em fontes de alto nível (ACL, EMNLP, COLING, NAACL, TACL, Nature Scientific Reports, Springer, arXiv). As recomendações propostas baseiam-se em evidências publicadas, não em intuição.

| Lacuna | Prioridade | Artigos Revisados | Recomendação Principal |
|--------|------------|-------------------|------------------------|
| Estratégia de Fusão | **ALTA** | 7 | Pipeline de 3 fases (RECAP) + prioridade por tipo |
| Calibração de Confiança | **ALTA** | 5 | Previsão Conforme + BRB para regex |
| Benchmark Comparativo | **MÉDIA** | 3 | nervaluate (SemEval'13) com correspondência parcial |
| Latência/Memória | **MÉDIA** | 4 | ONNX Runtime + Quantização INT8 |
| Gazetteers | **BAIXA** | 5 | Integração estilo GAIN como pós-filtro |

---

## 2. Literatura Revisada

| Artigo/Sistema | Local/Fonte | Ano | Descoberta Relevante |
|----------------|-------------|-----|----------------------|
| RECAP: Hybrid PII Detection | arXiv 2510.07551 | 2025 | Pipeline de 3 fases: detecção → desambiguação multi-label → consolidação de spans |
| Hybrid rule-based NLP + ML for PII (Mishra et al.) | Nature Scientific Reports | 2025 | F1 0.911 em docs financeiros, fusão de sobreposições por min(start)/max(end) |
| Conformal Prediction for NER | arXiv 2601.16999 | 2026 | Conjuntos de previsão com garantias de cobertura ≥95%, calibração estratificada |
| JCLB: Contrastive Learning + BRB | Springer Cybersecurity | 2024 | Belief Rule Base atribui confiança aprendida a regex, D-CMA-ES otimiza parâmetros |
| CMiNER | Expert Systems with Applications | 2025 | Estimadores de confiança em nível de entidade para dados ruidosos |
| B2NER | COLING 2025 | 2025 | Benchmark NER unificado, 54 conjuntos de dados, adaptadores LoRA ≤50MB, supera GPT-4 |
| nervaluate (SemEval'13 Task 9) | GitHub/MantisAI | 2024 | Métricas COR/INC/PAR/MIS/SPU com correspondência parcial |
| T2-NER | TACL | 2023 | Framework de 2 estágios baseado em spans para entidades sobrepostas e descontínuas |
| GNNer | ACL SRW 2022 | 2022 | Graph Neural Networks para reduzir spans sobrepostos |
| GAIN: Gazetteer-Adapted Integration | SemEval-2022 | 2022 | Divergência KL para adaptar rede gazetteer ao modelo de linguagem, 1º em 3 trilhas |
| Presidio | Microsoft Open Source | 2025 | `_remove_duplicates`: maior confiança vence, contenção → span maior |
| Soft Gazetteers | ACL 2020 | 2020 | Entity linking interlíngue para gazetteers em recursos limitados |
| SPLR (span-based nested NER) | J. Supercomputing | 2025 | F1 87.5 no ACE2005 com Função de Conhecimento Prévio |
| HuggingFace Optimum + ONNX | MarkTechPost/HuggingFace | 2025 | Benchmark PyTorch vs ONNX Runtime vs INT8 quantizado |
| PyDeID | PHI De-identification | 2025 | regex + spaCy NER, F1 87.9% em notas clínicas, 0.48s/nota |

---

## 3. Lacuna 1: Estratégia de Fusão (ALTA)

### 3.1 Problema

Quando o transformer NER e o Regex detectam a mesma entidade com limites ou tipos diferentes, qual preferir?

```
Texto: "Dom José García com DNI 12 345 678 Z"

NER detecta:   "José García com DNI 12 345 678" (PERSON estendido, parcial)
Regex detecta: "12 345 678 Z" (DNI_NIE, completo)
```

### 3.2 Estado da Arte

#### 3.2.1 Framework RECAP (arXiv 2510.07551, 2025)

O framework mais recente e completo para fusão híbrida de PII implementa **três fases**:

1.  **Fase I - Detecção Base:** Regex para PII estruturada (IDs, telefones) + LLM para não estruturada (nomes, endereços). Produz multi-labels, sobreposições e falsos positivos.

2.  **Fase II - Desambiguação Multi-label:** Para entidades com múltiplos labels, o texto, span e labels candidatos são passados para um LLM com prompt contextual que seleciona o rótulo correto.

3.  **Fase III - Consolidação:** Dois filtros:
    *   **Resolução determinística de sobreposição:** Entidades de menor prioridade completamente contidas em spans mais longos são removidas.
    *   **Filtragem contextual de falsos positivos:** Sequências numéricas curtas são verificadas com o contexto da frase circundante.

**Resultado:** F1 médio 0.657 em 13 locais, superando NER puro (0.360) em 82% e zero-shot LLM (0.558) em 17%.

#### 3.2.2 Microsoft Presidio (2025)

Presidio implementa `__remove_duplicates()` com regras simples:
*   **Maior pontuação de confiança vence** entre detecções sobrepostas
*   **Contenção:** Se uma PII está contida em outra, a de **texto mais longo** é usada
*   **Interseção parcial:** Ambas são retornadas concatenadas
*   Nenhuma prioridade por tipo, apenas por pontuação

#### 3.2.3 Mishra et al. (Nature Scientific Reports, 2025)

Para documentos financeiros, fusão de sobreposições:
*   `start = min(start1, start2)`
*   `end = max(end1, end2)`
*   A sobreposição é fundida em uma única entidade consolidada

**Limitação:** Não distingue tipos — inútil quando NER detecta PERSON e Regex detecta DNI no mesmo span.

#### 3.2.4 T2-NER (TACL, 2023)

Framework de 2 estágios baseado em spans:
1.  Extrair todos os spans de entidade (sobrepostos e planos)
2.  Classificar pares de spans para resolver descontinuidades

**Insight aplicável:** Separar a detecção de spans de sua classificação permite lidar com sobreposições de forma modular.

#### 3.2.5 GNNer (ACL Student Research Workshop, 2022)

Usa Graph Neural Networks para reduzir spans sobrepostos em NER baseado em spans. Os spans candidatos são nós em um grafo, e a GNN aprende a remover os sobrepostos.

**Insight aplicável:** Sobreposição nem sempre é erro — entidades aninhadas (nome dentro de endereço) são legítimas.

### 3.3 Implementação Atual da ContextSafe

Arquivo: `scripts/inference/ner_predictor.py`, método `_merge_regex_detections()`

```python
# Estratégia atual (linhas 430-443):
for ner_ent in ner_entities:
    replaced = False
    for match in regex_matches:
        if overlaps(match, ner_ent):
            if regex_len > ner_len * 1.2:  # Regex 20% mais longo
                replaced = True
                break
    if not replaced:
        ner_to_keep.append(ner_ent)
```

**Regra Atual:** Se regex é ≥20% mais longo que NER e há sobreposição → preferir regex.

### 3.4 Análise Comparativa

| Sistema | Estratégia | Lida com Aninhado | Usa Tipo | Usa Confiança |
|---------|------------|-------------------|----------|---------------|
| RECAP | 3 fases + LLM | ✅ | ✅ | Implícito |
| Presidio | Maior pontuação | ❌ | ❌ | ✅ |
| Mishra et al. | fusão min/max | ❌ | ❌ | ❌ |
| ContextSafe atual | Regex mais longo vence | ❌ | ❌ | ❌ |
| **Proposto** | **Prioridade tipo + validação** | **✅** | **✅** | **✅** |

### 3.5 Recomendação Baseada em Evidências

Inspirado pelo RECAP (3 fases) mas sem depender de LLM (nosso requisito é inferência em CPU sem LLM), propomos:

**Fase 1: Detecção Independente**
*   Transformer NER detecta entidades semânticas (PERSON, ORGANIZATION, LOCATION)
*   Regex detecta entidades estruturais (DNI, IBAN, PHONE, DATE)

**Fase 2: Resolução de Sobreposição por Prioridade de Tipo**

Baseado em evidências RECAP (regex se destaca em PII estruturada, NER em semântica):

```python
MERGE_PRIORITY = {
    # Tipo → (prioridade, fonte_preferida)
    # Regex com checksum = confiança máxima (evidência: Mishra et al. 2025)
    "DNI_NIE": (10, "regex"),      # Checksum verificável
    "IBAN": (10, "regex"),         # Checksum verificável
    "NSS": (10, "regex"),          # Checksum verificável
    "PHONE": (8, "regex"),         # Formato bem definido
    "POSTAL_CODE": (8, "regex"),   # 5 dígitos exatos
    "LICENSE_PLATE": (8, "regex"), # Formato bem definido
    # NER se destaca em entidades semânticas (RECAP, PyDeID)
    "DATE": (6, "any"),            # Ambos válidos
    "PERSON": (4, "ner"),          # NER melhor com contexto
    "ORGANIZATION": (4, "ner"),    # NER melhor com contexto
    "LOCATION": (4, "ner"),        # NER melhor com contexto
    "ADDRESS": (4, "ner"),         # NER melhor com contexto
}
```

**Fase 3: Consolidação**
*   Entidades **contidas** de tipos diferentes: manter ambas (aninhado legítimo, como no GNNer)
*   Entidades **contidas** do mesmo tipo: preferir a mais específica (fonte preferida)
*   Sobreposição **parcial**: preferir tipo de prioridade mais alta
*   Sem sobreposição: manter ambas

| Situação | Regra | Evidência |
|----------|-------|-----------|
| Sem sobreposição | Manter ambas | Padrão |
| Sobreposição, tipos dif. | Prioridade mais alta vence | RECAP Fase III |
| Contenção, tipos dif. | Manter ambas (aninhado) | GNNer, T2-NER |
| Contenção, mesmo tipo | Fonte preferida por tabela | Presidio (span maior) |
| Sobreposição parcial, mesmo tipo | Confiança mais alta vence | Presidio |

---

## 4. Lacuna 2: Calibração de Confiança (ALTA)

### 4.1 Problema

Regex retorna confiança fixa (0.95), NER retorna probabilidade softmax. Elas não são diretamente comparáveis.

### 4.2 Estado da Arte

#### 4.2.1 Previsão Conforme para NER (arXiv 2601.16999, Janeiro 2026)

**Artigo mais recente e relevante.** Introduz framework para produzir **conjuntos de previsão** com garantias de cobertura:

*   Dado nível de confiança `1-α`, gera conjuntos de previsão garantidos para conter o rótulo correto
*   Usa **pontuações de não-conformidade**:
    *   `nc1`: `1 - P̂(y|x)` — baseado na probabilidade, penaliza baixa confiança
    *   `nc2`: probabilidade cumulativa em sequências classificadas
    *   `nc3`: baseado no rank, produz conjuntos de tamanho fixo

**Descobertas Chave:**
*   `nc1` supera substancialmente `nc2` (que produz conjuntos "extremamente grandes")
*   **Calibração estratificada por comprimento** corrige descalibração sistemática em sequências longas
*   **Calibração por idioma** melhora cobertura (Inglês: 93.82% → 96.24% após estratificação)
*   Correção de Šidák para múltiplas entidades: confiança por entidade = `(1-α)^(1/s)` para `s` entidades

**Aplicabilidade à ContextSafe:** Calibração estratificada por comprimento é diretamente aplicável. Textos longos (contratos) podem ter pontuações sistematicamente diferentes de textos curtos.

#### 4.2.2 JCLB: Belief Rule Base (Springer Cybersecurity, 2024)

Introduz uma abordagem para **atribuir confiança a regras regex** de maneira aprendida:

*   Regras regex são formalizadas como uma **Belief Rule Base (BRB)**
*   Cada regra tem **graus de crença** otimizados por D-CMA-ES
*   A BRB filtra categorias de entidade e avalia sua correção simultaneamente
*   Parâmetros BRB são otimizados contra dados de treinamento

**Insight chave:** Regras regex NÃO devem ter confiança fixa. Sua confiança deve ser aprendida/calibrada contra dados reais.

#### 4.2.3 CMiNER (Expert Systems with Applications, 2025)

Projeta **estimadores de confiança em nível de entidade** que:
*   Avaliam a qualidade inicial de conjuntos de dados ruidosos
*   Auxiliam durante o treinamento ajustando pesos

**Insight aplicável:** Confiança em nível de entidade (não token) é mais útil para decisões de fusão.

#### 4.2.4 Conf-MPU (Zhou et al., 2022)

Classificação binária em nível de token para prever probabilidade de cada token ser uma entidade, então usa pontuações de confiança para estimativa de risco.

**Insight aplicável:** Separar "isso é uma entidade?" de "qual tipo?" permite calibrar em dois estágios.

### 4.3 Implementação Atual da ContextSafe

```python
# Padrões Regex (spanish_id_patterns.py):
RegexMatch(..., confidence=0.95)  # Valor fixo hardcoded

# Modelo NER:
confidence = softmax(logits).max()  # Probabilidade real [0.5-0.99]

# Ajuste de checksum (ner_predictor.py, linhas 473-485):
if is_valid:
    final_confidence = min(match.confidence * 1.1, 0.99)
elif checksum_conf < 0.5:
    final_confidence = match.confidence * 0.5
```

### 4.4 Análise do Problema

| Fonte | Confiança | Calibrada | Problema |
|-------|-----------|-----------|----------|
| NER softmax | 0.50-0.99 | ✅ | Pode estar descalibrada para textos longos (CP 2026) |
| Regex sem checksum | 0.95 fixa | ❌ | Superconfiança em correspondências ambíguas |
| Regex com checksum válido | 0.99 | ⚠️ | Apropriado para IDs com checksum |
| Regex com checksum inválido | 0.475 | ✅ | Penalidade apropriada |

### 4.5 Recomendação Baseada em Evidências

#### Nível 1: Confiança base diferenciada por tipo (inspirado por JCLB/BRB)

Não usar confiança fixa. Atribuir **confiança base** de acordo com o nível de validação disponível:

```python
REGEX_BASE_CONFIDENCE = {
    # Com checksum verificável (confiança máxima, Mishra et al. 2025)
    "DNI_NIE":  {"checksum_valid": 0.98, "checksum_invalid": 0.35, "format_only": 0.70},
    "IBAN":     {"checksum_valid": 0.99, "checksum_invalid": 0.30, "format_only": 0.65},
    "NSS":      {"checksum_valid": 0.95, "checksum_invalid": 0.35, "format_only": 0.65},

    # Sem checksum, com formato bem definido
    "PHONE":         {"with_prefix": 0.90, "without_prefix": 0.75},
    "POSTAL_CODE":   {"valid_province": 0.85, "format_only": 0.70},
    "LICENSE_PLATE": {"modern_format": 0.90, "old_format": 0.80},

    # Ambíguo
    "DATE":  {"full_textual": 0.85, "partial": 0.60, "ambiguous": 0.50},
    "EMAIL": {"standard": 0.95},
}
```

**Justificativa:** JCLB mostrou que a confiança da regra deve ser aprendida/diferenciada, não fixa. Sem acesso a dados de treinamento para otimizar BRB (como D-CMA-ES em JCLB), usamos heurísticas baseadas no nível de validação disponível (checksum > formato > correspondência simples).

#### Nível 2: Calibração estratificada (inspirado por CP 2026)

Para Transformer NER, considerar calibração por comprimento de texto:
*   Textos curtos (1-10 tokens): limite mínimo de confiança 0.60
*   Textos médios (11-50 tokens): limite 0.50
*   Textos longos (51+ tokens): limite 0.45

**Justificativa:** O artigo de Previsão Conforme (2026) mostrou que textos longos têm cobertura sistematicamente diferente. Estratificar por comprimento corrige essa descalibração.

#### Nível 3: Limite de confiança operacional

Baseado em RECAP e PyDeID:
*   **≥0.80:** Anonimização automática
*   **0.50-0.79:** Anonimização com flag "revisar"
*   **<0.50:** Não anonimizar, reportar como "duvidoso"

---

## 5. Lacuna 3: Benchmark Comparativo (MÉDIA)

### 5.1 Estado da Arte em Avaliação NER

#### 5.1.1 Métricas: seqeval vs nervaluate

| Framework | Tipo | Correspondência Parcial | Nível | Padrão |
|-----------|------|-------------------------|-------|--------|
| **seqeval** | Estrito nível-entidade | ❌ | Entidade completa | Eval CoNLL |
| **nervaluate** | Multi-cenário | ✅ | COR/INC/PAR/MIS/SPU | SemEval'13 Task 9 |

**seqeval** (padrão CoNLL):
*   Precisão, Recall, F1 em nível de entidade completa
*   Apenas correspondência exata: tipo correto E span completo
*   Média Micro/macro por tipo

**nervaluate** (SemEval'13 Task 9):
*   4 cenários: estrito, exato, parcial, tipo
*   5 categorias: COR (correto), INC (tipo incorreto), PAR (span parcial), MIS (perdido), SPU (espúrio)
*   Correspondência parcial: `Precisão = (COR + 0.5 × PAR) / ACT`

**Recomendação:** Usar **ambas** as métricas. seqeval para comparabilidade com literatura (CoNLL), nervaluate para análise de erro mais fina.

#### 5.1.2 Benchmark B2NER (COLING 2025)

*   54 conjuntos de dados, 400+ tipos de entidade, 6 idiomas
*   Benchmark unificado para Open NER
*   Adaptadores LoRA ≤50MB superam GPT-4 em 6.8-12.0 F1

**Aplicabilidade:** B2NER confirma que LoRA é viável para NER especializado, mas requer dados de qualidade (54 conjuntos de dados refinados).

### 5.2 Dados ContextSafe Disponíveis

| Configuração | F1 Estrito | Taxa de Aprovação | Fonte |
|--------------|------------|-------------------|-------|
| Apenas NER (legal_ner_v2 base) | 0.464 | 28.6% | Baseline |
| NER + Normalizador | 0.492 | 34.3% | Ciclo ML |
| NER + Regex | 0.543 | 45.7% | Ciclo ML |
| **Pipeline Completo (5 elem)** | **0.788** | **60.0%** | Ciclo ML |
| LoRA fine-tuning puro | 0.016 | 5.7% | Exp. 2026-02-04 |
| GLiNER zero-shot | 0.325 | 11.4% | Exp. 2026-02-04 |

### 5.3 Benchmark Pendente

| Teste | Métrica | Status |
|-------|---------|--------|
| Avaliar com nervaluate (match parcial) | COR/INC/PAR/MIS/SPU | Pendente |
| Apenas Regex (sem NER) | F1 estrito + parcial | Pendente |
| NER + Checksum (sem padrões regex) | F1 estrito + parcial | Pendente |
| Comparação de quebra por tipo de entidade | F1 por tipo | Pendente |

### 5.4 Recomendação

Criar script `scripts/evaluate/benchmark_nervaluate.py` que:
1.  Execute pipeline completo contra conjunto de teste adversarial
2.  Relate métricas seqeval (estrito, para comparabilidade)
3.  Relate métricas nervaluate (4 cenários, para análise de erro)
4.  Quebre por tipo de entidade
5.  Compare ablações (apenas NER, apenas Regex, Híbrido)

---

## 6. Lacuna 4: Latência/Memória (MÉDIA)

### 6.1 Objetivo

| Métrica | Meta | Justificativa |
|---------|------|---------------|
| Latência | <500ms por página A4 (~600 tokens) | UX responsiva |
| Memória | <2GB modelo em RAM | Implantação em 16GB |
| Vazão | >10 páginas/segundo (batch) | Processamento em massa |

### 6.2 Estado da Arte em Otimização de Inferência

#### 6.2.1 ONNX Runtime + Quantização (HuggingFace Optimum, 2025)

HuggingFace Optimum permite:
*   Exportar para ONNX
*   Otimização de grafo (fusão de operadores, eliminação de nós redundantes)
*   Quantização INT8 (dinâmica ou estática)
*   Benchmarking integrado: PyTorch vs torch.compile vs ONNX vs ONNX quantizado

**Resultados Relatados:**
*   Otimizado TensorRT: até 432 inferências/segundo (ResNet-50, não NER)
*   ONNX Runtime: aceleração típica de 2-4x sobre PyTorch vanilla em CPU

#### 6.2.2 PyDeID (2025)

Sistema híbrido regex + spaCy NER para desidentificação:
*   **0.48 segundos/nota** vs 6.38 segundos/nota do sistema base
*   Fator de aceleração 13x com regex otimizado + NER
*   F1 87.9% com o pipeline rápido

**Aplicabilidade direta:** PyDeID demonstra que um pipeline híbrido regex+NER pode processar 1 documento em <0.5s.

#### 6.2.3 Pipeline de Otimização Transformer

```
PyTorch FP32 → Exportar ONNX → Otimização Grafo → Quantização INT8
    baseline        2x               2-3x                 3-4x
```

### 6.3 Estimativa Teórica para ContextSafe

| Componente | CPU (PyTorch) | CPU (ONNX INT8) | Memória |
|------------|---------------|-----------------|---------|
| TextNormalizer | <1ms | <1ms | ~0 |
| NER (RoBERTa-BNE ~125M) | ~200-400ms | ~50-100ms | ~500MB → ~200MB |
| Validadores Checksum | <1ms | <1ms | ~0 |
| Padrões Regex | <5ms | <5ms | ~0 |
| Padrões Data | <2ms | <2ms | ~0 |
| Refinamento Limites | <1ms | <1ms | ~0 |
| **Total** | **~210-410ms** | **~60-110ms** | **~500MB → ~200MB** |

**Conclusão:** Com ONNX INT8 deve atingir <500ms/página com ampla margem.

### 6.4 Recomendação

1.  **Primeiro medir** latência atual com PyTorch (script `benchmark_latency.py`)
2.  **Se satisfizer** <500ms em CPU: documentar e adiar otimização ONNX
3.  **Se falhar**: exportar ONNX + quantização INT8 (priorizar)
4.  **Documentar** processo para replicabilidade em outros idiomas

---

## 7. Lacuna 5: Gazetteers (BAIXA)

### 7.1 Estado da Arte

#### 7.1.1 GAIN: Gazetteer-Adapted Integration Network (SemEval-2022)

*   **Adaptação divergência KL:** Rede Gazetteer se adapta ao modelo de linguagem minimizando divergência KL
*   **2 estágios:** Primeiro adaptar gazetteer ao modelo, depois treinar NER supervisionado
*   **Resultado:** 1º em 3 trilhas (Chinês, Code-mixed, Bangla), 2º em 10 trilhas
*   **Insight:** Gazetteers são mais úteis quando integrados como recurso adicional, não como busca direta

#### 7.1.2 Gazetteer-Enhanced Attentive Neural Networks (EMNLP 2019)

*   Rede auxiliar codificando "regularidade de nome" usando apenas gazetteers
*   Incorporado no NER principal para melhor reconhecimento
*   **Reduz requisitos de dados de treinamento** significativamente

#### 7.1.3 Soft Gazetteers para NER de Baixo Recurso (ACL 2020)

*   Em idiomas sem gazetteers exaustivos, usar entity linking interlíngue
*   Wikipedia como fonte de conhecimento
*   Experimentado em 4 idiomas de baixo recurso

#### 7.1.4 Redução de Correspondência Espúria

*   Gazetteers brutos geram **muitos falsos positivos** (correspondência espúria)
*   Filtrar por "popularidade da entidade" melhora F1 em +3.70%
*   **Gazetteers Limpos > Gazetteers Completos**

### 7.2 Gazetteers Disponíveis na ContextSafe

| Gazetteer | Registros | Fonte | No Pipeline |
|-----------|-----------|-------|-------------|
| Sobrenomes | 27,251 | INE | ❌ |
| Nomes homens | 550 | INE | ❌ |
| Nomes mulheres | 550 | INE | ❌ |
| Nomes arcaicos | 6,010 | Gerado | ❌ |
| Municípios | 8,115 | INE | ❌ |
| Códigos postais | 11,051 | INE | ❌ |

### 7.3 Recomendação Baseada em Evidências

**Não integrar gazetteers no pipeline principal** pelas seguintes razões baseadas na literatura:

1.  **Correspondência espúria** (EMNLP 2019): Sem filtragem de popularidade, gazetteers geram falsos positivos
2.  **Pipeline já funciona** (F1 0.788): Benefício marginal dos gazetteers é baixo
3.  **Complexidade de replicabilidade:** Gazetteers são específicos do idioma, cada idioma precisa de fontes diferentes

**Uso recomendado como pós-filtro:**
*   **Validação de nome:** Se NER detecta PERSON, verificar se nome/sobrenome está no gazetteer → aumentar confiança +0.05
*   **Validação de Código Postal:** Se regex detecta POSTAL_CODE 28001, verificar se corresponde a município real → aumentar confiança +0.10
*   **NÃO usar para detecção:** Não buscar nomes do gazetteer diretamente no texto (risco de correspondência espúria)

---

## 8. Plano de Ação

### 8.1 Ações Imediatas (Alta Prioridade)

| Ação | Base Acadêmica | Arquivo |
|------|----------------|---------|
| Implementar estratégia de fusão 3 fases | RECAP (2025) | `ner_predictor.py` |
| Remover confiança fixa de 0.95 no regex | JCLB/BRB (2024) | `spanish_id_patterns.py` |
| Adicionar tabela de prioridade por tipo | RECAP, Presidio | `ner_predictor.py` |

### 8.2 Ações de Melhoria (Média Prioridade)

| Ação | Base Acadêmica | Arquivo |
|------|----------------|---------|
| Avaliar com nervaluate (match parcial) | SemEval'13 Task 9 | `benchmark_nervaluate.py` |
| Criar benchmark de latência | PyDeID (2025) | `benchmark_latency.py` |
| Documentar calibração por comprimento | CP NER (2026) | Guia de replicabilidade |

### 8.3 Ações Adiosas (Baixa Prioridade)

| Ação | Base Acadêmica | Arquivo |
|------|----------------|---------|
| Gazetteers como pós-filtro | GAIN (2022) | `ner_predictor.py` |
| Exportar ONNX + INT8 | HuggingFace Optimum | `scripts/export/` |

---

## 9. Conclusões

### 9.1 Principais Descobertas da Pesquisa

1.  **O pipeline híbrido é SOTA para PII** — RECAP (2025), PyDeID (2025) e Mishra et al. (2025) confirmam que regex + NER supera cada componente separadamente.

2.  **A confiança do regex não deve ser fixa** — JCLB (2024) demonstrou que atribuir confiança aprendida às regras melhora significativamente o desempenho.

3.  **A calibração por comprimento de texto é importante** — Previsão Conforme (2026) demonstrou descalibração sistemática em sequências longas.

4.  **nervaluate complementa seqeval** — SemEval'13 Task 9 oferece métricas de correspondência parcial que capturam erros de limite que seqeval ignora.

5.  **ONNX INT8 é viável para latência <500ms** — PyDeID demonstrou <0.5s/documento com pipeline híbrido otimizado.

### 9.2 Status dos Modelos Avaliados

| Modelo | Avaliação | F1 Adversarial | Status |
|--------|-----------|----------------|--------|
| **RoBERTa-BNE CAPITEL NER** (`legal_ner_v2`) | Pipeline completo 5 elementos | **0.788** | **ATIVO** |
| GLiNER-PII (zero-shot) | Avaliado em 35 testes adversariais | 0.325 | Descartado (inferior) |
| LoRA Legal-XLM-R-base (`lora_ner_v1`) | Avaliado em 35 testes adversariais | 0.016 | Descartado (overfitting) |
| MEL (Modelo Legal Espanhol) | Investigado | N/A (sem versão NER) | Descartado |
| Legal-XLM-R-base (joelniklaus) | Investigado para multilíngue | N/A | Pendente para expansão futura |

> **Nota:** O modelo base do pipeline é `roberta-base-bne-capitel-ner` (RoBERTa-BNE, ~125M params, vocab 50,262),
> fine-tuned com dados sintéticos v3 (30% injeção de ruído). **NÃO** é XLM-RoBERTa.

### 9.3 Recomendações para Replicabilidade

Para replicar em outros idiomas, os adaptadores são:

| Componente | Espanha (ES) | França (FR) | Itália (IT) | Adaptação |
|------------|--------------|-------------|-------------|-----------|
| Modelo NER | RoBERTa-BNE CAPITEL | JuriBERT/CamemBERT | Legal-BERT-IT | Fine-tune NER por idioma |
| NER Multilíngue (alternativa) | Legal-XLM-R | Legal-XLM-R | Legal-XLM-R | Modelo multilíngue único |
| Padrões Regex | DNI/NIE, IBAN ES | CNI, IBAN FR | CF, IBAN IT | Novo arquivo regex |
| Validadores Checksum | mod-23 (DNI) | mod-97 (IBAN) | Codice Fiscale | Novo validador |
| Prioridades de Fusão | Tabela 3.5 | Mesma estrutura | Mesma estrutura | Ajustar tipos |
| Calibração de Confiança | Tabela 4.5 | Mesma estrutura | Mesma estrutura | Calibrar por tipo local |
| Gazetteers | INE | INSEE | ISTAT | Fontes nacionais |

---

**Gerado por:** AlexAlves87
**Data:** 30-01-2026
**Versão:** 2.0.0 — Reescrito com pesquisa acadêmica (v1.0 carecia de fundamentação)
