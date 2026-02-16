# Phase 5: Validation & Delivery - Research

**Researched:** 2026-02-16
**Domain:** Data validation, CLI design, LLM platform integration, documentation
**Confidence:** HIGH

## Summary

Phase 5 focuses on validating generated artifacts against the data contract, integrating with Langfuse for dataset upload and experiment tracking, and delivering complete project documentation. This phase builds on the existing Pydantic v2 models and validation infrastructure already in place.

The validation system must check three key areas: (1) Pydantic schema compliance for individual models, (2) referential integrity across models (foreign key-like relationships), and (3) evidence quote matching against source documents (already implemented via fuzzy matching). The Typer CLI framework is already in use and provides built-in support for exit codes and structured command output. Langfuse Python SDK v3 offers straightforward dataset upload via `create_dataset()` and `create_dataset_item()` methods.

**Primary recommendation:** Leverage existing Pydantic validators and evidence validation infrastructure. Build a validation orchestrator that loads all JSON artifacts, validates schema and cross-references, and produces a structured report with proper exit codes. Use Langfuse SDK's simple API for optional dataset upload. Document setup clearly with environment variables in README.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic | 2.0+ | Data validation, model loading | Already in use; v2 provides model_json_schema(), field/model validators, ValidationError handling |
| Typer | 0.12+ | CLI framework | Already in use; built-in exit code support, parameter validation |
| python-dotenv | 1.0+ | Environment variable management | Already in use; standard for .env file loading |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| langfuse | latest (3.x) | Dataset upload, experiment tracking | Optional Langfuse integration (INTG-01) |
| jsonschema | 4.x | JSON Schema validation | If generating/validating against external schemas |
| pathlib | stdlib | Path manipulation | File existence checks, JSON loading |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pydantic validation | jsonschema directly | Pydantic already in use, provides better error messages and type safety |
| Langfuse | LangSmith | LangSmith offers similar features; Langfuse has cleaner Python SDK v3 API |
| Typer exit codes | sys.exit() directly | Typer provides better abstraction and testing support |

**Installation:**
```bash
# Core already installed via pyproject.toml
# Optional Langfuse integration:
pip install langfuse  # Requires Python >=3.10, <4.0
```

## Architecture Patterns

### Recommended Project Structure
```
src/dataset_generator/
├── validation/              # NEW: Validation module
│   ├── __init__.py
│   ├── validator.py         # Main validation orchestrator
│   ├── integrity_checker.py # Cross-model referential integrity
│   └── report_generator.py  # Structured validation reports
├── integration/             # NEW: External integrations
│   ├── __init__.py
│   └── langfuse_client.py   # Langfuse dataset upload
├── cli.py                   # Add validate command
└── models/                  # EXISTING: Already has Pydantic models
```

### Pattern 1: Validation Orchestrator
**What:** Central coordinator that loads all artifacts, runs validation checks, and produces a structured report
**When to use:** For the `validate` command implementation
**Example:**
```python
# Validation orchestrator pattern
from pathlib import Path
from pydantic import ValidationError

class ValidationResult:
    """Structured validation result with counts and errors."""
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.counts: dict[str, int] = {}

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

class DatasetValidator:
    """Orchestrates validation of all generated artifacts."""

    def __init__(self, out_dir: Path):
        self.out_dir = out_dir
        self.result = ValidationResult()

    def validate(self) -> ValidationResult:
        """Run all validation checks."""
        # 1. Check file existence
        self._check_required_files()

        # 2. Load and validate Pydantic models
        use_cases = self._load_and_validate_model(
            "use_cases.json", UseCaseList
        )
        policies = self._load_and_validate_model(
            "policies.json", PolicyList
        )
        test_cases = self._load_and_validate_model(
            "test_cases.json", TestCaseList
        )
        dataset = self._load_and_validate_model(
            "dataset.json", DatasetExampleList
        )

        # 3. Check referential integrity
        if all([use_cases, policies, test_cases, dataset]):
            self._check_referential_integrity(
                use_cases, policies, test_cases, dataset
            )

        # 4. Validate evidence quotes (reuse existing validator)
        if use_cases and policies:
            self._validate_evidence(use_cases, policies)

        return self.result
```

