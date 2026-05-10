# Auditoria Subagente 1 — Pipeline NLP y Logica de Anonimizacion

Archivos principales auditados:
- `src/contextsafe/infrastructure/nlp/`
- `src/contextsafe/infrastructure/text_processing/`
- `src/contextsafe/domain/entity_detection/`
- `ml/gazetteers/`

---

## 1. Falsos Negativos / Positivos en Deteccion de PII

### 1.1 `spanish_phone.py` — Falso negativo en moviles +34 compactos
- **Archivo:** `src/contextsafe/infrastructure/nlp/recognizers/spanish_phone.py` (l. 35)
- **Severidad:** ALTO
- **Descripcion:** El patron `PHONE_INTERNATIONAL` exige separadores entre grupos de 3 digitos. Un numero compacto como `+34612345678` no se detecta.
- **Ejemplo:** Texto: `Llame al +34612345678.` -> No detecta telefono.

### 1.2 `spanish_id.py` — CIF sin validacion de digito de control
- **Archivo:** `src/contextsafe/infrastructure/nlp/recognizers/spanish_id.py` (l. 165-205)
- **Severidad:** ALTO
- **Descripcion:** `SpanishCIFRecognizer` no implementa `validate_result`. Cualquier cadena como `A12345678` pasa como CIF valido.
- **Ejemplo:** `A00000000` se acepta sin rechazo.

### 1.3 `spanish_id.py` — NSS sin validacion de digitos de control
- **Archivo:** `src/contextsafe/infrastructure/nlp/recognizers/spanish_id.py` (l. 252-263)
- **Severidad:** MEDIO
- **Descripcion:** Solo comprueba provincia 01-52. No valida los 2 digitos de control finales (algoritmo mod 97 del NAF).
- **Ejemplo:** `28/00000000/99` -> provincia 28 valida -> aceptado.

### 1.4 `spanish_dates.py` — Validacion laxa de fechas numericas invalidas
- **Archivo:** `src/contextsafe/infrastructure/nlp/recognizers/spanish_dates.py` (l. 114-143)
- **Severidad:** MEDIO
- **Descripcion:** Comprueba dia 1-31 y mes 1-12, pero no valida coherencia de dias por mes (ej. 31/02/2025) ni anos bisiestos.

### 1.5 `spanish_location.py` — CP con falsos positivos masivos
- **Archivo:** `src/contextsafe/infrastructure/nlp/recognizers/spanish_location.py` (l. 34-44)
- **Severidad:** ALTO
- **Descripcion:** Usa `r"\b(\d{5})\b"` con confianza 0.92. Cualquier secuencia de 5 digitos (anos, numeros de factura) se detecta como CP.

---

## 2. Logica de Merge y Votacion

### 2.1 `composite_adapter.py` — DESFASE CRITICO DE OFFSETS tras normalizacion
- **Archivo:** `src/contextsafe/infrastructure/nlp/composite_adapter.py` (l. 423-424)
- **Severidad:** CRITICO
- **Descripcion:** El adaptador normaliza el texto con `TextNormalizer.normalize(text)` y pasa ese texto normalizado a todos los adapters. Los adapters devuelven offsets relativos al texto normalizado. Nunca se traducen los offsets de vuelta al texto original.
- **Impacto:** Si NFKC expande un caracter (ej. ligatura fi -> fi), todos los offsets posteriores al cambio se desplazan.
- **Ejemplo:** Texto: `Señor final 12345678Z` (fi es U+FB01, 1 char). NFKC convierte a `fi` (2 chars). El DNI empieza en original en pos 12, pero en normalizado en pos 13. Al reemplazar en texto original: `text[13:22]` corta 1 caracter desplazado.
- **Fix:** Integrar `OffsetMapping` en la pipeline de NER. Ver `05-fixes-critical-high.md`.

### 2.2 `composite_adapter.py` — `_group_overlapping_detections` crea grupos transitivos no deseados
- **Archivo:** `src/contextsafe/infrastructure/nlp/composite_adapter.py` (l. 595-645)
- **Severidad:** MEDIO
- **Descripcion:** Agrupa detecciones transitivamente por IoU >= threshold. Si A solapa con B, y B solapa con C (pero A y C no se solapan), A, B y C quedan en el mismo grupo. Luego `_resolve_by_voting` elige un unico ganador para todo el grupo, descartando A o C.
- **Ejemplo:** A="Juan" (0-4), B="Juan Garcia" (0-11), C="Garcia Lopez" (5-15). A y C nunca se solapan, pero solo gana una deteccion. C se pierde.

### 2.3 `composite_adapter.py` — `_resolve_by_voting` favorece spans mas largos con texto adicional
- **Archivo:** `src/contextsafe/infrastructure/nlp/composite_adapter.py` (l. 675-682)
- **Severidad:** MEDIO
- **Descripcion:** Tras votar la categoria, elige la deteccion con mayor `(span_length, weighted_score)`. Si un modelo detecta `"Juan "` (con espacio, 5 chars) y otro `"Juan"` (4 chars), gana el primero, dejando doble espacio.

