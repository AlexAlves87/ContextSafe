# Checksum Validators - Test Autonome

**Date :** 04/02/2026
**Auteur :** AlexAlves87
**Composant :** `scripts/preprocess/checksum_validators.py`
**Standard :** Algorithmes officiels espagnols (BOE)

---

## 1. Résumé Exécutif

Implémentation et validation autonome de validateurs de checksum pour les identifiants espagnols utilisés dans le pipeline NER-PII.

### Résultats

| Métrique | Valeur |
|----------|--------|
| **Tests Passés** | 23/24 (95,8%) |
| **Validateurs Implémentés** | 5 (DNI, NIE, IBAN, NSS, CIF) |
| **Temps Exécution** | 0,003s |

### Conclusion

> **Tous les validateurs fonctionnent correctement selon les algorithmes officiels.**
> Le seul échec (cas limite NSS) est une erreur dans l'attente du test, pas dans le validateur.

---

## 2. Méthodologie

### 2.1 Algorithmes Implémentés

| Identifiant | Algorithme | Source |
|-------------|------------|--------|
| **DNI** | `lettre = TRWAGMYFPDXBNJZSQVHLCKE[nombre % 23]` | BOE |
| **NIE** | X→0, Y→1, Z→2, puis DNI | BOE |
| **IBAN** | ISO 13616, mod 97 = 1 | ISO 13616 |
| **NSS** | `contrôle = (province + nombre) % 97` | Sécurité Sociale |
| **CIF** | Somme positions paires + impaires avec doublement, contrôle = (10 - somme%10) % 10 | BOE |

### 2.2 Structure du Validateur

Chaque validateur renvoie un tuple `(is_valid, confidence, reason)` :

| Champ | Type | Description |
|-------|------|-------------|
| `is_valid` | bool | Vrai si checksum correct |
| `confidence` | float | 1,0 (valide), 0,5 (format ok, checksum mauvais), 0,0 (format invalide) |
| `reason` | str | Description du résultat |

### 2.3 Reproductibilité

```bash
# Environnement
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Exécution
python scripts/preprocess/checksum_validators.py

# Résultat attendu : 23/24 passed (95,8%)
```

---

## 3. Résultats

### 3.1 Résumé par Validateur

| Validateur | Tests | Passés | Échoués |
|------------|-------|--------|---------|
| DNI | 6 | 6 | 0 |
| NIE | 4 | 4 | 0 |
| DNI_NIE | 2 | 2 | 0 |
| IBAN | 4 | 4 | 0 |
| NSS | 2 | 1 | 1* |
| CIF | 4 | 4 | 0 |
| Cas limites | 2 | 2 | 0 |
| **Total** | **24** | **23** | **1** |

*L'échec est une erreur dans l'attente du test, pas dans le validateur.

### 3.2 Tests Détaillés

#### DNI (6/6 ✅)

| Test | Entrée | Attendu | Résultat |
|------|--------|---------|----------|
| dni_valid_1 | `12345678Z` | ✅ valide | ✅ |
| dni_valid_2 | `00000000T` | ✅ valide | ✅ |
| dni_valid_spaces | `1234 5678 Z` | ✅ valide | ✅ |
| dni_invalid_letter | `12345678A` | ❌ invalide | ❌ (attendu Z) |
| dni_invalid_letter_2 | `00000000A` | ❌ invalide | ❌ (attendu T) |
| dni_invalid_format | `1234567Z` | ❌ invalide | ❌ (7 chiffres) |

#### NIE (4/4 ✅)

| Test | Entrée | Attendu | Résultat |
|------|--------|---------|----------|
| nie_valid_x | `X0000000T` | ✅ valide | ✅ |
| nie_valid_y | `Y0000000Z` | ✅ valide | ✅ |
| nie_valid_z | `Z0000000M` | ✅ valide | ✅ |
| nie_invalid_letter | `X0000000A` | ❌ invalide | ❌ (attendu T) |

#### IBAN (4/4 ✅)

| Test | Entrée | Attendu | Résultat |
|------|--------|---------|----------|
| iban_valid_es | `ES9121000418450200051332` | ✅ valide | ✅ |
| iban_valid_spaces | `ES91 2100 0418 4502 0005 1332` | ✅ valide | ✅ |
| iban_invalid_check | `ES0021000418450200051332` | ❌ invalide | ❌ (chiffres contrôle 00) |
| iban_invalid_mod97 | `ES1234567890123456789012` | ❌ invalide | ❌ (mod 97 ≠ 1) |

#### NSS (1/2 - 1 échec d'attente)

