# Element 1: Text Normalizer - Isolierter Test

**Datum:** 03.02.2026
**Status:** ✅ ABGESCHLOSSEN
**Ausführungszeit:** 0,002s

---

## 1. Zusammenfassung

| Metrik | Wert |
|--------|------|
| Ausgeführte Tests | 15 |
| Bestandene Tests | 15 |
| Pass Rate | 100% |
| Zeit | 0,002s |

## 2. Komponente

**Datei:** `scripts/preprocess/text_normalizer.py`

**Hauptklasse:** `TextNormalizer`

**Funktionalität:**
- NFKC-Normalisierung (fullwidth → ASCII)
- Entfernung von Zero-Width-Zeichen (U+200B-U+200F, U+2060-U+206F, U+FEFF)
- Mapping Kyrillisch → Lateinische Homoglyphen (17 Zeichen)
- NBSP → Leerzeichen + Kollaps mehrerer Leerzeichen
- Entfernung weicher Trennzeichen (Soft hyphens)

**Bewahrt (kritisch für NER):**
- Groß-/Kleinschreibung (RoBERTa ist case-sensitive)
- Spanische Akzente (María, García, etc.)
- Legitime Interpunktion

## 3. Validierte Tests

| Test | Kategorie | Beschreibung |
|------|-----------|--------------|
| fullwidth_dni | Unicode | `１２３４５６７８Z` → `12345678Z` |
| fullwidth_mixed | Unicode | Fullwidth Buchstaben und Zahlen |
| zero_width_in_dni | Evasion | Zero-Width innerhalb DNI |
| zero_width_in_name | Evasion | Zero-Width in Namen |
| cyrillic_o_in_dni | Homoglyph | Kyrillisch О → Lateinisch O |
| cyrillic_mixed | Homoglyph | Gemischter kyrillischer/lateinischer Text |
| nbsp_in_address | Spaces | NBSP → normales Leerzeichen |
| multiple_spaces | Spaces | Kollaps mehrerer Leerzeichen |
| soft_hyphen_in_word | OCR | Weiche Trennzeichen entfernt |
| combined_evasion | Combined | Mehrere kombinierte Techniken |
| preserve_accents | Preserve | Spanische Akzente intakt |
| preserve_case | Preserve | Case nicht modifiziert |
| preserve_punctuation | Preserve | Legale Interpunktion bewahrt |
| empty_string | Edge | Leerer String |
| only_spaces | Edge | Nur Leerzeichen |

## 4. Diagnose-Beispiel

**Input:** `DNI: １２​３４​５６​７８Х del Sr. María`

**Output:** `DNI: 12345678X del Sr. María`

**Angewandte Änderungen:**
1. Removed 3 zero-width characters
2. Applied NFKC normalization
3. Replaced 1 Cyrillic homoglyphs

## 5. Nächster Schritt

Integrieren von `TextNormalizer` in die NER-Pipeline (`CompositeNerAdapter`) und Evaluierung der Auswirkung auf adversariale Tests.

---

**Generiert von:** AlexAlves87
