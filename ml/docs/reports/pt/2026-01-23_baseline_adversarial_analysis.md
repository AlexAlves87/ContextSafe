# Análise Adversarial Baseline: legal_ner_v2

**Data:** 23-01-2026
**Autor:** AlexAlves87
**Versão:** 1.0.0
**Modelo Avaliado:** `legal_ner_v2` (RoBERTalex fine-tuned)

---

## 1. Resumo Executivo

Este documento apresenta os resultados da avaliação adversarial do modelo `legal_ner_v2` para deteção de PII em textos legais espanhóis. O objetivo é estabelecer uma linha de base de robustez antes de implementar melhorias.

### Principais Descobertas

| Métrica | Valor | Interpretação |
|---------|-------|----------------|
| F1-Score (ao nível da entidade) | **0.784** | Baseline aceitável |
| Precisão | 0.845 | Modelo conservador |
| Revocação | 0.731 | Área de melhoria prioritária |
| Degradação pelo ruído | 0.080 | Dentro do limiar esperado (≤0.10) |
| Taxa de aprovação nos testes | 54.3% (19/35) | Nível 4 não superado |

### Conclusão

O modelo **NÃO supera** o Nível 4 de validação (adversarial). São necessárias melhorias em:
1. Normalização de entrada (Unicode, espaços)
2. Reconhecimento de datas em formato textual espanhol
3. Padrões específicos para NSS e CIF

---

## 2. Metodologia

### 2.1 Desenho Experimental

Foram desenhados 35 casos de teste adversarial distribuídos em 5 categorias:

| Categoria | Testes | Objetivo |
|-----------|-------|-----------|
| `edge_case` | 9 | Condições limite (nomes longos, formatos variantes) |
| `adversarial` | 8 | Casos desenhados para confundir (negações, exemplos) |
| `ocr_corruption` | 5 | Simulação de erros OCR |
| `unicode_evasion` | 3 | Tentativas de evasão com caracteres semelhantes |
| `real_world` | 10 | Extratos de documentos legais reais |

### 2.2 Níveis de Dificuldade

| Nível | Critério de Sucesso | Testes |
|-------|-------------------|-------|
| `easy` | Detetar todas as entidades esperadas | 4 |
| `medium` | Detetar todas as entidades esperadas | 12 |
| `hard` | Detetar todas as entidades E zero falsos positivos | 19 |

### 2.3 Métricas Utilizadas

1. **F1 ao nível da entidade** (estilo seqeval): Precisão, Revocação, F1 calculados ao nível da entidade completa, não token.

2. **Pontuação de Sobreposição**: Rácio de caracteres coincidentes entre entidade esperada e detetada (Jaccard sobre caracteres).

3. **Degradação pelo Ruído** (estilo NoiseBench): Diferença de F1 entre categorias "limpas" (`edge_case`, `adversarial`, `real_world`) e "ruidosas" (`ocr_corruption`, `unicode_evasion`).

### 2.4 Ambiente de Execução

| Componente | Especificação |
|------------|----------------|
| Hardware | CUDA (GPU) |
| Modelo | `legal_ner_v2` (RoBERTalex) |
| Framework | PyTorch 2.0+, Transformers |
| Tempo de carga | 1.6s |
| Tempo de avaliação | 1.5s (35 testes) |

### 2.5 Reprodutibilidade

```bash
cd ml
source .venv/bin/activate
python scripts/evaluate/test_ner_predictor_adversarial.py
```

O script gera automaticamente um relatório em `docs/reports/`.

---

## 3. Resultados

### 3.1 Métricas Agregadas

| Métrica | Valor |
|---------|-------|
| Verdadeiros Positivos | 49 |
| Falsos Positivos | 9 |
| Falsos Negativos | 18 |
| **Precisão** | 0.845 |
| **Revocação** | 0.731 |
| **F1-Score** | 0.784 |
| Pontuação Média de Sobreposição | 0.935 |

### 3.2 Resultados por Categoria

| Categoria | Taxa de Aprovação | TP | FP | FN | F1 |
|-----------|-----------|----|----|----|----|
| adversarial | 75.0% | 5 | 2 | 0 | 0.833 |
| edge_case | 66.7% | 9 | 1 | 3 | 0.818 |
| ocr_corruption | 40.0% | 5 | 0 | 4 | 0.714 |
| real_world | 40.0% | 26 | 5 | 9 | 0.788 |
| unicode_evasion | 33.3% | 4 | 1 | 2 | 0.727 |

