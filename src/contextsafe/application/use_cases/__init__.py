"""Use cases for ContextSafe."""
from contextsafe.application.use_cases.create_project import (
    CreateProject,
    CreateProjectRequest,
    CreateProjectResponse,
)
from contextsafe.application.use_cases.detect_pii import (
    DetectPii,
    DetectPiiRequest,
    DetectPiiResponse,
    DetectedEntity,
)
from contextsafe.application.use_cases.generate_anonymized import (
    GenerateAnonymized,
    GenerateAnonymizedRequest,
    GenerateAnonymizedResponse,
    EntityToAnonymize,
    AliasUsed,
)
from contextsafe.application.use_cases.ingest_document import (
    IngestDocument,
    IngestDocumentRequest,
    IngestDocumentResponse,
)
from contextsafe.application.use_cases.apply_glossary_changes import (
    ApplyGlossaryChanges,
    ApplyGlossaryChangesRequest,
    ApplyGlossaryChangesResponse,
    AliasChange,
)

__all__ = [
    # Ingest Document
    "IngestDocument",
    "IngestDocumentRequest",
    "IngestDocumentResponse",
    # Detect PII
    "DetectPii",
    "DetectPiiRequest",
    "DetectPiiResponse",
    "DetectedEntity",
    # Generate Anonymized
    "GenerateAnonymized",
    "GenerateAnonymizedRequest",
    "GenerateAnonymizedResponse",
    "EntityToAnonymize",
    "AliasUsed",
    # Create Project
    "CreateProject",
    "CreateProjectRequest",
    "CreateProjectResponse",
    # Apply Glossary Changes
    "ApplyGlossaryChanges",
    "ApplyGlossaryChangesRequest",
    "ApplyGlossaryChangesResponse",
    "AliasChange",
]

