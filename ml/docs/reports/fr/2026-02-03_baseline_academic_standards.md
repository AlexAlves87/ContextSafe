# Baseline Académique : Évaluation avec les Standards SemEval 2013

**Date :** 03/02/2026
**Auteur :** AlexAlves87
**Modèle :** legal_ner_v2 (RoBERTalex fine-tuned)
**Standard :** SemEval 2013 Task 9

---

## 1. Résumé Exécutif

Cette évaluation établit le **baseline réel** du modèle en utilisant les standards académiques (mode strict SemEval 2013), remplaçant les résultats précédents qui utilisaient le matching lenient.

### Comparaison v1 vs v2

| Métrique | v1 (lenient) | v2 (strict) | Différence |
|----------|--------------|-------------|------------|
| **Pass Rate** | 54,3% | **28,6%** | **-25,7pp** |
| **F1-Score** | 0,784 | **0,464** | **-0,320** |
| F1 (partiel) | - | 0,632 | - |

### Conclusion Principale

> **Les résultats précédents (F1=0,784, 54,3%) étaient ENFLÉS.**
> Le baseline réel avec les standards académiques est **F1=0,464, 28,6% de pass rate**.

---

## 2. Méthodologie

### 2.1 Conception Expérimentale

| Aspect | Spécification |
|--------|---------------|
| Modèle évalué | `legal_ner_v2` (RoBERTalex fine-tuned) |
| Framework | PyTorch 2.0+, Transformers |
| Matériel | CUDA (GPU) |
| Standard d'évaluation | SemEval 2013 Task 9 |
| Mode principal | Strict (limite + type exacts) |

### 2.2 Dataset d'Évaluation

| Catégorie | Tests | Objectif |
|-----------|-------|----------|
| edge_case | 9 | Conditions limites (noms longs, formats variants) |
| adversarial | 8 | Cas conçus pour confondre (négations, exemples) |
| ocr_corruption | 5 | Simulation d'erreurs OCR |
| unicode_evasion | 3 | Tentatives d'évasion avec caractères Unicode |
| real_world | 10 | Extraits de documents juridiques réels |
| **Total** | **35** | - |

### 2.3 Métriques Utilisées

Selon SemEval 2013 Task 9 :

| Métrique | Définition |
|----------|------------|
| COR | Correct : limite ET type exacts |
| INC | Incorrect : limite exacte, type incorrect |
| PAR | Partiel : limite chevauchante, n'importe quel type |
| MIS | Manquant : entité gold non détectée (FN) |
| SPU | Fallacieux : détection sans correspondance gold (FP) |

**Formules :**
- Précision (strict) = COR / (COR + INC + PAR + SPU)
- Rappel (strict) = COR / (COR + INC + PAR + MIS)
- F1 (strict) = 2 × P × R / (P + R)

### 2.4 Reproductibilité

```bash
# Environnement
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Dépendances
pip install nervaluate  # Optionnel, métriques implémentées manuellement

# Exécution
python scripts/evaluate/test_ner_predictor_adversarial_v2.py

# Sortie
# - Console : Résultats par test avec COR/INC/PAR/MIS/SPU
# - Rapport : docs/reports/YYYY-MM-DD_adversarial_v2_academic_rN.md
```

### 2.5 Différence avec Évaluation v1

| Aspect | v1 (lenient) | v2 (strict) |
|--------|--------------|-------------|
| Matching | Confinement + 80% chevauchement car. | Limite exacte normalisée |
| Type | Requis | Requis |
| Métriques | TP/FP/FN | COR/INC/PAR/MIS/SPU |
| Standard | Personnalisé | SemEval 2013 Task 9 |

---

## 3. Résultats

### 3.1 Décomptes SemEval 2013

| Métrique | Valeur | Description |
|----------|--------|-------------|
| **COR** | 29 | Correct (limite + type exacts) |
| **INC** | 0 | Limite correcte, type incorrect |
| **PAR** | 21 | Correspondance partielle (chevauchement seulement) |
| **MIS** | 17 | Manqués (FN) |
| **SPU** | 8 | Fallacieux (FP) |
| **POS** | 67 | Total or (COR+INC+PAR+MIS) |
| **ACT** | 58 | Total système (COR+INC+PAR+SPU) |

### 3.2 Interprétation

```
                    ┌─────────────────────────────────┐
                    │     GOLD: 67 entités            │
                    │                                 │
  ┌─────────────────┼─────────────────┐               │
  │                 │    COR: 29      │               │
  │   SYSTÈME: 58   │  (43% de gold)  │   MIS: 17     │
  │                 │                 │   (25%)       │
  │    SPU: 8       │    PAR: 21      │               │
  │    (14%)        │   (31% overlap) │               │
  └─────────────────┴─────────────────┴───────────────┘
```

**Analyse :**
- Seulement **43%** des entités gold sont détectées avec une limite exacte
- **31%** sont détectées avec un chevauchement partiel (v1 les comptait comme correctes)
- **25%** sont complètement manquées
- **14%** des détections sont des faux positifs

### 3.3 Formules Appliquées

**Mode Strict :**
```
Précision = COR / ACT = 29 / 58 = 0,500
Rappel = COR / POS = 29 / 67 = 0,433
F1 = 2 * P * R / (P + R) = 0,464
```

