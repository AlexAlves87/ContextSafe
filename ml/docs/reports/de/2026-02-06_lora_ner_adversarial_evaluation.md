# LoRA Legal-XLM-RoBERTa NER - Adversariale Evaluierung

**Datum:** 06.02.2026
**Modell:** lora_ner_v1 (Legal-XLM-RoBERTa-base + LoRA r=128)
**Tests:** 35
**Zeit:** 1,2s

---

## 1. Baseline-Vergleich

| Modell | F1 Strikt | Precision | Recall | Pass Rate | Delta |
|--------|-----------|-----------|--------|-----------|-------|
| **LoRA NER v1** | **0,016** | 0,017 | 0,015 | 5,7% | - |
| legal_ner_v2 | 0,788 | - | - | 60,0% | -0,772 |
| GLiNER zero-shot | 0,325 | - | - | 11,4% | -0,309 |

## 2. SemEval Zählungen

| Metrik | Wert |
|--------|------|
| COR | 1 |
| INC | 0 |
| PAR | 50 |
| MIS | 16 |
| SPU | 9 |

## 3. Ergebnisse nach Kategorie

| Kategorie | Pass Rate | COR | MIS | SPU |
|-----------|-----------|-----|-----|-----|
| edge_case | 0% | 0 | 2 | 1 |
| adversarial | 25% | 0 | 1 | 3 |
| ocr_corruption | 0% | 1 | 5 | 0 |
| unicode_evasion | 0% | 0 | 3 | 0 |
| real_world | 0% | 0 | 5 | 5 |

## 4. Fehlgeschlagene Tests

| Test | Kat | COR | INC | PAR | MIS | SPU | Detail |
|------|-----|-----|-----|-----|-----|-----|--------|
| single_letter_name | edge | 0 | 0 | 1 | 0 | 0 | PAR: 1 |
| very_long_name | edge | 0 | 0 | 1 | 0 | 0 | PAR: 1 |
| dni_without_letter | edge | 0 | 0 | 0 | 1 | 0 | MIS: ['12345678'] |
| dni_with_spaces | edge | 0 | 0 | 1 | 0 | 0 | PAR: 1 |
| iban_with_spaces | edge | 0 | 0 | 1 | 0 | 0 | PAR: 1 |
| phone_internationa | edge | 0 | 0 | 1 | 1 | 0 | MIS: ['+34 612 345 678']; PAR: 1 |
| date_roman_numeral | edge | 0 | 0 | 1 | 0 | 1 | SPU: ['ía']; PAR: 1 |
| date_ordinal | edge | 0 | 0 | 1 | 0 | 0 | PAR: 1 |
| address_floor_door | edge | 0 | 0 | 3 | 0 | 0 | PAR: 3 |
| example_dni | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['2345678X'] |
| fictional_person | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['on Quijote de la Mancha'] |
| organization_as_pe | adve | 0 | 0 | 0 | 1 | 0 | MIS: ['García y Asociados, S.L.'] |
| location_as_person | adve | 0 | 0 | 1 | 0 | 0 | PAR: 1 |
| numbers_not_dni | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['2345678'] |
| mixed_languages | adve | 0 | 0 | 3 | 0 | 0 | PAR: 3 |
| ocr_letter_substit | ocr_ | 0 | 0 | 1 | 1 | 0 | MIS: ['12345678Z']; PAR: 1 |
| ocr_zero_o_confusi | ocr_ | 0 | 0 | 0 | 1 | 0 | MIS: ['ES91 21O0 0418 45O2 OOO5 133... |
| ocr_missing_spaces | ocr_ | 0 | 0 | 1 | 1 | 0 | MIS: ['12345678X']; PAR: 1 |
| ocr_extra_spaces | ocr_ | 0 | 0 | 0 | 2 | 0 | MIS: ['1 2 3 4 5 6 7 8 Z', 'M a r í... |
| ocr_accent_loss | ocr_ | 1 | 0 | 1 | 0 | 0 | PAR: 1 |
| cyrillic_o | unic | 0 | 0 | 1 | 1 | 0 | MIS: ['12345678Х']; PAR: 1 |
| zero_width_space | unic | 0 | 0 | 1 | 1 | 0 | MIS: ['María García']; PAR: 1 |
| fullwidth_numbers | unic | 0 | 0 | 1 | 1 | 0 | MIS: ['１２３４５６７８Z']; PAR: 1 |
| notarial_header | real | 0 | 0 | 3 | 1 | 0 | MIS: ['Sevilla']; PAR: 3 |
| testament_comparec | real | 0 | 0 | 4 | 1 | 0 | MIS: ['12345678-Z']; PAR: 4 |
| judicial_sentence_ | real | 0 | 0 | 4 | 0 | 2 | SPU: ['º 123/2024', 'ala Primera de... |
| contract_parties | real | 0 | 0 | 7 | 1 | 0 | MIS: ['Madrid']; PAR: 7 |
| bank_account_claus | real | 0 | 0 | 3 | 0 | 0 | PAR: 3 |
| cadastral_referenc | real | 0 | 0 | 2 | 0 | 1 | SPU: ['úmero 12345']; PAR: 2 |
| professional_ids | real | 0 | 0 | 4 | 0 | 1 | SPU: ['olegio de Procuradores de Ma... |
| ecli_citation | real | 0 | 0 | 1 | 1 | 1 | MIS: ['ECLI:ES:TS:2023:1234']; SPU:... |
| vehicle_clause | real | 0 | 0 | 1 | 1 | 0 | MIS: ['1234 ABC']; PAR: 1 |
| social_security | real | 0 | 0 | 1 | 0 | 0 | PAR: 1 |

---

**Generiert von:** `scripts/evaluate/evaluate_lora_ner_adversarial.py`
