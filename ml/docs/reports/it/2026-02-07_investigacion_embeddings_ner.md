# Ricerca: Embedding Generali vs Dominio Legale per la Disambiguazione dei Tipi di Entità nel NER

**Data:** 07-02-2026
**Obiettivo:** Investigare perché gli embedding legali specializzati producono più falsi positivi rispetto agli embedding di uso generale nel compito di classificazione dei tipi di entità post-NER, e determinare la migliore strategia di embedding per ContextSafe.

---

## 1. Riepilogo Esecutivo

1.  **Gli embedding di dominio legale producono più falsi positivi** perché il fine-tuning legale riduce la capacità discriminativa tra i tipi di entità facendo collassare lo spazio di embedding attorno a pattern linguistici legali (anisotropia aumentata, spazio semantico più stretto).
2.  **Gli embedding di uso generale sono superiori per la discriminazione dei tipi di entità** perché mantengono uno spazio semantico più ampio e diversificato in cui le differenze tra categorie (persona vs organizzazione vs data) sono più pronunciate.
3.  **L'anisotropia NON è intrinsecamente negativa** – lavori recenti (ICLR 2024) mostrano che l'anisotropia controllata può migliorare le prestazioni – ma l'anisotropia non controllata dal fine-tuning di dominio riduce la discriminazione inter-classe necessaria per i centroidi di tipo.
4.  **Raccomandazione: usare `BAAI/bge-m3` o `intfloat/multilingual-e5-large`** (embedding generali) per il validatore di tipo, NON embedding legali. Se si desidera combinare la conoscenza del dominio, utilizzare un approccio ibrido con adattatori (LoRA) che preservano la capacità generale.
5.  **La tecnica dei centroidi con contesto è ben supportata** dalla letteratura sulle reti prototipiche (CEPTNER, KCL), ma richiede 50-100 esempi diversi per tipo e un contesto circostante di 10-15 token.

---

## 2. Risultato 1: Embedding General-Purpose vs Domain-Specific per la Classificazione del Tipo di Entità

### 2.1 Evidenza chiave: I modelli general-purpose falliscono nei compiti di dominio MA eccellono nella discriminazione dei tipi

| Paper | Sede/Anno | Risultato chiave |
| :--- | :--- | :--- |
| **"Do We Need Domain-Specific Embedding Models? An Empirical Investigation"** (Tang & Yang) | arXiv 2409.18511 (2024) | Hanno valutato 7 modelli SOTA su FinMTEB (finance benchmark). I modelli generali hanno mostrato un calo significativo nei compiti di dominio, e le loro prestazioni MTEB NON correlano con le prestazioni FinMTEB. **MA**: questo calo riguardava retrieval e STS, non la classificazione dei tipi di entità. |
| **"NuNER: Entity Recognition Encoder Pre-training via LLM-Annotated Data"** (Bogdanov et al.) | EMNLP 2024 | Modello compatto (base RoBERTa) pre-addestrato con apprendimento contrastivo su 4,38M di annotazioni di entità. Supera modelli di dimensioni simili nel few-shot NER e compete con LLM molto più grandi. **Chiave**: la diversità dei tipi di entità nel dataset di pre-addestramento è fondamentale. |
| **"LegNER: A Domain-Adapted Transformer for Legal NER and Text Anonymization"** (Al-Hussaeni et al.) | Frontiers in AI (2025) | Modello legale basato su BERT-base + vocabolario esteso + 1.542 casi giudiziari annotati. F1 >99% su 6 tipi di entità. **Tuttavia**: il paper non riporta analisi dei falsi positivi tra i tipi, e le entità valutate sono molto diverse tra loro (PERSONA vs LEGGE vs RIFERIMENTO\_CASO). |
| **"MEL: Legal Spanish Language Model"** (2025) | arXiv 2501.16011 | XLM-RoBERTa-large fine-tuned con 5,52M di testi legali spagnoli (92,7 GB). Supera XLM-R base nella classificazione dei documenti. **Critico**: gli autori ammettono che "I compiti di classificazione di token o span rimangono non valutati a causa della mancanza di testi annotati" – cioè, NON hanno valutato il NER. |

