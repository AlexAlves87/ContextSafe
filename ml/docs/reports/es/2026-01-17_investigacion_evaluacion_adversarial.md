# Investigación: Best Practices para Evaluación Adversarial de NER

**Fecha:** 2026-01-17
**Objetivo:** Fundamentar metodología de evaluación adversarial antes de implementar scripts

---

## 1. Resumen Ejecutivo

La literatura académica reciente (2024-2025) establece que la evaluación adversarial de modelos NER debe considerar:

1. **Ruido real vs simulado** - El ruido real es significativamente más difícil que el simulado
2. **Evaluación a nivel de entidad** - No a nivel de token
3. **Múltiples categorías de perturbación** - OCR, Unicode, contexto, formato
4. **Métricas estándar** - seqeval con F1, Precision, Recall por tipo de entidad

---

## 2. Fuentes Consultadas

### 2.1 NoiseBench (Mayo 2024)

**Fuente:** [NoiseBench: Benchmarking the Impact of Real Label Noise on NER](https://arxiv.org/abs/2405.07609)

**Hallazgos clave:**
- El ruido real (errores humanos, crowdsourcing, LLM) es **significativamente más difícil** que el ruido simulado
- Los modelos state-of-the-art "fall far short of their theoretically achievable upper bound"
- Se deben evaluar 6 tipos de ruido real: expert errors, crowdsourcing errors, automatic annotation errors, LLM errors

**Aplicación a nuestro proyecto:**
- Nuestros tests incluyen ruido OCR real (confusión l/I, 0/O) ✓
- Debemos añadir tests con errores de anotación automática

### 2.2 Context-Aware Adversarial Training for NER (MIT TACL)

**Fuente:** [Context-aware Adversarial Training for Name Regularity Bias](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00386/102846)

**Hallazgos clave:**
- Los modelos NER muestran "Name Regularity Bias" - dependen demasiado del nombre y no del contexto
- BERT fine-tuned supera significativamente a LSTM-CRF en tests de sesgo
- Adversarial training con vectores de ruido aprendibles mejora la capacidad contextual

**Aplicación a nuestro proyecto:**
- Nuestros tests `negation_dni`, `example_dni`, `fictional_person` evalúan capacidad contextual ✓
- El modelo v2 (entrenado con noise) debería ser más robusto

### 2.3 OCR Impact on NER (HAL Science)

**Fuente:** [Assessing and Minimizing the Impact of OCR Quality on NER](https://hal.science/hal-03026931/document)

**Hallazgos clave:**
- OCR noise causa pérdida de ~10 puntos F1 (72% vs 82% en texto limpio)
- Se debe evaluar con "varios niveles y tipos de ruido OCR"
- Primer estudio sistemático del impacto OCR en NER multilingüe

**Aplicación a nuestro proyecto:**
- Nuestros tests OCR (5 casos) son insuficientes - la literatura recomienda más niveles
- Objetivo realista: aceptar ~10 puntos de degradación con OCR

### 2.4 seqeval - Métricas Estándar

**Fuente:** [seqeval - Sequence Labeling Evaluation](https://github.com/chakki-works/seqeval)

**Hallazgos clave:**
- Evaluación a nivel de **entidad**, no token
- Métricas: Precision, Recall, F1 por tipo y macro/micro average
- Modo strict vs lenient para matching

**Aplicación a nuestro proyecto:**
- Nuestro script usa matching fuzzy con tolerancia ±5 chars (adecuado)
- Debemos reportar métricas por tipo de entidad, no solo pass/fail

### 2.5 Enterprise Robustness Benchmark (2025)

**Fuente:** [Evaluating Robustness of LLMs in Enterprise Applications](https://arxiv.org/html/2601.06341)

**Hallazgos clave:**
- Perturbaciones menores pueden reducir rendimiento hasta **40 puntos porcentuales**
- Se debe evaluar: text edits, formatting changes, multilingual inputs, positional variations
- Modelos 4B-120B parámetros todos muestran vulnerabilidades

**Aplicación a nuestro proyecto:**
- Nuestros tests cubren text edits y formatting ✓
- Debemos considerar tests multilingües (nombres extranjeros)

---

## 3. Taxonomía de Tests Adversariales (Literatura)

| Categoría | Subcategoría | Ejemplo | Nuestro Coverage |
|-----------|--------------|---------|------------------|
| **Label Noise** | Expert errors | Anotación incorrecta | ❌ No aplica (inferencia) |
| | Crowdsourcing | Inconsistencias | ❌ No aplica (inferencia) |
| | LLM errors | Hallucinations | ❌ No aplica (inferencia) |
| **Input Noise** | OCR corruption | l/I, 0/O, espacios | ✅ 5 tests |
| | Unicode evasion | Cyrillic, fullwidth | ✅ 3 tests |
| | Format variation | D.N.I. vs DNI | ✅ Incluido |
| **Context** | Negation | "NO tener DNI" | ✅ 1 test |
| | Example/illustrative | "ejemplo: 12345678X" | ✅ 1 test |
| | Fictional | Don Quijote | ✅ 1 test |
| | Legal references | Ley 15/2022 | ✅ 1 test |
| **Edge Cases** | Long entities | Nombres nobles | ✅ 1 test |
| | Short entities | J. García | ✅ 1 test |
| | Spaced entities | IBAN con espacios | ✅ 2 tests |
| **Real World** | Document patterns | Notarial, judicial | ✅ 10 tests |

---

## 4. Métricas Recomendadas

### 4.1 Métricas Primarias (seqeval)

| Métrica | Descripción | Uso |
|---------|-------------|-----|
| **F1 Macro** | Promedio F1 por tipo de entidad | Métrica principal |
| **F1 Micro** | F1 global (todas las entidades) | Métrica secundaria |
| **Precision** | TP / (TP + FP) | Evaluar falsos positivos |
| **Recall** | TP / (TP + FN) | Evaluar entidades perdidas |

### 4.2 Métricas Adversariales

| Métrica | Descripción | Objetivo |
|---------|-------------|----------|
| **Pass Rate** | Tests pasados / Total | ≥70% |
| **OCR Degradation** | F1_clean - F1_ocr | ≤10 puntos |
| **Context Sensitivity** | % tests contextuales correctos | ≥80% |
| **FP Rate** | Falsos positivos / Detecciones | ≤15% |

---

## 5. Gaps Identificados en Nuestro Script

| Gap | Severidad | Acción |
|-----|-----------|--------|
| No reporta F1/Precision/Recall por tipo | Media | Añadir métricas seqeval |
| Pocos tests OCR (5) vs recomendado (10+) | Media | Expandir en siguiente iteración |
| No evalúa degradación vs baseline | Alta | Comparar con tests limpios |
| No tests multilingües | Baja | Añadir nombres extranjeros |

---

## 6. Recomendaciones para Nuestro Script

### 6.1 Mejoras Inmediatas

1. **Añadir métricas seqeval** - Precision, Recall, F1 por tipo de entidad
2. **Calcular degradación** - Comparar con versión limpia de cada test
3. **Reportar FP rate** - Falsos positivos como métrica separada

### 6.2 Mejoras Futuras

1. Expandir tests OCR a 10+ casos con diferentes niveles de corrupción
2. Añadir tests con nombres extranjeros (John Smith, Mohammed Ali)
3. Implementar NoiseBench-style evaluation con ruido graduado

---

## 7. Conclusión

El script actual cubre las categorías principales de evaluación adversarial según la literatura, pero debe:

1. **Mejorar métricas** - Usar seqeval para F1/P/R por tipo
2. **Expandir OCR** - Más niveles de corrupción
3. **Calcular degradación** - vs baseline limpio

**El script actual es VÁLIDO para evaluación inicial**, pero se debe iterar para cumplir completamente con best practices académicas.

---

## Referencias

1. [NoiseBench: Benchmarking the Impact of Real Label Noise on NER](https://arxiv.org/abs/2405.07609) - ICLR 2024
2. [Context-aware Adversarial Training for Name Regularity Bias](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00386/102846) - MIT TACL
3. [Assessing and Minimizing the Impact of OCR Quality on NER](https://hal.science/hal-03026931/document) - HAL Science
4. [seqeval - Sequence Labeling Evaluation](https://github.com/chakki-works/seqeval) - GitHub
5. [Evaluating Robustness of LLMs in Enterprise Applications](https://arxiv.org/html/2601.06341) - arXiv 2025
6. [nervaluate - Entity-level NER Evaluation](https://github.com/MantisAI/nervaluate) - Based on SemEval'13

---

**Autor:** AlexAlves87
**Fecha:** 2026-01-17
