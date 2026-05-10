# Deuda Tecnica Estructural

Los 3 problemas de arquitectura mas urgentes.

---

## DT-1: `document_processor.py` viola la arquitectura hexagonal de forma flagrante

- **Archivo:** `src/contextsafe/api/services/document_processor.py`
- **Severidad:** ALTO
- **Descripcion:** Este "servicio" de API actua como orquestador que:
  1. Accede directamente a `session_manager` (infraestructura) en lugar de `DocumentRepository` / `GlossaryRepository`
  2. Llama directamente al handler WebSocket (`progress_handler`) desde la logica de negocio
  3. No utiliza el use case `GenerateAnonymized` ya existente (que si esta bien disenado con ports)
  4. Mezcla concerns de progreso UI, persistencia in-memory, anonimizacion y generacion de glossary en un solo bloque
- **Impacto:** Imposible testear la logica de negocio sin arrastrar FastAPI + WebSocket + SQLite. El codigo valioso del use case huerfano (`_glossary_consistency_scan`) esta desconectado.
- **Recomendacion:** Refactorizar para que `document_processor.py` delegue en `GenerateAnonymized` (o un nuevo use case async), pase callbacks de progreso como puertos, y use repositorios en lugar de `session_manager`.

---

## DT-2: Dos familias de extractores duplicados + codigo muerto que confunde

- **Archivos:**
  - `infrastructure/document_processing/pdf_extractor.py` vs `extractors/pdf_extractor.py`
  - `infrastructure/document_processing/docx_extractor.py` vs `extractors/docx_extractor.py`
  - `infrastructure/document_processing/txt_extractor.py` vs `extractors/txt_extractor.py`
- **Severidad:** MEDIO (pero estructural)
- **Descripcion:** Hay DOS implementaciones de cada extractor. Las de **raiz** implementan `TextExtractor` (async) y son usadas por `CompositeDocumentExtractor.create_default()`. Las de **`extractors/`** implementan `DocumentExtractor` (sync) y son usadas por `ExtractorFactory`, que no se usa en la API. Ademas:
  - `hybrid_ner_adapter.py` esta muerto (reemplazado por CompositeNerAdapter)
  - `presentation/` es scaffolding vacio (solo `__init__.py`)
  - `llamacpp_adapter.py` sin dependencia disponible (`llama-cpp-python` comentado en pyproject.toml)
- **Impacto:** Mantenimiento doble, riesgo de que alguien "mejore" el extractor equivocado, y metadatos DOCX (autor = PII) se extraen o no dependiendo del punto de entrada.
- **Recomendacion:** Consolidar en una sola familia de extractores. Eliminar `extractors/` o fusionar sus mejoras (metadatos, fallback pypdf) en los extractores activos. Eliminar codigo muerto confirmado.

---

## DT-3: Modelo de seguridad local roto (sesion global + DB plana)

- **Archivos:** `api/session_manager.py`, `infrastructure/persistence/database.py`
- **Severidad:** CRITICO (seguridad)
- **Descripcion:**
  - `SessionManager` usa `_local_session_id = "local"` hardcoded. Todos los requests comparten la misma sesion en memoria. Sin autenticacion ni separacion de tenencia.
  - `Database` usa `sqlite+aiosqlite` plano sin SQLCipher. `sqlcipher3-binary` esta en dependencias pero nunca se usa.
- **Impacto:** En una red local (el despliegue tipico), cualquier usuario del navegador ve los documentos de todos los demas, y un atacante con acceso al filesystem lee PII directamente del `.db`.
- **Recomendacion:**
  - Corto plazo: generar session_id UUID por cliente y aislar datos.
  - Medio plazo: migrar a base de datos cifrada o cifrar campos sensibles a nivel de aplicacion.

---

## Observacion positiva: Domain y Application estan LIMPIOS

- `grep -r "from contextsafe.(api|infrastructure)" src/contextsafe/domain/` -> **0 imports**
- `grep -r "from contextsafe.(api|infrastructure)" src/contextsafe/application/use_cases/` -> **0 imports directos**

La capa de dominio respeta la regla de independencia. Los use cases usan exclusivamente ports. Esto facilita enormemente la refactorizacion del pipeline de produccion sin tocar la logica de negocio central.

---

## Mapa de dependencias problematicas

```
api/services/document_processor.py
    -> session_manager (infraestructura)        [VIOLACION]
    -> progress_handler (infraestructura WS)     [VIOLACION]
    -> ner_registry (infraestructura)            [VIOLACION]
    -> NO usa GenerateAnonymized (use case)      [DEUDA]

infrastructure/document_processing/
    -> extractors/  vs  raiz/                    [DUPLICACION]

pyproject.toml
    -> sqlcipher3-binary declarado               [NO USADO]
    -> llama-cpp-python comentado                [DEP ROTA]
    -> pytest-cov ausente                        [NO INSTALADO]
```
