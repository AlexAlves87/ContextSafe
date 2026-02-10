"""
Document processing infrastructure for ContextSafe.

Provides text extraction from various document formats.
"""

from contextsafe.infrastructure.document_processing.composite_extractor import (
    CompositeDocumentExtractor,
)
from contextsafe.infrastructure.document_processing.docx_extractor import DocxExtractor
from contextsafe.infrastructure.document_processing.pdf_extractor import PdfExtractor
from contextsafe.infrastructure.document_processing.txt_extractor import TxtExtractor


__all__ = [
    "CompositeDocumentExtractor",
    "DocxExtractor",
    "PdfExtractor",
    "TxtExtractor",
]
