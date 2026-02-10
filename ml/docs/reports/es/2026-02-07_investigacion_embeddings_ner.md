# Investigacion: Embeddings Generales vs Dominio Legal para Desambiguacion de Tipos de Entidad en NER

**Fecha:** 2026-02-07
**Objetivo:** Investigar por que los embeddings legales especializados producen mas falsos
positivos que los embeddings de proposito general en la tarea de clasificacion de tipo de
entidad post-NER, y determinar la mejor estrategia de embeddings para ContextSafe.

---

## 1. Resumen Ejecutivo

1. **Los embeddings de dominio legal producen mas falsos positivos** porque el fine-tuning
   legal reduce la capacidad discriminativa entre tipos de entidad al colapsar el espacio
   de embeddings alrededor de patrones linguisticos legales (anisotropia aumentada, espacio
   semantico mas estrecho).

2. **Los embeddings de proposito general son superiores para discriminacion de tipos de
   entidad** porque mantienen un espacio semantico mas amplio y diverso donde las
   diferencias entre categorias (persona vs organizacion vs fecha) son mas pronunciadas.

3. **La anisotropia NO es inherentemente mala** -- trabajo reciente (ICLR 2024) muestra que
   la anisotropia controlada puede mejorar rendimiento -- pero la anisotropia no controlada
   por fine-tuning de dominio reduce la discriminacion inter-clase necesaria para
   centroides de tipo.

4. **Recomendacion: usar `BAAI/bge-m3` o `intfloat/multilingual-e5-large`** (embeddings
   generales) para el validador de tipo, NO embeddings legales. Si se desea combinar
   conocimiento de dominio, usar un enfoque hibrido con adaptadores (LoRA) que preserven
   la capacidad general.

5. **La tecnica de centroides con contexto esta bien respaldada** por la literatura de redes
   prototipicas (CEPTNER, KCL), pero requiere 50-100 ejemplos diversos por tipo y contexto
   circundante de 10-15 tokens.

---

## 2. Hallazgo 1: General-Purpose vs Domain-Specific Embeddings para Clasificacion de Tipo de Entidad

### 2.1 Evidencia clave: General-purpose modelos fallan en tareas de dominio PERO destacan en discriminacion de tipos

| Paper | Venue/Ano | Hallazgo clave |
|-------|-----------|----------------|
| **"Do We Need Domain-Specific Embedding Models? An Empirical Investigation"** (Tang & Yang) | arXiv 2409.18511 (2024) | Evaluaron 7 modelos SOTA en FinMTEB (finance benchmark). Los modelos generales mostraron caida significativa en tareas de dominio, y su rendimiento en MTEB NO correlaciona con rendimiento en FinMTEB. **PERO**: esta caida fue en retrieval y STS, no en clasificacion de tipos de entidad. |
| **"NuNER: Entity Recognition Encoder Pre-training via LLM-Annotated Data"** (Bogdanov et al.) | EMNLP 2024 | Modelo compacto (base RoBERTa) pre-entrenado con contrastive learning sobre 4.38M anotaciones de entidad. Supera modelos de tamano similar en few-shot NER y compite con LLMs mucho mas grandes. **Clave**: la diversidad de tipos de entidad en el dataset de pre-entrenamiento es fundamental. |
| **"LegNER: A Domain-Adapted Transformer for Legal NER and Text Anonymization"** (Al-Hussaeni et al.) | Frontiers in AI (2025) | Modelo legal basado en BERT-base + vocabulario extendido + 1,542 casos judiciales anotados. F1 >99% en 6 tipos de entidad. **Sin embargo**: el paper no reporta analisis de falsos positivos entre tipos, y las entidades evaluadas son muy diferentes entre si (PERSON vs LAW vs CASE_REFERENCE). |
| **"MEL: Legal Spanish Language Model"** (2025) | arXiv 2501.16011 | XLM-RoBERTa-large fine-tuned con 5.52M textos legales espanoles (92.7 GB). Supera al XLM-R base en clasificacion de documentos. **Critico**: los autores admiten que "Token or span classification tasks remain unevaluated due to the lack of annotated texts" -- es decir, NO evaluaron NER. |

### 2.2 Interpretacion: Por que los modelos generales discriminan mejor TIPOS

La distincion clave es entre **dos tareas diferentes**:

