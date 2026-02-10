"""
IngestPreprocessor implementation.

Phase 1 normalization: permanent, stored in database.

Traceability:
- Design: docs/plans/2026-02-01-text-preprocessing-design.md
"""
from __future__ import annotations

from contextsafe.application.ports.text_preprocessor import IngestPreprocessor
from contextsafe.domain.document_processing.services import text_normalization as norm


class DefaultIngestPreprocessor(IngestPreprocessor):
    """
    Default implementation of Phase 1 preprocessing.

    Applies normalization that:
    - Does NOT significantly change semantics
    - Does NOT significantly change offsets
    - IS permanent (stored in database)

    Operations:
    - Unicode NFKC normalization
    - Line endings normalization (CRLF -> LF)
    - NBSP and similar -> regular space
    - Control character removal (except newline, tab)
    """

    def preprocess(self, raw_text: str) -> str:
        """
        Apply Phase 1 normalization.

        Args:
            raw_text: Raw text from extractor

        Returns:
            Normalized text for permanent storage
        """
        text = raw_text

        # 1. Unicode NFKC (handles ligatures, superscripts, fullwidth)
        text = norm.normalize_unicode(text)

        # 2. Line endings (CRLF, CR -> LF)
        text = norm.normalize_line_endings(text)

        # 3. Whitespace chars (NBSP, etc. -> space)
        text = norm.normalize_whitespace_chars(text)

        # 4. Control chars (remove garbage, keep \n \t)
        text = norm.remove_control_chars(text)

        return text
