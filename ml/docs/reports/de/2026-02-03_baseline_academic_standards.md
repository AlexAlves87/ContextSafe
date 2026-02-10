# Akademische Baseline: Evaluierung mit SemEval 2013 Standards

**Datum:** 03.02.2026
**Autor:** AlexAlves87
**Modell:** legal_ner_v2 (RoBERTalex fine-tuned)
**Standard:** SemEval 2013 Task 9

---

## 1. Management-Zusammenfassung

Diese Evaluierung etabliert die **reale Baseline** des Modells unter Verwendung akademischer Standards (SemEval 2013 strikter Modus) und ersetzt frühere Ergebnisse, die Lenient Matching verwendeten.

### Vergleich v1 vs v2

| Metrik | v1 (lenient) | v2 (strikt) | Differenz |
|--------|--------------|-------------|-----------|
| **Pass Rate** | 54,3% | **28,6%** | **-25,7pp** |
| **F1-Score** | 0,784 | **0,464** | **-0,320** |
| F1 (partiell) | - | 0,632 | - |

### Hauptschlussfolgerung

> **Die früheren Ergebnisse (F1=0,784, 54,3%) waren AUFGEBLÄHT.**
> Die reale Baseline mit akademischen Standards ist **F1=0,464, 28,6% Pass Rate**.

---

## 2. Methodik

### 2.1 Experimentelles Design

| Aspekt | Spezifikation |
|--------|---------------|
| Evaluiertes Modell | `legal_ner_v2` (RoBERTalex fine-tuned) |
| Framework | PyTorch 2.0+, Transformers |
| Hardware | CUDA (GPU) |
| Evaluierungsstandard | SemEval 2013 Task 9 |
| Hauptmodus | Strikt (exakte Grenze + Typ) |

### 2.2 Evaluierungs-Dataset

| Kategorie | Tests | Zweck |
|-----------|-------|-------|
| edge_case | 9 | Grenzbedingungen (lange Namen, Variantenformate) |
| adversarial | 8 | Fälle zur Verwirrung (Negationen, Beispiele) |
| ocr_corruption | 5 | Simulation von OCR-Fehlern |
| unicode_evasion | 3 | Umgehungsversuche mit Unicode-Zeichen |
| real_world | 10 | Auszüge aus echten juristischen Dokumenten |
| **Gesamt** | **35** | - |

### 2.3 Verwendete Metriken

Gemäß SemEval 2013 Task 9:

| Metrik | Definition |
|--------|------------|
| COR | Korrekt: exakte Grenze UND Typ |
| INC | Inkorrekt: exakte Grenze, inkorrekter Typ |
| PAR | Partiell: überlappende Grenze, beliebiger Typ |
| MIS | Verpasst: Gold-Entität nicht erkannt (FN) |
| SPU | Espurios: Erkennung ohne Gold-Match (FP) |

**Formeln:**
- Precision (strikt) = COR / (COR + INC + PAR + SPU)
- Recall (strikt) = COR / (COR + INC + PAR + MIS)
- F1 (strikt) = 2 × P × R / (P + R)

### 2.4 Reproduzierbarkeit

```bash
# Umgebung
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Abhängigkeiten
pip install nervaluate  # Optional, Metriken manuell implementiert

# Ausführung
python scripts/evaluate/test_ner_predictor_adversarial_v2.py

# Output
# - Konsole: Ergebnisse pro Test mit COR/INC/PAR/MIS/SPU
# - Bericht: docs/reports/YYYY-MM-DD_adversarial_v2_academic_rN.md
```

### 2.5 Unterschied zur Evaluierung v1

| Aspekt | v1 (lenient) | v2 (strikt) |
|--------|--------------|-------------|
| Matching | Containment + 80% Zeichenüberlappung | Normalisierte exakte Grenze |
| Typ | Erforderlich | Erforderlich |
| Metriken | TP/FP/FN | COR/INC/PAR/MIS/SPU |
| Standard | Benutzerdefiniert | SemEval 2013 Task 9 |

