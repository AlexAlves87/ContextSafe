# Auditoria Subagente 2 — Seguridad, Arquitectura y Codigo Muerto

Archivos principales auditados:
- `src/contextsafe/api/`
- `src/contextsafe/infrastructure/persistence/`
- `src/contextsafe/infrastructure/llm/`
- `src/contextsafe/application/use_cases/`
- `pyproject.toml`

---

## 1. Seguridad

### SEC-001 — Fuga de PII por WebSocket en errores de procesamiento
- **Archivo:** `src/contextsafe/api/services/document_processor.py` (l. 273-279)
- **Severidad:** CRITICO
- **Descripcion:** El `except Exception` captura cualquier error, almacena `error=str(e)` en el documento y lo retransmite sin sanitizar via WebSocket. Un error de parsing puede incluir fragmentos del texto original.
- **Fix:** Sanitizar mensajes de error. Ver `05-fixes-critical-high.md` seccion 5.6.

### SEC-002 — Sesion unica global: sin aislamiento entre usuarios
- **Archivo:** `src/contextsafe/api/session_manager.py` (l. 72), `api/middleware/session.py`
- **Severidad:** CRITICO
- **Descripcion:** `SessionManager._local_session_id = "local"` es hardcoded. Todos los requests comparten la misma sesion. No hay autenticacion ni separacion de tenencia.
- **Fix:** Generar session_id UUID por cliente.

### SEC-003 — SQLCipher declarado pero NUNCA utilizado
- **Archivo:** `pyproject.toml` (l. 40), `infrastructure/persistence/database.py`, `infrastructure/persistence/sqlite/database.py`
- **Severidad:** CRITICO
- **Descripcion:** `sqlcipher3-binary` esta en dependencias pero no se importa. Tanto `Database` (runtime) como `Database` en `sqlite/` usan `sqlite+aiosqlite:///` sin PRAGMA key. El fichero `data/contextsafe.db` es SQLite plano.
- **Fix:** Cifrar a nivel de aplicacion o migrar a driver sync con sqlcipher3. Ver `05-fixes-critical-high.md`.

### SEC-004 — WebSocket sin control de acceso
- **Archivo:** `src/contextsafe/server.py` (l. 117-121), `api/websocket/progress_handler.py`
- **Severidad:** ALTO
- **Descripcion:** `/ws/documents/{document_id}/progress` acepta conexiones sin validar sesion. Cualquier cliente con el UUID puede suscribirse.
- **Fix:** Validar session_id/cookie en handshake antes de `websocket.accept()`.

### SEC-005 — Prompt injection posible en adapters LLM
- **Archivo:** `src/contextsafe/infrastructure/llm/ollama_ner_adapter.py` (l. 282), `llamacpp_adapter.py` (l. 117), `nlp/strategies/synthetic.py` (l. 709)
- **Severidad:** ALTO
- **Descripcion:** El texto del usuario se concatena directamente en el prompt sin sanitizacion. Output solo se parsea por regex/JSON, sin validacion estricta.
- **Fix:** Usar delimitadores XML y validar que start/end correspondan exactamente a substrings del original.

### SEC-006 — CORS permite credenciales con origenes por defecto inseguros
- **Archivo:** `src/contextsafe/api/middleware/cors.py` (l. 33-37, 54)
- **Severidad:** MEDIO
- **Descripcion:** `allow_credentials=True` por defecto con `allow_origins = ["http://localhost:5173", ...]`. Si se despliega en red local sin definir `CONTEXTSAFE_CORS_ORIGINS`, cualquier sitio en localhost puede hacer requests con credenciales.
- **Fix:** En produccion, forzar `allow_origins` desde variable de entorno. Ver `05-fixes-critical-high.md`.

### SEC-007 — Exposicion de `textContent` completo en endpoint GET
- **Archivo:** `src/contextsafe/api/routes/documents.py` (l. 175)
- **Severidad:** ALTO
- **Descripcion:** `GET /v1/documents/{document_id}` devuelve `"textContent": doc.content or ""`, texto original completo con PII.
- **Fix:** Eliminar campo por defecto. Ver `05-fixes-critical-high.md`.

