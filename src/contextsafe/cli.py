"""
Command Line Interface.

Administrative commands for ContextSafe.

Traceability:
- Contract: CNT-T5-CLI-001
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import click


@click.group()
@click.version_option(version="0.1.0", prog_name="contextsafe")
def cli() -> None:
    """ContextSafe - Document Anonymization CLI."""


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool) -> None:
    """Start the API server."""
    import uvicorn

    click.echo(f"Starting ContextSafe server on {host}:{port}")
    uvicorn.run(
        "contextsafe.server:app",
        host=host,
        port=port,
        reload=reload,
    )


@cli.command("init-db")
@click.option(
    "--path",
    type=click.Path(),
    default="data/contextsafe.db",
    help="Database path",
)
def init_db(path: str) -> None:
    """Initialize the database schema."""

    async def _init() -> None:
        from contextsafe.infrastructure.persistence import Database

        db_path = Path(path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        db_url = f"sqlite+aiosqlite:///{db_path}"
        database = Database(db_url)
        await database.create_all()
        await database.close()

        click.echo(f"Database initialized at {db_path}")

    asyncio.run(_init())


@cli.command("download-model")
@click.argument("model_name")
@click.option(
    "--output-dir",
    type=click.Path(),
    default="models",
    help="Output directory",
)
@click.option(
    "--compute-mode",
    type=click.Choice(["gpu", "cpu"]),
    default="cpu",
    help="Compute mode",
)
def download_model(model_name: str, output_dir: str, compute_mode: str) -> None:
    """Download an LLM model from Hugging Face."""
    click.echo(f"Downloading model: {model_name}")
    click.echo(f"Output directory: {output_dir}")
    click.echo(f"Compute mode: {compute_mode}")

    # TODO: Implement actual download logic
    click.echo("Model download not yet implemented.")


@cli.command()
def benchmark() -> None:
    """Run performance benchmark."""
    click.echo("Running benchmark...")

    # TODO: Implement benchmark logic
    click.echo("Benchmark not yet implemented.")


@cli.group()
def license() -> None:
    """License management commands."""


@license.command("status")
def license_status() -> None:
    """Check license status."""
    click.echo("License: Community Edition (Unlimited)")
    click.echo("Status: Active")


def main() -> None:
    """CLI entry point."""
    cli()


if __name__ == "__main__":
    main()
