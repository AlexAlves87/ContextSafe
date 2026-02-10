"""
Contextual anchors for Spanish legal domain.

Provides deterministic rules based on context tokens that force
a specific PII category, overriding model predictions.

Example:
    "doña Pura" -> "doña" is a PERSON anchor, forces PERSON_NAME
    "sito en Madrid" -> "sito en" is LOCATION anchor, forces LOCATION

Traceability:
- Design: docs/plans/2026-02-02-intelligent-merge-spacy-design.md
"""

from __future__ import annotations

import re
from typing import Pattern

from contextsafe.application.ports import NerDetection
from contextsafe.domain.shared.value_objects import PiiCategory


def _compile_anchors(anchors: list[str]) -> Pattern:
    """
    Compile anchors as regex with word boundaries.

    Uses \\b to prevent false positives like "asesor" matching "sor".
    """
    # Escape special regex characters and join with OR
    escaped = [re.escape(a) for a in anchors]
    pattern = r'\b(' + '|'.join(escaped) + r')\b'
    return re.compile(pattern, re.IGNORECASE)


# =============================================================================
# PERSON_NAME ANCHORS
# =============================================================================
# Tokens that indicate the following entity is a person

PERSON_ANCHORS_RAW = [
    # Honoríficos
    "don", "doña", "d.", "dña.", "d.ª",
    "sr.", "sra.", "señor", "señora",
    # Profesionales legales
    "letrado", "letrada", "abogado", "abogada",
    "procurador", "procuradora", "notario", "notaria",
    "magistrado", "magistrada", "juez", "jueza",
    # Eclesiásticos (testamentos)
    "fray", "sor",
    # Representación
    "en representación de", "representado por", "representada por",
    "tutor de", "tutora de", "curador de", "curadora de",
    # Filiación (Registro Civil)
    "hijo de", "hija de", "cónyuge de",
    "viudo de", "viuda de", "casado con", "casada con",
    # Peritos/Funcionarios
    "perito", "secretario judicial", "letrado de la administración",
    "LAJ", "agente judicial",
    # Partes procesales
    "demandante", "demandado", "demandada",
    "denunciante", "denunciado", "denunciada",
    "recurrente", "recurrido", "recurrida",
    "apelante", "apelado", "apelada",
    "querellante", "querellado", "querellada",
    "ejecutante", "ejecutado", "ejecutada",
    "acusado", "acusada", "imputado", "imputada",
    # Testigos y declarantes
    "testigo", "declarante", "compareciente",
]

PERSON_ANCHORS = _compile_anchors(PERSON_ANCHORS_RAW)


# =============================================================================
# LOCATION ANCHORS
# =============================================================================
# Tokens that indicate the following entity is a location

LOCATION_ANCHORS_RAW = [
    # Vías
    "calle", "c/", "avenida", "av.", "avda.", "plaza", "pza.",
    "paseo", "camino", "carretera", "ctra.", "glorieta",
    "travesía", "ronda", "vía",
    # Inmuebles (muy fuerte en documentos registrales)
    "sito en", "situada en", "situado en", "sita en",
    "finca registral", "finca catastral", "parcela",
    "inmueble sito", "local sito", "vivienda sita",
    # Registros
    "registro de la propiedad de", "registro civil de",
    "registro mercantil de",
    # Domicilios
    "domiciliado en", "domiciliada en",
    "con domicilio en", "vecino de", "vecina de",
    "residente en", "natural de",
    # Administrativos
    "municipio de", "localidad de", "provincia de",
    "partido judicial de", "término municipal de",
    "comunidad autónoma de",
]

LOCATION_ANCHORS = _compile_anchors(LOCATION_ANCHORS_RAW)


# =============================================================================
# ORGANIZATION ANCHORS
# =============================================================================
# Tokens that indicate the entity is an organization
# Note: Some are checked INSIDE the entity (suffixes like S.L.)

ORG_ANCHORS_RAW = [
    # Formas jurídicas (también se buscan dentro de la entidad)
    "s.a.", "s.l.", "s.l.u.", "s.l.p.", "s.c.", "s.c.p.",
    "sociedad anónima", "sociedad limitada",
    "sociedad civil", "comunidad de bienes",
    # Bancarias (crítico para contexto IBAN)
    "banco", "caja", "caixa", "entidad bancaria", "entidad mercantil",
    "entidad financiera",
    # Instituciones judiciales
    "juzgado de", "tribunal", "audiencia provincial",
    "sala de lo", "fiscalía", "ministerio fiscal",
    # Públicas
    "ayuntamiento de", "diputación de", "consejería de",
    "ministerio de", "gobierno de", "delegación de",
    # Órganos internos
    "consejo de administración", "junta de accionistas",
    "junta directiva", "comité de", "comisión de",
]

ORG_ANCHORS = _compile_anchors(ORG_ANCHORS_RAW)

# Sufijos que se buscan DENTRO de la entidad (no en contexto previo)
ORG_SUFFIXES_RAW = [
    "s.a.", "s.l.", "s.l.u.", "s.l.p.", "s.c.", "s.c.p.",
    "s.a.u.", "s.coop.",
]
ORG_SUFFIXES = _compile_anchors(ORG_SUFFIXES_RAW)


# =============================================================================
# APPLY CONTEXTUAL ANCHORS
# =============================================================================

# PiiCategory constants (avoid circular imports)
_PERSON_NAME = PiiCategory.from_string("PERSON_NAME").unwrap()
_LOCATION = PiiCategory.from_string("LOCATION").unwrap()
_ORGANIZATION = PiiCategory.from_string("ORGANIZATION").unwrap()


def apply_contextual_anchors(
    detection: NerDetection,
    text: str,
    window: int = 80,
) -> tuple[NerDetection, bool]:
    """
    Apply contextual anchors to force category.

    Looks for anchor patterns in the context before the entity.
    If found, forces the category regardless of model prediction.

    Args:
        detection: The NER detection to check
        text: Full text for context extraction
        window: Characters before entity to search for anchors

    Returns:
        Tuple of (detection, was_forced):
        - detection: Original or modified detection with forced category
        - was_forced: True if an anchor forced the category
    """
    start = detection.span.start

    # Extract context before the entity
    context_start = max(0, start - window)
    context_before = text[context_start:start]

    # Also get the entity text for suffix checking
    entity_text = detection.value

    # Phase 1: Check PERSON anchors in context
    if PERSON_ANCHORS.search(context_before):
        if detection.category != _PERSON_NAME:
            return detection.with_category(_PERSON_NAME), True
        return detection, True  # Already correct, but was anchored

    # Phase 2: Check LOCATION anchors in context
    if LOCATION_ANCHORS.search(context_before):
        if detection.category != _LOCATION:
            return detection.with_category(_LOCATION), True
        return detection, True

    # Phase 3: Check ORG anchors in context OR suffixes in entity
    if ORG_ANCHORS.search(context_before) or ORG_SUFFIXES.search(entity_text):
        if detection.category != _ORGANIZATION:
            return detection.with_category(_ORGANIZATION), True
        return detection, True

    # No anchor found
    return detection, False
