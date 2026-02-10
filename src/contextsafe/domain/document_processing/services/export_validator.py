"""
Export validation service (Safety Latch + Sanity Checks).

Implements two complementary safety mechanisms:
1. Safety Latch: Blocks export until all AMBER/RED entities are reviewed.
2. Sanity Checks: Validates minimum expected entities per document type.

Traceability:
- AI Act Art. 14: Human oversight for high-risk AI systems
- Design: Propuesta Mejoras Arquitectónicas v2.1, Módulo B §3.2
- Strategy C: Especificación Safety Net §4
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from contextsafe.domain.document_processing.services.document_classifier import (
    DocumentTypeEnum,
)
from contextsafe.domain.shared.value_objects.pii_category import PiiCategoryEnum


class ValidationSeverity(str, Enum):
    """Severity level of validation failures."""

    CRITICAL = "CRITICAL"  # Blocks export
    WARNING = "WARNING"    # Alerts user but allows override


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result of a single validation check."""

    passed: bool
    severity: ValidationSeverity
    rule_id: str
    message: str


@dataclass(frozen=True, slots=True)
class ExportValidation:
    """Aggregated result of all export validation checks."""

    can_export: bool
    pending_reviews: int
    total_entities: int
    reviewed_entities: int
    validation_results: tuple[ValidationResult, ...] = field(default_factory=tuple)

    @property
    def has_critical_failures(self) -> bool:
        """True if any CRITICAL validation failed."""
        return any(
            not r.passed and r.severity == ValidationSeverity.CRITICAL
            for r in self.validation_results
        )

    @property
    def warnings(self) -> list[ValidationResult]:
        """All WARNING-level failures."""
        return [
            r for r in self.validation_results
            if not r.passed and r.severity == ValidationSeverity.WARNING
        ]

    @property
    def review_percentage(self) -> int:
        """Percentage of entities reviewed (0-100)."""
        if self.total_entities == 0:
            return 100
        return int((self.reviewed_entities / self.total_entities) * 100)


# --- Sanity Check Rules ---

@dataclass(frozen=True)
class SanityCheckRule:
    """
    A deterministic validation rule based on document type.

    Defines minimum expected entity counts for a document type.
    If the detected entities don't meet these minimums, it signals
    a potential false negative problem.
    """

    rule_id: str
    document_type: DocumentTypeEnum
    severity: ValidationSeverity
    required_categories: Dict[PiiCategoryEnum, int]  # category → min count
    message_template: str

    def check(self, entity_counts: Dict[PiiCategoryEnum, int]) -> ValidationResult:
        """
        Validate entity counts against this rule.

        Args:
            entity_counts: Map of category → detected count.

        Returns:
            ValidationResult indicating pass/fail.
        """
        missing = []
        for category, min_count in self.required_categories.items():
            actual = entity_counts.get(category, 0)
            if actual < min_count:
                missing.append(f"{category.value} (expected >={min_count}, got {actual})")

        if missing:
            return ValidationResult(
                passed=False,
                severity=self.severity,
                rule_id=self.rule_id,
                message=self.message_template.format(missing=", ".join(missing)),
            )

        return ValidationResult(
            passed=True,
            severity=self.severity,
            rule_id=self.rule_id,
            message="OK",
        )


# Pre-defined sanity check rules per document type
SANITY_CHECK_RULES: List[SanityCheckRule] = [
    SanityCheckRule(
        rule_id="SC-001",
        document_type=DocumentTypeEnum.ESCRITURA,
        severity=ValidationSeverity.CRITICAL,
        required_categories={
            PiiCategoryEnum.PERSON_NAME: 1,
            PiiCategoryEnum.DNI_NIE: 1,
        },
        message_template=(
            "Una escritura notarial debe tener al menos un compareciente "
            "y un DNI detectados. Faltan: {missing}"
        ),
    ),
    SanityCheckRule(
        rule_id="SC-002",
        document_type=DocumentTypeEnum.SENTENCIA,
        severity=ValidationSeverity.WARNING,
        required_categories={
            PiiCategoryEnum.DATE: 1,
        },
        message_template=(
            "No se han detectado fechas en esta sentencia. "
            "Revise manualmente. Faltan: {missing}"
        ),
    ),
    SanityCheckRule(
        rule_id="SC-003",
        document_type=DocumentTypeEnum.FACTURA,
        severity=ValidationSeverity.WARNING,
        required_categories={
            PiiCategoryEnum.ORGANIZATION: 1,
        },
        message_template=(
            "Factura sin emisor (Organización) detectado. "
            "Faltan: {missing}"
        ),
    ),
    SanityCheckRule(
        rule_id="SC-004",
        document_type=DocumentTypeEnum.DENUNCIA,
        severity=ValidationSeverity.WARNING,
        required_categories={
            PiiCategoryEnum.PERSON_NAME: 1,
        },
        message_template=(
            "Una denuncia debería tener al menos una persona "
            "identificada. Faltan: {missing}"
        ),
    ),
]


class ExportValidator:
    """
    Validates whether a document is safe to export.

    Combines Safety Latch (review completeness) with Sanity Checks
    (minimum expected entities per document type).
    """

    def __init__(
        self,
        rules: Optional[List[SanityCheckRule]] = None,
    ) -> None:
        self._rules = rules or SANITY_CHECK_RULES

    def validate(
        self,
        document_type: DocumentTypeEnum,
        total_entities: int,
        reviewed_entities: int,
        pending_amber_red: int,
        entity_counts: Dict[PiiCategoryEnum, int],
    ) -> ExportValidation:
        """
        Validate document for export readiness.

        Args:
            document_type: Classified document type.
            total_entities: Total detected entities.
            reviewed_entities: Number of entities reviewed by human.
            pending_amber_red: Number of AMBER/RED entities not yet reviewed.
            entity_counts: Count per PII category.

        Returns:
            ExportValidation with overall pass/fail and details.
        """
        results: List[ValidationResult] = []

        # Safety Latch: All AMBER/RED entities must be reviewed
        latch_passed = pending_amber_red == 0
        results.append(
            ValidationResult(
                passed=latch_passed,
                severity=ValidationSeverity.CRITICAL,
                rule_id="LATCH-001",
                message=(
                    "OK" if latch_passed
                    else f"{pending_amber_red} entidades (ámbar/rojo) pendientes de revisión"
                ),
            )
        )

        # Sanity Checks: Apply rules for this document type
        applicable_rules = [
            r for r in self._rules if r.document_type == document_type
        ]
        for rule in applicable_rules:
            results.append(rule.check(entity_counts))

        # Can export only if no CRITICAL failures
        can_export = all(
            r.passed for r in results
            if r.severity == ValidationSeverity.CRITICAL
        )

        return ExportValidation(
            can_export=can_export,
            pending_reviews=pending_amber_red,
            total_entities=total_entities,
            reviewed_entities=reviewed_entities,
            validation_results=tuple(results),
        )
