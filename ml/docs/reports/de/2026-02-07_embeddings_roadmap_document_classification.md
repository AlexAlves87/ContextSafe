# Embeddings für ContextSafe: Roadmap und Aktivierungskriterien

**Datum:** 07.02.2026
**Ziel:** Dokumentation des evaluierten Embedding-Ansatzes, der implementierten Alternativen
und der Kriterien, unter denen eine Skalierung auf Embeddings in Zukunft gerechtfertigt wäre.

---

## 1. Management-Zusammenfassung

Zwei Vorschläge mit Embeddings wurden evaluiert:

| Vorschlag | Quelle | Modell | Entscheidung |
|-----------|--------|--------|--------------|
| Dokumentenklassifizierung mit Embeddings | Verbesserungen der Architektur v2.1, Modul A | `intfloat/multilingual-e5-small` | **Zurückgestellt** — Regex implementiert |
| Gap Scanning mit Embeddings | Sicherheitsnetz-Strategie A | `intfloat/multilingual-e5-small` | **Verworfen** — Kosinus-Ähnlichkeit unzureichend |

**Aktueller Status:** Ein Regex-/Schlüsselwort-basierter Klassifikator (`DocumentTypeClassifier`) wurde implementiert,
der die unmittelbaren Anforderungen mit 0 Bytes Modellgröße, <1ms Latenz und ~95% geschätzter Genauigkeit
für spanische Rechtsdokumente abdeckt.

Embeddings werden als **zukünftige Skalierungsoption** dokumentiert, wenn spezifische Kriterien erfüllt sind (Abschnitt 5).

---

## 2. Evaluierter Vorschlag: Dokumentenklassifizierung mit Embeddings

### 2.1 Vorgeschlagenes Modell

| Spezifikation | Wert |
|---------------|------|
| Modell | `intfloat/multilingual-e5-small` (Wang et al., arXiv:2402.05672) |
| Parameter | 117,65M |
| FP32 Größe | 448 MB |
| INT8 ONNX Größe | 112 MB |
| Embedding-Dimension | 384 |
| Max Token | 512 |
| Geschätzte Latenz (CPU INT8) | ~200ms |
| Unterstützte Sprachen | 94-100 |
| Lizenz | MIT |
| Laufzeit-RAM (FP32) | ~500 MB |
| Laufzeit-RAM (INT8) | ~200 MB |

**Verifizierungsquelle:** HuggingFace Modellkarte `intfloat/multilingual-e5-small`.

### 2.2 Vorgeschlagene Architektur

```
Dokument → Embedding (e5-small) → Kosinus-Ähnlichkeit vs Zentroide → Typ → NER Config
```

Dies ist NICHT RAG-NER (der in Vorschlag v2.1 verwendete Begriff ist falsch).
Es ist **Dokumentenklassifizierung + bedingte Konfiguration**
(siehe `ml/docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md`, Abschnitt 2).

### 2.3 Warum es zurückgestellt wurde

| Faktor | Embeddings | Regex (implementiert) |
|--------|------------|-----------------------|
| Größe | 112-448 MB | 0 Bytes |
| Latenz | ~200ms | <1ms |
| Geschätzte Genauigkeit | ~99% | ~95%+ |
| Komplexität | Hoch (ONNX Runtime, Quantisierung) | Trivial |
| Zusätzlicher RAM | 200-500 MB | 0 |
| Wartung | Versioniertes Modell, Updates | Editierbare Muster |

Für ~7 Arten von Rechtsdokumenten mit sehr markanten Kopfzeilen ist Regex ausreichend.
Die zusätzlichen 4% Genauigkeit rechtfertigen weder 200MB Modellgröße noch die Wartungskomplexität.

---

## 3. Evaluierter Vorschlag: Gap Scanning mit Embeddings

### 3.1 Konzept

Verwendung von Embeddings zur Erkennung von "verdächtigen" Fragmenten, die nicht von NER identifiziert wurden:

```
Volltext → In Chunks segmentieren → Embedding jedes Chunks
    → Vergleich vs "PII-Risiko-Zentroid" → Warnung bei hoher Ähnlichkeit
```

### 3.2 Warum es verworfen wurde

1. **Kosinus-Ähnlichkeit erkennt keine PII**: Semantische Ähnlichkeit misst thematische Nähe,
   nicht das Vorhandensein persönlicher Daten. "Juan García wohnt in Madrid" und "Das Unternehmen operiert
   in Madrid" haben eine hohe semantische Ähnlichkeit, aber nur einer enthält nominale PII.

2. **Ein "PII-Risiko-Zentroid" existiert nicht**: Persönliche Daten (Namen, DNIs, IBANs, Adressen)
   belegen völlig disjunkte semantische Regionen. Es gibt keinen Punkt im Embedding-Raum,
   der "dies enthält PII" repräsentiert
   (siehe Ethayarajh, EMNLP 2019, zur Anisotropie von Embeddings).

