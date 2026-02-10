# Checksum Validators - Test Standalone

**Fecha:** 2026-02-04
**Autor:** AlexAlves87
**Componente:** `scripts/preprocess/checksum_validators.py`
**Estándar:** Algoritmos oficiales españoles (BOE)

---

## 1. Resumen Ejecutivo

Implementación y validación standalone de validadores de checksum para identificadores españoles utilizados en el pipeline NER-PII.

### Resultados

| Métrica | Valor |
|---------|-------|
| **Tests Pasados** | 23/24 (95.8%) |
| **Validadores Implementados** | 5 (DNI, NIE, IBAN, NSS, CIF) |
| **Tiempo Ejecución** | 0.003s |

### Conclusión

> **Todos los validadores funcionan correctamente según algoritmos oficiales.**
> El único fallo (NSS edge case) es un error en la expectativa del test, no en el validador.

---

## 2. Metodología

### 2.1 Algoritmos Implementados

| Identificador | Algoritmo | Fuente |
|---------------|-----------|--------|
| **DNI** | `letra = TRWAGMYFPDXBNJZSQVHLCKE[número % 23]` | BOE |
| **NIE** | X→0, Y→1, Z→2, luego DNI | BOE |
| **IBAN** | ISO 13616, mod 97 = 1 | ISO 13616 |
| **NSS** | `control = (provincia + número) % 97` | Seguridad Social |
| **CIF** | Suma posiciones pares + impares con doblar, control = (10 - sum%10) % 10 | BOE |

### 2.2 Estructura del Validador

Cada validador retorna una tupla `(is_valid, confidence, reason)`:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `is_valid` | bool | True si checksum correcto |
| `confidence` | float | 1.0 (válido), 0.5 (formato ok, checksum mal), 0.0 (formato inválido) |
| `reason` | str | Descripción del resultado |

### 2.3 Reproducibilidad

```bash
# Entorno
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Ejecución
python scripts/preprocess/checksum_validators.py

# Output esperado: 23/24 passed (95.8%)
```

---

## 3. Resultados

### 3.1 Resumen por Validador

| Validador | Tests | Pasados | Fallados |
|-----------|-------|---------|----------|
| DNI | 6 | 6 | 0 |
| NIE | 4 | 4 | 0 |
| DNI_NIE | 2 | 2 | 0 |
| IBAN | 4 | 4 | 0 |
| NSS | 2 | 1 | 1* |
| CIF | 4 | 4 | 0 |
| Edge cases | 2 | 2 | 0 |
| **Total** | **24** | **23** | **1** |

*El fallo es un error en la expectativa del test, no en el validador.

### 3.2 Tests Detallados

#### DNI (6/6 ✅)

| Test | Input | Esperado | Resultado |
|------|-------|----------|-----------|
| dni_valid_1 | `12345678Z` | ✅ válido | ✅ |
| dni_valid_2 | `00000000T` | ✅ válido | ✅ |
| dni_valid_spaces | `1234 5678 Z` | ✅ válido | ✅ |
| dni_invalid_letter | `12345678A` | ❌ inválido | ❌ (expected Z) |
| dni_invalid_letter_2 | `00000000A` | ❌ inválido | ❌ (expected T) |
| dni_invalid_format | `1234567Z` | ❌ inválido | ❌ (7 dígitos) |

#### NIE (4/4 ✅)

| Test | Input | Esperado | Resultado |
|------|-------|----------|-----------|
| nie_valid_x | `X0000000T` | ✅ válido | ✅ |
| nie_valid_y | `Y0000000Z` | ✅ válido | ✅ |
| nie_valid_z | `Z0000000M` | ✅ válido | ✅ |
| nie_invalid_letter | `X0000000A` | ❌ inválido | ❌ (expected T) |

#### IBAN (4/4 ✅)

| Test | Input | Esperado | Resultado |
|------|-------|----------|-----------|
| iban_valid_es | `ES9121000418450200051332` | ✅ válido | ✅ |
| iban_valid_spaces | `ES91 2100 0418 4502 0005 1332` | ✅ válido | ✅ |
| iban_invalid_check | `ES0021000418450200051332` | ❌ inválido | ❌ (check digits 00) |
| iban_invalid_mod97 | `ES1234567890123456789012` | ❌ inválido | ❌ (mod 97 ≠ 1) |

#### NSS (1/2 - 1 fallo en expectativa)

