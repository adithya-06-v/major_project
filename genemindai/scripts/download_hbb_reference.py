#!/usr/bin/env python3
"""
Download the official Homo sapiens HBB RefSeqGene from NCBI.

Uses NCBI Entrez (via Biopython) to fetch the beta-globin (HBB) reference
nucleotide record and write it to ``dataset/raw/hbb_reference.fasta``.
"""

from __future__ import annotations

import os
import sys
from io import StringIO
from pathlib import Path
from typing import List, Tuple
from urllib.error import HTTPError, URLError

from Bio import Entrez, SeqIO
from Bio.SeqRecord import SeqRecord

# RefSeqGene locus for Homo sapiens hemoglobin subunit beta (HBB).
HBB_REFSEQ_ACCESSION: str = "NG_000007"

ENV_NCBI_EMAIL: str = "NCBI_EMAIL"

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_PATH: Path = (
    PROJECT_ROOT / "dataset" / "raw" / "hbb_reference.fasta"
)


class DownloadError(Exception):
    """Raised when the HBB reference sequence cannot be retrieved or saved."""


def get_ncbi_email() -> str:
    """
    Read the NCBI Entrez contact email from the environment.

    NCBI requires a valid email for Entrez API usage.

    Returns:
        The trimmed email string.

    Raises:
        DownloadError: If ``NCBI_EMAIL`` is unset or empty.
    """
    email = os.environ.get(ENV_NCBI_EMAIL, "").strip()
    if not email:
        raise DownloadError(
            f"Missing {ENV_NCBI_EMAIL} environment variable. "
            "Set it to your contact email before running this script, e.g.:\n"
            f'  export {ENV_NCBI_EMAIL}="you@example.com"'
        )
    return email


def configure_entrez(email: str) -> None:
    """
    Configure Biopython Entrez with the user-supplied contact email.

    Args:
        email: Contact email registered with NCBI Entrez guidelines.
    """
    Entrez.email = email


def fetch_fasta_from_ncbi(accession: str) -> str:
    """
    Fetch a nucleotide record from NCBI in FASTA format.

    Args:
        accession: NCBI nucleotide accession (e.g. RefSeqGene ID).

    Returns:
        Raw FASTA text returned by Entrez.

    Raises:
        DownloadError: On network errors, HTTP/API failures, or empty
            responses.
    """
    try:
        handle = Entrez.efetch(
            db="nuccore",
            id=accession,
            rettype="fasta",
            retmode="text",
        )
        try:
            fasta_text = handle.read()
        finally:
            handle.close()
    except HTTPError as exc:
        raise DownloadError(
            f"NCBI Entrez HTTP error for accession {accession!r}: "
            f"{exc.code} {exc.reason}"
        ) from exc
    except URLError as exc:
        raise DownloadError(
            f"Network failure while contacting NCBI Entrez: {exc.reason}"
        ) from exc
    except OSError as exc:
        raise DownloadError(
            f"Network or I/O error during Entrez fetch: {exc}"
        ) from exc

    if not fasta_text or not fasta_text.strip():
        raise DownloadError(
            f"NCBI returned an empty response for accession {accession!r}. "
            "The accession may be invalid or temporarily unavailable."
        )

    if fasta_text.lstrip().startswith("Error"):
        raise DownloadError(
            f"NCBI Entrez API error for accession {accession!r}: "
            f"{fasta_text.strip()}"
        )

    return fasta_text


def parse_fasta_records(fasta_text: str) -> List[SeqRecord]:
    """
    Parse FASTA text into Biopython sequence records.

    Args:
        fasta_text: Entrez FASTA payload.

    Returns:
        List of parsed records (may be empty if parsing fails).

    Raises:
        DownloadError: If no valid FASTA records are present.
    """
    records = list(SeqIO.parse(StringIO(fasta_text), "fasta"))
    if not records:
        raise DownloadError(
            "Could not parse any FASTA records from the NCBI response. "
            "The accession may be invalid or the response format unexpected."
        )
    return records


def write_fasta(records: List[SeqRecord], output_path: Path) -> None:
    """
    Write sequence records to a FASTA file, creating parent directories.

    Args:
        records: Sequences to persist.
        output_path: Destination ``.fasta`` file path.

    Raises:
        DownloadError: If the file cannot be written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        SeqIO.write(records, output_path, "fasta")
    except OSError as exc:
        raise DownloadError(
            f"Failed to write FASTA to {output_path}: {exc}"
        ) from exc


def download_hbb_reference(
    output_path: Path = DEFAULT_OUTPUT_PATH,
    accession: str = HBB_REFSEQ_ACCESSION,
) -> Tuple[SeqRecord, Path]:
    """
    Download Homo sapiens HBB reference DNA and save it as FASTA.

    Args:
        output_path: Where to write ``hbb_reference.fasta``.
        accession: NCBI nucleotide accession for the HBB RefSeqGene locus.

    Returns:
        Tuple of the primary ``SeqRecord`` written and the output path.

    Raises:
        DownloadError: For configuration, network, API, or validation errors.
    """
    email = get_ncbi_email()
    configure_entrez(email)

    fasta_text = fetch_fasta_from_ncbi(accession)
    records = parse_fasta_records(fasta_text)
    write_fasta(records, output_path)

    return records[0], output_path


def print_success(record: SeqRecord, output_path: Path) -> None:
    """
    Print download confirmation and summary statistics.

    Args:
        record: Primary sequence record that was saved.
        output_path: Path to the written FASTA file.
    """
    print("Download successful")
    print(f"Header: {record.description}")
    print(f"Sequence length: {len(record.seq)}")
    print(f"Output path: {output_path.resolve()}")


def main() -> int:
    """
    Entry point for CLI execution.

    Returns:
        Process exit code (0 on success, 1 on failure).
    """
    try:
        record, output_path = download_hbb_reference()
        print_success(record, output_path)
        return 0
    except DownloadError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
