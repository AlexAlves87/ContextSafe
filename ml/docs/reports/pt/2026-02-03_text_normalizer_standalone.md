# Elemento 1: Text Normalizer - Teste Isolado

**Data:** 03-02-2026
**Status:** ✅ CONCLUÍDO
**Tempo execução:** 0.002s

---

## 1. Resumo

| Métrica | Valor |
|---------|-------|
| Testes executados | 15 |
| Testes passados | 15 |
| Pass rate | 100% |
| Tempo | 0.002s |

## 2. Componente

**Arquivo:** `scripts/preprocess/text_normalizer.py`

**Classe principal:** `TextNormalizer`

**Funcionalidade:**
- Normalização NFKC (fullwidth → ASCII)
- Remoção de caracteres zero-width (U+200B-U+200F, U+2060-U+206F, U+FEFF)
- Mapeamento de homóglifos Cirílico → Latino (17 caracteres)
- NBSP → espaço + colapso de múltiplos espaços
- Remoção de hífen suave (soft hyphen)

**Preserva (crítico para NER):**
- Maiúsculas/Minúsculas (RoBERTa é case-sensitive)
- Acentos espanhóis (María, García, etc.)
- Pontuação legítima

## 3. Testes Validados

| Teste | Categoria | Descrição |
|-------|-----------|-----------|
| fullwidth_dni | Unicode | `１２３４５６７８Z` → `12345678Z` |
| fullwidth_mixed | Unicode | Letras e números fullwidth |
| zero_width_in_dni | Evasão | Zero-width dentro de DNI |
| zero_width_in_name | Evasão | Zero-width em nomes |
| cyrillic_o_in_dni | Homóglifo | Cirílico О → Latino O |
| cyrillic_mixed | Homóglifo | Texto misto Cirílico/Latino |
| nbsp_in_address | Espaços | NBSP → espaço normal |
| multiple_spaces | Espaços | Colapso de múltiplos espaços |
| soft_hyphen_in_word | OCR | Hífens suaves removidos |
| combined_evasion | Combinado | Múltiplas técnicas combinadas |
| preserve_accents | Preservar | Acentos espanhóis intactos |
| preserve_case | Preservar | Case não modificado |
| preserve_punctuation | Preservar | Pontuação legal preservada |
| empty_string | Edge | String vazia |
| only_spaces | Edge | Apenas espaços |

## 4. Exemplo de Diagnóstico

**Input:** `DNI: １２​３４​５６​７８Х del Sr. María`

**Output:** `DNI: 12345678X del Sr. María`

**Alterações aplicadas:**
1. Removed 3 zero-width characters
2. Applied NFKC normalization
3. Replaced 1 Cyrillic homoglyphs

## 5. Próximo Passo

Integrar `TextNormalizer` no pipeline NER (`CompositeNerAdapter`) e avaliar impacto em testes adversariais.

---

**Gerado por:** AlexAlves87
