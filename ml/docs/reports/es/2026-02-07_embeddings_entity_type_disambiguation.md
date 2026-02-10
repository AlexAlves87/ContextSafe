# Investigación: Embeddings para Desambiguación de Tipos de Entidad en NER

**Fecha:** 2026-02-07
**Objetivo:** Resolver errores de clasificación de tipo de entidad en el sistema NER de ContextSafe (ej: "Alejandro Alvarez" clasificado como ORGANIZATION en lugar de PERSON_NAME)

---

## 1. Resumen Ejecutivo

1. **Problema identificado**: El modelo NER actual confunde tipos de entidad, clasificando nombres de persona como organizaciones, fechas como organizaciones, y palabras comunes capitalizadas como PII.

2. **Solución propuesta**: Validador post-NER basado en embeddings que compara cada detección contra centroides semánticos por tipo de entidad.

3. **Modelo recomendado**: `intfloat/multilingual-e5-large` (1.1GB) con posible upgrade a `Legal-Embed` para dominio legal.

4. **Técnica principal**: Clasificación basada en centroides con umbral de reclasificación (threshold 0.75, margen 0.1).

5. **Reducción de errores esperada**: ~4.5% según literatura (WNUT17 benchmark).

---

## 2. Literatura Revisada

| Paper | Venue | Año | Hallazgo Relevante |
|-------|-------|-----|-------------------|
| NER Retriever: Zero-Shot Named Entity Retrieval with Type-Aware Embeddings | arXiv (2509.04011) | 2025 | Capas intermedias (layer 17) capturan mejor información de tipo que salidas finales. MLP con contrastive loss logra zero-shot a tipos no vistos. |
| CEPTNER: Contrastive Learning Enhanced Prototypical Network for Few-shot NER | Knowledge-Based Systems (ScienceDirect) | 2024 | Redes prototípicas con aprendizaje contrastivo separan efectivamente tipos de entidad con pocos ejemplos (50-100). |
| Recent Advances in Named Entity Recognition: A Comprehensive Survey | arXiv (2401.10825) | 2024 | Enfoques híbridos (reglas + ML + embeddings) superan consistentemente a modelos únicos. |
| Redundancy-Enhanced Framework for Error Correction in NER | OpenReview | 2025 | Post-procesador con Transformer refiner + entity-tag embeddings logra 4.48% reducción de errores en WNUT17. |
| Multilingual E5 Text Embeddings: A Technical Report | arXiv (2402.05672) | 2024 | Modelo multilingual-e5-large soporta 100 idiomas con excelente rendimiento en español. Requiere prefijo "query:" para embeddings de búsqueda. |

---

## 3. Best Practices Identificadas

1. **Incluir contexto**: Embeber la entidad CON su contexto circundante (10-15 palabras) mejora significativamente la desambiguación.

2. **Usar capas intermedias**: Las representaciones de capas medias (layer 15-17) contienen más información de tipo que las salidas finales.

3. **Contrastive learning**: Entrenar con pérdida contrastiva separa mejor los tipos en el espacio de embeddings.

4. **Umbral con margen**: No reclasificar solo por mayor similitud; requerir margen mínimo (>0.1) para evitar falsos positivos.

5. **Ejemplos por tipo**: 50-100 ejemplos confirmados por categoría son suficientes para construir centroides robustos.

6. **Dominio específico**: Modelos fine-tuned para el dominio (legal en nuestro caso) mejoran rendimiento.

7. **Flagging para HITL**: Cuando similitudes son cercanas (<0.05 diferencia), marcar para revisión humana en lugar de reclasificar automáticamente.

---

## 4. Recomendación para ContextSafe

### 4.1 Arquitectura Propuesta

```
┌─────────────────────────────────────────────────────────────────┐
│                    NER Pipeline Actual                          │
│  (RoBERTa + SpaCy + Regex → Intelligent Merge)                  │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Detecciones con tipo asignado
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              Entity Type Validator (NUEVO)                       │
│                                                                  │
│  1. Extraer entidad + contexto (±15 tokens)                     │
│  2. Generar embedding con multilingual-e5-large                 │
│  3. Calcular similitud coseno con centroides por tipo           │
│  4. Decisión:                                                   │
│     - Si mejor_tipo ≠ tipo_NER AND similitud > 0.75            │
│       AND margen > 0.1 → RECLASIFICAR                          │
│     - Si margen < 0.05 → MARCAR PARA HITL                      │
│     - Else → MANTENER tipo NER                                 │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Detecciones validadas/corregidas
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Glossary & Anonymization                         │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Modelo Seleccionado

**Principal**: `intfloat/multilingual-e5-large`
- Tamaño: 1.1GB
- Idiomas: 100 (excelente español)
- Latencia: ~50-100ms por embedding
- Requiere prefijo "query:" para embeddings

**Alternativa (evaluar)**: `Wasserstoff-AI/Legal-Embed-intfloat-multilingual-e5-large-instruct`
- Fine-tuned para dominio legal
- Mismo tamaño base
- Potencialmente mejor para documentos legales españoles

### 4.3 Construcción de Centroides

Categorías prioritarias (confusión frecuente):

| Categoría | Ejemplos Necesarios | Fuente |
|-----------|---------------------|--------|
| PERSON_NAME | 100 | Nombres de auditoria.md + gazetteers |
| ORGANIZATION | 100 | Empresas, instituciones de documentos legales |
| DATE | 50 | Fechas en formatos DD/MM/YYYY, DD-MM-YYYY |
| LOCATION | 50 | Ciudades, provincias españolas |

**Formato de ejemplo** (con contexto):
```
"query: El abogado Alejandro Alvarez compareció como testigo en el juicio"
"query: La empresa Telefónica S.A. interpuso recurso de casación"
"query: Con fecha 10/10/2025 se dictó sentencia"
```

### 4.4 Integración con Pipeline Existente

Ubicación propuesta: `src/contextsafe/infrastructure/nlp/validators/entity_type_validator.py`

```python
class EntityTypeValidator:
    """
    Post-processor that validates/corrects NER entity type assignments
    using embedding similarity to type centroids.

    Based on: NER Retriever (arXiv 2509.04011), CEPTNER (KBS 2024)
    """

    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-large",
        centroids_path: Path = None,
        reclassify_threshold: float = 0.75,
        margin_threshold: float = 0.10,
        hitl_margin: float = 0.05,
    ):
        ...

    def validate(
        self,
        entity_text: str,
        context: str,
        predicted_type: str,
    ) -> ValidationResult:
        """
        Returns ValidationResult with:
        - corrected_type: str
        - confidence: float
        - action: 'KEEP' | 'RECLASSIFY' | 'FLAG_HITL'
        """
        ...
