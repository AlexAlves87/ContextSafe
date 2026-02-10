# Investigación: Estándares Académicos para Evaluación de NER

**Fecha:** 2026-01-28
**Autor:** AlexAlves87
**Tipo:** Revisión de Literatura Académica
**Estado:** Completado

---

## 1. Resumen Ejecutivo

Esta investigación documenta los estándares académicos para evaluación de sistemas NER, con énfasis en:
1. Métricas entity-level (SemEval 2013 Task 9)
2. Evaluación adversarial (RockNER, NoiseBench)
3. Frameworks de evaluación (seqeval, nervaluate)
4. Best practices para robustness testing

### Hallazgos Principales

| Hallazgo | Fuente | Impacto |
|----------|--------|---------|
| 4 modos de evaluación: strict, exact, partial, type | SemEval 2013 | **CRÍTICO** |
| seqeval es el estándar de facto para entity-level F1 | CoNLL, HuggingFace | Alto |
| RockNER: entity-level + context-level perturbations | EMNLP 2021 | Alto |
| NoiseBench: ruido real >> ruido simulado en dificultad | EMNLP 2024 | Alto |
| nervaluate proporciona métricas más granulares que seqeval | MantisAI | Medio |

---

## 2. Metodología de Búsqueda

### 2.1 Fuentes Consultadas

| Fuente | Tipo | Año | Relevancia |
|--------|------|-----|------------|
| SemEval 2013 Task 9 | Shared Task | 2013 | Definición de métricas |
| RockNER (EMNLP 2021) | Paper ACL | 2021 | Evaluación adversarial |
| NoiseBench (EMNLP 2024) | Paper ACL | 2024 | Ruido realista |
| seqeval | Librería | 2018+ | Implementación estándar |
| nervaluate | Librería | 2020+ | Métricas extendidas |
| David Batista Blog | Tutorial | 2018 | Explicación detallada |

### 2.2 Criterios de Búsqueda

- "adversarial NER evaluation benchmark methodology"
- "NER robustness testing framework seqeval entity level"
- "SemEval 2013 task 9 entity level metrics"
- "RockNER adversarial NER EMNLP methodology"
- "NoiseBench NER evaluation realistic noise"

---

## 3. Estándares de Evaluación Entity-Level

### 3.1 SemEval 2013 Task 9: Los 4 Modos de Evaluación

**Fuente:** [Named-Entity evaluation metrics based on entity-level](https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/)

El estándar SemEval 2013 define **4 modos** de evaluación:

| Modo | Boundary | Type | Descripción |
|------|----------|------|-------------|
| **Strict** | Exacto | Exacto | Boundary Y type deben coincidir |
| **Exact** | Exacto | Ignorado | Solo boundary exacto |
| **Partial** | Overlap | Ignorado | Basta overlap parcial |
| **Type** | Overlap | Exacto | Overlap + type correcto |

#### 3.1.1 Definición de Métricas Base

| Métrica | Definición |
|---------|------------|
| **COR** (Correct) | Sistema y gold son idénticos |
| **INC** (Incorrect) | Sistema y gold no coinciden |
| **PAR** (Partial) | Sistema y gold tienen overlap parcial |
| **MIS** (Missing) | Gold no capturado por sistema (FN) |
| **SPU** (Spurious) | Sistema produce algo no en gold (FP) |
| **POS** (Possible) | COR + INC + PAR + MIS = total gold |
| **ACT** (Actual) | COR + INC + PAR + SPU = total sistema |

#### 3.1.2 Fórmulas de Cálculo

**Para modos exactos (strict, exact):**
```
Precision = COR / ACT
Recall = COR / POS
F1 = 2 * (P * R) / (P + R)
```

**Para modos parciales (partial, type):**
```
Precision = (COR + 0.5 × PAR) / ACT
Recall = (COR + 0.5 × PAR) / POS
F1 = 2 * (P * R) / (P + R)
```

### 3.2 seqeval: Implementación Estándar

