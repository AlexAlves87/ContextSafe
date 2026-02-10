#!/usr/bin/env python3
"""
Download Legal-XLM-RoBERTa models from HuggingFace.

Downloads the base model for fine-tuning on NER-PII tasks.
Also downloads tokenizer and config files.

Usage:
    python scripts/download_legal_xlm_roberta.py
"""

import os
import time
from pathlib import Path

# Ensure transformers is available
try:
    from transformers import AutoModel, AutoTokenizer, AutoConfig
    from huggingface_hub import snapshot_download
except ImportError:
    print("ERROR: transformers not installed")
    print("Run: pip install transformers huggingface_hub")
    exit(1)


# Model configurations
MODELS = {
    "base": {
        "name": "joelniklaus/legal-xlm-roberta-base",
        "description": "Legal XLM-RoBERTa Base (110M params, ~440MB)",
        "recommended": True,
    },
    "large": {
        "name": "joelniklaus/legal-xlm-roberta-large",
        "description": "Legal XLM-RoBERTa Large (355M params, ~1.4GB)",
        "recommended": False,
    },
}


def download_model(model_key: str, output_dir: Path) -> bool:
    """Download a model from HuggingFace."""
    if model_key not in MODELS:
        print(f"ERROR: Unknown model key: {model_key}")
        return False

    model_info = MODELS[model_key]
    model_name = model_info["name"]
    local_dir = output_dir / f"legal-xlm-roberta-{model_key}"

    print(f"\n{'='*60}")
    print(f"Downloading: {model_info['description']}")
    print(f"From: {model_name}")
    print(f"To: {local_dir}")
    print(f"{'='*60}")

    start_time = time.time()

    try:
        # Download using snapshot_download for complete model
        snapshot_download(
            repo_id=model_name,
            local_dir=str(local_dir),
            local_dir_use_symlinks=False,
            resume_download=True,
        )

        # Verify download
        print("\nVerifying download...")
        config = AutoConfig.from_pretrained(str(local_dir))
        tokenizer = AutoTokenizer.from_pretrained(str(local_dir))
        model = AutoModel.from_pretrained(str(local_dir))

        elapsed = time.time() - start_time

        print(f"\n✅ Download successful!")
        print(f"   Model type: {config.model_type}")
        print(f"   Hidden size: {config.hidden_size}")
        print(f"   Num layers: {config.num_hidden_layers}")
        print(f"   Vocab size: {tokenizer.vocab_size}")
        print(f"   Parameters: {model.num_parameters():,}")
        print(f"   Time: {elapsed:.1f}s")

        return True

    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        return False


def main():
    """Download Legal-XLM-RoBERTa models."""
    print("=" * 60)
    print("LEGAL-XLM-ROBERTA MODEL DOWNLOADER")
    print("=" * 60)

    # Setup output directory
    BASE_DIR = Path(__file__).resolve().parent.parent
    OUTPUT_DIR = BASE_DIR / "models" / "pretrained"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\nOutput directory: {OUTPUT_DIR}")
    print(f"\nAvailable models:")
    for key, info in MODELS.items():
        rec = " (RECOMMENDED)" if info["recommended"] else ""
        print(f"  - {key}: {info['description']}{rec}")

    # Download base model (recommended)
    print("\n" + "=" * 60)
    print("Downloading BASE model (recommended for fine-tuning)")
    print("=" * 60)

    success = download_model("base", OUTPUT_DIR)

    if success:
        print("\n" + "=" * 60)
        print("DOWNLOAD COMPLETE")
        print("=" * 60)
        print(f"\nModel saved to: {OUTPUT_DIR / 'legal-xlm-roberta-base'}")
        print("\nNext steps:")
        print("  1. Prepare legal corpus for DAPT")
        print("  2. Run DAPT: scripts/train/run_dapt.py")
        print("  3. Fine-tune NER: scripts/train/train_ner.py")
    else:
        print("\n❌ Download failed. Check your internet connection.")
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
