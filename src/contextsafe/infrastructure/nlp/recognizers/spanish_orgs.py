"""
Spanish organization recognizer.

Recognizes Spanish organizations including:
- Companies with legal forms (S.L., S.A., S.L.P., S.C., S.L.U., etc.)
- Law firms (Abogados, Bufete, Despacho)
- Professional associations (Colegio, Asociación)

Traceability:
- IMPLEMENTATION_PLAN.md Phase 5
- controlled_vocabulary.yaml#pii_categories.ORGANIZATION
"""

from __future__ import annotations

from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class SpanishOrgRecognizer(PatternRecognizer):
    """
    Recognizer for Spanish organizations.

    Handles:
    - Spanish legal forms: S.L., S.A., S.L.P., S.L.U., S.C., etc.
    - Law firms and professional services
    - Public and private entities
    """

    # Spanish legal entity suffixes
    LEGAL_FORMS = [
        r"S\.?L\.?P\.?",      # Sociedad Limitada Profesional
        r"S\.?L\.?U\.?",      # Sociedad Limitada Unipersonal
        r"S\.?L\.?",          # Sociedad Limitada
        r"S\.?A\.?U\.?",      # Sociedad Anónima Unipersonal
        r"S\.?A\.?",          # Sociedad Anónima
        r"S\.?C\.?",          # Sociedad Civil
        r"S\.?Coop\.?",       # Sociedad Cooperativa
        r"S\.?Com\.?",        # Sociedad Comanditaria
        r"A\.?I\.?E\.?",      # Agrupación de Interés Económico
        r"Cía\.?",            # Compañía
        r"Cia\.?",            # Compañía (sin tilde)
        r"Ltda\.?",           # Limitada
        r"Inc\.?",            # Incorporated (foreign)
        r"Corp\.?",           # Corporation (foreign)
    ]

    PATTERNS = [
        # Pattern 1: Name + Spanish legal form (e.g., "Mentor Abogados S.L.P.")
        # Very specific - requires legal form suffix
        Pattern(
            "ORG_LEGAL_FORM",
            r"\b([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s&\-]{2,30})\s+(S\.?L\.?P\.?|S\.?L\.?U\.?|S\.?L\.?|S\.?A\.?U\.?|S\.?A\.?|S\.?C\.?)(?:\s|$|,|\.|\n)",
            0.98,
        ),
        # Pattern 2: "Abogados" with legal form (very common in legal docs)
        Pattern(
            "ORG_ABOGADOS_LEGAL",
            r"\b([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s&]{2,20}\s+Abogados)\s+(S\.?L\.?P\.?|S\.?L\.?)(?:\s|$|,|\.|\n)",
            0.98,
        ),
        # Pattern 3: After "Parte Demandante:" - for company plaintiffs
        Pattern(
            "ORG_PLAINTIFF",
            r"Parte\s+Demandante:\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s&\.\-]{5,50})(?=\s*\n)",
            0.95,
        ),
        # Pattern 4: Banks (well-known names)
        Pattern(
            "ORG_BANK",
            r"\b((?:Banco\s+)?(?:Santander|BBVA|CaixaBank|Sabadell|Bankinter|ING|Openbank|Bankia|Kutxabank|Unicaja|Ibercaja)(?:\s+S\.?A\.?)?)(?:\s|$|,|\.)",
            0.95,
        ),
        # Pattern 5: "Compañía de Servicios" pattern (specific)
        Pattern(
            "ORG_COMPANIA_SERVICIOS",
            r"\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\s+Compañía\s+de\s+Servicios\s+Integrales\s+(S\.?L\.?)(?:\s|$|,|\.)",
            0.98,
        ),
    ]

    CONTEXT = [
        "empresa", "compañía", "sociedad", "mercantil", "entidad",
        "demandante", "actora", "ejecutante", "acreedora", "parte",
        "representada", "cliente", "proveedor", "contratista",
        "banco", "aseguradora", "despacho", "bufete", "firma",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "es",
        supported_entity: str = "ES_ORG",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )

    # Common Spanish words that are NEVER organization names
    FALSE_POSITIVE_WORDS = {
        # Articles and prepositions
        "del", "de", "la", "el", "las", "los", "al", "en", "con", "por", "para",
        "como", "que", "sin", "sobre", "entre", "hacia", "desde", "hasta",
        # Common verbs
        "hubiera", "habría", "había", "haber", "sido", "siendo", "fueron",
        "demanda", "reclama", "solicita", "declara", "declarada", "declarado",
        # Legal terms
        "concurso", "sociedad", "empresa", "mercantil", "entidad", "parte",
        "demandante", "demandada", "actora", "decisión", "cierre", "financiación",
        "propia", "propias", "propio", "propios",
        # Other common words
        "mismo", "misma", "mismos", "mismas", "otro", "otra", "otros", "otras",
    }

    def validate_result(self, pattern_text: str) -> Optional[bool]:
        """Validate organization name."""
        clean = pattern_text.strip()

        if not clean or len(clean) < 3:
            return False

        # Must not be just a legal form without a name
        legal_forms_only = ["S.L.", "S.A.", "S.L.P.", "S.L.U.", "S.C."]
        if clean.upper().replace(" ", "") in [lf.replace(".", "") for lf in legal_forms_only]:
            return False

        # Reject common Spanish words that are never organization names
        clean_lower = clean.lower()
        # Check each word in the text
        words = clean_lower.split()
        for word in words:
            if word in self.FALSE_POSITIVE_WORDS:
                return False

        # Reject if it's just a single common word
        if clean_lower in self.FALSE_POSITIVE_WORDS:
            return False

        # Organization names should typically start with uppercase
        if not clean[0].isupper():
            return False

        return True
