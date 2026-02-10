"""
IngestDocument use case.

Handles document upload and text extraction.

Traceability:
- Bounded Context: BC-001 (DocumentProcessing)
- Function: F-001, F-002 (multi-format ingestion)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from contextsafe.application.ports import (
    DocumentRepository,
    EventPublisher,
    IngestPreprocessor,
    TextExtractor,
)
from contextsafe.domain.document_processing.aggregates.document_aggregate import (
    DocumentAggregate,
)
from contextsafe.domain.shared.errors import DocumentError, DomainError
from contextsafe.domain.shared.events import DocumentIngested
from contextsafe.domain.shared.types import Err, Ok, Result
from contextsafe.domain.shared.value_objects import ProjectId


@dataclass(frozen=True, slots=True)
class IngestDocumentRequest:
    """Input for document ingestion."""

    project_id: str
    content: bytes
    filename: str
    metadata: Optional[dict[str, Any]] = None


@dataclass(frozen=True, slots=True)
class IngestDocumentResponse:
    """Output from document ingestion."""

    document_id: str
    project_id: str
    filename: str
    text_length: int
    format_detected: str
    state: str


class IngestDocument:
    """
    Use case for ingesting a document.

    Steps:
    1. Validate input
    2. Create document aggregate
    3. Extract text from document
    4. Update aggregate with extracted text
    5. Save to repository
    6. Publish DocumentIngested event
    """

    def __init__(
        self,
        document_repository: DocumentRepository,
        text_extractor: TextExtractor,
        event_publisher: EventPublisher,
        ingest_preprocessor: Optional[IngestPreprocessor] = None,
    ) -> None:
        self._document_repo = document_repository
        self._text_extractor = text_extractor
        self._event_publisher = event_publisher
        self._preprocessor = ingest_preprocessor

    async def execute(
        self, request: IngestDocumentRequest
    ) -> Result[IngestDocumentResponse, DomainError]:
        """
        Execute the document ingestion use case.

        Args:
            request: The ingestion request

        Returns:
            Ok[IngestDocumentResponse] on success, Err[DomainError] on failure
        """
        # 1. Validate project ID
        project_id_result = ProjectId.create(request.project_id)
        if project_id_result.is_err():
            return Err(DocumentError(f"Invalid project ID: {request.project_id}"))

        project_id = project_id_result.unwrap()

        # 2. Create document aggregate
        aggregate_result = DocumentAggregate.create(
            project_id=project_id,
            content=request.content,
            filename=request.filename,
            metadata=request.metadata,
        )

        if aggregate_result.is_err():
            return Err(aggregate_result.unwrap_err())

        aggregate = aggregate_result.unwrap()

        # 3. Extract text
        try:
            extraction = await self._text_extractor.extract(
                content=request.content,
                filename=request.filename,
                ocr_fallback=True,
            )
        except Exception as e:
            aggregate.fail(f"Text extraction failed: {e}")
            await self._document_repo.save(aggregate)
            return Err(DocumentError(f"Text extraction failed: {e}"))

        # 4. Phase 1: Pre-normalization (permanent, stored in DB)
        extracted_text = extraction.text
        if self._preprocessor is not None:
            extracted_text = self._preprocessor.preprocess(extracted_text)

        # 5. Update aggregate with normalized text
        result = aggregate.mark_ingested(extracted_text)
        if result.is_err():
            return Err(result.unwrap_err())

        # 6. Save to repository
        save_result = await self._document_repo.save(aggregate)
        if save_result.is_err():
            return Err(save_result.unwrap_err())

        saved_aggregate = save_result.unwrap()

        # 7. Publish event
        event = DocumentIngested.create(
            document_id=str(saved_aggregate.id),
            project_id=str(project_id),
            filename=request.filename,
            text_length=len(extracted_text),
            format_detected=extraction.format_detected,
        )
        await self._event_publisher.publish(event)

        # 8. Return response
        return Ok(
            IngestDocumentResponse(
                document_id=str(saved_aggregate.id),
                project_id=str(project_id),
                filename=request.filename,
                text_length=len(extracted_text),
                format_detected=extraction.format_detected,
                state=str(saved_aggregate.state),
            )
        )
