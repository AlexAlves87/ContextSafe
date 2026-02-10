"""
Application ports for ContextSafe.

Ports define abstract interfaces implemented by infrastructure adapters.
Following hexagonal architecture (Ports & Adapters).
"""
from contextsafe.application.ports.anonymization_service import (
    AnonymizationResult,
    AnonymizationService,
    EntityReplacement,
)
from contextsafe.application.ports.document_repository import DocumentRepository
from contextsafe.application.ports.event_publisher import EventPublisher
from contextsafe.application.ports.glossary_repository import GlossaryRepository
from contextsafe.application.ports.ner_service import NerDetection, NerService, ProgressCallback
from contextsafe.application.ports.project_repository import ProjectRepository
from contextsafe.application.ports.text_extractor import ExtractionResult, TextExtractor
from contextsafe.application.compute_mode import ComputeMode
from contextsafe.application.ports.text_preprocessor import (
    DetectionPreprocessor,
    IngestPreprocessor,
    OffsetMapping,
)

__all__ = [
    # Repositories
    "DocumentRepository",
    "ProjectRepository",
    "GlossaryRepository",
    # Services
    "NerService",
    "NerDetection",
    "ProgressCallback",
    "TextExtractor",
    "ExtractionResult",
    "EventPublisher",
    "AnonymizationService",
    "AnonymizationResult",
    "EntityReplacement",
    # Preprocessors
    "IngestPreprocessor",
    "DetectionPreprocessor",
    "OffsetMapping",
    # Compute
    "ComputeMode",
]
