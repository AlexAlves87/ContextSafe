# Avaliação Adversarial v2 (Padrões Acadêmicos) - legal_ner_v2

**Data:** 04-02-2026
**Modelo:** legal_ner_v2
**Testes:** 35
**Tempo total:** 1.3s
**Padrão:** SemEval 2013 Task 9

---

## 1. Resumo Executivo

### 1.1 Métricas SemEval 2013 (Modo Strict)

| Métrica | Valor |
|---------|-------|
| **F1 (strict)** | **0.492** |
| Precisão (strict) | 0.525 |
| Recall (strict) | 0.463 |
| F1 (parcial) | 0.659 |

### 1.2 Contagens SemEval

| Métrica | Valor | Descrição |
|---------|-------|-----------|
| COR | 31 | Corretos (limite + tipo exatos) |
| INC | 0 | Limite correto, tipo incorreto |
| PAR | 21 | Correspondência parcial (sobreposição) |
| MIS | 15 | Perdidos (FN) |
| SPU | 7 | Espúrios (FP) |
| **POS** | 67 | Total gold (COR+INC+PAR+MIS) |
| **ACT** | 59 | Total sistema (COR+INC+PAR+SPU) |

### 1.3 Taxa de Aprovação

| Modo | Aprovados | Total | Taxa |
|------|-----------|-------|------|
| **Strict** | 12 | 35 | **34.3%** |
| Lenient (v1) | 21 | 35 | 60.0% |

---

## 2. Métricas por Tipo de Entidade

| Tipo | COR | MIS | SPU | Precisão | Recall | F1 |
|------|-----|-----|-----|----------|--------|----|
| ADDRESS | 1 | 2 | 2 | 0.33 | 0.33 | 0.33 |
| CADASTRAL_REF | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| DATE | 1 | 3 | 1 | 0.50 | 0.25 | 0.33 |
| DNI_NIE | 9 | 4 | 2 | 0.82 | 0.69 | 0.75 |
| ECLI | 1 | 1 | 1 | 0.50 | 0.50 | 0.50 |
| IBAN | 0 | 3 | 2 | 0.00 | 0.00 | 0.00 |
| LICENSE_PLATE | 0 | 1 | 1 | 0.00 | 0.00 | 0.00 |
| LOCATION | 10 | 1 | 0 | 1.00 | 0.91 | 0.95 |
| NSS | 0 | 1 | 0 | 0.00 | 0.00 | 0.00 |
| ORGANIZATION | 1 | 2 | 5 | 0.17 | 0.33 | 0.22 |
| PERSON | 6 | 13 | 13 | 0.32 | 0.32 | 0.32 |
| PHONE | 1 | 1 | 0 | 1.00 | 0.50 | 0.67 |
| POSTAL_CODE | 0 | 2 | 1 | 0.00 | 0.00 | 0.00 |
| PROFESSIONAL_ID | 0 | 2 | 0 | 0.00 | 0.00 | 0.00 |

---

## 3. Resultados por Categoria

| Categoria | Strict | Lenient | COR | INC | PAR | MIS | SPU | F1 strict |
|-----------|--------|---------|-----|-----|-----|-----|-----|-----------|
| adversarial | 62% | 75% | 4 | 0 | 1 | 0 | 2 | 0.67 |
| edge_case | 22% | 67% | 6 | 0 | 3 | 3 | 1 | 0.55 |
| ocr_corruption | 40% | 40% | 4 | 0 | 1 | 4 | 0 | 0.57 |
| real_world | 10% | 50% | 12 | 0 | 16 | 7 | 4 | 0.36 |
| unicode_evasion | 67% | 67% | 5 | 0 | 0 | 1 | 0 | 0.91 |

## 4. Resultados por Dificuldade

| Dificuldade | Strict | Lenient | Total |
|-------------|--------|---------|-------|
| fácil | 25% | 100% | 4 |
| médio | 50% | 75% | 12 |
| difícil | 26% | 42% | 19 |

---

## 5. Testes Falhados (Modo Strict)

