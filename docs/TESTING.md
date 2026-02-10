# ContextSafe - Testing Guide

This guide covers the testing strategy, tools, and procedures for ContextSafe.

## Overview

ContextSafe employs a comprehensive testing strategy with multiple test tiers:

| Tier | Type | Framework | Purpose |
|------|------|-----------|---------|
| 1 | Unit Tests | pytest | Domain and application layer correctness |
| 2 | Property-Based Tests | Hypothesis | Invariant verification across random inputs |
| 3 | Contract Tests | icontract | Interface compliance verification |
| 4 | Integration Tests | pytest + testcontainers | Component interaction testing |
| 5 | E2E Tests | pytest + httpx | Full system flow testing |

## Quick Start

```bash
# Install dependencies (including test dependencies)
pip install -e ".[dev]"

# Run all tests
make test

# Run specific test tiers
make test-unit        # Unit tests only
make test-pbt         # Property-based tests only
make test-integration # Integration tests only
```

## Test Organization

```
tests/
├── unit/                    # Unit tests
│   ├── domain/              # Domain layer tests
│   │   ├── test_value_objects.py
│   │   ├── test_entities.py
│   │   ├── test_aggregates.py
│   │   ├── test_events.py
│   │   └── test_result.py
│   └── application/         # Application layer tests
│       └── test_use_cases.py
├── pbt/                     # Property-based tests
│   ├── conftest.py          # Hypothesis generators
│   ├── test_result_type.py  # Result monad laws
│   ├── test_value_objects.py
│   ├── test_aggregates.py
│   ├── test_use_cases.py
│   └── test_anonymization.py # Critical BR-004 tests
├── integration/             # Integration tests
│   └── test_api.py
├── contract/                # Contract compliance tests
│   └── test_ports.py
├── traceability/            # Function mapping audits
│   └── test_F_*.yaml
└── conftest.py              # Shared fixtures
```

## Unit Tests

Unit tests verify individual components in isolation using mocks for dependencies.

### Running Unit Tests

```bash
# All unit tests
pytest tests/unit/ -v

# Domain layer only
pytest tests/unit/domain/ -v

# Application layer only
pytest tests/unit/application/ -v

# With coverage
pytest tests/unit/ --cov=src/contextsafe --cov-report=html
```

### Writing Unit Tests

```python
import pytest
from contextsafe.domain.shared.value_objects import ConfidenceScore
from contextsafe.domain.shared.result import Ok, Err

class TestConfidenceScore:
    """Tests for ConfidenceScore value object."""

    def test_create_valid_score(self):
        """Valid scores between 0.0 and 1.0 should succeed."""
        score = ConfidenceScore(0.85)
        assert score.value == 0.85

    def test_reject_negative_score(self):
        """Negative scores should raise ValueError."""
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            ConfidenceScore(-0.1)

    def test_is_high_confidence(self):
        """Scores >= 0.8 are high confidence."""
        high = ConfidenceScore(0.85)
        low = ConfidenceScore(0.5)
        assert high.is_high_confidence()
        assert not low.is_high_confidence()
```

## Property-Based Tests (PBT)

Property-based tests use Hypothesis to generate random inputs and verify invariants hold.

### Running PBT Tests

```bash
# All PBT tests
pytest tests/pbt/ -v

# With increased examples
pytest tests/pbt/ --hypothesis-seed=42 -v

# Specific property file
pytest tests/pbt/test_anonymization.py -v
```

### Critical Properties (BR-002, BR-004)

These properties verify critical business rules:

| ID | Property | Business Rule |
|----|----------|---------------|
| PBT-021 | Glossary has no duplicate aliases | BR-002 |
| PBT-022 | Same entity always gets same alias | BR-002 |
| PBT-040 | No PII appears in anonymized output | BR-004 |
| PBT-041 | Anonymization is deterministic | BR-004 |
| PBT-042 | All detected entities are replaced | BR-004 |

### Writing PBT Tests

```python
from hypothesis import given, strategies as st
from tests.pbt.conftest import confidence_scores, pii_categories

@given(score=confidence_scores())
def test_confidence_score_roundtrip(score: float):
    """ConfidenceScore preserves value through creation."""
    cs = ConfidenceScore(score)
    assert cs.value == score

@given(
    entity=st.text(min_size=1, max_size=50),
    category=pii_categories()
)
def test_alias_consistency(entity: str, category: str):
    """Same entity+category always produces same alias."""
    glossary = Glossary.create(project_id)
    alias1 = glossary.get_or_create_alias(entity, category)
    alias2 = glossary.get_or_create_alias(entity, category)
    assert alias1 == alias2
```

