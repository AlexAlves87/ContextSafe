# Embeddings para ContextSafe: Hoja de Ruta y Criterios de Activación

**Fecha:** 2026-02-07
**Objetivo:** Documentar el enfoque de embeddings evaluado, las alternativas implementadas,
y los criterios bajo los cuales sería justificable escalar a embeddings en el futuro.

---

## 1. Resumen Ejecutivo

Se evaluaron dos propuestas que involucran embeddings:

| Propuesta | Fuente | Modelo | Decisión |
|-----------|--------|--------|----------|
| Clasificación de documento con embeddings | Mejoras Arquitectónicas v2.1, Módulo A | `intfloat/multilingual-e5-small` | **Diferida** — Regex implementado |
| Gap Scanning con embeddings | Estrategia Safety Net A | `intfloat/multilingual-e5-small` | **Descartada** — Cosine similarity inadecuada |

**Estado actual:** Se implementó un clasificador basado en regex/keywords
(`DocumentTypeClassifier`) que cubre los requisitos inmediatos con 0 bytes de modelo,
<1ms de latencia y ~95% de accuracy estimada para documentos legales españoles.

Los embeddings quedan documentados como **opción de escalado futuro** cuando se cumplan
criterios específicos (Sección 5).

---

## 2. Propuesta Evaluada: Clasificación de Documento con Embeddings

### 2.1 Modelo Propuesto

| Especificación | Valor |
|----------------|-------|
| Modelo | `intfloat/multilingual-e5-small` (Wang et al., arXiv:2402.05672) |
| Parámetros | 117.65M |
| Tamaño FP32 | 448 MB |
| Tamaño INT8 ONNX | 112 MB |
| Dimensión embedding | 384 |
| Max tokens | 512 |
| Latencia estimada (CPU INT8) | ~200ms |
| Idiomas soportados | 94-100 |
| Licencia | MIT |
| RAM runtime (FP32) | ~500 MB |
| RAM runtime (INT8) | ~200 MB |

**Fuente de verificación:** HuggingFace model card `intfloat/multilingual-e5-small`.

### 2.2 Arquitectura Propuesta

```
Documento → Embedding (e5-small) → Cosine Similarity vs centroides → Tipo → Config NER
```

Esto NO es RAG-NER (el término usado en la propuesta v2.1 es incorrecto).
Es **clasificación de documento + configuración condicional**
(ver `ml/docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md`, Sección 2).

### 2.3 Por Qué Se Difirió

| Factor | Embeddings | Regex (implementado) |
|--------|-----------|---------------------|
| Tamaño | 112-448 MB | 0 bytes |
| Latencia | ~200ms | <1ms |
| Accuracy estimada | ~99% | ~95%+ |
| Complejidad | Alta (ONNX runtime, quantización) | Trivial |
| RAM adicional | 200-500 MB | 0 |
| Mantenimiento | Modelo versionado, updates | Patrones editables |

Para ~7 tipos de documento legal con cabeceras altamente distintivas, el regex es
suficiente. El 4% adicional de accuracy no justifica 200MB de modelo ni la complejidad
de mantenimiento.

---

## 3. Propuesta Evaluada: Gap Scanning con Embeddings

### 3.1 Concepto

Usar embeddings para detectar fragmentos "sospechosos" no identificados por el NER:

```
Texto completo → Segmentar en chunks → Embedding de cada chunk
    → Comparar vs "centroide de riesgo PII" → Alertar si similitud alta
```

### 3.2 Por Qué Se Descartó

1. **Similitud coseno no detecta PII**: La similitud semántica mide cercanía temática,
   no presencia de datos personales. "Juan García vive en Madrid" y "La empresa opera
   en Madrid" tienen alta similitud semántica pero solo uno contiene PII nominal.

2. **No existe un "centroide de riesgo PII"**: Los datos personales (nombres, DNIs, IBANs,
   direcciones) ocupan regiones semánticas completamente disjuntas. No hay un punto en
   el espacio de embeddings que represente "esto contiene PII"
   (ver Ethayarajh, EMNLP 2019, sobre anisotropía de embeddings).

