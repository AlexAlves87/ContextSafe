# Baseline Acadêmico: Avaliação com Padrões SemEval 2013

**Data:** 03-02-2026
**Autor:** AlexAlves87
**Modelo:** legal_ner_v2 (RoBERTalex fine-tuned)
**Padrão:** SemEval 2013 Task 9

---

## 1. Resumo Executivo

Esta avaliação estabelece o **baseline real** do modelo usando padrões acadêmicos (modo strict do SemEval 2013), substituindo os resultados anteriores que usavam matching lenient.

### Comparação v1 vs v2

| Métrica | v1 (lenient) | v2 (strict) | Diferença |
|---------|--------------|-------------|-----------|
| **Pass Rate** | 54.3% | **28.6%** | **-25.7pp** |
| **F1-Score** | 0.784 | **0.464** | **-0.320** |
| F1 (parcial) | - | 0.632 | - |

### Conclusão Principal

> **Os resultados anteriores (F1=0.784, 54.3%) estavam INFLADOS.**
> O baseline real com padrões acadêmicos é **F1=0.464, 28.6% pass rate**.

---

## 2. Metodologia

### 2.1 Design Experimental

| Aspecto | Especificação |
|---------|---------------|
| Modelo avaliado | `legal_ner_v2` (RoBERTalex fine-tuned) |
| Framework | PyTorch 2.0+, Transformers |
| Hardware | CUDA (GPU) |
| Padrão de avaliação | SemEval 2013 Task 9 |
| Modo principal | Strict (limite + tipo exatos) |

### 2.2 Dataset de Avaliação

| Categoria | Testes | Propósito |
|-----------|--------|-----------|
| edge_case | 9 | Condições limite (nomes longos, formatos variantes) |
| adversarial | 8 | Casos projetados para confundir (negações, exemplos) |
| ocr_corruption | 5 | Simulação de erros OCR |
| unicode_evasion | 3 | Tentativas de evasão com caracteres Unicode |
| real_world | 10 | Extratos de documentos legais reais |
| **Total** | **35** | - |

### 2.3 Métricas Utilizadas

Segundo SemEval 2013 Task 9:

| Métrica | Definição |
|---------|-----------|
| COR | Correto: limite E tipo exatos |
| INC | Incorreto: limite exato, tipo incorreto |
| PAR | Parcial: limite sobreposto, qualquer tipo |
| MIS | Ausente: entidade gold não detectada (FN) |
| SPU | Espúrio: detecção sem correspondência gold (FP) |

**Fórmulas:**
- Precisão (strict) = COR / (COR + INC + PAR + SPU)
- Recall (strict) = COR / (COR + INC + PAR + MIS)
- F1 (strict) = 2 × P × R / (P + R)

### 2.4 Reprodutibilidade

```bash
# Ambiente
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Dependências
pip install nervaluate  # Opcional, métricas implementadas manualmente

# Execução
python scripts/evaluate/test_ner_predictor_adversarial_v2.py

# Saída
# - Console: Resultados por teste com COR/INC/PAR/MIS/SPU
# - Relatório: docs/reports/YYYY-MM-DD_adversarial_v2_academic_rN.md
```

### 2.5 Diferença com Avaliação v1

| Aspecto | v1 (lenient) | v2 (strict) |
|---------|--------------|-------------|
| Matching | Contenção + 80% sobreposição caracteres | Limite exato normalizado |
| Tipo | Requerido | Requerido |
| Métricas | TP/FP/FN | COR/INC/PAR/MIS/SPU |
| Padrão | Personalizado | SemEval 2013 Task 9 |

---

## 3. Resultados

### 3.1 Contagens SemEval 2013

| Métrica | Valor | Descrição |
|---------|-------|-----------|
| **COR** | 29 | Corretos (limite + tipo exatos) |
| **INC** | 0 | Limite correto, tipo incorreto |
| **PAR** | 21 | Correspondência parcial (apenas sobreposição) |
| **MIS** | 17 | Perdidos (FN) |
| **SPU** | 8 | Espúrios (FP) |
| **POS** | 67 | Total gold (COR+INC+PAR+MIS) |
| **ACT** | 58 | Total sistema (COR+INC+PAR+SPU) |

### 3.2 Interpretação

```
                    ┌─────────────────────────────────┐
                    │     GOLD: 67 entidades          │
                    │                                 │
  ┌─────────────────┼─────────────────┐               │
  │                 │    COR: 29      │               │
  │   SISTEMA: 58   │  (43% de gold)  │   MIS: 17     │
  │                 │                 │   (25%)       │
  │    SPU: 8       │    PAR: 21      │               │
  │    (14%)        │   (31% overlap) │               │
  └─────────────────┴─────────────────┴───────────────┘
```

**Análise:**
- Apenas **43%** das entidades gold são detectadas com limite exato
- **31%** são detectadas com sobreposição parcial (v1 contava como corretas)
- **25%** são completamente perdidas
- **14%** das detecções são falsos positivos

### 3.3 Fórmulas Aplicadas

**Modo Strict:**
```
Precisão = COR / ACT = 29 / 58 = 0.500
Recall = COR / POS = 29 / 67 = 0.433
F1 = 2 * P * R / (P + R) = 0.464
```

