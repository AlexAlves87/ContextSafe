# Pesquisa: Melhores Práticas de ML 2025-2026 para NER-PII Legal

**Data:** 31-01-2026
**Autor:** AlexAlves87
**Objetivo:** Identificar técnicas de ponta aplicáveis ao pipeline NER-PII do ContextSafe
**Escopo:** Literatura de primeira linha (ICLR, EMNLP, NeurIPS, NAACL, Nature) publicada em 2025-2026

---

## 1. Resumo Executivo

Revisão sistemática da literatura recente (2025-2026) em aprendizado de máquina aplicado ao Reconhecimento de Entidades Nomeadas (NER) e detecção de PII. Identificam-se **8 avanços significativos** em relação às práticas documentadas em nosso relatório anterior (2026-01-30_investigacion_finetuning_legal_xlm_r), com impacto direto na estratégia de treinamento do Legal-XLM-RoBERTa para o ContextSafe.

### Principais Descobertas

| # | Técnica | Fonte | Impacto para ContextSafe |
|---|---------|-------|--------------------------|
| 1 | LoRA/QLoRA com alto rank (128-256) em todas as camadas | Unsloth, COLING 2025 | Reduz VRAM de 16GB para ~4GB sem perda de F1 |
| 2 | RandLoRA (full-rank PEFT) | ICLR 2025 | Elimina o plateau do LoRA padrão |
| 3 | Knowledge Distillation multi-perspectiva | IGI Global 2025 | +2.5-5.8% F1 com dados limitados |
| 4 | Geração sintética LLM para NER | EMNLP 2025 | Bootstrap para idiomas sem corpus anotado |
| 5 | GLiNER zero-shot PII | NAACL 2024 + updates 2025 | Baseline 81% F1 sem treinamento |
| 6 | NER Híbrido (transformer + regras) | Nature Sci. Reports 2025 | 94.7% precisão em documentos financeiros |
| 7 | RECAP (regex + LLM contextual) | NeurIPS 2025 | +82% sobre NER fine-tuned, +17% sobre zero-shot |
| 8 | DAPT seletivo (não universal) | ICLR 2025 | DAPT nem sempre melhora; requer avaliação prévia |

### Diagnóstico: Estado Atual vs. Estado da Arte

| Capacidade | ContextSafe Atual | Estado da Arte 2026 | Gap |
|------------|-------------------|---------------------|-----|
| Fine-tuning | Full FT planejado | LoRA/RandLoRA (PEFT) | **Alto** |
| Dados de treinamento | Apenas gold labels | Gold + sintéticos (LLM) | **Alto** |
| Pipeline NER | Híbrido (regex+ML) | RECAP (regex+LLM contextual) | Médio |
| Zero-shot baseline | Não estabelecido | GLiNER ~81% F1 | **Alto** |
| DAPT | Planejado universal | Seletivo (avaliar antes) | Médio |
| Inferência | ONNX INT8 planejado | LoRA adapters + quantização | Baixo |
| Avaliação | SemEval entity-level | + adversarial + cross-lingual | Médio |
| Modelo legal espanhol | Nenhuma baseline | MEL (XLM-R-large, 82% F1) | **Alto** |

---

## 2. Metodologia de Revisão

### 2.1 Critérios de Inclusão

| Critério | Valor |
|----------|-------|
| Período | Janeiro 2025 - Fevereiro 2026 |
| Venues | ICLR, EMNLP, NeurIPS, NAACL, ACL, Nature, ArXiv (pre-print com citações) |
| Relevância | NER, PII, PEFT, DAPT, NLP legal, multilíngue |
| Idiomas | Multilíngue (com ênfase em espanhol) |

### 2.2 Pesquisas Realizadas

1. "LoRA QLoRA NER fine-tuning 2025 2026 best practices"
2. "knowledge distillation LLM small model NER 2025"
3. "ICL-APT in-context learning augmented pretraining 2025"
4. "Continual Pre-Training is (not) What You Need 2025 legal"
5. "GLiNER zero-shot NER PII detection 2025 2026"
6. "EMNLP 2025 LLM data generation NER multilingual"
7. "hybrid NER transformer rules PII detection 2025"
8. "RandLoRA ICLR 2025 full rank"
9. "MEL legal Spanish language model 2025"

---

## 3. Resultados por Área Temática

