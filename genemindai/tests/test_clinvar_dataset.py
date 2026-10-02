from pathlib import Path

import pytest

from scripts.build_clinvar_dataset import (
    apply_spdi_snv,
    assign_challenge_split,
    classification_label,
    read_fasta_sequence,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def reviewed_record(significance: str, traits: list[str]) -> dict:
    return {
        "genes": [{"symbol": "HBB"}],
        "germline_classification": {
            "description": significance,
            "review_status": "criteria provided, multiple submitters, no conflicts",
            "trait_set": [{"trait_name": trait} for trait in traits],
        },
    }


def test_spdi_maps_hbs_variant_to_hbb_reference() -> None:
    reference = read_fasta_sequence(
        PROJECT_ROOT / "dataset" / "healthy" / "hbb_gene.fasta"
    )
    expected = read_fasta_sequence(
        PROJECT_ROOT / "dataset" / "mutated" / "hbs_c_20a_t_p_glu7val.fasta"
    )

    sequence, position = apply_spdi_snv(
        "NC_000011.10:5227001:T:A", reference
    )

    assert sequence == expected
    assert position == 5_227_002


def test_spdi_rejects_reference_allele_mismatch() -> None:
    reference = read_fasta_sequence(
        PROJECT_ROOT / "dataset" / "healthy" / "hbb_gene.fasta"
    )

    with pytest.raises(ValueError, match="reference allele"):
        apply_spdi_snv("NC_000011.10:5227001:C:A", reference)


def test_classification_requires_beta_thal_trait_for_positive_label() -> None:
    assert classification_label(
        reviewed_record("Likely pathogenic", ["beta Thalassemia"])
    ) == 1
    assert classification_label(
        reviewed_record("Pathogenic", ["Sickle cell disease"])
    ) is None
    assert classification_label(
        reviewed_record("Uncertain significance", ["beta Thalassemia"])
    ) is None


def test_reviewed_benign_hbb_variant_is_control() -> None:
    assert classification_label(reviewed_record("Likely benign", ["not specified"])) == 0


def test_challenge_split_holds_out_whole_variant_positions() -> None:
    rows = [
        {"label": label, "mutation_group": str(position)}
        for label in (0, 1)
        for position in range(label * 10, label * 10 + 10)
    ]

    assign_challenge_split(rows)

    splits_by_group: dict[str, set[str]] = {}
    for row in rows:
        splits_by_group.setdefault(row["mutation_group"], set()).add(row["dataset_split"])
    assert all(len(splits) == 1 for splits in splits_by_group.values())
    assert {row["dataset_split"] for row in rows} == {"train", "challenge"}