3. **Paper de referencia**: Netflix/Cornell 2024 documenta limitaciones de cosine similarity
   para detección de características discretas vs continuas. PII es inherentemente
   discreto (presente o ausente).

4. **Alternativa implementada**: Los Sanity Checks deterministas (`ExportValidator`,
   `src/contextsafe/domain/document_processing/services/export_validator.py`) cubren
   el caso de falsos negativos por tipo de documento de forma más fiable y sin
   dependencias adicionales.

---

## 4. Alternativa Implementada: Clasificador Regex

### 4.1 Implementación

```
src/contextsafe/domain/document_processing/services/document_classifier.py
```

| Característica | Detalle |
|----------------|---------|
| Tipos soportados | SENTENCIA, ESCRITURA, FACTURA, RECURSO, DENUNCIA, CONTRATO, GENERIC |
| Método | Regex sobre primeros 500 caracteres (uppercased) |
| Patrones por tipo | 4-8 keywords distintivos |
| Fallback | Nombre de archivo si texto no clasifica |
| Confianza | Ratio de patrones encontrados / total por tipo |
| Latencia | <1ms |
| Dependencias | 0 (solo `re` de stdlib) |

### 4.2 Patrones Clave

| Tipo | Patrones principales |
|------|---------------------|
| SENTENCIA | `SENTENCIA`, `JUZGADO`, `TRIBUNAL`, `FALLO`, `MAGISTRAD[OA]` |
| ESCRITURA | `ESCRITURA`, `NOTAR[IÍ]`, `PROTOCOLO`, `OTORGAMIENTO` |
| FACTURA | `FACTURA`, `BASE IMPONIBLE`, `IVA`, `TOTAL FACTURA` |
| RECURSO | `RECURSO`, `APELACI[OÓ]N`, `CASACI[OÓ]N` |
| DENUNCIA | `DENUNCIA`, `ATESTADO`, `DILIGENCIAS PREVIAS` |
| CONTRATO | `CONTRATO`, `CL[AÁ]USULA`, `ESTIPULACIONES` |

### 4.3 Integración con Sanity Checks

El clasificador alimenta las reglas de validación de exportación:

```
Documento → DocumentTypeClassifier → tipo
                                       ↓
ExportValidator.validate(tipo, ...) → Aplica reglas SC-001..SC-004
```

| Regla | Tipo | Categorías mínimas | Severidad |
|-------|------|--------------------|-----------|
| SC-001 | ESCRITURA | PERSON_NAME ≥1, DNI_NIE ≥1 | CRITICAL |
| SC-002 | SENTENCIA | DATE ≥1 | WARNING |
| SC-003 | FACTURA | ORGANIZATION ≥1 | WARNING |
| SC-004 | DENUNCIA | PERSON_NAME ≥1 | WARNING |

---

## 5. Criterios de Activación para Escalar a Embeddings

Los embeddings deberían reconsiderarse SOLO si se cumplen **al menos 2** de estos criterios:

### 5.1 Criterios Funcionales

| # | Criterio | Umbral |
|---|----------|--------|
| CF-1 | Accuracy del regex cae por debajo del 90% | Medir con corpus de validación |
| CF-2 | Se añaden >15 tipos de documento | Regex se vuelve inmanejable |
| CF-3 | Documentos sin cabecera estandarizada | OCR degradado, escáneres variados |
| CF-4 | Requisito de clasificación multilingüe | Documentos en catalán, euskera, gallego |

### 5.2 Criterios de Infraestructura

| # | Criterio | Umbral |
|---|----------|--------|
| CI-1 | RAM disponible en producción | ≥32 GB (actualmente target es 16 GB) |
| CI-2 | Pipeline ya usa ONNX Runtime | Evita añadir nueva dependencia |
| CI-3 | Latencia actual del pipeline | <2s total (margen para +200ms) |

### 5.3 Ruta de Implementación (si se activa)

