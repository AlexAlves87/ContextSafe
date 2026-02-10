"""
TextPreprocessor ports.

Abstract interfaces for text preprocessing before NER detection.

Traceability:
- Design: docs/plans/2026-02-01-text-preprocessing-design.md
- Bounded Context: BC-001 (DocumentProcessing), BC-002 (EntityDetection)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass(frozen=True, slots=True)
class OffsetMapping:
    """
    Mapa bidireccional: texto normalizado <-> texto fuente.

    Permite traducir posiciones (spans) detectadas en texto normalizado
    de vuelta al texto original para preservar auditabilidad.

    Invariante: len(char_map) == len(normalized_text)
    """

    source_text: str
    normalized_text: str
    char_map: Tuple[int, ...] = field(default_factory=tuple)
    """char_map[i] = posición en source_text del carácter i del normalized."""

    def to_original_span(self, norm_start: int, norm_end: int) -> Tuple[int, int]:
        """
        Traduce span del texto normalizado al texto original.

        CONTRATO: SIEMPRE retorna un span válido (total function).

        COMPORTAMIENTO DE FALLBACK:
        - Si el span exacto no es mapeable, EXPANDE al contexto más cercano
        - Esto puede SOBRE-INCLUIR caracteres en el span original
        - Es deliberado: preferimos cobertura completa a precisión estricta

        GARANTÍAS:
        - orig_start < orig_end (span no vacío)
        - 0 <= orig_start < len(source_text)
        - orig_end <= len(source_text)

        TRADE-OFF ACEPTADO:
        - El código de reemplazo debe hacer strip() si es necesario

        Args:
            norm_start: Posición inicial en texto normalizado
            norm_end: Posición final en texto normalizado

        Returns:
            Tupla (orig_start, orig_end) en texto original
        """
        # Si no hay char_map, retornar span sin cambio
        if not self.char_map:
            return (norm_start, norm_end)

        # Clamp a rangos válidos
        norm_start = max(0, min(norm_start, len(self.char_map) - 1))
        norm_end = max(norm_start, min(norm_end, len(self.char_map)))

        # Buscar primera posición válida desde start
        orig_start = self.char_map[norm_start]
        search_start = norm_start
        while orig_start == -1 and search_start < norm_end:
            search_start += 1
            if search_start < len(self.char_map):
                orig_start = self.char_map[search_start]

        # Fallback si todo es -1
        if orig_start == -1:
            orig_start = 0

        # Buscar última posición válida antes de end
        if norm_end > 0 and norm_end <= len(self.char_map):
            orig_end = self.char_map[norm_end - 1] + 1
        else:
            orig_end = orig_start + 1

        # Asegurar span válido
        orig_end = max(orig_start + 1, orig_end)
        orig_end = min(orig_end, len(self.source_text))

        return (orig_start, orig_end)

    @classmethod
    def identity(cls, text: str) -> "OffsetMapping":
        """Crear mapping identidad (sin cambios)."""
        return cls(
            source_text=text,
            normalized_text=text,
            char_map=tuple(range(len(text))),
        )


class IngestPreprocessor(ABC):
    """
    Fase 1: Normalización permanente (se guarda en BD).

    Operaciones que NO cambian semántica ni offsets lógicos:
    - Unicode NFKC normalization
    - Line endings normalization
    - NBSP -> space
    - Control chars removal
    """

    @abstractmethod
    def preprocess(self, raw_text: str) -> str:
        """
        Normalizar texto para almacenamiento permanente.

        Args:
            raw_text: Texto crudo del extractor

        Returns:
            Texto normalizado (fase 1)
        """
        ...


class DetectionPreprocessor(ABC):
    """
    Fase 2: Normalización temporal para NER.

    Operaciones que SÍ pueden cambiar longitud (con offset tracking):
    - Colapsar espacios múltiples
    - Normalizar comillas/guiones tipográficos
    - Fix OCR letter spacing
    - Fix OCR linebreaks
    """

    @abstractmethod
    def preprocess(self, text: str) -> OffsetMapping:
        """
        Normalizar texto para detección NER.

        Args:
            text: Texto (ya normalizado fase 1)

        Returns:
            OffsetMapping con texto normalizado y mapa de offsets
        """
        ...
