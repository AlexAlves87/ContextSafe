# Analyse Adversariale de Référence : legal_ner_v2

**Date :** 2026-01-23
**Auteur :** AlexAlves87
**Version :** 1.0.0
**Modèle Évalué :** `legal_ner_v2` (RoBERTalex fine-tuned)

---

## 1. Résumé Exécutif

Ce document présente les résultats de l'évaluation adversariale du modèle `legal_ner_v2` pour la détection de PII dans des textes juridiques espagnols. L'objectif est d'établir une référence de robustesse avant d'implémenter des améliorations.

### Principales Conclusions

| Métrique | Valeur | Interprétation |
|---------|-------|----------------|
| Score F1 (niveau entité) | **0.784** | Référence acceptable |
| Précision | 0.845 | Modèle conservateur |
| Rappel | 0.731 | Zone d'amélioration prioritaire |
| Dégradation par le Bruit | 0.080 | Dans le seuil attendu (≤0.10) |
| Taux de réussite des tests | 54.3% (19/35) | Niveau 4 non atteint |

### Conclusion

Le modèle **N'ATTEINT PAS** le Niveau 4 de validation (adversarial). Des améliorations sont requises dans :
1. Normalisation de l'entrée (Unicode, espaces)
2. Reconnaissance des dates au format textuel espagnol
3. Modèles spécifiques pour NSS et CIF

---

## 2. Méthodologie

### 2.1 Conception Expérimentale

35 cas de tests adversariaux ont été conçus, répartis en 5 catégories :

| Catégorie | Tests | Objectif |
|-----------|-------|-----------|
| `edge_case` | 9 | Conditions limites (noms longs, variantes de format) |
| `adversarial` | 8 | Cas conçus pour confondre (négations, exemples) |
| `ocr_corruption` | 5 | Simulation d'erreurs OCR |
| `unicode_evasion` | 3 | Tentatives d'évasion avec des caractères similaires |
| `real_world` | 10 | Extraits de documents juridiques réels |

### 2.2 Niveaux de Difficulté

| Niveau | Critère de Succès | Tests |
|-------|-------------------|-------|
| `easy` | Détecter toutes les entités attendues | 4 |
| `medium` | Détecter toutes les entités attendues | 12 |
| `hard` | Détecter toutes les entités ET zéro faux positifs | 19 |

### 2.3 Métriques Utilisées

1. **F1 niveau entité** (style seqeval) : Précision, Rappel, F1 calculés au niveau de l'entité complète, pas du token.

2. **Score de Chevauchement** : Ratio de caractères correspondants entre l'entité attendue et détectée (Jaccard sur caractères).

3. **Dégradation par le Bruit** (style NoiseBench) : Différence de F1 entre catégories "propres" (`edge_case`, `adversarial`, `real_world`) et "bruitées" (`ocr_corruption`, `unicode_evasion`).

### 2.4 Environnement d'Exécution

| Composant | Spécification |
|------------|----------------|
| Matériel | CUDA (GPU) |
| Modèle | `legal_ner_v2` (RoBERTalex) |
| Framework | PyTorch 2.0+, Transformers |
| Temps de chargement | 1.6s |
| Temps d'évaluation | 1.5s (35 tests) |

### 2.5 Reproductibilité

```bash
cd ml
source .venv/bin/activate
python scripts/evaluate/test_ner_predictor_adversarial.py
```

Le script génère automatiquement un rapport dans `docs/reports/`.

---

## 3. Résultats

### 3.1 Métriques Agrégées

| Métrique | Valeur |
|---------|-------|
| Vrais Positifs | 49 |
| Faux Positifs | 9 |
| Faux Négatifs | 18 |
| **Précision** | 0.845 |
| **Rappel** | 0.731 |
| **Score F1** | 0.784 |
| Score Moyen de Chevauchement | 0.935 |

### 3.2 Résultats par Catégorie

| Catégorie | Taux de Réussite | TP | FP | FN | F1 |
|-----------|-----------|----|----|----|----|
| adversarial | 75.0% | 5 | 2 | 0 | 0.833 |
| edge_case | 66.7% | 9 | 1 | 3 | 0.818 |
| ocr_corruption | 40.0% | 5 | 0 | 4 | 0.714 |
| real_world | 40.0% | 26 | 5 | 9 | 0.788 |
| unicode_evasion | 33.3% | 4 | 1 | 2 | 0.727 |