### Pattern 2: Cross-Model Referential Integrity Checking
**What:** Validate foreign-key-like relationships between models (use_case_id, policy_ids, test_case_id)
**When to use:** Part of validation orchestrator
**Example:**
```python
# Referential integrity checking pattern
def check_referential_integrity(
    use_cases: UseCaseList,
    policies: PolicyList,
    test_cases: TestCaseList,
    dataset: DatasetExampleList
) -> list[str]:
    """Check cross-model references are valid.

    Returns list of error messages (empty if all valid).
    """
    errors = []

    # Build lookup sets for O(1) checking
    use_case_ids = {uc.id for uc in use_cases.use_cases}
    policy_ids = {p.id for p in policies.policies}
    test_case_ids = {tc.id for tc in test_cases.test_cases}

    # Check test_case -> use_case references
    for tc in test_cases.test_cases:
        if tc.use_case_id not in use_case_ids:
            errors.append(
                f"TestCase {tc.id} references non-existent "
                f"use_case_id: {tc.use_case_id}"
            )

    # Check dataset_example -> use_case/test_case references
    for ex in dataset.examples:
        if ex.use_case_id not in use_case_ids:
            errors.append(
                f"DatasetExample {ex.id} references non-existent "
                f"use_case_id: {ex.use_case_id}"
            )
        if ex.test_case_id not in test_case_ids:
            errors.append(
                f"DatasetExample {ex.id} references non-existent "
                f"test_case_id: {ex.test_case_id}"
            )

        # Check policy_ids references
        for policy_id in ex.policy_ids:
            if policy_id not in policy_ids:
                errors.append(
                    f"DatasetExample {ex.id} references non-existent "
                    f"policy_id: {policy_id}"
                )

    return errors
```

### Pattern 3: Typer CLI with Exit Codes
**What:** CLI command with proper exit code handling for CI/CD integration
**When to use:** For the `validate` command
**Example:**
```python
# Source: https://typer.tiangolo.com/tutorial/terminating/
from typer import Exit, echo

@app.command("validate")
def validate(
    out: Path = typer.Option(
        ..., "--out", exists=True, dir_okay=True, file_okay=False,
        help="Output directory to validate"
    )
) -> None:
    """Validate generated dataset files for data contract compliance."""
    validator = DatasetValidator(out)
    result = validator.validate()

    # Print summary report
    echo(f"\nValidation Summary for: {out}")
    echo(f"  Use Cases: {result.counts.get('use_cases', 0)}")
    echo(f"  Policies: {result.counts.get('policies', 0)}")
    echo(f"  Test Cases: {result.counts.get('test_cases', 0)}")
    echo(f"  Dataset Examples: {result.counts.get('examples', 0)}")
    echo(f"  Formats: {', '.join(result.counts.get('formats', []))}")

    if result.warnings:
        echo(f"\nWarnings ({len(result.warnings)}):")
        for warning in result.warnings:
            echo(f"  ⚠ {warning}")

    if result.errors:
        echo(f"\nErrors ({len(result.errors)}):", err=True)
        for error in result.errors:
            echo(f"  ✗ {error}", err=True)
        raise Exit(code=1)  # Exit with error code

    echo("\n✓ Validation passed")
    raise Exit(code=0)  # Explicit success exit
```

### Pattern 4: Langfuse Dataset Upload
**What:** Upload generated dataset to Langfuse as dataset items
**When to use:** Optional integration after successful generation
**Example:**
```python
# Source: https://langfuse.com/docs/evaluation/experiments/datasets
from langfuse import Langfuse

def upload_to_langfuse(
    dataset_name: str,
    examples: list[DatasetExample],
    langfuse_config: dict
) -> str:
    """Upload dataset to Langfuse.

    Returns:
        Dataset URL or identifier for tracking
    """
    # Initialize client
    langfuse = Langfuse(
        secret_key=langfuse_config["secret_key"],
        public_key=langfuse_config["public_key"],
        host=langfuse_config.get("host")  # Optional custom host
    )

    # Create dataset
    langfuse.create_dataset(
        name=dataset_name,
        description=f"Generated dataset from {dataset_name}",
        metadata={
            "generator": "dataset-generator",
            "version": "0.1.0",
            "timestamp": datetime.now().isoformat()
        }
    )

    # Upload items
    for example in examples:
        langfuse.create_dataset_item(
            dataset_name=dataset_name,
            input={
                "messages": [m.model_dump() for m in example.input.messages],
                "case": example.case,
                "format": example.format
            },
            expected_output=example.expected_output,
            metadata={
                "use_case_id": example.use_case_id,
                "test_case_id": example.test_case_id,
                "policy_ids": example.policy_ids,
                "evaluation_criteria": example.evaluation_criteria,
                **example.metadata
            }
        )

    # Flush to ensure all items are uploaded
    langfuse.flush()

    return f"Dataset '{dataset_name}' uploaded successfully"
```

