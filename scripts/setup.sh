#!/bin/bash
# ============================================
# ContextSafe - Setup Script
# ============================================
# Este script configura todo lo necesario para ejecutar ContextSafe
# Ejecutar con: bash scripts/setup.sh

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     ContextSafe - Script de Configuración      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Directorio del proyecto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo -e "${YELLOW}Directorio del proyecto: ${PROJECT_DIR}${NC}"
echo ""

# ============================================
# 1. Verificar Python
# ============================================
echo -e "${BLUE}[1/7] Verificando Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓ Python ${PYTHON_VERSION} encontrado${NC}"
else
    echo -e "${RED}✗ Python 3 no encontrado. Instálalo primero.${NC}"
    exit 1
fi

# ============================================
# 2. Crear/verificar entorno virtual
# ============================================
echo ""
echo -e "${BLUE}[2/7] Configurando entorno virtual...${NC}"
if [ -d ".venv" ]; then
    echo -e "${GREEN}✓ Entorno virtual existente encontrado${NC}"
else
    echo -e "${YELLOW}Creando entorno virtual...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✓ Entorno virtual creado${NC}"
fi

# Activar entorno virtual
source .venv/bin/activate

# ============================================
# 3. Instalar dependencias base
# ============================================
echo ""
echo -e "${BLUE}[3/7] Instalando dependencias Python...${NC}"
pip install --upgrade pip wheel setuptools > /dev/null 2>&1

# Instalar dependencias principales
echo -e "${YELLOW}Instalando dependencias (esto puede tardar varios minutos)...${NC}"

# Core dependencies
pip install pydantic pydantic-settings structlog httpx > /dev/null 2>&1
echo -e "${GREEN}  ✓ Core${NC}"

# Web framework
pip install fastapi "uvicorn[standard]" websockets > /dev/null 2>&1
echo -e "${GREEN}  ✓ FastAPI${NC}"

# Database
pip install "sqlalchemy[asyncio]" aiosqlite > /dev/null 2>&1
echo -e "${GREEN}  ✓ SQLAlchemy${NC}"

# Document processing
pip install pdfplumber python-docx chardet Pillow > /dev/null 2>&1
echo -e "${GREEN}  ✓ Document processing${NC}"

# Testing
pip install pytest pytest-asyncio pytest-cov hypothesis > /dev/null 2>&1
echo -e "${GREEN}  ✓ Testing${NC}"

# Quality tools
pip install ruff mypy bandit > /dev/null 2>&1
echo -e "${GREEN}  ✓ Quality tools${NC}"

# Design by Contract
pip install icontract > /dev/null 2>&1
echo -e "${GREEN}  ✓ icontract${NC}"

echo -e "${GREEN}✓ Dependencias Python instaladas${NC}"

# ============================================
# 4. Instalar spaCy y modelo español
# ============================================
echo ""
echo -e "${BLUE}[4/7] Instalando spaCy y modelo NER español...${NC}"
pip install spacy > /dev/null 2>&1

# Verificar si el modelo ya está instalado
if python3 -c "import spacy; spacy.load('es_core_news_lg')" 2>/dev/null; then
    echo -e "${GREEN}✓ Modelo es_core_news_lg ya instalado${NC}"
else
    echo -e "${YELLOW}Descargando modelo es_core_news_lg (~550MB)...${NC}"
    python3 -m spacy download es_core_news_lg
    echo -e "${GREEN}✓ Modelo spaCy descargado${NC}"
fi

# ============================================
# 5. Configurar directorio de modelos LLM
# ============================================
echo ""
echo -e "${BLUE}[5/7] Configurando directorio de modelos LLM...${NC}"
mkdir -p models
mkdir -p data

if [ -f "models/mistral-7b-v0.3.Q4_K_M.gguf" ]; then
    echo -e "${GREEN}✓ Modelo LLM ya descargado${NC}"
else
    echo -e "${YELLOW}⚠ Modelo LLM no encontrado${NC}"
    echo ""
    echo -e "${YELLOW}El modelo LLM es OPCIONAL pero recomendado para alias semánticos.${NC}"
    echo -e "${YELLOW}Para descargarlo manualmente (4.4GB):${NC}"
    echo ""
    echo -e "  ${BLUE}wget -c https://huggingface.co/TheBloke/Mistral-7B-v0.3-GGUF/resolve/main/mistral-7b-v0.3.Q4_K_M.gguf -O models/mistral-7b-v0.3.Q4_K_M.gguf${NC}"
    echo ""
    echo -e "${YELLOW}Modelos alternativos más pequeños:${NC}"
    echo -e "  - Q2_K (2.8GB): mistral-7b-v0.3.Q2_K.gguf"
    echo -e "  - Q3_K_S (3.2GB): mistral-7b-v0.3.Q3_K_S.gguf"
    echo ""
fi

# ============================================
# 6. Configurar .env
# ============================================
echo ""
echo -e "${BLUE}[6/7] Configurando variables de entorno...${NC}"
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ Archivo .env ya existe${NC}"
else
    cp .env.example .env
    # Generar clave de encriptación aleatoria
    DB_KEY=$(python3 -c "import secrets; print(secrets.token_hex(16))")
    sed -i "s/your_secure_encryption_key_here/${DB_KEY}/g" .env
    echo -e "${GREEN}✓ Archivo .env creado con clave de encriptación generada${NC}"
fi

# ============================================
# 7. Verificar instalación
# ============================================
echo ""
echo -e "${BLUE}[7/7] Verificando instalación...${NC}"

# Test imports
python3 << 'EOF'
import sys
errors = []

try:
    import pydantic
    print("  ✓ pydantic")
except ImportError as e:
    errors.append(f"pydantic: {e}")

try:
    import fastapi
    print("  ✓ fastapi")
except ImportError as e:
    errors.append(f"fastapi: {e}")

try:
    import sqlalchemy
    print("  ✓ sqlalchemy")
except ImportError as e:
    errors.append(f"sqlalchemy: {e}")

try:
    import spacy
    nlp = spacy.load("es_core_news_lg")
    print("  ✓ spacy + es_core_news_lg")
except Exception as e:
    errors.append(f"spacy: {e}")

try:
    import pytest
    print("  ✓ pytest")
except ImportError as e:
    errors.append(f"pytest: {e}")

try:
    import hypothesis
    print("  ✓ hypothesis")
except ImportError as e:
    errors.append(f"hypothesis: {e}")

if errors:
    print(f"\n⚠ Errores encontrados:")
    for err in errors:
        print(f"  - {err}")
    sys.exit(1)
EOF

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        ¡Configuración completada!              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Próximos pasos:${NC}"
echo ""
echo -e "  ${YELLOW}1. Activar el entorno virtual:${NC}"
echo -e "     ${BLUE}source .venv/bin/activate${NC}"
echo ""
echo -e "  ${YELLOW}2. Ejecutar tests:${NC}"
echo -e "     ${BLUE}PYTHONPATH=src pytest tests/unit -v${NC}"
echo ""
echo -e "  ${YELLOW}3. Iniciar el servidor de desarrollo:${NC}"
echo -e "     ${BLUE}PYTHONPATH=src uvicorn contextsafe.api.main:app --reload --port 8000${NC}"
echo ""
echo -e "  ${YELLOW}4. (Opcional) Descargar modelo LLM:${NC}"
echo -e "     ${BLUE}wget -c https://huggingface.co/TheBloke/Mistral-7B-v0.3-GGUF/resolve/main/mistral-7b-v0.3.Q4_K_M.gguf -O models/mistral-7b-v0.3.Q4_K_M.gguf${NC}"
echo ""
