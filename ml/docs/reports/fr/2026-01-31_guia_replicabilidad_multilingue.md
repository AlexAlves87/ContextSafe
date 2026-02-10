# Guide de Réplicabilité : Pipeline NER-PII Multilingue

**Date :** 31/01/2026
**Auteur :** AlexAlves87
**Projet :** ContextSafe ML - Expansion Multilingue
**Version :** 1.0.0

---

## 1. Résumé Exécutif

Ce document décrit comment répliquer le pipeline hybride NER-PII de ContextSafe (légal espagnol, F1 0.788) pour d'autres langues européennes. L'approche est **modulaire** : chaque composant est adapté à la langue cible tout en maintenant l'architecture éprouvée.

### Leçon Apprise (Expérience LoRA)

| Approche | F1 Adversarial | Verdict |
|----------|----------------|---------|
| Fine-tuning LoRA pur | 0.016 | ❌ Surapprentissage sévère |
| Pipeline hybride (5 éléments) | **0.788** | ✅ Généralise bien |

> **Conclusion :** Le fine-tuning de transformers sans le pipeline hybride ne généralise pas aux cas adverses. Les 5 éléments de post-traitement sont **essentiels**.

---

## 2. Architecture du Pipeline (Agnostique à la Langue)

```
┌─────────────────────────────────────────────────────────────────┐
│                     PIPELINE HYBRIDE NER-PII                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Texte d'entrée                                                  │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [1] TextNormalizer                     │ ← Agnostique         │
│  │     - Unicode NFKC                     │                      │
│  │     - Homoglyphes (Cyrillique→Latin)   │                      │
│  │     - Suppression zéro-largeur         │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [NER] Transformer LegalBERT            │ ← ADAPTER PAR LANGUE │
│  │     - ES: RoBERTa-BNE CAPITEL NER      │                      │
│  │     - EN: Legal-BERT                   │                      │
│  │     - FR: JuriBERT                     │                      │
│  │     - IT: Italian-Legal-BERT           │                      │
│  │     - PT: Legal-BERTimbau              │                      │
│  │     - DE: German-Legal-BERT            │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [2] Checksum Validators                │ ← ADAPTER PAR PAYS   │
│  │     - Algorithmes de vérification      │                      │
│  │     - Ajustement de confiance          │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [3] Regex Patterns                     │ ← ADAPTER PAR PAYS   │
│  │     - Identifiants nationaux           │                      │
│  │     - Formats avec espaces/tirets      │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [4] Date Patterns                      │ ← ADAPTER PAR LANGUE │
│  │     - Mois en langue locale            │                      │
│  │     - Formats légaux/notariaux         │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [5] Boundary Refinement                │ ← ADAPTER PAR LANGUE │
│  │     - Préfixes honorifiques            │                      │
│  │     - Suffixes d'organisation          │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  Entités finales                                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Composants par Type d'Adaptation

| Composant | Adaptation | Effort |
|-----------|------------|--------|
| TextNormalizer | Aucune (universel) | 0 |
| Transformer NER | Changer modèle de base | Faible |
| Checksum Validators | Algorithmes par pays | Moyen |
| Regex Patterns | Modèles par pays | Élevé |
| Date Patterns | Mois/formats par langue | Moyen |
| Boundary Refinement | Préfixes/suffixes par langue | Moyen |

---

## 3. Modèles de Base Recommandés par Langue

### 3.1 Modèles Monolingues (Performance Maximale)

| Langue | Modèle | HuggingFace | Params | Corpus |
|--------|--------|-------------|--------|--------|
| 🇪🇸 Espagnol | RoBERTa-BNE CAPITEL NER | `PlanTL-GOB-ES/roberta-base-bne-capitel-ner` | 125M | BNE + CAPITEL NER |
| 🇬🇧 Anglais | Legal-BERT | `nlpaueb/legal-bert-base-uncased` | 110M | 12GB légal |
| 🇫🇷 Français | JuriBERT | `dascim/juribert-base` | 110M | Légifrance |
| 🇮🇹 Italien | Italian-Legal-BERT | `dlicari/Italian-Legal-BERT` | 110M | Giurisprudenza |
| 🇵🇹 Portugais | Legal-BERTimbau | `rufimelo/Legal-BERTimbau-base` | 110M | 30K docs |
| 🇩🇪 Allemand | German-Legal-BERT | `elenanereiss/bert-german-legal` | 110M | Bundesrecht |

### 3.2 Modèle Multilingue (Déploiement Rapide)

| Modèle | HuggingFace | Params | Langues |
|--------|-------------|--------|---------|
| Legal-XLM-RoBERTa | `joelniklaus/legal-xlm-roberta-large` | 355M | 24 langues |

**Compromis :**
- Monolingue : +2-5% F1, nécessite un modèle par langue
- Multilingue : Un seul modèle, performance légèrement inférieure

---

## 4. Adaptations par Pays

### 4.1 Espagne (Implémenté ✅)

#### Identifiants Nationaux

| Type | Format | Checksum | Regex |
|------|--------|----------|-------|
| DNI | 8 chiffres + lettre | mod 23 | `\d{8}[A-Z]` |
| NIE | X/Y/Z + 7 chiffres + lett. | mod 23 | `[XYZ]\d{7}[A-Z]` |
| CIF | Lettre + 7 ch. + contr. | somme pairs/impairs | `[A-W]\d{7}[0-9A-J]` |
| IBAN | ES + 22 caractères | ISO 13616 mod 97 | `ES\d{2}[\d\s]{20}` |
| NSS | 12 chiffres | mod 97 | `\d{12}` |
| Plaque Immat. | 4 chiffres + 3 lettres | aucun | `\d{4}[BCDFGHJKLMNPRSTVWXYZ]{3}` |

#### Préfixes Honorifiques

```python
PREFIXES_ES = [
    "Don", "Doña", "D.", "Dña.", "D.ª",
    "Sr.", "Sra.", "Srta.",
    "Ilmo.", "Ilma.", "Excmo.", "Excma.",
]
```

#### Mois

```python
MONTHS_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]
```

---

### 4.2 France 🇫🇷

#### Identifiants Nationaux

| Type | Format | Checksum | Regex |
|------|--------|----------|-------|
| NIR (Sécu) | 15 chiffres | mod 97 | `[12]\d{2}(0[1-9]|1[0-2])\d{2}\d{3}\d{3}\d{2}` |
| SIRET | 14 chiffres | Luhn | `\d{14}` |
| SIREN | 9 chiffres | Luhn | `\d{9}` |
| IBAN | FR + 25 caractères | ISO 13616 | `FR\d{2}[\d\s]{23}` |
| Carte ID | 12 caractères | aucun | `[A-Z0-9]{12}` |

#### Préfixes Honorifiques

```python
PREFIXES_FR = [
    "Monsieur", "Madame", "Mademoiselle",
    "M.", "Mme", "Mlle",
    "Maître", "Me", "Me.",
    "Docteur", "Dr", "Dr.",
]
```

#### Mois

```python
MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
]
```

#### Suffixes d'Organisation

```python
ORG_SUFFIXES_FR = [
    "S.A.", "SA", "S.A.S.", "SAS", "S.A.R.L.", "SARL",
    "S.C.I.", "SCI", "E.U.R.L.", "EURL", "S.N.C.", "SNC",
]
```

---

### 4.3 Italie 🇮🇹

#### Identifiants Nationaux

| Type | Format | Checksum | Regex |
|------|--------|----------|-------|
| Codice Fiscale | 16 caractères | mod 26 spécial | `[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]` |
| Partita IVA | 11 chiffres | Luhn variante | `\d{11}` |
| IBAN | IT + 25 caractères | ISO 13616 | `IT\d{2}[A-Z][\d\s]{22}` |
| Carta Identità | 2 lettres + 7 chiffres | aucun | `[A-Z]{2}\d{7}` |

#### Checksum Codice Fiscale

```python
def validate_codice_fiscale(cf: str) -> bool:
    """Algorithme mod 26 avec valeurs spéciales pour positions paires/impaires."""
    ODD_VALUES = {'0': 1, '1': 0, '2': 5, ...}  # Table complète
    EVEN_VALUES = {'0': 0, '1': 1, '2': 2, ...}
    # Somme positions impaires avec ODD_VALUES, paires avec EVEN_VALUES
    # Lettre de contrôle = chr(ord('A') + total % 26)
