#!/usr/bin/env python3
"""
Augment GeneMindAI training dataset by generating biologically plausible DNA sequence variants.

Generates 500 neutral healthy variants and 500 disease-causing mutated variants
derived from the reference HBB gene sequence and MutationLibrary. Validates all
sequences with DNAValidator and saves expanded dataset to dataset/processed/expanded_dataset.csv.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Union

import numpy as np
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dna_processing.mutation.mutation_engine import DNAMutationEngine
from dna_processing.mutation.mutation_library import (
    DNAMutation,
    MutationLibrary,
)
from dna_processing.parsers.fasta_parser import FASTAParser
from dna_processing.validation.dna_validator import DNAValidator

DEFAULT_HEALTHY_FASTA: Path = (
    PROJECT_ROOT / "dataset" / "healthy" / "hbb_gene.fasta"
)
DEFAULT_OUTPUT_CSV: Path = (
    PROJECT_ROOT / "dataset" / "processed" / "expanded_dataset.csv"
)

VALID_BASES: List[str] = ["A", "T", "C", "G"]


class AugmentationError(Exception):
    """Raised when sequence augmentation or validation fails."""


def apply_random_substitutions(
    sequence: str,
    num_substitutions: int,
    forbidden_positions_1based: Set[int] | None = None,
) -> str:
    """
    Introduce random neutral nucleotide substitutions at allowed positions.

    Args:
        sequence: Input DNA sequence string.
        num_substitutions: Number of neutral edits to introduce (1..3).
        forbidden_positions_1based: Set of 1-based positions that must not be altered.

    Returns:
        Modified DNA sequence string.

    Raises:
        AugmentationError: If not enough allowed positions exist for substitution.
    """
    if forbidden_positions_1based is None:
        forbidden_positions_1based = set()

    seq_len = len(sequence)
    allowed_positions = [
        pos
        for pos in range(1, seq_len + 1)
        if pos not in forbidden_positions_1based
    ]

    if len(allowed_positions) < num_substitutions:
        raise AugmentationError(
            f"Not enough allowed positions ({len(allowed_positions)}) for "
            f"{num_substitutions} substitutions."
        )

    # Sample random 1-based positions without replacement
    chosen_positions = np.random.choice(
        allowed_positions, size=num_substitutions, replace=False
    )

    chars = list(sequence.upper())
    for pos in chosen_positions:
        idx = int(pos) - 1
        current_base = chars[idx]
        possible_bases = [b for b in VALID_BASES if b != current_base]
        new_base = str(np.random.choice(possible_bases))
        chars[idx] = new_base

    return "".join(chars)


def generate_healthy_variant(
    healthy_sequence: str,
    validator: DNAValidator,
) -> str:
    """
    Generate a healthy sequence variant with 1-3 neutral substitutions.

    Args:
        healthy_sequence: Reference healthy HBB sequence.
        validator: DNAValidator instance.

    Returns:
        Valid mutated healthy DNA sequence string.

    Raises:
        AugmentationError: If valid sequence cannot be generated within retries.
    """
    for _ in range(100):  # Retry loop to guarantee valid sequence
        num_edits = int(np.random.randint(1, 4))  # 1, 2, or 3
        variant = apply_random_substitutions(healthy_sequence, num_edits)
        is_valid, _ = validator.validate(variant)
        if is_valid:
            return variant

    raise AugmentationError(
        "Failed to generate valid healthy sequence variant."
    )


def generate_mutated_variant(
    healthy_fasta_path: Path,
    mutation: DNAMutation,
    validator: DNAValidator,
) -> str:
    """
    Apply a documented Beta Thalassemia mutation then add 1-3 neutral substitutions.

    Args:
        healthy_fasta_path: Path to reference healthy FASTA.
        mutation: Documented Beta Thalassemia DNAMutation object.
        validator: DNAValidator instance.

    Returns:
        Valid disease-causing mutated sequence string.

    Raises:
        AugmentationError: If mutation type is unsupported or generation fails.
    """
    engine = DNAMutationEngine()
    engine.load_sequence(healthy_fasta_path)

    m_type = mutation.mutation_type.lower()
    pos = mutation.position

    # Apply pathogenic mutation
    if m_type == "substitution":
        engine.substitute(pos, mutation.alternate_base)
        forbidden_positions = {pos}
    elif m_type == "insertion":
        engine.insert(pos, mutation.alternate_base)
        forbidden_positions = {pos, pos + 1}
    elif m_type == "deletion":
        engine.delete(pos)
        forbidden_positions = {max(1, pos - 1), pos}
    else:
        raise AugmentationError(
            f"Unsupported mutation type {mutation.mutation_type!r}"
        )

    mutated_seq = engine.get_sequence()

    # Add 1-3 neutral substitutions elsewhere, preserving the disease-causing edit
    for _ in range(100):
        num_edits = int(np.random.randint(1, 4))
        augmented_seq = apply_random_substitutions(
            mutated_seq,
            num_edits,
            forbidden_positions_1based=forbidden_positions,
        )
        is_valid, _ = validator.validate(augmented_seq)
        if is_valid:
            return augmented_seq

    raise AugmentationError(
        f"Failed to generate valid mutated variant for {mutation.name!r}."
    )


def augment_dataset(
    healthy_fasta_path: Path = DEFAULT_HEALTHY_FASTA,
    output_csv_path: Path = DEFAULT_OUTPUT_CSV,
    num_healthy: int = 500,
    num_mutated: int = 500,
    random_seed: int = 42,
) -> Tuple[int, int, int, Path]:
    """
    Execute full dataset augmentation pipeline and write expanded_dataset.csv.

    Args:
        healthy_fasta_path: Path to reference healthy FASTA.
        output_csv_path: Destination path for expanded dataset CSV.
        num_healthy: Number of healthy variants to generate (default 500).
        num_mutated: Number of mutated variants to generate (default 500).
        random_seed: Seed for random number generators (default 42).

    Returns:
        Tuple of (healthy_generated_count, mutated_generated_count, total_size, output_csv_path).

    Raises:
        AugmentationError: If input files are missing or augmentation fails.
    """
    np.random.seed(random_seed)

    if not healthy_fasta_path.is_file():
        raise AugmentationError(
            f"Healthy FASTA file not found: {healthy_fasta_path.resolve()}"
        )

    validator = DNAValidator()
    parser = FASTAParser()
    parser.load_fasta(healthy_fasta_path)
    healthy_sequence = parser.get_sequence()

    dataset_rows: List[Dict[str, Union[str, int]]] = []

    # 1. Generate 500 healthy variants
    for i in range(1, num_healthy + 1):
        seq = generate_healthy_variant(healthy_sequence, validator)
        dataset_rows.append(
            {
                "id": f"healthy_aug_{i:04d}",
                "sequence": seq,
                "label": 0,
                "mutation_name": "None",
                "mutation_type": "None",
            }
        )

    # 2. Generate 500 mutated variants
    mutations = MutationLibrary.get_beta_thalassemia_mutations()
    for i in range(1, num_mutated + 1):
        # Pick random documented mutation from library
        chosen_mutation = np.random.choice(mutations)
        seq = generate_mutated_variant(
            healthy_fasta_path, chosen_mutation, validator
        )
        dataset_rows.append(
            {
                "id": f"mutated_aug_{i:04d}",
                "sequence": seq,
                "label": 1,
                "mutation_name": chosen_mutation.name,
                "mutation_type": chosen_mutation.mutation_type,
            }
        )

    # 3. Save to expanded_dataset.csv
    df = pd.DataFrame(dataset_rows)
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv_path, index=False)

    healthy_count = num_healthy
    mutated_count = num_mutated
    total_size = len(df)

    return healthy_count, mutated_count, total_size, output_csv_path


def main() -> int:
    """
    Entry point for dataset augmentation script.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        h_cnt, m_cnt, total, out_path = augment_dataset()
        print(f"Healthy samples generated: {h_cnt}")
        print(f"Mutated samples generated: {m_cnt}")
        print(f"Total dataset size: {total}")
        print(f"Output path: {out_path.resolve()}")
        return 0
    except AugmentationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