### 2.4 `merge/voting.py` — Categorias nuevas sin prioridad GDPR
- **Archivo:** `src/contextsafe/infrastructure/nlp/merge/voting.py` (l. 68-86)
- **Severidad:** MEDIO
- **Descripcion:** `RISK_PRIORITY` no incluye `PROFESSIONAL_ID`, `ID_SUPPORT`, `NIG`, `ECLI`, `CSV`, `HEALTH_ID`, `CADASTRAL_REF`, `EMPLOYER_ID`. En empate tecnico, estas categorias obtienen prioridad 0 y pierden siempre.

### 2.5 `merge/anchors.py` — Anchors de ORG fuerzan categoria sin verificar entidad
- **Archivo:** `src/contextsafe/infrastructure/nlp/merge/anchors.py` (l. 192-196)
- **Severidad:** MEDIO
- **Descripcion:** Si el contexto contiene `banco`, `juzgado de`, etc., fuerza `ORGANIZATION`. Pero si el modelo solo detecto `"Espana"` dentro de `"Banco de Espana"`, `"Espana"` se fuerza a ORG en lugar de LOCATION.

---

## 3. Motor de Anonimizacion

### 3.1 `anonymization_adapter.py` — `_glossary_consistency_scan` usa offsets originales sobre texto MODIFICADO
- **Archivo:** `src/contextsafe/infrastructure/nlp/anonymization_adapter.py` (l. 489-553)
- **Severidad:** CRITICO
- **Descripcion:** El scan busca valores del glosario en el texto ya parcialmente anonimizado. Los reemplazos anteriores cambian la longitud del texto, pero `replaced_spans` contiene offsets del texto original.
- **Ejemplo:** Texto: `Alberto Baxeras Aizpun vive aqui. Alberto Baxeras firmo.` Primera ocurrencia reemplazada por `Persona_001` (11 vs 22 chars). Segunda ocurrencia estaba originalmente en pos 27, pero en texto modificado esta en pos ~16. El overlap check usa coordenadas descalibradas y se salta el reemplazo.

### 3.2 `anonymization_adapter.py` — Sustitucion inversa puede duplicar espacios
- **Archivo:** `src/contextsafe/infrastructure/nlp/anonymization_adapter.py` (l. 450-452)
- **Severidad:** MEDIO
- **Descripcion:** `after_char = anonymized[end:end + 1]` y `space_suffix = " " if after_char.isalnum() else ""`. Si la entidad detectada incluye espacio final, se anade otro espacio.

### 3.3 `anonymization_adapter.py` — Entidades anidadas pueden filtrarse
- **Archivo:** `src/contextsafe/infrastructure/nlp/anonymization_adapter.py` (l. 226-290)
- **Severidad:** ALTO
- **Descripcion:** `_remove_overlapping_detections` descarta solapamientos por prioridad GDPR. Si una entidad A esta completamente contenida dentro de B y B gana, A no se anonimiza. Ej: DNI dentro de direccion, si direccion gana -> DNI expuesto.

### 3.4 `strategies/synthetic.py` — Riesgo de inyeccion en payload JSON/PowerShell
- **Archivo:** `src/contextsafe/infrastructure/nlp/strategies/synthetic.py` (l. 628-675)
- **Severidad:** ALTO
- **Descripcion:** Se construye un JSON con `json.dumps(body)` y se interpola en un string de PowerShell. Aunque `json.dumps` escapa comillas, no hay sanitizacion de secuencias de escape de PowerShell.
- **Fix:** Usar `stdin` para pasar el JSON. Ver `05-fixes-critical-high.md`.

---

## 4. Recognizers Custom

### 4.1 `spanish_orgs.py` — `validate_result` rechaza organizaciones legitimas con particulas
- **Archivo:** `src/contextsafe/infrastructure/nlp/recognizers/spanish_orgs.py` (l. 138-140)
- **Severidad:** CRITICO
- **Descripcion:** `FALSE_POSITIVE_WORDS` incluye `"de"`, `"del"`, `"la"`, etc. La validacion rechaza cualquier organizacion que contenga estas particulas.
- **Ejemplo:** `"Banco de Espana S.A."` -> `validate_result` ve `"de"` -> devuelve False -> falso negativo.

### 4.2 `spanish_names.py` — No valida nombres compuestos contra gazetteers
- **Archivo:** `src/contextsafe/infrastructure/nlp/recognizers/spanish_names.py` (l. 236-237)
- **Severidad:** ALTO
- **Descripcion:** `validate_result` solo comprueba el gazetteer para nombres de una sola palabra. Nombres compuestos no reciben validacion adicional.

