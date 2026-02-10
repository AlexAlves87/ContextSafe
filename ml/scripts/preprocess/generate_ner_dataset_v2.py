#!/usr/bin/env python3
"""
Generate synthetic NER dataset with CORRECT tokenization for BERT fine-tuning.

Key improvements over v1:
1. Uses HuggingFace tokenizer for proper subword handling
2. Aligns labels using word_ids() - industry standard
3. Ensures entity spans don't include punctuation
4. Balanced entity distribution
5. Outputs in HuggingFace datasets format

Output: data/processed/ner_dataset_v2/
"""

import json
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from collections import Counter

from transformers import AutoTokenizer
from datasets import Dataset, DatasetDict


BASE_DIR = Path(__file__).parent.parent.parent
GAZETTEERS_DIR = BASE_DIR / "gazetteers"
OUTPUT_DIR = BASE_DIR / "data" / "processed" / "ner_dataset_v2"

# Model for tokenization
MODEL_PATH = BASE_DIR / "models" / "checkpoints" / "roberta-base-bne-capitel-ner"


# =============================================================================
# ENTITY LABELS
# =============================================================================

ENTITY_LABELS = [
    "O",
    "B-PERSON", "I-PERSON",
    "B-LOCATION", "I-LOCATION",
    "B-ORGANIZATION", "I-ORGANIZATION",
    "B-DATE", "I-DATE",
    "B-DNI_NIE", "I-DNI_NIE",
    "B-IBAN", "I-IBAN",
    "B-NSS", "I-NSS",
    "B-PHONE", "I-PHONE",
    "B-ADDRESS", "I-ADDRESS",
    "B-POSTAL_CODE", "I-POSTAL_CODE",
    "B-LICENSE_PLATE", "I-LICENSE_PLATE",
    "B-CADASTRAL_REF", "I-CADASTRAL_REF",
    "B-ECLI", "I-ECLI",
    "B-PROFESSIONAL_ID", "I-PROFESSIONAL_ID",
]

LABEL2ID = {label: i for i, label in enumerate(ENTITY_LABELS)}
ID2LABEL = {i: label for i, label in enumerate(ENTITY_LABELS)}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Entity:
    """Entity with character-level span."""
    text: str
    label: str
    start: int
    end: int


@dataclass
class AnnotatedSentence:
    """Sentence with entity annotations."""
    text: str
    entities: list[Entity] = field(default_factory=list)

    def validate(self) -> bool:
        """Validate entity spans."""
        for e in self.entities:
            # Check bounds
            if e.start < 0 or e.end > len(self.text):
                return False
            # Check text matches
            if self.text[e.start:e.end] != e.text:
                return False
            # Check no leading/trailing punctuation
            if e.text and e.text[-1] in ",.;:!?":
                return False
            if e.text and e.text[0] in ",.;:!?":
                return False
        return True


# =============================================================================
# GAZETTEER LOADER
# =============================================================================

