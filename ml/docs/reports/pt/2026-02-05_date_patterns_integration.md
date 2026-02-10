# Date Patterns - Teste de Integração

**Data:** 05-02-2026
**Autor:** AlexAlves87
**Componente:** `scripts/preprocess/spanish_date_patterns.py` integrado no pipeline
**Padrão:** TIMEX3 para expressões temporais

---

## 1. Resumo Executivo

Integração de padrões regex para datas textuais espanholas que complementam a detecção NER.

### Resultados

| Suíte de Teste | Resultado |
|----------------|-----------|
| Testes standalone | 14/14 (100%) |
| Testes de integração | 9/9 (100%) |
| Adversarial (melhoria) | +2.9pp taxa de aprovação |

### Conclusão

> **Os padrões de data agregam valor principalmente para números romanos.**
> O modelo NER já detecta a maioria das datas textuais.
> Melhoria total acumulada: Taxa de aprovação +20pp, F1 +0.081 desde a baseline.

---

## 2. Metodologia

### 2.1 Padrões Implementados (10 total)

| Padrão | Exemplo | Confiança |
|--------|---------|-----------|
| `date_roman_full` | XV de marzo del año MMXXIV | 0.95 |
| `date_roman_day_written_year` | XV de marzo de dos mil... | 0.90 |
| `date_written_full` | quince de marzo de dos mil... | 0.95 |
| `date_ordinal_full` | primero de enero de dos mil... | 0.95 |
| `date_written_day_numeric_year` | quince de marzo de 2024 | 0.90 |
| `date_ordinal_numeric_year` | primero de enero de 2024 | 0.90 |
| `date_a_written` | a veinte de abril de dos mil... | 0.90 |
| `date_el_dia_written` | el día quince de marzo de... | 0.90 |
| `date_numeric_standard` | 15 de marzo de 2024 | 0.85 |
| `date_formal_legal` | día 15 del mes de marzo del año 2024 | 0.90 |

### 2.2 Integração

Os padrões de data foram integrados em `spanish_id_patterns.py`:

```python
# Em find_matches():
if DATE_PATTERNS_AVAILABLE and (entity_types is None or "DATE" in entity_types):
    date_matches = find_date_matches(text)
    for dm in date_matches:
        matches.append(RegexMatch(
            text=dm.text,
            entity_type="DATE",
            ...
        ))
```

### 2.3 Reprodutibilidade

```bash
# Ambiente
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Teste standalone
python scripts/preprocess/spanish_date_patterns.py

# Teste integração
python scripts/evaluate/test_date_integration.py

# Teste adversarial completo
python scripts/evaluate/test_ner_predictor_adversarial_v2.py
```

---

## 3. Resultados

### 3.1 Testes de Integração (9/9)

| Teste | Texto | Fonte | Resultado |
|-------|-------|-------|-----------|
| roman_full | XV de marzo del año MMXXIV | **regex** | ✅ |
| ordinal_full | primero de enero de dos mil... | ner | ✅ |
| notarial_date | quince de marzo de dos mil... | ner | ✅ |
| testament_date | diez de enero de dos mil... | ner | ✅ |
| written_full | veintiocho de febrero de... | ner | ✅ |
| numeric_standard | 15 de marzo de 2024 | ner | ✅ |
| multiple_dates | uno de enero...diciembre... | ner | ✅ |
| date_roman_numerals | XV de marzo del año MMXXIV | **regex** | ✅ |
| date_ordinal | primero de enero de... | ner | ✅ |

### 3.2 Observação Chave

**O modelo NER já detecta a maioria das datas textuais.** O regex agrega valor apenas para:
- **Números romanos** (XV, MMXXIV) - não no vocabulário do modelo

### 3.3 Impacto em Testes Adversariais

| Métrica | Antes | Depois | Delta |
|---------|-------|--------|-------|
| Taxa de Aprovação | 45.7% | **48.6%** | **+2.9pp** |
| F1 (strict) | 0.543 | **0.545** | +0.002 |
| F1 (parcial) | 0.690 | **0.705** | +0.015 |
| COR | 35 | **36** | **+1** |
| MIS | 12 | **9** | **-3** |
| PAR | 19 | 21 | +2 |

---

## 4. Progresso Total Acumulado

### 4.1 Elementos Integrados

| Elemento | Standalone | Integração | Impacto Principal |
|----------|------------|------------|-------------------|
| 1. TextNormalizer | 15/15 | ✅ | Evasão Unicode |
| 2. Checksum | 23/24 | ✅ | Ajuste confiança |
| 3. Regex IDs | 22/22 | ✅ | Identificadores espaçados |
| 4. Padrões Data | 14/14 | ✅ | Números romanos |

### 4.2 Métricas Totais

| Métrica | Baseline | Atual | Melhoria | Meta | Gap |
|---------|----------|-------|----------|------|-----|
| **Taxa Aprovação** | 28.6% | **48.6%** | **+20pp** | ≥70% | -21.4pp |
| **F1 (strict)** | 0.464 | **0.545** | **+0.081** | ≥0.70 | -0.155 |
| COR | 29 | 36 | +7 | - | - |
| MIS | 17 | 9 | -8 | - | - |
| SPU | 8 | 7 | -1 | - | - |
| PAR | 21 | 21 | 0 | - | - |

### 4.3 Progresso Visual

```
Taxa de Aprovação:
Baseline   [████████░░░░░░░░░░░░░░░░░░░░░░░░░░░] 28.6%
Atual      [█████████████████░░░░░░░░░░░░░░░░░░] 48.6%
Meta       [████████████████████████████░░░░░░░] 70.0%

F1 (strict):
Baseline   [████████████████░░░░░░░░░░░░░░░░░░░] 0.464
Atual      [███████████████████░░░░░░░░░░░░░░░░] 0.545
Meta       [████████████████████████████░░░░░░░] 0.700
```

---

## 5. Conclusões e Trabalho Futuro

### 5.1 Conclusões

1. **Progresso significativo**: +20pp taxa de aprovação, +0.081 F1 desde baseline
2. **MIS reduzido drasticamente**: 17 → 9 (-8 entidades perdidas)
3. **Pipeline híbrido funciona**: NER + Regex + Checksum se complementam
4. **Modelo NER é robusto para datas**: Necessita apenas regex para romanos

### 5.2 Gap Restante

| Para atingir meta | Necessário |
|-------------------|------------|
| Taxa aprovação 70% | +21.4pp mais |
| F1 0.70 | +0.155 mais |
| Equivalente a | ~8-10 COR adicionais |

### 5.3 Próximos Passos Potenciais

| Prioridade | Melhoria | Impacto Estimado |
|------------|----------|------------------|
| ALTA | Refinamento limites (PAR→COR) | +5-6 COR |
| MÉDIA | Data augmentation modelo | +3-4 COR |
| MÉDIA | Corrigir classificação CIF | +1 COR |
| BAIXA | Melhorar detecção phone_intl | +1 COR |

---

## 6. Referências

1. **Testes standalone:** `scripts/preprocess/spanish_date_patterns.py`
2. **Testes integração:** `scripts/evaluate/test_date_integration.py`
3. **TIMEX3:** Padrão de anotação ISO-TimeML
4. **HeidelTime/SUTime:** Taggers temporais de referência

---

**Tempo de execução:** 2.51s (integração) + 1.4s (adversarial)
**Gerado por:** AlexAlves87
**Data:** 05-02-2026