---

## 3. Ergebnisse

### 3.1 SemEval 2013 Zählungen

| Metrik | Wert | Beschreibung |
|--------|------|--------------|
| **COR** | 29 | Korrekt (exakte Grenze + Typ) |
| **INC** | 0 | Grenze korrekt, Typ inkorrekt |
| **PAR** | 21 | Partielle Übereinstimmung (nur Überlappung) |
| **MIS** | 17 | Verpasst (FN) |
| **SPU** | 8 | Espurios (FP) |
| **POS** | 67 | Total Gold (COR+INC+PAR+MIS) |
| **ACT** | 58 | Total System (COR+INC+PAR+SPU) |

### 3.2 Interpretation

```
                    ┌─────────────────────────────────┐
                    │     GOLD: 67 Entitäten          │
                    │                                 │
  ┌─────────────────┼─────────────────┐               │
  │                 │    COR: 29      │               │
  │   SYSTEM: 58    │  (43% von Gold) │   MIS: 17     │
  │                 │                 │   (25%)       │
  │    SPU: 8       │    PAR: 21      │               │
  │    (14%)        │   (31% overlap) │               │
  └─────────────────┴─────────────────┴───────────────┘
```

**Analyse:**
- Nur **43%** der Gold-Entitäten werden mit exakter Grenze erkannt
- **31%** werden mit partieller Überlappung erkannt (v1 zählte sie als korrekt)
- **25%** werden komplett verpasst
- **14%** der Erkennungen sind falsch positiv

### 3.3 Angewendete Formeln

**Strikter Modus:**
```
Precision = COR / ACT = 29 / 58 = 0,500
Recall = COR / POS = 29 / 67 = 0,433
F1 = 2 * P * R / (P + R) = 0,464
```

**Partieller Modus:**
```
Precision = (COR + 0,5*PAR) / ACT = (29 + 10,5) / 58 = 0,681
Recall = (COR + 0,5*PAR) / POS = (29 + 10,5) / 67 = 0,590
F1 = 2 * P * R / (P + R) = 0,632
```

---

### 3.4 Ergebnisse nach Kategorie

| Kategorie | Strikt | Lenient | COR | PAR | MIS | SPU |
|-----------|--------|---------|-----|-----|-----|-----|
| adversarial | 75% | 75% | 5 | 1 | 0 | 3 |
| edge_case | 22% | 67% | 6 | 3 | 3 | 1 |
| ocr_corruption | 40% | 40% | 4 | 1 | 4 | 0 |
| real_world | 10% | 50% | 12 | 14 | 8 | 4 |
| unicode_evasion | 0% | 33% | 3 | 1 | 2 | 1 |

**Beobachtungen:**
- **real_world**: Größte Diskrepanz strikt vs lenient (10% vs 50%) - viele PAR
- **unicode_evasion**: 0% strikt - alle Erkennungen sind partiell oder inkorrekt
- **adversarial**: Gleich in beiden Modi - Nicht-Erkennungs-Tests

---

### 3.5 Ergebnisse nach Schwierigkeit

| Schwierigkeit | Strikt | Lenient |
|---------------|--------|---------|
| einfach | 50% | 75% |
| mittel | 42% | 75% |
| schwer | 16% | 42% |

**Beobachtung:** Der Unterschied strikt vs lenient nimmt mit der Schwierigkeit zu.

---

## 4. Fehleranalyse

### 4.1 Partielle Übereinstimmungen (PAR)

Die 21 partiellen Matches repräsentieren Erkennungen, bei denen die Grenze nicht exakt ist:

| Typ von PAR | Beispiele | Ursache |
|-------------|-----------|---------|
| Unvollständiger Name | "José María" vs "José María de la Santísima..." | RoBERTa schneidet lange Namen ab |
| IBAN mit Leerzeichen | "ES91 2100..." vs "ES912100..." | Leerzeichen-Normalisierung |
| Partielle Adresse | "Calle Mayor 15" vs "Calle Mayor 15, 3º B" | Grenze schließt Stockwerk/Tür aus |
| Person im Kontext | "John Smith" vs "Mr. John Smith" | Präfixe nicht enthalten |