3. **Referenz-Paper**: Netflix/Cornell 2024 dokumentiert Einschränkungen der Kosinus-Ähnlichkeit
   für die Erkennung von diskreten vs. kontinuierlichen Merkmalen. PII ist inhärent diskret
   (vorhanden oder abwesend).

4. **Implementierte Alternative**: Deterministische Sanity Checks (`ExportValidator`,
   `src/contextsafe/domain/document_processing/services/export_validator.py`) decken
   den Fall von False Negatives pro Dokumenttyp zuverlässiger und ohne zusätzliche Abhängigkeiten ab.

---

## 4. Implementierte Alternative: Regex-Klassifikator

### 4.1 Implementierung

```
src/contextsafe/domain/document_processing/services/document_classifier.py
```

| Merkmal | Detail |
|---------|--------|
| Unterstützte Typen | SENTENCIA, ESCRITURA, FACTURA, RECURSO, DENUNCIA, CONTRATO, GENERIC |
| Methode | Regex über die ersten 500 Zeichen (großgeschrieben) |
| Muster pro Typ | 4-8 markante Schlüsselwörter |
| Fallback | Dateiname, wenn Text nicht klassifiziert wird |
| Vertrauen | Anteil gefundener Muster / Total pro Typ |
| Latenz | <1ms |
| Abhängigkeiten | 0 (nur `re` aus stdlib) |

### 4.2 Schlüsselmuster

| Typ | Hauptmuster |
|-----|-------------|
| SENTENCIA | `SENTENCIA`, `JUZGADO`, `TRIBUNAL`, `FALLO`, `MAGISTRAD[OA]` |
| ESCRITURA | `ESCRITURA`, `NOTAR[IÍ]`, `PROTOCOLO`, `OTORGAMIENTO` |
| FACTURA | `FACTURA`, `BASE IMPONIBLE`, `IVA`, `TOTAL FACTURA` |
| RECURSO | `RECURSO`, `APELACI[OÓ]N`, `CASACI[OÓ]N` |
| DENUNCIA | `DENUNCIA`, `ATESTADO`, `DILIGENCIAS PREVIAS` |
| CONTRATO | `CONTRATO`, `CL[AÁ]USULA`, `ESTIPULACIONES` |

### 4.3 Integration mit Sanity Checks

Der Klassifikator speist die Export-Validierungsregeln:

```
Dokument → DocumentTypeClassifier → Typ
                                      ↓
ExportValidator.validate(Typ, ...) → Wendet Regeln SC-001..SC-004 an
```

| Regel | Typ | Minimale Kategorien | Schweregrad |
|-------|-----|---------------------|-------------|
| SC-001 | ESCRITURA | PERSON_NAME ≥1, DNI_NIE ≥1 | KRITISCH |
| SC-002 | SENTENCIA | DATE ≥1 | WARNUNG |
| SC-003 | FACTURA | ORGANIZATION ≥1 | WARNUNG |
| SC-004 | DENUNCIA | PERSON_NAME ≥1 | WARNUNG |

---

## 5. Aktivierungskriterien für Skalierung auf Embeddings

Embeddings sollten NUR dann neu in Betracht gezogen werden, wenn **mindestens 2** dieser Kriterien erfüllt sind:

### 5.1 Funktionale Kriterien

| # | Kriterium | Schwellenwert |
|---|-----------|---------------|
| CF-1 | Regex-Genauigkeit fällt unter 90% | Messen mit Validierungskorpus |
| CF-2 | >15 Dokumenttypen hinzugefügt | Regex wird unhandlich |
| CF-3 | Dokumente ohne standardisierte Kopfzeile | Verschlechtertes OCR, verschiedene Scanner |
| CF-4 | Anforderung an mehrsprachige Klassifizierung | Dokumente auf Katalanisch, Baskisch, Galizisch |

### 5.2 Infrastruktur-Kriterien

| # | Kriterium | Schwellenwert |
|---|-----------|---------------|
| CI-1 | Verfügbarer RAM in Produktion | ≥32 GB (aktuell Ziel ist 16 GB) |
| CI-2 | Pipeline nutzt bereits ONNX Runtime | Vermeidung neuer Abhängigkeit |
| CI-3 | Aktuelle Pipeline-Latenz | <2s total (Marge für +200ms) |

### 5.3 Implementierungspfad (falls aktiviert)