**Modo Parcial:**
```
Precisão = (COR + 0.5*PAR) / ACT = (29 + 10.5) / 58 = 0.681
Recall = (COR + 0.5*PAR) / POS = (29 + 10.5) / 67 = 0.590
F1 = 2 * P * R / (P + R) = 0.632
```

---

### 3.4 Resultados por Categoria

| Categoria | Strict | Lenient | COR | PAR | MIS | SPU |
|-----------|--------|---------|-----|-----|-----|-----|
| adversarial | 75% | 75% | 5 | 1 | 0 | 3 |
| edge_case | 22% | 67% | 6 | 3 | 3 | 1 |
| ocr_corruption | 40% | 40% | 4 | 1 | 4 | 0 |
| real_world | 10% | 50% | 12 | 14 | 8 | 4 |
| unicode_evasion | 0% | 33% | 3 | 1 | 2 | 1 |

**Observações:**
- **real_world**: Maior discrepância strict vs lenient (10% vs 50%) - muitos PAR
- **unicode_evasion**: 0% strict - todas as detecções são parciais ou incorretas
- **adversarial**: Igual em ambos os modos - testes de não-detecção

---

### 3.5 Resultados por Dificuldade

| Dificuldade | Strict | Lenient |
|-------------|--------|---------|
| fácil | 50% | 75% |
| médio | 42% | 75% |
| difícil | 16% | 42% |

**Observação:** A diferença strict vs lenient aumenta com a dificuldade.

---

## 4. Análise de Erros

### 4.1 Correspondências Parciais (PAR)

As 21 correspondências parciais representam detecções onde o limite não é exato:

| Tipo de PAR | Exemplos | Causa |
|-------------|----------|-------|
| Nome incompleto | "José María" vs "José María de la Santísima..." | RoBERTa trunca nomes longos |
| IBAN com espaços | "ES91 2100..." vs "ES912100..." | Normalização de espaços |
| Endereço parcial | "Calle Mayor 15" vs "Calle Mayor 15, 3º B" | Limite exclui piso/porta |
| Pessoa no contexto | "John Smith" vs "Mr. John Smith" | Prefixos não incluídos |

**Implicação:** O modelo detecta a entidade mas com limites imprecisos.

---

### 4.2 Testes Falhados (Strict)

#### 4.2.1 Por SPU (Falsos Positivos)

| Teste | SPU | Entidades Espúrias |
|-------|-----|--------------------|
| example_dni | 1 | "12345678X" (exemplo em contexto) |
| fictional_person | 1 | "Don Quijote de la Mancha" |
| date_ordinal | 1 | "El" |
| zero_width_space | 1 | "de" |
| judicial_sentence_header | 2 | Referências legais |
| professional_ids | 1 | Associação profissional |
| ecli_citation | 1 | Tribunal |

#### 4.2.2 Por MIS (Entidades Perdidas)

| Teste | MIS | Entidades Perdidas |
|-------|-----|--------------------|
| dni_with_spaces | 1 | "12 345 678 Z" |
| phone_international | 1 | "0034612345678" |
| date_roman_numerals | 1 | "XV de marzo del año MMXXIV" |
| ocr_zero_o_confusion | 1 | IBAN com O/0 |
| ocr_extra_spaces | 2 | DNI e nome com espaços |
| fullwidth_numbers | 2 | DNI fullwidth, nome |
| notarial_header | 1 | Data textual |

---

## 5. Conclusões e Trabalho Futuro

### 5.1 Prioridades de Melhoria

| Melhoria | Impacto em COR | Impacto em PAR→COR |
|----------|----------------|--------------------|
| Normalização de texto (Unicode) | +2-4 COR | +2-3 PAR→COR |
| Validação de checksum | Reduz SPU | - |
| Refinamento de limites | - | +10-15 PAR→COR |
| Augmentação de data | +3-5 COR | - |

### 5.2 Objetivo Revisto

| Métrica | Atual | Objetivo Nível 4 |
|---------|-------|------------------|
| F1 (strict) | 0.464 | **≥ 0.70** |
| Pass rate (strict) | 28.6% | **≥ 70%** |

**Gap a fechar:** +0.236 F1, +41.4pp pass rate

---

### 5.3 Próximos Passos

1. **Reavaliar** com TextNormalizer integrado (já preparado)
2. **Implementar** refinamento de limites para reduzir PAR
3. **Adicionar** validação de checksum para reduzir SPU
4. **Aumentar** dados para datas textuais para reduzir MIS

---

### 5.4 Lições Aprendidas

1. **Lenient matching infla significativamente os resultados** (F1 0.784 → 0.464)
2. **PAR é um problema maior que MIS** (21 vs 17) - limites imprecisos
3. **Testes reais (real_world) têm mais PAR** - documentos complexos
4. **Evasão Unicode não passa nenhum teste strict** - área crítica

### 5.5 Valor do Padrão Acadêmico

Avaliação com SemEval 2013 permite:
- Comparação com literatura acadêmica
- Diagnóstico granular (COR/INC/PAR/MIS/SPU)
- Identificação precisa de áreas de melhorar
- Medição honesta do progresso

---

## 6. Referências

1. **SemEval 2013 Task 9**: Segura-Bedmar et al. "Extraction of Drug-Drug Interactions from Biomedical Texts"
2. **nervaluate**: https://github.com/MantisAI/nervaluate
3. **Blog David Batista**: https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/

---

**Tempo de avaliação:** 1.3s
**Gerado por:** AlexAlves87
**Data:** 03-02-2026