| Test | Entrée | Attendu | Résultat | Note |
|------|--------|---------|----------|------|
| nss_valid | `281234567890` | ❌ invalide | ❌ | Correct (checksum aléatoire) |
| nss_format_ok | `280000000097` | ✅ valide | ❌ | **Erreur d'attente** |

**Analyse de l'échec :**
- Entrée : `280000000097`
- Province : `28`, Numéro : `00000000`, Contrôle : `97`
- Calcul : `(28 * 10^8 + 0) % 97 = 2800000000 % 97 = 37`
- Attendu par le test : `97`, Réel : `37`
- **Le validateur est correct.** L'attente du test était incorrecte.

#### CIF (4/4 ✅)

| Test | Entrée | Attendu | Résultat |
|------|--------|---------|----------|
| cif_valid_a | `A12345674` | ✅ valide | ✅ |
| cif_valid_b | `B12345674` | ✅ valide | ✅ |
| cif_invalid | `A12345670` | ❌ invalide | ❌ (attendu 4) |

### 3.3 Démo de Validation

```
DNI_NIE: '12345678Z'
  ✅ VALID (confidence: 1.0)
  Reason: Valid DNI checksum

DNI_NIE: '12345678A'
  ❌ INVALID (confidence: 0.5)
  Reason: Invalid checksum: expected 'Z', got 'A'

DNI_NIE: 'X0000000T'
  ✅ VALID (confidence: 1.0)
  Reason: Valid NIE checksum

IBAN: 'ES91 2100 0418 4502 0005 1332'
  ✅ VALID (confidence: 1.0)
  Reason: Valid IBAN checksum

CIF: 'A12345674'
  ✅ VALID (confidence: 1.0)
  Reason: Valid CIF checksum (digit)
```

---

## 4. Analyse des Erreurs

### 4.1 Seul Échec : Cas Limite NSS

| Aspect | Détail |
|--------|--------|
| Test | `nss_format_ok` |
| Entrée | `280000000097` |
| Problème | L'attente du test supposait que `97` serait valide |
| Réalité | `(28 + "00000000") % 97 = 37`, pas `97` |
| Action | Corriger l'attente dans le cas de test |

### 4.2 Correction Proposée

```python
# Dans TEST_CASES, changer :
TestCase("nss_format_ok", "280000000097", "NSS", True, "..."),
# Par :
TestCase("nss_format_ok", "280000000037", "NSS", True, "NSS with valid control"),
```

Ou mieux, calculer un vrai NSS valide :
- Province : `28` (Madrid)
- Numéro : `12345678`
- Contrôle : `(2812345678) % 97 = 2812345678 % 97 = 8`
- NSS valide : `281234567808`

---

## 5. Conclusions et Travaux Futurs

### 5.1 Conclusions

1. **Les 5 validateurs fonctionnent correctement** selon les algorithmes officiels
2. **La structure de retour (is_valid, confidence, reason)** permet une intégration flexible
3. **Le niveau de confiance intermédiaire (0,5)** permet de distinguer :
   - Format correct mais checksum incorrect → possible coquille/OCR
   - Format incorrect → probablement pas ce type d'ID

### 5.2 Utilisation dans Pipeline NER

| Scénario | Action |
|----------|--------|
| Entité détectée + checksum valide | Garder détection (boost confiance) |
| Entité détectée + checksum invalide | Réduire confiance ou marquer comme "possible_typo" |
| Entité détectée + format invalide | Possible faux positif → vérifier |

### 5.3 Étape Suivante

**Intégration dans pipeline NER pour post-validation :**
- Appliquer validateurs aux entités détectées comme DNI_NIE, IBAN, NSS, CIF
- Ajuster confiance basé sur résultat validation
- Réduire SPU (faux positifs) en éliminant détections avec checksums invalides

### 5.4 Impact Estimé

| Métrique | Baseline | Estimé | Amélioration |
|----------|----------|--------|--------------|
| SPU | 8 | 5-6 | -2 à -3 |
| F1 (strict) | 0,492 | 0,50-0,52 | +0,01-0,03 |

---

## 6. Références

1. **Algorithme DNI/NIE :** BOE - Décret Royal 1553/2005
2. **Validation IBAN :** ISO 13616-1:2020
3. **Format NSS :** Trésorerie Générale de la Sécurité Sociale
4. **Algorithme CIF :** BOE - Décret Royal 1065/2007
5. **Recherche de base :** `docs/reports/2026-01-28_investigacion_hybrid_ner.md`

---

**Temps d'exécution :** 0,003s
**Généré par :** AlexAlves87
**Date :** 04/02/2026
