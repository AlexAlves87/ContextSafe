#!/usr/bin/env python3
"""
Prepare synthetic NER dataset for LoRA fine-tuning.

Converts span-based JSON format to HuggingFace datasets format with BIO tags.
Creates train/dev/test splits (80/10/10).

Input: data/processed/synthetic_ner_dataset.json
Output: data/processed/lora_dataset/ (HuggingFace datasets format)

Usage:
    cd ml
    source .venv/bin/activate
    python scripts/preprocess/prepare_dataset_for_lora.py

Author: AlexAlves87
Date: 2026-02-04
"""

import json
import random
import time
from pathlib import Path
from typing import Any

from transformers import AutoTokenizer


# =============================================================================
# CONFIGURATION
# =============================================================================

# Entity types (same as training)
ENTITY_TYPES = [
    "PERSON", "DNI_NIE", "IBAN", "PHONE", "EMAIL", "ADDRESS",
    "LOCATION", "POSTAL_CODE", "DATE", "ORGANIZATION",
    "LICENSE_PLATE", "NSS", "CADASTRAL_REF", "ECLI", "PROFESSIONAL_ID"
]

# BIO label to ID mapping
def build_label_mappings(entity_types: list[str]) -> tuple[dict, dict]:
    """Build label2id and id2label mappings for BIO scheme."""
    label2id = {"O": 0}
    id2label = {0: "O"}

    idx = 1
    for entity_type in sorted(entity_types):
        label2id[f"B-{entity_type}"] = idx
        id2label[idx] = f"B-{entity_type}"
        idx += 1
        label2id[f"I-{entity_type}"] = idx
        id2label[idx] = f"I-{entity_type}"
        idx += 1

    return label2id, id2label


LABEL2ID, ID2LABEL = build_label_mappings(ENTITY_TYPES)


# =============================================================================
# TOKENIZATION AND ALIGNMENT
# =============================================================================

def align_labels_with_tokens(
    text: str,
    entities: list[dict],
    tokenizer: Any,
    max_length: int = 512,
) -> dict:
    """
    Tokenize text and align entity labels with subword tokens.

    Uses offset_mapping to map character spans to token indices.
    BIO tagging: B- for first token, I- for continuation tokens.

    Returns dict with input_ids, attention_mask, labels (aligned).
    """
    # Tokenize with offset mapping
    encoding = tokenizer(
        text,
        max_length=max_length,
        truncation=True,
        padding="max_length",
        return_offsets_mapping=True,
        return_tensors=None,
    )

    offset_mapping = encoding["offset_mapping"]
    labels = [LABEL2ID["O"]] * len(offset_mapping)

    # Sort entities by start position
    sorted_entities = sorted(entities, key=lambda e: e["start"])

    # Assign labels based on offset mapping
    for entity in sorted_entities:
        entity_start = entity["start"]
        entity_end = entity["end"]
        entity_label = entity["label"]

        # Validate entity type
        if entity_label not in ENTITY_TYPES:
            continue

        b_label = LABEL2ID.get(f"B-{entity_label}")
        i_label = LABEL2ID.get(f"I-{entity_label}")

        if b_label is None or i_label is None:
            continue

        # Find tokens that overlap with entity span
        is_first_token = True
        for idx, (token_start, token_end) in enumerate(offset_mapping):
            # Skip special tokens (offset 0,0)
            if token_start == 0 and token_end == 0:
                continue

            # Check if token overlaps with entity
            if token_start >= entity_start and token_end <= entity_end:
                # Token is fully within entity
                if is_first_token:
                    labels[idx] = b_label
                    is_first_token = False
                else:
                    labels[idx] = i_label
            elif token_start < entity_end and token_end > entity_start:
                # Partial overlap - include it
                if is_first_token:
                    labels[idx] = b_label
                    is_first_token = False
                else:
                    labels[idx] = i_label

    # Set labels for special tokens to -100 (ignored in loss)
    for idx, (token_start, token_end) in enumerate(offset_mapping):
        if token_start == 0 and token_end == 0:
            labels[idx] = -100

    return {
        "input_ids": encoding["input_ids"],
        "attention_mask": encoding["attention_mask"],
        "labels": labels,
    }


