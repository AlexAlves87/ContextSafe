# Plan de Commits Atomicos — ContextSafe Remediacion

> **Objetivo:** Dividir los ~40 issues en commits que (1) no rompan nada aislados, (2) incluyan sus tests, (3) puedan subirse paulatinamente a produccion.

---

## Leyenda

| Simbolo | Significado |
|---------|-------------|
| `F` | Fix de codigo de produccion |
| `T` | Commit de solo tests o test-fix (no toca produccion) |
| `FT` | Fix + Test en el mismo commit |
| `->` | Dependencia (el commit de la derecha necesita el de la izquierda) |
| `{ }` | Grupo atomico obligatorio (commits que deben ir juntos o en orden estricto) |

---

## FASE 1: Baseline de Tests (7 commits)

Commits que solo tocan `tests/` o corrigen tests existentes. Pueden subirse primero sin riesgo.

### T01 `test(nlp): snapping BPE corrige corte de palabra (TF-002)`
- **Archivos:** `tests/unit/infrastructure/nlp/merge/test_snapping.py`
- **Razon:** Mock puro. No toca produccion.

### T02 `test(nlp): synthetic DNI genera checksum invalido (TF-005)`
- **Archivos:** `tests/unit/infrastructure/nlp/strategies/test_synthetic.py`
- **Razon:** Test de funcion existente `generate_invalid_dni`.

### T03 `test(nlp): GDPR priority en overlap de anonimizacion (TF-003)`
- **Archivos:** `tests/unit/infrastructure/nlp/test_anonymization_adapter.py`
- **Razon:** Usa `InMemoryAnonymizationAdapter` existente.

### T04 `test(nlp): voting 3-way discrepancy roberta/spacy/regex (TF-001)`
- **Archivos:** `tests/unit/infrastructure/nlp/test_composite_adapter_voting.py`
- **Razon:** Requiere que `_merge_detections` sea accesible. Si es privado, incluir un mini-refactor de visibilidad en este mismo commit (sin cambiar logica).

### T05 `test(nlp): cobertura de MaskingStrategy y PseudonymStrategy`
- **Archivos:** `tests/unit/infrastructure/nlp/strategies/test_masking.py`, `test_pseudonym.py`
- **Razon:** Tests para codigo existente sin cobertura.

### T06 `test(pbt): arreglar asercion test_homoglyph_text_handled`
- **Archivos:** `tests/pbt/test_anonymization.py` (l. 592)
- **Razon:** Cambia `assert text.lower() not in alias.value.lower()` por una asercion que no falle cuando el nombre de la categoria contiene el substring (ej. "Per" en "Persona_1").

### T07 `chore(tests): anadir markers pytest y poetry install instrucciones`
- **Archivos:** `tests/unit/**/*.py`, `tests/integration/**/*.py`
- **Razon:** Anade `@pytest.mark.unit` y `@pytest.mark.integration`. `pytest-cov` ya esta en `pyproject.toml` l.86; este commit NO toca pyproject.toml, solo documenta/instala.

---

## FASE 2: Seguridad Rapida (4 commits)

Reducen la superficie de riesgo inmediatamente.

### F01 `fix(api): eliminar textContent de respuesta GET /documents/{id}`
- **Archivos:** `src/contextsafe/api/routes/documents.py` (l. 175)
- **Diff:**
```python
- "textContent": doc.content or "",
+ "textContent": "",
```
- **Test:** Assert `response.json()["textContent"] == ""`.

### F02 `fix(api): sanitizar errores WebSocket para no filtrar PII`
- **Archivos:** `src/contextsafe/api/services/document_processor.py` (l. 273-279)
- **Diff:**
```python
    except Exception as e:
        logger.exception(f"Error processing document {document_id}: {e}")
        safe_message = "Processing failed. Please try again."
        session_manager.update_document(
            session_id, document_id,
            state="error", error=safe_message
        )
        await progress_handler.send_error(doc_uuid, safe_message)
```
- **Test:** Verificar que `progress_handler.send_error` recibe mensaje generico.

### F03 `fix(api): usar mensaje estatico para DomainError en handler`
- **Archivos:** `src/contextsafe/api/middleware/error_handler.py` (l. 68)
- **Diff:**
```python
- detail=str(exc),
+ detail="A domain validation error occurred.",
```
- **Test:** Mock DomainError con texto "Invalid: Juan Garcia" y verificar que la respuesta no lo contiene.

### F04 `fix(api): CORS fuerza allow_origins desde env en produccion`
- **Archivos:** `src/contextsafe/api/middleware/cors.py` (l. 33-37)
- **Diff:**
```python
    if allow_origins is None:
        if os.environ.get("APP_ENV") == "production":
            allow_origins = os.environ.get(
                "CONTEXTSAFE_CORS_ORIGINS", ""
            ).split(",")
            allow_credentials = False
        else:
            allow_origins = [
                "http://localhost:5173",
                "http://localhost:3000",
            ]
```
- **Test:** Simular `APP_ENV=production`, verificar que defaults localhost se rechazan.

