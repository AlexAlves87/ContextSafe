"""Tests for glossary-based consistency scan in anonymization."""

import re

import pytest


class TestGlossaryConsistencyScan:
    """The glossary consistency scan should find bare names that NER missed."""

    def _scan(self, text, known_mappings, replaced_spans=None):
        """Simulate the consistency scan algorithm."""
        if replaced_spans is None:
            replaced_spans = []

        additional = []
        for key, alias_value in known_mappings.items():
            parts = key.split(":", 1)
            if len(parts) != 2:
                continue
            category_str, normalized = parts

            if category_str not in ("PERSON_NAME", "ORGANIZATION"):
                continue
            if len(normalized) < 5:
                continue

            pattern = re.compile(re.escape(normalized), re.IGNORECASE)
            for m in pattern.finditer(text):
                m_start, m_end = m.start(), m.end()

                overlaps = False
                for r_start, r_end in replaced_spans:
                    if m_start < r_end and m_end > r_start:
                        overlaps = True
                        break
                if overlaps:
                    continue

                additional.append((m_start, m_end, alias_value))

        return additional

    def test_finds_bare_name_in_text(self):
        """A name known to the glossary should be found without title prefix."""
        text = "En la tabla consta Rafael Durán Calvente como demandante."
        known = {"PERSON_NAME:rafael durán calvente": "Persona_001"}

        matches = self._scan(text, known)
        assert len(matches) == 1
        assert matches[0][2] == "Persona_001"

    def test_does_not_duplicate_already_replaced_spans(self):
        """Spans already replaced by NER should not be scanned again."""
        text = "D. Persona_001 presentó recurso. Rafael Durán Calvente firmó."
        known = {"PERSON_NAME:rafael durán calvente": "Persona_001"}
        # First occurrence "D. Rafael..." was at [3:27], now replaced
        # Second occurrence "Rafael Durán Calvente" starts at 32
        replaced = [(3, 14)]  # "Persona_001" span

        matches = self._scan(text, known, replaced)
        assert len(matches) == 1
        assert matches[0][0] == 33  # The bare name occurrence

    def test_handles_table_pipe_format(self):
        """Names in pipe-separated table cells should be found."""
        text = "Nombre | Rol\nRafael Durán Calvente | Demandante"
        known = {"PERSON_NAME:rafael durán calvente": "Persona_001"}

        matches = self._scan(text, known)
        assert len(matches) == 1

    def test_skips_short_values(self):
        """Values shorter than 5 chars should be skipped to avoid false matches."""
        text = "El juez Ana decidió sobre el caso."
        known = {"PERSON_NAME:ana": "Persona_001"}

        matches = self._scan(text, known)
        assert len(matches) == 0

    def test_skips_non_person_non_org(self):
        """Only PERSON_NAME and ORGANIZATION categories are scanned."""
        text = "la fecha 4 de diciembre de 2024 aparece aquí"
        known = {"DATE:4 de diciembre de 2024": "Fecha_001"}

        matches = self._scan(text, known)
        assert len(matches) == 0

    def test_finds_organization_in_text(self):
        """Organization names should also be found by the scan."""
        text = "La sentencia afecta a Mentor Abogados por incumplimiento."
        known = {"ORGANIZATION:mentor abogados": "Org_001"}

        matches = self._scan(text, known)
        assert len(matches) == 1
        assert matches[0][2] == "Org_001"

    def test_case_insensitive_matching(self):
        """Matching should be case-insensitive."""
        text = "RAFAEL DURÁN CALVENTE aparece en mayúsculas."
        known = {"PERSON_NAME:rafael durán calvente": "Persona_001"}

        matches = self._scan(text, known)
        assert len(matches) == 1

    def test_multiple_occurrences(self):
        """Multiple occurrences of the same name should all be found."""
        text = "Rafael Durán Calvente presentó. Rafael Durán Calvente firmó."
        known = {"PERSON_NAME:rafael durán calvente": "Persona_001"}

        matches = self._scan(text, known)
        assert len(matches) == 2
