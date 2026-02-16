"""Command-line interface for the dataset generator."""

import os
import sys
from pathlib import Path

import typer
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = typer.Typer(help="Generate synthetic datasets from requirements documents")


@app.command("generate")
def generate(
    input_file: Path = typer.Option(
        ...,
        "--input",
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Input markdown file",
    ),
    out: Path = typer.Option(
        Path("./out"), "--out", help="Output directory"
    ),
    seed: int = typer.Option(
        None, "--seed", help="Random seed for reproducibility"
    ),
    n_use_cases: int = typer.Option(
        5, "--n-use-cases", min=1, help="Minimum number of use cases to extract"
    ),
    n_test_cases_per_uc: int = typer.Option(
        3, "--n-test-cases-per-uc", min=1, help="Test cases per use case"
    ),
    n_examples_per_tc: int = typer.Option(
        1, "--n-examples-per-tc", min=1, help="Examples per test case"
    ),
    model: str = typer.Option(
        "gpt-4o-mini", "--model", help="OpenAI model name"
    ),
) -> None:
    """Generate a synthetic dataset from a requirements document."""
    # Check for OPENAI_API_KEY
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        typer.echo(
            "Error: OPENAI_API_KEY environment variable is not set.", err=True
        )
        typer.echo(
            "Please set it in your .env file or environment.", err=True
        )
        sys.exit(1)

    # Create output directory if it doesn't exist
    out.mkdir(parents=True, exist_ok=True)

    # Placeholder implementation
    typer.echo(f"Input file: {input_file}")
    typer.echo(f"Output directory: {out}")
    typer.echo(f"Model: {model}")
    typer.echo(f"Seed: {seed}")
    typer.echo(f"Use cases: {n_use_cases}")
    typer.echo(f"Test cases per UC: {n_test_cases_per_uc}")
    typer.echo(f"Examples per TC: {n_examples_per_tc}")
    typer.echo("\nNot yet implemented")


@app.command("validate")
def validate() -> None:
    """Validate generated dataset files."""
    typer.echo("Not yet implemented")
