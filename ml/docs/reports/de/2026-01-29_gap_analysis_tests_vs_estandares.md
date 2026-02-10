# Gap-Analyse: Aktuelle Tests vs. Akademische Standards

**Datum:** 29.01.2026
**Autor:** AlexAlves87
**Analysierte Datei:** `scripts/evaluate/test_ner_predictor_adversarial.py`

---

## 1. Zusammenfassung der Lücken

| Aspekt | Akademischer Standard | Aktuelle Implementierung | Schweregrad |
|--------|-----------------------|--------------------------|-------------|
| Evaluierungsmodus | Strict (SemEval 2013) | Lenient (benutzerdefiniert) | **KRITISCH** |
| 4 SemEval-Modi | strict, exact, partial, type | Nur 1 benutzerdefiniert | HOCH |
| Metrik-Bibliothek | seqeval oder nervaluate | Benutzerdefinierte Impl. | HOCH |
| Detaillierte Metriken | COR/INC/PAR/MIS/SPU | Nur TP/FP/FN | MITTEL |
| Metriken pro Typ | F1 pro PERSON, DNI, etc. | Nur aggregiertes F1 | MITTEL |
| NoiseBench-Referenz | EMNLP 2024 | "ICLR 2024" (Fehler) | NIEDRIG |
| Modus-Dokumentation | Explizit im Bericht | Nicht dokumentiert | MITTEL |

---

## 2. Detaillierte Analyse

### 2.1 KRITISCH: Matching-Modus ist nicht Strict

**Aktueller Code (Zeilen 458-493):**

```python
def entities_match(expected: dict, detected: dict, tolerance: int = 5) -> bool:
    # Type must match
    if expected["type"] != detected["type"]:
        return False

    # Containment (detected contains expected or vice versa)
    if exp_text in det_text or det_text in exp_text:
        return True

    # Length difference tolerance
    if abs(len(exp_text) - len(det_text)) <= tolerance:
        # Check character overlap
        common = sum(1 for c in exp_text if c in det_text)
        if common >= len(exp_text) * 0.8:
            return True
```

**Probleme:**
1. Erlaubt **Containment** (Wenn "José García" in "Don José García López" enthalten ist, zählt es als Treffer)
2. Erlaubt **80% Zeichenüberlappung** (keine exakte Grenze)
3. Erlaubt **5 Zeichen Toleranz** in der Länge

**SemEval Strict Standard:**
> "Exact boundary surface string match AND entity type match"

**Auswirkung:** Die aktuellen Ergebnisse (F1=0.784, 54.3% Pass-Rate) könnten **AUFGEBLÄHT** sein, da partielle Übereinstimmungen als korrekt akzeptiert werden.

### 2.2 HOCH: Verwendet weder seqeval noch nervaluate

**Standard:** Verwendung von Bibliotheken, die gegen conlleval validiert sind.

**Aktuell:** Benutzerdefinierte Metrik-Implementierung.

**Risiko:** Benutzerdefinierte Metriken sind möglicherweise nicht mit wissenschaftlicher Literatur vergleichbar.

### 2.3 HOCH: Nur ein Evaluierungsmodus

**SemEval 2013 definiert 4 Modi:**

| Modus | Grenze | Typ | Verwendung |
|-------|--------|-----|------------|
| **strict** | Exakt | Exakt | Hauptmodus, rigoros |
| exact | Exakt | Ignoriert | Grenzanalyse |
| partial | Überlappung | Ignoriert | Nachsichtige Analyse |
| type | Überlappung | Exakt | Klassifikationsanalyse |

**Aktuell:** Nur ein benutzerdefinierter Modus (ähnlich wie partial/lenient).

**Auswirkung:** Wir können Grenzfehler nicht von Typfehlern trennen.

### 2.4 MITTEL: Keine COR/INC/PAR/MIS/SPU Metriken

