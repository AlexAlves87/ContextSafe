# Rapport d'État : Système NER-PII pour Documents Juridiques Espagnols

**Date :** 2026-01-15
**Version :** 1.0
**Projet :** ContextSafe ML - Fine-tuning NER

---

## Résumé Exécutif

Ce rapport documente le développement du système de détection de PII (Personally Identifiable Information) pour des documents juridiques espagnols. Le système doit détecter 13 catégories d'entités avec un F1 ≥ 0.85.

### État Actuel

| Phase | État | Progrès |
|-------|------|---------|
| Téléchargement des données de base | Terminé | 100% |
| Génération des gazetteers | Terminé | 100% |
| Dataset synthétique v1 | Rejeté | Erreur critique |
| Dataset synthétique v2 | Terminé | 100% |
| Script d'entraînement | Terminé | 100% |
| Entraînement du modèle | En attente | 0% |

---

## 1. Objectif du Projet

Développer un modèle NER spécialisé dans les documents juridiques espagnols (testaments, jugements, actes, contrats) capable de détecter :

| Catégorie | Exemples | Priorité |
|-----------|----------|----------|
| PERSON | Hermógenes Pérez García | Haute |
| DATE | 15 de marzo de 2024 | Haute |
| DNI_NIE | 12345678Z, X1234567A | Haute |
| IBAN | ES9121000418450200051332 | Haute |
| NSS | 281234567890 | Moyenne |
| PHONE | 612 345 678 | Moyenne |
| ADDRESS | Calle Mayor 15, 3º B | Haute |
| POSTAL_CODE | 28001 | Moyenne |
| ORGANIZATION | Banco Santander, S.A. | Haute |
| LOCATION | Madrid, Comunidad de Madrid | Moyenne |
| ECLI | ECLI:ES:TS:2024:1234 | Basse |
| LICENSE_PLATE | 1234 ABC | Basse |
| CADASTRAL_REF | 1234567AB1234S0001AB | Basse |
| PROFESSIONAL_ID | Colegiado nº 12345 | Basse |

---

## 2. Données Téléchargées

### 2.1 Sources Officielles

| Ressource | Emplacement | Taille | Description |
|-----------|-------------|--------|-------------|
| CoNLL-2002 Espagnol | `data/raw/conll2002/` | 4.0 MB | Corpus NER standard |
| INE Prénoms par décennie | `data/raw/gazetteers_ine/nombres_por_fecha.xls` | 1.1 MB | Fréquence temporelle |
| INE Prénoms fréquents | `data/raw/gazetteers_ine/nombres_mas_frecuentes.xls` | 278 KB | Top prénoms |
| INE Noms de famille | `data/raw/gazetteers_ine/apellidos_frecuencia.xls` | 12 MB | 27 251 noms |
| INE Communes 2024 | `data/raw/municipios/municipios_2024.xlsx` | 300 KB | 8 115 communes |
| Codes postaux | `data/raw/codigos_postales/codigos_postales.csv` | 359 KB | 11 051 CP |
| ai4privacy/pii-masking-300k | `data/raw/ai4privacy/` | ~100 MB | Transfer learning |

### 2.2 Modèle de Base

| Modèle | Emplacement | Taille | F1 Base |
|--------|-------------|--------|---------|
| roberta-base-bne-capitel-ner | `models/checkpoints/` | ~500 MB | 88.5% (CAPITEL) |

**Décision de modèle :** MEL (Modelo Español Legal) a été évalué mais manque de fine-tuning NER. RoBERTa-BNE-capitel-ner a été sélectionné pour sa spécialisation en NER espagnol.

---

## 3. Gazetteers Générés

### 3.1 Scripts de Génération

| Script | Fonction | Sortie |
|--------|----------|--------|
| `parse_ine_gazetteers.py` | Parse Excel INE → JSON | apellidos.json, nombres_*.json |
| `generate_archaic_names.py` | Génère noms archaïques juridiques | nombres_arcaicos.json |
| `generate_textual_dates.py` | Dates en format juridique | fechas_textuales.json |
| `generate_administrative_ids.py` | DNI, NIE, IBAN, NSS avec checksums invalides | identificadores_administrativos.json |
| `generate_addresses.py` | Adresses espagnoles complètes | direcciones.json |
| `generate_organizations.py` | Entreprises, tribunaux, banques | organizaciones.json |

### 3.2 Fichiers Générés

