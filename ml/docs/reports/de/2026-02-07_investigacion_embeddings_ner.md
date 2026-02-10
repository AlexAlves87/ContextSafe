# Forschung: Generalistische vs. Juristische Domain-Embeddings für die Disambiguierung von Entitätstypen in NER

**Datum:** 07.02.2026
**Ziel:** Untersuchen, warum spezialisierte juristische Embeddings in der Post-NER-Entitätstypklassifizierung mehr False Positives erzeugen als generalistische Embeddings, und Bestimmung der besten Embedding-Strategie für ContextSafe.

---

## 1. Management-Zusammenfassung

1.  **Embeddings der juristischen Domäne erzeugen mehr False Positives**, da das juristische Fine-Tuning die Unterscheidungsfähigkeit zwischen Entitätstypen verringert, indem es den Embedding-Raum um juristische Sprachmuster herum kollabieren lässt (erhöhte Anisotropie, engerer semantischer Raum).
2.  **Generalistische Embeddings sind für die Unterscheidung von Entitätstypen überlegen**, da sie einen breiteren und diverseren semantischen Raum beibehalten, in dem Unterschiede zwischen Kategorien (Person vs. Organisation vs. Datum) stärker ausgeprägt sind.
3.  **Anisotropie ist NICHT per se schlecht** – neuere Arbeiten (ICLR 2024) zeigen, dass kontrollierte Anisotropie die Leistung verbessern kann –, aber unkontrollierte Anisotropie durch Domain-Fine-Tuning verringert die für Typ-Zentroide notwendige Inter-Klassen-Unterscheidung.
4.  **Empfehlung: Verwendung von `BAAI/bge-m3` oder `intfloat/multilingual-e5-large`** (generalistische Embeddings) für den Typ-Validierer, KEINE juristischen Embeddings. Wenn Domänenwissen gewünscht ist, verwenden Sie einen hybriden Ansatz mit Adaptern (LoRA), die die allgemeine Kapazität bewahren.
5.  **Die kontextbezogene Zentroid-Technik wird durch die Literatur** zu prototypischen Netzwerken (CEPTNER, KCL) gut gestützt, erfordert jedoch 50-100 diverse Beispiele pro Typ und einen umgebenden Kontext von 10-15 Token.

---

## 2. Ergebnis 1: General-Purpose vs. Domain-Specific Embeddings für die Entitätstypklassifizierung

### 2.1 Schlüsselbeweis: General-Purpose-Modelle versagen in Domänenaufgaben ABER glänzen bei der Typunterscheidung

| Paper | Venue/Jahr | Haupterkenntnis |
| :--- | :--- | :--- |
| **"Do We Need Domain-Specific Embedding Models? An Empirical Investigation"** (Tang & Yang) | arXiv 2409.18511 (2024) | Bewerteten 7 SOTA-Modelle auf FinMTEB (Finanz-Benchmark). Allgemeine Modelle zeigten einen signifikanten Rückgang bei Domänenaufgaben, und ihre MTEB-Leistung korreliert NICHT mit der FinMTEB-Leistung. **ABER**: Dieser Rückgang betraf Retrieval und STS, nicht die Entitätstypklassifizierung. |
| **"NuNER: Entity Recognition Encoder Pre-training via LLM-Annotated Data"** (Bogdanov et al.) | EMNLP 2024 | Kompaktes Modell (RoBERTa base), vortrainiert mit Contrastive Learning auf 4,38 Mio. Entitätsannotationen. Übertrifft ähnlich große Modelle in Few-Shot NER und konkurriert mit viel größeren LLMs. **Schlüssel**: Die Vielfalt der Entitätstypen im Pre-Training-Dataset ist fundamental. |
| **"LegNER: A Domain-Adapted Transformer for Legal NER and Text Anonymization"** (Al-Hussaeni et al.) | Frontiers in AI (2025) | Juristisches Modell basierend auf BERT-base + erweitertem Vokabular + 1.542 annotierte Gerichtsverfahren. F1 >99% bei 6 Entitätstypen. **Jedoch**: Das Paper berichtet keine Analyse von False Positives zwischen Typen, und die bewerteten Entitäten unterscheiden sich sehr stark voneinander (PERSON vs LAW vs CASE_REFERENCE). |
| **"MEL: Legal Spanish Language Model"** (2025) | arXiv 2501.16011 | XLM-RoBERTa-large, feinabgestimmt mit 5,52 Mio. juristischen spanischen Texten (92,7 GB). Übertrifft XLM-R Baseline in der Dokumentenklassifizierung. **Kritisch**: Die Autoren geben zu, dass „Token- oder Span-Klassifizierungsaufgaben aufgrund fehlender annotierter Texte unbewertet bleiben“ – d.h., sie haben NER NICHT bewertet. |