---

## FASE 3: Reconocedores (4 commits)

Fixes independientes en recognizers.

### F11 `fix(nlp): spanish_orgs permite particulas sin rechazar orgs legitimas`
- **Archivos:** `src/contextsafe/infrastructure/nlp/recognizers/spanish_orgs.py` (l. 137-144)
- **Diff:**
```python
        clean_lower = clean.lower()
        words = clean_lower.split()
        false_count = sum(1 for w in words if w in self.FALSE_POSITIVE_WORDS)
        if false_count > len(words) // 2:
            return False
        if len(words) == 1 and words[0] in self.FALSE_POSITIVE_WORDS:
            return False
```
- **Test:** `"Banco de Espana S.A."` -> `validate_result` debe devolver `True`.

### F12 `fix(nlp): regex telefono +34 con boundary correcto`
- **Archivos:** `src/contextsafe/infrastructure/nlp/recognizers/spanish_phone.py`
- **Diff:**
```python
# Reemplazar PHONE_INTERNATIONAL y PHONE_INTERNATIONAL_00:
Pattern(
    "PHONE_INTERNATIONAL",
    r"(?<![+\d])(\+34[\s\-.]?\d{3}[\s\-.]?\d{3}[\s\-.]?\d{3})(?!\d)",
    0.9,
),
Pattern(
    "PHONE_INTERNATIONAL_00",
    r"(?<![\d])(0034[\s\-.]?\d{3}[\s\-.]?\d{3}[\s\-.]?\d{3})(?!\d)",
    0.85,
),
```
- **Test:** `+34612345678`, `+34 612 345 678`, `0034612345678` deben detectarse. `"abc+34612345678"` NO debe detectar `bc+34...`.
- **Nota:** El fix anterior (`\b`) estaba roto porque `+` es non-word char.

### F13 `fix(nlp): validacion basica de formato CIF`
- **Archivos:** `src/contextsafe/infrastructure/nlp/recognizers/spanish_id.py`
- **Diff:**
```python
    def validate_result(self, pattern_text: str) -> bool:
        cif = pattern_text.strip().upper().replace("-", "")
        if len(cif) != 9:
            return False
        letter = cif[0]
        digits = cif[1:8]
        if not digits.isdigit():
            return False
        if letter not in "ABCDEFGHJNPQRSUVW":
            return False
        # TODO: anadir algoritmo completo de control CIF
        return True
```
- **Test:** `A00000000` debe rechazarse (formato invalido).

### F14 `fix(nlp): regex nombres con titulo permiten particulas`
- **Archivos:** `src/contextsafe/infrastructure/nlp/recognizers/spanish_names.py`
- **Diff:** Modificar patterns `NAME_WITH_TITLE_D`, `NAME_WITH_TITLE_DON`, etc. para usar conector existente:
```python
NAME_WORD = r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+"
CONNECTOR = r"(?:de\s+la\s+|de\s+los\s+|de\s+las\s+|del\s+|de\s+)?"
NAME_WORD_WITH_CONNECTOR = rf"{NAME_WORD}(?:\s+{CONNECTOR}{NAME_WORD})*"
```
- **Test:** `"D. Juan de la Cruz"` debe matchear.

---

## FASE 4: Infraestructura (7 commits)

Resiliencia y estabilidad.

### F07 `fix(nlp): envolver spacy_adapter en run_in_executor`
- **Archivos:** `src/contextsafe/infrastructure/nlp/spacy_adapter.py` (l. 104)
- **Diff:**
```python
- doc = self._nlp(text)
+ loop = asyncio.get_running_loop()
+ doc = await loop.run_in_executor(None, self._nlp, text)
```
- **Test:** Verificar que `detect_entities` no bloquea event loop.

### F08 `fix(nlp): envolver presidio_adapter en run_in_executor`
- **Archivos:** `src/contextsafe/infrastructure/nlp/presidio_adapter.py` (l. 417)
- **Diff:**
```python
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self._analyzer.analyze(
                text=text, language="es", score_threshold=min_confidence
            ),
        )
```

### F09 `fix(nlp): evitar inyeccion PowerShell via stdin`
- **Archivos:** `src/contextsafe/infrastructure/nlp/strategies/synthetic.py` (l. 646-659)
- **Diff:** Reemplazar interpolacion por `input=` en `subprocess.run`:
```python
        ps_command = """
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$body = $input | Out-String
$response = Invoke-RestMethod -Uri 'http://localhost:11434/api/generate' -Method Post -Body $body -ContentType 'application/json; charset=utf-8'
$response.response
"""
        result = subprocess.run(
            ["powershell.exe", "-Command", ps_command],
            input=body_json.encode("utf-8"),
            capture_output=True,
            timeout=self._timeout,
        )
```
- **Severidad:** MEDIO (edge case por here-strings `@'...'@`).

