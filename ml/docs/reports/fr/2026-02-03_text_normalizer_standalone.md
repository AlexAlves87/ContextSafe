# Élément 1 : Text Normalizer - Test Isolé

**Date :** 03/02/2026
**Statut :** ✅ TERMINÉ
**Temps d'exécution :** 0,002s

---

## 1. Résumé

| Métrique | Valeur |
|----------|--------|
| Tests exécutés | 15 |
| Tests passés | 15 |
| Taux de réussite | 100% |
| Temps | 0,002s |

## 2. Composant

**Fichier :** `scripts/preprocess/text_normalizer.py`

**Classe principale :** `TextNormalizer`

**Fonctionnalité :**
- Normalisation NFKC (fullwidth → ASCII)
- Suppression caractères zéro-largeur (U+200B-U+200F, U+2060-U+206F, U+FEFF)
- Mappage homoglyphes Cyrillique → Latin (17 caractères)
- NBSP → espace + réduction espaces multiples
- Suppression traits d'union conditionnels (soft hyphens)

**Préserve (critique pour NER) :**
- Casse (RoBERTa est sensible à la casse)
- Accents espagnols (María, García, etc.)
- Ponctuation légitime

## 3. Tests Validés

| Test | Catégorie | Description |
|------|-----------|-------------|
| fullwidth_dni | Unicode | `１２３４５６７８Z` → `12345678Z` |
| fullwidth_mixed | Unicode | Lettres et chiffres fullwidth |
| zero_width_in_dni | Evasion | Zéro-largeur dans DNI |
| zero_width_in_name | Evasion | Zéro-largeur dans noms |
| cyrillic_o_in_dni | Homoglyph | Cyrillique О → Latin O |
| cyrillic_mixed | Homoglyph | Texte mixte Cyrillique/Latin |
| nbsp_in_address | Spaces | NBSP → espace normal |
| multiple_spaces | Spaces | Réduction espaces multiples |
| soft_hyphen_in_word | OCR | Traits d'union conditionnels supprimés |
| combined_evasion | Combined | Multiples techniques combinées |
| preserve_accents | Preserve | Accents espagnols intacts |
| preserve_case | Preserve | Casse non modifiée |
| preserve_punctuation | Preserve | Ponctuation légale préservée |
| empty_string | Edge | Chaîne vide |
| only_spaces | Edge | Espaces seulement |

## 4. Exemple de Diagnostic

**Entrée :** `DNI: １２​３４​５６​７８Х del Sr. María`

**Sortie :** `DNI: 12345678X del Sr. María`

**Changements appliqués :**
1. Removed 3 zero-width characters
2. Applied NFKC normalization
3. Replaced 1 Cyrillic homoglyphs

## 5. Étape Suivante

Intégrer `TextNormalizer` dans le pipeline NER (`CompositeNerAdapter`) et évaluer l'impact sur les tests adversariaux.

---

**Généré par :** AlexAlves87
