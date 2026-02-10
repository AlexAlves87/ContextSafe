"""
Compute mode state.

Holds the runtime compute mode (GPU/CPU) in a shared location
so that ner_registry, document_processor, and system routes can
all access it without circular imports.
"""

from __future__ import annotations

import time

from contextsafe.application.compute_mode import ComputeMode

# Runtime compute mode (can be changed without restart)
_current_compute_mode: ComputeMode = ComputeMode.CPU

# GPU availability cache (avoids subprocess on every call)
_gpu_available_cache: bool | None = None
_gpu_cache_timestamp: float = 0.0
_GPU_CACHE_TTL: float = 60.0  # seconds


def set_current_compute_mode(mode: ComputeMode) -> None:
    """Set compute mode (called from system route)."""
    global _current_compute_mode, _gpu_available_cache, _gpu_cache_timestamp
    _current_compute_mode = mode
    # Invalidate cache on mode change
    _gpu_available_cache = None
    _gpu_cache_timestamp = 0.0


def get_current_compute_mode() -> ComputeMode:
    """Get current compute mode setting."""
    return _current_compute_mode


def _is_gpu_available() -> bool:
    """
    Check GPU availability using nvidia-smi first, then torch.

    Result is cached for 60 seconds to avoid subprocess overhead.
    """
    global _gpu_available_cache, _gpu_cache_timestamp

    now = time.monotonic()
    if _gpu_available_cache is not None and (now - _gpu_cache_timestamp) < _GPU_CACHE_TTL:
        return _gpu_available_cache

    available = False

    # Method 1: nvidia-smi (works on native Linux and WSL2 with GPU passthrough)
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            available = True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Method 2: torch.cuda (fallback)
    if not available:
        try:
            import torch
            available = torch.cuda.is_available()
        except ImportError:
            pass

    _gpu_available_cache = available
    _gpu_cache_timestamp = now
    return available


def get_effective_compute_mode() -> ComputeMode:
    """
    Get effective compute mode (falls back to CPU if GPU unavailable).

    Uses the same detection methods as system.py hardware endpoint
    (nvidia-smi + torch) for consistency. Result cached for 60s.
    """
    if _current_compute_mode == ComputeMode.GPU:
        if not _is_gpu_available():
            return ComputeMode.CPU
    return _current_compute_mode