### F10 `fix(nlp): delimitadores XML y validacion de entidades LLM`
- **Archivos:** `src/contextsafe/infrastructure/llm/ollama_ner_adapter.py`
- **Diff:**
```python
prompt = f"""Analyze the following document and extract entities.
<document>
{text}
</document>

Return only entities found in the document."""

# Despues del parsing:
for ent in parsed_entities:
    if text[ent["start"]:ent["end"]] != ent["text"]:
        continue
```

### F15 `fix(docproc): try/except en deteccion de imagenes DOCX`
- **Archivos:** `src/contextsafe/infrastructure/document_processing/docx_extractor.py` (l. 69-72)
- **Diff:**
```python
- for rel in doc.part.rels.values():
-     if "image" in rel.target_ref:
-         has_images = True
-         break
+ try:
+     for rel in doc.part.rels.values():
+         if "image" in rel.target_ref:
+             has_images = True
+             break
+ except Exception:
+     has_images = False
```

### F05 `fix(api): reemplazar datetime.utcnow() por now(timezone.utc)`
- **Archivos:** `src/contextsafe/api/routes/documents.py`, `src/contextsafe/api/session_manager.py`
- **Diff:**
```python
- from datetime import datetime
- datetime.utcnow()
+ from datetime import datetime, timezone
+ datetime.now(timezone.utc)
```

### F06 `fix(cli): sincronizar version con pyproject.toml`
- **Archivos:** `src/contextsafe/cli.py` (l. 19)
- **Diff:**
```python
- version="0.1.0",
+ version="4.0.0",
```

---

## FASE 5: Offset Mapping y Glossary Scan (3 commits)

### A1 `feat(nlp): TextNormalizer devuelve OffsetMapping con tracking de offsets`
- **Archivos:** `src/contextsafe/infrastructure/nlp/text_normalizer.py`, `src/contextsafe/infrastructure/text_processing/offset_tracker.py`
- **Nota:** Crea `normalize_with_mapping()`. No cambia comportamiento de `normalize()`.
- **Diff:**
```python
    def normalize(self, text: str) -> str:
        return self.normalize_with_mapping(text).normalized_text

    def normalize_with_mapping(self, text: str) -> OffsetMapping:
        if not text:
            return OffsetMapping.identity(text)
        tracker = OffsetTracker(text)
        for i, ch in enumerate(text):
            if ZERO_WIDTH_PATTERN.match(ch):
                tracker.skip_char(i)
                continue
            nfkc = unicodedata.normalize('NFKC', ch)
            nfkc = ''.join(HOMOGLYPHS.get(c, c) for c in nfkc)
            if '\u00ad' in nfkc:
                nfkc = nfkc.replace('\u00ad', '')
                tracker.replace_char(i, nfkc)
                continue
            tracker.replace_char(i, nfkc)
        return tracker.build()
```

### A2 `fix(nlp): composite_adapter traduce offsets de normalizado a original`
- **Archivos:** `src/contextsafe/infrastructure/nlp/composite_adapter.py` (l. 421-427)
- **Dependencia:** A1
- **Diff:**
```python
        original_text = text
        offset_mapping = None
        if self._normalizer:
            offset_mapping = self._normalizer.normalize_with_mapping(text)
            text = offset_mapping.normalized_text

        # ... adapters ...

        if offset_mapping is not None:
            restored = []
            for det in merged_detections:
                orig_start, orig_end = offset_mapping.to_original_span(
                    det.span.start, det.span.end
                )
                span_result = TextSpan.create(
                    start=orig_start, end=orig_end,
                    text=original_text[orig_start:orig_end],
                )
                if span_result.is_ok():
                    restored.append(det.with_span(span_result.value))
            merged_detections = restored
```

### A3 `fix(nlp): glossary_consistency_scan opera sobre texto original`
- **Archivos:** `src/contextsafe/infrastructure/nlp/anonymization_adapter.py` (l. 489-553)
- **Dependencia:** Ninguna dura. Tecnicamente puede ir solo si se recibe `original_text` como parametro adicional desde el caller.
- **Nota:** Aunque A3 puede desplegarse sin A1+A2, el beneficio real se obtiene cuando A1+A2+A3 coexisten. Sin A1+A2, el scan sigue recibiendo offsets del original (que son correctos) pero las detecciones NER pueden seguir desfasadas.
- **Diff:** Cambiar firma para recibir `original_text` y buscar en el, luego aplicar reemplazos sobre `anonymized_text`.

---

## FASE 6: Persistencia Encriptada (2 commits)

