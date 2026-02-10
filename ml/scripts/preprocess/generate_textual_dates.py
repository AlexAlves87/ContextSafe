#!/usr/bin/env python3
"""
Generate synthetic textual Spanish dates for NER training.

Spanish legal documents use fully spelled-out dates:
- "veintisiete de octubre de mil novecientos cuarenta y tres"
- "el día primero de enero del año dos mil veintiuno"
- "a los quince días del mes de septiembre de mil ochocientos noventa"

Output: gazetteers/fechas_textuales.json
"""

import json
import random
from pathlib import Path


BASE_DIR = Path(__file__).parent.parent.parent
GAZETTEERS_DIR = BASE_DIR / "gazetteers"

# =============================================================================
# NÚMEROS EN ESPAÑOL
# =============================================================================

UNIDADES = {
    0: "",
    1: "uno", 2: "dos", 3: "tres", 4: "cuatro", 5: "cinco",
    6: "seis", 7: "siete", 8: "ocho", 9: "nueve", 10: "diez",
    11: "once", 12: "doce", 13: "trece", 14: "catorce", 15: "quince",
    16: "dieciséis", 17: "diecisiete", 18: "dieciocho", 19: "diecinueve",
    20: "veinte", 21: "veintiuno", 22: "veintidós", 23: "veintitrés",
    24: "veinticuatro", 25: "veinticinco", 26: "veintiséis",
    27: "veintisiete", 28: "veintiocho", 29: "veintinueve",
}

DECENAS = {
    3: "treinta", 4: "cuarenta", 5: "cincuenta",
    6: "sesenta", 7: "setenta", 8: "ochenta", 9: "noventa",
}

CENTENAS = {
    1: "ciento", 2: "doscientos", 3: "trescientos", 4: "cuatrocientos",
    5: "quinientos", 6: "seiscientos", 7: "setecientos", 8: "ochocientos",
    9: "novecientos",
}

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]

# Ordinales para días (primero, segundo, etc.)
ORDINALES_DIA = {
    1: "primero", 2: "segundo", 3: "tercero", 4: "cuarto", 5: "quinto",
    6: "sexto", 7: "séptimo", 8: "octavo", 9: "noveno", 10: "décimo",
    11: "undécimo", 12: "duodécimo", 13: "decimotercero", 14: "decimocuarto",
    15: "decimoquinto", 16: "decimosexto", 17: "decimoséptimo",
    18: "decimoctavo", 19: "decimonoveno", 20: "vigésimo",
    21: "vigésimo primero", 22: "vigésimo segundo", 23: "vigésimo tercero",
    24: "vigésimo cuarto", 25: "vigésimo quinto", 26: "vigésimo sexto",
    27: "vigésimo séptimo", 28: "vigésimo octavo", 29: "vigésimo noveno",
    30: "trigésimo", 31: "trigésimo primero",
}


def numero_a_texto(n: int) -> str:
    """Convert a number (1-31) to Spanish text."""
    if n in UNIDADES:
        return UNIDADES[n]
    elif n < 100:
        decena = n // 10
        unidad = n % 10
        if unidad == 0:
            return DECENAS[decena]
        else:
            return f"{DECENAS[decena]} y {UNIDADES[unidad]}"
    return str(n)


def anio_a_texto(anio: int) -> str:
    """Convert a year (1800-2100) to Spanish text."""
    if anio == 2000:
        return "dos mil"

    # Split into components
    millar = anio // 1000
    resto = anio % 1000
    centena = resto // 100
    decena_unidad = resto % 100

    partes = []

    # Millar
    if millar == 1:
        partes.append("mil")
    elif millar == 2:
        partes.append("dos mil")

    # Centena
    if centena > 0:
        if centena == 1 and decena_unidad == 0:
            partes.append("cien")
        else:
            partes.append(CENTENAS[centena])

    # Decena y unidad
    if decena_unidad > 0:
        if decena_unidad in UNIDADES:
            partes.append(UNIDADES[decena_unidad])
        else:
            decena = decena_unidad // 10
            unidad = decena_unidad % 10
            if unidad == 0:
                partes.append(DECENAS[decena])
            else:
                partes.append(f"{DECENAS[decena]} y {UNIDADES[unidad]}")

    return " ".join(partes)