**SemEval 2013:**
- **COR**: Correct (Grenze UND Typ exakt)
- **INC**: Incorrect (Grenze exakt, Typ falsch)
- **PAR**: Partial (Grenze mit Überlappung)
- **MIS**: Missing (FN)
- **SPU**: Spurious (FP)

**Aktuell:** Nur TP/FP/FN (unterscheidet nicht zwischen INC und PAR).

### 2.5 MITTEL: Keine Metriken pro Entitätstyp

**Standard:** F1 für jeden Typ (PERSON, DNI_NIE, IBAN, etc.) berichten.

**Aktuell:** Nur aggregiertes F1.

**Auswirkung:** Wir wissen nicht, welche Entitätstypen schlechter abschneiden.

### 2.6 NIEDRIG: Referenzfehler

**Zeile 10:** `NoiseBench (ICLR 2024)`

**Korrekt:** `NoiseBench (EMNLP 2024)`

---

## 3. Auswirkung auf berichtete Ergebnisse

### 3.1 Schätzung Differenz Strict vs. Lenient

Basierend auf Literatur produziert der Strict-Modus typischerweise **5-15% weniger F1** als Lenient:

| Metrik | Aktuell (lenient) | Geschätzt (strict) |
|--------|-------------------|--------------------|
| F1 | 0.784 | 0.67-0.73 |
| Pass-Rate | 54.3% | 40-48% |

**Die aktuellen Ergebnisse sind optimistisch.**

### 3.2 Tests betroffen von Lenient Matching

Tests, bei denen Lenient Matching als korrekt akzeptiert, was Strict ablehnen würde:

| Test | Situation | Auswirkung |
|------|-----------|------------|
| `very_long_name` | Langer Name, exakte Grenze? | Möglich |
| `address_floor_door` | Komplexe Adresse | Möglich |
| `testament_comparecencia` | Mehrere Entitäten | Hoch |
| `judicial_sentence_header` | Textuelle Daten | Hoch |

---

## 4. Abhilfeplan

### 4.1 Erforderliche Änderungen

1. **Strict-Modus implementieren** (Priorität KRITISCH)
   - Grenze muss exakt sein (normalisiert)
   - Typ muss exakt sein

2. **nervaluate hinzufügen** (Priorität HOCH)
   ```bash
   pip install nervaluate
   ```

3. **4 Modi berichten** (Priorität HOCH)
   - strict (Haupt)
   - exact
   - partial
   - type

4. **Metriken pro Typ hinzufügen** (Priorität MITTEL)

5. **NoiseBench-Referenz korrigieren** (Priorität NIEDRIG)

### 4.2 Migrationsstrategie

Um die Vergleichbarkeit mit früheren Ergebnissen zu wahren:

1. Mit **beiden Modi** (Lenient UND Strict) ausführen
2. **Beide** in der Dokumentation berichten
3. **Strict als Hauptmetrik** für die Zukunft verwenden
4. Differenz für Baseline dokumentieren

---

## 5. Vorgeschlagenes neues Skript

Erstelle `test_ner_predictor_adversarial_v2.py` mit:

1. Strict-Modus als Standard
2. Integration mit nervaluate
3. COR/INC/PAR/MIS/SPU Metriken
4. F1 pro Entitätstyp
5. Legacy-Modus-Option für Vergleich

---

## 6. Schlussfolgerungen

**Aktuelle Ergebnisse (F1=0.784, 54.3% Pass) sind nicht mit wissenschaftlicher Literatur vergleichbar**, da:

1. Sie verwenden Lenient Matching, nicht Strict
2. Sie verwenden keine Standardbibliotheken (seqeval, nervaluate)
3. Sie berichten keine granularen Metriken (pro Typ, COR/INC/PAR)

**Sofortige Maßnahme:** Bevor mit der TextNormalizer-Integration fortgefahren wird, müssen wir:

1. v2-Skript mit akademischen Standards erstellen
2. Baseline mit Strict-Modus wiederherstellen
3. DANN Verbesserungsauswirkung bewerten

---

**Generiert von:** AlexAlves87
**Datum:** 29.01.2026
