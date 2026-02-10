"""
Plain text document extractor with encoding detection.

Traceability:
- IMPLEMENTATION_PLAN.md Phase 4.3
"""

from __future__ import annotations

from typing import BinaryIO

from contextsafe.infrastructure.document_processing.extractors.base import (
    DocumentExtractor,
    ExtractionResult,
)


class TxtExtractor(DocumentExtractor):
    """
    Extract text from plain text files.

    Uses chardet for automatic encoding detection.
    Supports UTF-8, ISO-8859-1, Windows-1252, and others.
    """

    # Common encodings to try in order
    FALLBACK_ENCODINGS = [
        "utf-8",
        "utf-8-sig",  # UTF-8 with BOM
        "iso-8859-1",
        "windows-1252",
        "cp1252",
        "latin-1",
    ]

    @property
    def supported_extensions(self) -> list[str]:
        return ["txt", "text", "log", "md", "markdown", "csv", "tsv"]

    @property
    def format_name(self) -> str:
        return "Plain Text"

    def extract(self, file: BinaryIO, filename: str = "") -> ExtractionResult:
        """
        Extract text with automatic encoding detection.

        Uses chardet for detection with fallback to common encodings.
        """
        errors: list[str] = []
        metadata: dict[str, str] = {}

        # Read raw bytes
        raw_content = file.read()

        if not raw_content:
            return ExtractionResult(
                text="",
                page_count=0,
                errors=["Empty file"],
                format="txt",
            )

        # Detect encoding using chardet
        encoding = None
        confidence = 0.0

        try:
            import chardet

            detection = chardet.detect(raw_content)
            if detection and detection.get("encoding"):
                encoding = detection["encoding"]
                confidence = detection.get("confidence", 0.0)
                metadata["detected_encoding"] = encoding
                metadata["encoding_confidence"] = f"{confidence:.2f}"
        except Exception as e:
            errors.append(f"chardet error: {str(e)}")

        # Try detected encoding first, then fallbacks
        text = None
        used_encoding = None

        encodings_to_try = []
        if encoding and confidence > 0.5:
            encodings_to_try.append(encoding)
        encodings_to_try.extend(self.FALLBACK_ENCODINGS)

        for enc in encodings_to_try:
            try:
                text = raw_content.decode(enc)
                used_encoding = enc
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if text is None:
            # Last resort: decode with errors='replace'
            text = raw_content.decode("utf-8", errors="replace")
            used_encoding = "utf-8 (with replacements)"
            errors.append("Could not detect encoding, used UTF-8 with replacements")

        metadata["used_encoding"] = used_encoding or "unknown"

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Estimate page count (rough: ~3000 chars per page)
        page_count = max(1, len(text) // 3000 + 1)

        return ExtractionResult(
            text=text,
            page_count=page_count,
            metadata=metadata,
            errors=errors,
            format="txt",
        )
