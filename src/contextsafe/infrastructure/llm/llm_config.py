"""
LLM configuration and model loading.

Traceability:
- Contract: CNT-T3-LLM-CONFIG-001
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ComputeMode(str, Enum):
    """Hardware compute modes for inference."""

    GPU = "gpu"  # GPU acceleration (NVIDIA CUDA)
    CPU = "cpu"  # CPU only


@dataclass(frozen=True)
class LLMConfig:
    """
    Configuration for LLM model loading.

    Supports llama.cpp for local inference.
    """

    model_path: Path
    compute_mode: ComputeMode = ComputeMode.CPU
    context_length: int = 4096
    n_threads: int = 4
    n_gpu_layers: int = 0
    temperature: float = 0.1
    top_p: float = 0.9
    repeat_penalty: float = 1.1
    max_tokens: int = 512

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not self.model_path.exists():
            raise ValueError(f"Model path does not exist: {self.model_path}")

        if self.context_length < 256:
            raise ValueError("context_length must be at least 256")

        if self.n_threads < 1:
            raise ValueError("n_threads must be at least 1")

    @classmethod
    def from_env(cls) -> LLMConfig:
        """
        Create configuration from environment variables.

        Environment variables:
        - CONTEXTSAFE_MODEL_PATH: Path to model file
        - CONTEXTSAFE_COMPUTE_MODE: gpu/cpu
        - CONTEXTSAFE_CONTEXT_LENGTH: Context window size
        - CONTEXTSAFE_N_THREADS: Number of CPU threads
        """
        import os

        model_path = Path(os.environ.get("CONTEXTSAFE_MODEL_PATH", "models/model.gguf"))
        compute_mode = ComputeMode(os.environ.get("CONTEXTSAFE_COMPUTE_MODE", "cpu"))

        n_gpu_layers = 35 if compute_mode == ComputeMode.GPU else 0
        n_threads = int(os.environ.get("CONTEXTSAFE_N_THREADS", "4"))
        context_length = int(os.environ.get("CONTEXTSAFE_CONTEXT_LENGTH", "4096"))

        return cls(
            model_path=model_path,
            compute_mode=compute_mode,
            context_length=context_length,
            n_threads=n_threads,
            n_gpu_layers=n_gpu_layers,
        )

    @property
    def is_gpu_enabled(self) -> bool:
        """Check if GPU acceleration is enabled."""
        return self.compute_mode == ComputeMode.GPU


def detect_compute_mode() -> ComputeMode:
    """
    Auto-detect the best compute mode for the current hardware.

    Returns:
        ComputeMode based on available hardware
    """
    try:
        import torch

        if torch.cuda.is_available():
            vram = torch.cuda.get_device_properties(0).total_memory
            if vram >= 4 * 1024**3:  # 4GB+
                return ComputeMode.GPU
    except ImportError:
        pass

    return ComputeMode.CPU
