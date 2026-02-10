"""
BatchJob entity.

Represents a batch processing job for multiple documents.

Traceability:
- Standard: consolidated_standards.yaml#factories.entities.BatchJob
- Bounded Context: BC-001 (DocumentProcessing)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional
from uuid import uuid4

from contextsafe.domain.shared.errors import BatchError
from contextsafe.domain.shared.types import Entity, Err, Ok, Result
from contextsafe.domain.shared.value_objects import (
    AnonymizationLevel,
    DocumentId,
    EntityId,
    INTERMEDIATE,
    ProjectId,
)


class BatchJobStatus(str, Enum):
    """Status of a batch job."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(kw_only=True)
class BatchJob(Entity[EntityId]):
    """
    A batch processing job for multiple documents.

    Tracks:
    - Documents to process
    - Progress (processed/total)
    - Status and errors
    - Processing options
    """

    id: EntityId = field(kw_only=False)
    project_id: ProjectId = field(kw_only=False)
    document_ids: List[DocumentId] = field(kw_only=False)
    status: BatchJobStatus = BatchJobStatus.PENDING
    anonymization_level: AnonymizationLevel = field(default_factory=lambda: INTERMEDIATE)
    total_documents: int = 0
    processed_documents: int = 0
    failed_documents: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = field(default=1)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        project_id: ProjectId,
        document_ids: List[DocumentId],
        anonymization_level: Optional[AnonymizationLevel] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Result[BatchJob, BatchError]:
        """
        Create a BatchJob.

        Args:
            project_id: The project for this batch
            document_ids: List of documents to process
            anonymization_level: Level of anonymization (default: INTERMEDIATE)
            metadata: Additional job metadata

        Returns:
            Ok[BatchJob] if valid, Err[BatchError] if invalid
        """
        if not document_ids:
            return Err(BatchError("Batch job must have at least one document"))

        # Generate job ID
        job_id_result = EntityId.create(str(uuid4()))
        if job_id_result.is_err():
            return Err(BatchError("Failed to generate job ID"))

        job_id = job_id_result.unwrap()

        return Ok(
            cls(
                id=job_id,
                project_id=project_id,
                document_ids=list(document_ids),
                status=BatchJobStatus.PENDING,
                anonymization_level=anonymization_level or INTERMEDIATE,
                total_documents=len(document_ids),
                processed_documents=0,
                failed_documents=0,
                metadata=metadata or {},
            )
        )

    def start(self) -> None:
        """Mark the job as started."""
        object.__setattr__(self, "status", BatchJobStatus.RUNNING)
        object.__setattr__(self, "started_at", datetime.utcnow())
        self._touch()

    def pause(self) -> None:
        """Pause the job."""
        if self.status == BatchJobStatus.RUNNING:
            object.__setattr__(self, "status", BatchJobStatus.PAUSED)
            self._touch()

    def resume(self) -> None:
        """Resume a paused job."""
        if self.status == BatchJobStatus.PAUSED:
            object.__setattr__(self, "status", BatchJobStatus.RUNNING)
            self._touch()

    def cancel(self) -> None:
        """Cancel the job."""
        if self.status in {BatchJobStatus.PENDING, BatchJobStatus.RUNNING, BatchJobStatus.PAUSED}:
            object.__setattr__(self, "status", BatchJobStatus.CANCELLED)
            object.__setattr__(self, "completed_at", datetime.utcnow())
            self._touch()

    def record_success(self) -> None:
        """Record a successfully processed document."""
        object.__setattr__(self, "processed_documents", self.processed_documents + 1)
        self._check_completion()
        self._touch()

    def record_failure(self, error: str) -> None:
        """Record a failed document."""
        object.__setattr__(self, "failed_documents", self.failed_documents + 1)
        object.__setattr__(self, "processed_documents", self.processed_documents + 1)
        object.__setattr__(self, "error_message", error)
        self._check_completion()
        self._touch()

    def fail(self, error: str) -> None:
        """Mark the entire job as failed."""
        object.__setattr__(self, "status", BatchJobStatus.FAILED)
        object.__setattr__(self, "error_message", error)
        object.__setattr__(self, "completed_at", datetime.utcnow())
        self._touch()

    def _check_completion(self) -> None:
        """Check if all documents have been processed."""
        if self.processed_documents >= self.total_documents:
            if self.failed_documents == self.total_documents:
                object.__setattr__(self, "status", BatchJobStatus.FAILED)
            else:
                object.__setattr__(self, "status", BatchJobStatus.COMPLETED)
            object.__setattr__(self, "completed_at", datetime.utcnow())

    @property
    def progress_percent(self) -> int:
        """Get progress as percentage."""
        if self.total_documents == 0:
            return 0
        return int((self.processed_documents / self.total_documents) * 100)

    @property
    def is_active(self) -> bool:
        """Check if job is still active."""
        return self.status in {BatchJobStatus.PENDING, BatchJobStatus.RUNNING, BatchJobStatus.PAUSED}

    @property
    def is_completed(self) -> bool:
        """Check if job is completed (success or failure)."""
        return self.status in {BatchJobStatus.COMPLETED, BatchJobStatus.FAILED, BatchJobStatus.CANCELLED}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "document_ids": [str(d) for d in self.document_ids],
            "status": self.status.value,
            "anonymization_level": str(self.anonymization_level),
            "total_documents": self.total_documents,
            "processed_documents": self.processed_documents,
            "failed_documents": self.failed_documents,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BatchJob:
        """Reconstruct from dictionary."""
        job_id = EntityId.create(data["id"]).unwrap()
        project_id = ProjectId.create(data["project_id"]).unwrap()
        document_ids = [DocumentId.create(d).unwrap() for d in data["document_ids"]]
        status = BatchJobStatus(data["status"])
        level = AnonymizationLevel.from_string(data["anonymization_level"]).unwrap()

        return cls(
            id=job_id,
            project_id=project_id,
            document_ids=document_ids,
            status=status,
            anonymization_level=level,
            total_documents=data["total_documents"],
            processed_documents=data["processed_documents"],
            failed_documents=data["failed_documents"],
            error_message=data.get("error_message"),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            version=data.get("version", 1),
            metadata=data.get("metadata", {}),
        )
