"""
Spanish person name recognizer.

Recognizes Spanish names including:
- Names with formal prefixes (D., Dña., Don, Doña, Sr., Sra.)
- Names in UPPERCASE (common in legal documents)
- Names with compound surnames

This recognizer compensates for spaCy's limitations with Spanish legal documents.

Traceability:
- IMPLEMENTATION_PLAN.md Phase 5
- controlled_vocabulary.yaml#pii_categories.PERSON_NAME
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class SpanishNameRecognizer(PatternRecognizer):
    """
    Recognizer for Spanish person names.

    Handles:
    - Formal prefixes: D., Dña., Don, Doña, Sr., Sra.
    - Names in UPPERCASE (legal documents)
    - Compound surnames with connectors (de, del, de la, de los)
    """

    # Common Spanish first names for pattern matching
    COMMON_NAMES = [
        # Male names
        "AGUSTÍN", "AGUSTIN", "ALEJANDRO", "ANTONIO", "CARLOS", "DANIEL",
        "DAVID", "FERNANDO", "FRANCISCO", "IGNACIO", "JAVIER", "JORGE",
        "JOSE", "JOSÉ", "JUAN", "LUIS", "MANUEL", "MIGUEL", "PABLO",
        "PEDRO", "RAFAEL", "ROBERTO", "SERGIO",
        # Female names
        "ANA", "ANDREA", "CARMEN", "CRISTINA", "ELENA", "ISABEL", "LAURA",
        "LUCIA", "LUCÍA", "MARIA", "MARÍA", "MARTA", "NURIA", "PATRICIA",
        "PAULA", "RAQUEL", "ROSA", "SANDRA", "SARA", "SILVIA", "SONIA", "SUSANA",
    ]

    # Surname connectors
    CONNECTORS = r"(?:de\s+la\s+|de\s+los\s+|de\s+las\s+|del\s+|de\s+)?"

    # Build name pattern (first name + optional connector + surname + optional second surname)
    NAME_WORD = r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+"
    NAME_WORD_UPPER = r"[A-ZÁÉÍÓÚÑ]{2,}"

    PATTERNS = [
        # Pattern 1: D./Dña. + Mixed-case Name (e.g., "D. Juan García López")
        Pattern(
            "NAME_WITH_TITLE_D",
            r"\b(?:D\.|Dña\.|D\.ª|Dª\.?)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})(?=\s*[,.\n]|\s+con\s|\s+y\s|$)",
            0.95,
        ),
        # Pattern 2: Don/Doña + Mixed-case Name (e.g., "Don Juan García")
        Pattern(
            "NAME_WITH_TITLE_DON",
            r"(?i)\b(?:Don|Doña)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})(?=\s*[,.\n]|\s+con\s|\s+y\s|$)",
            0.95,
        ),
        # Pattern 3: Sr./Sra. + Name (e.g., "Sr. García López")
        Pattern(
            "NAME_WITH_TITLE_SR",
            r"\b(?:Sr\.|Sra\.|Señor|Señora)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,2})(?=\s*[,.\n]|$)",
            0.90,
        ),
        # Pattern 4: UPPERCASE names after prefix (e.g., "DON PEDRO MARTINEZ")
        # Case-insensitive for prefix, captures ALL-CAPS names
        Pattern(
            "NAME_UPPERCASE_WITH_PREFIX",
            r"(?i)\b(?:D\.|Dña\.|Don|Doña)\s+([A-ZÁÉÍÓÚÑ]{2,}(?:\s+(?:DE\s+LA\s+|DE\s+LOS\s+|DEL\s+|DE\s+)?[A-ZÁÉÍÓÚÑ]{2,}){1,3})(?=\s*[,.\n]|\s+con\s|$)",
            0.95,
        ),
        # Pattern 5: After "Parte Demandada/Demandante:" context (most reliable)
        Pattern(
            "NAME_LEGAL_PARTY",
            r"Parte\s+(?:Demandad[ao]|Demandante|Actor[ae]?):\s*(?:D\.|Dña\.)?\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]{5,40})(?=\s*\n)",
            0.98,
        ),
        # Pattern 6: Name followed by professional title/role (e.g., "Agustín Pardillo Hernández, Letrado")
        # Captures: FirstName LastName LastName, Role (allows newline between comma and role)
        Pattern(
            "NAME_WITH_ROLE",
            r"\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3}),\s*\n?\s*(?:Letrado|Abogado|Procurador|Magistrado|Juez|Secretario|Fiscal|Notario|Registrador|Director|Presidente|Vocal|Consejero)",
            0.92,
        ),
        # Pattern 7: Excmo./Excma. Sr./Sra. D./Dña. + Name (judicial honorifics)
        # Added negative lookahead to stop before "Votación", "Ponente", etc.
        Pattern(
            "NAME_JUDICIAL_HONORIFIC",
            r"\b(?:Excm[oa]\.|Ilm[oa]\.)\s*(?:Sr\.|Sra\.)\s*(?:D\.|Dña\.)\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+(?!Votación|Ponente|Materia|Recurso)[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})(?=\s*\n|\s*$|\s+Votación|\s+Ponente)",
            0.95,
        ),
        # Pattern 8: Name after newline followed by role (common in document headers)
        # e.g., "Agustín Pardillo Hernández,\nLetrado del Gabinete Técnico"
        Pattern(
            "NAME_HEADER_WITH_ROLE",
            r"\n([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3}),?\s*\n\s*(?:Letrado|Abogado|Procurador|Magistrado|Secretario)",
            0.90,
        ),
        # Pattern 9: Name without prefix followed by comma and role context
        # Captures names like "Agustín Pardillo Hernández," when followed by professional role
        Pattern(
            "NAME_STANDALONE_WITH_ROLE_CONTEXT",
            r"(?:^|\n)([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?),\s*(?:\n\s*)?(?:Letrado|Abogado|Procurador|Magistrado|Juez|Secretario|Fiscal|Notario|del\s+Gabinete)",
            0.88,
        ),
        # Pattern 10: Name in list after D./Dña. entries (detects standalone names in magistrate lists)
        # e.g., after "D. Fernando Cerdá Albero\n" comes "Agustín Pardillo Hernández,"
        Pattern(
            "NAME_AFTER_MAGISTRATE_LIST",
            r"(?:D\.|Dña\.)[^\n]+\n([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?),",
            0.85,
        ),
    ]

    CONTEXT = [
        "demandado", "demandada", "demandante", "acusado", "acusada",
        "querellante", "denunciante", "compareciente", "firmante",
        "representado", "representada", "otorgante", "apoderado",
        "cliente", "paciente", "usuario", "persona", "ciudadano",
        "nombre", "apellido", "apellidos", "identificado", "identificada",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "es",
        supported_entity: str = "ES_PERSON",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )
        self._all_names = self._load_name_gazetteers()

    @staticmethod
    def _load_name_gazetteers() -> frozenset:
        """Load all name gazetteers from ml/gazetteers/."""
        base = Path(__file__).resolve().parents[4] / "ml" / "gazetteers"
        names: set[str] = set()

        # nombres_todos.json → campo "nombres" (lista)
        todos = base / "nombres_todos.json"
        if todos.exists():
            data = json.loads(todos.read_text(encoding="utf-8"))
            names.update(n.upper() for n in data.get("nombres", []))

        # nombres_arcaicos_flat.json → campo "todos_nombres" (lista)
        arcaicos = base / "nombres_arcaicos_flat.json"
        if arcaicos.exists():
            data = json.loads(arcaicos.read_text(encoding="utf-8"))
            names.update(n.upper() for n in data.get("todos_nombres", []))

        # nombres_hombres/mujeres.json → campo "nombres_por_decada"
        # Cada década es lista de {"nombre": "JOSE", "frecuencia": 8395}
        for f in ["nombres_hombres.json", "nombres_mujeres.json"]:
            path = base / f
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                for decade_entries in data.get("nombres_por_decada", {}).values():
                    for entry in decade_entries:
                        if isinstance(entry, dict):
                            names.add(entry["nombre"].upper())
                        else:
                            names.add(str(entry).upper())

        # Fallback: si no se encontraron gazetteers, usar COMMON_NAMES
        if not names:
            names.update(SpanishNameRecognizer.COMMON_NAMES)

        return frozenset(names)

    # Words that should NEVER appear in a person's name
    NAME_FALSE_POSITIVES = {
        # Legal terms
        "JUZGADO", "PRIMERA", "INSTANCIA", "PROCEDIMIENTO", "JUICIO",
        "VERBAL", "CIVIL", "PENAL", "AUDIENCIA", "TRIBUNAL", "SALA",
        "SENTENCIA", "DEMANDA", "ESCRITO", "RECURSO", "APELACIÓN",
        "DILIGENCIA", "ORDENACIÓN", "PROVIDENCIA", "AUTO", "DECRETO",
        # Document structure words (these indicate we captured too much)
        "VOTACIÓN", "VOTACION", "PONENTE", "MATERIA", "RECURSO",
        "FALLO", "LETRADO", "ABOGADO", "PROCURADOR",
        # Common words that aren't names
        "PRESIDENTE", "SECRETARIO", "GABINETE", "TÉCNICO", "TECNICO",
    }

    def validate_result(self, pattern_text: str) -> Optional[bool]:
        """
        Validate that the matched text looks like a name.

        Filters out:
        - Common non-name uppercase words
        - Single words (unless known first name)
        - Numbers or special characters
        - Names that are too long (probably multiple people)
        """
        # Clean the text
        clean = pattern_text.strip()

        # Remove common prefixes for validation
        clean = re.sub(
            r"^(?:D\.|Dña\.|D\.ª|Dª\.?|Don|Doña|Sr\.|Sra\.|Señor|Señora|Excm[oa]\.|Ilm[oa]\.)\s*",
            "",
            clean,
            flags=re.IGNORECASE,
        )
        # Also remove secondary prefixes
        clean = re.sub(
            r"^(?:Sr\.|Sra\.)\s*(?:D\.|Dña\.)\s*",
            "",
            clean,
            flags=re.IGNORECASE,
        )
        clean = clean.strip()

        if not clean:
            return False

        # Must have at least one space (first name + surname) unless it's a known name
        words = clean.split()
        if len(words) < 2:
            # Single word - only valid if it's a known first name
            return clean.upper() in self._all_names

        # CRITICAL: Names with more than 5 words are probably multiple people or errors
        if len(words) > 5:
            return False

        # Check if any word is a false positive
        for word in words:
            if word.upper() in self.NAME_FALSE_POSITIVES:
                return False

        # Must not contain numbers
        if any(c.isdigit() for c in clean):
            return False

        # Reject if contains newlines (probably multiple entries)
        if '\n' in pattern_text:
            return False

        return True
