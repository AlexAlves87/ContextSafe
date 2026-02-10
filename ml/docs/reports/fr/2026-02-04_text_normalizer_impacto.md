# Évaluation d'Impact : Text Normalizer

**Date :** 04/02/2026
**Auteur :** AlexAlves87
**Composant :** `TextNormalizer` (Normalisation Unicode/OCR)
**Standard :** SemEval 2013 Task 9 (mode strict)

---

## 1. Résumé Exécutif

Évaluation de l'impact de l'intégration du `TextNormalizer` dans le pipeline NER pour améliorer la robustesse face aux caractères Unicode et aux artefacts OCR.

### Résultats

| Métrique | Baseline | +Normalizer | Delta | Changement |
|----------|----------|-------------|-------|------------|
| **Taux de Réussite (strict)** | 28,6% | **34,3%** | **+5,7pp** | +20% relatif |
| **F1 (strict)** | 0,464 | **0,492** | **+0,028** | +6% relatif |
| F1 (partiel) | 0,632 | 0,659 | +0,027 | +4,3% relatif |
| COR | 29 | 31 | +2 | Plus de détections exactes |
| MIS | 17 | 15 | -2 | Moins d'entités manquées |
| SPU | 8 | 7 | -1 | Moins de faux positifs |

### Conclusion

> **Le TextNormalizer améliore significativement la robustesse du modèle NER.**
> Taux de réussite +5,7pp, F1 +0,028. Deux tests d'évasion Unicode passent maintenant.

---

## 2. Méthodologie

### 2.1 Conception Expérimentale

| Aspect | Spécification |
|--------|---------------|
| Variable Indépendante | TextNormalizer (ON/OFF) |
| Variable Dépendante | Métriques SemEval 2013 |
| Modèle | legal_ner_v2 (RoBERTalex) |
| Dataset | 35 tests adversariaux |
| Standard | SemEval 2013 Task 9 (strict) |

### 2.2 Composant Évalué

**Fichier :** `scripts/inference/ner_predictor.py` → fonction `normalize_text_for_ner()`

**Opérations Appliquées :**
1. Suppression caractères zéro-largeur (U+200B-U+200F, U+2060-U+206F, U+FEFF)
2. Normalisation NFKC (fullwidth → ASCII)
3. Mappage homoglyphes (Cyrillique → Latin)
4. Normalisation espaces (NBSP → espace, réduction multiples)
5. Suppression traits d'union conditionnels

### 2.3 Reproductibilité

```bash
# Environnement
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Exécution
python scripts/evaluate/test_ner_predictor_adversarial_v2.py

# Sortie : docs/reports/YYYY-MM-DD_adversarial_v2_academic_rN.md
```

---

## 3. Résultats

### 3.1 Comparaison Détaillée par Métrique SemEval

| Métrique | Baseline | +Normalizer | Delta |
|----------|----------|-------------|-------|
| COR (Correct) | 29 | 31 | **+2** |
| INC (Incorrect) | 0 | 0 | 0 |
| PAR (Partiel) | 21 | 21 | 0 |
| MIS (Manqué) | 17 | 15 | **-2** |
| SPU (Fallacieux) | 8 | 7 | **-1** |
| POS (Possible) | 67 | 67 | 0 |
| ACT (Actuel) | 58 | 59 | +1 |

### 3.2 Tests Améliorés

| Test | Baseline | +Normalizer | Amélioration |
|------|----------|-------------|--------------|
| `cyrillic_o` | ❌ COR:1 PAR:1 | ✅ COR:2 | **Mappage homoglyphes fonctionne** |
| `zero_width_space` | ❌ COR:2 SPU:1 | ✅ COR:2 SPU:0 | **Suppression zéro-largeur fonctionne** |
| `fullwidth_numbers` | ❌ MIS:2 | ❌ COR:1 MIS:1 | Amélioration partielle (+1 COR) |

### 3.3 Tests Sans Changement Significatif

