# ContextSafe

**100% local document anonymization for sensitive legal and personal documents.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

ContextSafe detects and replaces Personally Identifiable Information (PII) in documents with consistent, project-wide aliases. It runs entirely on your machine -- no cloud services, no API keys, no data leaves your infrastructure.

Built for legal professionals handling court documents, law firms processing client files, and anyone who needs to anonymize sensitive documents while maintaining referential consistency across them.

## Why ContextSafe?

Existing solutions force a choice between privacy and usability:

| | Cloud APIs | Presidio | Commercial tools | **ContextSafe** |
|---|---|---|---|---|
| **Data stays local** | No | Yes | Varies | **Yes** |
| **GUI for non-technical users** | No | No | Some | **Yes** |
| **Open source** | No | Yes | No | **Yes** |
| **Cross-document alias consistency** | No | No | Rare | **Yes** |
| **Spanish legal identifiers** (DNI, NIE, NIG, ECLI) | Partial | No | Varies | **Yes** |
| **Processes PDF, DOCX, images directly** | Partial | No | Some | **Yes** |
| **Runs on consumer hardware** (8-16 GB RAM) | N/A | Yes | Varies | **Yes** |
| **No recurring cost** | No | Yes | No | **Yes** |

**Cloud APIs** (Google Cloud DLP, AWS Comprehend, Azure AI Language) require sending documents to US-controlled servers subject to the CLOUD Act. None of them offer cross-document alias consistency or detect Spanish judicial identifiers (NIG, ECLI). The [CCBE guidelines (Feb 2025)](https://www.ccbe.eu/fileadmin/speciality_distribution/public/documents/IT_LAW/ITL_Guides_recommendations/EN_ITL_20250227__CCBE-guidelines-on-the-use-of-cloud-computing-by-lawyers.pdf) and the Spanish Bar Association explicitly advise against sending client data to cloud AI services.

**Microsoft Presidio** is an excellent open-source SDK that ContextSafe uses internally as one of its NER adapters. However, Presidio is a library, not an application -- it has no GUI, no document processing pipeline, no glossary system, and no built-in support for Spanish entity types.

## Features

- **27 PII categories** including Spanish-specific: DNI/NIE, NIG, ECLI, Social Security, cadastral references, employer IDs, case numbers, and more
- **3 anonymization levels**:
  - *Basic*: masking with asterisks (`Juan Garcia` -> `***** ******`)
  - *Intermediate*: consistent pseudonyms (`Juan Garcia` -> `Persona_001` across all documents)
  - *Advanced*: synthetic data with mathematically invalid checksums (generated DNIs fail mod-23 verification, IBANs have invalid check digits)
- **Multi-format**: PDF, DOCX, and images (via Tesseract OCR)
- **Cross-document glossary**: same person always gets the same alias within a project
- **Hybrid NER pipeline**: combines Presidio, spaCy, regex patterns, and transformer models for higher recall
- **Human-in-the-loop review**: confidence zones let users verify uncertain detections before anonymization
- **Audit trail**: full traceability for compliance

## Quick Start

### Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation) 1.7+
- Tesseract OCR (`sudo apt install tesseract-ocr tesseract-ocr-spa` on Debian/Ubuntu)
- Node.js 18+ (for the frontend)

### Installation

```bash
git clone https://github.com/AlexAlves87/ContextSafe.git
cd contextsafe

# Backend
make install-dev

# Frontend
make install-frontend

# Copy and edit environment config
cp .env.example .env
```

### Running

```bash
# Start backend (API)
make dev

# In another terminal, start frontend
make dev-frontend
```

The API will be available at `http://localhost:8000` and the frontend at `http://localhost:5173`.

### Using Docker

```bash
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up -d
```

## Architecture

ContextSafe follows **hexagonal architecture** (ports & adapters):

```
Frontend (React + TypeScript)
    |
API Layer (FastAPI + WebSocket)
    |
Application Layer (Use Cases)
    |
Domain Layer (Aggregates, Entities, Value Objects)
    |
Infrastructure Layer (Adapters)
    |--- NLP: Presidio, spaCy, Regex, RoBERTa (composite pipeline)
    |--- Persistence: SQLite + SQLAlchemy async
    |--- Document Processing: pdfplumber, python-docx, Tesseract
    |--- LLM: Ollama (for Level 3 synthetic data generation)
```

### Project Structure

```
src/contextsafe/
  domain/              # Core business logic (no external dependencies)
    document_processing/
    entity_detection/
    anonymization/     # Glossary aggregate, alias mappings
    project_management/
    shared/            # Value objects, events, errors
  application/         # Use cases and port interfaces
  infrastructure/      # Adapter implementations
    nlp/               # NER adapters and anonymization strategies
    persistence/       # SQLite repositories
    document_processing/  # PDF, DOCX, image extractors
  api/                 # FastAPI routes, middleware, WebSocket
frontend/              # React + TypeScript + Tailwind
tests/
  unit/                # ~270+ unit tests
  pbt/                 # ~70 property-based tests (Hypothesis)
  integration/
```

## PII Categories

ContextSafe detects 27 categories of personally identifiable information:

| Category | Alias Pattern | Example |
|---|---|---|
| Person Name | `Persona_1` | Juan Garcia Lopez |
| Organization | `Org_1` | Empresa ABC, S.L. |
| Address | `Dir_1` | Calle Mayor 15, 3-B |
| Location | `Lugar_1` | Fuenlabrada |
| Postal Code | `CP_1` | 28001 |
| DNI / NIE | `ID_1` | 12345678Z / X1234567L |
| Passport | `Pasaporte_1` | AAA123456 |
| Phone | `Tel_1` | +34 612 345 678 |
| Email | `Email_1` | nombre@ejemplo.es |
| Bank Account | `Cuenta_1` | 1234-5678-90-1234567890 |
| IBAN | `IBAN_1` | ES91 2100 0418 4502 0005 1332 |
| Credit Card | `Tarjeta_1` | 4111 1111 1111 1111 |
| Date | `Fecha_1` | 15 de marzo de 2024 |
| Medical Record | `HistoriaMedica_1` | HC-2024/12345 |
| License Plate | `Matricula_1` | 1234 BCD |
| Social Security | `NSS_1` | 28/12345678/90 |
| Professional ID | `IdProf_1` | Colegiado 12345 |
| Case Number | `Proc_1` | 123/2024 |
| Platform | `Plataforma_1` | @usuario_telegram |
| IP Address | `IP_1` | 192.168.1.100 |
| ID Support Number | `Soporte_1` | IDESP123456789 |
| NIG | `NIG_1` | 2806541234567890123 |
| ECLI | `ECLI_1` | ECLI:ES:TS:2024:1234 |
| CSV | `CSV_1` | GEN-a1b2-c3d4-e5f6 |
| Health ID (CIP) | `CIP_1` | BBBB12345678 |
| Cadastral Reference | `RefCat_1` | 1234567AB1234N0001AB |
| Employer ID (CCC) | `CCC_1` | 28/1234567/89 |

## Configuration

Key environment variables (see `.env.example` for full list):

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | SQLite connection string | `sqlite+aiosqlite:///data/contextsafe.db` |
| `SPACY_MODEL` | spaCy model for NER | `es_core_news_lg` |
| `TESSERACT_LANG` | Tesseract language | `spa` |
| `OLLAMA_HOST` | Ollama URL (Level 3 only) | `http://localhost:11434` |
| `OLLAMA_MODEL` | LLM model (Level 3 only) | `qwen2:1.5b` |
| `DEV_MODE` | Skip OAuth in development | `false` |

## Development

```bash
# Tests
make test              # All tests
make test-unit         # Unit tests
make test-pbt          # Property-based tests (Hypothesis)

# Code quality
make lint              # Ruff linter
make format            # Ruff formatter
make type-check        # mypy strict mode
make quality           # All checks
```

## ML Research

The NER pipeline behind ContextSafe is backed by applied research documented in 43 technical reports covering adversarial evaluation, hybrid NER architectures, data augmentation, text normalization, fine-tuning strategies, and evaluation standards aligned with SemEval/CoNLL methodologies.

All reports are available in 6 languages under [`ml/docs/reports/`](ml/docs/reports/):

| Language | Path |
|---|---|
| Spanish (original) | [`ml/docs/reports/es/`](ml/docs/reports/es/) |
| English | [`ml/docs/reports/en/`](ml/docs/reports/en/) |
| Portuguese | [`ml/docs/reports/pt/`](ml/docs/reports/pt/) |
| French | [`ml/docs/reports/fr/`](ml/docs/reports/fr/) |
| German | [`ml/docs/reports/de/`](ml/docs/reports/de/) |
| Italian | [`ml/docs/reports/it/`](ml/docs/reports/it/) |

Key topics covered:

- **Hybrid NER architecture**: Design of the composite pipeline (Presidio + spaCy + Regex + RoBERTa) with voting-based merge strategy
- **Adversarial evaluation**: Systematic testing against edge cases, OCR noise, Unicode evasion, and multilingual mixing
- **Spanish legal entity detection**: Custom recognizers for DNI/NIE, NIG, ECLI, cadastral references, and other identifiers with checksum validation
- **Fine-tuning strategy**: Investigation of Legal-XLM-RoBERTa with Domain Adaptive Pre-Training (DAPT) for legal Spanish
- **Evaluation standards**: Entity-level metrics following SemEval 2013 taxonomy (strict, exact, partial, type matching)
- **Multilingual replicability**: Guide for adapting the pipeline to other EU jurisdictions (France, Germany, Italy, Portugal)

The ML training suite, scripts, and gazetteers are located in [`ml/`](ml/).

## Objectives

ContextSafe is functional today for Spanish-language documents. These are the areas we are actively working to improve:

- **Multilingual support**: Extend detection and anonymization to 6 EU languages (French, German, Italian, Portuguese, Dutch, English) while maintaining Spanish legal entity support
- **Zero-coding deployment**: One-command installation packages for users without technical background
- **Accuracy hardening**: Improve NER precision through model fine-tuning, expanded gazetteers, and adversarial testing
- **Accessibility**: WCAG 2.1 AA compliance for the web interface

## Contributing

Contributions are welcome. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the [GNU Affero General Public License v3.0](LICENSE) (AGPL-3.0-or-later).

This means you can freely use, modify, and distribute this software, but any modified version that is accessible over a network must also be made available under the same license.
