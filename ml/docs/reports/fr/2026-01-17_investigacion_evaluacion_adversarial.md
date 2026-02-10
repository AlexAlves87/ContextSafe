# Recherche : Meilleures Pratiques pour l'Évaluation Adversariale de NER

**Date :** 2026-01-17
**Objectif :** Étayer la méthodologie d'évaluation adversariale avant d'implémenter les scripts

---

## 1. Résumé Exécutif

La littérature académique récente (2024-2025) établit que l'évaluation adversariale des modèles NER doit prendre en compte :

1. **Bruit Réel vs Simulé** - Le bruit réel est significativement plus difficile que le simulé.
2. **Évaluation au Niveau de l'Entité** - Pas au niveau du token.
3. **Multiples Catégories de Perturbation** - OCR, Unicode, contexte, format.
4. **Métriques Standard** - seqeval avec F1, Précision, Rappel par type d'entité.

---

## 2. Sources Consultées

### 2.1 NoiseBench (Mai 2024)

**Source :** [NoiseBench: Benchmarking the Impact of Real Label Noise on NER](https://arxiv.org/abs/2405.07609)

**Principales Découvertes :**
- Le bruit réel (erreurs humaines, crowdsourcing, LLM) est **significativement plus difficile** que le bruit simulé.
- Les modèles de pointe "sont bien en deçà de leur limite supérieure théoriquement atteignable".
- 6 types de bruit réel doivent être évalués : erreurs d'experts, erreurs de crowdsourcing, erreurs d'annotation automatique, erreurs LLM.

**Application à notre projet :**
- Nos tests incluent du bruit OCR réel (confusion l/I, 0/O) ✓
- Nous devons ajouter des tests avec des erreurs d'annotation automatique.

### 2.2 Context-Aware Adversarial Training for NER (MIT TACL)

**Source :** [Context-aware Adversarial Training for Name Regularity Bias](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00386/102846)

**Principales Découvertes :**
- Les modèles NER montrent un "Biais de Régularité de Nom" - ils dépendent trop du nom et pas assez du contexte.
- BERT fine-tuné surpasse significativement LSTM-CRF dans les tests de biais.
- L'entraînement adversarial avec des vecteurs de bruit apprenables améliore la capacité contextuelle.

**Application à notre projet :**
- Nos tests `negation_dni`, `example_dni`, `fictional_person` évaluent la capacité contextuelle ✓
- Le modèle v2 (entraîné avec du bruit) devrait être plus robuste.

### 2.3 OCR Impact on NER (HAL Science)

**Source :** [Assessing and Minimizing the Impact of OCR Quality on NER](https://hal.science/hal-03026931/document)

**Principales Découvertes :**
- Le bruit OCR cause une perte d'environ 10 points F1 (72% vs 82% sur texte propre).
- Doit être évalué avec "divers niveaux et types de bruit OCR".
- Première étude systématique de l'impact de l'OCR sur le NER multilingue.

**Application à notre projet :**
- Nos tests OCR (5 cas) sont insuffisants - la littérature recommande plus de niveaux.
- Objectif réaliste : accepter ~10 points de dégradation avec l'OCR.

### 2.4 seqeval - Métriques Standard

**Source :** [seqeval - Sequence Labeling Evaluation](https://github.com/chakki-works/seqeval)

**Principales Découvertes :**
- Évaluation au niveau de l'**entité**, pas du token.
- Métriques : Précision, Rappel, F1 par type et macro/micro moyenne.
- Mode strict vs indulgent pour la correspondance.

**Application à notre projet :**
- Notre script utilise une correspondance floue avec une tolérance de ±5 caractères (approprié).
- Nous devons rapporter les métriques par type d'entité, pas seulement réussite/échec.

### 2.5 Enterprise Robustness Benchmark (2025)

**Source :** [Evaluating Robustness of LLMs in Enterprise Applications](https://arxiv.org/html/2601.06341)

**Principales Découvertes :**
- Des perturbations mineures peuvent réduire la performance jusqu'à **40 points de pourcentage**.
- Il faut évaluer : éditions de texte, changements de format, entrées multilingues, variations positionnelles.
- Les modèles de 4B à 120B paramètres montrent tous des vulnérabilités.

**Application à notre projet :**
- Nos tests couvrent les éditions de texte et le formatage ✓
- Nous devons considérer des tests multilingues (noms étrangers).

---

## 3. Taxonomie des Tests Adversariaux (Littérature)

| Catégorie | Sous-catégorie | Exemple | Notre Couverture |
|-----------|----------------|---------|------------------|
| **Bruit d'Étiquette** | Erreurs d'experts | Annotation incorrecte | ❌ N/A (inférence) |
| | Crowdsourcing | Incohérences | ❌ N/A (inférence) |
| | Erreurs LLM | Hallucinations | ❌ N/A (inférence) |
| **Bruit d'Entrée** | Corruption OCR | l/I, 0/O, espaces | ✅ 5 tests |
| | Évasion Unicode | Cyrillique, fullwidth | ✅ 3 tests |
| | Variation de format | D.N.I. vs DNI | ✅ Inclus |
| **Contexte** | Négation | "ne PAS avoir de DNI" | ✅ 1 test |
| | Exemple/illustratif | "exemple : 12345678X" | ✅ 1 test |
| | Fictionnel | Don Quijote | ✅ 1 test |
| | Références légales | Loi 15/2022 | ✅ 1 test |
| **Cas Limites** | Entités longues | Noms nobles | ✅ 1 test |
| | Entités courtes | J. García | ✅ 1 test |
| | Entités espacées | IBAN avec espaces | ✅ 2 tests |
| **Monde Réel** | Modèles de documents | Notarial, judiciaire | ✅ 10 tests |

---

## 4. Métriques Recommandées

### 4.1 Métriques Primaires (seqeval)

| Métrique | Description | Utilisation |
|---------|-------------|-----|
| **F1 Macro** | Moyenne F1 par type d'entité | Métrique principale |
| **F1 Micro** | F1 global (toutes entités) | Métrique secondaire |
| **Précision** | TP / (TP + FP) | Évaluer les faux positifs |
| **Rappel** | TP / (TP + FN) | Évaluer les entités manquées |

### 4.2 Métriques Adversariales

| Métrique | Description | Cible |
|---------|-------------|----------|
| **Taux de Réussite** | Tests réussis / Total | ≥70% |
| **Dégradation OCR** | F1_propre - F1_ocr | ≤10 points |
| **Sensibilité Contextuelle** | % tests contextuels corrects | ≥80% |
| **Taux de FP** | Faux positifs / Détections | ≤15% |

---

## 5. Lacunes Identifiées dans Notre Script

| Lacune | Sévérité | Action |
|-----|-----------|--------|
| Pas de rapport F1/Précision/Rappel par type | Moyenne | Ajouter métriques seqeval |
| Peu de tests OCR (5) vs recommandé (10+) | Moyenne | Étendre dans l'itération suivante |
| N'évalue pas la dégradation vs baseline | Élevée | Comparer avec tests propres |
| Pas de tests multilingues | Faible | Ajouter noms étrangers |

---

## 6. Recommandations pour Notre Script

### 6.1 Améliorations Immédiates

1. **Ajouter métriques seqeval** - Précision, Rappel, F1 par type d'entité.
2. **Calculer la dégradation** - Comparer avec la version propre de chaque test.
3. **Rapporter taux de FP** - Faux positifs comme métrique séparée.

### 6.2 Améliorations Futures

1. Étendre les tests OCR à 10+ cas avec différents niveaux de corruption.
2. Ajouter des tests avec des noms étrangers (John Smith, Mohammed Ali).
3. Implémenter une évaluation style NoiseBench avec du bruit gradué.

---

## 7. Conclusion

Le script actuel couvre les principales catégories d'évaluation adversariale selon la littérature, mais doit :

1. **Améliorer les métriques** - Utiliser seqeval pour F1/P/R par type.
2. **Étendre l'OCR** - Plus de niveaux de corruption.
3. **Calculer la dégradation** - vs baseline propre.

**Le script actuel est VALIDE pour une évaluation initiale**, mais doit être itéré pour se conformer pleinement aux meilleures pratiques académiques.

---

## Références

1. [NoiseBench: Benchmarking the Impact of Real Label Noise on NER](https://arxiv.org/abs/2405.07609) - ICLR 2024
2. [Context-aware Adversarial Training for Name Regularity Bias](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00386/102846) - MIT TACL
3. [Assessing and Minimizing the Impact of OCR Quality on NER](https://hal.science/hal-03026931/document) - HAL Science
4. [seqeval - Sequence Labeling Evaluation](https://github.com/chakki-works/seqeval) - GitHub
5. [Evaluating Robustness of LLMs in Enterprise Applications](https://arxiv.org/html/2601.06341) - arXiv 2025
6. [nervaluate - Entity-level NER Evaluation](https://github.com/MantisAI/nervaluate) - Based on SemEval'13

---

**Date :** 2026-01-17