| Fichier | Taille | Contenu |
|---------|--------|---------|
| `apellidos.json` | 1.8 MB | 27 251 noms avec fréquences INE |
| `codigos_postales.json` | 1.2 MB | 11 051 codes postaux |
| `municipios.json` | 164 KB | 8 115 communes espagnoles |
| `nombres_hombres.json` | 40 KB | 550 prénoms masculins par décennie |
| `nombres_mujeres.json` | 41 KB | 550 prénoms féminins par décennie |
| `nombres_todos.json` | 3.9 KB | 260 prénoms uniques (INE) |
| `nombres_arcaicos.json` | 138 KB | 940 noms archaïques + 5 070 combinaisons |
| `nombres_arcaicos_flat.json` | 267 KB | Liste plate pour NER |
| `fechas_textuales.json` | 159 KB | 645 dates avec 41 modèles juridiques |
| `fechas_textuales_flat.json` | 86 KB | Liste plate |
| `identificadores_administrativos.json` | 482 KB | 2 550 IDs synthétiques |
| `identificadores_administrativos_flat.json` | 134 KB | Liste plate |
| `direcciones.json` | 159 KB | 600 adresses + 416 avec contexte juridique |
| `direcciones_flat.json` | 59 KB | Liste plate |
| `organizaciones.json` | 185 KB | 1 000 organisations |
| `organizaciones_flat.json` | 75 KB | Liste plate |

**Total gazetteers :** ~4.9 MB

### 3.3 Caractéristiques Spéciales

**Noms Archaïques :** Inclut des noms fréquents dans les documents juridiques historiques :
- Hermógenes, Segismundo, Práxedes, Gertrudis, Baldomero, Saturnino, Patrocinio...
- Combinaisons composées : María del Carmen, José Antonio, Juan de Dios...

**Identifiants Administratifs :** Générés avec checksums MATHÉMATIQUEMENT INVALIDES :
- DNI : Lettre de contrôle incorrecte (mod-23 incorrect)
- NIE : Préfixe X/Y/Z avec lettre incorrecte
- IBAN : Chiffres de contrôle "00" (toujours invalide)
- NSS : Chiffres de contrôle incorrects (mod-97)

Ceci garantit qu'aucun identifiant synthétique ne correspond à des données réelles.

---

## 4. Dataset Synthétique

### 4.1 Dataset v1 - ERREUR CRITIQUE (REJETÉ)

**Date :** 2026-01-15

Le premier dataset généré contenait des erreurs critiques qui auraient dégradé significativement le modèle.

#### Erreur 1 : Ponctuation Collée aux Tokens

**Problème :** La tokenisation simple par espaces blancs causait l'adhésion de la ponctuation aux entités.

**Exemple de l'erreur :**
```
Texte : "Don Hermógenes Freijanes, con DNI 73364386X."
Tokens : ["Don", "Hermógenes", "Freijanes,", "con", "DNI", "73364386X."]
Labels : ["O",   "B-PERSON",   "I-PERSON",   "O",   "O",   "B-DNI_NIE"]
```

**Impact :** Le modèle apprendrait que "Freijanes," (avec virgule) est une personne, mais durant l'inférence ne reconnaitrait pas "Freijanes" sans virgule.

**Statistiques de l'erreur :**
- 6 806 tokens avec ponctuation collée
- Affectait principalement : PERSON, DNI_NIE, IBAN, PHONE
- ~30% des entités compromises

#### Erreur 2 : Pas d'Alignement de Subwords

**Problème :** Les étiquettes BIO étaient au niveau du mot, mais BERT utilise la tokenisation de subwords.

**Exemple de l'erreur :**
```
Mot : "Hermógenes"
Subwords : ["Her", "##mó", "##genes"]
Label v1 : Une seule étiquette pour tout le mot → quel subword la reçoit ?
```

**Impact :** Sans alignement explicite, le modèle ne pourrait pas apprendre correctement la relation entre subwords et étiquettes.

#### Erreur 3 : Déséquilibre des Entités

| Entité | Pourcentage v1 | Problème |
|--------|----------------|----------|
| PERSON | 30.3% | Surreprésenté |
| ADDRESS | 12.6% | OK |
| DNI_NIE | 10.1% | OK |
| NSS | 1.7% | Sous-représenté |
| ECLI | 1.7% | Sous-représenté |
| LICENSE_PLATE | 1.7% | Sous-représenté |

