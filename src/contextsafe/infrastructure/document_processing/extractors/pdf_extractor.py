"""
PDF document extractor using pdfplumber.

Traceability:
- IMPLEMENTATION_PLAN.md Phase 4.1
"""

from __future__ import annotations

from typing import BinaryIO

from contextsafe.infrastructure.document_processing.extractors.base import (
    DocumentExtractor,
    ExtractionResult,
)


class PdfExtractor(DocumentExtractor):
    """
    Extract text from PDF documents.

    Uses pdfplumber as primary extractor with pypdf2 as fallback.
    Extracts text, tables, and metadata.
    """

    @property
    def supported_extensions(self) -> list[str]:
        return ["pdf"]

    @property
    def format_name(self) -> str:
        return "PDF"

    def extract(self, file: BinaryIO, filename: str = "") -> ExtractionResult:
        """
        Extract text from PDF using pdfplumber.

        Falls back to pypdf2 if pdfplumber fails.
        """
        errors: list[str] = []
        text_parts: list[str] = []
        tables: list[list[list[str]]] = []
        page_count = 0
        metadata: dict[str, str] = {}

        # Try pdfplumber first
        try:
            import pdfplumber

            with pdfplumber.open(file) as pdf:
                page_count = len(pdf.pages)

                # Extract metadata
                if pdf.metadata:
                    for key, value in pdf.metadata.items():
                        if value and isinstance(value, str):
                            metadata[key] = value

                # Extract text and tables from each page
                for i, page in enumerate(pdf.pages):
                    try:
                        # Extract text
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(f"--- Página {i + 1} ---\n{page_text}")

                        # Extract tables
                        page_tables = page.extract_tables()
                        if page_tables:
                            for table in page_tables:
                                # Convert None values to empty strings
                                cleaned_table = [
                                    [cell or "" for cell in row]
                                    for row in table
                                    if row
                                ]
                                if cleaned_table:
                                    tables.append(cleaned_table)

                    except Exception as e:
                        errors.append(f"Error en página {i + 1}: {str(e)}")

            text = "\n\n".join(text_parts)

        except Exception as e:
            errors.append(f"pdfplumber error: {str(e)}")
            text = ""

            # Fallback to pypdf2
            try:
                file.seek(0)
                text, page_count, metadata = self._extract_with_pypdf2(file)
            except Exception as e2:
                errors.append(f"pypdf2 fallback error: {str(e2)}")

        return ExtractionResult(
            text=text,
            page_count=page_count,
            tables=tables,
            metadata=metadata,
            errors=errors,
            format="pdf",
        )

    def _extract_with_pypdf2(
        self, file: BinaryIO
    ) -> tuple[str, int, dict[str, str]]:
        """Fallback extraction using pypdf2."""
        from pypdf import PdfReader

        reader = PdfReader(file)
        page_count = len(reader.pages)

        text_parts = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(f"--- Página {i + 1} ---\n{page_text}")

        text = "\n\n".join(text_parts)

        metadata = {}
        if reader.metadata:
            for key in ["/Title", "/Author", "/Subject", "/Creator"]:
                if key in reader.metadata and reader.metadata[key]:
                    metadata[key.lstrip("/")] = str(reader.metadata[key])

        return text, page_count, metadata
