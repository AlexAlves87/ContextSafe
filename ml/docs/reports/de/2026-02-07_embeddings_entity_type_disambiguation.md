# Forschung: Embeddings zur Entitätstyp-Disambiguierung in NER

**Datum:** 07.02.2026
**Ziel:** Lösung von Fehlern bei der Entitätstyp-Klassifizierung im ContextSafe NER-System (z.B. "Alejandro Alvarez" als ORGANIZATION statt PERSON_NAME klassifiziert)

---

## 1. Management-Zusammenfassung

1. **Identifiziertes Problem**: Das aktuelle NER-Modell verwechselt Entitätstypen, klassifiziert Personennamen als Organisationen, Daten als Organisationen und häufige großgeschriebene Wörter als PII.

2. **Vorgeschlagene Lösung**: Embedding-basierter Post-NER-Validator, der jede Erkennung gegen semantische Zentroide pro Entitätstyp vergleicht.

3. **Empfohlenes Modell**: `intfloat/multilingual-e5-large` (1,1GB) mit möglichem Upgrade auf `Legal-Embed` für den Rechtsbereich.

4. **Haupttechnik**: Zentroid-basierte Klassifizierung mit Neuklassifizierungs-Schwellenwert (Schwellenwert 0,75, Marge 0,1).

5. **Erwartete Fehlerreduktion**: ~4,5% laut Literatur (WNUT17 Benchmark).

---

## 2. Überprüfte Literatur

| Paper | Venue | Jahr | Relevantes Ergebnis |
|-------|-------|------|---------------------|
| NER Retriever: Zero-Shot Named Entity Retrieval with Type-Aware Embeddings | arXiv (2509.04011) | 2025 | Zwischenschichten (Schicht 17) erfassen Typinformationen besser als finale Ausgaben. MLP mit Contrastive Loss erreicht Zero-Shot auf ungesehene Typen. |
| CEPTNER: Contrastive Learning Enhanced Prototypical Network for Few-shot NER | Knowledge-Based Systems (ScienceDirect) | 2024 | Prototypische Netzwerke mit Contrastive Learning trennen Entitätstypen effektiv mit wenigen Beispielen (50-100). |
| Recent Advances in Named Entity Recognition: A Comprehensive Survey | arXiv (2401.10825) | 2024 | Hybride Ansätze (Regeln + ML + Embeddings) übertreffen konsequent einzelne Modelle. |
| Redundancy-Enhanced Framework for Error Correction in NER | OpenReview | 2025 | Post-Prozessor mit Transformer Refiner + Entity-Tag Embeddings erreicht 4,48% Fehlerreduktion in WNUT17. |
| Multilingual E5 Text Embeddings: A Technical Report | arXiv (2402.05672) | 2024 | Modell multilingual-e5-large unterstützt 100 Sprachen mit exzellenter Leistung in Spanisch. Erfordert Präfix "query:" für Such-Embeddings. |

---

## 3. Identifizierte Best Practices

1. **Kontext einbeziehen**: Das Embedding der Entität MIT ihrem umgebenden Kontext (10-15 Wörter) verbessert die Disambiguierung erheblich.

2. **Zwischenschichten nutzen**: Repräsentationen aus mittleren Schichten (Schicht 15-17) enthalten mehr Typinformationen als finale Ausgaben.

3. **Contrastive Learning**: Training mit Contrastive Loss trennt Typen im Embedding-Raum besser.

4. **Schwellenwert mit Marge**: Nicht nur aufgrund höherer Ähnlichkeit neu klassifizieren; Mindestmarge (>0,1) fordern, um False Positives zu vermeiden.

5. **Beispiele pro Typ**: 50-100 bestätigte Beispiele pro Kategorie reichen aus, um robuste Zentroide zu erstellen.

6. **Spezifischer Bereich**: Für den Bereich (Recht in unserem Fall) feinabgestimmte Modelle verbessern die Leistung.

7. **Markierung für HITL**: Wenn Ähnlichkeiten nah beieinander liegen (<0,05 Unterschied), für menschliche Überprüfung markieren statt automatisch neu zu klassifizieren.