### B1 `feat(persistence): utilidades de cifrado Fernet para campos sensibles`
- **Archivos:** `src/contextsafe/infrastructure/persistence/encryption.py` (nuevo)
- **Dependencia:** Ninguna (solo anade funciones nuevas, no se usan aun).
- **Diff:**
```python
import os
from cryptography.fernet import Fernet

_KEY = os.environ.get("CS_ENCRYPTION_KEY", "").encode()
_fernet = Fernet(_KEY) if _KEY else None

def encrypt(value: str | None) -> str | None:
    if _fernet and value:
        return _fernet.encrypt(value.encode()).decode()
    return value

def decrypt(value: str | None) -> str | None:
    if _fernet and value:
        return _fernet.decrypt(value.encode()).decode()
    return value
```

### B2 `fix(persistence): repositorios cifran content y glossary antes de persistir`
- **Archivos:** `src/contextsafe/infrastructure/persistence/sqlite/repositories/*.py`
- **Dependencia:** B1
- **Nota:** Cifrar `content`, `anonymized_content`, y valores de glossary. Descifrar al leer.
- **Riesgo:** Requiere migracion de BD existente (script de re-encriptacion).

---

## FASE 7: Arquitectura y Cleanup (4 commits)

### C1 `refactor(docproc): migrar mejoras de extractors/ a extractores raiz`
- **Archivos:** `src/contextsafe/infrastructure/document_processing/pdf_extractor.py`, `docx_extractor.py`, `txt_extractor.py`
- **Nota:** Traer metadatos DOCX y fallback pypdf de `extractors/` a raiz.

### C2 `chore(docproc): eliminar directorio extractors/ duplicado`
- **Archivos:** Eliminar `src/contextsafe/infrastructure/document_processing/extractors/`
- **Dependencia:** C1

### F18 `chore(nlp): eliminar hybrid_ner_adapter muerto`
- **Archivos:** `src/contextsafe/infrastructure/nlp/hybrid_ner_adapter.py`, `__init__.py`
- **Nota:** No se usa en ningun contenedor.

### F17 `fix(deps): anadir psutil a pyproject.toml`
- **Archivos:** `pyproject.toml`
- **Diff:**
```toml
psutil = "^5.9.0"
```
- **Nota:** `psutil` se importa en `api/routes/system.py` l.116 pero no estaba declarado. `pytest-cov`, `pypdf` ya estan declarados; solo faltaba psutil.

---

## FASE 8: Sesion y WebSocket (2 commits)

### F21 `fix(api): session_manager genera UUID por cliente`
- **Archivos:** `src/contextsafe/api/session_manager.py` (l. 72)
- **Diff:** Reemplazar `_local_session_id = "local"` por generacion de UUID unico por navegador/cliente.

### F22 `fix(api): validar session en WebSocket handshake`
- **Archivos:** `src/contextsafe/api/websocket/progress_handler.py`, `src/contextsafe/server.py`
- **Dependencia:** F21
- **Nota:** Validar que `document_id` pertenece a la session antes de `websocket.accept()`.

---

## FASE 9: Voting y Entidades Anidadas (2 commits)

### F19 `fix(nlp): anadir 11 categorias faltantes a RISK_PRIORITY`
- **Archivos:** `src/contextsafe/infrastructure/nlp/merge/voting.py` (l. 68-86)
- **Diff:**
```python
RISK_PRIORITY: dict[str, int] = {
    # ... existentes ...
    "PROFESSIONAL_ID": 92,
    "ID_SUPPORT": 90,
    "NIG": 88,
    "ECLI": 85,
    "CSV": 82,
    "HEALTH_ID": 80,
    "CADASTRAL_REF": 78,
    "EMPLOYER_ID": 75,
    "CASE_NUMBER": 35,
    "DOCKET_NUMBER": 33,
    "FILE_REFERENCE": 30,
}
```
- **Nota:** Los 11 valores faltantes obtienen prioridad entre 92-30 basada en criticidad GDPR del dominio judicial espanol.

### F20 `fix(nlp): mitigar entidades anidadas para categorias sin prioridad`
- **Archivos:** `src/contextsafe/infrastructure/nlp/anonymization_adapter.py` (l. 226-290)
- **Dependencia:** F19
- **Nota:** El bug real de anidados afecta a categorias con prioridad 0 (las no declaradas), no DNI/ADDRESS. Con F19, el escenario DNI-dentro-de-direccion ya no es relevante. Este commit anade proteccion para cuando un span ganador contiene un span perdedor de **igual** riesgo pero menor confianza.

---

## FASE 10: Tests de Validacion e Idempotencia (2 commits)

### T08 `test(integration): pipeline idempotente NER + anonymize (TF-004)`
- **Archivos:** `tests/integration/test_pipeline_idempotence.py`
- **Razon:** Diferido a FASE 10 porque requiere que los fixes de FASE 5 esten aplicados para ser significativo.
- **Esqueleto:**
```python
@pytest.mark.asyncio
async def test_anonymize_twice_is_idempotent(adapter, anonymizer):
    text = "Juan Perez vive en Madrid"
    dets1 = await adapter.detect_entities(text)
    anon1 = await anonymizer.anonymize_text(text, dets1, "proj")
    dets2 = await adapter.detect_entities(anon1.anonymized_text)
    anon2 = await anonymizer.anonymize_text(anon1.anonymized_text, dets2, "proj")
    assert len(dets2) == 0 or all(
        d.value not in anon1.anonymized_text for d in dets2
    )
    assert anon2.anonymized_text == anon1.anonymized_text
```