### 3.1 Parameter-Efficient Fine-Tuning (PEFT)

#### 3.1.1 LoRA/QLoRA: Configurações Ótimas 2025-2026

A literatura recente consolida as melhores práticas para LoRA aplicado a NER:

| Hiperparâmetro | Valor Recomendado | Fonte |
|----------------|-------------------|-------|
| Rank (r) | 128-256 | Unsloth Docs, Medical NER studies |
| Alpha (α) | 2×r (256-512) | Heurística validada empiricamente |
| Target modules | Atenção **+ MLP** (todas as camadas) | Databricks, Lightning AI |
| Learning rate | 2e-4 (início), faixa 5e-6 a 2e-4 | Unsloth, Medium/QuarkAndCode |
| Epochs | 1-3 (risco overfitting >3) | Consenso múltiplas fontes |
| Dropout | 0.05 (domínios especializados) | Medical NER studies |

**Evidência empírica recente:**

| Paper | Modelo | Tarefa | F1 | Venue |
|-------|--------|--------|----|-------|
| B2NER | LoRA adapters ≤50MB | NER universal (15 datasets, 6 idiomas) | +6.8-12.0 F1 vs GPT-4 | COLING 2025 |
| LLaMA-3-8B Financial NER | LoRA r=128 | NER financeiro | 0.894 micro-F1 | ArXiv Jan 2026 |
| Military IE | GRPO + LoRA | Extração de Informação | +48.8% F1 absoluto | 2025 |

**Decisão LoRA vs QLoRA:**
- **LoRA**: Velocidade ligeiramente maior, ~0.5% mais preciso, 4× mais VRAM
- **QLoRA**: Usar quando VRAM < 8GB ou modelo > 1B parâmetros
- **Para Legal-XLM-RoBERTa-base (184M)**: LoRA é viável em RTX 5060 Ti 16GB

#### 3.1.2 RandLoRA: PEFT de Full-Rank

**Paper:** "RandLoRA: Full-Rank Parameter-Efficient Fine-Tuning of Large Models"
**Venue:** ICLR 2025 (ArXiv: 2502.00987)

**Problema que resolve:**
O LoRA padrão produz atualizações de baixo rank, limitando a capacidade de representação. Aumentar o rank (r) não fecha a lacuna com o full fine-tuning: existe um *plateau* de desempenho.

**Inovação:**
- Gera matrizes aleatórias de baixo rank **não treináveis** (bases linearmente independentes)
- Aprende apenas **coeficientes diagonais** de escalonamento
- A combinação linear produz atualizações de **rank completo**
- Mesma quantidade de parâmetros treináveis que o LoRA, mas sem restrição de rank

**Resultados:**

| Modelo | Tarefa | LoRA | RandLoRA | Full FT |
|--------|--------|------|----------|---------|
| DinoV2 | Visão | 85.2 | 87.1 | 87.4 |
| CLIP | Visão-linguagem | 78.6 | 81.3 | 82.0 |
| Llama3-8B | Raciocínio | 71.2 | 73.8 | 74.1 |

**Implicação:** RandLoRA fecha >90% da lacuna LoRA→Full FT com os mesmos parâmetros treináveis.

### 3.2 Knowledge Distillation (LLM → Modelo Pequeno)

#### 3.2.1 Destilação Multi-Perspectiva para NER

**Paper:** "Multi-Perspective Knowledge Distillation of LLM for NER"
**Fonte:** IGI Global Scientific Publishing, 2025

**Pipeline:**
1. **Professor:** Qwen14B (14B parâmetros)
2. **Geração:** Chain-of-Thought (CoT) para gerar raciocínio intermediário sobre entidades
3. **Alinhamento:** Conhecimento multi-perspectiva (tipo de entidade, contexto, limites)
4. **Estudante:** Modelo NER pequeno com DoRA (variante do LoRA)

**Resultados sobre estado da arte:**

| Métrica | Melhoria |
|---------|----------|
| Precisão | +3.46% |
| Recall | +5.79% |
| F1-score | +2.54% |

**Capacidade adicional:** Desempenho forte em few-shot (dados limitados).

#### 3.2.2 Aplicação ao ContextSafe

