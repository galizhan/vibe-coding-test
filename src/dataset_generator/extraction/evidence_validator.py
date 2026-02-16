"""Evidence validation against source text."""

from dataset_generator.models import Evidence
from .markdown_parser import ParsedMarkdown
from dataset_generator.utils.fuzzy_matcher import normalize_for_comparison, fuzzy_match_score


def validate_evidence_quote(
    parsed: ParsedMarkdown,
    evidence: Evidence,
    enable_fuzzy: bool = True,
    fuzzy_threshold: float = 90.0
) -> tuple[bool, str]:
    """Validate that evidence quote matches source lines exactly or via fuzzy matching.

    Args:
        parsed: ParsedMarkdown instance with source lines
        evidence: Evidence instance to validate
        enable_fuzzy: Enable fuzzy matching fallback (default: True)
        fuzzy_threshold: Minimum similarity score for fuzzy match (default: 90.0)

    Returns:
        Tuple of (is_valid, message)
        - (True, "") if quote matches exactly
        - (True, "Fuzzy match (XX.X% similarity)") if fuzzy match succeeds
        - (False, "description") if both exact and fuzzy match fail

    Notes:
        - Converts 1-based line numbers to 0-based array indices
        - Normalizes whitespace (strips trailing whitespace per line)
        - Exact match is ALWAYS tried first, fuzzy is fallback only
        - Handles edge cases: out-of-bounds line numbers, empty lines
    """
    # Convert 1-based to 0-based indices
    start_idx = evidence.line_start - 1
    end_idx = evidence.line_end  # end_idx is exclusive in slice

    # Check bounds
    if start_idx < 0:
        return False, f"line_start={evidence.line_start} is invalid (must be >= 1)"

    if end_idx > len(parsed.lines):
        return False, (
            f"line_end={evidence.line_end} exceeds file length "
            f"({len(parsed.lines)} lines)"
        )

    # Extract actual text from source
    actual_lines = parsed.lines[start_idx:end_idx]
    actual_text = '\n'.join(actual_lines)

    # Normalize both sides for comparison using shared utility
    normalized_actual = normalize_for_comparison(actual_text)
    normalized_quote = normalize_for_comparison(evidence.quote)

    # Try exact match first
    if normalized_actual == normalized_quote:
        return True, ""

    # If exact match fails and fuzzy matching is enabled, try fuzzy fallback
    if enable_fuzzy:
        score = fuzzy_match_score(actual_text, evidence.quote)
        if score >= fuzzy_threshold:
            return True, f"Fuzzy match ({score:.1f}% similarity)"

        # Fuzzy match also failed - include score in error message
        return False, (
            f"Quote mismatch at lines {evidence.line_start}-{evidence.line_end} "
            f"(fuzzy score: {score:.1f}%):\n"
            f"Expected: {normalized_actual[:100]!r}...\n"
            f"Got:      {normalized_quote[:100]!r}..."
        )

    # Fuzzy matching disabled - return exact match error
    return False, (
        f"Quote mismatch at lines {evidence.line_start}-{evidence.line_end}:\n"
        f"Expected: {normalized_actual[:100]!r}...\n"
        f"Got:      {normalized_quote[:100]!r}..."
    )


def validate_all_evidence(
    parsed: ParsedMarkdown,
    items: list,
    enable_fuzzy: bool = True,
    fuzzy_threshold: float = 90.0
) -> tuple[int, int, list[str]]:
    """Validate evidence for all items (UseCases or Policies).

    Args:
        parsed: ParsedMarkdown instance with source lines
        items: List of objects with .evidence attribute (UseCase or Policy)
        enable_fuzzy: Enable fuzzy matching fallback (default: True)
        fuzzy_threshold: Minimum similarity score for fuzzy match (default: 90.0)

    Returns:
        Tuple of (valid_count, invalid_count, error_messages)

    Notes:
        Works with both UseCase and Policy objects since both have .evidence
    """
    valid_count = 0
    invalid_count = 0
    errors = []

    for item in items:
        item_id = getattr(item, 'id', 'unknown')

        for i, evidence in enumerate(item.evidence):
            is_valid, error_msg = validate_evidence_quote(
                parsed, evidence, enable_fuzzy, fuzzy_threshold
            )

            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                errors.append(f"{item_id} evidence[{i}]: {error_msg}")

    return valid_count, invalid_count, errors
