"""
ApplyGlossaryChanges use case.

Applies user-defined alias changes and regenerates document.
"""

from contextsafe.application.use_cases.apply_glossary_changes.apply_glossary_changes import (
    AliasChange,
    ApplyGlossaryChanges,
    ApplyGlossaryChangesRequest,
    ApplyGlossaryChangesResponse,
)


__all__ = [
    "ApplyGlossaryChanges",
    "ApplyGlossaryChangesRequest",
    "ApplyGlossaryChangesResponse",
    "AliasChange",
]
