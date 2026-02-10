# Forschung: Textnormalisierung für NER in juristischen Dokumenten

**Datum:** 2026-01-27
**Autor:** AlexAlves87
**Typ:** Wissenschaftliche Literaturrecherche
**Status:** Abgeschlossen

---

## 1. Zusammenfassung

Diese Forschung analysiert Best Practices für die Textnormalisierung in NER-Pipelines, mit Schwerpunkt auf:
1. Unicode-Normalisierung (Fullwidth, Zero-Width, Homoglyphen)
2. Korrektur von OCR-Artefakten
3. Integration mit Transformer-Modellen

### Wichtigste Erkenntnisse

| Erkenntnis | Quelle | Auswirkung |
|------------|--------|------------|
| NFKC normalisiert Fullwidth → ASCII automatisch | UAX #15 Unicode Standard | Hoch |
| Zero-Width-Zeichen (U+200B-U+200F) müssen explizit entfernt werden | Unicode Consortium | Hoch |
| OCR-sensitive Neuronen existieren in Transformern und können moduliert werden | arXiv:2409.16934 (ICADL 2024) | Mittel |
| Vorverarbeitung muss mit Modell-Vortraining übereinstimmen | Best Practices 2024 | Kritisch |
| NFKC zerstört Informationen in komplexen Skripten (Arabisch, Hebräisch) | UAX #15 | Niedrig (gilt nicht für Spanisch) |

---

## 2. Methodik

### 2.1 Konsultierte Quellen

| Quelle | Typ | Jahr | Relevanz |
|--------|-----|------|----------|
| UAX #15 Unicode Standard | Spezifikation | 2024 | Unicode Standard |
| arXiv:2409.16934 | Paper (ICADL 2024) | 2024 | OCR-sensitive Neuronen |
| TACL Neural OCR Post-Hoc | Wissenschaftliches Paper | 2021 | Neurale OCR-Korrektur |
| Brenndoerfer NLP Guide | Technisches Tutorial | 2024 | Industrielle Best Practices |
| Promptfoo Security | Technischer Artikel | 2024 | Unicode-Umgehung in KI |

### 2.2 Suchkriterien

- "text normalization NER preprocessing Unicode OCR"
- "Unicode normalization NLP NER fullwidth characters zero-width space"
- "OCR post-correction NER robustness neural network ACL EMNLP"

---

## 3. Ergebnisse

### 3.1 Unicode-Normalisierungsformen

