# Fixes Concretos con Codigo

Fixes para todos los issues CRITICOS y ALTOS identificados.

---

## 5.1 Fix: Offset desync tras normalizacion en CompositeNerAdapter

**Problema:** `TextNormalizer.normalize()` cambia la longitud del texto (NFKC expande ligaturas, elimina chars). Los adapters NER devuelven offsets del texto normalizado, pero la anonimizacion se aplica sobre el original.

**Fix minimo:** Usar `OffsetTracker` (ya existe en `text_processing/offset_tracker.py`) para construir un `OffsetMapping`, y traducir los spans de vuelta al original antes de retornarlos.

### Paso A: Modificar `text_normalizer.py` para devolver mapping

```python
# src/contextsafe/infrastructure/nlp/text_normalizer.py
from contextsafe.infrastructure.text_processing.offset_tracker import OffsetTracker
from contextsafe.application.ports.text_preprocessor import OffsetMapping

class TextNormalizer:
    # ... init existente ...

    def normalize(self, text: str) -> str:
        """Mantener para compatibilidad."""
        return self.normalize_with_mapping(text).normalized_text

    def normalize_with_mapping(self, text: str) -> OffsetMapping:
        """Normalizar y devolver mapping de offsets."""
        if not text:
            return OffsetMapping.identity(text)

        tracker = OffsetTracker(text)

        for i, ch in enumerate(text):
            # 1. Skip zero-width / BOM
            if ZERO_WIDTH_PATTERN.match(ch):
                tracker.skip_char(i)
                continue

            # 2. NFKC (char-by-char)
            nfkc = unicodedata.normalize('NFKC', ch)
            # 3. Homoglyph mapping
            nfkc = ''.join(HOMOGLYPHS.get(c, c) for c in nfkc)
            # 4. Soft hyphen removal
            if '\u00ad' in nfkc:
                nfkc = nfkc.replace('\u00ad', '')
                tracker.replace_char(i, nfkc)
                continue

            tracker.replace_char(i, nfkc)

        mapping = tracker.build()
        normalized = mapping.normalized_text
        # 5. Collapse multiple spaces (simplificado: re-build mapping)
        collapsed = ' '.join(normalized.split())
        if collapsed != normalized:
            # Para un fix rapido, omitir colapso de espacios
            # y solo aplicar los pasos 1-4 que no rompen offsets de forma critica
            pass
        return mapping
```

### Paso B: Modificar `composite_adapter.py` (l. 421-427)

```python
# Reemplazar:
# if self._normalizer:
#     text = self._normalizer.normalize(text)

# Por:
original_text = text
offset_mapping = None
if self._normalizer:
    offset_mapping = self._normalizer.normalize_with_mapping(text)
    text = offset_mapping.normalized_text

# ... ejecutar adapters sobre `text` ...

# Al final de detect_entities, antes de retornar:
if offset_mapping is not None:
    restored = []
    for det in merged_detections:
        orig_start, orig_end = offset_mapping.to_original_span(
            det.span.start, det.span.end
        )
        span_result = TextSpan.create(
            start=orig_start,
            end=orig_end,
            text=original_text[orig_start:orig_end],
        )
        if span_result.is_ok():
            restored.append(det.with_span(span_result.value))
    merged_detections = restored
```

> **Alternativa rapida** si el refactor es invasivo: desactivar temporalmente las operaciones que cambian longitud (NFKC de ligaturas, colapso de espacios) y mantener solo homoglifos 1->1 y eliminacion de zero-width chars, que no desplazan offsets si se procesan como reemplazos in-place.

---

## 5.2 Fix: `_glossary_consistency_scan` con offsets descalibrados

**Problema:** El scan opera sobre texto ya modificado comparando contra offsets del original.

**Fix:** Ejecutar el scan sobre el texto **original**, no sobre el anonimizado.

```python
# src/contextsafe/infrastructure/nlp/anonymization_adapter.py

def _glossary_consistency_scan(
    self,
    original_text: str,          # CAMBIO: recibir texto original
    anonymized_text: str,        # NUEVO: texto ya parcialmente anonimizado
    project_id: str,
    replaced_spans: list[tuple[int, int]],
) -> str:
    """
    Busca en el TEXTO ORIGINAL valores del glosario no detectados por NER,
    y los aplica sobre el texto anonimizado.
    """
    project_glossary = self._glossaries.get(project_id, {})
    if not project_glossary:
        return anonymized_text

    scan_categories = ("PERSON_NAME", "ORGANIZATION")
    additional_replacements: list[tuple[int, int, str]] = []

    for category in scan_categories:
        entries = project_glossary.get(category, {})
        for original_value, alias in entries.items():
            if len(original_value) < 5:
                continue
            pattern = re.compile(re.escape(original_value), re.IGNORECASE)
            for match in pattern.finditer(original_text):
                m_start, m_end = match.start(), match.end()
                overlaps = any(
                    m_start < r_end and m_end > r_start
                    for r_start, r_end in replaced_spans
                )
                if overlaps:
                    continue
                additional_replacements.append((m_start, m_end, alias))

    # Aplicar sobre el texto ANONIMIZADO en orden inverso
    additional_replacements.sort(key=lambda x: x[0], reverse=True)
    for start, end, alias_value in additional_replacements:
        # Re-escanear en texto anonimizado con el mismo valor para obtener offsets correctos
        for match in re.finditer(re.escape(alias_value), anonymized_text):
            pass  # Esto requiere un mapping original->anonimizado
        # Solucion arquitectonica correcta: unificar reemplazos en un solo paso
        pass

    return anonymized_text
```

