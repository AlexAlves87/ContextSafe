# Avaliação Baseline GLiNER-PII

**Data:** 24-01-2026
**Modelo:** knowledgator/gliner-pii-base-v1.0
**Limiar (Threshold):** 0.3 (equilibrado)
**Testes:** 35
**Tempo:** 3.8s

---

## 1. Resumo Executivo

### Comparação com legal_ner_v2

| Modelo | F1 Estrito | Precisão | Revocação | Taxa de Aprovação |
|--------|-----------|-----------|--------|-----------|
| **GLiNER-PII-base** | **0.325** | 0.287 | 0.373 | 11.4% |
| legal_ner_v2 | 0.788 | - | - | 60.0% |
| **Diferença** | **-0.463** | - | - | -48.6pp |

### Contagens SemEval

| Métrica | Valor | Descrição |
|---------|-------|-------------|
| COR | 25 | Correto (fronteira + tipo) |
| INC | 4 | Fronteira OK, tipo incorreto |
| PAR | 24 | Correspondência parcial |
| MIS | 14 | Perdidos (FN) |
| SPU | 34 | Espúrios (FP) |

---

## 2. Resultados por Categoria

| Categoria | Estrito | COR | INC | PAR | MIS | SPU |
|-----------|--------|-----|-----|-----|-----|-----|
| edge_case | 22% | 5 | 0 | 3 | 4 | 5 |
| adversarial | 0% | 1 | 0 | 3 | 1 | 9 |
| ocr_corruption | 0% | 2 | 0 | 4 | 3 | 2 |
| unicode_evasion | 67% | 5 | 0 | 1 | 0 | 1 |
| real_world | 0% | 12 | 4 | 13 | 6 | 17 |

---

## 3. Testes Reprovados (Estrito)

| Teste | Cat | COR | INC | PAR | MIS | SPU | Detalhe |
|------|-----|-----|-----|-----|-----|-----|---------|
| very_long_name | edge | 0 | 0 | 1 | 0 | 5 | SPU: ['Don', 'Trinidad', 'Fernández... |
| dni_with_spaces | edge | 0 | 0 | 0 | 1 | 0 | MIS: ['12 345 678 Z'] |
| iban_with_spaces | edge | 0 | 0 | 0 | 1 | 0 | MIS: ['ES91 2100 0418 4502 0005 133... |
| phone_international | edge | 1 | 0 | 0 | 1 | 0 | MIS: ['0034612345678'] |
| date_roman_numerals | edge | 0 | 0 | 1 | 0 | 0 | PAR: 1 |
| date_ordinal | edge | 0 | 0 | 1 | 0 | 0 | PAR: 1 |
| address_floor_door | edge | 2 | 0 | 0 | 1 | 0 | MIS: ['Calle Mayor 15, 3º B'] |
| negation_dni | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['NIE'] |
| example_dni | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['12345678X'] |
| fictional_person | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['Don'] |
| organization_as_pers | adve | 0 | 0 | 1 | 0 | 1 | SPU: ['demanda']; PAR: 1 |
| location_as_person | adve | 0 | 0 | 1 | 0 | 0 | PAR: 1 |
| date_in_reference | adve | 0 | 0 | 0 | 0 | 2 | SPU: ['15/2022', '12 de julio'] |
| numbers_not_dni | adve | 0 | 0 | 0 | 0 | 2 | SPU: ['12345678', '9'] |
| mixed_languages | adve | 1 | 0 | 1 | 1 | 1 | MIS: ['UK123456789']; SPU: ['Smith'... |
| ocr_letter_substitut | ocr_ | 1 | 0 | 1 | 0 | 2 | SPU: ['DNl', 'García']; PAR: 1 |
| ocr_zero_o_confusion | ocr_ | 0 | 0 | 1 | 0 | 0 | PAR: 1 |
| ocr_missing_spaces | ocr_ | 0 | 0 | 1 | 1 | 0 | MIS: ['12345678X']; PAR: 1 |
| ocr_extra_spaces | ocr_ | 0 | 0 | 0 | 2 | 0 | MIS: ['1 2 3 4 5 6 7 8 Z', 'M a r í... |
| ocr_accent_loss | ocr_ | 1 | 0 | 1 | 0 | 0 | PAR: 1 |
| ... | ... | ... | ... | ... | ... | ... | (mais 11) |

---

## 4. Análise

### Pontos Fortes do GLiNER

- Zero-shot: Não requer treino para novos tipos de entidade
- Multilingue: Suporte nativo para espanhol
- Etiquetas flexíveis: Especificadas em tempo de execução

### Pontos Fracos Observados

- Formatos espanhóis específicos (DNI, NIE, IBAN com espaços)
- Datas textuais em espanhol (XV de marzo de MMXXIV)
- Identificadores legais espanhóis (ECLI, referências cadastrais)
- Contexto negativo (NO tener DNI)

### Recomendação

O legal_ner_v2 supera o GLiNER zero-shot (0.325 F1). O fine-tuning específico para o domínio legal espanhol acrescenta valor.

> **Nota posterior (04-02-2026):** Foi testado o fine-tuning LoRA do Legal-XLM-RoBERTa-base: F1 0.016 adversarial (overfitting severo). Descartado. O modelo base do pipeline continua a ser o RoBERTa-BNE CAPITEL NER (`legal_ner_v2`).

---

## 5. Configuração

```python
# Etiquetas usadas (mapeamento para tipos ContextSafe)
GLINER_LABELS = ['phone_number', 'national id', 'zip code', 'company_name', 'date_of_birth', 'certificate_license_number', 'social security number', 'account_number', 'case number', 'ssn', 'address', 'location state', 'postal code', 'email', 'vehicle_identifier', 'city', 'phone number', 'date', 'vehicle id', 'dob', 'professional id', 'license number', 'property id', 'email address', 'location city', 'organization', 'name', 'company', 'national_id', 'court case id', 'iban', 'street_address', 'last name', 'location address', 'postcode', 'license_plate', 'unique_identifier', 'first name', 'country', 'cadastral reference', 'bank account']

# Limiar (Threshold)
threshold = 0.3  # Equilibrado (recomendado para produção)
```

---

**Gerado por:** `scripts/evaluate/evaluate_gliner_baseline.py`
**Data:** 24-01-2026
