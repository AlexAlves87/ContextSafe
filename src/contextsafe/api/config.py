# ContextSafe - API Configuration
# ============================================
"""
Application configuration using Pydantic Settings.

Loads configuration from environment variables and .env files.
Supports all compute modes: GPU, GPU_LIGHT, CPU, CPU_LIGHT.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from contextsafe.application.compute_mode import ComputeMode


class Environment(str, Enum):
    """Application environment."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ============================================
    # Application
    # ============================================
    app_env: Environment = Environment.DEVELOPMENT
    log_level: str = "info"
    debug: bool = False

    # ============================================
    # API Server
    # ============================================
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"]
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ============================================
    # Database
    # ============================================
    database_url: str = "sqlite+aiosqlite:///data/contextsafe.db"

    # ============================================
    # LLM (llama-cpp-python)
    # ============================================
    llm_model_path: Path = Path("models/mistral-7b-v0.3.Q4_K_M.gguf")
    llm_n_gpu_layers: int = 0
    llm_n_ctx: int = 4096
    llm_temperature: float = 0.7
    compute_mode: ComputeMode = ComputeMode.CPU

    @property
    def llm_gpu_layers_for_mode(self) -> int:
        """Get GPU layers based on compute mode."""
        if self.compute_mode == ComputeMode.GPU:
            return 35  # Full GPU offloading
        return 0  # CPU mode

    @property
    def ner_device_for_mode(self) -> int:
        """Get NER device based on compute mode. -1=CPU, 0+=GPU index."""
        if self.compute_mode == ComputeMode.GPU:
            return 0  # Use first GPU
        return -1  # CPU

    # ============================================
    # NLP / NER (spaCy)
    # ============================================
    spacy_model: str = "es_core_news_lg"
    ner_confidence_threshold: float = 0.7

    # ============================================
    # OCR (Tesseract)
    # ============================================
    tesseract_lang: str = "spa"
    tesseract_path: Path = Path("/usr/bin/tesseract")

    # ============================================
    # Spanish NER (XLM-RoBERTa-large transformer model)
    # ============================================
    ner_model: str = "MMG/xlm-roberta-large-ner-spanish"
    ner_min_score: float = 0.85
    ner_device: int = -1  # -1 = CPU, 0+ = GPU index

    # ============================================
    # Observability
    # ============================================
    metrics_enabled: bool = True
    metrics_port: int = 9090
    traces_enabled: bool = False

    # ============================================
    # Security
    # ============================================
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == Environment.PRODUCTION

    def validate_production_settings(self) -> list[str]:
        """Validate settings for production environment."""
        errors: list[str] = []

        if self.is_production:
            if self.debug:
                errors.append("DEBUG must be False in production")

        return errors


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
