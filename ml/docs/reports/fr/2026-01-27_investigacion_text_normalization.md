# Recherche : Normalisation de Texte pour NER dans les Documents Juridiques

**Date :** 2026-01-27
**Auteur :** AlexAlves87
**Type :** Revue de Littérature Académique
**État :** Terminé

---

## 1. Résumé Exécutif

Cette recherche analyse les meilleures pratiques pour la normalisation de texte dans les pipelines NER, en mettant l'accent sur :
1. La normalisation Unicode (fullwidth, zero-width, homoglyphes)
2. La correction des artefacts OCR
3. L'intégration avec les modèles transformers

### Principales Découvertes

| Découverte | Source | Impact |
|------------|--------|--------|
| NFKC normalise fullwidth → ASCII automatiquement | UAX #15 Standard Unicode | Haut |
| Les caractères zero-width (U+200B-U+200F) doivent être explicitement supprimés | Consortium Unicode | Haut |
| Des neurones sensibles à l'OCR existent dans les transformers et peuvent être modulés | arXiv:2409.16934 (ICADL 2024) | Moyen |
| Le préchauffage doit correspondre au pré-entraînement du modèle | Meilleures pratiques 2024 | Critique |
| NFKC détruit l'information dans les scripts complexes (arabe, hébreu) | UAX #15 | Bas (n'applique pas à l'espagnol) |

---

## 2. Méthodologie

### 2.1 Sources Consultées

| Source | Type | Année | Pertinence |
|--------|------|-------|------------|
| UAX #15 Standard Unicode | Spécification | 2024 | Norme Unicode |
| arXiv:2409.16934 | Papier (ICADL 2024) | 2024 | Neurones sensibles à l'OCR |
| TACL Neural OCR Post-Hoc | Papier académique | 2021 | Correction OCR neurale |
| Brenndoerfer NLP Guide | Tutoriel technique | 2024 | Meilleures pratiques industrielles |
| Promptfoo Security | Article technique | 2024 | Évasion Unicode en IA |

### 2.2 Critères de Recherche

- "text normalization NER preprocessing Unicode OCR"
- "Unicode normalization NLP NER fullwidth characters zero-width space"
- "OCR post-correction NER robustness neural network ACL EMNLP"

---

## 3. Résultats

### 3.1 Formes de Normalisation Unicode

