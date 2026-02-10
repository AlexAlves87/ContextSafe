#!/usr/bin/env python3
"""
Generate synthetic labeled sentences for NER training.

Combines gazetteers with legal document templates to create
sentences with entity annotations for fine-tuning RoBERTalex.

Output formats:
- JSON with span annotations (start, end, label)
- CoNLL/BIO format for direct training

Output: data/processed/synthetic_ner_dataset.json
"""

import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


BASE_DIR = Path(__file__).parent.parent.parent
GAZETTEERS_DIR = BASE_DIR / "gazetteers"
OUTPUT_DIR = BASE_DIR / "data" / "processed"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Entity:
    """Represents an entity annotation."""
    text: str
    label: str
    start: int = 0
    end: int = 0


@dataclass
class LabeledSentence:
    """A sentence with its entity annotations."""
    text: str
    entities: list[Entity]

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "entities": [
                {"text": e.text, "label": e.label, "start": e.start, "end": e.end}
                for e in self.entities
            ]
        }


# =============================================================================
# GAZETTEER LOADERS
# =============================================================================

class GazetteerLoader:
    """Loads and provides random samples from gazetteers."""

    def __init__(self):
        self.nombres_arcaicos_h = []
        self.nombres_arcaicos_m = []
        self.apellidos = []
        self.municipios = []
        self.codigos_postales = []
        self.fechas = []
        self.dnis = []
        self.nies = []
        self.ibans = []
        self.nss = []
        self.telefonos = []
        self.matriculas = []
        self.refs_catastrales = []
        self.eclis = []
        self.ids_profesionales = []
        self.direcciones = []
        self.organizaciones = []

    def load_all(self):
        """Load all gazetteers."""
        print("Loading gazetteers...")

        # Nombres arcaicos
        with open(GAZETTEERS_DIR / "nombres_arcaicos.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            self.nombres_arcaicos_h = data["nombres_arcaicos"]["hombres"]
            self.nombres_arcaicos_m = data["nombres_arcaicos"]["mujeres"]

        # Apellidos
        with open(GAZETTEERS_DIR / "apellidos.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            self.apellidos = [a["apellido"] for a in data["apellidos"]]

        # Municipios
        with open(GAZETTEERS_DIR / "municipios.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            self.municipios = data["municipios"]

        # Códigos postales
        with open(GAZETTEERS_DIR / "codigos_postales.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            self.codigos_postales = [cp["codigo_postal"] for cp in data["codigos_postales"]]

        # Fechas textuales
        with open(GAZETTEERS_DIR / "fechas_textuales_flat.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            self.fechas = data["todos_textos"]

        # Identificadores administrativos
        with open(GAZETTEERS_DIR / "identificadores_administrativos.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            self.dnis = [d["texto"] for d in data["datos"]["DNI"]]
            self.nies = [d["texto"] for d in data["datos"]["NIE"]]
            self.ibans = [d["texto"] for d in data["datos"]["IBAN"]]
            self.nss = [d["texto"] for d in data["datos"]["NSS"]]
            self.telefonos = [d["texto"] for d in data["datos"]["TELEFONO"]]
            self.matriculas = [d["texto"] for d in data["datos"]["MATRICULA"]]
            self.refs_catastrales = [d["texto"] for d in data["datos"]["REFERENCIA_CATASTRAL"]]
            self.eclis = [d["texto"] for d in data["datos"]["ECLI"]]
            self.ids_profesionales = [d["texto"] for d in data["datos"]["ID_PROFESIONAL"]]

        # Direcciones
        with open(GAZETTEERS_DIR / "direcciones_flat.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            self.direcciones = data["todos_textos"]

        # Organizaciones
        with open(GAZETTEERS_DIR / "organizaciones_flat.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            self.organizaciones = data["todos_textos"]

        print(f"  Nombres arcaicos: {len(self.nombres_arcaicos_h) + len(self.nombres_arcaicos_m)}")
        print(f"  Apellidos: {len(self.apellidos)}")
        print(f"  Municipios: {len(self.municipios)}")
        print(f"  Códigos postales: {len(self.codigos_postales)}")
        print(f"  Fechas: {len(self.fechas)}")
        print(f"  DNIs: {len(self.dnis)}")
        print(f"  NIEs: {len(self.nies)}")
        print(f"  IBANs: {len(self.ibans)}")
        print(f"  Direcciones: {len(self.direcciones)}")
        print(f"  Organizaciones: {len(self.organizaciones)}")

    def get_nombre_completo(self, genero: str = "M") -> tuple[str, str]:
        """Get a full name (nombre + 2 apellidos) and gender prefix."""
        if genero == "M":
            nombre = random.choice(self.nombres_arcaicos_h)
            prefijo = "Don"
        else:
            nombre = random.choice(self.nombres_arcaicos_m)
            prefijo = "Doña"

        ap1 = random.choice(self.apellidos)
        ap2 = random.choice(self.apellidos)

        nombre_completo = f"{nombre.title()} {ap1.title()} {ap2.title()}"
        return nombre_completo, prefijo

    def get_random(self, tipo: str) -> str:
        """Get a random item from a gazetteer type."""
        mapping = {
            "municipio": self.municipios,
            "cp": self.codigos_postales,
            "fecha": self.fechas,
            "dni": self.dnis,
            "nie": self.nies,
            "iban": self.ibans,
            "nss": self.nss,
            "telefono": self.telefonos,
            "matricula": self.matriculas,
            "ref_catastral": self.refs_catastrales,
            "ecli": self.eclis,
            "id_profesional": self.ids_profesionales,
            "direccion": self.direcciones,
            "organizacion": self.organizaciones,
        }
        return random.choice(mapping[tipo])


# =============================================================================
# SENTENCE TEMPLATES
# =============================================================================

# Templates use {ENTITY_TYPE} placeholders
# Each placeholder will be replaced and annotated

TEMPLATES_TESTAMENTO = [
    "En {MUNICIPIO}, a {DATE_TEXTUAL}, ante mí, {PERSON}, Notario del Ilustre Colegio de {MUNICIPIO}, comparece {PERSON} con DNI {DNI}.",
    "{PERSON}, mayor de edad, con DNI número {DNI}, vecino de {MUNICIPIO}, otorga testamento.",
    "El testador {PERSON}, nacido en {MUNICIPIO}, con domicilio en {ADDRESS}, manifiesta su última voluntad.",
    "Comparece ante mí {PERSON}, con NIE {NIE}, residente en {ADDRESS}, {CP} {MUNICIPIO}.",
    "PRIMERO.- Instituye heredero universal a {PERSON}, con DNI {DNI}, domiciliado en {ADDRESS}.",
    "SEGUNDO.- Lega a {PERSON} el inmueble sito en {ADDRESS}, con referencia catastral {CADASTRAL_REF}.",
    "El causante {PERSON} falleció el día {DATE_TEXTUAL} en {MUNICIPIO}.",
    "Doy fe de que conozco al testador {PERSON}, titular del DNI {DNI}.",
]

TEMPLATES_CONTRATO = [
    "De una parte, {PERSON}, con DNI {DNI}, en representación de {ORGANIZATION}, con domicilio social en {ADDRESS}.",
    "De otra parte, {PERSON}, con NIE {NIE}, actuando en nombre propio.",
    "El arrendador {PERSON} cede en arrendamiento el inmueble sito en {ADDRESS}, referencia catastral {CADASTRAL_REF}.",
    "El precio del arrendamiento será de MIL EUROS mensuales, a ingresar en la cuenta {IBAN}.",
    "Las partes acuerdan que {ORGANIZATION} realizará el pago mediante transferencia a {IBAN}.",
    "El contrato se firma en {MUNICIPIO}, a {DATE_TEXTUAL}.",
    "Para cualquier notificación, el arrendatario señala el domicilio en {ADDRESS}, {CP} {MUNICIPIO}, teléfono {PHONE}.",
    "{PERSON}, con número de colegiado {PROFESSIONAL_ID}, certifica la autenticidad del documento.",
]

TEMPLATES_SENTENCIA = [
    "En {MUNICIPIO}, a {DATE_TEXTUAL}, el {ORGANIZATION} dicta la siguiente sentencia.",
    "ANTECEDENTES: {PERSON}, con DNI {DNI}, interpuso demanda contra {ORGANIZATION}.",
    "El demandado {PERSON}, con domicilio en {ADDRESS}, fue debidamente notificado.",
    "FALLO: Se condena a {PERSON} al pago de las costas procesales.",
    "La presente resolución es recurrible según {ECLI}.",
    "Se ordena el embargo del vehículo con matrícula {LICENSE_PLATE}, propiedad de {PERSON}.",
    "El acusado {PERSON}, con DNI {DNI}, fue detenido el día {DATE_TEXTUAL} en {MUNICIPIO}.",
    "Notifíquese a {PERSON} en su domicilio de {ADDRESS}, teléfono de contacto {PHONE}.",
]

TEMPLATES_ESCRITURA = [
    "ESCRITURA DE COMPRAVENTA otorgada por {PERSON}, con DNI {DNI}.",
    "El vendedor {PERSON} transmite a {PERSON} la finca registral número {CADASTRAL_REF}.",
    "La finca objeto de esta escritura se encuentra en {ADDRESS}, {CP} {MUNICIPIO}.",
    "El precio de la compraventa asciende a CIENTO CINCUENTA MIL EUROS, que se abonarán mediante transferencia a {IBAN}.",
    "Las partes comparecen ante el Notario {PERSON}, con número de protocolo {PROFESSIONAL_ID}.",
    "Se inscribirá en el Registro de la Propiedad de {MUNICIPIO}.",
    "{PERSON}, en nombre de {ORGANIZATION}, con CIF que se dirá, vende el inmueble.",
    "Otorgada en {MUNICIPIO}, el día {DATE_TEXTUAL}.",
]

TEMPLATES_LABORAL = [
    "{PERSON}, con DNI {DNI} y número de afiliación a la Seguridad Social {NSS}, ha prestado servicios para {ORGANIZATION}.",
    "El trabajador {PERSON}, domiciliado en {ADDRESS}, fue despedido el {DATE_TEXTUAL}.",
    "La empresa {ORGANIZATION} deberá abonar los salarios adeudados en la cuenta {IBAN}.",
    "{PERSON}, con NSS {NSS}, reclama el reconocimiento de una incapacidad.",
    "El {ORGANIZATION} resuelve el recurso interpuesto por {PERSON}.",
    "Se cita a {PERSON} para el acto de conciliación el día {DATE_TEXTUAL} en {ADDRESS}.",
]

TEMPLATES_MISCELANEOS = [
    "{PERSON} autoriza a {PERSON} para actuar en su nombre.",
    "Contacto: {PERSON}, teléfono {PHONE}, correo electrónico.",
    "El vehículo matrícula {LICENSE_PLATE} está a nombre de {PERSON}, con domicilio en {ADDRESS}.",
    "{ORGANIZATION}, con domicilio en {ADDRESS}, {CP} {MUNICIPIO}.",
    "Según consta en {ECLI}, el tribunal resolvió a favor de {PERSON}.",
    "El abogado {PERSON}, colegiado número {PROFESSIONAL_ID}, asiste al demandante.",
    "La notificación se realizó el {DATE_TEXTUAL} en {ADDRESS}.",
    "{PERSON}, identificado con NIE {NIE}, solicita la nacionalidad española.",
]

ALL_TEMPLATES = (
    TEMPLATES_TESTAMENTO +
    TEMPLATES_CONTRATO +
    TEMPLATES_SENTENCIA +
    TEMPLATES_ESCRITURA +
    TEMPLATES_LABORAL +
    TEMPLATES_MISCELANEOS
)


# =============================================================================
# SENTENCE GENERATOR
# =============================================================================

# Mapping from placeholder to (gazetteer_key, entity_label)
PLACEHOLDER_MAP = {
    "PERSON": (None, "PERSON"),  # Special handling
    "MUNICIPIO": ("municipio", "LOCATION"),
    "CP": ("cp", "POSTAL_CODE"),
    "DATE_TEXTUAL": ("fecha", "DATE"),
    "DNI": ("dni", "DNI_NIE"),
    "NIE": ("nie", "DNI_NIE"),
    "IBAN": ("iban", "IBAN"),
    "NSS": ("nss", "NSS"),
    "PHONE": ("telefono", "PHONE"),
    "LICENSE_PLATE": ("matricula", "LICENSE_PLATE"),
    "CADASTRAL_REF": ("ref_catastral", "CADASTRAL_REF"),
    "ECLI": ("ecli", "ECLI"),
    "PROFESSIONAL_ID": ("id_profesional", "PROFESSIONAL_ID"),
    "ADDRESS": ("direccion", "ADDRESS"),
    "ORGANIZATION": ("organizacion", "ORGANIZATION"),
}


def generate_sentence(template: str, gazetteer: GazetteerLoader) -> LabeledSentence:
    """Generate a sentence from a template with entity annotations."""
    text = template
    entities = []

    # Find all placeholders
    pattern = r'\{([A-Z_]+)\}'
    matches = list(re.finditer(pattern, template))

    # Process in reverse order to maintain correct positions
    offset = 0

    # First pass: collect all replacements
    replacements = []
    for match in matches:
        placeholder = match.group(1)

        if placeholder not in PLACEHOLDER_MAP:
            continue

        gaz_key, label = PLACEHOLDER_MAP[placeholder]

        if placeholder == "PERSON":
            # Generate full name with random gender
            genero = random.choice(["M", "F"])
            value, prefijo = gazetteer.get_nombre_completo(genero)
            # 70% of the time include "Don/Doña"
            if random.random() < 0.7:
                value = f"{prefijo} {value}"
        else:
            value = gazetteer.get_random(gaz_key)

        replacements.append((match.start(), match.end(), value, label))

    # Apply replacements and track positions
    result_text = template
    current_offset = 0

    for orig_start, orig_end, value, label in replacements:
        # Adjust for previous replacements
        adj_start = orig_start + current_offset
        adj_end = orig_end + current_offset

        # Replace in text
        result_text = result_text[:adj_start] + value + result_text[adj_end:]

        # Calculate new positions
        new_start = adj_start
        new_end = adj_start + len(value)

        # Update offset for next replacement
        current_offset += len(value) - (orig_end - orig_start)

        # Add entity
        entities.append(Entity(
            text=value,
            label=label,
            start=new_start,
            end=new_end
        ))

    return LabeledSentence(text=result_text, entities=entities)


def sentence_to_bio(sentence: LabeledSentence) -> list[tuple[str, str]]:
    """Convert a labeled sentence to BIO format."""
    text = sentence.text
    tokens = []
    labels = []

    # Simple whitespace tokenization (can be improved with spaCy)
    words = text.split()
    current_pos = 0

    for word in words:
        # Find word position in original text
        word_start = text.find(word, current_pos)
        word_end = word_start + len(word)
        current_pos = word_end

        # Check if word is part of any entity
        word_label = "O"

        for entity in sentence.entities:
            if entity.start <= word_start < entity.end:
                # Word is inside this entity
                if word_start == entity.start:
                    word_label = f"B-{entity.label}"
                else:
                    word_label = f"I-{entity.label}"
                break

        tokens.append(word)
        labels.append(word_label)

    return list(zip(tokens, labels))


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Generate synthetic NER dataset."""
    print("=" * 60)
    print("GENERADOR DE FRASES SINTÉTICAS ETIQUETADAS")
    print("=" * 60)

    # Load gazetteers
    print("\n[1/4] Loading gazetteers...")
    gazetteer = GazetteerLoader()
    gazetteer.load_all()

    # Generate sentences
    print(f"\n[2/4] Generating sentences from {len(ALL_TEMPLATES)} templates...")

    sentences = []
    sentences_per_template = 50  # Generate 50 variants per template

    for i, template in enumerate(ALL_TEMPLATES):
        for _ in range(sentences_per_template):
            try:
                sentence = generate_sentence(template, gazetteer)
                sentences.append(sentence)
            except Exception as e:
                print(f"    Warning: Failed to generate from template {i}: {e}")

    print(f"    Generated {len(sentences)} sentences")

    # Convert to BIO format
    print("\n[3/4] Converting to BIO format...")
    bio_sentences = []
    for sentence in sentences:
        bio = sentence_to_bio(sentence)
        bio_sentences.append(bio)

    # Build output
    print("\n[4/4] Saving outputs...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # JSON format with spans
    output_json = {
        "source": "Synthetic - Spanish Legal NER Dataset",
        "description": "Frases sintéticas etiquetadas para entrenamiento NER",
        "total_sentences": len(sentences),
        "templates_used": len(ALL_TEMPLATES),
        "entity_types": list(set(PLACEHOLDER_MAP[k][1] for k in PLACEHOLDER_MAP)),
        "sentences": [s.to_dict() for s in sentences]
    }

    with open(OUTPUT_DIR / "synthetic_ner_dataset.json", "w", encoding="utf-8") as f:
        json.dump(output_json, f, ensure_ascii=False, indent=2)
    print(f"    Saved: {OUTPUT_DIR / 'synthetic_ner_dataset.json'}")

    # BIO/CoNLL format
    with open(OUTPUT_DIR / "synthetic_ner_dataset.bio", "w", encoding="utf-8") as f:
        for bio_sentence in bio_sentences:
            for token, label in bio_sentence:
                f.write(f"{token}\t{label}\n")
            f.write("\n")  # Blank line between sentences
    print(f"    Saved: {OUTPUT_DIR / 'synthetic_ner_dataset.bio'}")

    # Statistics
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Oraciones generadas: {len(sentences)}")
    print(f"Plantillas usadas: {len(ALL_TEMPLATES)}")

    # Entity count
    entity_counts = {}
    for sentence in sentences:
        for entity in sentence.entities:
            entity_counts[entity.label] = entity_counts.get(entity.label, 0) + 1

    print("\nEntidades por tipo:")
    for label, count in sorted(entity_counts.items(), key=lambda x: -x[1]):
        print(f"  {label}: {count}")

    print("\n5 Ejemplos de frases generadas:")
    for sentence in random.sample(sentences, 5):
        print(f"\n  Texto: {sentence.text[:100]}...")
        print(f"  Entidades: {[(e.text[:20], e.label) for e in sentence.entities[:3]]}")


if __name__ == "__main__":
    main()
