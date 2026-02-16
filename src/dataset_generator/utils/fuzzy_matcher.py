"""Fuzzy string matching utilities for evidence validation."""


def normalize_for_comparison(text: str) -> str:
    """Normalize text for comparison: strip trailing whitespace per line, normalize line endings.

    Does NOT lowercase — preserves case for accurate matching.
    Does NOT strip leading whitespace — preserves indentation.
    """
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    return '\n'.join(line.rstrip() for line in lines)


def fuzzy_match_score(text_a: str, text_b: str) -> float:
    """Return fuzzy similarity score (0-100) between two strings.

    Uses RapidFuzz fuzz.ratio for character-level comparison.
    Normalizes both inputs before comparison.

    Note: RapidFuzz 3.0+ does NOT auto-preprocess strings.
    We normalize explicitly before passing to fuzz.ratio.
    """
    from rapidfuzz import fuzz
    normalized_a = normalize_for_comparison(text_a)
    normalized_b = normalize_for_comparison(text_b)
    return fuzz.ratio(normalized_a, normalized_b)