| Test | Input | Esperado | Resultado | Nota |
|------|-------|----------|-----------|------|
| nss_valid | `281234567890` | ❌ inválido | ❌ | Correcto (checksum aleatorio) |
| nss_format_ok | `280000000097` | ✅ válido | ❌ | **Error en expectativa** |

**Análisis del fallo:**
- Input: `280000000097`
- Provincia: `28`, Número: `00000000`, Control: `97`
- Cálculo: `(28 * 10^8 + 0) % 97 = 2800000000 % 97 = 37`
- Esperado por test: `97`, Real: `37`
- **El validador es correcto.** La expectativa del test era incorrecta.

#### CIF (4/4 ✅)

| Test | Input | Esperado | Resultado |
|------|-------|----------|-----------|
| cif_valid_a | `A12345674` | ✅ válido | ✅ |
| cif_valid_b | `B12345674` | ✅ válido | ✅ |
| cif_invalid | `A12345670` | ❌ inválido | ❌ (expected 4) |

### 3.3 Demo de Validación

```
DNI_NIE: '12345678Z'
  ✅ VALID (confidence: 1.0)
  Reason: Valid DNI checksum

DNI_NIE: '12345678A'
  ❌ INVALID (confidence: 0.5)
  Reason: Invalid checksum: expected 'Z', got 'A'

DNI_NIE: 'X0000000T'
  ✅ VALID (confidence: 1.0)
  Reason: Valid NIE checksum

IBAN: 'ES91 2100 0418 4502 0005 1332'
  ✅ VALID (confidence: 1.0)
  Reason: Valid IBAN checksum

CIF: 'A12345674'
  ✅ VALID (confidence: 1.0)
  Reason: Valid CIF checksum (digit)
```

---

## 4. Análisis de Errores

### 4.1 Único Fallo: NSS Edge Case

| Aspecto | Detalle |
|---------|---------|
| Test | `nss_format_ok` |
| Input | `280000000097` |
| Problema | La expectativa del test asumía que `97` sería válido |
| Realidad | `(28 + "00000000") % 97 = 37`, no `97` |
| Acción | Corregir expectativa en test case |

### 4.2 Corrección Propuesta

```python
# En TEST_CASES, cambiar:
TestCase("nss_format_ok", "280000000097", "NSS", True, "..."),
# Por:
TestCase("nss_format_ok", "280000000037", "NSS", True, "NSS with valid control"),
```

O mejor, calcular un NSS válido real:
- Provincia: `28` (Madrid)
- Número: `12345678`
- Control: `(2812345678) % 97 = 2812345678 % 97 = 8`
- NSS válido: `281234567808`

---

## 5. Conclusiones y Trabajo Futuro

### 5.1 Conclusiones

1. **Los 5 validadores funcionan correctamente** según algoritmos oficiales
2. **La estructura de retorno (is_valid, confidence, reason)** permite integración flexible
3. **El nivel de confianza intermedio (0.5)** permite distinguir:
   - Formato correcto pero checksum incorrecto → posible typo/OCR
   - Formato incorrecto → probablemente no es ese tipo de ID

### 5.2 Uso en Pipeline NER

| Escenario | Acción |
|-----------|--------|
| Entidad detectada + checksum válido | Mantener detección (confidence boost) |
| Entidad detectada + checksum inválido | Reducir confidence o marcar como "possible_typo" |
| Entidad detectada + formato inválido | Posible falso positivo → revisar |

### 5.3 Próximo Paso

**Integración en pipeline NER para post-validación:**
- Aplicar validadores a entidades detectadas como DNI_NIE, IBAN, NSS, CIF
- Ajustar confidence basado en resultado de validación
- Reducir SPU (falsos positivos) eliminando detecciones con checksums inválidos

### 5.4 Impacto Estimado

| Métrica | Baseline | Estimado | Mejora |
|---------|----------|----------|--------|
| SPU | 8 | 5-6 | -2 a -3 |
| F1 (strict) | 0.492 | 0.50-0.52 | +0.01-0.03 |

---

## 6. Referencias

1. **DNI/NIE Algorithm:** BOE - Real Decreto 1553/2005
2. **IBAN Validation:** ISO 13616-1:2020
3. **NSS Format:** Tesorería General de la Seguridad Social
4. **CIF Algorithm:** BOE - Real Decreto 1065/2007
5. **Investigación base:** `docs/reports/2026-01-28_investigacion_hybrid_ner.md`

---

**Tiempo de ejecución:** 0.003s
**Generado por:** AlexAlves87
**Fecha:** 2026-02-04
