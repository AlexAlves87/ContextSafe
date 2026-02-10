#!/usr/bin/env python3
"""
LoRA fine-tuning for Legal-XLM-RoBERTa NER.

Fine-tunes Legal-XLM-RoBERTa-base using LoRA (Low-Rank Adaptation) for
Spanish legal NER. Based on best practices from 2025-2026 literature:
- B2NER (COLING 2025): LoRA adapters ≤50MB
- LLaMA-3 Financial NER (2026): r=128, 0.894 F1

Configuration (from docs/reports/2026-02-04_1300_mejores_practicas_ml_2026.md):
- Rank (r): 128
- Alpha (α): 256 (2×r)
- Target modules: All attention + MLP layers
- Learning rate: 2e-4
- Epochs: 3
- Dropout: 0.05

Hardware target: RTX 5060 Ti 16GB VRAM
Expected VRAM usage: ~4-6GB with LoRA
Expected adapter size: ~50MB

Usage:
    cd ml
    source .venv/bin/activate
    pip install peft accelerate seqeval
    python scripts/preprocess/prepare_dataset_for_lora.py  # Prepare data first
    python scripts/train/train_lora_ner.py

Author: AlexAlves87
Date: 2026-02-04
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import torch
from datasets import Dataset
from peft import LoraConfig, TaskType, get_peft_model
from seqeval.metrics import f1_score, precision_score, recall_score, classification_report
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    DataCollatorForTokenClassification,
    Trainer,
    TrainingArguments,
)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class LoRANERConfig:
    """Configuration for LoRA NER training."""

    # Model
    model_name_or_path: str = "models/pretrained/legal-xlm-roberta-base"
    output_dir: str = "models/lora_ner_v1"

    # Dataset
    dataset_dir: str = "data/processed/lora_dataset"

    # LoRA configuration (based on 2025-2026 best practices)
    lora_r: int = 128  # Rank
    lora_alpha: int = 256  # Alpha = 2×r
    lora_dropout: float = 0.05  # Specialized domains
    lora_target_modules: list = field(default_factory=lambda: [
        "query", "key", "value", "dense",  # Attention layers
        "intermediate.dense", "output.dense",  # MLP layers
    ])

    # Training hyperparameters
    learning_rate: float = 2e-4
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 16
    per_device_eval_batch_size: int = 32
    warmup_ratio: float = 0.06
    weight_decay: float = 0.01
    max_length: int = 512

    # Evaluation
    eval_strategy: str = "epoch"
    save_strategy: str = "epoch"
    load_best_model_at_end: bool = True
    metric_for_best_model: str = "eval_f1"
    greater_is_better: bool = True

    # Hardware
    fp16: bool = True  # Use mixed precision
    gradient_accumulation_steps: int = 2  # Effective batch = 32

    # Logging
    logging_steps: int = 50
    report_to: str = "none"  # Disable wandb/tensorboard


# =============================================================================
# DATA LOADING
# =============================================================================

def load_dataset_split(path: Path) -> Dataset:
    """Load a dataset split from JSON."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Remove 'text' field - only keep input_ids, attention_mask, labels
    # DataCollator can't handle string fields
    for item in data:
        if "text" in item:
            del item["text"]

    # Convert to HuggingFace Dataset
    return Dataset.from_list(data)


def load_label_mappings(dataset_dir: Path) -> tuple[dict, dict, int]:
    """Load label mappings."""
    path = dataset_dir / "label_mappings.json"
    with open(path, "r", encoding="utf-8") as f:
        mappings = json.load(f)

    label2id = mappings["label2id"]
    id2label = {int(k): v for k, v in mappings["id2label"].items()}
    num_labels = mappings["num_labels"]

    return label2id, id2label, num_labels


# =============================================================================
# METRICS
# =============================================================================

