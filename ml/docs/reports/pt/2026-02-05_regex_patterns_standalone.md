# Padrões Regex para Identificadores Espanhóis - Teste Standalone

**Data:** 05-02-2026
**Autor:** AlexAlves87
**Componente:** `scripts/preprocess/spanish_id_patterns.py`
**Padrão:** CHPDA (2025) - Abordagem híbrida regex+NER

---

## 1. Resumo Executivo

Implementação de padrões regex para detectar identificadores espanhóis com formatos variantes (espaços, hifens, pontos) que os modelos NER transformer tipicamente não detectam.

### Resultados

| Métrica | Valor |
|---------|-------|
| **Testes Aprovados** | 22/22 (100%) |
| **Tipos de Entidade** | 5 (DNI_NIE, IBAN, NSS, CIF, PHONE) |
| **Padrões Totais** | 25 |
| **Tempo Execução** | 0.003s |

### Conclusão

> **Todos os padrões funcionam corretamente para formatos com espaços e separadores.**
> Isso complementa o NER transformer que falha em casos como "12 345 678 Z" ou "ES91 2100 0418...".

---

## 2. Metodologia

### 2.1 Pesquisa Base

| Artigo | Abordagem | Aplicação |
|--------|-----------|-----------|
| **CHPDA (arXiv 2025)** | Híbrido Regex + AI NER | Reduz falsos positivos |
| **Hybrid ReGex (JCO 2025)** | Pipeline leve regex + ML | Extração dados médicos |
| **Legal NLP Survey (2024)** | NER especializado legal | Padrões regulatórios |

### 2.2 Padrões Implementados

| Tipo | Padrões | Exemplos |
|------|---------|----------|
| **DNI** | 6 | `12345678Z`, `12 345 678 Z`, `12.345.678-Z` |
| **NIE** | 3 | `X1234567Z`, `X 1234567 Z`, `X-1234567-Z` |
| **IBAN** | 3 | `ES9121...`, `ES91 2100 0418...` |
| **NSS** | 3 | `281234567890`, `28/12345678/90` |
| **CIF** | 3 | `A12345674`, `A-1234567-4` |
| **PHONE** | 7 | `612345678`, `612 345 678`, `+34 612...` |

### 2.3 Reprodutibilidade

```bash
# Ambiente
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Execução
python scripts/preprocess/spanish_id_patterns.py

# Saída esperada: 22/22 passed (100.0%)
```

---

## 3. Resultados

### 3.1 Testes por Tipo

| Tipo | Testes | Aprovados | Exemplos Chave |
|------|--------|-----------|----------------|
| DNI | 6 | 6 | Padrão, espaços 2-3-3, pontos |
| NIE | 3 | 3 | Padrão, espaços, hifens |
| IBAN | 2 | 2 | Padrão, espaços grupos 4 |
| NSS | 2 | 2 | Barras, espaços |
| CIF | 2 | 2 | Padrão, hifens |
| PHONE | 4 | 4 | Móvel, fixo, internacional |
| Negativos | 2 | 2 | Rejeita formatos inválidos |
| Multi | 1 | 1 | Múltiplas entidades no texto |

### 3.2 Demo de Detecção

| Input | Detecção | Normalizado |
|-------|----------|-------------|
| `DNI 12 345 678 Z` | ✅ DNI_NIE | `12345678Z` |
| `IBAN ES91 2100 0418 4502 0005 1332` | ✅ IBAN | `ES9121000418450200051332` |
| `NIE X-1234567-Z` | ✅ DNI_NIE | `X1234567Z` |
| `Tel: 612 345 678` | ✅ PHONE | `612345678` |
| `CIF A-1234567-4` | ✅ CIF | `A12345674` |

### 3.3 Estrutura de Match

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

## 4. Análise de Padrões

### 4.1 Níveis de Confiança

| Nível | Confiança | Critério |
|-------|-----------|----------|
| Alta | 0.95 | Formato padrão sem ambiguidade |
| Média | 0.90 | Formato com separadores válidos |
| Baixa | 0.70-0.85 | Formatos que podem ser ambíguos |

### 4.2 Padrões DNI com Espaços (Problema Original)

O teste adversarial `dni_with_spaces` falhava porque o NER não detectava "12 345 678 Z".

**Solução Implementada:**
```python
# Padrão para espaços 2-3-3
r'\b(\d{2})\s+(\d{3})\s+(\d{3})\s*([A-Z])\b'
```

Este padrão detecta:
- `12 345 678 Z` ✅
- `12 345 678Z` ✅ (sem espaço antes da letra)

### 4.3 Normalização para Checksum

Função `normalize_match()` remove separadores para validação:

```python
"12 345 678 Z" → "12345678Z"
"ES91 2100 0418..." → "ES9121000418..."
"X-1234567-Z" → "X1234567Z"
```

---

## 5. Conclusões e Trabalho Futuro

### 5.1 Conclusões

1. **25 padrões cobrem formatos variantes** de identificadores espanhóis
2. **Normalização permite integração** com validadores checksum
3. **Confiança variável** distingue formatos mais/menos confiáveis
4. **Detecção de sobreposição** evita duplicatas

### 5.2 Integração Pipeline

```
Texto Entrada
       ↓
┌──────────────────────┐
│  1. TextNormalizer   │  Limpeza Unicode/OCR
└──────────────────────┘
       ↓
┌──────────────────────┐
│  2. NER Transformer  │  Predições RoBERTalex
└──────────────────────┘
       ↓
┌──────────────────────┐
│  3. Padrões Regex    │  ← NOVO: detecta espaços
└──────────────────────┘
       ↓
┌──────────────────────┐
│  4. Merge & Dedup    │  Combina NER + Regex
└──────────────────────┘
       ↓
┌──────────────────────┐
│  5. Valid. Checksum  │  Ajusta confiança
└──────────────────────┘
       ↓
Entidades Finais
```

### 5.3 Impacto Estimado

| Teste Adversarial | Antes | Depois | Melhoria |
|-------------------|-------|--------|----------|
| `dni_with_spaces` | MIS:1 | COR:1 | +1 COR |
| `iban_with_spaces` | PAR:1 | COR:1 | +1 COR |
| `phone_international` | MIS:1 | COR:1 | +1 COR (potencial) |

**Estimativa Total:** +2-3 COR, conversão de MIS e PAR para COR.

---

## 6. Referências

1. **CHPDA (2025):** [arXiv](https://arxiv.org/html/2502.07815v1) - Abordagem híbrida regex+NER
2. **Hybrid ReGex (2025):** [JCO](https://ascopubs.org/doi/10.1200/CCI-25-00130) - Extração dados médicos
3. **Legal NLP Survey (2024):** [arXiv](https://arxiv.org/html/2410.21306v3) - NER para domínio legal

---

**Tempo de execução:** 0.003s
**Gerado por:** AlexAlves87
**Data:** 05-02-2026
