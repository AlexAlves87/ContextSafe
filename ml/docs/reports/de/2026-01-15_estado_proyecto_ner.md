# Statusbericht: NER-PII-System für spanische Rechtsdokumente

**Datum:** 2026-01-15
**Version:** 1.0
**Autor:** AlexAlves87
**Projekt:** ContextSafe ML - Fine-tuning NER

---

## Zusammenfassung

Dieser Bericht dokumentiert die Entwicklung des PII-Erkennungssystems (Personally Identifiable Information) für spanische Rechtsdokumente. Das System muss 13 Entitätskategorien mit F1 ≥ 0,85 erkennen.

### Aktueller Status

| Phase | Status | Fortschritt |
|------|--------|----------|
| Download der Basisdaten | Abgeschlossen | 100% |
| Generierung von Gazetteers | Abgeschlossen | 100% |
| Synthetischer Datensatz v1 | Verworfen | Kritischer Fehler |
| Synthetischer Datensatz v2 | Abgeschlossen | 100% |
| Trainingsskript | Abgeschlossen | 100% |
| Modelltraining | Ausstehend | 0% |

---

## 1. Projektziel

Entwicklung eines NER-Modells, das auf spanische Rechtsdokumente (Testamente, Urteile, Urkunden, Verträge) spezialisiert ist und Folgendes erkennen kann:

| Kategorie | Beispiele | Priorität |
|-----------|----------|-----------|
| PERSON | Hermógenes Pérez García | Hoch |
| DATE | 15 de marzo de 2024 | Hoch |
| DNI_NIE | 12345678Z, X1234567A | Hoch |
| IBAN | ES9121000418450200051332 | Hoch |
| NSS | 281234567890 | Mittel |
| PHONE | 612 345 678 | Mittel |
| ADDRESS | Calle Mayor 15, 3º B | Hoch |
| POSTAL_CODE | 28001 | Mittel |
| ORGANIZATION | Banco Santander, S.A. | Hoch |
| LOCATION | Madrid, Comunidad de Madrid | Mittel |
| ECLI | ECLI:ES:TS:2024:1234 | Niedrig |
| LICENSE_PLATE | 1234 ABC | Niedrig |
| CADASTRAL_REF | 1234567AB1234S0001AB | Niedrig |
| PROFESSIONAL_ID | Colegiado nº 12345 | Niedrig |

---

## 2. Heruntergeladene Daten

### 2.1 Offizielle Quellen

| Ressource | Ort | Größe | Beschreibung |
|---------|-----------|--------|-------------|
| CoNLL-2002 Spanish | `data/raw/conll2002/` | 4,0 MB | Standard NER Korpus |
| INE Vornamen nach Jahrzehnt | `data/raw/gazetteers_ine/nombres_por_fecha.xls` | 1,1 MB | Zeitliche Häufigkeit |
| INE Häufige Vornamen | `data/raw/gazetteers_ine/nombres_mas_frecuentes.xls` | 278 KB | Top Namen |
| INE Nachnamen | `data/raw/gazetteers_ine/apellidos_frecuencia.xls` | 12 MB | 27.251 Nachnamen |
| INE Gemeinden 2024 | `data/raw/municipios/municipios_2024.xlsx` | 300 KB | 8.115 Gemeinden |
| Postleitzahlen | `data/raw/codigos_postales/codigos_postales.csv` | 359 KB | 11.051 PLZ |
| ai4privacy/pii-masking-300k | `data/raw/ai4privacy/` | ~100 MB | Transfer Learning |

### 2.2 Basismodell

| Modell | Ort | Größe | Basis F1 |
|--------|-----------|--------|---------|
| roberta-base-bne-capitel-ner | `models/checkpoints/` | ~500 MB | 88,5% (CAPITEL) |

