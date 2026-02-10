# Evaluación Crítica: Propuesta de Embeddings (RAG-NER) para ContextSafe

**Fecha:** 2026-02-07
**Objetivo:** Evaluar la validez técnica y la necesidad del Módulo A de la propuesta
"Mejoras Arquitectónicas v2.1" — uso de `intfloat/multilingual-e5-small` para
pre-clasificación de documentos y configuración dinámica del NER.

---

## 1. Resumen Ejecutivo

La propuesta sugiere usar embeddings (`intfloat/multilingual-e5-small`, ~120MB) como
"Elemento 0" del pipeline NER para clasificar tipos de documento y ajustar dinámicamente
los umbrales de detección. Tras investigar la literatura académica, verificar las
especificaciones del modelo y contrastar con el estado actual del pipeline de ContextSafe,
**la conclusión es que la idea base tiene mérito parcial, pero la implementación propuesta
es sobre-ingeniería y el término "RAG-NER" es técnicamente incorrecto**.

### Veredicto

| Aspecto | Evaluación |
|---------|-----------|
| Concepto (NER consciente del tipo de documento) | Válido y útil |
| Término "RAG-NER" | Incorrecto: no es RAG |
| Modelo propuesto (`multilingual-e5-small`) | Sobredimensionado para la tarea |
| Necesidad real en ContextSafe | Media: alternativas más simples disponibles |
| Prioridad vs. otras mejoras | Baja frente a mejoras HITL y auditoría |

---

## 2. Análisis del Término "RAG-NER"

### Qué es RAG en la literatura

RAG (Retrieval-Augmented Generation) fue introducido por Lewis et al. (NeurIPS 2020)
y se refiere específicamente a la **recuperación de documentos/pasajes de una base de
conocimiento para aumentar la generación** de un modelo de lenguaje.

Los papers reales de RAG+NER (2024-2025) son:

| Paper | Venue | Qué hace realmente |
|-------|-------|--------------------|
| **RA-NER** (Dai et al.) | ICLR 2024 Tiny Papers | Recupera entidades similares de una KB externa para ayudar al NER |
| **RENER** (Shiraishi et al.) | arXiv 2410.13118 | Recupera ejemplos anotados similares como in-context learning para NER |
| **RA-IT Open NER** | arXiv 2406.17305 | Instruction tuning con ejemplos recuperados para NER abierto |
| **IF-WRANER** | arXiv 2411.00451 | Retrieval word-level para few-shot cross-domain NER |
| **RAG-BioNER** | arXiv 2508.06504 | Prompting dinámico con RAG para NER biomédico |

### Qué propone el documento v2.1

Lo que se describe NO es RAG. Es **clasificación de tipo de documento + configuración
condicional del NER**. No hay recuperación de documentos/ejemplos de una base de
conocimiento. No hay augmentación de generación. Es un clasificador seguido de un switch.

**Diagrama real de la propuesta:**
```
Documento → Embedding (e5-small) → Cosine Similarity → Tipo detectado → Switch de config → NER
```

**Diagrama real de RAG-NER (RA-NER, Amazon):**
```
Texto de entrada → Recuperar entidades similares de KB → Inyectar como contexto al NER → Predicción
```

Son arquitecturas fundamentalmente diferentes. Etiquetar la propuesta como "RAG-NER"
es incorrecto y podría inducir a error en documentación técnica o publicaciones.

---

## 3. Verificación del Modelo Propuesto

### Especificaciones reales de `intfloat/multilingual-e5-small`

| Especificación | Claim v2.1 | Valor real | Fuente |
|----------------|-----------|------------|--------|
| Peso | ~120 MB | **448 MB (FP32), 112 MB (INT8 ONNX)** | HuggingFace |
| Parámetros | No indicado | 117.65M | HuggingFace |
| Dimensión embedding | No indicado | 384 | Paper arXiv:2402.05672 |
| Max tokens | 512 | 512 (correcto) | HuggingFace |
| Latencia | <200ms en CPU | Plausible para 512 tokens INT8 | - |
| Idiomas | No indicado | 94-100 idiomas | HuggingFace |
| Licencia | No indicado | MIT | HuggingFace |

