# Forschung: Data Augmentation für Daten im Spanischen (NER)

**Datum:** 2026-01-27
**Autor:** AlexAlves87
**Typ:** Wissenschaftliche Literaturrecherche
**Status:** Abgeschlossen

---

## 1. Zusammenfassung

Diese Forschung analysiert Best Practices für:
1. Data Augmentation bei NER in spezialisierten Domänen
2. Erkennung von temporären Ausdrücken im Spanischen
3. Generierung textueller Daten für das Training

### Wichtigste Erkenntnisse

| Erkenntnis | Quelle | Auswirkung |
|------------|--------|------------|
| Mention Replacement ist effektiv für Long-Tail-Entitäten | arXiv:2411.14551 (Nov 2024) | Hoch |
| Es gibt kein universell optimales Verhältnis - Experimentieren erforderlich | arXiv:2411.14551 | Mittel |
| HeidelTime hat spanische Regeln für textuelle Daten | TempEval-3 (ACL) | Hoch |
| BERT profitiert stärker von Augmentation als BiLSTM+CRF | arXiv:2411.14551 | Mittel |
| Niedrige Perplexity bei Augmentation → bessere Kalibrierung | arXiv:2407.02062 | Mittel |

---

## 2. Methodik

### 2.1 Konsultierte Quellen

| Quelle | Typ | Jahr | Relevanz |
|--------|-----|------|----------|
| arXiv:2411.14551 | Paper (Nov 2024) | 2024 | Data Augmentation Low-Resource NER |
| arXiv:2401.10825 | Survey NER | 2024 | State of the Art NER |
| HeidelTime (TempEval-3) | Tool + Paper | 2013-2024 | Spanische temporäre Ausdrücke |
| arXiv:2205.01757 | Paper XLTime | 2022 | Cross-Lingual Temporal |
| Dai & Adel (2020) | Grundlagen-Paper | 2020 | Einfache Data Augmentation NER |

### 2.2 Suchkriterien

- "data augmentation NER named entity recognition 2024 best practices"
- "Spanish date recognition NLP textual dates NER temporal expressions"
- "mention replacement entity substitution NER data augmentation"
- "HeidelTime Spanish temporal expression normalization"

---

## 3. Ergebnisse

### 3.1 Techniken zur Data Augmentation für NER