---

## 4. Empfehlung für ContextSafe

### 4.1 Vorgeschlagene Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                    Aktuelle NER-Pipeline                        │
│  (RoBERTa + SpaCy + Regex → Intelligent Merge)                  │
60 └─────────────────────┬───────────────────────────────────────────┘
                      │ Erkennungen mit zugewiesenem Typ
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              Entity Type Validator (NEU)                         │
│                                                                  │
│  1. Entität + Kontext (±15 Token) extrahieren                   │
│  2. Embedding mit multilingual-e5-large generieren              │
│  3. Kosinus-Ähnlichkeit mit Zentroiden pro Typ berechnen        │
│  4. Entscheidung:                                               │
│     - Wenn bester_Typ ≠ NER_Typ UND Ähnlichkeit > 0,75          │
│       UND Marge > 0,1 → NEU KLASSIFIZIEREN                      │
│     - Wenn Marge < 0,05 → FÜR HITL MARKIEREN                    │
│     - Sonst → NER-Typ BEIBEHALTEN                               │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Validierte/korrigierte Erkennungen
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Glossary & Anonymization                         │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Ausgewähltes Modell

**Hauptmodell**: `intfloat/multilingual-e5-large`
- Größe: 1,1GB
- Sprachen: 100 (exzellentes Spanisch)
- Latenz: ~50-100ms pro Embedding
- Erfordert Präfix "query:" für Embeddings

**Alternative (evaluieren)**: `Wasserstoff-AI/Legal-Embed-intfloat-multilingual-e5-large-instruct`
- Feinabgestimmt für Rechtsbereich
- Gleiche Basisgröße
- Potenziell besser für spanische Rechtsdokumente

### 4.3 Konstruktion von Zentroiden

Prioritäre Kategorien (häufige Verwechslung):

| Kategorie | Benötigte Beispiele | Quelle |
|-----------|---------------------|--------|
| PERSON_NAME | 100 | Namen aus auditoria.md + Gazetteers |
| ORGANIZATION | 100 | Unternehmen, Institutionen aus Rechtsdokumenten |
| DATE | 50 | Daten in Formaten DD/MM/YYYY, DD-MM-YYYY |
| LOCATION | 50 | Städte, spanische Provinzen |

**Beispielformat** (mit Kontext):
```
"query: Der Anwalt Alejandro Alvarez erschien als Zeuge im Prozess"
"query: Das Unternehmen Telefónica S.A. legte Kassationsbeschwerde ein"
"query: Am Datum 10/10/2025 wurde das Urteil gefällt"
```

### 4.4 Integration in bestehende Pipeline

Vorgeschlagener Ort: `src/contextsafe/infrastructure/nlp/validators/entity_type_validator.py`

```python
class EntityTypeValidator:
    """
    Post-processor that validates/corrects NER entity type assignments
    using embedding similarity to type centroids.

    Based on: NER Retriever (arXiv 2509.04011), CEPTNER (KBS 2024)
    """

    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-large",
        centroids_path: Path = None,
        reclassify_threshold: float = 0.75,
        margin_threshold: float = 0.10,
        hitl_margin: float = 0.05,
    ):
        ...

    def validate(
        self,
        entity_text: str,
        context: str,
        predicted_type: str,
    ) -> ValidationResult:
        """
        Returns ValidationResult with:
        - corrected_type: str
        - confidence: float
        - action: 'KEEP' | 'RECLASSIFY' | 'FLAG_HITL'
        """
        ...
```

### 4.5 Erfolgsmetriken

| Metrik | Ziel | Messung |
|--------|------|---------|
| Reduktion von Typfehlern | ≥4% | Vergleich vor/nach auf Validierungsset |
| Zusätzliche Latenz | <100ms/Entität | Benchmark auf 16GB CPU |
| False Positives bei Neuklassifizierung | <2% | Manuelle Überprüfung von Neuklassifizierungen |
| HITL-Abdeckung | <10% markiert | Prozentsatz für menschliche Überprüfung markiert |

---

## 5. Referenzen

