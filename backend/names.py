"""Unicode-aware student-name normalization helpers."""
from __future__ import annotations

import unicodedata

# Normalize common Arabic glyph variants to their Persian counterparts so that
# visually equivalent Persian names share the same uniqueness key.
_PERSIAN_TRANSLATION = str.maketrans({
    "ي": "ی",  # Arabic Yeh -> Persian Yeh
    "ى": "ی",  # Alef Maksura -> Persian Yeh
    "ك": "ک",  # Arabic Kaf -> Persian Kaf
    "ـ": "",   # Tatweel
})


def normalize_student_name(value: str) -> str:
    """Return a trimmed, whitespace-collapsed, consistently composed name."""
    normalized = unicodedata.normalize("NFKC", value).translate(_PERSIAN_TRANSLATION)
    # Arabic vowel marks are optional in everyday name entry; ignore them for
    # both storage and comparison rather than treating them as different names.
    normalized = "".join(
        character
        for character in normalized
        if not ("\u064b" <= character <= "\u065f" or character == "\u0670")
    )
    return " ".join(normalized.split())


def student_name_key(value: str) -> str:
    """Return a case-insensitive Unicode comparison key for a student name."""
    return unicodedata.normalize("NFKC", normalize_student_name(value)).casefold()
