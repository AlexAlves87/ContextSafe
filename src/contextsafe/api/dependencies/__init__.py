"""
Dependency injection for ContextSafe API.
"""

from contextsafe.api.dependencies.container import (
    Container,
    get_anonymization_service,
    get_container,
    get_database_session,
    get_document_repository,
    get_event_publisher,
    get_glossary_repository,
    get_ner_service,
    get_project_repository,
    get_text_extractor,
)


__all__ = [
    "Container",
    "get_anonymization_service",
    "get_container",
    "get_database_session",
    "get_document_repository",
    "get_event_publisher",
    "get_glossary_repository",
    "get_ner_service",
    "get_project_repository",
    "get_text_extractor",
]
