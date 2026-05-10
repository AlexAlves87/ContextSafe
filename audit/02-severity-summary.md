# Tabla Resumen por Severidad

## Conteo Consolidado (eliminando duplicados entre subagentes)

| Severidad | Conteo | Issues principales |
|-----------|--------|-------------------|
| **CRITICO** | 4 | Desfase offsets normalizacion; scan glosario descalibrado; DB sin cifrar; ORG rechaza particulas |
| **ALTO** | 10 | API expone textContent; WS fuga PII; telefono +34 compacto; event loop blocking; inyeccion PS; entidades anidadas; CIF sin validar; nombres con particulas no detectados; PDF multi-columna; OCR fallback insuficiente; generate_anonymized.py huerfano |
| **MEDIO** | 14 | NSS/CP sin validar; voting empates; nombres >5 palabras; divergencia DOCX extractors; DOB mayusculas; CORS credenciales; logs con trazas; dependencias rotas; tests integracion 404; PBT alias substring bug; docx_extractor excepcion imagenes; hybrid_ner_adapter muerto; llamacpp_adapter sin dependencia; metadata_json tipo incorrecto |
| **BAJO** | 12 | Fechas ISO sin validacion; encoding TXT (ya mitigado); scaffolding vacio; version hardcoded; datetime.utcnow() deprecado; pool_pre_ping en SQLite; detect_cpu sin encoding; original_text.count case-sensitive; conftest test_db stub vacio; pytest-cov no instalado; markers inconsistentes; presentation/ vacio |

---

## Detalle por Subagente

### Subagente 1 — Pipeline NLP

| Severidad | Cantidad |
|-----------|----------|
| CRITICO | 2 |
| ALTO | 8 |
| MEDIO | 11 |
| BAJO | 3 |

### Subagente 2 — Seguridad y Arquitectura

| Severidad | Cantidad |
|-----------|----------|
| CRITICO | 3 |
| ALTO | 6 |
| MEDIO | 8 |
| BAJO | 7 |

### Subagente 3 — Tests, Cobertura y Tipos

| Severidad | Cantidad |
|-----------|----------|
| CRITICO | 1 (tests integracion completamente rotos) |
| ALTO | 4 |
| MEDIO | 6 |
| BAJO | 5 |

---

## Distribucion por Capa del Sistema

| Capa | CRITICO | ALTO | MEDIO | BAJO |
|------|---------|------|-------|------|
| Domain | 0 | 0 | 0 | 0 |
| Application | 0 | 1 (use case huerfano) | 1 | 0 |
| Infrastructure NLP | 2 | 6 | 8 | 2 |
| Infrastructure Persistence | 1 | 0 | 2 | 1 |
| API / Routes | 0 | 3 | 3 | 5 |
| Tests | 1 | 0 | 2 | 4 |
| Config/Deps | 0 | 0 | 2 | 0 |

---

*Los 0 en Domain confirman que la capa de dominio respeta la independencia arquitectonica (sin imports de infrastructure/api).*