def generar_fecha_textual(dia: int, mes: int, anio: int, patron: str) -> str:
    """Generate a textual date using the specified pattern."""
    dia_texto = numero_a_texto(dia)
    dia_ordinal = ORDINALES_DIA.get(dia, numero_a_texto(dia))
    mes_texto = MESES[mes - 1]
    anio_texto = anio_a_texto(anio)

    return patron.format(
        dia=dia_texto,
        dia_ordinal=dia_ordinal,
        mes=mes_texto,
        anio=anio_texto,
        anio_num=str(anio)
    )


# =============================================================================
# PATRONES DE FECHAS EN DOCUMENTOS LEGALES ESPAÑOLES
# =============================================================================

PATRONES_FECHA = [
    # Formato estándar
    "{dia} de {mes} de {anio}",
    "el {dia} de {mes} de {anio}",
    "día {dia} de {mes} de {anio}",
    "el día {dia} de {mes} de {anio}",
    "a {dia} de {mes} de {anio}",

    # Con "del año"
    "{dia} de {mes} del año {anio}",
    "el {dia} de {mes} del año {anio}",
    "día {dia} de {mes} del año {anio}",
    "el día {dia} de {mes} del año {anio}",

    # Ordinales
    "el día {dia_ordinal} de {mes} de {anio}",
    "día {dia_ordinal} del mes de {mes} de {anio}",
    "el {dia_ordinal} día del mes de {mes} de {anio}",

    # Formato largo notarial
    "a los {dia} días del mes de {mes} de {anio}",
    "a los {dia} días del mes de {mes} del año {anio}",
    "en el día {dia} del mes de {mes} del año {anio}",
    "siendo el día {dia} de {mes} de {anio}",
    "en fecha {dia} de {mes} de {anio}",
    "con fecha {dia} de {mes} de {anio}",
    "fechado el {dia} de {mes} de {anio}",
    "fechado a {dia} de {mes} de {anio}",

    # Formato testamentario
    "otorgado el {dia} de {mes} de {anio}",
    "extendido el día {dia} de {mes} de {anio}",
    "firmado el {dia} de {mes} de {anio}",
    "suscrito el día {dia} de {mes} de {anio}",
    "celebrado el {dia} de {mes} de {anio}",

    # Formato judicial
    "dictado el {dia} de {mes} de {anio}",
    "notificado el {dia} de {mes} de {anio}",
    "pronunciado el {dia} de {mes} de {anio}",
    "emitido el {dia} de {mes} de {anio}",

    # Nacimiento/defunción
    "nacido el {dia} de {mes} de {anio}",
    "nacida el {dia} de {mes} de {anio}",
    "fallecido el {dia} de {mes} de {anio}",
    "fallecida el {dia} de {mes} de {anio}",

    # Híbridos (texto + número)
    "{dia} de {mes} de {anio_num}",
    "el {dia} de {mes} de {anio_num}",
    "día {dia} de {mes} de {anio_num}",
]

# Patrones para "primero" en lugar de "uno"
PATRONES_PRIMERO = [
    "el primero de {mes} de {anio}",
    "día primero de {mes} de {anio}",
    "el día primero de {mes} de {anio}",
    "a primero de {mes} de {anio}",
    "el primero de {mes} del año {anio}",
]


def dias_en_mes(mes: int, anio: int) -> int:
    """Return number of days in a month."""
    if mes in [4, 6, 9, 11]:
        return 30
    elif mes == 2:
        if anio % 4 == 0 and (anio % 100 != 0 or anio % 400 == 0):
            return 29
        return 28
    return 31


def generar_fechas():
    """Generate comprehensive set of textual dates."""
    fechas = []

    # Rangos de años relevantes para documentos legales españoles
    rangos_anios = [
        (1850, 1900, 50),    # Siglo XIX
        (1900, 1940, 100),   # Pre-Guerra Civil
        (1940, 1980, 150),   # Franquismo
        (1980, 2000, 100),   # Transición
        (2000, 2025, 200),   # Contemporáneo
    ]

    for anio_inicio, anio_fin, cantidad in rangos_anios:
        for _ in range(cantidad):
            anio = random.randint(anio_inicio, anio_fin)
            mes = random.randint(1, 12)
            max_dia = dias_en_mes(mes, anio)
            dia = random.randint(1, max_dia)

            # Seleccionar patrón
            if dia == 1 and random.random() < 0.5:
                # Usar "primero" para día 1
                patron = random.choice(PATRONES_PRIMERO)
                texto = patron.format(
                    mes=MESES[mes - 1],
                    anio=anio_a_texto(anio)
                )
            else:
                patron = random.choice(PATRONES_FECHA)
                texto = generar_fecha_textual(dia, mes, anio, patron)

            fechas.append({
                "texto": texto,
                "dia": dia,
                "mes": mes,
                "anio": anio,
                "patron": patron,
                "fecha_iso": f"{anio:04d}-{mes:02d}-{dia:02d}"
            })

    return fechas


