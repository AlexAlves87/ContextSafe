"""
Date Shifter Service.

Preserves temporal intervals by applying a uniform delta to all dates
in a project. This maintains document chronology while anonymizing
actual dates.

Algorithm:
    New_Date = Original_Date + Delta

Where Delta is constant per project (calculated once, deterministic).

Traceability:
- Bug Fix: Corrección #3 - Fechas aleatorias sin date shifting
- Audit: PLAN_CORRECCION_AUDITORIA.md

Example:
    If delta = +730 days (2 years):
    - "13 de enero de 2026" → "13 de enero de 2028"
    - "12 de octubre de 2025" → "12 de octubre de 2027"
    Interval between dates is PRESERVED.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional


@dataclass
class DateShiftConfig:
    """Configuration for date shifting."""
    min_shift_days: int = -1825  # -5 years
    max_shift_days: int = 1825   # +5 years
    preserve_day_of_week: bool = False
    preserve_month: bool = False


# Spanish month names
MONTHS_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]


class DateShifter:
    """
    Uniform date shifting service per project.

    Guarantees:
    1. All dates in a project use the same delta
    2. Temporal intervals are preserved exactly
    3. Delta is deterministic per project_id (reproducible)
    """

    def __init__(self) -> None:
        # Delta per project: {project_id: timedelta}
        self._deltas: Dict[str, timedelta] = {}
        # Cache of original dates to shifted dates per project
        self._cache: Dict[str, Dict[datetime, datetime]] = {}

    def _get_or_create_delta(
        self,
        project_id: str,
        config: DateShiftConfig,
    ) -> timedelta:
        """
        Get or create the delta for a project.

        Delta is deterministic based on project_id for reproducibility.
        The same project_id always produces the same delta.
        """
        if project_id not in self._deltas:
            # Use project_id as seed for reproducibility
            seed = hash(project_id) % (2**32)
            rng = random.Random(seed)

            days = rng.randint(config.min_shift_days, config.max_shift_days)
            self._deltas[project_id] = timedelta(days=days)
            self._cache[project_id] = {}

        return self._deltas[project_id]

    def shift_date(
        self,
        original: datetime,
        project_id: str,
        config: Optional[DateShiftConfig] = None,
    ) -> datetime:
        """
        Apply date shifting to a date.

        Args:
            original: Original date
            project_id: Project ID (determines the delta)
            config: Optional configuration

        Returns:
            Shifted date (original + delta)
        """
        config = config or DateShiftConfig()

        # Get project delta
        delta = self._get_or_create_delta(project_id, config)

        # Check cache
        project_cache = self._cache.get(project_id, {})
        if original in project_cache:
            return project_cache[original]

        # Apply shift
        shifted = original + delta

        # Optional adjustments
        if config.preserve_day_of_week:
            # Adjust to the same day of the week
            day_diff = (original.weekday() - shifted.weekday()) % 7
            if day_diff > 3:
                day_diff -= 7
            shifted += timedelta(days=day_diff)

        if config.preserve_month:
            # Keep the same month (only shift years)
            try:
                shifted = shifted.replace(month=original.month, day=original.day)
            except ValueError:
                # Invalid day for month (e.g., 31 Feb)
                shifted = shifted.replace(month=original.month, day=28)

        # Cache
        project_cache[original] = shifted
        self._cache[project_id] = project_cache

        return shifted

    def format_shifted_date(
        self,
        original_str: str,
        project_id: str,
        original_format: str = "auto",
    ) -> str:
        """
        Parse, apply shift, and format date preserving original format.

        Preserves input format:
        - "17 de julio de 2025" → "22 de agosto de 2030" (if delta = +5 years)
        - "17/07/2025" → "22/08/2030"

        Args:
            original_str: Original date string
            project_id: Project ID
            original_format: Format hint ("auto" for auto-detection)

        Returns:
            Shifted date in the same format as original
        """
        parsed = self._parse_spanish_date(original_str)
        if not parsed:
            # Cannot parse - return original unchanged
            return original_str

        shifted = self.shift_date(parsed, project_id)

        # Format like original
        return self._format_like_original(shifted, original_str)

    def _parse_spanish_date(self, date_str: str) -> Optional[datetime]:
        """Parse Spanish date strings into datetime objects."""
        date_str = date_str.strip()
        date_lower = date_str.lower()

        # Format: "15 de marzo de 2024"
        match = re.match(
            r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})",
            date_lower,
            re.IGNORECASE
        )
        if match:
            day, month_name, year = match.groups()
            try:
                month_idx = MONTHS_ES.index(month_name.lower()) + 1
                return datetime(int(year), month_idx, int(day))
            except (ValueError, IndexError):
                pass

        # Format: "15/03/2024" or "15-03-2024"
        match = re.match(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", date_str)
        if match:
            day, month, year = match.groups()
            try:
                return datetime(int(year), int(month), int(day))
            except ValueError:
                pass

        # Format: "2024-03-15" or "2024/03/15" (ISO)
        match = re.match(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", date_str)
        if match:
            year, month, day = match.groups()
            try:
                return datetime(int(year), int(month), int(day))
            except ValueError:
                pass

        return None

    def _format_like_original(self, date: datetime, original_str: str) -> str:
        """Format date in the same style as the original string."""
        original_lower = original_str.lower()

        # Written format: "17 de julio de 2025"
        if " de " in original_lower:
            return f"{date.day} de {MONTHS_ES[date.month - 1]} de {date.year}"

        # Format with slashes: "17/07/2025"
        if "/" in original_str:
            # Detect if original was DD/MM/YYYY or MM/DD/YYYY
            # Spanish uses DD/MM/YYYY
            return f"{date.day:02d}/{date.month:02d}/{date.year}"

        # Format with dashes: "17-07-2025"
        if "-" in original_str and not original_str.startswith("20"):
            return f"{date.day:02d}-{date.month:02d}-{date.year}"

        # ISO format: "2025-07-17"
        if original_str.startswith("20") and "-" in original_str:
            return f"{date.year}-{date.month:02d}-{date.day:02d}"

        # Fallback: Spanish standard format
        return f"{date.day:02d}/{date.month:02d}/{date.year}"

    def get_project_delta_days(self, project_id: str) -> Optional[int]:
        """Get the delta in days for a project (for glossary info)."""
        delta = self._deltas.get(project_id)
        return delta.days if delta else None

    def clear_project(self, project_id: str) -> None:
        """Clear delta and cache for a project."""
        self._deltas.pop(project_id, None)
        self._cache.pop(project_id, None)


# Global singleton
_date_shifter: Optional[DateShifter] = None


def get_date_shifter() -> DateShifter:
    """Get the global date shifter instance."""
    global _date_shifter
    if _date_shifter is None:
        _date_shifter = DateShifter()
    return _date_shifter
