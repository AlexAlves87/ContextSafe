#!/usr/bin/env python3
"""
Inject OCR noise into NER dataset for robustness training.

Based on best practices from PMC12214779:
"To better simulate real-world document anomalies, data preprocessing
adds minor random noise like punctuation removal and text normalization."

Noise types:
- Character substitution (l↔I, 0↔O, 1↔l)
- Space collapse/expansion in numbers
- Accent removal (á→a, é→e, etc.)
- Random punctuation removal
- D.N.I. style variations

Usage:
    python scripts/preprocess/inject_ocr_noise.py

Output:
    data/processed/ner_dataset_v3/
"""

import json
import random
import re
import time
import unicodedata
from pathlib import Path
from typing import Optional

from datasets import Dataset, DatasetDict
from transformers import AutoTokenizer


# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"
INPUT_FILE = DATA_DIR / "synthetic_ner_dataset.json"
OUTPUT_DIR = DATA_DIR / "ner_dataset_v3"

# Noise parameters (based on PMC12214779 recommendation: ~30%)
NOISE_PROBABILITY = 0.30  # 30% of samples get noise
NOISE_INTENSITY = 0.15    # Within noisy samples, 15% of characters affected

# Model for tokenization (use local checkpoint that has all tokenizer files)
MODEL_NAME = str(BASE_DIR / "models" / "checkpoints" / "roberta-base-bne-capitel-ner")

# Random seed for reproducibility
RANDOM_SEED = 42


# =============================================================================
# NOISE FUNCTIONS
# =============================================================================

# Character substitution maps (OCR confusions)
OCR_SUBSTITUTIONS = {
    # Lowercase L and uppercase I
    'l': ['I', '1', '|'],
    'I': ['l', '1', '|'],
    '1': ['l', 'I', '|'],
    # Zero and O
    '0': ['O', 'o'],
    'O': ['0'],
    'o': ['0'],
    # Similar shapes
    '5': ['S', 's'],
    'S': ['5'],
    '8': ['B'],
    'B': ['8'],
    # Commonly confused
    'rn': ['m'],
    'm': ['rn'],
    'cl': ['d'],
    'vv': ['w'],
}

# Accent removal map
ACCENT_MAP = {
    'á': 'a', 'à': 'a', 'ä': 'a', 'â': 'a',
    'é': 'e', 'è': 'e', 'ë': 'e', 'ê': 'e',
    'í': 'i', 'ì': 'i', 'ï': 'i', 'î': 'i',
    'ó': 'o', 'ò': 'o', 'ö': 'o', 'ô': 'o',
    'ú': 'u', 'ù': 'u', 'ü': 'u', 'û': 'u',
    'ñ': 'n',
    'Á': 'A', 'À': 'A', 'Ä': 'A', 'Â': 'A',
    'É': 'E', 'È': 'E', 'Ë': 'E', 'Ê': 'E',
    'Í': 'I', 'Ì': 'I', 'Ï': 'I', 'Î': 'I',
    'Ó': 'O', 'Ò': 'O', 'Ö': 'O', 'Ô': 'O',
    'Ú': 'U', 'Ù': 'U', 'Ü': 'U', 'Û': 'U',
    'Ñ': 'N',
}

# Abbreviation variations for Spanish documents
ABBREVIATION_VARIATIONS = {
    'DNI': ['D.N.I.', 'D.N.I', 'D N I', 'DNl', 'DnI'],
    'NIF': ['N.I.F.', 'N.I.F', 'N I F', 'NlF'],
    'NIE': ['N.I.E.', 'N.I.E', 'N I E', 'NlE'],
    'CIF': ['C.I.F.', 'C.I.F', 'C I F'],
    'IBAN': ['I.B.A.N.', 'lBAN', 'IBAN'],
}


