# Auditoria Subagente 3 — Calidad de Tests, Cobertura y Tipos

Archivos principales auditados:
- `tests/`
- `src/contextsafe/domain/shared/types/result.py`
- `src/contextsafe/domain/shared/value_objects/`
- `pyproject.toml` (seccion mypy)

---

## 1. Cobertura de Tests

### 1.1 Modulos criticos del pipeline NLP SIN tests unitarios

Los siguientes archivos fuente no tienen tests unitarios dedicados:

| Archivo fuente | Lineas | Severidad | Riesgo |
|----------------|--------|-----------|--------|
| `roberta_ner_adapter.py` | ~200 | CRITICO | Modelo principal de NER |
| `spacy_adapter.py` | ~150 | CRITICO | Tokenizacion ground-truth |
| `presidio_adapter.py` | ~150 | CRITICO | Reconocimiento de patrones estructurados |
| `regex_adapter.py` | ~200 | ALTO | Regex espanolas especificas |
| `merge/snapping.py` | 114 | CRITICO | Alineacion BPE->spaCy |
| `strategies/masking.py` | 97 | ALTO | Estrategia BASIC |
| `strategies/pseudonym.py` | 90 | ALTO | Estrategia INTERMEDIATE |
| `strategies/synthetic.py` | 829 | CRITICO | Estrategia ADVANCED + LLM |

### 1.2 `test_anonymization_service.py` no cubre los 3 niveles

Solo prueba:
- Alias generation (prefixes, counters, case-insensitive)
- Text replacement basica (single/multiple entity)
- Glossary management

NO prueba:
- BASIC (masking con asteriscos)
- INTERMEDIATE (pseudonimos via PseudonymStrategy)
- ADVANCED (synthetic data + date shifting + LLM fallback)
- `_remove_overlapping_detections`
- `_glossary_consistency_scan` real
- Cross-category alias reuse

### 1.3 Merge de spans solapados

NO existe test que cubra:
- `_group_overlapping_detections()` con IoU parcial
- `_resolve_by_voting()` con 3+ detectores discrepando
- `_remove_overlapping_detections()` con categorias de distinto riesgo GDPR

### 1.4 Tests de integracion rotos

- `tests/integration/test_documents_api.py` usa `TestClient` con app FastAPI real.
- Devuelve 404 en `/api/v1/projects`. Indica que routers no estan incluidos o la app requiere inicializacion que no ocurre en test.
- **12 errores de setup**. Todos los tests de integracion fallan.

---

## 2. Calidad de Tests PBT (`tests/pbt/`)

### 2.1 Estrategias adversariales

| Aspecto | Estado |
|---------|--------|
| Entidades hardcodeadas | MEDIO — 23 ejemplos fijos; no genera DNI/IBAN validos |
| Texto filler | MEDIO — no incluye saltos de linea ni OCR noise real |
| Dirty text | MEDIO — `dirty_text_gen()` limitada a samples fijos |

### 2.2 Idempotencia

NO se testea idempotencia del pipeline COMPLETO (anonimizar 2 veces con NER real). Riesgo: segunda pasada detecta aliases como nuevas entidades.

### 2.3 Texto anonimizado no contiene spans detectados

`test_no_pii_text_in_anonymized_output` usa reemplazo simulado manual, NO el pipeline real.

### 2.4 Offsets de reemplazo

NO hay test PBT que verifique:
- Que offsets de reemplazo no se solapan
- Que no quedan gaps
- Que suma de replacements cubre todo el texto

### 2.5 Invariantes de dominio

Los dataclasses son `frozen=True, slots=True` (bien). NO hay tests que intenten mutarlas via `object.__setattr__` o reflexion.

---

## 3. Tipos y Contratos

### 3.1 `composite_adapter.py` — Tipos de retorno

`detect_entities() -> list[NerDetection]` es coherente. Problema en `_apply_type_validation()` (l. ~1265):

```python
if isinstance(category_result, Ok):
    det = det.with_category(category_result.value)
```

Inconsistente con patron `.is_ok()` del resto del codebase.

### 3.2 `result.py` — Uso no exhaustivo en tests

`tests/unit/infrastructure/test_anonymization_service.py:170`:

```python
span = span_result.value  # Extract from Ok
```

Sin verificar `is_ok()`. Si `TextSpan.create()` falla, el test explota en lugar de assert claro.

### 3.3 Optional sin verificacion de None

`composite_adapter.py` (l. 487-493):

```python
spacy_doc = None
if self._spacy_adapter:
    try:
        spacy_doc = await self._spacy_adapter.tokenize(text)
    except Exception:
        pass
```

