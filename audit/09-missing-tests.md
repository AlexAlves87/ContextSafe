# Tests Faltantes Criticos

Los 5 casos de test mas importantes que NO existen actualmente y que, si fallaran en produccion, causarian un fallo silencioso de anonimizacion (PII no detectado o no reemplazado).

---

## TF-001: Merge de spans solapados con 3 detectores discrepantes

**Modulo:** `composite_adapter.py` (`_merge_detections`, `_group_overlapping_detections`, `_resolve_by_voting`)  
**Severidad:** CRITICO  
**Descripcion:** Cuando RoBERTa detecta "28 de octubre de 2025" como ORGANIZATION, spaCy como DATE, y regex como DATE, el merge debe priorizar DATE (regex weight 5.0 + bonus 1.5). Si el voting falla, se anonimiza una fecha como ORG (fuga de contexto temporal) o se descarta (fuga de PII).

**Esqueleto del test:**

```python
import pytest
from contextsafe.infrastructure.nlp.composite_adapter import CompositeNerAdapter
from contextsafe.domain.shared.value_objects import TextSpan, ConfidenceScore
from contextsafe.application.ports import NerDetection
from contextsafe.domain.entity_detection.pii_category import PiiCategory


def _det(category: str, text: str, start: int, end: int, conf: float, source: str):
    return NerDetection(
        category=PiiCategory.from_string(category).value,
        value=text,
        span=TextSpan.create(start, end, text).unwrap(),
        confidence=ConfidenceScore(conf),
        source=source,
    )


@pytest.mark.asyncio
async def test_three_way_discrepancy_resolved_by_regex():
    adapter = CompositeNerAdapter(adapters=[])
    text = "firmado el 28 de octubre de 2025"
    detections = [
        _det("ORGANIZATION", "28 de octubre de 2025", 11, 31, 0.85, "roberta"),
        _det("DATE", "28 de octubre de 2025", 11, 31, 0.90, "spacy"),
        _det("DATE", "28 de octubre de 2025", 11, 31, 1.0, "regex"),
    ]
    merged = adapter._merge_detections(detections, text)
    assert len(merged) == 1
    assert merged[0].category.value == "DATE"
```

---

## TF-002: Snapping de tokens BPE corrige corte de palabra

**Modulo:** `merge/snapping.py` (`snap_to_tokens`)  
**Severidad:** CRITICO  
**Descripcion:** RoBERTa BPE corta "Juan" como " Ju" + "an". Si snapping no expande al token spaCy completo, el span queda como " an" y el reemplazo corrompe el texto original.

**Esqueleto del test:**

```python
import pytest
from unittest.mock import MagicMock
from contextsafe.infrastructure.nlp.merge.snapping import snap_to_tokens
from contextsafe.domain.shared.value_objects import TextSpan, ConfidenceScore
from contextsafe.application.ports import NerDetection
from contextsafe.domain.entity_detection.pii_category import PiiCategory


def test_snap_to_tokens_fixes_bpe_cut():
    # Mock spacy_doc con tokens: [Token("Juan", idx=1), Token("Carlos", idx=6)]
    mock_token = MagicMock()
    mock_token.idx = 1
    mock_token.text = "Juan"
    mock_token.text_with_ws = "Juan "

    mock_token2 = MagicMock()
    mock_token2.idx = 6
    mock_token2.text = "Carlos"
    mock_token2.text_with_ws = "Carlos"

    mock_spacy_doc = MagicMock()
    mock_spacy_doc.__iter__ = lambda self: iter([mock_token, mock_token2])
    mock_spacy_doc.text = "Juan Carlos"

    detection = NerDetection(
        category=PiiCategory.from_string("PERSON_NAME").value,
        value="an",
        span=TextSpan.create(2, 4, "an").unwrap(),
        confidence=ConfidenceScore(0.9),
        source="roberta",
    )
    snapped = snap_to_tokens(detection, mock_spacy_doc)
    assert snapped.value == "Juan"
    assert snapped.span.start == 1
    assert snapped.span.end == 5
```

---

## TF-003: `_remove_overlapping_detections` con prioridad GDPR