Le standard Unicode (UAX #15) définit 4 formes de normalisation :

| Forme | Nom | Description | Utilisation en NER |
|-------|-----|-------------|--------------------|
| **NFC** | Composition Canonique | Compose les caractères (é = e + ´) | Standard |
| **NFD** | Décomposition Canonique | Décompose les caractères | Recherche |
| **NFKC** | Composition de Compatibilité | NFC + compatibilité | **Recommandé pour NER** |
| **NFKD** | Décomposition de Compatibilité | NFD + compatibilité | Analyse |

**Source :** [UAX #15: Unicode Normalization Forms](https://unicode.org/reports/tr15/)

#### 3.1.1 NFKC pour la Normalisation d'Entités

NFKC est la forme recommandée pour NER car :

```
Fullwidth :  １２３４５６７８ → 12345678
Superscript : ² → 2
Fractions :   ½ → 1/2
Roman :       Ⅳ → IV
Ligatures :   ﬁ → fi
```

**Avertissement :** NFKC détruit l'information dans les scripts complexes (arabe, hébreu, devanagari) où les caractères de contrôle sont sémantiquement pertinents. Pour l'espagnol juridique, ce n'est pas un problème.

### 3.2 Caractères Invisibles Problématiques

**Source :** [The Invisible Threat: Zero-Width Unicode Characters](https://www.promptfoo.dev/blog/invisible-unicode-threats/)

| Point de Code | Nom | Problème | Action |
|---------------|-----|----------|--------|
| U+200B | Zero Width Space | Casse la tokenisation | Supprimer |
| U+200C | Zero Width Non-Joiner | Sépare les caractères joints | Supprimer |
| U+200D | Zero Width Joiner | Joint les caractères séparés | Supprimer |
| U+200E | Left-to-Right Mark | Confond la direction du texte | Supprimer |
| U+200F | Right-to-Left Mark | Confond la direction du texte | Supprimer |
| U+FEFF | BOM / Zero Width No-Break | Artefact d'encodage | Supprimer |
| U+00A0 | Non-Breaking Space | Non détecté par isspace() | → espace normal |
| U+00AD | Soft Hyphen | Trait d'union invisible | Supprimer |

**Impact sur NER :**
- DNI `123​456​78Z` (avec U+200B) ne correspond pas à la regex `\d{8}[A-Z]`
- Le tokenizer divise le mot en plusieurs tokens
- Le modèle ne reconnaît pas l'entité

### 3.3 Homoglyphes et Évasion

**Source :** [Invisible Unicode Tricks Bypass AI Detection](https://justdone.com/blog/ai/invisible-unicode-tricks)

| Latin | Cyrillique | Visuel | Code |
|-------|------------|--------|------|
| A | А | Identique | U+0041 vs U+0410 |
| B | В | Identique | U+0042 vs U+0412 |
| E | Е | Identique | U+0045 vs U+0415 |
| O | О | Identique | U+004F vs U+041E |
| X | Х | Identique | U+0058 vs U+0425 |

**Impact sur NER :**
- DNI `12345678Х` (Cyrillique) ne correspond pas à la regex avec `[A-Z]`
- Le modèle peut ne pas reconnaître comme DNI valide

**Solution :** Normaliser les homoglyphes latins communs avant NER.

### 3.4 Neurones Sensibles à l'OCR dans les Transformers

**Source :** [Investigating OCR-Sensitive Neurons](https://arxiv.org/abs/2409.16934) (ICADL 2024)

#### Découvertes du Papier

1. **Les transformers ont des neurones sensibles à l'OCR :**
   - Identifiés par analyse des modèles d'activation
   - Répondent différemment au texte propre vs corrompu

2. **Couches critiques identifiées :**
   - Llama 2 : Couches 0-2, 11-13, 23-28
   - Mistral : Couches 29-31

3. **Solution proposée :**
   - Neutraliser les neurones sensibles à l'OCR
   - Améliore la performance NER sur les documents historiques

#### Application à ContextSafe

Pour notre modèle RoBERTa fine-tuned :
- La normalisation de texte AVANT l'inférence est plus pratique
- Neutraliser les neurones nécessite de modifier l'architecture du modèle
- **Recommandation :** Pré-traitement, pas modification du modèle

### 3.5 Erreurs OCR Communes et Normalisation

**Source :** [OCR Data Entry: Preprocessing Text for NLP](https://labelyourdata.com/articles/ocr-data-entry)

| Erreur OCR | Modèle | Normalisation |
|------------|--------|---------------|
| l ↔ I ↔ 1 | `DNl`, `DN1` | → `DNI` |
| O ↔ 0 | `2l0O` | Contextuel (nombres) |
| rn ↔ m | `nom` → `nom` | Dictionnaire |
| S ↔ 5 | `E5123` | Contextuel |
| B ↔ 8 | `B-123` vs `8-123` | Contextuel |

**Stratégie recommandée :**
1. **Pré-traitement simple :** l/I/1 → normaliser selon le contexte
2. **Validation postérieure :** Checksums (DNI, IBAN) rejettent les invalides
3. **Ne pas essayer de tout corriger :** Mieux vaut rejeter qu'inventer

### 3.6 Non-concordance Pré-traitement-Pré-entraînement

**Source :** [Text Preprocessing Guide](https://mbrenndoerfer.com/writing/text-preprocessing-nlp-tokenization-normalization)

> "If you train a model with aggressively preprocessed text but deploy it on minimally preprocessed input, performance will crater."

**Critique pour notre modèle :**
- RoBERTa-BNE a été pré-entraîné avec du texte sensible à la casse
- NE PAS appliquer lowercase
- OUI appliquer la normalisation Unicode (NFKC)
- OUI supprimer les caractères zero-width

---

## 4. Pipeline de Normalisation Proposé

### 4.1 Ordre des Opérations

```
Texte OCR/Brut
    ↓
[1] Supprimer BOM (U+FEFF)
    ↓
[2] Supprimer zero-width (U+200B-U+200F, U+2060-U+206F)
    ↓
[3] Normalisation NFKC (fullwidth → ASCII)
    ↓
[4] Normaliser les espaces (U+00A0 → espace, réduire multiples)
    ↓
[5] Mapping d'homoglyphes (Cyrillique commun → Latin)
    ↓
[6] OCR contextuel (DNl → DNI seulement si le contexte indique)
    ↓
Texte Normalisé → NER
```

### 4.2 Implémentation Python

```python
import unicodedata
import re

# Caractères à supprimer
ZERO_WIDTH = re.compile(r'[\u200b-\u200f\u2060-\u206f\ufeff]')

# Homoglyphes Cyrillique → Latin
HOMOGLYPHS = {
    '\u0410': 'A',  # А → A
    '\u0412': 'B',  # В → B
    '\u0415': 'E',  # Е → E
    '\u041e': 'O',  # О → O
    '\u0421': 'C',  # С → C
    '\u0425': 'X',  # Х → X
    '\u0430': 'a',  # а → a
    '\u0435': 'e',  # е → e
    '\u043e': 'o',  # о → o
    '\u0441': 'c',  # с → c
    '\u0445': 'x',  # х → x
}

def normalize_text(text: str) -> str:
    """
    Normaliser le texte pour le traitement NER.

    Applique : NFKC, suppression zero-width, mapping homoglyphes, normalisation espaces.
    N'applique PAS : lowercase (RoBERTa est sensible à la casse).
    """
    # 1. Supprimer BOM et zero-width
    text = ZERO_WIDTH.sub('', text)

    # 2. Normalisation NFKC (fullwidth → ASCII)
    text = unicodedata.normalize('NFKC', text)

    # 3. Mapping d'homoglyphes
    for cyrillic, latin in HOMOGLYPHS.items():
        text = text.replace(cyrillic, latin)

    # 4. Normaliser les espaces (NBSP → espace, réduire multiples)
    text = text.replace('\u00a0', ' ')
    text = re.sub(r' +', ' ', text)

    # 5. Supprimer les traits d'union invisibles
    text = text.replace('\u00ad', '')

    return text.strip()
```

### 4.3 Tests de Validation

| Input | Résultat Attendu | Test |
|-------|------------------|------|
| `１２３４５６７８Z` | `12345678Z` | Fullwidth |
| `123​456​78Z` | `12345678Z` | Zero-width |
| `12345678Х` | `12345678X` | Cyrillique X |
| `D N I` | `D N I` | Espaces (sans réduire mots) |
| `María` | `María` | Accents préservés |

---

## 5. Analyse des Écarts

### 5.1 Comparaison : Pratique Actuelle vs Best Practices

| Aspect | Best Practice | Implémentation Actuelle | Écart |
|--------|---------------|-------------------------|-------|
| Normalisation NFKC | Appliquer avant NER | Non implémenté | **CRITIQUE** |
| Suppression zero-width | Supprimer U+200B-F | Non implémenté | **CRITIQUE** |
| Mapping homoglyphes | Cyrillique → Latin | Non implémenté | HAUT |
| Normalisation espaces | NBSP → espace | Non implémenté | MOYEN |
| OCR contextuel | DNl → DNI | Non implémenté | MOYEN |
| Préservation casse | NON lowercase | Correct | ✓ OK |

### 5.2 Impact Estimé

| Correction | Effort | Impact sur Tests |
|------------|--------|------------------|
| NFKC + zero-width | Bas (10 lignes) | `fullwidth_numbers` : PASS |
| Mapping homoglyphes | Bas (table) | `cyrillic_o` : PASS (passe déjà, mais plus robuste) |
| Normalisation espaces | Bas | Réduit les FPs dans la tokenisation |
| **Total** | **~50 lignes Python** | **+5-10% pass rate adversarial** |

---

## 6. Conclusions

### 6.1 Principales Découvertes

1. **NFKC est suffisant** pour normaliser fullwidth → ASCII sans code supplémentaire
2. **Caractères zero-width** doivent être explicitement supprimés (regex simple)
3. **Homoglyphes** nécessitent une table de mapping (Cyrillique → Latin)
4. **NE PAS appliquer lowercase** - RoBERTa est sensible à la casse
5. **OCR contextuel** est complexe - mieux vaut valider avec checksums après

### 6.2 Recommandation pour ContextSafe

**Implémenter `scripts/preprocess/text_normalizer.py`** avec :
1. Fonction `normalize_text()` comme décrit ci-dessus
2. Intégrer dans le pipeline d'inférence AVANT le tokenizer
3. Appliquer aussi durant la génération du dataset d'entraînement

**Priorité :** HAUTE - Résoudra les tests `fullwidth_numbers` et améliorera la robustesse générale.

---

## 7. Références

### Papiers Académiques

1. **Investigating OCR-Sensitive Neurons to Improve Entity Recognition in Historical Documents**
   - arXiv:2409.16934, ICADL 2024
   - URL: https://arxiv.org/abs/2409.16934

2. **Neural OCR Post-Hoc Correction of Historical Corpora**
   - TACL, MIT Press
   - URL: https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00379

### Standards et Spécifications

3. **UAX #15: Unicode Normalization Forms**
   - Consortium Unicode
   - URL: https://unicode.org/reports/tr15/

### Ressources Techniques

4. **Text Normalization: Unicode Forms, Case Folding & Whitespace Handling for NLP**
   - Michael Brenndoerfer, 2024
   - URL: https://mbrenndoerfer.com/writing/text-normalization-unicode-nlp

5. **The Invisible Threat: How Zero-Width Unicode Characters Can Silently Backdoor Your AI-Generated Code**
   - Promptfoo, 2024
   - URL: https://www.promptfoo.dev/blog/invisible-unicode-threats/

6. **OCR Data Entry: Preprocessing Text for NLP Tasks in 2025**
   - Label Your Data
   - URL: https://labelyourdata.com/articles/ocr-data-entry

7. **Zero-width space - Wikipedia**
   - URL: https://en.wikipedia.org/wiki/Zero-width_space

---

**Temps de recherche :** 45 min
**Généré par :** AlexAlves87
**Date :** 2026-01-27
