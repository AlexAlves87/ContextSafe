#!/usr/bin/env python3
"""
Generate synthetic Spanish administrative identifiers for NER training.

Generates INVALID but realistic-looking identifiers:
- DNI (Documento Nacional de Identidad) - 8 digits + letter (INVALID checksum)
- NIE (Número de Identidad de Extranjero) - X/Y/Z + 7 digits + letter (INVALID checksum)
- IBAN (International Bank Account Number) - ES + 22 digits (INVALID check digits)
- NSS (Número de Seguridad Social) - 12 digits (INVALID control)
- Tarjetas de crédito - 16 digits (FAILS Luhn)
- Matrículas - Spanish license plates
- Referencias catastrales - Cadastral references
- ECLI - European Case Law Identifier
- Números de colegiado - Professional IDs

IMPORTANT: All generated numbers have MATHEMATICALLY INVALID checksums
to ensure they cannot correspond to real people.

Output: gazetteers/identificadores_administrativos.json
"""

import json
import random
import string
from pathlib import Path


BASE_DIR = Path(__file__).parent.parent.parent
GAZETTEERS_DIR = BASE_DIR / "gazetteers"

# =============================================================================
# DNI / NIE
# =============================================================================

DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"

def generate_invalid_dni() -> dict:
    """Generate DNI with INVALID check letter."""
    numero = random.randint(10000000, 99999999)
    # Calculate correct letter
    correct_letter = DNI_LETTERS[numero % 23]
    # Pick a DIFFERENT letter (invalid)
    invalid_letters = [l for l in DNI_LETTERS if l != correct_letter]
    invalid_letter = random.choice(invalid_letters)

    # Format variations
    formats = [
        f"{numero}{invalid_letter}",
        f"{numero}-{invalid_letter}",
        f"{numero:08d}{invalid_letter}",
        f"{numero:08d}-{invalid_letter}",
    ]

    return {
        "texto": random.choice(formats),
        "numero": numero,
        "letra_invalida": invalid_letter,
        "letra_correcta": correct_letter,
        "tipo": "DNI"
    }


def generate_invalid_nie() -> dict:
    """Generate NIE with INVALID check letter."""
    # NIE starts with X, Y, or Z
    prefixes = {"X": 0, "Y": 1, "Z": 2}
    prefix = random.choice(list(prefixes.keys()))
    numero = random.randint(1000000, 9999999)

    # For NIE, replace X->0, Y->1, Z->2 to calculate letter
    full_number = prefixes[prefix] * 10000000 + numero
    correct_letter = DNI_LETTERS[full_number % 23]

    # Pick INVALID letter
    invalid_letters = [l for l in DNI_LETTERS if l != correct_letter]
    invalid_letter = random.choice(invalid_letters)

    formats = [
        f"{prefix}{numero:07d}{invalid_letter}",
        f"{prefix}-{numero:07d}-{invalid_letter}",
        f"{prefix}{numero:07d}-{invalid_letter}",
    ]

    return {
        "texto": random.choice(formats),
        "prefijo": prefix,
        "numero": numero,
        "letra_invalida": invalid_letter,
        "letra_correcta": correct_letter,
        "tipo": "NIE"
    }


# =============================================================================
# IBAN
# =============================================================================

# Spanish bank codes (BIC)
CODIGOS_BANCO = [
    "0049",  # Santander
    "0075",  # Banco Popular
    "0081",  # Sabadell
    "0128",  # Bankinter
    "0182",  # BBVA
    "2038",  # Bankia/CaixaBank
    "2100",  # CaixaBank
    "0030",  # Banco Español de Crédito
    "0019",  # Deutsche Bank
    "0073",  # Open Bank
    "2085",  # Ibercaja
    "2095",  # Kutxabank
    "2103",  # Unicaja
    "3058",  # Cajamar
    "0487",  # Banco Mare Nostrum
]


def generate_invalid_iban() -> dict:
    """Generate Spanish IBAN with INVALID check digits (always 00)."""
    banco = random.choice(CODIGOS_BANCO)
    sucursal = f"{random.randint(0, 9999):04d}"
    dc = f"{random.randint(0, 99):02d}"  # Control digits (random, likely invalid)
    cuenta = f"{random.randint(0, 9999999999):010d}"

    # IBAN check digits - we use "00" which is ALWAYS invalid
    # (valid check digits are 04-98)
    iban_check = "00"

    # Full IBAN
    iban = f"ES{iban_check}{banco}{sucursal}{dc}{cuenta}"

    # Format variations
    formats = [
        iban,
        f"ES{iban_check} {banco} {sucursal} {dc} {cuenta}",
        f"ES {iban_check} {banco} {sucursal} {dc} {cuenta}",
        f"IBAN: {iban}",
        f"IBAN {iban}",
    ]

    return {
        "texto": random.choice(formats),
        "pais": "ES",
        "digitos_control": iban_check,
        "banco": banco,
        "sucursal": sucursal,
        "dc": dc,
        "cuenta": cuenta,
        "tipo": "IBAN",
        "nota": "Check digits '00' always invalid"
    }


