"""DNA sequence validation against standard IUPAC nucleotide rules."""

import re
from typing import List, Tuple

_INVALID_BASE_PATTERN = re.compile(r"[^ATCGN]", re.IGNORECASE)


class DNAValidator:
    """Validate DNA strings for emptiness, length, and allowed bases."""

    def validate(self, sequence: str) -> Tuple[bool, List[str]]:
        """
        Run all validation checks on a DNA sequence.

        Args:
            sequence: Raw DNA sequence (whitespace is ignored for base checks).

        Returns:
            A tuple of (is_valid, error_messages). error_messages is empty
            when is_valid is True.
        """
        errors: List[str] = []
        normalized = sequence.strip() if sequence is not None else ""

        if sequence is None or not normalized:
            errors.append("Sequence is empty; provide at least one nucleotide.")
        else:
            compact = re.sub(r"\s+", "", normalized).upper()
            if len(compact) == 0:
                errors.append(
                    "Sequence contains only whitespace; no nucleotide bases found."
                )
            else:
                invalid_chars = sorted(
                    set(_INVALID_BASE_PATTERN.findall(compact))
                )
                if invalid_chars:
                    chars_display = ", ".join(repr(c) for c in invalid_chars)
                    errors.append(
                        "Sequence contains invalid characters: "
                        f"{chars_display}. Only A, T, C, G, and N are allowed."
                    )

        is_valid = len(errors) == 0
        return is_valid, errors

    def is_valid(self, sequence: str) -> bool:
        """
        Return True if the sequence passes all validation checks.

        Args:
            sequence: DNA sequence to validate.

        Returns:
            True when the sequence is non-empty and uses only A, T, C, G, N.
        """
        is_valid, _ = self.validate(sequence)
        return is_valid
