"""
LlamaCpp adapter for NER service.

Uses llama.cpp for local LLM-based named entity recognition.

Traceability:
- Contract: CNT-T3-LLAMACPP-ADAPTER-001
- Port: ports.NerService
"""

from __future__ import annotations

import json
import re
from typing import Any

from contextsafe.application.ports import NerDetection, NerService
from contextsafe.domain.shared.value_objects import (
    ConfidenceScore,
    PiiCategory,
    TextSpan,
)
from contextsafe.infrastructure.llm.llm_config import LLMConfig


# NER prompt template for entity extraction
NER_PROMPT_TEMPLATE = """<|system|>
You are a Named Entity Recognition (NER) system specialized in detecting Personal Identifiable Information (PII) in Spanish and English text.

Extract ALL PII entities from the given text. For each entity found, output a JSON object with:
- "category": The PII category (one of: PERSON_NAME, ORGANIZATION, ADDRESS, DNI_NIE, PASSPORT, PHONE, EMAIL, BANK_ACCOUNT, CREDIT_CARD, DATE, MEDICAL_RECORD, LICENSE_PLATE, SOCIAL_SECURITY)
- "value": The exact text of the entity
- "start": Start character position in text (0-indexed)
- "end": End character position in text (exclusive)
- "confidence": Confidence score between 0.0 and 1.0

Output ONLY a valid JSON array of entities. No additional text.
</|system|>

<|user|>
Extract PII entities from the following text:

{text}
</|user|>

<|assistant|>
"""


class LlamaCppNerAdapter(NerService):
    """
    NER service using llama.cpp for local inference.

    Provides LLM-based NER for PII detection without cloud dependencies.
    """

    def __init__(self, config: LLMConfig) -> None:
        """
        Initialize the LlamaCpp NER adapter.

        Args:
            config: LLM configuration
        """
        self._config = config
        self._model: Any = None
        self._is_loaded = False

    async def _ensure_loaded(self) -> None:
        """Ensure the model is loaded."""
        if self._is_loaded:
            return

        try:
            from llama_cpp import Llama

            self._model = Llama(
                model_path=str(self._config.model_path),
                n_ctx=self._config.context_length,
                n_threads=self._config.n_threads,
                n_gpu_layers=self._config.n_gpu_layers,
                verbose=False,
            )
            self._is_loaded = True
        except ImportError:
            raise RuntimeError("llama-cpp-python not installed")
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")

    async def detect_entities(
        self,
        text: str,
        categories: list[PiiCategory] | None = None,
        min_confidence: float = 0.5,
    ) -> list[NerDetection]:
        """
        Detect PII entities in text using LLM.

        Args:
            text: The text to analyze
            categories: Optional filter for specific categories
            min_confidence: Minimum confidence threshold

        Returns:
            List of detected entities
        """
        await self._ensure_loaded()

        if not text or not text.strip():
            return []

        # Truncate text if too long
        max_input_length = self._config.context_length - 1024
        if len(text) > max_input_length:
            text = text[:max_input_length]

        # Generate NER output
        prompt = NER_PROMPT_TEMPLATE.format(text=text)

        try:
            output = self._model(
                prompt,
                max_tokens=self._config.max_tokens,
                temperature=self._config.temperature,
                top_p=self._config.top_p,
                repeat_penalty=self._config.repeat_penalty,
                stop=["</|assistant|>", "\n\n\n"],
            )

            response_text = output["choices"][0]["text"].strip()
            entities = self._parse_response(response_text, text)

            # Filter by category if specified
            if categories:
                category_strs = {str(c) for c in categories}
                entities = [e for e in entities if str(e.category) in category_strs]

            # Filter by confidence
            entities = [e for e in entities if e.confidence.value >= min_confidence]

            return entities

        except Exception as e:
            # Log error but don't crash
            import logging

            logging.warning(f"LLM NER failed: {e}")
            return []

    def _parse_response(self, response: str, original_text: str) -> list[NerDetection]:
        """
        Parse LLM response into NerDetection objects.

        Args:
            response: The LLM output
            original_text: The original text for validation

        Returns:
            List of NerDetection objects
        """
        try:
            # Try to extract JSON array from response
            json_match = re.search(r"\[.*\]", response, re.DOTALL)
            if not json_match:
                return []

            entities_data = json.loads(json_match.group())
            detections = []

            for entity in entities_data:
                if not isinstance(entity, dict):
                    continue

                try:
                    category = PiiCategory.from_string(entity.get("category", ""))
                    if category.is_err():
                        continue

                    value = entity.get("value", "")
                    start = int(entity.get("start", 0))
                    end = int(entity.get("end", 0))
                    confidence = float(entity.get("confidence", 0.5))

                    # Validate span
                    if start < 0 or end <= start or end > len(original_text):
                        # Try to find the value in text
                        idx = original_text.find(value)
                        if idx >= 0:
                            start = idx
                            end = idx + len(value)
                        else:
                            continue

                    span_result = TextSpan.create(start, end, value)
                    if span_result.is_err():
                        continue

                    conf_result = ConfidenceScore.create(confidence)
                    if conf_result.is_err():
                        continue

                    detections.append(
                        NerDetection(
                            category=category.unwrap(),
                            value=value,
                            span=span_result.unwrap(),
                            confidence=conf_result.unwrap(),
                        )
                    )
                except (ValueError, TypeError):
                    continue

            return detections

        except json.JSONDecodeError:
            return []

    async def is_available(self) -> bool:
        """Check if the model is loaded and ready."""
        try:
            await self._ensure_loaded()
            return self._is_loaded
        except Exception:
            return False

    async def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        return {
            "type": "llama.cpp",
            "model_path": str(self._config.model_path),
            "compute_mode": str(self._config.compute_mode),
            "context_length": self._config.context_length,
            "is_loaded": self._is_loaded,
        }

    async def close(self) -> None:
        """Unload the model and free resources."""
        if self._model is not None:
            del self._model
            self._model = None
            self._is_loaded = False
