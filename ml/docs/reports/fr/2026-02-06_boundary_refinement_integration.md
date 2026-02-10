# Affinement des Limites - Intégration dans le Pipeline NER

**Date :** 06/02/2026
**Auteur :** AlexAlves87
**Composant :** `scripts/preprocess/boundary_refinement.py` intégré dans `ner_predictor.py`
**Standard :** SemEval 2013 Tâche 9 (Évaluation au niveau de l'entité)

---

## 1. Résumé Exécutif

Implémentation de l'affinement des limites des entités pour convertir les correspondances partielles (PAR) en correctes (COR) selon le cadre d'évaluation SemEval 2013.

### Résultats

| Suite de Tests | Résultat |
|----------------|----------|
| Tests autonomes | 12/12 (100%) |
| Test d'intégration | ✅ Fonctionnel |
| Affinements appliqués | 4/8 entités dans la démo |

### Types d'Affinement

| Type | Entités | Action |
|------|---------|--------|
| OVER_EXTENDED | PERSON | Supprimer préfixes : Don, Dña., D., Mr., Doña |
| OVER_EXTENDED | DATE | Supprimer préfixes : a, el día, día |
| OVER_EXTENDED | ORGANIZATION | Supprimer suffixes : virgules, points-virgules |
| OVER_EXTENDED | ADDRESS | Supprimer code postal+ville à la fin |
| TRUNCATED | POSTAL_CODE | Étendre à 5 chiffres |
| TRUNCATED | DNI_NIE | Étendre pour inclure la lettre de contrôle |

---

## 2. Méthodologie

### 2.1 Diagnostic Précédent

`scripts/evaluate/diagnose_par_cases.py` a été exécuté pour identifier les modèles d'erreur :

```
TRUNCATED (2 cas) :
  - [address_floor_door] Manquant à la fin : '001' (code postal)
  - [testament_comparecencia] Manquant à la fin : 'Z' (lettre DNI)

OVER_EXTENDED (9 cas) :
  - Noms avec préfixes honorifiques inclus
  - Dates avec préfixe "a" inclus
  - Organisations avec virgule finale
```

### 2.2 Implémentation

**Fichier :** `scripts/preprocess/boundary_refinement.py`

```python
# Préfixes honorifiques espagnols (ordre : plus longs en premier)
PERSON_PREFIXES = [
    r"(?:Compareció\s+)?Don\s+",
    r"(?:Compareció\s+)?Doña\s+",
    r"Dña\.\s*",
    r"D\.\s*",
    r"Mr\.\s*",
    r"Mrs\.\s*",
    # ...
]

# Fonction principale
def refine_entity(text, entity_type, start, end, confidence, source, original_text):
    """Applique l'affinement selon le type d'entité."""
    if entity_type in REFINEMENT_FUNCTIONS:
        refined_text, refinement_applied = REFINEMENT_FUNCTIONS[entity_type](text, original_text)
    # ...
```

### 2.3 Intégration au Pipeline

**Fichier :** `scripts/inference/ner_predictor.py`

```python
# Import avec dégradation élégante
try:
    from preprocess.boundary_refinement import refine_entity, RefinedEntity
    REFINEMENT_AVAILABLE = True
except ImportError:
    REFINEMENT_AVAILABLE = False

# Dans la méthode predict() :
def predict(self, text, min_confidence=0.5, max_length=512):
    # 1. Normalisation du texte
    text = normalize_text_for_ner(text)

    # 2. Prédiction NER
    entities = self._extract_entities(...)

    # 3. Fusion Regex (hybride)
    if REGEX_AVAILABLE:
        entities = self._merge_regex_detections(text, entities, min_confidence)

    # 4. Affinement des limites (NOUVEAU)
    if REFINEMENT_AVAILABLE:
        entities = self._apply_boundary_refinement(text, entities)

    return entities
```

### 2.4 Reproductibilité

```bash
# Environnement
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Test autonome
python scripts/preprocess/boundary_refinement.py

# Test d'intégration
python scripts/inference/ner_predictor.py
```

---

## 3. Résultats

### 3.1 Tests Autonomes (12/12)

| Test | Entité | Affinement | Résultat |
|------|--------|------------|----------|
| person_don | PERSON | Supprimer "Don " | ✅ |
| person_dña | PERSON | Supprimer "Dña. " | ✅ |
| person_d_dot | PERSON | Supprimer "D. " | ✅ |
| person_mr | PERSON | Supprimer "Mr. " | ✅ |
| person_no_change | PERSON | Aucun changement | ✅ |
| date_a_prefix | DATE | Supprimer "a " | ✅ |
| date_el_dia | DATE | Supprimer "el día " | ✅ |
| org_trailing_comma | ORGANIZATION | Supprimer "," | ✅ |
| address_with_postal_city | ADDRESS | Supprimer "28013 Madrid" | ✅ |
| postal_extend | POSTAL_CODE | "28" → "28001" | ✅ |
| dni_extend_letter | DNI_NIE | "12345678-" → "12345678Z" | ✅ |
| dni_no_extend | DNI_NIE | Aucun changement | ✅ |

**Temps d'exécution :** 0,002s

### 3.2 Test d'Intégration

| Entrée | Entité Originale | Entité Affinée | Affinement |
|--------|------------------|----------------|------------|
| "Don José García López con DNI..." | "Don José García López" | "José García López" | stripped_prefix:Don |
| "Dña. Ana Martínez Ruiz..." | "Dña. Ana Martínez Ruiz" | "Ana Martínez Ruiz" | stripped_prefix:Dña. |
| "Compareció Doña María Antonia..." | "Doña María Antonia Fernández Ruiz" | "María Antonia Fernández Ruiz" | stripped_prefix:Doña |
| "Mr. John Smith, residente..." | "Mr. John Smith" | "John Smith" | stripped_prefix:Mr. |

### 3.3 Entités Sans Affinement (Correctes)

| Entrée | Entité | Raison |
|--------|--------|--------|
| "DNI 12345678Z" | "12345678Z" | Déjà correct |
| "IBAN ES91 2100..." | "ES91 2100 0418 4502 0005 1332" | Déjà correct |
| "Calle Alcalá 50" | "Calle Alcalá 50" | Déjà correct |
| "Sevilla" | "Sevilla" | Déjà correct |

---

## 4. Analyse

### 4.1 Impact sur le Pipeline

L'affinement des limites est appliqué **après** la fusion NER+regex, agissant comme un post-processeur :

```
Texte → Normalisation → NER → Fusion Regex → Affinement → Entités finales
                                                ↑
                                          (Élément 5)
```

### 4.2 Préservation des Métadonnées

L'affinement préserve toutes les métadonnées originales :
- `confidence` : Non modifié
- `source` : Non modifié (ner/regex)
- `checksum_valid` : Non modifié
- `checksum_reason` : Non modifié

Ajoute de nouveaux champs :
- `original_text` : Texte avant affinement
- `refinement_applied` : Type d'affinement appliqué

### 4.3 Observation sur DATE

La date "a quince de marzo de dos mil veinticuatro" dans le test d'intégration **n'a pas été affinée** car le modèle NER a détecté "quince de marzo de dos mil veinticuatro" directement (sans le préfixe "a"). Cela indique que :

1. Le modèle NER apprend déjà certaines limites correctes
2. L'affinement agit comme un filet de sécurité pour les cas que le modèle ne gère pas

---

## 5. Pipeline Complet (5 Éléments)

### 5.1 Éléments Intégrés

| # | Élément | Autonome | Intégration | Fonction |
|---|---------|----------|-------------|----------|
| 1 | TextNormalizer | 15/15 | ✅ | Évasion Unicode, homoglyphes |
| 2 | Checksum Validators | 23/24 | ✅ | Ajustement de confiance |
| 3 | Regex Patterns | 22/22 | ✅ | IDs avec espaces/tirets |
| 4 | Date Patterns | 14/14 | ✅ | Chiffres romains |
| 5 | Boundary Refinement | 12/12 | ✅ | Conversion PAR→COR |

### 5.2 Flux de Données

```
Entrée : "Don José García López avec DNI 12345678Z"
                    ↓
[1] TextNormalizer : Aucun changement (texte propre)
                    ↓
[Modèle NER] : Détecte "Don José García López" (PERSON), "12345678Z" (DNI_NIE)
                    ↓
[3] Fusion Regex : Aucun changement (NER a déjà détecté DNI complet)
                    ↓
[2] Checksum : DNI valide → boost de confiance
                    ↓
[5] Boundary Refinement : "Don José García López" → "José García López"
                    ↓
Sortie : [PERSON] "José García López", [DNI_NIE] "12345678Z" ✅
```

---

## 6. Conclusions

### 6.1 Réalisations

1. **Affinement fonctionnel** : 12/12 tests autonomes, intégration vérifiée
2. **Dégradation élégante** : Le système fonctionne sans le module (REFINEMENT_AVAILABLE=False)
3. **Préservation des métadonnées** : Checksum et source intacts
4. **Traçabilité** : Champs `original_text` et `refinement_applied` pour audit

### 6.2 Limitations Connues

| Limitation | Impact | Atténuation |
|------------|--------|-------------|
| Seulement préfixes/suffixes statiques | Ne gère pas les cas dynamiques | Les modèles couvrent 90%+ des cas légaux |
| Extension dépend du contexte | Peut échouer si texte tronqué | Vérification de longueur |
| Pas d'affinement CIF | Priorité basse | Ajouter si modèle détecté |

### 6.3 Étape Suivante

Exécuter le test adversarial complet pour mesurer l'impact sur les métriques :

```bash
python scripts/evaluate/test_ner_predictor_adversarial_v2.py
```

**Métriques à observer :**
- PAR (correspondances partielles) - réduction attendue
- COR (correspondances correctes) - augmentation attendue
- Taux de réussite - amélioration attendue

---

## 7. Références

1. **SemEval 2013 Task 9** : Cadre d'évaluation des entités (COR/INC/PAR/MIS/SPU)
2. **Diagnostic PAR** : `scripts/evaluate/diagnose_par_cases.py`
3. **Implémentation** : `scripts/preprocess/boundary_refinement.py`
4. **Intégration** : `scripts/inference/ner_predictor.py` lignes 37-47, 385-432

---

**Temps d'exécution total :** 0,002s (autonome) + 1,39s (chargement modèle) + 18,1ms (inférence)
**Généré par :** AlexAlves87
**Date :** 06/02/2026
