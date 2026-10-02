"""
K-mer frequency encoding for DNA sequence feature extraction.

Converts raw DNA sequences into normalized k-mer count vector representations
suitable for machine learning model training and feature analysis.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Dict, List, Set, Union

import pandas as pd


class KMerEncoder:
    """
    Extract overlapping k-mer substring frequencies from DNA sequences.

    Attributes:
        k: Length of contiguous k-mer substrings (default 3).
    """

    def __init__(self, k: int = 3) -> None:
        """
        Initialize a KMerEncoder instance.

        Args:
            k: Substring length for k-mer extraction. Must be >= 1.

        Raises:
            ValueError: If k is less than 1.
        """
        if k < 1:
            raise ValueError(f"k-mer length must be at least 1, got {k}.")
        self.k: int = k

    def generate_kmers(self, sequence: str) -> List[str]:
        """
        Generate all overlapping k-mers from a DNA sequence.

        Args:
            sequence: Input nucleotide sequence.

        Returns:
            List of overlapping k-mer substrings of length k.
        """
        if not sequence:
            return []

        seq = sequence.strip().upper()
        if len(seq) < self.k:
            return []

        return [seq[i : i + self.k] for i in range(len(seq) - self.k + 1)]

    def encode(self, sequence: str) -> Dict[str, float]:
        """
        Compute normalized k-mer frequencies for a single DNA sequence.

        Args:
            sequence: Input nucleotide sequence.

        Returns:
            Dictionary mapping observed k-mers to their relative frequency
            (counts divided by total k-mers). Returns empty dict if no k-mers.
        """
        kmers = self.generate_kmers(sequence)
        if not kmers:
            return {}

        total_kmers = len(kmers)
        counts = Counter(kmers)

        return {kmer: count / total_kmers for kmer, count in counts.items()}

    def encode_csv(
        self,
        input_csv: Union[str, Path],
        output_csv: Union[str, Path],
    ) -> None:
        """
        Transform a sequence CSV file into a k-mer feature matrix CSV.

        Reads input_csv, extracts k-mer frequencies for each sequence, creates
        feature columns for every observed k-mer, fills missing k-mers with 0.0,
        preserves metadata columns ('id', 'label', 'mutation_name', 'mutation_type'),
        and saves the resulting DataFrame to output_csv.

        Args:
            input_csv: Path to input CSV dataset containing a 'sequence' column.
            output_csv: Destination path for the feature dataset CSV.

        Raises:
            FileNotFoundError: If input_csv does not exist.
            ValueError: If 'sequence' column is missing from input_csv.
        """
        in_path = Path(input_csv)
        out_path = Path(output_csv)

        if not in_path.is_file():
            raise FileNotFoundError(
                f"Input CSV file not found: {in_path.resolve()}"
            )

        df = pd.read_csv(in_path)
        if "sequence" not in df.columns:
            raise ValueError(
                f"Input CSV must contain a 'sequence' column: {in_path}"
            )

        # Compute k-mer encodings for all rows
        kmer_encodings: List[Dict[str, float]] = [
            self.encode(str(seq)) for seq in df["sequence"]
        ]

        # Gather all unique k-mers observed across all sequences
        all_kmers: Set[str] = set()
        for encoding in kmer_encodings:
            all_kmers.update(encoding.keys())

        sorted_kmers: List[str] = sorted(all_kmers)

        # Build feature DataFrame for k-mers
        features_df = pd.DataFrame(kmer_encodings, columns=sorted_kmers).fillna(
            0.0
        )

        # Retain metadata columns while preserving label and mutation_name
        preserved_cols = [col for col in df.columns if col != "sequence"]
        metadata_df = df[preserved_cols]

        # Combine metadata columns and k-mer feature columns
        result_df = pd.concat([metadata_df, features_df], axis=1)

        # Ensure output directory exists and write to output_csv
        out_path.parent.mkdir(parents=True, exist_ok=True)
        result_df.to_csv(out_path, index=False)