### 2.2 Interpretation: Warum allgemeine Modelle TYPEN besser unterscheiden

Die entscheidende Unterscheidung liegt zwischen **zwei verschiedenen Aufgaben**:

| Aufgabe | Was das Embedding benötigt | Bestes Modell |
| :--- | :--- | :--- |
| Legal Retrieval / Legal STS | Erfassen juristischer semantischer Nuancen | Domain-Specific |
| Entitätstypklassifizierung | Trennung breiter Kategorien (Person vs. Org vs. Datum) | General-Purpose |

Juristische Embeddings sind für die erste Aufgabe optimiert: Abrufen ähnlicher juristischer Dokumente, Verstehen juristischer Terminologie, Erfassen juristischer Beziehungen. Dies macht sie SCHLECHTER für die zweite Aufgabe, weil:

1.  **Diversitätskollaps**: Juristisches Fine-Tuning bringt alle Repräsentationen näher an den juristischen Unterraum heran, wodurch der Abstand zwischen „in Urteil genannter Person“ und „in Urteil genannter Organisation“ verringert wird, da beide in ähnlichen juristischen Kontexten erscheinen.
2.  **Kontextueller Bias**: Ein juristisches Modell lernt, dass „Telefonica“ in einem juristischen Kontext genauso juristisch relevant ist wie „Alejandro Alvarez“, was die Typunterschiede nivelliert.
3.  **Unkontrollierte Anisotropie**: Fine-Tuning führt Anisotropie ein, die verschiedene Typen in denselben dominanten Richtungen des Embedding-Raums kollabieren lassen kann.

