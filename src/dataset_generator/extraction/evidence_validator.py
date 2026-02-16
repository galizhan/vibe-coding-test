"""Evidence validation against source text."""

from dataset_generator.models import Evidence
from .markdown_parser import ParsedMarkdown


def validate_evidence_quote(
    parsed: ParsedMarkdown,
    evidence: Evidence
) -> tuple[bool, str]:
    """Validate that evidence quote matches source lines exactly.

    Args:
        parsed: ParsedMarkdown instance with source lines
        evidence: Evidence instance to validate

    Returns:
        Tuple of (is_valid, error_message)
        - (True, "") if quote matches exactly
        - (False, "description") if quote doesn't match

    Notes:
        - Converts 1-based line numbers to 0-based array indices
        - Normalizes whitespace (strips trailing whitespace per line)
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

    # Normalize both sides for comparison
    # Strip trailing whitespace per line, normalize line endings
    def normalize(text: str) -> str:
        lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        return '\n'.join(line.rstrip() for line in lines)

    normalized_actual = normalize(actual_text)
    normalized_quote = normalize(evidence.quote)

    # Compare
    if normalized_actual == normalized_quote:
        return True, ""

    # Build helpful error message
    return False, (
        f"Quote mismatch at lines {evidence.line_start}-{evidence.line_end}:\n"
        f"Expected: {normalized_actual[:100]!r}...\n"
        f"Got:      {normalized_quote[:100]!r}..."
    )


def validate_all_evidence(
    parsed: ParsedMarkdown,
    items: list
) -> tuple[int, int, list[str]]:
    """Validate evidence for all items (UseCases or Policies).

    Args:
        parsed: ParsedMarkdown instance with source lines
        items: List of objects with .evidence attribute (UseCase or Policy)

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
            is_valid, error_msg = validate_evidence_quote(parsed, evidence)

            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                errors.append(f"{item_id} evidence[{i}]: {error_msg}")

    return valid_count, invalid_count, errors