Pipeline proposto:
```
GPT-4 / Llama-3-70B (professor)
    ↓ Gera anotações PII com raciocínio CoT
    ↓ Sobre textos legais espanhóis não anotados
Legal-XLM-RoBERTa-base (estudante)
    ↓ Fine-tune com DoRA/LoRA
    ↓ Usando dados gerados + gold labels
Modelo PII implantável (~400MB ONNX)
```

### 3.3 Geração Sintética de Dados com LLMs

#### 3.3.1 Avaliação Rigorosa (EMNLP 2025)

**Paper:** "A Rigorous Evaluation of LLM Data Generation Strategies for NER"
**Venue:** EMNLP 2025 Main Conference (Paper ID: 2025.emnlp-main.418)

**Design experimental:**
- **Idiomas:** 11 (incluindo multilíngue)
- **Tarefas:** 3 diferentes
- **LLMs geradores:** 4 modelos
- **Modelos downstream:** 10 (fine-tuned XLM-R)
- **Métrica:** F1 médio gold vs artificial

**Descobertas chave:**

| Descoberta | Evidência |
|------------|-----------|
| Qualidade > Quantidade | Datasets pequenos, limpos e consistentes superam datasets grandes ruidosos |
| Formato importa | JSONL consistente é crítico para desempenho |
| Efetivo para low-resource | Dados sintéticos viáveis para idiomas sem corpus anotado |
| Comparável ao gold | Em alguns idiomas/tarefas, dados sintéticos atingem 90-95% do desempenho gold |

#### 3.3.2 Cross-lingual NER Zero-shot (EMNLP 2025)

**Paper:** "Zero-shot Cross-lingual NER via Mitigating Language Difference: An Entity-aligned Translation Perspective"
**Venue:** EMNLP 2025

**Técnica:** Tradução alinhada a entidades para transferência cross-lingual. Relevante para expandir ContextSafe a novos idiomas partindo do modelo espanhol.

### 3.4 GLiNER: Zero-Shot NER para PII

**Paper:** "GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer"
**Venue:** NAACL 2024 (modelos PII atualizados setembro 2025, colaboração Wordcab)

**Arquitetura:**
- Encoder bidirecional (BiLM)
- Input: prompts de tipo de entidade + texto
- Output: extração paralela de entidades (vantagem sobre geração sequencial de LLMs)
- Não requer categorias predefinidas: entidades especificadas em runtime

**Modelos PII disponíveis (2025):**

| Modelo | Tamanho | F1 |
|--------|---------|----|
| gliner-pii-edge-v1.0 | ~100MB | ~75% |
| gliner-pii-small-v1.0 | ~200MB | ~78% |
| gliner-pii-base-v1.0 | ~440MB | **80.99%** |
| gliner-pii-large-v1.0 | ~1.3GB | ~80% |

**Integração existente:** GLiNER integra-se com Microsoft Presidio (que ContextSafe já usa).

**Relevância:**
- **Baseline imediata:** 81% F1 sem treinamento, contra a qual medir nosso modelo fine-tuned
- **Ensemble:** Usar GLiNER para categorias PII raras onde não há dados de treinamento
- **Validação cruzada:** Comparar predições GLiNER vs Legal-XLM-R para detectar erros

### 3.5 Abordagens Híbridas (Transformer + Regras)

#### 3.5.1 Hybrid NER para PII em Documentos Financeiros

**Paper:** "A hybrid rule-based NLP and machine learning approach for PII detection and anonymization in financial documents"
**Venue:** Nature Scientific Reports, 2025 (DOI: 10.1038/s41598-025-04971-9)

**Resultados:**

| Métrica | Dataset Sintético | Documentos Reais |
|---------|-------------------|------------------|
| Precisão | **94.7%** | ~93% |
| Recall | 89.4% | ~93% |
| F1-score | 91.1% | ~93% |

**Arquitetura:** Regras NLP + ML + Custom NER, escalável.

#### 3.5.2 RECAP: Regex + LLM Contextual

**Paper:** Apresentado na NeurIPS 2025
**Metodologia:** Regex determinístico + LLMs context-aware para PII multilíngue

**Resultados comparativos:**

| Comparação | Melhoria RECAP |
|------------|----------------|
| vs NER fine-tuned | **+82% F1 ponderado** |
| vs zero-shot LLMs | **+17% F1 ponderado** |

**Benchmark:** nervaluate (avaliação em nível de entidade)

