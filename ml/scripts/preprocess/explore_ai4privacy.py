#!/usr/bin/env python3
"""
Explore ai4privacy/pii-masking-300k dataset structure and content.
"""

from collections import Counter
from datasets import load_from_disk
from pathlib import Path


DATA_PATH = Path(__file__).parent.parent.parent / "data" / "raw" / "ai4privacy" / "pii-masking-300k"


def main():
    print("=" * 70)
    print("EXPLORACIÓN: ai4privacy/pii-masking-300k")
    print("=" * 70)

    # Load dataset
    print("\n[1] Cargando dataset...")
    ds = load_from_disk(str(DATA_PATH))
    print(f"    Splits disponibles: {list(ds.keys())}")

    for split_name, split_data in ds.items():
        print(f"\n[2] Split: {split_name}")
        print(f"    Ejemplos: {len(split_data)}")
        print(f"    Columnas: {split_data.column_names}")

        # Show first example
        print(f"\n[3] Primer ejemplo ({split_name}):")
        example = split_data[0]
        for key, value in example.items():
            if isinstance(value, str) and len(value) > 200:
                print(f"    {key}: {value[:200]}...")
            elif isinstance(value, list) and len(value) > 5:
                print(f"    {key}: {value[:5]}... ({len(value)} items)")
            else:
                print(f"    {key}: {value}")

    # Analyze PII types in train split
    print("\n" + "=" * 70)
    print("[4] ANÁLISIS DE TIPOS DE PII (train)")
    print("=" * 70)

    train = ds["train"]

    # Check if there's a label or entity type column
    pii_types = Counter()
    languages = Counter()

    for i, example in enumerate(train):
        # Count languages if available
        if "language" in example:
            languages[example["language"]] += 1
        elif "lang" in example:
            languages[example["lang"]] += 1

        # Look for PII annotations
        if "privacy_mask" in example:
            masks = example["privacy_mask"]
            if isinstance(masks, list):
                for mask in masks:
                    if isinstance(mask, dict) and "label" in mask:
                        pii_types[mask["label"]] += 1
                    elif isinstance(mask, str):
                        pii_types[mask] += 1

        if "span_labels" in example:
            for label in example["span_labels"]:
                pii_types[label] += 1

        if "masked_text" in example and "source_text" in example:
            # Count [MASK] tokens or similar
            pass

        # Sample check - stop after 1000 for speed
        if i >= 1000:
            break

    if languages:
        print("\n    Idiomas (primeros 1000 ejemplos):")
        for lang, count in languages.most_common(20):
            print(f"      {lang}: {count}")

    if pii_types:
        print("\n    Tipos de PII encontrados:")
        for pii_type, count in pii_types.most_common(30):
            print(f"      {pii_type}: {count}")

    # Show 5 random examples with Spanish if available
    print("\n" + "=" * 70)
    print("[5] EJEMPLOS EN ESPAÑOL (si existen)")
    print("=" * 70)

    spanish_examples = []
    for i, example in enumerate(train):
        lang = example.get("language", example.get("lang", ""))
        if "spanish" in str(lang).lower() or "es" == str(lang).lower():
            spanish_examples.append(example)
            if len(spanish_examples) >= 5:
                break
        if i > 10000:  # Don't search forever
            break

    if spanish_examples:
        for i, ex in enumerate(spanish_examples, 1):
            print(f"\n--- Ejemplo español {i} ---")
            for key, value in ex.items():
                if isinstance(value, str) and len(value) > 300:
                    print(f"  {key}: {value[:300]}...")
                else:
                    print(f"  {key}: {value}")
    else:
        print("    No se encontraron ejemplos en español en los primeros 10k")
        print("    Mostrando 3 ejemplos aleatorios:")
        for i in [0, 100, 500]:
            print(f"\n--- Ejemplo {i} ---")
            ex = train[i]
            for key, value in ex.items():
                if isinstance(value, str) and len(value) > 300:
                    print(f"  {key}: {value[:300]}...")
                else:
                    print(f"  {key}: {value}")

    # Summary
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"Total ejemplos train: {len(train)}")
    print(f"Total ejemplos validation: {len(ds.get('validation', []))}")
    print(f"Columnas: {train.column_names}")


if __name__ == "__main__":
    main()
