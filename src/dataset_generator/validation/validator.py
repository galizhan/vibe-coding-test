"""Main validation orchestrator for dataset artifacts."""

import logging
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from dataset_generator.models import (
    UseCaseList,
    PolicyList,
    TestCaseList,
    DatasetExampleList,
)
from .report import ValidationResult
from .integrity_checker import check_referential_integrity

logger = logging.getLogger(__name__)


class DatasetValidator:
    """Orchestrates validation of generated dataset artifacts."""

    def __init__(self, out_dir: Path) -> None:
        """Initialize validator with output directory.

        Args:
            out_dir: Path to directory containing generated JSON files
        """
        self.out_dir = out_dir
        self.result = ValidationResult()

        # Store loaded models for potential reuse (e.g., Langfuse upload)
        self.use_cases: Optional[UseCaseList] = None
        self.policies: Optional[PolicyList] = None
        self.test_cases: Optional[TestCaseList] = None
        self.examples: Optional[DatasetExampleList] = None

    def validate(self) -> ValidationResult:
        """Run all validation checks.

        Validation steps:
        1. Check required files exist
        2. Load each file via Pydantic model_validate_json
        3. Check referential integrity across models
        4. Record counts and formats

        Returns:
            ValidationResult with errors, warnings, and counts
        """
        # Step 1: Check required files exist
        required_files = {
            "use_cases.json": UseCaseList,
            "policies.json": PolicyList,
            "test_cases.json": TestCaseList,
            "dataset.json": DatasetExampleList,
        }

        file_paths = {}
        for filename in required_files.keys():
            file_path = self.out_dir / filename
            if not file_path.exists():
                self.result.add_error(f"Missing required file: {filename}")
            else:
                file_paths[filename] = file_path

        # If any files missing, stop early
        if not self.result.is_valid:
            return self.result

        # Step 2: Load each file via Pydantic model_validate_json
        try:
            self.use_cases = UseCaseList.model_validate_json(
                file_paths["use_cases.json"].read_text(encoding="utf-8")
            )
            logger.info(f"Loaded {len(self.use_cases.use_cases)} use cases")
        except ValidationError as e:
            self._add_validation_errors("use_cases.json", e)
        except Exception as e:
            self.result.add_error(f"Failed to load use_cases.json: {e}")

        try:
            self.policies = PolicyList.model_validate_json(
                file_paths["policies.json"].read_text(encoding="utf-8")
            )
            logger.info(f"Loaded {len(self.policies.policies)} policies")
        except ValidationError as e:
            self._add_validation_errors("policies.json", e)
        except Exception as e:
            self.result.add_error(f"Failed to load policies.json: {e}")

        try:
            self.test_cases = TestCaseList.model_validate_json(
                file_paths["test_cases.json"].read_text(encoding="utf-8")
            )
            logger.info(f"Loaded {len(self.test_cases.test_cases)} test cases")
        except ValidationError as e:
            self._add_validation_errors("test_cases.json", e)
        except Exception as e:
            self.result.add_error(f"Failed to load test_cases.json: {e}")

        try:
            self.examples = DatasetExampleList.model_validate_json(
                file_paths["dataset.json"].read_text(encoding="utf-8")
            )
            logger.info(f"Loaded {len(self.examples.examples)} dataset examples")
        except ValidationError as e:
            self._add_validation_errors("dataset.json", e)
        except Exception as e:
            self.result.add_error(f"Failed to load dataset.json: {e}")

        # If any models failed to load, stop early
        if not all([self.use_cases, self.policies, self.test_cases, self.examples]):
            return self.result

        # Step 3: Check referential integrity across models
        integrity_errors = check_referential_integrity(
            self.use_cases,
            self.policies,
            self.test_cases,
            self.examples,
        )
        for error in integrity_errors:
            self.result.add_error(error)

        # Step 4: Record counts
        self.result.set_count("use_cases", len(self.use_cases.use_cases))
        self.result.set_count("policies", len(self.policies.policies))
        self.result.set_count("test_cases", len(self.test_cases.test_cases))
        self.result.set_count("examples", len(self.examples.examples))

        # Record detected formats
        self.result.formats = sorted(set(ex.format for ex in self.examples.examples))

        logger.info(
            f"Validation complete: {len(self.result.errors)} errors, "
            f"{len(self.result.warnings)} warnings"
        )

        return self.result

    def _add_validation_errors(self, filename: str, error: ValidationError) -> None:
        """Add Pydantic validation errors with file context.

        Args:
            filename: Name of file that failed validation
            error: Pydantic ValidationError with field-level details
        """
        for err in error.errors():
            loc = " -> ".join(str(x) for x in err["loc"])
            msg = err["msg"]
            self.result.add_error(f"{filename}: {loc}: {msg}")
