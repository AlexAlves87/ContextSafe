# Investigación: Text Normalization para NER en Documentos Legales

**Fecha:** 2026-01-27
**Autor:** AlexAlves87
**Tipo:** Revisión de Literatura Académica
**Estado:** Completado

---

## 1. Resumen Ejecutivo

Esta investigación analiza las mejores prácticas para normalización de texto en pipelines NER, con énfasis en:
1. Normalización Unicode (fullwidth, zero-width, homoglyphs)
2. Corrección de artefactos OCR
3. Integración con modelos transformer

### Hallazgos Principales

| Hallazgo | Fuente | Impacto |
|----------|--------|---------|
| NFKC normaliza fullwidth → ASCII automáticamente | UAX #15 Unicode Standard | Alto |
| Zero-width characters (U+200B-U+200F) deben eliminarse explícitamente | Unicode Consortium | Alto |
| OCR-sensitive neurons existen en transformers y pueden modularse | arXiv:2409.16934 (ICADL 2024) | Medio |
| Preprocessing debe coincidir con pretraining del modelo | Best practices 2024 | Crítico |
| NFKC destruye información en scripts complejos (árabe, hebreo) | UAX #15 | Bajo (no aplica español) |

---

## 2. Metodología

### 2.1 Fuentes Consultadas

| Fuente | Tipo | Año | Relevancia |
|--------|------|-----|------------|
| UAX #15 Unicode Standard | Especificación | 2024 | Normativa Unicode |
| arXiv:2409.16934 | Paper (ICADL 2024) | 2024 | OCR-sensitive neurons |
| TACL Neural OCR Post-Hoc | Paper académico | 2021 | Corrección OCR neural |
| Brenndoerfer NLP Guide | Tutorial técnico | 2024 | Best practices industriales |
| Promptfoo Security | Artículo técnico | 2024 | Evasión Unicode en AI |

### 2.2 Criterios de Búsqueda

- "text normalization NER preprocessing Unicode OCR"
- "Unicode normalization NLP NER fullwidth characters zero-width space"
- "OCR post-correction NER robustness neural network ACL EMNLP"

---

## 3. Resultados

### 3.1 Formas de Normalización Unicode