### 4.3 `spanish_names.py` — Rechaza nombres legitimos de >5 palabras
- **Archivo:** `src/contextsafe/infrastructure/nlp/recognizers/spanish_names.py` (l. 240-241)
- **Severidad:** MEDIO
- **Descripcion:** `if len(words) > 5: return False`. Nombres como `"Maria de los Angeles de la Cruz"` (7 palabras) se rechazan.

### 4.4 `spanish_names.py` — Regex no manejan particulas en nombres con titulo
- **Archivo:** `src/contextsafe/infrastructure/nlp/recognizers/spanish_names.py` (l. 60, 66, 72, etc.)
- **Severidad:** ALTO
- **Descripcion:** Los patterns `NAME_WITH_TITLE_D`, `NAME_WITH_TITLE_DON`, etc. usan `(?:\s+[A-Z][a-z]+){1,3}` que no permite `"de"`, `"del"`, `"de la"`. `"D. Juan de la Cruz"` no matchea.

### 4.5 `legal_titles.py` — No detecta nombres en mayusculas antes de titulo
- **Archivo:** `src/contextsafe/infrastructure/nlp/recognizers/legal_titles.py` (l. 49-63)
- **Severidad:** MEDIO
- **Descripcion:** Requieren nombre que empiece con mayuscula seguida de minusculas. Nombres completamente en mayusculas (comunes en cabeceras judiciales) no se detectan.

### 4.6 `legal_titles.py` — Coreference boost puede amplificar falsos positivos
- **Archivo:** `src/contextsafe/infrastructure/nlp/composite_adapter.py` (l. 745-809)
- **Severidad:** MEDIO
- **Descripcion:** Si un documento menciona `"D. Santiago Garcia"`, el sistema anade `"SANTIAGO"` a `confirmed_first_names`. Cualquier aparicion suelta de `"Santiago"` detectada como PERSON con confianza <0.75 se boostea a 0.85. Pero `"Santiago"` es tambien una ciudad (LOCATION).

### 4.7 `spanish_location.py` — `SpanishAddressRecognizer` regex permisivos
- **Archivo:** `src/contextsafe/infrastructure/nlp/recognizers/spanish_location.py` (l. 96-119)
- **Severidad:** MEDIO
- **Descripcion:** `ADDRESS_FULL` usa `[^,\n]{3,50}` que es extremadamente permisivo y puede capturar texto no direccional.

---

## 5. Procesado de Documentos

### 5.1 `pdf_extractor.py` — Sin soporte para layouts multi-columna
- **Archivo:** `src/contextsafe/infrastructure/document_processing/pdf_extractor.py` (l. 74)
- **Severidad:** ALTO
- **Descripcion:** `page.extract_text()` de pdfplumber extrae texto linea por linea sin respetar layout. En PDFs multi-columna, el texto se mezcla.

### 5.2 `pdf_extractor.py` — OCR fallback insuficiente
- **Archivo:** `src/contextsafe/infrastructure/document_processing/pdf_extractor.py` (l. 92-106)
- **Severidad:** ALTO
- **Descripcion:** OCR solo se activa si `len(page_text.strip()) < 50`. PDFs escaneados con texto OCR basura que supera 50 chars no se re-OCR-izan.

### 5.3 Divergencia entre dos implementaciones de `DocxExtractor`
- **Archivo:** `docx_extractor.py` (raiz) vs `extractors/docx_extractor.py`
- **Severidad:** MEDIO
- **Descripcion:** Raiz no extrae headers/footers ni metadata. Extractors/ si. `CompositeDocumentExtractor.create_default()` usa la raiz. `ExtractorFactory` usa extractors/. Resultados diferentes.

### 5.4 `docx_extractor.py` (raiz) — Excepcion no manejada en deteccion de imagenes
- **Archivo:** `src/contextsafe/infrastructure/document_processing/docx_extractor.py` (l. 69-72)
- **Severidad:** MEDIO
- **Descripcion:** `for rel in doc.part.rels.values()` no esta en try/except. Si `doc.part` no esta disponible, lanza excepcion y devuelve texto vacio.

### 5.5 `ocr/tesseract_adapter.py` — Sin validacion de confianza minima OCR
- **Archivo:** `src/contextsafe/infrastructure/ocr/tesseract_adapter.py` (l. 95-120)
- **Severidad:** MEDIO
- **Descripcion:** Se calcula `avg_confidence` pero no se rechaza si es demasiado bajo. Imagen borrosa con confianza 0.15 se considera exitosa.

### 5.6 `txt_extractor.py` — Asume UTF-8 (mitigado)
- **Archivo:** `src/contextsafe/infrastructure/document_processing/txt_extractor.py`
- **Severidad:** BAJO
- **Nota:** El extractor de raiz YA implementa fallback de encodings (`utf-8`, `latin-1`, `cp1252`, `iso-8859-1` + `chardet`). El subagente detecto que la version en `extractors/` podria no tenerlo.

---

## Resumen NLP

| Severidad | Cantidad |
|-----------|----------|
| CRITICO | 2 |
| ALTO | 8 |
| MEDIO | 11 |
| BAJO | 3 |
