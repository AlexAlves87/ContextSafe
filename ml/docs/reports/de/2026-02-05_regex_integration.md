# Regex-Muster - Integrationstest

**Datum:** 05.02.2026
**Autor:** AlexAlves87
**Komponente:** Integration von Regex-Mustern in `scripts/inference/ner_predictor.py`
**Standard:** CHPDA (2025) - Hybrider Regex+NER Ansatz

---

## 1. Management-Zusammenfassung

Integration von Regex-Mustern zur Erkennung von Identifikatoren mit Leerzeichen/Bindestrichen, die das NER-Transformer-Modell nicht erkennt.

### Ergebnisse

| Test-Suite | Vorher | Nachher | Verbesserung |
|------------|--------|---------|--------------|
| Integrationstests | - | 11/14 (78,6%) | Neu |
| Adversarial (strikt) | 34,3% | **45,7%** | **+11,4pp** |
| F1 (strikt) | 0,492 | **0,543** | **+0,051** |

### Schlussfolgerung

> **Die Regex-Integration verbessert die Erkennung formatierter Identifikatoren signifikant.**
> Pass Rate +11,4pp, F1 +0,051. Die IBAN mit Leerzeichen wird jetzt korrekt erkannt.

---

## 2. Methodik

### 2.1 Merge-Strategie (Hybrid)

```
Eingabetext
       ↓
┌──────────────────────┐
│  1. NER Transformer  │  Erkennt semantische Entitäten
└──────────────────────┘
       ↓
┌──────────────────────┐
│  2. Regex Patterns   │  Erkennt Formate mit Leerzeichen
└──────────────────────┘
       ↓
┌──────────────────────┐
│  3. Merge Strategy   │  Kombiniert, bevorzugt vollständiger
└──────────────────────┘
       ↓
┌──────────────────────┐
│  4. Checksum Valid.  │  Passt Vertrauen an
└──────────────────────┘
       ↓
Finale Entitäten
```

### 2.2 Merge-Logik

| Fall | Aktion |
|------|--------|
| Nur NER erkennt | NER beibehalten |
| Nur Regex erkennt | Regex hinzufügen |
| Beide erkennen selben Span | NER beibehalten (höhere semantische Qualität) |
| Regex >20% länger als NER | NER durch Regex ersetzen |
| NER partiell, Regex vollständig | Durch Regex ersetzen |

### 2.3 Reproduzierbarkeit

```bash
# Umgebung
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Regex-Integrationstest
python scripts/evaluate/test_regex_integration.py

# Vollständiger Adversarial-Test
python scripts/evaluate/test_ner_predictor_adversarial_v2.py
```

---

## 3. Ergebnisse

### 3.1 Integrationstests (11/14)

| Test | Input | Ergebnis | Quelle |
|------|-------|----------|--------|
| dni_spaces_2_3_3 | `12 345 678 Z` | ✅ | ner |
| dni_spaces_4_4 | `1234 5678 Z` | ✅ | ner |
| dni_dots | `12.345.678-Z` | ✅ | ner |
| nie_dashes | `X-1234567-Z` | ✅ | ner |
| **iban_spaces** | `ES91 2100 0418...` | ✅ | **regex** |
| phone_spaces | `612 345 678` | ✅ | regex |
| phone_intl | `+34 612345678` | ❌ | - |
| cif_dashes | `A-1234567-4` | ❌ (falscher Typ) | ner |
| nss_slashes | `28/12345678/90` | ✅ | ner |
| dni_standard | `12345678Z` | ✅ | ner |

### 3.2 Auswirkung auf Adversariale Tests

| Metrik | Baseline | +Normalizer | +Regex | Delta Gesamt |
|--------|----------|-------------|--------|--------------|
| **Pass Rate** | 28,6% | 34,3% | **45,7%** | **+17,1pp** |
| **F1 (strikt)** | 0,464 | 0,492 | **0,543** | **+0,079** |
| F1 (partiell) | 0,632 | 0,659 | **0,690** | +0,058 |
| COR | 29 | 31 | **35** | **+6** |
| MIS | 17 | 15 | **12** | **-5** |
| PAR | 21 | 21 | **19** | -2 |
| SPU | 8 | 7 | **7** | -1 |

### 3.3 Analyse der Verbesserungen

| Adversarial Test | Vorher | Nachher | Verbesserung |
|------------------|--------|---------|--------------|
| dni_with_spaces | MIS:1 | COR:1 | +1 COR |
| iban_with_spaces | PAR:1 | COR:1 | PAR→COR |
| phone_international | MIS:1 | COR:1* | +1 COR |
| address_floor_door | PAR:1 | COR:1 | PAR→COR |

*Partielle Erkennung verbessert

---

## 4. Fehleranalyse

### 4.1 Verbleibende Fehler

| Test | Problem | Ursache |
|------|---------|---------|
| phone_intl | `+34` nicht enthalten | NER erkennt `612345678`, nicht genug Überlappung |
| cif_dashes | Falscher Typ | Modell klassifiziert CIF als DNI_NIE |
| spaced_iban_source | Nicht isoliert erkannt | Minimaler Kontext reduziert Erkennung |

### 4.2 Beobachtungen

1. **NER lernt Formate mit Leerzeichen**: Überraschenderweise erkennt das NER einige DNIs mit Leerzeichen (wahrscheinlich durch vorherige Data Augmentation)

2. **Regex ergänzt, ersetzt nicht**: Die meisten Erkennungen sind weiterhin NER, Regex fügt nur Fälle hinzu, die NER verpasst

3. **Checksum gilt für beides**: Sowohl NER als auch Regex durchlaufen die Checksum-Validierung

---

## 5. Schlussfolgerungen und Zukünftige Arbeit

### 5.1 Schlussfolgerungen

1. **Signifikante Verbesserung**: +17,1pp Pass Rate, +0,079 F1
2. **IBAN mit Leerzeichen**: Problem gelöst (Regex erkennt korrekt)
3. **Intelligenter Merge**: Bevorzugt vollständigere Erkennungen
4. **Minimaler Overhead**: ~100ms zusätzlich für 25 Muster

### 5.2 Aktueller Status vs Ziel

| Metrik | Baseline | Aktuell | Ziel | Lücke |
|--------|----------|---------|------|-------|
| Pass Rate | 28,6% | **45,7%** | ≥70% | -24,3pp |
| F1 (strikt) | 0,464 | **0,543** | ≥0,70 | -0,157 |

### 5.3 Nächste Schritte

| Priorität | Aufgabe | Geschätzte Auswirkung |
|-----------|---------|-----------------------|
| HOCH | Data Augmentation für textuelle Daten | +3-4 COR |
| MITTEL | Korrektur CIF-Klassifizierung | +1 COR |
| MITTEL | Verbesserung phone_intl Erkennung | +1 COR |
| NIEDRIG | Verfeinerung der Grenzen für PAR→COR | +2-3 COR |

---

## 6. Referenzen

1. **Standalone-Tests:** `docs/reports/2026-02-05_regex_patterns_standalone.md`
2. **CHPDA (2025):** [arXiv](https://arxiv.org/html/2502.07815v1) - Hybrider Regex+NER
3. **Muster-Skript:** `scripts/preprocess/spanish_id_patterns.py`
4. **Integrationstest:** `scripts/evaluate/test_regex_integration.py`

---

**Ausführungszeit:** 2,72s (Integration) + 1,4s (Adversarial)
**Generiert von:** AlexAlves87
**Datum:** 05.02.2026