### 3.3 Résultats par Difficulté

| Difficulté | Réussis | Total | Taux |
|------------|---------|-------|------|
| easy | 3 | 4 | 75.0% |
| medium | 9 | 12 | 75.0% |
| hard | 7 | 19 | 36.8% |

### 3.4 Analyse de Résistance au Bruit

| Métrique | Valeur | Référence |
|---------|-------|------------|
| F1 (texte propre) | 0.800 | - |
| F1 (bruité) | 0.720 | - |
| **Dégradation** | 0.080 | ≤0.10 (HAL Science) |
| Statut | **OK** | Dans le seuil |

---

## 4. Analyse des Erreurs

### 4.1 Taxonomie des Échecs

5 modèles d'échec récurrents ont été identifiés :

#### Modèle 1 : Dates au Format Textuel Espagnol

| Test | Entité Manquée |
|------|-----------------|
| `date_roman_numerals` | "XV de marzo del año MMXXIV" |
| `notarial_header` | "quince de marzo de dos mil veinticuatro" |
| `judicial_sentence_header` | "diez de enero de dos mil veinticuatro" |

**Cause racine :** Le modèle a été entraîné principalement avec des formats de date numériques (JJ/MM/AAAA). Les dates écrites en style notarial espagnol ne sont pas représentées dans le corpus d'entraînement.

**Impact :** Élevé dans les documents notariaux et judiciaires où ce format est standard.

#### Modèle 2 : Corruption OCR Extrême

| Test | Entité Manquée |
|------|-----------------|
| `ocr_extra_spaces` | "1 2 3 4 5 6 7 8 Z", "M a r í a" |
| `ocr_missing_spaces` | "12345678X" (dans texte concaténé) |
| `ocr_zero_o_confusion` | "ES91 21O0 0418 45O2 OOO5 1332" |

**Cause racine :** Le tokenizer de RoBERTa ne gère pas bien le texte avec un espacement anormal. La confusion O/0 brise les modèles regex IBAN.

**Impact :** Moyen. Documents scannés de basse qualité.

#### Modèle 3 : Évasion Unicode

| Test | Entité Manquée |
|------|-----------------|
| `fullwidth_numbers` | "１２３４５６７８Z" (U+FF11-U+FF18) |

**Cause racine :** Pas de normalisation Unicode avant le NER. Les chiffres fullwidth (U+FF10-U+FF19) ne sont pas reconnus comme des nombres.

**Impact :** Bas en production, mais critique pour la sécurité (évasion intentionnelle).

#### Modèle 4 : Identifiants Espagnols Spécifiques

| Test | Entité Manquée |
|------|-----------------|
| `social_security` | "281234567890" (NSS) |
| `bank_account_clause` | "A-98765432" (CIF) |
| `professional_ids` | "12345", "67890" (numéros collégiaux) |

**Cause racine :** Modèles peu fréquents dans le corpus d'entraînement. Le NSS espagnol a un format spécifique (12 chiffres) qui n'a pas été appris.

**Impact :** Élevé pour les documents de travail et commerciaux.

#### Modèle 5 : Faux Positifs Contextuels

| Test | Entité Fausse |
|------|---------------|
| `example_dni` | "12345678X" (contexte : "exemple illustratif") |
| `fictional_person` | "Don Quijote de la Mancha" |

**Cause racine :** Le modèle détecte des motifs sans considérer le contexte sémantique (négations, exemples, fiction).

**Impact :** Moyen. Cause une anonymisation inutile.

### 4.2 Matrice de Confusion par Type d'Entité

| Type | TP | FP | FN | Observation |
|------|----|----|----|----|
| PERSON | 15 | 2 | 2 | Bon, échoue sur la fiction |
| DNI_NIE | 8 | 1 | 4 | Échoue sur les formats variants |
| LOCATION | 6 | 0 | 2 | Échoue sur les codes postaux isolés |
| DATE | 3 | 0 | 4 | Échoue sur le format textuel |
| IBAN | 2 | 0 | 1 | Échoue avec OCR |
| ORGANIZATION | 5 | 2 | 0 | Confond avec les tribunaux |
| NSS | 0 | 0 | 1 | Ne détecte pas |
| PROFESSIONAL_ID | 0 | 0 | 2 | Ne détecte pas |
| Autres | 10 | 4 | 2 | - |

