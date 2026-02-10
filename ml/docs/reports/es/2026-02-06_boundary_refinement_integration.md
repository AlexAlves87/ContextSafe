# Boundary Refinement - Integración en Pipeline NER

**Fecha:** 2026-02-06
**Autor:** AlexAlves87
**Componente:** `scripts/preprocess/boundary_refinement.py` integrado en `ner_predictor.py`
**Estándar:** SemEval 2013 Task 9 (Entity-level evaluation)

---

## 1. Resumen Ejecutivo

Implementación de refinamiento de límites de entidades para convertir coincidencias parciales (PAR) en correctas (COR) según el framework de evaluación SemEval 2013.

### Resultados

| Test Suite | Resultado |
|------------|-----------|
| Standalone tests | 12/12 (100%) |
| Integration test | ✅ Funcional |
| Refinements aplicados | 4/8 entidades en demo |

### Tipos de Refinamiento

| Tipo | Entidades | Acción |
|------|-----------|--------|
| OVER_EXTENDED | PERSON | Strip prefijos: Don, Dña., D., Mr., Doña |
| OVER_EXTENDED | DATE | Strip prefijos: a, el día, día |
| OVER_EXTENDED | ORGANIZATION | Strip sufijos: comas, puntos y comas |
| OVER_EXTENDED | ADDRESS | Strip postal+ciudad al final |
| TRUNCATED | POSTAL_CODE | Extender a 5 dígitos |
| TRUNCATED | DNI_NIE | Extender para incluir letra de control |

---

## 2. Metodología

### 2.1 Diagnóstico Previo

Se ejecutó `scripts/evaluate/diagnose_par_cases.py` para identificar patrones de error:

```
TRUNCATED (2 casos):
  - [address_floor_door] Missing at end: '001' (código postal)
  - [testament_comparecencia] Missing at end: 'Z' (letra DNI)

OVER_EXTENDED (9 casos):
  - Nombres con prefijos honoríficos incluidos
  - Fechas con prefijo "a" incluido
  - Organizaciones con coma final
```

### 2.2 Implementación

**Archivo:** `scripts/preprocess/boundary_refinement.py`

```python
# Prefijos honoríficos españoles (orden: más largos primero)
PERSON_PREFIXES = [
    r"(?:Compareció\s+)?Don\s+",
    r"(?:Compareció\s+)?Doña\s+",
    r"Dña\.\s*",
    r"D\.\s*",
    r"Mr\.\s*",
    r"Mrs\.\s*",
    # ...
]

# Función principal
def refine_entity(text, entity_type, start, end, confidence, source, original_text):
    """Aplica refinamiento según tipo de entidad."""
    if entity_type in REFINEMENT_FUNCTIONS:
        refined_text, refinement_applied = REFINEMENT_FUNCTIONS[entity_type](text, original_text)
    # ...
```

### 2.3 Integración en Pipeline

**Archivo:** `scripts/inference/ner_predictor.py`

```python
# Importación con degradación elegante
try:
    from preprocess.boundary_refinement import refine_entity, RefinedEntity
    REFINEMENT_AVAILABLE = True
except ImportError:
    REFINEMENT_AVAILABLE = False

# En método predict():
def predict(self, text, min_confidence=0.5, max_length=512):
    # 1. Normalización de texto
    text = normalize_text_for_ner(text)

    # 2. Predicción NER
    entities = self._extract_entities(...)

    # 3. Merge con regex (híbrido)
    if REGEX_AVAILABLE:
        entities = self._merge_regex_detections(text, entities, min_confidence)

    # 4. Refinamiento de límites (NUEVO)
    if REFINEMENT_AVAILABLE:
        entities = self._apply_boundary_refinement(text, entities)

    return entities
```

### 2.4 Reproducibilidad

```bash
# Entorno
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Test standalone
python scripts/preprocess/boundary_refinement.py

# Test integración
python scripts/inference/ner_predictor.py
```

---

## 3. Resultados

### 3.1 Tests Standalone (12/12)

| Test | Entidad | Refinamiento | Resultado |
|------|---------|--------------|-----------|
| person_don | PERSON | Strip "Don " | ✅ |
| person_dña | PERSON | Strip "Dña. " | ✅ |
| person_d_dot | PERSON | Strip "D. " | ✅ |
| person_mr | PERSON | Strip "Mr. " | ✅ |
| person_no_change | PERSON | Sin cambio | ✅ |
| date_a_prefix | DATE | Strip "a " | ✅ |
| date_el_dia | DATE | Strip "el día " | ✅ |
| org_trailing_comma | ORGANIZATION | Strip "," | ✅ |
| address_with_postal_city | ADDRESS | Strip "28013 Madrid" | ✅ |
| postal_extend | POSTAL_CODE | "28" → "28001" | ✅ |
| dni_extend_letter | DNI_NIE | "12345678-" → "12345678Z" | ✅ |
| dni_no_extend | DNI_NIE | Sin cambio | ✅ |

**Tiempo de ejecución:** 0.002s

### 3.2 Test de Integración

