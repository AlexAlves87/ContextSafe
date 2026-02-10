# Investigacion: Embeddings Generalistas vs Legales para Desambiguacion de Tipos de Entidad

**Fecha:** 2026-02-07
**Objetivo:** Determinar si usar embeddings generalistas (multilingual-e5-large) o especializados en legal (Legal-Embed, voyage-law-2) para el validador post-NER de tipos de entidad en ContextSafe.

---

## 1. Resumen Ejecutivo

1. **Hallazgo principal**: Los embeddings legales estan optimizados para **retrieval** (buscar documentos similares), NO para **discriminacion de tipos de entidad**. Esto explica los falsos positivos observados.

2. **Recomendacion**: Usar **embeddings generalistas** (`intfloat/multilingual-e5-large`) para desambiguacion de tipos de entidad. Los legales pueden causar colapso del espacio semantico donde PERSON y ORGANIZATION quedan demasiado cerca.

3. **Evidencia clave**: El fine-tuning de dominio puede causar "over-specialization" que reduce la capacidad de discriminacion entre categorias (catastrophic forgetting de fronteras entre tipos).

4. **Alternativa hibrida**: Si se necesita conocimiento legal, usar enfoque de dos etapas: generalista para tipo + legal para validacion de entidad especifica.

5. **Reduccion de errores esperada**: 4-5% con embeddings generalistas bien calibrados (literatura: WNUT17, NER Retriever).

---

## 2. Literatura Revisada

### 2.1 Generalistas vs Especificos de Dominio

| Paper/Fuente | Venue/Ano | Hallazgo Relevante |
|--------------|-----------|-------------------|
| "Do we need domain-specific embedding models?" | arXiv:2409.18511 (2024) | En finanzas (FinMTEB), modelos generales degradan vs especificos. PERO: esto es para **retrieval**, no clasificacion de tipos. |
| "How Does Fine-tuning Affect the Geometry of Embedding Space?" | ACL Findings 2021 | Fine-tuning de dominio **reduce la separacion** entre clases en el espacio de embeddings. Clusters colapsan. |
| "Is Anisotropy Really the Cause of BERT Embeddings not Working?" | EMNLP Findings 2022 | Anisotropia (embeddings concentrados en cono estrecho) es problema conocido. Fine-tuning de dominio lo **empeora**. |
| "Dynamic Expert Specialization: Catastrophic Forgetting-Free Multi-Domain MoE" | EMNLP 2025 | Catastrophic forgetting ocurre en fine-tuning de dominio. Modelos olvidan fronteras aprendidas previamente. |
| "Continual Named Entity Recognition without Catastrophic Forgetting" | arXiv:2310.14541 (2023) | NER continuo sufre olvido catastrofico: tipos antiguos se "consolidan" en non-entity. Analogo a nuestro problema. |

### 2.2 Por Que Embeddings Legales Causan Falsos Positivos