## Integration Tests

Integration tests verify component interactions with real (containerized) dependencies.

### Running Integration Tests

```bash
# Requires Docker
pytest tests/integration/ -v

# Skip if Docker unavailable
pytest tests/integration/ -v --ignore-docker
```

### Integration Test Example

```python
import pytest
from httpx import AsyncClient
from contextsafe.main import create_app

@pytest.fixture
async def client():
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_document_upload(client):
    """Test document upload flow."""
    files = {"file": ("test.txt", b"John Doe lives in Madrid", "text/plain")}
    response = await client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 201
    assert "document_id" in response.json()
```

## Contract Tests

Contract tests verify that implementations satisfy port interfaces.

```bash
pytest tests/contract/ -v
```

## Traceability Tests

YAML-based traceability tests map functions to implementation files for audit purposes.

```yaml
# tests/traceability/test_F_001.yaml
function_id: "F-001"
name: "DetectPiiEntities"
implementation:
  primary_file: "src/contextsafe/domain/entity_detection/entities/detection_result.py"
  supporting_files:
    - "src/contextsafe/infrastructure/nlp/spacy_adapter.py"
    - "src/contextsafe/infrastructure/nlp/regex_adapter.py"
test_coverage:
  unit_tests:
    - "tests/unit/domain/test_entities.py::TestDetectionResult"
  pbt_tests:
    - "tests/pbt/test_value_objects.py::test_confidence_score_*"
```

## Coverage Requirements

| Metric | Threshold | Current |
|--------|-----------|---------|
| Line Coverage | 80% | - |
| Branch Coverage | 70% | - |
| PBT Critical Properties | 100% pass | - |

### Generating Coverage Report

```bash
# HTML report
pytest --cov=src/contextsafe --cov-report=html --cov-report=term-missing

# Open report
open htmlcov/index.html
```

## CI/CD Integration

Tests run automatically on every push via GitHub Actions:

```yaml
# .github/workflows/ci.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Run tests
        run: make test
```

## Debugging Test Failures

### Common Issues

1. **Import Errors**: Ensure `PYTHONPATH=src` is set
   ```bash
   PYTHONPATH=src pytest tests/
   ```

2. **Database Lock**: SQLite file locked by another process
   ```bash
   rm -f tests/test.db
   ```

3. **Hypothesis Flaky**: Increase deadline or examples
   ```python
   @settings(deadline=None, max_examples=500)
   ```

### Verbose Output

```bash
# Maximum verbosity
pytest tests/ -vvv --tb=long

# Show print statements
pytest tests/ -s

# Stop on first failure
pytest tests/ -x
```

## Quality Gates

Before merging, all quality gates must pass:

```bash
# Run all quality checks
make quality

# Individual checks
ruff check src/              # Linting
ruff format --check src/     # Formatting
mypy src/                    # Type checking
bandit -r src/               # Security scan
pytest tests/                # All tests
```

## Test Data and Fixtures

### Shared Fixtures (conftest.py)

```python
@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    return Document.create(
        filename="test.txt",
        content="John Doe works at Acme Corp in Madrid.",
        mime_type="text/plain"
    )

@pytest.fixture
def empty_glossary():
    """Create an empty glossary for testing."""
    return Glossary.create(ProjectId(uuid4()))
```

### Hypothesis Strategies (tests/pbt/conftest.py)

```python
from hypothesis import strategies as st

@st.composite
def confidence_scores(draw):
    """Generate valid confidence scores [0.0, 1.0]."""
    return draw(st.floats(min_value=0.0, max_value=1.0))

@st.composite
def pii_categories(draw):
    """Generate valid PII category names."""
    categories = [
        "PERSON_NAME", "ORGANIZATION", "ADDRESS",
        "PHONE", "EMAIL", "ID_NUMBER"
    ]
    return draw(st.sampled_from(categories))
```

## Troubleshooting

### Tests Pass Locally but Fail in CI

1. Check Python version matches (3.11+)
2. Verify all dependencies are pinned
3. Check for timezone/locale differences
4. Review CI logs for resource limits

### Slow Tests

1. Use pytest-xdist for parallel execution:
   ```bash
   pytest tests/ -n auto
   ```

2. Profile slow tests:
   ```bash
   pytest tests/ --durations=10
   ```

### Flaky Tests

1. Add explicit waits for async operations
2. Use deterministic seeds for random data
3. Isolate database state between tests

---

## References

- [pytest Documentation](https://docs.pytest.org/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [icontract Documentation](https://icontract.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
