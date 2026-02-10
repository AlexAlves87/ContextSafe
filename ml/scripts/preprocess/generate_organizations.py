#!/usr/bin/env python3
"""
Generate synthetic Spanish organization names for NER training.

Includes:
- Private companies (S.A., S.L., S.L.U., etc.)
- Public institutions (Juzgados, Notarías, Registros)
- Professional associations (Colegios)
- Financial entities (Banks, Insurance)
- Religious/nonprofit organizations

Output: gazetteers/organizaciones.json
"""

import json
import random
from pathlib import Path


BASE_DIR = Path(__file__).parent.parent.parent
GAZETTEERS_DIR = BASE_DIR / "gazetteers"

# =============================================================================
# COMPONENTES DE NOMBRES DE EMPRESAS
# =============================================================================

# Apellidos comunes para empresas (Hermanos García, Hijos de Pérez)
APELLIDOS_EMPRESA = [
    "García", "Fernández", "González", "Rodríguez", "López",
    "Martínez", "Sánchez", "Pérez", "Gómez", "Martín",
    "Jiménez", "Ruiz", "Hernández", "Díaz", "Moreno",
    "Álvarez", "Muñoz", "Romero", "Alonso", "Gutiérrez",
    "Navarro", "Torres", "Domínguez", "Vázquez", "Ramos",
    "Gil", "Ramírez", "Serrano", "Blanco", "Molina",
    "Morales", "Suárez", "Ortega", "Delgado", "Castro",
    "Ortiz", "Rubio", "Marín", "Sanz", "Iglesias",
]

# Palabras para nombres de empresas
PALABRAS_EMPRESA = [
    "Ibérica", "Española", "Nacional", "Internacional", "Global",
    "Central", "General", "Universal", "Continental", "Peninsular",
    "Mediterránea", "Atlántica", "Europea", "Hispana", "Castilla",
    "Norte", "Sur", "Levante", "Cantábrica", "Andaluza",
    "Nueva", "Moderna", "Tradicional", "Clásica", "Primera",
    "Capital", "Premium", "Excellence", "Plus", "Pro",
]

# Sectores/actividades
SECTORES = [
    "Construcciones", "Promociones", "Inmobiliaria", "Inversiones", "Gestiones",
    "Transportes", "Logística", "Distribuciones", "Comercial", "Servicios",
    "Industrias", "Manufacturas", "Producciones", "Fabricaciones", "Textil",
    "Alimentación", "Agrícola", "Ganadera", "Pesquera", "Forestal",
    "Tecnología", "Informática", "Comunicaciones", "Digital", "Software",
    "Consultoría", "Asesoría", "Ingeniería", "Arquitectura", "Diseño",
    "Energía", "Renovables", "Solar", "Eléctrica", "Petróleo",
    "Hostelería", "Turismo", "Restauración", "Hotelera", "Ocio",
    "Farmacéutica", "Sanitaria", "Clínica", "Médica", "Dental",
    "Financiera", "Banca", "Seguros", "Crédito", "Ahorro",
    "Importación", "Exportación", "Trading", "Mayorista", "Minorista",
]

# Formas jurídicas
FORMAS_JURIDICAS = [
    ("S.A.", "Sociedad Anónima"),
    ("S.L.", "Sociedad Limitada"),
    ("S.L.U.", "Sociedad Limitada Unipersonal"),
    ("S.A.U.", "Sociedad Anónima Unipersonal"),
    ("S.L.L.", "Sociedad Limitada Laboral"),
    ("S.A.L.", "Sociedad Anónima Laboral"),
    ("S.C.", "Sociedad Colectiva"),
    ("S.Com.", "Sociedad Comanditaria"),
    ("S.Coop.", "Sociedad Cooperativa"),
    ("C.B.", "Comunidad de Bienes"),
    ("A.I.E.", "Agrupación de Interés Económico"),
]

# =============================================================================
# INSTITUCIONES PÚBLICAS
# =============================================================================

# Juzgados
TIPOS_JUZGADO = [
    "Juzgado de Primera Instancia",
    "Juzgado de Instrucción",
    "Juzgado de lo Penal",
    "Juzgado de lo Social",
    "Juzgado de lo Contencioso-Administrativo",
    "Juzgado de lo Mercantil",
    "Juzgado de Familia",
    "Juzgado de Violencia sobre la Mujer",
    "Juzgado de Menores",
    "Juzgado de Vigilancia Penitenciaria",
    "Juzgado de Primera Instancia e Instrucción",
]