class OCRNoiseInjector:
    """Injects realistic OCR noise into text while tracking span changes."""

    def __init__(self,
                 noise_probability: float = NOISE_PROBABILITY,
                 noise_intensity: float = NOISE_INTENSITY,
                 seed: int = RANDOM_SEED):
        self.noise_probability = noise_probability
        self.noise_intensity = noise_intensity
        self.rng = random.Random(seed)

    def should_apply_noise(self) -> bool:
        """Determine if noise should be applied to this sample."""
        return self.rng.random() < self.noise_probability

    def inject_noise(self, text: str, entities: list[dict]) -> tuple[str, list[dict]]:
        """
        Inject OCR noise into text and adjust entity spans.

        Args:
            text: Original text
            entities: List of {"text": ..., "type"/"label": ..., "start": ..., "end": ...}

        Returns:
            Tuple of (noisy_text, adjusted_entities)
        """
        if not self.should_apply_noise():
            return text, entities

        # Normalize entity format (support both "type" and "label" keys)
        entities = [
            {
                'text': e.get('text', ''),
                'type': e.get('type', e.get('label', '')),
                'start': e.get('start', 0),
                'end': e.get('end', 0),
            }
            for e in entities
        ]

        # Choose noise types to apply (1-3 types per sample)
        noise_types = self.rng.sample([
            self._apply_char_substitution,
            self._apply_accent_removal,
            self._apply_space_noise,
            self._apply_punctuation_noise,
            self._apply_abbreviation_variation,
        ], k=self.rng.randint(1, 3))

        # Track character-level mapping for span adjustment
        # Original text -> list of (new_char, original_index)
        char_map = list(range(len(text)))
        noisy_chars = list(text)

        # Apply each noise type
        for noise_func in noise_types:
            noisy_chars, char_map = noise_func(noisy_chars, char_map)

        noisy_text = ''.join(noisy_chars)

        # Adjust entity spans
        adjusted_entities = self._adjust_entities(entities, text, noisy_text, char_map)

        return noisy_text, adjusted_entities

    def _apply_char_substitution(self, chars: list[str], char_map: list[int]) -> tuple[list[str], list[int]]:
        """Apply OCR character substitutions (l↔I, 0↔O, etc.)."""
        result = []
        new_map = []

        i = 0
        while i < len(chars):
            char = chars[i]
            orig_idx = char_map[i]

            # Check for multi-char substitutions first
            if i < len(chars) - 1:
                two_char = char + chars[i + 1]
                if two_char in OCR_SUBSTITUTIONS and self.rng.random() < self.noise_intensity:
                    replacement = self.rng.choice(OCR_SUBSTITUTIONS[two_char])
                    result.append(replacement)
                    new_map.append(orig_idx)
                    i += 2
                    continue

            # Single char substitution
            if char in OCR_SUBSTITUTIONS and self.rng.random() < self.noise_intensity:
                replacement = self.rng.choice(OCR_SUBSTITUTIONS[char])
                result.append(replacement)
                new_map.append(orig_idx)
            else:
                result.append(char)
                new_map.append(orig_idx)

            i += 1

        return result, new_map

    def _apply_accent_removal(self, chars: list[str], char_map: list[int]) -> tuple[list[str], list[int]]:
        """Remove accents (common OCR issue with Spanish)."""
        result = []
        new_map = []

        for i, char in enumerate(chars):
            if char in ACCENT_MAP and self.rng.random() < self.noise_intensity * 2:  # More common
                result.append(ACCENT_MAP[char])
            else:
                result.append(char)
            new_map.append(char_map[i])

        return result, new_map

    def _apply_space_noise(self, chars: list[str], char_map: list[int]) -> tuple[list[str], list[int]]:
        """Add or remove spaces (OCR spacing issues)."""
        result = []
        new_map = []

        i = 0
        while i < len(chars):
            char = chars[i]
            orig_idx = char_map[i]

            if char == ' ':
                # Sometimes remove space between digits
                if (i > 0 and i < len(chars) - 1 and
                    chars[i-1].isdigit() and chars[i+1].isdigit() and
                    self.rng.random() < self.noise_intensity):
                    # Skip space (collapse)
                    i += 1
                    continue
                # Sometimes double space
                elif self.rng.random() < self.noise_intensity * 0.5:
                    result.append(' ')
                    result.append(' ')
                    new_map.append(orig_idx)
                    new_map.append(orig_idx)
                    i += 1
                    continue

            # Sometimes add space between digits
            if (char.isdigit() and i < len(chars) - 1 and chars[i+1].isdigit() and
                self.rng.random() < self.noise_intensity * 0.3):
                result.append(char)
                result.append(' ')
                new_map.append(orig_idx)
                new_map.append(orig_idx)
                i += 1
                continue

            result.append(char)
            new_map.append(orig_idx)
            i += 1

        return result, new_map

    def _apply_punctuation_noise(self, chars: list[str], char_map: list[int]) -> tuple[list[str], list[int]]:
        """Remove or alter punctuation (OCR often misses periods, commas)."""
        result = []
        new_map = []

        for i, char in enumerate(chars):
            # Skip punctuation sometimes
            if char in '.,;:' and self.rng.random() < self.noise_intensity:
                continue  # Remove punctuation

            result.append(char)
            new_map.append(char_map[i])

        return result, new_map

    def _apply_abbreviation_variation(self, chars: list[str], char_map: list[int]) -> tuple[list[str], list[int]]:
        """Replace abbreviations with variations (DNI → D.N.I., etc.)."""
        text = ''.join(chars)

        for abbrev, variations in ABBREVIATION_VARIATIONS.items():
            if abbrev in text and self.rng.random() < self.noise_intensity * 2:
                variation = self.rng.choice(variations)
                # Find position and replace
                idx = text.find(abbrev)
                if idx >= 0:
                    # Simple replacement (span tracking is approximate here)
                    text = text[:idx] + variation + text[idx + len(abbrev):]

        # Rebuild char map (approximate - may shift spans slightly)
        return list(text), list(range(len(text)))

    def _adjust_entities(self, entities: list[dict], original: str, noisy: str,
                        char_map: list[int]) -> list[dict]:
        """
        Adjust entity spans after noise injection.

        Uses fuzzy matching to relocate entities in noisy text.
        """
        adjusted = []

        for ent in entities:
            orig_text = ent['text']
            orig_start = ent['start']
            orig_end = ent['end']

            # Try to find entity text in noisy version
            # First, try exact match
            new_start = noisy.find(orig_text)

            if new_start >= 0:
                adjusted.append({
                    'text': orig_text,
                    'type': ent['type'],
                    'start': new_start,
                    'end': new_start + len(orig_text),
                })
                continue

            # Try normalized match (without accents)
            norm_entity = self._normalize(orig_text)
            norm_noisy = self._normalize(noisy)
            new_start = norm_noisy.find(norm_entity)

            if new_start >= 0:
                # Find actual position in noisy text
                # This is approximate but usually close enough
                new_end = new_start + len(orig_text)
                actual_text = noisy[new_start:new_end]

                adjusted.append({
                    'text': actual_text,
                    'type': ent['type'],
                    'start': new_start,
                    'end': new_end,
                })
                continue

            # Fallback: use char_map to estimate new position
            # Find new start position
            new_start = None
            new_end = None

            for i, orig_idx in enumerate(char_map):
                if orig_idx == orig_start and new_start is None:
                    new_start = i
                if orig_idx == orig_end - 1:
                    new_end = i + 1

            if new_start is not None and new_end is not None:
                actual_text = noisy[new_start:new_end]
                adjusted.append({
                    'text': actual_text,
                    'type': ent['type'],
                    'start': new_start,
                    'end': new_end,
                })
            else:
                # Last resort: skip this entity (rare)
                print(f"  Warning: Could not relocate entity '{orig_text}' ({ent['type']})")

        return adjusted

    def _normalize(self, text: str) -> str:
        """Normalize text for fuzzy matching."""
        # Remove accents
        text = ''.join(ACCENT_MAP.get(c, c) for c in text)
        # Collapse spaces
        text = re.sub(r'\s+', ' ', text)
        # Lowercase
        text = text.lower()
        return text


