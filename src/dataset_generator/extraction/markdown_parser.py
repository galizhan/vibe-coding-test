"""Markdown parser with line tracking for evidence extraction."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParsedMarkdown:
    """Parsed markdown file with line tracking.

    Attributes:
        full_text: Complete file contents as a single string
        lines: List of lines (0-indexed internally, evidence uses 1-based)
        file_path: Path to the source file
    """
    full_text: str
    lines: list[str]
    file_path: Path


def parse_markdown_with_lines(file_path: Path) -> ParsedMarkdown:
    """Parse markdown file with line tracking.

    Reads the file, normalizes line endings, and returns structured data.

    Args:
        file_path: Path to the markdown file

    Returns:
        ParsedMarkdown with full_text, lines list, and file_path

    Notes:
        - Lines are stored 0-indexed internally
        - Evidence uses 1-based line numbers (line 1 = lines[0])
        - Normalizes \r\n and \r to \n for cross-platform compatibility
    """
    with open(file_path, encoding='utf-8') as f:
        content = f.read()

    # Normalize line endings
    content = content.replace('\r\n', '\n').replace('\r', '\n')

    # Split into lines
    lines = content.split('\n')

    return ParsedMarkdown(
        full_text=content,
        lines=lines,
        file_path=file_path
    )


def get_numbered_text(parsed: ParsedMarkdown) -> str:
    """Return text with line numbers prepended for LLM context.

    Args:
        parsed: ParsedMarkdown instance

    Returns:
        String with format "1: line content\\n2: line content\\n..."

    Notes:
        This helps the LLM see line numbers when extracting evidence.
        Line numbers are 1-based to match text editor conventions.
    """
    numbered_lines = [
        f"{i + 1}: {line}"
        for i, line in enumerate(parsed.lines)
    ]
    return '\n'.join(numbered_lines)
