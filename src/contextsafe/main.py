"""
Application entry point.

Starts the FastAPI server with uvicorn.

Traceability:
- Contract: CNT-T5-MAIN-001
"""

from __future__ import annotations

import logging
import sys

import uvicorn

from contextsafe.api.config import get_settings


def setup_logging(level: str = "info") -> None:
    """
    Configure logging for the application.

    Args:
        level: Logging level (debug, info, warning, error)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def main() -> None:
    """
    Application entry point.

    Loads configuration and starts the server.
    """
    settings = get_settings()

    # Validate production settings
    if settings.is_production:
        errors = settings.validate_production_settings()
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            sys.exit(1)

    # Setup logging
    setup_logging(settings.log_level)

    logger = logging.getLogger(__name__)
    logger.info(f"Starting ContextSafe server on {settings.api_host}:{settings.api_port}")
    logger.info(f"Environment: {settings.app_env.value}")
    logger.info(f"Compute mode: {settings.compute_mode.value}")

    # Start server
    uvicorn.run(
        "contextsafe.server:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
