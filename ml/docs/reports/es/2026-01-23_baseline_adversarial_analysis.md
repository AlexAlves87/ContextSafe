# Evaluación Adversarial Baseline: legal_ner_v2

**Fecha:** 2026-01-23
**Autor:** AlexAlves87
**Versión:** 1.0.0
**Modelo evaluado:** `legal_ner_v2` (RoBERTalex fine-tuned)

---

## 1. Resumen Ejecutivo

Este documento presenta los resultados de la evaluación adversarial del modelo `legal_ner_v2` para detección de PII en textos legales españoles. El objetivo es establecer una línea base de robustez antes de implementar mejoras.

### Hallazgos Principales

| Métrica | Valor | Interpretación |
|---------|-------|----------------|
| F1-Score (entity-level) | **0.784** | Baseline aceptable |
| Precision | 0.845 | Modelo conservador |
| Recall | 0.731 | Área de mejora prioritaria |
| Degradación por ruido | 0.080 | Dentro del umbral esperado (≤0.10) |
| Pass rate tests | 54.3% (19/35) | Nivel 4 no superado |

### Conclusión

El modelo **NO supera** el Nivel 4 de validación (adversarial). Se requieren mejoras en:
1. Normalización de entrada (Unicode, espacios)
2. Reconocimiento de fechas en formato textual español
3. Patrones específicos para NSS y CIF

---

## 2. Metodología

### 2.1 Diseño Experimental

Se diseñaron 35 casos de prueba adversarial distribuidos en 5 categorías:

| Categoría | Tests | Propósito |
|-----------|-------|-----------|
| `edge_case` | 9 | Condiciones límite (nombres largos, formatos variantes) |
| `adversarial` | 8 | Casos diseñados para confundir (negaciones, ejemplos) |
| `ocr_corruption` | 5 | Simulación de errores OCR |
| `unicode_evasion` | 3 | Intentos de evasión con caracteres similares |
| `real_world` | 10 | Extractos de documentos legales reales |

### 2.2 Niveles de Dificultad

| Nivel | Criterio de Éxito | Tests |
|-------|-------------------|-------|
| `easy` | Detectar todas las entidades esperadas | 4 |
| `medium` | Detectar todas las entidades esperadas | 12 |
| `hard` | Detectar todas las entidades Y cero falsos positivos | 19 |

### 2.3 Métricas Utilizadas

1. **Entity-level F1** (seqeval-style): Precision, Recall, F1 calculados a nivel de entidad completa, no token.

2. **Overlap Score**: Ratio de caracteres coincidentes entre entidad esperada y detectada (Jaccard sobre caracteres).

3. **Degradación por Ruido** (NoiseBench-style): Diferencia de F1 entre categorías "limpias" (`edge_case`, `adversarial`, `real_world`) y "ruidosas" (`ocr_corruption`, `unicode_evasion`).

### 2.4 Entorno de Ejecución

| Componente | Especificación |
|------------|----------------|
| Hardware | CUDA (GPU) |
| Modelo | `legal_ner_v2` (RoBERTalex) |
| Framework | PyTorch 2.0+, Transformers |
| Tiempo de carga | 1.6s |
| Tiempo de evaluación | 1.5s (35 tests) |

### 2.5 Reproducibilidad

```bash
cd ml
source .venv/bin/activate
python scripts/evaluate/test_ner_predictor_adversarial.py
```

El script genera automáticamente un reporte en `docs/reports/`.

---

## 3. Resultados

### 3.1 Métricas Agregadas

| Métrica | Valor |
|---------|-------|
| True Positives | 49 |
| False Positives | 9 |
| False Negatives | 18 |
| **Precision** | 0.845 |
| **Recall** | 0.731 |
| **F1-Score** | 0.784 |
| Mean Overlap Score | 0.935 |

### 3.2 Resultados por Categoría

| Categoría | Pass Rate | TP | FP | FN | F1 |
|-----------|-----------|----|----|----|----|
| adversarial | 75.0% | 5 | 2 | 0 | 0.833 |
| edge_case | 66.7% | 9 | 1 | 3 | 0.818 |
| ocr_corruption | 40.0% | 5 | 0 | 4 | 0.714 |
| real_world | 40.0% | 26 | 5 | 9 | 0.788 |
| unicode_evasion | 33.3% | 4 | 1 | 2 | 0.727 |

