# Avaliação Adversarial v2 (Padrões Acadêmicos) - legal_ner_v2

**Data:** 06-02-2026
**Modelo:** legal_ner_v2
**Testes:** 35
**Tempo total:** 1.5s
**Padrão:** SemEval 2013 Task 9

---

## 1. Resumo Executivo

### 1.1 Métricas SemEval 2013 (Modo Strict)

| Métrica | Valor |
|---------|-------|
| **F1 (strict)** | **0.788** |
| Precisão (strict) | 0.800 |
| Recall (strict) | 0.776 |
| F1 (parcial) | 0.826 |

### 1.2 Contagens SemEval

| Métrica | Valor | Descrição |
|---------|-------|-----------|
| COR | 52 | Corretos (limite + tipo exatos) |
| INC | 1 | Limite correto, tipo incorreto |
| PAR | 5 | Correspondência parcial (sobreposição) |
| MIS | 9 | Perdidos (FN) |
| SPU | 7 | Espúrios (FP) |
| **POS** | 67 | Total gold (COR+INC+PAR+MIS) |
| **ACT** | 65 | Total sistema (COR+INC+PAR+SPU) |

### 1.3 Taxa de Aprovação

| Modo | Aprovados | Total | Taxa |
|------|-----------|-------|------|
| **Strict** | 21 | 35 | **60.0%** |
| Lenient (v1) | 25 | 35 | 71.4% |

---

## 2. Métricas por Tipo de Entidade

| Tipo | COR | MIS | SPU | Precisão | Recall | F1 |
|------|-----|-----|-----|----------|--------|----|
| ADDRESS | 2 | 1 | 1 | 0.67 | 0.67 | 0.67 |
| CADASTRAL_REF | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| CIF | 0 | 0 | 1 | 0.00 | 0.00 | 0.00 |
| DATE | 4 | 0 | 1 | 0.80 | 1.00 | 0.89 |
| DNI_NIE | 10 | 3 | 1 | 0.91 | 0.77 | 0.83 |
| ECLI | 1 | 1 | 1 | 0.50 | 0.50 | 0.50 |
| IBAN | 1 | 2 | 1 | 0.50 | 0.33 | 0.40 |
| LICENSE_PLATE | 0 | 1 | 1 | 0.00 | 0.00 | 0.00 |
| LOCATION | 10 | 1 | 0 | 1.00 | 0.91 | 0.95 |
| NSS | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| ORGANIZATION | 3 | 0 | 3 | 0.50 | 1.00 | 0.67 |
| PERSON | 16 | 3 | 3 | 0.84 | 0.84 | 0.84 |
| PHONE | 2 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| POSTAL_CODE | 1 | 1 | 0 | 1.00 | 0.50 | 0.67 |
| PROFESSIONAL_ID | 0 | 2 | 0 | 0.00 | 0.00 | 0.00 |

---

## 3. Resultados por Categoria

| Categoria | Strict | Lenient | COR | INC | PAR | MIS | SPU | F1 strict |
|-----------|--------|---------|-----|-----|-----|-----|-----|-----------|
| adversarial | 75% | 75% | 5 | 0 | 0 | 0 | 2 | 0.83 |
| edge_case | 89% | 100% | 12 | 0 | 0 | 0 | 1 | 0.96 |
| ocr_corruption | 40% | 40% | 4 | 0 | 1 | 4 | 0 | 0.57 |
| real_world | 30% | 60% | 26 | 1 | 4 | 4 | 4 | 0.74 |
| unicode_evasion | 67% | 67% | 5 | 0 | 0 | 1 | 0 | 0.91 |

## 4. Resultados por Dificuldade

| Dificuldade | Strict | Lenient | Total |
|-------------|--------|---------|-------|
| fácil | 75% | 100% | 4 |
| médio | 75% | 92% | 12 |
| difícil | 47% | 53% | 19 |

---

## 5. Testes Falhados (Modo Strict)

| Teste | Cat | COR | INC | PAR | MIS | SPU | Detalhe |
|-------|-----|-----|-----|-----|-----|-----|---------|
| date_ordinal | edge | 1 | 0 | 0 | 0 | 1 | SPU: ['El'] |
| example_dni | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['12345678X'] |
| fictional_person | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['Quijote de la Mancha'] |
| ocr_zero_o_confusion | ocr_ | 0 | 0 | 0 | 1 | 0 | MIS: ['ES91 21O0 0418 45O2 OOO5 1332'] |
| ocr_missing_spaces | ocr_ | 0 | 0 | 1 | 1 | 0 | MIS: ['12345678X']; PAR: 1 corresp... |
| ocr_extra_spaces | ocr_ | 0 | 0 | 0 | 2 | 0 | MIS: ['1 2 3 4 5 6 7 8 Z', 'M a r í a'] |
| fullwidth_numbers | unic | 1 | 0 | 0 | 1 | 0 | MIS: ['María'] |
| testament_comparecencia | real | 4 | 0 | 1 | 0 | 0 | PAR: 1 correspondência parcial |
| judicial_sentence_header | real | 4 | 0 | 0 | 0 | 1 | SPU: ['Sala Primera del Tribunal Supremo... |
| contract_parties | real | 6 | 0 | 0 | 2 | 0 | MIS: ['28013', 'Madrid'] |
| bank_account_clause | real | 1 | 1 | 1 | 0 | 0 | INC: 1 tipo incorreto; PAR: 1 corres... |
| professional_ids | real | 2 | 0 | 0 | 2 | 2 | MIS: ['12345', '67890']; SPU: ['Advogado... |
| ecli_citation | real | 1 | 0 | 1 | 0 | 1 | SPU: ['Tribunal Supremo']; PAR: 1 corresp... |
| vehicle_clause | real | 1 | 0 | 1 | 0 | 0 | PAR: 1 correspondência parcial |

---

## 6. Comparação v1 vs v2

| Métrica | v1 (lenient) | v2 (strict) | Diferença |
|---------|--------------|-------------|-----------|
| Pass rate | 71.4% | 60.0% | +11.4pp |
| F1 | 0.826 | 0.788 | +0.038 |

**Nota:** v1 usava matching lenient (confinement + 80% sobreposição). v2 usa strict (limite exato + tipo exato).

---

## 7. Referências

- **SemEval 2013 Task 9**: Avaliação em nível de entidade com 4 modos (strict, exact, partial, type)
- **RockNER (EMNLP 2021)**: Metodologia de avaliação NER adversarial
- **NoiseBench (EMNLP 2024)**: Benchmark ruído real vs ruído simulado
- **nervaluate**: Biblioteca Python para avaliação NER estilo SemEval

**Gerado por:** `scripts/evaluate/test_ner_predictor_adversarial_v2.py`
**Data:** 06-02-2026
