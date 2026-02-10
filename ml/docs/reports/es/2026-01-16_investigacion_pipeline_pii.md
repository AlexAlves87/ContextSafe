# Investigación: Mejores Prácticas para Pipeline de Detección PII

**Fecha:** 2026-01-16
**Autor:** AlexAlves87
**Tipo:** Revisión de Literatura
**Estado:** Completado

---

## Resumen Ejecutivo

Esta investigación analiza el estado del arte en detección de PII (Personally Identifiable Information) con enfoque en documentos legales españoles. Se revisaron papers académicos recientes (2024-2025) y frameworks de producción para identificar mejores prácticas en preprocesamiento, arquitectura de pipeline y postprocesamiento.

**Hallazgo principal:** La arquitectura óptima es **híbrida** (Regex → NER → Validación), no NER puro con postproceso. Además, la inyección de ruido OCR (30%) durante el entrenamiento mejora significativamente la robustez.

---

## Metodología

### Fuentes Consultadas

| Fuente | Tipo | Año | Relevancia |
|--------|------|-----|------------|
| PMC12214779 | Paper académico | 2025 | Híbrido NLP-ML para PII financiero |
| arXiv 2401.10825v3 | Survey | 2024 | Estado del arte NER |
| Microsoft Presidio | Framework | 2024 | Best practices industria |
| Presidio Research | Toolbox | 2024 | Evaluación de reconocedores |

### Criterios de Búsqueda

- "NER preprocessing postprocessing best practices 2024"
- "Spanish legal documents PII detection"
- "Hybrid rule-based NLP machine learning PII"
- "Presidio pipeline architecture"

---

## Resultados

### 1. Arquitectura de Pipeline Óptima

#### 1.1 Orden de Procesamiento (Presidio)

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Texto     │ → │   Regex     │ → │   NLP NER   │ → │  Checksum   │ → │  Threshold  │
│   (OCR)     │    │  Matchers   │    │   Model     │    │ Validation  │    │   Filter    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

**Fuente:** Microsoft Presidio Documentation

**Justificación:**
> "Presidio initially uses its regex matcher to identify matching entities. Then Natural Language Processing based NER model is used to detect PII autonomously. When possible, a checksum is used to validate the identified PIIs."

#### 1.2 Componentes del Pipeline

| Componente | Función | Implementación |
|------------|---------|----------------|
| **Regex Matchers** | Detectar patrones estructurados (DNI, IBAN, teléfono) | Ejecutar ANTES del NER |
| **NLP NER** | Detectar entidades contextuales (nombres, direcciones) | Modelo transformer |
| **Checksum Validation** | Validar integridad de identificadores | DNI mod-23, IBAN mod-97 |
| **Context Enhancement** | Mejorar confianza con contexto léxico | LemmaContextAwareEnhancer |
| **Threshold Filter** | Filtrar por score de confianza | Configurable (ej: 0.7) |

### 2. Preprocesamiento

#### 2.1 Normalización de Texto

**Fuente:** PMC12214779 (Hybrid NLP-ML)

| Técnica | Descripción | Aplicabilidad |
|---------|-------------|---------------|
| Tokenización | División en unidades discretas | Universal |
| Marcado de posición | Character-level position marking | Para span recovery |
| Normalización Unicode | Fullwidth → ASCII, zero-width removal | Alta para OCR |
| Normalización abreviaturas | D.N.I. → DNI | Alta para español |

#### 2.2 Inyección de Ruido (CRÍTICO)

**Fuente:** PMC12214779

> "To better simulate real-world document anomalies, data preprocessing adds minor random noise like punctuation removal and text normalization."

**Implementación recomendada:**
```python
# 30% probabilidad de ruido por muestra
noise_probability = 0.30

# Tipos de ruido:
# - Eliminación aleatoria de puntuación
# - Sustitución de caracteres OCR (l↔I, 0↔O)
# - Colapso/expansión de espacios
# - Pérdida de acentos
```

**Impacto:** Mejora robustez ante documentos escaneados reales.

### 3. Arquitectura de Modelo

#### 3.1 Estado del Arte NER (2024)

**Fuente:** arXiv 2401.10825v3

| Arquitectura | Características | F1 Benchmark |
|--------------|-----------------|--------------|
| DeBERTa | Disentangled attention + enhanced mask decoder | SOTA |
| RoBERTa + CRF | Transformer + sequence coherence | +4-13% vs base |
| BERT + BiLSTM | Contextual + sequential modeling | Robusto |
| GLiNER | Global attention para entidades distantes | Innovador |

#### 3.2 CRF Layer

**Fuente:** arXiv Survey

> "Applying CRF provides a robust method for NER by ensuring coherent label sequences and modeling dependencies between adjacent labels."

**Beneficio:** Evita secuencias inválidas como `B-PERSON I-LOCATION`.

### 4. Postprocesamiento

#### 4.1 Validación de Checksums

**Fuente:** Presidio Best Practices

| Tipo | Algoritmo | Ejemplo |
|------|-----------|---------|
| DNI español | letra = "TRWAGMYFPDXBNJZSQVHLCKE"[num % 23] | 12345678Z |
| NIE español | Prefijo X=0, Y=1, Z=2 + DNI algorithm | X1234567L |
| IBAN | ISO 7064 Mod 97-10 | ES9121000418450200051332 |
| NSS español | Mod 97 sobre primeros 10 dígitos | 281234567890 |
| Tarjeta crédito | Algoritmo Luhn | 4111111111111111 |