**Problemas detectados:**
- El claim de "~120 MB" solo es cierto con quantización INT8 ONNX. El modelo FP32 pesa
  448 MB. El documento no aclara que requiere quantización.
- En memoria (runtime), el modelo FP32 consume ~500MB RAM. Con INT8, ~200MB.
- Sobre el hardware target de 16GB RAM (ya con RoBERTa + Presidio + spaCy cargados),
  el margen disponible es limitado.

### Benchmark de referencia

| Benchmark | Resultado | Contexto |
|-----------|-----------|----------|
| Mr. TyDi (retrieval MRR@10) | 64.4 avg | Bueno para retrieval multilingüe |
| MTEB Classification (Amazon) | 88.7% accuracy | Aceptable para clasificación |

El modelo es competente para tareas de embeddings. La pregunta es si se necesita un
modelo de 117M parámetros para clasificar ~5 tipos de documento legal.

---

## 4. Análisis de Necesidad: Estado Actual vs. Propuesta

### Pipeline actual de ContextSafe

El `CompositeNerAdapter` ya implementa mecanismos sofisticados de contextualización:

| Mecanismo existente | Descripción |
|---------------------|-------------|
| **Contextual Anchors** (Fase 1) | Fuerza categorías según contexto legal español |
| **Weighted Voting** (Fase 2) | Regex=5, RoBERTa=2, Presidio=1.5, spaCy=1 |
| **GDPR Risk Tiebreaker** (Fase 3) | Prioridad: PERSON_NAME=100 → POSTAL_CODE=20 |
| **30+ False Positive Patterns** | Bloquea referencias legales, DOI, ORCID, ISBN |
| **Spanish Stopwords Filter** | Evita detección de artículos/pronombres |
| **Generic Terms Whitelist** | Términos nunca anonimizados (Estado, RGPD, etc.) |
| **Matrioshka (nested entities)** | Manejo de entidades anidadas |

El pipeline actual NO tiene:
- Clasificación de tipo de documento
- Umbrales dinámicos per-categoría
- Umbrales dinámicos per-tipo-de-documento

### ¿Necesita ContextSafe clasificación de documento?

**Parcialmente sí**, pero no como se propone. Los beneficios reales serían:
- Ajustar umbral de IBAN en facturas (más estricto) vs. sentencias (más relajado)
- Activar/desactivar categorías según contexto (ej. fecha de nacimiento relevante
  en sentencias penales, no en facturas)
- Reducir falsos positivos de nombres propios en documentos con muchas razones sociales

### Alternativas más simples y eficaces

| Método | Tamaño | Latencia | Accuracy estimada | Complejidad |
|--------|--------|----------|-------------------|-------------|
| **Regex sobre cabeceras** | 0 KB (código) | <1ms | ~95%+ | Trivial |
| **TF-IDF + LogisticRegression** | ~50 KB | <5ms | ~97%+ | Baja |
| **e5-small (INT8 ONNX)** | 112 MB | ~200ms | ~99% | Alta |
| **e5-small (FP32)** | 448 MB | ~400ms | ~99% | Alta |

Para documentos legales españoles, las cabeceras son extremadamente distintivas:
- `"SENTENCIA"`, `"JUZGADO"`, `"TRIBUNAL"` → Sentencia
- `"ESCRITURA"`, `"NOTARIO"`, `"PROTOCOLO"` → Escritura Notarial
- `"FACTURA"`, `"BASE IMPONIBLE"`, `"IVA"` → Factura
- `"RECURSO"`, `"APELACIÓN"`, `"CASACIÓN"` → Recurso

Un clasificador basado en regex/keywords en los primeros 200 caracteres probablemente
alcance >95% de accuracy sin añadir dependencias ni latencia significativa.

---

## 5. Recomendación

### Lo que SÍ se recomienda implementar

1. **Clasificación de tipo de documento** — pero con regex/keywords, no embeddings
2. **Umbrales dinámicos per-categoría** — independiente de la clasificación
3. **Configuración condicional del NER** — activar/desactivar reglas según tipo

### Lo que NO se recomienda

1. **No usar embeddings** para clasificar ~5 tipos de documento legal
2. **No llamar a esto "RAG-NER"** — es clasificación + configuración condicional
3. **No añadir 112-448MB de modelo** cuando regex logra el mismo objetivo

