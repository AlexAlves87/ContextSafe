# Regex-Muster für spanische Identifikatoren - Standalone Test

**Datum:** 05.02.2026
**Autor:** AlexAlves87
**Komponente:** `scripts/preprocess/spanish_id_patterns.py`
**Standard:** CHPDA (2025) - Hybrider Regex+NER Ansatz

---

## 1. Management-Zusammenfassung

Implementierung von Regex-Mustern zur Erkennung spanischer Identifikatoren mit varianten Formaten (Leerzeichen, Bindestriche, Punkte), die Transformer-NER-Modelle typischerweise nicht erkennen.

### Ergebnisse

| Metrik | Wert |
|--------|------|
| **Bestandene Tests** | 22/22 (100%) |
| **Entitätstypen** | 5 (DNI_NIE, IBAN, NSS, CIF, PHONE) |
| **Gesamte Muster** | 25 |
| **Ausführungszeit** | 0,003s |

### Schlussfolgerung

> **Alle Muster funktionieren korrekt für Formate mit Leerzeichen und Trennzeichen.**
> Dies ergänzt den Transformer-NER, der in Fällen wie "12 345 678 Z" oder "ES91 2100 0418..." versagt.

---

## 2. Methodik

### 2.1 Basisforschung

| Paper | Ansatz | Anwendung |
|-------|--------|-----------|
| **CHPDA (arXiv 2025)** | Hybrider Regex + AI NER | Reduziert False Positives |
| **Hybrid ReGex (JCO 2025)** | Leichte Regex + ML Pipeline | Medizinische Datenextraktion |
| **Legal NLP Survey (2024)** | Spezialisierter Legal NER | Regulatorische Muster |

### 2.2 Implementierte Muster

| Typ | Muster | Beispiele |
|-----|--------|-----------|
| **DNI** | 6 | `12345678Z`, `12 345 678 Z`, `12.345.678-Z` |
| **NIE** | 3 | `X1234567Z`, `X 1234567 Z`, `X-1234567-Z` |
| **IBAN** | 3 | `ES9121...`, `ES91 2100 0418...` |
| **NSS** | 3 | `281234567890`, `28/12345678/90` |
| **CIF** | 3 | `A12345674`, `A-1234567-4` |
| **PHONE** | 7 | `612345678`, `612 345 678`, `+34 612...` |

### 2.3 Reproduzierbarkeit

```bash
# Umgebung
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Ausführung
python scripts/preprocess/spanish_id_patterns.py

# Erwarteter Output: 22/22 passed (100.0%)
```

---

## 3. Ergebnisse

### 3.1 Tests nach Typ

| Typ | Tests | Bestanden | Schlüsselbeispiele |
|-----|-------|-----------|--------------------|
| DNI | 6 | 6 | Standard, Leerzeichen 2-3-3, Punkte |
| NIE | 3 | 3 | Standard, Leerzeichen, Bindestriche |
| IBAN | 2 | 2 | Standard, Leerzeichen Gruppen 4 |
| NSS | 2 | 2 | Schrägstriche, Leerzeichen |
| CIF | 2 | 2 | Standard, Bindestriche |
| PHONE | 4 | 4 | Mobil, Festnetz, International |
| Negativ | 2 | 2 | Weist ungültige Formate zurück |
| Multi | 1 | 1 | Mehrere Entitäten im Text |

### 3.2 Erkennungs-Demo

| Input | Erkennung | Normalisiert |
|-------|-----------|--------------|
| `DNI 12 345 678 Z` | ✅ DNI_NIE | `12345678Z` |
| `IBAN ES91 2100 0418 4502 0005 1332` | ✅ IBAN | `ES9121000418450200051332` |
| `NIE X-1234567-Z` | ✅ DNI_NIE | `X1234567Z` |
| `Tel: 612 345 678` | ✅ PHONE | `612345678` |
| `CIF A-1234567-4` | ✅ CIF | `A12345674` |

### 3.3 Match-Struktur

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

## 4. Musteranalyse

### 4.1 Konfidenzniveaus

| Niveau | Konfidenz | Kriterium |
|--------|-----------|-----------|
| Hoch | 0,95 | Standardformat ohne Ambiguität |
| Mittel | 0,90 | Format mit gültigen Trennzeichen |
| Niedrig | 0,70-0,85 | Formate, die mehrdeutig sein können |

### 4.2 DNI-Muster mit Leerzeichen (Originalproblem)

Der Adversarial-Test `dni_with_spaces` schlug fehl, weil NER "12 345 678 Z" nicht erkannte.

**Implementierte Lösung:**
```python
# Muster für Leerzeichen 2-3-3
r'\b(\d{2})\s+(\d{3})\s+(\d{3})\s*([A-Z])\b'
```

Dieses Muster erkennt:
- `12 345 678 Z` ✅
- `12 345 678Z` ✅ (kein Leerzeichen vor Buchstabe)

### 4.3 Normalisierung für Checksum

`normalize_match()` Funktion entfernt Trennzeichen für Validierung:

```python
"12 345 678 Z" → "12345678Z"
"ES91 2100 0418..." → "ES9121000418..."
"X-1234567-Z" → "X1234567Z"
```

---

## 5. Schlussfolgerungen und Zukünftige Arbeit

### 5.1 Schlussfolgerungen

1. **25 Muster decken variante Formate** spanischer Identifikatoren ab
2. **Normalisierung ermöglicht Integration** mit Checksum-Validatoren
3. **Variable Konfidenz** unterscheidet mehr/weniger zuverlässige Formate
4. **Überlappungserkennung** vermeidet Duplikate

### 5.2 Pipeline-Integration

```
Eingabetext
       ↓
┌──────────────────────┐
│  1. TextNormalizer   │  Unicode/OCR Bereinigung
└──────────────────────┘
       ↓
┌──────────────────────┐
│  2. NER Transformer  │  RoBERTalex Vorhersagen
└──────────────────────┘
       ↓
┌──────────────────────┐
│  3. Regex Patterns   │  ← NEU: erkennt Leerzeichen
└──────────────────────┘
       ↓
┌──────────────────────┐
│  4. Merge & Dedup    │  Kombiniert NER + Regex
└──────────────────────┘
       ↓
┌──────────────────────┐
│  5. Checksum Valid.  │  Passt Vertrauen an
└──────────────────────┘
       ↓
Finale Entitäten
```

### 5.3 Geschätzte Auswirkung

| Adversarial Test | Vorher | Nachher | Verbesserung |
|------------------|--------|---------|--------------|
| `dni_with_spaces` | MIS:1 | COR:1 | +1 COR |
| `iban_with_spaces` | PAR:1 | COR:1 | +1 COR |
| `phone_international` | MIS:1 | COR:1 | +1 COR (potenziell) |

**Gesamtschätzung:** +2-3 COR, Umwandlung von MIS und PAR zu COR.

---

## 6. Referenzen

1. **CHPDA (2025):** [arXiv](https://arxiv.org/html/2502.07815v1) - Hybrider Regex+NER Ansatz
2. **Hybrid ReGex (2025):** [JCO](https://ascopubs.org/doi/10.1200/CCI-25-00130) - Medizinische Datenextraktion
3. **Legal NLP Survey (2024):** [arXiv](https://arxiv.org/html/2410.21306v3) - NER für Rechtsdomäne

---

**Ausführungszeit:** 0,003s
**Generiert von:** AlexAlves87
**Datum:** 05.02.2026