**Modellentscheidung:** Das MEL (Modelo Español Legal) wurde evaluiert, verfügt jedoch nicht über NER-Fine-Tuning. RoBERTa-BNE-capitel-ner wurde aufgrund seiner Spezialisierung auf spanisches NER ausgewählt.

---

## 3. Generierte Gazetteers

### 3.1 Generierungsskripte

| Skript | Funktion | Output |
|--------|---------|--------|
| `parse_ine_gazetteers.py` | Parst INE Excel → JSON | apellidos.json, nombres_*.json |
| `generate_archaic_names.py` | Generiert archaische Rechtsnamen | nombres_arcaicos.json |
| `generate_textual_dates.py` | Daten im Rechtsformat | fechas_textuales.json |
| `generate_administrative_ids.py` | DNI, NIE, IBAN, NSS mit ungültigen Prüfsummen | identificadores_administrativos.json |
| `generate_addresses.py` | Vollständige spanische Adressen | direcciones.json |
| `generate_organizations.py` | Unternehmen, Gerichte, Banken | organizaciones.json |

### 3.2 Generierte Dateien

| Datei | Größe | Inhalt |
|---------|--------|-----------|
| `apellidos.json` | 1,8 MB | 27.251 Nachnamen mit INE-Häufigkeiten |
| `codigos_postales.json` | 1,2 MB | 11.051 Postleitzahlen |
| `municipios.json` | 164 KB | 8.115 spanische Gemeinden |
| `nombres_hombres.json` | 40 KB | 550 männliche Vornamen pro Jahrzehnt |
| `nombres_mujeres.json` | 41 KB | 550 weibliche Vornamen pro Jahrzehnt |
| `nombres_todos.json` | 3,9 KB | 260 eindeutige Vornamen (INE) |
| `nombres_arcaicos.json` | 138 KB | 940 archaische Namen + 5.070 Kombinationen |
| `nombres_arcaicos_flat.json` | 267 KB | Flache Liste für NER |
| `fechas_textuales.json` | 159 KB | 645 Daten mit 41 Rechtsmustern |
| `fechas_textuales_flat.json` | 86 KB | Flache Liste |
| `identificadores_administrativos.json` | 482 KB | 2.550 synthetische IDs |
| `identificadores_administrativos_flat.json` | 134 KB | Flache Liste |
| `direcciones.json` | 159 KB | 600 Adressen + 416 mit Rechtskontext |
| `direcciones_flat.json` | 59 KB | Flache Liste |
| `organizaciones.json` | 185 KB | 1.000 Organisationen |
| `organizaciones_flat.json` | 75 KB | Flache Liste |

**Gesamt Gazetteers:** ~4,9 MB

### 3.3 Besondere Merkmale

**Archaische Namen:** Enthält häufige Namen in historischen Rechtsdokumenten:
- Hermógenes, Segismundo, Práxedes, Gertrudis, Baldomero, Saturnino, Patrocinio...
- Zusammengesetzte Kombinationen: María del Carmen, José Antonio, Juan de Dios...

**Administrative Identifikatoren:** Generiert mit MATHEMATISCH UNGÜLTIGEN Prüfsummen:
- DNI: Falscher Kontrollbuchstabe (falscher mod-23)
- NIE: Präfix X/Y/Z mit falschem Buchstaben
- IBAN: Kontrollziffern "00" (immer ungültig)
- NSS: Falsche Kontrollziffern (mod-97)

Dies garantiert, dass kein synthetischer Identifikator echten Daten entspricht.

---

## 4. Synthetischer Datensatz

### 4.1 Datensatz v1 - KRITISCHER FEHLER (VERWORFEN)

**Datum:** 2026-01-15

Der erste generierte Datensatz enthielt kritische Fehler, die das Modell erheblich verschlechtert hätten.

#### Fehler 1: An Token haftende Interpunktion

**Problem:** Die einfache Tokenisierung durch Leerzeichen führte dazu, dass Satzzeichen an Entitäten hafteten.

