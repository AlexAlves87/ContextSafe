# ContextSafe - Test Configuration
# ============================================
"""
Pytest fixtures and configuration for all test types.
"""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator, Generator

import pytest


# ============================================
# ASYNC EVENT LOOP
# ============================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# ============================================
# DATABASE FIXTURES
# ============================================

@pytest.fixture
async def test_db() -> AsyncGenerator[None, None]:
    """
    Create a test database with schema.

    NOTE: Implementation will be added in Phase 4 Step 2.
    """
    # Setup: Create in-memory database
    yield
    # Teardown: Clean up


# ============================================
# MOCK FIXTURES
# ============================================

@pytest.fixture
def mock_ner_service():
    """
    Mock NER service for unit tests.

    NOTE: Implementation will be added in Phase 4 Step 3.
    """
    pass


@pytest.fixture
def mock_llm_service():
    """
    Mock LLM service for unit tests.

    NOTE: Implementation will be added in Phase 4 Step 3.
    """
    pass


@pytest.fixture
def mock_ocr_service():
    """
    Mock OCR service for unit tests.

    NOTE: Implementation will be added in Phase 4 Step 3.
    """
    pass


# ============================================
# PBT STRATEGIES
# ============================================

# NOTE: Hypothesis strategies will be added in Phase 4 Step 3
# based on consolidated_standards.yaml pbt_strategies section