TRIBUNALES = [
    "Tribunal Supremo",
    "Tribunal Constitucional",
    "Audiencia Nacional",
    "Audiencia Provincial",
    "Tribunal Superior de Justicia",
]

# Notarías y Registros
ENTIDADES_REGISTRALES = [
    "Notaría de",
    "Registro de la Propiedad de",
    "Registro Civil de",
    "Registro Mercantil de",
]

# Ciudades para instituciones
CIUDADES = [
    "Madrid", "Barcelona", "Valencia", "Sevilla", "Zaragoza",
    "Málaga", "Murcia", "Palma", "Bilbao", "Alicante",
    "Córdoba", "Valladolid", "Vigo", "Gijón", "Granada",
    "A Coruña", "Vitoria", "Elche", "Oviedo", "Santa Cruz de Tenerife",
    "Pamplona", "Santander", "San Sebastián", "Burgos", "Albacete",
    "Salamanca", "Logroño", "Badajoz", "Huelva", "Tarragona",
]

# =============================================================================
# ENTIDADES FINANCIERAS
# =============================================================================

BANCOS = [
    "Banco Santander", "BBVA", "CaixaBank", "Banco Sabadell",
    "Bankinter", "Unicaja Banco", "Ibercaja", "Kutxabank",
    "Abanca", "Cajamar", "Caja Rural", "Deutsche Bank España",
    "ING España", "Openbank", "EVO Banco", "Triodos Bank",
]

ASEGURADORAS = [
    "Mapfre", "Allianz Seguros", "AXA España", "Zurich España",
    "Generali Seguros", "Mutua Madrileña", "Línea Directa", "Pelayo",
    "Santa Lucía", "Caser", "Catalana Occidente", "Reale Seguros",
    "Liberty Seguros", "Santalucía", "DKV Seguros", "Asisa",
]

# =============================================================================
# COLEGIOS PROFESIONALES
# =============================================================================

COLEGIOS_PROFESIONALES = [
    "Ilustre Colegio de Abogados de",
    "Colegio de Procuradores de",
    "Colegio Oficial de Médicos de",
    "Colegio Oficial de Arquitectos de",
    "Colegio de Ingenieros de",
    "Colegio de Notarios de",
    "Colegio de Registradores de",
    "Colegio Oficial de Farmacéuticos de",
    "Colegio de Economistas de",
    "Colegio Oficial de Psicólogos de",
]

# =============================================================================
# ORGANIZACIONES RELIGIOSAS Y SIN ÁNIMO DE LUCRO
# =============================================================================

ORGANIZACIONES_RELIGIOSAS = [
    "Parroquia de",
    "Iglesia de",
    "Catedral de",
    "Basílica de",
    "Monasterio de",
    "Convento de",
    "Hermandad de",
    "Cofradía de",
    "Archidiócesis de",
    "Diócesis de",
    "Obispado de",
]

SANTOS_PARA_PARROQUIAS = [
    "San Juan", "San Pedro", "San Pablo", "Santa María", "San José",
    "San Antonio", "Santa Ana", "San Miguel", "Santiago", "San Francisco",
    "Santa Teresa", "San Isidro", "San Lorenzo", "San Sebastián", "San Martín",
    "Nuestra Señora del Carmen", "Nuestra Señora del Pilar",
    "Nuestra Señora de la Asunción", "Nuestra Señora de Fátima",
]

ONG_PREFIJOS = [
    "Fundación", "Asociación", "Federación", "Confederación",
    "Cruz Roja", "Cáritas", "ONG",
]


