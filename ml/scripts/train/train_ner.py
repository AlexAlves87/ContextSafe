#!/usr/bin/env python3
"""
Fine-tune RoBERTa-BNE-capitel-ner for Spanish Legal NER.

Based on best practices from research:
- Learning rate: 2e-5 (most important hyperparameter)
- Batch size: 16 + gradient accumulation 2 (effective 32)
- Epochs: 4 (conservative for legal domain)
- Warmup: 6% of total steps
- Weight decay: 0.01
- Max length: 384 (legal documents)
- Early stopping on validation F1

Usage:
    python scripts/train/train_ner.py

Output:
    models/legal_ner_v1/
"""

import json
import os
from pathlib import Path

import numpy as np
import torch
from datasets import load_from_disk
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    DataCollatorForTokenClassification,
    EarlyStoppingCallback,
    Trainer,
    TrainingArguments,
)

# Conditional import for evaluate
try:
    import evaluate
    seqeval = evaluate.load("seqeval")
except ImportError:
    print("WARNING: 'evaluate' not installed. Run: pip install evaluate seqeval")
    seqeval = None


# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "processed" / "ner_dataset_v3"
MODEL_PATH = BASE_DIR / "models" / "checkpoints" / "roberta-base-bne-capitel-ner"
OUTPUT_DIR = BASE_DIR / "models" / "legal_ner_v2"

# Hyperparameters from research (resultado.md)
CONFIG = {
    # Learning & Optimization (MOST IMPORTANT)
    "learning_rate": 2e-5,          # Start here, grid: {1e-5, 2e-5, 3e-5, 5e-5}
    "weight_decay": 0.01,           # L2 regularization
    "adam_epsilon": 1e-8,           # Numerical stability

    # Batching
    "per_device_train_batch_size": 16,
    "per_device_eval_batch_size": 32,
    "gradient_accumulation_steps": 2,  # Effective batch = 32

    # Epochs & Steps
    "num_train_epochs": 4,          # Conservative for legal domain

    # Learning Rate Scheduling
    "warmup_ratio": 0.06,           # 6% warmup (RoBERTa paper)
    "lr_scheduler_type": "linear",  # Linear decay after warmup

    # Early Stopping
    "early_stopping_patience": 2,   # Stop if no improvement for 2 evals
    "metric_for_best_model": "f1",

    # Sequence Length
    "max_length": 384,              # Legal documents (not 128!)

    # Hardware
    "fp16": torch.cuda.is_available(),  # Mixed precision if GPU
    "dataloader_num_workers": 4,

    # Reproducibility
    "seed": 42,
}


# =============================================================================
# LOAD DATA AND MODEL
# =============================================================================

def load_data():
    """Load dataset and label mappings."""
    print("Loading dataset...")
    dataset = load_from_disk(str(DATA_DIR))

    with open(DATA_DIR / "label_mappings.json") as f:
        mappings = json.load(f)

    label2id = mappings["label2id"]
    id2label = {int(k): v for k, v in mappings["id2label"].items()}

    print(f"  Train: {len(dataset['train'])} samples")
    print(f"  Validation: {len(dataset['validation'])} samples")
    print(f"  Test: {len(dataset['test'])} samples")
    print(f"  Labels: {len(label2id)}")

    return dataset, label2id, id2label


def load_model(label2id, id2label):
    """Load pretrained model and tokenizer."""
    print(f"\nLoading model from {MODEL_PATH}...")

    tokenizer = AutoTokenizer.from_pretrained(str(MODEL_PATH))

    model = AutoModelForTokenClassification.from_pretrained(
        str(MODEL_PATH),
        num_labels=len(label2id),
        id2label=id2label,
        label2id=label2id,
        ignore_mismatched_sizes=True,  # New classifier head
    )

    print(f"  Model: {type(model).__name__}")
    print(f"  Parameters: {model.num_parameters():,}")

    return model, tokenizer


