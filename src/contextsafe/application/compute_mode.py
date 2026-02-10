"""
Compute mode enum.

Standalone module to avoid import cascades through application.ports.__init__.py.
"""

from enum import Enum


class ComputeMode(str, Enum):
    """Processing compute mode."""
    GPU = "gpu"
    CPU = "cpu"
