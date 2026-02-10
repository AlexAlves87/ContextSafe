# Evaluación de Impacto: Text Normalizer

**Fecha:** 2026-02-04
**Autor:** AlexAlves87
**Componente:** `TextNormalizer` (normalización Unicode/OCR)
**Estándar:** SemEval 2013 Task 9 (strict mode)

---

## 1. Resumen Ejecutivo

Evaluación del impacto de integrar `TextNormalizer` en el pipeline NER para mejorar robustez ante caracteres Unicode y artefactos OCR.

### Resultados

| Métrica | Baseline | +Normalizer | Delta | Cambio |
|---------|----------|-------------|-------|--------|
| **Pass Rate (strict)** | 28.6% | **34.3%** | **+5.7pp** | +20% relativo |
| **F1 (strict)** | 0.464 | **0.492** | **+0.028** | +6% relativo |
| F1 (partial) | 0.632 | 0.659 | +0.027 | +4.3% relativo |
| COR | 29 | 31 | +2 | Más detecciones exactas |
| MIS | 17 | 15 | -2 | Menos entidades perdidas |
| SPU | 8 | 7 | -1 | Menos falsos positivos |

### Conclusión

> **El TextNormalizer mejora significativamente la robustez del modelo NER.**
> Pass rate +5.7pp, F1 +0.028. Dos tests de evasión Unicode ahora pasan.

---

## 2. Metodología

### 2.1 Diseño Experimental

| Aspecto | Especificación |
|---------|----------------|
| Variable independiente | TextNormalizer (ON/OFF) |
| Variable dependiente | Métricas SemEval 2013 |
| Modelo | legal_ner_v2 (RoBERTalex) |
| Dataset | 35 tests adversariales |
| Estándar | SemEval 2013 Task 9 (strict) |

### 2.2 Componente Evaluado

**Archivo:** `scripts/inference/ner_predictor.py` → función `normalize_text_for_ner()`

**Operaciones aplicadas:**
1. Eliminación zero-width characters (U+200B-U+200F, U+2060-U+206F, U+FEFF)
2. Normalización NFKC (fullwidth → ASCII)
3. Mapeo homoglyphs (Cirílico → Latino)
4. Normalización espacios (NBSP → espacio, colapsar múltiples)
5. Eliminación soft hyphens

### 2.3 Reproducibilidad

```bash
# Entorno
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Ejecución
python scripts/evaluate/test_ner_predictor_adversarial_v2.py

# Output: docs/reports/YYYY-MM-DD_adversarial_v2_academic_rN.md
```

---

## 3. Resultados

### 3.1 Comparación Detallada por Métrica SemEval

| Métrica | Baseline | +Normalizer | Delta |
|---------|----------|-------------|-------|
| COR (Correct) | 29 | 31 | **+2** |
| INC (Incorrect) | 0 | 0 | 0 |
| PAR (Partial) | 21 | 21 | 0 |
| MIS (Missing) | 17 | 15 | **-2** |
| SPU (Spurious) | 8 | 7 | **-1** |
| POS (Possible) | 67 | 67 | 0 |
| ACT (Actual) | 58 | 59 | +1 |

### 3.2 Tests que Mejoraron

| Test | Baseline | +Normalizer | Mejora |
|------|----------|-------------|--------|
| `cyrillic_o` | ❌ COR:1 PAR:1 | ✅ COR:2 | **Homoglyph mapping funciona** |
| `zero_width_space` | ❌ COR:2 SPU:1 | ✅ COR:2 SPU:0 | **Zero-width removal funciona** |
| `fullwidth_numbers` | ❌ MIS:2 | ❌ COR:1 MIS:1 | Mejora parcial (+1 COR) |

### 3.3 Tests Sin Cambio Significativo

| Test | Estado | Razón |
|------|--------|-------|
| `ocr_extra_spaces` | ❌ MIS:2 | Requiere normalización de espacios en entidades |
| `ocr_zero_o_confusion` | ❌ MIS:1 | Requiere corrección OCR O↔0 contextual |
| `dni_with_spaces` | ❌ MIS:1 | Espacios internos en DNI no se colapsan |

### 3.4 Resultados por Categoría

| Categoría | Baseline Strict | +Normalizer Strict | Delta |
|-----------|-----------------|-------------------|-------|
| adversarial | 75% | 75% | 0 |
| edge_case | 22% | 22% | 0 |
| ocr_corruption | 40% | 40% | 0 |
| real_world | 10% | 10% | 0 |
| **unicode_evasion** | 0% | **67%** | **+67pp** |

**Hallazgo clave:** El impacto se concentra en `unicode_evasion` (+67pp), que era el objetivo principal.

---

## 4. Análisis de Errores

### 4.1 Test `fullwidth_numbers` (Mejora Parcial)

**Input:** `"DNI １２３４５６７８Z de María."`

**Esperado:**
- `"１２３４５６７８Z"` → DNI_NIE
- `"María"` → PERSON

**Detectado (con normalizer):**
- `"12345678Z"` → DNI_NIE ✅ (match normalizado)
- `"María"` → MIS ❌

**Análisis:** El DNI se detecta correctamente tras NFKC. El nombre "María" se pierde porque el modelo no lo detecta (problema del modelo, no del normalizer).

### 4.2 Tests que Siguen Fallando

| Test | Problema | Solución Requerida |
|------|----------|-------------------|
| `dni_with_spaces` | "12 345 678 Z" no se reconoce | Regex para DNI con espacios |
| `date_roman_numerals` | Fechas con números romanos | Data augmentation |
| `ocr_zero_o_confusion` | IBAN con O/0 mezclados | OCR post-correction |

---

## 5. Conclusiones y Trabajo Futuro

### 5.1 Conclusiones

1. **TextNormalizer cumple su objetivo** para evasión Unicode:
   - `cyrillic_o`: ❌ → ✅
   - `zero_width_space`: ❌ → ✅
   - `unicode_evasion` category: 0% → 67%

2. **Impacto global moderado pero positivo:**
   - F1 strict: +0.028 (+6%)
   - Pass rate: +5.7pp (+20% relativo)

3. **No resuelve problemas de OCR** (esperado):
   - `ocr_extra_spaces`, `ocr_zero_o_confusion` requieren técnicas adicionales

### 5.2 Trabajo Futuro

| Prioridad | Mejora | Impacto Estimado |
|-----------|--------|------------------|
| ALTA | Regex para DNI/IBAN con espacios | +2-3 COR |
| ALTA | Checksum validation (reducir SPU) | -2-3 SPU |
| MEDIA | Data augmentation fechas textuales | +3-4 COR |
| BAJA | OCR post-correction (O↔0) | +1-2 COR |

### 5.3 Objetivo Actualizado

| Métrica | Antes | Ahora | Objetivo Nivel 4 | Gap |
|---------|-------|-------|------------------|-----|
| F1 (strict) | 0.464 | **0.492** | ≥0.70 | -0.208 |
| Pass rate | 28.6% | **34.3%** | ≥70% | -35.7pp |

---

## 6. Referencias

1. **Investigación base:** `docs/reports/2026-01-27_investigacion_text_normalization.md`
2. **Componente standalone:** `scripts/preprocess/text_normalizer.py`
3. **Integración producción:** `src/contextsafe/infrastructure/nlp/text_normalizer.py`
4. **UAX #15 Unicode Normalization Forms:** https://unicode.org/reports/tr15/

---

**Tiempo de evaluación:** 1.3s
**Generado por:** AlexAlves87
**Fecha:** 2026-02-04