```

#### Préfixes Honorifiques

```python
PREFIXES_IT = [
    "Signor", "Signora", "Signorina",
    "Sig.", "Sig.ra", "Sig.na",
    "Dott.", "Dott.ssa", "Avv.", "Ing.",
    "On.", "Sen.", "Onorevole",
]
```

#### Mois

```python
MONTHS_IT = [
    "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"
]
```

---

### 4.4 Portugal 🇵🇹

#### Identifiants Nationaux

| Type | Format | Checksum | Regex |
|------|--------|----------|-------|
| NIF | 9 chiffres | mod 11 | `[123568]\d{8}` |
| CC (Cartão Cidadão) | 8 ch. + 1 lett. + 2 ch. | mod 11 + lettre | `\d{8}[A-Z]\d{2}` |
| NISS | 11 chiffres | mod 10 | `\d{11}` |
| IBAN | PT + 23 caractères | ISO 13616 | `PT\d{2}[\d\s]{21}` |

#### Checksum NIF Portugal

```python
def validate_nif_pt(nif: str) -> bool:
    """Algorithme mod 11 avec poids décroissants."""
    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(d) * w for d, w in zip(nif[:8], weights))
    control = 11 - (total % 11)
    if control >= 10:
        control = 0
    return int(nif[8]) == control