Der Unicode-Standard (UAX #15) definiert 4 Normalisierungsformen:

| Form | Name | Beschreibung | Verwendung in NER |
|------|------|--------------|-------------------|
| **NFC** | Canonical Composition | Setzt Zeichen zusammen (é = e + ´) | Standard |
| **NFD** | Canonical Decomposition | Zerlegt Zeichen | Suche |
| **NFKC** | Compatibility Composition | NFC + Kompatibilität | **Empfohlen für NER** |
| **NFKD** | Compatibility Decomposition | NFD + Kompatibilität | Analyse |

**Quelle:** [UAX #15: Unicode Normalization Forms](https://unicode.org/reports/tr15/)

#### 3.1.1 NFKC für Entitätsnormalisierung

NFKC ist die empfohlene Form für NER, weil:

```
Fullwidth:  １２３４５６７８ → 12345678
Superscript: ² → 2
Fractions:   ½ → 1/2
Roman:       Ⅳ → IV
Ligatures:   ﬁ → fi
```

**Warnung:** NFKC zerstört Informationen in komplexen Skripten (Arabisch, Hebräisch, Devanagari), wo Steuerzeichen semantisch relevant sind. Für juristisches Spanisch ist dies kein Problem.

### 3.2 Problematische unsichtbare Zeichen

**Quelle:** [The Invisible Threat: Zero-Width Unicode Characters](https://www.promptfoo.dev/blog/invisible-unicode-threats/)

| Codepoint | Name | Problem | Aktion |
|-----------|------|---------|--------|
| U+200B | Zero Width Space | Bricht Tokenisierung | Entfernen |
| U+200C | Zero Width Non-Joiner | Trennt verbundene Zeichen | Entfernen |
| U+200D | Zero Width Joiner | Verbindet getrennte Zeichen | Entfernen |
| U+200E | Left-to-Right Mark | Verwirrt Textrichtung | Entfernen |
| U+200F | Right-to-Left Mark | Verwirrt Textrichtung | Entfernen |
| U+FEFF | BOM / Zero Width No-Break | Encoding-Artefakt | Entfernen |
| U+00A0 | Non-Breaking Space | Nicht erkannt von isspace() | → normales Leerzeichen |
| U+00AD | Soft Hyphen | Unsichtbarer Bindestrich | Entfernen |

**Auswirkung auf NER:**
- DNI `123​456​78Z` (mit U+200B) passt nicht zu Regex `\d{8}[A-Z]`
- Tokenizer teilt Wort in mehrere Token auf
- Modell erkennt die Entität nicht

### 3.3 Homoglyphen und Umgehung

**Quelle:** [Invisible Unicode Tricks Bypass AI Detection](https://justdone.com/blog/ai/invisible-unicode-tricks)

| Lateinisch | Kyrillisch | Visuell | Code |
|------------|------------|---------|------|
| A | А | Identisch | U+0041 vs U+0410 |
| B | В | Identisch | U+0042 vs U+0412 |
| E | Е | Identisch | U+0045 vs U+0415 |
| O | О | Identisch | U+004F vs U+041E |
| X | Х | Identisch | U+0058 vs U+0425 |

**Auswirkung auf NER:**
- DNI `12345678Х` (Kyrillisch) passt nicht zu Regex mit `[A-Z]`
- Modell erkennt möglicherweise nicht als gültige DNI

**Lösung:** Normalisierung häufiger lateinischer Homoglyphen vor NER.

### 3.4 OCR-Sensitive Neuronen in Transformern

**Quelle:** [Investigating OCR-Sensitive Neurons](https://arxiv.org/abs/2409.16934) (ICADL 2024)

#### Ergebnisse des Papers

1. **Transformer haben OCR-sensitive Neuronen:**
   - Identifiziert durch Analyse von Aktivierungsmustern
   - Reagieren unterschiedlich auf sauberen vs. verfälschten Text

2. **Kritische Schichten identifiziert:**
   - Llama 2: Schichten 0-2, 11-13, 23-28
   - Mistral: Schichten 29-31

3. **Vorgeschlagene Lösung:**
   - Neutralisierung OCR-sensitiver Neuronen
   - Verbessert NER-Leistung bei historischen Dokumenten

#### Anwendung auf ContextSafe

Für unser feinabgestimmtes RoBERTa-Modell:
- Textnormalisierung VOR Inferenz ist praktischer
- Neutralisierung von Neuronen erfordert Änderung der Modellarchitektur
- **Empfehlung:** Vorverarbeitung, nicht Modellmodifikation

### 3.5 Häufige OCR-Fehler und Normalisierung

**Quelle:** [OCR Data Entry: Preprocessing Text for NLP](https://labelyourdata.com/articles/ocr-data-entry)

| OCR-Fehler | Muster | Normalisierung |
|------------|--------|----------------|
| l ↔ I ↔ 1 | `DNl`, `DN1` | → `DNI` |
| O ↔ 0 | `2l0O` | Kontextabhängig (Zahlen) |
| rn ↔ m | `nom` → `nom` | Wörterbuch |
| S ↔ 5 | `E5123` | Kontextabhängig |
| B ↔ 8 | `B-123` vs `8-123` | Kontextabhängig |

**Empfohlene Strategie:**
1. **Einfache Vorverarbeitung:** l/I/1 → normalisieren basierend auf Kontext
2. **Nachvalidierung:** Checksummen (DNI, IBAN) weisen ungültige zurück
3. **Nicht versuchen, alles zu korrigieren:** Besser zurückweisen als erfinden

### 3.6 Nichtübereinstimmung Vorverarbeitung-Vortraining

**Quelle:** [Text Preprocessing Guide](https://mbrenndoerfer.com/writing/text-preprocessing-nlp-tokenization-normalization)

> "If you train a model with aggressively preprocessed text but deploy it on minimally preprocessed input, performance will crater."

**Kritisch für unser Modell:**
- RoBERTa-BNE wurde mit case-sensitivem Text vortrainiert
- KEIN lowercase anwenden
- JA Unicode-Normalisierung (NFKC) anwenden
- JA Zero-Width-Zeichen entfernen

---

## 4. Vorgeschlagene Normalisierungs-Pipeline

### 4.1 Reihenfolge der Operationen

```
OCR/Raw Text
    ↓
[1] BOM entfernen (U+FEFF)
    ↓
[2] Zero-Width entfernen (U+200B-U+200F, U+2060-U+206F)
    ↓
[3] NFKC-Normalisierung (Fullwidth → ASCII)
    ↓
[4] Leerzeichen normalisieren (U+00A0 → Leerzeichen, mehrere komprimieren)
    ↓
[5] Homoglyphen-Mapping (häufiges Kyrillisch → Lateinisch)
    ↓
[6] Kontextabhängige OCR (DNl → DNI nur wenn Kontext anzeigt)
    ↓
Normalisierter Text → NER
```

### 4.2 Python-Implementierung

```python
import unicodedata
import re

# Zu entfernende Zeichen
ZERO_WIDTH = re.compile(r'[\u200b-\u200f\u2060-\u206f\ufeff]')

# Kyrillisch → Lateinische Homoglyphen
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
    Normalize text for NER processing.

    Applies: NFKC, zero-width removal, homoglyph mapping, space normalization.
    Does NOT apply: lowercase (RoBERTa is case-sensitive).
    """
    # 1. Remove BOM and zero-width
    text = ZERO_WIDTH.sub('', text)

    # 2. NFKC normalization (fullwidth → ASCII)
    text = unicodedata.normalize('NFKC', text)

    # 3. Homoglyph mapping
    for cyrillic, latin in HOMOGLYPHS.items():
        text = text.replace(cyrillic, latin)

    # 4. Normalize spaces (NBSP → space, collapse multiples)
    text = text.replace('\u00a0', ' ')
    text = re.sub(r' +', ' ', text)

    # 5. Remove soft hyphens
    text = text.replace('\u00ad', '')

    return text.strip()
```

### 4.3 Validierungstests

| Input | Erwarteter Output | Test |
|-------|-------------------|------|
| `１２３４５６７８Z` | `12345678Z` | Fullwidth |
| `123​456​78Z` | `12345678Z` | Zero-Width |
| `12345678Х` | `12345678X` | Kyrillisch X |
| `D N I` | `D N I` | Leerzeichen (ohne Wörter zu komprimieren) |
| `María` | `María` | Akzente erhalten |

---

## 5. Lückenanalyse

### 5.1 Vergleich: Aktuelle Praxis vs Best Practices

| Aspekt | Best Practice | Aktuelle Implementierung | Lücke |
|--------|---------------|--------------------------|-------|
| NFKC-Normalisierung | Vor NER anwenden | Nicht implementiert | **KRITISCH** |
| Zero-Width-Entfernung | U+200B-F entfernen | Nicht implementiert | **KRITISCH** |
| Homoglyphen-Mapping | Kyrillisch → Lateinisch | Nicht implementiert | HOCH |
| Leerzeichen-Normalisierung | NBSP → Leerzeichen | Nicht implementiert | MITTEL |
| Kontextabhängige OCR | DNl → DNI | Nicht implementiert | MITTEL |
| Groß-/Kleinschreibung | KEIN lowercase | Korrekt | ✓ OK |

### 5.2 Geschätzte Auswirkung

| Korrektur | Aufwand | Auswirkung auf Tests |
|-----------|---------|----------------------|
| NFKC + Zero-Width | Niedrig (10 Zeilen) | `fullwidth_numbers`: PASS |
| Homoglyphen-Mapping | Niedrig (Tabelle) | `cyrillic_o`: PASS (passiert bereits, aber robuster) |
| Leerzeichen-Normalisierung | Niedrig | Reduziert FPs in Tokenisierung |
| **Gesamt** | **~50 Zeilen Python** | **+5-10% Pass-Rate Adversarial** |

---

## 6. Schlussfolgerungen

### 6.1 Wichtigste Erkenntnisse

1. **NFKC ist ausreichend**, um Fullwidth → ASCII ohne zusätzlichen Code zu normalisieren
2. **Zero-Width-Zeichen** müssen explizit entfernt werden (einfaches Regex)
3. **Homoglyphen** erfordern Mapping-Tabelle (Kyrillisch → Lateinisch)
4. **KEIN lowercase anwenden** - RoBERTa ist case-sensitive
5. **Kontextabhängige OCR** ist komplex - besser danach mit Checksummen validieren

### 6.2 Empfehlung für ContextSafe

**Implementierung von `scripts/preprocess/text_normalizer.py`** mit:
1. `normalize_text()` Funktion wie oben beschrieben
2. In Inferenz-Pipeline VOR Tokenizer integrieren
3. Auch während der Generierung des Trainingsdatensatzes anwenden

**Priorität:** HOCH - Wird `fullwidth_numbers` Tests lösen und die allgemeine Robustheit verbessern.

---

## 7. Referenzen

### Akademische Arbeiten

1. **Investigating OCR-Sensitive Neurons to Improve Entity Recognition in Historical Documents**
   - arXiv:2409.16934, ICADL 2024
   - URL: https://arxiv.org/abs/2409.16934

2. **Neural OCR Post-Hoc Correction of Historical Corpora**
   - TACL, MIT Press
   - URL: https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00379

### Standards und Spezifikationen

3. **UAX #15: Unicode Normalization Forms**
   - Unicode Consortium
   - URL: https://unicode.org/reports/tr15/

### Technische Ressourcen

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

**Recherchezeit:** 45 Min.
**Generiert von:** AlexAlves87
**Datum:** 2026-01-27