### 3.3 Resultados por Dificuldade

| Dificuldade | Aprovados | Total | Taxa |
|------------|---------|-------|------|
| easy | 3 | 4 | 75.0% |
| medium | 9 | 12 | 75.0% |
| hard | 7 | 19 | 36.8% |

### 3.4 Análise de Resistência ao Ruído

| Métrica | Valor | Referência |
|---------|-------|------------|
| F1 (texto limpo) | 0.800 | - |
| F1 (com ruído) | 0.720 | - |
| **Degradação** | 0.080 | ≤0.10 (HAL Science) |
| Estado | **OK** | Dentro do limiar |

---

## 4. Análise de Erros

### 4.1 Taxonomia de Falhas

Foram identificados 5 padrões de falha recorrentes:

#### Padrão 1: Datas em Formato Textual Espanhol

| Teste | Entidade Perdida |
|------|-----------------|
| `date_roman_numerals` | "XV de marzo del año MMXXIV" |
| `notarial_header` | "quince de marzo de dos mil veinticuatro" |
| `judicial_sentence_header` | "diez de enero de dos mil veinticuatro" |

**Causa raiz:** O modelo foi treinado principalmente com datas em formato numérico (DD/MM/AAAA). As datas escritas em estilo notarial espanhol não estão representadas no corpus de treino.

**Impacto:** Alto em documentos notariais e judiciais onde este formato é padrão.

#### Padrão 2: Corrupção OCR Extrema

| Teste | Entidade Perdida |
|------|-----------------|
| `ocr_extra_spaces` | "1 2 3 4 5 6 7 8 Z", "M a r í a" |
| `ocr_missing_spaces` | "12345678X" (em texto concatenado) |
| `ocr_zero_o_confusion` | "ES91 21O0 0418 45O2 OOO5 1332" |

**Causa raiz:** O tokenizador do RoBERTa não lida bem com texto com espaçamento anómalo. A confusão O/0 quebra padrões regex de IBAN.

**Impacto:** Médio. Documentos digitalizados de baixa qualidade.

#### Padrão 3: Evasão Unicode

| Teste | Entidade Perdida |
|------|-----------------|
| `fullwidth_numbers` | "１２３４５６７８Z" (U+FF11-U+FF18) |

**Causa raiz:** Não há normalização Unicode prévia ao NER. Os dígitos de largura total (U+FF10-U+FF19) não são reconhecidos como números.

**Impacto:** Baixo em produção, mas crítico para segurança (evasão intencional).

#### Padrão 4: Identificadores Específicos Espanhóis

| Teste | Entidade Perdida |
|------|-----------------|
| `social_security` | "281234567890" (NSS) |
| `bank_account_clause` | "A-98765432" (CIF) |
| `professional_ids` | "12345", "67890" (números de ordem) |

**Causa raiz:** Padrões pouco frequentes no corpus de treino. O NSS espanhol tem formato específico (12 dígitos) que não foi aprendido.

**Impacto:** Alto para documentos laborais e mercantis.

#### Padrão 5: Falsos Positivos por Contexto

| Teste | Entidade Falsa |
|------|---------------|
| `example_dni` | "12345678X" (contexto: "exemplo ilustrativo") |
| `fictional_person` | "Don Quijote de la Mancha" |

**Causa raiz:** O modelo deteta padrões sem considerar o contexto semântico (negações, exemplos, ficção).

**Impacto:** Médio. Causa anonimização desnecessária.

### 4.2 Matriz de Confusão por Tipo de Entidade

| Tipo | TP | FP | FN | Observação |
|------|----|----|----|----|
| PERSON | 15 | 2 | 2 | Bom, falha em ficção |
| DNI_NIE | 8 | 1 | 4 | Falha em formatos variantes |
| LOCATION | 6 | 0 | 2 | Falha em códigos postais isolados |
| DATE | 3 | 0 | 4 | Falha em formato textual |
| IBAN | 2 | 0 | 1 | Falha com OCR |
| ORGANIZATION | 5 | 2 | 0 | Confunde com tribunais |
| NSS | 0 | 0 | 1 | Não deteta |
| PROFESSIONAL_ID | 0 | 0 | 2 | Não deteta |
| Outros | 10 | 4 | 2 | - |