**Beispiel des Fehlers:**
```
Text: "Don Hermógenes Freijanes, con DNI 73364386X."
Token: ["Don", "Hermógenes", "Freijanes,", "con", "DNI", "73364386X."]
Label: ["O",   "B-PERSON",   "I-PERSON",   "O",   "O",   "B-DNI_NIE"]
```

**Auswirkung:** Das Modell würde lernen, dass "Freijanes," (mit Komma) eine Person ist, aber während der Inferenz "Freijanes" ohne Komma nicht erkennen.

**Fehlerstatistiken:**
- 6.806 Token mit anhaftender Interpunktion
- Betraf hauptsächlich: PERSON, DNI_NIE, IBAN, PHONE
- ~30% der betroffenen Entitäten

#### Fehler 2: Keine Subword-Ausrichtung

**Problem:** BIO-Tags waren auf Wortebene, aber BERT verwendet Subword-Tokenisierung.

**Beispiel des Fehlers:**
```
Wort: "Hermógenes"
Subwords: ["Her", "##mó", "##genes"]
Label v1: Nur ein Tag für das ganze Wort → welches Subword erhält es?
```

**Auswirkung:** Ohne explizite Ausrichtung könnte das Modell die Beziehung zwischen Subwords und Tags nicht korrekt lernen.

#### Fehler 3: Entitätsungleichgewicht

| Entität | Prozentsatz v1 | Problem |
|---------|---------------|----------|
| PERSON | 30,3% | Überrepräsentiert |
| ADDRESS | 12,6% | OK |
| DNI_NIE | 10,1% | OK |
| NSS | 1,7% | Unterrepräsentiert |
| ECLI | 1,7% | Unterrepräsentiert |
| LICENSE_PLATE | 1,7% | Unterrepräsentiert |

### 4.2 Datensatz v2 - KORRIGIERT

**Datum:** 2026-01-15

**Skript:** `scripts/preprocess/generate_ner_dataset_v2.py`

#### Implementierte Korrekturen

**1. Tokenisierung mit HuggingFace:**
```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("PlanTL-GOB-ES/roberta-base-bne")

# Die Tokenisierung trennt Satzzeichen automatisch
# "Freijanes," → ["Fre", "##ij", "##anes", ","]
```

**2. Ausrichtung mit word_ids():**
```python
def align(self, sentence, max_length=128):
    encoding = self.tokenizer(
        text,
        max_length=max_length,
        return_offsets_mapping=True,
    )

    word_ids = encoding.word_ids()

    labels = []
    for i, word_id in enumerate(word_ids):
        if word_id is None:
            labels.append(-100)  # Spezial-Token
        elif word_id != previous_word_id:
            labels.append(entity_label)  # Erstes Subword
        else:
            labels.append(-100)  # Fortsetzung
```

**3. Ausbalancierte Vorlagen:**
- 50+ spezifische Vorlagen für Minderheitsentitäten hinzugefügt
- Erhöhte Frequenz von NSS, ECLI, LICENSE_PLATE, CADASTRAL_REF

#### Statistiken v2

| Split | Proben | Gesamt-Token |
|-------|----------|----------------|
| Train | 4.925 | ~630.000 |
| Validation | 818 | ~105.000 |
| Test | 818 | ~105.000 |
| **Gesamt** | **6.561** | **~840.000** |

**Verteilung der Entitäten v2:**

| Entität | Anzahl | % |
|---------|-------|---|
| PERSON | 1.800 | 24,4% |
| ADDRESS | 750 | 10,2% |
| LOCATION | 700 | 9,5% |
| DNI_NIE | 600 | 8,1% |
| DATE | 450 | 6,1% |
| ORGANIZATION | 450 | 6,1% |
| POSTAL_CODE | 200 | 2,7% |
| IBAN | 200 | 2,7% |
| CADASTRAL_REF | 150 | 2,0% |
| PHONE | 150 | 2,0% |
| PROFESSIONAL_ID | 150 | 2,0% |
| ECLI | 100 | 1,4% |
| LICENSE_PLATE | 100 | 1,4% |
| NSS | 100 | 1,4% |

