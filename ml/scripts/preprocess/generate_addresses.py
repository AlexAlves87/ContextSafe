#!/usr/bin/env python3
"""
Generate synthetic Spanish addresses for NER training.

Combines:
- Street types (calle, avenida, plaza, paseo, etc.)
- Street names (historical figures, saints, generic names)
- Numbers, floors, doors
- Postal codes and municipalities from INE data

Output: gazetteers/direcciones.json
"""

import json
import random
from pathlib import Path


BASE_DIR = Path(__file__).parent.parent.parent
GAZETTEERS_DIR = BASE_DIR / "gazetteers"

# =============================================================================
# TIPOS DE VÍA
# =============================================================================

TIPOS_VIA = [
    ("Calle", "C/", "c/", "CL"),
    ("Avenida", "Av.", "Avda.", "AV"),
    ("Plaza", "Pza.", "Pl.", "PZ"),
    ("Paseo", "Pº", "P.", "PS"),
    ("Carretera", "Ctra.", "CR"),
    ("Camino", "Cmno.", "CM"),
    ("Travesía", "Trv.", "TR"),
    ("Ronda", "Rda.", "RD"),
    ("Glorieta", "Gta.", "GL"),
    ("Urbanización", "Urb.", "UR"),
    ("Pasaje", "Psje.", "PJ"),
    ("Callejón", "Cjón.", "CJ"),
    ("Costanilla", "Cost.", "CO"),
    ("Barrio", "Bº", "BO"),
    ("Partida", "Ptda.", "PD"),
    ("Polígono", "Pol.", "PG"),
    ("Parque", "Pq.", "PQ"),
    ("Jardín", "Jdín.", "JR"),
    ("Vía", "V.", "VI"),
    ("Bulevar", "Blvr.", "BV"),
]

# =============================================================================
# NOMBRES DE CALLES
# =============================================================================

# Personajes históricos
NOMBRES_HISTORICOS = [
    "Cervantes", "Quevedo", "Lope de Vega", "Góngora", "Calderón de la Barca",
    "Goya", "Velázquez", "Picasso", "Dalí", "Miró",
    "Colón", "Hernán Cortés", "Pizarro", "Magallanes", "Elcano",
    "Isabel la Católica", "Fernando el Católico", "Carlos V", "Felipe II", "Felipe IV",
    "Alfonso X el Sabio", "Jaime I", "El Cid", "Reyes Católicos",
    "Unamuno", "Ortega y Gasset", "Machado", "García Lorca", "Alberti",
    "Ramón y Cajal", "Severo Ochoa", "Juan de la Cierva", "Isaac Peral",
    "Jovellanos", "Moratín", "Zorrilla", "Bécquer", "Rosalía de Castro",
    "Galdós", "Clarín", "Pardo Bazán", "Valle-Inclán", "Baroja",
    "Sorolla", "Zuloaga", "Zurbarán", "Murillo", "El Greco",
    "Falla", "Albéniz", "Granados", "Rodrigo", "Casals",
    "Teresa de Jesús", "Juan de la Cruz", "Ignacio de Loyola",
    "Francisco de Asís", "Francisco de Borja", "Vicente Ferrer",
]

# Santos y vírgenes (muy comunes en callejeros españoles)
NOMBRES_SANTOS = [
    "San Juan", "San Pedro", "San Pablo", "San Miguel", "San Antonio",
    "San José", "San Francisco", "San Martín", "San Andrés", "San Sebastián",
    "San Lorenzo", "San Isidro", "San Roque", "San Vicente", "San Nicolás",
    "San Agustín", "San Bernardo", "San Fernando", "San Ignacio", "San Luis",
    "Santa María", "Santa Ana", "Santa Teresa", "Santa Isabel", "Santa Lucía",
    "Santa Catalina", "Santa Bárbara", "Santa Clara", "Santa Rosa", "Santa Cruz",
    "Virgen del Carmen", "Virgen del Pilar", "Virgen de la Paloma",
    "Virgen de Guadalupe", "Virgen de Fátima", "Virgen de Lourdes",
    "Virgen de Covadonga", "Virgen de Montserrat", "Virgen de los Desamparados",
    "Inmaculada", "Asunción", "Encarnación", "Purificación", "Anunciación",
]

# Genéricos y descriptivos
NOMBRES_GENERICOS = [
    "Mayor", "Real", "Nueva", "Vieja", "Alta", "Baja",
    "Grande", "Ancha", "Larga", "Corta", "Estrecha",
    "Norte", "Sur", "Este", "Oeste", "Central",
    "Principal", "Primera", "Segunda", "Tercera",
    "del Sol", "de la Luna", "de las Estrellas",
    "del Río", "del Mar", "de la Playa", "del Puerto",
    "del Castillo", "de la Torre", "de la Muralla", "del Palacio",
    "de la Iglesia", "de la Catedral", "del Convento", "del Monasterio",
    "del Mercado", "de la Plaza", "del Ayuntamiento", "de la Fuente",
    "de los Jardines", "del Parque", "del Prado", "de la Alameda",
    "de la Paz", "de la Libertad", "de la Constitución", "de la Democracia",
    "de España", "de Europa", "de América", "de Portugal", "de Francia",
    "del Trabajo", "de la Industria", "del Comercio", "de la Agricultura",
]

