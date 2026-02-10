"""
PII validation service.

Policy gate that validates anonymized text for residual PII before export.
Shared by export and document routes.

Traceability:
- Contract: CNT-T4-EXPORT-001 (Policy Gate)
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class CriticalPiiMatch:
    """A detected critical PII in anonymized text."""
    category: str
    value: str
    position: int
    severity: str  # "CRITICAL", "HIGH"


# Critical PII patterns (MUST be anonymized - export blocked if found)
CRITICAL_PII_PATTERNS = [
    # DNI/NIE (Spanish ID) - CRITICAL
    (r"\b[0-9]{8}[A-Za-z]\b", "DNI/NIE", "CRITICAL"),
    (r"\b[XYZxyz][0-9]{7}[A-Za-z]\b", "NIE", "CRITICAL"),
    # Social Security (Spanish) - CRITICAL
    (r"\b\d{2}/\d{8}/\d{2}\b", "Número Seguridad Social", "CRITICAL"),
    # IBAN / Bank Account - CRITICAL
    (r"\b[A-Z]{2}\d{2}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{2}[-\s]?\d{10}\b", "IBAN", "CRITICAL"),
    (r"\bES\d{22}\b", "IBAN España", "CRITICAL"),
    # Credit Card - CRITICAL
    (r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b", "Tarjeta Crédito", "CRITICAL"),
    (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "Número Tarjeta", "CRITICAL"),
    # Passport - HIGH
    (r"\b[A-Z]{2}[0-9]{7}\b", "Pasaporte", "HIGH"),
    # Email (could leak identity) - HIGH
    (r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", "Email", "HIGH"),
    # Phone (Spanish format) - HIGH
    (r"\b(?:\+34|0034)?[6789]\d{8}\b", "Teléfono", "HIGH"),
]


def validate_no_critical_pii(text: str, strict: bool = True) -> list[CriticalPiiMatch]:
    """
    Scan text for critical PII that should have been anonymized.

    This is the POLICY GATE that prevents export of documents with
    residual PII that violates RGPD.

    Args:
        text: The anonymized text to validate
        strict: If True, also check HIGH severity; if False, only CRITICAL

    Returns:
        List of CriticalPiiMatch objects found (empty = safe to export)
    """
    matches: list[CriticalPiiMatch] = []

    for pattern_str, category, severity in CRITICAL_PII_PATTERNS:
        # Skip HIGH severity in non-strict mode
        if not strict and severity == "HIGH":
            continue

        pattern = re.compile(pattern_str, re.IGNORECASE)

        for match in pattern.finditer(text):
            # Skip if it looks like an alias (e.g., "ID_001", "Persona_001")
            value = match.group()
            if re.match(r"^[A-Za-z]+_\d+$", value):
                continue
            # Skip case numbers like "61/2019"
            if re.match(r"^\d+/\d{4}$", value):
                continue

            matches.append(CriticalPiiMatch(
                category=category,
                value=value,
                position=match.start(),
                severity=severity,
            ))

    return matches


def format_pii_validation_error(matches: list[CriticalPiiMatch]) -> dict:
    """Format validation errors for API response."""
    critical = [m for m in matches if m.severity == "CRITICAL"]
    high = [m for m in matches if m.severity == "HIGH"]

    return {
        "error": "EXPORT_BLOCKED_PII_DETECTED",
        "message": f"Exportación bloqueada: se detectaron {len(matches)} datos personales sin anonimizar",
        "critical_count": len(critical),
        "high_count": len(high),
        "details": [
            {
                "category": m.category,
                "value": m.value[:3] + "***" + m.value[-1:] if len(m.value) > 4 else "***",
                "position": m.position,
                "severity": m.severity,
            }
            for m in matches[:10]  # Limit to first 10
        ],
        "recommendation": "Reprocese el documento con la detección NER actualizada antes de exportar.",
    }