def load_municipios() -> list[str]:
    """Load municipalities from gazetteers."""
    with open(GAZETTEERS_DIR / "municipios.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["municipios"]


def generate_private_company() -> dict:
    """Generate a private company name."""
    forma_abrev, forma_completa = random.choice(FORMAS_JURIDICAS)

    # Different naming patterns
    pattern = random.choice([
        "apellido_hnos", "apellido_hijos", "sector_palabra",
        "palabra_sector", "apellido_sector", "nombre_fantasía",
        "iniciales", "apellidos_doble"
    ])

    if pattern == "apellido_hnos":
        apellido = random.choice(APELLIDOS_EMPRESA)
        nombre = f"Hermanos {apellido}"
    elif pattern == "apellido_hijos":
        apellido = random.choice(APELLIDOS_EMPRESA)
        nombre = f"Hijos de {apellido}"
    elif pattern == "sector_palabra":
        sector = random.choice(SECTORES)
        palabra = random.choice(PALABRAS_EMPRESA)
        nombre = f"{sector} {palabra}"
    elif pattern == "palabra_sector":
        palabra = random.choice(PALABRAS_EMPRESA)
        sector = random.choice(SECTORES)
        nombre = f"{palabra} {sector}"
    elif pattern == "apellido_sector":
        apellido = random.choice(APELLIDOS_EMPRESA)
        sector = random.choice(SECTORES)
        nombre = f"{apellido} {sector}"
    elif pattern == "nombre_fantasía":
        # Invented names
        prefijos = ["Euro", "Iber", "Hispa", "Trans", "Inter", "Multi", "Tele", "Auto", "Agro", "Bio"]
        sufijos = ["sol", "mar", "sur", "norte", "tech", "nova", "plus", "group", "corp", "net"]
        nombre = random.choice(prefijos) + random.choice(sufijos).capitalize()
    elif pattern == "iniciales":
        # Like AENA, RENFE
        letras = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=random.randint(3, 5)))
        nombre = letras
    else:  # apellidos_doble
        ap1 = random.choice(APELLIDOS_EMPRESA)
        ap2 = random.choice(APELLIDOS_EMPRESA)
        nombre = f"{ap1} y {ap2}"

    # Full name with legal form
    texto_completo = f"{nombre}, {forma_abrev}"

    # Variations
    variaciones = [
        texto_completo,
        f"{nombre} {forma_abrev}",
        f"{nombre}, {forma_completa}",
        nombre,  # Sometimes without legal form
    ]

    return {
        "texto": random.choice(variaciones),
        "nombre": nombre,
        "forma_juridica": forma_abrev,
        "forma_juridica_completa": forma_completa,
        "tipo": "EMPRESA_PRIVADA"
    }


def generate_public_institution(ciudades: list[str]) -> dict:
    """Generate a public institution name."""
    ciudad = random.choice(ciudades)

    tipo = random.choice(["juzgado", "tribunal", "registro", "colegio"])

    if tipo == "juzgado":
        tipo_juzgado = random.choice(TIPOS_JUZGADO)
        numero = random.randint(1, 15)
        texto = f"{tipo_juzgado} nº {numero} de {ciudad}"
        subtipo = "juzgado"

    elif tipo == "tribunal":
        if random.random() < 0.3:
            texto = random.choice(TRIBUNALES)
        else:
            texto = f"Audiencia Provincial de {ciudad}"
        subtipo = "tribunal"

    elif tipo == "registro":
        entidad = random.choice(ENTIDADES_REGISTRALES)
        if "Mercantil" in entidad:
            texto = f"{entidad}{ciudad}"
        else:
            numero = random.randint(1, 5)
            texto = f"{entidad}{ciudad} nº {numero}"
        subtipo = "registro"

    else:  # colegio
        colegio = random.choice(COLEGIOS_PROFESIONALES)
        texto = f"{colegio}{ciudad}"
        subtipo = "colegio_profesional"

    return {
        "texto": texto,
        "ciudad": ciudad,
        "subtipo": subtipo,
        "tipo": "INSTITUCION_PUBLICA"
    }


def generate_financial_entity() -> dict:
    """Generate a financial entity name."""
    if random.random() < 0.7:
        nombre = random.choice(BANCOS)
        subtipo = "banco"
    else:
        nombre = random.choice(ASEGURADORAS)
        subtipo = "aseguradora"

    variaciones = [
        nombre,
        f"entidad bancaria {nombre}",
        f"la entidad {nombre}",
    ]

    return {
        "texto": random.choice(variaciones),
        "nombre": nombre,
        "subtipo": subtipo,
        "tipo": "ENTIDAD_FINANCIERA"
    }