# Profesiones (comunes en callejeros)
NOMBRES_PROFESIONES = [
    "Herreros", "Carpinteros", "Zapateros", "Tejedores", "Plateros",
    "Curtidores", "Alfareros", "Caldereros", "Cerrajeros", "Canteros",
    "Torneros", "Tintoreros", "Bordadores", "Sederos", "Laneros",
    "Panaderos", "Carniceros", "Pescaderos", "Fruteros", "Verduleros",
]

# Árboles y plantas
NOMBRES_NATURALEZA = [
    "Olmos", "Álamos", "Pinos", "Encinas", "Robles",
    "Cipreses", "Castaños", "Nogales", "Almendros", "Naranjos",
    "Limoneros", "Olivos", "Laureles", "Acacias", "Tilos",
    "Rosas", "Claveles", "Jazmines", "Violetas", "Margaritas",
    "Amapolas", "Girasoles", "Lirios", "Azucenas", "Geranios",
]

# Números ordinales
NUMEROS_ORDINALES = [
    "Primero de Mayo", "Dos de Mayo", "Catorce de Abril", "Doce de Octubre",
    "Dieciocho de Julio", "Seis de Diciembre", "Veintiocho de Febrero",
]

# =============================================================================
# COMPONENTES DE DIRECCIÓN
# =============================================================================

PISOS = [
    "bajo", "entresuelo", "principal", "1º", "2º", "3º", "4º", "5º",
    "6º", "7º", "8º", "9º", "10º", "ático", "sobreático",
    "planta baja", "planta primera", "planta segunda",
]

PUERTAS = [
    "A", "B", "C", "D", "E", "F", "izquierda", "derecha", "centro",
    "izda.", "dcha.", "ctro.", "1ª", "2ª", "3ª", "4ª",
    "interior", "exterior", "frente",
]

ESCALERAS = ["A", "B", "C", "D", "1", "2", "3", "izquierda", "derecha"]

BLOQUES = ["1", "2", "3", "4", "5", "A", "B", "C", "D", "E"]


