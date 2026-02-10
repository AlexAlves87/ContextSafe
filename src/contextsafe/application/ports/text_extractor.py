"""
TextExtractor port.

Abstract interface for extracting text from documents.

Traceability:
- Bounded Context: BC-001 (DocumentProcessing)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """Result of text extraction."""

    text: str
    format_detected: str
    page_count: int = 1
    has_tables: bool = False
    has_images: bool = False
    ocr_used: bool = False
    confidence: float = 1.0
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})


class TextExtractor(ABC):
    """
    Port for text extraction from documents.

    Handles different file formats:
    - PDF (pdfplumber + OCR fallback)
    - DOCX (python-docx)
    - TXT (direct read)
    - Images (Tesseract OCR)

    Implementations:
    - PdfPlumberExtractor
    - DocxExtractor
    - TesseractOcrExtractor
    - CompositeTextExtractor (router)
    """

    @abstractmethod
    async def extract(
        self,
        content: bytes,
        filename: str,
        ocr_fallback: bool = True,
    ) -> ExtractionResult:
        """
        Extract text from document content.

        Args:
            content: Raw document bytes
            filename: Original filename (for format detection)
            ocr_fallback: Whether to use OCR if text extraction fails

        Returns:
            ExtractionResult with extracted text and metadata
        """
        ...

    @abstractmethod
    async def extract_from_path(
        self,
        path: str,
        ocr_fallback: bool = True,
    ) -> ExtractionResult:
        """
        Extract text from a file path.

        Args:
            path: Path to the document file
            ocr_fallback: Whether to use OCR if text extraction fails

        Returns:
            ExtractionResult with extracted text and metadata
        """
        ...

    @abstractmethod
    def supports_format(self, extension: str) -> bool:
        """
        Check if this extractor supports a file format.

        Args:
            extension: File extension (e.g., ".pdf")

        Returns:
            True if supported, False otherwise
        """
        ...
