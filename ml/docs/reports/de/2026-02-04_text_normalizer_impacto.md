# Auswirkungsanalyse: Text Normalizer

**Datum:** 04.02.2026
**Autor:** AlexAlves87
**Komponente:** `TextNormalizer` (Unicode/OCR Normalisierung)
**Standard:** SemEval 2013 Task 9 (Strikter Modus)

---

## 1. Management-Zusammenfassung

Bewertung der Auswirkung der Integration des `TextNormalizer` in die NER-Pipeline zur Verbesserung der Robustheit gegenüber Unicode-Zeichen und OCR-Artefakten.

### Ergebnisse

| Metrik | Baseline | +Normalizer | Delta | Änderung |
|--------|----------|-------------|-------|----------|
| **Pass Rate (strikt)** | 28,6% | **34,3%** | **+5,7pp** | +20% relativ |
| **F1 (strikt)** | 0,464 | **0,492** | **+0,028** | +6% relativ |
| F1 (partiell) | 0,632 | 0,659 | +0,027 | +4,3% relativ |
| COR | 29 | 31 | +2 | Mehr exakte Erkennungen |
| MIS | 17 | 15 | -2 | Weniger verpasste Entitäten |
| SPU | 8 | 7 | -1 | Weniger Falsch-Positive |

### Schlussfolgerung

> **Der TextNormalizer verbessert die Robustheit des NER-Modells signifikant.**
> Pass Rate +5,7pp, F1 +0,028. Zwei Unicode-Evasion-Tests bestehen jetzt.

---

## 2. Methodik

### 2.1 Experimentelles Design

| Aspekt | Spezifikation |
|--------|---------------|
| Unabhängige Variable | TextNormalizer (AN/AUS) |
| Abhängige Variable | SemEval 2013 Metriken |
| Modell | legal_ner_v2 (RoBERTalex) |
| Datensatz | 35 adversariale Tests |
| Standard | SemEval 2013 Task 9 (strikt) |

### 2.2 Evaluierte Komponente

**Datei:** `scripts/inference/ner_predictor.py` → Funktion `normalize_text_for_ner()`

**Angewandte Operationen:**
1. Entfernung von Zero-Width-Zeichen (U+200B-U+200F, U+2060-U+206F, U+FEFF)
2. NFKC-Normalisierung (Fullwidth → ASCII)
3. Homoglyphen-Mapping (Kyrillisch → Lateinisch)
4. Leerzeichen-Normalisierung (NBSP → Leerzeichen, Kollaps mehrerer)
5. Entfernung weicher Trennzeichen (Soft Hyphens)

### 2.3 Reproduzierbarkeit

```bash
# Umgebung
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Ausführung
python scripts/evaluate/test_ner_predictor_adversarial_v2.py

# Output: docs/reports/YYYY-MM-DD_adversarial_v2_academic_rN.md
```

---

## 3. Ergebnisse

### 3.1 Detaillierter Vergleich nach SemEval-Metrik

| Metrik | Baseline | +Normalizer | Delta |
|--------|----------|-------------|-------|
| COR (Korrekt) | 29 | 31 | **+2** |
| INC (Inkorrekt) | 0 | 0 | 0 |
| PAR (Partiell) | 21 | 21 | 0 |
| MIS (Verpasst) | 17 | 15 | **-2** |
| SPU (Espurios) | 8 | 7 | **-1** |
| POS (Möglich) | 67 | 67 | 0 |
| ACT (Aktuell) | 58 | 59 | +1 |

### 3.2 Verbesserte Tests

| Test | Baseline | +Normalizer | Verbesserung |
|------|----------|-------------|--------------|
| `cyrillic_o` | ❌ COR:1 PAR:1 | ✅ COR:2 | **Homoglyphen-Mapping funktioniert** |
| `zero_width_space` | ❌ COR:2 SPU:1 | ✅ COR:2 SPU:0 | **Zero-Width-Entfernung funktioniert** |
| `fullwidth_numbers` | ❌ MIS:2 | ❌ COR:1 MIS:1 | Partielle Verbesserung (+1 COR) |

### 3.3 Tests ohne signifikante Änderung

