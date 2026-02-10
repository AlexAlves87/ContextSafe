"""
SQLAlchemy models for SQLite persistence.

Maps domain aggregates to database tables.

Traceability:
- Contract: CNT-T3-PERSISTENCE-MODELS-001
- Bounded Contexts: BC-001 (DocumentProcessing), BC-003 (Anonymization), BC-004 (ProjectManagement)
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""

    pass


class DocumentModel(Base):
    """
    SQLAlchemy model for Document aggregate.

    Maps DocumentAggregate to the 'documents' table.
    """

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    state: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    anonymized_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    anonymization_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    detection_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    metadata_json: Mapped[Optional[str]] = mapped_column(
        "metadata", JSON, nullable=True, default=None
    )

    @classmethod
    def from_aggregate(cls, aggregate: Any) -> DocumentModel:
        """
        Create a model instance from a DocumentAggregate.

        Args:
            aggregate: DocumentAggregate instance
        """
        data = aggregate.to_dict()
        doc_data = data.get("document", {})
        return cls(
            id=data["id"],
            project_id=doc_data.get("project_id", ""),
            filename=doc_data.get("filename", ""),
            content_path=doc_data.get("content_path"),
            extracted_text=data.get("extracted_text"),
            state=data["state"],
            anonymized_text=data.get("anonymized_text"),
            anonymization_level=data.get("anonymization_level"),
            detection_count=data.get("detection_count", 0),
            error_message=data.get("error_message"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            version=data.get("version", 1),
            metadata_json=doc_data.get("metadata"),
        )

    def update_from_aggregate(self, aggregate: Any) -> None:
        """
        Update model fields from aggregate.

        Args:
            aggregate: DocumentAggregate instance
        """
        data = aggregate.to_dict()
        doc_data = data.get("document", {})
        self.project_id = doc_data.get("project_id", self.project_id)
        self.filename = doc_data.get("filename", self.filename)
        self.content_path = doc_data.get("content_path")
        self.extracted_text = data.get("extracted_text")
        self.state = data["state"]
        self.anonymized_text = data.get("anonymized_text")
        self.anonymization_level = data.get("anonymization_level")
        self.detection_count = data.get("detection_count", 0)
        self.error_message = data.get("error_message")
        self.updated_at = datetime.fromisoformat(data["updated_at"])
        self.version = data.get("version", 1)
        self.metadata_json = doc_data.get("metadata")

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary for aggregate reconstruction."""
        return {
            "id": self.id,
            "document": {
                "id": self.id,
                "project_id": self.project_id,
                "filename": self.filename,
                "content_path": self.content_path,
                "extracted_text": self.extracted_text,
                "state": self.state,
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat(),
                "version": self.version,
                "metadata": self.metadata_json or {},
            },
            "state": self.state,
            "extracted_text": self.extracted_text,
            "anonymized_text": self.anonymized_text,
            "anonymization_level": self.anonymization_level,
            "detection_count": self.detection_count,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }


class ProjectModel(Base):
    """
    SQLAlchemy model for Project aggregate.

    Maps Project to the 'projects' table.
    """

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    owner_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    document_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    settings: Mapped[Optional[str]] = mapped_column(JSON, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    @classmethod
    def from_aggregate(cls, project: Any) -> ProjectModel:
        """
        Create a model instance from a Project aggregate.

        Args:
            project: Project aggregate instance
        """
        data = project.to_dict()
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            owner_id=data["owner_id"],
            document_count=data.get("document_count", 0),
            is_active=data.get("is_active", True),
            settings=data.get("settings"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            version=data.get("version", 1),
        )

    def update_from_aggregate(self, project: Any) -> None:
        """
        Update model fields from aggregate.

        Args:
            project: Project aggregate instance
        """
        data = project.to_dict()
        self.name = data["name"]
        self.description = data.get("description", "")
        self.owner_id = data["owner_id"]
        self.document_count = data.get("document_count", 0)
        self.is_active = data.get("is_active", True)
        self.settings = data.get("settings")
        self.updated_at = datetime.fromisoformat(data["updated_at"])
        self.version = data.get("version", 1)

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary for aggregate reconstruction."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "document_count": self.document_count,
            "is_active": self.is_active,
            "settings": self.settings or {},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }


class GlossaryModel(Base):
    """
    SQLAlchemy model for Glossary aggregate.

    Maps Glossary to the 'glossaries' table.
    One glossary per project.
    """

    __tablename__ = "glossaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(36), nullable=False, unique=True, index=True
    )
    mappings_json: Mapped[Optional[str]] = mapped_column(JSON, nullable=True, default=None)
    counters_json: Mapped[Optional[str]] = mapped_column(JSON, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    @classmethod
    def from_aggregate(cls, glossary: Any) -> GlossaryModel:
        """
        Create a model instance from a Glossary aggregate.

        Args:
            glossary: Glossary aggregate instance
        """
        from uuid import uuid4

        data = glossary.to_dict()
        return cls(
            id=str(uuid4()),
            project_id=data["id"],
            mappings_json=data.get("mappings", []),
            counters_json=data.get("counters", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            version=data.get("version", 1),
        )

    def update_from_aggregate(self, glossary: Any) -> None:
        """
        Update model fields from aggregate.

        Args:
            glossary: Glossary aggregate instance
        """
        data = glossary.to_dict()
        self.mappings_json = data.get("mappings", [])
        self.counters_json = data.get("counters", {})
        self.updated_at = datetime.fromisoformat(data["updated_at"])
        self.version = data.get("version", 1)

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary for aggregate reconstruction."""
        return {
            "id": self.project_id,
            "mappings": self.mappings_json or [],
            "counters": self.counters_json or {},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }
