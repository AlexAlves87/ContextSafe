# Forschung: Generalistische vs. Juristische Embeddings für die Disambiguierung von Entitätstypen

**Datum:** 07.02.2026
**Ziel:** Bestimmen, ob generalistische Embeddings (multilingual-e5-large) oder juristisch spezialisierte (Legal-Embed, voyage-law-2) für den Post-NER-Validierer von Entitätstypen in ContextSafe verwendet werden sollen.

---

## 1. Management-Zusammenfassung

1.  **Haupterkenntnis**: Juristische Embeddings sind für **Retrieval** (Suche nach ähnlichen Dokumenten) optimiert, NICHT für die **Unterscheidung von Entitätstypen**. Dies erklärt die beobachteten False Positives.
2.  **Empfehlung**: Verwendung von **generalistischen Embeddings** (`intfloat/multilingual-e5-large`) für die Disambiguierung von Entitätstypen. Juristische Embeddings können einen Kollaps des semantischen Raums verursachen, bei dem PERSON und ORGANIZATION zu nahe beieinander liegen.
3.  **Schlüsselbeweis**: Domain-Fine-Tuning kann zu einer „Überspezialisierung“ führen, die die Unterscheidungsfähigkeit zwischen Kategorien verringert (katastrophales Vergessen von Grenzen zwischen Typen).
4.  **Hybride Alternative**: Wenn juristisches Wissen erforderlich ist, verwenden Sie einen zweistufigen Ansatz: generalistisch für den Typ + juristisch für die Validierung spezifischer Entitäten.
5.  **Erwartete Fehlerreduzierung**: 4-5% mit gut kalibrierten generalistischen Embeddings (Literatur: WNUT17, NER Retriever).

---

## 2. Überprüfte Literatur

### 2.1 Generalistisch vs. Domänenspezifisch

| Paper/Quelle | Venue/Jahr | Relevante Erkenntnis |
| :--- | :--- | :--- |
| "Do we need domain-specific embedding models?" | arXiv:2409.18511 (2024) | Im Finanzwesen (FinMTEB) verschlechtern sich allgemeine Modelle im Vergleich zu spezifischen. ABER: Dies gilt für **Retrieval**, nicht für Typklassifizierung. |
| "How Does Fine-tuning Affect the Geometry of Embedding Space?" | ACL Findings 2021 | Domain-Fine-Tuning **verringert die Trennung** zwischen Klassen im Embedding-Raum. Cluster kollabieren. |
| "Is Anisotropy Really the Cause of BERT Embeddings not Working?" | EMNLP Findings 2022 | Anisotropie (Embeddings konzentriert in engem Kegel) ist ein bekanntes Problem. Domain-Fine-Tuning **verschlimmert** es. |
| "Dynamic Expert Specialization: Catastrophic Forgetting-Free Multi-Domain MoE" | EMNLP 2025 | Katastrophales Vergessen tritt beim Domain-Fine-Tuning auf. Modelle vergessen zuvor gelernte Grenzen. |
| "Continual Named Entity Recognition without Catastrophic Forgetting" | arXiv:2310.14541 (2023) | Kontinuierliches NER leidet unter katastrophalem Vergessen: Alte Typen „konsolidieren“ sich in Nicht-Entitäten. Analog zu unserem Problem. |

### 2.2 Warum juristische Embeddings False Positives verursachen

