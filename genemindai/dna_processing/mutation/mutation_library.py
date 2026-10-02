"""
Beta Thalassemia DNA mutation catalog and library.

Provides a structured collection of documented pathogenic mutations in the
Homo sapiens hemoglobin subunit beta (HBB) gene responsible for Beta Thalassemia.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DNAMutation:
    """
    Representation of a single-nucleotide mutation in a DNA sequence.

    Attributes:
        name: Standard clinical/HGVS nomenclature or short identifier.
        mutation_type: Category of edit ("substitution", "insertion", "deletion").
        position: 1-based nucleotide position in the reference sequence.
        reference_base: Original base at position before mutation, or None for insertions.
        alternate_base: Mutant base replacing reference, or None for deletions.
        description: Biological impact, clinical phenotype, and details.
    """

    name: str
    mutation_type: str
    position: int
    reference_base: Optional[str]
    alternate_base: Optional[str]
    description: str


class MutationLibrary:
    """
    Catalog of known pathogenic mutations associated with Beta Thalassemia.

    Serves as a repository of well-characterized single-nucleotide substitutions,
    insertions, and deletions in the HBB gene locus.
    """

    @classmethod
    def get_beta_thalassemia_mutations(cls) -> List[DNAMutation]:
        """
        Retrieve documented pathogenic Beta Thalassemia mutations in HBB.

        Returns:
            List of DNAMutation objects detailing position, mutation type,
            reference base, alternate base, and clinical significance.
        """
        mutations: List[DNAMutation] = [
            # 1. HBB:c.20A>T (HbS / Sickle Cell & Beta-Thalassemia interaction variant)
            # Position: Codon 6 (c.20), substitution of Adenine (A) to Thymine (T).
            # Causes GAG -> GTG (Glu -> Val) amino acid change, responsible for
            # Sickle Cell Hemoglobin (HbS) and severe Sickle-Beta Thalassemia.
            DNAMutation(
                name="HbS (c.20A>T, p.Glu7Val)",
                mutation_type="substitution",
                position=70,
                reference_base="A",
                alternate_base="T",
                description=(
                    "Pathogenic missense mutation in codon 6/7 (GAG->GTG) converting "
                    "glutamic acid to valine. Interacts with beta-thalassemia alleles "
                    "to cause Sickle-Beta Thalassemia."
                ),
            ),
            # 2. HBB:c.118C>T (Codon 39 Nonsense Mutation, Gln40Ter)
            # Position: Codon 39 (c.118), substitution of Cytosine (C) to Thymine (T).
            # Changes CAG (Glutamine) to TAG (Stop codon), producing a premature
            # termination codon resulting in non-functional mRNA and Beta-0 Thalassemia.
            DNAMutation(
                name="Codon 39 (c.118C>T, p.Gln40Ter)",
                mutation_type="substitution",
                position=118,
                reference_base="C",
                alternate_base="T",
                description=(
                    "Common Western Mediterranean nonsense mutation (CAG->TAG) introducing "
                    "a premature stop codon at codon 39, leading to total loss of "
                    "beta-globin synthesis (Beta-0 Thalassemia)."
                ),
            ),
            # 3. HBB:c.92+1G>A (IVS-I-1 G>A Donor Splice Site Mutation)
            # Position: Intron 1 donor splice site (+1 position, c.92+1).
            # Substitution of Guanine (G) to Adenine (A) completely destroys
            # the 5' splice donor site of Intron 1, preventing correct splicing.
            DNAMutation(
                name="IVS-I-1 (c.92+1G>A)",
                mutation_type="substitution",
                position=143,
                reference_base="G",
                alternate_base="A",
                description=(
                    "Severe Beta-0 thalassemia mutation disrupting the conserved "
                    "GU donor splice site at the start of Intron 1, causing aberrant "
                    "splicing and absence of functional beta-globin."
                ),
            ),
            # 4. HBB:c.93-21G>A (IVS-I-110 G>A Aberrant Splice Acceptor Mutation)
            # Position: Intron 1 position 110 (c.93-21).
            # Substitution of Guanine (G) to Adenine (A) creates a novel, competitive
            # AG splice acceptor site in Intron 1, causing incorrect mRNA processing.
            DNAMutation(
                name="IVS-I-110 (c.93-21G>A)",
                mutation_type="substitution",
                position=253,
                reference_base="G",
                alternate_base="A",
                description=(
                    "Prevalent Mediterranean Beta-plus thalassemia mutation creating "
                    "an artificial AG splice acceptor site in Intron 1, resulting in "
                    "incorrectly spliced mRNA and reduced beta-globin production."
                ),
            ),
            # 5. HBB:c.27dupG (Codon 8/9 Single Base Frameshift Insertion)
            # Position: Codon 8/9 (c.27), insertion of an extra Guanine (G).
            # Shifts the reading frame starting from codon 9, leading to downstream
            # premature stop codons and Beta-0 Thalassemia phenotype.
            DNAMutation(
                name="Codon 8/9 (+G insertion, c.27dupG)",
                mutation_type="insertion",
                position=27,
                reference_base=None,
                alternate_base="G",
                description=(
                    "Frameshift insertion mutation introducing an extra Guanine (+G) at "
                    "codons 8/9, disrupting the reading frame and resulting in "
                    "Beta-0 Thalassemia."
                ),
            ),
            # 6. HBB:c.126delT (Codon 41/42 Frameshift Deletion)
            # Position: Codon 41/42 (c.126), deletion of Thymine (T).
            # Alters the reading frame from codon 42 onwards, preventing synthesis
            # of full-length beta-globin protein.
            DNAMutation(
                name="Codon 41/42 (-T deletion, c.126delT)",
                mutation_type="deletion",
                position=126,
                reference_base="T",
                alternate_base=None,
                description=(
                    "Frameshift deletion of a single Thymine (-T) in codons 41/42, "
                    "causing frame shift, premature translation termination, and "
                    "severe Beta-0 Thalassemia."
                ),
            ),
        ]
        return mutations