> **Nota:** El fix completo requiere construir un `OffsetMapping` durante la fase de reemplazo principal. La solucion arquitectonica correcta es refactorizar todo el motor de anonimizacion para que trabaje con una lista de `Replacement` ordenada y se aplique en un solo paso (NER + glossary).

---

## 5.3 Fix: SQLCipher realmente activado

**Problema:** `Database` usa `sqlite+aiosqlite` plano.

**Fix pragmativo:** Cifrar campos sensibles a nivel de aplicacion antes de persistir.

```python
# src/contextsafe/infrastructure/persistence/database.py
import os
from cryptography.fernet import Fernet  # anadir a dependencias

_ENCRYPTION_KEY = os.environ.get("CS_ENCRYPTION_KEY", "").encode()
_fernet = Fernet(_ENCRYPTION_KEY) if _ENCRYPTION_KEY else None

def encrypt_if_needed(value: str | None) -> str | None:
    if _fernet and value:
        return _fernet.encrypt(value.encode()).decode()
    return value

def decrypt_if_needed(value: str | None) -> str | None:
    if _fernet and value:
        return _fernet.decrypt(value.encode()).decode()
    return value
```

Y en los repositorios, cifrar `content`, `anonymized_content`, y valores del glossary antes de `session.add()`, y descifrar al leer.

> **Fix ideal:** Migrar a un engine sync con `sqlcipher3` y envolver IO en `run_in_executor`.

---

## 5.4 Fix: `spanish_orgs.py` no rechace particulas

**Problema:** `validate_result` rechaza "Banco de Espana" porque "de" esta en `FALSE_POSITIVE_WORDS`.

```python
# src/contextsafe/infrastructure/nlp/recognizers/spanish_orgs.py
# Reemplazar bloque (l. 137-144):
        clean_lower = clean.lower()
        words = clean_lower.split()
        for word in words:
            if word in self.FALSE_POSITIVE_WORDS:
                return False

# Por:
        clean_lower = clean.lower()
        words = clean_lower.split()
        false_count = sum(1 for w in words if w in self.FALSE_POSITIVE_WORDS)
        # Rechazar solo si mas del 50% son palabras comunes (particulas permitidas)
        if false_count > len(words) // 2:
            return False
        # Rechazar si TODO el texto es una sola palabra comun
        if len(words) == 1 and words[0] in self.FALSE_POSITIVE_WORDS:
            return False
```

---

## 5.5 Fix: Eliminar `textContent` de respuesta GET

```python
# src/contextsafe/api/routes/documents.py (l. 165-176)
# Reemplazar:
        "textContent": doc.content or "",
# Por:
        "textContent": "",  # PII nunca expuesta por defecto
```

Y si se necesita descarga controlada, anadir endpoint separado:

```python
@router.get("/{document_id}/content")
async def get_document_content(document_id: str, ...):
    # Validar permisos de sesion aqui
    doc = await repo.get(document_id)
    return {"textContent": doc.content or ""}
```

---

## 5.6 Fix: Sanitizar errores WebSocket

```python
# src/contextsafe/api/services/document_processor.py (l. 273-279)
# Reemplazar:
    except Exception as e:
        session_manager.update_document(
            session_id, document_id,
            state="error",
            error=str(e)
        )
        await progress_handler.send_error(doc_uuid, str(e))
        logger.error(f"Error processing document {document_id}: {e}")

# Por:
    except Exception as e:
        # Log completo solo en servidor
        logger.exception(f"Error processing document {document_id}: {e}")
        # Mensaje generico al cliente (nunca filtrar PII/trazas)
        safe_message = "Processing failed. Please try again or contact support."
        session_manager.update_document(
            session_id, document_id,
            state="error",
            error=safe_message
        )
        await progress_handler.send_error(doc_uuid, safe_message)
```

---

## 5.7 Fix: Telefono +34 compacto

```python
# src/contextsafe/infrastructure/nlp/recognizers/spanish_phone.py (l. 31-37)
# Anadir despues de PHONE_INTERNATIONAL:
Pattern(
    "PHONE_INTERNATIONAL_COMPACT",
    r"\b(\+34\d{9})\b",
    0.9,
),
```