| Test | Statut | Raison |
|------|--------|--------|
| `ocr_extra_spaces` | ❌ MIS:2 | Nécessite normalisation espaces dans entités |
| `ocr_zero_o_confusion` | ❌ MIS:1 | Nécessite correction OCR O↔0 contextuelle |
| `dni_with_spaces` | ❌ MIS:1 | Espaces internes dans DNI non réduits |

### 3.4 Résultats par Catégorie

| Catégorie | Baseline Strict | +Normalizer Strict | Delta |
|-----------|-----------------|--------------------|-------|
| adversarial | 75% | 75% | 0 |
| edge_case | 22% | 22% | 0 |
| ocr_corruption | 40% | 40% | 0 |
| real_world | 10% | 10% | 0 |
| **unicode_evasion** | 0% | **67%** | **+67pp** |

**Découverte Clé :** L'impact est concentré sur `unicode_evasion` (+67pp), qui était l'objectif principal.

---

## 4. Analyse des Erreurs

### 4.1 Test `fullwidth_numbers` (Amélioration Partielle)

**Entrée :** `"DNI １２３４５６７８Z de María."`

**Attendu :**
- `"１２３４５６７８Z"` → DNI_NIE
- `"María"` → PERSON

**Détecté (avec normalizer) :**
- `"12345678Z"` → DNI_NIE ✅ (match normalisé)
- `"María"` → MIS ❌

**Analyse :** Le DNI est correctement détecté après NFKC. Le nom "María" est manqué car le modèle échoue à le détecter (problème modèle, pas normalizer).

### 4.2 Tests Toujours en Échec

| Test | Problème | Solution Requise |
|------|----------|------------------|
| `dni_with_spaces` | "12 345 678 Z" non reconnu | Regex pour DNI avec espaces |
| `date_roman_numerals` | Dates avec chiffres romains | Data augmentation |
| `ocr_zero_o_confusion` | IBAN avec mélange O/0 | Post-correction OCR |

---

## 5. Conclusions et Travaux Futurs

### 5.1 Conclusions

1. **TextNormalizer atteint son but** pour évasion Unicode :
   - `cyrillic_o` : ❌ → ✅
   - `zero_width_space` : ❌ → ✅
   - Catégorie `unicode_evasion` : 0% → 67%

2. **Impact global modéré mais positif :**
   - F1 strict : +0,028 (+6%)
   - Taux de réussite : +5,7pp (+20% relatif)

3. **Ne résout pas les problèmes OCR** (attendu) :
   - `ocr_extra_spaces`, `ocr_zero_o_confusion` nécessitent techniques additionnelles

### 5.2 Travaux Futurs

| Priorité | Amélioration | Impact Estimé |
|----------|--------------|---------------|
| HAUTE | Regex pour DNI/IBAN avec espaces | +2-3 COR |
| HAUTE | Validation checksum (réduire SPU) | -2-3 SPU |
| MOYENNE | Data augmentation pour dates textuelles | +3-4 COR |
| BASSE | Post-correction OCR (O↔0) | +1-2 COR |

### 5.3 Objectif Mis à Jour

| Métrique | Avant | Maintenant | Objectif Niveau 4 | Écart |
|----------|-------|------------|-------------------|-------|
| F1 (strict) | 0,464 | **0,492** | ≥0,70 | -0,208 |
| Taux de réussite | 28,6% | **34,3%** | ≥70% | -35,7pp |

---

## 6. Références

1. **Recherche de base :** `docs/reports/2026-01-27_investigacion_text_normalization.md`
2. **Composant autonome :** `scripts/preprocess/text_normalizer.py`
3. **Intégration production :** `src/contextsafe/infrastructure/nlp/text_normalizer.py`
4. **Formes de Normalisation Unicode UAX #15 :** https://unicode.org/reports/tr15/

---

**Temps d'évaluation :** 1,3s
**Généré par :** AlexAlves87
**Date :** 04/02/2026
