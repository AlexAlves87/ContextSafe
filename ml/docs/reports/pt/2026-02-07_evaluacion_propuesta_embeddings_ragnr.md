# Avaliação Crítica: Proposta de Embeddings (RAG-NER) para ContextSafe

**Data:** 07-02-2026
**Objetivo:** Avaliar a validade técnica e a necessidade do Módulo A da proposta
"Melhorias Arquitetônicas v2.1" — uso de `intfloat/multilingual-e5-small` para
pré-classificação de documentos e configuração dinâmica do NER.

---

## 1. Resumo Executivo

A proposta sugere usar embeddings (`intfloat/multilingual-e5-small`, ~120MB) como
"Elemento 0" do pipeline NER para classificar tipos de documento e ajustar dinamicamente
os limiares de detecção. Após investigar a literatura acadêmica, verificar as
especificações do modelo e contrastar com o estado atual do pipeline do ContextSafe,
**a conclusão é que a ideia base tem mérito parcial, mas a implementação proposta
é superengenharia e o termo "RAG-NER" é tecnicamente incorreto**.

### Veredito

| Aspecto | Avaliação |
|---------|-----------|
| Conceito (NER ciente do tipo de documento) | Válido e útil |
| Termo "RAG-NER" | Incorreto: não é RAG |
| Modelo proposto (`multilingual-e5-small`) | Superdimensionado para a tarefa |
| Necessidade real no ContextSafe | Média: alternativas mais simples disponíveis |
| Prioridade vs. outras melhorias | Baixa frente a melhorias HITL e auditoria |

---

## 2. Análise do Termo "RAG-NER"

### O que é RAG na literatura

RAG (Retrieval-Augmented Generation) foi introduzido por Lewis et al. (NeurIPS 2020)
e refere-se especificamente à **recuperação de documentos/passagens de uma base de
conhecimento para aumentar a geração** de um modelo de linguagem.

Os papers reais de RAG+NER (2024-2025) são:

| Paper | Local | O que faz realmente |
|-------|-------|---------------------|
| **RA-NER** (Dai et al.) | ICLR 2024 Tiny Papers | Recupera entidades similares de uma KB externa para ajudar o NER |
| **RENER** (Shiraishi et al.) | arXiv 2410.13118 | Recupera exemplos anotados similares como in-context learning para NER |
| **RA-IT Open NER** | arXiv 2406.17305 | Instruction tuning com exemplos recuperados para NER aberto |
| **IF-WRANER** | arXiv 2411.00451 | Retrieval nível de palavra para few-shot cross-domain NER |
| **RAG-BioNER** | arXiv 2508.06504 | Prompting dinâmico com RAG para NER biomédico |

### O que propõe o documento v2.1

O que se descreve NÃO é RAG. É **classificação de tipo de documento + configuração
condicional do NER**. Não há recuperação de documentos/exemplos de uma base de
conhecimento. Não há aumento de geração. É um classificador seguido de um switch.

**Diagrama real da proposta:**
```
Documento → Embedding (e5-small) → Similaridade Cosseno → Tipo detectado → Switch de config → NER
```

**Diagrama real de RAG-NER (RA-NER, Amazon):**
```
Texto de entrada → Recuperar entidades similares de KB → Injetar como contexto ao NER → Predição
```

São arquiteturas fundamentalmente diferentes. Rotular a proposta como "RAG-NER"
é incorreto e poderia induzir a erro em documentação técnica ou publicações.

---

## 3. Verificação do Modelo Proposto

### Especificações reais de `intfloat/multilingual-e5-small`

| Especificação | Alegação v2.1 | Valor real | Fonte |
|---------------|---------------|------------|-------|
| Peso | ~120 MB | **448 MB (FP32), 112 MB (INT8 ONNX)** | HuggingFace |
| Parâmetros | Não indicado | 117.65M | HuggingFace |
| Dimensão embedding | Não indicado | 384 | Paper arXiv:2402.05672 |
| Max tokens | 512 | 512 (correto) | HuggingFace |
| Latência | <200ms em CPU | Plausível para 512 tokens INT8 | - |
| Idiomas | Não indicado | 94-100 idiomas | HuggingFace |
| Licença | Não indicado | MIT | HuggingFace |

