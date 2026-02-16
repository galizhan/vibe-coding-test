"""Command-line interface for the dataset generator."""

import logging
import os
import sys
from pathlib import Path

import typer
from dotenv import load_dotenv
from openai import OpenAIError

from .pipeline import PipelineConfig, run_pipeline
from .models.dataset_example import DatasetExampleList
from .validation import DatasetValidator

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
        typer.echo(f"\nExtracted: {result.use_case_count} use cases, {result.policy_count} policies")
        typer.echo(f"Generated: {result.test_case_count} test cases, {result.dataset_example_count} dataset examples")
        typer.echo(f"Frameworks used: {', '.join(result.frameworks_used) if result.frameworks_used else 'fallback only'}")

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
        typer.echo(f"  - {result.test_cases_path}")
        typer.echo(f"  - {result.dataset_path}")
        typer.echo(f"  - {result.manifest_path}")

    except OpenAIError as e:
        typer.echo(f"OpenAI API error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        sys.exit(1)


@app.command("validate")
def validate(
    out: Path = typer.Option(
        ...,
        "--out",
        exists=True,
        dir_okay=True,
        file_okay=False,
        help="Output directory to validate",
    ),
) -> None:
    """Validate generated dataset files.

    Checks:
    - All required JSON files exist
    - Schema compliance via Pydantic models
    - Referential integrity across models
    - Policy ID references point to actual policies

    Exit codes:
    - 0: All validation checks passed
    - 1: Validation errors found
    """
    # Create validator and run checks
    validator = DatasetValidator(out)
    result = validator.validate()

    # Print report
    result.print_report()

    # Exit with appropriate code
    if result.is_valid:
        typer.echo("\n✓ Validation passed")
        raise typer.Exit(code=0)
    else:
        typer.echo(f"\n✗ Validation failed with {len(result.errors)} error(s)", err=True)
        raise typer.Exit(code=1)


@app.command("upload")
def upload(
    out: Path = typer.Option(
        ...,
        "--out",
        exists=True,
        dir_okay=True,
        file_okay=False,
        help="Output directory with dataset.json",
    ),
    dataset_name: str = typer.Option(
        ..., "--dataset-name", help="Name for the Langfuse dataset"
    ),
    host: str = typer.Option(
        None, "--langfuse-host", help="Custom Langfuse host URL"
    ),
) -> None:
    """Upload generated dataset to Langfuse for experiment tracking."""
    # Check for Langfuse credentials
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")

    if not public_key or not secret_key:
        typer.echo(
            "Error: Langfuse credentials not configured. "
            "Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in your .env file.",
            err=True,
        )
        sys.exit(1)

    # Use LANGFUSE_HOST env var as fallback if --langfuse-host not provided
    if host is None:
        host = os.getenv("LANGFUSE_HOST")

    # Load dataset.json
    dataset_path = out / "dataset.json"
    if not dataset_path.exists():
        typer.echo(
            f"Error: dataset.json not found in {out}",
            err=True,
        )
        sys.exit(1)

    try:
        dataset_json = dataset_path.read_text(encoding="utf-8")
        dataset = DatasetExampleList.model_validate_json(dataset_json)
    except Exception as e:
        typer.echo(f"Error loading dataset.json: {e}", err=True)
        sys.exit(1)

    # Upload to Langfuse
    try:
        from .integration.langfuse_client import upload_to_langfuse

        result = upload_to_langfuse(
            dataset_name=dataset_name,
            examples=dataset.examples,
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )

        typer.echo(f"\nSuccessfully uploaded dataset to Langfuse:")
        typer.echo(f"  Dataset name: {result['dataset_name']}")
        typer.echo(f"  Items uploaded: {result['items_uploaded']}")
        typer.echo(f"  Status: {result['status']}")

    except ImportError as e:
        typer.echo(f"Error: {e}", err=True)
        typer.echo(
            "\nTo use Langfuse integration, install with: pip install dataset-generator[langfuse]",
            err=True,
        )
        sys.exit(1)
    except Exception as e:
        typer.echo(f"Error uploading to Langfuse: {e}", err=True)
        sys.exit(1)
