#!/usr/bin/env python3
"""
Explore GenBank annotations for the downloaded HBB RefSeqGene record.

Reads ``dataset/raw/hbb_reference.gb``, prints record metadata, iterates all
features, and highlights any feature annotated with ``gene=HBB``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from Bio import SeqIO
from Bio.SeqFeature import SeqFeature
from Bio.SeqRecord import SeqRecord

HBB_GENE_SYMBOL: str = "HBB"

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_GENBANK_PATH: Path = (
    PROJECT_ROOT / "dataset" / "raw" / "hbb_reference.gb"
)


class GenBankExploreError(Exception):
    """Raised when the GenBank file cannot be read or parsed."""


def load_genbank_record(genbank_path: Path) -> SeqRecord:
    """
    Load the first sequence record from a GenBank flat file.

    Args:
        genbank_path: Path to the ``.gb`` annotation file.

    Returns:
        Parsed ``SeqRecord`` with features and sequence.

    Raises:
        GenBankExploreError: If the file is missing or contains no records.
    """
    if not genbank_path.is_file():
        raise GenBankExploreError(
            f"GenBank file not found: {genbank_path.resolve()}"
        )

    try:
        record = SeqIO.read(genbank_path, "genbank")
    except OSError as exc:
        raise GenBankExploreError(
            f"Could not read GenBank file {genbank_path}: {exc}"
        ) from exc
    except ValueError as exc:
        raise GenBankExploreError(
            f"Could not parse GenBank file {genbank_path}: {exc}"
        ) from exc

    return record


def print_record_summary(record: SeqRecord) -> None:
    """
    Print top-level identifiers and sequence length for a GenBank record.

    Args:
        record: Loaded GenBank ``SeqRecord``.
    """
    print(f"Record ID: {record.id}")
    print(f"Record Name: {record.name}")
    print(f"Sequence Length: {len(record.seq)}")


def get_gene_name(feature: SeqFeature) -> Optional[str]:
    """
    Return the gene symbol from a feature's qualifiers, if present.

    Args:
        feature: GenBank feature with optional ``gene`` qualifier.

    Returns:
        First ``gene`` qualifier value, or ``None`` when absent.
    """
    gene_values = feature.qualifiers.get("gene", [])
    if not gene_values:
        return None
    return str(gene_values[0])


def format_strand(feature: SeqFeature) -> str:
    """
    Format the feature location strand for display.

    Args:
        feature: GenBank feature with a location.

    Returns:
        ``+``, ``-``, or ``.`` when strand is unknown.
    """
    strand = feature.location.strand
    if strand == 1:
        return "+"
    if strand == -1:
        return "-"
    return "."


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


def feature_has_hbb_gene(feature: SeqFeature) -> bool:
    """
    Return True if the feature's ``gene`` qualifier includes HBB.

    Args:
        feature: GenBank feature to inspect.

    Returns:
        True when ``gene`` is set to ``HBB``.
    """
    gene_values = feature.qualifiers.get("gene", [])
    return HBB_GENE_SYMBOL in gene_values


def print_feature_overview(feature: SeqFeature) -> None:
    """
    Print type, location, and gene name for one GenBank feature.

    Args:
        feature: Feature from the record annotation.
    """
    print(f"Feature type: {feature.type}")
    print(f"Location: {feature.location}")
    gene_name = get_gene_name(feature)
    if gene_name is not None:
        print(f"Gene name: {gene_name}")
    else:
        print("Gene name: (not specified)")


def print_hbb_gene_details(feature: SeqFeature) -> None:
    """
    Print highlighted annotation details for an HBB gene feature.

    Args:
        feature: Feature whose ``gene`` qualifier is ``HBB``.
    """
    start, end = genbank_coordinates(feature)
    print("=========================")
    print("HBB GENE FOUND")
    print("=========================")
    print(f"Start coordinate: {start}")
    print(f"End coordinate: {end}")
    print(f"Strand: {format_strand(feature)}")
    print(f"Qualifiers: {format_qualifiers(feature.qualifiers)}")


def format_qualifiers(qualifiers: Dict[str, List[Any]]) -> str:
    """
    Format feature qualifiers for readable console output.

    Args:
        qualifiers: Biopython qualifier mapping on a feature.

    Returns:
        Single-line string representation of all qualifiers.
    """
    parts: List[str] = []
    for key in sorted(qualifiers):
        values = qualifiers[key]
        rendered = ", ".join(repr(value) for value in values)
        parts.append(f"{key}=[{rendered}]")
    return "; ".join(parts)


def explore_features(record: SeqRecord) -> None:
    """
    Iterate all features and print annotation details.

    Highlights features annotated with ``gene=HBB``.

    Args:
        record: GenBank record whose features will be listed.
    """
    for index, feature in enumerate(record.features, start=1):
        print()
        print(f"--- Feature {index} ---")
        print_feature_overview(feature)
        if feature_has_hbb_gene(feature):
            print()
            print_hbb_gene_details(feature)


def explore_genbank(genbank_path: Path = DEFAULT_GENBANK_PATH) -> None:
    """
    Load a GenBank file and print record and feature annotation.

    Args:
        genbank_path: Path to ``hbb_reference.gb``.

    Raises:
        GenBankExploreError: If loading or parsing fails.
    """
    record = load_genbank_record(genbank_path)
    print_record_summary(record)
    print()
    print("=== Feature annotations ===")
    explore_features(record)


def main() -> int:
    """
    Entry point for CLI execution.

    Returns:
        Process exit code (0 on success, 1 on failure).
    """
    try:
        explore_genbank()
        return 0
    except GenBankExploreError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
