"""Basic descriptive statistics for DNA sequences."""

import re
from typing import Dict


def compute_sequence_statistics(sequence: str) -> Dict[str, float]:
    """
    Compute nucleotide counts and composition metrics for a DNA sequence.

    Whitespace is removed; bases are counted case-insensitively. Ambiguous
    bases (e.g. N) contribute to length but not to A/T/C/G counts or AT/GC
    content percentages.

    Args:
        sequence: DNA sequence string.

    Returns:
        Dictionary with keys: sequence_length, a_count, t_count, c_count,
        g_count, gc_content, at_content. Counts are integers stored as
        numeric values; content fields are percentages in [0, 100] or 0.0
        when length is zero.

    Raises:
        ValueError: If sequence is None.
    """
    if sequence is None:
        raise ValueError("Sequence cannot be None.")

    compact = re.sub(r"\s+", "", sequence).upper()
    length = len(compact)

    a_count = compact.count("A")
    t_count = compact.count("T")
    c_count = compact.count("C")
    g_count = compact.count("G")

    countable = a_count + t_count + c_count + g_count
    if countable == 0:
        gc_content = 0.0
        at_content = 0.0
    else:
        gc_content = (c_count + g_count) / countable * 100.0
        at_content = (a_count + t_count) / countable * 100.0

    return {
        "sequence_length": length,
        "a_count": float(a_count),
        "t_count": float(t_count),
        "c_count": float(c_count),
        "g_count": float(g_count),
        "gc_content": gc_content,
        "at_content": at_content,
    }