```

### 4.5 Métricas de Éxito

| Métrica | Objetivo | Medición |
|---------|----------|----------|
| Reducción de errores de tipo | ≥4% | Comparar antes/después en set de validación |
| Latencia adicional | <100ms/entidad | Benchmark en CPU 16GB |
| Falsos positivos de reclasificación | <2% | Revisión manual de reclasificaciones |
| Cobertura HITL | <10% flagged | Porcentaje marcado para revisión humana |

---

## 5. Referencias

1. **NER Retriever**: Zhang et al. (2025). "NER Retriever: Zero-Shot Named Entity Retrieval with Type-Aware Embeddings." arXiv:2509.04011. https://arxiv.org/abs/2509.04011

2. **CEPTNER**: Wang et al. (2024). "CEPTNER: Contrastive learning Enhanced Prototypical network for Two-stage Few-shot Named Entity Recognition." Knowledge-Based Systems. https://doi.org/10.1016/j.knosys.2024.111512

3. **NER Survey**: Li et al. (2024). "Recent Advances in Named Entity Recognition: A Comprehensive Survey and Comparative Study." arXiv:2401.10825. https://arxiv.org/abs/2401.10825

4. **Error Correction Framework**: Chen et al. (2025). "A Redundancy-Enhanced Framework for Error Correction in Named Entity Recognition." OpenReview. https://openreview.net/forum?id=2jFWhxJE5pQ

5. **Multilingual E5**: Wang et al. (2024). "Multilingual E5 Text Embeddings: A Technical Report." arXiv:2402.05672. https://arxiv.org/abs/2402.05672

6. **Legal-Embed**: Wasserstoff-AI. (2024). "Legal-Embed-intfloat-multilingual-e5-large-instruct." HuggingFace. https://huggingface.co/Wasserstoff-AI/Legal-Embed-intfloat-multilingual-e5-large-instruct

---

## 6. Errores de Clasificación Identificados (Auditoría)

Análisis del archivo `auditoria.md` del documento STSJ ICAN 3407/2025:

| Entidad | Tipo Asignado | Tipo Correcto | Patrón |
|---------|---------------|---------------|--------|
| `"10/10/2025"` | ORGANIZATION (Org_038) | DATE | Fecha confundida con código |
| `"05-11-2024"` | ORGANIZATION | DATE | Fecha en formato DD-MM-YYYY |
| `"Pura"` | LOCATION (Lugar_001) | PERSON_NAME | Nombre corto sin honorífico |
| `"Finalmente"` | ORGANIZATION (Org_012) | NO ES PII | Adverbio capitalizado |
| `"Terminaba"` | ORGANIZATION (Org_017) | NO ES PII | Verbo capitalizado |
| `"Quien"` | ORGANIZATION | NO ES PII | Pronombre capitalizado |
| `"Whatsapp"` | PERSON | ORGANIZATION/PLATFORM | Nombre de plataforma |

**Patrón principal identificado**: El modelo RoBERTa clasifica como ORGANIZATION cualquier palabra capitalizada al inicio de frase que no reconoce claramente como otro tipo.

---

## Documentos Relacionados

| Documento | Relación |
|-----------|----------|
| `auditoria.md` | Fuente de errores de clasificación analizados |
| `docs/PLAN_CORRECCION_AUDITORIA.md` | Plan de corrección previo (7 issues identificados) |
| `ml/docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md` | Evaluación previa de embeddings (clasificación de documentos) |
| `ml/docs/reports/2026-02-07_embeddings_roadmap_document_classification.md` | Roadmap de embeddings para clasificación |
| `ml/README.md` | Instrucciones ML (formato de reportes) |

---

## Próximos Pasos

1. [ ] Descargar modelo `intfloat/multilingual-e5-large` (~1.1GB)
2. [ ] Construir dataset de ejemplos por tipo (PERSON_NAME, ORGANIZATION, DATE, LOCATION)
3. [ ] Implementar `EntityTypeValidator` en `infrastructure/nlp/validators/`
4. [ ] Calcular y persistir centroides por tipo
5. [ ] Integrar validador en pipeline NER existente
6. [ ] Evaluar reducción de errores en set de validación
7. [ ] (Opcional) Evaluar `Legal-Embed` vs `multilingual-e5-large`

---

```
Versión: 1.0.0
Autor: AlexAlves87
Tiempo de investigación: ~15 min
```