1. **NER Retriever**: Zhang et al. (2025). "NER Retriever: Zero-Shot Named Entity Retrieval with Type-Aware Embeddings." arXiv:2509.04011. https://arxiv.org/abs/2509.04011

2. **CEPTNER**: Wang et al. (2024). "CEPTNER: Contrastive learning Enhanced Prototypical network for Two-stage Few-shot Named Entity Recognition." Knowledge-Based Systems. https://doi.org/10.1016/j.knosys.2024.111512

3. **NER Survey**: Li et al. (2024). "Recent Advances in Named Entity Recognition: A Comprehensive Survey and Comparative Study." arXiv:2401.10825. https://arxiv.org/abs/2401.10825

4. **Error Correction Framework**: Chen et al. (2025). "A Redundancy-Enhanced Framework for Error Correction in Named Entity Recognition." OpenReview. https://openreview.net/forum?id=2jFWhxJE5pQ

5. **Multilingual E5**: Wang et al. (2024). "Multilingual E5 Text Embeddings: A Technical Report." arXiv:2402.05672. https://arxiv.org/abs/2402.05672

6. **Legal-Embed**: Wasserstoff-AI. (2024). "Legal-Embed-intfloat-multilingual-e5-large-instruct." HuggingFace. https://huggingface.co/Wasserstoff-AI/Legal-Embed-intfloat-multilingual-e5-large-instruct

---

## 6. Identifizierte Klassifizierungsfehler (Audit)

Analyse der Datei `auditoria.md` aus Dokument STSJ ICAN 3407/2025:

| Entität | Zugewiesener Typ | Korrekter Typ | Muster |
|---------|------------------|---------------|--------|
| `"10/10/2025"` | ORGANIZATION (Org_038) | DATE | Datum mit Code verwechselt |
| `"05-11-2024"` | ORGANIZATION | DATE | Datum im DD-MM-YYYY Format |
| `"Pura"` | LOCATION (Lugar_001) | PERSON_NAME | Kurzer Name ohne Ehrentitel |
| `"Finalmente"` | ORGANIZATION (Org_012) | KEIN PII | Großgeschriebenes Adverb |
| `"Terminaba"` | ORGANIZATION (Org_017) | KEIN PII | Großgeschriebenes Verb |
| `"Quien"` | ORGANIZATION | KEIN PII | Großgeschriebenes Pronomen |
| `"Whatsapp"` | PERSON | ORGANIZATION/PLATFORM | Plattformname |

**Identifiziertes Hauptmuster**: Das RoBERTa-Modell klassifiziert jedes großgeschriebene Wort am Satzanfang, das es nicht eindeutig als anderen Typ erkennt, als ORGANIZATION.

---

## Verwandte Dokumente

| Dokument | Beziehung |
|----------|-----------|
| `auditoria.md` | Quelle der analysierten Klassifizierungsfehler |
| `docs/PLAN_CORRECCION_AUDITORIA.md` | Vorheriger Korrekturplan (7 Issues identifiziert) |
| `ml/docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md` | Vorherige Embedding-Evaluierung (Dokumentenklassifizierung) |
| `ml/docs/reports/2026-02-07_embeddings_roadmap_document_classification.md` | Embedding-Roadmap für Klassifizierung |
| `ml/README.md` | ML-Anweisungen (Berichtsformat) |

---

## Nächste Schritte

1. [ ] Modell `intfloat/multilingual-e5-large` herunterladen (~1,1GB)
2. [ ] Datensatz von Beispielen pro Typ (PERSON_NAME, ORGANIZATION, DATE, LOCATION) erstellen
3. [ ] `EntityTypeValidator` in `infrastructure/nlp/validators/` implementieren
4. [ ] Zentroide pro Typ berechnen und persistieren
5. [ ] Validator in bestehende NER-Pipeline integrieren
6. [ ] Fehlerreduktion auf Validierungsset evaluieren
7. [ ] (Optional) `Legal-Embed` vs `multilingual-e5-large` evaluieren

---

```
Version: 1.0.0
Autor: AlexAlves87
Recherchezeit: ~15 min
```
