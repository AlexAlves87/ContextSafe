# Pesquisa: Embeddings para Desambiguação de Tipos de Entidade em NER

**Data:** 07-02-2026
**Objetivo:** Resolver erros de classificação de tipo de entidade no sistema NER do ContextSafe (ex: "Alejandro Alvarez" classificado como ORGANIZATION em vez de PERSON_NAME)

---

## 1. Resumo Executivo

1. **Problema identificado**: O modelo NER atual confunde tipos de entidade, classificando nomes de pessoas como organizações, datas como organizações e palavras comuns capitalizadas como PII.

2. **Solução proposta**: Validador pós-NER baseado em embeddings que compara cada detecção contra centroides semânticos por tipo de entidade.

3. **Modelo recomendado**: `intfloat/multilingual-e5-large` (1.1GB) com possível upgrade para `Legal-Embed` para domínio jurídico.

4. **Técnica principal**: Classificação baseada em centroides com limiar de reclassificação (threshold 0.75, margem 0.1).

5. **Redução de erros esperada**: ~4.5% segundo a literatura (benchmark WNUT17).

---

## 2. Literatura Revisada

| Paper | Local | Ano | Descoberta Relevante |
|-------|-------|-----|----------------------|
| NER Retriever: Zero-Shot Named Entity Retrieval with Type-Aware Embeddings | arXiv (2509.04011) | 2025 | Camadas intermediárias (camada 17) capturam melhor informações de tipo do que saídas finais. MLP com perda contrastiva atinge zero-shot em tipos não vistos. |
| CEPTNER: Contrastive Learning Enhanced Prototypical Network for Few-shot NER | Knowledge-Based Systems (ScienceDirect) | 2024 | Redes prototípicas com aprendizado contrastivo separam efetivamente tipos de entidade com poucos exemplos (50-100). |
| Recent Advances in Named Entity Recognition: A Comprehensive Survey | arXiv (2401.10825) | 2024 | Abordagens híbridas (regras + ML + embeddings) superam consistentemente modelos únicos. |
| Redundancy-Enhanced Framework for Error Correction in NER | OpenReview | 2025 | Pós-processador com refinador Transformer + embeddings de tag de entidade atinge redução de erros de 4.48% no WNUT17. |
| Multilingual E5 Text Embeddings: A Technical Report | arXiv (2402.05672) | 2024 | Modelo multilingual-e5-large suporta 100 idiomas com excelente desempenho em espanhol. Requer prefixo "query:" para embeddings de busca. |

---

## 3. Melhores Práticas Identificadas

1. **Incluir contexto**: Incorporar a entidade COM seu contexto circundante (10-15 palavras) melhora significativamente a desambiguação.

2. **Usar camadas intermediárias**: Representações de camadas médias (camada 15-17) contêm mais informações de tipo do que as saídas finais.

3. **Aprendizado contrastivo**: Treinar com perda contrastiva separa melhor os tipos no espaço de embeddings.

4. **Limiar com margem**: Não reclassificar apenas por maior similaridade; exigir margem mínima (>0.1) para evitar falsos positivos.

5. **Exemplos por tipo**: 50-100 exemplos confirmados por categoria são suficientes para construir centroides robustos.

6. **Domínio específico**: Modelos ajustados (fine-tuned) para o domínio (jurídico no nosso caso) melhoram o desempenho.

7. **Sinalização para HITL**: Quando similaridades são próximas (<0.05 diferença), marcar para revisão humana em vez de reclassificar automaticamente.

---

## 4. Recomendação para ContextSafe

### 4.1 Arquitetura Proposta

```
┌─────────────────────────────────────────────────────────────────┐
│                    Pipeline NER Atual                           │
│  (RoBERTa + SpaCy + Regex → Merge Inteligente)                  │
60 └─────────────────────┬───────────────────────────────────────────┘
                      │ Detecções com tipo atribuído
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              Entity Type Validator (NOVO)                        │
│                                                                  │
│  1. Extrair entidade + contexto (±15 tokens)                    │
│  2. Gerar embedding com multilingual-e5-large                   │
│  3. Calcular similaridade cosseno com centroides por tipo       │
│  4. Decisão:                                                    │
│     - Se melhor_tipo ≠ tipo_NER E similaridade > 0.75           │
│       E margem > 0.1 → RECLASSIFICAR                            │
│     - Se margem < 0.05 → MARCAR PARA HITL                       │
│     - Caso contrário → MANTER tipo NER                          │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Detecções validadas/corrigidas
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Glossário & Anonimização                         │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Modelo Selecionado

**Principal**: `intfloat/multilingual-e5-large`
- Tamanho: 1.1GB
- Idiomas: 100 (excelente espanhol)
- Latência: ~50-100ms por embedding
- Requer prefixo "query:" para embeddings

**Alternativa (avaliar)**: `Wasserstoff-AI/Legal-Embed-intfloat-multilingual-e5-large-instruct`
- Fine-tuned para domínio jurídico
- Mesmo tamanho base
- Potencialmente melhor para documentos jurídicos espanhóis

### 4.3 Construção de Centroides

Categorias prioritárias (confusão frequente):

| Categoria | Exemplos Necessários | Fonte |
|-----------|----------------------|-------|
| PERSON_NAME | 100 | Nomes de auditoria.md + gazetteers |
| ORGANIZATION | 100 | Empresas, instituições de documentos jurídicos |
| DATE | 50 | Datas em formatos DD/MM/AAAA, DD-MM-AAAA |
| LOCATION | 50 | Cidades, províncias espanholas |

**Formato de exemplo** (com contexto):
```
"query: O advogado Alejandro Alvarez compareceu como testemunha no julgamento"
"query: A empresa Telefónica S.A. interpôs recurso de cassação"
"query: Na data 10/10/2025 foi proferida a sentença"
```

### 4.4 Integração com Pipeline Existente

Local proposto: `src/contextsafe/infrastructure/nlp/validators/entity_type_validator.py`

```python
class EntityTypeValidator:
    """
    Post-processor that validates/corrects NER entity type assignments
    using embedding similarity to type centroids.

    Based on: NER Retriever (arXiv 2509.04011), CEPTNER (KBS 2024)
    """

    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-large",
        centroids_path: Path = None,
        reclassify_threshold: float = 0.75,
        margin_threshold: float = 0.10,
        hitl_margin: float = 0.05,
    ):
        ...

    def validate(
        self,
        entity_text: str,
        context: str,
        predicted_type: str,
    ) -> ValidationResult:
        """
        Returns ValidationResult with:
        - corrected_type: str
        - confidence: float
        - action: 'KEEP' | 'RECLASSIFY' | 'FLAG_HITL'
        """
        ...
