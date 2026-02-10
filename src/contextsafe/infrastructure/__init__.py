# ContextSafe - Infrastructure Layer
# ============================================
"""
Infrastructure layer containing adapter implementations.

Modules:
- persistence: Database adapters (SQLite)
- nlp: NER adapters (spaCy, regex, composite)
- llm: LLM adapter (llama-cpp-python)
- ocr: OCR adapter (Tesseract)
- document_processing: Document parser adapters
- events: Event publisher adapters
"""

from contextsafe.infrastructure.document_processing import (
    CompositeDocumentExtractor,
    DocxExtractor,
    PdfExtractor,
    TxtExtractor,
)
from contextsafe.infrastructure.events import (
    EventDispatcher,
    InMemoryEventPublisher,
)
from contextsafe.infrastructure.llm import (
    AliasGenerator,
    LlamaCppNerAdapter,
    LLMConfig,
)
from contextsafe.infrastructure.nlp import (
    CompositeNerAdapter,
    RegexNerAdapter,
    SpacyNerAdapter,
)
from contextsafe.infrastructure.ocr import TesseractOcrAdapter
from contextsafe.infrastructure.persistence import (
    Database,
    SQLiteDocumentRepository,
    SQLiteGlossaryRepository,
    SQLiteProjectRepository,
)


__all__ = [
    # Persistence
    "Database",
    "SQLiteDocumentRepository",
    "SQLiteProjectRepository",
    "SQLiteGlossaryRepository",
    # NLP
    "SpacyNerAdapter",
    "RegexNerAdapter",
    "CompositeNerAdapter",
    # LLM
    "LlamaCppNerAdapter",
    "LLMConfig",
    "AliasGenerator",
    # OCR
    "TesseractOcrAdapter",
    # Document processing
    "PdfExtractor",
    "DocxExtractor",
    "TxtExtractor",
    "CompositeDocumentExtractor",
    # Events
    "InMemoryEventPublisher",
    "EventDispatcher",
]
