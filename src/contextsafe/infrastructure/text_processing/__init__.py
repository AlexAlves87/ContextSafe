"""
Text processing infrastructure.

Implements text preprocessing for NER detection.

Traceability:
- Design: docs/plans/2026-02-01-text-preprocessing-design.md
"""
from contextsafe.infrastructure.text_processing.detection_preprocessor import (
    DefaultDetectionPreprocessor,
)
from contextsafe.infrastructure.text_processing.ingest_preprocessor import (
    DefaultIngestPreprocessor,
)
from contextsafe.infrastructure.text_processing.offset_tracker import OffsetTracker

__all__ = [
    "DefaultIngestPreprocessor",
    "DefaultDetectionPreprocessor",
    "OffsetTracker",
]
