# Investigação: Embeddings Generalistas vs Legais para Desambiguação de Tipos de Entidade

**Data:** 07-02-2026
**Objetivo:** Determinar se devemos usar embeddings generalistas (multilingual-e5-large) ou especializados em legal (Legal-Embed, voyage-law-2) para o validador pós-NER de tipos de entidade no ContextSafe.

---

## 1. Resumo Executivo

1.  **Descoberta principal**: Os embeddings legais são otimizados para **retrieval** (buscar documentos similares), NÃO para **discriminação de tipos de entidade**. Isso explica os falsos positivos observados.
2.  **Recomendação**: Usar **embeddings generalistas** (`intfloat/multilingual-e5-large`) para desambiguação de tipos de entidade. Os legais podem causar colapso do espaço semântico onde PERSON e ORGANIZATION ficam muito próximos.
3.  **Evidência chave**: O fine-tuning de domínio pode causar "over-specialization" que reduz a capacidade de discriminação entre categorias (esquecimento catastrófico de fronteiras entre tipos).
4.  **Alternativa híbrida**: Se for necessário conhecimento legal, usar abordagem em duas etapas: generalista para tipo + legal para validação de entidade específica.
5.  **Redução de erros esperada**: 4-5% com embeddings generalistas bem calibrados (literatura: WNUT17, NER Retriever).

---

## 2. Literatura Revisada

### 2.1 Generalistas vs Específicos de Domínio

| Paper/Fonte | Local/Ano | Descoberta Relevante |
| :--- | :--- | :--- |
| "Do we need domain-specific embedding models?" | arXiv:2409.18511 (2024) | Em finanças (FinMTEB), modelos gerais degradam vs específicos. MAS: isso é para **retrieval**, não classificação de tipos. |
| "How Does Fine-tuning Affect the Geometry of Embedding Space?" | ACL Findings 2021 | Fine-tuning de domínio **reduz a separação** entre classes no espaço de embeddings. Clusters colapsam. |
| "Is Anisotropy Really the Cause of BERT Embeddings not Working?" | EMNLP Findings 2022 | Anisotropia (embeddings concentrados em cone estreito) é problema conhecido. Fine-tuning de domínio **piora** isso. |
| "Dynamic Expert Specialization: Catastrophic Forgetting-Free Multi-Domain MoE" | EMNLP 2025 | Esquecimento catastrófico ocorre em fine-tuning de domínio. Modelos esquecem fronteiras aprendidas previamente. |
| "Continual Named Entity Recognition without Catastrophic Forgetting" | arXiv:2310.14541 (2023) | NER contínuo sofre esquecimento catastrófico: tipos antigos se "consolidam" em non-entity. Análogo ao nosso problema. |

### 2.2 Por Que Embeddings Legais Causam Falsos Positivos

