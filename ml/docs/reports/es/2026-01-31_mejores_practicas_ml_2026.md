# Investigación: Mejores Prácticas ML 2025-2026 para NER-PII Legal

**Fecha:** 2026-01-31
**Autor:** AlexAlves87
**Objetivo:** Identificar técnicas de vanguardia aplicables al pipeline NER-PII de ContextSafe
**Alcance:** Literatura de primer nivel (ICLR, EMNLP, NeurIPS, NAACL, Nature) publicada 2025-2026

---

## 1. Resumen Ejecutivo

Revisión sistemática de la literatura reciente (2025-2026) en aprendizaje automático aplicado a Named Entity Recognition (NER) y detección de PII. Se identifican **8 avances significativos** respecto a las prácticas documentadas en nuestro reporte previo (2026-01-30_investigacion_finetuning_legal_xlm_r), con impacto directo en la estrategia de entrenamiento de Legal-XLM-RoBERTa para ContextSafe.

### Hallazgos Principales

| # | Técnica | Fuente | Impacto para ContextSafe |
|---|---------|--------|--------------------------|
| 1 | LoRA/QLoRA con rank alto (128-256) en todas las capas | Unsloth, COLING 2025 | Reduce VRAM de 16GB a ~4GB sin pérdida de F1 |
| 2 | RandLoRA (full-rank PEFT) | ICLR 2025 | Elimina plateau de LoRA estándar |
| 3 | Knowledge Distillation multi-perspectiva | IGI Global 2025 | +2.5-5.8% F1 con datos limitados |
| 4 | Generación sintética LLM para NER | EMNLP 2025 | Bootstrap para idiomas sin corpus anotado |
| 5 | GLiNER zero-shot PII | NAACL 2024 + updates 2025 | Baseline 81% F1 sin entrenamiento |
| 6 | Hybrid NER (transformer + reglas) | Nature Sci. Reports 2025 | 94.7% precisión en documentos financieros |
| 7 | RECAP (regex + LLM contextual) | NeurIPS 2025 | +82% sobre NER fine-tuned, +17% sobre zero-shot |
| 8 | DAPT selectivo (no universal) | ICLR 2025 | DAPT no siempre mejora; requiere evaluación previa |

### Diagnóstico: Estado Actual vs. Estado del Arte

| Capacidad | ContextSafe Actual | Estado del Arte 2026 | Gap |
|-----------|-------------------|---------------------|-----|
| Fine-tuning | Full FT planificado | LoRA/RandLoRA (PEFT) | **Alto** |
| Datos de entrenamiento | Solo gold labels | Gold + sintéticos (LLM) | **Alto** |
| Pipeline NER | Hybrid (regex+ML) | RECAP (regex+LLM contextual) | Medio |
| Zero-shot baseline | No establecido | GLiNER ~81% F1 | **Alto** |
| DAPT | Planificado universal | Selectivo (evaluar antes) | Medio |
| Inferencia | ONNX INT8 planificado | LoRA adapters + quantización | Bajo |
| Evaluación | SemEval entity-level | + adversarial + cross-lingual | Medio |
| Modelo español legal | No hay baseline | MEL (XLM-R-large, 82% F1) | **Alto** |

---

## 2. Metodología de Revisión

### 2.1 Criterios de Inclusión

| Criterio | Valor |
|----------|-------|
| Período | Enero 2025 - Febrero 2026 |
| Venues | ICLR, EMNLP, NeurIPS, NAACL, ACL, Nature, ArXiv (pre-print con citas) |
| Relevancia | NER, PII, PEFT, DAPT, legal NLP, multilingual |
| Idiomas | Multilingüe (con énfasis en español) |

### 2.2 Búsquedas Realizadas

1. "LoRA QLoRA NER fine-tuning 2025 2026 best practices"
2. "knowledge distillation LLM small model NER 2025"
3. "ICL-APT in-context learning augmented pretraining 2025"
4. "Continual Pre-Training is (not) What You Need 2025 legal"
5. "GLiNER zero-shot NER PII detection 2025 2026"
6. "EMNLP 2025 LLM data generation NER multilingual"
7. "hybrid NER transformer rules PII detection 2025"
8. "RandLoRA ICLR 2025 full rank"
9. "MEL legal Spanish language model 2025"

---

## 3. Resultados por Área Temática