class GazetteerLoader:
    """Loads gazetteers with clean data."""

    def __init__(self):
        self.data = {}

    def load_all(self):
        """Load all gazetteers."""
        print("Loading gazetteers...")

        # Nombres arcaicos
        with open(GAZETTEERS_DIR / "nombres_arcaicos.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            self.data["nombres_h"] = [n.title() for n in data["nombres_arcaicos"]["hombres"]]
            self.data["nombres_m"] = [n.title() for n in data["nombres_arcaicos"]["mujeres"]]

        # Apellidos
        with open(GAZETTEERS_DIR / "apellidos.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            self.data["apellidos"] = [a["apellido"].title() for a in data["apellidos"]]

        # Municipios
        with open(GAZETTEERS_DIR / "municipios.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            self.data["municipios"] = data["municipios"]

        # Códigos postales
        with open(GAZETTEERS_DIR / "codigos_postales.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            self.data["codigos_postales"] = [cp["codigo_postal"] for cp in data["codigos_postales"]]

        # Fechas textuales - CLEAN (remove trailing punctuation)
        with open(GAZETTEERS_DIR / "fechas_textuales_flat.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            self.data["fechas"] = [self._clean_text(f) for f in data["todos_textos"]]

        # Identificadores administrativos - CLEAN
        with open(GAZETTEERS_DIR / "identificadores_administrativos.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            self.data["dnis"] = [self._clean_text(d["texto"]) for d in data["datos"]["DNI"]]
            self.data["nies"] = [self._clean_text(d["texto"]) for d in data["datos"]["NIE"]]
            self.data["ibans"] = [self._clean_text(d["texto"]) for d in data["datos"]["IBAN"]]
            self.data["nss"] = [self._clean_text(d["texto"]) for d in data["datos"]["NSS"]]
            self.data["telefonos"] = [self._clean_text(d["texto"]) for d in data["datos"]["TELEFONO"]]
            self.data["matriculas"] = [self._clean_text(d["texto"]) for d in data["datos"]["MATRICULA"]]
            self.data["refs_catastrales"] = [self._clean_text(d["texto"]) for d in data["datos"]["REFERENCIA_CATASTRAL"]]
            self.data["eclis"] = [self._clean_text(d["texto"]) for d in data["datos"]["ECLI"]]
            self.data["ids_profesionales"] = [self._clean_text(d["texto"]) for d in data["datos"]["ID_PROFESIONAL"]]

        # Direcciones - CLEAN
        with open(GAZETTEERS_DIR / "direcciones_flat.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            self.data["direcciones"] = [self._clean_text(d) for d in data["todos_textos"]]

        # Organizaciones - CLEAN
        with open(GAZETTEERS_DIR / "organizaciones_flat.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            self.data["organizaciones"] = [self._clean_text(o) for o in data["todos_textos"]]

        for key, values in self.data.items():
            print(f"  {key}: {len(values)}")

    def _clean_text(self, text: str) -> str:
        """Remove trailing punctuation from text."""
        return text.rstrip(",.;:!?").lstrip(",.;:!?")

    def get_nombre_completo(self, genero: str = "M") -> str:
        """Get a full name without title."""
        if genero == "M":
            nombre = random.choice(self.data["nombres_h"])
        else:
            nombre = random.choice(self.data["nombres_m"])

        ap1 = random.choice(self.data["apellidos"])
        ap2 = random.choice(self.data["apellidos"])

        return f"{nombre} {ap1} {ap2}"

    def get(self, key: str) -> str:
        """Get random item from gazetteer."""
        return random.choice(self.data[key])


# =============================================================================
# TEMPLATE-BASED SENTENCE GENERATOR
# =============================================================================

class SentenceGenerator:
    """
    Generates sentences with CLEAN entity annotations.

    Key principle: Entity text must NOT include surrounding punctuation.
    """

    def __init__(self, gazetteer: GazetteerLoader):
        self.gaz = gazetteer

    def generate(self, template_type: str = "random") -> AnnotatedSentence:
        """Generate a sentence from templates."""
        if template_type == "random":
            template_type = random.choice([
                "testamento", "contrato", "sentencia", "escritura",
                "laboral", "nss", "ecli", "matricula", "catastral", "profesional"
            ])

        generator = getattr(self, f"_gen_{template_type}", self._gen_testamento)
        return generator()

    def _make_sentence(self, parts: list) -> AnnotatedSentence:
        """
        Build sentence from parts, tracking entity positions.

        Parts can be:
        - str: literal text
        - tuple: (text, label) for entities
        """
        text_parts = []
        entities = []
        current_pos = 0

        for part in parts:
            if isinstance(part, tuple):
                entity_text, label = part
                # Clean entity text
                entity_text = entity_text.rstrip(",.;:!?").lstrip(",.;:!?")

                start = current_pos
                end = start + len(entity_text)

                entities.append(Entity(
                    text=entity_text,
                    label=label,
                    start=start,
                    end=end
                ))
                text_parts.append(entity_text)
                current_pos = end
            else:
                text_parts.append(part)
                current_pos += len(part)

        return AnnotatedSentence(text="".join(text_parts), entities=entities)

    # =========================================================================
    # TEMPLATE GENERATORS
    # =========================================================================

    def _gen_testamento(self) -> AnnotatedSentence:
        """Generate testamento-style sentence."""
        patterns = [
            lambda: self._make_sentence([
                "En ", (self.gaz.get("municipios"), "LOCATION"),
                ", a ", (self.gaz.get("fechas"), "DATE"),
                ", comparece ", (f"Don {self.gaz.get_nombre_completo('M')}", "PERSON"),
                ", con DNI ", (self.gaz.get("dnis"), "DNI_NIE"),
                "."
            ]),
            lambda: self._make_sentence([
                (f"Doña {self.gaz.get_nombre_completo('F')}", "PERSON"),
                ", mayor de edad, vecina de ", (self.gaz.get("municipios"), "LOCATION"),
                ", con domicilio en ", (self.gaz.get("direcciones"), "ADDRESS"),
                ", otorga testamento."
            ]),
            lambda: self._make_sentence([
                "El testador ", (f"Don {self.gaz.get_nombre_completo('M')}", "PERSON"),
                ", nacido en ", (self.gaz.get("municipios"), "LOCATION"),
                " el día ", (self.gaz.get("fechas"), "DATE"),
                ", con DNI número ", (self.gaz.get("dnis"), "DNI_NIE"),
                "."
            ]),
            lambda: self._make_sentence([
                "Instituye heredero a ", (f"Don {self.gaz.get_nombre_completo('M')}", "PERSON"),
                ", con NIE ", (self.gaz.get("nies"), "DNI_NIE"),
                ", domiciliado en ", (self.gaz.get("direcciones"), "ADDRESS"),
                ", ", (self.gaz.get("codigos_postales"), "POSTAL_CODE"),
                " ", (self.gaz.get("municipios"), "LOCATION"),
                "."
            ]),
        ]
        return random.choice(patterns)()

    def _gen_contrato(self) -> AnnotatedSentence:
        """Generate contrato-style sentence."""
        patterns = [
            lambda: self._make_sentence([
                "De una parte, ", (f"Don {self.gaz.get_nombre_completo('M')}", "PERSON"),
                ", con DNI ", (self.gaz.get("dnis"), "DNI_NIE"),
                ", en representación de ", (self.gaz.get("organizaciones"), "ORGANIZATION"),
                "."
            ]),
            lambda: self._make_sentence([
                "El arrendador ", (f"Doña {self.gaz.get_nombre_completo('F')}", "PERSON"),
                " cede el inmueble en ", (self.gaz.get("direcciones"), "ADDRESS"),
                " por el precio de MIL EUROS a ingresar en ", (self.gaz.get("ibans"), "IBAN"),
                "."
            ]),
            lambda: self._make_sentence([
                "Las partes, ", (self.gaz.get("organizaciones"), "ORGANIZATION"),
                " y ", (f"Don {self.gaz.get_nombre_completo('M')}", "PERSON"),
                ", firman en ", (self.gaz.get("municipios"), "LOCATION"),
                " a ", (self.gaz.get("fechas"), "DATE"),
                "."
            ]),
            lambda: self._make_sentence([
                "Contacto: ", (f"Doña {self.gaz.get_nombre_completo('F')}", "PERSON"),
                ", teléfono ", (self.gaz.get("telefonos"), "PHONE"),
                ", domicilio en ", (self.gaz.get("direcciones"), "ADDRESS"),
                "."
            ]),
        ]
        return random.choice(patterns)()

    def _gen_sentencia(self) -> AnnotatedSentence:
        """Generate sentencia-style sentence."""
        patterns = [
            lambda: self._make_sentence([
                "En ", (self.gaz.get("municipios"), "LOCATION"),
                ", a ", (self.gaz.get("fechas"), "DATE"),
                ", el ", (self.gaz.get("organizaciones"), "ORGANIZATION"),
                " dicta sentencia."
            ]),
            lambda: self._make_sentence([
                "El demandante ", (f"Don {self.gaz.get_nombre_completo('M')}", "PERSON"),
                ", con DNI ", (self.gaz.get("dnis"), "DNI_NIE"),
                ", interpuso demanda contra ", (self.gaz.get("organizaciones"), "ORGANIZATION"),
                "."
            ]),
            lambda: self._make_sentence([
                "Se condena a ", (f"Doña {self.gaz.get_nombre_completo('F')}", "PERSON"),
                ", domiciliada en ", (self.gaz.get("direcciones"), "ADDRESS"),
                ", al pago de las costas."
            ]),
        ]
        return random.choice(patterns)()

    def _gen_escritura(self) -> AnnotatedSentence:
        """Generate escritura-style sentence."""
        patterns = [
            lambda: self._make_sentence([
                "El vendedor ", (f"Don {self.gaz.get_nombre_completo('M')}", "PERSON"),
                " transmite la finca con referencia catastral ", (self.gaz.get("refs_catastrales"), "CADASTRAL_REF"),
                " en ", (self.gaz.get("municipios"), "LOCATION"),
                "."
            ]),
            lambda: self._make_sentence([
                "La finca sita en ", (self.gaz.get("direcciones"), "ADDRESS"),
                ", con referencia catastral ", (self.gaz.get("refs_catastrales"), "CADASTRAL_REF"),
                ", se vende por precio a ingresar en ", (self.gaz.get("ibans"), "IBAN"),
                "."
            ]),
        ]
        return random.choice(patterns)()

    def _gen_laboral(self) -> AnnotatedSentence:
        """Generate laboral-style sentence."""
        patterns = [
            lambda: self._make_sentence([
                (f"Don {self.gaz.get_nombre_completo('M')}", "PERSON"),
                ", con DNI ", (self.gaz.get("dnis"), "DNI_NIE"),
                " y NSS ", (self.gaz.get("nss"), "NSS"),
                ", ha prestado servicios para ", (self.gaz.get("organizaciones"), "ORGANIZATION"),
                "."
            ]),
            lambda: self._make_sentence([
                "El trabajador ", (f"Doña {self.gaz.get_nombre_completo('F')}", "PERSON"),
                ", con número de afiliación ", (self.gaz.get("nss"), "NSS"),
                ", fue despedido el ", (self.gaz.get("fechas"), "DATE"),
                "."
            ]),
            lambda: self._make_sentence([
                "Se reconoce a ", (f"Don {self.gaz.get_nombre_completo('M')}", "PERSON"),
                ", NSS ", (self.gaz.get("nss"), "NSS"),
                ", una incapacidad."
            ]),
        ]
        return random.choice(patterns)()

    def _gen_nss(self) -> AnnotatedSentence:
        """Generate NSS-focused sentence (minority entity)."""
        patterns = [
            lambda: self._make_sentence([
                "El beneficiario con NSS ", (self.gaz.get("nss"), "NSS"),
                " es ", (f"Don {self.gaz.get_nombre_completo('M')}", "PERSON"),
                "."
            ]),
            lambda: self._make_sentence([
                "Número de afiliación: ", (self.gaz.get("nss"), "NSS"),
                ", titular: ", (f"Doña {self.gaz.get_nombre_completo('F')}", "PERSON"),
                "."
            ]),
            lambda: self._make_sentence([
                (f"Don {self.gaz.get_nombre_completo('M')}", "PERSON"),
                " con NSS ", (self.gaz.get("nss"), "NSS"),
                " solicita prestación."
            ]),
            lambda: self._make_sentence([
                "Cotizante: ", (f"Doña {self.gaz.get_nombre_completo('F')}", "PERSON"),
                ", número Seguridad Social ", (self.gaz.get("nss"), "NSS"),
                ", empresa ", (self.gaz.get("organizaciones"), "ORGANIZATION"),
                "."
            ]),
        ]
        return random.choice(patterns)()

    def _gen_ecli(self) -> AnnotatedSentence:
        """Generate ECLI-focused sentence (minority entity)."""
        patterns = [
            lambda: self._make_sentence([
                "Según la sentencia ", (self.gaz.get("eclis"), "ECLI"),
                ", el demandante ", (f"Don {self.gaz.get_nombre_completo('M')}", "PERSON"),
                " tiene derecho."
            ]),
            lambda: self._make_sentence([
                "La resolución ", (self.gaz.get("eclis"), "ECLI"),
                " del ", (self.gaz.get("organizaciones"), "ORGANIZATION"),
                " resuelve el recurso."
            ]),
            lambda: self._make_sentence([
                "Conforme a ", (self.gaz.get("eclis"), "ECLI"),
                ", se condena a ", (f"Doña {self.gaz.get_nombre_completo('F')}", "PERSON"),
                "."
            ]),
            lambda: self._make_sentence([
                "Citando ", (self.gaz.get("eclis"), "ECLI"),
                " y ", (self.gaz.get("eclis"), "ECLI"),
                ", el tribunal falla."
            ]),
        ]
        return random.choice(patterns)()

    def _gen_matricula(self) -> AnnotatedSentence:
        """Generate LICENSE_PLATE-focused sentence (minority entity)."""
        patterns = [
            lambda: self._make_sentence([
                "El vehículo matrícula ", (self.gaz.get("matriculas"), "LICENSE_PLATE"),
                " propiedad de ", (f"Don {self.gaz.get_nombre_completo('M')}", "PERSON"),
                "."
            ]),
            lambda: self._make_sentence([
                "Se embarga el turismo ", (self.gaz.get("matriculas"), "LICENSE_PLATE"),
                " de ", (f"Doña {self.gaz.get_nombre_completo('F')}", "PERSON"),
                ", con DNI ", (self.gaz.get("dnis"), "DNI_NIE"),
                "."
            ]),
            lambda: self._make_sentence([
                "Matrícula: ", (self.gaz.get("matriculas"), "LICENSE_PLATE"),
                ", propietario: ", (f"Don {self.gaz.get_nombre_completo('M')}", "PERSON"),
                ", domicilio: ", (self.gaz.get("direcciones"), "ADDRESS"),
                "."
            ]),
        ]
        return random.choice(patterns)()

    def _gen_catastral(self) -> AnnotatedSentence:
        """Generate CADASTRAL_REF-focused sentence (minority entity)."""
        patterns = [
            lambda: self._make_sentence([
                "Finca con referencia catastral ", (self.gaz.get("refs_catastrales"), "CADASTRAL_REF"),
                " en ", (self.gaz.get("municipios"), "LOCATION"),
                "."
            ]),
            lambda: self._make_sentence([
                "Ref. catastral: ", (self.gaz.get("refs_catastrales"), "CADASTRAL_REF"),
                ", propietario: ", (f"Don {self.gaz.get_nombre_completo('M')}", "PERSON"),
                "."
            ]),
            lambda: self._make_sentence([
                "El inmueble ", (self.gaz.get("refs_catastrales"), "CADASTRAL_REF"),
                " sito en ", (self.gaz.get("direcciones"), "ADDRESS"),
                " de ", (self.gaz.get("municipios"), "LOCATION"),
                "."
            ]),
        ]
        return random.choice(patterns)()

    def _gen_profesional(self) -> AnnotatedSentence:
        """Generate PROFESSIONAL_ID-focused sentence (minority entity)."""
        patterns = [
            lambda: self._make_sentence([
                "El abogado ", (f"Don {self.gaz.get_nombre_completo('M')}", "PERSON"),
                ", colegiado ", (self.gaz.get("ids_profesionales"), "PROFESSIONAL_ID"),
                ", asiste al demandante."
            ]),
            lambda: self._make_sentence([
                "Notario: ", (f"Doña {self.gaz.get_nombre_completo('F')}", "PERSON"),
                ", número de colegiado ", (self.gaz.get("ids_profesionales"), "PROFESSIONAL_ID"),
                ", de ", (self.gaz.get("municipios"), "LOCATION"),
                "."
            ]),
            lambda: self._make_sentence([
                "Interviene ", (f"Don {self.gaz.get_nombre_completo('M')}", "PERSON"),
                " con número ", (self.gaz.get("ids_profesionales"), "PROFESSIONAL_ID"),
                " del Colegio de ", (self.gaz.get("municipios"), "LOCATION"),
                "."
            ]),
        ]
        return random.choice(patterns)()


# =============================================================================
# TOKENIZATION AND LABEL ALIGNMENT
# =============================================================================

class TokenizerAligner:
    """
    Aligns entity labels with BERT subword tokens.

    Uses word_ids() for proper alignment:
    - First subword of each word gets the word's label
    - Continuation subwords get -100 (ignored in loss)
    - Special tokens get -100
    """

    def __init__(self, tokenizer_path: str):
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        print(f"Loaded tokenizer: {type(self.tokenizer).__name__}")

    def align(self, sentence: AnnotatedSentence, max_length: int = 128) -> dict:
        """
        Tokenize sentence and align labels.

        Returns dict with:
        - input_ids: token IDs
        - attention_mask: attention mask
        - labels: aligned label IDs (-100 for ignored)
        """
        text = sentence.text

        # Tokenize
        encoding = self.tokenizer(
            text,
            max_length=max_length,
            padding="max_length",
            truncation=True,
            return_offsets_mapping=True,
            return_tensors=None
        )

        # Get word IDs for alignment
        word_ids = encoding.word_ids()
        offsets = encoding["offset_mapping"]

        # Create character-level label array
        char_labels = ["O"] * len(text)
        for entity in sentence.entities:
            if entity.start < len(char_labels):
                char_labels[entity.start] = f"B-{entity.label}"
                for i in range(entity.start + 1, min(entity.end, len(char_labels))):
                    char_labels[i] = f"I-{entity.label}"

        # Align labels to tokens
        labels = []
        previous_word_id = None

        for i, (word_id, (start, end)) in enumerate(zip(word_ids, offsets)):
            if word_id is None:
                # Special token
                labels.append(-100)
            elif word_id != previous_word_id:
                # First subword of a new word - get label at start position
                if start < len(char_labels):
                    label_str = char_labels[start]
                    labels.append(LABEL2ID.get(label_str, LABEL2ID["O"]))
                else:
                    labels.append(LABEL2ID["O"])
            else:
                # Continuation subword - ignore in loss
                labels.append(-100)

            previous_word_id = word_id

        return {
            "input_ids": encoding["input_ids"],
            "attention_mask": encoding["attention_mask"],
            "labels": labels
        }


# =============================================================================
# DATASET BUILDER
# =============================================================================

def build_dataset(
    num_samples: int,
    gazetteer: GazetteerLoader,
    aligner: TokenizerAligner,
    balanced: bool = True
) -> list[dict]:
    """
    Build dataset with balanced entity distribution.
    """
    generator = SentenceGenerator(gazetteer)
    samples = []

    if balanced:
        # Generate more samples for minority entity types
        type_counts = {
            "testamento": num_samples // 6,
            "contrato": num_samples // 6,
            "sentencia": num_samples // 8,
            "escritura": num_samples // 8,
            "laboral": num_samples // 8,
            # Minority types - generate MORE
            "nss": num_samples // 5,
            "ecli": num_samples // 5,
            "matricula": num_samples // 5,
            "catastral": num_samples // 6,
            "profesional": num_samples // 6,
        }
    else:
        type_counts = {"random": num_samples}

    for template_type, count in type_counts.items():
        for _ in range(count):
            sentence = generator.generate(template_type)

            # Validate
            if not sentence.validate():
                continue

            # Align with tokenizer
            try:
                aligned = aligner.align(sentence)
                aligned["text"] = sentence.text
                aligned["entities"] = [
                    {"text": e.text, "label": e.label, "start": e.start, "end": e.end}
                    for e in sentence.entities
                ]
                samples.append(aligned)
            except Exception as e:
                print(f"Warning: Failed to align: {e}")
                continue

    return samples


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("GENERADOR DE DATASET NER v2 (CORREGIDO)")
    print("=" * 60)

    # Load gazetteers
    print("\n[1/5] Loading gazetteers...")
    gazetteer = GazetteerLoader()
    gazetteer.load_all()

    # Load tokenizer
    print("\n[2/5] Loading tokenizer...")
    aligner = TokenizerAligner(str(MODEL_PATH))

    # Generate datasets
    print("\n[3/5] Generating datasets...")

    train_samples = build_dataset(3000, gazetteer, aligner, balanced=True)
    print(f"  Train: {len(train_samples)} samples")

    dev_samples = build_dataset(500, gazetteer, aligner, balanced=True)
    print(f"  Dev: {len(dev_samples)} samples")

    test_samples = build_dataset(500, gazetteer, aligner, balanced=True)
    print(f"  Test: {len(test_samples)} samples")

    # Create HuggingFace datasets
    print("\n[4/5] Creating HuggingFace datasets...")

    def samples_to_dataset(samples):
        return Dataset.from_dict({
            "input_ids": [s["input_ids"] for s in samples],
            "attention_mask": [s["attention_mask"] for s in samples],
            "labels": [s["labels"] for s in samples],
            "text": [s["text"] for s in samples],
        })

    dataset_dict = DatasetDict({
        "train": samples_to_dataset(train_samples),
        "validation": samples_to_dataset(dev_samples),
        "test": samples_to_dataset(test_samples),
    })

    # Save
    print("\n[5/5] Saving datasets...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    dataset_dict.save_to_disk(str(OUTPUT_DIR))
    print(f"  Saved to: {OUTPUT_DIR}")

    # Save label mappings
    with open(OUTPUT_DIR / "label_mappings.json", "w") as f:
        json.dump({"label2id": LABEL2ID, "id2label": ID2LABEL}, f, indent=2)

    # Statistics
    print("\n" + "=" * 60)
    print("ESTADÍSTICAS")
    print("=" * 60)

    # Count entities in train set
    entity_counts = Counter()
    for sample in train_samples:
        for entity in sample["entities"]:
            entity_counts[entity["label"]] += 1

    print("\nDistribución de entidades (train):")
    total = sum(entity_counts.values())
    for label, count in sorted(entity_counts.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        print(f"  {label:20} {count:5} ({pct:5.1f}%)")

    # Validate a few samples
    print("\n3 Ejemplos de alineación:")
    for sample in random.sample(train_samples, 3):
        tokens = aligner.tokenizer.convert_ids_to_tokens(sample["input_ids"][:20])
        labels = [ID2LABEL.get(l, "IGN") if l != -100 else "-100" for l in sample["labels"][:20]]
        print(f"\n  Text: {sample['text'][:60]}...")
        print(f"  Tokens: {tokens[:10]}")
        print(f"  Labels: {labels[:10]}")


if __name__ == "__main__":
    main()