### 3.3 Resultados por Dificultad

| Dificultad | Pasados | Total | Tasa |
|------------|---------|-------|------|
| easy | 3 | 4 | 75.0% |
| medium | 9 | 12 | 75.0% |
| hard | 7 | 19 | 36.8% |

### 3.4 Análisis de Resistencia al Ruido

| Métrica | Valor | Referencia |
|---------|-------|------------|
| F1 (texto limpio) | 0.800 | - |
| F1 (con ruido) | 0.720 | - |
| **Degradación** | 0.080 | ≤0.10 (HAL Science) |
| Estado | **OK** | Dentro del umbral |

---

## 4. Análisis de Errores

### 4.1 Taxonomía de Fallos

Se identificaron 5 patrones de fallo recurrentes:

#### Patrón 1: Fechas en Formato Textual Español

| Test | Entidad Perdida |
|------|-----------------|
| `date_roman_numerals` | "XV de marzo del año MMXXIV" |
| `notarial_header` | "quince de marzo de dos mil veinticuatro" |
| `judicial_sentence_header` | "diez de enero de dos mil veinticuatro" |

**Causa raíz:** El modelo fue entrenado principalmente con fechas en formato numérico (DD/MM/YYYY). Las fechas escritas en estilo notarial español no están representadas en el corpus de entrenamiento.

**Impacto:** Alto en documentos notariales y judiciales donde este formato es estándar.

#### Patrón 2: Corrupción OCR Extrema

| Test | Entidad Perdida |
|------|-----------------|
| `ocr_extra_spaces` | "1 2 3 4 5 6 7 8 Z", "M a r í a" |
| `ocr_missing_spaces` | "12345678X" (en texto concatenado) |
| `ocr_zero_o_confusion` | "ES91 21O0 0418 45O2 OOO5 1332" |

**Causa raíz:** El tokenizador de RoBERTa no maneja bien texto con espaciado anómalo. La confusión O/0 rompe patrones regex de IBAN.

**Impacto:** Medio. Documentos escaneados de baja calidad.

#### Patrón 3: Unicode Evasion

| Test | Entidad Perdida |
|------|-----------------|
| `fullwidth_numbers` | "１２３４５６７８Z" (U+FF11-U+FF18) |

**Causa raíz:** No hay normalización Unicode previa al NER. Los dígitos fullwidth (U+FF10-U+FF19) no son reconocidos como números.

**Impacto:** Bajo en producción, pero crítico para seguridad (evasión intencional).

#### Patrón 4: Identificadores Específicos Españoles

| Test | Entidad Perdida |
|------|-----------------|
| `social_security` | "281234567890" (NSS) |
| `bank_account_clause` | "A-98765432" (CIF) |
| `professional_ids` | "12345", "67890" (números colegiados) |

**Causa raíz:** Patrones poco frecuentes en el corpus de entrenamiento. El NSS español tiene formato específico (12 dígitos) que no fue aprendido.

**Impacto:** Alto para documentos laborales y mercantiles.

#### Patrón 5: Falsos Positivos por Contexto

| Test | Entidad Falsa |
|------|---------------|
| `example_dni` | "12345678X" (contexto: "ejemplo ilustrativo") |
| `fictional_person` | "Don Quijote de la Mancha" |

**Causa raíz:** El modelo detecta patrones sin considerar contexto semántico (negaciones, ejemplos, ficción).

**Impacto:** Medio. Causa anonimización innecesaria.

### 4.2 Matriz de Confusión por Tipo de Entidad

| Tipo | TP | FP | FN | Observación |
|------|----|----|----|----|
| PERSON | 15 | 2 | 2 | Bueno, falla en ficción |
| DNI_NIE | 8 | 1 | 4 | Falla en formatos variantes |
| LOCATION | 6 | 0 | 2 | Falla en CP aislados |
| DATE | 3 | 0 | 4 | Falla en formato textual |
| IBAN | 2 | 0 | 1 | Falla con OCR |
| ORGANIZATION | 5 | 2 | 0 | Confunde con tribunales |
| NSS | 0 | 0 | 1 | No detecta |
| PROFESSIONAL_ID | 0 | 0 | 2 | No detecta |
| Otros | 10 | 4 | 2 | - |