### Anti-Patterns to Avoid
- **Loading all JSON with json.load():** Use Pydantic model parsing to get validation for free
- **Catching ValidationError too broadly:** Catch and report specific validation failures
- **Hardcoded file paths:** Use Path objects and make paths configurable
- **Silent failures:** Always report what failed and where
- **Blocking on optional integrations:** Langfuse upload should not block validation

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Data model validation | Custom validators, manual type checking | Pydantic v2 field/model validators | Handles nested validation, type coercion, detailed error messages |
| CLI argument parsing | argparse with manual help | Typer with type hints | Auto-generates help, validates types, better UX |
| Evidence quote validation | Custom string comparison | Existing `evidence_validator.py` with fuzzy matching | Already handles line numbering, whitespace normalization, similarity scoring |
| JSON Schema generation | Manual schema writing | `Model.model_json_schema()` | Auto-generates from Pydantic models, stays in sync |
| Environment variable loading | os.getenv() everywhere | python-dotenv + validated config class | Centralized, validated, type-safe |
| Exit codes | Magic numbers | typer.Exit(code=X) with constants | Self-documenting, testable |

**Key insight:** Pydantic v2's validation is extremely thorough - ValidationError already contains all info needed for reporting. Don't rebuild what's already there.

## Common Pitfalls

### Pitfall 1: Not Loading Models for Validation
**What goes wrong:** Loading JSON with `json.load()` and manually checking fields instead of using Pydantic
**Why it happens:** Developers think validation is separate from loading
**How to avoid:** Always load via Pydantic models: `UseCaseList.model_validate_json(json_text)`
**Warning signs:** Manual field checks like `if "id" not in data or not data["id"].startswith("uc_")`

### Pitfall 2: Forgetting to Check Both Directions
**What goes wrong:** Checking that dataset examples reference valid test_cases, but not checking for orphaned test_cases
**Why it happens:** Thinking of validation as "does this reference exist?" instead of "is the data graph complete?"
**How to avoid:** Check both directions: forward references (FK validation) and backward coverage (are there test_cases with no examples?)
**Warning signs:** Passing validation but having low coverage or missing expected data

### Pitfall 3: Validation Errors Without Context
**What goes wrong:** Reporting "ValidationError" without saying which file, which model, or which field failed
**Why it happens:** Catching exceptions at too high a level
**How to avoid:** Catch ValidationError per-file and include file path, model type, and field path in error message
**Warning signs:** Users can't tell what to fix from error messages

### Pitfall 4: Evidence Validation Blocking Validation Command
**What goes wrong:** Evidence validation failures cause validation to error out, but requirements say evidence validation should warn
**Why it happens:** Not distinguishing between structural errors (fail) and evidence mismatches (warn)
**How to avoid:** Evidence validation adds to warnings, not errors. Exit code 0 if only warnings exist.
**Warning signs:** Validation fails on fuzzy match evidence when it should pass with warnings

### Pitfall 5: Hardcoding Langfuse Credentials
**What goes wrong:** Putting API keys in code or requiring them for non-Langfuse operations
**Why it happens:** Not treating Langfuse as truly optional
**How to avoid:** Check for credentials before attempting upload; skip silently or with info message if not present
**Warning signs:** Validation fails when LANGFUSE_* env vars not set