```
Paso 1: Recopilar corpus de validación (50+ docs por tipo)
Paso 2: Evaluar accuracy actual del regex con corpus
Paso 3: Si accuracy < 90%, evaluar TF-IDF + LogReg primero (~50KB, <5ms)
Paso 4: Solo si TF-IDF < 95%, escalar a e5-small INT8 ONNX
Paso 5: Generar centroides por tipo con corpus etiquetado
Paso 6: Validar con adversarial tests (documentos mixtos, OCR degradado)
```

### 5.4 Modelo Recomendado (si se escala)

| Opción | Tamaño | Latencia | Caso de uso |
|--------|--------|----------|-------------|
| TF-IDF + LogReg | ~50 KB | <5ms | Primera escalada |
| `intfloat/multilingual-e5-small` INT8 | 112 MB | ~200ms | Clasificación multilingüe |
| `BAAI/bge-small-en-v1.5` INT8 | 66 MB | ~150ms | Solo inglés/español |

**Nota:** `intfloat/multilingual-e5-small` sigue siendo la mejor opción para multilingüe
si se necesita. Pero TF-IDF es el paso intermedio correcto antes de embeddings neuronales.

---

## 6. Impacto en el Pipeline NER

### 6.1 Estado Actual (implementado)

```
Documento ingestado
    ↓
DocumentTypeClassifier.classify(primeros_500_chars)      ← REGEX
    ↓
ConfidenceZone.classify(score, category, checksum)        ← TRIAGE
    ↓
CompositeNerAdapter.detect_entities(text)                 ← NER
    ↓
ExportValidator.validate(tipo, entidades, revisiones)     ← SAFETY LATCH
    ↓
[Exportación permitida o bloqueada]
```

### 6.2 Estado Futuro (si embeddings se activan)

```
Documento ingestado
    ↓
DocumentTypeClassifier.classify(primeros_500_chars)       ← REGEX (fallback)
    ↓
EmbeddingClassifier.classify(primeros_512_tokens)         ← EMBEDDINGS
    ↓
merge_classifications(regex_result, embedding_result)     ← FUSIÓN
    ↓
CompositeNerAdapter.detect_entities(text, doc_type=tipo)  ← NER CONTEXTUAL
    ↓
ExportValidator.validate(tipo, entidades, revisiones)     ← SAFETY LATCH
```

La interfaz del clasificador (`DocumentClassification` dataclass) ya está diseñada para
ser reemplazable sin cambios en el resto del pipeline.

---

## 7. Conclusión

El enfoque actual (regex) es la decisión correcta para el estado presente del proyecto.
Los embeddings representan una mejora incremental que solo se justifica ante un crecimiento
significativo en tipos de documento o degradación medible de la accuracy.

La arquitectura hexagonal permite escalar sin refactoring: el `DocumentTypeClassifier`
puede ser reemplazado por un `EmbeddingClassifier` que implemente la misma interfaz
(`DocumentClassification`), sin impacto en el resto del pipeline.

---

## Documentos Relacionados

| Documento | Relación |
|-----------|----------|
| `ml/docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md` | Evaluación crítica de la propuesta RAG-NER |
| `ml/docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | Pipeline NER actual (5 elementos) |
| `ml/docs/reports/2026-02-06_adversarial_v2_academic_r7.md` | Evaluación adversarial del pipeline |
| `src/contextsafe/domain/document_processing/services/document_classifier.py` | Clasificador regex implementado |
| `src/contextsafe/domain/document_processing/services/export_validator.py` | Safety Latch + Sanity Checks |
| `src/contextsafe/domain/entity_detection/services/confidence_zone.py` | Triage por zonas de confianza |

## Referencias

| Referencia | Venue | Relevancia |
|-----------|-------|------------|
| Wang et al., "Multilingual E5 Text Embeddings" | arXiv:2402.05672 (2024) | Modelo evaluado |
| Ethayarajh, "How Contextual are Contextualized Word Representations?" | EMNLP 2019 | Anisotropía de embeddings |
| Netflix/Cornell, "Limitations of Cosine Similarity" | arXiv (2024) | Limitaciones para detección discreta |
| Lewis et al., "Retrieval-Augmented Generation" | NeurIPS 2020 | Definición correcta de RAG |
| Dai et al., "RA-NER" | ICLR 2024 Tiny Papers | RAG real aplicado a NER |