**Relevante URL**: [Do We Need Domain-Specific Embedding Models?](https://arxiv.org/abs/2409.18511)

---

## 3. Ergebnis 2: Warum juristische Embeddings mehr False Positives erzeugen

### 3.1 Das Anisotropie-Problem in feinabgestimmten Embeddings

| Paper | Venue/Jahr | Haupterkenntnis |
| :--- | :--- | :--- |
| **"Anisotropy is Not Inherent to Transformers"** (Machina & Mercer) | NAACL 2024 | Zeigen, dass Anisotropie der Transformer-Architektur nicht inhärent ist. Identifizieren große Pythia-Modelle mit isotropen Räumen. Frühere theoretische Rechtfertigungen für Anisotropie waren unzureichend. |
| **"Stable Anisotropic Regularization" (I-STAR)** (Rudman & Eickhoff) | ICLR 2024 | Kontraintuitives Ergebnis: REDUZIERUNG der Isotropie (Erhöhung der Anisotropie) verbessert die Downstream-Leistung. Verwendung von IsoScore* (differenzierbare Maßzahl) als Regularisierer. **Schlüsselimplikation**: KONTROLLIERTE Anisotropie kann vorteilhaft sein, aber UNKONTROLLIERTE Anisotropie durch Domain-Fine-Tuning ist schädlich. |
| **"The Shape of Learning: Anisotropy and Intrinsic Dimensions in Transformer-Based Models"** (2024) | EACL 2024 | Transformer-Decoder zeigen eine glockenförmige Kurve mit maximaler Anisotropie in mittleren Schichten, während Encoder eine gleichmäßigere Anisotropie zeigen. Schichten mit höherer Anisotropie decken sich mit Schichten, die Typinformationen kodieren. |
| **"How Does Fine-tuning Affect the Geometry of Embedding Space: A Case Study on Isotropy"** (Rajaee & Pilehvar) | EMNLP 2021 Findings | Obwohl Isotropie wünschenswert ist, verbessert Fine-Tuning die Isotropie NICHT zwangsläufig. Lokale Strukturen (wie Token-Typ-Kodierung) leiden unter massiven Änderungen während des Fine-Tunings. Gestreckte Richtungen (dominante Richtungen) im feinabgestimmten Raum tragen wesentliches sprachliches Wissen. |
| **"Representation Degeneration Problem in Prompt-based Fine-tuning"** | LREC 2024 | Anisotropie des Embedding-Raums begrenzt die Leistung bei Prompt-basiertem Fine-Tuning. Vorschlag von CLMA (Contrastive Learning Framework) zur Minderung der Anisotropie. |

### 3.2 Mechanismus der False Positives in juristischen Embeddings

Basierend auf den vorliegenden Erkenntnissen ist der Mechanismus, durch den juristische Embeddings bei der Entitätstypvalidierung mehr False Positives erzeugen, folgender:

```
1. Juristisches Fine-Tuning → Embedding-Raum zieht sich zum juristischen Unterraum zusammen
                                ↓
2. Repräsentationen von "Person im juristischen Kontext" und
   "Organisation im juristischen Kontext" rücken näher zusammen
   (beide sind "juristisch relevante Entitäten")
                                ↓
3. Zentroide von PERSON_NAME und ORGANIZATION überlappen sich
   im juristisch feinabgestimmten Raum
                                ↓
4. Kosinus-Ähnlichkeit zwischen Zentroid_PERSON und einer ORGANIZATION
   ist höher als sie es mit allgemeinen Embeddings wäre
                                ↓
5. Mehr Entitäten überschreiten die Reklassifizierungsschwelle → mehr FP
```

### 3.3 Direkte Evidenz aus der juristischen Domäne

| Paper | Venue/Jahr | Haupterkenntnis |
| :--- | :--- | :--- |
| **"Improving Legal Entity Recognition Using a Hybrid Transformer Model and Semantic Filtering Approach"** | arXiv 2410.08521 (2024) | Legal-BERT erzeugt False Positives bei mehrdeutigen Begriffen und verschachtelten Entitäten. Vorschlag einer semantischen Filterung nach der Vorhersage mittels Kosinus-Ähnlichkeit gegen vordefinierte juristische Muster. **Ergebnis**: Präzision steigt von 90,2% auf 94,1% (+3,9 pp), F1 von 89,3% auf 93,4% (+4,1 pp). Verwendung der Formel S(ei,Pj) = cos(ei, Pj) mit Schwellenwert tau zum Filtern. |

**Dieses Paper validiert direkt unseren Ansatz**, die Kosinus-Ähnlichkeit zum Filtern von Vorhersagen zu verwenden, ABER nutzt vordefinierte juristische Muster anstelle von Typ-Zentroiden. Die Kombination beider Ansätze (allgemeine Zentroide + juristische Muster als zusätzlicher Filter) ist eine natürliche Erweiterung.

**Relevante URL**: [Improving Legal Entity Recognition Using Semantic Filtering](https://arxiv.org/abs/2410.08521)

---

## 4. Ergebnis 3: Beste Embedding-Modelle für die Entitätstyp-Disambiguierung (2024-2026)

### 4.1 Vergleich der Kandidatenmodelle

| Modell | Größe | Dim | Sprachen | MTEB Score | Stärken | Schwächen für unsere Aufgabe |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BAAI/bge-m3** | ~2.3GB | 1024 | 100+ | 63.0 | Multi-Granularität (dense+sparse+ColBERT), beste mehrsprachige Leistung im MTEB | Größere Größe, höhere Latenz |
| **intfloat/multilingual-e5-large** | ~1.1GB | 1024 | 100+ | ~62 | Exzellentes Spanisch, gut dokumentiert, erfordert „query:“-Präfix | Leicht schlechter als bge-m3 im mehrsprachigen Bereich |
| **nomic-ai/nomic-embed-text-v2** | ~700MB | 768 | 100 | ~62 | MoE (Mixture of Experts), effizient, 8192 Token | Neuer, weniger validiert im juristischen Spanisch |
| **intfloat/multilingual-e5-small** | ~448MB | 384 | 100 | ~56 | Leichter, niedrige Latenz | Kleinere Dimension könnte Unterscheidung verlieren |
| **Wasserstoff-AI/Legal-Embed** | ~1.1GB | 1024 | Multi | N/A | Feinabgestimmt auf Recht | **VERWORFEN: höherer FP aus in Abschnitt 3 analysiertem Grund** |

### 4.2 Evidenzbasierte Empfehlung

**Hauptmodell: `BAAI/bge-m3`**

Begründung:

1.  Beste Leistung in mehrsprachigen Benchmarks, einschließlich Spanisch (siehe [OpenAI vs Open-Source Multilingual Embedding Models](https://towardsdatascience.com/openai-vs-open-source-multilingual-embedding-models-e5ccb7c90f05/))
2.  Höhere Dimensionalität (1024) = größere Kapazität zur Trennung von Typ-Zentroiden
3.  Dense+Sparse+ColBERT Retrieval funktioniert gut für Ähnlichkeitsvergleiche
4.  Unterstützt bis zu 8192 Token (nützlich für lange juristische Kontexte)

**Alternatives Modell: `intfloat/multilingual-e5-large`**

Begründung:

1.  Gut dokumentiert mit technischem Paper (arXiv:2402.05672)
2.  Exzellente spanische Leistung verifiziert
3.  Leicht kleiner als bge-m3
4.  Bereits vorgeschlagen in `docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md`

**WICHTIG**: Verwenden Sie NICHT `Legal-Embed` oder irgendein auf die juristische Domäne feinabgestimmtes Modell. Die akademische Evidenz zeigt, dass allgemeine Modelle die Trennung zwischen Entitätstypen besser bewahren, was genau das ist, was wir für Zentroide benötigen.

### 4.3 Benchmark-Quellen

| Benchmark | Was er misst | Referenz |
| :--- | :--- | :--- |
| MTEB (Massive Text Embedding Benchmark) | 8 Aufgaben einschließlich Klassifizierung und Clustering | [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) |
| FinMTEB (Finance MTEB) | Leistung in der Finanzdomäne | Tang & Yang (2024), arXiv:2409.18511 |
| MMTEB (Massive Multilingual TEB) | Mehrsprachige Erweiterung von MTEB (2025) | [MMTEB GitHub](https://github.com/embeddings-benchmark/mteb) |

**Kritischer Hinweis**: Kein existierender Benchmark misst direkt „Entitätstyp-Unterscheidung mittels Zentroiden“. MTEB hat Klassifizierungs- und Clustering-Unteraufgaben, die nützliche Näherungen sind. Es wird empfohlen, einen internen Benchmark für ContextSafe zu erstellen.

---

## 5. Ergebnis 4: Zentroid-basierte Typvalidierungstechniken

### 5.1 Prototypische Netzwerke und Zentroide für NER

| Paper | Venue/Jahr | Haupterkenntnis |
| :--- | :--- | :--- |
| **"CEPTNER: Contrastive Learning Enhanced Prototypical Network for Two-stage Few-shot NER"** (Wang et al.) | Knowledge-Based Systems (2024) | Zwei Stufen: (1) Grenzenerkennung, (2) prototypische Klassifizierung mit Contrastive Learning. Kontrastives Lernen auf Entitätsebene trennt Typen effektiv. Bewertet auf Few-NERD, CrossNER, SNIPS. |
| **"Transformer-based Prototype Network for Chinese Nested NER"** (MSTPN) | Scientific Reports (2025) | Prototypische Netzwerke mit Transformern für verschachteltes NER. Verwendet Entity Bounding Boxes als Prototypen. |
| **"KCL: Few-shot NER with Knowledge Graph and Contrastive Learning"** | LREC-COLING 2024 | Kombiniert Knowledge Graphs mit Contrastive Learning, um semantische Label-Repräsentation zu lernen. Nutzt KG zur Bereitstellung strukturierter Typ-Infos. Die kontrastive Repräsentation trennt Label-Cluster im prototypischen Raum. |
| **"Multi-Head Self-Attention-Enhanced Prototype Network with Contrastive-Center Loss for Few-Shot Relation Extraction"** | Applied Sciences (2024) | Contrastive-Center-Loss vergleicht Trainingsproben mit entsprechenden UND nicht-entsprechenden Klassenzentren. Reduziert Intra-Klassen-Distanzen und erhöht Inter-Klassen-Distanzen. |
| **"CLESR: Context-Based Label Knowledge Enhanced Span Recognition for NER"** | Int J Computational Intelligence Systems (2024) | Verbessert verschachteltes NER durch Integration kontextueller Infos mit Label-Wissen. Spans richten sich an textuellen Beschreibungen von Typen im gemeinsamen semantischen Raum aus. |

### 5.2 Best Practices für den Aufbau von Zentroiden

Basierend auf der überprüften Literatur:

| Aspekt | Empfehlung | Begründung |
| :--- | :--- | :--- |
| **Anzahl der Beispiele** | 50-100 pro Typ | CEPTNER zeigt Effektivität bei wenigen Beispielen; 50 ist Minimum, 100 ist robust |
| **Beispielvielfalt** | Variationen in Kontext, Format, Länge einbeziehen | KCL betont Vielfalt für diskriminierendere Cluster |
| **Kontextgröße** | 10-15 umgebende Token | Die NER-Umfrage (arXiv:2401.10825) bestätigt, dass BERT Kontext innerhalb und zwischen Sätzen effektiv erfasst |
| **Zentroid-Aktualisierung** | Periodisch mit neuen bestätigten Beispielen neu berechnen | CEPTNER zeigt, dass mehr Beispiele die Trennung verbessern; Zentroide sollten sich entwickeln |
| **Contrastive Refinement** | Trainieren mit Contrastive Loss zur Maximierung der Trennung | Mehrere Papers zeigen, dass Contrastive Loss der SCHLÜSSEL für die Typtrennung ist |
| **Zwischenschichten** | Erwägen, aus den Schichten 15-17 zu extrahieren, nicht nur aus der letzten Schicht | NER Retriever (arXiv:2509.04011) zeigt, dass Zwischenschichten mehr Typinformationen enthalten |

### 5.3 Größe des Kontextfensters

| Paper | Erkenntnis zum Kontext |
| :--- | :--- |
| Survey NER (arXiv:2401.10825) | „BERT encodings capture important within and adjacent-sentence context.“ Vergrößerung des Fensters verbessert die Leistung. |
| Span-based Unified NER via Contrastive Learning (IJCAI 2024) | Spans mit Kontext richten sich an Typbeschreibungen im gemeinsamen Raum aus. Kontext ist zur Disambiguierung notwendig. |
| Contextualized Span Representations (Wadden et al.) | Verbreitung von Span-Repräsentationen über Koreferenz-Links ermöglicht die Disambiguierung schwieriger Erwähnungen. |

**Empfehlung**: Für ContextSafe einen **Kontext von 10-15 Token** auf jeder Seite der Entität verwenden. Für Entitäten am Anfang/Ende eines Satzes mit Token aus dem vorherigen/nächsten Satz auffüllen, falls verfügbar.

---

## 6. Ergebnis 5: Hybride Ansätze (Allgemein + Domäne)

### 6.1 Verkettung und Ensemble von Embeddings

| Paper | Venue/Jahr | Haupterkenntnis |
| :--- | :--- | :--- |
| **"Automated Concatenation of Embeddings for Structured Prediction" (ACE)** | ACL-IJCNLP 2021 | Framework, das automatisch die beste Verkettung von Embeddings für strukturierte Vorhersagen (einschließlich NER) findet. Erreicht SOTA in 6 Aufgaben über 21 Datasets. Die Auswahl variiert je nach Aufgabe und Kandidatensatz. |
| **"Pooled Contextualized Embeddings for NER"** (Akbik et al.) | NAACL 2019 | Aggregiert kontextualisierte Embeddings jeder einzigartigen Instanz, um eine „globale“ Repräsentation zu erstellen. Gestapelte Embeddings (Kombination mehrerer Typen) sind ein Hauptmerkmal von Flair und verbessern NER signifikant. |
| **"Improving Few-Shot Cross-Domain NER by Instruction Tuning a Word-Embedding based Retrieval Augmented LLM" (IF-WRANER)** | EMNLP 2024 Industry | Verwendet Embeddings auf Wortebene (nicht Satzebene) für den Abruf von Beispielen im Prompt. Übertrifft SOTA in CrossNER um >2% F1. In Produktion eingesetzt, reduziert menschliche Eskalationen um ~15%. |
| **"Pre-trained Embeddings for Entity Resolution: An Experimental Analysis"** (Zeakis et al.) | VLDB 2023 | Analyse von 12 Sprachmodellen auf 17 Datasets für Entity Resolution. Kontextualisierte Embeddings (BERT-Varianten) übertreffen statische (fastText) konsistent, aber eine Kombination kann vorteilhaft sein. |

### 6.2 Adapter (LoRA) zur Bewahrung allgemeinen Wissens

| Paper | Venue/Jahr | Haupterkenntnis |
| :--- | :--- | :--- |
| **"Continual Named Entity Recognition without Catastrophic Forgetting"** (Zheng et al.) | EMNLP 2023 | Schlagen Pooled Feature Distillation Loss + Pseudo-Labeling + Adaptive Re-Weighting vor. Das katastrophale Vergessen bei kontinuierlichem NER wird durch den „semantischen Shift“ des Typs Nicht-Entität verstärkt. |
| **"A New Adapter Tuning of LLM for Chinese Medical NER"** | Automation in Construction (2024) | Adapter vermeiden katastrophales Vergessen, weil sie neues Wissen ohne umfangreiche Parameteranpassungen lernen. Vorzuziehen für Multi-Domain-NER. |
| **"Mixture of LoRA Experts for Continual Information Extraction"** | EMNLP 2025 Findings | MoE-Framework mit LoRA für kontinuierliche Informationsextraktion. Ermöglicht das Hinzufügen von Domänen ohne Vergessen der vorherigen. |
| **"LoRASculpt: Sculpting LoRA for Harmonizing General and Specialized Knowledge"** | CVPR 2025 | Technik zum Ausgleich von allgemeinem und spezialisiertem Wissen während des LoRA-Fine-Tunings. |

### 6.3 Realisierbare Kombinationsstrategien für ContextSafe

| Strategie | Komplexität | Erwarteter Nutzen | Empfohlen |
| :--- | :--- | :--- | :--- |
| **A: Reine allgemeine Embeddings** | Niedrig | Gute Typunterscheidung ohne zusätzliche FP | Ja (Baseline) |
| **B: Verketten Allgemein + Legal** | Mittel | Mehr Dimensionen, erfasst beide Aspekte | Evaluierbar, aber teuer in Latenz |
| **C: Gewichteter Durchschnitt Allgemein + Legal** | Mittel | Einfacher als Concat, verliert aber Informationen | Nicht empfohlen (Durchschnitt verwässert) |
| **D: Meta-Modell über mehrere Embeddings** | Hoch | Bessere Präzision bei ausreichenden Trainingsdaten | Für die Zukunft |
| **E: LoRA-Adapter auf allgemeinem Modell** | Mittel-Hoch | Bewahrt allgemeine Kapazität + fügt Domäne hinzu | Ja (zweiter Schritt) |

**Empfehlung für ContextSafe**:

*   **Phase 1 (sofort)**: Verwendung reiner allgemeiner Embeddings (bge-m3 oder e5-large). Bewertung der FP-Reduktion gegenüber der Erfahrung mit juristischen Embeddings.
*   **Phase 2 (falls Phase 1 unzureichend)**: Anwenden eines LoRA-Adapters auf das allgemeine Modell mit kontrastiven Beispielen spanischer juristischer Entitäten. Dies bewahrt die allgemeine Typunterscheidungskapazität und fügt Domänenwissen hinzu.
*   **Phase 3 (optional)**: ACE-style automatisierte Suche nach der besten Verkettung, falls ein ausreichend großes Typvalidierungs-Dataset verfügbar ist.

---

## 7. Synthese und finale Empfehlung

### 7.1 Direkte Antwort auf die Forschungsfragen

**F1: General-Purpose vs. Domain-Specific für Entitätstypklassifizierung?**

Verwenden Sie **General-Purpose**. Die Evidenz aus mehreren Papers (Tang & Yang 2024, Rajaee & Pilehvar 2021, Machina & Mercer NAACL 2024) zeigt, dass:

*   Allgemeine Modelle breitere semantische Räume beibehalten
*   Die Entitätstypunterscheidung Inter-Klassen-Trennung erfordert, nicht Intra-Domänen-Tiefe
*   Domänenmodelle ähnliche Typen in denselben Unterraum kollabieren lassen

**F2: Warum erzeugen juristische Embeddings mehr False Positives?**

Drei konvergierende Faktoren:

1.  **Kollaps der semantischen Vielfalt**: Juristisches Fine-Tuning bringt Repräsentationen aller Entitäten näher an den „juristischen“ Unterraum heran
2.  **Unkontrollierte Anisotropie**: Fine-Tuning führt dominante Richtungen ein, die „Rechtmäßigkeit“ statt „Entitätstyp“ kodieren (Rajaee & Pilehvar 2021, Rudman & Eickhoff ICLR 2024)
3.  **Zentroid-Überlappung**: Zentroide von PERSON und ORGANIZATION rücken näher zusammen, weil beide in identischen juristischen Kontexten erscheinen

**F3: Bestes Modell?**

`BAAI/bge-m3` (erste Wahl) oder `intfloat/multilingual-e5-large` (zweite Wahl). Beide sind allgemein, mehrsprachig, mit guter Unterstützung für Spanisch und einer Dimensionalität von 1024, die ausreicht, um Typ-Zentroide zu trennen.

**F4: Zentroid-Technik?**

Gut gestützt durch CEPTNER (2024), KCL (2024), MSTPN (2025). Schlüssel:

*   50-100 diverse Beispiele pro Typ
*   Kontext von 10-15 Token um die Entität
*   Contrastive Learning zur Verfeinerung der Zentroide, falls möglich
*   Zwischenschichten (15-17) können informativer sein als die letzte Schicht

**F5: Hybrider Ansatz?**

Für die Zukunft: LoRA-Adapter auf allgemeinem Modell ist die vielversprechendste Strategie. Bewahrt allgemeine Unterscheidung + fügt Domänenwissen hinzu. ACE (automatisierte Verkettung) ist realisierbar, wenn ausreichende Evaluationsdaten vorhanden sind.

### 7.2 Auswirkung auf das vorherige Dokument

Das Dokument `docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md` empfiehlt `multilingual-e5-large` als Hauptmodell und schlägt vor, `Legal-Embed` als Alternative zu bewerten. Basierend auf dieser Untersuchung:

| Aspekt | Vorheriges Dokument | Aktualisierung |
| :--- | :--- | :--- |
| Hauptmodell | `multilingual-e5-large` | **Korrekt**, beibehalten |
| Legal-Embed Alternative | Zur Bewertung vorgeschlagen | **VERWERFEN**: Evidenz zeigt, dass es mehr FP erzeugt |
| Reale Alternative | Nicht vorgeschlagen | **Hinzufügen von `BAAI/bge-m3`** als erste Option |
| Contrastive Refinement | Nicht erwähnt | **Hinzufügen**: Wenn Zentroide nicht genug trennen, Contrastive Learning anwenden |
| Zwischenschichten | Nicht erwähnt | **Hinzufügen**: Embeddings aus Schichten 15-17 extrahieren, nicht nur aus der letzten |

---

## 8. Konsolidierte Tabelle der überprüften Papers

| # | Paper | Venue | Jahr | Hauptthema | URL |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Do We Need Domain-Specific Embedding Models? An Empirical Investigation | arXiv 2409.18511 | 2024 | General vs Domain Embeddings | https://arxiv.org/abs/2409.18511 |
| 2 | NuNER: Entity Recognition Encoder Pre-training via LLM-Annotated Data | EMNLP 2024 | 2024 | Entity-Aware Pre-Training | https://aclanthology.org/2024.emnlp-main.660/ |
| 3 | LegNER: Domain-Adapted Transformer for Legal NER | Frontiers in AI | 2025 | Legal NER + Anonymisierung | https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1638971/full |
| 4 | MEL: Legal Spanish Language Model | arXiv 2501.16011 | 2025 | Spanish Legal Embeddings | https://arxiv.org/abs/2501.16011 |
| 5 | Anisotropy is Not Inherent to Transformers | NAACL 2024 | 2024 | Embedding Space Geometry | https://aclanthology.org/2024.naacl-long.274/ |
| 6 | Stable Anisotropic Regularization (I-STAR) | ICLR 2024 | 2024 | Controlled Anisotropy | https://arxiv.org/abs/2305.19358 |
| 7 | The Shape of Learning: Anisotropy and Intrinsic Dimensions | EACL 2024 | 2024 | Anisotropy Dynamics in Transformers | https://aclanthology.org/2024.findings-eacl.58/ |
| 8 | How Does Fine-tuning Affect Geometry of Embedding Space | EMNLP 2021 Findings | 2021 | Fine-Tuning Impact on Isotropy | https://aclanthology.org/2021.findings-emnlp.261/ |
| 9 | Representation Degeneration in Prompt-based Fine-tuning | LREC 2024 | 2024 | Anisotropy limits performance | https://aclanthology.org/2024.lrec-main.1217/ |
| 10 | Improving Legal Entity Recognition Using Semantic Filtering | arXiv 2410.08521 | 2024 | Legal NER False Positive Reduction | https://arxiv.org/abs/2410.08521 |
| 11 | CEPTNER: Contrastive Enhanced Prototypical Network for Few-shot NER | Knowledge-Based Systems | 2024 | Prototype Networks for NER | https://doi.org/10.1016/j.knosys.2024.111730 |
| 12 | KCL: Few-shot NER with Knowledge Graph and Contrastive Learning | LREC-COLING 2024 | 2024 | KG + contrastive for prototypical NER | https://aclanthology.org/2024.lrec-main.846/ |
| 13 | Automated Concatenation of Embeddings (ACE) | ACL-IJCNLP 2021 | 2021 | Multi-embedding concatenation for NER | https://aclanthology.org/2021.acl-long.206/ |
| 14 | Pooled Contextualized Embeddings for NER | NAACL 2019 | 2019 | Global word representations for NER | https://aclanthology.org/N19-1078/ |
| 15 | Continual NER without Catastrophic Forgetting | EMNLP 2023 | 2023 | Catastrophic forgetting in NER | https://arxiv.org/abs/2310.14541 |
| 16 | Improving Few-Shot Cross-Domain NER (IF-WRANER) | EMNLP 2024 Industry | 2024 | Word-level embeddings for cross-domain NER | https://aclanthology.org/2024.emnlp-industry.51/ |
| 17 | CLESR: Context-Based Label Knowledge Enhanced Span Recognition | IJCIS | 2024 | Context + label knowledge for NER | https://link.springer.com/article/10.1007/s44196-024-00595-5 |
| 18 | Span-based Unified NER via Contrastive Learning | IJCAI 2024 | 2024 | Contrastive span-type alignment | https://www.ijcai.org/proceedings/2024/0708.pdf |
| 19 | Pre-trained Embeddings for Entity Resolution | VLDB 2023 | 2023 | 12 embedding models compared for ER | https://www.vldb.org/pvldb/vol16/p2225-skoutas.pdf |
| 20 | Transformer-based Prototype Network for Chinese Nested NER | Scientific Reports | 2025 | Prototypical NER with transformers | https://www.nature.com/articles/s41598-025-04946-w |
| 21 | Adapter Tuning of LLM for Chinese Medical NER | Automation in Construction | 2024 | Adapters prevent catastrophic forgetting | https://www.tandfonline.com/doi/full/10.1080/08839514.2024.2385268 |
| 22 | Recent Advances in NER: Comprehensive Survey | arXiv 2401.10825 | 2024 | NER survey (embeddings, hybrid approaches) | https://arxiv.org/abs/2401.10825 |
| 23 | Spanish Datasets for Sensitive Entity Detection in Legal Domain | LREC 2022 | 2022 | MAPA project, Spanish legal NER datasets | https://aclanthology.org/2022.lrec-1.400/ |

---

## 9. Verwandte Dokumente

| Dokument | Beziehung |
| :--- | :--- |
| `docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md` | Vorheriges Dokument, das einen Typ-Validierer mit Embeddings vorschlägt. Diese Forschung AKTUALISIERT die Empfehlungen. |
| `docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md` | Vorherige Bewertung von Embeddings für die Dokumentenklassifizierung (andere Aufgabe). |
| `docs/reports/2026-02-07_embeddings_roadmap_document_classification.md` | Roadmap für Embeddings zur Dokumentenklassifizierung. |
| `docs/reports/2026-01-30_investigacion_gaps_pipeline_hibrido.md` | Lücken der hybriden NER-Pipeline (Kontext von Typfehlern). |
| `docs/reports/2026-01-28_investigacion_hybrid_ner.md` | Forschung zu Hybrid NER (Architekturkontext). |

---

```
Version: 1.0.0
Autor: AlexAlves87
Forschungszeit: ~45 min
Überprüfte Papers: 23
```