def generar_fechas_especiales():
    """Generate historically significant dates that appear in legal documents."""
    fechas_especiales = []

    # Fechas históricas relevantes
    fechas_historicas = [
        (18, 7, 1936, "inicio de la Guerra Civil"),
        (1, 4, 1939, "fin de la Guerra Civil"),
        (20, 11, 1975, "muerte de Franco"),
        (15, 6, 1977, "primeras elecciones democráticas"),
        (6, 12, 1978, "aprobación de la Constitución"),
        (29, 12, 1978, "entrada en vigor de la Constitución"),
        (23, 2, 1981, "intento de golpe de estado"),
        (1, 1, 1986, "entrada en la CEE"),
        (1, 1, 2002, "entrada del euro"),
    ]

    for dia, mes, anio, descripcion in fechas_historicas:
        for patron in random.sample(PATRONES_FECHA, min(5, len(PATRONES_FECHA))):
            texto = generar_fecha_textual(dia, mes, anio, patron)
            fechas_especiales.append({
                "texto": texto,
                "dia": dia,
                "mes": mes,
                "anio": anio,
                "patron": patron,
                "fecha_iso": f"{anio:04d}-{mes:02d}-{dia:02d}",
                "significado_historico": descripcion
            })

    return fechas_especiales


def main():
    """Generate textual dates dataset."""
    print("=" * 60)
    print("GENERADOR DE FECHAS TEXTUALES ESPAÑOLAS")
    print("=" * 60)

    # Generate dates
    print("\n[1/3] Generando fechas aleatorias...")
    fechas_aleatorias = generar_fechas()
    print(f"    Generadas {len(fechas_aleatorias)} fechas aleatorias")

    print("\n[2/3] Generando fechas históricas especiales...")
    fechas_especiales = generar_fechas_especiales()
    print(f"    Generadas {len(fechas_especiales)} fechas históricas")

    # Build output
    print("\n[3/3] Guardando resultados...")

    output = {
        "source": "Synthetic - Spanish Textual Dates for Legal Documents",
        "description": "Fechas textuales en español para documentos legales",
        "stats": {
            "fechas_aleatorias": len(fechas_aleatorias),
            "fechas_historicas": len(fechas_especiales),
            "total": len(fechas_aleatorias) + len(fechas_especiales),
            "patrones_disponibles": len(PATRONES_FECHA) + len(PATRONES_PRIMERO),
        },
        "patrones": {
            "estandar": PATRONES_FECHA,
            "primero": PATRONES_PRIMERO,
        },
        "fechas": {
            "aleatorias": fechas_aleatorias,
            "historicas": fechas_especiales,
        }
    }

    # Flat list for direct NER training
    flat_dates = {
        "todos_textos": [f["texto"] for f in fechas_aleatorias + fechas_especiales],
        "ejemplos_con_metadata": random.sample(
            fechas_aleatorias + fechas_especiales,
            min(200, len(fechas_aleatorias) + len(fechas_especiales))
        )
    }

    # Save
    with open(GAZETTEERS_DIR / "fechas_textuales.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"    Saved: {GAZETTEERS_DIR / 'fechas_textuales.json'}")

    with open(GAZETTEERS_DIR / "fechas_textuales_flat.json", "w", encoding="utf-8") as f:
        json.dump(flat_dates, f, ensure_ascii=False, indent=2)
    print(f"    Saved: {GAZETTEERS_DIR / 'fechas_textuales_flat.json'}")

    # Summary
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Fechas aleatorias: {len(fechas_aleatorias)}")
    print(f"Fechas históricas: {len(fechas_especiales)}")
    print(f"Total fechas: {len(fechas_aleatorias) + len(fechas_especiales)}")
    print(f"Patrones disponibles: {len(PATRONES_FECHA) + len(PATRONES_PRIMERO)}")

    print("\n10 Ejemplos aleatorios:")
    for ex in random.sample(fechas_aleatorias, min(10, len(fechas_aleatorias))):
        print(f"  • {ex['texto']} ({ex['fecha_iso']})")


if __name__ == "__main__":
    main()
