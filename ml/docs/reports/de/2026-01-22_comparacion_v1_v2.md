# Vergleich: Modell v1 vs v2 (Noise Training)

**Datum:** 2026-01-22
**Autor:** AlexAlves87
**Typ:** Vergleichende Analyse
**Status:** Abgeschlossen

---

## Zusammenfassung

| Metrik | v1 | v2 | Änderung |
|---------|-----|-----|--------|
| Adversarial Pass Rate | 45.7% (16/35) | 54.3% (19/35) | **+8.6 pp** |
| F1 Synthetischer Test | 99.87% | 100% | +0.13 pp |
| Datensatz | v2 (clean) | v3 (30% noise) | - |

**Schlussfolgerung:** Die Injektion von OCR-Rauschen während des Trainings verbesserte die Robustheit des Modells in adversarialen Tests um +8,6 Prozentpunkte.

---

## Methodik

### Unterschiede im Training

| Aspekt | v1 | v2 |
|---------|-----|-----|
| Datensatz | `ner_dataset_v2` | `ner_dataset_v3` |
| Rauschinjektion | 0% | 30% |
| Rauschart | - | l↔I, 0↔O, Akzente, Leerzeichen |
| Hyperparameter | Identisch | Identisch |
| Basismodell | roberta-bne-capitel-ner | roberta-bne-capitel-ner |

### Adversariale Tests (35 Fälle)

| Kategorie | Tests |
|-----------|-------|
| edge_case | 9 |
| adversarial | 8 |
| ocr_corruption | 5 |
| unicode_evasion | 3 |
| real_world | 10 |

---

## Ergebnisse nach Kategorie

### Pass Rate Vergleich

| Kategorie | v1 | v2 | Verbesserung |
|-----------|-----|-----|--------|
| edge_case | 55.6% (5/9) | 66.7% (6/9) | +11.1 pp |
| adversarial | 37.5% (3/8) | 62.5% (5/8) | **+25.0 pp** |
| ocr_corruption | 20.0% (1/5) | 40.0% (2/5) | **+20.0 pp** |
| unicode_evasion | 33.3% (1/3) | 33.3% (1/3) | 0 pp |
| real_world | 60.0% (6/10) | 50.0% (5/10) | -10.0 pp |

### Analyse nach Kategorie

**Signifikante Verbesserungen (+20 pp oder mehr):**
- **adversarial**: +25 pp - Bessere Kontextunterscheidung (Negation, Beispiele)
- **ocr_corruption**: +20 pp - Rauschen im Training half direkt

**Keine Änderung:**
- **unicode_evasion**: 33.3% - Erfordert Textnormalisierung, nicht nur Training

**Rückschritt:**
- **real_world**: -10 pp - Mögliches Overfitting auf Rauschen, weniger Robustheit bei komplexen Mustern

---

## Details der geänderten Tests

### Tests BESTANDEN in v2 (zuvor NICHT BESTANDEN)

| Test | Kategorie | Notiz |
|------|-----------|------|
| `ocr_letter_substitution` | ocr_corruption | DNl → DNI (l vs I) |
| `ocr_accent_loss` | ocr_corruption | José → Jose |
| `negation_dni` | adversarial | "NO tener DNI" - erkennt keine PII mehr |
| `organization_as_person` | adversarial | García y Asociados → ORG |
| `location_as_person` | adversarial | San Fernando → LOCATION |

### Tests NICHT BESTANDEN in v2 (zuvor BESTANDEN)

| Test | Kategorie | Notiz |
|------|-----------|------|
| `notarial_header` | real_world | Möglicher Rückschritt bei ausgeschriebenen Daten |
| `judicial_sentence_header` | real_world | Möglicher Rückschritt bei Namen in Großbuchstaben |

---

## Schlussfolgerungen

### Hauptbefunde

1. **Noise-Training funktioniert**: +8.6 pp globale Verbesserung, besonders bei OCR und Adversarial
2. **Spezifisches Rauschen ist wichtig**: l↔I, Akzente verbessert, aber 0↔O und Leerzeichen scheitern weiterhin
3. **Trade-off beobachtet**: Robustheit gegenüber Rauschen gewonnen, aber etwas Präzision bei komplexen Mustern verloren

### Grenzen des Ansatzes

1. **Unzureichendes Rauschen für 0↔O**: IBAN mit O statt 0 scheitert weiterhin
2. **Normalisierung erforderlich**: Unicode-Evasion erfordert Vorverarbeitung, nicht nur Training
3. **Komplexität der realen Welt**: Komplexe Dokumente erfordern mehr Trainingsdaten

### Empfehlungen

| Priorität | Maßnahme | Erwartete Auswirkung |
|-----------|--------|------------------|
| HOCH | Hinzufügen von Unicode-Normalisierung in der Vorverarbeitung | +10% unicode_evasion |
| HOCH | Mehr Vielfalt bei 0↔O Rauschen im Training | +5-10% ocr_corruption |
| MITTEL | Mehr real_world Beispiele im Datensatz | Wiederherstellung von -10% real_world |
| MITTEL | Hybride Pipeline (Regex → NER → Validierung) | +15-20% laut Literatur |

---

## Nächste Schritte

1. **Implementierung der hybriden Pipeline** gemäß Forschung PMC12214779
2. **Hinzufügen von text_normalizer.py** als Vorverarbeitung vor der Inferenz
3. **Erweiterung des Datensatzes** mit mehr Beispielen realer Dokumente
4. **Evaluierung der CRF-Schicht** zur Verbesserung der Sequenzkohärenz

---

## Verwandte Dateien

- `docs/reports/2026-01-20_adversarial_evaluation.md` - Evaluierung v1
- `docs/reports/2026-01-21_adversarial_evaluation_v2.md` - Evaluierung v2
- `docs/reports/2026-01-16_investigacion_pipeline_pii.md` - Best Practices
- `scripts/preprocess/inject_ocr_noise.py` - Rauschinjektions-Skript

---

**Datum:** 2026-01-22
