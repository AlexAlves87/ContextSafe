"""
ContextSafe Desktop Launcher.

Starts the API server and opens the browser automatically.
Provides a simple system tray icon for Windows.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))


def setup_environment() -> None:
    """Setup environment variables for the application."""
    # Default settings for desktop mode
    os.environ.setdefault("APP_ENV", "development")
    os.environ.setdefault("API_HOST", "127.0.0.1")
    os.environ.setdefault("API_PORT", "8000")
    os.environ.setdefault("DEBUG", "false")
    os.environ.setdefault("USE_HYBRID_NER", "true")


def check_ollama_available() -> bool:
    """Check if Ollama is running (for LLM-based detection)."""
    try:
        import httpx
        response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


def start_server() -> None:
    """Start the FastAPI server."""
    import uvicorn

    uvicorn.run(
        "contextsafe.server:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )


def wait_for_server(host: str = "127.0.0.1", port: int = 8000, timeout: int = 30) -> bool:
    """Wait for the server to be ready."""
    import httpx

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = httpx.get(f"http://{host}:{port}/health", timeout=1.0)
            if response.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def main() -> None:
    """Main entry point for the desktop application."""
    print("=" * 50)
    print("  ContextSafe - Anonimizador de Documentos")
    print("=" * 50)
    print()

    # Setup environment
    setup_environment()

    # Check Ollama
    print("Verificando dependencias...")
    if check_ollama_available():
        print("  [OK] Ollama detectado - LLM habilitado")
    else:
        print("  [--] Ollama no disponible - usando solo Presidio/NER")
        os.environ["USE_HYBRID_NER"] = "false"

    print()
    print("Iniciando servidor...")

    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Wait for server to be ready
    print("Esperando servidor... ", end="", flush=True)
    if wait_for_server():
        print("OK")
        print()
        print("Servidor iniciado en http://127.0.0.1:8000")
        print()

        # Open browser
        print("Abriendo navegador...")
        webbrowser.open("http://127.0.0.1:8000/docs")

        print()
        print("-" * 50)
        print("Presiona Ctrl+C para cerrar el servidor")
        print("-" * 50)

        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nCerrando servidor...")
    else:
        print("ERROR")
        print("No se pudo iniciar el servidor.")
        input("Presiona Enter para cerrar...")
        sys.exit(1)


if __name__ == "__main__":
    main()
