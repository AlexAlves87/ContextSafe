# Checksum Validators - Standalone Test

**Datum:** 04.02.2026
**Autor:** AlexAlves87
**Komponente:** `scripts/preprocess/checksum_validators.py`
**Standard:** Offizielle spanische Algorithmen (BOE)

---

## 1. Management-Zusammenfassung

Implementierung und Standalone-Validierung von Checksum-Validatoren für spanische Identifikatoren, die in der NER-PII-Pipeline verwendet werden.

### Ergebnisse

| Metrik | Wert |
|--------|------|
| **Bestandene Tests** | 23/24 (95,8%) |
| **Implementierte Validatoren** | 5 (DNI, NIE, IBAN, NSS, CIF) |
| **Ausführungszeit** | 0,003s |

### Schlussfolgerung

> **Alle Validatoren funktionieren gemäß offiziellen Algorithmen korrekt.**
> Der einzige Fehler (NSS Edge Case) ist ein Fehler in der Testerwartung, nicht im Validator.

---

## 2. Methodik

### 2.1 Implementierte Algorithmen

| Identifikator | Algorithmus | Quelle |
|---------------|-------------|--------|
| **DNI** | `Buchstabe = TRWAGMYFPDXBNJZSQVHLCKE[Zahl % 23]` | BOE |
| **NIE** | X→0, Y→1, Z→2, dann DNI | BOE |
| **IBAN** | ISO 13616, mod 97 = 1 | ISO 13616 |
| **NSS** | `Kontrolle = (Provinz + Nummer) % 97` | SV |
| **CIF** | Summe gerade + ungerade Positionen mit Verdopplung, Kontrolle = (10 - Summe%10) % 10 | BOE |

### 2.2 Validator-Struktur

Jeder Validator gibt ein Tupel `(is_valid, confidence, reason)` zurück:

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `is_valid` | bool | True wenn Checksumme korrekt |
| `confidence` | float | 1,0 (gültig), 0,5 (Format ok, Checksumme schlecht), 0,0 (Format ungültig) |
| `reason` | str | Beschreibung des Ergebnisses |

### 2.3 Reproduzierbarkeit

```bash
# Umgebung
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Ausführung
python scripts/preprocess/checksum_validators.py

# Erwarteter Output: 23/24 passed (95,8%)
```

---

## 3. Ergebnisse

### 3.1 Zusammenfassung nach Validator

| Validator | Tests | Bestanden | Fehlgeschlagen |
|-----------|-------|-----------|----------------|
| DNI | 6 | 6 | 0 |
| NIE | 4 | 4 | 0 |
| DNI_NIE | 2 | 2 | 0 |
| IBAN | 4 | 4 | 0 |
| NSS | 2 | 1 | 1* |
| CIF | 4 | 4 | 0 |
| Edge cases | 2 | 2 | 0 |
| **Gesamt** | **24** | **23** | **1** |

*Der Fehler ist ein Fehler in der Testerwartung, nicht im Validator.

### 3.2 Detaillierte Tests

#### DNI (6/6 ✅)

| Test | Input | Erwartet | Ergebnis |
|------|-------|----------|----------|
| dni_valid_1 | `12345678Z` | ✅ gültig | ✅ |
| dni_valid_2 | `00000000T` | ✅ gültig | ✅ |
| dni_valid_spaces | `1234 5678 Z` | ✅ gültig | ✅ |
| dni_invalid_letter | `12345678A` | ❌ ungültig | ❌ (erwartet Z) |
| dni_invalid_letter_2 | `00000000A` | ❌ ungültig | ❌ (erwartet T) |
| dni_invalid_format | `1234567Z` | ❌ ungültig | ❌ (7 Ziffern) |

#### NIE (4/4 ✅)

| Test | Input | Erwartet | Ergebnis |
|------|-------|----------|----------|
| nie_valid_x | `X0000000T` | ✅ gültig | ✅ |
| nie_valid_y | `Y0000000Z` | ✅ gültig | ✅ |
| nie_valid_z | `Z0000000M` | ✅ gültig | ✅ |
| nie_invalid_letter | `X0000000A` | ❌ ungültig | ❌ (erwartet T) |

#### IBAN (4/4 ✅)

| Test | Input | Erwartet | Ergebnis |
|------|-------|----------|----------|
| iban_valid_es | `ES9121000418450200051332` | ✅ gültig | ✅ |
| iban_valid_spaces | `ES91 2100 0418 4502 0005 1332` | ✅ gültig | ✅ |
| iban_invalid_check | `ES0021000418450200051332` | ❌ ungültig | ❌ (Prüfziffern 00) |
| iban_invalid_mod97 | `ES1234567890123456789012` | ❌ ungültig | ❌ (mod 97 ≠ 1) |