---

## 5. Conclusiones

### 5.1 Estado Actual

El modelo `legal_ner_v2` presenta un **F1 de 0.784** en evaluación adversarial, con las siguientes características:

- **Fortalezas:**
  - Alta precisión (0.845) - pocos falsos positivos
  - Buena resistencia al ruido (degradación 0.080)
  - Excelente en nombres compuestos y direcciones

- **Debilidades:**
  - Recall insuficiente (0.731) - pierde entidades
  - No reconoce fechas en formato textual español
  - Vulnerable a Unicode evasion (fullwidth)
  - No detecta NSS ni números de colegiado

### 5.2 Nivel de Validación

| Nivel | Estado | Criterio |
|-------|--------|----------|
| Nivel 1: Unit Tests | ✅ | Funciones individuales |
| Nivel 2: Integration | ✅ | Pipeline completo |
| Nivel 3: Benchmark | ✅ | F1 > 0.75 |
| **Nivel 4: Adversarial** | ❌ | Pass rate < 70% |
| Nivel 5: Production-like | ⏸️ | Pendiente |

**Conclusión:** El modelo **NO está listo para producción** según criterios del proyecto (Nivel 4 obligatorio).

### 5.3 Trabajo Futuro

#### Prioridad ALTA (impacto estimado > 3pts F1)

1. **Normalización Unicode en preprocesamiento**
   - Convertir fullwidth a ASCII
   - Eliminar zero-width characters
   - Normalizar O/0 en contextos numéricos

2. **Augmentación de fechas textuales**
   - Generar variantes: "primero de enero", "XV de marzo"
   - Incluir numerales romanos
   - Fine-tune con corpus aumentado

3. **Patrones regex para NSS/CIF**
   - Agregar al CompositeNerAdapter
   - NSS: `\d{12}` en contexto "Seguridad Social"
   - CIF: `[A-Z]-?\d{8}` en contexto empresa

#### Prioridad MEDIA (impacto estimado 1-3pts F1)

4. **Normalización de espacios OCR**
   - Detectar y colapsar espacios excesivos
   - Reconstruir tokens fragmentados

5. **Filtro post-proceso para contextos "ejemplo"**
   - Detectar frases: "por ejemplo", "ilustrativo", "formato"
   - Suprimir entidades en esos contextos

#### Prioridad BAJA (edge cases)

6. **Gazetteer de personajes ficticios**
   - Don Quijote, Sancho Panza, etc.
   - Filtro post-proceso

7. **Fechas con numerales romanos**
   - Regex específico para estilo notarial antiguo

---

## 6. Referencias

1. **seqeval** - Entity-level evaluation metrics for sequence labeling. https://github.com/chakki-works/seqeval

2. **NoiseBench (ICLR 2024)** - Benchmark for evaluating NLP models under realistic noise conditions.

3. **HAL Science** - Study on OCR impact in NER tasks. Establece degradación esperada de ~10pts F1.

4. **RoBERTalex** - Spanish legal domain RoBERTa model. Base del modelo evaluado.

5. **Directrices del proyecto v1.0.0** - Metodología de preparación ML para ContextSafe.

---

## Anexos

### A. Configuración del Test

```yaml
total_tests: 35
categories:
  edge_case: 9
  adversarial: 8
  ocr_corruption: 5
  unicode_evasion: 3
  real_world: 10
difficulty_distribution:
  easy: 4
  medium: 12
  hard: 19
```

### B. Comando de Reproducción

```bash
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate
python scripts/evaluate/test_ner_predictor_adversarial.py
```

### C. Archivos Generados

- Reporte automático: `docs/reports/2026-01-23_adversarial_ner_v2.md`
- Análisis académico: `docs/reports/2026-01-23_baseline_adversarial_analysis.md` (este documento)

---

**Tiempo de ejecución total:** 3.1s (carga + evaluación)
**Generado por:** AlexAlves87
**Fecha:** 2026-01-23
