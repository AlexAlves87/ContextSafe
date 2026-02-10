# Contributing to ContextSafe

Thank you for your interest in contributing to ContextSafe. This document explains how to participate in the project effectively.

ContextSafe is a privacy-first document anonymization system. Every contribution must respect this principle: **no user data should ever leave the local machine**.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Security Vulnerabilities](#security-vulnerabilities)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Architecture Guidelines](#architecture-guidelines)
- [Documentation](#documentation)
- [Recognition](#recognition)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you agree to uphold a respectful, inclusive, and harassment-free environment.

Report unacceptable behavior to **admin@contextsafe.es**.

## Security Vulnerabilities

**Do NOT report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability, please send a detailed report to **admin@contextsafe.es** with:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will acknowledge receipt within 48 hours and provide a detailed response within 7 days. We ask that you do not publicly disclose the vulnerability until we have had a chance to address it.

## How to Contribute

### Reporting Bugs

Before creating a bug report, search [existing issues](https://github.com/AlexAlves87/ContextSafe/issues) to avoid duplicates. When filing a new issue, include:

- **Environment**: OS, Python version, browser (if frontend-related)
- **Steps to reproduce**: Minimal, concrete steps
- **Expected behavior**: What should happen
- **Actual behavior**: What happens instead
- **Sample document** (if applicable): Use only synthetic/test data, **never real PII**

### Suggesting Features

Open a [GitHub Discussion](https://github.com/AlexAlves87/ContextSafe/discussions) or issue with the `enhancement` label. Include:

- The problem you are trying to solve
- Why existing functionality does not address it
- Your proposed approach (if any)

### Areas Where Help is Needed

- **New PII recognizers**: Additional entity types or improved patterns for existing ones
- **Language support**: Extending detection to other EU languages (see [`ml/docs/reports/`](ml/docs/reports/) for the multilingual replicability guide)
- **Accessibility**: WCAG 2.1 AA improvements in the frontend
- **Documentation**: Translations, tutorials, usage examples
- **Testing**: Adversarial test cases, edge cases for Spanish legal documents

Look for issues labeled [`good first issue`](https://github.com/AlexAlves87/ContextSafe/labels/good%20first%20issue) if you are new to the project.

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Tesseract OCR (`sudo apt install tesseract-ocr tesseract-ocr-spa`)

### Backend

```bash
git clone https://github.com/AlexAlves87/ContextSafe.git
cd ContextSafe

# Create virtual environment and install dependencies
make install-dev

# Copy environment config
cp .env.example .env

# Run the backend
make dev
```

### Frontend

```bash
make install-frontend
make dev-frontend
```

### Verify Everything Works

```bash
make test          # All tests
make quality       # Lint + format + type check
```

## Code Standards

### Language

| Element | Language |
|---|---|
| Code (variables, functions, classes) | English |
| Docstrings | English |
| User-facing documentation | English (primary), translations welcome |
| Git commits | English |

### Style

- **Python**: Follows [Ruff](https://docs.astral.sh/ruff/) defaults. Run `make lint` and `make format` before committing.
- **TypeScript**: ESLint configuration in `frontend/.eslintrc.cjs`.
- **Type hints**: Required for all Python function signatures.
- **No TODOs or stubs**: All contributed code must be complete and functional.

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>: <short description>

<optional body explaining WHY, not WHAT>
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `ci`, `chore`

Examples:
```
feat: add Cadastral Reference recognizer for Catastro format
fix: correct DNI checksum validation for NIE starting with Y
docs: add French translation for adversarial evaluation report
test: add edge cases for IBAN with mixed separators
```

Keep the subject line under 72 characters. Use imperative mood ("add", not "added").

## Pull Request Process

1. **Fork** the repository and create a branch from `main`
2. **Keep PRs focused**: One feature or fix per PR. Small PRs are reviewed faster.
3. **Write tests** for any new functionality (see [Testing](#testing))
4. **Update documentation** if your change affects the public API or user-facing behavior
5. **Ensure all checks pass**: `make quality && make test`
6. **Fill in the PR template** with a clear description of what and why

### What We Look For in Review

- Does it follow hexagonal architecture? (domain has no infrastructure imports)
- Are there tests? Do they cover edge cases?
- Does it introduce any external network calls? (not acceptable without explicit justification)
- Is PII handling safe? (no logging of real data, no external transmission)
- Is the code simple and readable?

### Response Times

We aim to review PRs within one week. Complex changes may take longer. If you haven't received feedback after 10 days, feel free to leave a comment.

## Testing

ContextSafe uses multiple testing strategies:

```bash
make test-unit     # Unit tests (~270+)
make test-pbt      # Property-based tests with Hypothesis (~70)
make test          # All tests
```

### Writing Tests

- **Unit tests** go in `tests/unit/`, mirroring the source structure
- **Property-based tests** go in `tests/pbt/`
- **Integration tests** go in `tests/integration/`
- Use `pytest` fixtures from `tests/conftest.py`
- For NER-related changes, include adversarial cases (OCR noise, Unicode tricks, boundary conditions)

### Test Data

**Never use real PII in tests.** Use synthetic data with intentionally invalid checksums:

- DNIs: Use letters that fail mod-23 verification
- IBANs: Use check digits `00` (always invalid)
- Names: Use obviously fictional combinations

## Architecture Guidelines

ContextSafe follows **hexagonal architecture**. Respect these boundaries:

```
domain/          Must NOT import from infrastructure/, api/, or external libraries
application/     Defines ports (interfaces). Imports only from domain/
infrastructure/  Implements ports. Can import external libraries
api/             HTTP/WebSocket layer. Orchestrates use cases
```

### Key Rules

- **Domain layer is pure Python**: No SQLAlchemy, no FastAPI, no spaCy imports
- **New NER adapters** must implement the `NerService` port in `application/ports/`
- **New repositories** must implement the corresponding port interface
- **Value objects are immutable**: Use `@dataclass(frozen=True)` or equivalent

### Adding a New PII Category

1. Add the enum value in `domain/shared/value_objects/pii_category.py`
2. Add the alias pattern in `ALIAS_PATTERNS`
3. Create or update the recognizer in `infrastructure/nlp/recognizers/`
4. Register it in the composite adapter
5. Add tests (unit + adversarial)
6. Update the PII Categories table in `README.md`

## Documentation

- **API changes**: Update `docs/API.md`
- **Deployment changes**: Update `docs/DEPLOYMENT.md`
- **New PII categories**: Update the table in `README.md`
- **ML research**: Reports go in `ml/docs/reports/` following the academic format described in the ML documentation

## Recognition

All contributors are recognized in the project. Significant contributions will be acknowledged in release notes and the project's contributors list.

## Questions?

If something is unclear or you need guidance before starting, open a [GitHub Discussion](https://github.com/AlexAlves87/ContextSafe/discussions) or email **admin@contextsafe.es**.
