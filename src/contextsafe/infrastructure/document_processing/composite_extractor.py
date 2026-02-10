"""
Composite document extractor.

Routes extraction to appropriate handler based on file format.

Traceability:
- Contract: CNT-T3-COMPOSITE-EXTRACTOR-001
- Port: ports.TextExtractor
"""

from __future__ import annotations

from pathlib import Path

from contextsafe.application.ports import ExtractionResult, TextExtractor


class CompositeDocumentExtractor(TextExtractor):
    """
    Composite extractor that routes to format-specific extractors.

    Features:
    - Format auto-detection
    - Extensible architecture
    - Fallback handling
    """

    def __init__(self) -> None:
        """Initialize the composite extractor."""
        self._extractors: dict[str, TextExtractor] = {}
        self._default_extractor: TextExtractor | None = None

    def register_extractor(self, extension: str, extractor: TextExtractor) -> None:
        """
        Register an extractor for a file extension.

        Args:
            extension: File extension (e.g., ".pdf")
            extractor: The extractor to use
        """
        self._extractors[extension.lower()] = extractor

    def set_default_extractor(self, extractor: TextExtractor) -> None:
        """
        Set the default extractor for unknown formats.

        Args:
            extractor: The default extractor
        """
        self._default_extractor = extractor

    def _get_extractor(self, filename: str) -> TextExtractor | None:
        """Get the appropriate extractor for a file."""
        ext = Path(filename).suffix.lower()
        return self._extractors.get(ext, self._default_extractor)

    async def extract(
        self,
        content: bytes,
        filename: str,
        ocr_fallback: bool = True,
    ) -> ExtractionResult:
        """
        Extract text by routing to appropriate extractor.

        Args:
            content: Raw document bytes
            filename: Original filename
            ocr_fallback: Whether to use OCR fallback

        Returns:
            ExtractionResult from the appropriate extractor
        """
        extractor = self._get_extractor(filename)

        if extractor is None:
            return ExtractionResult(
                text="",
                format_detected="unknown",
                confidence=0.0,
                metadata={"error": f"No extractor for format: {filename}"},
            )

        return await extractor.extract(content, filename, ocr_fallback)

    async def extract_from_path(
        self,
        path: str,
        ocr_fallback: bool = True,
    ) -> ExtractionResult:
        """
        Extract text from a file path.

        Args:
            path: Path to the document file
            ocr_fallback: Whether to use OCR fallback

        Returns:
            ExtractionResult from the appropriate extractor
        """
        extractor = self._get_extractor(path)

        if extractor is None:
            return ExtractionResult(
                text="",
                format_detected="unknown",
                confidence=0.0,
                metadata={"error": f"No extractor for format: {path}"},
            )

        return await extractor.extract_from_path(path, ocr_fallback)

    def supports_format(self, extension: str) -> bool:
        """Check if any registered extractor supports the format."""
        ext = extension.lower()
        if ext in self._extractors:
            return True
        if self._default_extractor:
            return self._default_extractor.supports_format(ext)
        return False

    @classmethod
    def create_default(cls) -> CompositeDocumentExtractor:
        """
        Create a composite extractor with default extractors.

        Returns:
            Configured CompositeDocumentExtractor
        """
        from contextsafe.infrastructure.document_processing.docx_extractor import (
            DocxExtractor,
        )
        from contextsafe.infrastructure.document_processing.pdf_extractor import (
            PdfExtractor,
        )
        from contextsafe.infrastructure.document_processing.txt_extractor import (
            TxtExtractor,
        )
        from contextsafe.infrastructure.ocr import TesseractOcrAdapter

        ocr = TesseractOcrAdapter()
        pdf = PdfExtractor(ocr_adapter=ocr)
        docx = DocxExtractor()
        txt = TxtExtractor()

        composite = cls()
        composite.register_extractor(".pdf", pdf)
        composite.register_extractor(".docx", docx)
        composite.register_extractor(".doc", docx)
        composite.register_extractor(".txt", txt)
        composite.register_extractor(".text", txt)
        composite.register_extractor(".md", txt)

        # Image formats use OCR
        composite.register_extractor(".png", ocr)
        composite.register_extractor(".jpg", ocr)
        composite.register_extractor(".jpeg", ocr)

        composite.set_default_extractor(txt)

        return composite
