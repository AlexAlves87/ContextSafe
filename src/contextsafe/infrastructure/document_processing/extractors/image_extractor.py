"""
Image document extractor using Tesseract OCR.

Traceability:
- IMPLEMENTATION_PLAN.md Phase 4.4
"""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

from contextsafe.infrastructure.document_processing.extractors.base import (
    DocumentExtractor,
    ExtractionResult,
)


class ImageExtractor(DocumentExtractor):
    """
    Extract text from images using Tesseract OCR.

    Supports PNG, JPG, JPEG, TIFF, BMP formats.
    Performs image preprocessing for better OCR results.
    """

    def __init__(
        self,
        languages: str = "spa+eng",
        tesseract_path: str | None = None,
    ):
        """
        Initialize image extractor.

        Args:
            languages: Tesseract language codes (e.g., 'spa+eng').
            tesseract_path: Path to tesseract binary (optional).
        """
        self.languages = languages
        self.tesseract_path = tesseract_path

    @property
    def supported_extensions(self) -> list[str]:
        return ["png", "jpg", "jpeg", "tiff", "tif", "bmp", "webp"]

    @property
    def format_name(self) -> str:
        return "Image (OCR)"

    def extract(self, file: BinaryIO, filename: str = "") -> ExtractionResult:
        """
        Extract text from image using Tesseract OCR.

        Applies preprocessing for better results.
        """
        errors: list[str] = []
        metadata: dict[str, str] = {}

        try:
            # Check if pytesseract is available
            import pytesseract
            from PIL import Image

            # Configure tesseract path if provided
            if self.tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_path

            # Load image
            image = Image.open(file)
            metadata["image_size"] = f"{image.width}x{image.height}"
            metadata["image_mode"] = image.mode

            # Preprocess image for better OCR
            processed_image = self._preprocess_image(image)

            # Perform OCR
            text = pytesseract.image_to_string(
                processed_image,
                lang=self.languages,
                config="--psm 1",  # Automatic page segmentation with OSD
            )

            # Clean up text
            text = self._clean_ocr_text(text)

            # Get OCR confidence data
            try:
                data = pytesseract.image_to_data(
                    processed_image,
                    lang=self.languages,
                    output_type=pytesseract.Output.DICT,
                )
                confidences = [
                    int(c) for c in data["conf"] if c != "-1" and str(c).isdigit()
                ]
                if confidences:
                    avg_confidence = sum(confidences) / len(confidences)
                    metadata["ocr_confidence"] = f"{avg_confidence:.1f}%"
            except Exception:
                pass  # Confidence data is optional

            metadata["languages"] = self.languages

        except ImportError as e:
            missing = "pytesseract" if "pytesseract" in str(e) else "PIL"
            errors.append(f"Missing dependency: {missing}")
            text = ""
        except Exception as e:
            error_msg = str(e)
            if "tesseract" in error_msg.lower():
                errors.append(
                    "Tesseract OCR not installed. Install with: "
                    "sudo apt install tesseract-ocr tesseract-ocr-spa"
                )
            else:
                errors.append(f"OCR error: {error_msg}")
            text = ""

        return ExtractionResult(
            text=text,
            page_count=1,
            metadata=metadata,
            errors=errors,
            format="image",
        )

    def _preprocess_image(self, image):
        """
        Preprocess image for better OCR results.

        - Convert to grayscale
        - Apply thresholding
        - Remove noise
        """
        from PIL import Image, ImageFilter, ImageOps

        # Convert to grayscale
        if image.mode != "L":
            image = image.convert("L")

        # Apply slight sharpening
        image = image.filter(ImageFilter.SHARPEN)

        # Increase contrast using autocontrast
        image = ImageOps.autocontrast(image)

        # Optional: Apply adaptive thresholding for scanned documents
        # This helps with uneven lighting
        # image = image.point(lambda x: 0 if x < 128 else 255, '1')

        return image

    def _clean_ocr_text(self, text: str) -> str:
        """Clean up OCR output text."""
        import re

        # Remove excessive whitespace
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)

        return text.strip()
