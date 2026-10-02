#!/usr/bin/env python3
"""
Test suite for DNAMutationEngine in dna_processing/mutation/mutation_engine.py.

Verifies loading FASTA sequences, applying single-nucleotide substitutions,
insertions, and deletions, input validation (positions, bases), error handling,
and saving mutated sequences to disk.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from dna_processing.mutation.mutation_engine import (
    DNAMutationEngine,
    InvalidBaseError,
    InvalidPositionError,
    MutationEngineError,
    SequenceNotLoadedError,
)


class TestDNAMutationEngine(unittest.TestCase):
    """Unit and integration test cases for DNAMutationEngine."""

    def setUp(self) -> None:
        """Create a temporary directory and sample FASTA file for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_dir_path = Path(self.temp_dir.name)

        self.sample_fasta = self.temp_dir_path / "sample.fasta"
        self.sample_record = SeqRecord(
            Seq("ATCGATCG"),
            id="seq1",
            name="seq1",
            description="Sample DNA sequence",
        )
        SeqIO.write(self.sample_record, self.sample_fasta, "fasta")

        self.engine = DNAMutationEngine()

    def tearDown(self) -> None:
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_unloaded_engine_raises_errors(self) -> None:
        """Verify that operations on an unloaded engine raise SequenceNotLoadedError."""
        unloaded = DNAMutationEngine()
        with self.assertRaises(SequenceNotLoadedError):
            unloaded.get_sequence()
        with self.assertRaises(SequenceNotLoadedError):
            unloaded.substitute(1, "A")
        with self.assertRaises(SequenceNotLoadedError):
            unloaded.insert(1, "A")
        with self.assertRaises(SequenceNotLoadedError):
            unloaded.delete(1)
        with self.assertRaises(SequenceNotLoadedError):
            unloaded.save(self.temp_dir_path / "out.fasta")

    def test_load_sequence_success(self) -> None:
        """Verify loading a valid FASTA sequence."""
        self.engine.load_sequence(self.sample_fasta)
        self.assertEqual(self.engine.get_sequence(), "ATCGATCG")

    def test_load_sequence_nonexistent_file(self) -> None:
        """Verify loading a non-existent FASTA file raises MutationEngineError."""
        non_existent = self.temp_dir_path / "does_not_exist.fasta"
        with self.assertRaises(MutationEngineError):
            self.engine.load_sequence(non_existent)

    def test_load_sequence_empty_file(self) -> None:
        """Verify loading an empty FASTA file raises MutationEngineError."""
        empty_fasta = self.temp_dir_path / "empty.fasta"
        empty_fasta.write_text("", encoding="utf-8")
        with self.assertRaises(MutationEngineError):
            self.engine.load_sequence(empty_fasta)

    def test_substitute_valid(self) -> None:
        """Verify single-base substitution at start, middle, and end."""
        self.engine.load_sequence(self.sample_fasta)
        
        # Initial: ATCGATCG
        self.engine.substitute(1, "G")
        self.assertEqual(self.engine.get_sequence(), "GTCGATCG")

        self.engine.substitute(8, "T")
        self.assertEqual(self.engine.get_sequence(), "GTCGATCT")

        # Test lowercase normalization
        self.engine.substitute(4, "a")
        self.assertEqual(self.engine.get_sequence(), "GTCAATCT")

    def test_substitute_invalid_position(self) -> None:
        """Verify substitution with out-of-range positions raises InvalidPositionError."""
        self.engine.load_sequence(self.sample_fasta)
        with self.assertRaises(InvalidPositionError):
            self.engine.substitute(0, "A")
        with self.assertRaises(InvalidPositionError):
            self.engine.substitute(9, "A")
        with self.assertRaises(InvalidPositionError):
            self.engine.substitute(-1, "A")

    def test_substitute_invalid_base(self) -> None:
        """Verify substitution with invalid bases raises InvalidBaseError."""
        self.engine.load_sequence(self.sample_fasta)
        with self.assertRaises(InvalidBaseError):
            self.engine.substitute(1, "N")
        with self.assertRaises(InvalidBaseError):
            self.engine.substitute(1, "AT")
        with self.assertRaises(InvalidBaseError):
            self.engine.substitute(1, "")
        with self.assertRaises(InvalidBaseError):
            self.engine.substitute(1, 123)  # type: ignore[arg-type]

    def test_insert_valid(self) -> None:
        """Verify single-base insertion at start, middle, and end."""
        self.engine.load_sequence(self.sample_fasta)
        
        # Initial: ATCGATCG (len 8)
        self.engine.insert(1, "G")
        self.assertEqual(self.engine.get_sequence(), "GATCGATCG")  # len 9

        # Append at position len + 1 (position 10)
        self.engine.insert(10, "T")
        self.assertEqual(self.engine.get_sequence(), "GATCGATCGT")  # len 10

        # Insert in middle (position 5) with lowercase base
        self.engine.insert(5, "c")
        self.assertEqual(self.engine.get_sequence(), "GATCCGATCGT")  # len 11

    def test_insert_invalid_position(self) -> None:
        """Verify insertion with out-of-range positions raises InvalidPositionError."""
        self.engine.load_sequence(self.sample_fasta)
        # Sequence length 8, valid insertion positions are 1..9
        with self.assertRaises(InvalidPositionError):
            self.engine.insert(0, "A")
        with self.assertRaises(InvalidPositionError):
            self.engine.insert(10, "A")

    def test_insert_invalid_base(self) -> None:
        """Verify insertion with invalid bases raises InvalidBaseError."""
        self.engine.load_sequence(self.sample_fasta)
        with self.assertRaises(InvalidBaseError):
            self.engine.insert(1, "X")

    def test_delete_valid(self) -> None:
        """Verify single-base deletion at start, middle, and end."""
        self.engine.load_sequence(self.sample_fasta)
        
        # Initial: ATCGATCG (len 8)
        self.engine.delete(1)
        self.assertEqual(self.engine.get_sequence(), "TCGATCG")  # len 7

        self.engine.delete(7)
        self.assertEqual(self.engine.get_sequence(), "TCGATC")  # len 6

        self.engine.delete(3)
        self.assertEqual(self.engine.get_sequence(), "TCATC")  # len 5

    def test_delete_invalid_position(self) -> None:
        """Verify deletion with out-of-range positions raises InvalidPositionError."""
        self.engine.load_sequence(self.sample_fasta)
        with self.assertRaises(InvalidPositionError):
            self.engine.delete(0)
        with self.assertRaises(InvalidPositionError):
            self.engine.delete(9)

    def test_save(self) -> None:
        """Verify saving mutated sequence to FASTA file."""
        self.engine.load_sequence(self.sample_fasta)
        self.engine.substitute(1, "C")
        self.engine.insert(9, "G")

        out_path = self.temp_dir_path / "output.fasta"
        self.engine.save(out_path)

        self.assertTrue(out_path.is_file())
        saved_record = SeqIO.read(out_path, "fasta")
        self.assertEqual(str(saved_record.seq), "CTCGATCGG")
        self.assertEqual(saved_record.id, "seq1")
        self.assertIn("Sample DNA sequence", saved_record.description)

    def test_hbb_gene_fasta_integration(self) -> None:
        """Integration test using dataset/healthy/hbb_gene.fasta if present."""
        hbb_fasta = PROJECT_ROOT / "dataset" / "healthy" / "hbb_gene.fasta"
        if not hbb_fasta.is_file():
            self.skipTest(f"{hbb_fasta} not found.")

        self.engine.load_sequence(hbb_fasta)
        seq = self.engine.get_sequence()
        self.assertGreater(len(seq), 0)

        # Apply a substitution mutation at position 1
        original_first_base = seq[0]
        new_base = "A" if original_first_base != "A" else "T"
        self.engine.substitute(1, new_base)
        self.assertEqual(self.engine.get_sequence()[0], new_base)


if __name__ == "__main__":
    unittest.main()
