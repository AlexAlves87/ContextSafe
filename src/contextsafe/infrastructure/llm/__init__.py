"""
LLM infrastructure for ContextSafe.

Provides local LLM-based NER and alias generation.
"""

from contextsafe.infrastructure.llm.alias_generator import AliasGenerator
from contextsafe.infrastructure.llm.llamacpp_adapter import LlamaCppNerAdapter
from contextsafe.infrastructure.llm.llm_config import (
    ComputeMode,
    LLMConfig,
    detect_compute_mode,
)
from contextsafe.infrastructure.llm.ollama_ner_adapter import OllamaNerAdapter


__all__ = [
    "AliasGenerator",
    "ComputeMode",
    "LLMConfig",
    "LlamaCppNerAdapter",
    "OllamaNerAdapter",
    "detect_compute_mode",
]
