# Refinamento de Limites - Integração no Pipeline NER

**Data:** 06-02-2026
**Autor:** AlexAlves87
**Componente:** `scripts/preprocess/boundary_refinement.py` integrado em `ner_predictor.py`
**Padrão:** SemEval 2013 Task 9 (Avaliação em nível de entidade)

---

## 1. Resumo Executivo

Implementação de refinamento de limites de entidades para converter correspondências parciais (PAR) em corretas (COR) de acordo com o framework de avaliação SemEval 2013.

### Resultados

| Suíte de Testes | Resultado |
|-----------------|-----------|
| Testes standalone | 12/12 (100%) |
| Teste de integração | ✅ Funcional |
| Refinamentos aplicados | 4/8 entidades na demonstração |

### Tipos de Refinamento

| Tipo | Entidades | Ação |
|------|-----------|------|
| OVER_EXTENDED | PERSON | Remover prefixos: Don, Dña., D., Mr., Doña |
| OVER_EXTENDED | DATE | Remover prefixos: a, el día, día |
| OVER_EXTENDED | ORGANIZATION | Remover sufixos: vírgulas, pontos e vírgulas |
| OVER_EXTENDED | ADDRESS | Remover código postal+cidade no final |
| TRUNCATED | POSTAL_CODE | Estender para 5 dígitos |
| TRUNCATED | DNI_NIE | Estender para incluir dígito verificador |

---

## 2. Metodologia

### 2.1 Diagnóstico Prévio

`scripts/evaluate/diagnose_par_cases.py` foi executado para identificar padrões de erro:

```
TRUNCATED (2 casos):
  - [address_floor_door] Faltando no final: '001' (código postal)
  - [testament_comparecencia] Faltando no final: 'Z' (letra DNI)

OVER_EXTENDED (9 casos):
  - Nomes com prefixos honoríficos incluídos
  - Datas com prefixo "a" incluído
  - Organizações com vírgula final
```

### 2.2 Implementação

**Arquivo:** `scripts/preprocess/boundary_refinement.py`

```python
# Prefixos honoríficos espanhóis (ordem: mais longos primeiro)
PERSON_PREFIXES = [
    r"(?:Compareció\s+)?Don\s+",
    r"(?:Compareció\s+)?Doña\s+",
    r"Dña\.\s*",
    r"D\.\s*",
    r"Mr\.\s*",
    r"Mrs\.\s*",
    # ...
]

# Função principal
def refine_entity(text, entity_type, start, end, confidence, source, original_text):
    """Aplica refinamento de acordo com o tipo de entidade."""
    if entity_type in REFINEMENT_FUNCTIONS:
        refined_text, refinement_applied = REFINEMENT_FUNCTIONS[entity_type](text, original_text)
    # ...
```

### 2.3 Integração no Pipeline

**Arquivo:** `scripts/inference/ner_predictor.py`

```python
# Importação com degradação elegante
try:
    from preprocess.boundary_refinement import refine_entity, RefinedEntity
    REFINEMENT_AVAILABLE = True
except ImportError:
    REFINEMENT_AVAILABLE = False

# No método predict():
def predict(self, text, min_confidence=0.5, max_length=512):
    # 1. Normalização de texto
    text = normalize_text_for_ner(text)

    # 2. Predição NER
    entities = self._extract_entities(...)

    # 3. Merge Regex (híbrido)
    if REGEX_AVAILABLE:
        entities = self._merge_regex_detections(text, entities, min_confidence)

    # 4. Refinamento de limites (NOVO)
    if REFINEMENT_AVAILABLE:
        entities = self._apply_boundary_refinement(text, entities)

    return entities
```

### 2.4 Reprodutibilidade

```bash
# Ambiente
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Teste standalone
python scripts/preprocess/boundary_refinement.py

# Teste de integração
python scripts/inference/ner_predictor.py
```

---

## 3. Resultados

### 3.1 Testes Standalone (12/12)

| Teste | Entidade | Refinamento | Resultado |
|-------|----------|-------------|-----------|
| person_don | PERSON | Remover "Don " | ✅ |
| person_dña | PERSON | Remover "Dña. " | ✅ |
| person_d_dot | PERSON | Remover "D. " | ✅ |
| person_mr | PERSON | Remover "Mr. " | ✅ |
| person_no_change | PERSON | Sem mudança | ✅ |
| date_a_prefix | DATE | Remover "a " | ✅ |
| date_el_dia | DATE | Remover "el día " | ✅ |
| org_trailing_comma | ORGANIZATION | Remover "," | ✅ |
| address_with_postal_city | ADDRESS | Remover "28013 Madrid" | ✅ |
| postal_extend | POSTAL_CODE | "28" → "28001" | ✅ |
| dni_extend_letter | DNI_NIE | "12345678-" → "12345678Z" | ✅ |
| dni_no_extend | DNI_NIE | Sem mudança | ✅ |

**Tempo de execução:** 0.002s

### 3.2 Teste de Integração

