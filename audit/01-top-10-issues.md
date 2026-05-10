# TOP 10 Issues ordenados por impacto real

Ordenados por riesgo de que PII quede sin anonimizar o de corrupcion de datos.

---

## 1. Desfase CRITICO de offsets tras normalizacion de texto

- **Archivo:** `src/contextsafe/infrastructure/nlp/composite_adapter.py` (l. 423-424)
- **Severidad:** CRITICO
- **Impacto:** `TextNormalizer.normalize()` aplica NFKC (expansion de ligaturas: fi -> fi), elimina zero-width chars y colapsa espacios. Los adapters NER devuelven offsets relativos al texto normalizado, pero la anonimizacion se aplica sobre el texto original. Cualquier caracter que cambie de longitud desplaza todos los offsets posteriores. Esto corta texto incorrecto o deja PII sin reemplazar.
- **Fix:** Ver `05-fixes-critical-high.md` seccion 5.1.

---

## 2. `_glossary_consistency_scan` opera sobre texto modificado con offsets del original

- **Archivo:** `src/contextsafe/infrastructure/nlp/anonymization_adapter.py` (l. 489-553)
- **Severidad:** CRITICO
- **Impacto:** Tras reemplazar una entidad larga por un alias corto, las posiciones del texto cambian. El scan busca ocurrencias del glosario en el texto ya modificado, pero `replaced_spans` contiene coordenadas del texto original. Genera falsos negativos masivos (nombres repetidos que no se re-anonimizan) y falsos positivos (reemplazar dentro de un alias previo).
- **Fix:** Ver `05-fixes-critical-high.md` seccion 5.2.

---

## 3. SQLCipher declarado pero NUNCA utilizado — base de datos en texto plano

- **Archivo:** `pyproject.toml`, `src/contextsafe/infrastructure/persistence/database.py`
- **Severidad:** CRITICO
- **Impacto:** `sqlcipher3-binary` esta en dependencias, pero Database usa `sqlite+aiosqlite:///`. El fichero `data/contextsafe.db` es SQLite plano. Todos los documentos, glossary con PII original y metadatos sensibles persisten sin cifrar.
- **Fix:** Ver `05-fixes-critical-high.md` seccion 5.3.

---

## 4. `spanish_orgs.py` rechaza organizaciones legitimas con particulas

- **Archivo:** `src/contextsafe/infrastructure/nlp/recognizers/spanish_orgs.py` (l. 138-140)
- **Severidad:** CRITICO
- **Impacto:** `FALSE_POSITIVE_WORDS` incluye "de", "del", "la", "los". La validacion itera palabra por palabra y rechaza si cualquiera esta en la lista. Descarta "Banco de Espana", "Compania del Sur", "Hijos de Rodriguez", etc. Falsos negativos masivos en documentos judiciales.
- **Fix:** Ver `05-fixes-critical-high.md` seccion 5.4.

---

## 5. Endpoint GET expone `textContent` completo con PII intacta

- **Archivo:** `src/contextsafe/api/routes/documents.py` (l. 175)
- **Severidad:** ALTO
- **Impacto:** `GET /v1/documents/{document_id}` devuelve el campo `"textContent": doc.content or ""`, que es el texto original sin anonimizar. Sin autenticacion ni control de acceso por sesion, cualquier cliente con el UUID puede leer PII.
- **Fix:** Ver `05-fixes-critical-high.md` seccion 5.5.

---

## 6. Fuga de PII por WebSocket en errores de procesamiento

- **Archivo:** `src/contextsafe/api/services/document_processor.py` (l. 273-279)
- **Severidad:** ALTO
- **Impacto:** El `except Exception` captura fallos y retransmite `str(e)` via WebSocket sin sanitizar. Si la excepcion incluye fragmentos del texto procesado, paths o trazas, se filtra PII al cliente.
- **Fix:** Ver `05-fixes-critical-high.md` seccion 5.6.

---

## 7. Telefonos internacionales +34 compactos no detectados

- **Archivo:** `src/contextsafe/infrastructure/nlp/recognizers/spanish_phone.py` (l. 35)
- **Severidad:** ALTO
- **Impacto:** El patron `PHONE_INTERNATIONAL` exige separadores entre grupos de 3 digitos. Un numero real y muy comun como `+34612345678` (9 digitos seguidos) no se detecta.
- **Fix:** Ver `05-fixes-critical-high.md` seccion 5.7.

---

## 8. Bloqueo del event loop async en adapters NLP

- **Archivo:** `src/contextsafe/infrastructure/nlp/spacy_adapter.py` (l. 104), `presidio_adapter.py` (l. 417)
- **Severidad:** ALTO
- **Impacto:** `self._nlp(text)` y `self._analyzer.analyze(...)` son llamadas bloqueantes de CPU dentro de `async def detect_entities` sin `run_in_executor`. Congelan el event loop de FastAPI: WebSockets dejan de responder, requests encolan y pueden timeout, dejando documentos sin procesar (PII sin anonimizar).
- **Fix:** Ver `05-fixes-critical-high.md` seccion 5.8.

---

## 9. Inyeccion de comandos PowerShell en estrategia synthetic

- **Archivo:** `src/contextsafe/infrastructure/nlp/strategies/synthetic.py` (l. 646-653)
- **Severidad:** ALTO
- **Impacto:** El JSON del prompt (que contiene texto del documento) se interpola directamente en un string de PowerShell. Un documento con contenido malicioso puede romper la estructura del script y ejecutar codigo arbitrario.
- **Fix:** Ver `05-fixes-critical-high.md` seccion 5.9.

---

## 10. Entidades anidadas pueden filtrarse si gana el span exterior

- **Archivo:** `src/contextsafe/infrastructure/nlp/anonymization_adapter.py` (l. 226-290)
- **Severidad:** ALTO
- **Impacto:** `_remove_overlapping_detections` descarta spans solapados por prioridad GDPR. Si un DNI esta contenido dentro de una direccion y la direccion gana (por confianza alta o bug de voting), el DNI no se reemplaza y queda expuesto en el texto final.
- **Fix:** Ver `05-fixes-critical-high.md` seccion 5.10.

---

*Ver fixes concretos en `05-fixes-critical-high.md`.*
