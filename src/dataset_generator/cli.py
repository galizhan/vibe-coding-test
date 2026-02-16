"""Command-line interface for the dataset generator."""

import logging
import os
import sys
from pathlib import Path

import typer
from dotenv import load_dotenv
from openai import OpenAIError

from .pipeline import PipelineConfig, run_pipeline

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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

    try:
        # Create pipeline configuration
        config = PipelineConfig(
            input_file=input_file,
            out_dir=out,
            seed=seed,
            model=model,
            n_use_cases=n_use_cases,
            n_test_cases_per_uc=n_test_cases_per_uc,
            n_examples_per_tc=n_examples_per_tc
        )

        # Run the pipeline
        result = run_pipeline(config)

        # Print summary
        typer.echo(f"\nGenerated {result.use_case_count} use cases, {result.policy_count} policies")

        if result.evidence_invalid > 0:
            typer.echo(
                f"Warning: {result.evidence_invalid} evidence quotes failed validation",
                err=True
            )
        else:
            typer.echo(f"All {result.evidence_valid} evidence quotes validated successfully")

        typer.echo(f"\nOutput files:")
        typer.echo(f"  - {result.use_cases_path}")
        typer.echo(f"  - {result.policies_path}")

    except OpenAIError as e:
        typer.echo(f"OpenAI API error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        sys.exit(1)


@app.command("validate")
def validate() -> None:
    """Validate generated dataset files."""
    typer.echo("Not yet implemented")