| Teste | Cat | COR | INC | PAR | MIS | SPU | Detalhe |
|-------|-----|-----|-----|-----|-----|-----|---------|
| very_long_name | edge | 0 | 0 | 1 | 0 | 0 | PAR: 1 correspondência parcial |
| dni_with_spaces | edge | 0 | 0 | 0 | 1 | 0 | MIS: ['12 345 678 Z'] |
| iban_with_spaces | edge | 0 | 0 | 1 | 0 | 0 | PAR: 1 correspondência parcial |
| phone_international | edge | 1 | 0 | 0 | 1 | 0 | MIS: ['0034612345678'] |
| date_roman_numerals | edge | 0 | 0 | 0 | 1 | 0 | MIS: ['XV de marzo del año MMXXIV'] |
| date_ordinal | edge | 1 | 0 | 0 | 0 | 1 | SPU: ['El'] |
| address_floor_door | edge | 2 | 0 | 1 | 0 | 0 | PAR: 1 correspondência parcial |
| example_dni | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['12345678X'] |
| fictional_person | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['Don Quijote de la Mancha'] |
| mixed_languages | adve | 2 | 0 | 1 | 0 | 0 | PAR: 1 correspondência parcial |
| ocr_zero_o_confusion | ocr_ | 0 | 0 | 0 | 1 | 0 | MIS: ['ES91 21O0 0418 45O2 OOO5 1332'] |
| ocr_missing_spaces | ocr_ | 0 | 0 | 1 | 1 | 0 | MIS: ['12345678X']; PAR: 1 corresp... |
| ocr_extra_spaces | ocr_ | 0 | 0 | 0 | 2 | 0 | MIS: ['1 2 3 4 5 6 7 8 Z', 'M a r í a'] |
| fullwidth_numbers | unic | 1 | 0 | 0 | 1 | 0 | MIS: ['María'] |
| notarial_header | real | 3 | 0 | 0 | 1 | 0 | MIS: ['quince de marzo de dos mil veinti... |
| testament_comparecencia | real | 3 | 0 | 2 | 0 | 0 | PAR: 2 correspondências parciais |
| judicial_sentence_header | real | 1 | 0 | 2 | 1 | 1 | MIS: ['diez de enero de dos mil veinticu... |
| contract_parties | real | 2 | 0 | 4 | 2 | 0 | MIS: ['28013', 'Madrid']; PAR: 4 corresp... |
| bank_account_clause | real | 0 | 0 | 2 | 1 | 0 | MIS: ['A-98765432']; PAR: 2 corresp... |
| professional_ids | real | 0 | 0 | 2 | 2 | 2 | MIS: ['12345', '67890']; SPU: ['Advogado... |
| ecli_citation | real | 1 | 0 | 1 | 0 | 1 | SPU: ['Tribunal Supremo']; PAR: 1 parcia... |
| vehicle_clause | real | 0 | 0 | 2 | 0 | 0 | PAR: 2 correspondências parciais |
| social_security | real | 0 | 0 | 1 | 0 | 0 | PAR: 1 correspondência parcial |

---

## 6. Comparação v1 vs v2

| Métrica | v1 (lenient) | v2 (strict) | Diferença |
|---------|--------------|-------------|-----------|
| Pass rate | 60.0% | 34.3% | +25.7pp |
| F1 | 0.659 | 0.492 | +0.167 |

**Nota:** v1 usava matching lenient (confinement + 80% sobreposição). v2 usa strict (limite exato + tipo exato).

---

## 7. Referências

- **SemEval 2013 Task 9**: Avaliação em nível de entidade com 4 modos (strict, exact, partial, type)
- **RockNER (EMNLP 2021)**: Metodologia de avaliação NER adversarial
- **NoiseBench (EMNLP 2024)**: Benchmark ruído real vs ruído simulado
- **nervaluate**: Biblioteca Python para avaliação NER estilo SemEval

**Gerado por:** `scripts/evaluate/test_ner_predictor_adversarial_v2.py`
**Data:** 04-02-2026