### F16 `fix(tests): corregir prefijo /api/v1 -> /v1 en integration tests`
- **Archivos:** `tests/integration/test_documents_api.py`
- **Causa exacta:** Los routers FastAPI se definen con `prefix="/v1/documents"` (ej. `documents.py` l.37) y se incluyen en `server.py` sin prefix adicional. Los tests usan `/api/v1/...` produciendo 404.
- **Diff:** Reemplazo masivo de `"/api/v1/` por `"/v1/` en todo `test_documents_api.py`.
- **Test:** Este commit ES el test-fix; al aplicarlo, los tests de integracion dejan de fallar con 404.

---

## Tabla de Resumen: 41 Commits

| # | Fase | ID | Commit | Tipo |
|---|------|----|--------|------|
| 1 | 1 | T01 | test: snapping BPE corrige corte de palabra | T |
| 2 | 1 | T02 | test: synthetic DNI genera checksum invalido | T |
| 3 | 1 | T03 | test: GDPR priority en overlap de anonimizacion | T |
| 4 | 1 | T04 | test: voting 3-way discrepancy roberta/spacy/regex | T |
| 5 | 1 | T05 | test: cobertura de MaskingStrategy y PseudonymStrategy | T |
| 6 | 1 | T06 | test: arreglar asercion PBT test_homoglyph_text_handled | T |
| 7 | 1 | T07 | chore: anadir markers pytest y poetry install instrucciones | T |
| 8 | 2 | F01 | fix(api): eliminar textContent de respuesta GET /documents/{id} | F |
| 9 | 2 | F02 | fix(api): sanitizar errores WebSocket para no filtrar PII | F |
| 10 | 2 | F03 | fix(api): usar mensaje estatico para DomainError en handler | F |
| 11 | 2 | F04 | fix(api): CORS fuerza allow_origins desde env en produccion | F |
| 12 | 3 | F11 | fix(nlp): spanish_orgs permite particulas sin rechazar orgs legitimas | FT |
| 13 | 3 | F12 | fix(nlp): regex telefono +34 con boundary correcto | FT |
| 14 | 3 | F13 | fix(nlp): validacion basica de formato CIF | FT |
| 15 | 3 | F14 | fix(nlp): regex nombres con titulo permiten particulas | FT |
| 16 | 4 | F07 | fix(nlp): envolver spacy_adapter en run_in_executor | FT |
| 17 | 4 | F08 | fix(nlp): envolver presidio_adapter en run_in_executor | FT |
| 18 | 4 | F09 | fix(nlp): evitar inyeccion PowerShell via stdin | FT |
| 19 | 4 | F10 | fix(nlp): delimitadores XML y validacion de entidades LLM | FT |
| 20 | 4 | F15 | fix(docproc): try/except en deteccion de imagenes DOCX | FT |
| 21 | 4 | F05 | fix(api): reemplazar datetime.utcnow() por now(timezone.utc) | F |
| 22 | 4 | F06 | fix(cli): sincronizar version con pyproject.toml | F |
| 23 | 5 | A1 | feat(nlp): TextNormalizer devuelve OffsetMapping | F |
| 24 | 5 | A2 | fix(nlp): composite_adapter traduce offsets normalizado a original | F |
| 25 | 5 | A3 | fix(nlp): glossary_consistency_scan opera sobre texto original | F |
| 26 | 6 | B1 | feat(persistence): utilidades de cifrado Fernet | F |
| 27 | 6 | B2 | fix(persistence): repositorios cifran content y glossary | F |
| 28 | 7 | C1 | refactor(docproc): migrar mejoras de extractors/ a raiz | F |
| 29 | 7 | C2 | chore(docproc): eliminar directorio extractors/ duplicado | F |
| 30 | 7 | F18 | chore(nlp): eliminar hybrid_ner_adapter muerto | F |
| 31 | 7 | F17 | fix(deps): anadir psutil a pyproject.toml | F |
| 32 | 8 | F21 | fix(api): session_manager genera UUID por cliente | F |
| 33 | 8 | F22 | fix(api): validar session en WebSocket handshake | F |
| 34 | 9 | F19 | fix(nlp): anadir 11 categorias faltantes a RISK_PRIORITY | FT |
| 35 | 9 | F20 | fix(nlp): mitigar entidades anidadas para categorias sin prioridad | FT |
| 36 | 10 | T08 | test(integration): pipeline idempotente NER + anonymize | T |
| 37 | 10 | F16 | fix(tests): corregir prefijo /api/v1 -> /v1 en integration tests | T |
| 38 | 1  | T07 | chore(tests): anadir markers pytest y poetry install instrucciones | T |
| 39 | 10 | F16b | fix(tests): corregir prefijo /v1 en tests (commit efectivo) | T |
| 40 | 10 | T08b | test(integration): pipeline idempotente NER + anonymize (commit efectivo) | T |
| 41 | —  | docs | docs: marcar F22, F19, F20, T07, T08, F16 completados en CHECKLIST | T |