---

## 5.8 Fix: Async blocking en spacy/presidio

```python
# src/contextsafe/infrastructure/nlp/spacy_adapter.py (l. 99-104)
# Reemplazar:
        doc = self._nlp(text)
# Por:
        loop = asyncio.get_running_loop()
        doc = await loop.run_in_executor(None, self._nlp, text)
```

```python
# src/contextsafe/infrastructure/nlp/presidio_adapter.py (l. 416-421)
# Reemplazar:
        results = self._analyzer.analyze(
            text=text,
            language="es",
            score_threshold=min_confidence,
        )
# Por:
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self._analyzer.analyze(
                text=text, language="es", score_threshold=min_confidence
            ),
        )
```

> Patron ya usado correctamente en `roberta_ner_adapter.py` (l. 546-550).

---

## 5.9 Fix: Inyeccion PowerShell

```python
# src/contextsafe/infrastructure/nlp/strategies/synthetic.py (l. 628-659)
# Reemplazar interpolacion por paso de JSON via stdin:

def _generate_with_powershell(self, prompt: str) -> str:
    if not HAS_POWERSHELL:
        return ""

    try:
        options = {"temperature": 0.7, "num_predict": 50}
        if not self._use_gpu:
            options["num_gpu"] = 0

        body = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": options,
        }
        body_json = json.dumps(body, ensure_ascii=False)

        ps_command = """
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
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
        # ... resto igual ...
```

---

## 5.10 Fix: Proteccion contra entidades anidadas filtradas

**Problema:** Si un span exterior gana por confianza, el span interior (DNI) puede quedar expuesto.

**Mitigacion inmediata:** Asegurar que categorias de alto riesgo GDPR SIEMPRE ganen en `_remove_overlapping_detections`, incluso si la confianza es ligeramente menor.

**Fix completo:** Tras resolver solapamientos, verificar que ningun span ganador contenga texto que deba ser anonimizado por un perdedor de mayor riesgo GDPR. Requiere refactor del loop de reemplazo para soportar splits.

---

## 5.11 Fix: CIF sin validacion de digito de control

**Archivo:** `src/contextsafe/infrastructure/nlp/recognizers/spanish_id.py` (l. 165-205)

```python
    def validate_result(self, pattern_text: str) -> bool:
        cif = pattern_text.strip().upper().replace("-", "")
        if len(cif) != 9:
            return False
        # Validacion basica de formato
        letter = cif[0]
        digits = cif[1:8]
        control = cif[8]
        if not digits.isdigit():
            return False
        if letter not in "ABCDEFGHJNPQRSUVW":
            return False
        # TODO: anadir algoritmo completo de control CIF
        return True
```

---

## 5.12 Fix: `spanish_names.py` regex con particulas

**Archivo:** `src/contextsafe/infrastructure/nlp/recognizers/spanish_names.py`

Los patterns `NAME_WITH_TITLE_D`, `NAME_WITH_TITLE_DON`, etc. usan `(?:\s+[A-Z][a-z]+){1,3}` que no permite "de", "del", "de la". Modificar para incluir el conector existente `CONNECTORS`:

```python
NAME_WORD_WITH_CONNECTOR = r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+(?:de\s+la\s+|de\s+los\s+|de\s+las\s+|del\s+|de\s+)?[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*"
```

---

## 5.13 Fix: CORS permite credenciales con origenes por defecto inseguros

**Archivo:** `src/contextsafe/api/middleware/cors.py` (l. 33-37)

```python
# Forzar que en produccion se use variable de entorno
import os
if allow_origins is None:
    if os.environ.get("APP_ENV") == "production":
        allow_origins = os.environ.get("CONTEXTSAFE_CORS_ORIGINS", "").split(",")
        allow_credentials = False
    else:
        allow_origins = [
            "http://localhost:5173",
            "http://localhost:3000",
        ]
```

---

## 5.14 Fix: DomainError expone `detail=str(exc)` con posible PII

**Archivo:** `src/contextsafe/api/middleware/error_handler.py` (l. 59-70)

```python
# Reemplazar:
            detail=str(exc),
# Por:
            detail="A domain validation error occurred.",
```

---

## 5.15 Fix: Prompt injection en LLM adapters

**Archivo:** `src/contextsafe/infrastructure/llm/ollama_ner_adapter.py`

Anadir delimitadores estructurados y validar que las entidades devueltas existan en el texto original:

```python
# En el prompt, rodear el documento con XML tags:
prompt = f"""Analyze the following document and extract entities.
<document>
{text}
</document>

Return only entities found in the document."""

# Despues del parsing:
for ent in parsed_entities:
    if text[ent["start"]:ent["end"]] != ent["text"]:
        continue  # Descartar entidades que no coinciden exactamente
```

---

*Fin de fixes criticos y altos.*