### 3.1 Parameter-Efficient Fine-Tuning (PEFT)

#### 3.1.1 LoRA/QLoRA: Configuraciones Óptimas 2025-2026

La literatura reciente consolida las mejores prácticas para LoRA aplicado a NER:

| Hiperparámetro | Valor Recomendado | Fuente |
|----------------|-------------------|--------|
| Rank (r) | 128-256 | Unsloth Docs, Medical NER studies |
| Alpha (α) | 2×r (256-512) | Heurística validada empíricamente |
| Target modules | Atención **+ MLP** (todas las capas) | Databricks, Lightning AI |
| Learning rate | 2e-4 (inicio), rango 5e-6 a 2e-4 | Unsloth, Medium/QuarkAndCode |
| Epochs | 1-3 (riesgo overfitting >3) | Consenso múltiples fuentes |
| Dropout | 0.05 (dominios especializados) | Medical NER studies |

**Evidencia empírica reciente:**

| Paper | Modelo | Tarea | F1 | Venue |
|-------|--------|-------|-----|-------|
| B2NER | LoRA adapters ≤50MB | NER universal (15 datasets, 6 idiomas) | +6.8-12.0 F1 vs GPT-4 | COLING 2025 |
| LLaMA-3-8B Financial NER | LoRA r=128 | NER financiero | 0.894 micro-F1 | ArXiv Jan 2026 |
| Military IE | GRPO + LoRA | Information Extraction | +48.8% F1 absoluto | 2025 |

**Decisión LoRA vs QLoRA:**
- **LoRA**: Velocidad ligeramente mayor, ~0.5% más preciso, 4× más VRAM
- **QLoRA**: Usar cuando VRAM < 8GB o modelo > 1B parámetros
- **Para Legal-XLM-RoBERTa-base (184M)**: LoRA es viable en RTX 5060 Ti 16GB

#### 3.1.2 RandLoRA: PEFT de Rango Completo

**Paper:** "RandLoRA: Full-Rank Parameter-Efficient Fine-Tuning of Large Models"
**Venue:** ICLR 2025 (ArXiv: 2502.00987)

**Problema que resuelve:**
LoRA estándar produce actualizaciones de bajo rango, lo que limita la capacidad de representación. Aumentar el rango (r) no cierra la brecha con full fine-tuning: existe un *plateau* de rendimiento.

**Innovación:**
- Genera matrices aleatorias de bajo rango **no entrenables** (bases linealmente independientes)
- Aprende solo **coeficientes diagonales** de escalado
- La combinación lineal produce actualizaciones de **rango completo**
- Misma cantidad de parámetros entrenables que LoRA, pero sin restricción de rango

**Resultados:**

| Modelo | Tarea | LoRA | RandLoRA | Full FT |
|--------|-------|------|----------|---------|
| DinoV2 | Visión | 85.2 | 87.1 | 87.4 |
| CLIP | Visión-lenguaje | 78.6 | 81.3 | 82.0 |
| Llama3-8B | Razonamiento | 71.2 | 73.8 | 74.1 |

**Implicación:** RandLoRA cierra >90% de la brecha LoRA→Full FT con los mismos parámetros entrenables.

### 3.2 Knowledge Distillation (LLM → Modelo Pequeño)

#### 3.2.1 Destilación Multi-Perspectiva para NER

**Paper:** "Multi-Perspective Knowledge Distillation of LLM for NER"
**Fuente:** IGI Global Scientific Publishing, 2025

**Pipeline:**
1. **Teacher:** Qwen14B (14B parámetros)
2. **Generación:** Chain-of-Thought (CoT) para generar razonamiento intermedio sobre entidades
3. **Alineación:** Conocimiento multi-perspectiva (tipo de entidad, contexto, límites)
4. **Student:** Modelo NER pequeño con DoRA (variante de LoRA)

**Resultados sobre estado del arte:**

| Métrica | Mejora |
|---------|--------|
| Precision | +3.46% |
| Recall | +5.79% |
| F1-score | +2.54% |

**Capacidad adicional:** Rendimiento fuerte en few-shot (datos limitados).

#### 3.2.2 Aplicación a ContextSafe

