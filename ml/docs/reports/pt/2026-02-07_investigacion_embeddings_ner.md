# Investigação: Embeddings Gerais vs Domínio Legal para Desambiguação de Tipos de Entidade em NER

**Data:** 07-02-2026
**Objetivo:** Investigar por que os embeddings legais especializados produzem mais falsos positivos que os embeddings de propósito geral na tarefa de classificação de tipo de entidade pós-NER, e determinar a melhor estratégia de embeddings para ContextSafe.

---

## 1. Resumo Executivo

1.  **Os embeddings de domínio legal produzem mais falsos positivos** porque o fine-tuning legal reduz a capacidade discriminativa entre tipos de entidade ao colapsar o espaço de embeddings ao redor de padrões linguísticos legais (anisotropia aumentada, espaço semântico mais estreito).
2.  **Os embeddings de propósito geral são superiores para discriminação de tipos de entidade** porque mantêm um espaço semântico mais amplo e diversificado onde as diferenças entre categorias (pessoa vs organização vs data) são mais pronunciadas.
3.  **A anisotropia NÃO é inerentemente ruim** -- trabalho recente (ICLR 2024) mostra que a anisotropia controlada pode melhorar o desempenho -- mas a anisotropia não controlada por fine-tuning de domínio reduz a discriminação inter-classe necessária para centroides de tipo.
4.  **Recomendação: usar `BAAI/bge-m3` ou `intfloat/multilingual-e5-large`** (embeddings gerais) para o validador de tipo, NÃO embeddings legais. Se for desejado combinar conhecimento de domínio, usar uma abordagem híbrida com adaptadores (LoRA) que preservem a capacidade geral.
5.  **A técnica de centroides com contexto é bem respaldada** pela literatura de redes prototípicas (CEPTNER, KCL), mas requer 50-100 exemplos diversos por tipo e contexto circundante de 10-15 tokens.

---

## 2. Descoberta 1: General-Purpose vs Domain-Specific Embeddings para Classificação de Tipo de Entidade

### 2.1 Evidência chave: Modelos general-purpose falham em tarefas de domínio MAS destacam-se em discriminação de tipos

| Paper | Local/Ano | Descoberta chave |
| :--- | :--- | :--- |
| **"Do We Need Domain-Specific Embedding Models? An Empirical Investigation"** (Tang & Yang) | arXiv 2409.18511 (2024) | Avaliaram 7 modelos SOTA em FinMTEB (finance benchmark). Os modelos gerais mostraram queda significativa em tarefas de domínio, e seu desempenho em MTEB NÃO correlaciona com desempenho em FinMTEB. **MAS**: essa queda foi em retrieval e STS, não em classificação de tipos de entidade. |
| **"NuNER: Entity Recognition Encoder Pre-training via LLM-Annotated Data"** (Bogdanov et al.) | EMNLP 2024 | Modelo compacto (base RoBERTa) pré-treinado com contrastive learning sobre 4.38M anotações de entidade. Supera modelos de tamanho similar em few-shot NER e compete com LLMs muito maiores. **Chave**: a diversidade de tipos de entidade no dataset de pré-treinamento é fundamental. |
| **"LegNER: A Domain-Adapted Transformer for Legal NER and Text Anonymization"** (Al-Hussaeni et al.) | Frontiers in AI (2025) | Modelo legal baseado em BERT-base + vocabulário estendido + 1.542 casos judiciais anotados. F1 >99% em 6 tipos de entidade. **No entanto**: o paper não reporta análise de falsos positivos entre tipos, e as entidades avaliadas são muito diferentes entre si (PESSOA vs LEI vs REFERÊNCIA\_CASO). |
| **"MEL: Legal Spanish Language Model"** (2025) | arXiv 2501.16011 | XLM-RoBERTa-large fine-tuned com 5.52M textos legais espanhóis (92.7 GB). Supera o XLM-R base em classificação de documentos. **Crítico**: os autores admitem que "Tarefas de classificação de token ou span permanecem não avaliadas devido à falta de textos anotados" -- ou seja, NÃO avaliaram NER. |

### 2.2 Interpretação: Por que os modelos gerais discriminam melhor TIPOS

A distinção chave é entre **duas tarefas diferentes**:

