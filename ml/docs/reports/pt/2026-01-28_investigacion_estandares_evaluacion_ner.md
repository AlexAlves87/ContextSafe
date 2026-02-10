# Investigação: Padrões Académicos para Avaliação de NER

**Data:** 28-01-2026
**Autor:** AlexAlves87
**Tipo:** Revisão de Literatura Académica
**Estado:** Concluído

---

## 1. Resumo Executivo

Esta investigação documenta os padrões académicos para avaliação de sistemas NER, com ênfase em:
1. Métricas ao nível de entidade (SemEval 2013 Task 9)
2. Avaliação adversarial (RockNER, NoiseBench)
3. Frameworks de avaliação (seqeval, nervaluate)
4. Best practices para testes de robustez

### Principais Descobertas

| Descoberta | Fonte | Impacto |
|------------|-------|---------|
| 4 modos de avaliação: strict, exact, partial, type | SemEval 2013 | **CRÍTICO** |
| seqeval é o padrão de facto para F1 ao nível de entidade | CoNLL, HuggingFace | Alto |
| RockNER: perturbações ao nível de entidade + contexto | EMNLP 2021 | Alto |
| NoiseBench: ruído real >> ruído simulado em dificuldade | EMNLP 2024 | Alto |
| nervaluate fornece métricas mais granulares que seqeval | MantisAI | Médio |

---

## 2. Metodologia

### 2.1 Fontes Consultadas

| Fonte | Tipo | Ano | Relevância |
|-------|------|-----|------------|
| SemEval 2013 Task 9 | Shared Task | 2013 | Definição de métricas |
| RockNER (EMNLP 2021) | Paper ACL | 2021 | Avaliação adversarial |
| NoiseBench (EMNLP 2024) | Paper ACL | 2024 | Ruído realista |
| seqeval | Biblioteca | 2018+ | Implementação padrão |
| nervaluate | Biblioteca | 2020+ | Métricas estendidas |
| David Batista Blog | Tutorial | 2018 | Explicação detalhada |

### 2.2 Critérios de Pesquisa

- "adversarial NER evaluation benchmark methodology"
- "NER robustness testing framework seqeval entity level"
- "SemEval 2013 task 9 entity level metrics"
- "RockNER adversarial NER EMNLP methodology"
- "NoiseBench NER evaluation realistic noise"

---

## 3. Padrões de Avaliação ao Nível de Entidade

### 3.1 SemEval 2013 Task 9: Os 4 Modos de Avaliação

**Fonte:** [Named-Entity evaluation metrics based on entity-level](https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/)

O padrão SemEval 2013 define **4 modos** de avaliação:

| Modo | Limite | Tipo | Descrição |
|------|--------|------|-----------|
| **Strict** | Exato | Exato | Limite E tipo devem corresponder |
| **Exact** | Exato | Ignorado | Apenas limite exato |
| **Partial** | Sobreposição | Ignorado | Sobreposição parcial é suficiente |
| **Type** | Sobreposição | Exato | Sobreposição + tipo correto |

#### 3.1.1 Definição de Métricas Base

| Métrica | Definição |
|---------|-----------|
| **COR** (Correct) | Sistema e gold são idênticos |
| **INC** (Incorrect) | Sistema e gold não correspondem |
| **PAR** (Partial) | Sistema e gold têm sobreposição parcial |
| **MIS** (Missing) | Gold não capturado pelo sistema (FN) |
| **SPU** (Spurious) | Sistema produz algo não no gold (FP) |
| **POS** (Possible) | COR + INC + PAR + MIS = total gold |
| **ACT** (Actual) | COR + INC + PAR + SPU = total sistema |

#### 3.1.2 Fórmulas de Cálculo

**Para modos exatos (strict, exact):**
```
Precision = COR / ACT
Recall = COR / POS
F1 = 2 * (P * R) / (P + R)
```

**Para modos parciais (partial, type):**
```
Precision = (COR + 0.5 × PAR) / ACT
Recall = (COR + 0.5 × PAR) / POS
F1 = 2 * (P * R) / (P + R)
```

### 3.2 seqeval: Implementação Padrão