### Pitfall 6: Not Flushing Langfuse Client
**What goes wrong:** Dataset upload appears to succeed but items don't appear in Langfuse UI
**Why it happens:** Langfuse SDK batches uploads; need to call `flush()` to ensure completion
**How to avoid:** Always call `langfuse.flush()` after uploading dataset items
**Warning signs:** Intermittent "missing items" when checking Langfuse immediately after upload

## Code Examples

Verified patterns from official sources:

### Loading and Validating Pydantic Models
```python
# Source: https://docs.pydantic.dev/latest/concepts/models/
from pathlib import Path
from pydantic import ValidationError

def load_and_validate(
    file_path: Path,
    model_class: type[BaseModel]
) -> tuple[BaseModel | None, list[str]]:
    """Load JSON file and validate against Pydantic model.

    Returns:
        Tuple of (model_instance, error_messages)
    """
    errors = []

    if not file_path.exists():
        errors.append(f"File not found: {file_path}")
        return None, errors

    try:
        json_text = file_path.read_text()
        model_instance = model_class.model_validate_json(json_text)
        return model_instance, []
    except ValidationError as e:
        # Extract field paths and messages from Pydantic error
        for error in e.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            errors.append(
                f"{file_path.name}: {field_path}: {error['msg']}"
            )
        return None, errors
    except Exception as e:
        errors.append(f"{file_path.name}: {str(e)}")
        return None, errors
```

### Typer Exit Code Best Practices
```python
# Source: https://typer.tiangolo.com/tutorial/terminating/
import typer
from enum import IntEnum

class ExitCode(IntEnum):
    """Standard exit codes for validation command."""
    SUCCESS = 0
    VALIDATION_ERROR = 1
    FILE_NOT_FOUND = 2
    INVALID_CONFIG = 3

@app.command("validate")
def validate(out: Path) -> None:
    """Validate generated dataset files."""
    if not out.exists():
        typer.echo(f"Error: Directory not found: {out}", err=True)
        raise typer.Exit(code=ExitCode.FILE_NOT_FOUND)

    # Run validation...

    if has_errors:
        typer.echo("Validation failed", err=True)
        raise typer.Exit(code=ExitCode.VALIDATION_ERROR)

    typer.echo("Validation passed")
    # Exit code 0 is implicit, but can be explicit:
    raise typer.Exit(code=ExitCode.SUCCESS)
```

### README Environment Variables Section
```markdown
# Source: Best practices from multiple Python projects

## Environment Variables

This project uses environment variables for configuration. Create a `.env` file in the project root:

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional: Langfuse Integration
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com  # Optional, defaults to cloud
```

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for LLM generation | `sk-proj-...` |

### Optional Variables (Langfuse Integration)

| Variable | Description | Default |
|----------|-------------|---------|
| `LANGFUSE_PUBLIC_KEY` | Langfuse public API key | None (integration disabled) |
| `LANGFUSE_SECRET_KEY` | Langfuse secret API key | None (integration disabled) |
| `LANGFUSE_HOST` | Langfuse instance URL | `https://cloud.langfuse.com` |

**Note:** Langfuse integration is optional. If credentials are not provided, dataset generation and validation will still work normally.
```

### Generating JSON Schema from Pydantic Models
```python
# Source: https://docs.pydantic.dev/latest/concepts/json_schema/
from dataset_generator.models import (
    UseCaseList, PolicyList, TestCaseList, DatasetExampleList
)

def generate_schemas(output_dir: Path) -> None:
    """Generate JSON Schema files for all models."""
    schemas = {
        "schema_use_cases.json": UseCaseList,
        "schema_policies.json": PolicyList,
        "schema_test_cases.json": TestCaseList,
        "schema_dataset.json": DatasetExampleList,
    }

    for filename, model_class in schemas.items():
        schema = model_class.model_json_schema()
        schema_path = output_dir / filename
        schema_path.write_text(
            json.dumps(schema, indent=2)
        )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual JSON validation | Pydantic model_validate_json() | Pydantic v2 (2023) | Auto validation, better errors |