**Implikation:** Das Modell erkennt die Entität, aber mit ungenauen Grenzen.

---

### 4.2 Fehlgeschlagene Tests (Strikt)

#### 4.2.1 Durch SPU (Falsch Positiv)

| Test | SPU | Espurios Entitäten |
|------|-----|--------------------|
| example_dni | 1 | "12345678X" (Beispielkontext) |
| fictional_person | 1 | "Don Quijote de la Mancha" |
| date_ordinal | 1 | "El" |
| zero_width_space | 1 | "de" |
| judicial_sentence_header | 2 | Gesetzesreferenzen |
| professional_ids | 1 | Berufsverband |
| ecli_citation | 1 | Gericht |

#### 4.2.2 Durch MIS (Verpasste Entitäten)

| Test | MIS | Verpasste Entitäten |
|------|-----|---------------------|
| dni_with_spaces | 1 | "12 345 678 Z" |
| phone_international | 1 | "0034612345678" |
| date_roman_numerals | 1 | "XV de marzo del año MMXXIV" |
| ocr_zero_o_confusion | 1 | IBAN mit O/0 |
| ocr_extra_spaces | 2 | DNI und Name mit Leerzeichen |
| fullwidth_numbers | 2 | Fullwidth DNI, Name |
| notarial_header | 1 | Textuelles Datum |

---

## 5. Schlussfolgerungen und Zukünftige Arbeit

### 5.1 Verbesserungsprioritäten

| Verbesserung | Auswirkung auf COR | Auswirkung auf PAR→COR |
|--------------|--------------------|------------------------|
| Tex-Normalisierung (Unicode) | +2-4 COR | +2-3 PAR→COR |
| Checksum-Validierung | Reduziert SPU | - |
| Grenzverfeinerung | - | +10-15 PAR→COR |
| Datums-Augmentierung | +3-5 COR | - |

### 5.2 Revidiertes Ziel

| Metrik | Aktuell | Ziel Level 4 |
|--------|---------|--------------|
| F1 (strikt) | 0,464 | **≥ 0,70** |
| Pass Rate (strikt) | 28,6% | **≥ 70%** |

**Lücke zu schließen:** +0,236 F1, +41,4pp pass rate

---

### 5.3 Nächste Schritte

1. **Re-evaluieren** mit integriertem TextNormalizer (bereits vorbereitet)
2. **Implementieren** von Grenzverfeinerung zur Reduzierung von PAR
3. **Hinzufügen** von Checksum-Validierung zur Reduzierung von SPU
4. **Augmentieren** von Daten für textuelle Daten zur Reduzierung von MIS

---

### 5.4 Gelernte Lektionen

1. **Lenient Matching bläht Ergebnisse signifikant auf** (F1 0,784 → 0,464)
2. **PAR ist ein größeres Problem als MIS** (21 vs 17) - ungenaue Grenzen
3. **Echte Tests (real_world) haben mehr PAR** - komplexe Dokumente
4. **Unicode Evasion besteht keine strikten Tests** - kritischer Bereich

### 5.5 Wert des Akademischen Standards

Evaluierung mit SemEval 2013 ermöglicht:
- Vergleich mit akademischer Literatur
- Granulare Diagnose (COR/INC/PAR/MIS/SPU)
- Präzise Identifizierung von Verbesserungsbereichen
- Ehrliche Messung des Fortschritts

---

## 6. Referenzen

1. **SemEval 2013 Task 9**: Segura-Bedmar et al. "Extraction of Drug-Drug Interactions from Biomedical Texts"
2. **nervaluate**: https://github.com/MantisAI/nervaluate
3. **David Batista Blog**: https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/

---

**Evaluierungszeit:** 1,3s
**Generiert von:** AlexAlves87
**Datum:** 03.02.2026