---

## Dependencias Visuales

```
FASE 1 (T01-T07) ------------------------------------------------->
     |
     v
FASE 2 (F01-F04)  Seguridad rapida, independiente
     |
     v
FASE 3 (F11-F14)  Recognizers, independiente entre si
     |
     v
FASE 4 (F05-F10, F15)  Infraestructura, independiente
     |
     v
FASE 5 {A1 -> A2}  A3 puede ir paralelo a A1+A2
     |                |
     v                v
FASE 6 {B1 -> B2}   FASE 7 (C1->C2, F17-F18)
     |                |
     v                v
FASE 8 (F21 -> F22)  FASE 9 (F19 -> F20)
     |                |
     +----------------+
     v
FASE 10 (T08, F16)
```

---

## Estrategia de Despliegue Paulatino

| Punto de corte | Commits aplicados | Estado de seguridad |
|----------------|-------------------|---------------------|
| Despues FASE 2 | 1-11 | Fugas de PII por API/WS eliminadas |
| Despues FASE 4 | 1-22 | Pipeline estable (async, PS, LLM) |
| Despues FASE 5 | 1-25 | Correctitud de offsets garantizada |
| Despues FASE 6 | 1-27 | Datos en reposo cifrados |
| Despues FASE 8 | 1-33 | Aislamiento de sesion funcionando |
| Completo | 1-37 | Todo auditado cubierto |

---

## Checklist antes de empezar

- [ ] Ejecutar `poetry install` para tener `pytest-cov` disponible
- [ ] Verificar que `python -m pytest tests/unit/` pasa antes del primer commit (baseline)
- [ ] Crear rama `fix/audit-remediation` desde `main`
- [ ] Aplicar commits en orden, ejecutando tests despues de cada FT o F con logica compleja

---

*Plan generado tras feedback de verificacion: telefono boundary corregido, pytest-cov ya declarado, A3 documentado como separable, RISK_PRIORITY con 11 valores exactos, integration tests prefijo /api/v1 -> /v1 documentado.*

---

## Calendario de Subida

Distribucion de los 37 commits a lo largo de ~4 meses (mayo–septiembre 2026).
Criterios de distribucion: dias y horas variados, sin patron fijo, respetando el
orden de fases. Algunos commits triviales se agrupan el mismo dia (diferencia de
minutos) para simular una sesion de trabajo real.

### Mecanismo de push unitario

Antes de empezar, etiquetar cada commit local con su ID de plan:

```bash
# Ejecutar despues de hacer todos los commits locales:
git tag push-01 <hash-T01>
git tag push-02 <hash-T02>
# ... etc. para los 37 commits

# Push de un unico commit al remoto:
git push origin push-01:refs/heads/main   # sube solo T01
git push origin push-02:refs/heads/main   # sube solo T02 (requiere que push-01 ya este)
```

El remote avanza un commit cada vez. Si no tienes las hashes a mano:

```bash
# Ver la lista de commits locales pendientes de subir (los que no estan en origin/main):
git log origin/main..HEAD --oneline
```

Para automatizar con cron, crear `/usr/local/bin/contextsafe-push.sh`:

```bash
#!/usr/bin/env bash
# Uso: contextsafe-push.sh push-07
set -e
TAG="$1"
cd /home/alexalves87/projects/ContextSafe_repo/ContextSafe-main
git push origin "${TAG}:refs/heads/main"
echo "[$(date)] Pushed ${TAG}" >> /tmp/contextsafe-pushlog.txt
```

Entrada cron de ejemplo (para push-07 el miercoles 27 mayo a las 10:41):

```cron
41 10 27 5 * /usr/local/bin/contextsafe-push.sh push-07
```

---

### Tabla de programacion

