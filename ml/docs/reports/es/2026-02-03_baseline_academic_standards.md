# Baseline Académico: Evaluación con Estándares SemEval 2013

**Fecha:** 2026-02-03
**Autor:** AlexAlves87
**Modelo:** legal_ner_v2 (RoBERTalex fine-tuned)
**Estándar:** SemEval 2013 Task 9

---

## 1. Resumen Ejecutivo

Esta evaluación establece el **baseline real** del modelo usando estándares académicos (modo strict de SemEval 2013), reemplazando los resultados anteriores que usaban matching lenient.

### Comparación v1 vs v2

| Métrica | v1 (lenient) | v2 (strict) | Diferencia |
|---------|--------------|-------------|------------|
| **Pass Rate** | 54.3% | **28.6%** | **-25.7pp** |
| **F1-Score** | 0.784 | **0.464** | **-0.320** |
| F1 (partial) | - | 0.632 | - |

### Conclusión Principal

> **Los resultados anteriores (F1=0.784, 54.3%) estaban INFLADOS.**
> El baseline real con estándares académicos es **F1=0.464, 28.6% pass rate**.

---

## 2. Metodología

### 2.1 Diseño Experimental

| Aspecto | Especificación |
|---------|----------------|
| Modelo evaluado | `legal_ner_v2` (RoBERTalex fine-tuned) |
| Framework | PyTorch 2.0+, Transformers |
| Hardware | CUDA (GPU) |
| Estándar de evaluación | SemEval 2013 Task 9 |
| Modo principal | Strict (boundary + type exactos) |

### 2.2 Dataset de Evaluación

| Categoría | Tests | Propósito |
|-----------|-------|-----------|
| edge_case | 9 | Condiciones límite (nombres largos, formatos variantes) |
| adversarial | 8 | Casos diseñados para confundir (negaciones, ejemplos) |
| ocr_corruption | 5 | Simulación de errores OCR |
| unicode_evasion | 3 | Intentos de evasión con caracteres Unicode |
| real_world | 10 | Extractos de documentos legales reales |
| **Total** | **35** | - |

### 2.3 Métricas Utilizadas

Según SemEval 2013 Task 9:

| Métrica | Definición |
|---------|------------|
| COR | Correct: boundary Y type exactos |
| INC | Incorrect: boundary exacto, type incorrecto |
| PAR | Partial: boundary con overlap, cualquier type |
| MIS | Missing: entidad gold no detectada (FN) |
| SPU | Spurious: detección sin correspondencia gold (FP) |

**Fórmulas:**
- Precision (strict) = COR / (COR + INC + PAR + SPU)
- Recall (strict) = COR / (COR + INC + PAR + MIS)
- F1 (strict) = 2 × P × R / (P + R)

### 2.4 Reproducibilidad

```bash
# Entorno
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Dependencias
pip install nervaluate  # Opcional, métricas implementadas manualmente

# Ejecución
python scripts/evaluate/test_ner_predictor_adversarial_v2.py

# Output
# - Consola: Resultados por test con COR/INC/PAR/MIS/SPU
# - Reporte: docs/reports/YYYY-MM-DD_adversarial_v2_academic_rN.md
```

### 2.5 Diferencia con Evaluación v1

| Aspecto | v1 (lenient) | v2 (strict) |
|---------|--------------|-------------|
| Matching | Containment + 80% char overlap | Boundary exacto normalizado |
| Type | Requerido | Requerido |
| Métricas | TP/FP/FN | COR/INC/PAR/MIS/SPU |
| Estándar | Custom | SemEval 2013 Task 9 |

---

## 3. Resultados

### 3.1 Conteos SemEval 2013

| Métrica | Valor | Descripción |
|---------|-------|-------------|
| **COR** | 29 | Correctos (boundary + type exactos) |
| **INC** | 0 | Boundary correcto, type incorrecto |
| **PAR** | 21 | Match parcial (overlap solamente) |
| **MIS** | 17 | Perdidos (FN) |
| **SPU** | 8 | Espurios (FP) |
| **POS** | 67 | Total gold (COR+INC+PAR+MIS) |
| **ACT** | 58 | Total sistema (COR+INC+PAR+SPU) |

### 3.2 Interpretación

```
                    ┌─────────────────────────────────┐
                    │     GOLD: 67 entidades          │
                    │                                 │
  ┌─────────────────┼─────────────────┐               │
  │                 │    COR: 29      │               │
  │   SISTEMA: 58   │  (43% de gold)  │   MIS: 17     │
  │                 │                 │   (25%)       │
  │    SPU: 8       │    PAR: 21      │               │
  │    (14%)        │   (31% overlap) │               │
  └─────────────────┴─────────────────┴───────────────┘
```

**Análisis:**
- Solo **43%** de las entidades gold se detectan con boundary exacto
- **31%** se detectan con overlap parcial (v1 las contaba como correctas)
- **25%** se pierden completamente
- **14%** de las detecciones son falsos positivos

### 3.3 Fórmulas Aplicadas

**Modo Strict:**
```
Precision = COR / ACT = 29 / 58 = 0.500
Recall = COR / POS = 29 / 67 = 0.433
F1 = 2 * P * R / (P + R) = 0.464
```

**Modo Partial:**
```
Precision = (COR + 0.5*PAR) / ACT = (29 + 10.5) / 58 = 0.681
Recall = (COR + 0.5*PAR) / POS = (29 + 10.5) / 67 = 0.590
F1 = 2 * P * R / (P + R) = 0.632
```

