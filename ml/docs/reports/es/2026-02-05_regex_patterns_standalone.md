# Regex Patterns para Identificadores Españoles - Test Standalone

**Fecha:** 2026-02-05
**Autor:** AlexAlves87
**Componente:** `scripts/preprocess/spanish_id_patterns.py`
**Estándar:** CHPDA (2025) - Hybrid regex+NER approach

---

## 1. Resumen Ejecutivo

Implementación de patrones regex para detectar identificadores españoles con formatos variantes (espacios, guiones, puntos) que los modelos NER transformer típicamente no detectan.

### Resultados

| Métrica | Valor |
|---------|-------|
| **Tests Pasados** | 22/22 (100%) |
| **Tipos de Entidad** | 5 (DNI_NIE, IBAN, NSS, CIF, PHONE) |
| **Patrones Totales** | 25 |
| **Tiempo Ejecución** | 0.003s |

### Conclusión

> **Todos los patrones funcionan correctamente para formatos con espacios y separadores.**
> Esto complementa al NER transformer que falla en casos como "12 345 678 Z" o "ES91 2100 0418...".

---

## 2. Metodología

### 2.1 Investigación Base

| Paper | Enfoque | Aplicación |
|-------|---------|------------|
| **CHPDA (arXiv 2025)** | Regex + AI NER híbrido | Reduce falsos positivos |
| **Hybrid ReGex (JCO 2025)** | Pipeline ligero regex + ML | Extracción datos médicos |
| **Legal NLP Survey (2024)** | NER especializado legal | Patrones de normativa |

### 2.2 Patrones Implementados

| Tipo | Patrones | Ejemplos |
|------|----------|----------|
| **DNI** | 6 | `12345678Z`, `12 345 678 Z`, `12.345.678-Z` |
| **NIE** | 3 | `X1234567Z`, `X 1234567 Z`, `X-1234567-Z` |
| **IBAN** | 3 | `ES9121...`, `ES91 2100 0418...` |
| **NSS** | 3 | `281234567890`, `28/12345678/90` |
| **CIF** | 3 | `A12345674`, `A-1234567-4` |
| **PHONE** | 7 | `612345678`, `612 345 678`, `+34 612...` |

### 2.3 Reproducibilidad

```bash
# Entorno
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Ejecución
python scripts/preprocess/spanish_id_patterns.py

# Output esperado: 22/22 passed (100.0%)
```

---

## 3. Resultados

### 3.1 Tests por Tipo

| Tipo | Tests | Pasados | Ejemplos Clave |
|------|-------|---------|----------------|
| DNI | 6 | 6 | Standard, espacios 2-3-3, puntos |
| NIE | 3 | 3 | Standard, espacios, guiones |
| IBAN | 2 | 2 | Standard, espacios grupos 4 |
| NSS | 2 | 2 | Barras, espacios |
| CIF | 2 | 2 | Standard, guiones |
| PHONE | 4 | 4 | Móvil, fijo, internacional |
| Negativos | 2 | 2 | Rechaza formatos inválidos |
| Multi | 1 | 1 | Múltiples entidades en texto |

### 3.2 Demo de Detección

| Input | Detección | Normalizado |
|-------|-----------|-------------|
| `DNI 12 345 678 Z` | ✅ DNI_NIE | `12345678Z` |
| `IBAN ES91 2100 0418 4502 0005 1332` | ✅ IBAN | `ES9121000418450200051332` |
| `NIE X-1234567-Z` | ✅ DNI_NIE | `X1234567Z` |
| `Tel: 612 345 678` | ✅ PHONE | `612345678` |
| `CIF A-1234567-4` | ✅ CIF | `A12345674` |

### 3.3 Estructura de Match

```python
@dataclass
class RegexMatch:
    text: str           # "12 345 678 Z"
    entity_type: str    # "DNI_NIE"
    start: int          # 4
    end: int            # 16
    confidence: float   # 0.90
    pattern_name: str   # "dni_spaced_2_3_3"
```

---

## 4. Análisis de Patrones

### 4.1 Niveles de Confianza

| Nivel | Confianza | Criterio |
|-------|-----------|----------|
| Alta | 0.95 | Formato estándar sin ambigüedad |
| Media | 0.90 | Formato con separadores válidos |
| Baja | 0.70-0.85 | Formatos que pueden ser ambiguos |

### 4.2 Patrones DNI con Espacios (Problema Original)

El test adversarial `dni_with_spaces` fallaba porque el NER no detectaba "12 345 678 Z".

**Solución implementada:**
```python
# Patrón para espacios 2-3-3
r'\b(\d{2})\s+(\d{3})\s+(\d{3})\s*([A-Z])\b'
```

Este patrón detecta:
- `12 345 678 Z` ✅
- `12 345 678Z` ✅ (sin espacio antes de letra)

### 4.3 Normalización para Checksum

Función `normalize_match()` elimina separadores para validación:

```python
"12 345 678 Z" → "12345678Z"
"ES91 2100 0418..." → "ES9121000418..."
"X-1234567-Z" → "X1234567Z"
```

---

## 5. Conclusiones y Trabajo Futuro

### 5.1 Conclusiones

1. **25 patrones cubren formatos variantes** de identificadores españoles
2. **Normalización permite integración** con checksum validators
3. **Confianza variable** distingue formatos más/menos confiables
4. **Detección de overlaps** evita duplicados

### 5.2 Integración en Pipeline

```
Texto de entrada
       ↓
┌──────────────────────┐
│  1. TextNormalizer   │  Unicode/OCR cleanup
└──────────────────────┘
       ↓
┌──────────────────────┐
│  2. NER Transformer  │  RoBERTalex predictions
└──────────────────────┘
       ↓
┌──────────────────────┐
│  3. Regex Patterns   │  ← NUEVO: detecta espacios
└──────────────────────┘
       ↓
┌──────────────────────┐
│  4. Merge & Dedup    │  Combina NER + Regex
└──────────────────────┘
       ↓
┌──────────────────────┐
│  5. Checksum Valid.  │  Ajusta confianza
└──────────────────────┘
       ↓
Entidades finales
```

### 5.3 Impacto Estimado

| Test Adversarial | Antes | Después | Mejora |
|------------------|-------|---------|--------|
| `dni_with_spaces` | MIS:1 | COR:1 | +1 COR |
| `iban_with_spaces` | PAR:1 | COR:1 | +1 COR |
| `phone_international` | MIS:1 | COR:1 | +1 COR (potencial) |

**Estimación total:** +2-3 COR, conversión de MIS y PAR a COR.

---

## 6. Referencias

1. **CHPDA (2025):** [arXiv](https://arxiv.org/html/2502.07815v1) - Hybrid regex+NER approach
2. **Hybrid ReGex (2025):** [JCO](https://ascopubs.org/doi/10.1200/CCI-25-00130) - Medical data extraction
3. **Legal NLP Survey (2024):** [arXiv](https://arxiv.org/html/2410.21306v3) - NER for legal domain

---

**Tiempo de ejecución:** 0.003s
**Generado por:** AlexAlves87
**Fecha:** 2026-02-05