| Input | Entidade Original | Entidade Refinada | Refinamento |
|-------|-------------------|-------------------|-------------|
| "Don José García López con DNI..." | "Don José García López" | "José García López" | stripped_prefix:Don |
| "Dña. Ana Martínez Ruiz..." | "Dña. Ana Martínez Ruiz" | "Ana Martínez Ruiz" | stripped_prefix:Dña. |
| "Compareció Doña María Antonia..." | "Doña María Antonia Fernández Ruiz" | "María Antonia Fernández Ruiz" | stripped_prefix:Doña |
| "Mr. John Smith, residente..." | "Mr. John Smith" | "John Smith" | stripped_prefix:Mr. |

### 3.3 Entidades Sem Refinamento (Corretas)

| Input | Entidade | Razão |
|-------|----------|-------|
| "DNI 12345678Z" | "12345678Z" | Já correto |
| "IBAN ES91 2100..." | "ES91 2100 0418 4502 0005 1332" | Já correto |
| "Calle Alcalá 50" | "Calle Alcalá 50" | Já correto |
| "Sevilla" | "Sevilla" | Já correto |

---

## 4. Análise

### 4.1 Impacto no Pipeline

O refinamento de limites é aplicado **após** o merge NER+regex, atuando como pós-processador:

```
Texto → Normalização → NER → Merge Regex → Refinamento → Entidades finais
                                              ↑
                                        (Elemento 5)
```

### 4.2 Preservação de Metadados

O refinamento preserva todos os metadados originais:
- `confidence`: Não modificado
- `source`: Não modificado (ner/regex)
- `checksum_valid`: Não modificado
- `checksum_reason`: Não modificado

Adiciona novos campos:
- `original_text`: Texto antes do refinamento
- `refinement_applied`: Tipo de refinamento aplicado

### 4.3 Observação sobre DATE

A data "a quince de marzo de dos mil veinticuatro" no teste de integração **não foi refinada** porque o modelo NER detectou "quince de marzo de dos mil veinticuatro" diretamente (sem o prefixo "a"). Isso indica que:

1. O modelo NER já aprende alguns limites corretos
2. O refinamento atua como rede de segurança para casos que o modelo não lida

---

## 5. Pipeline Completo (5 Elementos)

### 5.1 Elementos Integrados

| # | Elemento | Standalone | Integração | Função |
|---|----------|------------|------------|--------|
| 1 | TextNormalizer | 15/15 | ✅ | Evasão Unicode, homóglifos |
| 2 | Checksum Validators | 23/24 | ✅ | Ajuste de confiança |
| 3 | Regex Patterns | 22/22 | ✅ | IDs com espaços/hifens |
| 4 | Date Patterns | 14/14 | ✅ | Números romanos |
| 5 | Boundary Refinement | 12/12 | ✅ | Conversão PAR→COR |

### 5.2 Fluxo de Dados

```
Input: "Don José García López com DNI 12345678Z"
                    ↓
[1] TextNormalizer: Sem mudanças (texto limpo)
                    ↓
[Modelo NER]: Detecta "Don José García López" (PERSON), "12345678Z" (DNI_NIE)
                    ↓
[3] Merge Regex: Sem mudanças (NER já detectou DNI completo)
                    ↓
[2] Checksum: DNI válido → aumento de confiança
                    ↓
[5] Boundary Refinement: "Don José García López" → "José García López"
                    ↓
Output: [PERSON] "José García López", [DNI_NIE] "12345678Z" ✅
```

---

## 6. Conclusões

### 6.1 Conquistas

1. **Refinamento funcional**: 12/12 testes standalone, integração verificada
2. **Degradação elegante**: Sistema funciona sem o módulo (REFINEMENT_AVAILABLE=False)
3. **Preservação de metadados**: Checksum e fonte intactos
4. **Rastreabilidade**: Campos `original_text` e `refinement_applied` para auditoria

### 6.2 Limitações Conhecidas

| Limitação | Impacto | Mitigação |
|-----------|---------|-----------|
| Apenas prefixos/sufixos estáticos | Não lida com casos dinâmicos | Padrões cobrem 90%+ casos legais |
| Extensão depende do contexto | Pode falhar se texto truncado | Verificação de comprimento |
| Sem refinamento CIF | Baixa prioridade | Adicionar se padrão detectado |

### 6.3 Próximo Passo

Executar teste adversarial completo para medir impacto nas métricas:

```bash
python scripts/evaluate/test_ner_predictor_adversarial_v2.py
```

**Métricas a observar:**
- PAR (correspondências parciais) - redução esperada
- COR (correspondências corretas) - aumento esperado
- Taxa de aprovação - melhoria esperada

---

## 7. Referências

1. **SemEval 2013 Task 9**: Framework de avaliação de entidades (COR/INC/PAR/MIS/SPU)
2. **Diagnóstico PAR**: `scripts/evaluate/diagnose_par_cases.py`
3. **Implementação**: `scripts/preprocess/boundary_refinement.py`
4. **Integração**: `scripts/inference/ner_predictor.py` linhas 37-47, 385-432

---

**Tempo de execução total:** 0.002s (standalone) + 1.39s (carregar modelo) + 18.1ms (inferência)
**Gerado por:** AlexAlves87
**Data:** 06-02-2026