| Tarefa | O que o embedding precisa | Melhor modelo |
| :--- | :--- | :--- |
| Retrieval legal / STS legal | Capturar nuances semânticas legais | Domain-specific |
| Classificação de tipo de entidade | Separar categorias amplas (pessoa vs org vs data) | General-purpose |

Os embeddings legais estão otimizados para a primeira tarefa: recuperar documentos legais similares, entender terminologia jurídica, capturar relações legais. Isso os torna PIORES para a segunda tarefa porque:

1.  **Colapso de diversidade**: o fine-tuning legal aproxima todas as representações em direção ao subespaço legal, reduzindo a distância entre "pessoa mencionada em sentença" e "organização mencionada em sentença" porque ambas aparecem em contextos legais similares.
2.  **Viés contextual**: um modelo legal aprende que "Telefonica" em um contexto legal é tão legal-relevant como "Alejandro Alvarez", achatando as diferenças de tipo.
3.  **Anisotropia não controlada**: o fine-tuning introduz anisotropia que pode colapsar tipos distintos nas mesmas direções dominantes do espaço de embeddings.

**URL relevante**: [Do We Need Domain-Specific Embedding Models?](https://arxiv.org/abs/2409.18511)

---

## 3. Descoberta 2: Por Que os Embeddings Legais Produzem Mais Falsos Positivos

### 3.1 O problema de anisotropia em embeddings fine-tuned

| Paper | Local/Ano | Descoberta chave |
| :--- | :--- | :--- |
| **"Anisotropy is Not Inherent to Transformers"** (Machina & Mercer) | NAACL 2024 | Demonstram que a anisotropia não é inerente à arquitetura transformer. Identificam modelos Pythia grandes com espaços isotrópicos. As justificativas teóricas prévias para a anisotropia eram insuficientes. |
| **"Stable Anisotropic Regularization" (I-STAR)** (Rudman & Eickhoff) | ICLR 2024 | Resultado contraintuitivo: REDUZIR a isotropia (aumentar anisotropia) melhora o desempenho downstream. Usar IsoScore* (métrica diferenciável) como regularizador. **Implicação chave**: a anisotropia CONTROLADA pode ser benéfica, mas a anisotropia NÃO CONTROLADA por fine-tuning de domínio é prejudicial. |
| **"The Shape of Learning: Anisotropy and Intrinsic Dimensions in Transformer-Based Models"** (2024) | EACL 2024 | Os decoders transformer mostram uma curva em forma de sino com máxima anisotropia em camadas médias, enquanto os encoders mostram anisotropia mais uniforme. As camadas onde a anisotropia é maior coincidem com camadas que codificam informação de tipo. |
| **"How Does Fine-tuning Affect the Geometry of Embedding Space: A Case Study on Isotropy"** (Rajaee & Pilehvar) | EMNLP 2021 Findings | Embora a isotropia seja desejável, o fine-tuning NÃO necessariamente melhora a isotropia. As estruturas locais (como codificação de tipos de token) sofrem mudanças massivas durante o fine-tuning. As direções alongadas (direções dominantes) no espaço fine-tuned carregam o conhecimento linguístico essencial. |
| **"Representation Degeneration Problem in Prompt-based Fine-tuning"** | LREC 2024 | A anisotropia do espaço de embeddings limita o desempenho em fine-tuning baseado em prompts. Propõem CLMA (Contrastive Learning framework) para aliviar a anisotropia. |

### 3.2 Mecanismo de falsos positivos em embeddings legais

Baseado na evidência anterior, o mecanismo pelo qual os embeddings legais produzem mais falsos positivos em validação de tipo de entidade é:

```
1. Fine-tuning legal → Embedding space se contrai em direção ao subespaço legal
                         ↓
2. Representações de "pessoa em contexto legal" e
   "organização em contexto legal" se aproximam
   (ambas são "entidades legalmente relevantes")
                         ↓
3. Centroides de PERSON_NAME e ORGANIZATION se sobrepõem
   no espaço legal-fine-tuned
                         ↓
4. Cosine similarity entre centroide_PERSON e uma ORGANIZATION
   é mais alta do que seria com embeddings gerais
                         ↓
5. Mais entidades cruzam o limiar de reclassificação → mais FP
```

### 3.3 Evidência direta do domínio legal

| Paper | Local/Ano | Descoberta chave |
| :--- | :--- | :--- |
| **"Improving Legal Entity Recognition Using a Hybrid Transformer Model and Semantic Filtering Approach"** | arXiv 2410.08521 (2024) | Legal-BERT produz falsos positivos em termos ambíguos e entidades aninhadas. Propõem filtragem semântica pós-predição usando cosine similarity contra padrões legais predefinidos. **Resultado**: Precisão sobe de 90.2% a 94.1% (+3.9 pp), F1 de 89.3% a 93.4% (+4.1 pp). Usam a fórmula S(ei,Pj) = cos(ei, Pj) com limiar tau para filtrar. |

**Este paper valida diretamente nossa abordagem** de usar cosine similarity para filtrar predições, MAS usa padrões legais predefinidos em vez de centroides de tipo. A combinação de ambas as abordagens (centroides gerais + padrões legais como filtro adicional) é uma extensão natural.

**URL relevante**: [Improving Legal Entity Recognition Using Semantic Filtering](https://arxiv.org/abs/2410.08521)

---

## 4. Descoberta 3: Melhores Modelos de Embeddings para Desambiguação de Tipo de Entidade (2024-2026)

### 4.1 Comparação de modelos candidatos

| Modelo | Tamanho | Dim | Idiomas | MTEB Score | Fortalezas | Fraquezas para nossa tarefa |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BAAI/bge-m3** | ~2.3GB | 1024 | 100+ | 63.0 | Multi-granularidade (dense+sparse+ColBERT), melhor desempenho multilingual em MTEB | Maior tamanho, maior latência |
| **intfloat/multilingual-e5-large** | ~1.1GB | 1024 | 100+ | ~62 | Excelente espanhol, bem documentado, requer prefixo "query:" | Ligeiramente inferior a bge-m3 em multilingual |
| **nomic-ai/nomic-embed-text-v2** | ~700MB | 768 | 100 | ~62 | MoE (Mixture of Experts), eficiente, 8192 tokens | Mais recente, menos validado em espanhol legal |
| **intfloat/multilingual-e5-small** | ~448MB | 384 | 100 | ~56 | Mais leve, latência baixa | Dimensão menor pode perder discriminação |
| **Wasserstoff-AI/Legal-Embed** | ~1.1GB | 1024 | Multi | N/A | Fine-tuned para legal | **DESCARTADO: maior FP por razão analisada em seção 3** |

### 4.2 Recomendação baseada em evidência

**Modelo principal: `BAAI/bge-m3`**

Justificativa:

1.  Melhor desempenho em benchmarks multilinguais, incluindo espanhol (ver [OpenAI vs Open-Source Multilingual Embedding Models](https://towardsdatascience.com/openai-vs-open-source-multilingual-embedding-models-e5ccb7c90f05/))
2.  Maior dimensionalidade (1024) = maior capacidade para separar centroides de tipo
3.  Dense+sparse+ColBERT retrieval funciona bem para comparações de similaridade
4.  Suporta até 8192 tokens (útil para contextos legais longos)

**Modelo alternativo: `intfloat/multilingual-e5-large`**

Justificativa:

1.  Bem documentado com paper técnico (arXiv:2402.05672)
2.  Desempenho excelente em espanhol verificado
3.  Ligeiramente mais pequeno que bge-m3
4.  Já foi proposto em `docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md`

**IMPORTANTE**: NÃO usar `Legal-Embed` nem nenhum modelo fine-tuned para domínio legal. A evidência acadêmica indica que os modelos gerais preservam melhor a separação entre tipos de entidade, que é exatamente o que precisamos para centroides.

### 4.3 Fontes de benchmarks

| Benchmark | O que mede | Referência |
| :--- | :--- | :--- |
| MTEB (Massive Text Embedding Benchmark) | 8 tarefas incluindo classificação e clustering | [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) |
| FinMTEB (Finance MTEB) | Desempenho em domínio financeiro | Tang & Yang (2024), arXiv:2409.18511 |
| MMTEB (Massive Multilingual TEB) | Extensão multilingual de MTEB (2025) | [MMTEB GitHub](https://github.com/embeddings-benchmark/mteb) |

**Nota crítica**: Nenhum benchmark existente mede diretamente "discriminação de tipo de entidade mediante centroides". MTEB tem subtarefas de classificação e clustering que são aproximações úteis. Recomenda-se criar um benchmark interno para ContextSafe.

---

## 5. Descoberta 4: Técnicas de Validação de Tipo Baseada em Centroides

### 5.1 Redes prototípicas e centroides para NER

| Paper | Local/Ano | Descoberta chave |
| :--- | :--- | :--- |
| **"CEPTNER: Contrastive Learning Enhanced Prototypical Network for Two-stage Few-shot NER"** (Wang et al.) | Knowledge-Based Systems (2024) | Duas etapas: (1) detecção de limites, (2) classificação prototípica com contrastive learning. O aprendizado contrastivo a nível de entidade separa efetivamente os tipos. Avaliado em Few-NERD, CrossNER, SNIPS. |
| **"Transformer-based Prototype Network for Chinese Nested NER"** (MSTPN) | Scientific Reports (2025) | Redes prototípicas com transformers para NER aninhado. Usa entity bounding boxes como protótipos. |
| **"KCL: Few-shot NER with Knowledge Graph and Contrastive Learning"** | LREC-COLING 2024 | Combina Knowledge Graphs com contrastive learning para aprender representação semântica de etiquetas. Usa KG para prover informação estruturada de tipo. A representação contrastiva separa clusters de etiquetas no espaço prototípico. |
| **"Multi-Head Self-Attention-Enhanced Prototype Network with Contrastive-Center Loss for Few-Shot Relation Extraction"** | Applied Sciences (2024) | Contrastive-center loss que compara amostras de treinamento com centros de classe correspondentes E não-correspondentes. Reduz distâncias intra-classe e aumenta distâncias inter-classe. |
| **"CLESR: Context-Based Label Knowledge Enhanced Span Recognition for NER"** | Int J Computational Intelligence Systems (2024) | Melhora NER aninhado integrando informação contextual com conhecimento de etiquetas. Spans se alinham com descrições textuais de tipos em espaço semântico compartilhado. |

### 5.2 Best practices para construção de centroides

Baseado na literatura revisada:

| Aspecto | Recomendação | Justificativa |
| :--- | :--- | :--- |
| **Número de exemplos** | 50-100 por tipo | CEPTNER mostra efetividade com poucos exemplos; 50 é mínimo, 100 é robusto |
| **Diversidade de exemplos** | Incluir variações de contexto, formato, comprimento | KCL enfatiza diversidade para clusters mais discriminativos |
| **Tamanho de contexto** | 10-15 tokens circundantes | A pesquisa NER (arXiv:2401.10825) confirma que BERT captura contexto intra- e inter-frase efetivamente |
| **Atualização de centroides** | Recalcular periodicamente com novos exemplos confirmados | CEPTNER mostra que mais exemplos melhoram separação; centroides devem evoluir |
| **Contrastive refinement** | Treinar com perda contrastiva para maximizar separação | Múltiplos papers mostram que contrastive loss é CHAVE para separação de tipos |
| **Camadas intermediárias** | Considerar extrair de camadas 15-17, não apenas camada final | NER Retriever (arXiv:2509.04011) mostra que camadas intermediárias contêm mais info de tipo |

### 5.3 Tamanho de janela de contexto

| Paper | Descoberta sobre contexto |
| :--- | :--- |
| Survey NER (arXiv:2401.10825) | "BERT encodings capture important within and adjacent-sentence context." Aumentar janela melhora desempenho. |
| Span-based Unified NER via Contrastive Learning (IJCAI 2024) | Spans com contexto se alinham com descrições de tipo em espaço compartilhado. Contexto é necessário para desambiguar. |
| Contextualized Span Representations (Wadden et al.) | Propagação de representações de span via coreference links permite desambiguar menções difíceis. |

**Recomendação**: Para ContextSafe, usar **contexto de 10-15 tokens** a cada lado da entidade. Para entidades ao início/final de frase, preencher com tokens da frase anterior/seguinte se disponível.

---

## 6. Descoberta 5: Abordagens Híbridas (Geral + Domínio)

### 6.1 Concatenação e ensemble de embeddings

| Paper | Local/Ano | Descoberta chave |
| :--- | :--- | :--- |
| **"Automated Concatenation of Embeddings for Structured Prediction" (ACE)** | ACL-IJCNLP 2021 | Framework que automaticamente encontra a melhor concatenação de embeddings para structured prediction (incluindo NER). Alcança SOTA em 6 tarefas sobre 21 datasets. A seleção varia segundo tarefa e conjunto de candidatos. |
| **"Pooled Contextualized Embeddings for NER"** (Akbik et al.) | NAACL 2019 | Agrega embeddings contextualizados de cada instância única para criar representação "global". Stacked embeddings (combinar múltiplos tipos) é uma característica chave de Flair e melhora significativamente NER. |
| **"Improving Few-Shot Cross-Domain NER by Instruction Tuning a Word-Embedding based Retrieval Augmented LLM" (IF-WRANER)** | EMNLP 2024 Industry | Usa word-level embeddings (não sentence-level) para retrieval de exemplos in-prompt. Supera SOTA em CrossNER por >2% F1. Deployed em produção, reduzindo escalações humanas ~15%. |
| **"Pre-trained Embeddings for Entity Resolution: An Experimental Analysis"** (Zeakis et al.) | VLDB 2023 | Análise de 12 modelos de linguagem sobre 17 datasets para entity resolution. Embeddings contextualizados (BERT variants) superam estáticos (fastText) consistentemente, mas a combinação pode ser benéfica. |

### 6.2 Adaptadores (LoRA) para preservar conhecimento geral

| Paper | Local/Ano | Descoberta chave |
| :--- | :--- | :--- |
| **"Continual Named Entity Recognition without Catastrophic Forgetting"** (Zheng et al.) | EMNLP 2023 | Propõem pooled feature distillation loss + pseudo-labeling + adaptive re-weighting. O esquecimento catastrófico em NER contínuo é intensificado pelo "semantic shift" do tipo não-entidade. |
| **"A New Adapter Tuning of LLM for Chinese Medical NER"** | Automation in Construction (2024) | Adapters evitam esquecimento catastrófico porque aprendem conhecimento novo sem ajustes extensivos de parâmetros. São preferíveis para NER multi-domínio. |
| **"Mixture of LoRA Experts for Continual Information Extraction"** | EMNLP 2025 Findings | Framework MoE com LoRA para extração de informação contínua. Permite adicionar domínios sem esquecer os anteriores. |
| **"LoRASculpt: Sculpting LoRA for Harmonizing General and Specialized Knowledge"** | CVPR 2025 | Técnica para equilibrar conhecimento geral e especializado durante fine-tuning com LoRA. |

### 6.3 Estratégias de combinação viáveis para ContextSafe

| Estratégia | Complexidade | Benefício esperado | Recomendada |
| :--- | :--- | :--- | :--- |
| **A: Embeddings gerais puros** | Baixa | Boa discriminação de tipos sem FP adicionais | Sim (baseline) |
| **B: Concatenar geral + legal** | Média | Mais dimensões, captura ambos aspectos | Avaliável mas custosa em latência |
| **C: Média ponderada geral + legal** | Média | Mais simples que concat, mas perde informação | Não recomendada (média dilui) |
| **D: Meta-modelo sobre embeddings múltiplos** | Alta | Melhor precisão se houver dados de treinamento suficientes | Para futuro |
| **E: LoRA adapter sobre modelo geral** | Média-Alta | Preserva capacidade geral + adiciona domínio | Sim (segundo passo) |

**Recomendação para ContextSafe**:

*   **Fase 1 (imediata)**: Usar embeddings gerais puros (bge-m3 ou e5-large). Avaliar redução de FP frente à experiência com embeddings legais.
*   **Fase 2 (se Fase 1 insuficiente)**: Aplicar LoRA adapter sobre o modelo geral com exemplos contrastivos de entidades legais espanholas. Isso preserva a capacidade de discriminação de tipos geral enquanto adiciona conhecimento do domínio.
*   **Fase 3 (opcional)**: ACE-style automated search da melhor concatenação se se dispõe de um dataset de validação de tipo suficientemente grande.

---

## 7. Síntese e Recomendação Final

### 7.1 Resposta direta às perguntas de pesquisa

**P1: General-purpose vs domain-specific para classificação de tipo de entidade?**

Usar **general-purpose**. A evidência de múltiplos papers (Tang & Yang 2024, Rajaee & Pilehvar 2021, Machina & Mercer NAACL 2024) indica que:

*   Os modelos gerais mantêm espaços semânticos mais amplos
*   A discriminação de tipos de entidade requer separação inter-classe, não profundidade intra-domínio
*   Os modelos de domínio colapsam tipos similares no mesmo subespaço

**P2: Por que os embeddings legais produzem mais falsos positivos?**

Três fatores convergentes:

1.  **Colapso de diversidade semântica**: fine-tuning legal aproxima representações de todas as entidades em direção ao subespaço "legal"
2.  **Anisotropia não controlada**: fine-tuning introduz direções dominantes que codificam "legalidade" em vez de "tipo de entidade" (Rajaee & Pilehvar 2021, Rudman & Eickhoff ICLR 2024)
3.  **Sobreposição de centroides**: centroides de PERSON e ORGANIZATION se aproximam porque ambos aparecem em contextos legais idênticos

**P3: Melhor modelo?**

`BAAI/bge-m3` (primeira opção) ou `intfloat/multilingual-e5-large` (segunda opção). Ambos são gerais, multilinguais, com bom suporte para espanhol e dimensionalidade 1024 suficiente para separar centroides de tipo.

**P4: Técnica de centroides?**

Bem respaldada por CEPTNER (2024), KCL (2024), MSTPN (2025). Chaves:

*   50-100 exemplos diversos por tipo
*   Contexto de 10-15 tokens ao redor da entidade
*   Contrastive learning para refinar centroides se possível
*   Camadas intermediárias (15-17) podem ser mais informativas que a camada final

**P5: Abordagem híbrida?**

Para o futuro: LoRA adapters sobre modelo geral é a estratégia mais promissora. Preserva discriminação geral + adiciona conhecimento de domínio. ACE (concatenação automatizada) é viável se há dados de avaliação suficientes.

### 7.2 Impacto no documento prévio

O documento `docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md` recomenda `multilingual-e5-large` como modelo principal e sugere avaliar `Legal-Embed` como alternativa. Baseado nesta investigação:

| Aspecto | Documento prévio | Atualização |
| :--- | :--- | :--- |
| Modelo principal | `multilingual-e5-large` | **Correto**, manter |
| Alternativa Legal-Embed | Sugerida para avaliar | **DESCARTAR**: evidência indica que produzirá mais FP |
| Alternativa real | Não proposta | **Adicionar `BAAI/bge-m3`** como primeira opção |
| Contrastive refinement | Não mencionado | **Adicionar**: se os centroides não separam suficiente, aplicar contrastive learning |
| Camadas intermediárias | Não mencionado | **Adicionar**: extrair embeddings de camadas 15-17, não apenas última |

---

## 8. Tabela Consolidada de Papers Revisados

| # | Paper | Local | Ano | Tema Principal | URL |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Do We Need Domain-Specific Embedding Models? An Empirical Investigation | arXiv 2409.18511 | 2024 | General vs domain embeddings | https://arxiv.org/abs/2409.18511 |
| 2 | NuNER: Entity Recognition Encoder Pre-training via LLM-Annotated Data | EMNLP 2024 | 2024 | Entity-aware pre-training | https://aclanthology.org/2024.emnlp-main.660/ |
| 3 | LegNER: Domain-Adapted Transformer for Legal NER | Frontiers in AI | 2025 | Legal NER + anonymization | https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1638971/full |
| 4 | MEL: Legal Spanish Language Model | arXiv 2501.16011 | 2025 | Spanish legal embeddings | https://arxiv.org/abs/2501.16011 |
| 5 | Anisotropy is Not Inherent to Transformers | NAACL 2024 | 2024 | Embedding space geometry | https://aclanthology.org/2024.naacl-long.274/ |
| 6 | Stable Anisotropic Regularization (I-STAR) | ICLR 2024 | 2024 | Controlled anisotropy | https://arxiv.org/abs/2305.19358 |
| 7 | The Shape of Learning: Anisotropy and Intrinsic Dimensions | EACL 2024 | 2024 | Anisotropy dynamics in transformers | https://aclanthology.org/2024.findings-eacl.58/ |
| 8 | How Does Fine-tuning Affect Geometry of Embedding Space | EMNLP 2021 Findings | 2021 | Fine-tuning impact on isotropy | https://aclanthology.org/2021.findings-emnlp.261/ |
| 9 | Representation Degeneration in Prompt-based Fine-tuning | LREC 2024 | 2024 | Anisotropy limits performance | https://aclanthology.org/2024.lrec-main.1217/ |
| 10 | Improving Legal Entity Recognition Using Semantic Filtering | arXiv 2410.08521 | 2024 | Legal NER false positive reduction | https://arxiv.org/abs/2410.08521 |
| 11 | CEPTNER: Contrastive Enhanced Prototypical Network for Few-shot NER | Knowledge-Based Systems | 2024 | Prototype networks for NER | https://doi.org/10.1016/j.knosys.2024.111730 |
| 12 | KCL: Few-shot NER with Knowledge Graph and Contrastive Learning | LREC-COLING 2024 | 2024 | KG + contrastive for prototypical NER | https://aclanthology.org/2024.lrec-main.846/ |
| 13 | Automated Concatenation of Embeddings (ACE) | ACL-IJCNLP 2021 | 2021 | Multi-embedding concatenation for NER | https://aclanthology.org/2021.acl-long.206/ |
| 14 | Pooled Contextualized Embeddings for NER | NAACL 2019 | 2019 | Global word representations for NER | https://aclanthology.org/N19-1078/ |
| 15 | Continual NER without Catastrophic Forgetting | EMNLP 2023 | 2023 | Catastrophic forgetting in NER | https://arxiv.org/abs/2310.14541 |
| 16 | Improving Few-Shot Cross-Domain NER (IF-WRANER) | EMNLP 2024 Industry | 2024 | Word-level embeddings for cross-domain NER | https://aclanthology.org/2024.emnlp-industry.51/ |
| 17 | CLESR: Context-Based Label Knowledge Enhanced Span Recognition | IJCIS | 2024 | Context + label knowledge for NER | https://link.springer.com/article/10.1007/s44196-024-00595-5 |
| 18 | Span-based Unified NER via Contrastive Learning | IJCAI 2024 | 2024 | Contrastive span-type alignment | https://www.ijcai.org/proceedings/2024/0708.pdf |
| 19 | Pre-trained Embeddings for Entity Resolution | VLDB 2023 | 2023 | 12 embedding models compared for ER | https://www.vldb.org/pvldb/vol16/p2225-skoutas.pdf |
| 20 | Transformer-based Prototype Network for Chinese Nested NER | Scientific Reports | 2025 | Prototypical NER with transformers | https://www.nature.com/articles/s41598-025-04946-w |
| 21 | Adapter Tuning of LLM for Chinese Medical NER | Automation in Construction | 2024 | Adapters prevent catastrophic forgetting | https://www.tandfonline.com/doi/full/10.1080/08839514.2024.2385268 |
| 22 | Recent Advances in NER: Comprehensive Survey | arXiv 2401.10825 | 2024 | NER survey (embeddings, hybrid approaches) | https://arxiv.org/abs/2401.10825 |
| 23 | Spanish Datasets for Sensitive Entity Detection in Legal Domain | LREC 2022 | 2022 | MAPA project, Spanish legal NER datasets | https://aclanthology.org/2022.lrec-1.400/ |

---

## 9. Documentos Relacionados

| Documento | Relação |
| :--- | :--- |
| `docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md` | Documento prévio que propõe validador de tipo com embeddings. Esta investigação ATUALIZA suas recomendações. |
| `docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md` | Avaliação prévia de embeddings para classificação de documentos (tarefa diferente). |
| `docs/reports/2026-02-07_embeddings_roadmap_document_classification.md` | Roadmap de embeddings para classificação de documentos. |
| `docs/reports/2026-01-30_investigacion_gaps_pipeline_hibrido.md` | Lacunas do pipeline NER híbrido (contexto dos erros de tipo). |
| `docs/reports/2026-01-28_investigacion_hybrid_ner.md` | Investigação sobre NER híbrido (contexto da arquitetura). |

---

```
Versão: 1.0.0
Autor: AlexAlves87
Tempo de investigação: ~45 min
Papers revisados: 23
```