| Test | Status | Grund |
|------|--------|-------|
| `ocr_extra_spaces` | ❌ MIS:2 | Erfordert Leerzeichen-Normalisierung innerhalb von Entitäten |
| `ocr_zero_o_confusion` | ❌ MIS:1 | Erfordert kontextuelle OCR O↔0 Korrektur |
| `dni_with_spaces` | ❌ MIS:1 | Interne Leerzeichen in DNI werden nicht kollabiert |

### 3.4 Ergebnisse nach Kategorie

| Kategorie | Baseline Strikt | +Normalizer Strikt | Delta |
|-----------|-----------------|--------------------|-------|
| adversarial | 75% | 75% | 0 |
| edge_case | 22% | 22% | 0 |
| ocr_corruption | 40% | 40% | 0 |
| real_world | 10% | 10% | 0 |
| **unicode_evasion** | 0% | **67%** | **+67pp** |

**Wichtige Erkenntnis:** Die Auswirkung konzentriert sich auf `unicode_evasion` (+67pp), was das Hauptziel war.

---

## 4. Fehleranalyse

### 4.1 Test `fullwidth_numbers` (Partielle Verbesserung)

**Input:** `"DNI １２３４５６７８Z de María."`

**Erwartet:**
- `"１２３４５６７８Z"` → DNI_NIE
- `"María"` → PERSON

**Erkannt (mit Normalizer):**
- `"12345678Z"` → DNI_NIE ✅ (normalisierter Match)
- `"María"` → MIS ❌

**Analyse:** Der DNI wird nach NFKC korrekt erkannt. Der Name "María" wird verpasst, weil das Modell ihn nicht erkennt (Modellproblem, nicht Normalizer).

### 4.2 Weiterhin fehlschlagende Tests

| Test | Problem | Erforderliche Lösung |
|------|---------|----------------------|
| `dni_with_spaces` | "12 345 678 Z" nicht erkannt | Regex für DNI mit Leerzeichen |
| `date_roman_numerals` | Daten mit römischen Zahlen | Data Augmentation |
| `ocr_zero_o_confusion` | IBAN mit gemischten O/0 | OCR Post-Correction |

---

## 5. Schlussfolgerungen und Zukünftige Arbeit

### 5.1 Schlussfolgerungen

1. **TextNormalizer erfüllt sein Ziel** für Unicode-Evasion:
   - `cyrillic_o`: ❌ → ✅
   - `zero_width_space`: ❌ → ✅
   - `unicode_evasion` Kategorie: 0% → 67%

2. **Moderate aber positive globale Auswirkung:**
   - F1 strikt: +0.028 (+6%)
   - Pass Rate: +5,7pp (+20% relativ)

3. **Löst keine OCR-Probleme** (erwartet):
   - `ocr_extra_spaces`, `ocr_zero_o_confusion` erfordern zusätzliche Techniken

### 5.2 Zukünftige Arbeit

| Priorität | Verbesserung | Geschätzte Auswirkung |
|-----------|--------------|-----------------------|
| HOCH | Regex für DNI/IBAN mit Leerzeichen | +2-3 COR |
| HOCH | Checksum-Validierung (SPU reduzieren) | -2-3 SPU |
| MITTEL | Data Augmentation für textuelle Daten | +3-4 COR |
| NIEDRIG | OCR Post-Correction (O↔0) | +1-2 COR |

### 5.3 Aktualisiertes Ziel

| Metrik | Vorher | Jetzt | Ziel Level 4 | Lücke |
|--------|--------|-------|--------------|-------|
| F1 (strikt) | 0,464 | **0,492** | ≥0,70 | -0,208 |
| Pass Rate | 28,6% | **34,3%** | ≥70% | -35,7pp |

---

## 6. Referenzen

1. **Grundlagenforschung:** `docs/reports/2026-01-27_investigacion_text_normalization.md`
2. **Standalone-Komponente:** `scripts/preprocess/text_normalizer.py`
3. **Produktionsintegration:** `src/contextsafe/infrastructure/nlp/text_normalizer.py`
4. **UAX #15 Unicode Normalization Forms:** https://unicode.org/reports/tr15/

---

**Evaluierungszeit:** 1,3s
**Generiert von:** AlexAlves87
**Datum:** 04.02.2026