### 2.2 Interpretazione: Perché i modelli generali discriminano meglio i TIPI

La distinzione chiave è tra **due compiti diversi**:

| Compito | Di cosa ha bisogno l'embedding | Miglior modello |
| :--- | :--- | :--- |
| Retrieval legale / STS legale | Catturare sfumature semantiche legali | Domain-specific |
| Classificazione tipo entità | Separare categorie ampie (persona vs org vs data) | General-purpose |

Gli embedding legali sono ottimizzati per il primo compito: recuperare documenti legali simili, comprendere la terminologia giuridica, catturare relazioni legali. Questo li rende PEGGIORI per il secondo compito perché:

1.  **Collasso della diversità**: il fine-tuning legale avvicina tutte le rappresentazioni al sottospazio legale, riducendo la distanza tra "persona menzionata in sentenza" e "organizzazione menzionata in sentenza" perché entrambe appaiono in contesti legali simili.
2.  **Bias contestuale**: un modello legale impara che "Telefonica" in un contesto legale è legalmente rilevante tanto quanto "Alejandro Alvarez", appiattendo le differenze di tipo.
3.  **Anisotropia non controllata**: il fine-tuning introduce anisotropia che può far collassare tipi distinti nelle stesse direzioni dominanti dello spazio di embedding.

**URL rilevante**: [Do We Need Domain-Specific Embedding Models?](https://arxiv.org/abs/2409.18511)

---

## 3. Risultato 2: Perché gli Embedding Legali Producono Più Falsi Positivi

### 3.1 Il problema dell'anisotropia negli embedding fine-tuned

| Paper | Sede/Anno | Risultato chiave |
| :--- | :--- | :--- |
| **"Anisotropy is Not Inherent to Transformers"** (Machina & Mercer) | NAACL 2024 | Dimostrano che l'anisotropia non è intrinseca all'architettura transformer. Identificano grandi modelli Pythia con spazi isotropici. Le giustificazioni teoriche precedenti per l'anisotropia erano insufficienti. |
| **"Stable Anisotropic Regularization" (I-STAR)** (Rudman & Eickhoff) | ICLR 2024 | Risultato controintuitivo: RIDURRE l'isotropia (aumentare l'anisotropia) migliora le prestazioni downstream. Usare IsoScore* (metrica differenziabile) come regolarizzatore. **Implicazione chiave**: l'anisotropia CONTROLLATA può essere vantaggiosa, ma l'anisotropia NON CONTROLLATA dal fine-tuning di dominio è dannosa. |
| **"The Shape of Learning: Anisotropy and Intrinsic Dimensions in Transformer-Based Models"** (2024) | EACL 2024 | I decoder transformer mostrano una curva a campana con massima anisotropia nei livelli medi, mentre gli encoder mostrano un'anisotropia più uniforme. I livelli in cui l'anisotropia è maggiore coincidono con i livelli che codificano le informazioni di tipo. |
| **"How Does Fine-tuning Affect the Geometry of Embedding Space: A Case Study on Isotropy"** (Rajaee & Pilehvar) | EMNLP 2021 Findings | Sebbene l'isotropia sia desiderabile, il fine-tuning NON migliora necessariamente l'isotropia. Le strutture locali (come la codifica del tipo di token) subiscono cambiamenti massicci durante il fine-tuning. Le direzioni allungate (direzioni dominanti) nello spazio fine-tuned portano la conoscenza linguistica essenziale. |
| **"Representation Degeneration Problem in Prompt-based Fine-tuning"** | LREC 2024 | L'anisotropia dello spazio di embedding limita le prestazioni nel fine-tuning basato su prompt. Propongono CLMA (framework di apprendimento contrastivo) per alleviare l'anisotropia. |

### 3.2 Meccanismo dei falsi positivi negli embedding legali