def generate_religious_org(ciudades: list[str]) -> dict:
    """Generate a religious organization name."""
    tipo = random.choice(ORGANIZACIONES_RELIGIOSAS)
    ciudad = random.choice(ciudades)

    if "Parroquia" in tipo or "Iglesia" in tipo or "Basílica" in tipo:
        santo = random.choice(SANTOS_PARA_PARROQUIAS)
        texto = f"{tipo}{santo} de {ciudad}"
    elif "Archidiócesis" in tipo or "Diócesis" in tipo or "Obispado" in tipo:
        texto = f"{tipo}{ciudad}"
    else:
        santo = random.choice(SANTOS_PARA_PARROQUIAS)
        texto = f"{tipo}{santo}"

    return {
        "texto": texto,
        "tipo": "ORGANIZACION_RELIGIOSA"
    }


def generate_nonprofit() -> dict:
    """Generate a nonprofit organization name."""
    prefijo = random.choice(ONG_PREFIJOS)

    temas = [
        "para la Protección del Medio Ambiente",
        "de Ayuda Humanitaria",
        "contra el Hambre",
        "de Derechos Humanos",
        "de Apoyo a la Infancia",
        "para el Desarrollo Sostenible",
        "de Cooperación Internacional",
        "de Acción Social",
        "para la Investigación del Cáncer",
        "de Enfermedades Raras",
        "de Víctimas del Terrorismo",
        "de Familias Numerosas",
        "de Consumidores y Usuarios",
        "de Vecinos",
        "Cultural",
        "Deportiva",
    ]

    tema = random.choice(temas)
    texto = f"{prefijo} {tema}"

    return {
        "texto": texto,
        "prefijo": prefijo,
        "tipo": "ORGANIZACION_SIN_ANIMO_LUCRO"
    }


def main():
    """Generate organizations dataset."""
    print("=" * 60)
    print("GENERADOR DE ORGANIZACIONES ESPAÑOLAS")
    print("=" * 60)

    # Load data
    print("\n[1/3] Loading gazetteers...")
    municipios = load_municipios()
    ciudades = CIUDADES + random.sample(municipios, min(50, len(municipios)))
    print(f"    Ciudades disponibles: {len(ciudades)}")

    # Generate organizations
    print("\n[2/3] Generating organizations...")

    organizaciones = {
        "empresas_privadas": [generate_private_company() for _ in range(400)],
        "instituciones_publicas": [generate_public_institution(ciudades) for _ in range(300)],
        "entidades_financieras": [generate_financial_entity() for _ in range(100)],
        "organizaciones_religiosas": [generate_religious_org(ciudades) for _ in range(100)],
        "sin_animo_lucro": [generate_nonprofit() for _ in range(100)],
    }

    total = sum(len(v) for v in organizaciones.values())
    print(f"    Total organizaciones: {total}")

    # Build output
    print("\n[3/3] Saving output...")

    output = {
        "source": "Synthetic - Spanish Organizations for Legal Documents",
        "description": "Organizaciones españolas sintéticas para documentos legales",
        "stats": {k: len(v) for k, v in organizaciones.items()},
        "total": total,
        "datos": organizaciones,
    }

    # Flat list for NER training
    flat_data = {
        "todos_textos": [],
        "por_tipo": {}
    }

    for tipo, orgs in organizaciones.items():
        textos = [o["texto"] for o in orgs]
        flat_data["todos_textos"].extend(textos)
        flat_data["por_tipo"][tipo] = textos

    # Save
    with open(GAZETTEERS_DIR / "organizaciones.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"    Saved: {GAZETTEERS_DIR / 'organizaciones.json'}")

    with open(GAZETTEERS_DIR / "organizaciones_flat.json", "w", encoding="utf-8") as f:
        json.dump(flat_data, f, ensure_ascii=False, indent=2)
    print(f"    Saved: {GAZETTEERS_DIR / 'organizaciones_flat.json'}")

    # Summary
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    for tipo, orgs in organizaciones.items():
        print(f"  {tipo}: {len(orgs)}")
    print(f"\n  TOTAL: {total}")

    print("\nEjemplos por tipo:")
    for tipo, orgs in organizaciones.items():
        muestra = random.choice(orgs)
        print(f"  {tipo}: {muestra['texto']}")


if __name__ == "__main__":
    main()