#### Ausgabeformat

```
data/processed/ner_dataset_v2/
├── train/
│   ├── data-00000-of-00001.arrow
│   └── dataset_info.json
├── validation/
│   ├── data-00000-of-00001.arrow
│   └── dataset_info.json
├── test/
│   ├── data-00000-of-00001.arrow
│   └── dataset_info.json
├── label_mappings.json
└── dataset_dict.json
```

**Datenschema:**
```python
{
    "input_ids": [0, 1234, 5678, ...],      # Token IDs
    "attention_mask": [1, 1, 1, ...],        # Aufmerksamkeitsmaske
    "labels": [-100, 1, 2, -100, ...],       # Ausgerichtete Labels
}
```

**Labels (29 Klassen):**
```json
{
    "O": 0,
    "B-PERSON": 1, "I-PERSON": 2,
    "B-LOCATION": 3, "I-LOCATION": 4,
    "B-ORGANIZATION": 5, "I-ORGANIZATION": 6,
    "B-DATE": 7, "I-DATE": 8,
    "B-DNI_NIE": 9, "I-DNI_NIE": 10,
    "B-IBAN": 11, "I-IBAN": 12,
    "B-NSS": 13, "I-NSS": 14,
    "B-PHONE": 15, "I-PHONE": 16,
    "B-ADDRESS": 17, "I-ADDRESS": 18,
    "B-POSTAL_CODE": 19, "I-POSTAL_CODE": 20,
    "B-LICENSE_PLATE": 21, "I-LICENSE_PLATE": 22,
    "B-CADASTRAL_REF": 23, "I-CADASTRAL_REF": 24,
    "B-ECLI": 25, "I-ECLI": 26,
    "B-PROFESSIONAL_ID": 27, "I-PROFESSIONAL_ID": 28
}
```

---

## 5. Trainingskonfiguration

### 5.1 Recherche der Best Practices

Best Practices für NER-Fine-Tuning wurden untersucht basierend auf:
- HuggingFace Dokumentation
- Akademische Paper (RoBERTa, BERT für NER)
- Spanische Modell-Benchmarks (CAPITEL, AnCora)

### 5.2 Ausgewählte Hyperparameter

**Datei:** `scripts/train/train_ner.py`

```python
CONFIG = {
    # Optimierung (WICHTIGSTE)
    "learning_rate": 2e-5,          # Grid: {1e-5, 2e-5, 3e-5, 5e-5}
    "weight_decay": 0.01,           # L2 Regularisierung
    "adam_epsilon": 1e-8,           # Numerische Stabilität

    # Batching
    "per_device_train_batch_size": 16,
    "per_device_eval_batch_size": 32,
    "gradient_accumulation_steps": 2,  # Effektiver Batch = 32

    # Epochen
    "num_train_epochs": 4,          # Konservativ für Rechtstexte

    # Learning Rate Scheduling
    "warmup_ratio": 0.06,           # 6% Warmup (Paper RoBERTa)
    "lr_scheduler_type": "linear",  # Linearer Abfall

    # Early Stopping
    "early_stopping_patience": 2,   # Stopp wenn keine Verbesserung in 2 Evals
    "metric_for_best_model": "f1",

    # Sequenzlänge
    "max_length": 384,              # Lange Rechtsdokumente

    # Hardware
    "fp16": True,                   # Mixed Precision wenn GPU
    "dataloader_num_workers": 4,

    # Reproduzierbarkeit
    "seed": 42,
}
```

### 5.3 Begründung der Entscheidungen