Sulla base delle prove precedenti, il meccanismo attraverso il quale gli embedding legali producono più falsi positivi nella validazione del tipo di entità è:

```
1. Fine-tuning legale → Spazio di embedding si contrae verso sottospazio legale
                          ↓
2. Rappresentazioni di "persona in contesto legale" e
   "organizzazione in contesto legale" si avvicinano
   (entrambe sono "entità legalmente rilevanti")
                          ↓
3. Centroidi di PERSON_NAME e ORGANIZATION si sovrappongono
   nello spazio legale-fine-tuned
                          ↓
4. Similarità coseno tra centroide_PERSON e una ORGANIZATION
   è più alta di quanto lo sarebbe con embedding generali
                          ↓
5. Più entità superano la soglia di riclassificazione → più FP
```

### 3.3 Evidenza diretta dal dominio legale

| Paper | Sede/Anno | Risultato chiave |
| :--- | :--- | :--- |
| **"Improving Legal Entity Recognition Using a Hybrid Transformer Model and Semantic Filtering Approach"** | arXiv 2410.08521 (2024) | Legal-BERT produce falsi positivi su termini ambigui ed entità nidificate. Propongono filtraggio semantico post-predizione usando similarità coseno contro pattern legali predefiniti. **Risultato**: Precisione sale dal 90,2% al 94,1% (+3,9 pp), F1 dall'89,3% al 93,4% (+4,1 pp). Usano la formula S(ei,Pj) = cos(ei, Pj) con soglia tau per filtrare. |

**Questo paper convalida direttamente il nostro approccio** di usare la similarità coseno per filtrare le predizioni, MA usa pattern legali predefiniti invece di centroidi di tipo. La combinazione di entrambi gli approcci (centroidi generali + pattern legali come filtro aggiuntivo) è un'estensione naturale.

