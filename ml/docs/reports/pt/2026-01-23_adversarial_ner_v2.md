# Avaliação Adversarial - legal_ner_v2

**Data:** 23-01-2026
**Modelo:** legal_ner_v2
**Testes:** 35
**Tempo Total:** 1.4s

---

## Resumo Executivo

### Métricas ao Nível da Entidade (estilo seqeval)

| Métrica | Valor |
|---------|-------|
| Precisão | 0.845 |
| Revocação | 0.731 |
| **F1-Score** | **0.784** |
| Verdadeiros Positivos | 49 |
| Falsos Positivos | 9 |
| Falsos Negativos | 18 |
| Pontuação Média de Sobreposição | 0.935 |

### Resistência ao Ruído (estilo NoiseBench)

| Métrica | Valor | Referência |
|---------|-------|------------|
| F1 (texto limpo) | 0.800 | - |
| F1 (com ruído) | 0.720 | - |
| Degradação | 0.080 | ≤0.10 esperado |
| Estado | ✅ OK | Ref. HAL Science |

### Testes por Resultado

| Métrica | Valor |
|---------|-------|
| Total de Testes | 35 |
| Aprovados | 19 (54.3%) |
| Reprovados | 16 (45.7%) |

### Por Categoria (com F1)

| Categoria | Taxa de Aprovação | TP | FP | FN | F1 |
|-----------|-----------|----|----|----|----|
| adversarial | 75.0% | 5 | 2 | 0 | 0.833 |
| edge_case | 66.7% | 9 | 1 | 3 | 0.818 |
| ocr_corruption | 40.0% | 5 | 0 | 4 | 0.714 |
| real_world | 40.0% | 26 | 5 | 9 | 0.788 |
| unicode_evasion | 33.3% | 4 | 1 | 2 | 0.727 |

### Por Dificuldade

| Dificuldade | Aprovados | Total | Taxa |
|------------|---------|-------|------|
| easy | 3 | 4 | 75.0% |
| medium | 9 | 12 | 75.0% |
| hard | 7 | 19 | 36.8% |

---

## Análise de Erros

### Testes Reprovados

