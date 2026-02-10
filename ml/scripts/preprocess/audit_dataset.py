#!/usr/bin/env python3
"""Audit the synthetic NER dataset for quality issues."""

import json
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"


def audit_spans():
    """Check if JSON spans match actual text."""
    print("=== AUDITORÍA DE SPANS ===\n")

    with open(DATA_DIR / "synthetic_ner_dataset.json") as f:
        data = json.load(f)

    errors = []
    for i, sent in enumerate(data["sentences"]):
        text = sent["text"]
        for ent in sent["entities"]:
            extracted = text[ent["start"]:ent["end"]]
            if extracted != ent["text"]:
                errors.append({
                    "sentence": i,
                    "expected": ent["text"],
                    "got": extracted,
                    "start": ent["start"],
                    "end": ent["end"]
                })

    if errors:
        print(f"❌ ERRORES DE SPAN: {len(errors)}")
        for e in errors[:5]:
            print(f"   Sent {e['sentence']}: esperado '{e['expected']}' pero extraído '{e['got']}'")
    else:
        print("✅ Todos los spans JSON son correctos")

    return len(errors)


def audit_bio_sequences():
    """Check BIO tag sequences for errors."""
    print("\n=== AUDITORÍA DE SECUENCIAS BIO ===\n")

    with open(DATA_DIR / "synthetic_ner_dataset.bio") as f:
        lines = f.readlines()

    errors = []
    prev_label = "O"

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            prev_label = "O"
            continue

        parts = line.split("\t")
        if len(parts) != 2:
            continue

        token, label = parts

        # Check I- without B-
        if label.startswith("I-"):
            entity_type = label[2:]
            if prev_label == "O" or (prev_label.startswith("B-") and prev_label[2:] != entity_type):
                if not (prev_label.startswith("I-") and prev_label[2:] == entity_type):
                    errors.append(f"Line {i}: I-{entity_type} sin B- previo (prev: {prev_label})")

        prev_label = label

    if errors:
        print(f"❌ ERRORES DE SECUENCIA BIO: {len(errors)}")
        for e in errors[:5]:
            print(f"   {e}")
    else:
        print("✅ Todas las secuencias BIO son válidas")

    return len(errors)


def audit_tokenization():
    """Check for tokenization issues (punctuation attached)."""
    print("\n=== AUDITORÍA DE TOKENIZACIÓN ===\n")

    with open(DATA_DIR / "synthetic_ner_dataset.bio") as f:
        lines = f.readlines()

    punct_attached = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        parts = line.split("\t")
        if len(parts) != 2:
            continue

        token, label = parts

        # Check punctuation at end of entity tokens
        if label != "O" and token and token[-1] in ",.;:!?":
            punct_attached.append((i, token, label))

    if punct_attached:
        print(f"⚠️  TOKENS CON PUNTUACIÓN PEGADA: {len(punct_attached)}")
        print("   (Esto causará problemas en inferencia)")
        for i, token, label in punct_attached[:10]:
            print(f"   Line {i}: '{token}' -> {label}")
    else:
        print("✅ No hay puntuación pegada a tokens de entidades")

    return len(punct_attached)


def audit_balance():
    """Check entity type balance."""
    print("\n=== AUDITORÍA DE BALANCE ===\n")

    with open(DATA_DIR / "synthetic_ner_dataset.bio") as f:
        lines = f.readlines()

    entity_counts = Counter()
    for line in lines:
        line = line.strip()
        if not line:
            continue

        parts = line.split("\t")
        if len(parts) != 2:
            continue

        token, label = parts
        if label.startswith("B-"):
            entity_counts[label[2:]] += 1

    print("Distribución de entidades (por B- tags):")
    total = sum(entity_counts.values())
    for entity, count in sorted(entity_counts.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        bar = "█" * int(pct / 2)
        balance = "⚠️ BAJO" if pct < 3 else "✅"
        print(f"   {entity:20} {count:5} ({pct:5.1f}%) {bar} {balance}")

    low_count = sum(1 for c in entity_counts.values() if c < 150)
    return low_count


def audit_diversity():
    """Check template diversity."""
    print("\n=== AUDITORÍA DE DIVERSIDAD ===\n")

    with open(DATA_DIR / "synthetic_ner_dataset.json") as f:
        data = json.load(f)

    # Check first 20 chars pattern
    starts = Counter()
    for sent in data["sentences"]:
        start = sent["text"][:30]
        starts[start] += 1

    repetitions = sum(1 for c in starts.values() if c > 10)

    print(f"Patrones de inicio únicos: {len(starts)}")
    print(f"Patrones muy repetidos (>10 veces): {repetitions}")

    if repetitions > 20:
        print("⚠️  POCA DIVERSIDAD - muchos patrones repetidos")
    else:
        print("✅ Diversidad aceptable")

    return repetitions


def main():
    print("=" * 60)
    print("AUDITORÍA DE CALIDAD DEL DATASET SINTÉTICO")
    print("=" * 60)

    span_errors = audit_spans()
    bio_errors = audit_bio_sequences()
    punct_issues = audit_tokenization()
    balance_issues = audit_balance()
    diversity_issues = audit_diversity()

    print("\n" + "=" * 60)
    print("RESUMEN DE PROBLEMAS")
    print("=" * 60)

    issues = []
    if span_errors > 0:
        issues.append(f"❌ {span_errors} errores de span")
    if bio_errors > 0:
        issues.append(f"❌ {bio_errors} errores de secuencia BIO")
    if punct_issues > 0:
        issues.append(f"⚠️  {punct_issues} tokens con puntuación pegada")
    if balance_issues > 3:
        issues.append(f"⚠️  {balance_issues} tipos de entidad con pocos ejemplos")
    if diversity_issues > 20:
        issues.append(f"⚠️  {diversity_issues} patrones muy repetidos")

    if issues:
        print("\nProblemas detectados:")
        for issue in issues:
            print(f"  {issue}")

        print("\n⚠️  EL DATASET NECESITA CORRECCIONES ANTES DEL ENTRENAMIENTO")
    else:
        print("\n✅ Dataset listo para entrenamiento")


if __name__ == "__main__":
    main()