Pipeline propuesto:
```
GPT-4 / Llama-3-70B (teacher)
    ↓ Genera anotaciones PII con razonamiento CoT
    ↓ Sobre textos legales españoles no anotados
Legal-XLM-RoBERTa-base (student)
    ↓ Fine-tune con DoRA/LoRA
    ↓ Usando datos generados + gold labels
Modelo PII desplegable (~400MB ONNX)
```

### 3.3 Generación Sintética de Datos con LLMs

#### 3.3.1 Evaluación Rigurosa (EMNLP 2025)

**Paper:** "A Rigorous Evaluation of LLM Data Generation Strategies for NER"
**Venue:** EMNLP 2025 Main Conference (Paper ID: 2025.emnlp-main.418)

**Diseño experimental:**
- **Idiomas:** 11 (incluyendo multilingüe)
- **Tareas:** 3 diferentes
- **LLMs generadores:** 4 modelos
- **Modelos downstream:** 10 (fine-tuned XLM-R)
- **Métrica:** F1 promedio gold vs artificial

**Hallazgos clave:**

| Hallazgo | Evidencia |
|----------|-----------|
| Calidad > Cantidad | Datasets pequeños, limpios y consistentes superan a datasets grandes ruidosos |
| Formato importa | JSONL consistente es crítico para rendimiento |
| Efectivo para low-resource | Datos sintéticos viables para idiomas sin corpus anotado |
| Comparable a gold | En algunos idiomas/tareas, datos sintéticos alcanzan 90-95% del rendimiento gold |

#### 3.3.2 Cross-lingual NER Zero-shot (EMNLP 2025)

**Paper:** "Zero-shot Cross-lingual NER via Mitigating Language Difference: An Entity-aligned Translation Perspective"
**Venue:** EMNLP 2025

**Técnica:** Traducción alineada a entidades para transferencia cross-lingual. Relevante para expandir ContextSafe a nuevos idiomas partiendo del modelo español.

### 3.4 GLiNER: Zero-Shot NER para PII

**Paper:** "GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer"
**Venue:** NAACL 2024 (modelos PII actualizados septiembre 2025, colaboración Wordcab)

**Arquitectura:**
- Encoder bidireccional (BiLM)
- Input: prompts de tipo de entidad + texto
- Output: extracción paralela de entidades (ventaja sobre generación secuencial de LLMs)
- No requiere categorías predefinidas: entidades especificadas en runtime

**Modelos PII disponibles (2025):**

| Modelo | Tamaño | F1 |
|--------|--------|-----|
| gliner-pii-edge-v1.0 | ~100MB | ~75% |
| gliner-pii-small-v1.0 | ~200MB | ~78% |
| gliner-pii-base-v1.0 | ~440MB | **80.99%** |
| gliner-pii-large-v1.0 | ~1.3GB | ~80% |

**Integración existente:** GLiNER se integra con Microsoft Presidio (que ContextSafe ya usa).

**Relevancia:**
- **Baseline inmediato:** 81% F1 sin entrenamiento, contra el cual medir nuestro modelo fine-tuned
- **Ensemble:** Usar GLiNER para categorías PII raras donde no hay datos de entrenamiento
- **Validación cruzada:** Comparar predicciones GLiNER vs Legal-XLM-R para detectar errores

### 3.5 Enfoques Híbridos (Transformer + Reglas)

#### 3.5.1 Hybrid NER para PII en Documentos Financieros

**Paper:** "A hybrid rule-based NLP and machine learning approach for PII detection and anonymization in financial documents"
**Venue:** Nature Scientific Reports, 2025 (DOI: 10.1038/s41598-025-04971-9)

**Resultados:**

| Métrica | Dataset Sintético | Documentos Reales |
|---------|-------------------|-------------------|
| Precision | **94.7%** | ~93% |
| Recall | 89.4% | ~93% |
| F1-score | 91.1% | ~93% |

**Arquitectura:** Reglas NLP + ML + NER custom, escalable.

#### 3.5.2 RECAP: Regex + LLM Contextual

**Paper:** Presentado en NeurIPS 2025
**Metodología:** Regex determinista + LLMs context-aware para PII multilingüe

**Resultados comparativos:**

| Comparación | Mejora RECAP |
|-------------|-------------|
| vs NER fine-tuned | **+82% weighted F1** |
| vs zero-shot LLMs | **+17% weighted F1** |

**Benchmark:** nervaluate (evaluación a nivel de entidad)