`spacy_doc` puede ser None y luego se pasa a `snap_all_detections()`. `snap_all_detections` acepta `Any`, por lo que mypy no detecta el error.

### 3.4 cast() / # type: ignore

- `result.py:49`: `# type: ignore[return-value]` en `Ok.map_err`. Justificado.
- `snapping.py:24`: `if TYPE_CHECKING: pass`. Aceptable.
- `anonymization_adapter.py`: imports lazy para evitar circulares. Aceptable pero debilita verificacion estatica.

### 3.5 Problema de tipo en `_remove_overlapping_detections`

```python
d.category.value if hasattr(d.category, 'value') else str(d.category)
```

Uso de `hasattr` en lugar de tipos fuertes. Code smell.

---

## 4. Tests Faltantes Criticos

Ver archivo `09-missing-tests.md` para los 5 esqueletos completos.

Resumen:

| ID | Modulo | Severidad | Descripcion |
|---|---|---|---|
| TF-001 | `composite_adapter.py` | CRITICO | Merge de spans solapados con 3 detectores discrepantes |
| TF-002 | `merge/snapping.py` | CRITICO | Snapping de tokens BPE corrige corte de palabra |
| TF-003 | `anonymization_adapter.py` | CRITICO | `_remove_overlapping_detections` con prioridad GDPR |
| TF-004 | Pipeline completo | ALTO | Idempotencia completa (NER + Anonymize) |
| TF-005 | `strategies/synthetic.py` | CRITICO | Estrategia ADVANCED genera checksums INVALIDOS |

---

## 5. Configuracion de Test

### 5.1 pytest.ini_options

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    ...
]
```

`asyncio_mode = "auto"` con pytest-asyncio. Tests de integracion usan `TestClient` sincrono sobre app async (correcto).

### 5.2 Markers inconsistentes

| Marker | Declarado | Usado |
|--------|-----------|-------|
| `unit` | Si | No en tests/unit/ |
| `integration` | Si | No en tests/integration/ |
| `slow` | Si | No usado |

### 5.3 Coverage `fail_under = 80`

- `pytest-cov` NO esta instalado (`unrecognized arguments: --cov`).
- No hay forma de verificar el 80%.
- Estimacion: modulos como `roberta_ner_adapter`, `strategies/synthetic.py`, `api/routes/` tienen 0%.

### 5.4 Tests sincronos vs async

Tests de `test_anonymization_service.py` marcan `@pytest.mark.asyncio` pero muchos solo prueban logica sincrona. Correcto porque los metodos son `async`.

---

## Issues Especificas por Archivo

| Archivo | Linea | Severidad | Issue |
|---------|-------|-----------|-------|
| `tests/unit/infrastructure/test_anonymization_service.py` | 170 | ALTO | `span = span_result.value` sin `is_ok()` |
| `tests/unit/infrastructure/test_anonymization_service.py` | 39-315 | ALTO | NO cubre BASIC/INTERMEDIATE/ADVANCED |
| `tests/pbt/test_anonymization.py` | 592 | MEDIO | `assert text.lower() not in alias.value.lower()` falla con "Per" vs "Persona_1" |
| `tests/integration/test_documents_api.py` | 39 | CRITICO | API devuelve 404 en tests |
| `tests/conftest.py` | 48-75 | MEDIO | Fixtures mock son stubs vacios |
| `src/contextsafe/infrastructure/nlp/composite_adapter.py` | 461-468 | ALTO | `except Exception: pass` silencia fallos |
| `src/contextsafe/infrastructure/nlp/anonymization_adapter.py` | 450-452 | ALTO | Insercion de espacio post-alias crea dobles espacios |

---

## Recomendaciones de Fix Priorizadas

### Inmediatas (antes del proximo release)
1. Crear tests unitarios para `MaskingStrategy`, `PseudonymStrategy`, `SyntheticStrategy`.
2. Crear tests para `snap_to_tokens`.
3. Arreglar `test_homoglyph_text_handled` — cambiar asercion.
4. Arreglar tests de integracion o marcar como `@pytest.mark.skip`.
5. Instalar `pytest-cov` y ejecutar coverage report.

### Corto plazo (1-2 sprints)
6. Anadir test TF-001 y TF-003.
7. Anadir test de idempotencia completa (TF-004).
8. Revisar todos los `.value` directos sobre Result.
9. Anadir `@pytest.mark.unit` / `@pytest.mark.integration` consistentemente.

---

## Resumen Tests/Cobertura

| Severidad | Cantidad |
|-----------|----------|
| CRITICO | 1 |
| ALTO | 4 |
| MEDIO | 6 |
| BAJO | 5 |
