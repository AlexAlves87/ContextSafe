# Embeddings para ContextSafe: Roteiro e Critérios de Ativação

**Data:** 07-02-2026
**Objetivo:** Documentar a abordagem de embeddings avaliada, as alternativas implementadas,
e os critérios sob os quais seria justificável escalar para embeddings no futuro.

---

## 1. Resumo Executivo

Duas propostas envolvendo embeddings foram avaliadas:

| Proposta | Fonte | Modelo | Decisão |
|----------|-------|--------|---------|
| Classificação de documento com embeddings | Melhorias Arquitetônicas v2.1, Módulo A | `intfloat/multilingual-e5-small` | **Adiada** — Regex implementada |
| Gap Scanning com embeddings | Estratégia Safety Net A | `intfloat/multilingual-e5-small` | **Descartada** — Similaridade cosseno inadequada |

**Status atual:** Foi implementado um classificador baseado em regex/palavras-chave
(`DocumentTypeClassifier`) que cobre os requisitos imediatos com 0 bytes de modelo,
<1ms de latência e ~95% de precisão estimada para documentos jurídicos espanhóis.

Os embeddings ficam documentados como **opção de escalabilidade futura** quando critérios
específicos forem atendidos (Seção 5).

---

## 2. Proposta Avaliada: Classificação de Documento com Embeddings

### 2.1 Modelo Proposto

| Especificação | Valor |
|---------------|-------|
| Modelo | `intfloat/multilingual-e5-small` (Wang et al., arXiv:2402.05672) |
| Parâmetros | 117.65M |
| Tamanho FP32 | 448 MB |
| Tamanho INT8 ONNX | 112 MB |
| Dimensão embedding | 384 |
| Max tokens | 512 |
| Latência estimada (CPU INT8) | ~200ms |
| Idiomas suportados | 94-100 |
| Licença | MIT |
| RAM runtime (FP32) | ~500 MB |
| RAM runtime (INT8) | ~200 MB |

**Fonte de verificação:** HuggingFace model card `intfloat/multilingual-e5-small`.

### 2.2 Arquitetura Proposta

```
Documento → Embedding (e5-small) → Similaridade Cosseno vs centroides → Tipo → Config NER
```

Isso NÃO é RAG-NER (o termo usado na proposta v2.1 está incorreto).
É **classificação de documento + configuração condicional**
(ver `ml/docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md`, Seção 2).

### 2.3 Por Que Foi Adiada

| Fator | Embeddings | Regex (implementada) |
|-------|------------|----------------------|
| Tamanho | 112-448 MB | 0 bytes |
| Latência | ~200ms | <1ms |
| Precisão estimada | ~99% | ~95%+ |
| Complexidade | Alta (runtime ONNX, quantização) | Trivial |
| RAM adicional | 200-500 MB | 0 |
| Manutenção | Modelo versionado, atualizações | Padrões editáveis |

Para ~7 tipos de documentos jurídicos com cabeçalhos altamente distintivos, a regex é
suficiente. Os 4% adicionais de precisão não justificam 200MB de modelo nem a complexidade
de manutenção.

---

## 3. Proposta Avaliada: Gap Scanning com Embeddings

### 3.1 Conceito

Usar embeddings para detectar fragmentos "suspeitos" não identificados pelo NER:

```
Texto completo → Segmentar em chunks → Embedding de cada chunk
    → Comparar vs "centroide de risco PII" → Alertar se similaridade alta
```

### 3.2 Por Que Foi Descartada

1. **Similaridade cosseno não detecta PII**: A similaridade semântica mede proximidade temática,
   não presença de dados pessoais. "Juan García vive em Madrid" e "A empresa opera
   em Madrid" têm alta similaridade semântica mas apenas um contém PII nominal.

2. **Não existe um "centroide de risco PII"**: Os dados pessoais (nomes, DNIs, IBANs,
   endereços) ocupam regiões semânticas completamente disjuntas. Não há um ponto no
   espaço de embeddings que represente "isto contém PII"
   (ver Ethayarajh, EMNLP 2019, sobre anisotropia de embeddings).