**Implicación para ContextSafe:** Nuestro pipeline actual (Regex + Presidio + RoBERTa) ya sigue este patrón híbrido. RECAP valida que esta arquitectura es la más efectiva según la evidencia 2025.

### 3.6 Domain Adaptive Pre-Training (DAPT): Revisión Crítica

#### 3.6.1 DAPT No Es Universal

**Paper:** "Continual Pre-Training is (not) What You Need in Domain Adaptation"
**Venue:** ICLR 2025

**Conclusiones clave:**

| Escenario | DAPT Ayuda? | Evidencia |
|-----------|-------------|-----------|
| Vocabulario especializado (legal, médico) | **Sí** | Familiariza con estilo legal |
| Razonamiento lógico (derecho civil) | **Sí** | Mejora comprensión de relaciones |
| Tareas con datos abundantes | **No necesariamente** | Fine-tuning directo puede ser suficiente |
| Sin mitigación de catástrofe | **Perjudicial** | Catastrophic forgetting degrada general |

**Mitigación recomendada:**
- Capas adapter / LoRA durante DAPT (no full fine-tuning del backbone)
- Unfreezing gradual (descongelar capas progresivamente)
- Evaluar ANTES y DESPUÉS de DAPT en benchmark NER-PII

#### 3.6.2 ICL-APT: Alternativa Eficiente

**Concepto:** In-Context Learning Augmented Pre-Training

**Pipeline:**
1. Muestrear textos del corpus objetivo
2. Recuperar documentos similares del dominio (semantic retrieval)
3. Aumentar contexto con definiciones, abreviaciones, terminología
4. Continuar pre-training con MLM sobre contexto aumentado

**Ventaja:** Más eficiente con corpus limitado. No requiere millones de documentos como DAPT tradicional.

**Aplicación:** Para cada documento legal español, recuperar sentencias similares + añadir definiciones de categorías PII como contexto de pre-training.

### 3.7 Modelos Españoles Legales (Baselines 2025)

#### 3.7.1 MEL (Modelo de Español Legal)

**Paper:** "MEL: Legal Spanish language model"
**Fecha:** Enero 2025 (ArXiv: 2501.16011)

| Aspecto | Detalle |
|---------|---------|
| Base | XLM-RoBERTa-large |
| Datos entrenamiento | BOE (Boletín Oficial del Estado), textos congreso |
| Tareas | Clasificación legal, NER |
| F1 macro | ~0.82 (15 labels) |
| Comparación | Supera xlm-roberta-large, legal-xlm-roberta-large, RoBERTalex |

#### 3.7.2 3CEL Corpus

**Paper:** "3CEL: a Corpus of Legal Spanish Contract Clauses"
**Fecha:** Enero 2025 (ArXiv: 2501.15990)

Corpus de cláusulas contractuales españolas con anotaciones. Potencialmente útil como datos de entrenamiento o evaluación.

---

## 4. Lecturas Previas Obligatorias

> **IMPORTANTE:** Antes de ejecutar cualquier fase del plan, el modelo debe leer estos documentos en el orden indicado para comprender el contexto completo del proyecto, las decisiones tomadas y el estado actual.

### 4.1 Nivel 0: Identidad y Reglas del Proyecto

| # | Archivo | Propósito | Obligatorio |
|---|---------|-----------|-------------|
| 0.1 | `ml/README.md` | Reglas operativas, estructura de archivos, flujo de trabajo | **Sí** |
| 0.2 | `README.md` (raíz proyecto) | Arquitectura hexagonal, dominio ContextSafe, pipeline NER, niveles de anonimización | **Sí** |

### 4.2 Nivel 1: Historia del Ciclo ML (leer en orden cronológico)

Estos documentos narran la evolución completa del modelo NER v2, desde baseline hasta el estado actual. Sin ellos no se entiende por qué se tomaron ciertas decisiones.