| Phänomen | Erklärung | Quelle |
| :--- | :--- | :--- |
| **Kollaps des semantischen Raums** | Juristisches Fine-Tuning optimiert darauf, dass ähnliche juristische Dokumente nahe beieinander liegen, NICHT darauf, PERSON von ORGANIZATION zu trennen | Weaviate Blog, MongoDB Fine-Tuning Guide |
| **Überspezialisierung** | „Zu enges Training kann das fein abgestimmte Modell zu spezialisiert machen“ – verliert allgemeine Unterscheidungsfähigkeit | [Weaviate](https://weaviate.io/blog/fine-tune-embedding-model) |
| **Retrieval-orientierter Contrastive Loss** | voyage-law-2 verwendet „speziell entworfene positive Paare“ für juristisches Retrieval, nicht für Entitätsklassifizierung | [Voyage AI Blog](https://blog.voyageai.com/2024/04/15/domain-specific-embeddings-and-retrieval-legal-edition-voyage-law-2/) |
| **Einheitliche juristische Terminologie** | In juristischen Texten kann „Garcia“ Kläger, Anwalt oder Name einer Kanzlei sein. Das juristische Modell bettet sie **nahe beieinander** ein, weil alle juristisch sind | Empirische Beobachtung des Benutzers |

### 2.3 Zentroide und Prototyp-basierte Klassifizierung

| Paper/Quelle | Venue/Jahr | Relevante Erkenntnis |
| :--- | :--- | :--- |
| "NER Retriever: Zero-Shot NER with Type-Aware Embeddings" | arXiv:2509.04011 (2025) | Zwischenschichten (Layer 17) besser als Endausgaben für Typ. MLP mit Contrastive Loss zur Trennung von Typen. |
| "CEPTNER: Contrastive Learning Enhanced Prototypical Network" | KBS (2024) | Prototypische Netzwerke mit 50-100 Beispielen pro Typ reichen für robuste Zentroide aus. |
| "ReProCon: Scalable Few-Shot Biomedical NER" | arXiv:2508.16833 (2025) | Mehrere Prototypen pro Kategorie verbessern die Repräsentation heterogener Entitäten. |
| "Mastering Intent Classification with Embeddings: Centroids" | Medium (2024) | Zentroide haben die „schnellste Trainingszeit“ und eine ordentliche Genauigkeit. Perfekt für schnelle Updates. |

### 2.4 Benchmarks für Embedding-Modelle

| Modell | Größe | Sprachen | MTEB Avg | Vorteil | Nachteil |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `intfloat/multilingual-e5-large` | 1.1GB | 100 | ~64 | Bestes allgemeines mehrsprachiges Modell, exzellentes Spanisch | Erfordert Präfix „query:“ |
| `intfloat/multilingual-e5-large-instruct` | 1.1GB | 100 | ~65 | Unterstützt Anweisungen, flexibler | Etwas langsamer |
| `BAAI/bge-m3` | 1.5GB | 100+ | ~66 | Hybrid dense+sparse, 8192 Token | Komplexer in der Anwendung |
| `voyage-law-2` | API | EN | ~72 (legal) | Am besten für juristisches Retrieval | Kommerzielle API, nur Englisch |
| `Legal-Embed (Wasserstoff)` | 1.1GB | Multi | N/A | Feinabgestimmt auf Recht | **Verursacht wahrscheinlich FPs in der Klassifizierung** |

---

## 3. Analyse: Warum Generalisten besser für Entitätstypen sind

### 3.1 Unterschiedliches Trainingsziel

| Juristische Embeddings | Generalistische Embeddings |
| :--- | :--- |
| Optimiert für: „Dokument A ähnlich wie Dokument B“ | Optimiert für: „Text A semantisch verwandt mit Text B“ |
| Positive Paare: Fragmente desselben juristischen Dokuments | Positive Paare: Paraphrasen, Übersetzungen, Varianten |
| Ergebnis: Alles Juristische ist nah beieinander | Ergebnis: Semantische Typen getrennt |

**Konsequenz**: In juristischen Embeddings sind „Alejandro Alvarez“ (Anwalt) und „Bufete Alvarez S.L.“ (Firma) **nahe beieinander**, weil beide juristisch sind. In generalistischen sind sie **weit voneinander entfernt**, weil eines eine Person und das andere eine Organisation ist.

### 3.2 Beweis für verschärfte Anisotropie

Das Paper von ACL Findings 2021 zeigt, dass:

1.  Fine-Tuning die **Varianz** des Embedding-Raums verringert
2.  Cluster verschiedener Typen **näher zusammenrücken**
3.  Die lineare Trennbarkeit **abnimmt**

Dies erklärt direkt die False Positives: Wenn alle juristischen Embeddings in eine Region kollabieren, verliert die Kosinus-Distanz an Unterscheidungskraft.

### 3.3 Aufgabe vs. Domäne

| Aspekt | Domänen-Embeddings (Legal) | Aufgaben-Embeddings (Typ) |
| :--- | :--- | :--- |
| Frage, die sie beantworten | „Ist dieser Text juristisch?“ | „Ist das eine Person oder eine Firma?“ |
| Training | Juristisches Korpus | Kontrastiv nach Entitätstyp |
| Nutzen für NER-Typvalidierung | Gering | Hoch |

Unser Problem ist ein **Aufgabenproblem** (Typ klassifizieren), kein **Domänenproblem** (juristische Texte identifizieren).

---

## 4. Empfehlung für ContextSafe

### 4.1 Empfohlener Ansatz: Rein generalistisch

```
Pipeline:
  NER → Erkennungen mit zugewiesenem Typ
    ↓
  EntityTypeValidator (multilingual-e5-large)
    ↓
  Für jede Entität:
    1. Einbetten "query: [Entität + Kontext ±10 Token]"
    2. Vergleichen vs Zentroide nach Typ (PERSON_NAME, ORGANIZATION, DATE, LOCATION)
    3. Entscheidungen:
       - Wenn best_centroid ≠ NER_type AND Ähnlichkeit > 0.75 AND Marge > 0.10 → REKLASSIFIZIEREN
       - Wenn Marge < 0.05 → FLAG HITL
       - Sonst → NER-Typ BEIBEHALTEN
```

**Modell**: `intfloat/multilingual-e5-large` (1.1GB)

**Begründung**:

*   Trainiert in 100 Sprachen einschließlich Spanisch
*   NICHT überspezialisiert in irgendeiner Domäne
*   Bewahrt semantische Trennung zwischen PERSON/ORGANIZATION/DATE/LOCATION
*   Bereits in früherer Forschung empfohlen (siehe `2026-02-07_embeddings_entity_type_disambiguation.md`)

### 4.2 Alternativer Ansatz: Hybrid (Wenn juristisches Wissen erforderlich ist)

```
Stufe 1: Typklassifizierung (GENERALISTISCH)
  multilingual-e5-large → Entitätstyp

Stufe 2: Juristische Entitätsvalidierung (LEGAL, optional)
  voyage-law-2 oder Legal-Embed → "Ist diese Entität im juristischen Kontext gültig?"
  (Nur für als zweifelhaft markierte Fälle)
```

**Wann hybrid verwenden**: Wenn es spezifische juristische Entitäten gibt (z. B. „Artikel 24.2 CE“, „Gesetz 13/2022“), die eine Validierung durch juristisches Wissen erfordern.

Für ContextSafe (generische PII) ist der rein generalistische Ansatz ausreichend.

### 4.3 Konfiguration der Zentroide

| Typ | Benötigte Beispiele | Kontextstrategie |
| :--- | :--- | :--- |
| PERSON_NAME | 100 | "query: Der Anwalt [NAME] erschien..." |
| ORGANIZATION | 100 | "query: Die Firma [ORG] legte Berufung ein..." |
| DATE | 50 | "query: Am Datum [DATUM] wurde das Urteil gefällt..." |
| LOCATION | 50 | "query: In der Stadt [ORT] fand statt..." |
| DNI_NIE | 30 | "query: mit DNI [NUMMER]" (kurzer Kontext, festes Muster) |

**Kontext**: ±10 Token um die Entität. Weder zu kurz (verliert Kontext) noch zu lang (führt Rauschen ein).

---

## 5. Vorgeschlagenes Experiment

### 5.1 A/B-Vergleich

| Bedingung | Modell | Erwartet |
| :--- | :--- | :--- |
| A (Baseline) | Ohne Validierer | Aktuelle Pass-Rate: 60% |
| B (Generalistisch) | `multilingual-e5-large` | Erwartete Pass-Rate: 64-65% |
| C (Legal) | `Legal-Embed-intfloat-multilingual-e5-large-instruct` | Erwartete Pass-Rate: < 60% (mehr FPs) |

### 5.2 Zu bewertende Metriken

1.  **Pass-Rate im Adversarial Test** (35 vorhandene Tests)
2.  **Genauigkeit der Reklassifizierung**: % der korrekten Reklassifizierungen
3.  **False-Positive-Rate**: Korrekt typisierte Entitäten, die falsch reklassifiziert wurden
4.  **Zusätzliche Latenz**: ms pro validierter Entität

### 5.3 Spezifische Testfälle

Basierend auf Fehlern aus audit.md (siehe `2026-02-07_embeddings_entity_type_disambiguation.md`, Abschnitt 6):

| Entität | NER-Typ | Korrekter Typ | Erwartetes OK Modell |
| :--- | :--- | :--- | :--- |
| "Alejandro Alvarez" | ORGANIZATION | PERSON_NAME | Generalistisch |
| "10/10/2025" | ORGANIZATION | DATE | Generalistisch |
| "Pura" | LOCATION | PERSON_NAME | Generalistisch |
| "Finalmente" | ORGANIZATION | KEIN PII | Generalistisch (geringe Ähnlichkeit mit allen) |
| "Whatsapp" | PERSON | ORGANIZATION/PLATFORM | Generalistisch |

---

## 6. Risiken und Minderungsmaßnahmen

| Risiko | Wahrscheinlichkeit | Minderung |
| :--- | :--- | :--- |
| Generalist unterscheidet PERSON/ORG auch im juristischen Spanisch nicht gut | Mittel | Vor Implementierung bewerten; wenn fehlgeschlagen, Zentroide mit Contrastive Loss trainieren |
| Inakzeptable Latenz (>100ms/Entität) | Niedrig | Stapelverarbeitung, Caching häufiger Embeddings |
| Zentroide erfordern mehr als 100 Beispiele | Niedrig | Auf 200 erhöhen, wenn F1 < 0.90 in Validierung |
| 1.1GB Modell passt nicht in Produktion | Niedrig | Auf INT8 quantisieren (~300MB) oder e5-base (560MB) verwenden |

---

## 7. Schlussfolgerung

**Juristische Embeddings sind für die falsche Aufgabe optimiert.** Ihr Ziel (Retrieval ähnlicher Dokumente) führt dazu, dass Entitäten verschiedener Typen, aber derselben Domäne (Recht) nahe beieinander eingebettet werden, was die Unterscheidungsfähigkeit verringert.

Für die Disambiguierung von Entitätstypen bewahren **generalistische Embeddings** die semantischen Grenzen zwischen PERSON, ORGANIZATION, DATE usw. besser, da sie nicht auf eine bestimmte Domäne „kollabiert“ sind.

**Abschließende Empfehlung**: Validierer mit `intfloat/multilingual-e5-large` implementieren und empirisch bewerten, bevor juristische Alternativen in Betracht gezogen werden.

---

## 8. Nächste Schritte

1.  [ ] Herunterladen von `intfloat/multilingual-e5-large` (~1.1GB)
2.  [ ] Erstellen eines Datasets mit Beispielen pro Typ (PERSON_NAME, ORGANIZATION, DATE, LOCATION) mit juristischem Kontext
3.  [ ] Berechnen von Zentroiden für jeden Typ
4.  [ ] Implementieren von `EntityTypeValidator` mit konfigurierbaren Schwellenwerten
5.  [ ] Bewerten im Adversarial Test (35 Tests)
6.  [ ] (Optional) Vergleichen vs `Legal-Embed`, um Hypothese der False Positives zu bestätigen
7.  [ ] Dokumentieren der Ergebnisse und finale Entscheidung

---

## Verwandte Dokumente

| Dokument | Beziehung |
| :--- | :--- |
| `ml/docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md` | Vorherige Forschung, vorgeschlagene Architektur |
| `ml/docs/reports/2026-02-07_embeddings_roadmap_document_classification.md` | Embeddings-Roadmap, Aktivierungskriterien |
| `ml/docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | Aktuelle Pipeline, Baseline-Metriken |
| `auditoria.md` | Identifizierte Klassifizierungsfehler |
| `ml/models/type_centroids.json` | Vorhandene Zentroide (erfordert Überprüfung des verwendeten Modells) |

---

## Referenzen

1.  **FinMTEB**: Li et al. (2024). "Do we need domain-specific embedding models? An empirical investigation." arXiv:2409.18511. https://arxiv.org/abs/2409.18511
2.  **Geometry of Fine-tuning**: Merchant et al. (2020). "What Happens To BERT Embeddings During Fine-tuning?" ACL Findings 2021. https://aclanthology.org/2021.findings-emnlp.261.pdf
3.  **Anisotropy**: Ethayarajh (2019). "How Contextual are Contextualized Word Representations?" EMNLP 2019. Rajaee & Pilehvar (2022). "Is Anisotropy Really the Cause?" EMNLP Findings 2022. https://aclanthology.org/2022.findings-emnlp.314.pdf
4.  **Catastrophic Forgetting in NER**: Wang et al. (2023). "Continual Named Entity Recognition without Catastrophic Forgetting." arXiv:2310.14541. https://arxiv.org/abs/2310.14541
5.  **DES-MoE**: Yang et al. (2025). "Dynamic Expert Specialization: Catastrophic Forgetting-Free Multi-Domain MoE." EMNLP 2025. https://aclanthology.org/2025.emnlp-main.932.pdf
6.  **NER Retriever**: Zhang et al. (2025). "NER Retriever: Zero-Shot NER with Type-Aware Embeddings." arXiv:2509.04011. https://arxiv.org/abs/2509.04011
7.  **CEPTNER**: Wang et al. (2024). "Contrastive learning Enhanced Prototypical network for Few-shot NER." Knowledge-Based Systems. https://doi.org/10.1016/j.knosys.2024.111512
8.  **ReProCon**: Liu et al. (2025). "ReProCon: Scalable Few-Shot Biomedical NER." arXiv:2508.16833. https://arxiv.org/abs/2508.16833
9.  **Multilingual E5**: Wang et al. (2024). "Multilingual E5 Text Embeddings." arXiv:2402.05672. https://huggingface.co/intfloat/multilingual-e5-large
10. **voyage-law-2**: Voyage AI (2024). "Domain-Specific Embeddings: Legal Edition." https://blog.voyageai.com/2024/04/15/domain-specific-embeddings-and-retrieval-legal-edition-voyage-law-2/
11. **Fine-tuning Trade-offs**: Weaviate (2024). "Why, When and How to Fine-Tune a Custom Embedding Model." https://weaviate.io/blog/fine-tune-embedding-model
12. **Intent Classification with Centroids**: Puig (2024). "Mastering Intent Classification with Embeddings." Medium. https://medium.com/@mpuig/mastering-intent-classification-with-embeddings-centroids-neural-networks-and-random-forests-3fe7c57ca54c

---

```
Version: 1.0.0
Autor: AlexAlves87
Forschungszeit: ~25 Min
Such-Token: 12 Anfragen
```