| ID do Teste | Categoria | Perdidos | FP | Detalhe |
|---------|-----------|--------|----|---------|
| dni_with_spaces | edge_case | 1 | 0 | Perdido: ['12 345 678 Z'] |
| phone_international | edge_case | 1 | 0 | Perdido: ['0034612345678'] |
| date_roman_numerals | edge_case | 1 | 0 | Perdido: ['XV de marzo del año MMXXIV'] |
| example_dni | adversarial | 0 | 1 | FP: ['12345678X'] |
| fictional_person | adversarial | 0 | 1 | FP: ['Don Quijote de la Mancha'] |
| ocr_zero_o_confusion | ocr_corruption | 1 | 0 | Perdido: ['ES91 21O0 0418 45O2 OOO5 1332'] |
| ocr_missing_spaces | ocr_corruption | 1 | 0 | Perdido: ['12345678X'] |
| ocr_extra_spaces | ocr_corruption | 2 | 0 | Perdido: ['1 2 3 4 5 6 7 8 Z', 'M a r í a'] |
| zero_width_space | unicode_evasion | 0 | 1 | FP: ['de'] |
| fullwidth_numbers | unicode_evasion | 2 | 0 | Perdido: ['１２３４５６７８Z', 'María'] |
| notarial_header | real_world | 1 | 0 | Perdido: ['quince de marzo de dos mil veinticuatro'... |
| judicial_sentence_header | real_world | 1 | 2 | Perdido: ['diez de enero de dos mil veinticuatro'];... |
| contract_parties | real_world | 2 | 0 | Perdido: ['28013', 'Madrid'] |
| bank_account_clause | real_world | 1 | 0 | Perdido: ['A-98765432'] |
| professional_ids | real_world | 3 | 1 | Perdido: ['12345', 'MIGUEL TORRES', '67890']; FP: [... |
| social_security | real_world | 1 | 1 | Perdido: ['281234567890']; FP: ['28'] |

---

## Resultados Detalhados

### ADVERSARIAL

#### date_in_reference [✅ PASS]

**Dificuldade:** hard | **Sobreposição:** 0.00
**Esperado:** 0 | **Detectado:** 0
**Corretos:** 0 | **Perdidos:** 0 | **FP:** 0
**Detalhes:** OK

#### example_dni [❌ FAIL]

**Dificuldade:** hard | **Sobreposição:** 0.00
**Esperado:** 0 | **Detectado:** 1
**Corretos:** 0 | **Perdidos:** 0 | **FP:** 1
**Detalhes:** FP: ['12345678X']

#### fictional_person [❌ FAIL]

**Dificuldade:** hard | **Sobreposição:** 0.00
**Esperado:** 0 | **Detectado:** 1
**Corretos:** 0 | **Perdidos:** 0 | **FP:** 1
**Detalhes:** FP: ['Don Quijote de la Mancha']

#### location_as_person [✅ PASS]

**Dificuldade:** hard | **Sobreposição:** 1.00
**Esperado:** 1 | **Detectado:** 1
**Corretos:** 1 | **Perdidos:** 0 | **FP:** 0
**Detalhes:** OK

#### mixed_languages [✅ PASS]

**Dificuldade:** hard | **Sobreposição:** 0.94
**Esperado:** 3 | **Detectado:** 3
**Corretos:** 3 | **Perdidos:** 0 | **FP:** 0
**Detalhes:** OK

#### negation_dni [✅ PASS]

**Dificuldade:** hard | **Sobreposição:** 0.00
**Esperado:** 0 | **Detectado:** 0
**Corretos:** 0 | **Perdidos:** 0 | **FP:** 0
**Detalhes:** OK

#### numbers_not_dni [✅ PASS]

**Dificuldade:** medium | **Sobreposição:** 0.00
**Esperado:** 0 | **Detectado:** 0
**Corretos:** 0 | **Perdidos:** 0 | **FP:** 0
**Detalhes:** OK

#### organization_as_person [✅ PASS]

**Dificuldade:** medium | **Sobreposição:** 1.00
**Esperado:** 1 | **Detectado:** 1
**Corretos:** 1 | **Perdidos:** 0 | **FP:** 0
**Detalhes:** OK

### EDGE_CASE

#### address_floor_door [✅ PASS]

**Dificuldade:** medium | **Sobreposição:** 0.83
**Esperado:** 3 | **Detectado:** 3
**Corretos:** 3 | **Perdidos:** 0 | **FP:** 0
**Detalhes:** OK

#### date_ordinal [✅ PASS]

**Dificuldade:** medium | **Sobreposição:** 1.00
**Esperado:** 1 | **Detectado:** 2
**Corretos:** 1 | **Perdidos:** 0 | **FP:** 1
**Detalhes:** FP: ['El']

#### date_roman_numerals [❌ FAIL]

**Dificuldade:** hard | **Sobreposição:** 0.00
**Esperado:** 1 | **Detectado:** 0
**Corretos:** 0 | **Perdidos:** 1 | **FP:** 0
**Detalhes:** Perdido: ['XV de marzo del año MMXXIV']

#### dni_with_spaces [❌ FAIL]

**Dificuldade:** hard | **Sobreposição:** 0.00
**Esperado:** 1 | **Detectado:** 0
**Corretos:** 0 | **Perdidos:** 1 | **FP:** 0
**Detalhes:** Perdido: ['12 345 678 Z']

#### dni_without_letter [✅ PASS]

**Dificuldade:** medium | **Sobreposição:** 1.00
**Esperado:** 1 | **Detectado:** 1
**Corretos:** 1 | **Perdidos:** 0 | **FP:** 0
**Detalhes:** OK

#### iban_with_spaces [✅ PASS]

**Dificuldade:** easy | **Sobreposição:** 0.91
**Esperado:** 1 | **Detectado:** 1
**Corretos:** 1 | **Perdidos:** 0 | **FP:** 0
**Detalhes:** OK

#### phone_international [❌ FAIL]

**Dificuldade:** medium | **Sobreposição:** 1.00
**Esperado:** 2 | **Detectado:** 1
**Corretos:** 1 | **Perdidos:** 1 | **FP:** 0
**Detalhes:** Perdido: ['0034612345678']

#### single_letter_name [✅ PASS]

**Dificuldade:** medium | **Sobreposição:** 1.00
**Esperado:** 1 | **Detectado:** 1
**Corretos:** 1 | **Perdidos:** 0 | **FP:** 0
**Detalhes:** OK

#### very_long_name [✅ PASS]

**Dificuldade:** hard | **Sobreposição:** 1.00
**Esperado:** 1 | **Detectado:** 1
**Corretos:** 1 | **Perdidos:** 0 | **FP:** 0
**Detalhes:** OK

### OCR_CORRUPTION

#### ocr_accent_loss [✅ PASS]

**Dificuldade:** easy | **Sobreposição:** 1.00
**Esperado:** 2 | **Detectado:** 2
**Corretos:** 2 | **Perdidos:** 0 | **FP:** 0
**Detalhes:** OK

#### ocr_extra_spaces [❌ FAIL]

**Dificuldade:** hard | **Sobreposição:** 0.00
**Esperado:** 2 | **Detectado:** 0
**Corretos:** 0 | **Perdidos:** 2 | **FP:** 0
**Detalhes:** Perdido: ['1 2 3 4 5 6 7 8 Z', 'M a r í a']

#### ocr_letter_substitution [✅ PASS]

**Dificuldade:** medium | **Sobreposição:** 1.00
**Esperado:** 2 | **Detectado:** 2
**Corretos:** 2 | **Perdidos:** 0 | **FP:** 0
**Detalhes:** OK

#### ocr_missing_spaces [❌ FAIL]

**Dificuldade:** hard | **Sobreposição:** 0.88
**Esperado:** 2 | **Detectado:** 1
**Corretos:** 1 | **Perdidos:** 1 | **FP:** 0
**Detalhes:** Perdido: ['12345678X']

#### ocr_zero_o_confusion [❌ FAIL]

**Dificuldade:** hard | **Sobreposição:** 0.00
**Esperado:** 1 | **Detectado:** 0
**Corretos:** 0 | **Perdidos:** 1 | **FP:** 0
**Detalhes:** Perdido: ['ES91 21O0 0418 45O2 OOO5 1332']

### REAL_WORLD

#### bank_account_clause [❌ FAIL]

**Dificuldade:** medium | **Sobreposição:** 0.88
**Esperado:** 3 | **Detectado:** 2
**Corretos:** 2 | **Perdidos:** 1 | **FP:** 0
**Detalhes:** Perdido: ['A-98765432']

#### cadastral_reference [✅ PASS]

**Dificuldade:** medium | **Sobreposição:** 1.00
**Esperado:** 2 | **Detectado:** 2
**Corretos:** 2 | **Perdidos:** 0 | **FP:** 0
**Detalhes:** OK

#### contract_parties [❌ FAIL]

**Dificuldade:** hard | **Sobreposição:** 0.88
**Esperado:** 8 | **Detectado:** 6
**Corretos:** 6 | **Perdidos:** 2 | **FP:** 0
**Detalhes:** Perdido: ['28013', 'Madrid']

#### ecli_citation [✅ PASS]

**Dificuldade:** easy | **Sobreposição:** 0.90
**Esperado:** 2 | **Detectado:** 3
**Corretos:** 2 | **Perdidos:** 0 | **FP:** 1
**Detalhes:** FP: ['Tribunal Supremo']

#### judicial_sentence_header [❌ FAIL]

**Dificuldade:** hard | **Sobreposição:** 0.92
**Esperado:** 4 | **Detectado:** 5
**Corretos:** 3 | **Perdidos:** 1 | **FP:** 2
**Detalhes:** Perdido: ['diez de enero de dos mil veinticuatro']; FP: ['Nº 123/2024', 'Sala Primera del Tribunal Supremo']

#### notarial_header [❌ FAIL]

**Dificuldade:** medium | **Sobreposição:** 1.00
**Esperado:** 4 | **Detectado:** 3
**Corretos:** 3 | **Perdidos:** 1 | **FP:** 0
**Detalhes:** Perdido: ['quince de marzo de dos mil veinticuatro']

#### professional_ids [❌ FAIL]

**Dificuldade:** hard | **Sobreposição:** 0.65
**Esperado:** 4 | **Detectado:** 2
**Corretos:** 1 | **Perdidos:** 3 | **FP:** 1
**Detalhes:** Perdido: ['12345', 'MIGUEL TORRES', '67890']; FP: ['Colegio de Procuradores de Madrid']

#### social_security [❌ FAIL]

**Dificuldade:** easy | **Sobreposição:** 0.00
**Esperado:** 1 | **Detectado:** 1
**Corretos:** 0 | **Perdidos:** 1 | **FP:** 1
**Detalhes:** Perdido: ['281234567890']; FP: ['28']

#### testament_comparecencia [✅ PASS]

**Dificuldade:** hard | **Sobreposição:** 0.99
**Esperado:** 5 | **Detectado:** 5
**Corretos:** 5 | **Perdidos:** 0 | **FP:** 0
**Detalhes:** OK

#### vehicle_clause [✅ PASS]

**Dificuldade:** medium | **Sobreposição:** 0.72
**Esperado:** 2 | **Detectado:** 2
**Corretos:** 2 | **Perdidos:** 0 | **FP:** 0
**Detalhes:** OK

### UNICODE_EVASION

#### cyrillic_o [✅ PASS]

**Dificuldade:** hard | **Sobreposição:** 0.94
**Esperado:** 2 | **Detectado:** 2
**Corretos:** 2 | **Perdidos:** 0 | **FP:** 0
**Detalhes:** OK

#### fullwidth_numbers [❌ FAIL]

**Dificuldade:** hard | **Sobreposição:** 0.00
**Esperado:** 2 | **Detectado:** 0
**Corretos:** 0 | **Perdidos:** 2 | **FP:** 0
**Detalhes:** Perdido: ['１２３４５６７８Z', 'María']

#### zero_width_space [❌ FAIL]

**Dificuldade:** hard | **Sobreposição:** 1.00
**Esperado:** 2 | **Detectado:** 3
**Corretos:** 2 | **Perdidos:** 0 | **FP:** 1
**Detalhes:** FP: ['de']

---

## Referências

- **seqeval**: Métricas de avaliação ao nível da entidade para NER
- **NoiseBench (ICLR 2024)**: Avaliação de ruído real vs simulado
- **HAL Science**: Avaliação de impacto OCR (~10pt degradação F1 esperada)

**Gerado por:** `scripts/evaluate/test_ner_predictor_adversarial.py`
**Data:** 23-01-2026
