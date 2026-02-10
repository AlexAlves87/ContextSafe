#!/usr/bin/env python3
"""
Parse INE Excel gazetteers into structured JSON format for NER training.

Outputs:
- gazetteers/apellidos.json: 27k+ Spanish surnames with frequencies
- gazetteers/nombres_hombres.json: Male names by decade
- gazetteers/nombres_mujeres.json: Female names by decade
- gazetteers/nombres_todos.json: All names merged
- gazetteers/codigos_postales.json: 14k+ postal codes with municipalities
- gazetteers/municipios.json: 8k+ Spanish municipalities
"""

import json
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).parent.parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "gazetteers"


def parse_apellidos() -> dict:
    """Parse INE apellidos_frecuencia.xls into structured format."""
    print("[1/6] Parsing apellidos...")

    filepath = RAW_DIR / "gazetteers_ine" / "apellidos_frecuencia.xls"
    df = pd.read_excel(filepath, engine="xlrd", header=4, usecols=[0, 1, 2, 3, 4])
    df.columns = ["orden", "apellido", "freq_1er", "freq_2do", "freq_ambos"]
    df = df.dropna(subset=["apellido"])
    df = df[df["apellido"].apply(lambda x: isinstance(x, str))]

    apellidos = []
    for _, row in df.iterrows():
        apellidos.append({
            "apellido": row["apellido"].strip(),
            "frecuencia": int(row["freq_1er"]) if pd.notna(row["freq_1er"]) else 0
        })

    result = {
        "source": "INE - Estadística de Apellidos",
        "url": "https://www.ine.es/dyngs/INEbase/operacion.htm?c=Estadistica_C&cid=1254736177009",
        "total": len(apellidos),
        "apellidos": apellidos
    }

    print(f"    Extracted {len(apellidos)} surnames")
    return result


def parse_nombres_por_decada() -> tuple[dict, dict]:
    """Parse INE nombres_por_fecha.xls into male/female names by decade."""
    print("[2/6] Parsing nombres por década...")

    filepath = RAW_DIR / "gazetteers_ine" / "nombres_por_fecha.xls"
    xls = pd.ExcelFile(filepath, engine="xlrd")

    decades = [
        ("pre1930", "NACIDOS ANTES DE 1930"),
        ("1930s", "NACIDOS EN AÑOS 1930 A 1939"),
        ("1940s", "NACIDOS EN AÑOS 1940 A 1949"),
        ("1950s", "NACIDOS EN AÑOS 1950 A 1959"),
        ("1960s", "NACIDOS EN AÑOS 1960 A 1969"),
        ("1970s", "NACIDOS EN AÑOS 1970 A 1979"),
        ("1980s", "NACIDOS EN AÑOS 1980 A 1989"),
        ("1990s", "NACIDOS EN AÑOS 1990 A 1999"),
        ("2000s", "NACIDOS EN AÑOS 2000 A 2009"),
        ("2010s", "NACIDOS EN AÑOS 2010 A 2019"),
        ("2020s", "NACIDOS EN AÑOS 2020 Y 2021"),
    ]

    def extract_names_from_sheet(sheet_name: str, gender: str) -> dict:
        """Extract names from a gender-specific sheet."""
        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)

        names_by_decade = {}
        for i, (decade_key, decade_label) in enumerate(decades):
            col_name = i * 3 + 1
            col_freq = i * 3 + 2

            decade_names = []
            for row_idx in range(5, min(55, len(df))):
                name = df.iloc[row_idx, col_name] if col_name < len(df.columns) else None
                freq = df.iloc[row_idx, col_freq] if col_freq < len(df.columns) else None

                if pd.notna(name) and isinstance(name, str) and name.strip():
                    decade_names.append({
                        "nombre": name.strip(),
                        "frecuencia": int(freq) if pd.notna(freq) else 0
                    })

            if decade_names:
                names_by_decade[decade_key] = decade_names

        return names_by_decade

    hombres = extract_names_from_sheet("ESPAÑA_hombres", "M")
    mujeres = extract_names_from_sheet("ESPAÑA_mujeres", "F")

    result_h = {
        "source": "INE - Nombres por fecha de nacimiento",
        "gender": "male",
        "total_decades": len(hombres),
        "nombres_por_decada": hombres
    }

    result_m = {
        "source": "INE - Nombres por fecha de nacimiento",
        "gender": "female",
        "total_decades": len(mujeres),
        "nombres_por_decada": mujeres
    }

    total_h = sum(len(v) for v in hombres.values())
    total_m = sum(len(v) for v in mujeres.values())
    print(f"    Extracted {total_h} male names, {total_m} female names")

    return result_h, result_m


