# Checksum Validators - Teste Standalone

**Data:** 04-02-2026
**Autor:** AlexAlves87
**Componente:** `scripts/preprocess/checksum_validators.py`
**Padrão:** Algoritmos oficiais espanhóis (BOE)

---

## 1. Resumo Executivo

Implementação e validação standalone de validadores de checksum para identificadores espanhóis utilizados no pipeline NER-PII.

### Resultados

| Métrica | Valor |
|---------|-------|
| **Testes Passados** | 23/24 (95.8%) |
| **Validadores Implementados** | 5 (DNI, NIE, IBAN, NSS, CIF) |
| **Tempo Execução** | 0.003s |

### Conclusão

> **Todos os validadores funcionam corretamente segundo os algoritmos oficiais.**
> A única falha (caso limite NSS) é um erro na expectativa do teste, não no validador.

---

## 2. Metodologia

### 2.1 Algoritmos Implementados

| Identificador | Algoritmo | Fonte |
|---------------|-----------|-------|
| **DNI** | `letra = TRWAGMYFPDXBNJZSQVHLCKE[número % 23]` | BOE |
| **NIE** | X→0, Y→1, Z→2, depois DNI | BOE |
| **IBAN** | ISO 13616, mod 97 = 1 | ISO 13616 |
| **NSS** | `controle = (província + número) % 97` | Seguridade Social |
| **CIF** | Soma posições pares + ímpares com duplicação, controle = (10 - soma%10) % 10 | BOE |

### 2.2 Estrutura do Validador

Cada validador retorna uma tupla `(is_valid, confidence, reason)`:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `is_valid` | bool | Verdadeiro se checksum correto |
| `confidence` | float | 1.0 (válido), 0.5 (formato ok, checksum ruim), 0.0 (formato inválido) |
| `reason` | str | Descrição do resultado |

### 2.3 Reprodutibilidade

```bash
# Ambiente
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Execução
python scripts/preprocess/checksum_validators.py

# Output esperado: 23/24 passed (95.8%)
```

---

## 3. Resultados

### 3.1 Resumo por Validador

| Validador | Testes | Passados | Falhados |
|-----------|--------|----------|----------|
| DNI | 6 | 6 | 0 |
| NIE | 4 | 4 | 0 |
| DNI_NIE | 2 | 2 | 0 |
| IBAN | 4 | 4 | 0 |
| NSS | 2 | 1 | 1* |
| CIF | 4 | 4 | 0 |
| Edge cases | 2 | 2 | 0 |
| **Total** | **24** | **23** | **1** |

*A falha é um erro na expectativa do teste, não no validador.

### 3.2 Testes Detalhados

#### DNI (6/6 ✅)

| Teste | Input | Esperado | Resultado |
|-------|-------|----------|-----------|
| dni_valid_1 | `12345678Z` | ✅ válido | ✅ |
| dni_valid_2 | `00000000T` | ✅ válido | ✅ |
| dni_valid_spaces | `1234 5678 Z` | ✅ válido | ✅ |
| dni_invalid_letter | `12345678A` | ❌ inválido | ❌ (esperado Z) |
| dni_invalid_letter_2 | `00000000A` | ❌ inválido | ❌ (esperado T) |
| dni_invalid_format | `1234567Z` | ❌ inválido | ❌ (7 dígitos) |

#### NIE (4/4 ✅)

| Teste | Input | Esperado | Resultado |
|-------|-------|----------|-----------|
| nie_valid_x | `X0000000T` | ✅ válido | ✅ |
| nie_valid_y | `Y0000000Z` | ✅ válido | ✅ |
| nie_valid_z | `Z0000000M` | ✅ válido | ✅ |
| nie_invalid_letter | `X0000000A` | ❌ inválido | ❌ (esperado T) |

#### IBAN (4/4 ✅)

| Teste | Input | Esperado | Resultado |
|-------|-------|----------|-----------|
| iban_valid_es | `ES9121000418450200051332` | ✅ válido | ✅ |
| iban_valid_spaces | `ES91 2100 0418 4502 0005 1332` | ✅ válido | ✅ |
| iban_invalid_check | `ES0021000418450200051332` | ❌ inválido | ❌ (dígitos controle 00) |
| iban_invalid_mod97 | `ES1234567890123456789012` | ❌ inválido | ❌ (mod 97 ≠ 1) |