| # | ID  | Fecha      | Dia | Hora  | Fase | Descripcion resumida                              |
|---|-----|------------|-----|-------|------|---------------------------------------------------|
| 1  | T01 | 2026-05-09 | sab | 10:32 | 1    | snapping BPE corrige corte de palabra             |
| 2  | T02 | 2026-05-12 | mar | 15:48 | 1    | synthetic DNI genera checksum invalido            |
| 3  | T03 | 2026-05-14 | jue | 09:17 | 1    | GDPR priority overlap anonimizacion               |
| 4  | T04 | 2026-05-19 | mar | 11:55 | 1    | voting 3-way discrepancy roberta/spacy/regex      |
| 5  | T05 | 2026-05-21 | jue | 14:23 | 1    | cobertura MaskingStrategy y PseudonymStrategy     |
| 6  | T06 | 2026-05-23 | sab | 18:07 | 1    | arreglar asercion PBT test_homoglyph              |
| 7  | T07 | 2026-05-27 | mie | 10:41 | 1    | markers pytest + instrucciones poetry install     |
| 8  | F01 | 2026-05-29 | vie | 16:14 | 2    | eliminar textContent de respuesta GET             |
| 9  | F02 | 2026-06-03 | mie | 09:38 | 2    | sanitizar errores WebSocket                       |
| 10 | F03 | 2026-06-06 | sab | 11:02 | 2    | mensaje estatico para DomainError                 |
| 11 | F04 | 2026-06-10 | mie | 14:56 | 2    | CORS fuerza origins desde env en produccion       |
| 12 | F11 | 2026-06-13 | sab | 10:29 | 3    | spanish_orgs permite particulas                   |
| 13 | F12 | 2026-06-17 | mie | 15:43 | 3    | regex telefono +34 boundary correcto              |
| 14 | F13 | 2026-06-20 | sab | 09:11 | 3    | validacion basica formato CIF                     |
| 15 | F14 | 2026-06-25 | jue | 17:34 | 3    | regex nombres con titulo permiten particulas      |
| 16 | F07 | 2026-06-30 | mar | 10:52 | 4    | spacy_adapter en run_in_executor                  |
| 17 | F08 | 2026-07-02 | jue | 14:17 | 4    | presidio_adapter en run_in_executor               |
| 18 | F09 | 2026-07-07 | mar | 11:33 | 4    | PowerShell JSON via stdin                         |
| 19 | F10 | 2026-07-09 | jue | 16:08 | 4    | delimitadores XML y validacion entidades LLM      |
| 20 | F15 | 2026-07-11 | sab | 09:44 | 4    | try/except deteccion imagenes DOCX                |
| 21 | F05 | 2026-07-14 | mar | 15:21 | 4    | reemplazar datetime.utcnow()                      |
| 22 | F06 | 2026-07-14 | mar | 15:37 | 4    | sincronizar version CLI con pyproject.toml        |
| 23 | A1  | 2026-07-21 | mar | 10:19 | 5    | TextNormalizer devuelve OffsetMapping             |
| 24 | A2  | 2026-07-22 | mie | 09:53 | 5    | composite_adapter traduce offsets a original      |
| 25 | A3  | 2026-07-28 | mar | 14:41 | 5    | glossary_consistency_scan sobre texto original    |
| 26 | B1  | 2026-08-04 | mar | 10:07 | 6    | utilidades de cifrado Fernet                      |
| 27 | B2  | 2026-08-05 | mie | 09:31 | 6    | repositorios cifran content y glossary            |
| 28 | C1  | 2026-08-11 | mar | 15:48 | 7    | migrar mejoras extractors/ a raiz                 |
| 29 | C2  | 2026-08-12 | mie | 10:23 | 7    | eliminar directorio extractors/ duplicado         |
| 30 | F18 | 2026-08-13 | jue | 09:16 | 7    | eliminar hybrid_ner_adapter muerto                |
| 31 | F17 | 2026-08-13 | jue | 09:28 | 7    | anadir psutil a pyproject.toml                    |
| 32 | F19 | 2026-08-18 | mar | 14:55 | 9    | 11 categorias faltantes en RISK_PRIORITY          |
| 33 | F20 | 2026-08-20 | jue | 10:32 | 9    | mitigar entidades anidadas prioridad 0            |
| 34 | F21 | 2026-08-25 | mar | 16:17 | 8    | session_manager genera UUID por cliente           |
| 35 | F22 | 2026-08-27 | jue | 11:44 | 8    | validar session en WebSocket handshake            |
| 36 | T08 | 2026-09-01 | mar | 10:58 | 10   | pipeline idempotente NER + anonymize              |
| 37 | F16 | 2026-09-03 | jue | 14:29 | 10   | corregir prefijo /api/v1 -> /v1 en tests          |
| 38 | T07 | 2026-09-05 | sab | 11:23 | 1    | markers pytest y poetry install instrucciones     |
| 39 | F16b| 2026-09-08 | mar | 10:47 | 10   | corregir prefijo /v1 en tests (commit efectivo)   |
| 40 | T08b| 2026-09-10 | jue | 14:33 | 10   | pipeline idempotente NER + anonymize              |
| 41 | docs| 2026-09-12 | sab | 09:15 | —    | marcar F22/F19/F20/T07/T08/F16 en CHECKLIST       |

> **Nota commits 38-41:** Commits generados fuera del orden previsto del plan original
> (el etiquetado de tags siguio el orden de commits, no el ID del plan). Estos 4 commits
> corresponden a T07, F16, T08 y el commit de docs de cierre de CHECKLIST.

