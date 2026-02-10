# Changelog

All notable changes to ContextSafe will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-11

### Added

#### Core Features
- **Document Ingestion**: Support for PDF, DOCX, and TXT files
- **PII Detection**: Multi-strategy detection using spaCy NER and regex patterns
- **Alias Assignment**: Consistent alias generation per entity type (BR-002)
- **Document Anonymization**: Replace PII with configurable aliases (BR-004)
- **Project Management**: Organize documents into projects with shared glossaries

#### Privacy & Security
- Local-only processing (no external API calls)
- SQLite with SQLCipher encryption for data at rest
- Comprehensive audit logging for GDPR compliance
- Per-project glossary isolation

#### PII Categories Supported
- Person names (PERSON_NAME)
- Organizations (ORGANIZATION)
- Addresses (ADDRESS)
- Phone numbers (PHONE)
- Email addresses (EMAIL)
- ID numbers (ID_NUMBER)
- Credit cards (CREDIT_CARD)
- Bank accounts (BANK_ACCOUNT)
- Dates (DATE)
- Currency amounts (CURRENCY)
- Locations (LOCATION)
- Medical terms (MEDICAL)
- Biometric data (BIOMETRIC)

#### User Interface
- React-based SPA with TypeScript
- Workspace view with document list and preview
- Document detail view with entity highlighting
- Real-time processing status via WebSocket
- Dark mode support
- WCAG-A accessibility compliance

#### API
- RESTful API with FastAPI
- WebSocket endpoint for progress updates
- OpenAPI documentation at /docs
- Health check endpoint

#### Developer Experience
- Comprehensive test suite (unit, PBT, integration, contract)
- Property-based tests with Hypothesis
- Contract validation with icontract
- CI/CD pipeline with GitHub Actions
- Docker support with docker-compose
- Makefile for common operations

#### Documentation
- QUICKSTART.md for getting started
- DEPLOYMENT.md for production deployment
- ROLLBACK.md for rollback procedures
- API.md for API reference
- Inline code documentation

### Architecture

- Hexagonal architecture (ADR-001)
- Domain-Driven Design with bounded contexts:
  - BC-001: Document Processing
  - BC-002: Entity Detection
  - BC-003: Anonymization
  - BC-004: Project Management
- Railway-Oriented Programming for error handling

### Technical Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy async
- **Frontend**: React 18, TypeScript 5, Vite, Tailwind CSS, Zustand
- **NLP**: spaCy (es_core_news_lg)
- **OCR**: Tesseract (optional)
- **LLM**: llama-cpp-python (optional, for semantic aliases)
- **Database**: SQLite with SQLCipher

### Quality Metrics

- Test coverage target: 80%+
- PII detection recall: 95%+ on structured text
- Alias consistency: 99.9%
- Response time: <3s for document ingestion (p99)

### Traceability

- 8 Risks addressed (R-001 to R-008)
- 8 QAS scenarios covered (QAS-001 to QAS-006, QAS-UX-001, QAS-UX-002)
- 24 Functions implemented (F-001 to F-019, F-UI-001 to F-UI-005)
- 6 ADRs enforced (ADR-001 to ADR-006)

---

## [Unreleased]

### Planned
- Enhanced LLM-based semantic alias generation
- Batch processing improvements
- Additional language models support
- Export to multiple formats (DOCX, PDF redacted)