| Fenômeno | Explicação | Fonte |
| :--- | :--- | :--- |
| **Colapso de espaço semântico** | Fine-tuning legal otimiza para que documentos legais similares estejam próximos, NÃO para separar PERSON de ORGANIZATION | Weaviate Blog, MongoDB Fine-Tuning Guide |
| **Over-specialization** | "Treinamento excessivamente restrito pode tornar o modelo fine-tuned muito especializado" - perde capacidade de discriminação geral | [Weaviate](https://weaviate.io/blog/fine-tune-embedding-model) |
| **Contrastive loss orientado a retrieval** | voyage-law-2 usa "pares positivos especificamente projetados" para retrieval legal, não para classificação de entidades | [Voyage AI Blog](https://blog.voyageai.com/2024/04/15/domain-specific-embeddings-and-retrieval-legal-edition-voyage-law-2/) |
| **Terminologia legal uniforme** | Em textos legais, "Garcia" pode ser demandante, advogado, ou nome de escritório. O modelo legal os incorpora **perto** porque todos são legais | Observação empírica do usuário |

### 2.3 Centroides e Classificação Baseada em Protótipos

| Paper/Fonte | Local/Ano | Descoberta Relevante |
| :--- | :--- | :--- |
| "NER Retriever: Zero-Shot NER with Type-Aware Embeddings" | arXiv:2509.04011 (2025) | Camadas intermediárias (layer 17) melhor que saídas finais para tipo. MLP com contrastive loss para separar tipos. |
| "CEPTNER: Contrastive Learning Enhanced Prototypical Network" | KBS (2024) | Redes prototípicas com 50-100 exemplos por tipo são suficientes para centroides robustos. |
| "ReProCon: Scalable Few-Shot Biomedical NER" | arXiv:2508.16833 (2025) | Múltiplos protótipos por categoria melhoram representação de entidades heterogêneas. |
| "Mastering Intent Classification with Embeddings: Centroids" | Medium (2024) | Centroides têm "tempo de treinamento mais rápido" e precisão decente. Perfeitos para atualizações rápidas. |

### 2.4 Benchmarks de Modelos de Embedding

| Modelo | Tamanho | Idiomas | MTEB Avg | Vantagem | Desvantagem |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `intfloat/multilingual-e5-large` | 1.1GB | 100 | ~64 | Melhor multilingual geral, excelente espanhol | Requer prefixo "query:" |
| `intfloat/multilingual-e5-large-instruct` | 1.1GB | 100 | ~65 | Suporta instruções, mais flexível | Ligeiramente mais lento |
| `BAAI/bge-m3` | 1.5GB | 100+ | ~66 | Híbrido dense+sparse, 8192 tokens | Mais complexo de usar |
| `voyage-law-2` | API | EN | ~72 (legal) | Melhor para retrieval legal | API comercial, apenas inglês |
| `Legal-Embed (Wasserstoff)` | 1.1GB | Multi | N/A | Fine-tuned em legal | **Provavelmente causa FPs em classificação** |

---

## 3. Análise: Por Que Generalistas São Melhores para Tipo de Entidade

### 3.1 Objetivo de Treinamento Diferente

| Embeddings Legais | Embeddings Generalistas |
| :--- | :--- |
| Otimizados para: "documento A similar a documento B" | Otimizados para: "texto A semanticamente relacionado com texto B" |
| Pares positivos: fragmentos do mesmo documento legal | Pares positivos: paráfrases, traduções, variantes |
| Resultado: tudo o que é legal está junto | Resultado: tipos semânticos separados |

**Consequência**: Em embeddings legais, "Alejandro Alvarez" (advogado) e "Bufete Alvarez S.L." (empresa) estão **perto** porque ambos são legais. Em generalistas, estão **longe** porque um é pessoa e outro é organização.

### 3.2 Evidência de Anisotropia Agravada

O paper de ACL Findings 2021 demonstra que:

1.  Fine-tuning **reduz a variância** do espaço de embeddings
2.  Os clusters de tipos diferentes **se aproximam**
3.  A separabilidade linear **diminui**

Isso explica diretamente os falsos positivos: quando todos os embeddings legais colapsam em direção a uma região, a distância cosseno perde poder discriminativo.

### 3.3 Tarefa vs Domínio

| Aspecto | Embeddings de Domínio (Legal) | Embeddings de Tarefa (Tipo) |
| :--- | :--- | :--- |
| Pergunta que respondem | "Este texto é legal?" | "Isto é uma pessoa ou empresa?" |
| Treinamento | Corpus legal | Contrastivo por tipo de entidade |
| Utilidade para validação tipo NER | Baixa | Alta |

Nosso problema é de **tarefa** (classificar tipo), não de **domínio** (identificar textos legais).

---

## 4. Recomendação para ContextSafe

### 4.1 Abordagem Recomendada: Generalista Puro

```
Pipeline:
  NER → Detecções com tipo atribuído
    ↓
  EntityTypeValidator (multilingual-e5-large)
    ↓
  Para cada entidade:
    1. Incorporar "query: [entidade + contexto ±10 tokens]"
    2. Comparar vs centroides por tipo (PERSON_NAME, ORGANIZATION, DATE, LOCATION)
    3. Decisões:
       - Se melhor_centroide ≠ tipo_NER AND similaridade > 0.75 AND margem > 0.10 → RECLASSIFICAR
       - Se margem < 0.05 → FLAG HITL
       - Senão → MANTER tipo NER
```

**Modelo**: `intfloat/multilingual-e5-large` (1.1GB)

**Justificativa**:

*   Treinado em 100 idiomas incluindo espanhol
*   NÃO superespecializado em nenhum domínio
*   Preserva separação semântica entre PERSON/ORGANIZATION/DATE/LOCATION
*   Já recomendado em pesquisa prévia (ver `2026-02-07_embeddings_entity_type_disambiguation.md`)

### 4.2 Abordagem Alternativa: Híbrida (Se Necessário Conhecimento Legal)

```
Etapa 1: Classificação de tipo (GENERALISTA)
  multilingual-e5-large → Tipo de entidade

Etapa 2: Validação de entidade legal (LEGAL, opcional)
  voyage-law-2 ou Legal-Embed → "Esta entidade é válida em contexto legal?"
  (Apenas para casos sinalizados como duvidosos)
```

**Quando usar híbrido**: Se houver entidades legais específicas (ex: "artigo 24.2 CE", "Lei 13/2022") que requerem validação de conhecimento legal.

Para ContextSafe (PII genérico), a abordagem generalista pura é suficiente.

### 4.3 Configuração de Centroides

| Tipo | Exemplos Necessários | Estratégia de Contexto |
| :--- | :--- | :--- |
| PERSON_NAME | 100 | "query: O advogado [NOME] compareceu..." |
| ORGANIZATION | 100 | "query: A empresa [ORG] interpôs recurso..." |
| DATE | 50 | "query: Com data [DATA] foi proferida sentença..." |
| LOCATION | 50 | "query: Na cidade de [LUGAR] celebrou-se..." |
| DNI_NIE | 30 | "query: com DNI [NÚMERO]" (contexto curto, padrão fixo) |

**Contexto**: ±10 tokens ao redor da entidade. Nem muito curto (perde contexto) nem muito longo (introduz ruído).

---

## 5. Experimento Proposto

### 5.1 Comparação A/B

| Condição | Modelo | Esperado |
| :--- | :--- | :--- |
| A (Baseline) | Sem validador | Pass rate atual: 60% |
| B (Generalista) | `multilingual-e5-large` | Pass rate esperado: 64-65% |
| C (Legal) | `Legal-Embed-intfloat-multilingual-e5-large-instruct` | Pass rate esperado: < 60% (mais FPs) |

### 5.2 Métricas a Avaliar

1.  **Pass rate em teste adversarial** (35 testes existentes)
2.  **Precisão de reclassificação**: % de reclassificações corretas
3.  **Taxa de falsos positivos**: Entidades corretamente tipadas que foram mal reclassificadas
4.  **Latência adicional**: ms por entidade validada

### 5.3 Casos de Teste Específicos

Baseados em erros de auditoria.md (ver `2026-02-07_embeddings_entity_type_disambiguation.md`, seção 6):

| Entidade | Tipo NER | Tipo Correto | Modelo Esperado OK |
| :--- | :--- | :--- | :--- |
| "Alejandro Alvarez" | ORGANIZATION | PERSON_NAME | Generalista |
| "10/10/2025" | ORGANIZATION | DATE | Generalista |
| "Pura" | LOCATION | PERSON_NAME | Generalista |
| "Finalmente" | ORGANIZATION | NÃO É PII | Generalista (baixa similaridade com todos) |
| "Whatsapp" | PERSON | ORGANIZATION/PLATFORM | Generalista |

---

## 6. Riscos e Mitigações

| Risco | Probabilidade | Mitigação |
| :--- | :--- | :--- |
| Generalista também não discrimina bem PERSON/ORG em espanhol legal | Média | Avaliar antes de implementar; se falhar, treinar centroides com contrastive loss |
| Latência inaceitável (>100ms/entidade) | Baixa | Batch processing, cache de embeddings frequentes |
| Centroides requerem mais de 100 exemplos | Baixa | Aumentar para 200 se F1 < 0.90 em validação |
| Modelo de 1.1GB não cabe em produção | Baixa | Quantizar para INT8 (~300MB) ou usar e5-base (560MB) |

---

## 7. Conclusão

**Os embeddings legais são otimizados para a tarefa errada.** Seu objetivo (retrieval de documentos similares) faz com que entidades de diferentes tipos mas do mesmo domínio (legal) fiquem incorporadas perto, reduzindo a capacidade de discriminação.

Para desambiguação de tipos de entidade, os **embeddings generalistas** preservam melhor as fronteiras semânticas entre PERSON, ORGANIZATION, DATE, etc., porque não foram "colapsados" em direção a um domínio específico.

**Recomendação final**: Implementar validador com `intfloat/multilingual-e5-large` e avaliar empiricamente antes de considerar alternativas legais.

---

## 8. Próximos Passos

1.  [ ] Baixar `intfloat/multilingual-e5-large` (~1.1GB)
2.  [ ] Construir dataset de exemplos por tipo (PERSON_NAME, ORGANIZATION, DATE, LOCATION) com contexto legal
3.  [ ] Calcular centroides para cada tipo
4.  [ ] Implementar `EntityTypeValidator` com limiares configuráveis
5.  [ ] Avaliar em teste adversarial (35 testes)
6.  [ ] (Opcional) Comparar vs `Legal-Embed` para confirmar hipótese de falsos positivos
7.  [ ] Documentar resultados e decisão final

---

## Documentos Relacionados

| Documento | Relação |
| :--- | :--- |
| `ml/docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md` | Pesquisa prévia, arquitetura proposta |
| `ml/docs/reports/2026-02-07_embeddings_roadmap_document_classification.md` | Roteiro embeddings, critérios de ativação |
| `ml/docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | Pipeline atual, métricas baseline |
| `auditoria.md` | Erros de classificação identificados |
| `ml/models/type_centroids.json` | Centroides existentes (requer verificar modelo usado) |

---

## Referências

1.  **FinMTEB**: Li et al. (2024). "Do we need domain-specific embedding models? An empirical investigation." arXiv:2409.18511. https://arxiv.org/abs/2409.18511
2.  **Geometry of Fine-tuning**: Merchant et al. (2020). "What Happens To BERT Embeddings During Fine-tuning?" ACL Findings 2021. https://aclanthology.org/2021.findings-emnlp.261.pdf
3.  **Anisotropy**: Ethayarajh (2019). "How Contextual are Contextualized Word Representations?" EMNLP 2019. Rajaee & Pilehvar (2022). "Is Anisotropy Really the Cause?" EMNLP Findings 2022. https://aclanthology.org/2022.findings-emnlp.314.pdf
4.  **Catastrophic Forgetting in NER**: Wang et al. (2023). "Continual Named Entity Recognition without Catastrophic Forgetting." arXiv:2310.14541. https://arxiv.org/abs/2310.14541
5.  **DES-MoE**: Yang et al. (2025). "Dynamic Expert Specialization: Catastrophic Forgetting-Free Multi-Domain MoE." EMNLP 2025. https://aclanthology.org/2025.emnlp-main.932.pdf
6.  **NER Retriever**: Zhang et al. (2025). "NER Retriever: Zero-Shot NER with Type-Aware Embeddings." arXiv:2509.04011. https://arxiv.org/abs/2509.04011
7.  **CEPTNER**: Wang et al. (2024). "Contrastive learning Enhanced Prototypical network for Few-shot NER." Knowledge-Based Systems. https://doi.org/10.1016/j.knosys.2024.111512
8.  **ReProCon**: Liu et al. (2025). "ReProCon: Scalable Few-Shot Biomedical NER." arXiv:2508.16833. https://arxiv.org/abs/2508.16833
9.  **Multilingual E5**: Wang et al. (2024). "Multilingual E5 Text Embeddings." arXiv:2402.05672. https://huggingface.co/intfloat/multilingual-e5-large
10. **voyage-law-2**: Voyage AI (2024). "Domain-Specific Embeddings: Legal Edition." https://blog.voyageai.com/2024/04/15/domain-specific-embeddings-and-retrieval-legal-edition-voyage-law-2/
11. **Fine-tuning Trade-offs**: Weaviate (2024). "Why, When and How to Fine-Tune a Custom Embedding Model." https://weaviate.io/blog/fine-tune-embedding-model
12. **Intent Classification with Centroids**: Puig (2024). "Mastering Intent Classification with Embeddings." Medium. https://medium.com/@mpuig/mastering-intent-classification-with-embeddings-centroids-neural-networks-and-random-forests-3fe7c57ca54c

---

```
Versão: 1.0.0
Autor: AlexAlves87
Tempo de pesquisa: ~25 min
Tokens de busca: 12 queries
```