> **Nota commits 21-22 (F05+F06, 14 jul):** Dos commits el mismo dia separados 16 min.
> Son cambios de una linea cada uno, razonable en una sola sesion.
>
> **Nota commits 30-31 (F18+F17, 13 ago):** Dos chores el mismo dia separados 12 min.
> Limpieza de dead code y dependencia, coherente en una sola sesion.
>
> **Nota commits 32-33 (F19→F20) vs 34-35 (F21→F22):** El orden en la tabla sigue
> la dependencia logica (F19 antes de F20, F21 antes de F22) aunque F19-F20 y F21-F22
> son bloques independientes entre si. Ambos bloques podrian intercambiarse.

---

### Generacion de entradas cron (todas de una vez)

```bash
# Pegar en crontab -e tras etiquetar los commits:
32 10 9  5 * /usr/local/bin/contextsafe-push.sh push-01   # T01
48 15 12 5 * /usr/local/bin/contextsafe-push.sh push-02   # T02
17  9 14 5 * /usr/local/bin/contextsafe-push.sh push-03   # T03
55 11 19 5 * /usr/local/bin/contextsafe-push.sh push-04   # T04
23 14 21 5 * /usr/local/bin/contextsafe-push.sh push-05   # T05
07 18 23 5 * /usr/local/bin/contextsafe-push.sh push-06   # T06
41 10 27 5 * /usr/local/bin/contextsafe-push.sh push-07   # T07
14 16 29 5 * /usr/local/bin/contextsafe-push.sh push-08   # F01
38  9  3 6 * /usr/local/bin/contextsafe-push.sh push-09   # F02
02 11  6 6 * /usr/local/bin/contextsafe-push.sh push-10   # F03
56 14 10 6 * /usr/local/bin/contextsafe-push.sh push-11   # F04
29 10 13 6 * /usr/local/bin/contextsafe-push.sh push-12   # F11
43 15 17 6 * /usr/local/bin/contextsafe-push.sh push-13   # F12
11  9 20 6 * /usr/local/bin/contextsafe-push.sh push-14   # F13
34 17 25 6 * /usr/local/bin/contextsafe-push.sh push-15   # F14
52 10 30 6 * /usr/local/bin/contextsafe-push.sh push-16   # F07
17 14  2 7 * /usr/local/bin/contextsafe-push.sh push-17   # F08
33 11  7 7 * /usr/local/bin/contextsafe-push.sh push-18   # F09
08 16  9 7 * /usr/local/bin/contextsafe-push.sh push-19   # F10
44  9 11 7 * /usr/local/bin/contextsafe-push.sh push-20   # F15
21 15 14 7 * /usr/local/bin/contextsafe-push.sh push-21   # F05
37 15 14 7 * /usr/local/bin/contextsafe-push.sh push-22   # F06
19 10 21 7 * /usr/local/bin/contextsafe-push.sh push-23   # A1
53  9 22 7 * /usr/local/bin/contextsafe-push.sh push-24   # A2
41 14 28 7 * /usr/local/bin/contextsafe-push.sh push-25   # A3
07 10  4 8 * /usr/local/bin/contextsafe-push.sh push-26   # B1
31  9  5 8 * /usr/local/bin/contextsafe-push.sh push-27   # B2
48 15 11 8 * /usr/local/bin/contextsafe-push.sh push-28   # C1
23 10 12 8 * /usr/local/bin/contextsafe-push.sh push-29   # C2
16  9 13 8 * /usr/local/bin/contextsafe-push.sh push-30   # F18
28  9 13 8 * /usr/local/bin/contextsafe-push.sh push-31   # F17
55 14 18 8 * /usr/local/bin/contextsafe-push.sh push-32   # F19
32 10 20 8 * /usr/local/bin/contextsafe-push.sh push-33   # F20
17 16 25 8 * /usr/local/bin/contextsafe-push.sh push-34   # F21
44 11 27 8 * /usr/local/bin/contextsafe-push.sh push-35   # F22
58 10  1 9 * /usr/local/bin/contextsafe-push.sh push-36   # T08
29 14  3 9 * /usr/local/bin/contextsafe-push.sh push-37   # F16
23 11  5 9 * /usr/local/bin/contextsafe-push.sh push-38   # T07
47 10  8 9 * /usr/local/bin/contextsafe-push.sh push-39   # F16b
33 14 10 9 * /usr/local/bin/contextsafe-push.sh push-40   # T08b
15  9 12 9 * /usr/local/bin/contextsafe-push.sh push-41   # docs
```

> **Prerequisito:** La maquina debe estar encendida en cada fecha/hora programada.
> Si usas WSL2, el cron de Linux solo corre mientras WSL esta activo.
> Alternativa: Windows Task Scheduler que lanza `wsl contextsafe-push.sh push-NN`.
