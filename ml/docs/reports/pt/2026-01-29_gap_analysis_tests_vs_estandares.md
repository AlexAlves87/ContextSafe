# Gap Analysis: Testes Atuais vs Padrões Académicos

**Data:** 29-01-2026
**Autor:** AlexAlves87
**Ficheiro analisado:** `scripts/evaluate/test_ner_predictor_adversarial.py`

---

## 1. Resumo de Gaps

| Aspeto | Padrão Académico | Implementação Atual | Severidade |
|--------|------------------|---------------------|------------|
| Modo de avaliação | Strict (SemEval 2013) | Lenient (custom) | **CRÍTICO** |
| 4 Modos SemEval | strict, exact, partial, type | Apenas 1 modo custom | ALTO |
| Biblioteca métricas | seqeval ou nervaluate | Implementação custom | ALTO |
| Métricas detalhadas | COR/INC/PAR/MIS/SPU | Apenas TP/FP/FN | MÉDIO |
| Métricas por tipo | F1 por PERSON, DNI, etc. | Apenas F1 agregado | MÉDIO |
| Referência NoiseBench | EMNLP 2024 | "ICLR 2024" (erro) | BAIXO |
| Documentação modo | Explícito no relatório | Não documentado | MÉDIO |

---

## 2. Análise Detalhada

### 2.1 CRÍTICO: Modo de Matching Não É Strict

**Código atual (linhas 458-493):**

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
1. Permite **containment** (Se "José García" está em "Don José García López", conta como match)
2. Permite **80% character overlap** (não é fronteira exata)
3. Permite **tolerância de 5 caracteres** em comprimento

**Padrão SemEval Strict:**
> "Exact boundary surface string match AND entity type match"

**Impacto:** Os resultados atuais (F1=0.784, 54.3% pass) poderiam ser **INFLACIONADOS** porque se aceitam matches parciais como corretos.

### 2.2 ALTO: Não Usa seqeval nem nervaluate

**Padrão:** Usar bibliotecas validadas contra conlleval.

**Atual:** Implementação custom de métricas.

**Risco:** As métricas custom podem não ser comparáveis com literatura académica.

### 2.3 ALTO: Apenas Um Modo de Avaliação

**SemEval 2013 define 4 modos:**

| Modo | Boundary | Type | Uso |
|------|----------|------|-----|
| **strict** | Exato | Exato | Principal, rigoroso |
| exact | Exato | Ignorado | Análise boundary |
| partial | Overlap | Ignorado | Análise lenient |
| type | Overlap | Exato | Análise classificação |

**Atual:** Apenas um modo custom (similar a partial/lenient).

**Impacto:** Não podemos separar erros de boundary vs erros de type.

### 2.4 MÉDIO: Sem Métricas COR/INC/PAR/MIS/SPU

**SemEval 2013:**
- **COR**: Correct (boundary E type exatos)
- **INC**: Incorrect (boundary exato, type incorreto)
- **PAR**: Partial (boundary com overlap)
- **MIS**: Missing (FN)
- **SPU**: Spurious (FP)

**Atual:** Apenas TP/FP/FN (não distingue INC de PAR).

### 2.5 MÉDIO: Sem Métricas por Tipo de Entidade

**Padrão:** Reportar F1 para cada tipo (PERSON, DNI_NIE, IBAN, etc.)

**Atual:** Apenas F1 agregado.

**Impacto:** Não sabemos que tipos de entidade têm pior desempenho.

### 2.6 BAIXO: Erro em Referência

**Linha 10:** `NoiseBench (ICLR 2024)`

**Correto:** `NoiseBench (EMNLP 2024)`

---

## 3. Impacto nos Resultados Reportados

### 3.1 Estimativa de Diferença Strict vs Lenient

Baseado na literatura, modo strict tipicamente produz **5-15% menos F1** que lenient:

| Métrica | Atual (lenient) | Estimado (strict) |
|---------|-----------------|-------------------|
| F1 | 0.784 | 0.67-0.73 |
| Pass rate | 54.3% | 40-48% |

**Os resultados atuais são otimistas.**

### 3.2 Testes Afetados por Matching Lenient

Testes onde o matching lenient aceita como correto o que strict rejeitaria:

| Teste | Situação | Impacto |
|-------|----------|---------|
| `very_long_name` | Nome longo, boundary exato? | Possível |
| `address_floor_door` | Morada complexa | Possível |
| `testament_comparecencia` | Múltiplas entidades | Alto |
| `judicial_sentence_header` | Datas textuais | Alto |

---

## 4. Plano de Correção

### 4.1 Mudanças Requeridas

1. **Implementar modo strict** (prioridade CRÍTICA)
   - Boundary deve ser exato (normalizado)
   - Type deve ser exato

2. **Adicionar nervaluate** (prioridade ALTA)
   ```bash
   pip install nervaluate
   ```

3. **Reportar 4 modos** (prioridade ALTA)
   - strict (principal)
   - exact
   - partial
   - type

4. **Adicionar métricas por tipo** (prioridade MÉDIA)

5. **Corrigir referência NoiseBench** (prioridade BAIXA)

### 4.2 Estratégia de Migração

Para manter comparabilidade com resultados anteriores:

1. Executar com **ambos os modos** (lenient E strict)
2. Reportar **ambos** na documentação
3. Usar **strict como métrica principal** de agora em diante
4. Documentar diferença para baseline

---

## 5. Novo Script Proposto

Criar `test_ner_predictor_adversarial_v2.py` com:

1. Modo strict por defeito
2. Integração com nervaluate
3. Métricas COR/INC/PAR/MIS/SPU
4. F1 por tipo de entidade
5. Opção de modo legacy para comparação

---

## 6. Conclusões

**Os resultados atuais (F1=0.784, 54.3% pass) não são comparáveis com literatura académica** porque:

1. Usam matching lenient, não strict
2. Não usam bibliotecas padrão (seqeval, nervaluate)
3. Não reportam métricas granulares (por tipo, COR/INC/PAR)

**Ação imediata:** Antes de continuar com integração de TextNormalizer, devemos:

1. Criar script v2 com padrões académicos
2. Re-estabelecer baseline com modo strict
3. DEPOIS avaliar impacto de melhorias

---

**Gerado por:** AlexAlves87
**Data:** 29-01-2026
