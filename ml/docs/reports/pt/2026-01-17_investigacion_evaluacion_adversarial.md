# Pesquisa: Melhores Práticas para Avaliação Adversarial de NER

**Data:** 2026-01-17
**Objetivo:** Fundamentar metodologia de avaliação adversarial antes de implementar scripts

---

## 1. Resumo Executivo

A literatura acadêmica recente (2024-2025) estabelece que a avaliação adversarial de modelos NER deve considerar:

1. **Ruído Real vs Simulado** - O ruído real é significativamente mais difícil que o simulado.
2. **Avaliação a Nível de Entidade** - Não a nível de token.
3. **Múltiplas Categorias de Perturbação** - OCR, Unicode, contexto, formato.
4. **Métricas Padrão** - seqeval com F1, Precisão, Recall por tipo de entidade.

---

## 2. Fontes Consultadas

### 2.1 NoiseBench (Maio 2024)

**Fonte:** [NoiseBench: Benchmarking the Impact of Real Label Noise on NER](https://arxiv.org/abs/2405.07609)

**Principais Descobertas:**
- O ruído real (erros humanos, crowdsourcing, LLM) é **significativamente mais difícil** que o ruído simulado.
- Os modelos state-of-the-art "ficam muito aquém do seu limite superior teoricamente alcançável".
- 6 tipos de ruído real devem ser avaliados: erros de especialistas, erros de crowdsourcing, erros de anotação automática, erros LLM.

**Aplicação ao nosso projeto:**
- Nossos testes incluem ruído OCR real (confusão l/I, 0/O) ✓
- Devemos adicionar testes com erros de anotação automática.

### 2.2 Context-Aware Adversarial Training for NER (MIT TACL)

**Fonte:** [Context-aware Adversarial Training for Name Regularity Bias](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00386/102846)

**Principais Descobertas:**
- Modelos NER mostram "Name Regularity Bias" - dependem muito do nome e não do contexto.
- BERT fine-tuned supera significativamente LSTM-CRF em testes de viés.
- Treinamento adversarial com vetores de ruído aprendíveis melhora a capacidade contextual.

**Aplicação ao nosso projeto:**
- Nossos testes `negation_dni`, `example_dni`, `fictional_person` avaliam capacidade contextual ✓
- O modelo v2 (treinado com ruído) deve ser mais robusto.

### 2.3 OCR Impact on NER (HAL Science)

**Fonte:** [Assessing and Minimizing the Impact of OCR Quality on NER](https://hal.science/hal-03026931/document)

**Principais Descobertas:**
- Ruído OCR causa uma perda de ~10 pontos F1 (72% vs 82% em texto limpo).
- Deve ser avaliado com "vários níveis e tipos de ruído OCR".
- Primeiro estudo sistemático do impacto de OCR em NER multilíngue.

**Aplicação ao nosso projeto:**
- Nossos testes OCR (5 casos) são insuficientes - a literatura recomenda mais níveis.
- Objetivo realista: aceitar ~10 pontos de degradação com OCR.

### 2.4 seqeval - Métricas Padrão

**Fonte:** [seqeval - Sequence Labeling Evaluation](https://github.com/chakki-works/seqeval)

**Principais Descobertas:**
- Avaliação a nível de **entidade**, não token.
- Métricas: Precisão, Recall, F1 por tipo e média macro/micro.
- Modo strict vs lenient para correspondência.

**Aplicação ao nosso projeto:**
- Nosso script usa correspondência fuzzy com tolerância de ±5 caracteres (adequado).
- Devemos reportar métricas por tipo de entidade, não apenas aprovado/reprovado.

### 2.5 Enterprise Robustness Benchmark (2025)

**Fonte:** [Evaluating Robustness of LLMs in Enterprise Applications](https://arxiv.org/html/2601.06341)

**Principais Descobertas:**
- Perturbações menores podem reduzir o desempenho em até **40 pontos percentuais**.
- Deve-se avaliar: edições de texto, mudanças de formatação, entradas multilíngues, variações posicionais.
- Modelos de 4B-120B parâmetros mostram todos vulnerabilidades.

**Aplicação ao nosso projeto:**
- Nossos testes cobrem edições de texto e formatação ✓
- Devemos considerar testes multilíngues (nomes estrangeiros).

---

## 3. Taxonomia de Testes Adversariais (Literatura)

| Categoria | Subcategoria | Exemplo | Nossa Cobertura |
|-----------|--------------|---------|------------------|
| **Ruído de Rótulo** | Erros de especialistas | Anotação incorreta | ❌ N/A (inferência) |
| | Crowdsourcing | Inconsistências | ❌ N/A (inferência) |
| | Erros LLM | Alucinações | ❌ N/A (inferência) |
| **Ruído de Entrada** | Corrupção OCR | l/I, 0/O, espaços | ✅ 5 testes |
| | Evasão Unicode | Cirílico, fullwidth | ✅ 3 testes |
| | Variação de formato | D.N.I. vs DNI | ✅ Incluído |
| **Contexto** | Negação | "NÃO ter DNI" | ✅ 1 teste |
| | Exemplo/ilustrativo | "exemplo: 12345678X" | ✅ 1 teste |
| | Ficcional | Dom Quixote | ✅ 1 teste |
| | Referências legais | Lei 15/2022 | ✅ 1 teste |
| **Casos Limite** | Entidades longas | Nomes nobres | ✅ 1 teste |
| | Entidades curtas | J. García | ✅ 1 teste |
| | Entidades espaçadas | IBAN com espaços | ✅ 2 testes |
| **Mundo Real** | Padrões de documentos | Notarial, judicial | ✅ 10 testes |

---

## 4. Métricas Recomendadas

### 4.1 Métricas Primárias (seqeval)

| Métrica | Descrição | Uso |
|---------|-------------|-----|
| **F1 Macro** | Média F1 por tipo de entidade | Métrica principal |
| **F1 Micro** | F1 global (todas as entidades) | Métrica secundária |
| **Precisão** | TP / (TP + FP) | Avaliar falsos positivos |
| **Recall** | TP / (TP + FN) | Avaliar entidades perdidas |

### 4.2 Métricas Adversariais

| Métrica | Descrição | Alvo |
|---------|-------------|----------|
| **Taxa de Aprovação** | Testes aprovados / Total | ≥70% |
| **Degradação OCR** | F1_limpo - F1_ocr | ≤10 pontos |
| **Sensibilidade Contextual** | % testes contextuais corretos | ≥80% |
| **Taxa FP** | Falsos positivos / Detecções | ≤15% |

---

## 5. Lacunas Identificadas em Nosso Script

| Lacuna | Severidade | Ação |
|-----|-----------|--------|
| Nenhum relatório F1/Precisão/Recall por tipo | Média | Adicionar métricas seqeval |
| Poucos testes OCR (5) vs recomendado (10+) | Média | Expandir na próxima iteração |
| Não avalia degradação vs baseline | Alta | Comparar com testes limpos |
| Sem testes multilíngues | Baixa | Adicionar nomes estrangeiros |

---

## 6. Recomendações para Nosso Script

### 6.1 Melhorias Imediatas

1. **Adicionar métricas seqeval** - Precisão, Recall, F1 por tipo de entidade.
2. **Calcular degradação** - Comparar com versão limpa de cada teste.
3. **Reportar taxa FP** - Falsos positivos como métrica separada.

### 6.2 Melhorias Futuras

1. Expandir testes OCR para 10+ casos com diferentes níveis de corrupção.
2. Adicionar testes com nomes estrangeiros (John Smith, Mohammed Ali).
3. Implementar avaliação estilo NoiseBench com ruído graduado.

---

## 7. Conclusão

O script atual cobre as principais categorias de avaliação adversarial de acordo com a literatura, mas deve:

1. **Melhorar métricas** - Usar seqeval para F1/P/R por tipo.
2. **Expandir OCR** - Mais níveis de corrupção.
3. **Calcular degradação** - vs baseline limpo.

**O script atual é VÁLIDO para avaliação inicial**, mas deve ser iterado para cumprir totalmente as melhores práticas acadêmicas.

---

## Referências

1. [NoiseBench: Benchmarking the Impact of Real Label Noise on NER](https://arxiv.org/abs/2405.07609) - ICLR 2024
2. [Context-aware Adversarial Training for Name Regularity Bias](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00386/102846) - MIT TACL
3. [Assessing and Minimizing the Impact of OCR Quality on NER](https://hal.science/hal-03026931/document) - HAL Science
4. [seqeval - Sequence Labeling Evaluation](https://github.com/chakki-works/seqeval) - GitHub
5. [Evaluating Robustness of LLMs in Enterprise Applications](https://arxiv.org/html/2601.06341) - arXiv 2025
6. [nervaluate - Entity-level NER Evaluation](https://github.com/MantisAI/nervaluate) - Based on SemEval'13

---

**Autor:** AlexAlves87
**Data:** 2026-01-17