#### 4.2 Context-Aware Enhancement

**Fuente:** Presidio LemmaContextAwareEnhancer

> "The ContextAwareEnhancer is a module that enhances the detection of entities by using the context of the text. It can improve detection of entities that are dependent on context."

**Implementación:**
- Buscar palabras clave en ventana de ±N tokens
- Aumentar/disminuir score según contexto
- Ejemplo: "DNI" cerca de número aumenta confianza de DNI_NIE

#### 4.3 Threshold Filtering

**Fuente:** Presidio Tuning Guide

> "Adjust confidence thresholds on ML recognizers to balance missed cases versus over-masking."

**Recomendación:**
- Threshold alto (0.8+): Menos falsos positivos, más falsos negativos
- Threshold bajo (0.5-0.6): Más cobertura, más ruido
- Piloto inicial para calibrar

### 5. Resultados de Referencia

#### 5.1 Hybrid NLP-ML (PMC12214779)

| Métrica | Valor |
|---------|-------|
| Precision | 94.7% |
| Recall | 89.4% |
| F1-score | 91.1% |
| Accuracy (real-world) | 93.0% |

**Factores de éxito:**
1. Datos de entrenamiento diversos (templates variados)
2. Framework ligero (spaCy vs transformers pesados)
3. Métricas balanceadas (precision ≈ recall)
4. Anonimización que preserva contexto

#### 5.2 Presidio Tuning

**Fuente:** Presidio Research Notebook 5

> "Notebook 5 in presidio-research shows how one can configure Presidio to detect PII much more accurately, and boost the F-score by ~30%."

---

## Análisis de Gaps

### Comparación: Implementación Actual vs Best Practices

| Aspecto | Best Practice | Implementación Actual | Gap |
|---------|---------------|----------------------|-----|
| Pipeline order | Regex → NER → Validation | NER → Postprocess | **CRÍTICO** |
| Noise injection | 30% en training | 0% | **CRÍTICO** |
| CRF layer | Añadir sobre transformer | No implementado | MEDIO |
| Confidence threshold | Filtrar por score | No implementado | MEDIO |
| Context enhancement | Lemma-based | Parcial (regex) | BAJO |
| Checksum validation | DNI, IBAN, NSS | Implementado | ✓ OK |
| Format validation | Regex patterns | Implementado | ✓ OK |

### Impacto Estimado de Correcciones

| Corrección | Esfuerzo | Impacto F1 Estimado |
|------------|----------|---------------------|
| Noise injection en dataset | Bajo | +10-15% en OCR |
| Pipeline Regex-first | Medio | +5-10% precision |
| CRF layer | Alto | +4-13% (literatura) |
| Confidence threshold | Bajo | Reduce FP 20-30% |

---

## Conclusiones

### Hallazgos Principales

1. **Arquitectura híbrida es superior**: Combinar regex (patrones estructurados) con NER (contextuales) supera a enfoques puros.

2. **El orden importa**: Regex ANTES de NER, no después. Presidio usa este orden por diseño.

3. **Ruido en training es crítico**: 30% de inyección de errores OCR mejora robustez significativamente.

4. **Checksum validation es estándar**: Validar identificadores estructurados (DNI, IBAN) es práctica universal.

5. **CRF mejora coherencia**: Añadir CRF layer sobre transformer previene secuencias inválidas.

### Recomendaciones

#### Prioridad ALTA (Implementar Inmediatamente)

1. **Inyectar ruido OCR en dataset v3**
   - 30% de muestras con errores simulados
   - Tipos: l↔I, 0↔O, espacios, acentos perdidos
   - Re-entrenar modelo

2. **Reestructurar pipeline**
   ```
   ANTES: Texto → NER → Postprocess
   DESPUÉS: Texto → Preprocess → Regex → NER → Validate → Filter
   ```

#### Prioridad MEDIA

3. **Añadir confidence threshold**
   - Filtrar entidades con score < 0.7
   - Calibrar con conjunto de validación

4. **Evaluar CRF layer**
   - Investigar `transformers` + `pytorch-crf`
   - Benchmark contra modelo actual

#### Prioridad BAJA

5. **Context enhancement avanzado**
   - Implementar LemmaContextAwareEnhancer
   - Gazetteers de contexto por tipo de entidad

---

## Referencias

1. **PMC12214779** - "A hybrid rule-based NLP and machine learning approach for PII detection and anonymization in financial documents"
   - URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC12214779/
   - Año: 2025

2. **arXiv 2401.10825v3** - "Recent Advances in Named Entity Recognition: A Comprehensive Survey and Comparative Study"
   - URL: https://arxiv.org/html/2401.10825v3
   - Año: 2024 (actualizado 2025)

3. **Microsoft Presidio** - Best Practices for Developing Recognizers
   - URL: https://microsoft.github.io/presidio/analyzer/developing_recognizers/
   - Año: 2024

4. **Presidio Research** - Evaluation Toolbox
   - URL: https://github.com/microsoft/presidio-research
   - Año: 2024

5. **Nature Scientific Reports** - "A hybrid rule-based NLP and machine learning approach"
   - URL: https://www.nature.com/articles/s41598-025-04971-9
   - Año: 2025

---

**Fecha:** 2026-01-16
**Versión:** 1.0
