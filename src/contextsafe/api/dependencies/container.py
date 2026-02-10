"""
Dependency injection container.

Provides FastAPI Depends() functions for injecting services.

Traceability:
- Contract: CNT-T4-CONTAINER-001
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from contextsafe.application.ports import (
    AnonymizationService,
    DetectionPreprocessor,
    DocumentRepository,
    EventPublisher,
    GlossaryRepository,
    IngestPreprocessor,
    NerService,
    ProjectRepository,
    TextExtractor,
)
from contextsafe.infrastructure.persistence import Database


class Container:
    """
    Dependency injection container.

    Holds singleton instances and provides factory functions.
    """

    _instance: Container | None = None

    def __init__(self) -> None:
        """Initialize the container."""
        self._database: Database | None = None
        self._ner_service: NerService | None = None
        self._anonymization_service: AnonymizationService | None = None
        self._event_publisher: EventPublisher | None = None
        self._text_extractor: TextExtractor | None = None
        self._ingest_preprocessor: IngestPreprocessor | None = None
        self._detection_preprocessor: DetectionPreprocessor | None = None

    @classmethod
    def instance(cls) -> Container:
        """Get the singleton container instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_database(self, database: Database) -> None:
        """Set the database instance."""
        self._database = database

    def set_ner_service(self, service: NerService) -> None:
        """Set the NER service."""
        self._ner_service = service

    def set_event_publisher(self, publisher: EventPublisher) -> None:
        """Set the event publisher."""
        self._event_publisher = publisher

    def set_text_extractor(self, extractor: TextExtractor) -> None:
        """Set the text extractor."""
        self._text_extractor = extractor

    def set_ingest_preprocessor(self, preprocessor: IngestPreprocessor) -> None:
        """Set the ingest preprocessor (Phase 1)."""
        self._ingest_preprocessor = preprocessor

    def set_detection_preprocessor(self, preprocessor: DetectionPreprocessor) -> None:
        """Set the detection preprocessor (Phase 2)."""
        self._detection_preprocessor = preprocessor

    @property
    def database(self) -> Database:
        """Get the database instance."""
        if self._database is None:
            raise RuntimeError("Database not configured")
        return self._database

    def reset_ner_service(self) -> None:
        """Reset NER service (e.g., after compute mode change). Reinitializes on next access."""
        self._ner_service = None

    @property
    def ner_service(self) -> NerService:
        """Get the NER service (lazy-initialized with compute mode detection)."""
        if self._ner_service is None:
            self._ner_service = self._create_ner_service()
        return self._ner_service

    @staticmethod
    def _create_ner_service() -> NerService:
        """Create comprehensive NER service with compute mode detection."""
        from pathlib import Path

        from contextsafe.api.services.compute_state import get_effective_compute_mode
        from contextsafe.application.compute_mode import ComputeMode
        from contextsafe.infrastructure.nlp import (
            CompositeNerAdapter,
            RegexNerAdapter,
            RobertaNerAdapter,
            SpacyNerAdapter,
        )

        compute_mode = get_effective_compute_mode()
        device = 0 if compute_mode == ComputeMode.GPU else -1
        device_name = "GPU" if device >= 0 else "CPU"

        # Priority: local trained model v2 > HuggingFace fallback
        project_root = Path(__file__).parent.parent.parent.parent
        local_model_path = project_root / "ml" / "models" / "legal_ner_v2"

        if local_model_path.exists():
            model_name = str(local_model_path)
            model_display = "legal_ner_v2 (local)"
            use_local_only = False
        else:
            model_name = "MMG/xlm-roberta-large-ner-spanish"
            model_display = "XLM-RoBERTa-large (HuggingFace)"
            use_local_only = True

        roberta_ner = RobertaNerAdapter(
            model_name=model_name,
            min_score=0.85,
            device=device,
            local_files_only=use_local_only,
        )

        spacy_ner = SpacyNerAdapter(
            model_name="es_core_news_lg",
            confidence_default=0.85,
        )

        regex_ner = RegexNerAdapter()

        ner_service = CompositeNerAdapter(
            adapters=[roberta_ner, spacy_ner, regex_ner],
            spacy_adapter=spacy_ner,
            tie_threshold=0.3,
        )
        print(f"[NER] Using {model_display} + SpaCy + Regex on {device_name}")
        print("[NER] Intelligent merge enabled: anchors + weighted voting + risk tiebreaker")
        return ner_service

    def set_anonymization_service(self, service: AnonymizationService) -> None:
        """Set the anonymization service."""
        self._anonymization_service = service

    @property
    def anonymization_service(self) -> AnonymizationService:
        """Get the anonymization service (lazy-initialized)."""
        if self._anonymization_service is None:
            from contextsafe.infrastructure.nlp import InMemoryAnonymizationAdapter
            self._anonymization_service = InMemoryAnonymizationAdapter()
        return self._anonymization_service

    @property
    def event_publisher(self) -> EventPublisher:
        """Get the event publisher."""
        if self._event_publisher is None:
            raise RuntimeError("Event publisher not configured")
        return self._event_publisher

    @property
    def text_extractor(self) -> TextExtractor:
        """Get the text extractor."""
        if self._text_extractor is None:
            raise RuntimeError("Text extractor not configured")
        return self._text_extractor

    @property
    def ingest_preprocessor(self) -> IngestPreprocessor:
        """Get the ingest preprocessor (Phase 1)."""
        if self._ingest_preprocessor is None:
            # Create default if not configured
            from contextsafe.infrastructure.text_processing import (
                DefaultIngestPreprocessor,
            )
            self._ingest_preprocessor = DefaultIngestPreprocessor()
        return self._ingest_preprocessor

    @property
    def detection_preprocessor(self) -> DetectionPreprocessor:
        """Get the detection preprocessor (Phase 2)."""
        if self._detection_preprocessor is None:
            # Create default if not configured
            from contextsafe.infrastructure.text_processing import (
                DefaultDetectionPreprocessor,
            )
            self._detection_preprocessor = DefaultDetectionPreprocessor()
        return self._detection_preprocessor