def load_codigos_postales() -> list[dict]:
    """Load postal codes from gazetteers."""
    with open(GAZETTEERS_DIR / "codigos_postales.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["codigos_postales"]


def load_municipios() -> list[str]:
    """Load municipalities from gazetteers."""
    with open(GAZETTEERS_DIR / "municipios.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["municipios"]


def generate_street_name() -> str:
    """Generate a street name."""
    all_names = (
        NOMBRES_HISTORICOS + NOMBRES_SANTOS + NOMBRES_GENERICOS +
        NOMBRES_PROFESIONES + NOMBRES_NATURALEZA + NUMEROS_ORDINALES
    )
    return random.choice(all_names)


def generate_address(codigos_postales: list[dict], municipios: list[str]) -> dict:
    """Generate a complete Spanish address."""
    # Select street type
    tipo_completo, *abreviaturas = random.choice(TIPOS_VIA)

    # Use full name or abbreviation
    if random.random() < 0.7:
        tipo_via = tipo_completo
    else:
        tipo_via = random.choice(abreviaturas)

    # Street name
    nombre_calle = generate_street_name()

    # Street number
    numero = random.randint(1, 150)

    # Additional details (floor, door, etc.)
    detalles = []
    componentes = {}

    if random.random() < 0.7:
        # Has floor/door
        if random.random() < 0.3:
            # Has block
            bloque = random.choice(BLOQUES)
            detalles.append(f"bloque {bloque}")
            componentes["bloque"] = bloque

        if random.random() < 0.3:
            # Has escalera
            escalera = random.choice(ESCALERAS)
            detalles.append(f"escalera {escalera}")
            componentes["escalera"] = escalera

        piso = random.choice(PISOS)
        detalles.append(piso)
        componentes["piso"] = piso

        if random.random() < 0.8:
            puerta = random.choice(PUERTAS)
            detalles.append(puerta)
            componentes["puerta"] = puerta

    # Postal code and municipality
    if random.random() < 0.8 and codigos_postales:
        cp_data = random.choice(codigos_postales)
        codigo_postal = cp_data["codigo_postal"]
        municipio = random.choice(cp_data["municipios"]) if cp_data["municipios"] else random.choice(municipios)
    else:
        codigo_postal = f"{random.randint(1, 52):02d}{random.randint(0, 999):03d}"
        municipio = random.choice(municipios)

    # Province (derived from CP)
    provincia_num = int(codigo_postal[:2])

    # Build address text
    # Multiple format variations
    formato = random.choice([
        "completo_con_cp",
        "completo_sin_cp",
        "solo_calle",
        "legal_extenso",
        "abreviado",
    ])

    if formato == "completo_con_cp":
        if detalles:
            texto = f"{tipo_via} {nombre_calle}, {numero}, {', '.join(detalles)}, {codigo_postal} {municipio}"
        else:
            texto = f"{tipo_via} {nombre_calle}, {numero}, {codigo_postal} {municipio}"

    elif formato == "completo_sin_cp":
        if detalles:
            texto = f"{tipo_via} {nombre_calle}, nº {numero}, {', '.join(detalles)}"
        else:
            texto = f"{tipo_via} {nombre_calle}, nº {numero}"

    elif formato == "solo_calle":
        texto = f"{tipo_via} {nombre_calle} {numero}"

    elif formato == "legal_extenso":
        partes = [f"{tipo_via} {nombre_calle}", f"número {numero}"]
        if detalles:
            partes.extend(detalles)
        partes.append(f"de {municipio}")
        texto = ", ".join(partes)

    else:  # abreviado
        if detalles:
            texto = f"{tipo_via} {nombre_calle} {numero}, {'-'.join(detalles[:2])}"
        else:
            texto = f"{tipo_via} {nombre_calle} {numero}"

    return {
        "texto": texto,
        "tipo_via": tipo_completo,
        "nombre_calle": nombre_calle,
        "numero": numero,
        "componentes": componentes,
        "codigo_postal": codigo_postal,
        "municipio": municipio,
        "formato": formato,
    }


def generate_legal_address_context(address: dict) -> str:
    """Generate address in legal document context."""
    patterns = [
        "con domicilio en {direccion}",
        "domiciliado en {direccion}",
        "domiciliada en {direccion}",
        "residente en {direccion}",
        "vecino de {municipio}, con domicilio en {direccion}",
        "vecina de {municipio}, con domicilio en {direccion}",
        "natural de {municipio}, con residencia en {direccion}",
        "con residencia habitual en {direccion}",
        "en su domicilio sito en {direccion}",
        "en la dirección {direccion}",
        "cuyo domicilio radica en {direccion}",
        "con domicilio social en {direccion}",
        "establecido en {direccion}",
    ]

    pattern = random.choice(patterns)
    return pattern.format(
        direccion=address["texto"],
        municipio=address["municipio"]
    )


def main():
    """Generate addresses dataset."""
    print("=" * 60)
    print("GENERADOR DE DIRECCIONES ESPAÑOLAS")
    print("=" * 60)

    # Load data
    print("\n[1/4] Loading gazetteers...")
    codigos_postales = load_codigos_postales()
    municipios = load_municipios()
    print(f"    Códigos postales: {len(codigos_postales)}")
    print(f"    Municipios: {len(municipios)}")

    # Generate addresses
    print("\n[2/4] Generating addresses...")

    direcciones = []
    direcciones_con_contexto = []

    # Generate 600 addresses
    for _ in range(600):
        addr = generate_address(codigos_postales, municipios)
        direcciones.append(addr)

        # 70% also get legal context
        if random.random() < 0.7:
            contexto = generate_legal_address_context(addr)
            direcciones_con_contexto.append({
                "texto_contexto": contexto,
                "direccion": addr
            })

    print(f"    Direcciones generadas: {len(direcciones)}")
    print(f"    Con contexto legal: {len(direcciones_con_contexto)}")

    # Build output
    print("\n[3/4] Building output...")

    output = {
        "source": "Synthetic - Spanish Addresses for Legal Documents",
        "description": "Direcciones españolas sintéticas para documentos legales",
        "stats": {
            "direcciones": len(direcciones),
            "con_contexto_legal": len(direcciones_con_contexto),
            "tipos_via": len(TIPOS_VIA),
            "nombres_calles_disponibles": (
                len(NOMBRES_HISTORICOS) + len(NOMBRES_SANTOS) +
                len(NOMBRES_GENERICOS) + len(NOMBRES_PROFESIONES) +
                len(NOMBRES_NATURALEZA) + len(NUMEROS_ORDINALES)
            ),
        },
        "vocabulario": {
            "tipos_via": [t[0] for t in TIPOS_VIA],
            "pisos": PISOS,
            "puertas": PUERTAS,
        },
        "direcciones": direcciones[:200],  # Sample for main file
        "direcciones_con_contexto": direcciones_con_contexto[:200],
    }

    # Flat list for NER training
    flat_data = {
        "todos_textos": [d["texto"] for d in direcciones],
        "con_contexto": [d["texto_contexto"] for d in direcciones_con_contexto],
    }

    # Save
    print("\n[4/4] Saving output...")

    with open(GAZETTEERS_DIR / "direcciones.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"    Saved: {GAZETTEERS_DIR / 'direcciones.json'}")

    with open(GAZETTEERS_DIR / "direcciones_flat.json", "w", encoding="utf-8") as f:
        json.dump(flat_data, f, ensure_ascii=False, indent=2)
    print(f"    Saved: {GAZETTEERS_DIR / 'direcciones_flat.json'}")

    # Summary
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Direcciones generadas: {len(direcciones)}")
    print(f"Con contexto legal: {len(direcciones_con_contexto)}")

    print("\n10 Ejemplos de direcciones:")
    for addr in random.sample(direcciones, 10):
        print(f"  • {addr['texto']}")

    print("\n5 Ejemplos con contexto legal:")
    for ctx in random.sample(direcciones_con_contexto, 5):
        print(f"  • {ctx['texto_contexto']}")


if __name__ == "__main__":
    main()