**Mode Partiel :**
```
Précision = (COR + 0,5*PAR) / ACT = (29 + 10,5) / 58 = 0,681
Rappel = (COR + 0,5*PAR) / POS = (29 + 10,5) / 67 = 0,590
F1 = 2 * P * R / (P + R) = 0,632
```

---

### 3.4 Résultats par Catégorie

| Catégorie | Strict | Lenient | COR | PAR | MIS | SPU |
|-----------|--------|---------|-----|-----|-----|-----|
| adversarial | 75% | 75% | 5 | 1 | 0 | 3 |
| edge_case | 22% | 67% | 6 | 3 | 3 | 1 |
| ocr_corruption | 40% | 40% | 4 | 1 | 4 | 0 |
| real_world | 10% | 50% | 12 | 14 | 8 | 4 |
| unicode_evasion | 0% | 33% | 3 | 1 | 2 | 1 |

**Observations :**
- **real_world** : Plus grande divergence strict vs lenient (10% vs 50%) - beaucoup de PAR
- **unicode_evasion** : 0% strict - toutes les détections sont partielles ou incorrectes
- **adversarial** : Égal dans les deux modes - tests de non-détection

---

### 3.5 Résultats par Difficulté

| Difficulté | Strict | Lenient |
|------------|--------|---------|
| facile | 50% | 75% |
| moyen | 42% | 75% |
| difficile | 16% | 42% |

**Observation :** La différence strict vs lenient augmente avec la difficulté.

---

## 4. Analyse des Erreurs

### 4.1 Matches Partiels (PAR)

Les 21 matches partiels représentent des détections où la limite n'est pas exacte :

| Type de PAR | Exemples | Cause |
|-------------|----------|-------|
| Nom incomplet | "José María" vs "José María de la Santísima..." | RoBERTa tronque les noms longs |
| IBAN avec espaces | "ES91 2100..." vs "ES912100..." | Normalisation des espaces |
| Adresse partielle | "Calle Mayor 15" vs "Calle Mayor 15, 3º B" | Limite exclut étage/porte |
| Personne en contexte | "John Smith" vs "Mr. John Smith" | Préfixes non inclus |

**Implication :** Le modèle détecte l'entité mais avec des limites imprécises.

---

### 4.2 Tests Échoués (Strict)

#### 4.2.1 Par SPU (Faux Positifs)

| Test | SPU | Entités Fallacieuses |
|------|-----|----------------------|
| example_dni | 1 | "12345678X" (contexte exemple) |
| fictional_person | 1 | "Don Quijote de la Mancha" |
| date_ordinal | 1 | "El" |
| zero_width_space | 1 | "de" |
| judicial_sentence_header | 2 | Références légales |
| professional_ids | 1 | Association professionnelle |
| ecli_citation | 1 | Tribunal |

#### 4.2.2 Par MIS (Entités Manquantes)

| Test | MIS | Entités Manquantes |
|------|-----|--------------------|
| dni_with_spaces | 1 | "12 345 678 Z" |
| phone_international | 1 | "0034612345678" |
| date_roman_numerals | 1 | "XV de marzo del año MMXXIV" |
| ocr_zero_o_confusion | 1 | IBAN avec O/0 |
| ocr_extra_spaces | 2 | DNI et nom avec espaces |
| fullwidth_numbers | 2 | DNI fullwidth, nom |
| notarial_header | 1 | Date textuelle |

---

## 5. Conclusions et Travaux Futurs

### 5.1 Priorités d'Amélioration

| Amélioration | Impact sur COR | Impact sur PAR→COR |
|--------------|----------------|--------------------|
| Normalisation texte (Unicode) | +2-4 COR | +2-3 PAR→COR |
| Validation Checksum | Réduit SPU | - |
| Raffinement limites | - | +10-15 PAR→COR |
| Augmentation date | +3-5 COR | - |

### 5.2 Objectif Révisé

| Métrique | Actuel | Objectif Niveau 4 |
|----------|--------|-------------------|
| F1 (strict) | 0,464 | **≥ 0,70** |
| Pass rate (strict) | 28,6% | **≥ 70%** |

**Écart à combler :** +0,236 F1, +41,4pp pass rate

---

### 5.3 Prochaines Étapes

1. **Ré-évaluer** avec TextNormalizer intégré (déjà préparé)
2. **Implémenter** raffinement des limites pour réduire PAR
3. **Ajouter** validation checksum pour réduire SPU
4. **Augmenter** données pour dates textuelles pour réduire MIS

---

### 5.4 Leçons Apprises

1. **Le matching lenient gonfle significativement les résultats** (F1 0,784 → 0,464)
2. **PAR est un plus gros problème que MIS** (21 vs 17) - limites imprécises
3. **Les tests réels (real_world) ont plus de PAR** - documents complexes
4. **L'évasion Unicode ne passe aucun test strict** - zone critique

### 5.5 Valeur du Standard Académique

L'évaluation avec SemEval 2013 permet :
- Comparaison avec la littérature académique
- Diagnostic granulaire (COR/INC/PAR/MIS/SPU)
- Identification précise des zones d'amélioration
- Mesure honnête du progrès

---

## 6. Références

1. **SemEval 2013 Task 9** : Segura-Bedmar et al. "Extraction of Drug-Drug Interactions from Biomedical Texts"
2. **nervaluate** : https://github.com/MantisAI/nervaluate
3. **Blog David Batista** : https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/

---

**Temps d'évaluation :** 1,3s
**Généré par :** AlexAlves87
**Date :** 03/02/2026