3. **Paper de referência**: Netflix/Cornell 2024 documenta limitações da similaridade cosseno
   para detecção de características discretas vs contínuas. PII é inerentemente
   discreto (presente ou ausente).

4. **Alternativa implementada**: Os Sanity Checks determinísticos (`ExportValidator`,
   `src/contextsafe/domain/document_processing/services/export_validator.py`) cobrem
   o caso de falsos negativos por tipo de documento de forma mais confiável e sem
   dependências adicionais.

---

## 4. Alternativa Implementada: Classificador Regex

### 4.1 Implementação

```
src/contextsafe/domain/document_processing/services/document_classifier.py
```

| Característica | Detalhe |
|----------------|---------|
| Tipos suportados | SENTENCIA, ESCRITURA, FACTURA, RECURSO, DENUNCIA, CONTRATO, GENERIC |
| Método | Regex sobre primeiros 500 caracteres (maiusculo) |
| Padrões por tipo | 4-8 palavras-chave distintivas |
| Fallback | Nome do arquivo se texto não classifica |
| Confiança | Proporção de padrões encontrados / total por tipo |
| Latência | <1ms |
| Dependências | 0 (apenas `re` da stdlib) |

### 4.2 Padrões Chave

| Tipo | Padrões principais |
|------|--------------------|
| SENTENCIA | `SENTENCIA`, `JUZGADO`, `TRIBUNAL`, `FALLO`, `MAGISTRAD[OA]` |
| ESCRITURA | `ESCRITURA`, `NOTAR[IÍ]`, `PROTOCOLO`, `OTORGAMIENTO` |
| FACTURA | `FACTURA`, `BASE IMPONIBLE`, `IVA`, `TOTAL FACTURA` |
| RECURSO | `RECURSO`, `APELACI[OÓ]N`, `CASACI[OÓ]N` |
| DENUNCIA | `DENUNCIA`, `ATESTADO`, `DILIGENCIAS PREVIAS` |
| CONTRATO | `CONTRATO`, `CL[AÁ]USULA`, `ESTIPULACIONES` |

### 4.3 Integração com Sanity Checks

O classificador alimenta as regras de validação de exportação:

```
Documento → DocumentTypeClassifier → tipo
                                       ↓
ExportValidator.validate(tipo, ...) → Aplica regras SC-001..SC-004
```

| Regra | Tipo | Categorias mínimas | Severidade |
|-------|------|--------------------|------------|
| SC-001 | ESCRITURA | PERSON_NAME ≥1, DNI_NIE ≥1 | CRÍTICA |
| SC-002 | SENTENCIA | DATE ≥1 | AVISO |
| SC-003 | FACTURA | ORGANIZATION ≥1 | AVISO |
| SC-004 | DENUNCIA | PERSON_NAME ≥1 | AVISO |

---

## 5. Critérios de Ativação para Escalar para Embeddings

Os embeddings deveriam ser reconsiderados APENAS se forem atendidos **pelo menos 2** destes critérios:

### 5.1 Critérios Funcionais

| # | Critério | Limiar |
|---|----------|--------|
| CF-1 | Precisão do regex cai abaixo de 90% | Medir com corpus de validação |
| CF-2 | >15 tipos de documento adicionados | Regex se torna incontrolável |
| CF-3 | Documentos sem cabeçalho padronizado | OCR degradado, scanners variados |
| CF-4 | Requisito de classificação multilíngue | Documentos em catalão, basco, galego |

### 5.2 Critérios de Infraestrutura

| # | Critério | Limiar |
|---|----------|--------|
| CI-1 | RAM disponível em produção | ≥32 GB (atualmente alvo é 16 GB) |
| CI-2 | Pipeline já usa ONNX Runtime | Evita adicionar nova dependência |
| CI-3 | Latência atual do pipeline | <2s total (margem para +200ms) |

### 5.3 Rota de Implementação (se ativada)

```
Passo 1: Coletar corpus de validação (50+ docs por tipo)
Passo 2: Avaliar precisão atual do regex com corpus
Passo 3: Se precisão < 90%, avaliar TF-IDF + LogReg primeiro (~50KB, <5ms)
Passo 4: Apenas se TF-IDF < 95%, escalar para e5-small INT8 ONNX
Passo 5: Gerar centroides por tipo com corpus rotulado
Passo 6: Validar com testes adversariais (documentos mistos, OCR degradado)
```