def compute_metrics(p, id2label: dict):
    """Compute seqeval metrics for NER."""
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)

    # Convert to label strings, ignoring -100
    true_labels = []
    true_predictions = []

    for prediction, label in zip(predictions, labels):
        true_label = []
        true_pred = []

        for p_val, l_val in zip(prediction, label):
            if l_val != -100:
                true_label.append(id2label[l_val])
                true_pred.append(id2label[p_val])

        true_labels.append(true_label)
        true_predictions.append(true_pred)

    return {
        "precision": precision_score(true_labels, true_predictions),
        "recall": recall_score(true_labels, true_predictions),
        "f1": f1_score(true_labels, true_predictions),
    }


# =============================================================================
# MODEL SETUP
# =============================================================================

def create_lora_model(
    model_path: str,
    num_labels: int,
    label2id: dict,
    id2label: dict,
    config: LoRANERConfig,
):
    """Create model with LoRA adapters."""
    print(f"Loading base model from {model_path}...")

    # Load base model for token classification
    model = AutoModelForTokenClassification.from_pretrained(
        model_path,
        num_labels=num_labels,
        label2id=label2id,
        id2label=id2label,
    )

    # Configure LoRA
    lora_config = LoraConfig(
        task_type=TaskType.TOKEN_CLS,
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=config.lora_target_modules,
        bias="none",
        inference_mode=False,
    )

    # Apply LoRA
    model = get_peft_model(model, lora_config)

    # Print trainable parameters
    model.print_trainable_parameters()

    return model


# =============================================================================
# TRAINING
# =============================================================================