---

## 5. Conclusões

### 5.1 Estado Atual

O modelo `legal_ner_v2` apresenta um **F1 de 0.784** em avaliação adversarial, com as seguintes características:

- **Pontos Fortes:**
  - Alta precisão (0.845) - poucos falsos positivos
  - Boa resistência ao ruído (degradação 0.080)
  - Excelente em nomes compostos e moradas

- **Pontos Fracos:**
  - Revocação insuficiente (0.731) - perde entidades
  - Não reconhece datas em formato textual espanhol
  - Vulnerável a evasão Unicode (largura total)
  - Não deteta NSS nem números de ordem

### 5.2 Nível de Validação

| Nível | Estado | Critério |
|-------|--------|----------|
| Nível 1: Testes Unitários | ✅ | Funções individuais |
| Nível 2: Integração | ✅ | Pipeline completo |
| Nível 3: Benchmark | ✅ | F1 > 0.75 |
| **Nível 4: Adversarial** | ❌ | Taxa de aprovação < 70% |
| Nível 5: Semelhante a Prod | ⏸️ | Pendente |

**Conclusão:** O modelo **NÃO está pronto para produção** segundo critérios do projeto (Nível 4 obrigatório).

### 5.3 Trabalho Futuro

#### Prioridade ALTA (impacto estimado > 3pts F1)

1. **Normalização Unicode em pré-processamento**
   - Converter largura total para ASCII
   - Remover caracteres de largura zero
   - Normalizar O/0 em contextos numéricos

2. **Aumentação de datas textuais**
   - Gerar variantes: "primero de enero", "XV de marzo"
   - Incluir numerais romanos
   - Fine-tune com corpus aumentado

3. **Padrões regex para NSS/CIF**
   - Adicionar ao CompositeNerAdapter
   - NSS: `\d{12}` em contexto "Seguridad Social"
   - CIF: `[A-Z]-?\d{8}` em contexto empresa

#### Prioridade MÉDIA (impacto estimado 1-3pts F1)

4. **Normalização de espaços OCR**
   - Detetar e colapsar espaços excessivos
   - Reconstruir tokens fragmentados

5. **Filtro pós-processo para contextos "exemplo"**
   - Detetar frases: "por exemplo", "ilustrativo", "formato"
   - Suprimir entidades nesses contextos

#### Prioridade BAIXA (casos limite)

6.  **Gazetteer de personagens fictícios**
   - Don Quijote, Sancho Panza, etc.
   - Filtro pós-processo

7. **Datas com numerais romanos**
   - Regex específico para estilo notarial antigo

---

## 6. Referências

1. **seqeval** - Métricas de avaliação ao nível da entidade para rotulagem de sequência. https://github.com/chakki-works/seqeval

2. **NoiseBench (ICLR 2024)** - Benchmark para avaliar modelos NLP sob condições de ruído realistas.

3. **HAL Science** - Estudo sobre impacto de OCR em tarefas NER. Estabelece degradação esperada de ~10pts F1.

4. **RoBERTalex** - Modelo RoBERTa domínio legal espanhol. Base do modelo avaliado.

5. **Diretrizes do projeto v1.0.0** - Metodologia de preparação ML para ContextSafe.

---

## Anexos

### A. Configuração do Teste

```yaml
total_tests: 35
categories:
  edge_case: 9
  adversarial: 8
  ocr_corruption: 5
  unicode_evasion: 3
  real_world: 10
difficulty_distribution:
  easy: 4
  medium: 12
  hard: 19
```

### B. Comando de Reprodução

```bash
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate
python scripts/evaluate/test_ner_predictor_adversarial.py
```

### C. Ficheiros Gerados

- Relatório automático: `docs/reports/2026-01-23_adversarial_ner_v2.md`
- Análise académica: `docs/reports/2026-01-23_baseline_adversarial_analysis.md` (este documento)

---

**Tempo de execução total:** 3.1s (carga + avaliação)
**Gerado por:** AlexAlves87
**Data:** 23-01-2026
