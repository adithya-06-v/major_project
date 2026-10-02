#!/usr/bin/env python3
"""
Generate a labeled DNA sequence dataset for Beta Thalassemia classification.

Loads the reference healthy HBB gene sequence, applies documented Beta Thalassemia
mutations from MutationLibrary using DNAMutationEngine, validates all sequences
using DNAValidator, persists mutated FASTA files into dataset/mutated/, and
saves a structured CSV dataset into dataset/processed/dataset.csv.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Union

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dna_processing.mutation.mutation_engine import DNAMutationEngine
from dna_processing.mutation.mutation_library import DNAMutation, MutationLibrary
from dna_processing.parsers.fasta_parser import FASTAParser
from dna_processing.validation.dna_validator import DNAValidator

DEFAULT_HEALTHY_FASTA: Path = (
    PROJECT_ROOT / "dataset" / "healthy" / "hbb_gene.fasta"
)
DEFAULT_MUTATED_DIR: Path = PROJECT_ROOT / "dataset" / "mutated"
DEFAULT_CSV_PATH: Path = PROJECT_ROOT / "dataset" / "processed" / "dataset.csv"


class DatasetGenerationError(Exception):
    """Raised when dataset generation or sequence validation fails."""


def sanitize_filename(name: str) -> str:
    """
    Convert a mutation name into a filesystem-safe filename string.

    Args:
        name: Raw mutation display name or nomenclature.

    Returns:
        Sanitized string suitable for filenames without extension.
    """
    clean_name = re.sub(r"[^\w\-]+", "_", name).strip("_").lower()
    return clean_name


def validate_sequence_or_raise(
    validator: DNAValidator,
    sequence: str,
    sample_id: str,
) -> None:
    """
    Validate a DNA sequence and raise DatasetGenerationError if invalid.

    Args:
        validator: Instance of DNAValidator.
        sequence: DNA sequence string.
        sample_id: Identifier for logging context.

    Raises:
        DatasetGenerationError: If sequence fails validation checks.
    """
    is_valid, errors = validator.validate(sequence)
    if not is_valid:
        raise DatasetGenerationError(
            f"Validation failed for sample {sample_id!r}: {', '.join(errors)}"
        )


def apply_mutation(
    healthy_fasta_path: Path,
    mutation: DNAMutation,
) -> Tuple[DNAMutationEngine, str]:
    """
    Load healthy sequence in a fresh DNAMutationEngine and apply a mutation.

    Args:
        healthy_fasta_path: Path to reference healthy FASTA.
        mutation: DNAMutation object describing the edit.

    Returns:
        Tuple of (configured engine, mutated sequence string).

    Raises:
        DatasetGenerationError: If mutation type is invalid or mutation fails.
    """
    engine = DNAMutationEngine()
    try:
        engine.load_sequence(healthy_fasta_path)
    except Exception as exc:
        raise DatasetGenerationError(
            f"Failed to load healthy FASTA from {healthy_fasta_path}: {exc}"
        ) from exc

    m_type = mutation.mutation_type.lower()
    try:
        if m_type == "substitution":
            if mutation.alternate_base is None:
                raise DatasetGenerationError(
                    f"Substitution mutation {mutation.name!r} requires alternate_base."
                )
            engine.substitute(mutation.position, mutation.alternate_base)
        elif m_type == "insertion":
            if mutation.alternate_base is None:
                raise DatasetGenerationError(
                    f"Insertion mutation {mutation.name!r} requires alternate_base."
                )
            engine.insert(mutation.position, mutation.alternate_base)
        elif m_type == "deletion":
            engine.delete(mutation.position)
        else:
            raise DatasetGenerationError(
                f"Unsupported mutation type {mutation.mutation_type!r} for {mutation.name!r}."
            )
    except Exception as exc:
        raise DatasetGenerationError(
            f"Failed to apply mutation {mutation.name!r} at position {mutation.position}: {exc}"
        ) from exc

    return engine, engine.get_sequence()


def generate_dataset(
    healthy_fasta_path: Path = DEFAULT_HEALTHY_FASTA,
    mutated_dir: Path = DEFAULT_MUTATED_DIR,
    csv_path: Path = DEFAULT_CSV_PATH,
) -> Tuple[int, int, Path]:
    """
    Generate mutated FASTA files and a master CSV dataset.

    Args:
        healthy_fasta_path: Path to input healthy FASTA file.
        mutated_dir: Directory where mutated FASTA files will be saved.
        csv_path: Destination path for the dataset CSV file.

    Returns:
        Tuple of (healthy_sample_count, mutated_sample_count, csv_path).

    Raises:
        DatasetGenerationError: If healthy file missing or generation fails.
    """
    if not healthy_fasta_path.is_file():
        raise DatasetGenerationError(
            f"Healthy FASTA file not found: {healthy_fasta_path.resolve()}"
        )

    # Ensure output directories exist
    mutated_dir.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    validator = DNAValidator()

    # 1. Load and validate healthy sequence
    parser = FASTAParser()
    try:
        parser.load_fasta(healthy_fasta_path)
        healthy_sequence = parser.get_sequence()
    except Exception as exc:
        raise DatasetGenerationError(
            f"Failed to parse healthy FASTA: {exc}"
        ) from exc

    validate_sequence_or_raise(validator, healthy_sequence, "healthy_hbb")

    dataset_rows: List[Dict[str, Union[str, int]]] = [
        {
            "id": "healthy_hbb",
            "sequence": healthy_sequence,
            "label": 0,
            "mutation_name": "None",
            "mutation_type": "None",
        }
    ]

    # 2. Load mutations from library
    mutations = MutationLibrary.get_beta_thalassemia_mutations()

    # 3. Process each mutation
    for idx, mutation in enumerate(mutations, start=1):
        sample_id = f"mutated_{idx:03d}"
        engine, mutated_sequence = apply_mutation(healthy_fasta_path, mutation)
        validate_sequence_or_raise(validator, mutated_sequence, sample_id)

        # Save mutated FASTA file
        file_stub = sanitize_filename(mutation.name)
        fasta_filename = f"{file_stub}.fasta"
        fasta_output_path = mutated_dir / fasta_filename
        try:
            engine.save(fasta_output_path)
        except Exception as exc:
            raise DatasetGenerationError(
                f"Failed to save FASTA for mutation {mutation.name!r}: {exc}"
            ) from exc

        dataset_rows.append(
            {
                "id": sample_id,
                "sequence": mutated_sequence,
                "label": 1,
                "mutation_name": mutation.name,
                "mutation_type": mutation.mutation_type,
            }
        )

    # 4. Save CSV dataset
    fieldnames = ["id", "sequence", "label", "mutation_name", "mutation_type"]
    try:
        with open(csv_path, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(dataset_rows)
    except OSError as exc:
        raise DatasetGenerationError(
            f"Failed to write CSV dataset to {csv_path}: {exc}"
        ) from exc

    healthy_count = 1
    mutated_count = len(mutations)
    return healthy_count, mutated_count, csv_path


def main() -> int:
    """
    Entry point for dataset generation script.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        healthy_count, mutated_count, csv_path = generate_dataset()
        print(f"Healthy samples: {healthy_count}")
        print(f"Mutated samples: {mutated_count}")
        print(f"CSV path: {csv_path.resolve()}")
        return 0
    except DatasetGenerationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