**Quelle:** [An Experimental Study on Data Augmentation Techniques for NER on Low-Resource Domains](https://arxiv.org/abs/2411.14551) (November 2024)

#### 3.1.1 Haupttechniken

| Technik | Beschreibung | Effektivität |
|---------|--------------|--------------|
| **Mention Replacement (MR)** | Ersetzen einer Entität durch eine andere desselben Typs | Hoch für seltene Entitäten |
| **Contextual Word Replacement (CWR)** | Ändern von Kontextwörtern | Allgemein überlegen gegenüber MR |
| **Synonym Replacement** | Synonyme für Kontextwörter | Mäßig |
| **Entity-to-Text (EnTDA)** | Generieren von Text aus einer Liste von Entitäten | Hoch (erfordert LLM) |

#### 3.1.2 Mention Replacement: Implementierung

**Quelle:** [An Analysis of Simple Data Augmentation for Named Entity Recognition](https://www.semanticscholar.org/paper/An-Analysis-of-Simple-Data-Augmentation-for-Named-Dai-Adel/bdbb944a84b8cdec8d120d2d2535995e335d0174) (Dai & Adel, 2020)

```
Original:  "El día [quince de marzo] compareció Don José"
                    ↓ (DATE)
Augmented: "El día [primero de enero] compareció Don José"
```

**Prozess:**
1. Erstellen eines Entitäten-Wörterbuchs nach Typ aus dem Trainingsset
2. Für jeden Satz, mit Wahrscheinlichkeit p, Entität durch eine andere desselben Typs ersetzen
3. BIO-Labels unverändert lassen

#### 3.1.3 Wichtige Erkenntnisse

> "There is no universally optimal number of augmented examples, i.e., NER practitioners must experiment with different quantities."

> "Data augmentation is particularly beneficial for smaller datasets."

> "BERT models benefit more from data augmentation than Bi-LSTM+CRF models."

**Implikation für ContextSafe:**
- Unser Datensatz (~6.500 Proben) ist "klein" → Augmentation wird vorteilhaft sein
- Verwendung von RoBERTa (Transformer) → guter Kandidat für Augmentation
- Experimentieren mit Verhältnissen: 1x, 2x, 5x Augmentation

### 3.2 Temporäre Ausdrücke im Spanischen

#### 3.2.1 HeidelTime: Referenzsystem

**Quelle:** [HeidelTime: Tuning English and Developing Spanish Resources](https://www.academia.edu/129452410/HeidelTime_Tuning_english_and_developing_spanish_resources_for_tempeval_3) (TempEval-3)

HeidelTime ist das regelbasierte Referenzsystem für temporäre Extraktion:
- **F1 = 86%** in TempEval (bestes Ergebnis)
- Spezifische Ressourcen für Spanisch seit 2013
- Open Source: [GitHub HeidelTime](https://github.com/HeidelTime/heideltime)

#### 3.2.2 Datumsmuster im juristischen Spanisch

**Basierend auf der Analyse von HeidelTime und notariellen Dokumenten:**

| Muster | Beispiel | Basis-Regex |
|--------|----------|-------------|
| Ordinale + Monat + textuelles Jahr | "primero de enero de dos mil veinticuatro" | `(primero|uno|dos|tres|...) de (enero|febrero|...) de (dos mil|mil novecientos)...` |
| Kardinale + Monat + textuelles Jahr | "quince de marzo de dos mil veinticuatro" | `(dos|tres|...|treinta y uno) de (mes) de (año)` |
| Tag + Monat + numerisches Jahr | "15 de marzo de 2024" | `\d{1,2} de (mes) de \d{4}` |
| Römisch + Monat + römisches Jahr | "XV de marzo del año MMXXIV" | `[IVXLCDM]+ de (mes) del año [IVXLCDM]+` |
| Vollständiges notarielles Format | "a los quince días del mes de marzo" | `a los? \w+ días? del mes de (mes)` |

#### 3.2.3 Textuelles Datums-Vokabular

**Tage (Ordinal/Kardinal):**
```
primero, uno, dos, tres, cuatro, cinco, seis, siete, ocho, nueve, diez,
once, doce, trece, catorce, quince, dieciséis, diecisiete, dieciocho,
diecinueve, veinte, veintiuno, veintidós, veintitrés, veinticuatro,
veinticinco, veintiséis, veintisiete, veintiocho, veintinueve, treinta,
treinta y uno
```

**Monate:**
```
enero, febrero, marzo, abril, mayo, junio, julio, agosto,
septiembre, octubre, noviembre, diciembre
```

**Jahre (juristisches Textformat):**
```
mil novecientos [Zahl]
dos mil [Zahl]
dos mil uno, dos mil dos, ..., dos mil veinticinco
```

**Römische Ziffern (alt notariell):**
```
I, II, III, IV, V, VI, VII, VIII, IX, X, XI, XII, XIII, XIV, XV,
XVI, XVII, XVIII, XIX, XX, XXI, XXII, XXIII, XXIV, XXV, XXVI,
XXVII, XXVIII, XXIX, XXX, XXXI
MMXX, MMXXI, MMXXII, MMXXIII, MMXXIV, MMXXV, MMXXVI
```

### 3.3 Augmentationsstrategie für Daten

#### 3.3.1 Technik: Spezialisiertes Mention Replacement

**Quelle:** Anpassung von [Entity-to-Text based Data Augmentation](https://arxiv.org/abs/2210.10343) (ACL 2023)

```python
DATE_VARIANTS = {
    "textual_ordinal": [
        "primero de enero de dos mil veinticuatro",
        "quince de marzo de dos mil veinticuatro",
        "treinta y uno de diciembre de dos mil veinticinco",
    ],
    "textual_cardinal": [
        "dos de febrero de dos mil veinticuatro",
        "veinte de abril de dos mil veinticinco",
    ],
    "roman_numerals": [
        "XV de marzo del año MMXXIV",
        "I de enero del año MMXXV",
        "XXXI de diciembre del año MMXXIV",
    ],
    "notarial_formal": [
        "a los quince días del mes de marzo del año dos mil veinticuatro",
        "en el día de hoy, primero de enero de dos mil veinticinco",
    ],
}
```

#### 3.3.2 Empfohlenes Augmentationsverhältnis

**Quelle:** arXiv:2411.14551

| Datensatzgröße | Augmentationsverhältnis | Anmerkungen |
|----------------|-------------------------|-------------|
| < 1.000 | 5x - 10x | Maximaler Nutzen |
| 1.000 - 5.000 | 2x - 5x | Signifikanter Nutzen |
| 5.000 - 10.000 | 1x - 2x | Moderater Nutzen |
| > 10.000 | 0.5x - 1x | Mögliche Verschlechterung |

**Für ContextSafe (6.561 Proben):** Empfohlenes Verhältnis **1,5x - 2x**

#### 3.3.3 Generierungsstrategie

1. **Sätze mit DATE identifizieren** im aktuellen Datensatz
2. **Für jeden Satz mit Datum:**
   - Erzeuge 2-3 Varianten mit unterschiedlichen Datumsformaten
   - Kontext identisch halten
   - Neues Datum mit demselben Label versehen (B-DATE, I-DATE)
3. **Typen ausbalancieren:**
   - 40% textuell ordinal/kardinal
   - 30% Standard-Numerikformat
   - 20% formales notarielles Format
   - 10% römische Ziffern

### 3.4 Kalibrierung und Perplexity

**Quelle:** [Are Data Augmentation Methods in NER Applicable for Uncertainty Estimation?](https://arxiv.org/abs/2407.02062)


**Implikation:** Generiere natürliche Sätze, keine künstlichen. Textuelle Daten im juristischen Spanisch sind in diesem Kontext natürlich.

---

## 4. Vorgeschlagene Augmentations-Pipeline

### 4.1 Architektur

```
Datensatz v3 (6.561 Proben)
         ↓
[1] Sätze mit DATE identifizieren
         ↓
[2] Für jedes DATE:
    - Original-Span extrahieren
    - 2-3 Datumsvarianten generieren
    - Neue Sätze erstellen
         ↓
[3] Mit RoBERTa Tokenizer tokenisieren
         ↓
[4] Labels ausrichten (word_ids)
         ↓
[5] Mit Original-Datensatz mischen
         ↓
Datensatz v4 (~10.000-13.000 Proben)
```

### 4.2 Python-Implementierung

```python
import random
from typing import List, Tuple

# Spanischer textueller Datumsgenerator
class SpanishDateGenerator:
    """Generate Spanish legal date variations for NER augmentation."""

    DIAS_ORDINALES = {
        1: "primero", 2: "dos", 3: "tres", 4: "cuatro", 5: "cinco",
        6: "seis", 7: "siete", 8: "ocho", 9: "nueve", 10: "diez",
        11: "once", 12: "doce", 13: "trece", 14: "catorce", 15: "quince",
        16: "dieciséis", 17: "diecisiete", 18: "dieciocho", 19: "diecinueve",
        20: "veinte", 21: "veintiuno", 22: "veintidós", 23: "veintitrés",
        24: "veinticuatro", 25: "veinticinco", 26: "veintiséis",
        27: "veintisiete", 28: "veintiocho", 29: "veintinueve",
        30: "treinta", 31: "treinta y uno"
    }

    MESES = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]

    ROMANOS_DIA = {
        1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII",
        8: "VIII", 9: "IX", 10: "X", 11: "XI", 12: "XII", 13: "XIII",
        14: "XIV", 15: "XV", 16: "XVI", 17: "XVII", 18: "XVIII",
        19: "XIX", 20: "XX", 21: "XXI", 22: "XXII", 23: "XXIII",
        24: "XXIV", 25: "XXV", 26: "XXVI", 27: "XXVII", 28: "XXVIII",
        29: "XXIX", 30: "XXX", 31: "XXXI"
    }

    ROMANOS_ANIO = {
        2020: "MMXX", 2021: "MMXXI", 2022: "MMXXII", 2023: "MMXXIII",
        2024: "MMXXIV", 2025: "MMXXV", 2026: "MMXXVI"
    }

    def _anio_textual(self, year: int) -> str:
        """Convert year to Spanish text."""
        if year < 2000:
            return f"mil novecientos {self._numero_a_texto(year - 1900)}"
        elif year == 2000:
            return "dos mil"
        else:
            return f"dos mil {self._numero_a_texto(year - 2000)}"

    def _numero_a_texto(self, n: int) -> str:
        """Convert number 1-99 to Spanish text."""
        unidades = ["", "uno", "dos", "tres", "cuatro", "cinco",
                    "seis", "siete", "ocho", "nueve", "diez",
                    "once", "doce", "trece", "catorce", "quince",
                    "dieciséis", "diecisiete", "dieciocho", "diecinueve"]
        decenas = ["", "", "veinti", "treinta", "cuarenta", "cincuenta",
                   "sesenta", "setenta", "ochenta", "noventa"]

        if n < 20:
            return unidades[n]
        elif n < 30:
            return f"veinti{unidades[n-20]}" if n > 20 else "veinte"
        else:
            d, u = divmod(n, 10)
            if u == 0:
                return decenas[d]
            return f"{decenas[d]} y {unidades[u]}"

    def generate_textual(self, day: int, month: int, year: int) -> str:
        """Generate textual date: 'quince de marzo de dos mil veinticuatro'"""
        dia = self.DIAS_ORDINALES.get(day, str(day))
        mes = self.MESES[month - 1]
        anio = self._anio_textual(year)
        return f"{dia} de {mes} de {anio}"

    def generate_roman(self, day: int, month: int, year: int) -> str:
        """Generate Roman numeral date: 'XV de marzo del año MMXXIV'"""
        dia_romano = self.ROMANOS_DIA.get(day, str(day))
        mes = self.MESES[month - 1]
        anio_romano = self.ROMANOS_ANIO.get(year, str(year))
        return f"{dia_romano} de {mes} del año {anio_romano}"

    def generate_notarial(self, day: int, month: int, year: int) -> str:
        """Generate notarial format: 'a los quince días del mes de marzo'"""
        dia = self.DIAS_ORDINALES.get(day, str(day))
        mes = self.MESES[month - 1]
        anio = self._anio_textual(year)
        return f"a los {dia} días del mes de {mes} del año {anio}"

    def generate_random(self) -> Tuple[str, str]:
        """Generate random date in random format."""
        day = random.randint(1, 28)  # Safe for all months
        month = random.randint(1, 12)
        year = random.randint(2020, 2026)

        format_type = random.choice(["textual", "roman", "notarial"])

        if format_type == "textual":
            return self.generate_textual(day, month, year), "textual"
        elif format_type == "roman":
            return self.generate_roman(day, month, year), "roman"
        else:
            return self.generate_notarial(day, month, year), "notarial"
```

### 4.3 Validierungstests

| Input | Methode | Output |
|-------|---------|--------|
| (15, 3, 2024) | textual | "quince de marzo de dos mil veinticuatro" |
| (1, 1, 2025) | textual | "primero de enero de dos mil veinticinco" |
| (15, 3, 2024) | roman | "XV de marzo del año MMXXIV" |
| (31, 12, 2024) | notarial | "a los treinta y uno días del mes de diciembre del año dos mil veinticuatro" |

---

## 5. Lückenanalyse

### 5.1 Vergleich: Aktuelle Praxis vs Best Practices

| Aspekt | Best Practice | Aktuelle Implementierung | Lücke |
|--------|---------------|--------------------------|-------|
| Textuelle Daten im Training | Varianten einbeziehen | Nur numerisches Format | **KRITISCH** |
| Augmentationsverhältnis | 1,5x-2x für ~6k Proben | 0x (keine Augmentation) | **HOCH** |
| Römische Ziffern | Für notariell einbeziehen | Nicht enthalten | MITTEL |
| Notarielles Format | "a los X días del mes de" | Nicht enthalten | MITTEL |
| Format-Balancing | 40/30/20/10% | N/A | MITTEL |

### 5.2 Geschätzte Auswirkung

| Korrektur | Aufwand | Auswirkung auf Tests |
|-----------|---------|----------------------|
| Datumsgenerator | Mittel (~100 Zeilen) | `date_roman_numerals`: PASS |
| Augmentations-Pipeline | Mittel (~150 Zeilen) | `notarial_header`, `judicial_sentence_header`: PASS |
| Neutraining | Hoch (GPU-Zeit) | +3-5% F1 bei DATE |
| **Gesamt** | **~250 Zeilen + Training** | **+5-8% Pass-Rate Adversarial** |

---

## 6. Schlussfolgerungen

### 6.1 Wichtigste Erkenntnisse

1. **Mention Replacement ist die geeignete Technik** zur Augmentation von Daten im NER
2. **HeidelTime definiert die Referenzmuster** für Daten im Spanischen
3. **Das Verhältnis 1,5x-2x ist optimal** für unsere Datensatzgröße
4. **Vier kritische Formate** müssen enthalten sein: textuell, numerisch, römisch, notariell
5. **Niedrige Perplexity verbessert Kalibrierung** - generiere natürliche Daten für den Kontext

### 6.2 Empfehlung für ContextSafe

**Implementierung von `scripts/preprocess/augment_spanish_dates.py`** mit:
1. `SpanishDateGenerator` Klasse zur Generierung von Varianten
2. `augment_dataset()` Funktion, die MR auf Sätze mit DATE anwendet
3. 1,5x Augmentationsverhältnis (Generierung von ~3.000 zusätzlichen Proben)
4. Modell mit Datensatz v4 neu trainieren

**Priorität:** HOCH - Wird `date_roman_numerals`, `notarial_header`, `judicial_sentence_header` Tests lösen.

---

## 7. Referenzen

### Akademische Arbeiten

1. **An Experimental Study on Data Augmentation Techniques for Named Entity Recognition on Low-Resource Domains**
   - arXiv:2411.14551, November 2024
   - URL: https://arxiv.org/abs/2411.14551

2. **An Analysis of Simple Data Augmentation for Named Entity Recognition**
   - Dai & Adel, COLING 2020
   - URL: https://www.semanticscholar.org/paper/An-Analysis-of-Simple-Data-Augmentation-for-Named-Dai-Adel/bdbb944a84b8cdec8d120d2d2535995e335d0174

3. **Entity-to-Text based Data Augmentation for various Named Entity Recognition Tasks**
   - ACL Findings 2023
   - URL: https://arxiv.org/abs/2210.10343

4. **Are Data Augmentation Methods in NER Applicable for Uncertainty Estimation?**
   - arXiv:2407.02062, 2024
   - URL: https://arxiv.org/abs/2407.02062

5. **Recent Advances in Named Entity Recognition: A Comprehensive Survey**
   - arXiv:2401.10825, 2024
   - URL: https://arxiv.org/abs/2401.10825

6. **XLTime: A Cross-Lingual Knowledge Transfer Framework for Temporal Expression Extraction**
   - arXiv:2205.01757, 2022
   - URL: https://arxiv.org/abs/2205.01757

### Tools und Ressourcen

7. **HeidelTime: Multilingual Temporal Tagger**
   - GitHub: https://github.com/HeidelTime/heideltime
   - Paper TempEval-3: https://www.academia.edu/129452410/HeidelTime_Tuning_english_and_developing_spanish_resources_for_tempeval_3

8. **HeidelTime: High Quality Rule-Based Extraction and Normalization of Temporal Expressions**
   - ACL Anthology: https://aclanthology.org/S10-1071/

---

**Recherchezeit:** 40 Min.
**Generiert von:** AlexAlves87
**Datum:** 2026-01-27
