#!/usr/bin/env python3
"""Build a reviewed, ClinVar-derived HBB sequence dataset."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REFERENCE_FASTA = PROJECT_ROOT / "dataset" / "healthy" / "hbb_gene.fasta"
FEATURE_COLUMNS_PATH = PROJECT_ROOT / "ai" / "models" / "feature_columns.json"
RAW_OUTPUT_PATH = PROJECT_ROOT / "dataset" / "processed" / "clinvar_hbb_dataset.csv"
FEATURE_OUTPUT_PATH = (
    PROJECT_ROOT / "dataset" / "processed" / "clinvar_hbb_feature_dataset.csv"
)

CLINVAR_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
GENOMIC_ACCESSION = "NC_000011.10"
HBB_GRCH38_START = 5_225_464
HBB_GRCH38_END = 5_227_071
REVIEW_STATUSES = {
    "criteria provided, multiple submitters, no conflicts",
    "reviewed by expert panel",
}
POSITIVE_CLASSIFICATIONS = {
    "pathogenic",
    "likely pathogenic",
    "pathogenic/likely pathogenic",
}
NEGATIVE_CLASSIFICATIONS = {
    "benign",
    "likely benign",
    "benign/likely benign",
}
METADATA_COLUMNS = [
    "id",
    "sequence",
    "label",
    "mutation_name",
    "mutation_type",
    "clinvar_accession",
    "clinical_significance",
    "review_status",
    "condition",
    "mutation_group",
    "dataset_split",
    "source",
]


class ClinVarDatasetError(Exception):
    """Raised when ClinVar records cannot be safely mapped to the HBB reference."""


def read_fasta_sequence(path: Path) -> str:
    """Read a single FASTA sequence, ignoring headers and whitespace."""
    if not path.is_file():
        raise FileNotFoundError(f"Reference FASTA not found: {path}")
    sequence = "".join(
        line.strip().upper()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith(">")
    )
    if not sequence or re.search(r"[^ATCGN]", sequence):
        raise ClinVarDatasetError(f"Reference FASTA contains invalid bases: {path}")
    return sequence


def reverse_complement(sequence: str) -> str:
    """Return the reverse complement of an unambiguous nucleotide string."""
    if re.search(r"[^ATCG]", sequence):
        raise ValueError("SPDI alleles must contain only A, T, C, and G.")
    return sequence.translate(str.maketrans("ATCG", "TAGC"))[::-1]


def apply_spdi_snv(spdi: str, reference_sequence: str) -> Tuple[str, int]:
    """Apply a GRCh38 HBB SNV to the gene-oriented RefSeqGene sequence.

    Returns the altered sequence and 1-based genomic position. SPDI positions
    are zero-based, and HBB is on the reverse strand of chromosome 11.
    """
    parts = spdi.split(":")
    if len(parts) != 4 or parts[0] != GENOMIC_ACCESSION:
        raise ValueError(f"Unsupported ClinVar SPDI: {spdi}")

    try:
        position = int(parts[1])
    except ValueError as exc:
        raise ValueError(f"Invalid SPDI position: {spdi}") from exc

    deleted, inserted = parts[2].upper(), parts[3].upper()
    if len(deleted) != 1 or len(inserted) != 1 or deleted == inserted:
        raise ValueError(f"Only single-base substitutions are supported: {spdi}")

    genomic_position = position + 1
    if not HBB_GRCH38_START <= genomic_position <= HBB_GRCH38_END:
        raise ValueError(f"SPDI position is outside the HBB gene: {spdi}")

    index = HBB_GRCH38_END - genomic_position
    reference_base = reverse_complement(deleted)
    alternate_base = reverse_complement(inserted)
    if index >= len(reference_sequence) or reference_sequence[index] != reference_base:
        raise ValueError(f"SPDI reference allele does not match HBB reference: {spdi}")

    sequence = (
        reference_sequence[:index]
        + alternate_base
        + reference_sequence[index + 1 :]
    )
    return sequence, genomic_position


def classification_label(record: Dict[str, Any]) -> Optional[int]:
    """Return 1 for reviewed beta-thal variants, 0 for reviewed benign HBB SNVs."""
    classification = record.get("germline_classification", {})
    review_status = classification.get("review_status", "").casefold()
    if review_status not in REVIEW_STATUSES:
        return None

    genes = {gene.get("symbol") for gene in record.get("genes", [])}
    if "HBB" not in genes:
        return None

    significance = re.sub(
        r"\s+", " ", classification.get("description", "").casefold()
    ).strip()
    if significance in NEGATIVE_CLASSIFICATIONS:
        return 0
    if significance not in POSITIVE_CLASSIFICATIONS:
        return None

    traits = [
        trait.get("trait_name", "").casefold()
        for trait in classification.get("trait_set", [])
    ]
    has_beta_thal_trait = any(
        re.search(r"\bbeta[\s-]*thalassemia\b", trait) for trait in traits
    )
    has_sickle_trait = any("sickle" in trait or "hb ss" in trait for trait in traits)
    if has_beta_thal_trait and not has_sickle_trait:
        return 1
    return None


def fetch_clinvar_records(client: httpx.Client, query: str) -> List[Dict[str, Any]]:
    """Fetch all ClinVar summaries for an ESearch query in bounded batches."""
    response = client.get(
        CLINVAR_BASE_URL + "esearch.fcgi",
        params={"db": "clinvar", "term": query, "retmax": 1000, "retmode": "json"},
    )
    response.raise_for_status()
    search_result = response.json()["esearchresult"]
    ids = search_result["idlist"]
    if len(ids) < int(search_result["count"]):
        raise ClinVarDatasetError("ClinVar result exceeds the supported 1,000-record query limit.")

    records: List[Dict[str, Any]] = []
    for start in range(0, len(ids), 100):
        summary_response = client.post(
            CLINVAR_BASE_URL + "esummary.fcgi",
            data={"db": "clinvar", "id": ",".join(ids[start : start + 100]), "retmode": "json"},
        )
        summary_response.raise_for_status()
        summary = summary_response.json()["result"]
        records.extend(summary[uid] for uid in summary["uids"])
    return records


def _variant_metadata(record: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    variations = record.get("variation_set", [])
    if len(variations) != 1:
        return None
    variation = variations[0]
    if variation.get("variant_type", "").casefold() != "single nucleotide variant":
        return None
    spdi = variation.get("canonical_spdi", "")
    return (spdi, variation.get("cdna_change") or variation.get("variation_name", "")) if spdi else None


def _candidate_rows(
    records: List[Dict[str, Any]], reference_sequence: str, expected_label: int
) -> Tuple[List[Dict[str, Any]], Counter[str]]:
    candidates: List[Dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    seen_sequences: set[str] = set()

    for record in records:
        label = classification_label(record)
        if label is None or label != expected_label:
            skipped["unreviewed, uncertain, or out-of-scope classification"] += 1
            continue

        variant = _variant_metadata(record)
        if variant is None:
            skipped["not a single nucleotide variant"] += 1
            continue

        spdi, mutation_name = variant
        try:
            sequence, position = apply_spdi_snv(spdi, reference_sequence)
        except ValueError:
            skipped["unmappable or reference-mismatched variant"] += 1
            continue

        if sequence in seen_sequences:
            skipped["duplicate sequence"] += 1
            continue
        seen_sequences.add(sequence)

        classification = record["germline_classification"]
        candidates.append(
            {
                "id": record.get("accession_version", record.get("accession", "")),
                "sequence": sequence,
                "label": label,
                "mutation_name": mutation_name,
                "mutation_type": "substitution",
                "clinvar_accession": record.get("accession", ""),
                "clinical_significance": classification.get("description", ""),
                "review_status": classification.get("review_status", ""),
                "condition": "; ".join(
                    sorted(
                        trait.get("trait_name", "")
                        for trait in classification.get("trait_set", [])
                        if trait.get("trait_name")
                    )
                ),
                "mutation_group": str(position),
                "source": "ClinVar",
            }
        )

    return candidates, skipped


def assign_challenge_split(
    rows: List[Dict[str, Any]], seed: int = 42, fraction: float = 0.2
) -> None:
    """Hold out whole genomic positions so near-identical variants do not leak."""
    challenge_groups: set[str] = set()
    for label in (0, 1):
        groups = sorted({row["mutation_group"] for row in rows if row["label"] == label})
        if len(groups) < 2:
            continue
        ordered = sorted(
            groups,
            key=lambda group: hashlib.sha256(f"{seed}:{label}:{group}".encode()).hexdigest(),
        )
        holdout_count = min(len(groups) - 1, max(1, round(len(groups) * fraction)))
        challenge_groups.update(ordered[:holdout_count])

    for row in rows:
        row["dataset_split"] = (
            "challenge" if row["mutation_group"] in challenge_groups else "train"
        )


def encode_kmer_features(
    sequence: str, feature_columns: List[str], k: int = 3
) -> Dict[str, float]:
    """Encode normalized overlapping k-mer frequencies in saved model order."""
    windows = [sequence[index : index + k] for index in range(len(sequence) - k + 1)]
    counts = Counter(windows)
    denominator = len(windows) or 1
    return {feature: counts.get(feature, 0) / denominator for feature in feature_columns}


def write_dataset(
    rows: List[Dict[str, Any]],
    feature_columns: List[str],
    raw_path: Path = RAW_OUTPUT_PATH,
    feature_path: Path = FEATURE_OUTPUT_PATH,
) -> None:
    """Write raw sequences and a model-ready k-mer feature table."""
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    feature_path.parent.mkdir(parents=True, exist_ok=True)

    with raw_path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=METADATA_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    feature_columns_out = [column for column in METADATA_COLUMNS if column != "sequence"] + feature_columns
    with feature_path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=feature_columns_out)
        writer.writeheader()
        for row in rows:
            feature_row = {key: value for key, value in row.items() if key != "sequence"}
            feature_row.update(encode_kmer_features(row["sequence"], feature_columns))
            writer.writerow(feature_row)


def build_dataset() -> Tuple[List[Dict[str, Any]], Counter[str]]:
    """Fetch curated ClinVar HBB variants and build the raw/feature datasets."""
    quote = chr(34)
    review_filter = (
        f"({quote}criteria provided, multiple submitters, no conflicts{quote}[Review Status] "
        f"OR {quote}reviewed by expert panel{quote}[Review Status])"
    )
    positive_query = f"HBB[gene] AND {quote}beta-thalassemia{quote}[dis] AND {review_filter}"
    negative_query = f"HBB[gene] AND {review_filter}"

    with httpx.Client(
        timeout=60,
        headers={"User-Agent": "GeneMindAI-curated-dataset-builder/1.0"},
    ) as client:
        positive_records = fetch_clinvar_records(client, positive_query)
        benign_records = fetch_clinvar_records(client, negative_query)

    reference_sequence = read_fasta_sequence(REFERENCE_FASTA)
    positive_rows, skipped_positive = _candidate_rows(
        positive_records, reference_sequence, expected_label=1
    )
    benign_rows, skipped_benign = _candidate_rows(
        benign_records, reference_sequence, expected_label=0
    )

    positive_sequences = {row["sequence"] for row in positive_rows if row["label"] == 1}
    benign_rows = [row for row in benign_rows if row["label"] == 0]
    benign_sequences = {row["sequence"] for row in benign_rows}
    conflicting_sequences = positive_sequences & benign_sequences
    rows = [
        row
        for row in positive_rows + benign_rows
        if row["sequence"] not in conflicting_sequences
    ]
    rows.sort(key=lambda row: (row["label"], row["mutation_group"], row["id"]))
    assign_challenge_split(rows)

    if not any(row["label"] == 0 for row in rows) or not any(row["label"] == 1 for row in rows):
        raise ClinVarDatasetError("ClinVar filters did not produce both target classes.")

    skipped = skipped_positive + skipped_benign
    skipped["cross-class sequence conflicts"] = len(conflicting_sequences)
    return rows, skipped


def main() -> int:
    rows, skipped = build_dataset()
    feature_columns = json.loads(FEATURE_COLUMNS_PATH.read_text(encoding="utf-8"))
    write_dataset(rows, feature_columns)

    counts = Counter((row["dataset_split"], row["label"]) for row in rows)
    print(f"ClinVar retrieval date: {date.today().isoformat()}")
    print(f"Curated samples written: {len(rows)}")
    print(f"Healthy / benign controls: {sum(row['label'] == 0 for row in rows)}")
    print(f"Beta Thalassemia variants: {sum(row['label'] == 1 for row in rows)}")
    print(f"Train/challenge by class: {dict(counts)}")
    print(f"Excluded records: {dict(skipped)}")
    print(f"Raw dataset: {RAW_OUTPUT_PATH}")
    print(f"Feature dataset: {FEATURE_OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())