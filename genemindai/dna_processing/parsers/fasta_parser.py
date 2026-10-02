"""FASTA file parsing utilities built on Biopython."""

from pathlib import Path
from typing import Optional, Union

from Bio import SeqIO
from Bio.SeqRecord import SeqRecord


class FASTAParser:
    """Load and query a single FASTA record from disk."""

    def __init__(self) -> None:
        """Initialize an empty parser with no loaded record."""
        self._record: Optional[SeqRecord] = None

    def load_fasta(self, file_path: Union[str, Path]) -> None:
        """
        Load the first sequence record from a FASTA file.

        Args:
            file_path: Path to a FASTA file containing at least one record.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file contains no parseable FASTA records.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"FASTA file not found: {path}")

        record = next(SeqIO.parse(path, "fasta"), None)
        if record is None:
            raise ValueError(f"No FASTA records found in: {path}")

        self._record = record

    def get_sequence(self) -> str:
        """
        Return the loaded sequence as an uppercase string.

        Returns:
            The nucleotide sequence.

        Raises:
            RuntimeError: If no FASTA record has been loaded.
        """
        self._ensure_loaded()
        return str(self._record.seq).upper()

    def get_header(self) -> str:
        """
        Return the FASTA header (description line without leading '>' ).

        Returns:
            The record identifier / description from the FASTA header.

        Raises:
            RuntimeError: If no FASTA record has been loaded.
        """
        self._ensure_loaded()
        return self._record.description

    def get_length(self) -> int:
        """
        Return the length of the loaded sequence in bases.

        Returns:
            Number of residues in the sequence.

        Raises:
            RuntimeError: If no FASTA record has been loaded.
        """
        self._ensure_loaded()
        return len(self._record.seq)

    def _ensure_loaded(self) -> None:
        if self._record is None:
            raise RuntimeError(
                "No FASTA record loaded. Call load_fasta(file_path) first."
            )
