"""
Regex-based NER adapter.

Uses regular expressions for pattern-based PII detection.
Includes algorithmic validation for DNI/NIE (Spanish ID).

Traceability:
- Contract: CNT-T3-REGEX-ADAPTER-001
- Port: ports.NerService
- Optimization: Validated patterns return confidence=1.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from re import Pattern

from contextsafe.application.ports import NerDetection, NerService, ProgressCallback
from contextsafe.domain.shared.value_objects import (
    ConfidenceScore,
    PiiCategory,
    TextSpan,
)


# DNI/NIE validation letters (official algorithm)
DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"


def validate_dni(dni: str) -> bool:
    """
    Validate Spanish DNI using official algorithm.

    The control letter is calculated as: number % 23 -> letter from DNI_LETTERS

    Args:
        dni: DNI string (8 digits + 1 letter)

    Returns:
        True if the DNI is valid
    """
    dni = dni.upper().strip()
    if len(dni) != 9:
        return False

    try:
        number = int(dni[:8])
        letter = dni[8]
        expected_letter = DNI_LETTERS[number % 23]
        return letter == expected_letter
    except (ValueError, IndexError):
        return False


def validate_nie(nie: str) -> bool:
    """
    Validate Spanish NIE using official algorithm.

    NIE starts with X, Y, or Z which is replaced by 0, 1, or 2 respectively,
    then the same DNI algorithm is applied.

    Args:
        nie: NIE string (X/Y/Z + 7 digits + 1 letter)

    Returns:
        True if the NIE is valid
    """
    nie = nie.upper().strip()
    if len(nie) != 9:
        return False

    prefix = nie[0]
    if prefix not in "XYZ":
        return False

    try:
        # Replace X->0, Y->1, Z->2
        prefix_value = {"X": "0", "Y": "1", "Z": "2"}[prefix]
        number = int(prefix_value + nie[1:8])
        letter = nie[8]
        expected_letter = DNI_LETTERS[number % 23]
        return letter == expected_letter
    except (ValueError, IndexError):
        return False


def validate_iban_spain(iban: str) -> bool:
    """
    Validate Spanish IBAN using modulo 97 check.

    Args:
        iban: IBAN string (ES + 22 digits)

    Returns:
        True if the IBAN is valid
    """
    # Remove spaces and convert to uppercase
    iban = re.sub(r"[\s\-]", "", iban).upper()

    if not iban.startswith("ES") or len(iban) != 24:
        return False

    # Move first 4 chars to end
    rearranged = iban[4:] + iban[:4]

    # Convert letters to numbers (A=10, B=11, ..., Z=35)
    numeric = ""
    for char in rearranged:
        if char.isdigit():
            numeric += char
        elif char.isalpha():
            numeric += str(ord(char) - ord("A") + 10)
        else:
            return False

    try:
        return int(numeric) % 97 == 1
    except ValueError:
        return False


@dataclass
class RegexPattern:
    """A regex pattern with associated PII category and confidence."""

    pattern: Pattern
    category: PiiCategory
    base_confidence: float
    validator: callable = None  # Optional validation function
    case_sensitive: bool = False  # Whether pattern needs case-sensitive matching


# ============================================================================
# PERSON NAME — Building blocks (ML audit R4)
# Source: plan_integracion_hallazgos_ml_a_produccion.md §3.2
# ============================================================================
_S = r'[^\S\n]+'           # whitespace but NOT newline
_S0 = r'[^\S\n]*'          # optional non-newline whitespace
_SN = r'[\s]+'             # whitespace INCLUDING newline (title→name gap only)
_CAP = r'[A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]+'
_CAP_HYP = r'[A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]+(?:-[A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]+)?'
_CAP_UC = r'[A-ZÁÉÍÓÚÑÜ]{2,}'
_PARTICLE = rf'(?:de(?:{_S}(?:la|los|las))?{_S}|del{_S})'
_PARTICLE_UC = rf'(?:DE(?:{_S}(?:LA|LOS|LAS))?{_S}|DEL{_S})'
_FIRST = rf'(?:Mª|{_CAP})'
_NWORD = rf'(?:{_PARTICLE})?{_CAP_HYP}'
_NWORD_UC = rf'(?:{_PARTICLE_UC})?{_CAP_UC}'
_TERM = rf'(?={_S0}[,.:;\n>)\]|]|{_S}[a-záéíóúñü]|\s*$)'
_TERM_UC = rf'(?={_S0}[,.:;\n>)\]]|\s*$)'


# Regex patterns for Spanish PII
# Patterns with validators will get confidence=1.0 if validation passes
PII_PATTERNS: list[tuple[str, str, float, callable | None]] = [
    # =========================================================================
    # PERSON NAMES (ML audit R1-R4: 19 patterns with particles, hyphens,
    # cross-line, double titles, extended terminators)
    # Source: plan_integracion_hallazgos_ml_a_produccion.md §3.2, §5 Cambios 4-7
    # Evidence: +9 TP across 5 audited documents, 0 regressions
    # =========================================================================
    # "D. Nombre [de/del/de la] Apellido1 Apellido2"
    (
        rf'\bD\.{_S}({_FIRST}(?:{_S}{_NWORD}){{0,4}}){_TERM}',
        "PERSON_NAME",
        0.98,
        None,
        True,
    ),
    # "D.ª Nombre Apellido1 Apellido2" (feminine magistrates)
    (
        rf'\bD\.ª{_S}({_FIRST}(?:{_S}{_NWORD}){{0,4}}){_TERM}',
        "PERSON_NAME",
        0.98,
        None,
        True,
    ),
    # "Dª[.] Nombre Apellido1 Apellido2"
    (
        rf'\bDª\.?{_S}({_FIRST}(?:{_S}{_NWORD}){{0,4}}){_TERM}',
        "PERSON_NAME",
        0.98,
        None,
        True,
    ),
    # "Dña./DÑA. Nombre [de/del] Apellido1 Apellido2"
    (
        rf'\bD(?:ña|ÑA)\.{_S}({_FIRST}(?:{_S}{_NWORD}){{0,4}}){_TERM}',
        "PERSON_NAME",
        0.98,
        None,
        True,
    ),
    # "don/doña/Don/Doña Nombre [de/del] Apellido1 Apellido2"
    (
        rf'\b(?:[Dd]on|[Dd]oña){_S}({_FIRST}(?:{_S}{_NWORD}){{0,4}}){_TERM}',
        "PERSON_NAME",
        0.98,
        None,
        True,
    ),
    # "Sra. Dña./D.ª Nombre Apellido" (double title — Cambio 5)
    (
        rf'\b(?:Sr|Sra)\.{_S}(?:Dña\.|D\.ª|Dª\.?){_S}({_FIRST}(?:{_S}{_NWORD}){{0,4}}){_TERM}',
        "PERSON_NAME",
        0.98,
        None,
        True,
    ),
    # "Sr./Sra./Srta. Nombre [de/del] Apellido1 Apellido2"
    # Excludes titles/roles as first word (Dña, Letrada, Fiscal, ...)
    (
        rf'\b(?:Sr|Sra|Srta)\.{_S}(?!Dña|Dña\.|D\.{_S0}|Letrad[oa]|Fiscal|President[ea]|Magistrad[oa]|Secretari[oa])({_CAP}(?:{_S}{_NWORD}){{0,3}}){_TERM}',
        "PERSON_NAME",
        0.95,
        None,
        True,
    ),
    # ALL CAPS: "D. ALEJANDRO ÁLVAREZ ESPEJO DE LA TORRE"
    (
        rf'\bD\.{_S}({_CAP_UC}(?:{_S}{_NWORD_UC}){{0,4}}){_TERM_UC}',
        "PERSON_NAME",
        0.98,
        None,
        True,
    ),
    # ALL CAPS: "DÑA. MARÍA GARCÍA LÓPEZ"
    (
        rf'\bD(?:ña|ÑA)\.{_S}({_CAP_UC}(?:{_S}{_NWORD_UC}){{0,4}}){_TERM_UC}',
        "PERSON_NAME",
        0.98,
        None,
        True,
    ),
    # Person initials: "D. A", "Dña. M"
    (
        r'\bD\.\s+([A-ZÁÉÍÓÚÑÜ])\b',
        "PERSON_NAME",
        0.92,
        None,
        True,
    ),
    (
        r'\bD(?:ña|ÑA)\.\s+([A-ZÁÉÍÓÚÑÜ])\b',
        "PERSON_NAME",
        0.92,
        None,
        True,
    ),
    # Multiple initials: "D. A. B. C."
    (
        r'\bD\.\s*([A-ZÁÉÍÓÚÑÜ]\.(?:\s*[A-ZÁÉÍÓÚÑÜ]\.)+)',
        "PERSON_NAME",
        0.92,
        None,
        True,
    ),
    # --- Cross-line variants (title\nName) — Cambio 6 ---
    # Lower confidence (0.93) to distinguish from same-line matches.
    # _SN allows newline ONLY between title and first name;
    # subsequent name parts use _S (no newline) to prevent bleeding.
    # "D.\nNombre Apellido1 Apellido2"
    (
        rf'\bD\.{_SN}({_FIRST}(?:{_S}{_NWORD}){{0,4}}){_TERM}',
        "PERSON_NAME",
        0.93,
        None,
        True,
    ),
    # "D.ª\nNombre Apellido1 Apellido2"
    (
        rf'\bD\.ª{_SN}({_FIRST}(?:{_S}{_NWORD}){{0,4}}){_TERM}',
        "PERSON_NAME",
        0.93,
        None,
        True,
    ),
    # "Dª[.]\nNombre Apellido1 Apellido2"
    (
        rf'\bDª\.?{_SN}({_FIRST}(?:{_S}{_NWORD}){{0,4}}){_TERM}',
        "PERSON_NAME",
        0.93,
        None,
        True,
    ),
    # "Dña.\nNombre Apellido1 Apellido2"
    (
        rf'\bD(?:ña|ÑA)\.{_SN}({_FIRST}(?:{_S}{_NWORD}){{0,4}}){_TERM}',
        "PERSON_NAME",
        0.93,
        None,
        True,
    ),
    # "don/doña\nNombre Apellido1 Apellido2"
    (
        rf'\b(?:[Dd]on|[Dd]oña){_SN}({_FIRST}(?:{_S}{_NWORD}){{0,4}}){_TERM}',
        "PERSON_NAME",
        0.93,
        None,
        True,
    ),
    # "Sr./Sra.\nNombre Apellido1 Apellido2" (with role exclusion)
    (
        rf'\b(?:Sr|Sra|Srta)\.{_SN}(?!Dña|Dña\.|D\.{_S0}|Letrad[oa]|Fiscal|President[ea]|Magistrad[oa]|Secretari[oa])({_CAP}(?:{_S}{_NWORD}){{0,3}}){_TERM}',
        "PERSON_NAME",
        0.90,
        None,
        True,
    ),

    # =========================================================================
    # ADDRESSES (BUG 2 - Critical)
    # Complete street addresses: "c/ Santiago Ramón y Cajal nº 45"
    # NOTE: Uses \s* (not \s+) to allow "c/Santiago" without space
    # =========================================================================
    # Pattern: "c/Nombre de Calle nº/núm/número XXX" (with or without space after c/)
    (
        r"\b(?:c/|C/|calle|Calle|CALLE|Avda\.|Av\.|Avenida|Plaza|Pza\.|Paseo|Pº)\s*([A-ZÁÉÍÓÚÑa-záéíóúñ\s]+?)(?:\s+n[ºúo]\.?\s*|\s+núm\.?\s*|\s+número\s+|\s+)(\d+)(?:\s*[-,]\s*(\d+[ºª]?))?",
        "ADDRESS",
        0.95,
        None,
    ),
    # Pattern: Full address with city "c/Calle nº XX, XXXXX Ciudad"
    # FIXED: Stop before "y DNI", "con DNI", ", DNI" patterns
    (
        r"\b(?:c/|C/|calle|Calle)\s*[A-ZÁÉÍÓÚÑa-záéíóúñ\s]+?\s+(?:n[ºúo]\.?\s*)?\d+(?:\s*[-,]\s*\d+[ºª]?)?,\s*\d{5}\s+[A-ZÁÉÍÓÚÑa-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑa-záéíóúñ]+)*(?=\s+(?:y\s+DNI|con\s+DNI|,?\s+DNI|y\s+NIE|con\s+NIE|,|\.|\s*$))",
        "ADDRESS",
        0.98,
        None,
    ),

    # =========================================================================
    # IDENTITY DOCUMENTS
    # =========================================================================
    # DNI (Spanish ID) - with validation
    (r"\b[0-9]{8}[A-Za-z]\b", "DNI_NIE", 0.95, validate_dni),
    # NIE (Foreigner ID) - with validation
    (r"\b[XYZxyz][0-9]{7}[A-Za-z]\b", "DNI_NIE", 0.95, validate_nie),
    # Passport
    (r"\b[A-Z]{2}[0-9]{7}\b", "PASSPORT", 0.85, None),
    (r"\b[A-Z]{3}[0-9]{6}\b", "PASSPORT", 0.85, None),

    # =========================================================================
    # ORGANIZATIONS (FUGA 1 - Critical)
    # Spanish legal entities: S.L., S.L.P., S.A., S.L.U., S.C., etc.
    # =========================================================================

    # Pattern: Single word company name + legal form
    # Captures: "Seguriber S.L.", "Telefónica S.A."
    (
        r"\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\s+(S\.?\s?L\.?\s?P\.?|S\.?\s?L\.?\s?U\.?|S\.?\s?L\.?|S\.?\s?A\.?\s?U\.?|S\.?\s?A\.?|S\.?\s?C\.?)(?=[\s,\.\)\n]|$)",
        "ORGANIZATION",
        0.95,
        None,
        True,  # case_sensitive
    ),

    # Pattern: Two+ word company names + legal form
    # Captures: "Uniformes Universales S.A.", "Servicios Integrales S.L."
    (
        r"\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+)\s+(S\.?\s?L\.?\s?P\.?|S\.?\s?L\.?\s?U\.?|S\.?\s?L\.?|S\.?\s?A\.?\s?U\.?|S\.?\s?A\.?|S\.?\s?C\.?)(?=[\s,\.\)\n]|$)",
        "ORGANIZATION",
        0.96,
        None,
        True,  # case_sensitive
    ),

    # Pattern: FLEXIBLE - Names with prepositions + legal form
    # Captures: "Seguriber Compañía de Servicios Integrales S.L."
    # Allows lowercase prepositions (de, y, del, la, los, las, e) between words
    (
        r"\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+(?:de|y|del|la|los|las|e)\s+)?(?:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s*)+)\s+(S\.?\s?L\.?\s?P\.?|S\.?\s?L\.?\s?U\.?|S\.?\s?L\.?|S\.?\s?A\.?\s?U\.?|S\.?\s?A\.?|S\.?\s?C\.?)(?=[\s,\.\)\n]|$)",
        "ORGANIZATION",
        0.95,
        None,
        True,  # case_sensitive
    ),

    # Pattern: ALL CAPS name + legal form (highest confidence)
    # "MENTOR ABOGADOS S.L.P." - uppercase words followed by legal form
    (
        r"\b([A-ZÁÉÍÓÚÑ]{2,}(?:\s+[A-ZÁÉÍÓÚÑ]{2,}){0,5})\s+(S\.?\s?L\.?\s?P\.?|S\.?\s?L\.?\s?U\.?|S\.?\s?L\.?|S\.?\s?A\.?\s?U\.?|S\.?\s?A\.?)(?=[\s,\.\)\n]|$)",
        "ORGANIZATION",
        0.98,
        None,
        True,  # case_sensitive=True - CRITICAL for uppercase org names
    ),

    # Pattern: Mixed case with "Abogados" - law firms
    # "Mentor Abogados S.L.P."
    (
        r"\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+Abogados)\s+(S\.?L\.?P\.?|S\.?L\.?)(?=[\s,\.\)\n]|$)",
        "ORGANIZATION",
        0.98,
        None,
        True,  # case_sensitive=True
    ),

    # Pattern: "Compañía de ..." - Spanish company naming
    # "Seguriber Compañía de Servicios Integrales S.L."
    (
        r"\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+Compañía\s+de\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)\s+(S\.?L\.?|S\.?A\.?)(?=[\s,\.\)\n]|$)",
        "ORGANIZATION",
        0.98,
        None,
        True,
    ),

    # Pattern: Investment funds - FCR, SICAV, FI, etc.
    # "Ezten FCR", "Fondo XYZ SICAV"
    (
        r"\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]*(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]*)*)\s+(FCR|SICAV|FI|FII|SOCIMI)(?=[\s,\.\)\n]|$)",
        "ORGANIZATION",
        0.95,
        None,
        True,
    ),
    # Pattern: "Bufete/Despacho XXX" - law offices
    (
        r"\b((?:Bufete|Despacho)\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)(?=[\s,\.\n]|$)",
        "ORGANIZATION",
        0.95,
        None,
        True,  # case_sensitive=True
    ),
    # Pattern: Well-known Spanish banks (case-insensitive for brand names)
    (
        r"\b((?:Banco\s+)?(?:Santander|BBVA|CaixaBank|Sabadell|Bankinter|ING|Openbank|Bankia|Kutxabank|Unicaja|Ibercaja|Liberbank|Abanca)(?:\s+S\.?A\.?)?)(?=[\s,\.\n]|$)",
        "ORGANIZATION",
        0.98,
        None,
        False,  # case_sensitive=False - bank names can be mixed case
    ),
    # Pattern: Insurance companies (case-insensitive for brand names)
    (
        r"\b((?:Mapfre|Allianz|AXA|Generali|Zurich|Mutua\s+Madrileña|Catalana\s+Occidente|Sanitas|DKV|Asisa)(?:\s+S\.?A\.?)?)(?=[\s,\.\n]|$)",
        "ORGANIZATION",
        0.95,
        None,
        False,  # case_sensitive=False - insurance names can be mixed case
    ),

    # =========================================================================
    # ORGANIZATIONS - CONTEXTUAL DETECTION (sin sufijo legal)
    # Detecta nombres propios seguidos de verbos típicos de organizaciones
    # USA LOOKAHEAD (?=...) para NO incluir el verbo en el match
    # "Graphiland reclama" → captura solo "Graphiland"
    # =========================================================================
    # Pattern: Nombre + verbo en 3ra persona (lookahead)
    (
        r"\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)(?=\s+(?:alega|reclama|demanda|solicita|interpone|presenta|denuncia|comunica|notifica|requiere|exige|afirma|sostiene|manifiesta|declara|reconoce|niega|impugna|recurre|apela))",
        "ORGANIZATION",
        0.85,
        None,
        True,  # case_sensitive
    ),
    # Pattern: "también X lo/la/le" - captura solo X (lookahead y lookbehind)
    (
        r"(?<=también\s)([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)(?=\s+(?:lo|la|le|los|las|les))",
        "ORGANIZATION",
        0.85,
        None,
        True,  # case_sensitive
    ),
    # Pattern: "que X lo/la calificó" - captura solo X
    (
        r"(?<=que\s)([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)(?=\s+(?:lo|la|le)\s+(?:calificó|consideró|estimó|valoró|rechazó|aceptó|aprobó|denegó))",
        "ORGANIZATION",
        0.85,
        None,
        True,  # case_sensitive
    ),

    # =========================================================================
    # PROCEDURE NUMBERS (FUGA 2 - Critical)
    # Judicial procedure identifiers: nº XXX/YYYY, Proc. XXX/YYYY-XX
    # =========================================================================
    # Pattern: "nº 548/2025" or "núm. 548/2025" with optional suffix like "-D7"
    (
        r"(?:n[ºúu]m?\.?|número)\s*(\d{1,5}/\d{4}(?:-[A-Z0-9]+)?)",
        "CASE_NUMBER",
        0.95,
        None,
    ),
    # Pattern: "Proc. 548/2025", "Procedimiento 548/2025-D7"
    (
        r"(?:Proc\.?|Procedimiento)\s*(\d{1,5}/\d{4}(?:-[A-Z0-9]+)?)",
        "CASE_NUMBER",
        0.95,
        None,
    ),
    # Pattern: "JUICIO VERBAL 548/2025-D", "JUICIO ORDINARIO 123/2024"
    (
        r"(?i)JUICIO\s+(?:VERBAL|ORDINARIO|MONITORIO|CAMBIARIO)\s+(\d{1,5}/\d{4}(?:-[A-Z0-9]+)?)",
        "CASE_NUMBER",
        0.98,
        None,
    ),
    # Pattern: "Autos 123/2020", "Rollo 456/2021", "Recurso 789/2022"
    (
        r"(?:Autos|Rollo|Recurso|Ejecutoria|Diligencias)\s*(?:n[ºúu]m?\.?\s*)?(\d{1,5}/\d{4}(?:-[A-Z0-9]+)?)",
        "CASE_NUMBER",
        0.95,
        None,
    ),
    # Pattern: Standalone case number with suffix (high confidence for legal context)
    # "548/2025-D7" - the suffix differentiates from year-like numbers
    (
        r"\b(\d{1,5}/\d{4}-[A-Z0-9]{1,4})\b",
        "CASE_NUMBER",
        0.90,
        None,
    ),

    # =========================================================================
    # SENSITIVE PLATFORMS (FUGA 3)
    # Messaging and social media platforms (contextual sensitivity)
    # Expanded list including Spanish-relevant platforms
    # =========================================================================
    (
        r"\b(WhatsApp|Telegram|Signal|Messenger|Instagram|Facebook|Twitter|X|TikTok|LinkedIn|Snapchat|Discord|Slack|Teams|Skype|Zoom|WeChat|Viber|LINE|iMessage|FaceTime|Wallapop|Vinted|Milanuncios|Idealista|Fotocasa|InfoJobs)(?:\s|$|,|\.|:)",
        "PLATFORM",
        0.85,
        None,
    ),
    # Pattern: contextual platform references
    # "mensaje de WhatsApp", "grupo de Telegram", "conversación por Signal"
    (
        r"(?:mensaje|grupo|chat|conversación|llamada|videollamada|foto|vídeo|video|audio|nota\s+de\s+voz)\s+(?:de|por|en|vía)\s+(WhatsApp|Telegram|Signal|Messenger|Instagram|Facebook|Twitter)",
        "PLATFORM",
        0.90,
        None,
    ),

    # =========================================================================
    # CONTACT INFORMATION
    # =========================================================================
    # Phone numbers (Spanish format)
    (r"\b(?:\+34|0034)?\s*[6789]\d{2}[\s.-]?\d{3}[\s.-]?\d{3}\b", "PHONE", 0.95, None),
    (r"\b[6789]\d{8}\b", "PHONE", 0.90, None),
    # Email - high confidence for valid format
    (r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", "EMAIL", 0.98, None),

    # =========================================================================
    # FINANCIAL INFORMATION
    # =========================================================================
    # Credit card (Visa, MasterCard, AMEX patterns)
    (r"\b4[0-9]{12}(?:[0-9]{3})?\b", "CREDIT_CARD", 0.95, None),  # Visa
    (r"\b5[1-5][0-9]{14}\b", "CREDIT_CARD", 0.95, None),  # MasterCard
    (r"\b3[47][0-9]{13}\b", "CREDIT_CARD", 0.95, None),  # AMEX
    (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "CREDIT_CARD", 0.85, None),
    # IBAN (Spanish) - with validation
    (r"\bES\s?\d{2}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", "IBAN", 0.95, validate_iban_spain),
    (r"\bES\d{22}\b", "IBAN", 0.95, validate_iban_spain),
    # Generic IBAN (other countries)
    (r"\b[A-Z]{2}\d{2}[\s-]?(?:\d{4}[\s-]?){3,5}\d{1,4}\b", "BANK_ACCOUNT", 0.90, None),

    # =========================================================================
    # VEHICLE & LOCATION
    # =========================================================================
    # License plate (Spanish - new format): 4 digits + 3 consonants
    # IMPORTANT: Exclude years (19XX, 20XX) followed by letters that could be words
    # FP-5: "en 2021 se" was incorrectly detected as license plate
    # Solution: First two digits cannot be 19 or 20 (year prefixes)
    (r"\b(?!(?:19|20)\d{2})\d{4}\s?[BCDFGHJKLMNPRSTVWXYZ]{3}\b", "LICENSE_PLATE", 0.95, None),
    # License plate (Spanish - old format with province code)
    # FP-5: Must be case_sensitive to avoid matching "en 2021 se" as plate
    # Old format plates were ALWAYS uppercase (M 1234 AB, B 5678 CD)
    (r"\b[A-Z]{1,2}\s?(?!(?:19|20)\d{2})\d{4}\s?[A-Z]{2}\b", "LICENSE_PLATE", 0.90, None, True),
    # Postal code (Spanish - 5 digits, starts with 01-52)
    # NOTE: Increased confidence to 0.92 to ensure detection even when adjacent to address
    # Province codes 01-52 are validated (01=Álava, 08=Barcelona, 28=Madrid, 52=Melilla)
    (r"\b(?:0[1-9]|[1-4]\d|5[0-2])\d{3}\b", "POSTAL_CODE", 0.92, None),

    # =========================================================================
    # LOCATIONS IN JUDICIAL CONTEXT
    # Captures city names in common judicial patterns (often in UPPERCASE)
    # =========================================================================
    # Pattern: "en [Ciudad], a [fecha]" - common in document signatures
    (
        r"(?i)\ben\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,30}?),?\s+a\s+(?:\[FECHA\]|\d{1,2})",
        "LOCATION",
        0.90,
        None,
    ),
    # Pattern: "[Ciudad], a [fecha]" - signature WITHOUT "en" prefix (Fix C3)
    # Common in Spanish legal signatures: "Martorell, a 15 de febrero de 2025"
    # Uses ^/newline anchor to avoid false positives mid-sentence
    # Confidence 0.88 (lower than "en Ciudad" variant to avoid FP)
    (
        r"(?im)^([A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,25}),?\s+a\s+(?:\[FECHA\]|\d{1,2})",
        "LOCATION",
        0.88,
        None,
    ),
    # Pattern: "AL JUZGADO DE [algo] Nº X DE [CIUDAD]" header
    # FIXED: Handle "Nº X" in the middle and ensure clean word boundary at end
    (
        r"(?i)AL\s+JUZGADO\s+DE\s+(?:PRIMERA\s+INSTANCIA|LO\s+(?:PENAL|CIVIL|SOCIAL)|INSTRUCCIÓN|FAMILIA|MERCANTIL)(?:\s+(?:E\s+INSTRUCCIÓN\s+)?N[ºÚO°]\s*\d+)?\s+DE\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ]{2,25})(?=\s*[\n\r,\.]|\s*$)",
        "LOCATION",
        0.95,
        None,
    ),
    # Pattern: "JUZGADO DE [algo] Nº X DE [CIUDAD]" (header without "AL")
    # Uses (?m) for multiline mode so ^ matches start of each line
    (
        r"(?im)^JUZGADO\s+DE\s+(?:PRIMERA\s+INSTANCIA|LO\s+(?:PENAL|CIVIL|SOCIAL)|INSTRUCCIÓN|FAMILIA|MERCANTIL)(?:\s+(?:E\s+INSTRUCCIÓN\s+)?N[ºÚO°]\s*\d+)?\s+DE\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ]{2,25})(?=\s*[\n\r,\.]|\s*$)",
        "LOCATION",
        0.95,
        None,
    ),

    # =========================================================================
    # SOCIAL SECURITY & PROFESSIONAL IDS
    # =========================================================================
    # Social Security Number (Spanish)
    (r"\b\d{2}/\d{8}/\d{2}\b", "SOCIAL_SECURITY", 0.95, None),
    (r"\b\d{2}-\d{8}-\d{2}\b", "SOCIAL_SECURITY", 0.95, None),
    # Professional ID numbers (Colegiado nº XXX) - HIGH CONFIDENCE to beat POSTAL_CODE
    (
        r"(?:colegiado|n[ºúu]\s*colegiado|número\s+de\s+colegiado)[:\s]*n?[ºúu]?\s*(\d{3,8})",
        "PROFESSIONAL_ID",
        0.98,
        None
    ),

    # =========================================================================
    # DATES
    # =========================================================================
    # Date formats (common in Spanish documents)
    (r"\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b", "DATE", 0.75, None),
    (r"\b\d{4}[-/]\d{2}[-/]\d{2}\b", "DATE", 0.75, None),
    # Written dates: "12 de marzo de 2024"
    (
        r"\b\d{1,2}\s+de\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+\d{4}\b",
        "DATE",
        0.90,
        None
    ),

    # =========================================================================
    # NETWORK
    # =========================================================================
    # IP Address
    (r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "IP_ADDRESS", 0.85, None),

    # =========================================================================
    # SECTOR LEGAL ESPAÑOL - Nuevos patrones
    # Ref: "Patrones Regex Sector Legal Español.md"
    # =========================================================================

    # -------------------------------------------------------------------------
    # NÚMERO DE SOPORTE (IDESP/IXESP) - CRÍTICO
    # Permite acceso a Cl@ve de la Agencia Tributaria
    # -------------------------------------------------------------------------
    # DNI (Soporte): 3 letras + 6 números
    (r"\b[A-Z]{3}\d{6}\b", "ID_SUPPORT", 0.90, None),
    # TIE (Tarjeta Extranjero - IXESP): E + 8 dígitos
    (r"\bE\d{8}\b", "ID_SUPPORT", 0.92, None),
    # Certificado UE (Papel Verde): C + 8 dígitos
    (r"\bC\d{8}\b", "ID_SUPPORT", 0.90, None),
    # Contextual: "Número de soporte", "IDESP", "IXESP"
    (
        r"(?i)(?:n[ºúu]mero\s+de\s+soporte|soporte|IDESP|IXESP)[:\s]+([A-Z0-9]{9,12})",
        "ID_SUPPORT",
        0.98,
        None,
    ),

    # -------------------------------------------------------------------------
    # NIG - NÚMERO DE IDENTIFICACIÓN GENERAL (19 dígitos)
    # Identificador único de procedimientos judiciales en España
    # Estructura: Municipio(5) + Órgano(2) + Jurisdicción(1) + Año(4) + Correlativo(7)
    # -------------------------------------------------------------------------
    # NIG completo sin separadores (19 dígitos)
    (r"\b\d{5}\d{2}\d{1}\d{4}\d{7}\b", "NIG", 0.95, None),
    # NIG con separadores (barras, guiones, espacios, puntos)
    (
        r"\b(\d{5})[\\/\-\s\.]+(\d{2})[\\/\-\s\.]+(\d{1})[\\/\-\s\.]+(\d{4})[\\/\-\s\.]+(\d{7})\b",
        "NIG",
        0.98,
        None,
    ),
    # NIG contextual: "NIG:", "N.I.G."
    (
        r"(?i)(?:NIG|N\.I\.G\.)[:\s]+(\d{5}[\\/\-\s\.]*\d{2}[\\/\-\s\.]*\d{1}[\\/\-\s\.]*\d{4}[\\/\-\s\.]*\d{7})",
        "NIG",
        0.99,
        None,
    ),

    # -------------------------------------------------------------------------
    # ECLI - European Case Law Identifier
    # Formato: ECLI:ES:Órgano:Año:Número
    # -------------------------------------------------------------------------
    # ECLI estándar
    (r"\bECLI:ES:[A-Z0-9]{2,5}:\d{4}:\d+\b", "ECLI", 0.99, None),
    # ECLI con variaciones (espacios, puntos en lugar de dos puntos)
    (
        r"\bECLI[\s\.:]+ES[\s\.:]+[A-Z0-9]{2,5}[\s\.:]+\d{4}[\s\.:]+\d+\b",
        "ECLI",
        0.95,
        None,
    ),

    # -------------------------------------------------------------------------
    # CSV - CÓDIGO SEGURO DE VERIFICACIÓN - ¡¡CRÍTICO!!
    # Permite descargar documento original desde sede electrónica
    # Cadena alfanumérica de alta entropía (16-24 caracteres)
    # -------------------------------------------------------------------------
    # CSV genérico (16-24 caracteres alfanuméricos)
    # IMPORTANTE: Usar lookbehind/lookahead para evitar palabras normales
    (
        r"(?<![A-Za-z])([A-Z0-9]{16,24})(?![A-Za-z])",
        "CSV",
        0.85,
        None,
        True,  # case_sensitive
    ),
    # CSV contextual: "CSV:", "Código Seguro", "Verificación"
    (
        r"(?i)(?:CSV|c[oó]digo\s+seguro(?:\s+de\s+verificaci[oó]n)?|huella\s+digital)[:\s]+([A-Z0-9]{12,24})",
        "CSV",
        0.99,
        None,
    ),

    # -------------------------------------------------------------------------
    # CIP-SNS - Código de Identificación Personal del Sistema Nacional de Salud
    # Estructura: 4 letras + 12 dígitos
    # -------------------------------------------------------------------------
    (r"\b[A-Z]{4}\d{12}\b", "HEALTH_ID", 0.95, None),
    # CIP-SNS contextual
    (
        r"(?i)(?:CIP|CIP-SNS|tarjeta\s+sanitaria)[:\s]+([A-Z]{4}\d{10,12})",
        "HEALTH_ID",
        0.99,
        None,
    ),

    # -------------------------------------------------------------------------
    # CIP AUTONÓMICOS - Códigos de tarjeta sanitaria por Comunidad Autónoma
    # -------------------------------------------------------------------------
    # Cataluña (CatSalut): 4 letras + 10 dígitos
    (r"\b[A-Z]{4}\d{10}\b", "HEALTH_ID", 0.90, None),
    # Andalucía (NUHSA): AN + 8-10 dígitos
    (r"\b(?:AN|NU)\d{8,10}\b", "HEALTH_ID", 0.95, None),
    # País Vasco (TIS) contextual: 8 dígitos (requiere contexto por falsos positivos)
    (
        r"(?i)(?:TIS|Osakidetza)[:\s]+(\d{8})",
        "HEALTH_ID",
        0.98,
        None,
    ),
    # Comunidad Valenciana (SIP) contextual
    (
        r"(?i)SIP[:\s]+(\d{7,8})",
        "HEALTH_ID",
        0.98,
        None,
    ),
    # Castilla y León: CYL + 10 dígitos
    (r"\bCYL\d{10}\b", "HEALTH_ID", 0.95, None),

    # -------------------------------------------------------------------------
    # REFERENCIA CATASTRAL
    # Identificador único de inmuebles en España
    # -------------------------------------------------------------------------
    # Urbana (20 caracteres): 7 dígitos + 7 dígitos + 2 letras + 4 dígitos
    (r"\b\d{7}[A-Z]{2}\d{4}[A-Z]{4}\b", "CADASTRAL_REF", 0.95, None, True),
    # Con posibles separadores
    (
        r"\b(\d{7})[A-Z]{2}(\d{4})[A-Z]{4}\b",
        "CADASTRAL_REF",
        0.95,
        None,
        True,
    ),
    # Rústica: estructura diferente basada en polígonos/parcelas
    (
        r"\b(\d{2})(\d{3})([A-Z])(\d{3})(\d{5})(\d{4})([A-Z]{2})\b",
        "CADASTRAL_REF",
        0.95,
        None,
        True,
    ),
    # Contextual: "Referencia Catastral", "Ref. Cat."
    (
        r"(?i)(?:referencia\s+catastral|ref\.?\s*cat\.?)[:\s]+([A-Z0-9]{14,20})",
        "CADASTRAL_REF",
        0.99,
        None,
    ),

    # -------------------------------------------------------------------------
    # CCC - CÓDIGO DE CUENTA DE COTIZACIÓN (Empresas)
    # Estructura: Provincia(2) + Régimen(2) + Número(7) + Control(2) = 13 dígitos
    # -------------------------------------------------------------------------
    # CCC con separadores
    (
        r"\b(\d{2})[\\/\s](\d{2})[\\/\s](\d{7})[\\/\s](\d{2})\b",
        "EMPLOYER_ID",
        0.95,
        None,
    ),
    # CCC contextual: "CCC:", "Cuenta de Cotización"
    (
        r"(?i)(?:CCC|cuenta\s+de\s+cotizaci[oó]n|c[oó]digo\s+de\s+cuenta)[:\s]+(\d{2}[\\/\s]?\d{2}[\\/\s]?\d{7}[\\/\s]?\d{2})",
        "EMPLOYER_ID",
        0.99,
        None,
    ),

    # -------------------------------------------------------------------------
    # NAF - NÚMERO DE AFILIACIÓN (mejora del patrón existente)
    # Estructura: Provincia(2) + Secuencial(8) + Control(2) = 12 dígitos
    # -------------------------------------------------------------------------
    # NAF con barras (común en formularios)
    (r"\b\d{2}/\d{8}/\d{2}\b", "SOCIAL_SECURITY", 0.98, None),
    # NAF con guiones
    (r"\b\d{2}-\d{8}-\d{2}\b", "SOCIAL_SECURITY", 0.98, None),
    # NAF con espacios
    (r"\b\d{2}\s\d{8}\s\d{2}\b", "SOCIAL_SECURITY", 0.95, None),
    # NAF contextual
    (
        r"(?i)(?:NAF|n[úu]mero\s+de\s+afiliaci[oó]n|afiliaci[oó]n\s+SS)[:\s]+(\d{2}[\\/\s\-]?\d{8}[\\/\s\-]?\d{2})",
        "SOCIAL_SECURITY",
        0.99,
        None,
    ),
]


class RegexNerAdapter(NerService):
    """
    NER service using regex patterns with validation.

    Provides fast, deterministic detection for structured PII patterns.
    Validated patterns (DNI, IBAN) return confidence=1.0.
    """

    def __init__(self) -> None:
        """Initialize the regex NER adapter."""
        self._patterns: list[RegexPattern] = []
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile all regex patterns."""
        for item in PII_PATTERNS:
            pattern_str, category_str, confidence = item[:3]
            validator = item[3] if len(item) > 3 else None
            # 5th element is case_sensitive flag (default False = use IGNORECASE)
            case_sensitive = item[4] if len(item) > 4 else False

            category_result = PiiCategory.from_string(category_str)
            if category_result.is_ok():
                # Use IGNORECASE only when NOT case_sensitive
                flags = 0 if case_sensitive else re.IGNORECASE
                self._patterns.append(
                    RegexPattern(
                        pattern=re.compile(pattern_str, flags),
                        category=category_result.unwrap(),
                        base_confidence=confidence,
                        validator=validator,
                        case_sensitive=case_sensitive,
                    )
                )

    async def detect_entities(
        self,
        text: str,
        categories: list[PiiCategory] | None = None,
        min_confidence: float = 0.5,
        progress_callback: ProgressCallback | None = None,
    ) -> list[NerDetection]:
        """
        Detect entities in text using regex patterns.

        Args:
            text: The text to analyze
            categories: Optional filter for specific categories
            min_confidence: Minimum confidence threshold
            progress_callback: Optional async callback for progress (unused, regex is fast)

        Returns:
            List of detected entities
        """
        if not text or not text.strip():
            return []

        detections: list[NerDetection] = []
        seen_spans: set = set()  # Avoid duplicates

        for regex_pattern in self._patterns:
            # Filter by category if specified
            if categories and regex_pattern.category not in categories:
                continue

            # Skip if base confidence is below threshold
            if regex_pattern.base_confidence < min_confidence:
                continue

            for match in regex_pattern.pattern.finditer(text):
                # ============================================================
                # CRITICAL FIX: Decide whether to use group 1 or full match
                #
                # CONTEXT PATTERNS (use group 1 - context shouldn't be replaced):
                # - "AL JUZGADO DE ... DE ([CIUDAD])" → city only
                # - "D. ([Nombre Apellido])" → name only
                # - "en ([Ciudad]), a [fecha]" → city only
                #
                # FULL ENTITY PATTERNS (use full match - all is the entity):
                # - "([Nombre]) (S.L.P.)" → full org with legal form
                # - "[0-9]{8}[A-Za-z]" → full DNI
                #
                # DETECTION: If match.start() != match.start(1), there's prefix
                # context that shouldn't be replaced (e.g., "D." or "AL JUZGADO DE").
                # ============================================================
                if match.lastindex and match.lastindex >= 1:
                    group1_start = match.start(1)
                    group1_end = match.end(1)
                    full_start = match.start()
                    full_end = match.end()

                    # Check if there's prefix context (like "D." or "AL JUZGADO DE")
                    has_prefix_context = (full_start < group1_start)

                    # Check if there's suffix context (like lookahead matches)
                    # For organizations with legal form, group 2 has the S.L.P.
                    # but we WANT to include it, so we use full match
                    has_suffix_entity = (
                        match.lastindex >= 2 and
                        regex_pattern.category.value == "ORGANIZATION"
                    )

                    if has_prefix_context and not has_suffix_entity:
                        # Use group 1 only (prefix is context, not entity)
                        matched_text = match.group(1)
                        start = group1_start
                        end = group1_end
                    elif has_suffix_entity:
                        # Combine all groups for organizations with legal form
                        parts = [match.group(i) for i in range(1, match.lastindex + 1) if match.group(i)]
                        matched_text = " ".join(parts)
                        # Recalculate span to cover all groups
                        start = min(match.start(i) for i in range(1, match.lastindex + 1) if match.group(i))
                        end = max(match.end(i) for i in range(1, match.lastindex + 1) if match.group(i))
                    else:
                        # No prefix context - use full match
                        start, end = full_start, full_end
                        matched_text = match.group()
                else:
                    # No capturing groups - use full match
                    start, end = match.start(), match.end()
                    matched_text = match.group()

                # Skip overlapping matches
                span_key = (start, end)
                if span_key in seen_spans:
                    continue
                seen_spans.add(span_key)

                # Determine confidence
                # If there's a validator, use it to boost confidence to 1.0
                confidence = regex_pattern.base_confidence
                if regex_pattern.validator:
                    try:
                        if regex_pattern.validator(matched_text):
                            confidence = 1.0  # Validated pattern = maximum confidence
                        else:
                            # Pattern matched but validation failed
                            # Still include but with lower confidence
                            confidence = regex_pattern.base_confidence * 0.7
                    except Exception:
                        # Validation error, keep base confidence
                        pass

                # Skip if final confidence is below threshold
                if confidence < min_confidence:
                    continue

                # Create span with the matched text
                span_result = TextSpan.create(start, end, matched_text)
                if span_result.is_err():
                    continue

                # Create confidence
                conf_result = ConfidenceScore.create(confidence)
                if conf_result.is_err():
                    continue

                detections.append(
                    NerDetection(
                        category=regex_pattern.category,
                        value=matched_text,
                        span=span_result.unwrap(),
                        confidence=conf_result.unwrap(),
                        source="regex",
                    )
                )

        # Sort by position
        detections.sort(key=lambda d: (d.span.start, d.span.end))
        return detections

    async def is_available(self) -> bool:
        """Regex adapter is always available."""
        return True

    async def get_model_info(self) -> dict:
        """Get information about the regex patterns."""
        validated_patterns = sum(1 for p in self._patterns if p.validator)
        return {
            "type": "regex",
            "pattern_count": len(self._patterns),
            "validated_patterns": validated_patterns,
            "categories": list(set(str(p.category) for p in self._patterns)),
            "note": "Validated patterns (DNI, IBAN) return confidence=1.0",
        }
