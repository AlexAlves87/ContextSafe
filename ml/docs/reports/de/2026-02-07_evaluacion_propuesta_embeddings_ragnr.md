# Kritische Evaluation: Embedding-Vorschlag (RAG-NER) für ContextSafe

**Datum:** 07.02.2026
**Ziel:** Bewertung der technischen Validität und Notwendigkeit von Modul A des Vorschlags
"Architektonische Verbesserungen v2.1" — Verwendung von `intfloat/multilingual-e5-small` zur
Dokumentenvorklassifizierung und dynamischen NER-Konfiguration.

---

## 1. Management-Zusammenfassung

Der Vorschlag empfiehlt die Verwendung von Embeddings (`intfloat/multilingual-e5-small`, ~120MB) als
"Element 0" der NER-Pipeline zur Klassifizierung von Dokumenttypen und dynamischen Anpassung der
Erkennungsschwellenwerte. Nach Untersuchung der akademischen Literatur, Überprüfung der
Modellspezifikationen und Abgleich mit dem aktuellen Status der ContextSafe-Pipeline
**lautet die Schlussfolgerung, dass die Kernidee teilweise sinnvoll ist, die vorgeschlagene Implementierung
jedoch überdimensioniert ist und der Begriff "RAG-NER" technisch inkorrekt ist**.

### Urteil

| Aspekt | Bewertung |
|--------|-----------|
| Konzept (Dokumenttyp-bewusstes NER) | Valide und nützlich |
| Begriff "RAG-NER" | Inkorrekt: es ist kein RAG |
| Vorgeschlagenes Modell (`multilingual-e5-small`) | Überdimensioniert für die Aufgabe |
| Reale Notwendigkeit in ContextSafe | Mittel: einfachere Alternativen verfügbar |
| Priorität vs. andere Verbesserungen | Niedrig gegenüber HITL- und Audit-Verbesserungen |

---

## 2. Analyse des Begriffs "RAG-NER"

### Was ist RAG in der Literatur

RAG (Retrieval-Augmented Generation) wurde von Lewis et al. (NeurIPS 2020) eingeführt
und bezieht sich spezifisch auf den **Abruf von Dokumenten/Passagen aus einer Wissensbasis
zur Erweiterung der Generierung** eines Sprachmodells.

Die tatsächlichen RAG+NER Papers (2024-2025) sind:

| Paper | Venue | Was es tatsächlich tut |
|-------|-------|------------------------|
| **RA-NER** (Dai et al.) | ICLR 2024 Tiny Papers | Ruft ähnliche Entitäten aus einer externen KB ab, um NER zu unterstützen |
| **RENER** (Shiraishi et al.) | arXiv 2410.13118 | Ruft ähnliche annotierte Beispiele als In-Context-Learning für NER ab |
| **RA-IT Open NER** | arXiv 2406.17305 | Instruction Tuning mit abgerufenen Beispielen für offenes NER |
| **IF-WRANER** | arXiv 2411.00451 | Wort-Level-Abruf für Few-Shot Cross-Domain NER |
| **RAG-BioNER** | arXiv 2508.06504 | Dynamisches Prompting mit RAG für biomedizinisches NER |

### Was Dokument v2.1 vorschlägt

Was beschrieben wird, ist KEIN RAG. Es ist **Dokumenttyp-Klassifizierung + bedingte NER-Konfiguration**.
Es erfolgt kein Abruf von Dokumenten/Beispielen aus einer Wissensbasis.
Es gibt keine Generierungserweiterung. Es ist ein Klassifikator, gefolgt von einem Schalter.

**Tatsächliches Diagramm des Vorschlags:**
```
Dokument → Embedding (e5-small) → Kosinus-Ähnlichkeit → Erkannter Typ → Config-Switch → NER
```

**Tatsächliches Diagramm von RAG-NER (RA-NER, Amazon):**
```
Eingabetext → Ähnliche Entitäten aus KB abrufen → Als Kontext in NER injizieren → Vorhersage
```

Es sind grundlegend unterschiedliche Architekturen. Die Bezeichnung des Vorschlags als "RAG-NER"
ist inkorrekt und könnte in technischer Dokumentation oder Publikationen irreführend sein.

---

## 3. Überprüfung des vorgeschlagenen Modells

### Tatsächliche Spezifikationen von `intfloat/multilingual-e5-small`

| Spezifikation | Behauptung v2.1 | Realer Wert | Quelle |
|---------------|-----------------|-------------|--------|
| Gewicht | ~120 MB | **448 MB (FP32), 112 MB (INT8 ONNX)** | HuggingFace |
| Parameter | Nicht angegeben | 117,65M | HuggingFace |
| Embedding-Dimension | Nicht angegeben | 384 | Paper arXiv:2402.05672 |
| Max Token | 512 | 512 (korrekt) | HuggingFace |
| Latenz | <200ms auf CPU | Plausibel für 512 Token INT8 | - |
| Sprachen | Nicht angegeben | 94-100 Sprachen | HuggingFace |
| Lizenz | Nicht angegeben | MIT | HuggingFace |

