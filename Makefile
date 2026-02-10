# ContextSafe - Development Makefile
# ============================================

.PHONY: help install install-dev test test-unit test-integration test-pbt test-e2e \
        lint format type-check security-check quality run dev docker-build docker-up \
        docker-down clean

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
POETRY := poetry
SRC_DIR := src/contextsafe
TEST_DIR := tests
DOCKER_COMPOSE := docker compose

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# ============================================
# HELP
# ============================================

help: ## Show this help message
	@echo "$(BLUE)ContextSafe - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ============================================
# INSTALLATION
# ============================================

install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	$(POETRY) install --only main

install-dev: ## Install all dependencies (dev included)
	@echo "$(BLUE)Installing all dependencies...$(NC)"
	$(POETRY) install
	@echo "$(GREEN)Installing spaCy Spanish model...$(NC)"
	$(POETRY) run python -m spacy download es_core_news_lg

install-frontend: ## Install frontend dependencies
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	cd frontend && npm install

# ============================================
# TESTING
# ============================================

test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	$(POETRY) run pytest $(TEST_DIR) -v --cov=$(SRC_DIR) --cov-report=term-missing

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	$(POETRY) run pytest $(TEST_DIR)/unit -v -m unit

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	$(POETRY) run pytest $(TEST_DIR)/integration -v -m integration

test-contract: ## Run contract tests only
	@echo "$(BLUE)Running contract tests...$(NC)"
	$(POETRY) run pytest $(TEST_DIR)/contract -v -m contract

test-pbt: ## Run property-based tests only
	@echo "$(BLUE)Running property-based tests...$(NC)"
	$(POETRY) run pytest $(TEST_DIR)/pbt -v -m pbt

test-e2e: ## Run end-to-end tests (requires running services)
	@echo "$(BLUE)Running E2E tests...$(NC)"
	$(POETRY) run pytest $(TEST_DIR)/e2e -v -m e2e

test-a11y: ## Run accessibility tests
	@echo "$(BLUE)Running accessibility tests...$(NC)"
	$(POETRY) run pytest $(TEST_DIR)/a11y -v

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(POETRY) run pytest $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=xml
	@echo "$(GREEN)Coverage report generated in htmlcov/$(NC)"

test-mutation: ## Run mutation tests (slow)
	@echo "$(YELLOW)Running mutation tests (this may take a while)...$(NC)"
	$(POETRY) run mutmut run --paths-to-mutate=$(SRC_DIR)

# ============================================
# CODE QUALITY
# ============================================

lint: ## Run linter (ruff)
	@echo "$(BLUE)Running linter...$(NC)"
	$(POETRY) run ruff check $(SRC_DIR) $(TEST_DIR)

lint-fix: ## Run linter and auto-fix issues
	@echo "$(BLUE)Running linter with auto-fix...$(NC)"
	$(POETRY) run ruff check $(SRC_DIR) $(TEST_DIR) --fix

format: ## Format code (ruff format)
	@echo "$(BLUE)Formatting code...$(NC)"
	$(POETRY) run ruff format $(SRC_DIR) $(TEST_DIR)

format-check: ## Check code formatting without changing
	@echo "$(BLUE)Checking code formatting...$(NC)"
	$(POETRY) run ruff format $(SRC_DIR) $(TEST_DIR) --check

type-check: ## Run type checker (mypy)
	@echo "$(BLUE)Running type checker...$(NC)"
	$(POETRY) run mypy $(SRC_DIR)

security-check: ## Run security scanner (bandit)
	@echo "$(BLUE)Running security scanner...$(NC)"
	$(POETRY) run bandit -r $(SRC_DIR) -c pyproject.toml

quality: lint type-check security-check ## Run all quality checks
	@echo "$(GREEN)All quality checks passed!$(NC)"

pre-commit: format lint-fix type-check test-unit ## Run pre-commit checks
	@echo "$(GREEN)Pre-commit checks passed!$(NC)"

# ============================================
# RUNNING
# ============================================

run: ## Run the application (production mode)
	@echo "$(BLUE)Starting ContextSafe API...$(NC)"
	$(POETRY) run uvicorn contextsafe.api.main:app --host 0.0.0.0 --port 8000

dev: ## Run in development mode with hot reload
	@echo "$(BLUE)Starting ContextSafe API (development mode)...$(NC)"
	$(POETRY) run uvicorn contextsafe.api.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend: ## Run frontend in development mode
	@echo "$(BLUE)Starting frontend (development mode)...$(NC)"
	cd frontend && npm run dev

# ============================================
# DOCKER
# ============================================

docker-build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	$(DOCKER_COMPOSE) build

docker-up: ## Start all services with Docker Compose
	@echo "$(BLUE)Starting services...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)Services started. API available at http://localhost:8000$(NC)"

docker-down: ## Stop all services
	@echo "$(BLUE)Stopping services...$(NC)"
	$(DOCKER_COMPOSE) down

docker-logs: ## Show logs from all services
	$(DOCKER_COMPOSE) logs -f

docker-ps: ## Show running containers
	$(DOCKER_COMPOSE) ps

docker-clean: ## Remove all containers, volumes, and images
	@echo "$(RED)Removing all Docker resources...$(NC)"
	$(DOCKER_COMPOSE) down -v --rmi local

# ============================================
# UTILITIES
# ============================================

clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	rm -rf dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Clean complete!$(NC)"

shell: ## Open Python shell with project context
	$(POETRY) run python

# ============================================
# LLM / NLP SETUP
# ============================================

download-models: ## Download required AI models
	@echo "$(BLUE)Downloading AI models...$(NC)"
	@echo "1. Downloading spaCy Spanish model..."
	$(POETRY) run python -m spacy download es_core_news_lg
	@echo ""
	@echo "$(YELLOW)2. For LLM (llama.cpp), manually download a GGUF model:$(NC)"
	@echo "   - Mistral-7B-v0.3 (recommended): https://huggingface.co/TheBloke/Mistral-7B-v0.3-GGUF"
	@echo "   - Place in: models/mistral-7b-v0.3.Q4_K_M.gguf"
	@echo ""
	@echo "$(YELLOW)3. For OCR, ensure Tesseract is installed:$(NC)"
	@echo "   - Ubuntu/Debian: sudo apt-get install tesseract-ocr tesseract-ocr-spa"
	@echo "   - macOS: brew install tesseract tesseract-lang"
	@echo ""
	@echo "$(GREEN)Model setup instructions complete!$(NC)"

check-hardware: ## Check hardware capabilities (GPU/CPU)
	@echo "$(BLUE)Checking hardware capabilities...$(NC)"
	$(POETRY) run python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU count: {torch.cuda.device_count() if torch.cuda.is_available() else 0}')"

# ============================================
# CI/CD HELPERS
# ============================================

ci-test: ## Run tests in CI mode
	$(POETRY) run pytest $(TEST_DIR) -v --cov=$(SRC_DIR) --cov-report=xml --junitxml=test-results.xml

ci-quality: format-check lint type-check security-check ## Run quality checks in CI mode
	@echo "$(GREEN)CI quality checks passed!$(NC)"
