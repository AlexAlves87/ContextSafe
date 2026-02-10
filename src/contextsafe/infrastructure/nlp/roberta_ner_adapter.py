"""
Spanish RoBERTa NER adapter for PII detection.

Supports two modes:
1. HuggingFace model (default): MMG/xlm-roberta-large-ner-spanish (4 labels)
2. Local fine-tuned model: legal_ner_v2 with 14 PII categories for Spanish legal

The local model (legal_ner_v2) was trained specifically for Spanish legal documents
and detects: PERSON, LOCATION, ORGANIZATION, DATE, DNI_NIE, IBAN, NSS, PHONE,
ADDRESS, POSTAL_CODE, LICENSE_PLATE, CADASTRAL_REF, ECLI, PROFESSIONAL_ID.

Traceability:
- Port: ports.NerService
- Model: MMG/xlm-roberta-large-ner-spanish OR local legal_ner_v2
- Architecture: Pre-Presidio transformer detection
- Labels: 4 (HF) or 14 (local v2)

OFFLINE MODE:
- Set HF_OFFLINE=1 or TRANSFORMERS_OFFLINE=1 environment variable
- Or use local_files_only=True when initializing
- For local models, set model_name to the full path
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from contextsafe.application.ports import NerDetection, NerService, ProgressCallback
from contextsafe.domain.shared.value_objects import (
    ConfidenceScore,
    PiiCategory,
    TextSpan,
)


# Check for offline mode via environment variables
OFFLINE_MODE = os.environ.get("HF_OFFLINE", "0") == "1" or \
               os.environ.get("TRANSFORMERS_OFFLINE", "0") == "1"

# Default cache directory for HuggingFace models
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "huggingface" / "hub"


logger = logging.getLogger(__name__)

# Label mapping from RoBERTa NER to ContextSafe PiiCategory
# Supports both HuggingFace generic model (4 labels) and local v2 model (14 labels)
LABEL_TO_CATEGORY: dict[str, str] = {
    # === HuggingFace generic model labels (MMG/xlm-roberta-large-ner-spanish) ===
    "PER": "PERSON_NAME",
    "ORG": "ORGANIZATION",
    "LOC": "LOCATION",
    # MISC is skipped - too generic for reliable PII detection

    # === Local v2 model labels (legal_ner_v2) ===
    "PERSON": "PERSON_NAME",
    "LOCATION": "LOCATION",
    "ORGANIZATION": "ORGANIZATION",
    "DATE": "DATE",
    "DNI_NIE": "DNI_NIE",
    "IBAN": "IBAN",
    "NSS": "SOCIAL_SECURITY",  # Maps to PiiCategory.SOCIAL_SECURITY
    "PHONE": "PHONE",
    "ADDRESS": "ADDRESS",
    "POSTAL_CODE": "POSTAL_CODE",
    "LICENSE_PLATE": "LICENSE_PLATE",
    "CADASTRAL_REF": "CADASTRAL_REF",
    "ECLI": "ECLI",
    "PROFESSIONAL_ID": "PROFESSIONAL_ID",
}

# Titles and honorifics that should NOT be detected as person names
HONORIFIC_TITLES = {
    "d", "d.", "dña", "dña.", "don", "doña",
    "sr", "sr.", "sra", "sra.", "señor", "señora",
    "excmo", "excmo.", "excma", "excma.",
    "ilmo", "ilmo.", "ilma", "ilma.",
    "dr", "dr.", "dra", "dra.",
    "lic", "lic.", "ing", "ing.",
}

# Public institutions that should NOT be anonymized (they are public, not PII)
# NOTE (Corrección #2): Removed local judicial organs (juzgado, audiencia provincial)
# to prevent triangulation in small judicial districts. Kept only national-level
# institutions where triangulation is not possible.
PUBLIC_INSTITUTIONS = {
    # National-level courts only (no triangulation risk)
    "tribunal supremo", "tribunal constitucional", "audiencia nacional",
    # Government bodies
    "ministerio fiscal", "ministerio de justicia", "gobierno",
    "administración", "administracion", "congreso", "senado",
    # Court offices (generic terms, not identifying)
    "gabinete técnico", "gabinete tecnico", "decanato",
    # Generic legal terms
    "consejo de administración", "consejo de administracion",
    "junta general", "asamblea",
}

# Minimum length for valid entity names
MIN_ENTITY_LENGTH = 3


class RobertaNerAdapter(NerService):
    """
    NER service using XLM-RoBERTa-large model for Spanish.

    Provides high-accuracy NER for Spanish text using MMG's
    xlm-roberta-large-ner-spanish model, one of the most popular and
    accurate Spanish NER models with 189k+ downloads.

    Features:
    - Lazy model loading
    - Automatic chunking for long documents (>512 tokens)
    - Overlap handling to avoid losing entities at chunk boundaries
    - High accuracy for formal Spanish text
    - Non-blocking inference via ThreadPoolExecutor
    """

    # RoBERTa max tokens is 512, but we use less to be safe with special tokens
    MAX_CHUNK_CHARS = 1500  # ~375 tokens approx (4 chars/token average)
    OVERLAP_CHARS = 200    # Overlap between chunks to catch boundary entities

    # Thread pool for non-blocking ML inference
    # Using max_workers=1 to avoid GPU memory issues with concurrent inference
    _executor: ThreadPoolExecutor | None = None

    def __init__(
        self,
        model_name: str = "MMG/xlm-roberta-large-ner-spanish",
        min_score: float = 0.85,
        device: str | int = -1,  # -1 = CPU, 0+ = GPU index
        local_files_only: bool | None = None,  # None = auto-detect
        cache_dir: str | Path | None = None,
    ) -> None:
        """
        Initialize the Spanish NER adapter.

        Args:
            model_name: HuggingFace model identifier
            min_score: Minimum confidence score to accept entities (0.85 recommended)
            device: Device to run inference on (-1 for CPU, 0+ for GPU)
            local_files_only: If True, only use cached models (no internet required)
                             If None, auto-detect based on HF_OFFLINE env var
            cache_dir: Custom cache directory for models
        """
        self._model_name = model_name
        self._min_score = min_score
        self._device = device
        self._pipeline: Any = None
        self._is_loaded = False
        self._load_error: str | None = None
        self._cache_dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
        # Auto-detect offline mode from environment
        self._local_files_only = local_files_only if local_files_only is not None else OFFLINE_MODE

    @classmethod
    def _get_executor(cls) -> ThreadPoolExecutor:
        """Get or create the shared thread pool executor."""
        if cls._executor is None:
            # Single worker to prevent GPU memory issues with concurrent inference
            cls._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="roberta_ner")
        return cls._executor

    def _is_local_path(self) -> bool:
        """Check if model_name is a local filesystem path."""
        model_path = Path(self._model_name)
        return model_path.is_absolute() or model_path.exists()

    def _check_model_cached(self) -> bool:
        """
        Check if the model is available in local cache or as local path.

        Returns:
            True if model files exist in cache or local path
        """
        # If it's a local path, check directly
        if self._is_local_path():
            local_path = Path(self._model_name)
            if local_path.exists() and (local_path / "config.json").exists():
                logger.info(f"Model found at local path: {local_path}")
                return True
            logger.warning(f"Local model path not valid: {local_path}")
            return False

        # HuggingFace cache structure: models--{org}--{model}/
        cache_model_name = self._model_name.replace("/", "--")
        model_cache_path = self._cache_dir / f"models--{cache_model_name}"

        if model_cache_path.exists():
            # Check for actual model files (not just empty directory)
            snapshots_dir = model_cache_path / "snapshots"
            if snapshots_dir.exists():
                # Check if any snapshot has model files
                for snapshot in snapshots_dir.iterdir():
                    if (snapshot / "config.json").exists():
                        logger.info(f"Model found in cache: {model_cache_path}")
                        return True

        logger.warning(f"Model not found in cache: {model_cache_path}")
        return False

    def _ensure_pipeline(self) -> Any:
        """
        Lazily load the transformers pipeline.

        Supports offline mode:
        - If HF_OFFLINE=1 or local_files_only=True, only uses cached models
        - If model not in cache and offline, raises clear error
        - If online, downloads model to cache for future offline use
        """
        if self._pipeline is not None:
            return self._pipeline

        # If already failed to load, don't retry
        if self._load_error:
            raise RuntimeError(self._load_error)

        try:
            from transformers import pipeline

            # Determine if we should try online or offline
            use_local_only = self._local_files_only

            # If offline mode and model not cached, fail early with clear message
            if use_local_only and not self._check_model_cached():
                error_msg = (
                    f"Model '{self._model_name}' not found in cache and offline mode is enabled. "
                    f"Cache directory: {self._cache_dir}\n"
                    f"To download the model:\n"
                    f"  1. Unset HF_OFFLINE=1 and TRANSFORMERS_OFFLINE=1\n"
                    f"  2. Run: python -c \"from transformers import pipeline; "
                    f"pipeline('ner', model='{self._model_name}')\"\n"
                    f"  3. The model will be cached for offline use"
                )
                self._load_error = error_msg
                raise RuntimeError(error_msg)

            is_local = self._is_local_path()
            logger.info(f"Loading RoBERTa NER model: {self._model_name}")
            logger.info(f"  Is local path: {is_local}")
            logger.info(f"  Local files only: {use_local_only}")
            logger.info(f"  Cache dir: {self._cache_dir}")

            # Try to load the pipeline
            # Note: local_files_only must be set via environment variable
            # because pipeline() doesn't accept it directly
            try:
                # Set environment variable for offline mode (only for HuggingFace models, not local paths)
                if use_local_only and not is_local:
                    os.environ["HF_HUB_OFFLINE"] = "1"
                    os.environ["TRANSFORMERS_OFFLINE"] = "1"

                self._pipeline = pipeline(
                    "ner",
                    model=self._model_name,
                    aggregation_strategy="simple",
                    device=self._device,
                )
                self._is_loaded = True
                logger.info("RoBERTa NER model loaded successfully")
                return self._pipeline

            except OSError as e:
                # Network error - try offline mode if model is cached
                if "resolve" in str(e).lower() or "connection" in str(e).lower():
                    logger.warning(f"Network error, trying offline mode: {e}")
                    if self._check_model_cached():
                        logger.info("Retrying with TRANSFORMERS_OFFLINE=1")
                        os.environ["HF_HUB_OFFLINE"] = "1"
                        os.environ["TRANSFORMERS_OFFLINE"] = "1"
                        self._pipeline = pipeline(
                            "ner",
                            model=self._model_name,
                            aggregation_strategy="simple",
                            device=self._device,
                        )
                        self._is_loaded = True
                        logger.info("RoBERTa NER model loaded from cache (offline mode)")
                        return self._pipeline
                    else:
                        error_msg = (
                            f"Cannot load model '{self._model_name}': Network unavailable "
                            f"and model not found in cache.\n"
                            f"The system will continue using regex-based detection only."
                        )
                        self._load_error = error_msg
                        raise RuntimeError(error_msg) from e
                raise

        except Exception as e:
            error_msg = f"Failed to load RoBERTa model: {e}"
            self._load_error = error_msg
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _map_label_to_category(self, label: str) -> str | None:
        """
        Map RoBERTa NER label to ContextSafe PiiCategory.

        RoBERTa labels: B-PER, I-PER, B-ORG, I-ORG, B-LOC, I-LOC, B-MISC, I-MISC
        With aggregation_strategy="simple", we get: PER, ORG, LOC, MISC

        Args:
            label: The NER label from the model

        Returns:
            PiiCategory string or None if not mappable
        """
        # Remove B-/I- prefix if present (shouldn't be with aggregation_strategy)
        clean_label = label.replace("B-", "").replace("I-", "")
        return LABEL_TO_CATEGORY.get(clean_label)

    async def detect_entities(
        self,
        text: str,
        categories: list[PiiCategory] | None = None,
        min_confidence: float = 0.5,
        progress_callback: ProgressCallback | None = None,
    ) -> list[NerDetection]:
        """
        Detect PII entities using BERT NER with automatic chunking.

        For long documents (>1500 chars), splits into overlapping chunks
        to handle BERT's 512 token limit.

        Args:
            text: The text to analyze
            categories: Optional filter for specific categories
            min_confidence: Minimum confidence threshold (overridden by min_score)
            progress_callback: Optional async callback for progress updates

        Returns:
            List of detected entities
        """
        if not text or not text.strip():
            return []

        # Use the stricter of min_confidence or configured min_score
        effective_min_score = max(min_confidence, self._min_score)

        try:
            # Report start
            if progress_callback:
                await progress_callback(0, 100, "Cargando modelo RoBERTa...")

            # For long texts, use chunking
            if len(text) > self.MAX_CHUNK_CHARS:
                return await self._detect_with_chunking(
                    text, categories, effective_min_score, progress_callback
                )

            # Short text - process directly with simulated progress
            if progress_callback:
                await progress_callback(10, 100, "Analizando texto con RoBERTa...")

            result = await self._detect_single_chunk(text, 0, categories, effective_min_score)

            if progress_callback:
                await progress_callback(90, 100, f"RoBERTa: procesando {len(result)} detecciones...")
                await progress_callback(100, 100, f"RoBERTa: {len(result)} entidades detectadas")

            return result

        except Exception as e:
            logger.error(f"[RobertaNerAdapter] Error during detection: {e}")
            return []

    async def _detect_with_chunking(
        self,
        text: str,
        categories: list[PiiCategory] | None,
        min_score: float,
        progress_callback: ProgressCallback | None = None,
    ) -> list[NerDetection]:
        """
        Process long text in overlapping chunks with intelligent splitting.

        Uses smart boundaries to avoid cutting words or entities:
        1. Paragraph boundaries (double newline)
        2. Sentence boundaries (period + space/newline)
        3. Single newlines
        4. Word boundaries (space) - NEVER cuts mid-word

        Args:
            text: Full text to process
            categories: Category filter
            min_score: Minimum confidence
            progress_callback: Optional async callback for progress updates

        Returns:
            Merged detections from all chunks
        """
        all_detections: list[NerDetection] = []
        chunk_size = self.MAX_CHUNK_CHARS
        overlap = self.OVERLAP_CHARS

        pos = 0
        chunk_num = 0
        total_chunks = (len(text) // (chunk_size - overlap)) + 1
        logger.info(f"Processing {len(text)} chars in ~{total_chunks} chunks")

        while pos < len(text):
            # Calculate ideal chunk end
            ideal_end = min(pos + chunk_size, len(text))

            # Find the best breaking point
            chunk_end = self._find_chunk_boundary(text, pos, ideal_end)

            chunk = text[pos:chunk_end]
            chunk_num += 1

            # Report progress before processing chunk (map to 0-90 range)
            if progress_callback:
                # Use percentage scale (0-100) for more granular updates
                pre_progress = int(10 + (80 * (chunk_num - 1) / total_chunks))
                await progress_callback(
                    pre_progress, 100,
                    f"RoBERTa: analizando chunk {chunk_num}/{total_chunks}..."
                )

            # Detect entities in this chunk (async to allow WebSocket updates)
            chunk_detections = await self._detect_single_chunk(
                chunk, pos, categories, min_score
            )
            all_detections.extend(chunk_detections)

            # Report progress after processing chunk
            if progress_callback:
                post_progress = int(10 + (80 * chunk_num / total_chunks))
                await progress_callback(
                    post_progress, 100,
                    f"RoBERTa: chunk {chunk_num}/{total_chunks} - {len(chunk_detections)} entidades"
                )

            # Move position for next chunk
            # Start overlap from a word boundary
            next_pos = chunk_end - overlap
            if next_pos > pos:
                # Find word boundary for overlap start
                while next_pos > pos and next_pos < len(text) and text[next_pos].isalnum():
                    next_pos -= 1
                pos = max(pos + 1, next_pos)  # Ensure we advance
            else:
                pos = chunk_end  # No overlap possible

            if pos >= len(text):
                break

        # Report completion
        if progress_callback:
            await progress_callback(
                95, 100,
                f"RoBERTa: deduplicando {len(all_detections)} detecciones..."
            )

        # Deduplicate (especially important for overlap regions)
        return self._deduplicate_overlapping(all_detections)

    def _find_chunk_boundary(self, text: str, start: int, ideal_end: int) -> int:
        """
        Find the best position to end a chunk without cutting words.

        Priorities (in order):
        1. Paragraph break (double newline)
        2. Sentence end (. or ! or ? followed by space/newline)
        3. Single newline
        4. Space (word boundary)

        Args:
            text: Full text
            start: Chunk start position
            ideal_end: Ideal end position

        Returns:
            Best end position that doesn't cut words
        """
        if ideal_end >= len(text):
            return len(text)

        chunk = text[start:ideal_end]
        min_chunk = len(chunk) // 2  # Don't make chunks smaller than half

        # Priority 1: Paragraph break
        para_break = chunk.rfind('\n\n')
        if para_break > min_chunk:
            return start + para_break + 2

        # Priority 2: Sentence end
        for sentence_end in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
            pos = chunk.rfind(sentence_end)
            if pos > min_chunk:
                return start + pos + len(sentence_end)

        # Priority 3: Single newline
        newline = chunk.rfind('\n')
        if newline > min_chunk:
            return start + newline + 1

        # Priority 4: Word boundary (space)
        space = chunk.rfind(' ')
        if space > min_chunk:
            return start + space + 1

        # Fallback: Find any non-alphanumeric boundary near the end
        search_start = max(0, len(chunk) - 50)
        for i in range(len(chunk) - 1, search_start, -1):
            if not chunk[i].isalnum():
                return start + i + 1

        # Last resort: use ideal_end (may cut word, but rare)
        return ideal_end

    async def _detect_single_chunk(
        self,
        chunk: str,
        offset: int,
        categories: list[PiiCategory] | None,
        min_score: float,
    ) -> list[NerDetection]:
        """
        Detect entities in a single text chunk.

        Uses run_in_executor to avoid blocking the asyncio event loop during
        ML inference. This allows WebSocket progress updates to continue
        while the model processes the chunk.

        Args:
            chunk: Text chunk to process
            offset: Character offset of this chunk in the original text
            categories: Category filter
            min_score: Minimum confidence

        Returns:
            List of detections with positions adjusted by offset
        """
        pipe = self._ensure_pipeline()

        # Run inference in thread pool to avoid blocking event loop
        # This allows WebSocket updates to be sent during processing
        loop = asyncio.get_running_loop()
        raw_entities = await loop.run_in_executor(
            self._get_executor(),
            pipe,
            chunk,
        )

        detections: list[NerDetection] = []

        for entity in raw_entities:
            # Filter by score - convert numpy.float32 to Python float for Pydantic
            score = float(entity.get("score", 0.0))
            if score < min_score:
                continue

            # Map label to category
            label = entity.get("entity_group", entity.get("entity", ""))
            category_str = self._map_label_to_category(label)
            if not category_str:
                # DEBUG: Log unmapped labels
                print(f"[ROBERTA-DEBUG] Unmapped label: '{label}' for text: '{entity.get('word', '')[:30]}'")
                continue

            # Create PiiCategory
            category_result = PiiCategory.from_string(category_str)
            if category_result.is_err():
                continue
            category = category_result.unwrap()

            # Filter by requested categories
            if categories and category not in categories:
                continue

            # Extract text and positions (relative to chunk)
            entity_text = entity.get("word", "")
            local_start = entity.get("start", 0)
            local_end = entity.get("end", 0)

            # Get the raw text from the chunk
            raw_text = chunk[local_start:local_end]

            # Clean up tokenization artifacts and title remnants
            cleaned_text = self._clean_entity_text(
                entity_text, chunk, local_start, local_end
            )

            if not cleaned_text or local_start >= local_end:
                continue

            # Adjust start position if we cleaned leading chars
            adjusted_start = local_start
            if raw_text != cleaned_text and cleaned_text in raw_text:
                # Find where the cleaned text starts in the raw text
                offset_in_raw = raw_text.find(cleaned_text)
                if offset_in_raw > 0:
                    adjusted_start = local_start + offset_in_raw
                    local_end = adjusted_start + len(cleaned_text)

            # Use cleaned text for validation
            actual_text = cleaned_text

            # === VALIDATION FILTERS ===

            # Skip entities that are too short
            if len(actual_text) < MIN_ENTITY_LENGTH:
                continue

            # Skip honorific titles (not PII by themselves)
            if actual_text.lower().strip(".") in HONORIFIC_TITLES:
                continue

            # Skip public institutions (not PII)
            if self._is_public_institution(actual_text):
                continue

            # Skip fragmented entities (partial words)
            if self._is_fragmented_entity(actual_text, chunk, adjusted_start, local_end):
                continue

            # Adjust positions to global offset
            global_start = offset + adjusted_start
            global_end = offset + local_end

            # Create TextSpan with global positions
            span_result = TextSpan.create(global_start, global_end, actual_text)
            if span_result.is_err():
                continue

            # Create ConfidenceScore
            conf_result = ConfidenceScore.create(score)
            if conf_result.is_err():
                continue

            # DEBUG: Log detected entities
            print(f"[ROBERTA-DEBUG] Detected: label='{label}' -> category={category.value} text='{actual_text[:40]}' score={score:.3f}")
            detections.append(
                NerDetection(
                    category=category,
                    value=actual_text,
                    span=span_result.unwrap(),
                    confidence=conf_result.unwrap(),
                    source="roberta",
                )
            )

        return detections

    def _clean_entity_text(
        self, entity_text: str, original_text: str, start: int, end: int
    ) -> str:
        """
        Clean tokenization artifacts from entity text.

        RoBERTa tokenizer may add special characters or spacing issues.
        Also handles malformed entities like "MARTORELL\n\nD" where the model
        incorrectly grouped a location with trailing garbage.
        """
        # Remove leading/trailing special chars from tokenization
        cleaned = entity_text.strip()

        # Handle subword tokens (## prefix from BERT-style tokenization)
        cleaned = cleaned.replace("##", "")

        # Remove leading special characters that aren't part of the word
        while cleaned and cleaned[0] in "▁Ġ":  # Common subword markers
            cleaned = cleaned[1:]

        # Remove leading title remnants (ª, º, .)
        while cleaned and cleaned[0] in "ªº.":
            cleaned = cleaned[1:].strip()

        # === FIX: Handle newlines and trailing garbage ===
        # Pattern: "MARTORELL\n\nD" -> "MARTORELL"
        # If entity contains newline, take only the first "word" before newlines
        if '\n' in cleaned:
            # Split by newlines and take the first non-empty part
            parts = cleaned.split('\n')
            first_part = parts[0].strip()
            if first_part and len(first_part) >= MIN_ENTITY_LENGTH:
                cleaned = first_part
            else:
                # Entity is garbage after cleanup
                return ""

        # Remove trailing single letters (often title remnants like "D" for "Don")
        # Pattern: "García D" -> "García"
        cleaned = re.sub(r'\s+[A-ZÁÉÍÓÚÑ]\.?$', '', cleaned).strip()

        # If we have the original text positions, prefer that
        if 0 <= start < end <= len(original_text):
            original = original_text[start:end]
            # Clean original too
            original_clean = original.strip()

            # Apply same newline fix to original
            if '\n' in original_clean:
                parts = original_clean.split('\n')
                first_part = parts[0].strip()
                if first_part and len(first_part) >= MIN_ENTITY_LENGTH:
                    original_clean = first_part
                else:
                    return ""

            while original_clean and original_clean[0] in "ªº.":
                original_clean = original_clean[1:].strip()

            # Remove trailing single letters from original too
            original_clean = re.sub(r'\s+[A-ZÁÉÍÓÚÑ]\.?$', '', original_clean).strip()

            # If similar enough, use original
            if original_clean.lower() == cleaned.lower():
                return original_clean

        return cleaned

    def _deduplicate_overlapping(
        self, detections: list[NerDetection]
    ) -> list[NerDetection]:
        """
        Remove overlapping detections, keeping the highest confidence one.

        Args:
            detections: List of detections, possibly with overlaps

        Returns:
            Deduplicated list of detections
        """
        if not detections:
            return []

        # Sort by start position, then by confidence (descending)
        sorted_detections = sorted(
            detections,
            key=lambda d: (d.span.start, -d.confidence.value),
        )

        result: list[NerDetection] = []
        for detection in sorted_detections:
            # Check if this overlaps with any kept detection
            overlaps = False
            for kept in result:
                if detection.span.overlaps(kept.span):
                    overlaps = True
                    break

            if not overlaps:
                result.append(detection)

        return result

    def _is_public_institution(self, text: str) -> bool:
        """
        Check if the text is a public institution (should not be anonymized).

        Args:
            text: Entity text to check

        Returns:
            True if it's a public institution
        """
        text_lower = text.lower().strip()

        # Check exact match
        if text_lower in PUBLIC_INSTITUTIONS:
            return True

        # Check if text contains a public institution name
        for institution in PUBLIC_INSTITUTIONS:
            if institution in text_lower:
                return True

        return False

    def _is_fragmented_entity(
        self, text: str, chunk: str, start: int, end: int
    ) -> bool:
        """
        Check if the entity appears to be a fragment (cut by chunking).

        Fragments are detected by:
        - Starting with lowercase (likely mid-word)
        - Being very short and at chunk boundary
        - Not being a complete word

        Args:
            text: Entity text
            chunk: Full chunk text
            start: Start position in chunk
            end: End position in chunk

        Returns:
            True if entity appears fragmented
        """
        text = text.strip()

        # Skip check for entities starting with title markers (they were cleaned)
        if text and text[0] in "ªº":
            return False

        # Very short entities at boundaries are suspicious
        if len(text) <= 3:
            # At start of chunk and starts lowercase
            if start < 5 and text and text[0].islower():
                return True
            # At end of chunk and starts lowercase
            if end > len(chunk) - 5 and text and text[0].islower():
                return True

        # Check if we're in the middle of a word
        # (previous char is alphanumeric, but not a title marker)
        if start > 0:
            prev_char = chunk[start - 1]
            # Allow if previous char is a title marker or punctuation
            if prev_char.isalnum() and prev_char not in "ªº":
                return True

        # Check if word continues after (but allow for punctuation)
        if end < len(chunk):
            next_char = chunk[end]
            if next_char.isalnum():
                return True

        return False

    async def is_available(self) -> bool:
        """
        Check if the RoBERTa model can be loaded.

        Handles offline mode gracefully:
        - If already loaded, returns True
        - If already failed, returns False without retrying
        - If model cached and offline, still returns True

        Returns:
            True if model is available, False otherwise
        """
        try:
            # Try to import transformers
            import transformers  # noqa: F401

            # If already loaded, we're good
            if self._is_loaded:
                return True

            # If already failed to load, don't retry (prevents repeated timeouts)
            if self._load_error:
                logger.debug(f"RoBERTa unavailable (previous error): {self._load_error}")
                return False

            # Try to load the model
            self._ensure_pipeline()
            return True

        except Exception as e:
            logger.warning(f"RoBERTa NER not available: {e}")
            return False

    async def get_model_info(self) -> dict:
        """
        Get information about the RoBERTa model configuration.

        Returns:
            Dict with model details and status
        """
        available = await self.is_available()
        model_cached = self._check_model_cached()

        return {
            "type": "roberta_ner",
            "model": self._model_name,
            "is_available": available,
            "is_loaded": self._is_loaded,
            "is_cached": model_cached,
            "offline_mode": self._local_files_only,
            "cache_dir": str(self._cache_dir),
            "load_error": self._load_error,
            "min_score": self._min_score,
            "device": "CPU" if self._device == -1 else f"GPU:{self._device}",
            "architecture": "pre-presidio",
            "label_mapping": LABEL_TO_CATEGORY,
            "tip": (
                "To cache model for offline use, run: "
                f"python -c \"from transformers import pipeline; "
                f"pipeline('ner', model='{self._model_name}')\""
            ) if not model_cached else None,
        }
