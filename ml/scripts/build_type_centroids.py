#!/usr/bin/env python3
"""
Build Type Centroids for Entity Type Validation.

This script generates embedding centroids for each PII category using
curated training examples. The centroids are used by EntityTypeValidator
to validate/correct NER type assignments.

Strategy: Embed ONLY the entity text (not full sentences) to maximize
inter-category separation. Full-sentence embeddings produce centroids
with >0.93 cosine similarity because the legal context dominates.

Usage:
    python ml/scripts/build_type_centroids.py
    python ml/scripts/build_type_centroids.py --validate

Output:
    ml/models/type_centroids.json

References:
    - NER Retriever: arXiv 2509.04011 (2025)
    - CEPTNER: Knowledge-Based Systems (2024)
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

# Training examples: ENTITY TEXT ONLY (no surrounding context)
# E5 uses "query:" prefix for the piece we want to classify
TRAINING_EXAMPLES: dict[str, list[str]] = {
    "PERSON_NAME": [
        # Full names (nombre + apellidos)
        "query: Juan García López",
        "query: María López Fernández",
        "query: Pedro Sánchez Martínez",
        "query: Ana Martínez Ruiz",
        "query: Carlos Rodríguez Pérez",
        "query: Isabel Fernández Díaz",
        "query: Miguel Ángel González",
        "query: Carmen Ruiz Torres",
        "query: Alberto Baxeras Aizpún",
        "query: Alejandro Álvarez García",
        "query: Francisco Javier López Hernández",
        "query: Rosa María Díaz Pérez",
        "query: José Antonio Muñoz Sanz",
        "query: Marta Sánchez García",
        "query: Luis Fernández Ruiz",
        "query: Elena Torres Vega",
        "query: Manuel Gómez López",
        "query: Patricia Hernández Moreno",
        "query: Rafael Martín Sanz",
        "query: Lucía García Navarro",
        # With honorifics (as NER would detect them)
        "query: D. Pedro Sánchez",
        "query: Dña. Ana Martínez",
        "query: Don Carlos Rodríguez",
        "query: Doña Isabel Fernández",
        "query: Sr. González Ruiz",
        "query: Sra. Carmen López",
        # Short/single names
        "query: Pura",
        "query: Iker",
        "query: Aitor",
        "query: Nerea",
        "query: Iñaki",
        "query: Antonio",
        "query: Cristina",
        "query: Roberto",
        "query: Macarena",
        "query: Gonzalo",
        # Surnames only (as they appear in legal texts)
        "query: García López",
        "query: Martínez Rodríguez",
        "query: Fernández Díaz",
        "query: Sánchez Moreno",
        "query: González Pérez",
    ],
    "ORGANIZATION": [
        # Companies with legal forms
        "query: Telefónica S.A.",
        "query: Banco Santander",
        "query: BBVA",
        "query: Repsol S.A.",
        "query: Iberdrola",
        "query: Endesa S.A.",
        "query: Mapfre Seguros",
        "query: El Corte Inglés S.A.",
        "query: Inditex",
        "query: Mercadona S.A.",
        "query: Caixabank",
        "query: Banco Sabadell",
        "query: Ferrovial S.A.",
        "query: ACS Construcciones",
        "query: Naturgy Energy Group",
        # Public institutions
        "query: Ministerio de Justicia",
        "query: Agencia Tributaria",
        "query: SEPE",
        "query: Seguridad Social",
        "query: Ayuntamiento de Madrid",
        "query: Comunidad de Madrid",
        "query: Tribunal Supremo",
        "query: Audiencia Provincial",
        "query: Juzgado de lo Social",
        "query: Tribunal Superior de Justicia",
        "query: Consejo General del Poder Judicial",
        # NGOs and associations
        "query: Fundación ONCE",
        "query: Cruz Roja Española",
        "query: Cáritas Diocesana",
        "query: Asociación de Consumidores",
        # Foreign companies
        "query: Google Spain S.L.",
        "query: Amazon EU S.à.r.l.",
        "query: Microsoft Ibérica S.R.L.",
        # Unions
        "query: Comisiones Obreras",
        "query: Unión General de Trabajadores",
        "query: Confederación Sindical",
    ],
    "LOCATION": [
        # Cities
        "query: Madrid",
        "query: Barcelona",
        "query: Valencia",
        "query: Sevilla",
        "query: Bilbao",
        "query: Zaragoza",
        "query: Málaga",
        "query: Murcia",
        "query: Palma de Mallorca",
        "query: Las Palmas de Gran Canaria",
        "query: Valladolid",
        "query: Vigo",
        "query: Gijón",
        "query: Hospitalet de Llobregat",
        # Provinces and regions
        "query: Cantabria",
        "query: Asturias",
        "query: Galicia",
        "query: Andalucía",
        "query: Cataluña",
        "query: Aragón",
        "query: País Vasco",
        "query: Extremadura",
        "query: Castilla y León",
        "query: Castilla-La Mancha",
        # Islands
        "query: Tenerife",
        "query: Gran Canaria",
        "query: Lanzarote",
        "query: Fuerteventura",
        "query: Mallorca",
        "query: Ibiza",
        # Towns
        "query: Alcobendas",
        "query: Pozuelo de Alarcón",
        "query: Getafe",
        "query: Leganés",
        "query: Móstoles",
        "query: Torrejón de Ardoz",
        "query: Alcalá de Henares",
    ],
    "ADDRESS": [
        # Street addresses (as they appear in documents)
        "query: Calle Mayor número 15",
        "query: C/ Gran Vía 45, 3º B",
        "query: Avenida de la Constitución 23",
        "query: Paseo de la Castellana 120",
        "query: Plaza de España 7, bajo",
        "query: Calle Alcalá 200",
        "query: C/ Serrano 50, 2º izquierda",
        "query: Avda. Diagonal 450, 4º 1ª",
        "query: Rambla Catalunya 100",
        "query: C/ Princesa 25, 4º izquierda",
        "query: Calle Goya 15, 2º derecha",
        "query: Avda. América 30, ático",
        "query: Plaza Mayor 3, entresuelo",
        "query: C/ Fuencarral 100, bajo A",
        "query: Camino de los Molinos km 5",
        "query: Carretera Nacional 340",
        "query: Polígono Industrial Sur, nave 12",
        "query: C/ del Carmen 8, 1º piso",
        "query: Travesía de Gracia 15",
        "query: Ronda de Segovia 42, 3º C",
    ],
    "DATE": [
        # Dates as they appear in text (just the date part)
        "query: 15 de marzo de 2024",
        "query: 10/10/2025",
        "query: 05-11-2024",
        "query: 23 de enero de 2025",
        "query: 1 de febrero de 2023",
        "query: 30/06/2024",
        "query: 31-12-2025",
        "query: 14 de abril de 1985",
        "query: 22/09/2020",
        "query: 15-08-2030",
        "query: 5 de octubre de 2024",
        "query: 3 de noviembre de 2025",
        "query: 20 de diciembre de 2023",
        "query: 1 de enero de 2025",
        "query: 15/03/2024",
        "query: 31 de julio de 2024",
        "query: 28/02/2025",
        "query: 12-09-2023",
        "query: 25 de septiembre de 2024",
        "query: 7 de junio de 2025",
    ],
    # NOT_ENTITY: Spanish words commonly misclassified as entities
    "NOT_ENTITY": [
        "query: Finalmente",
        "query: Terminaba",
        "query: Quien",
        "query: Mientras",
        "query: Aunque",
        "query: Porque",
        "query: Entonces",
        "query: Además",
        "query: También",
        "query: Siendo",
        "query: Habiendo",
        "query: Teniendo",
        "query: Dice",
        "query: Señala",
        "query: Indica",
        "query: Establece",
        "query: Dispone",
        "query: Resultando",
        "query: Considerando",
        "query: Estado",
    ],
}


def build_centroids(
    model_name: str = "intfloat/multilingual-e5-large",
    output_path: Path | None = None,
) -> dict[str, list[float]]:
    """
    Build embedding centroids for each entity type.

    Strategy: Embed entity text only (no context sentences) to maximize
    inter-category separation.

    Args:
        model_name: HuggingFace model for embeddings.
        output_path: Where to save the centroids JSON.

    Returns:
        Dictionary mapping category -> centroid (as list).
    """
    from sentence_transformers import SentenceTransformer

    print(f"Loading model: {model_name}")
    start = time.time()
    model = SentenceTransformer(model_name)
    print(f"Model loaded in {time.time() - start:.2f}s")

    centroids = {}

    for category, examples in TRAINING_EXAMPLES.items():
        print(f"\nProcessing {category} ({len(examples)} examples)...")
        start = time.time()

        # Generate embeddings for all examples
        embeddings = model.encode(
            examples,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        # Compute centroid (mean of all embeddings)
        centroid = np.mean(embeddings, axis=0)

        # Normalize centroid
        centroid = centroid / np.linalg.norm(centroid)

        centroids[category] = centroid.tolist()

        elapsed = time.time() - start
        print(f"  Computed centroid in {elapsed:.2f}s")
        print(f"  Embedding dimension: {len(centroid)}")

    # Save to file
    if output_path is None:
        output_path = Path(__file__).parent.parent / "models" / "type_centroids.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(centroids, f, indent=2)

    print(f"\nCentroids saved to: {output_path}")
    print(f"Categories: {list(centroids.keys())}")

    return centroids


def validate_centroids(centroids_path: Path) -> None:
    """
    Validate centroids by computing inter-category distances.

    Good centroids should have:
    - Low inter-class similarity (< 0.85 ideally)
    - NOT_ENTITY should be far from all PII types
    """
    print("\n=== Centroid Validation ===\n")

    with open(centroids_path) as f:
        centroids = json.load(f)

    categories = list(centroids.keys())
    n = len(categories)

    # Convert to numpy arrays
    centroid_arrays = {k: np.array(v) for k, v in centroids.items()}

    # Compute pairwise similarities
    print("Inter-category cosine similarities:")
    print("-" * 60)

    similarity_matrix = np.zeros((n, n))
    for i, cat1 in enumerate(categories):
        for j, cat2 in enumerate(categories):
            sim = float(np.dot(centroid_arrays[cat1], centroid_arrays[cat2]))
            similarity_matrix[i, j] = sim
            if i < j:
                marker = " !!!" if sim > 0.90 else " !" if sim > 0.85 else ""
                print(f"  {cat1:15} <-> {cat2:15}: {sim:.4f}{marker}")

    print("-" * 60)

    # Summary
    pii_cats = [c for c in categories if c != "NOT_ENTITY"]
    not_entity_sims = []
    pii_sims = []

    for i, cat1 in enumerate(categories):
        for j, cat2 in enumerate(categories):
            if i >= j:
                continue
            sim = similarity_matrix[i, j]
            if cat1 == "NOT_ENTITY" or cat2 == "NOT_ENTITY":
                not_entity_sims.append((cat1, cat2, sim))
            else:
                pii_sims.append((cat1, cat2, sim))

    print("\nPII inter-category similarities:")
    if pii_sims:
        sims = [s[2] for s in pii_sims]
        print(f"  Min: {min(sims):.4f}")
        print(f"  Max: {max(sims):.4f}")
        print(f"  Mean: {np.mean(sims):.4f}")

    print("\nNOT_ENTITY distance from PII types:")
    if not_entity_sims:
        for cat1, cat2, sim in not_entity_sims:
            other = cat2 if cat1 == "NOT_ENTITY" else cat1
            print(f"  {other:15}: {sim:.4f}")

    # Warnings
    print("\nPotentially confusable pairs (similarity > 0.90):")
    confusable = [(c1, c2, s) for c1, c2, s in pii_sims if s > 0.90]
    if confusable:
        for c1, c2, s in confusable:
            print(f"  WARNING: {c1} <-> {c2}: {s:.4f}")
    else:
        print("  None - centroids are well separated!")


def test_classification(centroids_path: Path) -> None:
    """
    Test classification on known examples to verify accuracy.
    """
    from sentence_transformers import SentenceTransformer

    print("\n=== Classification Test ===\n")

    with open(centroids_path) as f:
        centroids = json.load(f)

    centroid_arrays = {k: np.array(v) for k, v in centroids.items()}

    model = SentenceTransformer("intfloat/multilingual-e5-large")

    # Test cases: (entity_text, expected_type)
    test_cases = [
        # Person names
        ("query: Alejandro Alvarez", "PERSON_NAME"),
        ("query: D. Alberto Baxeras", "PERSON_NAME"),
        ("query: María García", "PERSON_NAME"),
        ("query: Pura", "PERSON_NAME"),
        # Organizations
        ("query: Telefónica S.A.", "ORGANIZATION"),
        ("query: Banco Santander", "ORGANIZATION"),
        ("query: Ministerio de Justicia", "ORGANIZATION"),
        ("query: BBVA", "ORGANIZATION"),
        # Locations
        ("query: Madrid", "LOCATION"),
        ("query: Tenerife", "LOCATION"),
        ("query: Barcelona", "LOCATION"),
        # Dates
        ("query: 10/10/2025", "DATE"),
        ("query: 15 de marzo de 2024", "DATE"),
        ("query: 05-11-2024", "DATE"),
        # Addresses
        ("query: C/ Gran Vía 45, 3º B", "ADDRESS"),
        ("query: Calle Mayor 15", "ADDRESS"),
        # Not entities (should be closest to NOT_ENTITY)
        ("query: Finalmente", "NOT_ENTITY"),
        ("query: Quien", "NOT_ENTITY"),
        ("query: Terminaba", "NOT_ENTITY"),
    ]

    embeddings = model.encode(
        [tc[0] for tc in test_cases],
        normalize_embeddings=True,
    )

    correct = 0
    total = len(test_cases)

    for i, (text, expected) in enumerate(test_cases):
        emb = embeddings[i]
        sims = {cat: float(np.dot(emb, centroid_arrays[cat])) for cat in centroids}
        predicted = max(sims, key=sims.get)
        match = "OK" if predicted == expected else "FAIL"
        if predicted == expected:
            correct += 1

        entity_text = text.replace("query: ", "")
        print(
            f"  [{match:4}] '{entity_text:35}' "
            f"expected={expected:15} predicted={predicted:15} "
            f"(score={sims[predicted]:.4f}, expected_score={sims[expected]:.4f})"
        )

    print(f"\nAccuracy: {correct}/{total} ({100*correct/total:.1f}%)")


if __name__ == "__main__":
    import sys

    output_path = Path(__file__).parent.parent / "models" / "type_centroids.json"

    if len(sys.argv) > 1 and sys.argv[1] == "--validate":
        if output_path.exists():
            validate_centroids(output_path)
        else:
            print(f"Centroids file not found: {output_path}")
            print("Run without --validate to build centroids first.")

    elif len(sys.argv) > 1 and sys.argv[1] == "--test":
        if output_path.exists():
            test_classification(output_path)
        else:
            print(f"Centroids file not found: {output_path}")
            print("Run without --test to build centroids first.")

    else:
        print("=" * 60)
        print("Building Entity Type Centroids (entity-only strategy)")
        print("=" * 60)

        centroids = build_centroids(output_path=output_path)

        print("\n" + "=" * 60)
        print("Validating Centroids")
        print("=" * 60)

        validate_centroids(output_path)

        print("\n" + "=" * 60)
        print("Testing Classification")
        print("=" * 60)

        test_classification(output_path)

        elapsed_total = time.time()
        print("\n" + "=" * 60)
        print("DONE")
        print("=" * 60)
        print(f"\nCentroids file: {output_path}")
