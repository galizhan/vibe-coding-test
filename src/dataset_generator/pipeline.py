"""Pipeline orchestrator for end-to-end dataset generation."""

import logging
from dataclasses import dataclass
from pathlib import Path

from .extraction.markdown_parser import parse_markdown_with_lines
from .extraction.use_case_extractor import extract_use_cases
from .extraction.policy_extractor import extract_policies
from .extraction.evidence_validator import validate_all_evidence
from .utils.file_writer import write_json_output


logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for pipeline execution.

    Attributes:
        input_file: Path to input markdown file
        out_dir: Output directory for JSON files
        seed: Random seed for reproducibility (optional)
        model: OpenAI model name
        n_use_cases: Minimum number of use cases to extract
        n_test_cases_per_uc: Test cases per use case (for future phases)
        n_examples_per_tc: Examples per test case (for future phases)
    """
    input_file: Path
    out_dir: Path
    seed: int | None
    model: str
    n_use_cases: int
    n_test_cases_per_uc: int
    n_examples_per_tc: int


@dataclass
class PipelineResult:
    """Result of pipeline execution.

    Attributes:
        use_cases_path: Path to generated use_cases.json
        policies_path: Path to generated policies.json
        use_case_count: Number of use cases extracted
        policy_count: Number of policies extracted
        evidence_valid: Number of valid evidence quotes
        evidence_invalid: Number of invalid evidence quotes
    """
    use_cases_path: Path
    policies_path: Path
    use_case_count: int
    policy_count: int
    evidence_valid: int
    evidence_invalid: int


def run_pipeline(config: PipelineConfig) -> PipelineResult:
    """Run the complete extraction pipeline.

    Pipeline steps:
        1. Parse markdown file with line tracking
        2. Extract use cases with LLM structured outputs
        3. Extract policies with LLM structured outputs
        4. Validate all evidence quotes against source
        5. Write use_cases.json
        6. Write policies.json
        7. Print summary and return results

    Args:
        config: PipelineConfig with all settings

    Returns:
        PipelineResult with paths and counts

    Raises:
        FileNotFoundError: If input file doesn't exist
        OpenAI API errors: If LLM calls fail
    """
    logger.info(f"Starting pipeline for {config.input_file.name}")
    logger.info(f"Model: {config.model}, Seed: {config.seed}")

    # Step 1: Parse markdown
    logger.info("Step 1: Parsing markdown with line tracking")
    parsed = parse_markdown_with_lines(config.input_file)
    logger.info(f"Parsed {len(parsed.lines)} lines from {config.input_file.name}")

    # Step 2: Extract use cases
    logger.info("Step 2: Extracting use cases")
    use_case_list = extract_use_cases(
        parsed,
        model=config.model,
        seed=config.seed,
        min_use_cases=config.n_use_cases
    )

    # Step 3: Extract policies
    logger.info("Step 3: Extracting policies")
    policy_list = extract_policies(
        parsed,
        model=config.model,
        seed=config.seed
    )

    # Step 4: Validate evidence (already done in extractors, but collect totals)
    logger.info("Step 4: Validating all evidence")
    uc_valid, uc_invalid, uc_errors = validate_all_evidence(parsed, use_case_list.use_cases)
    pol_valid, pol_invalid, pol_errors = validate_all_evidence(parsed, policy_list.policies)

    total_valid = uc_valid + pol_valid
    total_invalid = uc_invalid + pol_invalid

    # Log validation summary
    if total_invalid > 0:
        logger.warning(
            f"Evidence validation: {total_valid} valid, {total_invalid} invalid"
        )
        for error in uc_errors + pol_errors:
            logger.warning(f"  {error}")
    else:
        logger.info(f"Evidence validation: all {total_valid} quotes valid")

    # Step 5: Write use_cases.json
    logger.info("Step 5: Writing use_cases.json")
    use_cases_path = config.out_dir / "use_cases.json"
    write_json_output(use_case_list, use_cases_path)

    # Step 6: Write policies.json
    logger.info("Step 6: Writing policies.json")
    policies_path = config.out_dir / "policies.json"
    write_json_output(policy_list, policies_path)

    # Step 7: Print summary
    print(f"\n=== Pipeline Complete ===")
    print(f"Input: {config.input_file.name}")
    print(f"Extracted: {len(use_case_list.use_cases)} use cases, {len(policy_list.policies)} policies")
    print(f"Evidence validation: {total_valid} valid, {total_invalid} invalid")
    print(f"\nOutput files:")
    print(f"  - {use_cases_path}")
    print(f"  - {policies_path}")

    # Return result
    return PipelineResult(
        use_cases_path=use_cases_path,
        policies_path=policies_path,
        use_case_count=len(use_case_list.use_cases),
        policy_count=len(policy_list.policies),
        evidence_valid=total_valid,
        evidence_invalid=total_invalid
    )