El estándar Unicode (UAX #15) define 4 formas de normalización:

| Forma | Nombre | Descripción | Uso en NER |
|-------|--------|-------------|------------|
| **NFC** | Canonical Composition | Compone caracteres (é = e + ´) | Estándar |
| **NFD** | Canonical Decomposition | Descompone caracteres | Búsqueda |
| **NFKC** | Compatibility Composition | NFC + compatibilidad | **Recomendado para NER** |
| **NFKD** | Compatibility Decomposition | NFD + compatibilidad | Análisis |

**Fuente:** [UAX #15: Unicode Normalization Forms](https://unicode.org/reports/tr15/)

#### 3.1.1 NFKC para Normalización de Entidades

NFKC es la forma recomendada para NER porque:

```
Fullwidth:  １２３４５６７８ → 12345678
Superscript: ² → 2
Fractions:   ½ → 1/2
Roman:       Ⅳ → IV
Ligatures:   ﬁ → fi
```

**Advertencia:** NFKC destruye información en scripts complejos (árabe, hebreo, devanagari) donde los caracteres de control son semánticamente relevantes. Para español legal, esto no es un problema.

### 3.2 Caracteres Invisibles Problemáticos

**Fuente:** [The Invisible Threat: Zero-Width Unicode Characters](https://www.promptfoo.dev/blog/invisible-unicode-threats/)

| Codepoint | Nombre | Problema | Acción |
|-----------|--------|----------|--------|
| U+200B | Zero Width Space | Rompe tokenización | Eliminar |
| U+200C | Zero Width Non-Joiner | Separa caracteres unidos | Eliminar |
| U+200D | Zero Width Joiner | Une caracteres separados | Eliminar |
| U+200E | Left-to-Right Mark | Confunde dirección texto | Eliminar |
| U+200F | Right-to-Left Mark | Confunde dirección texto | Eliminar |
| U+FEFF | BOM / Zero Width No-Break | Artefacto de encoding | Eliminar |
| U+00A0 | Non-Breaking Space | No detectado por isspace() | → espacio normal |
| U+00AD | Soft Hyphen | Guión invisible | Eliminar |

**Impacto en NER:**
- DNI `123​456​78Z` (con U+200B) no matchea regex `\d{8}[A-Z]`
- Tokenizador divide palabra en múltiples tokens
- Modelo no reconoce la entidad

### 3.3 Homoglyphs y Evasión

**Fuente:** [Invisible Unicode Tricks Bypass AI Detection](https://justdone.com/blog/ai/invisible-unicode-tricks)

| Latino | Cirílico | Visual | Código |
|--------|----------|--------|--------|
| A | А | Idéntico | U+0041 vs U+0410 |
| B | В | Idéntico | U+0042 vs U+0412 |
| E | Е | Idéntico | U+0045 vs U+0415 |
| O | О | Idéntico | U+004F vs U+041E |
| X | Х | Idéntico | U+0058 vs U+0425 |

**Impacto en NER:**
- DNI `12345678Х` (cirílico) no matchea regex con `[A-Z]`
- Modelo puede no reconocer como DNI válido

**Solución:** Normalizar homoglyphs latinos comunes antes de NER.

### 3.4 OCR-Sensitive Neurons en Transformers

**Fuente:** [Investigating OCR-Sensitive Neurons](https://arxiv.org/abs/2409.16934) (ICADL 2024)

#### Hallazgos del Paper

1. **Los transformers tienen neuronas sensibles a OCR:**
   - Identificadas mediante análisis de patrones de activación
   - Responden diferente a texto limpio vs corrupto

2. **Capas críticas identificadas:**
   - Llama 2: Capas 0-2, 11-13, 23-28
   - Mistral: Capas 29-31

3. **Solución propuesta:**
   - Neutralizar neuronas OCR-sensibles
   - Mejora rendimiento NER en documentos históricos

#### Aplicación a ContextSafe

Para nuestro modelo RoBERTa fine-tuned:
- La normalización de texto ANTES de inferencia es más práctica
- Neutralizar neuronas requiere modificar arquitectura del modelo
- **Recomendación:** Preprocesamiento, no modificación de modelo

### 3.5 Errores OCR Comunes y Normalización

**Fuente:** [OCR Data Entry: Preprocessing Text for NLP](https://labelyourdata.com/articles/ocr-data-entry)

| Error OCR | Patrón | Normalización |
|-----------|--------|---------------|
| l ↔ I ↔ 1 | `DNl`, `DN1` | → `DNI` |
| O ↔ 0 | `2l0O` | Contextual (números) |
| rn ↔ m | `nom` → `nom` | Diccionario |
| S ↔ 5 | `E5123` | Contextual |
| B ↔ 8 | `B-123` vs `8-123` | Contextual |

**Estrategia recomendada:**
1. **Preproceso simple:** l/I/1 → normalizar según contexto
2. **Validación posterior:** Checksums (DNI, IBAN) rechazan inválidos
3. **No intentar corregir todo:** Mejor rechazar que inventar

### 3.6 Mismatch Preprocessing-Pretraining

**Fuente:** [Text Preprocessing Guide](https://mbrenndoerfer.com/writing/text-preprocessing-nlp-tokenization-normalization)

> "If you train a model with aggressively preprocessed text but deploy it on minimally preprocessed input, performance will crater."

**Crítico para nuestro modelo:**
- RoBERTa-BNE fue preentrenado con texto case-sensitive
- NO aplicar lowercase
- SÍ aplicar normalización Unicode (NFKC)
- SÍ eliminar zero-width characters

---

## 4. Pipeline de Normalización Propuesto

### 4.1 Orden de Operaciones

```
Texto OCR/Raw
    ↓
[1] Eliminar BOM (U+FEFF)
    ↓
[2] Eliminar zero-width (U+200B-U+200F, U+2060-U+206F)
    ↓
[3] NFKC normalization (fullwidth → ASCII)
    ↓
[4] Normalizar espacios (U+00A0 → espacio, colapsar múltiples)
    ↓
[5] Homoglyph mapping (cirílico común → latino)
    ↓
[6] OCR contextual (DNl → DNI solo si contexto indica)
    ↓
Texto Normalizado → NER
```

### 4.2 Implementación Python

```python
import unicodedata
import re

# Caracteres a eliminar
ZERO_WIDTH = re.compile(r'[\u200b-\u200f\u2060-\u206f\ufeff]')

# Homoglyphs cirílico → latino
HOMOGLYPHS = {
    '\u0410': 'A',  # А → A
    '\u0412': 'B',  # В → B
    '\u0415': 'E',  # Е → E
    '\u041e': 'O',  # О → O
    '\u0421': 'C',  # С → C
    '\u0425': 'X',  # Х → X
    '\u0430': 'a',  # а → a
    '\u0435': 'e',  # е → e
    '\u043e': 'o',  # о → o
    '\u0441': 'c',  # с → c
    '\u0445': 'x',  # х → x
}

def normalize_text(text: str) -> str:
    """
    Normalize text for NER processing.

    Applies: NFKC, zero-width removal, homoglyph mapping, space normalization.
    Does NOT apply: lowercase (RoBERTa is case-sensitive).
    """
    # 1. Remove BOM and zero-width
    text = ZERO_WIDTH.sub('', text)

    # 2. NFKC normalization (fullwidth → ASCII)
    text = unicodedata.normalize('NFKC', text)

    # 3. Homoglyph mapping
    for cyrillic, latin in HOMOGLYPHS.items():
        text = text.replace(cyrillic, latin)

    # 4. Normalize spaces (NBSP → space, collapse multiples)
    text = text.replace('\u00a0', ' ')
    text = re.sub(r' +', ' ', text)

    # 5. Remove soft hyphens
    text = text.replace('\u00ad', '')

    return text.strip()
```

### 4.3 Tests de Validación

| Input | Expected Output | Test |
|-------|-----------------|------|
| `１２３４５６７８Z` | `12345678Z` | Fullwidth |
| `123​456​78Z` | `12345678Z` | Zero-width |
| `12345678Х` | `12345678X` | Cyrillic X |
| `D N I` | `D N I` | Espacios (sin colapsar palabras) |
| `María` | `María` | Acentos preservados |

---

## 5. Análisis de Gaps

### 5.1 Comparación: Práctica Actual vs Best Practices

| Aspecto | Best Practice | Implementación Actual | Gap |
|---------|---------------|----------------------|-----|
| NFKC normalization | Aplicar antes de NER | No implementado | **CRÍTICO** |
| Zero-width removal | Eliminar U+200B-F | No implementado | **CRÍTICO** |
| Homoglyph mapping | Cirílico → Latino | No implementado | ALTO |
| Space normalization | NBSP → espacio | No implementado | MEDIO |
| OCR contextual | DNl → DNI | No implementado | MEDIO |
| Case preservation | NO lowercase | Correcto | ✓ OK |

### 5.2 Impacto Estimado

| Corrección | Esfuerzo | Impacto en Tests |
|------------|----------|------------------|
| NFKC + zero-width | Bajo (10 líneas) | `fullwidth_numbers`: PASS |
| Homoglyph mapping | Bajo (tabla) | `cyrillic_o`: PASS (ya pasa, pero más robusto) |
| Space normalization | Bajo | Reduce FPs en tokenización |
| **Total** | **~50 líneas Python** | **+5-10% pass rate adversarial** |

---

## 6. Conclusiones

### 6.1 Hallazgos Principales

1. **NFKC es suficiente** para normalizar fullwidth → ASCII sin código adicional
2. **Zero-width characters** deben eliminarse explícitamente (regex simple)
3. **Homoglyphs** requieren tabla de mapeo (cirílico → latino)
4. **NO aplicar lowercase** - RoBERTa es case-sensitive
5. **OCR contextual** es complejo - mejor validar con checksums después

### 6.2 Recomendación para ContextSafe

**Implementar `scripts/preprocess/text_normalizer.py`** con:
1. Función `normalize_text()` como se describe arriba
2. Integrar en pipeline de inferencia ANTES del tokenizador
3. Aplicar también durante generación de dataset de entrenamiento

**Prioridad:** ALTA - Resolverá tests `fullwidth_numbers` y mejorará robustez general.

---

## 7. Referencias

### Papers Académicos

1. **Investigating OCR-Sensitive Neurons to Improve Entity Recognition in Historical Documents**
   - arXiv:2409.16934, ICADL 2024
   - URL: https://arxiv.org/abs/2409.16934

2. **Neural OCR Post-Hoc Correction of Historical Corpora**
   - TACL, MIT Press
   - URL: https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00379

### Estándares y Especificaciones

3. **UAX #15: Unicode Normalization Forms**
   - Unicode Consortium
   - URL: https://unicode.org/reports/tr15/

### Recursos Técnicos

4. **Text Normalization: Unicode Forms, Case Folding & Whitespace Handling for NLP**
   - Michael Brenndoerfer, 2024
   - URL: https://mbrenndoerfer.com/writing/text-normalization-unicode-nlp

5. **The Invisible Threat: How Zero-Width Unicode Characters Can Silently Backdoor Your AI-Generated Code**
   - Promptfoo, 2024
   - URL: https://www.promptfoo.dev/blog/invisible-unicode-threats/

6. **OCR Data Entry: Preprocessing Text for NLP Tasks in 2025**
   - Label Your Data
   - URL: https://labelyourdata.com/articles/ocr-data-entry

7. **Zero-width space - Wikipedia**
   - URL: https://en.wikipedia.org/wiki/Zero-width_space

---

**Tiempo de investigación:** 45 min
**Generado por:** AlexAlves87
**Fecha:** 2026-01-27