# =============================================================================
# METRICS
# =============================================================================

def compute_metrics(eval_preds, id2label):
    """
    Compute entity-level metrics using seqeval.

    Returns precision, recall, F1 overall and per entity type.
    """
    predictions, labels = eval_preds
    predictions = np.argmax(predictions, axis=2)

    # Convert IDs to label strings, ignoring -100
    true_labels = []
    pred_labels = []

    for prediction, label in zip(predictions, labels):
        true_seq = []
        pred_seq = []

        for pred_id, label_id in zip(prediction, label):
            if label_id != -100:  # Ignore padding/subwords
                true_seq.append(id2label[label_id])
                pred_seq.append(id2label[pred_id])

        true_labels.append(true_seq)
        pred_labels.append(pred_seq)

    if seqeval is None:
        # Fallback if seqeval not available
        return {"f1": 0.0, "precision": 0.0, "recall": 0.0}

    results = seqeval.compute(predictions=pred_labels, references=true_labels)

    return {
        "precision": results["overall_precision"],
        "recall": results["overall_recall"],
        "f1": results["overall_f1"],
        "accuracy": results["overall_accuracy"],
    }


def compute_metrics_detailed(eval_preds, id2label):
    """
    Compute detailed metrics per entity type.

    Call this separately for final evaluation.
    """
    predictions, labels = eval_preds
    predictions = np.argmax(predictions, axis=2)

    true_labels = []
    pred_labels = []

    for prediction, label in zip(predictions, labels):
        true_seq = []
        pred_seq = []

        for pred_id, label_id in zip(prediction, label):
            if label_id != -100:
                true_seq.append(id2label[label_id])
                pred_seq.append(id2label[pred_id])

        true_labels.append(true_seq)
        pred_labels.append(pred_seq)

    if seqeval is None:
        return {}

    results = seqeval.compute(predictions=pred_labels, references=true_labels)

    return results


# =============================================================================
# TRAINING
# =============================================================================

def train(model, tokenizer, dataset, id2label):
    """Run training with Trainer API."""

    # Data collator
    data_collator = DataCollatorForTokenClassification(
        tokenizer=tokenizer,
        padding=True,
        max_length=CONFIG["max_length"],
    )

    # Calculate warmup steps (6% of total training steps)
    effective_batch_size = CONFIG["per_device_train_batch_size"] * CONFIG["gradient_accumulation_steps"]
    total_steps = (len(dataset["train"]) // effective_batch_size) * CONFIG["num_train_epochs"]
    warmup_steps = int(total_steps * CONFIG["warmup_ratio"])

    # Training arguments
    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),

        # Learning & Optimization
        learning_rate=CONFIG["learning_rate"],
        weight_decay=CONFIG["weight_decay"],
        adam_epsilon=CONFIG["adam_epsilon"],

        # Batching
        per_device_train_batch_size=CONFIG["per_device_train_batch_size"],
        per_device_eval_batch_size=CONFIG["per_device_eval_batch_size"],
        gradient_accumulation_steps=CONFIG["gradient_accumulation_steps"],

        # Epochs
        num_train_epochs=CONFIG["num_train_epochs"],

        # LR Scheduling
        warmup_steps=warmup_steps,
        lr_scheduler_type=CONFIG["lr_scheduler_type"],

        # Evaluation & Saving
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model=CONFIG["metric_for_best_model"],
        greater_is_better=True,

        # Logging
        logging_strategy="steps",
        logging_steps=50,
        report_to="none",  # Disable wandb/tensorboard

        # Hardware
        fp16=CONFIG["fp16"],
        dataloader_num_workers=CONFIG["dataloader_num_workers"],

        # Reproducibility
        seed=CONFIG["seed"],

        # Save limits
        save_total_limit=2,
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        data_collator=data_collator,
        processing_class=tokenizer,  # Changed from tokenizer= (deprecated in v5)
        compute_metrics=lambda p: compute_metrics(p, id2label),
        callbacks=[
            EarlyStoppingCallback(
                early_stopping_patience=CONFIG["early_stopping_patience"]
            )
        ],
    )

    print("\n" + "=" * 60)
    print("STARTING TRAINING")
    print("=" * 60)
    print(f"Learning rate: {CONFIG['learning_rate']}")
    print(f"Effective batch size: {effective_batch_size}")
    print(f"Total steps: {total_steps}")
    print(f"Warmup steps: {warmup_steps} ({CONFIG['warmup_ratio']*100}%)")
    print(f"Epochs: {CONFIG['num_train_epochs']}")
    print(f"Early stopping patience: {CONFIG['early_stopping_patience']}")
    print("=" * 60 + "\n")

    # Train
    trainer.train()

    return trainer