### SEC-008 — Logs de error con trazas completas (potencial PII)
- **Archivo:** `src/contextsafe/api/middleware/error_handler.py` (l. 86-88), `api/routes/glossary.py` (l. 356-359)
- **Severidad:** MEDIO
- **Descripcion:** Loguea `traceback.format_exc()` completo en nivel CRITICAL. Si la excepcion incluye datos de request (texto procesado, nombres), se persiste en logs. `glossary.py` escribe traceback a `debug_error.log` sin rotacion.
- **Fix:** Sanitizar logs; nunca escribir traceback a disco en produccion.

---

## 2. Codigo Muerto y Duplicacion

### DEAD-001 — `generate_anonymized.py`: use case huerfano
- **Archivo:** `src/contextsafe/application/use_cases/generate_anonymized/generate_anonymized.py`
- **Severidad:** ALTO
- **Descripcion:** Use case bien disenado con ports, pero ninguna ruta API lo invoca. `document_processor.py` implementa logica ad-hoc que no realiza el consistency scan del use case.
- **Recomendacion:** Migrar logica de `GenerateAnonymized` a `document_processor.py` o refactorizar rutas para usar el use case.

### DEAD-002 — Extractores duplicados: raiz vs `extractors/`
- **Archivos:** `document_processing/pdf_extractor.py` vs `extractors/pdf_extractor.py`, `docx_extractor.py` vs `extractors/docx_extractor.py`, `txt_extractor.py` vs `extractors/txt_extractor.py`
- **Severidad:** MEDIO
- **Descripcion:** Dos implementaciones de cada extractor. Raiz implementa `TextExtractor` (async), usada por `CompositeDocumentExtractor`. Extractors/ implementa `DocumentExtractor` (sync), usada por `ExtractorFactory` que no se usa en la API.
- **Recomendacion:** Consolidar en una sola familia. Eliminar `extractors/` o fusionar mejoras.

### DEAD-003 — `HybridNerAdapter` reemplazado por `CompositeNerAdapter`
- **Archivo:** `src/contextsafe/infrastructure/nlp/hybrid_ner_adapter.py`
- **Severidad:** BAJO
- **Descripcion:** Implementa combinacion LLM+Presidio, pero el contenedor instancia `CompositeNerAdapter`. Nunca se instancia.
- **Recomendacion:** Eliminar archivo y su exportacion.

### DEAD-004 — `presentation/` es scaffolding vacio
- **Archivo:** `src/contextsafe/presentation/`
- **Severidad:** BAJO
- **Descripcion:** Directorio completo con solo `__init__.py` y docstrings.
- **Recomendacion:** Eliminar o implementar si hay frontend CLI/TUI planificado.

### DEAD-005 — `llamacpp_adapter.py` sin dependencia disponible
- **Archivo:** `src/contextsafe/infrastructure/llm/llamacpp_adapter.py`
- **Severidad:** MEDIO
- **Descripcion:** `llama-cpp-python` esta comentado en `pyproject.toml`. El adapter importa `from llama_cpp import Llama` y fallara.
- **Recomendacion:** Descomentar dependencia o eliminar adapter.

---

## 3. Violaciones de Arquitectura Hexagonal

### ARCH-001 — `document_processor.py` viola la capa de aplicacion
- **Archivo:** `src/contextsafe/api/services/document_processor.py`
- **Severidad:** ALTO
- **Descripcion:** Accede directamente a `session_manager` (infraestructura) en lugar de repositorios. Llama directamente a `progress_handler`. No utiliza `GenerateAnonymized`.
- **Fix:** Refactorizar para delegar en use case y pasar callbacks como puertos.

### ARCH-002 — `compute_state.py` y `ner_registry.py`
- **Archivo:** `src/contextsafe/api/services/compute_state.py`, `api/services/ner_registry.py`
- **Severidad:** BAJO
- **Descripcion:** `compute_state.py` mantiene estado global GPU/CPU en API. `ner_registry.py` es un thin facade sobre DI container. Aceptables con matices.
- **Recomendacion:** Mover `compute_state.py` a `infrastructure.compute`.

### ARCH-003 — Domain layer: LIMPIO
- **Verificacion:** `grep -r "from contextsafe.(api|infrastructure)" src/contextsafe/domain/`
- **Resultado:** Cero imports. La capa de dominio respeta la regla.

### ARCH-004 — Application layer: LIMPIO
- **Verificacion:** `grep -r "from contextsafe.(api|infrastructure)" src/contextsafe/application/use_cases/`
- **Resultado:** Cero imports directos. Los use cases usan exclusivamente ports.

---

## 4. Dependencias y Configuracion

