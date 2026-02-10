"""
Document extractor factory.

Traceability:
- IMPLEMENTATION_PLAN.md Phase 4
"""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

from contextsafe.infrastructure.document_processing.extractors.base import (
    DocumentExtractor,
    ExtractionResult,
)
from contextsafe.infrastructure.document_processing.extractors.pdf_extractor import (
    PdfExtractor,
)
from contextsafe.infrastructure.document_processing.extractors.docx_extractor import (
    DocxExtractor,
)
from contextsafe.infrastructure.document_processing.extractors.txt_extractor import (
    TxtExtractor,
)
from contextsafe.infrastructure.document_processing.extractors.image_extractor import (
    ImageExtractor,
)


class ExtractorFactory:
    """
    Factory for creating document extractors.

    Automatically selects the appropriate extractor based on file type.
    """

    def __init__(
        self,
        ocr_languages: str = "spa+eng",
        tesseract_path: str | None = None,
    ):
        """
        Initialize factory with configuration.

        Args:
            ocr_languages: Languages for OCR (e.g., 'spa+eng').
            tesseract_path: Path to tesseract binary.
        """
        self._extractors: list[DocumentExtractor] = [
            PdfExtractor(),
            DocxExtractor(),
            TxtExtractor(),
            ImageExtractor(
                languages=ocr_languages,
                tesseract_path=tesseract_path,
            ),
        ]

    def get_extractor(self, filename: str) -> DocumentExtractor | None:
        """
        Get appropriate extractor for a filename.

        Args:
            filename: Name of the file to extract.

        Returns:
            DocumentExtractor if supported, None otherwise.
        """
        for extractor in self._extractors:
            if extractor.supports(filename):
                return extractor
        return None

    def supports(self, filename: str) -> bool:
        """Check if any extractor supports this file type."""
        return self.get_extractor(filename) is not None

    def extract(self, file: BinaryIO, filename: str) -> ExtractionResult:
        """
        Extract text from a document.

        Automatically selects the appropriate extractor.

        Args:
            file: Binary file-like object.
            filename: Original filename.

        Returns:
            ExtractionResult with extracted content.

        Raises:
            ValueError: If file type is not supported.
        """
        extractor = self.get_extractor(filename)
        if extractor is None:
            ext = Path(filename).suffix
            return ExtractionResult(
                text="",
                page_count=0,
                errors=[f"Unsupported file type: {ext}"],
                format="unknown",
            )
        return extractor.extract(file, filename)

    def extract_from_path(self, path: Path | str) -> ExtractionResult:
        """
        Extract text from a file path.

        Args:
            path: Path to the document.

        Returns:
            ExtractionResult with extracted content.
        """
        path = Path(path)
        with open(path, "rb") as f:
            return self.extract(f, path.name)

    def extract_from_bytes(self, data: bytes, filename: str) -> ExtractionResult:
        """
        Extract text from bytes.

        Args:
            data: Document content as bytes.
            filename: Original filename.

        Returns:
            ExtractionResult with extracted content.
        """
        from io import BytesIO

        return self.extract(BytesIO(data), filename)

    @property
    def supported_extensions(self) -> list[str]:
        """Get all supported file extensions."""
        extensions = []
        for extractor in self._extractors:
            extensions.extend(extractor.supported_extensions)
        return sorted(set(extensions))


# Global factory instance
_factory: ExtractorFactory | None = None


def get_extractor_factory(
    ocr_languages: str = "spa+eng",
    tesseract_path: str | None = None,
) -> ExtractorFactory:
    """
    Get or create the global extractor factory.

    Args:
        ocr_languages: Languages for OCR.
        tesseract_path: Path to tesseract binary.

    Returns:
        ExtractorFactory instance.
    """
    global _factory
    if _factory is None:
        _factory = ExtractorFactory(
            ocr_languages=ocr_languages,
            tesseract_path=tesseract_path,
        )
    return _factory


def get_extractor(filename: str) -> DocumentExtractor | None:
    """
    Convenience function to get an extractor for a filename.

    Args:
        filename: Name of the file.

    Returns:
        DocumentExtractor if supported, None otherwise.
    """
    return get_extractor_factory().get_extractor(filename)