def train(config: LoRANERConfig) -> dict:
    """Run LoRA fine-tuning."""
    start_time = time.time()

    print("=" * 70)
    print("LORA FINE-TUNING FOR LEGAL NER")
    print("=" * 70)

    # Paths
    base_dir = Path(__file__).resolve().parent.parent.parent
    model_path = base_dir / config.model_name_or_path
    dataset_dir = base_dir / config.dataset_dir
    output_dir = base_dir / config.output_dir

    # Load label mappings
    print("\nLoading label mappings...")
    label2id, id2label, num_labels = load_label_mappings(dataset_dir)
    print(f"  Labels: {num_labels}")

    # Load datasets
    print("\nLoading datasets...")
    train_dataset = load_dataset_split(dataset_dir / "train.json")
    eval_dataset = load_dataset_split(dataset_dir / "dev.json")
    print(f"  Train: {len(train_dataset)}")
    print(f"  Dev: {len(eval_dataset)}")

    # Load tokenizer
    print("\nLoading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(str(model_path))

    # Create model with LoRA
    print("\nCreating model with LoRA adapters...")
    model = create_lora_model(
        str(model_path),
        num_labels,
        label2id,
        id2label,
        config,
    )

    # Data collator
    data_collator = DataCollatorForTokenClassification(
        tokenizer=tokenizer,
        padding=True,
        max_length=config.max_length,
    )

    # Training arguments
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        learning_rate=config.learning_rate,
        num_train_epochs=config.num_train_epochs,
        per_device_train_batch_size=config.per_device_train_batch_size,
        per_device_eval_batch_size=config.per_device_eval_batch_size,
        warmup_ratio=config.warmup_ratio,
        weight_decay=config.weight_decay,
        eval_strategy=config.eval_strategy,
        save_strategy=config.save_strategy,
        load_best_model_at_end=config.load_best_model_at_end,
        metric_for_best_model=config.metric_for_best_model,
        greater_is_better=config.greater_is_better,
        fp16=config.fp16,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        logging_steps=config.logging_steps,
        report_to=config.report_to,
        save_total_limit=2,
        remove_unused_columns=False,
    )

    # Create trainer
    # Note: 'tokenizer' was renamed to 'processing_class' in transformers >= 4.46
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        processing_class=tokenizer,
        data_collator=data_collator,
        compute_metrics=lambda p: compute_metrics(p, id2label),
    )

    # Train
    print("\n" + "=" * 70)
    print("TRAINING")
    print("=" * 70)
    print(f"\nLoRA config:")
    print(f"  r={config.lora_r}, alpha={config.lora_alpha}, dropout={config.lora_dropout}")
    print(f"  target_modules={config.lora_target_modules}")
    print(f"\nTraining config:")
    print(f"  epochs={config.num_train_epochs}, lr={config.learning_rate}")
    print(f"  batch_size={config.per_device_train_batch_size} × {config.gradient_accumulation_steps} = {config.per_device_train_batch_size * config.gradient_accumulation_steps}")
    print(f"  fp16={config.fp16}")
    print()

    train_result = trainer.train()

    # Evaluate
    print("\n" + "=" * 70)
    print("EVALUATION")
    print("=" * 70)
    eval_result = trainer.evaluate()

    for key, value in eval_result.items():
        print(f"  {key}: {value:.4f}" if isinstance(value, float) else f"  {key}: {value}")

    # Save model
    print("\n" + "=" * 70)
    print("SAVING MODEL")
    print("=" * 70)

    # Save LoRA adapter
    adapter_dir = output_dir / "adapter"
    model.save_pretrained(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))

    # Save label mappings
    mappings = {
        "label2id": label2id,
        "id2label": {str(k): v for k, v in id2label.items()},
        "num_labels": num_labels,
    }
    with open(adapter_dir / "label_mappings.json", "w") as f:
        json.dump(mappings, f, indent=2)

    # Calculate adapter size
    adapter_size = sum(
        f.stat().st_size for f in adapter_dir.glob("**/*") if f.is_file()
    ) / (1024 * 1024)

    print(f"  Adapter saved to: {adapter_dir}")
    print(f"  Adapter size: {adapter_size:.1f} MB")

    # Save merged model (optional - for inference without PEFT)
    print("\nMerging adapter with base model...")
    merged_model = model.merge_and_unload()

    merged_dir = output_dir / "merged"
    merged_model.save_pretrained(str(merged_dir))
    tokenizer.save_pretrained(str(merged_dir))

    with open(merged_dir / "label_mappings.json", "w") as f:
        json.dump(mappings, f, indent=2)

    merged_size = sum(
        f.stat().st_size for f in merged_dir.glob("**/*") if f.is_file()
    ) / (1024 * 1024)

    print(f"  Merged model saved to: {merged_dir}")
    print(f"  Merged model size: {merged_size:.1f} MB")

    # Summary
    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print("TRAINING COMPLETE")
    print("=" * 70)
    print(f"\n  Total time: {elapsed / 60:.1f} min")
    print(f"  Best F1: {eval_result.get('eval_f1', 0):.4f}")
    print(f"  Adapter size: {adapter_size:.1f} MB")
    print(f"\n  Output: {output_dir}")

    # Save training report
    report = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "model": config.model_name_or_path,
            "lora_r": config.lora_r,
            "lora_alpha": config.lora_alpha,
            "lora_dropout": config.lora_dropout,
            "learning_rate": config.learning_rate,
            "epochs": config.num_train_epochs,
            "batch_size": config.per_device_train_batch_size * config.gradient_accumulation_steps,
        },
        "results": {
            "train_loss": train_result.training_loss,
            "eval_f1": eval_result.get("eval_f1", 0),
            "eval_precision": eval_result.get("eval_precision", 0),
            "eval_recall": eval_result.get("eval_recall", 0),
        },
        "sizes": {
            "adapter_mb": adapter_size,
            "merged_mb": merged_size,
        },
        "time_minutes": elapsed / 60,
    }

    report_path = output_dir / "training_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n  Report saved to: {report_path}")

    return report


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run LoRA fine-tuning with default config."""
    # Check CUDA
    if torch.cuda.is_available():
        print(f"CUDA available: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    else:
        print("WARNING: CUDA not available, training on CPU (will be slow)")

    config = LoRANERConfig()
    report = train(config)

    return 0


if __name__ == "__main__":
    exit(main())