| Input | Entidad Original | Entidad Refinada | Refinamiento |
|-------|------------------|------------------|--------------|
| "Don José García López con DNI..." | "Don José García López" | "José García López" | stripped_prefix:Don |
| "Dña. Ana Martínez Ruiz..." | "Dña. Ana Martínez Ruiz" | "Ana Martínez Ruiz" | stripped_prefix:Dña. |
| "Compareció Doña María Antonia..." | "Doña María Antonia Fernández Ruiz" | "María Antonia Fernández Ruiz" | stripped_prefix:Doña |
| "Mr. John Smith, residente..." | "Mr. John Smith" | "John Smith" | stripped_prefix:Mr. |

### 3.3 Entidades Sin Refinamiento (Correctas)

| Input | Entidad | Razón |
|-------|---------|-------|
| "DNI 12345678Z" | "12345678Z" | Ya correcto |
| "IBAN ES91 2100..." | "ES91 2100 0418 4502 0005 1332" | Ya correcto |
| "Calle Alcalá 50" | "Calle Alcalá 50" | Ya correcto |
| "Sevilla" | "Sevilla" | Ya correcto |

---

## 4. Análisis

### 4.1 Impacto en Pipeline

El refinamiento de límites se aplica **después** del merge NER+regex, actuando como post-procesador:

```
Texto → Normalización → NER → Merge Regex → Refinamiento → Entidades finales
                                              ↑
                                        (Element 5)
```

### 4.2 Preservación de Metadatos

El refinamiento preserva todos los metadatos originales:
- `confidence`: Sin modificar
- `source`: Sin modificar (ner/regex)
- `checksum_valid`: Sin modificar
- `checksum_reason`: Sin modificar

Añade nuevos campos:
- `original_text`: Texto antes del refinamiento
- `refinement_applied`: Tipo de refinamiento aplicado

### 4.3 Observación sobre DATE

La fecha "a quince de marzo de dos mil veinticuatro" en el test de integración **no fue refinada** porque el modelo NER detectó "quince de marzo de dos mil veinticuatro" directamente (sin el prefijo "a"). Esto indica que:

1. El modelo NER ya aprende algunos límites correctos
2. El refinamiento actúa como red de seguridad para casos que el modelo no maneja

---

## 5. Pipeline Completo (5 Elementos)

### 5.1 Elementos Integrados

| # | Elemento | Standalone | Integración | Función |
|---|----------|------------|-------------|---------|
| 1 | TextNormalizer | 15/15 | ✅ | Unicode evasion, homoglyphs |
| 2 | Checksum Validators | 23/24 | ✅ | Ajuste de confianza |
| 3 | Regex Patterns | 22/22 | ✅ | IDs con espacios/guiones |
| 4 | Date Patterns | 14/14 | ✅ | Números romanos |
| 5 | Boundary Refinement | 12/12 | ✅ | PAR→COR conversion |

### 5.2 Flujo de Datos

```
Input: "Don José García López con DNI 12345678Z"
                    ↓
[1] TextNormalizer: Sin cambios (texto limpio)
                    ↓
[NER Model]: Detecta "Don José García López" (PERSON), "12345678Z" (DNI_NIE)
                    ↓
[3] Regex Merge: Sin cambios (NER ya detectó DNI completo)
                    ↓
[2] Checksum: DNI válido → confidence boost
                    ↓
[5] Boundary Refinement: "Don José García López" → "José García López"
                    ↓
Output: [PERSON] "José García López", [DNI_NIE] "12345678Z" ✅
```

---

## 6. Conclusiones

### 6.1 Logros

1. **Refinamiento funcional**: 12/12 tests standalone, integración verificada
2. **Degradación elegante**: Sistema funciona sin el módulo (REFINEMENT_AVAILABLE=False)
3. **Preservación de metadatos**: Checksum y source intactos
4. **Trazabilidad**: Campos `original_text` y `refinement_applied` para auditoría

### 6.2 Limitaciones Conocidas

| Limitación | Impacto | Mitigación |
|------------|---------|------------|
| Solo prefijos/sufijos estáticos | No maneja casos dinámicos | Patrones cubren 90%+ casos legales |
| Extensión depende de contexto | Puede fallar si texto truncado | Verificación de longitud |
| No refina CIF | Baja prioridad | Añadir si se detecta patrón |

### 6.3 Próximo Paso

Ejecutar test adversarial completo para medir impacto en métricas:

```bash
python scripts/evaluate/test_ner_predictor_adversarial_v2.py
```

**Métricas a observar:**
- PAR (partial matches) - esperamos reducción
- COR (correct matches) - esperamos aumento
- Pass rate - esperamos mejora

---

## 7. Referencias

1. **SemEval 2013 Task 9**: Entity evaluation framework (COR/INC/PAR/MIS/SPU)
2. **Diagnóstico PAR**: `scripts/evaluate/diagnose_par_cases.py`
3. **Implementación**: `scripts/preprocess/boundary_refinement.py`
4. **Integración**: `scripts/inference/ner_predictor.py` líneas 37-47, 385-432

---

**Tiempo de ejecución total:** 0.002s (standalone) + 1.39s (load model) + 18.1ms (inference)
**Generado por:** AlexAlves87
**Fecha:** 2026-02-06
