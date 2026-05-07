# Checklist — Remediacion Auditoria ContextSafe

> Rama de trabajo: `fix/audit-remediation`

---

## FASE 1: Baseline de Tests (SIN tocar produccion)

- [x] T01 — test: snapping BPE corrige corte de palabra (TF-002)
- [x] T02 — test: synthetic DNI/NIE genera checksum invalido (TF-005)
- [x] T03 — test: GDPR priority sobrevive en overlap de anonimizacion (TF-003)
- [x] T04 — test: voting 3-way discrepancy roberta/spacy/regex (TF-001)
- [x] T05 — test: cobertura de MaskingStrategy y PseudonymStrategy

## FASE 2: Seguridad Rapida

- [x] F01 — fix(api): eliminar textContent de respuesta GET /documents/{id}
- [x] F02 — fix(api): sanitizar errores WebSocket para no filtrar PII
- [x] F03 — fix(api): usar mensaje estatico para DomainError en handler
- [x] F04 — fix(api): CORS fuerza allow_origins desde env en produccion

## FASE 3: Reconocedores

- [x] F11 — fix(nlp): spanish_orgs permite particulas sin rechazar orgs legitimas
- [x] F12 — fix(nlp): regex telefono +34 con boundary correcto
- [x] F13 — fix(nlp): validacion basica de formato CIF
- [x] F14 — fix(nlp): regex nombres con titulo permiten particulas
- [x] F15 — fix(nlp): envolver spacy_adapter y presidio_adapter en run_in_executor

## FASE 4: Infraestructura

- [x] F09 — fix(nlp): evitar inyeccion PowerShell via stdin
- [x] F10 — fix(nlp): delimitadores XML y validacion de entidades LLM
- [x] F07 — fix(docproc): try/except en deteccion de imagenes DOCX
- [x] F05 — fix(api): reemplazar datetime.utcnow() por now(timezone.utc)
- [x] F06 — fix(cli): sincronizar version con pyproject.toml

## FASE 5: Offset Mapping + Glossary Scan

- [x] A1 — feat(nlp): TextNormalizer devuelve OffsetMapping
- [x] A2 — fix(nlp): composite_adapter traduce offsets normalizado a original
- [x] A3 — fix(nlp): glossary_consistency_scan opera sobre texto original

## FASE 6: Persistencia Encriptada

- [x] B1 — feat(persistence): utilidades de cifrado Fernet
- [x] B2 — fix(persistence): repositorios cifran content y glossary

## FASE 7: Arquitectura y Cleanup

- [x] C1 — refactor(docproc): migrar mejoras de extractors/ a raiz
- [x] C2 — chore(docproc): eliminar directorio extractors/ duplicado
- [x] F18 — chore(nlp): eliminar hybrid_ner_adapter muerto
- [x] F17 — fix(deps): anadir psutil a pyproject.toml

## FASE 8: Sesion y WebSocket

- [x] F21 — fix(api): session_manager genera UUID por cliente
- [ ] F22 — fix(api): validar session en WebSocket handshake

## FASE 9: Voting y Entidades Anidadas

- [ ] F19 — fix(nlp): anadir 11 categorias faltantes a RISK_PRIORITY
- [ ] F20 — fix(nlp): mitigar entidades anidadas para categorias sin prioridad

## FASE 10: Tests de Validacion e Idempotencia

- [x] T06 — test(pbt): arreglar asercion test_homoglyph_text_handled
- [ ] T07 — chore(tests): anadir markers pytest y poetry install instrucciones
- [ ] T08 — test(integration): pipeline idempotente NER + anonymize (TF-004)
- [ ] F16 — fix(tests): corregir prefijo /api/v1 -> /v1 en integration tests

---

## Leyenda de Progreso

| Simbolo | Significado |
|---------|-------------|
| [x] | Commit aplicado y testeado |
| [ ] | Pendiente |
| ~~tachado~~ | Descartado o no aplica |

---

## Notas

- Aplicar commits **de 5 en 5**, validando con usuario antes de continuar.
- Cada commit atomico incluye sus tests cuando aplica (FT).
- No usar firmas GPG ni `Signed-off-by` en los commits.
- Baseline inicial: **311 passed** en `tests/unit/`.