**Implicação para ContextSafe:** Nosso pipeline atual (Regex + Presidio + RoBERTa) já segue esse padrão híbrido. RECAP valida que essa arquitetura é a mais efetiva segundo a evidência de 2025.

### 3.6 Domain Adaptive Pre-Training (DAPT): Revisão Crítica

#### 3.6.1 DAPT Não É Universal

**Paper:** "Continual Pre-Training is (not) What You Need in Domain Adaptation"
**Venue:** ICLR 2025

**Conclusões chave:**

| Cenário | DAPT Ajuda? | Evidência |
|---------|-------------|-----------|
| Vocabulário especializado (legal, médico) | **Sim** | Familiariza com estilo legal |
| Raciocínio lógico (direito civil) | **Sim** | Melhora compreensão de relações |
| Tarefas com dados abundantes | **Não necessariamente** | Fine-tuning direto pode ser suficiente |
| Sem mitigação de catástrofe | **Prejudicial** | Catastrophic forgetting degrada geral |

**Mitigação recomendada:**
- Camadas adapter / LoRA durante DAPT (não full fine-tuning do backbone)
- Unfreezing gradual
- Avaliar ANTES e DEPOIS do DAPT no benchmark NER-PII

#### 3.6.2 ICL-APT: Alternativa Eficiente

**Conceito:** In-Context Learning Augmented Pre-Training

**Pipeline:**
1. Amostrar textos do corpus alvo
2. Recuperar documentos similares do domínio (recuperação semântica)
3. Aumentar contexto com definições, abreviações, terminologia
4. Continuar pré-treinamento com MLM sobre contexto aumentado

**Vantagem:** Mais eficiente com corpus limitado. Não requer milhões de documentos como DAPT tradicional.

**Aplicação:** Para cada documento legal espanhol, recuperar sentenças similares + adicionar definições de categorias PII como contexto de pré-treinamento.

### 3.7 Modelos Legais Espanhóis (Baselines 2025)

#### 3.7.1 MEL (Modelo de Español Legal)

**Paper:** "MEL: Legal Spanish language model"
**Data:** Janeiro 2025 (ArXiv: 2501.16011)

| Aspecto | Detalhe |
|---------|---------|
| Base | XLM-RoBERTa-large |
| Dados treinamento | BOE (Boletim Oficial do Estado), textos congresso |
| Tarefas | Classificação legal, NER |
| F1 macro | ~0.82 (15 labels) |
| Comparação | Supera xlm-roberta-large, legal-xlm-roberta-large, RoBERTalex |

#### 3.7.2 Corpus 3CEL

**Paper:** "3CEL: a Corpus of Legal Spanish Contract Clauses"
**Data:** Janeiro 2025 (ArXiv: 2501.15990)

Corpus de cláusulas contratuais espanholas com anotações. Potencialmente útil como dados de treinamento ou avaliação.

---

## 4. Leituras Prévias Obrigatórias

> **IMPORTANTE:** Antes de executar qualquer fase do plano, o modelo deve ler estes documentos na ordem indicada para entender o contexto completo do projeto, as decisões tomadas e o estado atual.

### 4.1 Nível 0: Identidade e Regras do Projeto

| # | Arquivo | Propósito | Obrigatório |
|---|---------|-----------|-------------|
| 0.1 | `ml/README.md` | Regras operacionais, estrutura de arquivos, fluxo de trabalho | **Sim** |
| 0.2 | `README.md` (raiz projeto) | Arquitetura hexagonal, domínio ContextSafe, pipeline NER, níveis de anonimização | **Sim** |

### 4.2 Nível 1: História do Ciclo ML (ler em ordem cronológica)

Estes documentos narram a evolução completa do modelo NER v2, desde baseline até o estado atual. Sem eles não se entende por que certas decisões foram tomadas.