**Fuente:** [seqeval GitHub](https://github.com/chakki-works/seqeval)

seqeval es el framework estándar para evaluación de sequence labeling, validado contra el script Perl `conlleval` de CoNLL-2000.

#### Características

| Feature | Descripción |
|---------|-------------|
| Formato | CoNLL (BIO/BIOES tags) |
| Métricas | Precision, Recall, F1 por tipo y overall |
| Modo default | Simula conlleval (lenient con B/I) |
| Modo strict | Solo matches exactos |

#### Uso Correcto

```python
from seqeval.metrics import classification_report, f1_score
from seqeval.scheme import IOB2

# Modo strict (recomendado para evaluación rigurosa)
f1 = f1_score(y_true, y_pred, mode='strict', scheme=IOB2)
report = classification_report(y_true, y_pred, mode='strict', scheme=IOB2)
```

**IMPORTANTE:** El modo default de seqeval es lenient. Para evaluación rigurosa, usar `mode='strict'`.

### 3.3 nervaluate: Métricas Extendidas

**Fuente:** [nervaluate GitHub](https://github.com/MantisAI/nervaluate)

nervaluate implementa los 4 modos de SemEval 2013 completos.

#### Ventajas sobre seqeval

| Aspecto | seqeval | nervaluate |
|---------|---------|------------|
| Modos | 2 (default, strict) | 4 (strict, exact, partial, type) |
| Granularidad | Por tipo de entidad | Por tipo + por escenario |
| Métricas | P/R/F1 | P/R/F1 + COR/INC/PAR/MIS/SPU |

#### Uso

```python
from nervaluate import Evaluator

evaluator = Evaluator(true_labels, pred_labels, tags=['PER', 'ORG', 'LOC'])
results, results_per_tag = evaluator.evaluate()

# Acceder a modo strict
strict_f1 = results['strict']['f1']

# Acceder a métricas detalladas
cor = results['strict']['correct']
inc = results['strict']['incorrect']
par = results['partial']['partial']
```

---

## 4. Evaluación Adversarial: Estándares Académicos

### 4.1 RockNER (EMNLP 2021)

**Fuente:** [RockNER - ACL Anthology](https://aclanthology.org/2021.emnlp-main.302/)

RockNER propone un framework sistemático para crear ejemplos adversariales naturales.

#### Taxonomía de Perturbaciones

| Nivel | Método | Descripción |
|-------|--------|-------------|
| **Entity-level** | Reemplazo Wikidata | Sustituir entidades por otras de la misma clase semántica |
| **Context-level** | BERT MLM | Generar sustituciones de palabras con LM |
| **Combinado** | Ambos | Aplicar ambos para máxima adversarialidad |

#### Benchmark OntoRock

- Derivado de OntoNotes
- Aplica perturbaciones sistemáticas
- Mide degradación de F1

#### Hallazgo Clave

> "Even the best model has a significant performance drop... models seem to memorize in-domain entity patterns instead of reasoning from the context."

### 4.2 NoiseBench (EMNLP 2024)

**Fuente:** [NoiseBench - ACL Anthology](https://aclanthology.org/2024.emnlp-main.1011/)

NoiseBench demuestra que el ruido simulado es **significativamente más fácil** que el ruido real.

#### Tipos de Ruido Real

| Tipo | Fuente | Descripción |
|------|--------|-------------|
| Expert errors | Anotadores expertos | Errores de fatiga, interpretación |
| Crowdsourcing | Amazon Turk, etc. | Errores de no-expertos |
| Automatic annotation | Regex, heurísticas | Errores sistemáticos |
| LLM errors | GPT, etc. | Alucinaciones, inconsistencias |

#### Hallazgo Clave

> "Real noise is significantly more challenging than simulated noise, and current state-of-the-art models for noise-robust learning fall far short of their theoretically achievable upper bound."

### 4.3 Taxonomía de Perturbaciones para NER

Basado en la literatura, las perturbaciones adversariales se clasifican en:

| Categoría | Ejemplos | Papers |
|-----------|----------|--------|
| **Character-level** | Typos, OCR errors, homoglyphs | RockNER, NoiseBench |
| **Token-level** | Sinónimos, inflexiones | RockNER |
| **Entity-level** | Reemplazo por entidades similares | RockNER |
| **Context-level** | Modificar contexto circundante | RockNER |
| **Format-level** | Espacios, puntuación, casing | NoiseBench |
| **Semantic-level** | Negaciones, ejemplos ficticios | Custom |

---

## 5. Revisión de Tests Actuales vs Estándares

### 5.1 Tests Adversariales Actuales

Nuestro script `test_ner_predictor_adversarial.py` tiene:

| Categoría | Tests | Cobertura |
|-----------|-------|-----------|
| edge_case | 9 | Condiciones límite |
| adversarial | 8 | Confusión semántica |
| ocr_corruption | 5 | Errores OCR |
| unicode_evasion | 3 | Evasión Unicode |
| real_world | 10 | Documentos reales |

### 5.2 Gaps Identificados

| Gap | Estándar | Estado Actual | Severidad |
|-----|----------|---------------|-----------|
| Modo strict vs default | seqeval strict | No especificado | **CRÍTICO** |
| 4 modos SemEval | nervaluate | Solo 1 modo | ALTO |
| Entity-level perturbations | RockNER | No sistemático | ALTO |
| Métricas COR/INC/PAR/MIS/SPU | SemEval 2013 | No reportadas | MEDIO |
| Ruido real vs simulado | NoiseBench | Solo simulado | MEDIO |
| Context-level perturbations | RockNER | Parcial | MEDIO |

### 5.3 Métricas Actuales vs Requeridas

| Métrica | Actual | Requerido | Gap |
|---------|--------|-----------|-----|
| F1 overall | ✅ | ✅ | OK |
| Precision/Recall | ✅ | ✅ | OK |
| F1 por tipo de entidad | ❌ | ✅ | **FALTA** |
| Modo strict | ❓ | ✅ | **VERIFICAR** |
| COR/INC/PAR/MIS/SPU | ❌ | ✅ | **FALTA** |
| 4 modos SemEval | ❌ | ✅ | **FALTA** |

---

## 6. Recomendaciones de Mejora

### 6.1 Prioridad CRÍTICA

1. **Verificar modo strict en seqeval**
   ```python
   # Cambiar de:
   f1 = f1_score(y_true, y_pred)
   # A:
   f1 = f1_score(y_true, y_pred, mode='strict', scheme=IOB2)
   ```

2. **Reportar métricas por tipo de entidad**
   ```python
   report = classification_report(y_true, y_pred, mode='strict')
   ```

### 6.2 Prioridad ALTA

3. **Implementar los 4 modos de SemEval**
   - Usar nervaluate en lugar de (o además de) seqeval
   - Reportar strict, exact, partial, type

4. **Añadir entity-level perturbations (RockNER style)**
   - Reemplazar nombres por otros nombres españoles
   - Reemplazar DNIs por otros DNIs válidos
   - Mantener contexto, cambiar entidad

### 6.3 Prioridad MEDIA

5. **Reportar COR/INC/PAR/MIS/SPU**
   - Permite análisis más fino de errores
   - Distingue entre boundary errors y type errors

6. **Añadir context-level perturbations**
   - Modificar verbos/adjetivos circundantes
   - Usar BERT/spaCy para sustituciones naturales

---

## 7. Checklist de Evaluación Académica

### 7.1 Antes de Reportar Resultados

- [ ] Especificar modo de evaluación (strict/default)
- [ ] Usar formato CoNLL estándar (BIO/BIOES)
- [ ] Reportar F1, Precision, Recall
- [ ] Reportar métricas por tipo de entidad
- [ ] Documentar versión de seqeval/nervaluate usado
- [ ] Incluir intervalos de confianza si hay varianza

### 7.2 Para Evaluación Adversarial

- [ ] Categorizar perturbaciones (character, token, entity, context)
- [ ] Medir degradación relativa (F1_clean - F1_adversarial)
- [ ] Reportar pass rate por categoría de dificultad
- [ ] Incluir análisis de errores con ejemplos
- [ ] Comparar con baseline (modelo sin modificar)

### 7.3 Para Publicación/Documentación

- [ ] Describir metodología reproducible
- [ ] Publicar dataset de test (o generador)
- [ ] Reportar tiempo de ejecución
- [ ] Incluir análisis estadístico si aplica

---

## 8. Conclusiones

### 8.1 Acciones Inmediatas

1. **Revisar script adversarial** para verificar modo strict
2. **Añadir nervaluate** para métricas completas
3. **Reorganizar tests** según taxonomía RockNER

### 8.2 Impacto en Resultados Actuales

Los resultados actuales (F1=0.784, 54.3% pass rate) podrían cambiar si:
- El modo no era strict (resultados serían menores en strict)
- Las métricas por tipo revelan debilidades específicas
- Los 4 modos muestran diferente comportamiento en boundary vs type

---

## 9. Referencias

### Papers Académicos

1. **RockNER: A Simple Method to Create Adversarial Examples for Evaluating the Robustness of Named Entity Recognition Models**
   - Lin et al., EMNLP 2021
   - URL: https://aclanthology.org/2021.emnlp-main.302/

2. **NoiseBench: Benchmarking the Impact of Real Label Noise on Named Entity Recognition**
   - Merdjanovska et al., EMNLP 2024
   - URL: https://aclanthology.org/2024.emnlp-main.1011/

3. **SemEval-2013 Task 9: Extraction of Drug-Drug Interactions from Biomedical Texts**
   - Segura-Bedmar et al., SemEval 2013
   - Definición de métricas entity-level

### Herramientas y Librerías

4. **seqeval**
   - URL: https://github.com/chakki-works/seqeval

5. **nervaluate**
   - URL: https://github.com/MantisAI/nervaluate

6. **Named-Entity Evaluation Metrics Based on Entity-Level**
   - David Batista, 2018
   - URL: https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/

---

**Tiempo de investigación:** 45 min
**Generado por:** AlexAlves87
**Fecha:** 2026-01-28
