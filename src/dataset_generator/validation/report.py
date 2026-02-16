"""Validation report structures."""

import sys
from typing import Any

import typer


class ValidationResult:
    """Structured validation report with counts, errors, and warnings."""

    def __init__(self) -> None:
        """Initialize empty validation result."""
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.counts: dict[str, int] = {}
        self.formats: list[str] = []

    @property
    def is_valid(self) -> bool:
        """Return True if no errors exist."""
        return len(self.errors) == 0

    def add_error(self, msg: str) -> None:
        """Add an error message."""
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        """Add a warning message."""
        self.warnings.append(msg)

    def set_count(self, key: str, val: int) -> None:
        """Set a count value."""
        self.counts[key] = val

    def print_report(self) -> None:
        """Print formatted validation summary to stdout."""
        typer.echo("\n" + "=" * 60)
        typer.echo("VALIDATION REPORT")
        typer.echo("=" * 60)

        # Print counts
        if self.counts:
            typer.echo("\nArtifact Counts:")
            for key, val in sorted(self.counts.items()):
                typer.echo(f"  {key}: {val}")

        # Print formats if available
        if self.formats:
            typer.echo(f"\nDetected Formats: {', '.join(sorted(set(self.formats)))}")

        # Print warnings
        if self.warnings:
            typer.echo(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                typer.echo(f"  ⚠ {warning}")

        # Print errors to stderr
        if self.errors:
            typer.echo(f"\nErrors ({len(self.errors)}):", err=True)
            for error in self.errors:
                typer.echo(f"  ✗ {error}", err=True)
        else:
            typer.echo("\n✓ All validation checks passed")

        typer.echo("=" * 60)