**Modulo:** `anonymization_adapter.py`  
**Severidad:** CRITICO  
**Descripcion:** Si DNI_NIE (riesgo 95) y ORGANIZATION (riesgo 50) se solapan, debe sobrevivir el DNI. Fallo = DNI no anonimizado.

**Esqueleto del test:**

```python
import pytest
from contextsafe.infrastructure.nlp.anonymization_adapter import InMemoryAnonymizationAdapter
from contextsafe.domain.shared.value_objects import TextSpan, ConfidenceScore
from contextsafe.application.ports import NerDetection
from contextsafe.domain.entity_detection.pii_category import PiiCategory


def _det(category: str, text: str, start: int, end: int, conf: float):
    return NerDetection(
        category=PiiCategory.from_string(category).value,
        value=text,
        span=TextSpan.create(start, end, text).unwrap(),
        confidence=ConfidenceScore(conf),
        source="test",
    )


@pytest.mark.asyncio
async def test_gdpr_priority_survives_overlap():
    adapter = InMemoryAnonymizationAdapter()
    text = "Empresa 12345678Z presento"
    detections = [
        _det("ORGANIZATION", "Empresa 12345678Z", 0, 17, 0.8),
        _det("DNI_NIE", "12345678Z", 8, 17, 1.0),
    ]
    result = await adapter.anonymize_text(text, detections, "proj")
    assert "12345678Z" not in result.anonymized_text
    assert "ID_" in result.anonymized_text
```

---

## TF-004: Idempotencia completa del pipeline (NER + Anonymize)

**Modulo:** `composite_adapter.py` + `anonymization_adapter.py`  
**Severidad:** ALTO  
**Descripcion:** Anonimizar el mismo texto dos veces debe producir el mismo resultado. Riesgo: segunda pasada detecta los aliases como nuevas entidades.

**Esqueleto del test:**

```python
import pytest


@pytest.mark.asyncio
async def test_anonymize_twice_is_idempotent(adapter, anonymizer):
    text = "Juan Perez vive en Madrid"
    # First pass
    dets1 = await adapter.detect_entities(text)
    anon1 = await anonymizer.anonymize_text(text, dets1, "proj")
    # Second pass on anonymized text
    dets2 = await adapter.detect_entities(anon1.anonymized_text)
    anon2 = await anonymizer.anonymize_text(anon1.anonymized_text, dets2, "proj")
    # Should not detect aliases as new entities
    assert len(dets2) == 0 or all(
        d.value not in anon1.anonymized_text for d in dets2
    )
    assert anon2.anonymized_text == anon1.anonymized_text
```

---

## TF-005: Estrategia ADVANCED genera checksums INVALIDOS

**Modulo:** `strategies/synthetic.py`  
**Severidad:** CRITICO  
**Descripcion:** DNI/IBAN/NSS generados en nivel ADVANCED deben tener checksums matematicamente invalidos. Si el generador usa `random.choice` incorrectamente, podria generar un DNI real.

**Esqueleto del test:**

```python
import pytest
from contextsafe.infrastructure.nlp.strategies.synthetic import generate_invalid_dni

# Asumiendo que DNI_LETTERS esta disponible en el modulo
DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"


def test_synthetic_dni_is_invalid():
    for _ in range(100):
        dni = generate_invalid_dni()
        digits = int(dni[:-1])
        valid_letter = DNI_LETTERS[digits % 23]
        assert dni[-1] != valid_letter, f"Generated valid DNI: {dni}"
```

---

## Recomendaciones de Implementacion

1. **Crear directorio** `tests/unit/infrastructure/nlp/strategies/` para tests de `MaskingStrategy`, `PseudonymStrategy` y `SyntheticStrategy`.
2. **Crear directorio** `tests/unit/infrastructure/nlp/merge/` para tests de snapping y voting.
3. **Anadir fixture** de `mock_spacy_doc` en `conftest.py` para facilitar tests de snapping.
4. **Instalar `pytest-cov`** y ejecutar `pytest --cov=src/contextsafe --cov-fail-under=80`.
5. **Marcar tests de integracion** como `@pytest.mark.skip` hasta que la app exponga rutas correctamente en modo test.

---

*Estos 5 tests, si existieran, detectarian regresiones en las areas de mayor riesgo del sistema.*