### 4.2 Dataset v2 - CORRIGÉ

**Date :** 2026-01-15

**Script :** `scripts/preprocess/generate_ner_dataset_v2.py`

#### Corrections Implémentées

**1. Tokenisation avec HuggingFace :**
```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("PlanTL-GOB-ES/roberta-base-bne")

# La tokenisation sépare automatiquement la ponctuation
# "Freijanes," → ["Fre", "##ij", "##anes", ","]
```

**2. Alignement avec word_ids() :**
```python
def align(self, sentence, max_length=128):
    encoding = self.tokenizer(
        text,
        max_length=max_length,
        return_offsets_mapping=True,
    )

    word_ids = encoding.word_ids()

    labels = []
    for i, word_id in enumerate(word_ids):
        if word_id is None:
            labels.append(-100)  # Token spécial
        elif word_id != previous_word_id:
            labels.append(entity_label)  # Premier subword
        else:
            labels.append(-100)  # Continuation
```

**3. Modèles Équilibrés :**
- Ajout de 50+ modèles spécifiques pour entités minoritaires
- Augmentation de la fréquence de NSS, ECLI, LICENSE_PLATE, CADASTRAL_REF

#### Statistiques v2

| Split | Échantillons | Tokens Totaux |
|-------|--------------|---------------|
| Train | 4 925 | ~630 000 |
| Validation | 818 | ~105 000 |
| Test | 818 | ~105 000 |
| **Total** | **6 561** | **~840 000** |

**Distribution des entités v2 :**

| Entité | Compte | % |
|--------|--------|---|
| PERSON | 1 800 | 24.4% |
| ADDRESS | 750 | 10.2% |
| LOCATION | 700 | 9.5% |
| DNI_NIE | 600 | 8.1% |
| DATE | 450 | 6.1% |
| ORGANIZATION | 450 | 6.1% |
| POSTAL_CODE | 200 | 2.7% |
| IBAN | 200 | 2.7% |
| CADASTRAL_REF | 150 | 2.0% |
| PHONE | 150 | 2.0% |
| PROFESSIONAL_ID | 150 | 2.0% |
| ECLI | 100 | 1.4% |
| LICENSE_PLATE | 100 | 1.4% |
| NSS | 100 | 1.4% |

#### Format de Sortie

```
data/processed/ner_dataset_v2/
├── train/
│   ├── data-00000-of-00001.arrow
│   └── dataset_info.json
├── validation/
│   ├── data-00000-of-00001.arrow
│   └── dataset_info.json
├── test/
│   ├── data-00000-of-00001.arrow
│   └── dataset_info.json
├── label_mappings.json
└── dataset_dict.json
```

**Schéma de données :**
```python
{
    "input_ids": [0, 1234, 5678, ...],      # Token IDs
    "attention_mask": [1, 1, 1, ...],        # Masque d'attention
    "labels": [-100, 1, 2, -100, ...],       # Étiquettes alignées
}
```

**Étiquettes (29 classes) :**
```json
{
    "O": 0,
    "B-PERSON": 1, "I-PERSON": 2,
    "B-LOCATION": 3, "I-LOCATION": 4,
    "B-ORGANIZATION": 5, "I-ORGANIZATION": 6,
    "B-DATE": 7, "I-DATE": 8,
    "B-DNI_NIE": 9, "I-DNI_NIE": 10,
    "B-IBAN": 11, "I-IBAN": 12,
    "B-NSS": 13, "I-NSS": 14,
    "B-PHONE": 15, "I-PHONE": 16,
    "B-ADDRESS": 17, "I-ADDRESS": 18,
    "B-POSTAL_CODE": 19, "I-POSTAL_CODE": 20,
    "B-LICENSE_PLATE": 21, "I-LICENSE_PLATE": 22,
    "B-CADASTRAL_REF": 23, "I-CADASTRAL_REF": 24,
    "B-ECLI": 25, "I-ECLI": 26,
    "B-PROFESSIONAL_ID": 27, "I-PROFESSIONAL_ID": 28
}
```

---

## 5. Configuration d'Entraînement

### 5.1 Recherche des Meilleures Pratiques

Les meilleures pratiques pour le fine-tuning NER ont été étudiées basées sur :
- Documentation HuggingFace
- Papiers académiques (RoBERTa, BERT pour NER)
- Benchmarks de modèles espagnols (CAPITEL, AnCora)