| Parameter | Wert | Begründung |
|-----------|-------|---------------|
| learning_rate | 2e-5 | Standardwert für BERT/RoBERTa Fine-Tuning |
| batch_size | 32 (effektiv) | Balance zwischen Stabilität und Speicher |
| epochs | 4 | Vermeidung von Overfitting bei synthetischen Daten |
| warmup | 6% | Empfehlung Paper RoBERTa |
| max_length | 384 | Rechtsdokumente können umfangreich sein |
| early_stopping | 2 | Früherkennung von Overfitting |

### 5.4 Abhängigkeiten

**Datei:** `scripts/train/requirements_train.txt`

```
transformers>=4.36.0
datasets>=2.14.0
torch>=2.0.0
evaluate>=0.4.0
seqeval>=1.2.2
accelerate>=0.25.0
```

---

## 6. Gelernte Lektionen

### 6.1 Fehler ISS-001: Unzureichende Tokenisierung

**Ursache:** Annahme, dass Tokenisierung durch Leerzeichen für NER mit Transformer-Modellen ausreichend sei.

**Potenzielle Auswirkung:** Wenn mit Datensatz v1 trainiert worden wäre:
- Geschätzter F1-Abfall: -15% bis -25%
- Entitäten mit Interpunktion nicht erkannt
- Schlechte Generalisierung auf echten Text

**Künftige Prävention:**
1. Immer den Tokenizer des Basismodells verwenden
2. Datensatz-Audit vor dem Training implementieren
3. Subword-Label-Ausrichtung explizit überprüfen

### 6.2 Wichtigkeit der Vorabrecherche

Die Untersuchung von Best Practices VOR der Implementierung verhinderte:
- Suboptimale Hyperparameter (z.B. learning_rate=1e-4 verursacht Divergenz)
- Falsche Architektur (z.B. ohne CRF-Layer in klassischem NER)
- Falsche Evaluierung (z.B. Accuracy vs F1 für NER)

### 6.3 Synthetische Daten: Stärken und Grenzen

**Stärken:**
- Totale Kontrolle über Entitätsverteilung
- Abdeckung von Randfällen (archaische Namen, seltene Formate)
- Skalierbares Volumen ohne Annotationskosten

**Grenzen:**
- Künstliche Sprachmuster
- Kein echtes Rauschen (OCR-Fehler, Tippfehler)
- Erfordert Validierung an echten Daten

---

## 7. Zukünftige Arbeit

### 7.1 Sofort (Nächste Schritte)

1. **Training ausführen:**
   ```bash
   cd ml
   source .venv/bin/activate
   pip install -r scripts/train/requirements_train.txt
   python scripts/train/train_ner.py
   ```

2. **Evaluierung nach Entitätstyp:**
   - Verifizierung F1 ≥ 0,85 für jede Kategorie
   - Identifizierung problematischer Entitäten

3. **Adversarial Test:**
   - Ungesehene archaische Namen
   - Mehrdeutige Datumsformate
   - Unvollständige Adressen

### 7.2 Potenzielle Verbesserungen

| Verbesserung | Priorität | Erwartete Auswirkung |
|--------|-----------|------------------|
| CRF Layer | Hoch | +4-13% F1 |
| Echte annotierte Daten | Hoch | Bessere Generalisierung |
| Data Augmentation | Mittel | +2-5% F1 |
| Ensemble mit Regex | Mittel | +3-5% Recall |
| Active Learning | Niedrig | Reduzierung Annotationskosten |

### 7.3 Optionale Ressourcen

Akademische Paper, die noch evaluiert werden müssen:
- MAPA Project (aclanthology.org/2022.lrec-1.400/) - Legal PII annotiert
- 3CEL Contracts (arxiv.org/abs/2501.15990) - Vertragsklauseln
- IMPACT-es Corpus (arxiv.org/pdf/1306.3692.pdf) - Historische Namen

---

## 8. Projektstruktur

