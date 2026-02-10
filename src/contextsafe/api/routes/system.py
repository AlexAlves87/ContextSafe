"""
System information and compute configuration routes.

Provides hardware detection and compute mode configuration.

Traceability:
- Contract: CNT-T4-SYSTEM-001
"""

from __future__ import annotations

import os
import subprocess
import re
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from contextsafe.application.compute_mode import ComputeMode
from contextsafe.api.services.compute_state import (
    get_current_compute_mode,
    get_effective_compute_mode,
    set_current_compute_mode,
)


router = APIRouter(prefix="/v1/system", tags=["system"])


# ============================================================================
# DETECTION FUNCTIONS
# ============================================================================

def detect_nvidia_gpu() -> dict[str, Any]:
    """
    Detect NVIDIA GPU using multiple methods.

    Priority:
    1. nvidia-smi (most reliable on native Linux)
    2. torch.cuda (works better on WSL2)
    """
    # Method 1: nvidia-smi
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            line = result.stdout.strip().split("\n")[0]
            parts = line.split(", ")
            if len(parts) >= 2:
                name = parts[0].strip()
                vram_mb = int(parts[1].strip())
                vram_gb = round(vram_mb / 1024, 1)
                vram_free_gb = round(int(parts[2].strip()) / 1024, 1) if len(parts) >= 3 else vram_gb
                return {
                    "available": True,
                    "name": name,
                    "vram_gb": vram_gb,
                    "vram_free_gb": vram_free_gb,
                    "driver": "nvidia",
                }
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass

    # Method 2: torch.cuda (fallback, better for WSL2)
    try:
        import torch
        if torch.cuda.is_available():
            device_props = torch.cuda.get_device_properties(0)
            vram_bytes = device_props.total_memory
            vram_gb = round(vram_bytes / (1024 ** 3), 1)
            vram_free = torch.cuda.memory_reserved(0) - torch.cuda.memory_allocated(0)
            vram_free_gb = round(vram_free / (1024 ** 3), 1) if vram_free > 0 else vram_gb
            return {
                "available": True,
                "name": device_props.name,
                "vram_gb": vram_gb,
                "vram_free_gb": vram_free_gb,
                "driver": "cuda",
            }
    except (ImportError, RuntimeError):
        pass

    return {"available": False, "name": None, "vram_gb": 0, "vram_free_gb": 0, "driver": None}


def detect_cpu() -> dict[str, Any]:
    """Detect CPU information."""
    cpu_count = os.cpu_count() or 1

    cpu_name = "Unknown CPU"
    try:
        # Linux: read from /proc/cpuinfo
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("model name"):
                    cpu_name = line.split(":")[1].strip()
                    break
    except Exception:
        pass

    return {
        "name": cpu_name,
        "cores": cpu_count,
        "threads": cpu_count,  # Usually same as cores reported by os.cpu_count()
    }


def detect_ram() -> dict[str, Any]:
    """Detect system RAM information."""
    try:
        import psutil
        mem = psutil.virtual_memory()
        return {
            "total_gb": round(mem.total / (1024 ** 3), 1),
            "available_gb": round(mem.available / (1024 ** 3), 1),
            "percent_used": mem.percent,
        }
    except ImportError:
        # Fallback: read from /proc/meminfo on Linux
        try:
            total_kb = 0
            available_kb = 0
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        total_kb = int(re.search(r"\d+", line).group())
                    elif line.startswith("MemAvailable:"):
                        available_kb = int(re.search(r"\d+", line).group())
            total_gb = round(total_kb / (1024 ** 2), 1)
            available_gb = round(available_kb / (1024 ** 2), 1)
            return {
                "total_gb": total_gb,
                "available_gb": available_gb,
                "percent_used": round((1 - available_gb / total_gb) * 100, 1) if total_gb > 0 else 0,
            }
        except Exception:
            pass
    return {"total_gb": 0, "available_gb": 0, "percent_used": 0}


def recommend_compute_mode(gpu_info: dict, ram_info: dict) -> ComputeMode:
    """
    Recommend compute mode based on hardware.

    Rules:
    - GPU with >=4GB VRAM → GPU mode
    - No GPU or <4GB VRAM → CPU mode
    """
    if gpu_info.get("available", False):
        vram_gb = gpu_info.get("vram_gb", 0)
        if vram_gb >= 4:
            return ComputeMode.GPU
    return ComputeMode.CPU


# ============================================================================
# API SCHEMAS
# ============================================================================

class ComputeModeRequest(BaseModel):
    """Request to set compute mode."""
    mode: Literal["gpu", "cpu"]


class ComputeModeResponse(BaseModel):
    """Response with current compute mode."""
    mode: str
    gpu_available: bool
    effective: str  # What's actually being used


class HardwareInfoResponse(BaseModel):
    """Full hardware information response."""
    gpu: dict
    cpu: dict
    ram: dict
    current_mode: str
    recommended_mode: str


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.get("/hardware", response_model=HardwareInfoResponse)
async def get_hardware_info() -> HardwareInfoResponse:
    """
    Detect system hardware for processing configuration.

    Returns:
        Hardware information including GPU, CPU, RAM, and modes.
    """
    gpu_info = detect_nvidia_gpu()
    cpu_info = detect_cpu()
    ram_info = detect_ram()
    recommended = recommend_compute_mode(gpu_info, ram_info)

    return HardwareInfoResponse(
        gpu=gpu_info,
        cpu=cpu_info,
        ram=ram_info,
        current_mode=get_current_compute_mode().value,
        recommended_mode=recommended.value,
    )


@router.get("/compute-mode", response_model=ComputeModeResponse)
async def get_compute_mode() -> ComputeModeResponse:
    """Get current compute mode."""
    gpu_info = detect_nvidia_gpu()
    current = get_current_compute_mode()
    effective = get_effective_compute_mode()

    return ComputeModeResponse(
        mode=current.value,
        gpu_available=gpu_info.get("available", False),
        effective=effective.value,
    )


@router.post("/compute-mode", response_model=ComputeModeResponse)
async def set_compute_mode(request: ComputeModeRequest) -> ComputeModeResponse:
    """
    Set compute mode for processing.

    If GPU is selected but not available, returns error.
    Resets NER service to use new device on next call.
    """
    gpu_info = detect_nvidia_gpu()
    requested_mode = ComputeMode(request.mode)

    # Validate GPU availability
    if requested_mode == ComputeMode.GPU and not gpu_info.get("available", False):
        raise HTTPException(
            status_code=400,
            detail="GPU mode requested but no compatible GPU detected"
        )

    old_mode = get_current_compute_mode()
    set_current_compute_mode(requested_mode)

    # Reset NER service if mode changed (so it reinitializes with new device)
    if old_mode != requested_mode:
        from contextsafe.api.services.ner_registry import reset_ner_service
        reset_ner_service()

    return ComputeModeResponse(
        mode=requested_mode.value,
        gpu_available=gpu_info.get("available", False),
        effective=get_effective_compute_mode().value,
    )
