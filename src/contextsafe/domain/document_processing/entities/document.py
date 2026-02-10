"""
Document entity.

Represents a document being processed for anonymization.

Traceability:
- Standard: consolidated_standards.yaml#factories.entities.Document
- Invariants: INV-001, INV-003, INV-004
- Bounded Context: BC-001 (DocumentProcessing)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from contextsafe.domain.shared.errors import (
    DocumentError,
    DocumentSizeError,
    InvalidExtensionError,
)
from contextsafe.domain.shared.types import Entity, Err, Ok, Result
from contextsafe.domain.shared.value_objects import (
    DocumentId,
    DocumentState,
    PENDING,
    ProjectId,
)


# Maximum document size (10MB)
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024

# Valid extensions
VALID_EXTENSIONS = frozenset({".txt", ".pdf", ".png", ".jpg", ".jpeg", ".docx"})


@dataclass(kw_only=True)
class Document(Entity[DocumentId]):
    """
    Document entity for anonymization processing.

    A document has:
    - Content (bytes or path to file)
    - Filename with valid extension
    - Processing state
    - Extracted text (after ingestion)
    """

    id: DocumentId = field(kw_only=False)
    project_id: ProjectId = field(kw_only=False)
    filename: str = field(kw_only=False)
    content: Optional[bytes] = None
    content_path: Optional[str] = None
    extracted_text: Optional[str] = None
    state: DocumentState = field(default_factory=lambda: PENDING)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = field(default=1)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        project_id: ProjectId,
        content: bytes,
        filename: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Result[Document, DocumentError]:
        """
        Create a new Document.

        Args:
            project_id: The project this document belongs to
            content: The document content as bytes
            filename: The original filename

        Returns:
            Ok[Document] if valid, Err[DocumentError] if invalid
        """
        # Validate content size (INV-004)
        if len(content) > MAX_DOCUMENT_SIZE:
            return Err(DocumentSizeError.create(len(content), MAX_DOCUMENT_SIZE))

        if len(content) == 0:
            return Err(DocumentError("Document content cannot be empty"))

        # Validate extension (INV-003)
        ext = Path(filename).suffix.lower()
        if ext not in VALID_EXTENSIONS:
            return Err(InvalidExtensionError.create(ext, list(VALID_EXTENSIONS)))

        # Create document ID
        doc_id_result = DocumentId.create(str(uuid4()))
        if doc_id_result.is_err():
            return Err(DocumentError("Failed to generate document ID"))

        doc_id = doc_id_result.unwrap()

        return Ok(
            cls(
                id=doc_id,
                project_id=project_id,
                filename=filename,
                content=content,
                content_path=None,
                extracted_text=None,
                state=PENDING,
                metadata=metadata or {},
            )
        )

    @classmethod
    def create_from_path(
        cls,
        project_id: ProjectId,
        content_path: str,
        filename: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Result[Document, DocumentError]:
        """
        Create a Document from a file path (lazy loading).

        Args:
            project_id: The project this document belongs to
            content_path: Path to the document file
            filename: The original filename

        Returns:
            Ok[Document] if valid, Err[DocumentError] if invalid
        """
        # Validate extension
        ext = Path(filename).suffix.lower()
        if ext not in VALID_EXTENSIONS:
            return Err(InvalidExtensionError.create(ext, list(VALID_EXTENSIONS)))

        # Create document ID
        doc_id_result = DocumentId.create(str(uuid4()))
        if doc_id_result.is_err():
            return Err(DocumentError("Failed to generate document ID"))

        doc_id = doc_id_result.unwrap()

        return Ok(
            cls(
                id=doc_id,
                project_id=project_id,
                filename=filename,
                content=None,
                content_path=content_path,
                extracted_text=None,
                state=PENDING,
                metadata=metadata or {},
            )
        )

    @property
    def extension(self) -> str:
        """Get the file extension."""
        return Path(self.filename).suffix.lower()

    @property
    def is_image(self) -> bool:
        """Check if this is an image file (requires OCR)."""
        return self.extension in {".png", ".jpg", ".jpeg"}

    @property
    def is_pdf(self) -> bool:
        """Check if this is a PDF file."""
        return self.extension == ".pdf"

    @property
    def has_content(self) -> bool:
        """Check if document has content (direct or path)."""
        return self.content is not None or self.content_path is not None

    @property
    def has_extracted_text(self) -> bool:
        """Check if text has been extracted."""
        return self.extracted_text is not None

    def set_extracted_text(self, text: str) -> None:
        """Set the extracted text content."""
        object.__setattr__(self, "extracted_text", text)
        self._touch()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "filename": self.filename,
            "content_path": self.content_path,
            "extracted_text": self.extracted_text,
            "state": str(self.state),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Document:
        """Reconstruct from dictionary."""
        doc_id = DocumentId.create(data["id"]).unwrap()
        project_id = ProjectId.create(data["project_id"]).unwrap()
        state = DocumentState.from_string(data["state"]).unwrap()

        return cls(
            id=doc_id,
            project_id=project_id,
            filename=data["filename"],
            content=None,
            content_path=data.get("content_path"),
            extracted_text=data.get("extracted_text"),
            state=state,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            version=data.get("version", 1),
            metadata=data.get("metadata", {}),
        )