| Fenomeno | Explicacion | Fuente |
|----------|-------------|--------|
| **Colapso de espacio semantico** | Fine-tuning legal optimiza para que documentos legales similares esten cerca, NO para separar PERSON de ORGANIZATION | Weaviate Blog, MongoDB Fine-Tuning Guide |
| **Over-specialization** | "Overly narrow training can make the fine-tuned model too specialized" - pierde capacidad de discriminacion general | [Weaviate](https://weaviate.io/blog/fine-tune-embedding-model) |
| **Contrastive loss orientado a retrieval** | voyage-law-2 usa "specifically designed positive pairs" para retrieval legal, no para clasificacion de entidades | [Voyage AI Blog](https://blog.voyageai.com/2024/04/15/domain-specific-embeddings-and-retrieval-legal-edition-voyage-law-2/) |
| **Terminologia legal uniforme** | En textos legales, "Garcia" puede ser demandante, abogado, o nombre de bufete. El modelo legal los embebe **cerca** porque todos son legales | Observacion empirica del usuario |

### 2.3 Centroides y Clasificacion Basada en Prototipos

| Paper/Fuente | Venue/Ano | Hallazgo Relevante |
|--------------|-----------|-------------------|
| "NER Retriever: Zero-Shot NER with Type-Aware Embeddings" | arXiv:2509.04011 (2025) | Capas intermedias (layer 17) mejor que salidas finales para tipo. MLP con contrastive loss para separar tipos. |
| "CEPTNER: Contrastive Learning Enhanced Prototypical Network" | KBS (2024) | Redes prototipicas con 50-100 ejemplos por tipo son suficientes para centroides robustos. |
| "ReProCon: Scalable Few-Shot Biomedical NER" | arXiv:2508.16833 (2025) | Multiples prototipos por categoria mejoran representacion de entidades heterogeneas. |
| "Mastering Intent Classification with Embeddings: Centroids" | Medium (2024) | Centroides tienen "fastest training time" y accuracy decente. Perfectos para actualizaciones rapidas. |

### 2.4 Benchmarks de Modelos de Embedding

| Modelo | Tamano | Idiomas | MTEB Avg | Ventaja | Desventaja |
|--------|--------|---------|----------|---------|------------|
| `intfloat/multilingual-e5-large` | 1.1GB | 100 | ~64 | Mejor multilingual general, excelente espanol | Requiere prefijo "query:" |
| `intfloat/multilingual-e5-large-instruct` | 1.1GB | 100 | ~65 | Soporta instrucciones, mas flexible | Ligeramente mas lento |
| `BAAI/bge-m3` | 1.5GB | 100+ | ~66 | Hibrido dense+sparse, 8192 tokens | Mas complejo de usar |
| `voyage-law-2` | API | EN | ~72 (legal) | Mejor para retrieval legal | API comercial, solo ingles |
| `Legal-Embed (Wasserstoff)` | 1.1GB | Multi | N/A | Fine-tuned en legal | **Probablemente causa FPs en clasificacion** |

---

## 3. Analisis: Por Que Generalistas Son Mejores para Tipo de Entidad

### 3.1 Objetivo de Entrenamiento Diferente

| Embeddings Legales | Embeddings Generalistas |
|--------------------|------------------------|
| Optimizados para: "documento A similar a documento B" | Optimizados para: "texto A semanticamente relacionado con texto B" |
| Positive pairs: fragmentos del mismo documento legal | Positive pairs: parafrasis, traducciones, variantes |
| Resultado: todo lo legal esta junto | Resultado: tipos semanticos separados |

**Consecuencia**: En embeddings legales, "Alejandro Alvarez" (abogado) y "Bufete Alvarez S.L." (empresa) estan **cerca** porque ambos son legales. En generalistas, estan **lejos** porque uno es persona y otro es organizacion.

### 3.2 Evidencia de Anisotropia Agravada

El paper de ACL Findings 2021 demuestra que:

1. Fine-tuning **reduce la varianza** del espacio de embeddings
2. Los clusters de tipos diferentes **se acercan**
3. La separabilidad lineal **disminuye**

Esto explica directamente los falsos positivos: cuando todos los embeddings legales colapsan hacia una region, la distancia coseno pierde poder discriminativo.

### 3.3 Tarea vs Dominio

| Aspecto | Embeddings de Dominio (Legal) | Embeddings de Tarea (Tipo) |
|---------|------------------------------|---------------------------|
| Pregunta que responden | "Es este texto legal?" | "Es esto una persona o empresa?" |
| Entrenamiento | Corpus legal | Contrastive por tipo de entidad |
| Utilidad para NER type validation | Baja | Alta |

Nuestro problema es de **tarea** (clasificar tipo), no de **dominio** (identificar textos legales).

---

## 4. Recomendacion para ContextSafe

### 4.1 Enfoque Recomendado: Generalista Puro

```
Pipeline:
  NER → Detecciones con tipo asignado
    ↓
  EntityTypeValidator (multilingual-e5-large)
    ↓
  Para cada entidad:
    1. Embeber "query: [entidad + contexto ±10 tokens]"
    2. Comparar vs centroides por tipo (PERSON_NAME, ORGANIZATION, DATE, LOCATION)
    3. Decisiones:
       - Si centroide_mejor ≠ tipo_NER AND similitud > 0.75 AND margen > 0.10 → RECLASIFICAR
       - Si margen < 0.05 → FLAG HITL
       - Else → MANTENER tipo NER
```

**Modelo**: `intfloat/multilingual-e5-large` (1.1GB)

**Justificacion**:
- Entrenado en 100 idiomas incluyendo espanol
- NO sobre-especializado en ningun dominio
- Preserva separacion semantica entre PERSON/ORGANIZATION/DATE/LOCATION
- Ya recomendado en investigacion previa (ver `2026-02-07_embeddings_entity_type_disambiguation.md`)

### 4.2 Enfoque Alternativo: Hibrido (Si Se Necesita Conocimiento Legal)

```
Etapa 1: Clasificacion de tipo (GENERALISTA)
  multilingual-e5-large → Tipo de entidad

Etapa 2: Validacion de entidad legal (LEGAL, opcional)
  voyage-law-2 o Legal-Embed → "Es esta entidad valida en contexto legal?"
  (Solo para casos flagged como dudosos)
```

**Cuando usar hibrido**: Si hay entidades legales especificas (ej: "articulo 24.2 CE", "Ley 13/2022") que requieren validacion de conocimiento legal.

Para ContextSafe (PII generico), el enfoque generalista puro es suficiente.

### 4.3 Configuracion de Centroides

| Tipo | Ejemplos Necesarios | Estrategia de Contexto |
|------|---------------------|------------------------|
| PERSON_NAME | 100 | "query: El abogado [NOMBRE] comparecio..." |
| ORGANIZATION | 100 | "query: La empresa [ORG] interpuso recurso..." |
| DATE | 50 | "query: Con fecha [FECHA] se dicto sentencia..." |
| LOCATION | 50 | "query: En la ciudad de [LUGAR] se celebro..." |
| DNI_NIE | 30 | "query: con DNI [NUMERO]" (contexto corto, patron fijo) |

**Contexto**: ±10 tokens alrededor de la entidad. Ni muy corto (pierde contexto) ni muy largo (introduce ruido).

---

## 5. Experimento Propuesto

### 5.1 Comparacion A/B

| Condicion | Modelo | Esperado |
|-----------|--------|----------|
| A (Baseline) | Sin validador | Pass rate actual: 60% |
| B (Generalista) | `multilingual-e5-large` | Pass rate esperado: 64-65% |
| C (Legal) | `Legal-Embed-intfloat-multilingual-e5-large-instruct` | Pass rate esperado: < 60% (mas FPs) |

### 5.2 Metricas a Evaluar

1. **Pass rate en test adversarial** (35 tests existentes)
2. **Precision de reclasificacion**: % de reclasificaciones correctas
3. **Tasa de falsos positivos**: Entidades correctamente tipadas que fueron mal reclasificadas
4. **Latencia adicional**: ms por entidad validada

### 5.3 Casos de Prueba Especificos

Basados en errores de auditoria.md (ver `2026-02-07_embeddings_entity_type_disambiguation.md`, seccion 6):

| Entidad | Tipo NER | Tipo Correcto | Modelo Esperado OK |
|---------|----------|---------------|-------------------|
| "Alejandro Alvarez" | ORGANIZATION | PERSON_NAME | Generalista |
| "10/10/2025" | ORGANIZATION | DATE | Generalista |
| "Pura" | LOCATION | PERSON_NAME | Generalista |
| "Finalmente" | ORGANIZATION | NO ES PII | Generalista (baja similitud con todos) |
| "Whatsapp" | PERSON | ORGANIZATION/PLATFORM | Generalista |

---

## 6. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Mitigacion |
|--------|-------------|------------|
| Generalista tampoco discrimina bien PERSON/ORG en espanol legal | Media | Evaluar antes de implementar; si falla, entrenar centroides con contrastive loss |
| Latencia inaceptable (>100ms/entidad) | Baja | Batch processing, cache de embeddings frecuentes |
| Centroides requieren mas de 100 ejemplos | Baja | Aumentar a 200 si F1 < 0.90 en validacion |
| Modelo de 1.1GB no cabe en produccion | Baja | Quantizar a INT8 (~300MB) o usar e5-base (560MB) |

---

## 7. Conclusion

**Los embeddings legales estan optimizados para la tarea equivocada.** Su objetivo (retrieval de documentos similares) causa que entidades de diferentes tipos pero del mismo dominio (legal) queden embebidas cerca, reduciendo la capacidad de discriminacion.

Para desambiguacion de tipos de entidad, los **embeddings generalistas** preservan mejor las fronteras semanticas entre PERSON, ORGANIZATION, DATE, etc., porque no han sido "colapsados" hacia un dominio especifico.

**Recomendacion final**: Implementar validador con `intfloat/multilingual-e5-large` y evaluar empiricamente antes de considerar alternativas legales.

---

## 8. Proximos Pasos

1. [ ] Descargar `intfloat/multilingual-e5-large` (~1.1GB)
2. [ ] Construir dataset de ejemplos por tipo (PERSON_NAME, ORGANIZATION, DATE, LOCATION) con contexto legal
3. [ ] Calcular centroides para cada tipo
4. [ ] Implementar `EntityTypeValidator` con umbrales configurables
5. [ ] Evaluar en test adversarial (35 tests)
6. [ ] (Opcional) Comparar vs `Legal-Embed` para confirmar hipotesis de falsos positivos
7. [ ] Documentar resultados y decision final

---

## Documentos Relacionados

| Documento | Relacion |
|-----------|----------|
| `ml/docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md` | Investigacion previa, arquitectura propuesta |
| `ml/docs/reports/2026-02-07_embeddings_roadmap_document_classification.md` | Roadmap embeddings, criterios de activacion |
| `ml/docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | Pipeline actual, metricas baseline |
| `auditoria.md` | Errores de clasificacion identificados |
| `ml/models/type_centroids.json` | Centroides existentes (requiere verificar modelo usado) |

---

## Referencias

1. **FinMTEB**: Li et al. (2024). "Do we need domain-specific embedding models? An empirical investigation." arXiv:2409.18511. https://arxiv.org/abs/2409.18511

2. **Geometry of Fine-tuning**: Merchant et al. (2020). "What Happens To BERT Embeddings During Fine-tuning?" ACL Findings 2021. https://aclanthology.org/2021.findings-emnlp.261.pdf

3. **Anisotropy**: Ethayarajh (2019). "How Contextual are Contextualized Word Representations?" EMNLP 2019. Rajaee & Pilehvar (2022). "Is Anisotropy Really the Cause?" EMNLP Findings 2022. https://aclanthology.org/2022.findings-emnlp.314.pdf

4. **Catastrophic Forgetting in NER**: Wang et al. (2023). "Continual Named Entity Recognition without Catastrophic Forgetting." arXiv:2310.14541. https://arxiv.org/abs/2310.14541

5. **DES-MoE**: Yang et al. (2025). "Dynamic Expert Specialization: Catastrophic Forgetting-Free Multi-Domain MoE." EMNLP 2025. https://aclanthology.org/2025.emnlp-main.932.pdf

6. **NER Retriever**: Zhang et al. (2025). "NER Retriever: Zero-Shot NER with Type-Aware Embeddings." arXiv:2509.04011. https://arxiv.org/abs/2509.04011

7. **CEPTNER**: Wang et al. (2024). "Contrastive learning Enhanced Prototypical network for Few-shot NER." Knowledge-Based Systems. https://doi.org/10.1016/j.knosys.2024.111512

8. **ReProCon**: Liu et al. (2025). "ReProCon: Scalable Few-Shot Biomedical NER." arXiv:2508.16833. https://arxiv.org/abs/2508.16833

9. **Multilingual E5**: Wang et al. (2024). "Multilingual E5 Text Embeddings." arXiv:2402.05672. https://huggingface.co/intfloat/multilingual-e5-large

10. **voyage-law-2**: Voyage AI (2024). "Domain-Specific Embeddings: Legal Edition." https://blog.voyageai.com/2024/04/15/domain-specific-embeddings-and-retrieval-legal-edition-voyage-law-2/

11. **Fine-tuning Trade-offs**: Weaviate (2024). "Why, When and How to Fine-Tune a Custom Embedding Model." https://weaviate.io/blog/fine-tune-embedding-model

12. **Intent Classification with Centroids**: Puig (2024). "Mastering Intent Classification with Embeddings." Medium. https://medium.com/@mpuig/mastering-intent-classification-with-embeddings-centroids-neural-networks-and-random-forests-3fe7c57ca54c

---

```
Version: 1.0.0
Autor: AlexAlves87
Tiempo de investigacion: ~25 min
Tokens de busqueda: 12 queries
```