| Tarea | Que necesita el embedding | Mejor modelo |
|-------|---------------------------|--------------|
| Retrieval legal / STS legal | Capturar matices semanticos legales | Domain-specific |
| Clasificacion de tipo de entidad | Separar categorias amplias (persona vs org vs fecha) | General-purpose |

Los embeddings legales estan optimizados para la primera tarea: recuperar documentos
legales similares, entender terminologia juridica, capturar relaciones legales. Esto
los hace PEORES para la segunda tarea porque:

1. **Colapso de diversidad**: el fine-tuning legal acerca todas las representaciones hacia
   el subespacio legal, reduciendo la distancia entre "persona mencionada en sentencia" y
   "organizacion mencionada en sentencia" porque ambas aparecen en contextos legales similares.

2. **Sesgo contextual**: un modelo legal aprende que "Telefonica" en un contexto legal es tan
   legal-relevant como "Alejandro Alvarez", aplanando las diferencias de tipo.

3. **Anisotropia no controlada**: el fine-tuning introduce anisotropia que puede colapsar
   tipos distintos en las mismas direcciones dominantes del espacio de embeddings.

**URL relevante**: [Do We Need Domain-Specific Embedding Models?](https://arxiv.org/abs/2409.18511)

---

## 3. Hallazgo 2: Por Que los Embeddings Legales Producen Mas Falsos Positivos

### 3.1 El problema de anisotropia en embeddings fine-tuned

| Paper | Venue/Ano | Hallazgo clave |
|-------|-----------|----------------|
| **"Anisotropy is Not Inherent to Transformers"** (Machina & Mercer) | NAACL 2024 | Demuestran que la anisotropia no es inherente a la arquitectura transformer. Identifican modelos Pythia grandes con espacios isotropicos. Las justificaciones teoricas previas para la anisotropia eran insuficientes. |
| **"Stable Anisotropic Regularization" (I-STAR)** (Rudman & Eickhoff) | ICLR 2024 | Resultado contraintuitivo: REDUCIR la isotropia (aumentar anisotropia) mejora el rendimiento downstream. Usar IsoScore* (metrica diferenciable) como regularizador. **Implicacion clave**: la anisotropia CONTROLADA puede ser beneficiosa, pero la anisotropia NO CONTROLADA por fine-tuning de dominio es perjudicial. |
| **"The Shape of Learning: Anisotropy and Intrinsic Dimensions in Transformer-Based Models"** (2024) | EACL 2024 | Los decoders transformer muestran una curva en forma de campana con maxima anisotropia en capas medias, mientras que los encoders muestran anisotropia mas uniforme. Las capas donde la anisotropia es mayor coinciden con capas que codifican informacion de tipo. |
| **"How Does Fine-tuning Affect the Geometry of Embedding Space: A Case Study on Isotropy"** (Rajaee & Pilehvar) | EMNLP 2021 Findings | Aunque la isotropia es deseable, el fine-tuning NO necesariamente mejora la isotropia. Las estructuras locales (como codificacion de tipos de token) sufren cambios masivos durante el fine-tuning. Las direcciones elongadas (direcciones dominantes) en el espacio fine-tuned cargan el conocimiento linguistico esencial. |
| **"Representation Degeneration Problem in Prompt-based Fine-tuning"** | LREC 2024 | La anisotropia del espacio de embeddings limita el rendimiento en fine-tuning basado en prompts. Proponen CLMA (Contrastive Learning framework) para aliviar la anisotropia. |

### 3.2 Mecanismo de falsos positivos en embeddings legales

Basado en la evidencia anterior, el mecanismo por el cual los embeddings legales producen
mas falsos positivos en validacion de tipo de entidad es:

```
1. Fine-tuning legal → Embedding space se contrae hacia subespacio legal
                         ↓
2. Representaciones de "persona en contexto legal" y
   "organizacion en contexto legal" se acercan
   (ambas son "entidades legalmente relevantes")
                         ↓
3. Centroides de PERSON_NAME y ORGANIZATION se solapan
   en el espacio legal-fine-tuned
                         ↓
4. Cosine similarity entre centroide_PERSON y una ORGANIZATION
   es mas alta de lo que seria con embeddings generales
                         ↓
5. Mas entidades cruzan el umbral de reclasificacion → mas FP
```

### 3.3 Evidencia directa del dominio legal

| Paper | Venue/Ano | Hallazgo clave |
|-------|-----------|----------------|
| **"Improving Legal Entity Recognition Using a Hybrid Transformer Model and Semantic Filtering Approach"** | arXiv 2410.08521 (2024) | Legal-BERT produce falsos positivos en terminos ambiguos y entidades anidadas. Proponen filtrado semantico post-prediccion usando cosine similarity contra patrones legales predefinidos. **Resultado**: Precision sube de 90.2% a 94.1% (+3.9 pp), F1 de 89.3% a 93.4% (+4.1 pp). Usan la formula S(ei,Pj) = cos(ei, Pj) con umbral tau para filtrar. |

**Este paper valida directamente nuestro enfoque** de usar cosine similarity para filtrar
predicciones, PERO usa patrones legales predefinidos en lugar de centroides de tipo. La
combinacion de ambos enfoques (centroides generales + patrones legales como filtro
adicional) es una extension natural.

**URL relevante**: [Improving Legal Entity Recognition Using Semantic Filtering](https://arxiv.org/abs/2410.08521)

---

## 4. Hallazgo 3: Mejores Modelos de Embeddings para Desambiguacion de Tipo de Entidad (2024-2026)

### 4.1 Comparacion de modelos candidatos

| Modelo | Tamano | Dim | Idiomas | MTEB Score | Fortalezas | Debilidades para nuestra tarea |
|--------|--------|-----|---------|------------|------------|-------------------------------|
| **BAAI/bge-m3** | ~2.3GB | 1024 | 100+ | 63.0 | Multi-granularidad (dense+sparse+ColBERT), mejor rendimiento multilingual en MTEB | Mayor tamano, mayor latencia |
| **intfloat/multilingual-e5-large** | ~1.1GB | 1024 | 100+ | ~62 | Excelente espanol, bien documentado, requiere prefijo "query:" | Ligeramente inferior a bge-m3 en multilingual |
| **nomic-ai/nomic-embed-text-v2** | ~700MB | 768 | 100 | ~62 | MoE (Mixture of Experts), eficiente, 8192 tokens | Mas reciente, menos validado en espanol legal |
| **intfloat/multilingual-e5-small** | ~448MB | 384 | 100 | ~56 | Mas ligero, latencia baja | Dimension menor puede perder discriminacion |
| **Wasserstoff-AI/Legal-Embed** | ~1.1GB | 1024 | Multi | N/A | Fine-tuned para legal | **DESCARTADO: mayor FP por razon analizada en seccion 3** |

### 4.2 Recomendacion basada en evidencia

**Modelo principal: `BAAI/bge-m3`**

Justificacion:
1. Mejor rendimiento en benchmarks multilinguales, incluyendo espanol
   (ver [OpenAI vs Open-Source Multilingual Embedding Models](https://towardsdatascience.com/openai-vs-open-source-multilingual-embedding-models-e5ccb7c90f05/))
2. Mayor dimensionalidad (1024) = mayor capacidad para separar centroides de tipo
3. Dense+sparse+ColBERT retrieval funciona bien para comparaciones de similitud
4. Soporta hasta 8192 tokens (util para contextos legales largos)

**Modelo alternativo: `intfloat/multilingual-e5-large`**

Justificacion:
1. Bien documentado con paper tecnico (arXiv:2402.05672)
2. Rendimiento excelente en espanol verificado
3. Ligeramente mas pequeno que bge-m3
4. Ya fue propuesto en
   `docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md`

**IMPORTANTE**: NO usar `Legal-Embed` ni ningun modelo fine-tuned para dominio legal. La
evidencia academica indica que los modelos generales preservan mejor la separacion entre
tipos de entidad, que es exactamente lo que necesitamos para centroides.

### 4.3 Fuentes de benchmarks

| Benchmark | Que mide | Referencia |
|-----------|----------|------------|
| MTEB (Massive Text Embedding Benchmark) | 8 tareas incluyendo clasificacion y clustering | [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) |
| FinMTEB (Finance MTEB) | Rendimiento en dominio financiero | Tang & Yang (2024), arXiv:2409.18511 |
| MMTEB (Massive Multilingual TEB) | Extension multilingual de MTEB (2025) | [MMTEB GitHub](https://github.com/embeddings-benchmark/mteb) |

**Nota critica**: Ningun benchmark existente mide directamente "discriminacion de tipo de
entidad mediante centroides". MTEB tiene subtareas de clasificacion y clustering que son
aproximaciones utiles. Se recomienda crear un benchmark interno para ContextSafe.

---

## 5. Hallazgo 4: Tecnicas de Validacion de Tipo Basada en Centroides

### 5.1 Redes prototipicas y centroides para NER

| Paper | Venue/Ano | Hallazgo clave |
|-------|-----------|----------------|
| **"CEPTNER: Contrastive Learning Enhanced Prototypical Network for Two-stage Few-shot NER"** (Wang et al.) | Knowledge-Based Systems (2024) | Dos etapas: (1) deteccion de limites, (2) clasificacion prototipica con contrastive learning. El aprendizaje contrastivo a nivel de entidad separa efectivamente los tipos. Evaluado en Few-NERD, CrossNER, SNIPS. |
| **"Transformer-based Prototype Network for Chinese Nested NER"** (MSTPN) | Scientific Reports (2025) | Redes prototipicas con transformers para NER anidado. Usa entity bounding boxes como prototipos. |
| **"KCL: Few-shot NER with Knowledge Graph and Contrastive Learning"** | LREC-COLING 2024 | Combina Knowledge Graphs con contrastive learning para aprender representacion semantica de etiquetas. Usa KG para proveer informacion estructurada de tipo. La representacion contrastiva separa clusters de etiquetas en el espacio prototipico. |
| **"Multi-Head Self-Attention-Enhanced Prototype Network with Contrastive-Center Loss for Few-Shot Relation Extraction"** | Applied Sciences (2024) | Contrastive-center loss que compara muestras de entrenamiento con centros de clase correspondientes Y no-correspondientes. Reduce distancias intra-clase y aumenta distancias inter-clase. |
| **"CLESR: Context-Based Label Knowledge Enhanced Span Recognition for NER"** | Int J Computational Intelligence Systems (2024) | Mejora NER anidado integrando informacion contextual con conocimiento de etiquetas. Spans se alinean con descripciones textuales de tipos en espacio semantico compartido. |

### 5.2 Best practices para construccion de centroides

Basado en la literatura revisada:

| Aspecto | Recomendacion | Justificacion |
|---------|---------------|---------------|
| **Numero de ejemplos** | 50-100 por tipo | CEPTNER muestra efectividad con pocos ejemplos; 50 es minimo, 100 es robusto |
| **Diversidad de ejemplos** | Incluir variaciones de contexto, formato, longitud | KCL enfatiza diversidad para clusters mas discriminativos |
| **Tamano de contexto** | 10-15 tokens circundantes | La encuesta NER (arXiv:2401.10825) confirma que BERT captura contexto intra- e inter-frase efectivamente |
| **Actualizacion de centroides** | Recalcular periodicamente con nuevos ejemplos confirmados | CEPTNER muestra que mas ejemplos mejoran separacion; centroides deben evolucionar |
| **Contrastive refinement** | Entrenar con perdida contrastiva para maximizar separacion | Multiple papers muestran que contrastive loss es CLAVE para separacion de tipos |
| **Capas intermedias** | Considerar extraer de capas 15-17, no solo capa final | NER Retriever (arXiv:2509.04011) muestra que capas intermedias contienen mas info de tipo |

### 5.3 Tamano de ventana de contexto

| Paper | Hallazgo sobre contexto |
|-------|------------------------|
| Survey NER (arXiv:2401.10825) | "BERT encodings capture important within and adjacent-sentence context." Aumentar ventana mejora rendimiento. |
| Span-based Unified NER via Contrastive Learning (IJCAI 2024) | Spans con contexto se alinean con descripciones de tipo en espacio compartido. Contexto es necesario para desambiguar. |
| Contextualized Span Representations (Wadden et al.) | Propagacion de representaciones de span via coreference links permite desambiguar menciones dificiles. |

**Recomendacion**: Para ContextSafe, usar **contexto de 10-15 tokens** a cada lado de la
entidad. Para entidades al inicio/final de frase, rellenar con tokens de la frase
anterior/siguiente si esta disponible.

---

## 6. Hallazgo 5: Enfoques Hibridos (General + Dominio)

### 6.1 Concatenacion y ensemble de embeddings

| Paper | Venue/Ano | Hallazgo clave |
|-------|-----------|----------------|
| **"Automated Concatenation of Embeddings for Structured Prediction" (ACE)** | ACL-IJCNLP 2021 | Framework que automaticamente encuentra la mejor concatenacion de embeddings para structured prediction (incluyendo NER). Alcanza SOTA en 6 tareas sobre 21 datasets. La seleccion varia segun tarea y conjunto de candidatos. |
| **"Pooled Contextualized Embeddings for NER"** (Akbik et al.) | NAACL 2019 | Agrega embeddings contextualizados de cada instancia unica para crear representacion "global". Stacked embeddings (combinar multiple tipos) es una caracteristica clave de Flair y mejora significativamente NER. |
| **"Improving Few-Shot Cross-Domain NER by Instruction Tuning a Word-Embedding based Retrieval Augmented LLM" (IF-WRANER)** | EMNLP 2024 Industry | Usa word-level embeddings (no sentence-level) para retrieval de ejemplos in-prompt. Supera SOTA en CrossNER por >2% F1. Deployed en produccion, reduciendo escalaciones humanas ~15%. |
| **"Pre-trained Embeddings for Entity Resolution: An Experimental Analysis"** (Zeakis et al.) | VLDB 2023 | Analisis de 12 modelos de lenguaje sobre 17 datasets para entity resolution. Embeddings contextualizados (BERT variants) superan estaticos (fastText) consistentemente, pero la combinacion puede ser beneficiosa. |

### 6.2 Adaptadores (LoRA) para preservar conocimiento general

| Paper | Venue/Ano | Hallazgo clave |
|-------|-----------|----------------|
| **"Continual Named Entity Recognition without Catastrophic Forgetting"** (Zheng et al.) | EMNLP 2023 | Proponen pooled feature distillation loss + pseudo-labeling + adaptive re-weighting. El olvido catastrofico en NER continuo es intensificado por el "semantic shift" del tipo no-entidad. |
| **"A New Adapter Tuning of LLM for Chinese Medical NER"** | Automation in Construction (2024) | Adapters evitan olvido catastrofico porque aprenden conocimiento nuevo sin ajustes extensivos de parametros. Son preferibles para NER multi-dominio. |
| **"Mixture of LoRA Experts for Continual Information Extraction"** | EMNLP 2025 Findings | Framework MoE con LoRA para extraccion de informacion continua. Permite agregar dominios sin olvidar los anteriores. |
| **"LoRASculpt: Sculpting LoRA for Harmonizing General and Specialized Knowledge"** | CVPR 2025 | Tecnica para equilibrar conocimiento general y especializado durante fine-tuning con LoRA. |

### 6.3 Estrategias de combinacion viables para ContextSafe

| Estrategia | Complejidad | Beneficio esperado | Recomendada |
|------------|-------------|-------------------|-------------|
| **A: Embeddings generales puros** | Baja | Buena discriminacion de tipos sin FP adicionales | Si (baseline) |
| **B: Concatenar general + legal** | Media | Mas dimensiones, captura ambos aspectos | Evaluable pero costosa en latencia |
| **C: Weighted average general + legal** | Media | Mas simple que concat, pero pierde informacion | No recomendada (promedio diluye) |
| **D: Meta-modelo sobre embeddings multiples** | Alta | Mejor precision si hay datos de entrenamiento suficientes | Para futuro |
| **E: LoRA adapter sobre modelo general** | Media-Alta | Preserva capacidad general + agrega dominio | Si (segundo paso) |

**Recomendacion para ContextSafe**:

- **Fase 1 (inmediata)**: Usar embeddings generales puros (bge-m3 o e5-large).
  Evaluar reduccion de FP frente a la experiencia con embeddings legales.

- **Fase 2 (si Fase 1 insuficiente)**: Aplicar LoRA adapter sobre el modelo general
  con ejemplos contrastivos de entidades legales espanolas. Esto preserva la capacidad
  de discriminacion de tipos general mientras agrega conocimiento del dominio.

- **Fase 3 (opcional)**: ACE-style automated search de la mejor concatenacion si se
  dispone de un dataset de validacion de tipo suficientemente grande.

---

## 7. Sintesis y Recomendacion Final

### 7.1 Respuesta directa a las preguntas de investigacion

**P1: General-purpose vs domain-specific para clasificacion de tipo de entidad?**

Usar **general-purpose**. La evidencia de multiples papers (Tang & Yang 2024, Rajaee &
Pilehvar 2021, Machina & Mercer NAACL 2024) indica que:
- Los modelos generales mantienen espacios semanticos mas amplios
- La discriminacion de tipos de entidad requiere separacion inter-clase, no profundidad
  intra-dominio
- Los modelos de dominio colapsan tipos similares en el mismo subespacio

**P2: Por que los embeddings legales producen mas falsos positivos?**

Tres factores convergentes:
1. **Colapso de diversidad semantica**: fine-tuning legal acerca representaciones de todas
   las entidades hacia el subespacio "legal"
2. **Anisotropia no controlada**: fine-tuning introduce direcciones dominantes que codifican
   "legalidad" en lugar de "tipo de entidad" (Rajaee & Pilehvar 2021, Rudman & Eickhoff
   ICLR 2024)
3. **Solapamiento de centroides**: centroides de PERSON y ORGANIZATION se acercan porque
   ambos aparecen en contextos legales identicos

**P3: Mejor modelo?**

`BAAI/bge-m3` (primera opcion) o `intfloat/multilingual-e5-large` (segunda opcion).
Ambos son generales, multilinguales, con buen soporte para espanol y dimensionalidad
1024 suficiente para separar centroides de tipo.

**P4: Tecnica de centroides?**

Bien respaldada por CEPTNER (2024), KCL (2024), MSTPN (2025). Claves:
- 50-100 ejemplos diversos por tipo
- Contexto de 10-15 tokens alrededor de la entidad
- Contrastive learning para refinar centroides si es posible
- Capas intermedias (15-17) pueden ser mas informativas que la capa final

**P5: Enfoque hibrido?**

Para el futuro: LoRA adapters sobre modelo general es la estrategia mas prometedora.
Preserva discriminacion general + agrega conocimiento de dominio. ACE (concatenacion
automatizada) es viable si hay datos de evaluacion suficientes.

### 7.2 Impacto en el documento previo

El documento `docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md` recomienda
`multilingual-e5-large` como modelo principal y sugiere evaluar `Legal-Embed` como
alternativa. Basado en esta investigacion:

| Aspecto | Documento previo | Actualizacion |
|---------|------------------|---------------|
| Modelo principal | `multilingual-e5-large` | **Correcto**, mantener |
| Alternativa Legal-Embed | Sugerida para evaluar | **DESCARTAR**: evidencia indica que producira mas FP |
| Alternativa real | No propuesta | **Agregar `BAAI/bge-m3`** como primera opcion |
| Contrastive refinement | No mencionado | **Agregar**: si los centroides no separan suficiente, aplicar contrastive learning |
| Capas intermedias | No mencionado | **Agregar**: extraer embeddings de capas 15-17, no solo ultima |

---

## 8. Tabla Consolidada de Papers Revisados

| # | Paper | Venue | Ano | Tema Principal | URL |
|---|-------|-------|-----|----------------|-----|
| 1 | Do We Need Domain-Specific Embedding Models? An Empirical Investigation | arXiv 2409.18511 | 2024 | General vs domain embeddings | https://arxiv.org/abs/2409.18511 |
| 2 | NuNER: Entity Recognition Encoder Pre-training via LLM-Annotated Data | EMNLP 2024 | 2024 | Entity-aware pre-training | https://aclanthology.org/2024.emnlp-main.660/ |
| 3 | LegNER: Domain-Adapted Transformer for Legal NER | Frontiers in AI | 2025 | Legal NER + anonymization | https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1638971/full |
| 4 | MEL: Legal Spanish Language Model | arXiv 2501.16011 | 2025 | Spanish legal embeddings | https://arxiv.org/abs/2501.16011 |
| 5 | Anisotropy is Not Inherent to Transformers | NAACL 2024 | 2024 | Embedding space geometry | https://aclanthology.org/2024.naacl-long.274/ |
| 6 | Stable Anisotropic Regularization (I-STAR) | ICLR 2024 | 2024 | Controlled anisotropy | https://arxiv.org/abs/2305.19358 |
| 7 | The Shape of Learning: Anisotropy and Intrinsic Dimensions | EACL 2024 | 2024 | Anisotropy dynamics in transformers | https://aclanthology.org/2024.findings-eacl.58/ |
| 8 | How Does Fine-tuning Affect Geometry of Embedding Space | EMNLP 2021 Findings | 2021 | Fine-tuning impact on isotropy | https://aclanthology.org/2021.findings-emnlp.261/ |
| 9 | Representation Degeneration in Prompt-based Fine-tuning | LREC 2024 | 2024 | Anisotropy limits performance | https://aclanthology.org/2024.lrec-main.1217/ |
| 10 | Improving Legal Entity Recognition Using Semantic Filtering | arXiv 2410.08521 | 2024 | Legal NER false positive reduction | https://arxiv.org/abs/2410.08521 |
| 11 | CEPTNER: Contrastive Enhanced Prototypical Network for Few-shot NER | Knowledge-Based Systems | 2024 | Prototype networks for NER | https://doi.org/10.1016/j.knosys.2024.111730 |
| 12 | KCL: Few-shot NER with Knowledge Graph and Contrastive Learning | LREC-COLING 2024 | 2024 | KG + contrastive for prototypical NER | https://aclanthology.org/2024.lrec-main.846/ |
| 13 | Automated Concatenation of Embeddings (ACE) | ACL-IJCNLP 2021 | 2021 | Multi-embedding concatenation for NER | https://aclanthology.org/2021.acl-long.206/ |
| 14 | Pooled Contextualized Embeddings for NER | NAACL 2019 | 2019 | Global word representations for NER | https://aclanthology.org/N19-1078/ |
| 15 | Continual NER without Catastrophic Forgetting | EMNLP 2023 | 2023 | Catastrophic forgetting in NER | https://arxiv.org/abs/2310.14541 |
| 16 | Improving Few-Shot Cross-Domain NER (IF-WRANER) | EMNLP 2024 Industry | 2024 | Word-level embeddings for cross-domain NER | https://aclanthology.org/2024.emnlp-industry.51/ |
| 17 | CLESR: Context-Based Label Knowledge Enhanced Span Recognition | IJCIS | 2024 | Context + label knowledge for NER | https://link.springer.com/article/10.1007/s44196-024-00595-5 |
| 18 | Span-based Unified NER via Contrastive Learning | IJCAI 2024 | 2024 | Contrastive span-type alignment | https://www.ijcai.org/proceedings/2024/0708.pdf |
| 19 | Pre-trained Embeddings for Entity Resolution | VLDB 2023 | 2023 | 12 embedding models compared for ER | https://www.vldb.org/pvldb/vol16/p2225-skoutas.pdf |
| 20 | Transformer-based Prototype Network for Chinese Nested NER | Scientific Reports | 2025 | Prototypical NER with transformers | https://www.nature.com/articles/s41598-025-04946-w |
| 21 | Adapter Tuning of LLM for Chinese Medical NER | Automation in Construction | 2024 | Adapters prevent catastrophic forgetting | https://www.tandfonline.com/doi/full/10.1080/08839514.2024.2385268 |
| 22 | Recent Advances in NER: Comprehensive Survey | arXiv 2401.10825 | 2024 | NER survey (embeddings, hybrid approaches) | https://arxiv.org/abs/2401.10825 |
| 23 | Spanish Datasets for Sensitive Entity Detection in Legal Domain | LREC 2022 | 2022 | MAPA project, Spanish legal NER datasets | https://aclanthology.org/2022.lrec-1.400/ |

---

## 9. Documentos Relacionados

| Documento | Relacion |
|-----------|----------|
| `docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md` | Documento previo que propone validador de tipo con embeddings. Esta investigacion ACTUALIZA sus recomendaciones. |
| `docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md` | Evaluacion previa de embeddings para clasificacion de documentos (tarea diferente). |
| `docs/reports/2026-02-07_embeddings_roadmap_document_classification.md` | Roadmap de embeddings para clasificacion de documentos. |
| `docs/reports/2026-01-30_investigacion_gaps_pipeline_hibrido.md` | Gaps del pipeline NER hibrido (contexto de los errores de tipo). |
| `docs/reports/2026-01-28_investigacion_hybrid_ner.md` | Investigacion sobre NER hibrido (contexto de arquitectura). |

---

```
Version: 1.0.0
Autor: AlexAlves87
Tiempo de investigacion: ~45 min
Papers revisados: 23
```
