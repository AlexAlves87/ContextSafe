"""
OCR infrastructure for ContextSafe.

Provides Tesseract-based OCR for image text extraction.
"""

from contextsafe.infrastructure.ocr.tesseract_adapter import TesseractOcrAdapter


__all__ = [
    "TesseractOcrAdapter",
]
