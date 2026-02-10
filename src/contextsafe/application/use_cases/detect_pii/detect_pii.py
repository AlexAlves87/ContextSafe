"""
DetectPii use case.

Handles PII detection in documents.

Traceability:
- Bounded Context: BC-002 (EntityDetection)
- Function: F-004, F-005 (NER detection, categorization)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from contextsafe.application.ports import (
    DetectionPreprocessor,
    DocumentRepository,
    EventPublisher,
    NerService,
    OffsetMapping,
)
from contextsafe.domain.entity_detection.entities.detection_result import (
    DetectionResult,
)
from contextsafe.domain.shared.errors import DetectionError, DocumentError, DomainError, NotFoundError
from contextsafe.domain.shared.events import PiiDetected
from contextsafe.domain.shared.types import Err, Ok, Result
from contextsafe.domain.shared.value_objects import DocumentId, PiiCategory


@dataclass(frozen=True, slots=True)
class DetectPiiRequest:
    """Input for PII detection."""

    document_id: str
    categories: Optional[List[str]] = None
    min_confidence: float = 0.5


@dataclass(frozen=True, slots=True)
class DetectedEntity:
    """A detected PII entity."""

    entity_id: str
    category: str
    value: str
    start: int
    end: int
    confidence: float
    needs_review: bool


@dataclass(frozen=True, slots=True)
class DetectPiiResponse:
    """Output from PII detection."""

    document_id: str
    total_entities: int
    entities_by_category: Dict[str, int]
    low_confidence_count: int
    entities: List[DetectedEntity]


class DetectPii:
    """
    Use case for detecting PII in a document.

    Steps:
    1. Load document from repository
    2. Verify document is in correct state
    3. Run NER detection on extracted text
    4. Create DetectionResult entities
    5. Update document state
    6. Publish PiiDetected event
    """

    def __init__(
        self,
        document_repository: DocumentRepository,
        ner_service: NerService,
        event_publisher: EventPublisher,
        detection_preprocessor: Optional[DetectionPreprocessor] = None,
    ) -> None:
        self._document_repo = document_repository
        self._ner_service = ner_service
        self._event_publisher = event_publisher
        self._preprocessor = detection_preprocessor

    async def execute(
        self, request: DetectPiiRequest
    ) -> Result[DetectPiiResponse, DomainError]:
        """
        Execute the PII detection use case.

        Args:
            request: The detection request

        Returns:
            Ok[DetectPiiResponse] on success, Err[DomainError] on failure
        """
        # 1. Validate document ID
        doc_id_result = DocumentId.create(request.document_id)
        if doc_id_result.is_err():
            return Err(DocumentError(f"Invalid document ID: {request.document_id}"))

        doc_id = doc_id_result.unwrap()

        # 2. Load document
        aggregate = await self._document_repo.find_by_id(doc_id)
        if aggregate is None:
            return Err(NotFoundError.create("Document", request.document_id))

        # 3. Verify state and get text
        if aggregate.extracted_text is None:
            return Err(DocumentError("Document has no extracted text"))

        # 4. Start detection
        result = aggregate.start_detection()
        if result.is_err():
            return Err(result.unwrap_err())

        # 5. Parse categories filter
        categories_filter: Optional[List[PiiCategory]] = None
        if request.categories:
            categories_filter = []
            for cat_str in request.categories:
                cat_result = PiiCategory.from_string(cat_str)
                if cat_result.is_ok():
                    categories_filter.append(cat_result.unwrap())

        # 6. Phase 2: Pre-normalization for NER (temporary, with offset tracking)
        source_text = aggregate.extracted_text
        if self._preprocessor is not None:
            mapping = self._preprocessor.preprocess(source_text)
            ner_text = mapping.normalized_text
        else:
            mapping = OffsetMapping.identity(source_text)
            ner_text = source_text

        # 7. Run NER detection on normalized text
        try:
            detections = await self._ner_service.detect_entities(
                text=ner_text,
                categories=categories_filter,
                min_confidence=request.min_confidence,
            )
        except Exception as e:
            aggregate.fail(f"NER detection failed: {e}")
            await self._document_repo.save(aggregate)
            return Err(DetectionError(f"NER detection failed: {e}"))

        # 8. Create DetectionResult entities with original spans
        detection_results: List[DetectionResult] = []
        for detection in detections:
            # Translate span from normalized text back to original
            orig_start, orig_end = mapping.to_original_span(
                detection.span.start, detection.span.end
            )
            # Use value from ORIGINAL text (for auditability)
            original_value = source_text[orig_start:orig_end]

            det_result = DetectionResult.create(
                document_id=doc_id,
                category=detection.category,
                value=original_value,
                span=(orig_start, orig_end),
                confidence=detection.confidence,
            )
            if det_result.is_ok():
                detection_results.append(det_result.unwrap())

        # 9. Complete detection
        result = aggregate.complete_detection(len(detection_results))
        if result.is_err():
            return Err(result.unwrap_err())

        # 10. Save aggregate
        await self._document_repo.save(aggregate)

        # 11. Build response
        entities_by_category: Dict[str, int] = {}
        low_confidence_count = 0
        entities: List[DetectedEntity] = []

        for det in detection_results:
            cat_str = str(det.category)
            entities_by_category[cat_str] = entities_by_category.get(cat_str, 0) + 1

            if det.needs_review:
                low_confidence_count += 1

            entities.append(
                DetectedEntity(
                    entity_id=str(det.id),
                    category=cat_str,
                    value=det.original_value,
                    start=det.span.start,
                    end=det.span.end,
                    confidence=det.confidence.value,
                    needs_review=det.needs_review,
                )
            )

        # 12. Publish event
        event = PiiDetected.create(
            document_id=str(doc_id),
            project_id=str(aggregate.document.project_id),
            total_entities=len(detection_results),
            entities_by_category=entities_by_category,
            low_confidence_count=low_confidence_count,
        )
        await self._event_publisher.publish(event)

        return Ok(
            DetectPiiResponse(
                document_id=str(doc_id),
                total_entities=len(detection_results),
                entities_by_category=entities_by_category,
                low_confidence_count=low_confidence_count,
                entities=entities,
            )
        )
