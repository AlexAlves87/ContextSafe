# Quick Wins

Issues de alta severidad y bajo esfuerzo de fix (< 1 hora cada uno).

---

## QW-1: Corregir regex telefono +34 compacto

- **Archivo:** `src/contextsafe/infrastructure/nlp/recognizers/spanish_phone.py`
- **Tiempo:** 2 minutos
- **Diff:**

```python
# Anadir despues de PHONE_INTERNATIONAL (l. 37):
Pattern(
    "PHONE_INTERNATIONAL_COMPACT",
    r"\b(\+34\d{9})\b",
    0.9,
),
```

---

## QW-2: No rechazar organizaciones con particulas

- **Archivo:** `src/contextsafe/infrastructure/nlp/recognizers/spanish_orgs.py`
- **Tiempo:** 5 minutos
- **Diff:** Reemplazar bloque l. 137-144 por:

```python
        clean_lower = clean.lower()
        words = clean_lower.split()
        false_count = sum(1 for w in words if w in self.FALSE_POSITIVE_WORDS)
        if false_count > len(words) // 2:
            return False
        if len(words) == 1 and words[0] in self.FALSE_POSITIVE_WORDS:
            return False
```

---

## QW-3: Eliminar `textContent` de respuesta GET

- **Archivo:** `src/contextsafe/api/routes/documents.py`
- **Tiempo:** 1 minuto
- **Diff:**

```python
# Reemplazar (l. 175):
"textContent": doc.content or "",
# Por:
"textContent": "",
```

---

## QW-4: Sanitizar errores WebSocket

- **Archivo:** `src/contextsafe/api/services/document_processor.py`
- **Tiempo:** 15 minutos
- **Diff:** Reemplazar bloque l. 273-279 por:

```python
    except Exception as e:
        logger.exception(f"Error processing document {document_id}: {e}")
        safe_message = "Processing failed. Please try again or contact support."
        session_manager.update_document(
            session_id, document_id,
            state="error",
            error=safe_message
        )
        await progress_handler.send_error(doc_uuid, safe_message)
```

---

## QW-5: Wrap spacy/presidio en run_in_executor

- **Archivo:** `spacy_adapter.py` y `presidio_adapter.py`
- **Tiempo:** 10 minutos
- **Diff spacy_adapter.py (l. 104):**

```python
        loop = asyncio.get_running_loop()
        doc = await loop.run_in_executor(None, self._nlp, text)
```

- **Diff presidio_adapter.py (l. 417):**

```python
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self._analyzer.analyze(
                text=text, language="es", score_threshold=min_confidence
            ),
        )
```

---

## QW-6: Anadir pytest-cov a dev-dependencies

- **Archivo:** `pyproject.toml`
- **Tiempo:** 2 minutos
- **Diff:** Anadir bajo `[tool.poetry.group.dev.dependencies]`:

```toml
pytest-cov = "^5.0"
```

---

## QW-7: Evitar inyeccion PowerShell

- **Archivo:** `src/contextsafe/infrastructure/nlp/strategies/synthetic.py`
- **Tiempo:** 20 minutos
- **Diff:** Ver `05-fixes-critical-high.md` seccion 5.9 (pasa JSON por stdin en lugar de interpolar en string).

---

## QW-8: Anadir try/except en deteccion de imagenes DOCX

- **Archivo:** `src/contextsafe/infrastructure/document_processing/docx_extractor.py`
- **Tiempo:** 5 minutos
- **Diff:**

```python
# Reemplazar (l. 69-72):
for rel in doc.part.rels.values():
    if "image" in rel.target_ref:
        has_images = True
        break

# Por:
try:
    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            has_images = True
            break
except Exception:
    has_images = False
```

---

## QW-9: Corregir `datetime.utcnow()` deprecado

- **Archivo:** `src/contextsafe/api/routes/documents.py` (l. 132), `api/session_manager.py` (l. 79)
- **Tiempo:** 3 minutos
- **Diff:**

```python
# Reemplazar:
from datetime import datetime
datetime.utcnow()
# Por:
from datetime import datetime, timezone
datetime.now(timezone.utc)
```

---

## QW-10: Sincronizar version CLI con pyproject.toml

- **Archivo:** `src/contextsafe/cli.py` (l. 19)
- **Tiempo:** 1 minuto
- **Diff:**

```python
# Reemplazar:
version="0.1.0",
# Por (leer dinamicamente o hardcodear 4.0.0):
version="4.0.0",
```

---

*Aplicar estos 10 quick wins reduce drasticamente la superficie de riesgo en menos de 1 hora de trabajo.*