**Identifizierte Probleme:**
- Die Behauptung von "~120 MB" stimmt nur mit INT8-ONNX-Quantisierung. Das FP32-Modell wiegt
  448 MB. Das Dokument stellt nicht klar, dass Quantisierung erforderlich ist.
- Im Speicher (Runtime) verbraucht das FP32-Modell ~500MB RAM. Mit INT8 ~200MB.
- Auf der Zielhardware mit 16GB RAM (bereits mit RoBERTa + Presidio + spaCy geladen)
  ist der verfügbare Spielraum begrenzt.

### Referenz-Benchmark

| Benchmark | Ergebnis | Kontext |
|-----------|----------|---------|
| Mr. TyDi (Retrieval MRR@10) | 64,4 im Durchschnitt | Gut für mehrsprachiges Retrieval |
| MTEB Classification (Amazon) | 88,7% Genauigkeit | Akzeptabel für Klassifizierung |

Das Modell ist kompetent für Embedding-Aufgaben. Die Frage ist, ob ein 117M-Parameter-Modell
benötigt wird, um ~5 Arten von juristischen Dokumenten zu klassifizieren.

---

## 4. Bedarfsanalyse: Aktueller Status vs. Vorschlag

### Aktuelle ContextSafe-Pipeline

Der `CompositeNerAdapter` implementiert bereits ausgefeilte Kontextualisierungsmechanismen:

| Vorhandener Mechanismus | Beschreibung |
|-------------------------|--------------|
| **Contextual Anchors** (Phase 1) | Erzwingt Kategorien gemäß spanischem Rechtskontext |
| **Weighted Voting** (Phase 2) | Regex=5, RoBERTa=2, Presidio=1,5, spaCy=1 |
| **GDPR Risk Tiebreaker** (Phase 3) | Priorität: PERSON_NAME=100 → POSTAL_CODE=20 |
| **30+ False Positive Patterns** | Blockiert Rechtsverweise, DOI, ORCID, ISBN |
| **Spanish Stopwords Filter** | Vermeidet Erkennung von Artikeln/Pronomen |
| **Generic Terms Whitelist** | Begriffe, die nie anonymisiert werden (Staat, DSGVO, etc.) |
| **Matrioshka (verschachtelte Entitäten)** | Handhabung verschachtelter Entitäten |

Die aktuelle Pipeline hat NICHT:
- Dokumenttyp-Klassifizierung
- Dynamische Schwellenwerte pro Kategorie
- Dynamische Schwellenwerte pro Dokumenttyp

### Benötigt ContextSafe eine Dokumentenklassifizierung?

**Teilweise ja**, aber nicht wie vorgeschlagen. Die wirklichen Vorteile wären:
- Anpassung des IBAN-Schwellenwerts in Rechnungen (strenger) vs. Urteilen (entspannter)
- Aktivierung/Deaktivierung von Kategorien nach Kontext (z.B. Geburtsdatum relevant
  in Strafurteilen, nicht in Rechnungen)
- Reduzierung von False Positives von Eigennamen in Dokumenten mit vielen Firmennamen

### Einfachere und effektivere Alternativen

| Methode | Größe | Latenz | Geschätzte Genauigkeit | Komplexität |
|---------|-------|--------|------------------------|-------------|
| **Regex auf Kopfzeilen** | 0 KB (Code) | <1ms | ~95%+ | Trivial |
| **TF-IDF + LogisticRegression** | ~50 KB | <5ms | ~97%+ | Niedrig |
| **e5-small (INT8 ONNX)** | 112 MB | ~200ms | ~99% | Hoch |
| **e5-small (FP32)** | 448 MB | ~400ms | ~99% | Hoch |

Für spanische Rechtsdokumente sind die Kopfzeilen extrem markant:
- `"SENTENCIA"`, `"JUZGADO"`, `"TRIBUNAL"` → Urteil
- `"ESCRITURA"`, `"NOTARIO"`, `"PROTOCOLO"` → Notarielle Urkunde
- `"FACTURA"`, `"BASE IMPONIBLE"`, `"IVA"` → Rechnung
- `"RECURSO"`, `"APELACIÓN"`, `"CASACIÓN"` → Berufung/Revision

Ein Klassifikator basierend auf Regex/Schlüsselwörtern in den ersten 200 Zeichen erreicht
wahrscheinlich >95% Genauigkeit ohne Hinzufügen von Abhängigkeiten oder signifikanter Latenz.

---

## 5. Empfehlung

### Was zur Implementierung EMPFOHLEN wird

1. **Dokumenttyp-Klassifizierung** — aber mit Regex/Schlüsselwörtern, nicht Embeddings
2. **Dynamische Schwellenwerte pro Kategorie** — unabhängig von der Klassifizierung
3. **Bedingte NER-Konfiguration** — Regeln nach Typ aktivieren/deaktivieren

### Was NICHT empfohlen wird