**Problemas detectados:**
- A alegação de "~120 MB" só é verdadeira com quantização INT8 ONNX. O modelo FP32 pesa
  448 MB. O documento não esclarece que requer quantização.
- Em memória (runtime), o modelo FP32 consome ~500MB RAM. Com INT8, ~200MB.
- Sobre o hardware alvo de 16GB RAM (já com RoBERTa + Presidio + spaCy carregados),
  a margem disponível é limitada.

### Benchmark de referência

| Benchmark | Resultado | Contexto |
|-----------|-----------|----------|
| Mr. TyDi (retrieval MRR@10) | 64.4 média | Bom para retrieval multilíngue |
| MTEB Classification (Amazon) | 88.7% precisão | Aceitável para classificação |

O modelo é competente para tarefas de embeddings. A questão é se é necessário um
modelo de 117M parâmetros para classificar ~5 tipos de documento jurídico.

---

## 4. Análise de Necessidade: Estado Atual vs. Proposta

### Pipeline atual do ContextSafe

O `CompositeNerAdapter` já implementa mecanismos sofisticados de contextualização:

| Mecanismo existente | Descrição |
|---------------------|-----------|
| **Âncoras Contextuais** (Fase 1) | Força categorias segundo contexto jurídico espanhol |
| **Votação Ponderada** (Fase 2) | Regex=5, RoBERTa=2, Presidio=1.5, spaCy=1 |
| **Desempate de Risco GDPR** (Fase 3) | Prioridade: PERSON_NAME=100 → POSTAL_CODE=20 |
| **30+ Padrões de Falso Positivo** | Bloqueia referências legais, DOI, ORCID, ISBN |
| **Filtro de Stopwords Espanholas** | Evita detecção de artigos/pronomes |
| **Lista Branca Termos Genéricos** | Termos nunca anonimizados (Estado, RGPD, etc.) |
| **Matrioshka (entidades aninhadas)** | Manuseio de entidades aninhadas |

O pipeline atual NÃO tem:
- Classificação de tipo de documento
- Limiares dinâmicos por categoria
- Limiares dinâmicos por tipo de documento

### O ContextSafe precisa de classificação de documento?

**Parcialmente sim**, mas não como proposto. Os benefícios reais seriam:
- Ajustar limiar de IBAN em faturas (mais estrito) vs. sentenças (mais relaxado)
- Ativar/desativar categorias segundo contexto (ex. data de nascimento relevante
  em sentenças penais, não em faturas)
- Reduzir falsos positivos de nomes próprios em documentos com muitas razões sociais

### Alternativas mais simples e eficazes

| Método | Tamanho | Latência | Precisão estimada | Complexidade |
|--------|---------|----------|-------------------|--------------|
| **Regex sobre cabeçalhos** | 0 KB (código) | <1ms | ~95%+ | Trivial |
| **TF-IDF + LogisticRegression** | ~50 KB | <5ms | ~97%+ | Baixa |
| **e5-small (INT8 ONNX)** | 112 MB | ~200ms | ~99% | Alta |
| **e5-small (FP32)** | 448 MB | ~400ms | ~99% | Alta |

Para documentos jurídicos espanhóis, os cabeçalhos são extremamente distintivos:
- `"SENTENCIA"`, `"JUZGADO"`, `"TRIBUNAL"` → Sentença
- `"ESCRITURA"`, `"NOTARIO"`, `"PROTOCOLO"` → Escritura Notarial
- `"FACTURA"`, `"BASE IMPONIBLE"`, `"IVA"` → Fatura
- `"RECURSO"`, `"APELACIÓN"`, `"CASACIÓN"` → Recurso/Apelação

Um classificador baseado em regex/palavras-chave nos primeiros 200 caracteres provavelmente
alcance >95% de precisão sem adicionar dependências nem latência significativa.

---

## 5. Recomendação

### O que SIM se recomenda implementar

1. **Classificação de tipo de documento** — mas com regex/palavras-chave, não embeddings
2. **Limiares dinâmicos por categoria** — independente da classificação
3. **Configuração condicional do NER** — ativar/desativar regras segundo tipo

### O que NÃO se recomenda

