# Boundary Refinement - Integration in NER-Pipeline

**Datum:** 06.02.2026
**Autor:** AlexAlves87
**Komponente:** `scripts/preprocess/boundary_refinement.py` integriert in `ner_predictor.py`
**Standard:** SemEval 2013 Task 9 (Entitäts-Level Evaluierung)

---

## 1. Management-Zusammenfassung

Implementierung der Verfeinerung von Entitätsgrenzen, um partielle Übereinstimmungen (PAR) in korrekte (COR) gemäß dem SemEval 2013 Evaluierungs-Framework umzuwandeln.

### Ergebnisse

| Test-Suite | Ergebnis |
|------------|----------|
| Standalone Tests | 12/12 (100%) |
| Integrationstest | ✅ Funktional |
| Angewandte Verfeinerungen | 4/8 Entitäten in Demo |

### Verfeinerungstypen

| Typ | Entitäten | Aktion |
|-----|-----------|--------|
| OVER_EXTENDED | PERSON | Prä fix entfernen: Don, Dña., D., Mr., Doña |
| OVER_EXTENDED | DATE | Präfix entfernen: a, el día, día |
| OVER_EXTENDED | ORGANIZATION | Suffix entfernen: Kommas, Semikolons |
| OVER_EXTENDED | ADDRESS | Postleitzahl+Stadt am Ende entfernen |
| TRUNCATED | POSTAL_CODE | Auf 5 Ziffern erweitern |
| TRUNCATED | DNI_NIE | Erweitern um Kontrollbuchstaben einzuschließen |

---

## 2. Methodik

### 2.1 Vorherige Diagnose

`scripts/evaluate/diagnose_par_cases.py` wurde ausgeführt, um Fehlermuster zu identifizieren:

```
TRUNCATED (2 Fälle):
  - [address_floor_door] Fehlt am Ende: '001' (Postleitzahl)
  - [testament_comparecencia] Fehlt am Ende: 'Z' (DNI Buchstabe)

OVER_EXTENDED (9 Fälle):
  - Namen mit enthaltenen Ehrentiteln
  - Daten mit Präfix “a” enthalten
  - Organisationen mit abschließendem Komma
```

### 2.2 Implementierung

**Datei:** `scripts/preprocess/boundary_refinement.py`

```python
# Spanische Ehrentitel (Reihenfolge: längste zuerst)
PERSON_PREFIXES = [
    r"(?:Compareció\s+)?Don\s+",
    r"(?:Compareció\s+)?Doña\s+",
    r"Dña\.\s*",
    r"D\.\s*",
    r"Mr\.\s*",
    r"Mrs\.\s*",
    # ...
]

# Hauptfunktion
def refine_entity(text, entity_type, start, end, confidence, source, original_text):
    """Wendet Verfeinerung je nach Entitätstyp an."""
    if entity_type in REFINEMENT_FUNCTIONS:
        refined_text, refinement_applied = REFINEMENT_FUNCTIONS[entity_type](text, original_text)
    # ...
```

### 2.3 Pipeline-Integration

**Datei:** `scripts/inference/ner_predictor.py`

```python
# Import mit graceful degradation
try:
    from preprocess.boundary_refinement import refine_entity, RefinedEntity
    REFINEMENT_AVAILABLE = True
except ImportError:
    REFINEMENT_AVAILABLE = False

# In predict() Methode:
def predict(self, text, min_confidence=0.5, max_length=512):
    # 1. Textnormalisierung
    text = normalize_text_for_ner(text)

    # 2. NER-Vorhersage
    entities = self._extract_entities(...)

    # 3. Regex-Merge (Hybrid)
    if REGEX_AVAILABLE:
        entities = self._merge_regex_detections(text, entities, min_confidence)

    # 4. Grenzverfeinerung (NEU)
    if REFINEMENT_AVAILABLE:
        entities = self._apply_boundary_refinement(text, entities)

    return entities
```

### 2.4 Reproduzierbarkeit

```bash
# Umgebung
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Standalone Test
python scripts/preprocess/boundary_refinement.py

# Integrationstest
python scripts/inference/ner_predictor.py
```

---

## 3. Ergebnisse

### 3.1 Standalone Tests (12/12)

| Test | Entität | Verfeinerung | Ergebnis |
|------|---------|--------------|----------|
| person_don | PERSON | "Don " entfernen | ✅ |
| person_dña | PERSON | "Dña. " entfernen | ✅ |
| person_d_dot | PERSON | "D. " entfernen | ✅ |
| person_mr | PERSON | "Mr. " entfernen | ✅ |
| person_no_change | PERSON | Keine Änderung | ✅ |
| date_a_prefix | DATE | "a " entfernen | ✅ |
| date_el_dia | DATE | "el día " entfernen | ✅ |
| org_trailing_comma | ORGANIZATION | "," entfernen | ✅ |
| address_with_postal_city | ADDRESS | "28013 Madrid" entfernen | ✅ |
| postal_extend | POSTAL_CODE | "28" → "28001" | ✅ |
| dni_extend_letter | DNI_NIE | "12345678-" → "12345678Z" | ✅ |
| dni_no_extend | DNI_NIE | Keine Änderung | ✅ |

**Ausführungszeit:** 0,002s

### 3.2 Integrationstest