---

## 5. Conclusions

### 5.1 État Actuel

Le modèle `legal_ner_v2` présente un **F1 de 0.784** en évaluation adversariale, avec les caractéristiques suivantes :

- **Forces :**
  - Haute précision (0.845) - peu de faux positifs
  - Bonne résistance au bruit (dégradation 0.080)
  - Excellent sur les noms composés et les adresses

- **Faiblesses :**
  - Rappel insuffisant (0.731) - manque des entités
  - Ne reconnaît pas les dates au format textuel espagnol
  - Vulnérable à l'évasion Unicode (fullwidth)
  - Ne détecte pas NSS ni les numéros collégiaux

### 5.2 Niveau de Validation

| Niveau | Statut | Critère |
|-------|--------|----------|
| Niveau 1 : Tests Unitaires | ✅ | Fonctions individuelles |
| Niveau 2 : Intégration | ✅ | Pipeline complet |
| Niveau 3 : Benchmark | ✅ | F1 > 0.75 |
| **Niveau 4 : Adversarial** | ❌ | Taux de réussite < 70% |
| Niveau 5 : Production-like | ⏸️ | En attente |

**Conclusion :** Le modèle n'est **PAS prêt pour la production** selon les critères du projet (Niveau 4 obligatoire).

### 5.3 Travaux Futurs

#### Priorité HAUTE (impact estimé > 3pts F1)

1. **Normalisation Unicode en prétraitement**
   - Convertir fullwidth vers ASCII
   - Supprimer les caractères de largeur nulle
   - Normaliser O/0 dans les contextes numériques

2. **Augmentation de données textuelles**
   - Générer des variantes : "primero de enero", "XV de marzo"
   - Inclure des chiffres romains
   - Fine-tune avec corpus augmenté

3. **Motifs regex pour NSS/CIF**
   - Ajouter au CompositeNerAdapter
   - NSS : `\d{12}` en contexte "Seguridad Social"
   - CIF : `[A-Z]-?\d{8}` en contexte entreprise

#### Priorité MOYENNE (impact estimé 1-3pts F1)

4. **Normalisation des espaces OCR**
   - Détecter et réduire les espaces excessifs
   - Reconstruire les tokens fragmentés

5. **Filtre post-traitement pour contextes "exemple"**
   - Détecter les phrases : "por ejemplo", "ilustrativo", "formato"
   - Supprimer les entités dans ces contextes

#### Priorité BASSE (cas limites)

6. **Gazetteer de personnages fictifs**
   - Don Quijote, Sancho Panza, etc.
   - Filtre post-traitement

7. **Dates avec chiffres romains**
   - Regex spécifique pour ancien style notarial

---

## 6. Références

1. **seqeval** - Métriques d'évaluation au niveau entité pour étiquetage de séquence. https://github.com/chakki-works/seqeval

2. **NoiseBench (ICLR 2024)** - Benchmark pour évaluer les modèles NLP sous conditions de bruit réalistes.

3. **HAL Science** - Étude sur l'impact de l'OCR dans les tâches NER. Établit une dégradation attendue de ~10pts F1.

4. **RoBERTalex** - Modèle RoBERTa domaine juridique espagnol. Base du modèle évalué.

5. **Directives du projet v1.0.0** - Méthodologie de préparation ML pour ContextSafe.

---

## Annexes

### A. Configuration du Test

```yaml
total_tests: 35
categories:
  edge_case: 9
  adversarial: 8
  ocr_corruption: 5
  unicode_evasion: 3
  real_world: 10
difficulty_distribution:
  easy: 4
  medium: 12
  hard: 19
```

### B. Commande de Reproduction

```bash
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate
python scripts/evaluate/test_ner_predictor_adversarial.py
```

### C. Fichiers Générés

- Rapport automatique : `docs/reports/2026-01-23_adversarial_ner_v2.md`
- Analyse académique : `docs/reports/2026-01-23_baseline_adversarial_analysis.md` (ce document)

---

**Temps d'exécution total :** 3.1s (chargement + évaluation)
**Généré par :** AlexAlves87
**Date :** 2026-01-23
