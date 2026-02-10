# Modèles Regex pour Identifiants Espagnols - Test Autonome

**Date :** 05/02/2026
**Auteur :** AlexAlves87
**Composant :** `scripts/preprocess/spanish_id_patterns.py`
**Standard :** CHPDA (2025) - Approche hybride regex+NER

---

## 1. Résumé Exécutif

Implémentation de modèles regex pour détecter les identifiants espagnols avec des formats variants (espaces, tirets, points) que les modèles NER transformer échouent typiquement à détecter.

### Résultats

| Métrique | Valeur |
|----------|--------|
| **Tests Passés** | 22/22 (100%) |
| **Types d'Entité** | 5 (DNI_NIE, IBAN, NSS, CIF, PHONE) |
| **Total Modèles** | 25 |
| **Temps Exécution** | 0,003s |

### Conclusion

> **Tous les modèles fonctionnent correctement pour les formats avec espaces et séparateurs.**
> Cela complète le NER transformer qui échoue dans des cas comme "12 345 678 Z" ou "ES91 2100 0418...".

---

## 2. Méthodologie

### 2.1 Recherche de Base

| Papier | Approche | Application |
|--------|----------|-------------|
| **CHPDA (arXiv 2025)** | Hybride Regex + AI NER | Réduit faux positifs |
| **Hybrid ReGex (JCO 2025)** | Pipeline léger regex + ML | Extraction données médicales |
| **Legal NLP Survey (2024)** | NER spécialisé légal | Modèles réglementaires |

### 2.2 Modèles Implémentés

| Type | Modèles | Exemples |
|------|---------|----------|
| **DNI** | 6 | `12345678Z`, `12 345 678 Z`, `12.345.678-Z` |
| **NIE** | 3 | `X1234567Z`, `X 1234567 Z`, `X-1234567-Z` |
| **IBAN** | 3 | `ES9121...`, `ES91 2100 0418...` |
| **NSS** | 3 | `281234567890`, `28/12345678/90` |
| **CIF** | 3 | `A12345674`, `A-1234567-4` |
| **PHONE** | 7 | `612345678`, `612 345 678`, `+34 612...` |

### 2.3 Reproductibilité

```bash
# Environnement
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Exécution
python scripts/preprocess/spanish_id_patterns.py

# Sortie attendue : 22/22 passed (100.0%)
```

---

## 3. Résultats

### 3.1 Tests par Type

| Type | Tests | Passés | Exemples Clés |
|------|-------|--------|---------------|
| DNI | 6 | 6 | Standard, espaces 2-3-3, points |
| NIE | 3 | 3 | Standard, espaces, tirets |
| IBAN | 2 | 2 | Standard, espaces groupes 4 |
| NSS | 2 | 2 | Barres, espaces |
| CIF | 2 | 2 | Standard, tirets |
| PHONE | 4 | 4 | Mobile, fixe, international |
| Négatifs | 2 | 2 | Rejette formats invalides |
| Multi | 1 | 1 | Multiples entités dans texte |

### 3.2 Démo de Détection

| Entrée | Détection | Normalisé |
|--------|-----------|-----------|
| `DNI 12 345 678 Z` | ✅ DNI_NIE | `12345678Z` |
| `IBAN ES91 2100 0418 4502 0005 1332` | ✅ IBAN | `ES9121000418450200051332` |
| `NIE X-1234567-Z` | ✅ DNI_NIE | `X1234567Z` |
| `Tel: 612 345 678` | ✅ PHONE | `612345678` |
| `CIF A-1234567-4` | ✅ CIF | `A12345674` |

### 3.3 Structure de Match

```python
@dataclass
class RegexMatch:
    text: str           # "12 345 678 Z"
    entity_type: str    # "DNI_NIE"
    start: int          # 4
    end: int            # 16
    confidence: float   # 0,90
    pattern_name: str   # "dni_spaced_2_3_3"
```

---

## 4. Analyse des Modèles

### 4.1 Niveaux de Confiance

| Niveau | Confiance | Critère |
|--------|-----------|---------|
| Haut | 0,95 | Format standard sans ambiguïté |
| Moyen | 0,90 | Format avec séparateurs valides |
| Bas | 0,70-0,85 | Formats pouvant être ambigus |

### 4.2 Modèles DNI avec Espaces (Problème Original)

Le test adversarial `dni_with_spaces` échouait car le NER ne détectait pas "12 345 678 Z".

**Solution Implémentée :**
```python
# Modèle pour espaces 2-3-3
r'\b(\d{2})\s+(\d{3})\s+(\d{3})\s*([A-Z])\b'
```

Ce modèle détecte :
- `12 345 678 Z` ✅
- `12 345 678Z` ✅ (sans espace avant lettre)

### 4.3 Normalisation pour Checksum

Fonction `normalize_match()` élimine séparateurs pour validation :

```python
"12 345 678 Z" → "12345678Z"
"ES91 2100 0418..." → "ES9121000418..."
"X-1234567-Z" → "X1234567Z"
```

---

## 5. Conclusions et Travaux Futurs

### 5.1 Conclusions

1. **25 modèles couvrent formats variants** d'identifiants espagnols
2. **Normalisation permet intégration** avec validateur checksum
3. **Confiance variable** distingue formats plus/moins fiables
4. **Détection chevauchement** évite doublons

### 5.2 Intégration Pipeline

```
Texte Entrée
       ↓
┌──────────────────────┐
│  1. TextNormalizer   │  Nettoyage Unicode/OCR
└──────────────────────┘
       ↓
┌──────────────────────┐
│  2. NER Transformer  │  Prédictions RoBERTalex
└──────────────────────┘
       ↓
┌──────────────────────┐
│  3. Modèles Regex    │  ← NOUVEAU : détecte espaces
└──────────────────────┘
       ↓
┌──────────────────────┐
│  4. Fusion & Dedup   │  Combine NER + Regex
└──────────────────────┘
       ↓
┌──────────────────────┐
│  5. Valid. Checksum  │  Ajuste confiance
└──────────────────────┘
       ↓
Entités Finales
```

### 5.3 Impact Estimé

| Test Adversarial | Avant | Après | Amélioration |
|------------------|-------|-------|--------------|
| `dni_with_spaces` | MIS:1 | COR:1 | +1 COR |
| `iban_with_spaces` | PAR:1 | COR:1 | +1 COR |
| `phone_international` | MIS:1 | COR:1 | +1 COR (potentiel) |

**Estimation Totale :** +2-3 COR, conversion de MIS et PAR à COR.

---

## 6. Références

1. **CHPDA (2025) :** [arXiv](https://arxiv.org/html/2502.07815v1) - Approche hybride regex+NER
2. **Hybrid ReGex (2025) :** [JCO](https://ascopubs.org/doi/10.1200/CCI-25-00130) - Extraction données médicales
3. **Legal NLP Survey (2024) :** [arXiv](https://arxiv.org/html/2410.21306v3) - NER pour domaine légal

---

**Temps d'exécution :** 0,003s
**Généré par :** AlexAlves87
**Date :** 05/02/2026
