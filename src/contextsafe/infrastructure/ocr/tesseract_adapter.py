"""
Tesseract OCR adapter.

Uses Tesseract for optical character recognition on images.

Traceability:
- Contract: CNT-T3-TESSERACT-ADAPTER-001
- Port: ports.TextExtractor
"""

from __future__ import annotations

import io
from pathlib import Path

from contextsafe.application.ports import ExtractionResult, TextExtractor


class TesseractOcrAdapter(TextExtractor):
    """
    OCR service using Tesseract.

    Extracts text from images (PNG, JPG, JPEG) and scanned PDFs.
    """

    def __init__(
        self,
        language: str = "spa+eng",
        tesseract_cmd: str | None = None,
    ) -> None:
        """
        Initialize the Tesseract OCR adapter.

        Args:
            language: Tesseract language codes (e.g., "spa+eng")
            tesseract_cmd: Path to tesseract executable (optional)
        """
        self._language = language
        self._tesseract_cmd = tesseract_cmd
        self._is_available: bool | None = None

    def _check_available(self) -> bool:
        """Check if Tesseract is available."""
        if self._is_available is not None:
            return self._is_available

        try:
            import pytesseract

            if self._tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = self._tesseract_cmd

            # Test tesseract
            pytesseract.get_tesseract_version()
            self._is_available = True
        except Exception:
            self._is_available = False

        return self._is_available

    async def extract(
        self,
        content: bytes,
        filename: str,
        ocr_fallback: bool = True,
    ) -> ExtractionResult:
        """
        Extract text from image content using OCR.

        Args:
            content: Raw image bytes
            filename: Original filename
            ocr_fallback: Ignored (OCR is the primary method)

        Returns:
            ExtractionResult with extracted text
        """
        if not self._check_available():
            return ExtractionResult(
                text="",
                format_detected="image",
                ocr_used=True,
                confidence=0.0,
                metadata={"error": "Tesseract not available"},
            )

        try:
            import pytesseract
            from PIL import Image

            # Open image from bytes
            image = Image.open(io.BytesIO(content))

            # Extract text
            text = pytesseract.image_to_string(
                image,
                lang=self._language,
                config="--psm 1",  # Automatic page segmentation with OSD
            )

            # Get confidence score
            data = pytesseract.image_to_data(
                image,
                lang=self._language,
                output_type=pytesseract.Output.DICT,
            )

            # Calculate average confidence
            confidences = [int(c) for c in data["conf"] if c != "-1" and str(c).isdigit()]
            avg_confidence = sum(confidences) / len(confidences) / 100 if confidences else 0.5

            ext = Path(filename).suffix.lower()
            return ExtractionResult(
                text=text.strip(),
                format_detected=ext.lstrip(".") or "image",
                page_count=1,
                has_images=True,
                ocr_used=True,
                confidence=avg_confidence,
            )

        except Exception as e:
            return ExtractionResult(
                text="",
                format_detected="image",
                ocr_used=True,
                confidence=0.0,
                metadata={"error": str(e)},
            )

    async def extract_from_path(
        self,
        path: str,
        ocr_fallback: bool = True,
    ) -> ExtractionResult:
        """
        Extract text from an image file.

        Args:
            path: Path to the image file
            ocr_fallback: Ignored (OCR is the primary method)

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
                format_detected="unknown",
                confidence=0.0,
                metadata={"error": f"File not found: {path}"},
            )

    def supports_format(self, extension: str) -> bool:
        """Check if this extractor supports the format."""
        supported = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"}
        return extension.lower() in supported