# =============================================================================
# NSS (Número de Seguridad Social)
# =============================================================================

def generate_invalid_nss() -> dict:
    """Generate NSS with INVALID control digits."""
    # NSS format: AA/NNNNNNNN/CC
    # AA = provincia (01-52)
    # NNNNNNNN = número secuencial
    # CC = dígitos de control

    provincia = f"{random.randint(1, 52):02d}"
    numero = f"{random.randint(10000000, 99999999):08d}"

    # Control digits should be: (provincia + numero) mod 97
    # We generate INVALID ones
    full_number = int(provincia + numero)
    correct_control = full_number % 97

    # Pick invalid control (different from correct)
    invalid_control = (correct_control + random.randint(1, 96)) % 97
    control = f"{invalid_control:02d}"

    formats = [
        f"{provincia}/{numero}/{control}",
        f"{provincia}-{numero}-{control}",
        f"{provincia}{numero}{control}",
        f"{provincia} {numero} {control}",
    ]

    return {
        "texto": random.choice(formats),
        "provincia": provincia,
        "numero": numero,
        "control_invalido": control,
        "control_correcto": f"{correct_control:02d}",
        "tipo": "NSS"
    }


# =============================================================================
# TARJETAS DE CRÉDITO (Luhn invalid)
# =============================================================================

def luhn_checksum(card_number: str) -> int:
    """Calculate Luhn checksum."""
    def digits_of(n):
        return [int(d) for d in str(n)]

    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]

    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))

    return checksum % 10


def generate_invalid_credit_card() -> dict:
    """Generate credit card number that FAILS Luhn check."""
    # Common Spanish card prefixes
    prefixes = [
        "4",      # Visa
        "5",      # Mastercard
        "37",     # Amex
        "6011",   # Discover
    ]

    prefix = random.choice(prefixes)

    # Generate 15 digits (16 total with check digit)
    remaining_length = 15 - len(prefix)
    number = prefix + "".join([str(random.randint(0, 9)) for _ in range(remaining_length)])

    # Calculate correct Luhn digit
    checksum = luhn_checksum(number + "0")
    correct_digit = (10 - checksum) % 10

    # Use WRONG digit
    invalid_digit = (correct_digit + random.randint(1, 9)) % 10

    card = number + str(invalid_digit)

    # Format variations
    formats = [
        card,
        f"{card[:4]} {card[4:8]} {card[8:12]} {card[12:]}",
        f"{card[:4]}-{card[4:8]}-{card[8:12]}-{card[12:]}",
    ]

    return {
        "texto": random.choice(formats),
        "numero": card,
        "digito_invalido": str(invalid_digit),
        "digito_correcto": str(correct_digit),
        "tipo": "TARJETA_CREDITO"
    }


# =============================================================================
# TELÉFONOS ESPAÑOLES
# =============================================================================

def generate_phone() -> dict:
    """Generate realistic Spanish phone number."""
    # Spanish phone prefixes
    prefixes_movil = ["6", "7"]
    prefixes_fijo = ["91", "93", "94", "95", "96", "98"]  # Major cities

    if random.random() < 0.6:
        # Mobile
        prefix = random.choice(prefixes_movil)
        resto = "".join([str(random.randint(0, 9)) for _ in range(8)])
        numero = prefix + resto
        tipo_tel = "movil"
    else:
        # Landline
        prefix = random.choice(prefixes_fijo)
        resto = "".join([str(random.randint(0, 9)) for _ in range(7)])
        numero = prefix + resto
        tipo_tel = "fijo"

    # Format variations
    if len(numero) == 9:
        formats = [
            numero,
            f"+34 {numero}",
            f"+34{numero}",
            f"0034 {numero}",
            f"{numero[:3]} {numero[3:6]} {numero[6:]}",
            f"{numero[:3]}-{numero[3:6]}-{numero[6:]}",
            f"+34 {numero[:3]} {numero[3:6]} {numero[6:]}",
            f"Tel: {numero}",
            f"Teléfono: {numero}",
            f"Tfno: {numero}",
            f"Tfno.: {numero}",
        ]
    else:
        formats = [numero]

    return {
        "texto": random.choice(formats),
        "numero": numero,
        "tipo_telefono": tipo_tel,
        "tipo": "TELEFONO"
    }


# =============================================================================
# MATRÍCULAS ESPAÑOLAS
# =============================================================================