@lru_cache
def get_container() -> Container:
    """Get the container instance (cached)."""
    return Container.instance()


async def get_database_session() -> AsyncIterator[AsyncSession]:
    """
    Get a database session as async generator.

    Yields:
        AsyncSession: Database session
    """
    container = get_container()
    async with container.database.session() as session:
        yield session


async def get_document_repository(
    session: AsyncSession,
) -> DocumentRepository:
    """
    Get document repository instance.

    Args:
        session: Database session (injected)

    Returns:
        DocumentRepository implementation
    """
    from contextsafe.infrastructure.persistence import SQLiteDocumentRepository

    return SQLiteDocumentRepository(session)


async def get_project_repository(
    session: AsyncSession,
) -> ProjectRepository:
    """
    Get project repository instance.

    Args:
        session: Database session (injected)

    Returns:
        ProjectRepository implementation
    """
    from contextsafe.infrastructure.persistence import SQLiteProjectRepository

    return SQLiteProjectRepository(session)


async def get_glossary_repository(
    session: AsyncSession,
) -> GlossaryRepository:
    """
    Get glossary repository instance.

    Args:
        session: Database session (injected)

    Returns:
        GlossaryRepository implementation
    """
    from contextsafe.infrastructure.persistence import SQLiteGlossaryRepository

    return SQLiteGlossaryRepository(session)


def get_ner_service() -> NerService:
    """Get NER service instance."""
    return get_container().ner_service


def get_anonymization_service() -> AnonymizationService:
    """Get anonymization service instance."""
    return get_container().anonymization_service


def get_event_publisher() -> EventPublisher:
    """Get event publisher instance."""
    return get_container().event_publisher


def get_text_extractor() -> TextExtractor:
    """Get text extractor instance."""
    return get_container().text_extractor


def get_ingest_preprocessor() -> IngestPreprocessor:
    """Get ingest preprocessor instance (Phase 1)."""
    return get_container().ingest_preprocessor


def get_detection_preprocessor() -> DetectionPreprocessor:
    """Get detection preprocessor instance (Phase 2)."""
    return get_container().detection_preprocessor
