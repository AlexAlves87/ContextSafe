"""
PDF text extractor.

Uses pdfplumber for text extraction with OCR fallback.

Traceability:
- Contract: CNT-T3-PDF-EXTRACTOR-001
- Port: ports.TextExtractor
"""

from __future__ import annotations

import io

from contextsafe.application.ports import ExtractionResult, TextExtractor


class PdfExtractor(TextExtractor):
    """
    PDF text extractor using pdfplumber.

    Features:
    - Text extraction from text-based PDFs
    - Table detection
    - OCR fallback for scanned pages
    """

    def __init__(
        self,
        ocr_adapter: TextExtractor | None = None,
        min_text_length: int = 50,
    ) -> None:
        """
        Initialize the PDF extractor.

        Args:
            ocr_adapter: Optional OCR adapter for scanned pages
            min_text_length: Minimum text length to consider a page as text-based
        """
        self._ocr_adapter = ocr_adapter
        self._min_text_length = min_text_length

    async def extract(
        self,
        content: bytes,
        filename: str,
        ocr_fallback: bool = True,
    ) -> ExtractionResult:
        """
        Extract text from PDF content.

        Args:
            content: Raw PDF bytes
            filename: Original filename
            ocr_fallback: Whether to use OCR for scanned pages

        Returns:
            ExtractionResult with extracted text
        """
        try:
            import pdfplumber

            texts: list[str] = []
            page_count = 0
            has_tables = False
            has_images = False
            ocr_used = False

            with pdfplumber.open(io.BytesIO(content)) as pdf:
                page_count = len(pdf.pages)

                for page in pdf.pages:
                    # Extract text
                    page_text = page.extract_text() or ""

                    # Check for tables
                    tables = page.extract_tables()
                    if tables:
                        has_tables = True
                        # Convert tables to text
                        for table in tables:
                            for row in table:
                                row_text = " | ".join(cell or "" for cell in row if cell)
                                if row_text.strip():
                                    texts.append(row_text)

                    # Check for images
                    if page.images:
                        has_images = True

                    # Check if page needs OCR
                    if len(page_text.strip()) < self._min_text_length:
                        if ocr_fallback and self._ocr_adapter and has_images:
                            # Try OCR on page image
                            try:
                                page_image = page.to_image(resolution=300)
                                img_bytes = io.BytesIO()
                                page_image.original.save(img_bytes, format="PNG")
                                ocr_result = await self._ocr_adapter.extract(
                                    img_bytes.getvalue(), "page.png"
                                )
                                if ocr_result.text.strip():
                                    page_text = ocr_result.text
                                    ocr_used = True
                            except Exception:
                                pass

                    if page_text.strip():
                        texts.append(page_text)

            full_text = "\n\n".join(texts)

            return ExtractionResult(
                text=full_text,
                format_detected="pdf",
                page_count=page_count,
                has_tables=has_tables,
                has_images=has_images,
                ocr_used=ocr_used,
                confidence=0.9 if not ocr_used else 0.7,
            )

        except ImportError:
            return ExtractionResult(
                text="",
                format_detected="pdf",
                confidence=0.0,
                metadata={"error": "pdfplumber not installed"},
            )
        except Exception as e:
            return ExtractionResult(
                text="",
                format_detected="pdf",
                confidence=0.0,
                metadata={"error": str(e)},
            )

    async def extract_from_path(
        self,
        path: str,
        ocr_fallback: bool = True,
    ) -> ExtractionResult:
        """
        Extract text from a PDF file.

        Args:
            path: Path to the PDF file
            ocr_fallback: Whether to use OCR for scanned pages

        Returns:
            ExtractionResult with extracted text
        """
        try:
            with open(path, "rb") as f:
                content = f.read()
            return await self.extract(content, path, ocr_fallback)
        except FileNotFoundError:
            return ExtractionResult(
                text="",
                format_detected="pdf",
                confidence=0.0,
                metadata={"error": f"File not found: {path}"},
            )

    def supports_format(self, extension: str) -> bool:
        """Check if this extractor supports the format."""
        return extension.lower() == ".pdf"
