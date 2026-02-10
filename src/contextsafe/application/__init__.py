# ContextSafe - Application Layer
# ============================================
"""
Application layer containing use cases and ports.

Modules:
- ports: Abstract interfaces for infrastructure adapters
- use_cases: Application use cases (handlers, commands, results)

Use Cases:
- UC-001: IngestDocument - Document ingestion with OCR fallback
- UC-002: DetectPii - PII detection using NER
- UC-003: AssignAlias - Alias assignment with LLM
- UC-004: GenerateAnonymized - Document reconstruction
- UC-005: CreateProject - Project creation
- UC-006: LogAudit - Audit logging
"""
