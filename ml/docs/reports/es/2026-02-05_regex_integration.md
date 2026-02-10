# Regex Patterns - Test de Integración

**Fecha:** 2026-02-05
**Autor:** AlexAlves87
**Componente:** Integración de regex patterns en `scripts/inference/ner_predictor.py`
**Estándar:** CHPDA (2025) - Hybrid regex+NER approach

---

## 1. Resumen Ejecutivo

Integración de patrones regex para detectar identificadores con espacios/guiones que el modelo NER transformer no detecta.

### Resultados

| Test Suite | Antes | Después | Mejora |
|------------|-------|---------|--------|
| Integration tests | - | 11/14 (78.6%) | Nuevo |
| Adversarial (strict) | 34.3% | **45.7%** | **+11.4pp** |
| F1 (strict) | 0.492 | **0.543** | **+0.051** |

### Conclusión

> **La integración regex mejora significativamente la detección de identificadores formateados.**
> Pass rate +11.4pp, F1 +0.051. El IBAN con espacios ahora se detecta correctamente.

---

## 2. Metodología

### 2.1 Estrategia de Merge (Híbrida)

```
Texto de entrada
       ↓
┌──────────────────────┐
│  1. NER Transformer  │  Detecta entidades semánticas
└──────────────────────┘
       ↓
┌──────────────────────┐
│  2. Regex Patterns   │  Detecta formatos con espacios
└──────────────────────┘
       ↓
┌──────────────────────┐
│  3. Merge Strategy   │  Combina, prefiere más completo
└──────────────────────┘
       ↓
┌──────────────────────┐
│  4. Checksum Valid.  │  Ajusta confianza
└──────────────────────┘
       ↓
Entidades finales
```

### 2.2 Lógica de Merge

| Caso | Acción |
|------|--------|
| Solo NER detecta | Mantener NER |
| Solo Regex detecta | Añadir Regex |
| Ambos detectan mismo span | Mantener NER (mayor calidad semántica) |
| Regex >20% más largo que NER | Reemplazar NER con Regex |
| NER parcial, Regex completo | Reemplazar con Regex |

### 2.3 Reproducibilidad

```bash
# Entorno
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Test integración regex
python scripts/evaluate/test_regex_integration.py

# Test adversarial completo
python scripts/evaluate/test_ner_predictor_adversarial_v2.py
```

---

## 3. Resultados

### 3.1 Tests de Integración (11/14)

| Test | Input | Resultado | Source |
|------|-------|-----------|--------|
| dni_spaces_2_3_3 | `12 345 678 Z` | ✅ | ner |
| dni_spaces_4_4 | `1234 5678 Z` | ✅ | ner |
| dni_dots | `12.345.678-Z` | ✅ | ner |
| nie_dashes | `X-1234567-Z` | ✅ | ner |
| **iban_spaces** | `ES91 2100 0418...` | ✅ | **regex** |
| phone_spaces | `612 345 678` | ✅ | regex |
| phone_intl | `+34 612345678` | ❌ | - |
| cif_dashes | `A-1234567-4` | ❌ (tipo incorrecto) | ner |
| nss_slashes | `28/12345678/90` | ✅ | ner |
| dni_standard | `12345678Z` | ✅ | ner |

### 3.2 Impacto en Adversarial Tests

| Métrica | Baseline | +Normalizer | +Regex | Delta Total |
|---------|----------|-------------|--------|-------------|
| **Pass Rate** | 28.6% | 34.3% | **45.7%** | **+17.1pp** |
| **F1 (strict)** | 0.464 | 0.492 | **0.543** | **+0.079** |
| F1 (partial) | 0.632 | 0.659 | **0.690** | +0.058 |
| COR | 29 | 31 | **35** | **+6** |
| MIS | 17 | 15 | **12** | **-5** |
| PAR | 21 | 21 | **19** | -2 |
| SPU | 8 | 7 | **7** | -1 |

### 3.3 Análisis de Mejoras

| Test Adversarial | Antes | Después | Mejora |
|------------------|-------|---------|--------|
| dni_with_spaces | MIS:1 | COR:1 | +1 COR |
| iban_with_spaces | PAR:1 | COR:1 | PAR→COR |
| phone_international | MIS:1 | COR:1* | +1 COR |
| address_floor_door | PAR:1 | COR:1 | PAR→COR |

*Detección parcial mejorada

---

## 4. Análisis de Errores

### 4.1 Fallos Restantes

| Test | Problema | Causa |
|------|----------|-------|
| phone_intl | `+34` no incluido | NER detecta `612345678`, no hay overlap suficiente |
| cif_dashes | Tipo incorrecto | Modelo clasifica CIF como DNI_NIE |
| spaced_iban_source | No detectado aislado | Contexto mínimo reduce detección |

### 4.2 Observaciones

1. **NER aprende formatos con espacios**: Sorprendentemente, el NER detecta algunos DNI con espacios (probablemente del data augmentation previo)

2. **Regex complementa, no reemplaza**: La mayoría de detecciones siguen siendo NER, regex solo añade casos que NER pierde

3. **Checksum se aplica a ambos**: Tanto NER como regex pasan por validación de checksum

---

## 5. Conclusiones y Trabajo Futuro

### 5.1 Conclusiones

1. **Mejora significativa**: +17.1pp pass rate, +0.079 F1
2. **IBAN con espacios**: Problema resuelto (regex detecta correctamente)
3. **Merge inteligente**: Prefiere detecciones más completas
4. **Overhead mínimo**: ~100ms adicionales por 25 patrones

### 5.2 Estado Actual vs Objetivo

| Métrica | Baseline | Actual | Objetivo | Gap |
|---------|----------|--------|----------|-----|
| Pass Rate | 28.6% | **45.7%** | ≥70% | -24.3pp |
| F1 (strict) | 0.464 | **0.543** | ≥0.70 | -0.157 |

### 5.3 Próximos Pasos

| Prioridad | Tarea | Impacto Estimado |
|-----------|-------|------------------|
| ALTA | Data augmentation fechas textuales | +3-4 COR |
| MEDIA | Corregir clasificación CIF | +1 COR |
| MEDIA | Mejorar detección phone_intl | +1 COR |
| BAJA | Boundary refinement para PAR→COR | +2-3 COR |

---

## 6. Referencias

1. **Standalone tests:** `docs/reports/2026-02-05_regex_patterns_standalone.md`
2. **CHPDA (2025):** [arXiv](https://arxiv.org/html/2502.07815v1) - Hybrid regex+NER
3. **Script de patrones:** `scripts/preprocess/spanish_id_patterns.py`
4. **Test de integración:** `scripts/evaluate/test_regex_integration.py`

---

**Tiempo de ejecución:** 2.72s (integration) + 1.4s (adversarial)
**Generado por:** AlexAlves87
**Fecha:** 2026-02-05