1. **Não usar embeddings** para classificar ~5 tipos de documento jurídico
2. **Não chamar isso de "RAG-NER"** — é classificação + configuração condicional
3. **Não adicionar 112-448MB de modelo** quando regex atinge o mesmo objetivo

### Implementação sugerida (alternativa)

```python
# Element 0: Document Type Classifier (lightweight)
class DocumentTypeClassifier:
    """Classify legal document type from header text."""

    PATTERNS = {
        DocumentType.SENTENCIA: [r"SENTENCIA", r"JUZGADO", r"TRIBUNAL", r"FALLO"],
        DocumentType.ESCRITURA: [r"ESCRITURA", r"NOTARI", r"PROTOCOLO"],
        DocumentType.FACTURA: [r"FACTURA", r"BASE IMPONIBLE", r"IVA"],
        DocumentType.RECURSO: [r"RECURSO", r"APELACI[OÓ]N", r"CASACI[OÓ]N"],
    }

    def classify(self, text: str, max_chars: int = 500) -> DocumentType:
        header = text[:max_chars].upper()
        scores = {}
        for doc_type, patterns in self.PATTERNS.items():
            scores[doc_type] = sum(1 for p in patterns if re.search(p, header))
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return DocumentType.GENERIC
```

**Custo:** 0 bytes de modelo, <1ms latência, ~0 complexidade adicional.
**Extensível:** Se no futuro for necessária maior sofisticação, pode-se escalar
para TF-IDF ou embeddings. Mas começar simples.

---

## 6. Sobre o "Elemento 0" no pipeline

Se decidir implementar classificação de documento (com o método simples recomendado),
a localização correta seria:

```
Documento ingerido
    ↓
Element 0: classify_document_type(first_500_chars)  ← NOVO
    ↓
CompositeNerAdapter.detect_entities(text, doc_type=tipo)
    ↓
[RoBERTa | Presidio | Regex | spaCy] com limiares ajustados segundo doc_type
    ↓
Merge (votação ponderada atual, já funciona bem)
```

Este passo é coerente com a arquitetura hexagonal atual e não requer mudanças
nas portas ou adaptadores existentes.

---

## 7. Conclusão

A proposta identifica uma necessidade real (NER ciente do tipo de documento)
mas propõe uma solução superengenharia com terminologia incorreta. Um classificador
baseado em regex sobre os cabeçalhos do documento alcançaria o mesmo objetivo sem adicionar
120-448MB de modelo, 200ms de latência adicional, nem complexidade de manutenção.

O investimento de esforço se rentabiliza muito mais no Módulo B (auditoria ativa e
rastreabilidade HITL), onde o ContextSafe tem gaps reais de conformidade normativa.

---

## 8. Literatura Consultada

| Referência | Local | Relevância |
|------------|-------|------------|
| Wang et al., "Multilingual E5 Text Embeddings" | arXiv:2402.05672 (2024) | Modelo proposto |
| Dai et al., "RA-NER" | ICLR 2024 Tiny Papers | RAG real aplicado a NER |
| Shiraishi et al., "RENER" | arXiv:2410.13118 (2024) | Retrieval-enhanced NER |
| arXiv 2406.17305, "RA-IT Open NER" | arXiv (2024) | Instruction tuning + retrieval |
| arXiv 2411.00451, "IF-WRANER" | arXiv (2024) | Few-shot cross-domain NER + RAG |
| arXiv 2508.06504, "RAG-BioNER" | arXiv (2025) | Dynamic prompting + RAG |
| ACL 2020 LT4Gov, "Legal-ES" | ACL Anthology | Embeddings legais espanhóis |
| IEEE 2024, "Fine-grained NER Spanish legal" | IEEE Xplore | NER legal espanhol |
| Frontiers AI 2025, "LegNER multilingual" | Frontiers | NER legal multilíngue |

## Documentos Relacionados

| Documento | Relação |
|-----------|---------|
| `ml/docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | Pipeline NER atual (5 elementos) |
| `ml/docs/reports/2026-02-06_adversarial_v2_academic_r7.md` | Avaliação adversarial do pipeline atual |
| `ml/docs/reports/2026-01-31_mejores_practicas_ml_2026.md` | Melhores práticas ML |
| `src/contextsafe/infrastructure/nlp/composite_adapter.py` | Implementação atual do pipeline NER |
