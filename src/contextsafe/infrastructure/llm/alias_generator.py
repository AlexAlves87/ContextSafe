"""
Alias generator for PII anonymization.

Generates consistent, reversible aliases for detected PII entities.

Traceability:
- Contract: CNT-T3-ALIAS-GENERATOR-001
- Business Rule: BR-002 (Alias Consistency)
"""

from __future__ import annotations

import hashlib
import re

from contextsafe.domain.shared.value_objects import Alias, PiiCategory


# Alias patterns per category (from controlled_vocabulary.yaml)
ALIAS_PATTERNS: dict[str, str] = {
    "PERSON_NAME": "Persona_{counter}",
    "ORGANIZATION": "Org_{counter}",
    "ADDRESS": "Dir_{counter}",
    "DNI_NIE": "Doc_{counter}",
    "PASSPORT": "Pasaporte_{counter}",
    "PHONE": "Tel_{counter}",
    "EMAIL": "Email_{counter}",
    "BANK_ACCOUNT": "Cuenta_{counter}",
    "CREDIT_CARD": "Tarjeta_{counter}",
    "DATE": "Fecha_{counter}",
    "MEDICAL_RECORD": "Historial_{counter}",
    "LICENSE_PLATE": "Matricula_{counter}",
    "SOCIAL_SECURITY": "SS_{counter}",
}


class AliasGenerator:
    """
    Generates unique, deterministic aliases for PII entities.

    Features:
    - Consistent aliases across sessions (same input = same alias)
    - Category-specific prefixes
    - Collision-resistant within a project
    """

    def __init__(self, project_seed: str = "") -> None:
        """
        Initialize the alias generator.

        Args:
            project_seed: Project-specific seed for deterministic hashing
        """
        self._seed = project_seed
        self._counters: dict[str, int] = {}
        self._cache: dict[str, Alias] = {}

    def generate(
        self,
        category: PiiCategory,
        original_value: str,
        use_counter: bool = True,
    ) -> Alias:
        """
        Generate an alias for a PII value.

        Args:
            category: The PII category
            original_value: The original text value
            use_counter: Whether to use sequential counter

        Returns:
            A deterministic Alias for the value
        """
        # Check cache first
        cache_key = f"{category}:{original_value}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        category_str = str(category)
        pattern = ALIAS_PATTERNS.get(category_str, "{category}_{counter}")

        if use_counter:
            # Use sequential counter per category
            if category_str not in self._counters:
                self._counters[category_str] = 0
            self._counters[category_str] += 1
            counter = self._counters[category_str]
        else:
            # Use hash-based counter for determinism
            hash_input = f"{self._seed}:{category_str}:{original_value}"
            hash_value = hashlib.sha256(hash_input.encode()).hexdigest()[:6]
            counter = int(hash_value, 16) % 10000

        # Format alias
        alias_str = pattern.format(
            category=category_str,
            counter=str(counter).zfill(3),
        )

        # Create alias value object
        alias_result = Alias.create(alias_str)
        if alias_result.is_err():
            # Fallback to simple format
            alias_result = Alias.create(f"{category_str}_{counter:03d}")

        alias = alias_result.unwrap()
        self._cache[cache_key] = alias
        return alias

    def get_cached_alias(self, category: PiiCategory, original_value: str) -> Alias | None:
        """
        Get a previously generated alias from cache.

        Args:
            category: The PII category
            original_value: The original text value

        Returns:
            The cached Alias if exists, None otherwise
        """
        cache_key = f"{category}:{original_value}"
        return self._cache.get(cache_key)

    def reset(self) -> None:
        """Reset all counters and cache."""
        self._counters.clear()
        self._cache.clear()

    def export_mappings(self) -> dict[str, str]:
        """
        Export all generated mappings.

        Returns:
            Dict mapping original values to aliases
        """
        return {k: str(v) for k, v in self._cache.items()}

    def import_mappings(self, mappings: dict[str, str]) -> None:
        """
        Import previously generated mappings.

        Args:
            mappings: Dict from export_mappings()
        """
        for key, alias_str in mappings.items():
            alias_result = Alias.create(alias_str)
            if alias_result.is_ok():
                self._cache[key] = alias_result.unwrap()

                # Update counter if needed
                parts = key.split(":", 1)
                if len(parts) == 2:
                    category = parts[0]
                    # Extract counter from alias
                    match = re.search(r"_(\d+)$", alias_str)
                    if match:
                        counter = int(match.group(1))
                        self._counters[category] = max(self._counters.get(category, 0), counter)
