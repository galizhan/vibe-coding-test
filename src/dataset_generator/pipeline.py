"""Pipeline orchestrator for end-to-end dataset generation."""

import logging
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone

from .extraction.markdown_parser import parse_markdown_with_lines
from .extraction.use_case_extractor import extract_use_cases
from .extraction.policy_extractor import extract_policies
from .extraction.evidence_validator import validate_all_evidence
from .generation.orchestrator import orchestrate_generation
from .generation.coverage import enforce_coverage, check_referential_integrity
from .utils.file_writer import write_json_output
from .models import (
    TestCaseList,
    DatasetExampleList,
    RunManifest,
    LLMConfig,
    GenerationCounts,
)
from . import __version__


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
        test_cases_path: Path to generated test_cases.json
        dataset_path: Path to generated dataset.json
        manifest_path: Path to generated run_manifest.json
        use_case_count: Number of use cases extracted
        policy_count: Number of policies extracted
        test_case_count: Number of test cases generated
        dataset_example_count: Number of dataset examples generated
        evidence_valid: Number of valid evidence quotes
        evidence_invalid: Number of invalid evidence quotes
        frameworks_used: List of frameworks used for generation
    """
    use_cases_path: Path
    policies_path: Path
    test_cases_path: Path
    dataset_path: Path
    manifest_path: Path
    use_case_count: int
    policy_count: int
    test_case_count: int
    dataset_example_count: int
    evidence_valid: int
    evidence_invalid: int
    frameworks_used: list[str]


def run_pipeline(config: PipelineConfig) -> PipelineResult:
    """Run the complete extraction and generation pipeline.

    Pipeline steps:
        1. Parse markdown file with line tracking
        2. Extract use cases with LLM structured outputs
        3. Extract policies with LLM structured outputs
        4. Validate all evidence quotes against source
        5. Generate test cases and dataset examples per use case
        6. Enforce coverage and check referential integrity
        7. Write use_cases.json
        8. Write policies.json
        9. Write test_cases.json
        10. Write dataset.json
        11. Generate quality report (INTG-03)
        12. Write run_manifest.json
        13. Print summary and return results

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

    # Step 5: Generate test cases and dataset examples
    logger.info("Step 5: Generating test cases and dataset examples")
    all_test_cases = []
    all_examples = []
    frameworks_used = set()

    for use_case in use_case_list.use_cases:
        logger.info(f"Generating for use case: {use_case.id}")

        # Get policies relevant to this use case (all policies for now)
        test_cases, examples = orchestrate_generation(
            use_case=use_case,
            policies=policy_list.policies,
            document_path=str(config.input_file),
            model=config.model,
            seed=config.seed,
            min_test_cases=config.n_test_cases_per_uc,
        )

        # Enforce coverage per use case
        valid_tcs, valid_exs, warnings = enforce_coverage(
            use_case.id,
            test_cases,
            examples,
            min_test_cases=config.n_test_cases_per_uc,
        )

        all_test_cases.extend(valid_tcs)
        all_examples.extend(valid_exs)

        # Track which frameworks were used (from metadata)
        for tc in valid_tcs:
            if "generator" in tc.metadata:
                frameworks_used.add(tc.metadata["generator"])

        for warning in warnings:
            logger.warning(warning)

    logger.info(
        f"Generated {len(all_test_cases)} test cases and "
        f"{len(all_examples)} dataset examples"
    )

    # Step 6: Check referential integrity
    logger.info("Step 6: Checking referential integrity")
    integrity_issues = check_referential_integrity(
        use_case_list.use_cases, all_test_cases, all_examples
    )
    for issue in integrity_issues:
        logger.warning(f"Integrity: {issue}")

    # Step 7: Write use_cases.json
    logger.info("Step 7: Writing use_cases.json")
    use_cases_path = config.out_dir / "use_cases.json"
    write_json_output(use_case_list, use_cases_path)

    # Step 8: Write policies.json
    logger.info("Step 8: Writing policies.json")
    policies_path = config.out_dir / "policies.json"
    write_json_output(policy_list, policies_path)

    # Step 9: Write test_cases.json
    logger.info("Step 9: Writing test_cases.json")
    test_cases_list = TestCaseList(test_cases=all_test_cases)
    test_cases_path = config.out_dir / "test_cases.json"
    write_json_output(test_cases_list, test_cases_path)

    # Step 10: Write dataset.json
    logger.info("Step 10: Writing dataset.json")
    dataset_list = DatasetExampleList(examples=all_examples)
    dataset_path = config.out_dir / "dataset.json"
    write_json_output(dataset_list, dataset_path)

    # Step 11: Generate quality report (INTG-03)
    logger.info("Step 11: Generating data quality report")
    quality_summary = {}
    quality_report_path = None
    try:
        from .generation.quality_report import generate_quality_report
        quality_summary = generate_quality_report(all_examples, config.out_dir)
        logger.info(f"Quality report: {quality_summary.get('total', 0)} examples analyzed, "
                    f"{quality_summary.get('duplicates', 0)} potential duplicates")
        quality_report_path = config.out_dir / "quality_report.html"
    except Exception as e:
        logger.warning(f"Quality report generation failed (non-blocking): {e}")
        quality_summary = {}

    # Step 12: Write run_manifest.json
    logger.info("Step 12: Writing run_manifest.json")
    manifest = RunManifest(
        input_path=str(config.input_file),
        out_path=str(config.out_dir),
        seed=config.seed,
        timestamp=datetime.now(timezone.utc).isoformat(),
        generator_version=__version__,
        llm=LLMConfig(provider="openai", model=config.model, temperature=0.0),
        frameworks_used=sorted(frameworks_used),
        counts=GenerationCounts(
            use_cases=len(use_case_list.use_cases),
            policies=len(policy_list.policies),
            test_cases=len(all_test_cases),
            dataset_examples=len(all_examples),
        ),
    )
    manifest_path = config.out_dir / "run_manifest.json"
    write_json_output(manifest, manifest_path)

    # Step 13: Print summary
    print(f"\n=== Pipeline Complete ===")
    print(f"Input: {config.input_file.name}")
    print(f"Extracted: {len(use_case_list.use_cases)} use cases, {len(policy_list.policies)} policies")
    print(f"Generated: {len(all_test_cases)} test cases, {len(all_examples)} dataset examples")
    print(f"Frameworks used: {', '.join(sorted(frameworks_used)) if frameworks_used else 'fallback only'}")
    print(f"Evidence validation: {total_valid} valid, {total_invalid} invalid")
    if quality_summary:
        print(f"Quality analysis: {quality_summary.get('duplicates', 0)} duplicates, "
              f"{quality_summary.get('placeholder_count', 0)} placeholders")
    print(f"\nOutput files:")
    print(f"  - {use_cases_path}")
    print(f"  - {policies_path}")
    print(f"  - {test_cases_path}")
    print(f"  - {dataset_path}")
    print(f"  - {manifest_path}")
    if quality_report_path and quality_report_path.exists():
        print(f"  - {quality_report_path}")

    # Return result
    return PipelineResult(
        use_cases_path=use_cases_path,
        policies_path=policies_path,
        test_cases_path=test_cases_path,
        dataset_path=dataset_path,
        manifest_path=manifest_path,
        use_case_count=len(use_case_list.use_cases),
        policy_count=len(policy_list.policies),
        test_case_count=len(all_test_cases),
        dataset_example_count=len(all_examples),
        evidence_valid=total_valid,
        evidence_invalid=total_invalid,
        frameworks_used=sorted(frameworks_used),
    )
