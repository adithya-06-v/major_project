"""Apply single-nucleotide edits to DNA sequences loaded from FASTA."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Set, Union

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

VALID_MUTATION_BASES: Set[str] = {"A", "T", "C", "G"}


class MutationEngineError(Exception):
    """Base exception for DNA mutation engine failures."""


class SequenceNotLoadedError(MutationEngineError):
    """Raised when an operation requires a loaded sequence."""


class InvalidPositionError(MutationEngineError):
    """Raised when a position is outside the allowed range."""


class InvalidBaseError(MutationEngineError):
    """Raised when a nucleotide is not a valid {A, T, C, G} base."""


class DNAMutationEngine:
    """
    Load a DNA FASTA sequence and apply single-base substitutions, insertions,
    or deletions in memory.

    Positions are **1-based** and refer to the current sequence state (after
    any prior edits in the same session).
    """

    def __init__(self) -> None:
        """Initialize an engine with no loaded sequence."""
        self._record: Optional[SeqRecord] = None
        self._sequence: Optional[str] = None

    def load_sequence(self, fasta_path: Union[str, Path]) -> None:
        """
        Load the first FASTA record and store its sequence internally.

        Args:
            fasta_path: Path to a FASTA file with at least one record.

        Raises:
            MutationEngineError: If the file is missing or empty.
        """
        path = Path(fasta_path)
        if not path.is_file():
            raise MutationEngineError(
                f"FASTA file not found: {path.resolve()}"
            )

        try:
            record = SeqIO.read(path, "fasta")
        except OSError as exc:
            raise MutationEngineError(
                f"Could not read FASTA file {path}: {exc}"
            ) from exc
        except ValueError as exc:
            raise MutationEngineError(
                f"Could not parse FASTA file {path}: {exc}"
            ) from exc

        if len(record.seq) == 0:
            raise MutationEngineError(
                f"FASTA record in {path} has an empty sequence."
            )

        self._record = record
        self._sequence = str(record.seq).upper()

    def substitute(self, position: int, new_base: str) -> None:
        """
        Replace the nucleotide at ``position`` with ``new_base``.

        Args:
            position: 1-based index into the current sequence.
            new_base: Single allowed base (A, T, C, or G).

        Raises:
            SequenceNotLoadedError: If no sequence has been loaded.
            InvalidPositionError: If ``position`` is out of range.
            InvalidBaseError: If ``new_base`` is not A, T, C, or G.
        """
        sequence = self._require_sequence()
        self._validate_position(position, len(sequence), "substitute")
        base = self._normalize_base(new_base, "substitute")

        index = position - 1
        chars = list(sequence)
        chars[index] = base
        self._sequence = "".join(chars)

    def insert(self, position: int, base: str) -> None:
        """
        Insert one nucleotide before the base currently at ``position``.

        If ``position`` equals ``len(sequence) + 1``, the base is appended.

        Args:
            position: 1-based index; valid range ``1 .. len(sequence) + 1``.
            base: Single allowed base (A, T, C, or G).

        Raises:
            SequenceNotLoadedError: If no sequence has been loaded.
            InvalidPositionError: If ``position`` is out of range.
            InvalidBaseError: If ``base`` is not A, T, C, or G.
        """
        sequence = self._require_sequence()
        length = len(sequence)
        if position < 1 or position > length + 1:
            raise InvalidPositionError(
                f"Insert position {position} is out of range. "
                f"Valid range: 1 to {length + 1} (inclusive)."
            )

        nucleotide = self._normalize_base(base, "insert")
        index = position - 1
        self._sequence = sequence[:index] + nucleotide + sequence[index:]

    def delete(self, position: int) -> None:
        """
        Delete the nucleotide at ``position``.

        Args:
            position: 1-based index into the current sequence.

        Raises:
            SequenceNotLoadedError: If no sequence has been loaded.
            InvalidPositionError: If ``position`` is out of range.
        """
        sequence = self._require_sequence()
        self._validate_position(position, len(sequence), "delete")

        index = position - 1
        self._sequence = sequence[:index] + sequence[index + 1:]

    def save(self, output_path: Union[str, Path]) -> None:
        """
        Write the current sequence to a FASTA file.

        Preserves the identifier and description from the loaded record.

        Args:
            output_path: Destination ``.fasta`` path.

        Raises:
            SequenceNotLoadedError: If no sequence has been loaded.
            MutationEngineError: If the file cannot be written.
        """
        sequence = self._require_sequence()
        if self._record is None:
            raise SequenceNotLoadedError(
                "No FASTA record metadata available. "
                "Call load_sequence first."
            )

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        out_record = SeqRecord(
            Seq(sequence),
            id=self._record.id,
            name=self._record.name,
            description=self._record.description,
        )

        try:
            SeqIO.write(out_record, path, "fasta")
        except OSError as exc:
            raise MutationEngineError(
                f"Failed to write FASTA to {path}: {exc}"
            ) from exc

    def get_sequence(self) -> str:
        """
        Return the current DNA sequence (after any applied mutations).

        Returns:
            Uppercase nucleotide string.

        Raises:
            SequenceNotLoadedError: If no sequence has been loaded.
        """
        return self._require_sequence()

    def _require_sequence(self) -> str:
        if self._sequence is None:
            raise SequenceNotLoadedError(
                "No sequence loaded. Call load_sequence(fasta_path) first."
            )
        return self._sequence

    @staticmethod
    def _validate_position(
        position: int,
        sequence_length: int,
        operation: str,
    ) -> None:
        if position < 1 or position > sequence_length:
            raise InvalidPositionError(
                f"{operation.capitalize()} position {position} is out of "
                f"range. Valid range: 1 to {sequence_length} (inclusive)."
            )

    @staticmethod
    def _normalize_base(base: str, operation: str) -> str:
        if not isinstance(base, str):
            raise InvalidBaseError(
                f"{operation.capitalize()} base must be a string, "
                f"got {type(base).__name__}."
            )

        normalized = base.strip().upper()
        if len(normalized) != 1:
            raise InvalidBaseError(
                f"{operation.capitalize()} requires exactly one nucleotide, "
                f"got {base!r}."
            )

        if normalized not in VALID_MUTATION_BASES:
            raise InvalidBaseError(
                f"Invalid base {base!r} for {operation}. "
                f"Allowed bases: {', '.join(sorted(VALID_MUTATION_BASES))}."
            )

        return normalized