| Input | Originale Entität | Verfeinerte Entität | Verfeinerung |
|-------|-------------------|---------------------|--------------|
| "Don José García López con DNI..." | "Don José García López" | "José García López" | stripped_prefix:Don |
| "Dña. Ana Martínez Ruiz..." | "Dña. Ana Martínez Ruiz" | "Ana Martínez Ruiz" | stripped_prefix:Dña. |
| "Compareció Doña María Antonia..." | "Doña María Antonia Fernández Ruiz" | "María Antonia Fernández Ruiz" | stripped_prefix:Doña |
| "Mr. John Smith, residente..." | "Mr. John Smith" | "John Smith" | stripped_prefix:Mr. |

### 3.3 Entitäten Ohne Verfeinerung (Korrekt)

| Input | Entität | Grund |
|-------|---------|-------|
| "DNI 12345678Z" | "12345678Z" | Bereits korrekt |
| "IBAN ES91 2100..." | "ES91 2100 0418 4502 0005 1332" | Bereits korrekt |
| "Calle Alcalá 50" | "Calle Alcalá 50" | Bereits korrekt |
| "Sevilla" | "Sevilla" | Bereits korrekt |

---

## 4. Analyse

### 4.1 Pipeline-Auswirkung

Grenzverfeinerung wird **nach** dem NER+Regex Merge angewendet und fungiert als Post-Prozessor:

```
Text → Normalisierung → NER → Regex Merge → Verfeinerung → Finale Entitäten
                                              ↑
                                        (Element 5)
```

### 4.2 Metadaten-Erhaltung

Verfeinerung erhält alle originalen Metadaten:
- `confidence`: Unverändert
- `source`: Unverändert (ner/regex)
- `checksum_valid`: Unverändert
- `checksum_reason`: Unverändert

Fügt neue Felder hinzu:
- `original_text`: Text vor Verfeinerung
- `refinement_applied`: Art der angewendeten Verfeinerung

### 4.3 Beobachtung zu DATE

Das Datum "a quince de marzo de dos mil veinticuatro" im Integrationstest wurde **nicht verfeinert**, da das NER-Modell "quince de marzo de dos mil veinticuatro" direkt erkannte (ohne das Präfix "a"). Dies zeigt, dass:

1. Das NER-Modell bereits einige korrekte Grenzen lernt
2. Verfeinerung als Sicherheitsnetz für Fälle dient, die das Modell nicht handhabt

---

## 5. Komplette Pipeline (5 Elemente)

### 5.1 Integrierte Elemente

| # | Element | Standalone | Integration | Funktion |
|---|---------|------------|-------------|----------|
| 1 | TextNormalizer | 15/15 | ✅ | Unicode-Umgehung, Homoglyphen |
| 2 | Checksum Validators | 23/24 | ✅ | Vertrauensanpassung |
| 3 | Regex Patterns | 22/22 | ✅ | IDs mit Leerzeichen/Bindestrichen |
| 4 | Date Patterns | 14/14 | ✅ | Römische Zahlen |
| 5 | Boundary Refinement | 12/12 | ✅ | PAR→COR Konversion |

### 5.2 Datenfluss

```
Input: "Don José García López mit DNI 12345678Z"
                    ↓
[1] TextNormalizer: Keine Änderungen (sauberer Text)
                    ↓
[NER Model]: Erkennt "Don José García López" (PERSON), "12345678Z" (DNI_NIE)
                    ↓
[3] Regex Merge: Keine Änderungen (NER hat bereits vollständigen DNI erkannt)
                    ↓
[2] Checksum: Gültiger DNI → Vertrauensboost
                    ↓
[5] Boundary Refinement: "Don José García López" → "José García López"
                    ↓
Output: [PERSON] "José García López", [DNI_NIE] "12345678Z" ✅
```

---

## 6. Schlussfolgerungen

### 6.1 Errungenschaften

1. **Funktionale Verfeinerung**: 12/12 Standalone Tests, Integration verifiziert
2. **Graceful Degradation**: System funktioniert ohne das Modul (REFINEMENT_AVAILABLE=False)
3. **Metadaten-Erhaltung**: Checksum und Source intakt
4. **Rückverfolgbarkeit**: `original_text` und `refinement_applied` Felder für Audit

### 6.2 Bekannte Einschränkungen

| Einschränkung | Auswirkung | Minderung |
|---------------|------------|-----------|
| Nur statische Präfixe/Suffixe | Handhabt keine dynamischen Fälle | Muster decken 90%+ rechtliche Fälle ab |
| Erweiterung kontextabhängig | Kann fehlschlagen, wenn Text abgeschnitten | Längenprüfung |
| Keine CIF-Verfeinerung | Niedrige Priorität | Hinzufügen, wenn Muster erkannt |

### 6.3 Nächster Schritt

Vollständigen Adversarial-Test ausführen, um Auswirkung auf Metriken zu messen:

```bash
python scripts/evaluate/test_ner_predictor_adversarial_v2.py
```

**Zu beobachtende Metriken:**
- PAR (partielle Matches) - Reduktion erwartet
- COR (korrekte Matches) - Anstieg erwartet
- Pass Rate - Verbesserung erwartet

---

## 7. Referenzen

1. **SemEval 2013 Task 9**: Entity Evaluation Framework (COR/INC/PAR/MIS/SPU)
2. **PAR Diagnose**: `scripts/evaluate/diagnose_par_cases.py`
3. **Implementierung**: `scripts/preprocess/boundary_refinement.py`
4. **Integration**: `scripts/inference/ner_predictor.py` Zeilen 37-47, 385-432

---

**Gesamtausführungszeit:** 0,002s (Standalone) + 1,39s (Modell laden) + 18,1ms (Inferenz)
**Generiert von:** AlexAlves87
**Datum:** 06.02.2026