| # | Archivo | Contenido Clave |
|---|---------|-----------------|
| 1.1 | `docs/reports/2026-01-15_estado_proyecto_ner.md` | Estado inicial del proyecto NER, modelo v1 vs v2 |
| 1.2 | `docs/reports/2026-01-16_investigacion_pipeline_pii.md` | Investigación pipelines PII existentes |
| 1.3 | `docs/reports/2026-01-28_investigacion_hybrid_ner.md` | Decisión arquitectónica: pipeline híbrido (Regex+ML) |
| 1.4 | `docs/reports/2026-01-28_investigacion_estandares_evaluacion_ner.md` | Adopción de SemEval 2013 Task 9 (COR/INC/PAR/MIS/SPU) |
| 1.5 | `docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | **ESENCIAL** - Ciclo ML completo: 5 elementos integrados, métricas finales (F1 0.788), lecciones aprendidas |

### 4.3 Nivel 2: Los 5 Elementos del Pipeline (detalle técnico)

Cada elemento documenta una mejora concreta integrada en `ner_predictor.py`. Leer si se necesita entender o modificar el pipeline.

| # | Archivo | Elemento | Impacto |
|---|---------|----------|---------|
| 2.1 | `docs/reports/2026-02-04_text_normalizer_impacto.md` | Elem.1: Normalización de texto | OCR noise → texto limpio |
| 2.2 | `docs/reports/2026-02-04_checksum_validators_standalone.md` | Elem.2: Validación checksums | DNI, IBAN, NSS con verificación matemática |
| 2.3 | `docs/reports/2026-02-05_regex_patterns_standalone.md` | Elem.3: Patrones regex españoles | Matrículas, CP, teléfonos |
| 2.4 | `docs/reports/2026-02-05_date_patterns_integration.md` | Elem.4: Fechas textuales | "12 de enero de 2024" |
| 2.5 | `docs/reports/2026-02-06_boundary_refinement_integration.md` | Elem.5: Refinamiento de límites | PAR→COR (16 parciales corregidos) |

### 4.4 Nivel 3: Investigaciones para Siguiente Fase

Estos reportes fundamentan las decisiones del plan de fine-tuning de Legal-XLM-RoBERTa.

| # | Archivo | Contenido Clave |
|---|---------|-----------------|
| 3.1 | `docs/reports/2026-01-29_investigacion_modelos_legales_multilingues.md` | Survey de modelos legales: Legal-BERT, JuriBERT, Legal-XLM-R. Justificación de Legal-XLM-RoBERTa-base |
| 3.2 | `docs/reports/2026-01-30_investigacion_finetuning_legal_xlm_r.md` | Estrategias DAPT, mDAPT, span masking, hiperparámetros. Plan original de fine-tuning |
| 3.3 | **Este documento** (`2026-01-31_mejores_practicas_ml_2026.md`) | Actualización 2025-2026: LoRA, RandLoRA, datos sintéticos, GLiNER, DAPT selectivo. **Plan actualizado** |

### 4.5 Nivel 4: Diseños Pendientes de Implementación

| # | Archivo | Contenido Clave |
|---|---------|-----------------|
| 4.1 | `docs/plans/2026-02-04_uncertainty_queue_design.md` | Diseño Human-in-the-Loop: zonas de confianza (HIGH/UNCERTAIN/LOW), cola de revisión, bloqueo de exportación. **No implementar en ML**, transferido a proyecto principal |

### 4.6 Nivel 5: Código Actual (estado del pipeline)

| # | Archivo | Propósito |
|---|---------|-----------|
| 5.1 | `scripts/inference/ner_predictor.py` | **Pipeline NER completo** - Integra los 5 elementos, predictor principal |
| 5.2 | `scripts/inference/text_normalizer.py` | Normalización de texto (Elem.1) |
| 5.3 | `scripts/inference/entity_validator.py` | Validación de checksums (Elem.2) |
| 5.4 | `scripts/preprocess/boundary_refinement.py` | Refinamiento de límites (Elem.5) |
| 5.5 | `scripts/preprocess/checksum_validators.py` | Validators: DNI, IBAN, NSS, tarjetas |
| 5.6 | `scripts/evaluate/test_ner_predictor_adversarial_v2.py` | Test set adversarial (35 casos, evaluación SemEval) |
| 5.7 | `scripts/download_legal_xlm_roberta.py` | Script de descarga del modelo base |

### 4.7 Nivel 6: Modelos Disponibles

| # | Ruta | Estado |
|---|------|--------|
| 6.1 | `models/checkpoints/roberta-base-bne-capitel-ner/` | Modelo actual (RoBERTa-BNE CAPITEL NER) |
| 6.2 | `models/legal_ner_v1/` | Modelo v1 (deprecado) |
| 6.3 | `models/legal_ner_v2/` | Modelo v2 actual (F1 0.788 con pipeline completo) |
| 6.4 | `models/pretrained/legal-xlm-roberta-base/` | **Legal-XLM-RoBERTa-base descargado** (184M params, 128K vocab, 1.48GB) |

### 4.8 Orden de Lectura Recomendado por Tarea

| Si el modelo va a... | Leer niveles |
|----------------------|-------------|
| Continuar el plan de fine-tuning | 0 → 1.5 → 3.1 → 3.2 → 3.3 (este doc) |
| Modificar el pipeline NER | 0 → 1.5 → 2.x (el elemento relevante) → 5.1 |
| Evaluar baselines (GLiNER, MEL) | 0 → 1.5 → 3.3 (sección 4.2 Fase 1) → 5.6 |
| Generar datos sintéticos | 0 → 1.5 → 3.3 (sección 3.3) |
| Implementar DAPT | 0 → 3.1 → 3.2 → 3.3 (secciones 3.6 + 4.2 Fase 4) |
| Implementar Uncertainty Queue | 0 → 4.1 (transferir al proyecto principal) |

### 4.9 Estado Actual del Proyecto (Snapshot Feb-04 2026)

```
Modelo actual:    legal_ner_v2 (RoBERTa-BNE + 5 elementos pipeline)
F1 strict:        0.788 (SemEval entity-level, test adversarial 35 casos)
Pass rate:        60.0% (lenient 71.4%)
Modelo descargado: Legal-XLM-RoBERTa-base (184M params, listo para fine-tuning)
Próximo paso:     Establecer baselines (GLiNER + MEL) → LoRA fine-tuning
```

---

## 5. Análisis de Gaps y Recomendaciones

### 5.1 Lo Que Nos Falta (Gap Analysis)

| # | Gap Identificado | Prioridad | Técnica Recomendada | Fuente |
|---|-------------------|-----------|---------------------|--------|
| **G1** | No hay baseline zero-shot | **Crítico** | Evaluar GLiNER-PII-base en nuestro test set | NAACL 2024 |
| **G2** | Fine-tuning planificado como Full FT | **Alto** | Migrar a LoRA r=128, α=256, todas las capas | COLING 2025, ICLR 2025 |
| **G3** | Solo gold labels para entrenamiento | **Alto** | Generar datos sintéticos con LLM (EMNLP 2025) | EMNLP 2025 |
| **G4** | No hay baseline MEL | **Alto** | Evaluar MEL en nuestro test set | ArXiv Jan 2025 |
| **G5** | DAPT planificado sin evaluación previa | **Medio** | Evaluar NER antes/después de DAPT, usar LoRA | ICLR 2025 |
| **G6** | No se usa RandLoRA | **Medio** | Si LoRA plateau, migrar a RandLoRA | ICLR 2025 |
| **G7** | Sin destilación de conocimiento | **Medio** | Pipeline teacher(LLM)→student(XLM-R) con CoT | IGI Global 2025 |
| **G8** | Pipeline híbrido sin validación formal | **Bajo** | Benchmark RECAP para validar arquitectura | NeurIPS 2025 |

### 5.2 Recomendaciones Ordenadas

#### Fase 1: Establecer Baselines (Inmediato)

1. **Evaluar GLiNER-PII-base** en nuestro test set adversarial
   - F1 esperado: ~81% (benchmark publicado)
   - Si supera nuestro modelo actual (F1 0.788): priorizar integración
   - Si no: confirma que nuestro pipeline es competitivo

2. **Evaluar MEL** (si disponible) en nuestro test set
   - F1 esperado: ~82% (benchmark publicado con 15 labels)
   - Establece benchmark español legal

#### Fase 2: Fine-tuning con PEFT (Siguiente Ciclo)

3. **Migrar de Full FT a LoRA**
   - Config: r=128, α=256, target=all_layers, lr=2e-4, epochs=3, dropout=0.05
   - Hardware: RTX 5060 Ti 16GB VRAM es suficiente
   - Adapter size: ~50MB (vs ~700MB full model)

4. **Si plateau con LoRA → RandLoRA**
   - Mismos parámetros entrenables, rango completo
   - Cierra >90% de la brecha LoRA→Full FT

#### Fase 3: Augmentación de Datos (Paralelo a Fase 2)

5. **Generar datos sintéticos PII con LLM**
   - Teacher: GPT-4 o Llama-3-70B
   - Formato: CoNLL/JSONL consistente
   - Foco: categorías con pocos ejemplos (IBAN, NSS, MATRICULA)
   - Validar: comparar F1 con gold vs gold+sintético

6. **Knowledge distillation (opcional)**
   - Solo si datos limitados persisten tras augmentación
   - Pipeline: LLM genera razonamiento CoT → student aprende

#### Fase 4: DAPT Selectivo (Después de Fase 2-3)

7. **Evaluar NER ANTES de DAPT** (baseline)
8. **DAPT con LoRA** (no full backbone FT) sobre corpus BOE
9. **Evaluar NER DESPUÉS de DAPT** (comparar)
10. **Decisión basada en evidencia:** si DAPT no mejora >2% F1, descartar

---

## 6. Comparación: Plan Original vs. Plan Actualizado

| Aspecto | Plan Original (Feb 2026) | Plan Actualizado (Post-Revisión) |
|---------|--------------------------|----------------------------------|
| Fine-tuning | Full FT | **LoRA r=128 / RandLoRA** |
| Datos | Solo gold labels manuales | **Gold + sintéticos LLM** |
| DAPT | Universal, 1-2 epochs | **Selectivo, evaluar antes/después** |
| Baseline | Ninguno | **GLiNER 81% + MEL 82%** |
| Destilación | No considerada | **Opcional (si datos limitados)** |
| Evaluación | SemEval entity-level | **+ adversarial + cross-lingual** |
| Tamaño adapter | ~700MB (modelo completo) | **~50MB (LoRA adapter)** |
| VRAM requerida | ~8GB (Full FT batch pequeño) | **~4GB (LoRA)** |

---

## 7. Tabla de Evidencia

| Paper | Venue | Año | Técnica | Métrica Clave | URL |
|-------|-------|-----|---------|---------------|-----|
| B2NER | COLING | 2025 | LoRA NER universal | +6.8-12.0 F1 vs GPT-4 | github.com/UmeanNever/B2NER |
| RandLoRA | ICLR | 2025 | Full-rank PEFT | >90% gap LoRA→FT cerrado | arxiv.org/abs/2502.00987 |
| Multi-Perspective KD | IGI Global | 2025 | Distillation NER | +2.54% F1, +5.79% Recall | igi-global.com/gateway/article/372672 |
| LLM Data Gen for NER | EMNLP | 2025 | Datos sintéticos | 90-95% rendimiento gold | aclanthology.org/2025.emnlp-main.418 |
| GLiNER PII | NAACL+updates | 2024-2025 | Zero-shot PII | 80.99% F1 | huggingface.co/knowledgator/gliner-pii-base-v1.0 |
| Hybrid PII Financial | Nature Sci.Rep | 2025 | Rules+ML PII | 94.7% precisión | doi.org/10.1038/s41598-025-04971-9 |
| RECAP | NeurIPS | 2025 | Regex+LLM PII | +82% vs NER fine-tuned | neurips.cc/virtual/2025/122402 |
| CPT is (not) WYNG | ICLR | 2025 | DAPT selectivo | No mejora uniformemente | openreview.net/pdf?id=rpi9ARgvXc |
| MEL | ArXiv | 2025 | Español legal | 82% F1 macro (15 labels) | arxiv.org/html/2501.16011 |
| 3CEL | ArXiv | 2025 | Corpus español legal | Benchmark cláusulas | arxiv.org/html/2501.15990 |
| Financial NER LLaMA-3 | ArXiv | 2026 | LoRA NER financiero | 0.894 micro-F1 | arxiv.org/abs/2601.10043 |

---

## 8. Conclusiones

### 8.1 Cambios de Paradigma 2025-2026

1. **PEFT reemplaza Full Fine-Tuning:** LoRA/RandLoRA es ahora el estándar para modelos ≤1B parámetros. Full FT solo se justifica si LoRA no converge (raro en modelos base).

2. **Datos sintéticos LLM son viables:** EMNLP 2025 demuestra que datos generados por LLM pueden alcanzar 90-95% del rendimiento de datos gold para NER multilingüe. Esto resuelve el cuello de botella de anotación manual.

3. **DAPT no es dogma:** ICLR 2025 demuestra que DAPT puede no mejorar e incluso perjudicar si no se mitiga catastrophic forgetting. Evaluar siempre antes y después.

4. **Hybrid > Pure ML:** Nature y NeurIPS 2025 confirman que enfoques híbridos (reglas + ML) superan a ML puro para PII. ContextSafe ya sigue esta arquitectura.

5. **Zero-shot NER es competitivo:** GLiNER alcanza 81% F1 sin entrenamiento. Cualquier modelo fine-tuned debe superar significativamente este umbral para justificar el esfuerzo.

### 8.2 Impacto en ContextSafe

El pipeline actual de ContextSafe (Regex + Presidio + RoBERTa) está **arquitectónicamente alineado** con la evidencia 2025-2026. Los gaps principales son operacionales:

- **No usar Full FT** → LoRA/RandLoRA
- **No depender solo de gold labels** → datos sintéticos LLM
- **Establecer baselines** → GLiNER + MEL antes de fine-tuning
- **DAPT selectivo** → evaluar, no asumir

### 8.3 Trabajo Futuro

| Tarea | Prioridad | Dependencia |
|-------|-----------|-------------|
| Evaluar GLiNER-PII en test set ContextSafe | Crítica | Ninguna |
| Preparar script LoRA fine-tuning (r=128, α=256) | Alta | Modelo descargado (completado) |
| Generar datos sintéticos PII con LLM | Alta | Definir categorías objetivo |
| Evaluar MEL en test set ContextSafe | Alta | Descargar modelo MEL |
| DAPT selectivo con evaluación pre/post | Media | Corpus BOE disponible |
| Implementar RandLoRA si plateau | Media | Resultados LoRA |
| Pipeline knowledge distillation | Baja | Solo si datos insuficientes |

---

## 9. Referencias

1. UmeanNever et al. "B2NER: Beyond Boundaries: Learning Universal Entity Taxonomy across Datasets and Languages for Open Named Entity Recognition." COLING 2025. GitHub: github.com/UmeanNever/B2NER

2. Koo et al. "RandLoRA: Full-Rank Parameter-Efficient Fine-Tuning of Large Models." ICLR 2025. ArXiv: 2502.00987

3. "Multi-Perspective Knowledge Distillation of LLM for Named Entity Recognition." IGI Global Scientific Publishing, 2025. igi-global.com/gateway/article/372672

4. "A Rigorous Evaluation of LLM Data Generation Strategies for NER." EMNLP 2025 Main Conference. Paper ID: 2025.emnlp-main.418

5. Urchade Zaratiana et al. "GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer." NAACL 2024. Modelos PII: knowledgator/gliner-pii-base-v1.0 (actualizado Sep 2025).

6. "A hybrid rule-based NLP and machine learning approach for PII detection and anonymization in financial documents." Nature Scientific Reports, 2025. DOI: 10.1038/s41598-025-04971-9

7. "RECAP: Deterministic Regex + Context-Aware LLMs for Multilingual PII Detection." NeurIPS 2025. neurips.cc/virtual/2025/122402

8. "Continual Pre-Training is (not) What You Need in Domain Adaptation." ICLR 2025. openreview.net/pdf?id=rpi9ARgvXc

9. "MEL: Legal Spanish language model." ArXiv, Enero 2025. arxiv.org/html/2501.16011

10. "3CEL: a Corpus of Legal Spanish Contract Clauses." ArXiv, Enero 2025. arxiv.org/html/2501.15990

11. "Instruction Finetuning LLaMA-3-8B Model Using LoRA for Financial Named Entity Recognition." ArXiv, Enero 2026. arxiv.org/abs/2601.10043

12. Unsloth Documentation. "LoRA Fine-tuning Hyperparameters Guide." unsloth.ai/docs (2025).

13. Gretel.ai. "GLiNER Models for PII Detection." gretel.ai/blog (2025).

14. Microsoft Presidio. "Using GLiNER with Presidio." microsoft.github.io/presidio (2025).

---

**Generado por:** AlexAlves87
**Fecha:** 2026-01-31
**Revisión:** 1.1 (añadida sección 4: Lecturas Previas Obligatorias)
**Próximo paso:** Establecer baselines (GLiNER + MEL) antes de iniciar fine-tuning