def merge_all_names(hombres: dict, mujeres: dict) -> dict:
    """Merge all unique names from both genders."""
    print("[3/6] Merging all names...")

    all_names = set()

    for decade_names in hombres.get("nombres_por_decada", {}).values():
        for item in decade_names:
            all_names.add(item["nombre"].upper())

    for decade_names in mujeres.get("nombres_por_decada", {}).values():
        for item in decade_names:
            all_names.add(item["nombre"].upper())

    result = {
        "source": "INE - Nombres combinados",
        "total": len(all_names),
        "nombres": sorted(all_names)
    }

    print(f"    Total unique names: {len(all_names)}")
    return result


def parse_codigos_postales() -> dict:
    """Parse códigos postales CSV."""
    print("[4/6] Parsing códigos postales...")

    filepath = RAW_DIR / "codigos_postales" / "codigos_postales_municipios.csv"
    df = pd.read_csv(filepath)

    # Group by CP to get all municipalities for each CP
    cp_data = {}
    for _, row in df.iterrows():
        cp = str(row["codigo_postal"]).zfill(5)
        municipio = row["municipio_nombre"]

        if cp not in cp_data:
            cp_data[cp] = {"codigo_postal": cp, "municipios": []}

        if municipio not in cp_data[cp]["municipios"]:
            cp_data[cp]["municipios"].append(municipio)

    result = {
        "source": "ds-codigos-postales-ine-es",
        "url": "https://github.com/inigoflores/ds-codigos-postales-ine-es",
        "total": len(cp_data),
        "codigos_postales": list(cp_data.values())
    }

    print(f"    Extracted {len(cp_data)} unique postal codes")
    return result


def parse_municipios() -> dict:
    """Parse municipios Excel."""
    print("[5/6] Parsing municipios...")

    filepath = RAW_DIR / "municipios" / "municipios_2024.xlsx"
    df = pd.read_excel(filepath, engine="openpyxl", header=None)

    # Find the actual header row and data
    municipios = []
    for idx in range(1, len(df)):
        row = df.iloc[idx]
        nombre = row.iloc[4] if len(row) > 4 else None

        if pd.notna(nombre) and isinstance(nombre, str) and nombre.strip():
            if nombre.upper() != "NOMBRE":
                municipios.append(nombre.strip())

    result = {
        "source": "INE - Relación de municipios",
        "url": "https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736177031",
        "total": len(municipios),
        "municipios": sorted(set(municipios))
    }

    print(f"    Extracted {len(result['municipios'])} unique municipalities")
    return result


def save_json(data: dict, filename: str) -> None:
    """Save data to JSON file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = OUTPUT_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"    Saved: {filepath}")


def main() -> None:
    """Main entry point."""
    print("=" * 60)
    print("INE GAZETTEERS PARSER")
    print("=" * 60)

    # Parse all sources
    apellidos = parse_apellidos()
    nombres_h, nombres_m = parse_nombres_por_decada()
    nombres_todos = merge_all_names(nombres_h, nombres_m)
    codigos_postales = parse_codigos_postales()
    municipios = parse_municipios()

    # Save all outputs
    print("\n[6/6] Saving JSON files...")
    save_json(apellidos, "apellidos.json")
    save_json(nombres_h, "nombres_hombres.json")
    save_json(nombres_m, "nombres_mujeres.json")
    save_json(nombres_todos, "nombres_todos.json")
    save_json(codigos_postales, "codigos_postales.json")
    save_json(municipios, "municipios.json")

    # Summary
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Apellidos: {apellidos['total']}")
    print(f"Nombres (únicos): {nombres_todos['total']}")
    print(f"Códigos postales: {codigos_postales['total']}")
    print(f"Municipios: {municipios['total']}")
    print(f"\nOutput directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
