"""
SessionManager para ContextSafe (uso local).

Almacén in-memory para documentos, proyectos y glossary.
Sesión única local sin autenticación.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
import uuid


# ============================================================================
# MODELOS
# ============================================================================
@dataclass
class DocumentWithTimer:
    """Documento en memoria."""
    id: str
    filename: str
    page_count: int
    created_at: datetime
    project_id: str = ""
    format: str = "txt"
    state: str = "pending"
    progress: float = 0.0
    current_entity: str = ""
    entity_count: int = 0
    size_bytes: int = 0
    content: Any = None
    original_content: Any = None
    detected_pii: Any = None
    anonymized: Any = None
    error: Optional[str] = None


@dataclass
class Session:
    """Sesión local con documentos."""
    id: str
    created_at: datetime
    documents: Dict[str, DocumentWithTimer] = field(default_factory=dict)
    projects: Dict[str, Dict] = field(default_factory=dict)
    glossary: Dict[str, list] = field(default_factory=dict)

    @property
    def docs_count(self) -> int:
        return len(self.documents)

    @property
    def active_documents(self) -> Dict[str, DocumentWithTimer]:
        return self.documents

    def get_project_documents(self, project_id: str) -> Dict[str, DocumentWithTimer]:
        """Documentos de un proyecto específico."""
        return {
            k: v for k, v in self.documents.items()
            if v.project_id == project_id
        }


# ============================================================================
# SESSION MANAGER
# ============================================================================
class SessionManager:
    """Gestor de sesión local en memoria."""

    def __init__(self):
        self._sessions: Dict[str, Session] = {}

    _local_session_id: str = "local"

    def get_or_create_local_session(self) -> Session:
        """Obtiene o crea la sesión local única."""
        session = self._sessions.get(self._local_session_id)
        if session:
            return session
        now = datetime.utcnow()
        session = Session(
            id=self._local_session_id,
            created_at=now,
        )
        self._sessions[self._local_session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Obtiene sesión si existe."""
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str) -> None:
        """Elimina una sesión."""
        self._sessions.pop(session_id, None)

    # --- Documentos ---
    def add_document(
        self,
        session_id: str,
        filename: str,
        page_count: int,
        project_id: str = "",
        format: str = "txt",
        size_bytes: int = 0,
        content: Any = None,
        original_content: Any = None,
    ) -> Optional[DocumentWithTimer]:
        """Añade documento a la sesión."""
        session = self.get_session(session_id)
        if not session:
            return None

        now = datetime.utcnow()
        doc_id = str(uuid.uuid4())
        doc = DocumentWithTimer(
            id=doc_id,
            filename=filename,
            page_count=page_count,
            created_at=now,
            project_id=project_id,
            format=format,
            size_bytes=size_bytes,
            content=content,
            original_content=original_content,
        )
        session.documents[doc_id] = doc
        return doc

    def get_document(self, session_id: str, doc_id: str) -> Optional[DocumentWithTimer]:
        """Obtiene documento si existe."""
        session = self.get_session(session_id)
        if not session:
            return None
        return session.documents.get(doc_id)

    def update_document(
        self,
        session_id: str,
        doc_id: str,
        state: str = None,
        entity_count: int = None,
        detected_pii: Any = None,
        anonymized: Any = None,
        error: str = None,
        progress: float = None,
        current_entity: str = None,
    ) -> bool:
        """Actualiza datos de un documento."""
        doc = self.get_document(session_id, doc_id)
        if not doc:
            return False
        if state is not None:
            doc.state = state
        if entity_count is not None:
            doc.entity_count = entity_count
        if detected_pii is not None:
            doc.detected_pii = detected_pii
        if anonymized is not None:
            doc.anonymized = anonymized
        if error is not None:
            doc.error = error
        if progress is not None:
            doc.progress = progress
        if current_entity is not None:
            doc.current_entity = current_entity
        return True

    def delete_document(self, session_id: str, doc_id: str) -> bool:
        """Elimina un documento de la sesión."""
        session = self.get_session(session_id)
        if not session:
            return False
        if doc_id in session.documents:
            del session.documents[doc_id]
            return True
        return False

    # --- Proyectos ---
    def add_project(self, session_id: str, project_id: str, project_data: Dict) -> bool:
        """Añade un proyecto a la sesión."""
        session = self.get_session(session_id)
        if not session:
            return False
        session.projects[project_id] = project_data
        return True

    def get_project(self, session_id: str, project_id: str) -> Optional[Dict]:
        """Obtiene un proyecto de la sesión."""
        session = self.get_session(session_id)
        if not session:
            return None
        return session.projects.get(project_id)

    def list_projects(self, session_id: str) -> list:
        """Lista todos los proyectos de la sesión."""
        session = self.get_session(session_id)
        if not session:
            return []
        return list(session.projects.values())

    def update_project(self, session_id: str, project_id: str, project_data: Dict) -> bool:
        """Actualiza un proyecto en la sesión."""
        session = self.get_session(session_id)
        if not session or project_id not in session.projects:
            return False
        session.projects[project_id] = project_data
        return True

    def delete_project(self, session_id: str, project_id: str) -> bool:
        """Elimina un proyecto y sus documentos asociados."""
        session = self.get_session(session_id)
        if not session:
            return False
        if project_id in session.projects:
            del session.projects[project_id]
            docs_to_delete = [
                doc_id for doc_id, doc in session.documents.items()
                if doc.project_id == project_id
            ]
            for doc_id in docs_to_delete:
                del session.documents[doc_id]
            session.glossary.pop(project_id, None)
            return True
        return False

    # --- Glossary ---
    def get_glossary(self, session_id: str, project_id: str) -> list:
        """Obtiene el glossary de un proyecto."""
        session = self.get_session(session_id)
        if not session:
            return []
        return session.glossary.get(project_id, [])

    def set_glossary(self, session_id: str, project_id: str, entries: list) -> bool:
        """Establece el glossary completo de un proyecto."""
        session = self.get_session(session_id)
        if not session:
            return False
        session.glossary[project_id] = entries
        return True

    def add_glossary_entry(self, session_id: str, project_id: str, entry: Dict) -> bool:
        """Añade una entrada al glossary de un proyecto."""
        session = self.get_session(session_id)
        if not session:
            return False
        if project_id not in session.glossary:
            session.glossary[project_id] = []
        session.glossary[project_id].append(entry)
        return True


# Instancia global
session_manager = SessionManager()
