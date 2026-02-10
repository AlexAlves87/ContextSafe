"""
Text normalization functions.

Pure functions for normalizing text. No state, no I/O.

Traceability:
- Design: docs/plans/2026-02-01-text-preprocessing-design.md
- Bounded Context: BC-001 (DocumentProcessing)
"""
from __future__ import annotations

import re
import unicodedata


# ============================================================================
# FASE 1: Normalización permanente (IngestDocument)
# Operaciones que NO cambian semántica ni offsets lógicos significativos.
# ============================================================================


def sanitize_encoding(raw_bytes: bytes, fallback: str = "utf-8") -> str:
    """
    Decodificar bytes a string con fallbacks.

    NOTA: Solo usar para input desde bytes (OCR/legacy).
    Si ya tienes str, NO usar esta función.

    Args:
        raw_bytes: Bytes crudos
        fallback: Encoding preferido

    Returns:
        String decodificado
    """
    for encoding in [fallback, "utf-8", "latin-1", "cp1252"]:
        try:
            return raw_bytes.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw_bytes.decode("utf-8", errors="replace")


def normalize_unicode(text: str) -> str:
    """
    Normalizar a Unicode NFKC.

    NFKC es mejor que NFC para OCR porque:
    - fi ligature (U+FB01) -> "fi"
    - superscripts (²) -> "2"
    - fullwidth chars -> normal

    Args:
        text: Texto a normalizar

    Returns:
        Texto en forma NFKC
    """
    return unicodedata.normalize("NFKC", text)


def normalize_line_endings(text: str) -> str:
    """
    Normalizar line endings a LF.

    \\r\\n (Windows) -> \\n
    \\r (old Mac) -> \\n

    Args:
        text: Texto con line endings mixtos

    Returns:
        Texto con solo \\n
    """
    return text.replace("\r\n", "\n").replace("\r", "\n")


def normalize_whitespace_chars(text: str) -> str:
    """
    Normalizar espacios no separables a espacio normal.

    Incluye:
    - NBSP (U+00A0)
    - Figure space (U+2007)
    - Narrow NBSP (U+202F)
    - Word joiner (U+2060)

    Args:
        text: Texto con espacios especiales

    Returns:
        Texto con espacios normales
    """
    return re.sub(r"[\u00A0\u2007\u202F\u2060]", " ", text)


def remove_control_chars(text: str) -> str:
    """
    Eliminar caracteres de control excepto \\n, \\t.

    Elimina:
    - NUL, SOH, STX, etc. (0x00-0x08)
    - VT (0x0B)
    - FF (0x0C)
    - SO, SI, DLE, etc. (0x0E-0x1F)
    - DEL (0x7F)

    Preserva:
    - TAB (0x09)
    - LF (0x0A)
    - CR (0x0D) - se normaliza en normalize_line_endings

    Args:
        text: Texto con caracteres de control

    Returns:
        Texto limpio
    """
    return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)


# ============================================================================
# FASE 2: Normalización temporal (DetectPii)
# Operaciones que SÍ pueden cambiar longitud.
# Usar con OffsetTracker para mantener mapa de posiciones.
# ============================================================================


QUOTE_MAP = {
    "\u201c": '"',  # " left double
    "\u201d": '"',  # " right double
    "\u201e": '"',  # „ double low-9
    "\u00ab": '"',  # « left guillemet
    "\u00bb": '"',  # » right guillemet
    "\u2018": "'",  # ' left single
    "\u2019": "'",  # ' right single
    "\u201a": "'",  # ‚ single low-9
}


def normalize_quotes(text: str) -> str:
    """
    Normalizar comillas tipográficas a rectas.

    Convierte:
    - "" -> "
    - '' -> '
    - «» -> "

    Args:
        text: Texto con comillas tipográficas

    Returns:
        Texto con comillas rectas
    """
    return text.translate(str.maketrans(QUOTE_MAP))


DASH_PATTERN = re.compile(r"[–—−\u2010\u2011\u2012\u2013\u2014\u2015]")


def normalize_dashes(text: str) -> str:
    """
    Normalizar guiones tipográficos a guion normal.

    Convierte:
    - – (en dash)
    - — (em dash)
    - − (minus sign)
    - ‐‑‒ (hyphens)

    Args:
        text: Texto con guiones tipográficos

    Returns:
        Texto con guiones normales (-)
    """
    return DASH_PATTERN.sub("-", text)


# Pattern para letras sueltas separadas por espacio (OCR error)
# Solo lowercase para ser conservador y no romper siglas
OCR_LETTER_SPACING_PATTERN = re.compile(
    r"\b([a-záéíóúüñ])(?: ([a-záéíóúüñ])){2,}\b",
    re.IGNORECASE,
)


def fix_ocr_letter_spacing(text: str) -> str:
    """
    Corregir letras separadas por espacios (error común de OCR).

    Ejemplo: "J u a n" -> "Juan"

    NOTA: Solo aplica a secuencias de 3+ letras lowercase separadas.
    Conservador para evitar romper siglas como "A B C".

    Args:
        text: Texto con posibles errores de OCR

    Returns:
        Texto corregido
    """

    def join_letters(match: re.Match) -> str:
        return "".join(c for c in match.group(0) if c != " ")

    return OCR_LETTER_SPACING_PATTERN.sub(join_letters, text)


def fix_ocr_linebreaks(text: str) -> str:
    """
    Corregir saltos de línea dentro de palabras (error de OCR).

    Ejemplo: "Juan\\nGarcía" -> "Juan García"

    Solo aplica cuando hay letra antes y después del \\n.

    Args:
        text: Texto con posibles linebreaks incorrectos

    Returns:
        Texto corregido
    """
    return re.sub(r"(\w)\n(\w)", r"\1 \2", text)


def collapse_spaces(text: str) -> str:
    """
    Colapsar espacios múltiples a uno solo.

    Ejemplo: "Juan   García" -> "Juan García"

    Args:
        text: Texto con espacios múltiples

    Returns:
        Texto con espacios simples
    """
    return re.sub(r" +", " ", text)


# ============================================================================
# FUNCIONES COMPUESTAS (para uso directo en preprocessors)
# ============================================================================


def apply_ingest_normalization(text: str) -> str:
    """
    Aplicar todas las normalizaciones de Fase 1.

    Args:
        text: Texto crudo

    Returns:
        Texto normalizado (fase 1)
    """
    text = normalize_unicode(text)
    text = normalize_line_endings(text)
    text = normalize_whitespace_chars(text)
    text = remove_control_chars(text)
    return text