### 5.4 Modelo Recomendado (se escalar)

| Opção | Tamanho | Latência | Caso de uso |
|-------|---------|----------|-------------|
| TF-IDF + LogReg | ~50 KB | <5ms | Primeiro passo de escalabilidade |
| `intfloat/multilingual-e5-small` INT8 | 112 MB | ~200ms | Classificação multilíngue |
| `BAAI/bge-small-en-v1.5` INT8 | 66 MB | ~150ms | Apenas inglês/espanhol |

**Nota:** `intfloat/multilingual-e5-small` continua sendo a melhor opção para multilíngue
se necessário. Mas TF-IDF é o passo intermediário correto antes de embeddings neurais.

---

## 6. Impacto no Pipeline NER

### 6.1 Estado Atual (implementado)

```
Documento ingerido
    ↓
DocumentTypeClassifier.classify(primeiros_500_chars)    ← REGEX
    ↓
ConfidenceZone.classify(score, categoria, checksum)     ← TRIAGEM
    ↓
CompositeNerAdapter.detect_entities(text)               ← NER
    ↓
ExportValidator.validate(tipo, entidades, revisões)     ← TRAVA DE SEGURANÇA
    ↓
[Exportação permitida ou bloqueada]
```

### 6.2 Estado Futuro (se embeddings ativados)

```
Documento ingerido
    ↓
DocumentTypeClassifier.classify(primeiros_500_chars)    ← REGEX (fallback)
    ↓
EmbeddingClassifier.classify(primeiros_512_tokens)      ← EMBEDDINGS
    ↓
merge_classifications(resultado_regex, resultado_emb)   ← FUSÃO
    ↓
CompositeNerAdapter.detect_entities(text, doc_type=tipo) ← NER CONTEXTUAL
    ↓
ExportValidator.validate(tipo, entidades, revisões)     ← TRAVA DE SEGURANÇA
```

A interface do classificador (`DocumentClassification` dataclass) já está projetada para
ser substituível sem mudanças no resto do pipeline.

---

## 7. Conclusão

A abordagem atual (regex) é a decisão correta para o estado presente do projeto.
Os embeddings representam uma melhoria incremental que só se justifica diante de um crescimento
significativo em tipos de documento ou degradação mensurável da precisão.

A arquitetura hexagonal permite escalar sem refatoração: o `DocumentTypeClassifier`
pode ser substituído por um `EmbeddingClassifier` que implemente a mesma interface
(`DocumentClassification`), sem impacto no resto do pipeline.

---

## Documentos Relacionados

| Documento | Relação |
|-----------|---------|
| `ml/docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md` | Avaliação crítica da proposta RAG-NER |
| `ml/docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | Pipeline NER atual (5 elementos) |
| `ml/docs/reports/2026-02-06_adversarial_v2_academic_r7.md` | Avaliação adversarial do pipeline |
| `src/contextsafe/domain/document_processing/services/document_classifier.py` | Classificador regex implementado |
| `src/contextsafe/domain/document_processing/services/export_validator.py` | Trava de Segurança + Sanity Checks |
| `src/contextsafe/domain/entity_detection/services/confidence_zone.py` | Triagem por zonas de confiança |

## Referências

| Referência | Local | Relevância |
|------------|-------|------------|
| Wang et al., "Multilingual E5 Text Embeddings" | arXiv:2402.05672 (2024) | Modelo avaliado |
| Ethayarajh, "How Contextual are Contextualized Word Representations?" | EMNLP 2019 | Anisotropia de embeddings |
| Netflix/Cornell, "Limitations of Cosine Similarity" | arXiv (2024) | Limitações para detecção discreta |
| Lewis et al., "Retrieval-Augmented Generation" | NeurIPS 2020 | Definição correta de RAG |
| Dai et al., "RA-NER" | ICLR 2024 Tiny Papers | RAG real aplicado a NER |