### 5.2 Hyperparamètres Sélectionnés

**Fichier :** `scripts/train/train_ner.py`

```python
CONFIG = {
    # Optimisation (LE PLUS IMPORTANT)
    "learning_rate": 2e-5,          # Grille : {1e-5, 2e-5, 3e-5, 5e-5}
    "weight_decay": 0.01,           # Régularisation L2
    "adam_epsilon": 1e-8,           # Stabilité numérique

    # Batching
    "per_device_train_batch_size": 16,
    "per_device_eval_batch_size": 32,
    "gradient_accumulation_steps": 2,  # Batch effectif = 32

    # Époques
    "num_train_epochs": 4,          # Conservateur pour juridique

    # Learning Rate Scheduling
    "warmup_ratio": 0.06,           # 6% warmup (papier RoBERTa)
    "lr_scheduler_type": "linear",  # Décroissance linéaire

    # Early Stopping
    "early_stopping_patience": 2,   # Arrêter si pas d'amélioration en 2 evals
    "metric_for_best_model": "f1",

    # Longueur de Séquence
    "max_length": 384,              # Les documents juridiques peuvent être longs

    # Matériel
    "fp16": True,                   # Précision mixte si GPU
    "dataloader_num_workers": 4,

    # Reproductibilité
    "seed": 42,
}
```

### 5.3 Justification des Décisions

| Paramètre | Valeur | Justification |
|-----------|--------|---------------|
| learning_rate | 2e-5 | Valeur standard pour fine-tuning BERT/RoBERTa |
| batch_size | 32 (effectif) | Équilibre entre stabilité et mémoire |
| epochs | 4 | Éviter overfitting sur données synthétiques |
| warmup | 6% | Recommandation papier RoBERTa |
| max_length | 384 | Documents juridiques peuvent être étendus |
| early_stopping | 2 | Détection précoce d'overfitting |

### 5.4 Dépendances

**Fichier :** `scripts/train/requirements_train.txt`

```
transformers>=4.36.0
datasets>=2.14.0
torch>=2.0.0
evaluate>=0.4.0
seqeval>=1.2.2
accelerate>=0.25.0
```

---

## 6. Leçons Apprises

### 6.1 Erreur ISS-001 : Tokenisation Inadéquate

**Cause racine :** Supposer que la tokenisation par espaces était suffisante pour le NER avec des modèles transformer.

**Impact potentiel :** Si entraîné avec le dataset v1 :
- Dégradation F1 estimée : -15% à -25%
- Entités avec ponctuation non reconnues
- Pauvre généralisation au texte réel

**Prévention future :**
1. Toujours utiliser le tokenizer du modèle de base
2. Implémenter audit de dataset avant l'entraînement
3. Vérifier explicitement l'alignement subword-label

### 6.2 Importance de la Recherche Préalable

Rechercher les meilleures pratiques AVANT d'implémenter a évité :
- Hyperparamètres sous-optimaux (ex: learning_rate=1e-4 cause divergence)
- Architecture incorrecte (ex: pas de couche CRF dans NER classique)
- Évaluation erronée (ex: accuracy vs F1 pour NER)

### 6.3 Données Synthétiques : Forces et Limitations

**Forces :**
- Contrôle total sur la distribution des entités
- Couverture des cas limites (noms archaïques, formats rares)
- Volume évolutif sans coût d'annotation

**Limitations :**
- Modèles de langage artificiels
- Pas de bruit réel (erreurs OCR, typos)
- Nécessite validation sur données réelles

---

## 7. Travaux Futurs

### 7.1 Immédiat (Prochaines étapes)

1. **Exécuter l'entraînement :**
   ```bash
   cd ml
   source .venv/bin/activate
   pip install -r scripts/train/requirements_train.txt
   python scripts/train/train_ner.py
   ```

2. **Évaluer par type d'entité :**
   - Vérifier F1 ≥ 0.85 pour chaque catégorie
   - Identifier les entités problématiques

3. **Test adversarial :**
   - Noms archaïques non vus
   - Formats de date ambigus
   - Adresses incomplètes

### 7.2 Améliorations Potentielles

| Amélioration | Priorité | Impact Attendu |
|--------------|----------|----------------|
| Couche CRF | Haute | +4-13% F1 |
| Données réelles annotées | Haute | Meilleure généralisation |
| Data augmentation | Moyenne | +2-5% F1 |
| Ensemble avec regex | Moyenne | +3-5% rappel |
| Active learning | Basse | Réduction coût annotation |