| argparse CLI | Typer with type hints | Typer 0.9+ (2023) | Cleaner code, auto help |
| Langfuse SDK v2 | Langfuse SDK v3 | June 2025 | Simplified API, better async support |
| setup.py | pyproject.toml | PEP 621 (2021+) | Declarative, tool-agnostic |

**Deprecated/outdated:**
- `setup.py` for package metadata - Use pyproject.toml [project] table instead
- Pydantic v1 `Config` class - Use v2 `model_config = ConfigDict(...)` instead
- `pydantic.parse_obj_as()` - Use `model_validate()` in v2

## Open Questions

1. **Should validation generate JSON Schema files for external validators?**
   - What we know: Pydantic can generate schemas via `model_json_schema()`
   - What's unclear: Whether tz.md expects schema files in output or just for reference
   - Recommendation: Generate schemas to `out/*/schemas/` as bonus; not required for MVP

2. **How should validation handle missing optional Langfuse credentials?**
   - What we know: Integration is optional per tz.md
   - What's unclear: Silent skip vs. info message vs. warning
   - Recommendation: Print info message "Langfuse integration skipped (no credentials)" but don't warn/error

3. **Should validation check for minimum coverage (5+ use cases, etc.)?**
   - What we know: Requirements specify minimum counts
   - What's unclear: Whether validation should enforce these or just report
   - Recommendation: Validation reports counts but doesn't enforce minimums (that's generation's job)

## Sources

### Primary (HIGH confidence)
- [Pydantic v2 Validators Documentation](https://docs.pydantic.dev/latest/concepts/validators/) - Field and model validation patterns
- [Pydantic v2 Models Documentation](https://docs.pydantic.dev/latest/concepts/models/) - Model loading and validation
- [Pydantic v2 JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/) - Schema generation
- [Typer Terminating Documentation](https://typer.tiangolo.com/tutorial/terminating/) - Exit codes and error handling
- [Langfuse Datasets Documentation](https://langfuse.com/docs/evaluation/experiments/datasets) - Dataset creation and upload API
- [Langfuse Python SDK Setup](https://langfuse.com/docs/observability/sdk/python/setup) - Installation and configuration
- [Python Packaging Guide: pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) - Package configuration

### Secondary (MEDIUM confidence)
- [Pydantic Complete Guide 2026](https://devtoolbox.dedyn.io/blog/pydantic-complete-guide) - Validation patterns and best practices
- [Python CLI Tools Complete Guide 2026](https://devtoolbox.dedyn.io/blog/python-click-typer-cli-guide) - Typer CLI best practices
- [Typer CLI Best Practices - Project Rules](https://www.projectrules.ai/rules/typer) - Typer coding standards
- [Python Environment Variables Best Practices 2026](https://purpletutor.com/python-virtual-environment-best-practices/) - Environment setup
- [Python Environment Variables Guide](https://dagster.io/blog/python-environment-variables) - .env file best practices
- [Langfuse Python SDK GitHub](https://github.com/langfuse/langfuse-python) - SDK source and examples

### Tertiary (LOW confidence)
- [Data Quality Referential Integrity](https://dqops.com/docs/categories-of-data-quality-checks/how-to-detect-data-referential-integrity-issues/) - Referential integrity patterns
- [Python Data Validation Framework](https://oneuptime.com/blog/post/2026-01-25-data-validation-framework-python/view) - Validation framework design
- [How to Build Data Validation Framework](https://oneuptime.com/blog/post/2026-01-25-data-validation-framework-python/view) - Severity levels and error handling

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in use or standard choices (Pydantic v2, Typer, langfuse)
- Architecture: HIGH - Patterns verified with official Pydantic v2 and Typer docs
- Pitfalls: MEDIUM-HIGH - Based on common Python validation mistakes and evidence validator already in codebase
- Langfuse integration: MEDIUM - Official docs clear but integration optional per requirements

**Research date:** 2026-02-16
**Valid until:** 2026-03-16 (30 days - stable libraries)

**Key prior decisions honored:**
- Pydantic v2 syntax throughout (already in codebase)
- OpenAI as LLM provider (generation only, not validation)
- Typer for CLI (already in use)
- Evidence validation warns but doesn't fail (per Phase 4 decisions)
- Format adapters as primary generation path (validation consumes their output)