```

### 4.5 Métricas de Sucesso

| Métrica | Objetivo | Medição |
|---------|----------|---------|
| Redução de erros de tipo | ≥4% | Comparar antes/depois no conjunto de validação |
| Latência adicional | <100ms/entidade | Benchmark em CPU 16GB |
| Falsos positivos de reclassificação | <2% | Revisão manual das reclassificações |
| Cobertura HITL | <10% sinalizados | Porcentagem marcada para revisão humana |

---

## 5. Referências

1. **NER Retriever**: Zhang et al. (2025). "NER Retriever: Zero-Shot Named Entity Retrieval with Type-Aware Embeddings." arXiv:2509.04011. https://arxiv.org/abs/2509.04011

2. **CEPTNER**: Wang et al. (2024). "CEPTNER: Contrastive learning Enhanced Prototypical network for Two-stage Few-shot Named Entity Recognition." Knowledge-Based Systems. https://doi.org/10.1016/j.knosys.2024.111512

3. **NER Survey**: Li et al. (2024). "Recent Advances in Named Entity Recognition: A Comprehensive Survey and Comparative Study." arXiv:2401.10825. https://arxiv.org/abs/2401.10825

4. **Error Correction Framework**: Chen et al. (2025). "A Redundancy-Enhanced Framework for Error Correction in Named Entity Recognition." OpenReview. https://openreview.net/forum?id=2jFWhxJE5pQ

5. **Multilingual E5**: Wang et al. (2024). "Multilingual E5 Text Embeddings: A Technical Report." arXiv:2402.05672. https://arxiv.org/abs/2402.05672

6. **Legal-Embed**: Wasserstoff-AI. (2024). "Legal-Embed-intfloat-multilingual-e5-large-instruct." HuggingFace. https://huggingface.co/Wasserstoff-AI/Legal-Embed-intfloat-multilingual-e5-large-instruct

---

## 6. Erros de Classificação Identificados (Auditoria)

Análise do arquivo `auditoria.md` do documento STSJ ICAN 3407/2025:

| Entidade | Tipo Atribuído | Tipo Correto | Padrão |
|----------|----------------|--------------|--------|
| `"10/10/2025"` | ORGANIZATION (Org_038) | DATE | Data confundida com código |
| `"05-11-2024"` | ORGANIZATION | DATE | Data no formato DD-MM-AAAA |
| `"Pura"` | LOCATION (Lugar_001) | PERSON_NAME | Nome curto sem honorífico |
| `"Finalmente"` | ORGANIZATION (Org_012) | NÃO É PII | Advérbio capitalizado |
| `"Terminaba"` | ORGANIZATION (Org_017) | NÃO É PII | Verbo capitalizado |
| `"Quien"` | ORGANIZATION | NÃO É PII | Pronome capitalizado |
| `"Whatsapp"` | PERSON | ORGANIZATION/PLATFORM | Nome da plataforma |

**Padrão principal identificado**: O modelo RoBERTa classifica como ORGANIZATION qualquer palavra capitalizada no início da frase que não reconhece claramente como outro tipo.

---

## Documentos Relacionados

| Documento | Relação |
|-----------|---------|
| `auditoria.md` | Fonte de erros de classificação analisados |
| `docs/PLAN_CORRECCION_AUDITORIA.md` | Plano de correção anterior (7 problemas identificados) |
| `ml/docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md` | Avaliação anterior de embeddings (classificação de documentos) |
| `ml/docs/reports/2026-02-07_embeddings_roadmap_document_classification.md` | Roteiro de embeddings para classificação |
| `ml/README.md` | Instruções ML (formato de relatório) |

---

## Próximos Passos

1. [ ] Baixar modelo `intfloat/multilingual-e5-large` (~1.1GB)
2. [ ] Construir conjunto de dados de exemplos por tipo (PERSON_NAME, ORGANIZATION, DATE, LOCATION)
3. [ ] Implementar `EntityTypeValidator` em `infrastructure/nlp/validators/`
4. [ ] Calcular e persistir centroides por tipo
5. [ ] Integrar validador no pipeline NER existente
6. [ ] Avaliar redução de erros no conjunto de validação
7. [ ] (Opcional) Avaliar `Legal-Embed` versus `multilingual-e5-large`

---

```
Versão: 1.0.0
Autor: AlexAlves87
Tempo de pesquisa: ~15 min
```