```
Schritt 1: Validierungskorpus sammeln (50+ Docs pro Typ)
Schritt 2: Aktuelle Regex-Genauigkeit mit Korpus bewerten
Schritt 3: Wenn Genauigkeit < 90%, zuerst TF-IDF + LogReg bewerten (~50KB, <5ms)
Schritt 4: Nur wenn TF-IDF < 95%, skalieren auf e5-small INT8 ONNX
Schritt 5: Zentroide pro Typ mit gelabeltem Korpus generieren
Schritt 6: Validieren mit Adversarial Tests (gemischte Dokumente, verschlechtertes OCR)
```

### 5.4 Empfohlenes Modell (bei Skalierung)

| Option | Größe | Latenz | Anwendungsfall |
|--------|-------|--------|----------------|
| TF-IDF + LogReg | ~50 KB | <5ms | Erster Skalierungsschritt |
| `intfloat/multilingual-e5-small` INT8 | 112 MB | ~200ms | Mehrsprachige Klassifizierung |
| `BAAI/bge-small-en-v1.5` INT8 | 66 MB | ~150ms | Nur Englisch/Spanisch |

**Hinweis:** `intfloat/multilingual-e5-small` bleibt die beste Option für mehrsprachige Anforderungen,
falls benötigt. Aber TF-IDF ist der korrekte Zwischenschritt vor neuronalen Embeddings.

---

## 6. Auswirkung auf die NER-Pipeline

### 6.1 Aktueller Status (implementiert)

```
Ingestiertes Dokument
    ↓
DocumentTypeClassifier.classify(erste_500_zeichen)      ← REGEX
    ↓
ConfidenceZone.classify(score, kategorie, checksum)     ← TRIAGE
    ↓
CompositeNerAdapter.detect_entities(text)               ← NER
    ↓
ExportValidator.validate(typ, entitäten, revisionen)    ← SAFETY LATCH
    ↓
[Export erlaubt oder blockiert]
```

### 6.2 Zukünftiger Status (wenn Embeddings aktiviert)

```
Ingestiertes Dokument
    ↓
DocumentTypeClassifier.classify(erste_500_zeichen)      ← REGEX (Fallback)
    ↓
EmbeddingClassifier.classify(erste_512_token)           ← EMBEDDINGS
    ↓
merge_classifications(regex_result, embedding_result)   ← FUSION
    ↓
CompositeNerAdapter.detect_entities(text, doc_type=typ) ← KONTEXTUELLES NER
    ↓
ExportValidator.validate(typ, entitäten, revisionen)    ← SAFETY LATCH
```

Die Schnittstelle des Klassifikators (`DocumentClassification` Dataclass) ist bereits so konzipiert,
dass sie ohne Änderungen am Rest der Pipeline austauschbar ist.

---

## 7. Schlussfolgerung

Der aktuelle Ansatz (Regex) ist die richtige Entscheidung für den aktuellen Status des Projekts.
Embeddings stellen eine inkrementelle Verbesserung dar, die nur bei signifikantem Wachstum
der Dokumenttypen oder messbarer Verschlechterung der Genauigkeit gerechtfertigt ist.

Die hexagonale Architektur ermöglicht Skalierung ohne Refactoring: Der `DocumentTypeClassifier`
kann durch einen `EmbeddingClassifier` ersetzt werden, der dieselbe Schnittstelle (`DocumentClassification`)
implementiert, ohne Auswirkungen auf den Rest der Pipeline.

---

## Verwandte Dokumente

| Dokument | Beziehung |
|----------|-----------|
| `ml/docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md` | Kritische Bewertung des RAG-NER-Vorschlags |
| `ml/docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | Aktuelle NER-Pipeline (5 Elemente) |
| `ml/docs/reports/2026-02-06_adversarial_v2_academic_r7.md` | Adversariale Evaluierung der Pipeline |
| `src/contextsafe/domain/document_processing/services/document_classifier.py` | Implementierter Regex-Klassifikator |
| `src/contextsafe/domain/document_processing/services/export_validator.py` | Safety Latch + Sanity Checks |
| `src/contextsafe/domain/entity_detection/services/confidence_zone.py` | Triage durch Vertrauenszonen |

## Referenzen

| Referenz | Venue | Relevanz |
|----------|-------|----------|
| Wang et al., "Multilingual E5 Text Embeddings" | arXiv:2402.05672 (2024) | Evaluiertes Modell |
| Ethayarajh, "How Contextual are Contextualized Word Representations?" | EMNLP 2019 | Embedding-Anisotropie |
| Netflix/Cornell, "Limitations of Cosine Similarity" | arXiv (2024) | Einschränkungen für diskrete Erkennung |
| Lewis et al., "Retrieval-Augmented Generation" | NeurIPS 2020 | Korrekte Definition von RAG |
| Dai et al., "RA-NER" | ICLR 2024 Tiny Papers | Echtes RAG angewendet auf NER |