def generate_license_plate() -> dict:
    """Generate Spanish license plate."""
    # Current format (since 2000): 0000 BBB (4 digits + 3 letters)
    # Letters exclude vowels and Ñ, Q
    valid_letters = "BCDFGHJKLMNPRSTVWXYZ"

    if random.random() < 0.8:
        # New format (post-2000)
        digits = f"{random.randint(0, 9999):04d}"
        letters = "".join(random.choices(valid_letters, k=3))
        plate = f"{digits} {letters}"
        formato = "nuevo"
    else:
        # Old format (pre-2000): XX-0000-XX (province code)
        provincias = ["M", "B", "V", "SE", "MA", "A", "MU", "Z", "BI", "SS", "NA", "GR", "CO", "PM"]
        provincia = random.choice(provincias)
        digits = f"{random.randint(0, 9999):04d}"
        letters = "".join(random.choices(valid_letters, k=2))
        plate = f"{provincia}-{digits}-{letters}"
        formato = "antiguo"

    # Format variations
    formats = [
        plate,
        plate.replace(" ", ""),
        plate.replace(" ", "-"),
        f"matrícula {plate}",
        f"vehículo con matrícula {plate}",
    ]

    return {
        "texto": random.choice(formats),
        "matricula": plate,
        "formato": formato,
        "tipo": "MATRICULA"
    }


# =============================================================================
# REFERENCIAS CATASTRALES
# =============================================================================

def generate_cadastral_ref() -> dict:
    """Generate Spanish cadastral reference."""
    # Format: 14 or 20 alphanumeric characters
    # Structure: PPMMMSS_AAAAPPPP (province, municipality, section, parcel, etc.)

    provincia = f"{random.randint(1, 52):02d}"
    municipio = f"{random.randint(1, 999):03d}"
    seccion = random.choice(string.ascii_uppercase)

    # Parcel identifier
    parcela = "".join(random.choices(string.digits + string.ascii_uppercase, k=5))

    # Block and floor (urban)
    bloque = f"{random.randint(0, 99):02d}"
    escalera = random.choice(string.ascii_uppercase)
    planta = f"{random.randint(0, 15):02d}"
    puerta = random.choice(string.ascii_uppercase)

    if random.random() < 0.6:
        # Urban reference (20 chars)
        ref = f"{provincia}{municipio}{seccion}{parcela}{bloque}{escalera}{planta}{puerta}"
        tipo_ref = "urbana"
    else:
        # Rural reference (14 chars)
        poligono = f"{random.randint(1, 999):03d}"
        parcela_rural = f"{random.randint(1, 9999):05d}"
        ref = f"{provincia}{municipio}{poligono}{parcela_rural}"
        tipo_ref = "rustica"

    formats = [
        ref,
        f"Ref. Catastral: {ref}",
        f"Referencia catastral {ref}",
        f"finca registral con referencia catastral {ref}",
    ]

    return {
        "texto": random.choice(formats),
        "referencia": ref,
        "tipo_finca": tipo_ref,
        "tipo": "REFERENCIA_CATASTRAL"
    }


# =============================================================================
# ECLI (European Case Law Identifier)
# =============================================================================

def generate_ecli() -> dict:
    """Generate Spanish ECLI identifier."""
    # Format: ECLI:ES:tribunal:year:number
    # Example: ECLI:ES:TS:2020:1234

    tribunales = [
        ("TC", "Tribunal Constitucional"),
        ("TS", "Tribunal Supremo"),
        ("AN", "Audiencia Nacional"),
        ("TSJ", "Tribunal Superior de Justicia"),
        ("APM", "Audiencia Provincial de Madrid"),
        ("APB", "Audiencia Provincial de Barcelona"),
        ("APV", "Audiencia Provincial de Valencia"),
        ("APS", "Audiencia Provincial de Sevilla"),
        ("JPI", "Juzgado de Primera Instancia"),
        ("JS", "Juzgado de lo Social"),
        ("JCA", "Juzgado Contencioso-Administrativo"),
    ]

    tribunal_code, tribunal_name = random.choice(tribunales)
    year = random.randint(1990, 2025)
    number = random.randint(1, 9999)

    ecli = f"ECLI:ES:{tribunal_code}:{year}:{number}"

    formats = [
        ecli,
        f"sentencia {ecli}",
        f"resolución {ecli}",
        f"auto {ecli}",
        f"({ecli})",
    ]

    return {
        "texto": random.choice(formats),
        "ecli": ecli,
        "tribunal": tribunal_code,
        "tribunal_nombre": tribunal_name,
        "anio": year,
        "numero": number,
        "tipo": "ECLI"
    }


# =============================================================================
# NÚMEROS DE COLEGIADO (Professional IDs)
# =============================================================================