def process_dataset(
    sentences: list[dict],
    tokenizer: Any,
    max_length: int = 512,
) -> list[dict]:
    """Process all sentences into tokenized format."""
    processed = []

    for sent in sentences:
        text = sent["text"]
        entities = sent["entities"]

        result = align_labels_with_tokens(text, entities, tokenizer, max_length)
        result["text"] = text  # Keep original text for reference
        processed.append(result)

    return processed


# =============================================================================
# SPLIT AND SAVE
# =============================================================================

def split_dataset(
    data: list[dict],
    train_ratio: float = 0.8,
    dev_ratio: float = 0.1,
    seed: int = 42,
) -> tuple[list, list, list]:
    """Split dataset into train/dev/test."""
    random.seed(seed)
    shuffled = data.copy()
    random.shuffle(shuffled)

    n = len(shuffled)
    train_end = int(n * train_ratio)
    dev_end = int(n * (train_ratio + dev_ratio))

    return shuffled[:train_end], shuffled[train_end:dev_end], shuffled[dev_end:]


def save_dataset(
    train_data: list[dict],
    dev_data: list[dict],
    test_data: list[dict],
    output_dir: Path,
    label2id: dict,
    id2label: dict,
) -> None:
    """Save dataset in HuggingFace-compatible JSON format."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save splits
    for name, data in [("train", train_data), ("dev", dev_data), ("test", test_data)]:
        path = output_dir / f"{name}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  Saved {name}: {len(data)} examples → {path}")

    # Save label mappings
    mappings = {
        "label2id": label2id,
        "id2label": {str(k): v for k, v in id2label.items()},
        "num_labels": len(label2id),
        "entity_types": sorted(ENTITY_TYPES),
    }

    mappings_path = output_dir / "label_mappings.json"
    with open(mappings_path, "w", encoding="utf-8") as f:
        json.dump(mappings, f, ensure_ascii=False, indent=2)
    print(f"  Saved label mappings → {mappings_path}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Prepare dataset for LoRA fine-tuning."""
    start_time = time.time()

    print("=" * 70)
    print("DATASET PREPARATION FOR LORA FINE-TUNING")
    print("=" * 70)

    # Paths
    base_dir = Path(__file__).resolve().parent.parent.parent
    input_path = base_dir / "data" / "processed" / "synthetic_ner_dataset.json"
    output_dir = base_dir / "data" / "processed" / "lora_dataset"
    model_path = base_dir / "models" / "pretrained" / "legal-xlm-roberta-base"

    # Load tokenizer
    print(f"\nLoading tokenizer from {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(str(model_path))
    print(f"  Vocab size: {tokenizer.vocab_size}")
    print(f"  Max length: {tokenizer.model_max_length}")

    # Load dataset
    print(f"\nLoading dataset from {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    sentences = data["sentences"]
    print(f"  Total sentences: {len(sentences)}")
    print(f"  Entity types: {len(data['entity_types'])}")

    # Process dataset
    print("\nTokenizing and aligning labels...")
    processed = process_dataset(sentences, tokenizer, max_length=512)
    print(f"  Processed: {len(processed)} examples")

    # Count entity distribution
    entity_counts = {}
    for sent in sentences:
        for ent in sent["entities"]:
            label = ent["label"]
            entity_counts[label] = entity_counts.get(label, 0) + 1

    print("\n  Entity distribution:")
    for label in sorted(entity_counts.keys()):
        print(f"    {label}: {entity_counts[label]}")

    # Split dataset
    print("\nSplitting dataset (80/10/10)...")
    train_data, dev_data, test_data = split_dataset(processed)
    print(f"  Train: {len(train_data)}")
    print(f"  Dev: {len(dev_data)}")
    print(f"  Test: {len(test_data)}")

    # Save dataset
    print(f"\nSaving to {output_dir}...")
    save_dataset(train_data, dev_data, test_data, output_dir, LABEL2ID, ID2LABEL)

    # Summary
    elapsed = time.time() - start_time
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Input: {input_path}")
    print(f"  Output: {output_dir}")
    print(f"  Total examples: {len(processed)}")
    print(f"  Train/Dev/Test: {len(train_data)}/{len(dev_data)}/{len(test_data)}")
    print(f"  Labels: {len(LABEL2ID)} (O + {len(ENTITY_TYPES)} types × 2)")
    print(f"  Time: {elapsed:.1f}s")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    exit(main())