# =============================================================================
# EVALUATION
# =============================================================================

def evaluate_model(trainer, dataset, id2label):
    """Final evaluation on test set with detailed metrics."""

    print("\n" + "=" * 60)
    print("FINAL EVALUATION ON TEST SET")
    print("=" * 60)

    # Get predictions
    predictions = trainer.predict(dataset["test"])

    # Detailed metrics
    results = compute_metrics_detailed(
        (predictions.predictions, predictions.label_ids),
        id2label
    )

    # Print overall metrics
    print(f"\nOverall Metrics:")
    print(f"  Precision: {results.get('overall_precision', 0):.4f}")
    print(f"  Recall:    {results.get('overall_recall', 0):.4f}")
    print(f"  F1:        {results.get('overall_f1', 0):.4f}")
    print(f"  Accuracy:  {results.get('overall_accuracy', 0):.4f}")

    # Print per-entity metrics
    print(f"\nPer-Entity Metrics:")
    print(f"{'Entity':<20} {'Precision':>10} {'Recall':>10} {'F1':>10} {'Support':>10}")
    print("-" * 60)

    for entity, metrics in sorted(results.items()):
        if entity.startswith("overall"):
            continue
        if isinstance(metrics, dict):
            print(f"{entity:<20} {metrics.get('precision', 0):>10.4f} {metrics.get('recall', 0):>10.4f} {metrics.get('f1', 0):>10.4f} {metrics.get('number', 0):>10}")

    return results


def save_model(trainer, tokenizer, id2label, label2id):
    """Save model, tokenizer, and config."""

    print(f"\nSaving model to {OUTPUT_DIR}...")

    # Save model
    trainer.save_model(str(OUTPUT_DIR))

    # Save tokenizer
    tokenizer.save_pretrained(str(OUTPUT_DIR))

    # Save label mappings
    with open(OUTPUT_DIR / "label_mappings.json", "w") as f:
        json.dump({
            "label2id": label2id,
            "id2label": {str(k): v for k, v in id2label.items()},
        }, f, indent=2)

    # Save config
    with open(OUTPUT_DIR / "training_config.json", "w") as f:
        json.dump(CONFIG, f, indent=2)

    print("  ✓ Model saved")
    print("  ✓ Tokenizer saved")
    print("  ✓ Label mappings saved")
    print("  ✓ Training config saved")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("SPANISH LEGAL NER FINE-TUNING")
    print("=" * 60)

    # Check GPU
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    else:
        print("WARNING: No GPU detected. Training will be slow.")

    # Load data
    dataset, label2id, id2label = load_data()

    # Load model
    model, tokenizer = load_model(label2id, id2label)

    # Train
    trainer = train(model, tokenizer, dataset, id2label)

    # Evaluate
    results = evaluate_model(trainer, dataset, id2label)

    # Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    save_model(trainer, tokenizer, id2label, label2id)

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"Best model saved to: {OUTPUT_DIR}")
    print(f"Final F1: {results.get('overall_f1', 0):.4f}")


if __name__ == "__main__":
    main()