#### NSS (1/2 - 1 Erwartungsfehler)

| Test | Input | Erwartet | Ergebnis | Anmerkung |
|------|-------|----------|----------|-----------|
| nss_valid | `281234567890` | ❌ ungültig | ❌ | Korrekt (zufällige Checksumme) |
| nss_format_ok | `280000000097` | ✅ gültig | ❌ | **Erwartungsfehler** |

**Fehleranalyse:**
- Input: `280000000097`
- Provinz: `28`, Nummer: `00000000`, Kontrolle: `97`
- Berechnung: `(28 * 10^8 + 0) % 97 = 2800000000 % 97 = 37`
- Vom Test erwartet: `97`, Tatsächlich: `37`
- **Der Validator ist korrekt.** Die Testerwartung war inkorrekt.

#### CIF (4/4 ✅)

| Test | Input | Erwartet | Ergebnis |
|------|-------|----------|----------|
| cif_valid_a | `A12345674` | ✅ gültig | ✅ |
| cif_valid_b | `B12345674` | ✅ gültig | ✅ |
| cif_invalid | `A12345670` | ❌ ungültig | ❌ (erwartet 4) |

### 3.3 Validierungs-Demo

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

## 4. Fehleranalyse

### 4.1 Einziger Fehler: NSS Edge Case

| Aspekt | Detail |
|--------|--------|
| Test | `nss_format_ok` |
| Input | `280000000097` |
| Problem | Testerwartung nahm an, `97` wäre gültig |
| Realität | `(28 + "00000000") % 97 = 37`, nicht `97` |
| Aktion | Erwartung im Testfall korrigieren |

### 4.2 Vorgeschlagene Korrektur

```python
# In TEST_CASES, ändern:
TestCase("nss_format_ok", "280000000097", "NSS", True, "..."),
# Zu:
TestCase("nss_format_ok", "280000000037", "NSS", True, "NSS with valid control"),
```

Oder besser, berechnen Sie eine echte gültige NSS:
- Provinz: `28` (Madrid)
- Nummer: `12345678`
- Kontrolle: `(2812345678) % 97 = 2812345678 % 97 = 8`
- Gültige NSS: `281234567808`

---

## 5. Schlussfolgerungen und Zukünftige Arbeit

### 5.1 Schlussfolgerungen

1. **Alle 5 Validatoren funktionieren korrekt** gemäß offiziellen Algorithmen
2. **Rückgabestruktur (is_valid, confidence, reason)** ermöglicht flexible Integration
3. **Zwischenliegendes Konfidenzniveau (0,5)** ermöglicht Unterscheidung:
   - Format korrekt aber Checksumme inkorrekt → möglicher Tippfehler/OCR
   - Format inkorrekt → wahrscheinlich nicht dieser ID-Typ

### 5.2 Verwendung in NER-Pipeline

| Szenario | Aktion |
|----------|--------|
| Entität erkannt + gültige Checksumme | Erkennung beibehalten (Konfidenz-Boost) |
| Entität erkannt + ungültige Checksumme | Konfidenz reduzieren oder als "possible_typo" markieren |
| Entität erkannt + ungültiges Format | Mögliches Falsch-Positiv → überprüfen |

### 5.3 Nächster Schritt

**Integration in NER-Pipeline für Post-Validierung:**
- Anwendung von Validatoren auf Entitäten, die als DNI_NIE, IBAN, NSS, CIF erkannt wurden
- Anpassung der Konfidenz basierend auf Validierungsergebnis
- Reduzierung von SPU (Falsch-Positive) durch Eliminierung von Erkennungen mit ungültigen Checksummen

### 5.4 Geschätzte Auswirkung

| Metrik | Baseline | Geschätzt | Verbesserung |
|--------|----------|-----------|--------------|
| SPU | 8 | 5-6 | -2 bis -3 |
| F1 (strikt) | 0,492 | 0,50-0,52 | +0,01-0,03 |

---

## 6. Referenzen

1. **DNI/NIE Algorithmus:** BOE - Königliches Dekret 1553/2005
2. **IBAN Validierung:** ISO 13616-1:2020
3. **NSS Format:** Allgemeine Staatskasse der Sozialversicherung
4. **CIF Algorithmus:** BOE - Königliches Dekret 1065/2007
5. **Grundlagenforschung:** `docs/reports/2026-01-28_investigacion_hybrid_ner.md`

---

**Ausführungszeit:** 0,003s
**Generiert von:** AlexAlves87
**Datum:** 04.02.2026
