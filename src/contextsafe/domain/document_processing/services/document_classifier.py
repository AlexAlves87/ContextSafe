"""
Document type classifier based on header keyword matching.

Classifies legal documents by scanning the first N characters for
distinctive patterns. Designed to be lightweight (0 dependencies,
<1ms latency) while achieving >95% accuracy on Spanish legal documents.

Traceability:
- Decision: ml/docs/reports/2026-02-04_2330_evaluacion_propuesta_embeddings_ragnr.md
- Justification: Regex/keyword approach recommended over embeddings (Section 5)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class DocumentTypeEnum(str, Enum):
    """Classification of legal document types."""

    SENTENCIA = "SENTENCIA"
    ESCRITURA = "ESCRITURA"
    FACTURA = "FACTURA"
    RECURSO = "RECURSO"
    DENUNCIA = "DENUNCIA"
    CONTRATO = "CONTRATO"
    GENERIC = "GENERIC"


# Patterns for each document type (applied to uppercased header text)
DOCUMENT_TYPE_PATTERNS: Dict[DocumentTypeEnum, List[str]] = {
    DocumentTypeEnum.SENTENCIA: [
        r"SENTENCIA",
        r"JUZGADO",
        r"TRIBUNAL",
        r"FALLO",
        r"MAGISTRAD[OA]",
        r"SALA\s+DE\s+LO",
        r"AUDIENCIA\s+PROVINCIAL",
        r"EN\s+NOMBRE\s+DEL\s+REY",
    ],
    DocumentTypeEnum.ESCRITURA: [
        r"ESCRITURA",
        r"NOTAR[IÍ]",
        r"PROTOCOLO",
        r"OTORGAMIENTO",
        r"FE\s+P[UÚ]BLICA",
        r"COMPARECE[N]?",
    ],
    DocumentTypeEnum.FACTURA: [
        r"FACTURA",
        r"BASE\s+IMPONIBLE",
        r"IVA",
        r"N[UÚ]MERO\s+DE\s+FACTURA",
        r"CONCEPTO\s+IMPORTE",
        r"TOTAL\s+FACTURA",
    ],
    DocumentTypeEnum.RECURSO: [
        r"RECURSO",
        r"APELACI[OÓ]N",
        r"CASACI[OÓ]N",
        r"SUPLICACI[OÓ]N",
        r"RECURRENTE",
    ],
    DocumentTypeEnum.DENUNCIA: [
        r"DENUNCIA",
        r"ATESTADO",
        r"DILIGENCIAS\s+PREVIAS",
        r"QUERELLA",
    ],
    DocumentTypeEnum.CONTRATO: [
        r"CONTRATO",
        r"CL[AÁ]USULA",
        r"PARTES\s+CONTRATANTES",
        r"ESTIPULACIONES",
    ],
}


@dataclass(frozen=True, slots=True)
class DocumentClassification:
    """Result of document type classification."""

    document_type: DocumentTypeEnum
    confidence: float  # 0.0-1.0 based on pattern match density
    matched_patterns: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_classified(self) -> bool:
        """True if a specific type was identified (not GENERIC)."""
        return self.document_type != DocumentTypeEnum.GENERIC


class DocumentTypeClassifier:
    """
    Classify legal document type from header text using keyword patterns.

    Scans the first `max_chars` characters of a document for distinctive
    keywords. Returns the best matching type with confidence score.
    """

    def __init__(self, max_chars: int = 500) -> None:
        self._max_chars = max_chars
        self._compiled_patterns: Dict[DocumentTypeEnum, List[re.Pattern[str]]] = {
            doc_type: [re.compile(p) for p in patterns]
            for doc_type, patterns in DOCUMENT_TYPE_PATTERNS.items()
        }

    def classify(self, text: str) -> DocumentClassification:
        """
        Classify document type from text content.

        Args:
            text: Full document text (only first max_chars are analyzed).

        Returns:
            DocumentClassification with type, confidence, and matched patterns.
        """
        header = text[: self._max_chars].upper()
        scores: Dict[DocumentTypeEnum, List[str]] = {}

        for doc_type, patterns in self._compiled_patterns.items():
            matched = [p.pattern for p in patterns if p.search(header)]
            if matched:
                scores[doc_type] = matched

        if not scores:
            return DocumentClassification(
                document_type=DocumentTypeEnum.GENERIC,
                confidence=0.0,
                matched_patterns=(),
            )

        # Best type = most pattern matches, weighted by total patterns available
        best_type = max(
            scores,
            key=lambda dt: len(scores[dt]) / len(self._compiled_patterns[dt]),
        )
        best_matches = scores[best_type]
        total_patterns = len(self._compiled_patterns[best_type])
        confidence = min(len(best_matches) / total_patterns, 1.0)

        return DocumentClassification(
            document_type=best_type,
            confidence=confidence,
            matched_patterns=tuple(best_matches),
        )

    def classify_with_fallback(
        self, text: str, metadata: Optional[Dict[str, str]] = None
    ) -> DocumentClassification:
        """
        Classify with optional metadata fallback.

        If text-based classification fails, checks filename extension
        or metadata hints.
        """
        result = self.classify(text)
        if result.is_classified:
            return result

        if metadata:
            filename = metadata.get("filename", "").upper()
            if "SENTENCIA" in filename:
                return DocumentClassification(
                    document_type=DocumentTypeEnum.SENTENCIA,
                    confidence=0.5,
                    matched_patterns=("filename_hint",),
                )
            if "ESCRITURA" in filename:
                return DocumentClassification(
                    document_type=DocumentTypeEnum.ESCRITURA,
                    confidence=0.5,
                    matched_patterns=("filename_hint",),
                )
            if "FACTURA" in filename:
                return DocumentClassification(
                    document_type=DocumentTypeEnum.FACTURA,
                    confidence=0.5,
                    matched_patterns=("filename_hint",),
                )

        return result