```

#### Préfixes Honorifiques

```python
PREFIXES_PT = [
    "Senhor", "Senhora", "Sr.", "Sra.", "Srª",
    "Dom", "Dona", "D.",
    "Doutor", "Doutora", "Dr.", "Dra.",
    "Exmo.", "Exma.",
]
```

---

### 4.5 Allemagne 🇩🇪

#### Identifiants Nationaux

| Type | Format | Checksum | Regex |
|------|--------|----------|-------|
| Steuer-ID | 11 chiffres | ISO 7064 mod 11-10 | `\d{11}` |
| Personalausweis | 10 caractères | mod 10 spécial | `[A-Z0-9]{10}` |
| IBAN | DE + 20 caractères | ISO 13616 | `DE\d{2}[\d\s]{18}` |
| Handelsregister | HRA/HRB + numéro | aucun | `HR[AB]\s?\d+` |

#### Préfixes Honorifiques

```python
PREFIXES_DE = [
    "Herr", "Frau",
    "Dr.", "Prof.", "Prof. Dr.",
    "Rechtsanwalt", "RA", "Notar",
]
```

#### Mois

```python
MONTHS_DE = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember"
]
```

---

### 4.6 Royaume-Uni 🇬🇧

#### Identifiants Nationaux

| Type | Format | Checksum | Regex |
|------|--------|----------|-------|
| NI Number | 2 lett. + 6 ch. + lett. | non vérifiable | `[A-Z]{2}\d{6}[A-D]` |
| Company Number | 8 caractères | aucun | `[A-Z]{2}\d{6}|[\d]{8}` |
| IBAN | GB + 22 caractères | ISO 13616 | `GB\d{2}[A-Z]{4}[\d\s]{14}` |
| Passeport | 9 chiffres | aucun | `\d{9}` |

#### Préfixes Honorifiques

```python
PREFIXES_EN = [
    "Mr", "Mr.", "Mrs", "Mrs.", "Ms", "Ms.", "Miss",
    "Dr", "Dr.", "Prof", "Prof.",
    "Sir", "Dame", "Lord", "Lady",
    "The Honourable", "Hon.",
]
```

---

## 5. Checklist d'Implémentation par Langue

### Phase 1 : Préparation (1-2 jours)

- [ ] **Sélectionner modèle de base** de la table 3.1
- [ ] **Télécharger modèle** vers `models/pretrained/{modele}/`
- [ ] **Vérifier chargement** avec script de test
- [ ] **Définir catégories PII** pertinentes pour le pays

### Phase 2 : Checksum Validators (2-3 jours)

- [ ] **Rechercher algorithmes de validation** pour le pays
- [ ] **Implémenter validateurs** dans `scripts/preprocess/{country}_validators.py`
- [ ] **Créer tests unitaires** (minimum 20 cas par type)
- [ ] **Documenter algorithmes** avec références officielles

### Phase 3 : Regex Patterns (3-5 jours)

- [ ] **Collecter formats officiels** d'IDs du pays
- [ ] **Implémenter modèles** dans `scripts/preprocess/{country}_id_patterns.py`
- [ ] **Inclure variantes** avec espaces, tirets, points
- [ ] **Tests avec exemples réels** (anonymisés)

### Phase 4 : Date Patterns (1-2 jours)

- [ ] **Traduire mois** vers langue cible
- [ ] **Adapter formats** légaux/notariaux locaux
- [ ] **Implémenter** dans `scripts/preprocess/{country}_date_patterns.py`
- [ ] **Tests avec dates réelles** de documents légaux

### Phase 5 : Boundary Refinement (1-2 jours)

- [ ] **Compiler liste** de préfixes honorifiques
- [ ] **Compiler liste** de suffixes d'organisation
- [ ] **Implémenter** dans `scripts/preprocess/{country}_boundary_refinement.py`
- [ ] **Tests avec noms/orgs réels**

### Phase 6 : Gazetteers (2-4 jours)

- [ ] **Prénoms** fréquents (équivalent INE)
- [ ] **Noms de famille** fréquents
- [ ] **Communes/villes**
- [ ] **Organisations** connues (entreprises, institutions)

### Phase 7 : Test Set Adversarial (2-3 jours)

- [ ] **Créer 30-40 cas** spécifiques à la langue :
  - Cas limites (formats inhabituels)
  - Adversarial (négations, exemples, fiction)
  - Corruption OCR
  - Évasion Unicode (déjà couvert)
  - Monde réel (documents légaux typiques)
- [ ] **Définir entités attendues** pour chaque cas
- [ ] **Exécuter évaluation SemEval**

### Phase 8 : Intégration (1-2 jours)

- [ ] **Intégrer composants** dans `ner_predictor_{lang}.py`
- [ ] **Exécuter test set adversarial**
- [ ] **Ajuster** jusqu'à F1 ≥ 0.70
- [ ] **Documenter résultats**

---

## 6. Estimation de l'Effort Total

| Langue | Modèle | Complexité IDs | Effort Est. |
|--------|--------|----------------|-------------|
| 🇫🇷 Français | JuriBERT | Moyenne (NIR, SIRET) | 2-3 semaines |
| 🇮🇹 Italien | Italian-Legal-BERT | Élevée (Codice Fiscale) | 3-4 semaines |
| 🇵🇹 Portugais | Legal-BERTimbau | Moyenne (NIF, CC) | 2-3 semaines |
| 🇩🇪 Allemand | German-Legal-BERT | Moyenne (Steuer-ID) | 2-3 semaines |
| 🇬🇧 Anglais | Legal-BERT | Faible (NI Number) | 1-2 semaines |

**Total pour 5 langues :** 10-15 semaines (1 développeur)
**Avec parallélisation (2-3 devs) :** 4-6 semaines

---

## 7. Structure de Fichiers par Langue

```
ml/
├── scripts/
│   ├── preprocess/
│   │   ├── spanish_id_patterns.py      # ✅ Implémenté
│   │   ├── spanish_date_patterns.py    # ✅ Implémenté
│   │   ├── boundary_refinement.py      # ✅ Implémenté (adapter)
│   │   │
│   │   ├── french_id_patterns.py       # À implémenter
│   │   ├── french_date_patterns.py
│   │   ├── french_validators.py
│   │   │
│   │   ├── italian_id_patterns.py      # À implémenter
│   │   ├── italian_date_patterns.py
│   │   ├── italian_validators.py
│   │   │
│   │   └── ... (par langue)
│   │
│   ├── inference/
│   │   ├── ner_predictor.py            # ✅ Espagnol
│   │   ├── ner_predictor_fr.py         # À implémenter
│   │   ├── ner_predictor_it.py
│   │   └── ...
│   │
│   └── evaluate/
│       ├── test_ner_predictor_adversarial_v2.py  # ✅ Espagnol
│       ├── adversarial_tests_fr.py               # À implémenter
│       └── ...
│
├── gazetteers/
│   ├── es/                             # ✅ Implémenté
│   │   ├── nombres.json
│   │   ├── apellidos.json
│   │   └── municipios.json
│   │
│   ├── fr/                             # À implémenter
│   ├── it/
│   ├── pt/
│   ├── de/
│   └── en/
│
└── models/
    └── pretrained/
        ├── legal-xlm-roberta-base/     # ✅ Téléchargé
        ├── juribert-base/              # À télécharger
        ├── italian-legal-bert/
        └── ...
