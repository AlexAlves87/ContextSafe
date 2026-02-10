# Gap Analysis: Tests Actuales vs Estándares Académicos

**Fecha:** 2026-01-29
**Autor:** AlexAlves87
**Archivo analizado:** `scripts/evaluate/test_ner_predictor_adversarial.py`

---

## 1. Resumen de Gaps

| Aspecto | Estándar Académico | Implementación Actual | Severidad |
|---------|--------------------|-----------------------|-----------|
| Modo de evaluación | Strict (SemEval 2013) | Lenient (custom) | **CRÍTICO** |
| 4 modos SemEval | strict, exact, partial, type | Solo 1 modo custom | ALTO |
| Librería de métricas | seqeval o nervaluate | Implementación custom | ALTO |
| Métricas detalladas | COR/INC/PAR/MIS/SPU | Solo TP/FP/FN | MEDIO |
| Métricas por tipo | F1 por PERSON, DNI, etc. | Solo F1 agregado | MEDIO |
| Referencia NoiseBench | EMNLP 2024 | "ICLR 2024" (error) | BAJO |
| Documentación de modo | Explícito en reporte | No documentado | MEDIO |

---

## 2. Análisis Detallado

### 2.1 CRÍTICO: Modo de Matching No Es Strict

**Código actual (líneas 458-493):**

```python
def entities_match(expected: dict, detected: dict, tolerance: int = 5) -> bool:
    # Type must match
    if expected["type"] != detected["type"]:
        return False

    # Containment (detected contains expected or vice versa)
    if exp_text in det_text or det_text in exp_text:
        return True

    # Length difference tolerance
    if abs(len(exp_text) - len(det_text)) <= tolerance:
        # Check character overlap
        common = sum(1 for c in exp_text if c in det_text)
        if common >= len(exp_text) * 0.8:
            return True
```

**Problemas:**
1. Permite **containment** (Si "José García" está en "Don José García López", cuenta como match)
2. Permite **80% character overlap** (no es boundary exacto)
3. Permite **tolerancia de 5 caracteres** en longitud

**Estándar SemEval strict:**
> "Exact boundary surface string match AND entity type match"

**Impacto:** Los resultados actuales (F1=0.784, 54.3% pass) podrían ser **INFLADOS** porque se aceptan matches parciales como correctos.

### 2.2 ALTO: No Usa seqeval ni nervaluate

**Estándar:** Usar librerías validadas contra conlleval.

**Actual:** Implementación custom de métricas.

**Riesgo:** Las métricas custom pueden no ser comparables con literatura académica.

### 2.3 ALTO: Solo Un Modo de Evaluación

**SemEval 2013 define 4 modos:**

| Modo | Boundary | Type | Uso |
|------|----------|------|-----|
| **strict** | Exacto | Exacto | Principal, riguroso |
| exact | Exacto | Ignorado | Análisis de boundaries |
| partial | Overlap | Ignorado | Análisis lenient |
| type | Overlap | Exacto | Análisis de clasificación |

**Actual:** Solo un modo custom (similar a partial/lenient).

**Impacto:** No podemos separar errores de boundary vs errores de type.

### 2.4 MEDIO: Sin Métricas COR/INC/PAR/MIS/SPU

**SemEval 2013:**
- **COR**: Correct (boundary Y type exactos)
- **INC**: Incorrect (boundary exacto, type incorrecto)
- **PAR**: Partial (boundary con overlap)
- **MIS**: Missing (FN)
- **SPU**: Spurious (FP)

**Actual:** Solo TP/FP/FN (no distingue INC de PAR).

### 2.5 MEDIO: Sin Métricas por Tipo de Entidad

**Estándar:** Reportar F1 para cada tipo (PERSON, DNI_NIE, IBAN, etc.)

**Actual:** Solo F1 agregado.

**Impacto:** No sabemos qué tipos de entidad tienen peor rendimiento.

### 2.6 BAJO: Error en Referencia

**Línea 10:** `NoiseBench (ICLR 2024)`

**Correcto:** `NoiseBench (EMNLP 2024)`

---

## 3. Impacto en Resultados Reportados

### 3.1 Estimación de Diferencia Strict vs Lenient

Basado en literatura, modo strict típicamente produce **5-15% menos F1** que lenient:

| Métrica | Actual (lenient) | Estimado (strict) |
|---------|------------------|-------------------|
| F1 | 0.784 | 0.67-0.73 |
| Pass rate | 54.3% | 40-48% |

**Los resultados actuales son optimistas.**

### 3.2 Tests Afectados por Matching Lenient

Tests donde el matching lenient acepta como correcto lo que strict rechazaría:

| Test | Situación | Impacto |
|------|-----------|---------|
| `very_long_name` | Nombre largo, ¿boundary exacto? | Posible |
| `address_floor_door` | Dirección compleja | Posible |
| `testament_comparecencia` | Múltiples entidades | Alto |
| `judicial_sentence_header` | Fechas textuales | Alto |

---

## 4. Plan de Corrección

### 4.1 Cambios Requeridos

1. **Implementar modo strict** (prioridad CRÍTICA)
   - Boundary debe ser exacto (normalizado)
   - Type debe ser exacto

2. **Añadir nervaluate** (prioridad ALTA)
   ```bash
   pip install nervaluate
   ```

3. **Reportar 4 modos** (prioridad ALTA)
   - strict (principal)
   - exact
   - partial
   - type

4. **Añadir métricas por tipo** (prioridad MEDIA)

5. **Corregir referencia NoiseBench** (prioridad BAJA)

### 4.2 Estrategia de Migración

Para mantener comparabilidad con resultados anteriores:

1. Ejecutar con **ambos modos** (lenient Y strict)
2. Reportar **ambos** en documentación
3. Usar **strict como métrica principal** going forward
4. Documentar diferencia para baseline

---

## 5. Nuevo Script Propuesto

Crear `test_ner_predictor_adversarial_v2.py` con:

1. Modo strict por defecto
2. Integración con nervaluate
3. Métricas COR/INC/PAR/MIS/SPU
4. F1 por tipo de entidad
5. Opción de modo legacy para comparación

---

## 6. Conclusiones

**Los resultados actuales (F1=0.784, 54.3% pass) no son comparables con literatura académica** porque:

1. Usan matching lenient, no strict
2. No usan librerías estándar (seqeval, nervaluate)
3. No reportan métricas granulares (por tipo, COR/INC/PAR)

**Acción inmediata:** Antes de continuar con integración de TextNormalizer, debemos:

1. Crear script v2 con estándares académicos
2. Re-establecer baseline con modo strict
3. DESPUÉS evaluar impacto de mejoras

---

**Generado por:** AlexAlves87
**Fecha:** 2026-01-29
