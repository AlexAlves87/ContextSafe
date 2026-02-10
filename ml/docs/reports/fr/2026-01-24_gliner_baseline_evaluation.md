# Évaluation de Référence GLiNER-PII

**Date :** 2026-01-24
**Modèle :** knowledgator/gliner-pii-base-v1.0
**Seuil :** 0.3 (équilibré)
**Tests :** 35
**Temps :** 3.8s

---

## 1. Résumé Exécutif

### Comparaison avec legal_ner_v2

| Modèle | F1 Strict | Précision | Rappel | Taux de Réussite |
|--------|-----------|-----------|--------|-----------|
| **GLiNER-PII-base** | **0.325** | 0.287 | 0.373 | 11.4% |
| legal_ner_v2 | 0.788 | - | - | 60.0% |
| **Différence** | **-0.463** | - | - | -48.6pp |

### Décomptes SemEval

| Métrique | Valeur | Description |
|--------|-------|-------------|
| COR | 25 | Correct (limite + type) |
| INC | 4 | Limite OK, type incorrect |
| PAR | 24 | Correspondance partielle |
| MIS | 14 | Manqué (FN) |
| SPU | 34 | Spurious (FP) |

---

## 2. Résultats par Catégorie

| Catégorie | Strict | COR | INC | PAR | MIS | SPU |
|----------|--------|-----|-----|-----|-----|-----|
| edge_case | 22% | 5 | 0 | 3 | 4 | 5 |
| adversarial | 0% | 1 | 0 | 3 | 1 | 9 |
| ocr_corruption | 0% | 2 | 0 | 4 | 3 | 2 |
| unicode_evasion | 67% | 5 | 0 | 1 | 0 | 1 |
| real_world | 0% | 12 | 4 | 13 | 6 | 17 |

---

## 3. Tests Échoués (Strict)

| Test | Cat | COR | INC | PAR | MIS | SPU | Détail |
|------|-----|-----|-----|-----|-----|-----|--------|
| very_long_name | edge | 0 | 0 | 1 | 0 | 5 | SPU : ['Don', 'Trinidad', 'Fernández... |
| dni_with_spaces | edge | 0 | 0 | 0 | 1 | 0 | MIS : ['12 345 678 Z'] |
| iban_with_spaces | edge | 0 | 0 | 0 | 1 | 0 | MIS : ['ES91 2100 0418 4502 0005 133... |
| phone_international | edge | 1 | 0 | 0 | 1 | 0 | MIS : ['0034612345678'] |
| date_roman_numerals | edge | 0 | 0 | 1 | 0 | 0 | PAR : 1 |
| date_ordinal | edge | 0 | 0 | 1 | 0 | 0 | PAR : 1 |
| address_floor_door | edge | 2 | 0 | 0 | 1 | 0 | MIS : ['Calle Mayor 15, 3º B'] |
| negation_dni | adve | 0 | 0 | 0 | 0 | 1 | SPU : ['NIE'] |
| example_dni | adve | 0 | 0 | 0 | 0 | 1 | SPU : ['12345678X'] |
| fictional_person | adve | 0 | 0 | 0 | 0 | 1 | SPU : ['Don'] |
| organization_as_pers | adve | 0 | 0 | 1 | 0 | 1 | SPU : ['demanda'] ; PAR : 1 |
| location_as_person | adve | 0 | 0 | 1 | 0 | 0 | PAR : 1 |
| date_in_reference | adve | 0 | 0 | 0 | 0 | 2 | SPU : ['15/2022', '12 de julio'] |
| numbers_not_dni | adve | 0 | 0 | 0 | 0 | 2 | SPU : ['12345678', '9'] |
| mixed_languages | adve | 1 | 0 | 1 | 1 | 1 | MIS : ['UK123456789'] ; SPU : ['Smith'... |
| ocr_letter_substitut | ocr_ | 1 | 0 | 1 | 0 | 2 | SPU : ['DNl', 'García'] ; PAR : 1 |
| ocr_zero_o_confusion | ocr_ | 0 | 0 | 1 | 0 | 0 | PAR : 1 |
| ocr_missing_spaces | ocr_ | 0 | 0 | 1 | 1 | 0 | MIS : ['12345678X'] ; PAR : 1 |
| ocr_extra_spaces | ocr_ | 0 | 0 | 0 | 2 | 0 | MIS : ['1 2 3 4 5 6 7 8 Z', 'M a r í... |
| ocr_accent_loss | ocr_ | 1 | 0 | 1 | 0 | 0 | PAR : 1 |
| ... | ... | ... | ... | ... | ... | ... | (11 de plus) |

---

## 4. Analyse

### Forces de GLiNER

- Zero-shot : Ne nécessite pas d'entraînement pour les nouveaux types d'entités
- Multilingue : Support natif de l'espagnol
- Labels flexibles : Spécifiés à l'exécution

### Faiblesses observées

- Formats espagnols spécifiques (DNI, NIE, IBAN avec espaces)
- Dates textuelles en espagnol (XV de marzo de MMXXIV)
- Identifiants juridiques espagnols (ECLI, références cadastrales)
- Contexte négatif (NO tener DNI)

### Recommandation

legal_ner_v2 surpasse GLiNER zero-shot (0.325 F1). Le fine-tuning spécifique au domaine juridique espagnol apporte de la valeur.

> **Note ultérieure (2026-02-04) :** Le fine-tuning LoRA de Legal-XLM-RoBERTa-base a été testé : F1 0.016 adversarial (sur-apprentissage sévère). Rejeté. Le modèle de base du pipeline reste RoBERTa-BNE CAPITEL NER (`legal_ner_v2`).

---

## 5. Configuration

```python
# Labels utilisés (mapping vers types ContextSafe)
GLINER_LABELS = ['phone_number', 'national id', 'zip code', 'company_name', 'date_of_birth', 'certificate_license_number', 'social security number', 'account_number', 'case number', 'ssn', 'address', 'location state', 'postal code', 'email', 'vehicle_identifier', 'city', 'phone number', 'date', 'vehicle id', 'dob', 'professional id', 'license number', 'property id', 'email address', 'location city', 'organization', 'name', 'company', 'national_id', 'court case id', 'iban', 'street_address', 'last name', 'location address', 'postcode', 'license_plate', 'unique_identifier', 'first name', 'country', 'cadastral reference', 'bank account']

# Seuil
threshold = 0.3  # Équilibré (recommandé pour la production)
```

---

**Généré par :** `scripts/evaluate/evaluate_gliner_baseline.py`
**Date :** 2026-01-24
