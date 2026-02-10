# Avaliação de Impacto: Text Normalizer

**Data:** 04-02-2026
**Autor:** AlexAlves87
**Componente:** `TextNormalizer` (Normalização Unicode/OCR)
**Padrão:** SemEval 2013 Task 9 (modo strict)

---

## 1. Resumo Executivo

Avaliação do impacto da integração do `TextNormalizer` no pipeline NER para melhorar a robustez contra caracteres Unicode e artefatos OCR.

### Resultados

| Métrica | Baseline | +Normalizer | Delta | Mudança |
|---------|----------|-------------|-------|---------|
| **Taxa de Aprovação (strict)** | 28.6% | **34.3%** | **+5.7pp** | +20% relativo |
| **F1 (strict)** | 0.464 | **0.492** | **+0.028** | +6% relativo |
| F1 (parcial) | 0.632 | 0.659 | +0.027 | +4.3% relativo |
| COR | 29 | 31 | +2 | Mais detecções exatas |
| MIS | 17 | 15 | -2 | Menos entidades perdidas |
| SPU | 8 | 7 | -1 | Menos falsos positivos |

### Conclusão

> **O TextNormalizer melhora significativamente a robustez do modelo NER.**
> Taxa de aprovação +5.7pp, F1 +0.028. Dois testes de evasão Unicode agora passam.

---

## 2. Metodologia

### 2.1 Design Experimental

| Aspecto | Especificação |
|---------|---------------|
| Variável Independente | TextNormalizer (ON/OFF) |
| Variável Dependente | Métricas SemEval 2013 |
| Modelo | legal_ner_v2 (RoBERTalex) |
| Dataset | 35 testes adversariais |
| Padrão | SemEval 2013 Task 9 (strict) |

### 2.2 Componente Avaliado

**Arquivo:** `scripts/inference/ner_predictor.py` → função `normalize_text_for_ner()`

**Operações Aplicadas:**
1. Remoção caracteres zero-width (U+200B-U+200F, U+2060-U+206F, U+FEFF)
2. Normalização NFKC (fullwidth → ASCII)
3. Mapeamento homóglifos (Cirílico → Latino)
4. Normalização espaços (NBSP → espaço, colapsar múltiplos)
5. Remoção hífens suaves

### 2.3 Reprodutibilidade

```bash
# Ambiente
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Execução
python scripts/evaluate/test_ner_predictor_adversarial_v2.py

# Output: docs/reports/YYYY-MM-DD_adversarial_v2_academic_rN.md
```

---

## 3. Resultados

### 3.1 Comparação Detalhada por Métrica SemEval

| Métrica | Baseline | +Normalizer | Delta |
|---------|----------|-------------|-------|
| COR (Correto) | 29 | 31 | **+2** |
| INC (Incorreto) | 0 | 0 | 0 |
| PAR (Parcial) | 21 | 21 | 0 |
| MIS (Perdido) | 17 | 15 | **-2** |
| SPU (Espúrio) | 8 | 7 | **-1** |
| POS (Possível) | 67 | 67 | 0 |
| ACT (Atual) | 58 | 59 | +1 |

### 3.2 Testes que Melhoraram

| Teste | Baseline | +Normalizer | Melhoria |
|-------|----------|-------------|----------|
| `cyrillic_o` | ❌ COR:1 PAR:1 | ✅ COR:2 | **Mapeamento homóglifos funciona** |
| `zero_width_space` | ❌ COR:2 SPU:1 | ✅ COR:2 SPU:0 | **Remoção zero-width funciona** |
| `fullwidth_numbers` | ❌ MIS:2 | ❌ COR:1 MIS:1 | Melhoria parcial (+1 COR) |

### 3.3 Testes Sem Mudança Significativa

| Teste | Status | Razão |
|-------|--------|-------|
| `ocr_extra_spaces` | ❌ MIS:2 | Requer normalização de espaços dentro de entidades |
| `ocr_zero_o_confusion` | ❌ MIS:1 | Requer correção contextual OCR O↔0 |
| `dni_with_spaces` | ❌ MIS:1 | Espaços internos em DNI não colapsados |

### 3.4 Resultados por Categoria

| Categoria | Baseline Strict | +Normalizer Strict | Delta |
|-----------|-----------------|--------------------|-------|
| adversarial | 75% | 75% | 0 |
| edge_case | 22% | 22% | 0 |
| ocr_corruption | 40% | 40% | 0 |
| real_world | 10% | 10% | 0 |
| **unicode_evasion** | 0% | **67%** | **+67pp** |

**Descoberta Chave:** O impacto concentra-se em `unicode_evasion` (+67pp), que era o objetivo principal.

---

## 4. Análise de Erros

### 4.1 Teste `fullwidth_numbers` (Melhoria Parcial)

**Input:** `"DNI １２３４５６７８Z de María."`

**Esperado:**
- `"１２３４５６７８Z"` → DNI_NIE
- `"María"` → PERSON

**Detectado (com normalizer):**
- `"12345678Z"` → DNI_NIE ✅ (match normalizado)
- `"María"` → MIS ❌

**Análise:** O DNI é detectado corretamente após NFKC. O nome "María" é perdido porque o modelo não o detecta (problema do modelo, não do normalizer).

### 4.2 Testes que Continuam Falhando

| Teste | Problema | Solução Necessária |
|-------|----------|--------------------|
| `dni_with_spaces` | "12 345 678 Z" não reconhecido | Regex para DNI com espaços |
| `date_roman_numerals` | Datas com números romanos | Data augmentation |
| `ocr_zero_o_confusion` | IBAN com O/0 misturados | Pós-correção OCR |

---

## 5. Conclusões e Trabalho Futuro

### 5.1 Conclusões

1. **TextNormalizer cumpre seu objetivo** para evasão Unicode:
   - `cyrillic_o`: ❌ → ✅
   - `zero_width_space`: ❌ → ✅
   - Categoria `unicode_evasion`: 0% → 67%

2. **Impacto global moderado mas positivo:**
   - F1 strict: +0.028 (+6%)
   - Taxa de aprovação: +5.7pp (+20% relativo)

3. **Não resolve problemas de OCR** (esperado):
   - `ocr_extra_spaces`, `ocr_zero_o_confusion` requerem técnicas adicionais

### 5.2 Trabalho Futuro

| Prioridade | Melhoria | Impacto Estimado |
|------------|----------|------------------|
| ALTA | Regex para DNI/IBAN com espaços | +2-3 COR |
| ALTA | Validação checksum (reduzir SPU) | -2-3 SPU |
| MÉDIA | Data augmentation para datas textuais | +3-4 COR |
| BAIXA | Pós-correção OCR (O↔0) | +1-2 COR |

### 5.3 Objetivo Atualizado

| Métrica | Antes | Agora | Meta Nível 4 | Gap |
|---------|-------|-------|--------------|-----|
| F1 (strict) | 0.464 | **0.492** | ≥0.70 | -0.208 |
| Taxa aprovação | 28.6% | **34.3%** | ≥70% | -35.7pp |

---

## 6. Referências

1. **Pesquisa base:** `docs/reports/2026-01-27_investigacion_text_normalization.md`
2. **Componente standalone:** `scripts/preprocess/text_normalizer.py`
3. **Integração produção:** `src/contextsafe/infrastructure/nlp/text_normalizer.py`
4. **Formas de Normalização Unicode UAX #15:** https://unicode.org/reports/tr15/

---

**Tempo de avaliação:** 1.3s
**Gerado por:** AlexAlves87
**Data:** 04-02-2026