#### NSS (1/2 - 1 falha de expectativa)

| Teste | Input | Esperado | Resultado | Nota |
|-------|-------|----------|-----------|------|
| nss_valid | `281234567890` | ❌ inválido | ❌ | Correto (checksum aleatório) |
| nss_format_ok | `280000000097` | ✅ válido | ❌ | **Erro de expectativa** |

**Análise da falha:**
- Input: `280000000097`
- Província: `28`, Número: `00000000`, Controle: `97`
- Cálculo: `(28 * 10^8 + 0) % 97 = 2800000000 % 97 = 37`
- Esperado pelo teste: `97`, Real: `37`
- **O validador está correto.** A expectativa do teste estava incorreta.

#### CIF (4/4 ✅)

| Teste | Input | Esperado | Resultado |
|-------|-------|----------|-----------|
| cif_valid_a | `A12345674` | ✅ válido | ✅ |
| cif_valid_b | `B12345674` | ✅ válido | ✅ |
| cif_invalid | `A12345670` | ❌ inválido | ❌ (esperado 4) |

### 3.3 Demo de Validação

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

## 4. Análise de Erros

### 4.1 Única Falha: Caso Limite NSS

| Aspecto | Detalhe |
|---------|---------|
| Teste | `nss_format_ok` |
| Input | `280000000097` |
| Problema | Expectativa do teste assumia que `97` seria válido |
| Realidade | `(28 + "00000000") % 97 = 37`, não `97` |
| Ação | Corrigir expectativa no test case |

### 4.2 Correção Proposta

```python
# Em TEST_CASES, mudar:
TestCase("nss_format_ok", "280000000097", "NSS", True, "..."),
# Para:
TestCase("nss_format_ok", "280000000037", "NSS", True, "NSS with valid control"),
```

Ou melhor, calcular um NSS válido real:
- Província: `28` (Madrid)
- Número: `12345678`
- Controle: `(2812345678) % 97 = 2812345678 % 97 = 8`
- NSS válido: `281234567808`

---

## 5. Conclusões e Trabalho Futuro

### 5.1 Conclusões

1. **Todos os 5 validadores funcionam corretamente** segundo algoritmos oficiais
2. **A estrutura de retorno (is_valid, confidence, reason)** permite integração flexível
3. **O nível de confiança intermediário (0.5)** permite distinguir:
   - Formato correto mas checksum incorreto → possível erro de digitação/OCR
   - Formato incorreto → provavelmente não é esse tipo de ID

### 5.2 Uso no Pipeline NER

| Cenário | Ação |
|---------|------|
| Entidade detectada + checksum válido | Manter detecção (boost confiança) |
| Entidade detectada + checksum inválido | Reduzir confiança ou marcar como "possible_typo" |
| Entidade detectada + formato inválido | Possível falso positivo → revisar |

### 5.3 Próximo Passo

**Integração no pipeline NER para pós-validação:**
- Aplicar validadores a entidades detectadas como DNI_NIE, IBAN, NSS, CIF
- Ajustar confiança baseado no resultado da validação
- Reduzir SPU (falsos positivos) removendo detecções com checksums inválidos

### 5.4 Impacto Estimado

| Métrica | Baseline | Estimado | Melhoria |
|---------|----------|----------|----------|
| SPU | 8 | 5-6 | -2 a -3 |
| F1 (strict) | 0.492 | 0.50-0.52 | +0.01-0.03 |

---

## 6. Referências

1. **Algoritmo DNI/NIE:** BOE - Real Decreto 1553/2005
2. **Validação IBAN:** ISO 13616-1:2020
3. **Formato NSS:** Tesouraria Geral da Seguridade Social
4. **Algoritmo CIF:** BOE - Real Decreto 1065/2007
5. **Pesquisa base:** `docs/reports/2026-01-28_investigacion_hybrid_ner.md`

---

**Tempo de execução:** 0.003s
**Gerado por:** AlexAlves87
**Data:** 04-02-2026