| # | Arquivo | Conteúdo Chave |
|---|---------|----------------|
| 1.1 | `docs/reports/2026-01-15_estado_proyecto_ner.md` | Estado inicial do projeto NER, modelo v1 vs v2 |
| 1.2 | `docs/reports/2026-01-16_investigacion_pipeline_pii.md` | Investigação pipelines PII existentes |
| 1.3 | `docs/reports/2026-01-28_investigacion_hybrid_ner.md` | Decisão arquitetônica: pipeline híbrido (Regex+ML) |
| 1.4 | `docs/reports/2026-01-28_investigacion_estandares_evaluacion_ner.md` | Adoção SemEval 2013 Task 9 (COR/INC/PAR/MIS/SPU) |
| 1.5 | `docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | **ESSENCIAL** - Ciclo ML completo: 5 elementos integrados, métricas finais (F1 0.788), lições aprendidas |

### 4.3 Nível 2: Os 5 Elementos do Pipeline (detalhe técnico)

Cada elemento documenta uma melhoria concreta integrada em `ner_predictor.py`. Ler se precisar entender ou modificar o pipeline.

| # | Arquivo | Elemento | Impacto |
|---|---------|----------|---------|
| 2.1 | `docs/reports/2026-02-04_text_normalizer_impacto.md` | Elem.1: Normalização de texto | Ruído OCR → texto limpo |
| 2.2 | `docs/reports/2026-02-04_checksum_validators_standalone.md` | Elem.2: Validação checksum | DNI, IBAN, NSS com verificação matemática |
| 2.3 | `docs/reports/2026-02-05_regex_patterns_standalone.md` | Elem.3: Padrões regex espanhóis | Matrículas, CP, telefones |
| 2.4 | `docs/reports/2026-02-05_date_patterns_integration.md` | Elem.4: Datas textuais | "12 de enero de 2024" |
| 2.5 | `docs/reports/2026-02-06_boundary_refinement_integration.md` | Elem.5: Refinamento de limites | PAR→COR (16 parciais corrigidos) |

### 4.4 Nível 3: Investigações para Próxima Fase

Estes relatórios fundamentam as decisões do plano de fine-tuning do Legal-XLM-RoBERTa.

| # | Arquivo | Conteúdo Chave |
|---|---------|----------------|
| 3.1 | `docs/reports/2026-01-29_investigacion_modelos_legales_multilingues.md` | Survey de modelos legais: Legal-BERT, JuriBERT, Legal-XLM-R. Justificativa do Legal-XLM-RoBERTa-base |
| 3.2 | `docs/reports/2026-01-30_investigacion_finetuning_legal_xlm_r.md` | Estratégias DAPT, mDAPT, span masking, hiperparâmetros. Plano original de fine-tuning |
| 3.3 | **Este documento** (`2026-01-31_mejores_practicas_ml_2026.md`) | Atualização 2025-2026: LoRA, RandLoRA, dados sintéticos, GLiNER, DAPT seletivo. **Plano atualizado** |

### 4.5 Nível 4: Designs Pendentes de Implementação

| # | Arquivo | Conteúdo Chave |
|---|---------|----------------|
| 4.1 | `docs/plans/2026-02-04_uncertainty_queue_design.md` | Design Human-in-the-Loop: zonas de confiança (HIGH/UNCERTAIN/LOW), fila de revisão, bloqueio de exportação. **Não implementar em ML**, transferido para projeto principal |

### 4.6 Nível 5: Código Atual (estado do pipeline)

| # | Arquivo | Propósito |
|---|---------|-----------|
| 5.1 | `scripts/inference/ner_predictor.py` | **Pipeline NER Completo** - Integra os 5 elementos, preditor principal |
| 5.2 | `scripts/inference/text_normalizer.py` | Normalização de texto (Elem.1) |
| 5.3 | `scripts/inference/entity_validator.py` | Validação checksum (Elem.2) |
| 5.4 | `scripts/preprocess/boundary_refinement.py` | Refinamento de limites (Elem.5) |
| 5.5 | `scripts/preprocess/checksum_validators.py` | Validadores: DNI, IBAN, NSS, cartões |
| 5.6 | `scripts/evaluate/test_ner_predictor_adversarial_v2.py` | Test set adversarial (35 casos, avaliação SemEval) |
| 5.7 | `scripts/download_legal_xlm_roberta.py` | Script download modelo base |

### 4.7 Nível 6: Modelos Disponíveis

| # | Caminho | Estado |
|---|---------|--------|
| 6.1 | `models/checkpoints/roberta-base-bne-capitel-ner/` | Modelo atual (RoBERTa-BNE CAPITEL NER) |
| 6.2 | `models/legal_ner_v1/` | Modelo v1 (deprecado) |
| 6.3 | `models/legal_ner_v2/` | Modelo v2 atual (F1 0.788 com pipeline completo) |
| 6.4 | `models/pretrained/legal-xlm-roberta-base/` | **Legal-XLM-RoBERTa-base baixado** (184M params, 128K vocab, 1.48GB) |

### 4.8 Ordem de Leitura Recomendada por Tarefa

| Se o modelo vai... | Ler níveis |
|--------------------|------------|
| Continuar o plano de fine-tuning | 0 → 1.5 → 3.1 → 3.2 → 3.3 (este doc) |
| Modificar o pipeline NER | 0 → 1.5 → 2.x (elemento relevante) → 5.1 |
| Avaliar baselines (GLiNER, MEL) | 0 → 1.5 → 3.3 (seção 4.2 Fase 1) → 5.6 |
| Gerar dados sintéticos | 0 → 1.5 → 3.3 (seção 3.3) |
| Implementar DAPT | 0 → 3.1 → 3.2 → 3.3 (seções 3.6 + 4.2 Fase 4) |
| Implementar Uncertainty Queue | 0 → 4.1 (transferir para projeto principal) |

### 4.9 Estado Atual do Projeto (Snapshot 04 Fev 2026)

```
Modelo atual:    legal_ner_v2 (RoBERTa-BNE + 5 elementos pipeline)
F1 strict:        0.788 (SemEval entity-level, test adversarial 35 casos)
Pass rate:        60.0% (lenient 71.4%)
Modelo baixado:   Legal-XLM-RoBERTa-base (184M params, pronto para FT)
Próximo passo:    Estabelecer baselines (GLiNER + MEL) → LoRA fine-tuning
```

---

## 5. Análise de Gaps e Recomendações

### 5.1 O Que Nos Falta (Gap Analysis)

| # | Gap Identificado | Prioridade | Técnica Recomendada | Fonte |
|---|------------------|------------|---------------------|-------|
| **G1** | Nenhuma baseline zero-shot | **Crítico** | Avaliar GLiNER-PII-base no nosso test set | NAACL 2024 |
| **G2** | Fine-tuning planejado como Full FT | **Alto** | Migrar para LoRA r=128, α=256, todas camadas | COLING 2025, ICLR 2025 |
| **G3** | Apenas gold labels para treinamento | **Alto** | Gerar dados sintéticos com LLM (EMNLP 2025) | EMNLP 2025 |
| **G4** | Nenhuma baseline MEL | **Alto** | Avaliar MEL no nosso test set | ArXiv Jan 2025 |
| **G5** | DAPT planejado sem avaliação prévia | **Médio** | Avaliar NER antes/depois DAPT, usar LoRA | ICLR 2025 |
| **G6** | RandLoRA não usado | **Médio** | Se plateau LoRA, migrar para RandLoRA | ICLR 2025 |
| **G7** | Nenhuma knowledge distillation | **Médio** | Pipeline teacher(LLM)→student(XLM-R) com CoT | IGI Global 2025 |
| **G8** | Pipeline híbrido sem validação formal | **Baixo** | Benchmark RECAP para validar arquitetura | NeurIPS 2025 |

### 5.2 Recomendações Ordenadas

#### Fase 1: Estabelecer Baselines (Imediato)

1. **Avaliar GLiNER-PII-base** no nosso test set adversarial
   - F1 esperado: ~81% (benchmark publicado)
   - Se superar nosso modelo atual (F1 0.788): priorizar integração
   - Se não: confirma que nosso pipeline é competitivo

2. **Avaliar MEL** (se disponível) no nosso test set
   - F1 esperado: ~82% (benchmark publicado com 15 labels)
   - Estabelece benchmark legal espanhol

#### Fase 2: Fine-tuning com PEFT (Próximo Ciclo)

3. **Migrar de Full FT para LoRA**
   - Config: r=128, α=256, target=all_layers, lr=2e-4, epochs=3, dropout=0.05
   - Hardware: RTX 5060 Ti 16GB VRAM é suficiente
   - Tamanho adapter: ~50MB (vs ~700MB modelo completo)

4. **Se plateau com LoRA → RandLoRA**
   - Mesmos parâmetros treináveis, rank completo
   - Fecha >90% da lacuna LoRA→Full FT

#### Fase 3: Aumento de Dados (Paralelo à Fase 2)

5. **Gerar dados sintéticos PII com LLM**
   - Professor: GPT-4 ou Llama-3-70B
   - Formato: CoNLL/JSONL consistente
   - Foco: categorias com poucos exemplos (IBAN, NSS, MATRICULA)
   - Validar: comparar F1 com gold vs gold+sintético

6. **Knowledge distillation (opcional)**
   - Apenas se dados limitados persistirem após aumento
   - Pipeline: LLM gera raciocínio CoT → estudante aprende

#### Fase 4: DAPT Seletivo (Após Fase 2-3)

7. **Avaliar NER ANTES DAPT** (baseline)
8. **DAPT com LoRA** (não full backbone FT) sobre corpus BOE
9. **Avaliar NER DEPOIS DAPT** (comparar)
10. **Decisão baseada em evidência:** se DAPT não melhorar >2% F1, descartar

---

## 6. Comparação: Plano Original vs. Plano Atualizado

| Aspecto | Plano Original (Fev 2026) | Plano Atualizado (Pós-Revisão) |
|---------|---------------------------|--------------------------------|
| Fine-tuning | Full FT | **LoRA r=128 / RandLoRA** |
| Dados | Apenas gold labels manuais | **Gold + sintéticos LLM** |
| DAPT | Universal, 1-2 épocas | **Seletivo, avaliar antes/depois** |
| Baseline | Nenhuma | **GLiNER 81% + MEL 82%** |
| Destilação | Não considerada | **Opcional (se dados limitados)** |
| Avaliação | SemEval entity-level | **+ adversarial + cross-lingual** |
| Tamanho adapter | ~700MB (modelo completo) | **~50MB (LoRA adapter)** |
| VRAM requerida | ~8GB (Full FT batch pequeno) | **~4GB (LoRA)** |

---

## 7. Tabela de Evidências

| Paper | Venue | Ano | Técnica | Métrica Chave | URL |
|-------|-------|-----|---------|---------------|-----|
| B2NER | COLING | 2025 | LoRA NER universal | +6.8-12.0 F1 vs GPT-4 | github.com/UmeanNever/B2NER |
| RandLoRA | ICLR | 2025 | Full-rank PEFT | >90% gap LoRA→FT fechado | arxiv.org/abs/2502.00987 |
| Multi-Perspective KD | IGI Global | 2025 | Destilação NER | +2.54% F1, +5.79% Recall | igi-global.com/gateway/article/372672 |
| LLM Data Gen for NER | EMNLP | 2025 | Dados sintéticos | 90-95% desempenho gold | aclanthology.org/2025.emnlp-main.418 |
| GLiNER PII | NAACL+updates | 2024-2025 | Zero-shot PII | 80.99% F1 | huggingface.co/knowledgator/gliner-pii-base-v1.0 |
| Hybrid PII Financial | Nature Sci.Rep | 2025 | Regras+ML PII | 94.7% precisão | doi.org/10.1038/s41598-025-04971-9 |
| RECAP | NeurIPS | 2025 | Regex+LLM PII | +82% vs NER fine-tuned | neurips.cc/virtual/2025/122402 |
| CPT is (not) WYNG | ICLR | 2025 | DAPT seletivo | Não melhora uniformemente | openreview.net/pdf?id=rpi9ARgvXc |
| MEL | ArXiv | 2025 | Espanhol legal | 82% F1 macro (15 labels) | arxiv.org/html/2501.16011 |
| 3CEL | ArXiv | 2025 | Corpus Espanhol legal | Benchmark cláusulas | arxiv.org/html/2501.15990 |
| Financial NER LLaMA-3 | ArXiv | 2026 | LoRA NER Financeiro | 0.894 micro-F1 | arxiv.org/abs/2601.10043 |

---

## 8. Conclusões

### 8.1 Mudanças de Paradigma 2025-2026

1. **PEFT substitui Full Fine-Tuning:** LoRA/RandLoRA é agora o padrão para modelos ≤1B parâmetros. Full FT só é justificado se LoRA não convergir (raro em modelos base).

2. **Dados Sintéticos LLM são Viáveis:** EMNLP 2025 demonstra que dados gerados por LLM podem atingir 90-95% do desempenho de dados gold para NER multilíngue. Isso resolve o gargalo da anotação manual.

3. **DAPT não é Dogma:** ICLR 2025 demonstra que DAPT pode não melhorar e até prejudicar se catastrophic forgetting não for mitigado. Sempre avaliar antes e depois.

4. **Híbrido > Puro ML:** Nature e NeurIPS 2025 confirmam que abordagens híbridas (regras + ML) superam puro ML para PII. ContextSafe já segue essa arquitetura.

5. **Zero-shot NER é Competitivo:** GLiNER atinge 81% F1 sem treinamento. Qualquer modelo fine-tuned deve bater significativamente esse limiar para justificar o esforço.

### 8.2 Impacto no ContextSafe

O pipeline atual do ContextSafe (Regex + Presidio + RoBERTa) está **arquiteturalmente alinhado** com a evidência 2025-2026. Os principais gaps são operacionais:

- **Não usar Full FT** → LoRA/RandLoRA
- **Não depender apenas de gold labels** → dados sintéticos LLM
- **Estabelecer baselines** → GLiNER + MEL antes de fine-tuning
- **DAPT seletivo** → avaliar, não assumir

### 8.3 Trabalho Futuro

| Tarefa | Prioridade | Dependência |
|--------|------------|-------------|
| Avaliar GLiNER-PII no test set ContextSafe | Crítica | Nenhuma |
| Preparar script LoRA fine-tuning (r=128, α=256) | Alta | Modelo baixado (concluído) |
| Gerar dados sintéticos PII com LLM | Alta | Definir categorias alvo |
| Avaliar MEL no test set ContextSafe | Alta | Baixar modelo MEL |
| DAPT seletivo com avaliação pré/pós | Média | Corpus BOE disponível |
| Implementar RandLoRA se plateau | Média | Resultados LoRA |
| Pipeline knowledge distillation | Baixa | Apenas se dados insuficientes |

---

## 9. Referências

1. UmeanNever et al. "B2NER: Beyond Boundaries: Learning Universal Entity Taxonomy across Datasets and Languages for Open Named Entity Recognition." COLING 2025. GitHub: github.com/UmeanNever/B2NER

2. Koo et al. "RandLoRA: Full-Rank Parameter-Efficient Fine-Tuning of Large Models." ICLR 2025. ArXiv: 2502.00987

3. "Multi-Perspective Knowledge Distillation of LLM for Named Entity Recognition." IGI Global Scientific Publishing, 2025. igi-global.com/gateway/article/372672

4. "A Rigorous Evaluation of LLM Data Generation Strategies for NER." EMNLP 2025 Main Conference. Paper ID: 2025.emnlp-main.418

5. Urchade Zaratiana et al. "GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer." NAACL 2024. Modelos PII: knowledgator/gliner-pii-base-v1.0 (atualizado Set 2025).

6. "A hybrid rule-based NLP and machine learning approach for PII detection and anonymization in financial documents." Nature Scientific Reports, 2025. DOI: 10.1038/s41598-025-04971-9

7. "RECAP: Deterministic Regex + Context-Aware LLMs for Multilingual PII Detection." NeurIPS 2025. neurips.cc/virtual/2025/122402

8. "Continual Pre-Training is (not) What You Need in Domain Adaptation." ICLR 2025. openreview.net/pdf?id=rpi9ARgvXc

9. "MEL: Legal Spanish language model." ArXiv, Janeiro 2025. arxiv.org/html/2501.16011

10. "3CEL: a Corpus of Legal Spanish Contract Clauses." ArXiv, Janeiro 2025. arxiv.org/html/2501.15990

11. "Instruction Finetuning LLaMA-3-8B Model Using LoRA for Financial Named Entity Recognition." ArXiv, Janeiro 2026. arxiv.org/abs/2601.10043

12. Unsloth Documentation. "LoRA Fine-tuning Hyperparameters Guide." unsloth.ai/docs (2025).

13. Gretel.ai. "GLiNER Models for PII Detection." gretel.ai/blog (2025).

14. Microsoft Presidio. "Using GLiNER with Presidio." microsoft.github.io/presidio (2025).

---

**Gerado por:** AlexAlves87
**Data:** 31-01-2026
**Revisão:** 1.1 (adicionado seção 4: Leituras Prévias Obrigatórias)
**Próximo passo:** Estabelecer baselines (GLiNER + MEL) antes de iniciar fine-tuning
