"""
Document extractors for ContextSafe.

Traceability:
- IMPLEMENTATION_PLAN.md Phase 4
"""

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
from contextsafe.infrastructure.document_processing.extractors.factory import (
    ExtractorFactory,
    get_extractor,
)

__all__ = [
    "DocumentExtractor",
    "ExtractionResult",
    "PdfExtractor",
    "DocxExtractor",
    "TxtExtractor",
    "ImageExtractor",
    "ExtractorFactory",
    "get_extractor",
]