1. **Keine Verwendung von Embeddings** zur Klassifizierung von ~5 Arten juristischer Dokumente
2. **Dies nicht "RAG-NER" nennen** — es ist Klassifizierung + bedingte Konfiguration
3. **Kein Hinzufügen von 112-448MB Modell**, wenn Regex das gleiche Ziel erreicht

### Vorgeschlagene Implementierung (Alternative)

```python
# Element 0: Dokumenttyp-Klassifikator (leichtgewichtig)
class DocumentTypeClassifier:
    """Klassifiziert juristischen Dokumenttyp aus Kopfzeilentext."""

    PATTERNS = {
        DocumentType.SENTENCIA: [r"SENTENCIA", r"JUZGADO", r"TRIBUNAL", r"FALLO"],
        DocumentType.ESCRITURA: [r"ESCRITURA", r"NOTARI", r"PROTOCOLO"],
        DocumentType.FACTURA: [r"FACTURA", r"BASE IMPONIBLE", r"IVA"],
        DocumentType.RECURSO: [r"RECURSO", r"APELACI[OÓ]N", r"CASACI[OÓ]N"],
    }

    def classify(self, text: str, max_chars: int = 500) -> DocumentType:
        header = text[:max_chars].upper()
        scores = {}
        for doc_type, patterns in self.PATTERNS.items():
            scores[doc_type] = sum(1 for p in patterns if re.search(p, header))
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return DocumentType.GENERIC
```

**Kosten:** 0 Bytes Modell, <1ms Latenz, ~0 zusätzliche Komplexität.
**Erweiterbar:** Wenn in Zukunft größere Raffinesse benötigt wird, kann auf
TF-IDF oder Embeddings skaliert werden. Aber einfach anfangen.

---

## 6. Über "Element 0" in der Pipeline

Wenn entschieden wird, die Dokumentenklassifizierung zu implementieren (mit der einfachen empfohlenen Methode),
wäre der korrekte Ort:

```
Ingestiertes Dokument
    ↓
Element 0: classify_document_type(erste_500_zeichen)  ← NEU
    ↓
CompositeNerAdapter.detect_entities(text, doc_type=typ)
    ↓
[RoBERTa | Presidio | Regex | spaCy] mit Schwellenwerten angepasst nach doc_type
    ↓
Merge (aktuelles gewichtetes Voting, funktioniert bereits gut)
```

Dieser Schritt ist konsistent mit der aktuellen hexagonalen Architektur und erfordert keine Änderungen
an bestehenden Ports oder Adaptern.

---

## 7. Schlussfolgerung

Der Vorschlag identifiziert einen echten Bedarf (Dokumenttyp-bewusstes NER),
schlägt jedoch eine überdimensionierte Lösung mit inkorrekter Terminologie vor. Ein Klassifikator
basierend auf Regex in Dokumentenkopfzeilen würde das gleiche Ziel erreichen, ohne
120-448MB Modell, 200ms zusätzliche Latenz oder Wartungskomplexität hinzuzufügen.

Die Investition von Aufwand zahlt sich viel mehr in Modul B (aktives Audit und
HITL-Rückverfolgbarkeit) aus, wo ContextSafe echte Lücken in der Einhaltung gesetzlicher Vorschriften aufweist.

---

## 8. Konsultierte Literatur

| Referenz | Venue | Relevanz |
|----------|-------|----------|
| Wang et al., "Multilingual E5 Text Embeddings" | arXiv:2402.05672 (2024) | Vorgeschlagenes Modell |
| Dai et al., "RA-NER" | ICLR 2024 Tiny Papers | Echtes RAG angewendet auf NER |
| Shiraishi et al., "RENER" | arXiv:2410.13118 (2024) | Retrieval-enhanced NER |
| arXiv 2406.17305, "RA-IT Open NER" | arXiv (2024) | Instruction Tuning + Retrieval |
| arXiv 2411.00451, "IF-WRANER" | arXiv (2024) | Few-Shot Cross-Domain NER + RAG |
| arXiv 2508.06504, "RAG-BioNER" | arXiv (2025) | Dynamisches Prompting + RAG |
| ACL 2020 LT4Gov, "Legal-ES" | ACL Anthology | Spanische Rechts-Embeddings |
| IEEE 2024, "Fine-grained NER Spanish legal" | IEEE Xplore | Spanisches Rechts-NER |
| Frontiers AI 2025, "LegNER multilingual" | Frontiers | Mehrsprachiges Rechts-NER |

## Verwandte Dokumente

| Dokument | Beziehung |
|----------|-----------|
| `ml/docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | Aktuelle NER-Pipeline (5 Elemente) |
| `ml/docs/reports/2026-02-06_adversarial_v2_academic_r7.md` | Adversariale Bewertung der aktuellen Pipeline |
| `ml/docs/reports/2026-01-31_mejores_practicas_ml_2026.md` | ML Best Practices |
| `src/contextsafe/infrastructure/nlp/composite_adapter.py` | Aktuelle Implementierung der NER-Pipeline |
