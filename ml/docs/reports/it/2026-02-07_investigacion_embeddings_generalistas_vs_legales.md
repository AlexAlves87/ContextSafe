# Ricerca: Embedding Generalisti vs Legali per la Disambiguazione dei Tipi di Entità

**Data:** 07-02-2026
**Obiettivo:** Determinare se usare embedding generalisti (multilingual-e5-large) o specializzati in ambito legale (Legal-Embed, voyage-law-2) per il validatore post-NER dei tipi di entità in ContextSafe.

---

## 1. Riepilogo Esecutivo

1.  **Risultato principale**: Gli embedding legali sono ottimizzati per il **retrieval** (cercare documenti simili), NON per la **discriminazione dei tipi di entità**. Questo spiega i falsi positivi osservati.
2.  **Raccomandazione**: Usare **embedding generalisti** (`intfloat/multilingual-e5-large`) per la disambiguazione dei tipi di entità. Quelli legali possono causare il collasso dello spazio semantico dove PERSON e ORGANIZATION risultano troppo vicine.
3.  **Evidenza chiave**: Il fine-tuning di dominio può causare "sovra-specializzazione" che riduce la capacità di discriminazione tra categorie (catastrophic forgetting dei confini tra tipi).
4.  **Alternativa ibrida**: Se è necessaria conoscenza legale, usare un approccio a due stadi: generalista per il tipo + legale per la validazione dell'entità specifica.
5.  **Riduzione errori attesa**: 4-5% con embedding generalisti ben calibrati (letteratura: WNUT17, NER Retriever).

---

## 2. Letteratura Revisionata

### 2.1 Generalisti vs Specifici di Dominio

| Paper/Fonte | Sede/Anno | Risultato Rilevante |
| :--- | :--- | :--- |
| "Do we need domain-specific embedding models?" | arXiv:2409.18511 (2024) | In finanza (FinMTEB), i modelli generali degradano rispetto agli specifici. MA: questo è per **retrieval**, non per classificazione di tipi. |
| "How Does Fine-tuning Affect the Geometry of Embedding Space?" | ACL Findings 2021 | Il fine-tuning di dominio **riduce la separazione** tra classi nello spazio di embedding. I cluster collassano. |
| "Is Anisotropy Really the Cause of BERT Embeddings not Working?" | EMNLP Findings 2022 | L'anisotropia (embedding concentrati in un cono stretto) è un problema noto. Il fine-tuning di dominio lo **peggiora**. |
| "Dynamic Expert Specialization: Catastrophic Forgetting-Free Multi-Domain MoE" | EMNLP 2025 | Il catastrophic forgetting si verifica nel fine-tuning di dominio. I modelli dimenticano i confini appresi in precedenza. |
| "Continual Named Entity Recognition without Catastrophic Forgetting" | arXiv:2310.14541 (2023) | Il NER continuo soffre di oblio catastrofico: i vecchi tipi si "consolidano" in non-entità. Analogo al nostro problema. |

### 2.2 Perché gli Embedding Legali Causano Falsi Positivi

