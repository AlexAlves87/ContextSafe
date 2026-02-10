# ContextSafe - Domain Layer
# ============================================
"""
Domain layer containing business logic, entities, value objects, and domain events.

Bounded Contexts:
- BC-001: DocumentProcessing - Document ingestion and state management
- BC-002: EntityDetection - PII detection and classification
- BC-003: Anonymization - Alias generation and glossary management
- BC-004: ProjectManagement - Projects, users, and audit logging

This layer is framework-agnostic and contains no infrastructure dependencies.
"""
