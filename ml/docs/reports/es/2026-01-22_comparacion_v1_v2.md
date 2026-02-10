# Comparación: Modelo v1 vs v2 (Noise Training)

**Fecha:** 2026-01-22
**Autor:** AlexAlves87
**Tipo:** Análisis Comparativo
**Estado:** Completado

---

## Resumen Ejecutivo

| Métrica | v1 | v2 | Cambio |
|---------|-----|-----|--------|
| Pass Rate Adversarial | 45.7% (16/35) | 54.3% (19/35) | **+8.6 pp** |
| F1 Test Sintético | 99.87% | 100% | +0.13 pp |
| Dataset | v2 (clean) | v3 (30% noise) | - |

**Conclusión:** La inyección de ruido OCR durante el entrenamiento mejoró la robustez del modelo en +8.6 puntos porcentuales en tests adversariales.

---

## Metodología

### Diferencias en Training

| Aspecto | v1 | v2 |
|---------|-----|-----|
| Dataset | `ner_dataset_v2` | `ner_dataset_v3` |
| Noise injection | 0% | 30% |
| Tipos de ruido | - | l↔I, 0↔O, acentos, espacios |
| Hyperparams | Idénticos | Idénticos |
| Base model | roberta-bne-capitel-ner | roberta-bne-capitel-ner |

### Tests Adversariales (35 casos)

| Categoría | Tests |
|-----------|-------|
| edge_case | 9 |
| adversarial | 8 |
| ocr_corruption | 5 |
| unicode_evasion | 3 |
| real_world | 10 |

---

## Resultados por Categoría

### Comparación de Pass Rate

| Categoría | v1 | v2 | Mejora |
|-----------|-----|-----|--------|
| edge_case | 55.6% (5/9) | 66.7% (6/9) | +11.1 pp |
| adversarial | 37.5% (3/8) | 62.5% (5/8) | **+25.0 pp** |
| ocr_corruption | 20.0% (1/5) | 40.0% (2/5) | **+20.0 pp** |
| unicode_evasion | 33.3% (1/3) | 33.3% (1/3) | 0 pp |
| real_world | 60.0% (6/10) | 50.0% (5/10) | -10.0 pp |

### Análisis por Categoría

**Mejoras significativas (+20 pp o más):**
- **adversarial**: +25 pp - Mejor discriminación de contexto (negación, ejemplos)
- **ocr_corruption**: +20 pp - Ruido en training ayudó directamente

**Sin cambio:**
- **unicode_evasion**: 33.3% - Requiere normalización de texto, no solo training

**Regresión:**
- **real_world**: -10 pp - Posible overfitting a ruido, menos robustez a patrones complejos

---

## Detalle de Tests Cambiados

### Tests que PASARON en v2 (antes FAIL)

| Test | Categoría | Nota |
|------|-----------|------|
| `ocr_letter_substitution` | ocr_corruption | DNl → DNI (l vs I) |
| `ocr_accent_loss` | ocr_corruption | José → Jose |
| `negation_dni` | adversarial | "NO tener DNI" - ya no detecta PII |
| `organization_as_person` | adversarial | García y Asociados → ORG |
| `location_as_person` | adversarial | San Fernando → LOCATION |

### Tests que FALLARON en v2 (antes PASS)

| Test | Categoría | Nota |
|------|-----------|------|
| `notarial_header` | real_world | Posible regresión en fechas escritas |
| `judicial_sentence_header` | real_world | Posible regresión en nombres mayúsculas |

---

## Conclusiones

### Hallazgos Principales

1. **Noise training funciona**: +8.6 pp mejora global, especialmente en OCR y adversarial
2. **El ruido específico importa**: l↔I, acentos mejoraron, pero 0↔O y espacios siguen fallando
3. **Trade-off observado**: Ganamos robustez a ruido pero perdimos algo de precisión en patrones complejos

### Limitaciones del Enfoque

1. **Ruido insuficiente para 0↔O**: El IBAN con O en lugar de 0 sigue fallando
2. **Normalización necesaria**: Unicode evasion requiere preprocesamiento, no solo training
3. **Real-world complexity**: Documentos complejos requieren más datos de entrenamiento

### Recomendaciones

| Prioridad | Acción | Impacto Esperado |
|-----------|--------|------------------|
| ALTA | Añadir normalización Unicode en preprocesamiento | +10% unicode_evasion |
| ALTA | Más variedad de ruido 0↔O en training | +5-10% ocr_corruption |
| MEDIA | Más ejemplos real_world en dataset | Recuperar -10% real_world |
| MEDIA | Pipeline híbrido (Regex → NER → Validación) | +15-20% según literatura |

---

## Próximos Pasos

1. **Implementar pipeline híbrido** según investigación PMC12214779
2. **Añadir text_normalizer.py** como preprocesamiento antes de inferencia
3. **Expandir dataset** con más ejemplos de documentos reales
4. **Evaluar CRF layer** para mejorar coherencia de secuencias

---

## Archivos Relacionados

- `docs/reports/2026-01-20_adversarial_evaluation.md` - Evaluación v1
- `docs/reports/2026-01-21_adversarial_evaluation_v2.md` - Evaluación v2
- `docs/reports/2026-01-16_investigacion_pipeline_pii.md` - Best practices
- `scripts/preprocess/inject_ocr_noise.py` - Script de inyección de ruido

---

**Fecha:** 2026-01-22
