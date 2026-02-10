# ContextSafe - Document Anonymization System
# ============================================
"""
ContextSafe - Sistema de anonimizacion inteligente de documentos sensibles.

A 100% local document anonymization system that:
- Ingests documents (PDF, Word, images via OCR)
- Detects PII using local NER (spaCy)
- Generates consistent aliases using local LLM (llama.cpp)
- Outputs anonymized documents with reversible glossary

Features:
- Full local execution (no cloud dependencies)
- GPU and CPU support
- Consistent alias mapping across documents
- Audit trail for compliance
"""

__version__ = "0.1.0"
__author__ = "ContextSafe Team"


def get_settings():
    """Lazy load settings to avoid import-time configuration loading."""
    from contextsafe.api.config import get_settings as _get_settings
    return _get_settings()


def create_app():
    """Lazy load app factory to avoid import-time configuration loading."""
    from contextsafe.server import create_app as _create_app
    return _create_app()


__all__ = [
    "__version__",
    "__author__",
    "get_settings",
    "create_app",
]
