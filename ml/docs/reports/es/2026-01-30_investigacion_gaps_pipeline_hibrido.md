# Investigación: Gaps del Pipeline Híbrido NER-PII

**Fecha:** 2026-01-30
**Autor:** AlexAlves87
**Objetivo:** Analizar gaps críticos del pipeline híbrido basándose en literatura académica 2024-2026
**Versión:** 2.0.0 (reescrito con fundamento académico)

---

## 1. Resumen Ejecutivo

Se identificaron 5 gaps en el pipeline híbrido NER-PII de ContextSafe. Para cada gap se realizó revisión de literatura académica en fuentes de primer nivel (ACL, EMNLP, COLING, NAACL, TACL, Nature Scientific Reports, Springer, arXiv). Las recomendaciones propuestas se basan en evidencia publicada, no en intuiciones.

| Gap | Prioridad | Papers Revisados | Recomendación Principal |
|-----|-----------|------------------|------------------------|
| Merge Strategy | **ALTA** | 7 | Pipeline 3 fases (RECAP) + prioridad por tipo |
| Confidence Calibration | **ALTA** | 5 | Conformal Prediction + BRB para regex |
| Benchmark Comparativo | **MEDIA** | 3 | nervaluate (SemEval'13) con partial matching |
| Latencia/Memoria | **MEDIA** | 4 | ONNX Runtime + INT8 quantization |
| Gazetteers | **BAJA** | 5 | GAIN-style integration como post-filtro |

---

## 2. Literatura Revisada

| Paper/Sistema | Venue/Fuente | Año | Hallazgo Relevante |
|---------------|-------------|------|-------------------|
| RECAP: Hybrid PII Detection | arXiv 2510.07551 | 2025 | Pipeline 3 fases: detección → desambiguación multi-label → consolidación spans |
| Hybrid rule-based NLP + ML for PII (Mishra et al.) | Nature Scientific Reports | 2025 | F1 0.911 en docs financieros, merge overlaps por min(start)/max(end) |
| Conformal Prediction for NER | arXiv 2601.16999 | 2026 | Prediction sets con garantías de cobertura ≥95%, calibración estratificada |
| JCLB: Contrastive Learning + BRB | Springer Cybersecurity | 2024 | Belief Rule Base asigna confianza aprendida a regex, D-CMA-ES optimiza params |
| CMiNER | Expert Systems with Applications | 2025 | Entity-level confidence estimators para datos ruidosos |
| B2NER | COLING 2025 | 2025 | Unified NER benchmark, 54 datasets, LoRA adapters ≤50MB, supera GPT-4 |
| nervaluate (SemEval'13 Task 9) | GitHub/MantisAI | 2024 | Métricas COR/INC/PAR/MIS/SPU con partial matching |
| T2-NER | TACL | 2023 | Framework 2 etapas span-based para entidades overlapped y discontinuas |
| GNNer | ACL SRW 2022 | 2022 | Graph Neural Networks para reducir spans solapados |
| GAIN: Gazetteer-Adapted Integration | SemEval-2022 | 2022 | KL divergence para adaptar gazetteer network a language model, 1st en 3 tracks |
| Presidio | Microsoft Open Source | 2025 | `_remove_duplicates`: highest confidence wins, containment → larger span |
| Soft Gazetteers | ACL 2020 | 2020 | Cross-lingual entity linking para gazetteers en low-resource |
| SPLR (span-based nested NER) | J. Supercomputing | 2025 | F1 87.5 en ACE2005 con Prior Knowledge Function |
| HuggingFace Optimum + ONNX | MarkTechPost/HuggingFace | 2025 | Benchmark PyTorch vs ONNX Runtime vs quantized INT8 |
| PyDeID | PHI De-identification | 2025 | regex + spaCy NER, F1 87.9% en notas clínicas, 0.48s/nota |

---

## 3. Gap 1: Merge Strategy (ALTA)

### 3.1 Problema

Cuando NER transformer y Regex detectan la misma entidad con límites o tipos diferentes, ¿cuál preferir?

```
Texto: "Don José García con DNI 12 345 678 Z"

NER detecta:   "José García con DNI 12 345 678" (PERSON extendido, parcial)
Regex detecta: "12 345 678 Z" (DNI_NIE, completo)
```

### 3.2 Estado del Arte

#### 3.2.1 RECAP Framework (arXiv 2510.07551, 2025)

El framework más reciente y completo para merge en PII híbrido implementa **tres fases**:

1. **Fase I - Detección base:** Regex para PII estructurado (IDs, teléfonos) + LLM para no-estructurado (nombres, direcciones). Produce multi-labels, overlaps y falsos positivos.

2. **Fase II - Desambiguación multi-label:** Para entidades con múltiples labels, el texto, span y labels candidatos se pasan a un LLM con prompt contextual que selecciona la label correcta.

3. **Fase III - Consolidación:** Dos filtros:
   - **Resolución de overlap determinista:** Entidades de menor prioridad completamente contenidas en spans más largos se eliminan.
   - **Filtrado contextual de falsos positivos:** Secuencias numéricas cortas se verifican con contexto de la oración circundante.

**Resultado:** F1 0.657 promedio en 13 locales, superando NER puro (0.360) en 82% y zero-shot LLM (0.558) en 17%.

#### 3.2.2 Microsoft Presidio (2025)

Presidio implementa `__remove_duplicates()` con reglas simples:
- **Mayor confidence score gana** entre detecciones solapadas
- **Containment:** Si un PII está contenido en otro, se usa el de **texto más largo**
- **Partial intersection:** Ambos se retornan concatenados
- No hay prioridad por tipo, solo por score

#### 3.2.3 Mishra et al. (Nature Scientific Reports, 2025)

Para documentos financieros, merging de overlaps:
- `start = min(start1, start2)`
- `end = max(end1, end2)`
- El overlap se fusiona en una sola entidad consolidada

**Limitación:** No distingue tipos — no sirve cuando NER detecta PERSON y Regex detecta DNI en el mismo span.

#### 3.2.4 T2-NER (TACL, 2023)

Framework span-based de 2 etapas:
1. Extraer todos los entity spans (overlapped y flat)
2. Clasificar pares de spans para resolver discontinuidades

**Insight aplicable:** Separar detección de spans de su clasificación permite manejar overlaps de forma modular.

#### 3.2.5 GNNer (ACL Student Research Workshop, 2022)

Usa Graph Neural Networks para reducir overlapping spans en NER span-based. Los spans candidatos son nodos en un grafo, y GNN aprende a eliminar los solapados.

**Insight aplicable:** El overlap no siempre es error — entidades nested (nombre dentro de dirección) son legítimas.

### 3.3 Implementación Actual de ContextSafe

Archivo: `scripts/inference/ner_predictor.py`, método `_merge_regex_detections()`

```python
# Estrategia actual (líneas 430-443):
for ner_ent in ner_entities:
    replaced = False
    for match in regex_matches:
        if overlaps(match, ner_ent):
            if regex_len > ner_len * 1.2:  # Regex 20% más largo
                replaced = True
                break
    if not replaced:
        ner_to_keep.append(ner_ent)
```

**Regla actual:** Si regex es ≥20% más largo que NER y hay overlap → preferir regex.

### 3.4 Análisis Comparativo

| Sistema | Estrategia | Maneja Nested | Usa Tipo | Usa Confianza |
|---------|-----------|---------------|----------|---------------|
| RECAP | 3 fases + LLM | ✅ | ✅ | Implícito |
| Presidio | Highest score | ❌ | ❌ | ✅ |
| Mishra et al. | min/max merge | ❌ | ❌ | ❌ |
| ContextSafe actual | Regex más largo gana | ❌ | ❌ | ❌ |
| **Propuesta** | **Prioridad tipo + validación** | **✅** | **✅** | **✅** |

### 3.5 Recomendación Basada en Evidencia

Inspirándose en RECAP (3 fases) pero sin depender de LLM (nuestro requisito es inferencia CPU sin LLM), proponemos:

**Fase 1: Detección independiente**
- NER transformer detecta entidades semánticas (PERSON, ORGANIZATION, LOCATION)
- Regex detecta entidades estructurales (DNI, IBAN, PHONE, DATE)

**Fase 2: Resolución de overlaps por prioridad de tipo**

Basado en la evidencia de RECAP (regex excele en PII estructurado, NER en semántico):

```python
MERGE_PRIORITY = {
    # Tipo → (prioridad, fuente_preferida)
    # Regex con checksum = máxima confianza (evidencia: Mishra et al. 2025)
    "DNI_NIE": (10, "regex"),      # Checksum validable
    "IBAN": (10, "regex"),         # Checksum validable
    "NSS": (10, "regex"),          # Checksum validable
    "PHONE": (8, "regex"),         # Formato bien definido
    "POSTAL_CODE": (8, "regex"),   # 5 dígitos exactos
    "LICENSE_PLATE": (8, "regex"), # Formato bien definido
    # NER excele en entidades semánticas (RECAP, PyDeID)
    "DATE": (6, "any"),            # Ambos válidos
    "PERSON": (4, "ner"),          # NER mejor con contexto
    "ORGANIZATION": (4, "ner"),    # NER mejor con contexto
    "LOCATION": (4, "ner"),        # NER mejor con contexto
    "ADDRESS": (4, "ner"),         # NER mejor con contexto
}
```

**Fase 3: Consolidación**
- Entidades **contenidas** de diferente tipo: mantener ambas (nested legítimo, como en GNNer)
- Entidades **contenidas** de mismo tipo: preferir la más específica (fuente preferida)
- Overlap **parcial**: preferir tipo de mayor prioridad
- Sin overlap: mantener ambas

| Situación | Regla | Evidencia |
|-----------|-------|-----------|
| Sin overlap | Mantener ambos | Estándar |
| Overlap, tipos diferentes | Mayor prioridad gana | RECAP Fase III |
| Containment, tipos diferentes | Mantener ambos (nested) | GNNer, T2-NER |
| Containment, mismo tipo | Fuente preferida según tabla | Presidio (larger span) |
| Overlap parcial, mismo tipo | Mayor confianza gana | Presidio |

---

## 4. Gap 2: Confidence Calibration (ALTA)

### 4.1 Problema

Regex devuelve confianza fija (0.95), NER devuelve probabilidad de softmax. No son comparables directamente.

### 4.2 Estado del Arte

#### 4.2.1 Conformal Prediction para NER (arXiv 2601.16999, enero 2026)

**Paper más reciente y relevante.** Introduce framework para producir **prediction sets** con garantías de cobertura:

- Dado nivel de confianza `1-α`, genera conjuntos de predicción garantizados de contener la etiqueta correcta
- Usa **non-conformity scores**:
  - `nc1`: `1 - P̂(y|x)` — basado en probabilidad, penaliza baja confianza
  - `nc2`: probabilidad acumulada en secuencias rankeadas
  - `nc3`: basado en rank, produce sets de tamaño fijo

**Hallazgos clave:**
- `nc1` sustancialmente supera a `nc2` (que produce sets "extremadamente grandes")
- **Calibración estratificada por longitud** corrige miscalibración sistemática en secuencias largas
- **Calibración por idioma** mejora cobertura (inglés: 93.82% → 96.24% tras estratificación)
- Corrección de Šidák para múltiples entidades: confianza per-entidad = `(1-α)^(1/s)` para `s` entidades

**Aplicabilidad a ContextSafe:** La calibración estratificada por longitud del texto es directamente aplicable. Textos largos (contratos) pueden tener scores sistemáticamente diferentes a textos cortos.

#### 4.2.2 JCLB: Belief Rule Base (Springer Cybersecurity, 2024)

Introduce un enfoque para **asignar confianza a reglas regex** de forma aprendida:

- Las reglas regex se formalizan como un **Belief Rule Base (BRB)**
- Cada regla tiene **belief degrees** (grados de creencia) optimizados por D-CMA-ES
- El BRB filtra categorías de entidades y evalúa su corrección simultáneamente
- Los parámetros del BRB se optimizan contra datos de entrenamiento

**Insight clave:** Las reglas regex NO deberían tener confianza fija. Su confianza debe aprenderse/calibrarse contra datos reales.

#### 4.2.3 CMiNER (Expert Systems with Applications, 2025)

Diseña **entity-level confidence estimators** que:
- Evalúan calidad inicial de datasets ruidosos
- Asisten durante el entrenamiento ajustando pesos

**Insight aplicable:** La confianza a nivel de entidad (no token) es más útil para decisiones de merge.

#### 4.2.4 Conf-MPU (Zhou et al., 2022)

Token-level binary classification para predecir probabilidad de cada token ser entidad, luego usa scores de confianza para risk estimation.

**Insight aplicable:** Separar "¿es esto una entidad?" de "¿qué tipo?" permite calibrar en dos etapas.

### 4.3 Implementación Actual de ContextSafe

```python
# Regex patterns (spanish_id_patterns.py):
RegexMatch(..., confidence=0.95)  # Valor fijo hardcodeado

# NER model:
confidence = softmax(logits).max()  # Probabilidad real [0.5-0.99]

# Ajuste por checksum (ner_predictor.py, líneas 473-485):
if is_valid:
    final_confidence = min(match.confidence * 1.1, 0.99)
elif checksum_conf < 0.5:
    final_confidence = match.confidence * 0.5
```

### 4.4 Análisis del Problema

| Fuente | Confianza | Calibrada | Problema |
|--------|-----------|-----------|----------|
| NER softmax | 0.50-0.99 | ✅ | Puede estar miscalibrada para textos largos (CP 2026) |
| Regex sin checksum | 0.95 fijo | ❌ | Sobreconfianza en matches ambiguos |
| Regex con checksum válido | 0.99 | ⚠️ | Apropiado para IDs con checksum |
| Regex con checksum inválido | 0.475 | ✅ | Penalización adecuada |

### 4.5 Recomendación Basada en Evidencia

#### Nivel 1: Confianza base diferenciada por tipo (inspirado en JCLB/BRB)

No usar confianza fija. Asignar **confianza base** según el nivel de validación disponible:

```python
REGEX_BASE_CONFIDENCE = {
    # Con checksum validable (máxima confianza, Mishra et al. 2025)
    "DNI_NIE":  {"checksum_valid": 0.98, "checksum_invalid": 0.35, "format_only": 0.70},
    "IBAN":     {"checksum_valid": 0.99, "checksum_invalid": 0.30, "format_only": 0.65},
    "NSS":      {"checksum_valid": 0.95, "checksum_invalid": 0.35, "format_only": 0.65},

    # Sin checksum, con formato bien definido
    "PHONE":         {"with_prefix": 0.90, "without_prefix": 0.75},
    "POSTAL_CODE":   {"valid_province": 0.85, "format_only": 0.70},
    "LICENSE_PLATE": {"modern_format": 0.90, "old_format": 0.80},

    # Ambiguos
    "DATE":  {"full_textual": 0.85, "partial": 0.60, "ambiguous": 0.50},
    "EMAIL": {"standard": 0.95},
}
```

**Justificación:** JCLB demostró que la confianza de reglas debe ser aprendida/diferenciada, no fija. Sin acceso a datos de entrenamiento para optimizar BRB (como D-CMA-ES en JCLB), usamos heurísticas basadas en el nivel de validación disponible (checksum > formato > match simple).

#### Nivel 2: Calibración estratificada (inspirado en CP 2026)

Para NER transformer, considerar calibración por longitud de texto:
- Textos cortos (1-10 tokens): umbral mínimo de confianza 0.60
- Textos medios (11-50 tokens): umbral 0.50
- Textos largos (51+ tokens): umbral 0.45

**Justificación:** El paper de Conformal Prediction (2026) demostró que textos largos tienen cobertura sistemáticamente diferente. Estratificar por longitud corrige esta miscalibración.

#### Nivel 3: Umbral de confianza operativo

Basado en RECAP y PyDeID:
- **≥0.80:** Anonimización automática
- **0.50-0.79:** Anonimización con flag "revisar"
- **<0.50:** No anonimizar, reportar como "dudoso"

---

## 5. Gap 3: Benchmark Comparativo (MEDIA)

### 5.1 Estado del Arte en Evaluación NER

#### 5.1.1 Métricas: seqeval vs nervaluate

| Framework | Tipo | Partial Match | Nivel | Estándar |
|-----------|------|---------------|-------|----------|
| **seqeval** | Strict entity-level | ❌ | Entidad completa | CoNLL eval |
| **nervaluate** | Multi-escenario | ✅ | COR/INC/PAR/MIS/SPU | SemEval'13 Task 9 |

**seqeval** (CoNLL standard):
- Precision, Recall, F1 a nivel de entidad completa
- Solo match exacto: tipo correcto Y span completo
- Micro/macro average por tipo

**nervaluate** (SemEval'13 Task 9):
- 4 escenarios: strict, exact, partial, type
- 5 categorías: COR (correct), INC (incorrect type), PAR (partial span), MIS (missed), SPU (spurious)
- Partial matching: `Precision = (COR + 0.5 × PAR) / ACT`

**Recomendación:** Usar **ambas** métricas. seqeval para comparabilidad con literatura (CoNLL), nervaluate para análisis más fino de errores parciales.

#### 5.1.2 B2NER Benchmark (COLING 2025)

- 54 datasets, 400+ entity types, 6 idiomas
- Benchmark unificado para Open NER
- LoRA adapters ≤50MB superan GPT-4 por 6.8-12.0 F1

**Aplicabilidad:** B2NER confirma que LoRA es viable para NER especializado, pero requiere datos de calidad (54 datasets refinados).

### 5.2 Datos Disponibles de ContextSafe

| Configuración | F1 Strict | Pass Rate | Fuente |
|---------------|-----------|-----------|--------|
| NER solo (legal_ner_v2 base) | 0.464 | 28.6% | Baseline |
| NER + Normalizer | 0.492 | 34.3% | Ciclo ML |
| NER + Regex | 0.543 | 45.7% | Ciclo ML |
| **Pipeline completo (5 elem)** | **0.788** | **60.0%** | Ciclo ML |
| LoRA fine-tuning puro | 0.016 | 5.7% | Exp. 2026-02-04 |
| GLiNER zero-shot | 0.325 | 11.4% | Exp. 2026-02-04 |

### 5.3 Benchmark Pendiente

| Test | Métrica | Estado |
|------|---------|--------|
| Evaluar con nervaluate (partial matching) | COR/INC/PAR/MIS/SPU | Pendiente |
| Solo Regex (sin NER) | F1 strict + partial | Pendiente |
| NER + Checksum (sin regex patterns) | F1 strict + partial | Pendiente |
| Comparación entity-type breakdown | Per-type F1 | Pendiente |

### 5.4 Recomendación

Crear script `scripts/evaluate/benchmark_nervaluate.py` que:
1. Ejecute pipeline completo contra adversarial test set
2. Reporte métricas seqeval (strict, para comparabilidad)
3. Reporte métricas nervaluate (4 escenarios, para análisis de errores)
4. Desglose por tipo de entidad
5. Compare ablaciones (NER solo, Regex solo, Híbrido)

---

## 6. Gap 4: Latencia/Memoria (MEDIA)

### 6.1 Objetivo

| Métrica | Objetivo | Justificación |
|---------|----------|---------------|
| Latencia | <500ms por página A4 (~600 tokens) | UX responsiva |
| Memoria | <2GB modelo en RAM | Despliegue en 16GB |
| Throughput | >10 páginas/segundo (batch) | Procesamiento masivo |

### 6.2 Estado del Arte en Optimización de Inferencia

#### 6.2.1 ONNX Runtime + Quantization (HuggingFace Optimum, 2025)

HuggingFace Optimum permite:
- Export a ONNX
- Optimización de grafos (fusion de operadores, eliminación de nodos redundantes)
- Quantización INT8 (dynamic o static)
- Benchmarking integrado: PyTorch vs torch.compile vs ONNX vs ONNX quantized

**Resultados reportados:**
- TensorRT-Optimized: hasta 432 inferencias/segundo (ResNet-50, no NER)
- ONNX Runtime: speedup típico 2-4x sobre PyTorch vanilla en CPU

#### 6.2.2 PyDeID (2025)

Sistema híbrido regex + spaCy NER para de-identificación:
- **0.48 segundos/nota** vs 6.38 segundos/nota del sistema base
- Factor 13x de speedup con regex + NER optimizado
- F1 87.9% con el pipeline rápido

**Aplicabilidad directa:** PyDeID demuestra que un pipeline híbrido regex+NER puede procesar 1 documento en <0.5s.

#### 6.2.3 Transformer Optimization Pipeline

```
PyTorch FP32 → ONNX Export → Graph Optimization → INT8 Quantization
    baseline        2x             2-3x                  3-4x
```

### 6.3 Estimación Teórica para ContextSafe

| Componente | CPU (PyTorch) | CPU (ONNX INT8) | Memoria |
|------------|---------------|------------------|---------|
| TextNormalizer | <1ms | <1ms | ~0 |
| NER (RoBERTa-BNE ~125M) | ~200-400ms | ~50-100ms | ~500MB → ~200MB |
| Checksum validators | <1ms | <1ms | ~0 |
| Regex patterns | <5ms | <5ms | ~0 |
| Date patterns | <2ms | <2ms | ~0 |
| Boundary refinement | <1ms | <1ms | ~0 |
| **Total** | **~210-410ms** | **~60-110ms** | **~500MB → ~200MB** |

**Conclusión:** Con ONNX INT8 debería cumplir <500ms/página con margen amplio.

### 6.4 Recomendación

1. **Primero medir** latencia actual con PyTorch (script `benchmark_latency.py`)
2. **Si cumple** <500ms en CPU: documentar y diferir optimización ONNX
3. **Si no cumple**: export ONNX + quantización INT8 (priorizar)
4. **Documentar** proceso para replicabilidad en otros idiomas

---

## 7. Gap 5: Gazetteers (BAJA)

### 7.1 Estado del Arte

#### 7.1.1 GAIN: Gazetteer-Adapted Integration Network (SemEval-2022)

- **Adaptación KL divergence:** Gazetteer network se adapta a language model minimizando KL divergence
- **2 etapas:** Primero adaptar gazetteer al modelo, luego entrenar NER supervisado
- **Resultado:** 1ro en 3 tracks (Chino, Code-mixed, Bangla), 2do en 10 tracks
- **Insight:** Gazetteers son más útiles cuando se integran como feature adicional, no como lookup directo

#### 7.1.2 Gazetteer-Enhanced Attentive Neural Networks (EMNLP 2019)

- Red auxiliar que codifica "regularidad de nombres" usando solo gazetteers
- Se incorpora al NER principal para mejor reconocimiento
- **Reduce requisitos de datos de entrenamiento** significativamente

#### 7.1.3 Soft Gazetteers para Low-Resource NER (ACL 2020)

- En idiomas sin gazetteers exhaustivos, usar cross-lingual entity linking
- Wikipedia como fuente de conocimiento
- Experimentado en 4 idiomas low-resource

#### 7.1.4 Reducción de Spurious Matching

- Gazetteers crudos generan **muchos falsos positivos** (matching espurio)
- Filtrar por "entity popularity" mejora F1 en +3.70%
- **Gazetteers limpios > Gazetteers completos**

### 7.2 Gazetteers Disponibles en ContextSafe

| Gazetteer | Registros | Fuente | En Pipeline |
|-----------|-----------|--------|-------------|
| Apellidos | 27,251 | INE | ❌ |
| Nombres hombres | 550 | INE | ❌ |
| Nombres mujeres | 550 | INE | ❌ |
| Nombres arcaicos | 6,010 | Generado | ❌ |
| Municipios | 8,115 | INE | ❌ |
| Códigos postales | 11,051 | INE | ❌ |

### 7.3 Recomendación Basada en Evidencia

**No integrar gazetteers en el pipeline core** por las siguientes razones basadas en literatura:

1. **Spurious matching** (EMNLP 2019): Sin filtrado de popularidad, los gazetteers generan falsos positivos
2. **Pipeline ya funciona** (F1 0.788): El beneficio marginal de gazetteers es bajo
3. **Complejidad de replicabilidad**: Gazetteers son language-specific, cada idioma necesita fuentes diferentes

**Uso recomendado como post-filtro:**
- **Validación de nombres:** Si NER detecta PERSON, verificar si nombre/apellido está en gazetteer → boost confidence +0.05
- **Validación de CP:** Si regex detecta POSTAL_CODE 28001, verificar si corresponde a municipio real → boost confidence +0.10
- **NO usar para detección:** No buscar nombres del gazetteer en texto directamente (riesgo de spurious matching)

---

## 8. Plan de Acción

### 8.1 Acciones Inmediatas (Alta Prioridad)

| Acción | Base Académica | Archivo |
|--------|---------------|---------|
| Implementar merge strategy 3 fases | RECAP (2025) | `ner_predictor.py` |
| Eliminar confianza fija 0.95 en regex | JCLB/BRB (2024) | `spanish_id_patterns.py` |
| Añadir tabla de prioridades por tipo | RECAP, Presidio | `ner_predictor.py` |

### 8.2 Acciones de Mejora (Media Prioridad)

| Acción | Base Académica | Archivo |
|--------|---------------|---------|
| Evaluar con nervaluate (partial matching) | SemEval'13 Task 9 | `benchmark_nervaluate.py` |
| Crear benchmark de latencia | PyDeID (2025) | `benchmark_latency.py` |
| Documentar calibración por longitud | CP NER (2026) | Guía replicabilidad |

### 8.3 Acciones Diferidas (Baja Prioridad)

| Acción | Base Académica | Archivo |
|--------|---------------|---------|
| Gazetteers como post-filtro | GAIN (2022) | `ner_predictor.py` |
| Export ONNX + INT8 | HuggingFace Optimum | `scripts/export/` |

---

## 9. Conclusiones

### 9.1 Hallazgos Principales de la Investigación

1. **El pipeline híbrido es el enfoque SOTA para PII** — RECAP (2025), PyDeID (2025) y Mishra et al. (2025) confirman que regex + NER supera a cada componente por separado.

2. **La confianza de regex no debe ser fija** — JCLB (2024) demostró que asignar confianza aprendida a reglas mejora significativamente el rendimiento.

3. **La calibración por longitud de texto es importante** — Conformal Prediction (2026) demostró miscalibración sistemática en secuencias largas.

4. **nervaluate complementa seqeval** — SemEval'13 Task 9 ofrece métricas de partial matching que capturan errores de boundary que seqeval ignora.

5. **ONNX INT8 es viable para latencia <500ms** — PyDeID demostró <0.5s/documento con pipeline híbrido optimizado.

### 9.2 Estado de Modelos Evaluados

| Modelo | Evaluación | F1 Adversarial | Estado |
|--------|-----------|----------------|--------|
| **RoBERTa-BNE CAPITEL NER** (`legal_ner_v2`) | Pipeline completo 5 elementos | **0.788** | **ACTIVO** |
| GLiNER-PII (zero-shot) | Evaluado en 35 tests adversariales | 0.325 | Descartado (inferior) |
| LoRA Legal-XLM-R-base (`lora_ner_v1`) | Evaluado en 35 tests adversariales | 0.016 | Descartado (overfitting) |
| MEL (Modelo Español Legal) | Investigado | N/A (sin versión NER) | Descartado |
| Legal-XLM-R-base (joelniklaus) | Investigado para multilingüe | N/A | Pendiente para expansión futura |

> **Nota:** El modelo base del pipeline es `roberta-base-bne-capitel-ner` (RoBERTa-BNE, ~125M params, vocab 50,262),
> fine-tuned con datos sintéticos v3 (30% noise injection). **No** es XLM-RoBERTa.

### 9.3 Recomendaciones para Replicabilidad

Para replicar en otros idiomas, los adaptadores son:

| Componente | Spain (ES) | Francia (FR) | Italia (IT) | Adaptación |
|------------|-----------|-------------|------------|------------|
| NER Model | RoBERTa-BNE CAPITEL | JuriBERT/CamemBERT | Legal-BERT-IT | Fine-tune NER por idioma |
| NER Multilingüe (alternativa) | Legal-XLM-R | Legal-XLM-R | Legal-XLM-R | Un solo modelo multilingüe |
| Regex patterns | DNI/NIE, IBAN ES | CNI, IBAN FR | CF, IBAN IT | Nuevo archivo regex |
| Checksum validators | mod-23 (DNI) | mod-97 (IBAN) | Codice Fiscale | Nuevo validador |
| Merge priorities | Tabla 3.5 | Misma estructura | Misma estructura | Ajustar tipos |
| Confidence calibration | Tabla 4.5 | Misma estructura | Misma estructura | Calibrar por tipo local |
| Gazetteers | INE | INSEE | ISTAT | Fuentes nacionales |

---

## 10. Referencias

1. **RECAP Framework.** "An Evaluation Study of Hybrid Methods for Multilingual PII Detection." arXiv:2510.07551, 2025.
2. **Mishra et al.** "A hybrid rule-based NLP and machine learning approach for PII detection and anonymization in financial documents." *Nature Scientific Reports*, 2025. DOI: 10.1038/s41598-025-04971-9
3. **Conformal Prediction for NER.** "Uncertainty Quantification for Named Entity Recognition via Full-Sequence and Subsequence Conformal Prediction." arXiv:2601.16999, 2026.
4. **JCLB.** "Joint contrastive learning and belief rule base for named entity recognition in cybersecurity." *Springer Cybersecurity*, 2024. DOI: 10.1186/s42400-024-00206-y
5. **CMiNER.** "Named entity recognition on imperfectly annotated data via confidence and meta weight adaptation." *Expert Systems with Applications*, 2025.
6. **B2NER.** "Beyond Boundaries: Learning Universal Entity Taxonomy across Datasets and Languages for Open Named Entity Recognition." *COLING 2025*.
7. **nervaluate.** MantisAI. SemEval 2013 Task 9 evaluation metrics. GitHub, 2024.
8. **T2-NER.** "A Two-Stage Span-Based Framework for Unified Named Entity Recognition with Templates." *TACL*, 2023.
9. **GNNer.** "Reducing Overlapping in Span-based NER Using Graph Neural Networks." *ACL Student Research Workshop*, 2022.
10. **GAIN.** "Gazetteer-Adapted Integration Network for Multilingual Complex Named Entity Recognition." *SemEval-2022*.
11. **Soft Gazetteers.** "Soft Gazetteers for Low-resource Named Entity Recognition." *ACL*, 2020.
12. **Gazetteer-Enhanced ANN.** "Gazetteer-Enhanced Attentive Neural Networks for Named Entity Recognition." *EMNLP*, 2019.
13. **SPLR.** "A single-point and length-representation-based model for nested named entity recognition." *Journal of Supercomputing*, 2025.
14. **PyDeID.** Sundrelingam et al. Updated open-source PHI de-identification tool. 2025.
15. **Microsoft Presidio.** Open-source framework for detecting PII. Microsoft, 2025.
16. **HuggingFace Optimum.** End-to-end Transformer model optimization with ONNX Runtime. 2025.

---

**Generado por:** AlexAlves87
**Fecha:** 2026-01-30
**Versión:** 2.0.0 — Reescrito con investigación académica (v1.0 carecía de fundamento)
