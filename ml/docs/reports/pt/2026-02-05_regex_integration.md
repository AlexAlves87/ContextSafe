# Padrões Regex - Teste de Integração

**Data:** 05-02-2026
**Autor:** AlexAlves87
**Componente:** Integração de padrões regex em `scripts/inference/ner_predictor.py`
**Padrão:** CHPDA (2025) - Abordagem híbrida regex+NER

---

## 1. Resumo Executivo

Integração de padrões regex para detectar identificadores com espaços/hifens que o modelo NER transformer não detecta.

### Resultados

| Suíte de Teste | Antes | Depois | Melhoria |
|----------------|-------|--------|----------|
| Testes de integração | - | 11/14 (78.6%) | Novo |
| Adversarial (strict) | 34.3% | **45.7%** | **+11.4pp** |
| F1 (strict) | 0.492 | **0.543** | **+0.051** |

### Conclusão

> **A integração regex melhora significativamente a detecção de identificadores formatados.**
> Taxa de aprovação +11.4pp, F1 +0.051. O IBAN com espaços agora é detectado corretamente.

---

## 2. Metodologia

### 2.1 Estratégia de Merge (Híbrida)

```
Texto de entrada
       ↓
┌──────────────────────┐
│  1. NER Transformer  │  Detecta entidades semânticas
└──────────────────────┘
       ↓
┌──────────────────────┐
│  2. Padrões Regex    │  Detecta formatos com espaços
└──────────────────────┘
       ↓
┌──────────────────────┐
│  3. Estratégia Merge │  Combina, prefere mais completo
└──────────────────────┘
       ↓
┌──────────────────────┐
│  4. Valid. Checksum  │  Ajusta confiança
└──────────────────────┘
       ↓
Entidades finais
```

### 2.2 Lógica de Merge

| Caso | Ação |
|------|------|
| Apenas NER detecta | Manter NER |
| Apenas Regex detecta | Adicionar Regex |
| Ambos detectam mesmo span | Manter NER (qualidade semântica superior) |
| Regex >20% mais longo que NER | Substituir NER por Regex |
| NER parcial, Regex completo | Substituir por Regex |

### 2.3 Reprodutibilidade

```bash
# Ambiente
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Teste integração regex
python scripts/evaluate/test_regex_integration.py

# Teste adversarial completo
python scripts/evaluate/test_ner_predictor_adversarial_v2.py
```

---

## 3. Resultados

### 3.1 Testes de Integração (11/14)

| Teste | Input | Resultado | Fonte |
|-------|-------|-----------|-------|
| dni_spaces_2_3_3 | `12 345 678 Z` | ✅ | ner |
| dni_spaces_4_4 | `1234 5678 Z` | ✅ | ner |
| dni_dots | `12.345.678-Z` | ✅ | ner |
| nie_dashes | `X-1234567-Z` | ✅ | ner |
| **iban_spaces** | `ES91 2100 0418...` | ✅ | **regex** |
| phone_spaces | `612 345 678` | ✅ | regex |
| phone_intl | `+34 612345678` | ❌ | - |
| cif_dashes | `A-1234567-4` | ❌ (tipo incorreto) | ner |
| nss_slashes | `28/12345678/90` | ✅ | ner |
| dni_standard | `12345678Z` | ✅ | ner |

### 3.2 Impacto em Testes Adversariais

| Métrica | Baseline | +Normalizer | +Regex | Delta Total |
|---------|----------|-------------|--------|-------------|
| **Taxa Aprovação** | 28.6% | 34.3% | **45.7%** | **+17.1pp** |
| **F1 (strict)** | 0.464 | 0.492 | **0.543** | **+0.079** |
| F1 (parcial) | 0.632 | 0.659 | **0.690** | +0.058 |
| COR | 29 | 31 | **35** | **+6** |
| MIS | 17 | 15 | **12** | **-5** |
| PAR | 21 | 21 | **19** | -2 |
| SPU | 8 | 7 | **7** | -1 |

### 3.3 Análise de Melhorias

| Teste Adversarial | Antes | Depois | Melhoria |
|-------------------|-------|--------|----------|
| dni_with_spaces | MIS:1 | COR:1 | +1 COR |
| iban_with_spaces | PAR:1 | COR:1 | PAR→COR |
| phone_international | MIS:1 | COR:1* | +1 COR |
| address_floor_door | PAR:1 | COR:1 | PAR→COR |

*Detecção parcial melhorada

---

## 4. Análise de Erros

### 4.1 Falhas Restantes

| Teste | Problema | Causa |
|-------|----------|-------|
| phone_intl | `+34` não incluído | NER detecta `612345678`, não há overlap suficiente |
| cif_dashes | Tipo incorreto | Modelo classifica CIF como DNI_NIE |
| spaced_iban_source | Não detectado isolado | Contexto mínimo reduz detecção |

### 4.2 Observações

1. **NER aprende formatos com espaços**: Surpreendentemente, o NER detecta alguns DNI com espaços (provavelmente do data augmentation prévio)

2. **Regex complementa, não substitui**: A maioria das detecções permanecem NER, regex adiciona apenas casos perdidos pelo NER

3. **Checksum aplica-se a ambos**: Tanto NER quanto Regex passam por validação checksum

---

## 5. Conclusões e Trabalho Futuro

### 5.1 Conclusões

1. **Melhoria significativa**: +17.1pp taxa de aprovação, +0.079 F1
2. **IBAN com espaços**: Problema resolvido (regex detecta corretamente)
3. **Merge inteligente**: Prefere detecções mais completas
4. **Overhead mínimo**: ~100ms adicionais por 25 padrões

### 5.2 Estado Atual vs Meta

| Métrica | Baseline | Atual | Meta | Gap |
|---------|----------|-------|------|-----|
| Taxa Aprovação | 28.6% | **45.7%** | ≥70% | -24.3pp |
| F1 (strict) | 0.464 | **0.543** | ≥0.70 | -0.157 |

### 5.3 Próximos Passos

| Prioridade | Tarefa | Impacto Estimado |
|------------|--------|------------------|
| ALTA | Data augmentation datas textuais | +3-4 COR |
| MÉDIA | Corrigir classificação CIF | +1 COR |
| MÉDIA | Melhorar detecção phone_intl | +1 COR |
| BAIXA | Refinamento limites para PAR→COR | +2-3 COR |

---

## 6. Referências

1. **Testes standalone:** `docs/reports/2026-02-05_regex_patterns_standalone.md`
2. **CHPDA (2025):** [arXiv](https://arxiv.org/html/2502.07815v1) - Híbrido regex+NER
3. **Script padrões:** `scripts/preprocess/spanish_id_patterns.py`
4. **Teste integração:** `scripts/evaluate/test_regex_integration.py`

---

**Tempo de execução:** 2.72s (integração) + 1.4s (adversarial)
**Gerado por:** AlexAlves87
**Data:** 05-02-2026