def generate_professional_id() -> dict:
    """Generate Spanish professional registration numbers."""
    colegios = [
        ("ICAM", "Ilustre Colegio de Abogados de Madrid", 6),
        ("ICAB", "Ilustre Colegio de Abogados de Barcelona", 6),
        ("ICAV", "Ilustre Colegio de Abogados de Valencia", 5),
        ("ICAS", "Ilustre Colegio de Abogados de Sevilla", 5),
        ("REICAZ", "Real e Ilustre Colegio de Abogados de Zaragoza", 5),
        ("ICOMEM", "Ilustre Colegio de Médicos de Madrid", 6),
        ("COMB", "Col·legi de Metges de Barcelona", 6),
        ("COAM", "Colegio Oficial de Arquitectos de Madrid", 5),
        ("COAIB", "Colegio Oficial de Arquitectos de las Islas Baleares", 4),
        ("COGITI", "Colegio Oficial de Graduados e Ingenieros Técnicos", 6),
        ("COPITIMAC", "Colegio de Peritos e Ingenieros Técnicos", 5),
        ("CNP", "Cuerpo Nacional de Policía", 6),
        ("GUARDIA_CIVIL", "Guardia Civil", 8),
    ]

    colegio_code, colegio_name, num_digits = random.choice(colegios)
    numero = random.randint(10**(num_digits-1), 10**num_digits - 1)

    formats = [
        f"{colegio_code} {numero}",
        f"{colegio_code}-{numero}",
        f"{colegio_code}/{numero}",
        f"colegiado nº {numero} del {colegio_code}",
        f"colegiado número {numero}",
        f"nº colegiado {numero}",
        f"col. nº {numero}",
    ]

    return {
        "texto": random.choice(formats),
        "colegio": colegio_code,
        "colegio_nombre": colegio_name,
        "numero": numero,
        "tipo": "ID_PROFESIONAL"
    }


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Generate all administrative identifiers."""
    print("=" * 60)
    print("GENERADOR DE IDENTIFICADORES ADMINISTRATIVOS")
    print("=" * 60)

    # Configuration
    config = {
        "DNI": (generate_invalid_dni, 500),
        "NIE": (generate_invalid_nie, 200),
        "IBAN": (generate_invalid_iban, 300),
        "NSS": (generate_invalid_nss, 200),
        "TARJETA_CREDITO": (generate_invalid_credit_card, 150),
        "TELEFONO": (generate_phone, 400),
        "MATRICULA": (generate_license_plate, 200),
        "REFERENCIA_CATASTRAL": (generate_cadastral_ref, 200),
        "ECLI": (generate_ecli, 200),
        "ID_PROFESIONAL": (generate_professional_id, 200),
    }

    all_data = {}
    total = 0

    for tipo, (generator, cantidad) in config.items():
        print(f"\n[{tipo}] Generando {cantidad} ejemplos...")
        ejemplos = [generator() for _ in range(cantidad)]
        all_data[tipo] = ejemplos
        total += cantidad
        print(f"    ✓ {len(ejemplos)} generados")

    # Build output
    print("\n" + "=" * 60)
    print("Guardando resultados...")

    output = {
        "source": "Synthetic - Spanish Administrative Identifiers",
        "description": "Identificadores administrativos españoles sintéticos con checksums INVÁLIDOS",
        "warning": "TODOS los checksums son matemáticamente inválidos - no corresponden a datos reales",
        "stats": {tipo: len(data) for tipo, data in all_data.items()},
        "total": total,
        "datos": all_data
    }

    # Flat list for NER training
    flat_data = {
        "todos_textos": [],
        "por_tipo": {}
    }

    for tipo, ejemplos in all_data.items():
        textos = [e["texto"] for e in ejemplos]
        flat_data["todos_textos"].extend(textos)
        flat_data["por_tipo"][tipo] = textos

    # Save
    with open(GAZETTEERS_DIR / "identificadores_administrativos.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"    Saved: {GAZETTEERS_DIR / 'identificadores_administrativos.json'}")

    with open(GAZETTEERS_DIR / "identificadores_administrativos_flat.json", "w", encoding="utf-8") as f:
        json.dump(flat_data, f, ensure_ascii=False, indent=2)
    print(f"    Saved: {GAZETTEERS_DIR / 'identificadores_administrativos_flat.json'}")

    # Summary
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    for tipo, cantidad in output["stats"].items():
        print(f"  {tipo}: {cantidad}")
    print(f"\n  TOTAL: {total}")

    print("\nEjemplos por tipo:")
    for tipo, ejemplos in all_data.items():
        muestra = random.choice(ejemplos)
        print(f"  {tipo}: {muestra['texto']}")


if __name__ == "__main__":
    main()