**Fonte:** [seqeval GitHub](https://github.com/chakki-works/seqeval)

seqeval é o framework padrão para avaliação de sequence labeling, validado contra o script Perl `conlleval` do CoNLL-2000.

#### Características

| Funcionalidade | Descrição |
|----------------|-----------|
| Formato | CoNLL (tags BIO/BIOES) |
| Métricas | Precision, Recall, F1 por tipo e global |
| Modo default | Simula conlleval (indulgente com B/I) |
| Modo strict | Apenas correspondências exatas |

#### Uso Correto

```python
from seqeval.metrics import classification_report, f1_score
from seqeval.scheme import IOB2

# Modo strict (recomendado para avaliação rigorosa)
f1 = f1_score(y_true, y_pred, mode='strict', scheme=IOB2)
report = classification_report(y_true, y_pred, mode='strict', scheme=IOB2)
```

**IMPORTANTE:** O modo default do seqeval é indulgente. Para avaliação rigorosa, usar `mode='strict'`.

### 3.3 nervaluate: Métricas Estendidas

**Fonte:** [nervaluate GitHub](https://github.com/MantisAI/nervaluate)

nervaluate implementa totalmente todos os 4 modos do SemEval 2013.

#### Vantagens sobre seqeval

| Aspeto | seqeval | nervaluate |
|--------|---------|------------|
| Modos | 2 (default, strict) | 4 (strict, exact, partial, type) |
| Granularidade | Por tipo de entidade | Por tipo + por cenário |
| Métricas | P/R/F1 | P/R/F1 + COR/INC/PAR/MIS/SPU |

#### Uso

```python
from nervaluate import Evaluator

evaluator = Evaluator(true_labels, pred_labels, tags=['PER', 'ORG', 'LOC'])
results, results_per_tag = evaluator.evaluate()

# Aceder a modo strict
strict_f1 = results['strict']['f1']

# Aceder a métricas detalhadas
cor = results['strict']['correct']
inc = results['strict']['incorrect']
par = results['partial']['partial']
```

---

## 4. Avaliação Adversarial: Padrões Académicos

### 4.1 RockNER (EMNLP 2021)

**Fonte:** [RockNER - ACL Anthology](https://aclanthology.org/2021.emnlp-main.302/)

RockNER propõe um framework sistemático para criar exemplos adversariais naturais.

#### Taxonomia de Perturbações

| Nível | Método | Descrição |
|-------|--------|-----------|
| **Nível Entidade** | Substituição Wikidata | Substituir entidades por outras da mesma classe semântica |
| **Nível Contexto** | BERT MLM | Gerar substituições de palavras com LM |
| **Combinado** | Ambos | Aplicar ambos para máxima adversarialidade |

#### Benchmark OntoRock

- Derivado de OntoNotes
- Aplica perturbações sistemáticas
- Mede degradação de F1

#### Descoberta Chave

> "Even the best model has a significant performance drop... models seem to memorize in-domain entity patterns instead of reasoning from the context."

### 4.2 NoiseBench (EMNLP 2024)

**Fonte:** [NoiseBench - ACL Anthology](https://aclanthology.org/2024.emnlp-main.1011/)

NoiseBench demonstra que o ruído simulado é **significativamente mais fácil** que o ruído real.

#### Tipos de Ruído Real

| Tipo | Fonte | Descrição |
|------|-------|-----------|
| Erros de peritos | Anotadores peritos | Erros de fadiga, interpretação |
| Crowdsourcing | Amazon Turk, etc. | Erros de não-peritos |
| Anotação automática | Regex, heurísticas | Erros sistemáticos |
| Erros LLM | GPT, etc. | Alucinações, inconsistências |

#### Descoberta Chave

> "Real noise is significantly more challenging than simulated noise, and current state-of-the-art models for noise-robust learning fall far short of their theoretically achievable upper bound."

### 4.3 Taxonomia de Perturbações para NER

Baseado na literatura, as perturbações adversariais classificam-se em:

| Categoria | Exemplos | Papers |
|-----------|----------|--------|
| **Nível carater** | Typos, erros OCR, homoglyphs | RockNER, NoiseBench |
| **Nível token** | Sinónimos, flexões | RockNER |
| **Nível entidade** | Substituição por entidades similares | RockNER |
| **Nível contexto** | Modificar contexto circundante | RockNER |
| **Nível formato** | Espaços, pontuação, casing | NoiseBench |
| **Nível semântico** | Negações, exemplos fictícios | Custom |

---

## 5. Revisão de Testes Atuais vs Padrões

### 5.1 Testes Adversariais Atuais

O nosso script `test_ner_predictor_adversarial.py` tem:

| Categoria | Testes | Cobertura |
|-----------|--------|-----------|
| edge_case | 9 | Condições limite |
| adversarial | 8 | Confusão semântica |
| ocr_corruption | 5 | Erros OCR |
| unicode_evasion | 3 | Evasão Unicode |
| real_world | 10 | Documentos reais |

### 5.2 Gaps Identificados

| Gap | Padrão | Estado Atual | Severidade |
|-----|--------|--------------|------------|
| Modo strict vs default | seqeval strict | Não especificado | **CRÍTICO** |
| 4 modos SemEval | nervaluate | Apenas 1 modo | ALTO |
| Perturbações nível entidade | RockNER | Não sistemático | ALTO |
| Métricas COR/INC/PAR/MIS/SPU | SemEval 2013 | Não reportadas | MÉDIO |
| Ruído real vs simulado | NoiseBench | Apenas simulado | MÉDIO |
| Perturbações nível contexto | RockNER | Parcial | MÉDIO |

### 5.3 Métricas Atuais vs Requeridas

| Métrica | Atual | Requerido | Gap |
|---------|-------|-----------|-----|
| F1 overall | ✅ | ✅ | OK |
| Precision/Recall | ✅ | ✅ | OK |
| F1 por tipo de entidade | ❌ | ✅ | **EM FALTA** |
| Modo strict | ❓ | ✅ | **VERIFICAR** |
| COR/INC/PAR/MIS/SPU | ❌ | ✅ | **EM FALTA** |
| 4 modos SemEval | ❌ | ✅ | **EM FALTA** |

---

## 6. Recomendações de Melhoria

### 6.1 Prioridade CRÍTICA

1. **Verificar modo strict em seqeval**
   ```python
   # Mudar de:
   f1 = f1_score(y_true, y_pred)
   # Para:
   f1 = f1_score(y_true, y_pred, mode='strict', scheme=IOB2)
   ```

2. **Reportar métricas por tipo de entidade**
   ```python
   report = classification_report(y_true, y_pred, mode='strict')
   ```

### 6.2 Prioridade ALTA

3. **Implementar os 4 modos do SemEval**
   - Usar nervaluate em vez de (ou além de) seqeval
   - Reportar strict, exact, partial, type

4. **Adicionar perturbações nível entidade (estilo RockNER)**
   - Substituir nomes por outros nomes espanhóis
   - Substituir IDs por outros IDs válidos
   - Manter contexto, mudar entidade

### 6.3 Prioridade MÉDIA

5. **Reportar COR/INC/PAR/MIS/SPU**
   - Permite análise mais fina de erros
   - Distingue entre erros de limite e erros de tipo

6. **Adicionar perturbações nível contexto**
   - Modificar verbos/adjetivos circundantes
   - Usar BERT/spaCy para substituições naturais

---

## 7. Checklist de Avaliação Académica

### 7.1 Antes de Reportar Resultados

- [ ] Especificar modo de avaliação (strict/default)
- [ ] Usar formato CoNLL padrão (BIO/BIOES)
- [ ] Reportar F1, Precision, Recall
- [ ] Reportar métricas por tipo de entidade
- [ ] Documentar versão de seqeval/nervaluate usada
- [ ] Incluir intervalos de confiança se houver variância

### 7.2 Para Avaliação Adversarial

- [ ] Categorizar perturbações (Carater, Token, Entidade, Contexto)
- [ ] Medir degradação relativa (F1_clean - F1_adversarial)
- [ ] Reportar pass rate por categoria de dificuldade
- [ ] Incluir análise de erros com exemplos
- [ ] Comparar com baseline (modelo não modificado)

### 7.3 Para Publicação/Documentação

- [ ] Descrever metodologia reprodutível
- [ ] Publicar dataset de teste (ou gerador)
- [ ] Reportar tempo de execução
- [ ] Incluir análise estatística se aplicável

---

## 8. Conclusões

### 8.1 Ações Imediatas

1. **Rever script adversarial** para verificar modo strict
2. **Adicionar nervaluate** para métricas completas
3. **Reorganizar testes** de acordo com taxonomia RockNER

### 8.2 Impacto nos Resultados Atuais

Os resultados atuais (F1=0.784, 54.3% pass rate) podem mudar se:
- O modo não era strict (resultados seriam inferiores em strict)
- As métricas por tipo revelam fraquezas específicas
- Os 4 modos mostram comportamento diferente em limite vs tipo

---

## 9. Referências

### Papers Académicos

1. **RockNER: A Simple Method to Create Adversarial Examples for Evaluating the Robustness of Named Entity Recognition Models**
   - Lin et al., EMNLP 2021
   - URL: https://aclanthology.org/2021.emnlp-main.302/

2. **NoiseBench: Benchmarking the Impact of Real Label Noise on Named Entity Recognition**
   - Merdjanovska et al., EMNLP 2024
   - URL: https://aclanthology.org/2024.emnlp-main.1011/

3. **SemEval-2013 Task 9: Extraction of Drug-Drug Interactions from Biomedical Texts**
   - Segura-Bedmar et al., SemEval 2013
   - Definição métricas ao nível de entidade

### Ferramentas e Bibliotecas

4. **seqeval**
   - URL: https://github.com/chakki-works/seqeval

5. **nervaluate**
   - URL: https://github.com/MantisAI/nervaluate

6. **Named-Entity Evaluation Metrics Based on Entity-Level**
   - David Batista, 2018
   - URL: https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/

---

**Tempo de investigação:** 45 min
**Gerado por:** AlexAlves87
**Data:** 28-01-2026