```
ml/
├── data/
│   ├── raw/
│   │   ├── conll2002/              # Standard NER Korpus
│   │   ├── gazetteers_ine/         # Original INE Excel
│   │   ├── municipios/             # Gemeinden 2024
│   │   ├── codigos_postales/       # Spanien PLZ
│   │   └── ai4privacy/             # Transfer Learning Datensatz
│   └── processed/
│       ├── gazetteers/             # Verarbeitete JSONs
│       ├── synthetic_sentences/     # Sätze v1 (verworfen)
│       └── ner_dataset_v2/         # Finaler HuggingFace Datensatz
├── models/
│   ├── checkpoints/                # Basismodell RoBERTa-BNE
│   └── legal_ner_v1/               # Trainings-Output (ausstehend)
├── scripts/
│   ├── preprocess/
│   │   ├── parse_ine_gazetteers.py
│   │   ├── generate_archaic_names.py
│   │   ├── generate_textual_dates.py
│   │   ├── generate_administrative_ids.py
│   │   ├── generate_addresses.py
│   │   ├── generate_organizations.py
│   │   ├── generate_ner_dataset_v2.py
│   │   └── audit_dataset.py
│   └── train/
│       ├── train_ner.py
│       └── requirements_train.txt
└── docs/
    ├── checklists/
    │   └── 2026-02-02_descargas_fase1.md
    └── reports/
        └── 2026-01-15_estado_proyecto_ner.md  # Dieses Dokument
```

---

## 9. Schlussfolgerungen

1. **Vorbereitung abgeschlossen:** Gazetteers, Datensatz v2 und Trainingsskript bereit.

2. **Kritischen Fehler vermieden:** Der Audit von Datensatz v1 identifizierte Probleme, die das Modell erheblich verschlechtert hätten.

3. **Best Practices angewendet:** Hyperparameter basierend auf Recherche, nicht auf Annahmen.

4. **Nächster Meilenstein:** Training ausführen und F1 pro Entität bewerten.

---

---

## 10. Referenzen

### Modelle und Datensätze

1. **RoBERTa-BNE-capitel-ner** - PlanTL-GOB-ES
   - https://huggingface.co/PlanTL-GOB-ES/roberta-base-bne-capitel-ner
   - F1 88,5% auf CAPITEL

2. **CoNLL-2002 Spanish** - Standard NER Korpus
   - https://www.clips.uantwerpen.be/conll2002/ner/

3. **ai4privacy/pii-masking-300k** - Englisch PII Datensatz
   - https://huggingface.co/datasets/ai4privacy/pii-masking-300k

### Offizielle INE Daten

4. **Namen nach Häufigkeit** - INE
   - https://www.ine.es/daco/daco42/nombyam/nombres_por_edad.xls

5. **Nachnamen nach Häufigkeit** - INE
   - https://www.ine.es/daco/daco42/nombyam/apellidos_frecuencia.xls

6. **Gemeinden Spanien 2024** - INE
   - https://www.ine.es/daco/daco42/codmun/

### Paper und Dokumentation

7. **RoBERTa: A Robustly Optimized BERT Pretraining Approach** - Liu et al., 2019
   - https://arxiv.org/abs/1907.11692
   - Referenz für Warmup Ratio 6%

8. **HuggingFace Token Classification Guide**
   - https://huggingface.co/docs/transformers/tasks/token_classification
   - Anleitung zur Subword-Label-Ausrichtung

9. **seqeval: A Python framework for sequence labeling evaluation**
   - https://github.com/chakki-works/seqeval
   - Entity-Level-Metriken für NER

### Paper in Evaluierung

10. **MAPA Project** - Legal PII annotiert
    - https://aclanthology.org/2022.lrec-1.400/

11. **3CEL Contracts** - Vertragsklauseln
    - https://arxiv.org/abs/2501.15990

12. **IMPACT-es Corpus** - Historische Namen
    - https://arxiv.org/pdf/1306.3692.pdf

---

**Letztes Update:** 2026-02-03
**Nächste Überprüfung:** Post-Training