### 7.3 Ressources Optionnelles

Papiers académiques en attente d'évaluation :
- MAPA Project (aclanthology.org/2022.lrec-1.400/) - Legal PII annoté
- 3CEL Contracts (arxiv.org/abs/2501.15990) - Clauses contrats
- IMPACT-es Corpus (arxiv.org/pdf/1306.3692.pdf) - Noms historiques

---

## 8. Structure du Projet

```
ml/
├── data/
│   ├── raw/
│   │   ├── conll2002/              # Corpus NER standard
│   │   ├── gazetteers_ine/         # Excel INE originaux
│   │   ├── municipios/             # Communes 2024
│   │   ├── codigos_postales/       # CP Espagne
│   │   └── ai4privacy/             # Dataset transfer learning
│   └── processed/
│       ├── gazetteers/             # JSON traités
│       ├── synthetic_sentences/     # Phrases v1 (rejeté)
│       └── ner_dataset_v2/         # Dataset final HuggingFace
├── models/
│   ├── checkpoints/                # Modèle base RoBERTa-BNE
│   └── legal_ner_v1/               # Sortie entraînement (en attente)
├── scripts/
│   ├── preprocess/
│   │   ├── parse_ine_gazetteers.py
│   │   ├── generate_archaic_names.py
│   │   ├── generate_textual_dates.py
│   │   ├── generate_administrative_ids.py
│   │   ├── generate_addresses.py
│   │   ├── generate_organizations.py
│   │   ├── generate_ner_dataset_v2.py
│   │   └── audit_dataset.py
│   └── train/
│       ├── train_ner.py
│       └── requirements_train.txt
└── docs/
    ├── checklists/
    │   └── 2026-02-02_descargas_fase1.md
    └── reports/
        └── 2026-01-15_estado_proyecto_ner.md  # Ce document
```

---

## 9. Conclusions

1. **Préparation terminée :** Gazetteers, dataset v2, et script d'entraînement prêts.

2. **Erreur critique évitée :** L'audit du dataset v1 a identifié des problèmes qui auraient dégradé le modèle significativement.

3. **Meilleures pratiques appliquées :** Hyperparamètres basés sur la recherche, pas des suppositions.

4. **Prochain jalon :** Exécuter entraînement et évaluer F1 par entité.

---

---

## 10. Références

### Modèles et Datasets

1. **RoBERTa-BNE-capitel-ner** - PlanTL-GOB-ES
   - https://huggingface.co/PlanTL-GOB-ES/roberta-base-bne-capitel-ner
   - F1 88.5% sur CAPITEL

2. **CoNLL-2002 Espagnol** - Corpus NER standard
   - https://www.clips.uantwerpen.be/conll2002/ner/

3. **ai4privacy/pii-masking-300k** - Dataset PII anglais
   - https://huggingface.co/datasets/ai4privacy/pii-masking-300k

### Données Officielles INE

4. **Noms par fréquence** - INE
   - https://www.ine.es/daco/daco42/nombyam/nombres_por_edad.xls

5. **Noms de famille par fréquence** - INE
   - https://www.ine.es/daco/daco42/nombyam/apellidos_frecuencia.xls

6. **Communes Espagne 2024** - INE
   - https://www.ine.es/daco/daco42/codmun/

### Papiers et Documentation

7. **RoBERTa: A Robustly Optimized BERT Pretraining Approach** - Liu et al., 2019
   - https://arxiv.org/abs/1907.11692
   - Référence pour ratio warmup 6%

8. **HuggingFace Token Classification Guide**
   - https://huggingface.co/docs/transformers/tasks/token_classification
   - Moodle d'alignement subword-label

9. **seqeval: A Python framework for sequence labeling evaluation**
   - https://github.com/chakki-works/seqeval
   - Métriques entity-level pour NER

### Papiers en Attente d'Évaluation

10. **MAPA Project** - Legal PII annoté
    - https://aclanthology.org/2022.lrec-1.400/

11. **3CEL Contracts** - Clauses contrats
    - https://arxiv.org/abs/2501.15990

12. **IMPACT-es Corpus** - Noms historiques
    - https://arxiv.org/pdf/1306.3692.pdf

---

**Dernière mise à jour :** 2026-02-03
**Prochaine révision :** Post-entraînement