---

### 3.4 Resultados por Categoría

| Categoría | Strict | Lenient | COR | PAR | MIS | SPU |
|-----------|--------|---------|-----|-----|-----|-----|
| adversarial | 75% | 75% | 5 | 1 | 0 | 3 |
| edge_case | 22% | 67% | 6 | 3 | 3 | 1 |
| ocr_corruption | 40% | 40% | 4 | 1 | 4 | 0 |
| real_world | 10% | 50% | 12 | 14 | 8 | 4 |
| unicode_evasion | 0% | 33% | 3 | 1 | 2 | 1 |

**Observaciones:**
- **real_world**: Mayor discrepancia strict vs lenient (10% vs 50%) - muchos PAR
- **unicode_evasion**: 0% strict - todas las detecciones son parciales o incorrectas
- **adversarial**: Igual en ambos modos - tests de no-detección

---

### 3.5 Resultados por Dificultad

| Dificultad | Strict | Lenient |
|------------|--------|---------|
| easy | 50% | 75% |
| medium | 42% | 75% |
| hard | 16% | 42% |

**Observación:** La diferencia strict vs lenient aumenta con la dificultad.

---

## 4. Análisis de Errores

### 4.1 Matches Parciales (PAR)

Los 21 matches parciales representan detecciones donde el boundary no es exacto:

| Tipo de PAR | Ejemplos | Causa |
|-------------|----------|-------|
| Nombre incompleto | "José María" vs "José María de la Santísima..." | RoBERTa trunca nombres largos |
| IBAN con espacios | "ES91 2100..." vs "ES912100..." | Normalización de espacios |
| Dirección parcial | "Calle Mayor 15" vs "Calle Mayor 15, 3º B" | Boundary no incluye piso/puerta |
| Persona en contexto | "John Smith" vs "Mr. John Smith" | Prefijos no incluidos |

**Implicación:** El modelo detecta la entidad pero con boundaries imprecisos.

---

### 4.2 Tests Fallados (Strict)

#### 4.2.1 Por SPU (Falsos Positivos)

| Test | SPU | Entidades Espurias |
|------|-----|-------------------|
| example_dni | 1 | "12345678X" (contexto ejemplo) |
| fictional_person | 1 | "Don Quijote de la Mancha" |
| date_ordinal | 1 | "El" |
| zero_width_space | 1 | "de" |
| judicial_sentence_header | 2 | Referencias legales |
| professional_ids | 1 | Colegio profesional |
| ecli_citation | 1 | Tribunal |

#### 4.2.2 Por MIS (Entidades Perdidas)

| Test | MIS | Entidades Perdidas |
|------|-----|-------------------|
| dni_with_spaces | 1 | "12 345 678 Z" |
| phone_international | 1 | "0034612345678" |
| date_roman_numerals | 1 | "XV de marzo del año MMXXIV" |
| ocr_zero_o_confusion | 1 | IBAN con O/0 |
| ocr_extra_spaces | 2 | DNI y nombre con espacios |
| fullwidth_numbers | 2 | DNI fullwidth, nombre |
| notarial_header | 1 | Fecha textual |

---

## 5. Conclusiones y Trabajo Futuro

### 5.1 Prioridades de Mejora

| Mejora | Impacto en COR | Impacto en PAR→COR |
|--------|----------------|-------------------|
| Text normalization (Unicode) | +2-4 COR | +2-3 PAR→COR |
| Checksum validation | Reduce SPU | - |
| Boundary refinement | - | +10-15 PAR→COR |
| Date augmentation | +3-5 COR | - |

### 5.2 Objetivo Revisado

| Métrica | Actual | Objetivo Nivel 4 |
|---------|--------|------------------|
| F1 (strict) | 0.464 | **≥ 0.70** |
| Pass rate (strict) | 28.6% | **≥ 70%** |

**Gap a cerrar:** +0.236 F1, +41.4pp pass rate

---

### 5.3 Próximos Pasos

1. **Re-evaluar** con TextNormalizer integrado (ya preparado)
2. **Implementar** boundary refinement para reducir PAR
3. **Añadir** checksum validation para reducir SPU
4. **Augmentar** datos de fechas textuales para reducir MIS

---

### 5.4 Lecciones Aprendidas

1. **El matching lenient infla resultados significativamente** (F1 0.784 → 0.464)
2. **PAR es un problema mayor que MIS** (21 vs 17) - boundaries imprecisos
3. **Los tests reales (real_world) tienen más PAR** - documentos complejos
4. **Unicode evasion no pasa ningún test strict** - área crítica

### 5.5 Valor del Estándar Académico

La evaluación con SemEval 2013 permite:
- Comparación con literatura académica
- Diagnóstico granular (COR/INC/PAR/MIS/SPU)
- Identificación precisa de áreas de mejora
- Medición honesta del progreso

---

## 6. Referencias

1. **SemEval 2013 Task 9**: Segura-Bedmar et al. "Extraction of Drug-Drug Interactions from Biomedical Texts"
2. **nervaluate**: https://github.com/MantisAI/nervaluate
3. **David Batista Blog**: https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/

---

**Tiempo de evaluación:** 1.3s
**Generado por:** AlexAlves87
**Fecha:** 2026-02-03
