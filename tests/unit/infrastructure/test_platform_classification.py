"""Tests that platform names are not misclassified as PERSON_NAME."""

import pytest

from contextsafe.infrastructure.nlp.composite_adapter import (
    PLATFORM_NAMES_BLOCKLIST,
)
from contextsafe.domain.shared.value_objects import PiiCategory
from contextsafe.domain.shared.value_objects.pii_category import PiiCategoryEnum
from contextsafe.domain.shared.value_objects.anonymization_level import (
    INTERMEDIATE,
    ADVANCED,
)


class TestPlatformBlocklist:
    """Platform names should never be classified as PERSON_NAME."""

    def test_whatsapp_in_blocklist(self):
        assert "whatsapp" in PLATFORM_NAMES_BLOCKLIST

    def test_telegram_in_blocklist(self):
        assert "telegram" in PLATFORM_NAMES_BLOCKLIST

    def test_common_platforms_in_blocklist(self):
        expected = {
            "whatsapp", "telegram", "signal", "instagram", "facebook",
            "twitter", "tiktok", "linkedin", "discord", "slack",
        }
        assert expected.issubset(PLATFORM_NAMES_BLOCKLIST)


class TestPlatformInAnonymizationLevels:
    """PLATFORM category should be included in anonymization levels."""

    def test_platform_in_intermediate(self):
        assert INTERMEDIATE.includes_category(PiiCategoryEnum.PLATFORM)

    def test_platform_in_advanced(self):
        assert ADVANCED.includes_category(PiiCategoryEnum.PLATFORM)
