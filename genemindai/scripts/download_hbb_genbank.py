#!/usr/bin/env python3
"""
Download the annotated Homo sapiens HBB RefSeqGene record from NCBI.

Uses NCBI Entrez (via Biopython) to fetch accession ``NG_000007.3`` in
GenBank format and write it to ``dataset/raw/hbb_reference.gb``.
"""

from __future__ import annotations

import os
import sys
from io import StringIO
from pathlib import Path
from typing import Tuple
from urllib.error import HTTPError, URLError

from Bio import Entrez, SeqIO

# Annotated RefSeqGene for Homo sapiens hemoglobin subunit beta (HBB).
HBB_REFSEQGENE_ACCESSION: str = "NG_000007.3"

ENV_NCBI_EMAIL: str = "NCBI_EMAIL"

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_PATH: Path = (
    PROJECT_ROOT / "dataset" / "raw" / "hbb_reference.gb"
)


class DownloadError(Exception):
    """Raised when the HBB GenBank record cannot be retrieved or saved."""


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


def fetch_genbank_from_ncbi(accession: str) -> str:
    """
    Fetch a nucleotide record from NCBI in GenBank flat-file format.

    Args:
        accession: NCBI nucleotide accession (RefSeqGene versioned ID).

    Returns:
        Raw GenBank text returned by Entrez.

    Raises:
        DownloadError: On network errors, HTTP/API failures, empty
            responses, or invalid accession data.
    """
    try:
        handle = Entrez.efetch(
            db="nuccore",
            id=accession,
            rettype="gb",
            retmode="text",
        )
        try:
            genbank_text = handle.read()
        finally:
            handle.close()
    except HTTPError as exc:
        raise DownloadError(
            f"NCBI Entrez HTTP error for accession {accession!r}: "
            f"{exc.code} {exc.reason}"
        ) from exc
    except URLError as exc:
        raise DownloadError(
            f"Internet failure while contacting NCBI Entrez: {exc.reason}"
        ) from exc
    except OSError as exc:
        raise DownloadError(
            f"Network or I/O error during Entrez fetch: {exc}"
        ) from exc

    if not genbank_text or not genbank_text.strip():
        raise DownloadError(
            f"NCBI returned an empty response for accession {accession!r}. "
            "The accession may be invalid or temporarily unavailable."
        )

    if genbank_text.lstrip().startswith("Error"):
        raise DownloadError(
            f"NCBI Entrez API error for accession {accession!r}: "
            f"{genbank_text.strip()}"
        )

    records = list(SeqIO.parse(StringIO(genbank_text), "genbank"))
    if not records:
        raise DownloadError(
            f"Invalid accession or unparseable GenBank data for "
            f"{accession!r}. No records could be read from the response."
        )

    return genbank_text


def write_genbank_file(genbank_text: str, output_path: Path) -> None:
    """
    Persist GenBank flat-file text, creating parent directories as needed.

    Args:
        genbank_text: Annotated GenBank record from Entrez.
        output_path: Destination ``.gb`` file path.

    Raises:
        DownloadError: If the file cannot be written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        output_path.write_text(genbank_text, encoding="utf-8")
    except OSError as exc:
        raise DownloadError(
            f"Failed to write GenBank file to {output_path}: {exc}"
        ) from exc


def download_hbb_genbank(
    output_path: Path = DEFAULT_OUTPUT_PATH,
    accession: str = HBB_REFSEQGENE_ACCESSION,
) -> Tuple[str, Path]:
    """
    Download the annotated HBB RefSeqGene record and save it as GenBank.

    Args:
        output_path: Where to write ``hbb_reference.gb``.
        accession: Versioned NCBI accession (default ``NG_000007.3``).

    Returns:
        Tuple of the accession used and the output file path.

    Raises:
        DownloadError: For configuration, network, API, or validation errors.
    """
    email = get_ncbi_email()
    configure_entrez(email)

    genbank_text = fetch_genbank_from_ncbi(accession)
    write_genbank_file(genbank_text, output_path)

    return accession, output_path


def print_success(accession: str, output_path: Path) -> None:
    """
    Print download confirmation and output location.

    Args:
        accession: NCBI accession that was downloaded.
        output_path: Path to the written GenBank file.
    """
    print("Download successful")
    print(f"Accession: {accession}")
    print(f"Output file: {output_path.resolve()}")


def main() -> int:
    """
    Entry point for CLI execution.

    Returns:
        Process exit code (0 on success, 1 on failure).
    """
    try:
        accession, output_path = download_hbb_genbank()
        print_success(accession, output_path)
        return 0
    except DownloadError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
