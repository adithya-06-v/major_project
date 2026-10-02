#!/usr/bin/env python3
"""
Extract the HBB gene region from the RefSeqGene GenBank annotation.

Locates the ``gene`` feature with ``/gene="HBB"``, slices the parent
sequence by that feature's coordinates, and writes ``hbb_gene.fasta``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Tuple

from Bio import SeqIO
from Bio.SeqFeature import SeqFeature
from Bio.SeqRecord import SeqRecord

HBB_GENE_SYMBOL: str = "HBB"
GENE_FEATURE_TYPE: str = "gene"

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_GENBANK_PATH: Path = (
    PROJECT_ROOT / "dataset" / "raw" / "hbb_reference.gb"
)
DEFAULT_OUTPUT_PATH: Path = (
    PROJECT_ROOT / "dataset" / "healthy" / "hbb_gene.fasta"
)


class GeneExtractError(Exception):
    """Raised when the HBB gene cannot be located or written to FASTA."""


def load_genbank_record(genbank_path: Path) -> SeqRecord:
    """
    Load the first sequence record from a GenBank flat file.

    Args:
        genbank_path: Path to the ``.gb`` annotation file.

    Returns:
        Parsed ``SeqRecord`` with features and sequence.

    Raises:
        GeneExtractError: If the file is missing or cannot be parsed.
    """
    if not genbank_path.is_file():
        raise GeneExtractError(
            f"GenBank file not found: {genbank_path.resolve()}"
        )

    try:
        record = SeqIO.read(genbank_path, "genbank")
    except OSError as exc:
        raise GeneExtractError(
            f"Could not read GenBank file {genbank_path}: {exc}"
        ) from exc
    except ValueError as exc:
        raise GeneExtractError(
            f"Could not parse GenBank file {genbank_path}: {exc}"
        ) from exc

    return record


def is_hbb_gene_feature(feature: SeqFeature) -> bool:
    """
    Return True if the feature is a ``gene`` type annotated as HBB.

    Args:
        feature: GenBank feature entry.

    Returns:
        True when ``type`` is ``gene`` and the ``gene`` qualifier is HBB.
    """
    if feature.type != GENE_FEATURE_TYPE:
        return False
    gene_values = feature.qualifiers.get("gene", [])
    return HBB_GENE_SYMBOL in gene_values


def find_hbb_gene_feature(record: SeqRecord) -> SeqFeature:
    """
    Search record features for the HBB ``gene`` feature.

    Args:
        record: GenBank record containing feature tables.

    Returns:
        The single matching ``gene`` feature.

    Raises:
        GeneExtractError: If zero or multiple HBB ``gene`` features exist.
    """
    matches: List[SeqFeature] = [
        feature for feature in record.features if is_hbb_gene_feature(feature)
    ]

    if not matches:
        raise GeneExtractError(
            f"No {GENE_FEATURE_TYPE!r} feature with "
            f"gene={HBB_GENE_SYMBOL!r} found in {record.id!r}."
        )

    if len(matches) > 1:
        raise GeneExtractError(
            f"Expected one HBB {GENE_FEATURE_TYPE!r} feature, "
            f"found {len(matches)} in {record.id!r}."
        )

    return matches[0]


def genbank_coordinates(feature: SeqFeature) -> Tuple[int, int]:
    """
    Convert a feature location to 1-based inclusive GenBank coordinates.

    Args:
        feature: GenBank feature with a location.

    Returns:
        Tuple of (start, end) in GenBank numbering.
    """
    start = int(feature.location.start) + 1
    end = int(feature.location.end)
    return start, end


def build_gene_record(parent: SeqRecord, feature: SeqFeature) -> SeqRecord:
    """
    Extract gene sequence and preserve the parent FASTA header fields.

    Args:
        parent: Full RefSeqGene ``SeqRecord``.
        feature: HBB ``gene`` feature defining coordinates.

    Returns:
        New ``SeqRecord`` containing only the gene region sequence.

    Raises:
        GeneExtractError: If sequence extraction fails.
    """
    try:
        gene_sequence = feature.extract(parent.seq)
    except (ValueError, TypeError) as exc:
        raise GeneExtractError(
            f"Failed to extract sequence for gene {HBB_GENE_SYMBOL!r}: "
            f"{exc}"
        ) from exc

    return SeqRecord(
        gene_sequence,
        id=parent.id,
        name=parent.name,
        description=parent.description,
    )


def write_fasta(gene_record: SeqRecord, output_path: Path) -> None:
    """
    Write a sequence record to FASTA, creating parent directories.

    Args:
        gene_record: Extracted gene ``SeqRecord`` to persist.
        output_path: Destination ``.fasta`` file.

    Raises:
        GeneExtractError: If the file cannot be written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        SeqIO.write(gene_record, output_path, "fasta")
    except OSError as exc:
        raise GeneExtractError(
            f"Failed to write FASTA to {output_path}: {exc}"
        ) from exc


def extract_hbb_gene(
    genbank_path: Path = DEFAULT_GENBANK_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> Tuple[str, int, int, int, Path]:
    """
    Locate HBB in GenBank annotations and save the gene region as FASTA.

    Args:
        genbank_path: Input GenBank annotation file.
        output_path: Output FASTA path under ``dataset/healthy/``.

    Returns:
        Tuple of gene name, start, end, sequence length, and output path.

    Raises:
        GeneExtractError: On read, search, extract, or write failures.
    """
    record = load_genbank_record(genbank_path)
    gene_feature = find_hbb_gene_feature(record)
    gene_record = build_gene_record(record, gene_feature)
    write_fasta(gene_record, output_path)

    start, end = genbank_coordinates(gene_feature)
    length = len(gene_record.seq)
    return HBB_GENE_SYMBOL, start, end, length, output_path


def print_summary(
    gene_name: str,
    start: int,
    end: int,
    length: int,
    output_path: Path,
) -> None:
    """
    Print extraction results to stdout.

    Args:
        gene_name: Gene symbol extracted.
        start: 1-based GenBank start coordinate.
        end: 1-based GenBank end coordinate.
        length: Extracted sequence length in bases.
        output_path: Written FASTA file path.
    """
    print(f"Gene name: {gene_name}")
    print(f"Start: {start}")
    print(f"End: {end}")
    print(f"Length: {length}")
    print(f"Output file: {output_path.resolve()}")


def main() -> int:
    """
    Entry point for CLI execution.

    Returns:
        Process exit code (0 on success, 1 on failure).
    """
    try:
        gene_name, start, end, length, output_path = extract_hbb_gene()
        print_summary(gene_name, start, end, length, output_path)
        return 0
    except GeneExtractError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
