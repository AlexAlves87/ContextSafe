"""
NER service registry.

Thin facade that delegates to the DI container.
Extracted from routes/documents.py to break the documents<->system import cycle.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def reset_ner_service() -> None:
    """Reset NER service to reinitialize on next call (e.g., after compute mode change)."""
    from contextsafe.api.dependencies import get_container
    get_container().reset_ner_service()
    logger.info("[NER] Service reset - will reinitialize on next call")


def get_ner_service():
    """Get the NER service from the container."""
    from contextsafe.api.dependencies import get_container
    return get_container().ner_service


def get_anonymization_service():
    """Get the anonymization service from the container."""
    from contextsafe.api.dependencies import get_container
    return get_container().anonymization_service