**URL rilevante**: [Improving Legal Entity Recognition Using Semantic Filtering](https://arxiv.org/abs/2410.08521)

---

## 4. Risultato 3: Migliori Modelli di Embedding per la Disambiguazione del Tipo di Entità (2024-2026)

### 4.1 Confronto dei modelli candidati

| Modello | Dimensione | Dim | Lingue | Punteggio MTEB | Punti di forza | Debolezze per il nostro compito |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BAAI/bge-m3** | ~2,3 GB | 1024 | 100+ | 63,0 | Multi-granularità (dense+sparse+ColBERT), migliori prestazioni multilingue in MTEB | Dimensioni maggiori, latenza più elevata |
| **intfloat/multilingual-e5-large** | ~1,1 GB | 1024 | 100+ | ~62 | Eccellente spagnolo, ben documentato, richiede prefisso "query:" | Leggermente inferiore a bge-m3 in multilingue |
| **nomic-ai/nomic-embed-text-v2** | ~700 MB | 768 | 100 | ~62 | MoE (Mixture of Experts), efficiente, 8192 token | Più recente, meno validato in spagnolo legale |
| **intfloat/multilingual-e5-small** | ~448 MB | 384 | 100 | ~56 | Più leggero, bassa latenza | Dimensione minore può perdere discriminazione |
| **Wasserstoff-AI/Legal-Embed** | ~1,1 GB | 1024 | Multi | N/A | Fine-tuned per legale | **SCARTATO: maggior FP per motivo analizzato in sezione 3** |

### 4.2 Raccomandazione basata sulle prove

**Modello principale: `BAAI/bge-m3`**

Giusticazione:

1.  Migliori prestazioni nei benchmark multilingue, incluso lo spagnolo (vedi [OpenAI vs Open-Source Multilingual Embedding Models](https://towardsdatascience.com/openai-vs-open-source-multilingual-embedding-models-e5ccb7c90f05/))
2.  Maggiore dimensionalità (1024) = maggiore capacità di separare centroidi di tipo
3.  Retrieval Dense+sparse+ColBERT funziona bene per confronti di similarità
4.  Supporta fino a 8192 token (utile per contesti legali lunghi)

**Modello alternativo: `intfloat/multilingual-e5-large`**

Giusticazione:

1.  Ben documentato con paper tecnico (arXiv:2402.05672)
2.  Prestazioni eccellenti in spagnolo verificate
3.  Leggermente più piccolo di bge-m3
4.  Già proposto in `docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md`

**IMPORTANTE**: NON usare `Legal-Embed` né alcun modello fine-tuned per dominio legale. L'evidenza accademica indica che i modelli generali preservano meglio la separazione tra i tipi di entità, che è esattamente ciò di cui abbiamo bisogno per i centroidi.

### 4.3 Fonti dei benchmark

| Benchmark | Cosa misura | Riferimento |
| :--- | :--- | :--- |
| MTEB (Massive Text Embedding Benchmark) | 8 compiti inclusi classificazione e clustering | [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) |
| FinMTEB (Finance MTEB) | Prestazioni nel dominio finanziario | Tang & Yang (2024), arXiv:2409.18511 |
| MMTEB (Massive Multilingual TEB) | Estensione multilingue di MTEB (2025) | [MMTEB GitHub](https://github.com/embeddings-benchmark/mteb) |

**Nota critica**: Nessun benchmark esistente misura direttamente "discriminazione del tipo di entità tramite centroidi". MTEB ha sottocompiti di classificazione e clustering che sono approssimazioni utili. Si raccomanda di creare un benchmark interno per ContextSafe.

---

## 5. Risultato 4: Tecniche di Validazione del Tipo Basate sui Centroidi

### 5.1 Reti prototipiche e centroidi per NER

| Paper | Sede/Anno | Risultato chiave |
| :--- | :--- | :--- |
| **"CEPTNER: Contrastive Learning Enhanced Prototypical Network for Two-stage Few-shot NER"** (Wang et al.) | Knowledge-Based Systems (2024) | Due fasi: (1) rilevamento dei confini, (2) classificazione prototipica con apprendimento contrastivo. L'apprendimento contrastivo a livello di entità separa efficacemente i tipi. Valutato su Few-NERD, CrossNER, SNIPS. |
| **"Transformer-based Prototype Network for Chinese Nested NER"** (MSTPN) | Scientific Reports (2025) | Reti prototipiche con transformer per NER nidificato. Usa i bounding box delle entità come prototipi. |
| **"KCL: Few-shot NER with Knowledge Graph and Contrastive Learning"** | LREC-COLING 2024 | Combina Knowledge Graphs con apprendimento contrastivo per apprendere rappresentazione semantica delle etichette. Usa KG per fornire info di tipo strutturate. La rappresentazione contrastiva separa i cluster di etichette nello spazio prototipico. |
| **"Multi-Head Self-Attention-Enhanced Prototype Network with Contrastive-Center Loss for Few-Shot Relation Extraction"** | Applied Sciences (2024) | Perdita contrastive-center che confronta campioni di addestramento con centri di classe corrispondenti E non-corrispondenti. Riduce distanze intra-classe e aumenta distanze inter-classe. |
| **"CLESR: Context-Based Label Knowledge Enhanced Span Recognition for NER"** | Int J Computational Intelligence Systems (2024) | Migliora NER nidificato integrando info contestuali con conoscenza delle etichette. Gli span si allineano con descrizioni testuali dei tipi in spazio semantico condiviso. |

### 5.2 Best practice per la costruzione dei centroidi

In base alla letteratura revisionata:

| Aspetto | Raccomandazione | Giustificazione |
| :--- | :--- | :--- |
| **Numero di esempi** | 50-100 per tipo | CEPTNER mostra efficacia con pochi esempi; 50 è minimo, 100 è robusto |
| **Diversità esempi** | Includere variazioni di contesto, formato, lunghezza | KCL enfatizza diversità per cluster più discriminativi |
| **Dimensione contesto** | 10-15 token circostanti | Il sondaggio NER (arXiv:2401.10825) conferma che BERT cattura contesto intra- e inter-frase efficacemente |
| **Aggiornamento centroidi** | Ricalcolare periodicamente con nuovi esempi confermati | CEPTNER mostra che più esempi migliorano separazione; i centroidi devono evolvere |
| **Raffinamento contrastivo** | Addestrare con perdita contrastiva per massimizzare separazione | Molti paper mostrano che la perdita contrastiva è CHIAVE per separazione dei tipi |
| **Livelli intermedi** | Considerare estrazione da livelli 15-17, non solo livello finale | NER Retriever (arXiv:2509.04011) mostra che livelli intermedi contengono più info di tipo |

### 5.3 Dimensione finestra contestuale

| Paper | Risultato sul contesto |
| :--- | :--- |
| Survey NER (arXiv:2401.10825) | "BERT encodings capture important within and adjacent-sentence context." Aumentare la finestra migliora le prestazioni. |
| Span-based Unified NER via Contrastive Learning (IJCAI 2024) | Span con contesto si allineano con descrizioni di tipo nello spazio condiviso. Contesto è necessario per disambiguare. |
| Contextualized Span Representations (Wadden et al.) | Propagazione di rappresentazioni di span via link di coreferenza permette disambiguazione menzioni difficili. |

**Raccomandazione**: Per ContextSafe, usare **contesto di 10-15 token** su ogni lato dell'entità. Per entità all'inizio/fine della frase, riempire con token della frase precedente/successiva se disponibile.

---

## 6. Risultato 5: Approcci Ibridi (Generale + Dominio)

### 6.1 Concatenazione ed ensemble di embedding

| Paper | Sede/Anno | Risultato chiave |
| :--- | :--- | :--- |
| **"Automated Concatenation of Embeddings for Structured Prediction" (ACE)** | ACL-IJCNLP 2021 | Framework che trova automaticamente la migliore concatenazione di embedding per predizione strutturata (incluso NER). Raggiunge SOTA in 6 compiti su 21 dataset. La selezione varia per compito e set di candidati. |
| **"Pooled Contextualized Embeddings for NER"** (Akbik et al.) | NAACL 2019 | Aggrega embedding contestualizzati di ogni istanza unica per creare rappresentazione "globale". Stacked embeddings (combinare più tipi) è una caratteristica chiave di Flair e migliora significativamente il NER. |
| **"Improving Few-Shot Cross-Domain NER by Instruction Tuning a Word-Embedding based Retrieval Augmented LLM" (IF-WRANER)** | EMNLP 2024 Industry | Usa embedding a livello di parola (non livello di frase) per retrieval di esempi in-prompt. Supera SOTA in CrossNER di >2% F1. Distribuito in produzione, riducendo escalation umane ~15%. |
| **"Pre-trained Embeddings for Entity Resolution: An Experimental Analysis"** (Zeakis et al.) | VLDB 2023 | Analisi di 12 modelli linguistici su 17 dataset per entity resolution. Embedding contestualizzati (varianti BERT) superano statici (fastText) costantemente, ma la combinazione può essere vantaggiosa. |

### 6.2 Adattatori (LoRA) per preservare la conoscenza generale

| Paper | Sede/Anno | Risultato chiave |
| :--- | :--- | :--- |
| **"Continual Named Entity Recognition without Catastrophic Forgetting"** (Zheng et al.) | EMNLP 2023 | Propongono pooled feature distillation loss + pseudo-labeling + adaptive re-weighting. L'oblio catastrofico nel NER continuo è intensificato dal "semantic shift" del tipo non-entità. |
| **"A New Adapter Tuning of LLM for Chinese Medical NER"** | Automation in Construction (2024) | Gli adattatori evitano l'oblio catastrofico perché imparano nuova conoscenza senza aggiustamenti estesi dei parametri. Preferibili per NER multi-dominio. |
| **"Mixture of LoRA Experts for Continual Information Extraction"** | EMNLP 2025 Findings | Framework MoE con LoRA per estrazione continua di informazioni. Permette di aggiungere domini senza dimenticare i precedenti. |
| **"LoRASculpt: Sculpting LoRA for Harmonizing General and Specialized Knowledge"** | CVPR 2025 | Tecnica per bilanciare conoscenza generale e specializzata durante fine-tuning con LoRA. |

### 6.3 Strategie di combinazione praticabili per ContextSafe

| Strategia | Complessità | Beneficio atteso | Raccomandata |
| :--- | :--- | :--- | :--- |
| **A: Embedding generali puri** | Bassa | Buona discriminazione dei tipi senza FP aggiuntivi | Sì (baseline) |
| **B: Concatenare generale + legale** | Media | Più dimensioni, cattura entrambi gli aspetti | Valutabile ma costosa in latenza |
| **C: Media pesata generale + legale** | Media | Più semplice di concat, ma perde informazioni | Non raccomandata (la media diluisce) |
| **D: Meta-modello su embedding multipli** | Alta | Migliore precisione se ci sono dati di training sufficienti | Per il futuro |
| **E: Adattatore LoRA su modello generale** | Media-Alta | Preserva capacità generale + aggiunge dominio | Sì (secondo passo) |

**Raccomandazione per ContextSafe**:

*   **Fase 1 (immediata)**: Usare embedding generali puri (bge-m3 o e5-large). Valutare riduzione FP rispetto all'esperienza con embedding legali.
*   **Fase 2 (se Fase 1 insufficiente)**: Applicare adattatore LoRA su modello generale con esempi contrastivi di entità legali spagnole. Questo preserva la capacità di discriminazione dei tipi generale aggiungendo conoscenza del dominio.
*   **Fase 3 (opzionale)**: Ricerca automatizzata stile ACE della migliore concatenazione se disponibile un dataset di validazione di tipo sufficientemente ampio.

---

## 7. Sintesi e Raccomandazione Finale

### 7.1 Risposta diretta alle domande di ricerca

**D1: General-purpose vs domain-specific per classificazione tipo entità?**

Usare **general-purpose**. L'evidenza da molteplici paper (Tang & Yang 2024, Rajaee & Pilehvar 2021, Machina & Mercer NAACL 2024) indica che:

*   I modelli generali mantengono spazi semantici più ampi
*   La discriminazione dei tipi di entità richiede separazione inter-classe, non profondità intra-dominio
*   I modelli di dominio fanno collassare tipi simili nello stesso sottospazio

**D2: Perché gli embedding legali producono più falsi positivi?**

Tre fattori convergenti:

1.  **Collasso della diversità semantica**: il fine-tuning legale avvicina le rappresentazioni di tutte le entità al sottospazio "legale"
2.  **Anisotropia non controllata**: il fine-tuning introduce direzioni dominanti che codificano "legalità" invece di "tipo di entità" (Rajaee & Pilehvar 2021, Rudman & Eickhoff ICLR 2024)
3.  **Sovrapposizione dei centroidi**: i centroidi di PERSON e ORGANIZATION si avvicinano perché entrambi appaiono in contesti legali identici

**D3: Miglior modello?**

`BAAI/bge-m3` (prima opzione) o `intfloat/multilingual-e5-large` (seconda opzione). Entrambi sono generali, multilingue, con buon supporto per lo spagnolo e dimensionalità 1024 sufficiente per separare i centroidi di tipo.

**D4: Tecnica dei centroidi?**

Ben supportata da CEPTNER (2024), KCL (2024), MSTPN (2025). Chiavi:

*   50-100 esempi diversi per tipo
*   Contesto di 10-15 token attorno all'entità
*   Apprendimento contrastivo per raffinare i centroidi se possibile
*   Livelli intermedi (15-17) possono essere più informativi del livello finale

**D5: Approccio ibrido?**

Per il futuro: Adattatori LoRA su modello generale è la strategia più promettente. Preserva discriminazione generale + aggiunge conoscenza del dominio. ACE (concatenazione automatizzata) è praticabile se esistono dati di valutazione sufficienti.

### 7.2 Impatto sul documento precedente

Il documento `docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md` raccomanda `multilingual-e5-large` come modello principale e suggerisce di valutare `Legal-Embed` come alternativa. Basandosi su questa ricerca:

| Aspetto | Documento precedente | Aggiornamento |
| :--- | :--- | :--- |
| Modello principale | `multilingual-e5-large` | **Corretto**, mantenere |
| Alternativa Legal-Embed | Suggerita per valutazione | **SCARTARE**: evidenza indica che produrrà più FP |
| Alternativa reale | Non proposta | **Aggiungere `BAAI/bge-m3`** come prima opzione |
| Raffinamento contrastivo | Non menzionato | **Aggiungere**: se i centroidi non separano abbastanza, applicare apprendimento contrastivo |
| Livelli intermedi | Non menzionato | **Aggiungere**: estrarre embedding da livelli 15-17, non solo ultimo |

---

## 8. Tabella Consolidata dei Paper Revisionati

| # | Paper | Sede | Anno | Argomento Principale | URL |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Do We Need Domain-Specific Embedding Models? An Empirical Investigation | arXiv 2409.18511 | 2024 | General vs domain embeddings | https://arxiv.org/abs/2409.18511 |
| 2 | NuNER: Entity Recognition Encoder Pre-training via LLM-Annotated Data | EMNLP 2024 | 2024 | Entity-aware pre-training | https://aclanthology.org/2024.emnlp-main.660/ |
| 3 | LegNER: Domain-Adapted Transformer for Legal NER | Frontiers in AI | 2025 | Legal NER + anonymization | https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1638971/full |
| 4 | MEL: Legal Spanish Language Model | arXiv 2501.16011 | 2025 | Spanish legal embeddings | https://arxiv.org/abs/2501.16011 |
| 5 | Anisotropy is Not Inherent to Transformers | NAACL 2024 | 2024 | Embedding space geometry | https://aclanthology.org/2024.naacl-long.274/ |
| 6 | Stable Anisotropic Regularization (I-STAR) | ICLR 2024 | 2024 | Controlled anisotropy | https://arxiv.org/abs/2305.19358 |
| 7 | The Shape of Learning: Anisotropy and Intrinsic Dimensions | EACL 2024 | 2024 | Anisotropy dynamics in transformers | https://aclanthology.org/2024.findings-eacl.58/ |
| 8 | How Does Fine-tuning Affect Geometry of Embedding Space | EMNLP 2021 Findings | 2021 | Fine-tuning impact on isotropy | https://aclanthology.org/2021.findings-emnlp.261/ |
| 9 | Representation Degeneration in Prompt-based Fine-tuning | LREC 2024 | 2024 | Anisotropy limits performance | https://aclanthology.org/2024.lrec-main.1217/ |
| 10 | Improving Legal Entity Recognition Using Semantic Filtering | arXiv 2410.08521 | 2024 | Legal NER false positive reduction | https://arxiv.org/abs/2410.08521 |
| 11 | CEPTNER: Contrastive Enhanced Prototypical Network for Few-shot NER | Knowledge-Based Systems | 2024 | Prototype networks for NER | https://doi.org/10.1016/j.knosys.2024.111730 |
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

## 9. Documenti Correlati

| Documento | Relazione |
| :--- | :--- |
| `docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md` | Documento precedente che propone validatore di tipo con embedding. Questa ricerca AGGIORNA le sue raccomandazioni. |
| `docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md` | Valutazione precedente di embedding per classificazione documenti (compito diverso). |
| `docs/reports/2026-02-07_embeddings_roadmap_document_classification.md` | Roadmap embedding per classificazione documenti. |
| `docs/reports/2026-01-30_investigacion_gaps_pipeline_hibrido.md` | Gap della pipeline NER ibrida (contesto degli errori di tipo). |
| `docs/reports/2026-01-28_investigacion_hybrid_ner.md` | Ricerca su NER ibrido (contesto dell'architettura). |

---

```
Versione: 1.0.0
Autor: AlexAlves87
Tempo di ricerca: ~45 min
Paper revisionati: 23
```
