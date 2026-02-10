# Comparação: Modelo v1 vs v2 (Treino com Ruído)

**Data:** 2026-01-22
**Autor:** AlexAlves87
**Tipo:** Análise Comparativa
**Estado:** Concluído

---

## Resumo Executivo

| Métrica | v1 | v2 | Mudança |
|---------|-----|-----|--------|
| Taxa de Aprovação Adversarial | 45.7% (16/35) | 54.3% (19/35) | **+8.6 pp** |
| F1 Teste Sintético | 99.87% | 100% | +0.13 pp |
| Dataset | v2 (limpo) | v3 (30% ruído) | - |

**Conclusão:** A injeção de ruído OCR durante o treino melhorou a robustez do modelo em +8.6 pontos percentuais em testes adversariais.

---

## Metodologia

### Diferenças no Treino

| Aspeto | v1 | v2 |
|---------|-----|-----|
| Dataset | `ner_dataset_v2` | `ner_dataset_v3` |
| Injeção de ruído | 0% | 30% |
| Tipos de ruído | - | l↔I, 0↔O, acentos, espaços |
| Hiperparâmetros | Idênticos | Idênticos |
| Modelo base | roberta-bne-capitel-ner | roberta-bne-capitel-ner |

### Testes Adversariais (35 casos)

| Categoria | Testes |
|-----------|-------|
| edge_case | 9 |
| adversarial | 8 |
| ocr_corruption | 5 |
| unicode_evasion | 3 |
| real_world | 10 |

---

## Resultados por Categoria

### Comparação de Taxa de Aprovação

| Categoria | v1 | v2 | Melhoria |
|-----------|-----|-----|--------|
| edge_case | 55.6% (5/9) | 66.7% (6/9) | +11.1 pp |
| adversarial | 37.5% (3/8) | 62.5% (5/8) | **+25.0 pp** |
| ocr_corruption | 20.0% (1/5) | 40.0% (2/5) | **+20.0 pp** |
| unicode_evasion | 33.3% (1/3) | 33.3% (1/3) | 0 pp |
| real_world | 60.0% (6/10) | 50.0% (5/10) | -10.0 pp |

### Análise por Categoria

**Melhorias Significativas (+20 pp ou mais):**
- **adversarial**: +25 pp - Melhor discriminação de contexto (negação, exemplos)
- **ocr_corruption**: +20 pp - Ruído no treino ajudou diretamente

**Sem Mudança:**
- **unicode_evasion**: 33.3% - Requer normalização de texto, não apenas treino

**Regressão:**
- **real_world**: -10 pp - Possível overfitting ao ruído, menos robustez a padrões complexos

---

## Detalhe dos Testes Alterados

### Testes APROVADOS na v2 (anteriormente FALHARAM)

| Teste | Categoria | Nota |
|------|-----------|------|
| `ocr_letter_substitution` | ocr_corruption | DNl → DNI (l vs I) |
| `ocr_accent_loss` | ocr_corruption | José → Jose |
| `negation_dni` | adversarial | "NO tener DNI" - já não deteta PII |
| `organization_as_person` | adversarial | García y Asociados → ORG |
| `location_as_person` | adversarial | San Fernando → LOCATION |

### Testes FALHARAM na v2 (anteriormente APROVADOS)

| Teste | Categoria | Nota |
|------|-----------|------|
| `notarial_header` | real_world | Possível regressão em datas por extenso |
| `judicial_sentence_header` | real_world | Possível regressão em nomes maiúsculos |

---

## Conclusões

### Principais Descobertas

1. **Treino com ruído funciona**: +8.6 pp melhoria global, especialmente em OCR e adversarial
2. **Ruído específico importa**: l↔I, acentos melhoraram, mas 0↔O e espaços continuam a falhar
3. **Compromisso observado**: Ganhou-se robustez ao ruído mas perdeu-se alguma precisão em padrões complexos

### Limitações da Abordagem

1. **Ruído insuficiente para 0↔O**: IBAN com O em vez de 0 continua a falhar
2. **Normalização necessária**: Evasão Unicode requer pré-processamento, não apenas treino
3. **Complexidade do mundo real**: Documentos complexos requerem mais dados de treino

### Recomendações

| Prioridade | Ação | Impacto Esperado |
|-----------|--------|------------------|
| ALTA | Adicionar normalização Unicode no pré-processamento | +10% unicode_evasion |
| ALTA | Mais variedade de ruído 0↔O no treino | +5-10% ocr_corruption |
| MÉDIA | Mais exemplos real_world no dataset | Recuperar -10% real_world |
| MÉDIA | Pipeline híbrido (Regex → NER → Validação) | +15-20% segundo a literatura |

---

## Próximos Passos

1. **Implementar pipeline híbrido** segundo a investigação PMC12214779
2. **Adicionar text_normalizer.py** como pré-processamento antes da inferência
3. **Expandir dataset** com mais exemplos de documentos reais
4. **Avaliar camada CRF** para melhorar a coerência das sequências

---

## Ficheiros Relacionados

- `docs/reports/2026-01-20_adversarial_evaluation.md` - Avaliação v1
- `docs/reports/2026-01-21_adversarial_evaluation_v2.md` - Avaliação v2
- `docs/reports/2026-01-16_investigacion_pipeline_pii.md` - Melhores práticas
- `scripts/preprocess/inject_ocr_noise.py` - Script de injeção de ruído

---

**Data:** 2026-01-22
