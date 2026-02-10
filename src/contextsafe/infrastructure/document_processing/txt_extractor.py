"""
Plain text extractor.

Simple extractor for .txt files with encoding detection.

Traceability:
- Contract: CNT-T3-TXT-EXTRACTOR-001
- Port: ports.TextExtractor
"""

from __future__ import annotations

from contextsafe.application.ports import ExtractionResult, TextExtractor


class TxtExtractor(TextExtractor):
    """
    Plain text extractor with encoding detection.

    Supports common encodings (UTF-8, Latin-1, etc.).
    """

    def __init__(self, default_encoding: str = "utf-8") -> None:
        """
        Initialize the text extractor.

        Args:
            default_encoding: Default encoding to try first
        """
        self._default_encoding = default_encoding
        self._encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]

    async def extract(
        self,
        content: bytes,
        filename: str,
        ocr_fallback: bool = True,
    ) -> ExtractionResult:
        """
        Extract text from plain text content.

        Args:
            content: Raw text bytes
            filename: Original filename
            ocr_fallback: Ignored (not applicable for text)

        Returns:
            ExtractionResult with text content
        """
        text = ""
        encoding_used = self._default_encoding

        # Try different encodings
        for encoding in self._encodings:
            try:
                text = content.decode(encoding)
                encoding_used = encoding
                break
            except (UnicodeDecodeError, LookupError):
                continue

        # Fallback: try chardet for detection
        if not text:
            try:
                import chardet

                detected = chardet.detect(content)
                if detected["encoding"]:
                    text = content.decode(detected["encoding"])
                    encoding_used = detected["encoding"]
            except (ImportError, Exception):
                # Last resort: ignore errors
                text = content.decode("utf-8", errors="ignore")
                encoding_used = "utf-8 (fallback)"

        # Count lines as rough page estimate
        line_count = len(text.splitlines())
        page_count = max(1, line_count // 60)  # ~60 lines per page

        return ExtractionResult(
            text=text,
            format_detected="txt",
            page_count=page_count,
            has_tables=False,
            has_images=False,
            ocr_used=False,
            confidence=1.0,
            metadata={"encoding": encoding_used},
        )

    async def extract_from_path(
        self,
        path: str,
        ocr_fallback: bool = True,
    ) -> ExtractionResult:
        """
        Extract text from a text file.

        Args:
            path: Path to the text file
            ocr_fallback: Ignored (not applicable for text)

        Returns:
            ExtractionResult with text content
        """
        try:
            with open(path, "rb") as f:
                content = f.read()
            return await self.extract(content, path, ocr_fallback)
        except FileNotFoundError:
            return ExtractionResult(
                text="",
                format_detected="txt",
                confidence=0.0,
                metadata={"error": f"File not found: {path}"},
            )

    def supports_format(self, extension: str) -> bool:
        """Check if this extractor supports the format."""
        return extension.lower() in {".txt", ".text", ".md", ".csv"}