```

---

## 8. Références

### 8.1 Papiers et Documentation

| Ressource | URL | Usage |
|-----------|-----|-------|
| Legal-BERT Paper | aclanthology.org/2020.findings-emnlp.261 | Architecture |
| JuriBERT Paper | aclanthology.org/2021.nllp-1.9 | Français légal |
| SemEval 2013 Task 9 | aclweb.org/anthology/S13-2013 | Métriques d'évaluation |
| ISO 13616 (IBAN) | iso.org/standard/81090.html | Checksum IBAN |

### 8.2 Sources de Gazetteers par Pays

| Pays | Noms | Communes | IDs |
|------|------|----------|-----|
| 🇪🇸 Espagne | INE | INE | BOE |
| 🇫🇷 France | INSEE | INSEE | Légifrance |
| 🇮🇹 Italie | ISTAT | ISTAT | Normattiva |
| 🇵🇹 Portugal | INE-PT | INE-PT | DRE |
| 🇩🇪 Allemagne | Statistisches Bundesamt | - | Bundesrecht |
| 🇬🇧 R-U | ONS | ONS | legislation.gov.uk |

---

## 9. Leçons Apprises (ContextSafe ES)

### 9.1 Ce qui a fonctionné

1.  **Pipeline hydride > ML pur** : Les transformers seuls ne généralisent pas aux cas adverses
2.  **Regex pour formats variables** : DNI avec espaces, IBAN avec groupes
3.  **Validation Checksum** : Réduit significativement les faux positifs
4.  **Raffinement de limites** : Convertit PAR→COR (16 cas corrigés)
5.  **Test set adversarial** : Détecte les problèmes avant production

### 9.2 Ce qui n'a PAS fonctionné

1.  **Fine-tuning LoRA sans pipeline** : 0.016 F1 en adversarial (surapprentissage)
2.  **GLiNER zero-shot** : 0.325 F1 (ne connaît pas les formats espagnols)
3.  **Se fier uniquement aux métriques dev set** : 0.989 dev vs 0.016 adversarial

### 9.3 Recommandations

1.  **Toujours créer un test set adversarial** avant de déclarer "prêt"
2.  **Implémenter validateurs checksum** pour tous les IDs avec vérification mathématique
3.  **Investir dans des gazetteers de qualité** (noms, communes)
4.  **Documenter chaque élément** avec des tests autonomes

---

## 10. Prochaines Étapes

1.  **Prioriser langue** selon demande marché
2.  **Télécharger modèle de base** de la langue sélectionnée
3.  **Adapter composants** en suivant cette checklist
4.  **Créer test set adversarial** spécifique
5.  **Itérer jusqu'à F1 ≥ 0.70** en adversarial

---

**Généré par :** AlexAlves87
**Date :** 31/01/2026
**Version :** 1.0.0