| Fenomeno | Spiegazione | Fonte |
| :--- | :--- | :--- |
| **Collasso dello spazio semantico** | Il fine-tuning legale ottimizza affinché documenti legali simili siano vicini, NON per separare PERSON da ORGANIZATION | Blog Weaviate, MongoDB Fine-Tuning Guide |
| **Sovra-specializzazione** | "Un addestramento troppo ristretto può rendere il modello fine-tuned troppo specializzato" - perde capacità di discriminazione generale | [Weaviate](https://weaviate.io/blog/fine-tune-embedding-model) |
| **Contrastive loss orientata al retrieval** | voyage-law-2 usa "coppie positive specificamente progettate" per retrieval legale, non per classificazione di entità | [Blog Voyage AI](https://blog.voyageai.com/2024/04/15/domain-specific-embeddings-and-retrieval-legal-edition-voyage-law-2/) |
| **Terminologia legale uniforme** | Nei testi legali, "Garcia" può essere querelante, avvocato o nome di studio legale. Il modello legale li incorpora **vicini** perché sono tutti legali | Osservazione empirica dell'utente |

### 2.3 Centroidi e Classificazione Basata su Prototipi

| Paper/Fonte | Sede/Anno | Risultato Rilevante |
| :--- | :--- | :--- |
| "NER Retriever: Zero-Shot NER with Type-Aware Embeddings" | arXiv:2509.04011 (2025) | Strati intermedi (layer 17) meglio degli output finali per il tipo. MLP con contrastive loss per separare i tipi. |
| "CEPTNER: Contrastive Learning Enhanced Prototypical Network" | KBS (2024) | Reti prototipiche con 50-100 esempi per tipo sono sufficienti per centroidi robusti. |
| "ReProCon: Scalable Few-Shot Biomedical NER" | arXiv:2508.16833 (2025) | Prototipi multipli per categoria migliorano la rappresentazione di entità eterogenee. |
| "Mastering Intent Classification with Embeddings: Centroids" | Medium (2024) | I centroidi hanno il "tempo di addestramento più veloce" e un'accuratezza decente. Perfetti per aggiornamenti rapidi. |

### 2.4 Benchmark dei Modelli di Embedding

| Modello | Dimensione | Lingue | MTEB Avg | Vantaggio | Svantaggio |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `intfloat/multilingual-e5-large` | 1.1GB | 100 | ~64 | Miglior multilingue generale, eccellente spagnolo | Richiede prefisso "query:" |
| `intfloat/multilingual-e5-large-instruct` | 1.1GB | 100 | ~65 | Supporta istruzioni, più flessibile | Leggermente più lento |
| `BAAI/bge-m3` | 1.5GB | 100+ | ~66 | Ibrido dense+sparse, 8192 token | Più complesso da usare |
| `voyage-law-2` | API | EN | ~72 (legale) | Migliore per retrieval legale | API commerciale, solo inglese |
| `Legal-Embed (Wasserstoff)` | 1.1GB | Multi | N/A | Fine-tuned su legale | **Probabilmente causa FP in classificazione** |

---

## 3. Analisi: Perché i Generalisti Sono Migliori per il Tipo di Entità

### 3.1 Diverso Obiettivo di Addestramento

| Embedding Legali | Embedding Generalisti |
| :--- | :--- |
| Ottimizzati per: "documento A simile a documento B" | Ottimizzati per: "testo A semanticamente correlato a testo B" |
| Coppie positive: frammenti dello stesso documento legale | Coppie positive: parafrasi, traduzioni, varianti |
| Risultato: tutto ciò che è legale è vicino | Risultato: tipi semantici separati |

**Conseguenza**: Negli embedding legali, "Alejandro Alvarez" (avvocato) e "Bufete Alvarez S.L." (azienda) sono **vicini** perché entrambi sono legali. Nei generalisti, sono **lontani** perché uno è una persona e l'altro un'organizzazione.

### 3.2 Evidenza di Anisotropia Aggravata

Il paper di ACL Findings 2021 dimostra che:

1.  Il fine-tuning **riduce la varianza** dello spazio di embedding
2.  I cluster di tipi diversi **si avvicinano**
3.  La separabilità lineare **diminuisce**

Questo spiega direttamente i falsi positivi: quando tutti gli embedding legali collassano verso una regione, la distanza coseno perde potere discriminante.

### 3.3 Task vs Dominio

| Aspetto | Embedding di Dominio (Legale) | Embedding di Task (Tipo) |
| :--- | :--- | :--- |
| Domanda a cui rispondono | "Questo testo è legale?" | "Questa è una persona o un'azienda?" |
| Addestramento | Corpus legale | Contrastivo per tipo di entità |
| Utilità per validazione tipo NER | Bassa | Alta |

Il nostro problema è un problema di **task** (classificare tipo), non di **dominio** (identificare testi legali).

---

## 4. Raccomandazione per ContextSafe

### 4.1 Approccio Raccomandato: Generalista Puro

```
Pipeline:
  NER → Rilevamenti con tipo assegnato
    ↓
  EntityTypeValidator (multilingual-e5-large)
    ↓
  Per ogni entità:
    1. Incorporare "query: [entità + contesto ±10 token]"
    2. Confrontare vs centroidi per tipo (PERSON_NAME, ORGANIZATION, DATE, LOCATION)
    3. Decisioni:
       - Se miglior_centroide ≠ tipo_NER AND similarità > 0.75 AND margine > 0.10 → RICLASSIFICARE
       - Se margine < 0.05 → SEGNALARE HITL
       - Altrimenti → MANTENERE tipo NER
```

**Modello**: `intfloat/multilingual-e5-large` (1.1GB)

**Giustificazione**:

*   Addestrato su 100 lingue incluso lo spagnolo
*   NON sovra-specializzato in alcun dominio
*   Preserva la separazione semantica tra PERSON/ORGANIZATION/DATE/LOCATION
*   Già raccomandato in ricerca precedente (vedi `2026-02-07_embeddings_entity_type_disambiguation.md`)

### 4.2 Approccio Alternativo: Ibrido (Se Necessaria Conoscenza Legale)

```
Fase 1: Classificazione tipo (GENERALISTA)
  multilingual-e5-large → Tipo di entità

Fase 2: Validazione entità legale (LEGALE, opzionale)
  voyage-law-2 o Legal-Embed → "Questa entità è valida in contesto legale?"
  (Solo per casi segnalati come dubbi)
```

**Quando usare ibrido**: Se ci sono entità legali specifiche (es: "articolo 24.2 CE", "Legge 13/2022") che richiedono validazione di conoscenza legale.

Per ContextSafe (PII generico), l'approccio generalista puro è sufficiente.

### 4.3 Configurazione dei Centroidi

| Tipo | Esempi Necessari | Strategia di Contesto |
| :--- | :--- | :--- |
| PERSON_NAME | 100 | "query: L'avvocato [NOME] è comparso..." |
| ORGANIZATION | 100 | "query: L'azienda [ORG] ha presentato ricorso..." |
| DATE | 50 | "query: In data [DATA] è stata emessa sentenza..." |
| LOCATION | 50 | "query: Nella città di [LUOGO] si è tenuto..." |
| DNI_NIE | 30 | "query: con DNI [NUMERO]" (contesto breve, pattern fisso) |

**Contesto**: ±10 token attorno all'entità. Né troppo breve (perde contesto) né troppo lungo (introduce rumore).

---

## 5. Esperimento Proposto

### 5.1 Confronto A/B

| Condizione | Modello | Atteso |
| :--- | :--- | :--- |
| A (Baseline) | Senza validatore | Pass rate attuale: 60% |
| B (Generalista) | `multilingual-e5-large` | Pass rate atteso: 64-65% |
| C (Legale) | `Legal-Embed-intfloat-multilingual-e5-large-instruct` | Pass rate atteso: < 60% (più FP) |

### 5.2 Metriche da Valutare

1.  **Pass rate in test adversarial** (35 test esistenti)
2.  **Accuratezza di riclassificazione**: % di riclassificazioni corrette
3.  **Tasso di falsi positivi**: Entità correttamente tipizzate che sono state erroneamente riclassificate
4.  **Latenza aggiuntiva**: ms per entità validata

### 5.3 Casi di Test Specifici

Basati su errori di auditoria.md (vedi `2026-02-07_embeddings_entity_type_disambiguation.md`, sezione 6):

| Entità | Tipo NER | Tipo Corretto | Modello Atteso OK |
| :--- | :--- | :--- | :--- |
| "Alejandro Alvarez" | ORGANIZATION | PERSON_NAME | Generalista |
| "10/10/2025" | ORGANIZATION | DATE | Generalista |
| "Pura" | LOCATION | PERSON_NAME | Generalista |
| "Finalmente" | ORGANIZATION | NON È PII | Generalista (bassa similarità con tutti) |
| "Whatsapp" | PERSON | ORGANIZATION/PLATFORM | Generalista |

---

## 6. Rischi e Mitigazioni

| Rischio | Probabilità | Mitigazione |
| :--- | :--- | :--- |
| Generalista non discrimina bene neanche PERSON/ORG in spagnolo legale | Media | Valutare prima di implementare; se fallisce, addestrare centroidi con contrastive loss |
| Latenza inaccettabile (>100ms/entità) | Bassa | Elaborazione batch, cache di embedding frequenti |
| Centroidi richiedono più di 100 esempi | Bassa | Aumentare a 200 se F1 < 0.90 in validazione |
| Modello da 1.1GB non sta in produzione | Bassa | Quantizzare a INT8 (~300MB) o usare e5-base (560MB) |

---

## 7. Conclusione

**Gli embedding legali sono ottimizzati per il task sbagliato.** Il loro obiettivo (retrieval di documenti simili) fa sì che entità di tipi diversi ma dello stesso dominio (legale) vengano incorporate vicine, riducendo la capacità di discriminazione.

Per la disambiguazione dei tipi di entità, gli **embedding generalisti** preservano meglio i confini semantici tra PERSON, ORGANIZATION, DATE, ecc., perché non sono stati "collassati" verso un dominio specifico.

**Raccomandazione finale**: Implementare validatore con `intfloat/multilingual-e5-large` e valutare empiricamente prima di considerare alternative legali.

---

## 8. Prossimi Passi

1.  [ ] Scaricare `intfloat/multilingual-e5-large` (~1.1GB)
2.  [ ] Costruire dataset di esempi per tipo (PERSON_NAME, ORGANIZATION, DATE, LOCATION) con contesto legale
3.  [ ] Calcolare centroidi per ogni tipo
4.  [ ] Implementare `EntityTypeValidator` con soglie configurabili
5.  [ ] Valutare su test adversarial (35 test)
6.  [ ] (Opzionale) Confrontare vs `Legal-Embed` per confermare ipotesi di falsi positivi
7.  [ ] Documentare risultati e decisione finale

---

## Documenti Correlati

| Documento | Relazione |
| :--- | :--- |
| `ml/docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md` | Ricerca precedente, architettura proposta |
| `ml/docs/reports/2026-02-07_embeddings_roadmap_document_classification.md` | Roadmap embedding, criteri di attivazione |
| `ml/docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | Pipeline attuale, metriche baseline |
| `auditoria.md` | Errori di classificazione identificati |
| `ml/models/type_centroids.json` | Centroidi esistenti (richiede verifica del modello usato) |

---

## Riferimenti

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
Versione: 1.0.0
Autor: AlexAlves87
Tempo di ricerca: ~25 min
Token di ricerca: 12 query
```
