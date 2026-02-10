# Elemento 1: Text Normalizer - Prueba Aislada

**Fecha:** 2026-02-03
**Estado:** ✅ COMPLETADO
**Tiempo ejecución:** 0.002s

---

## 1. Resumen

| Métrica | Valor |
|---------|-------|
| Tests ejecutados | 15 |
| Tests pasados | 15 |
| Pass rate | 100% |
| Tiempo | 0.002s |

## 2. Componente

**Archivo:** `scripts/preprocess/text_normalizer.py`

**Clase principal:** `TextNormalizer`

**Funcionalidad:**
- NFKC normalization (fullwidth → ASCII)
- Zero-width character removal (U+200B-U+200F, U+2060-U+206F, U+FEFF)
- Cyrillic → Latin homoglyph mapping (17 caracteres)
- NBSP → space + collapse múltiples espacios
- Soft hyphen removal

**Preserva (crítico para NER):**
- Case (RoBERTa es case-sensitive)
- Acentos españoles (María, García, etc.)
- Puntuación legítima

## 3. Tests Validados

| Test | Categoría | Descripción |
|------|-----------|-------------|
| fullwidth_dni | Unicode | `１２３４５６７８Z` → `12345678Z` |
| fullwidth_mixed | Unicode | Letras y números fullwidth |
| zero_width_in_dni | Evasion | Zero-width dentro de DNI |
| zero_width_in_name | Evasion | Zero-width en nombres |
| cyrillic_o_in_dni | Homoglyph | Cirílico О → Latino O |
| cyrillic_mixed | Homoglyph | Texto mixto cirílico/latino |
| nbsp_in_address | Spaces | NBSP → espacio normal |
| multiple_spaces | Spaces | Colapso de espacios múltiples |
| soft_hyphen_in_word | OCR | Soft hyphens eliminados |
| combined_evasion | Combined | Múltiples técnicas combinadas |
| preserve_accents | Preserve | Acentos españoles intactos |
| preserve_case | Preserve | Case no modificado |
| preserve_punctuation | Preserve | Puntuación legal preservada |
| empty_string | Edge | String vacío |
| only_spaces | Edge | Solo espacios |

## 4. Ejemplo de Diagnóstico

**Input:** `DNI: １２​３４​５６​７８Х del Sr. María`

**Output:** `DNI: 12345678X del Sr. María`

**Cambios aplicados:**
1. Removed 3 zero-width characters
2. Applied NFKC normalization
3. Replaced 1 Cyrillic homoglyphs

## 5. Siguiente Paso

Integrar `TextNormalizer` en el pipeline NER (`CompositeNerAdapter`) y evaluar impacto en tests adversariales.

---

**Generado por:** AlexAlves87