### DEP-001 — `pypdf` usado pero no declarado
- **Archivo:** `extractors/pdf_extractor.py` (l. 109)
- **Severidad:** MEDIO
- **Fix:** Anadir `pypdf = "^4.0.0"` a dependencias o eliminar fallback.

### DEP-002 — `psutil` usado pero no declarado
- **Archivo:** `src/contextsafe/api/routes/system.py` (l. 116)
- **Severidad:** BAJO
- **Fix:** Anadir `psutil = "^5.9.0"` o eliminar import intent.

### DEP-003 — `prometheus-client` declarado pero sin uso
- **Archivo:** `pyproject.toml` (l. 68)
- **Severidad:** BAJO
- **Fix:** Implementar endpoint `/metrics` o eliminar.

### DEP-004 — Posible conflicto de versiones ML
- **Archivo:** `pyproject.toml` (l. 54-56)
- **Severidad:** MEDIO
- **Descripcion:** `torch ^2.1.0`, `transformers ^4.36.0`, `spacy ^3.7.0`. Arboles de dependencia complejos pueden causar incompatibilidades.
- **Fix:** Fijar versiones menores exactas (`==`) o usar grupos de Poetry.

### DEP-005 — `python-dotenv` carga `.env` automaticamente
- **Archivo:** `src/contextsafe/api/config.py` (l. 34-39)
- **Severidad:** BAJO
- **Fix:** Condicionar `env_file` al entorno: `env_file=".env" if app_env != "production" else None`.

---

## 5. Gestion de Errores y Resiliencia

### ERR-001 — Bloqueo del event loop async en adapters NLP
- **Archivos:** `spacy_adapter.py` (l. 104), `presidio_adapter.py` (l. 417), `llm/ollama_ner_adapter.py` (l. 193)
- **Severidad:** ALTO
- **Fix:** Envolver en `await asyncio.get_running_loop().run_in_executor(...)`. Ver `05-fixes-critical-high.md`.

### ERR-002 — Fallo silencioso de modelos NLP no descargados
- **Archivo:** `spacy_adapter.py` (l. 72-80), `presidio_adapter.py` (l. 346-354)
- **Severidad:** MEDIO
- **Descripcion:** Si el modelo no esta descargado, `_ensure_loaded()` lanza RuntimeError. La primera request falla con 500 en lugar de degradar a regex-only.
- **Fix:** En contenedor, envolver carga de cada adapter en try/except.

### ERR-003 — `error_handler.py` expone `detail=str(exc)` para DomainError
- **Archivo:** `src/contextsafe/api/middleware/error_handler.py` (l. 59-70)
- **Severidad:** MEDIO
- **Fix:** Sanitizar `str(exc)` o usar mensajes de error estaticos. Ver `05-fixes-critical-high.md`.

### ERR-004 — `anonymize_selection` no maneja excepciones de regex
- **Archivo:** `src/contextsafe/api/routes/documents.py` (l. 1036-1042)
- **Severidad:** BAJO
- **Fix:** Anadir manejo de `re.error`.

---

## Hallazgos Adicionales

| ID | Archivo | Linea | Issue | Severidad |
|---|---|---|---|---|
| MISC-001 | `api/routes/documents.py` | 132 | `datetime.utcnow()` deprecado en Python 3.12+ | BAJO |
| MISC-002 | `api/routes/documents.py` | 1018 | `original_text.count(text)` case-sensitive vs `re.IGNORECASE` | BAJO |
| MISC-003 | `infrastructure/persistence/sqlite/models.py` | 53 | `metadata_json: Mapped[Optional[str]]` asignado a columna JSON | BAJO |
| MISC-004 | `infrastructure/persistence/database.py` | 46 | `pool_pre_ping=True` en SQLite+aiosqlite puede generar warnings | BAJO |
| MISC-005 | `tests/conftest.py` | 33-42 | Fixture `test_db` es stub vacio | BAJO |
| MISC-006 | `api/routes/system.py` | 93-104 | `detect_cpu()` sin manejo de encoding | BAJO |
| MISC-007 | `src/contextsafe/cli.py` | 19 | `version="0.1.0"` hardcoded, desincronizado | BAJO |

---

## Resumen Seguridad/Arquitectura

| Severidad | Cantidad |
|-----------|----------|
| CRITICO | 3 |
| ALTO | 6 |
| MEDIO | 8 |
| BAJO | 7 |
