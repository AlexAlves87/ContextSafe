"""
Base interface for document extractors.

Traceability:
- IMPLEMENTATION_PLAN.md Phase 4
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO


@dataclass
class ExtractionResult:
    """Result of document text extraction."""

    text: str
    """Extracted plain text content."""

    page_count: int = 1
    """Number of pages in the document."""

    tables: list[list[list[str]]] = field(default_factory=list)
    """Extracted tables as list of rows, each row is list of cells."""

    metadata: dict[str, str] = field(default_factory=dict)
    """Document metadata (title, author, etc.)."""

    errors: list[str] = field(default_factory=list)
    """Any errors encountered during extraction."""

    format: str = "unknown"
    """Document format (pdf, docx, txt, image)."""

    @property
    def success(self) -> bool:
        """Check if extraction was successful."""
        return len(self.text.strip()) > 0 or len(self.tables) > 0

    @property
    def char_count(self) -> int:
        """Get character count of extracted text."""
        return len(self.text)

    @property
    def word_count(self) -> int:
        """Get approximate word count."""
        return len(self.text.split())


class DocumentExtractor(ABC):
    """
    Abstract base class for document text extraction.

    Each extractor handles a specific document format.
    """

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """List of supported file extensions (lowercase, without dot)."""
        ...

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Human-readable format name."""
        ...

    def supports(self, filename: str) -> bool:
        """Check if this extractor supports the given filename."""
        ext = Path(filename).suffix.lower().lstrip(".")
        return ext in self.supported_extensions

    @abstractmethod
    def extract(self, file: BinaryIO, filename: str = "") -> ExtractionResult:
        """
        Extract text from a document.

        Args:
            file: Binary file-like object to extract from.
            filename: Original filename (for format detection).

        Returns:
            ExtractionResult with extracted text and metadata.
        """
        ...

    def extract_from_path(self, path: Path | str) -> ExtractionResult:
        """
        Extract text from a file path.

        Args:
            path: Path to the document file.

        Returns:
            ExtractionResult with extracted text and metadata.
        """
        path = Path(path)
        with open(path, "rb") as f:
            return self.extract(f, path.name)

    def extract_from_bytes(self, data: bytes, filename: str = "") -> ExtractionResult:
        """
        Extract text from bytes.

        Args:
            data: Document content as bytes.
            filename: Original filename (for format detection).

        Returns:
            ExtractionResult with extracted text and metadata.
        """
        from io import BytesIO

        return self.extract(BytesIO(data), filename)