# =============================================================================
# DATASET GENERATION
# =============================================================================

# Label mappings (same as v2)
LABEL2ID = {
    "O": 0,
    "B-PERSON": 1, "I-PERSON": 2,
    "B-LOCATION": 3, "I-LOCATION": 4,
    "B-ORGANIZATION": 5, "I-ORGANIZATION": 6,
    "B-DATE": 7, "I-DATE": 8,
    "B-DNI_NIE": 9, "I-DNI_NIE": 10,
    "B-IBAN": 11, "I-IBAN": 12,
    "B-NSS": 13, "I-NSS": 14,
    "B-PHONE": 15, "I-PHONE": 16,
    "B-ADDRESS": 17, "I-ADDRESS": 18,
    "B-POSTAL_CODE": 19, "I-POSTAL_CODE": 20,
    "B-LICENSE_PLATE": 21, "I-LICENSE_PLATE": 22,
    "B-CADASTRAL_REF": 23, "I-CADASTRAL_REF": 24,
    "B-ECLI": 25, "I-ECLI": 26,
    "B-PROFESSIONAL_ID": 27, "I-PROFESSIONAL_ID": 28,
}

ID2LABEL = {v: k for k, v in LABEL2ID.items()}


class DatasetGenerator:
    """Generate HuggingFace dataset with noise injection."""

    def __init__(self, model_name: str = MODEL_NAME):
        print(f"Loading tokenizer: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        self.noise_injector = OCRNoiseInjector()

    def load_sentences(self, path: Path) -> list[dict]:
        """Load synthetic sentences from JSON."""
        print(f"Loading sentences from {path}")
        with open(path) as f:
            data = json.load(f)

        sentences = data.get('sentences', data)
        print(f"  Loaded {len(sentences)} sentences")
        return sentences

    def process_sentence(self, sentence: dict, apply_noise: bool = True) -> Optional[dict]:
        """
        Process a single sentence: optionally inject noise, tokenize, align labels.

        Args:
            sentence: {"text": ..., "entities": [...]}
            apply_noise: Whether to potentially inject OCR noise

        Returns:
            {"input_ids": [...], "attention_mask": [...], "labels": [...]}
        """
        text = sentence['text']
        entities = sentence.get('entities', [])

        # Inject noise (30% probability)
        if apply_noise:
            text, entities = self.noise_injector.inject_noise(text, entities)

        # Tokenize
        encoding = self.tokenizer(
            text,
            max_length=384,
            padding='max_length',
            truncation=True,
            return_offsets_mapping=True,
        )

        # Build character-level labels
        char_labels = ['O'] * len(text)
        for ent in entities:
            start = ent['start']
            end = ent['end']
            ent_type = ent.get('type', ent.get('label', ''))

            if start >= len(text) or end > len(text):
                continue

            # BIO tagging
            char_labels[start] = f'B-{ent_type}'
            for i in range(start + 1, end):
                if i < len(text):
                    char_labels[i] = f'I-{ent_type}'

        # Align labels to tokens
        offsets = encoding['offset_mapping']
        word_ids = encoding.word_ids()
        labels = []
        previous_word_id = None

        for i, (word_id, (start, end)) in enumerate(zip(word_ids, offsets)):
            if word_id is None:
                # Special token
                labels.append(-100)
            elif start == end:
                # Empty span
                labels.append(-100)
            elif word_id != previous_word_id:
                # First token of word - get label from first character
                if start < len(char_labels):
                    label = char_labels[start]
                    labels.append(LABEL2ID.get(label, 0))
                else:
                    labels.append(0)
            else:
                # Continuation of word
                labels.append(-100)

            previous_word_id = word_id

        # Remove offset_mapping (not needed for training)
        del encoding['offset_mapping']

        return {
            'input_ids': encoding['input_ids'],
            'attention_mask': encoding['attention_mask'],
            'labels': labels,
        }

    def generate_dataset(self, sentences: list[dict]) -> DatasetDict:
        """Generate train/validation/test splits with noise injection."""

        # Shuffle sentences
        rng = random.Random(RANDOM_SEED)
        shuffled = sentences.copy()
        rng.shuffle(shuffled)

        # Split: 80% train, 10% val, 10% test
        n = len(shuffled)
        train_end = int(n * 0.8)
        val_end = int(n * 0.9)

        splits = {
            'train': shuffled[:train_end],
            'validation': shuffled[train_end:val_end],
            'test': shuffled[val_end:],
        }

        datasets = {}
        noise_stats = {'train': {'total': 0, 'noisy': 0}}

        for split_name, split_sentences in splits.items():
            print(f"\nProcessing {split_name} ({len(split_sentences)} sentences)...")

            samples = []
            # Only apply noise to training set
            apply_noise = (split_name == 'train')

            # Reset noise injector for consistent noise application
            if apply_noise:
                self.noise_injector = OCRNoiseInjector(seed=RANDOM_SEED + hash(split_name))

            for sentence in split_sentences:
                # Track noise stats for training
                if apply_noise:
                    noise_stats['train']['total'] += 1
                    # Check if noise will be applied (peek at RNG)
                    self.noise_injector.rng.random()  # Advance RNG state check

                sample = self.process_sentence(sentence, apply_noise=apply_noise)
                if sample:
                    samples.append(sample)

            # Create HuggingFace Dataset
            datasets[split_name] = Dataset.from_dict({
                'input_ids': [s['input_ids'] for s in samples],
                'attention_mask': [s['attention_mask'] for s in samples],
                'labels': [s['labels'] for s in samples],
            })

            print(f"  Created {len(samples)} samples")

        return DatasetDict(datasets)


# =============================================================================
# MAIN
# =============================================================================

def main():
    start_time = time.time()

    print("=" * 60)
    print("OCR NOISE INJECTION FOR NER DATASET")
    print("=" * 60)
    print(f"Noise probability: {NOISE_PROBABILITY * 100}%")
    print(f"Noise intensity: {NOISE_INTENSITY * 100}%")

    # Initialize generator
    generator = DatasetGenerator()

    # Load sentences
    sentences = generator.load_sentences(INPUT_FILE)

    # Generate dataset with noise
    dataset = generator.generate_dataset(sentences)

    # Save dataset
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset.save_to_disk(str(OUTPUT_DIR))

    # Save label mappings
    with open(OUTPUT_DIR / 'label_mappings.json', 'w') as f:
        json.dump({
            'label2id': LABEL2ID,
            'id2label': {str(k): v for k, v in ID2LABEL.items()},
        }, f, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("DATASET GENERATED")
    print("=" * 60)
    print(f"Output: {OUTPUT_DIR}")
    print(f"Train: {len(dataset['train'])} samples (~{NOISE_PROBABILITY*100}% with noise)")
    print(f"Validation: {len(dataset['validation'])} samples (clean)")
    print(f"Test: {len(dataset['test'])} samples (clean)")
    print(f"Labels: {len(LABEL2ID)}")

    # Show noise examples
    print("\n--- Noise Examples ---")
    injector = OCRNoiseInjector(seed=12345)

    examples = [
        {
            "text": "Don José García López con DNI 12345678Z",
            "entities": [
                {"text": "José García López", "type": "PERSON", "start": 4, "end": 21},
                {"text": "12345678Z", "type": "DNI_NIE", "start": 30, "end": 39},
            ]
        },
        {
            "text": "IBAN ES91 2100 0418 4502 0005 1332",
            "entities": [
                {"text": "ES91 2100 0418 4502 0005 1332", "type": "IBAN", "start": 5, "end": 34},
            ]
        },
    ]

    for ex in examples:
        # Force noise application for demo
        injector.noise_probability = 1.0
        noisy_text, noisy_ents = injector.inject_noise(ex['text'], ex['entities'])
        print(f"\nOriginal: {ex['text']}")
        print(f"Noisy:    {noisy_text}")

    # Report execution time
    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"Tiempo de ejecución: {elapsed:.2f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