### Implementación sugerida (alternativa)

```python
# Element 0: Document Type Classifier (lightweight)
class DocumentTypeClassifier:
    """Classify legal document type from header text."""

    PATTERNS = {
        DocumentType.SENTENCIA: [r"SENTENCIA", r"JUZGADO", r"TRIBUNAL", r"FALLO"],
        DocumentType.ESCRITURA: [r"ESCRITURA", r"NOTARI", r"PROTOCOLO"],
        DocumentType.FACTURA: [r"FACTURA", r"BASE IMPONIBLE", r"IVA"],
        DocumentType.RECURSO: [r"RECURSO", r"APELACI[OÓ]N", r"CASACI[OÓ]N"],
    }

    def classify(self, text: str, max_chars: int = 500) -> DocumentType:
        header = text[:max_chars].upper()
        scores = {}
        for doc_type, patterns in self.PATTERNS.items():
            scores[doc_type] = sum(1 for p in patterns if re.search(p, header))
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return DocumentType.GENERIC
```

**Coste:** 0 bytes de modelo, <1ms latencia, ~0 complejidad adicional.
**Extensible:** Si en el futuro se necesita mayor sofisticación, se puede escalar
a TF-IDF o embeddings. Pero empezar simple.

---

## 6. Sobre el "Elemento 0" en el pipeline

Si se decide implementar clasificación de documento (con el método simple recomendado),
la ubicación correcta sería:

```
Documento ingestado
    ↓
Element 0: classify_document_type(first_500_chars)  ← NUEVO
    ↓
CompositeNerAdapter.detect_entities(text, doc_type=tipo)
    ↓
[RoBERTa | Presidio | Regex | spaCy] con umbrales ajustados según doc_type
    ↓
Merge (voting ponderado actual, ya funciona bien)
```

Este paso es coherente con la arquitectura hexagonal actual y no requiere cambios
en los puertos ni adaptadores existentes.

---

## 7. Conclusión

La propuesta identifica una necesidad real (NER consciente del tipo de documento)
pero propone una solución sobre-ingeniería con terminología incorrecta. Un clasificador
basado en regex sobre las cabeceras del documento lograría el mismo objetivo sin añadir
120-448MB de modelo, 200ms de latencia adicional, ni complejidad de mantenimiento.

La inversión de esfuerzo se rentabiliza mucho más en el Módulo B (auditoría activa y
trazabilidad HITL), donde ContextSafe tiene gaps reales de cumplimiento normativo.

---

## 8. Literatura Consultada

| Referencia | Venue | Relevancia |
|-----------|-------|------------|
| Wang et al., "Multilingual E5 Text Embeddings" | arXiv:2402.05672 (2024) | Modelo propuesto |
| Dai et al., "RA-NER" | ICLR 2024 Tiny Papers | RAG real aplicado a NER |
| Shiraishi et al., "RENER" | arXiv:2410.13118 (2024) | Retrieval-enhanced NER |
| arXiv 2406.17305, "RA-IT Open NER" | arXiv (2024) | Instruction tuning + retrieval |
| arXiv 2411.00451, "IF-WRANER" | arXiv (2024) | Few-shot cross-domain NER + RAG |
| arXiv 2508.06504, "RAG-BioNER" | arXiv (2025) | Dynamic prompting + RAG |
| ACL 2020 LT4Gov, "Legal-ES" | ACL Anthology | Embeddings legales español |
| IEEE 2024, "Fine-grained NER Spanish legal" | IEEE Xplore | NER legal español |
| Frontiers AI 2025, "LegNER multilingual" | Frontiers | NER legal multilingüe |

## Documentos Relacionados

| Documento | Relación |
|-----------|----------|
| `ml/docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | Pipeline NER actual (5 elementos) |
| `ml/docs/reports/2026-02-06_adversarial_v2_academic_r7.md` | Evaluación adversarial del pipeline actual |
| `ml/docs/reports/2026-01-31_mejores_practicas_ml_2026.md` | Best practices ML |
| `src/contextsafe/infrastructure/nlp/composite_adapter.py` | Implementación actual del pipeline NER |
