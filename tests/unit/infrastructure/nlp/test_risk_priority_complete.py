"""
Test that all PiiCategory values have a non-zero priority in RISK_PRIORITY.

This prevents nested entity leaks where a category with priority 0
would always lose to any overlapping span.
"""
from contextsafe.domain.shared.value_objects.pii_category import PiiCategoryEnum
from contextsafe.infrastructure.nlp.merge.voting import RISK_PRIORITY


def test_all_pii_categories_have_risk_priority():
    """Every PiiCategory must have a defined risk priority > 0."""
    for cat in PiiCategoryEnum:
        assert cat.value in RISK_PRIORITY, f"Missing RISK_PRIORITY for {cat.value}"
        assert RISK_PRIORITY[cat.value] > 0, f"RISK_PRIORITY for {cat.value} must be > 0"
