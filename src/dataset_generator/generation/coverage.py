"""Coverage enforcement for test cases and dataset examples."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dataset_generator.models.use_case import UseCase
    from dataset_generator.models.test_case import TestCase
    from dataset_generator.models.dataset_example import DatasetExample

logger = logging.getLogger(__name__)


def enforce_coverage(
    use_case_id: str,
    test_cases: list["TestCase"],
    examples: list["DatasetExample"],
    min_test_cases: int = 3,
    min_criteria: int = 3,
    min_policy_ids: int = 1,
) -> tuple[list["TestCase"], list["DatasetExample"], list[str]]:
    """Enforce minimum coverage requirements.

    Validates that test cases and dataset examples meet minimum quality thresholds:
    - Minimum number of test cases per use case
    - 2-3 parameter variation axes per test case (already enforced by Pydantic)
    - Minimum evaluation criteria per example (already enforced by Pydantic)
    - Minimum policy IDs per example (already enforced by Pydantic)
    - Each test case has at least one associated example

    Args:
        use_case_id: Use case identifier to validate against
        test_cases: List of test cases to validate
        examples: List of dataset examples to validate
        min_test_cases: Minimum test cases required (default: 3)
        min_criteria: Minimum evaluation criteria per example (default: 3)
        min_policy_ids: Minimum policy IDs per example (default: 1)

    Returns:
        Tuple of (valid_test_cases, valid_examples, warnings)

    Raises:
        ValueError: If minimum test case count is not met

    Example:
        >>> from dataset_generator.models.test_case import TestCase
        >>> from dataset_generator.models.dataset_example import DatasetExample, InputData, Message
        >>> tcs = [TestCase(id=f'tc_001{i}', use_case_id='uc_001', name=f'TC{i}', description='D', parameter_variation_axes=['a','b']) for i in range(1,4)]
        >>> exs = [DatasetExample(id=f'ex_001{i}', case='test', format='qa', use_case_id='uc_001', test_case_id=f'tc_001{i}', input=InputData(messages=[Message(role='user', content='Q')]), expected_output='A', evaluation_criteria=['c1','c2','c3'], policy_ids=['pol_001']) for i in range(1,4)]
        >>> valid_tcs, valid_exs, warnings = enforce_coverage('uc_001', tcs, exs)
        >>> len(valid_tcs) == 3
        True
    """
    warnings = []

    # Check 1: Minimum test case count
    if len(test_cases) < min_test_cases:
        raise ValueError(
            f"Use case {use_case_id} has only {len(test_cases)} test cases, "
            f"minimum required: {min_test_cases}"
        )

    logger.info(
        f"Use case {use_case_id}: {len(test_cases)} test cases (minimum: {min_test_cases}) ✓"
    )

    # Check 2: Validate parameter variation axes (already enforced by Pydantic)
    for tc in test_cases:
        axes_count = len(tc.parameter_variation_axes)
        if not (2 <= axes_count <= 3):
            warnings.append(
                f"Test case {tc.id} has {axes_count} parameter_variation_axes, "
                f"expected 2-3 (Pydantic should have caught this)"
            )

    # Check 3: Validate evaluation criteria (already enforced by Pydantic)
    for ex in examples:
        criteria_count = len(ex.evaluation_criteria)
        if criteria_count < min_criteria:
            warnings.append(
                f"Example {ex.id} has only {criteria_count} evaluation_criteria, "
                f"minimum: {min_criteria} (Pydantic should have caught this)"
            )

    # Check 4: Validate policy IDs (already enforced by Pydantic)
    for ex in examples:
        policy_count = len(ex.policy_ids)
        if policy_count < min_policy_ids:
            warnings.append(
                f"Example {ex.id} has only {policy_count} policy_ids, "
                f"minimum: {min_policy_ids} (Pydantic should have caught this)"
            )

    # Check 5: Each test case has at least one associated example
    test_case_ids = {tc.id for tc in test_cases}
    example_test_case_ids = {ex.test_case_id for ex in examples}

    orphan_test_cases = test_case_ids - example_test_case_ids
    if orphan_test_cases:
        warnings.append(
            f"Test cases without examples: {sorted(orphan_test_cases)}"
        )

    # Check 6: All examples reference valid test cases
    invalid_references = example_test_case_ids - test_case_ids
    if invalid_references:
        warnings.append(
            f"Examples reference invalid test case IDs: {sorted(invalid_references)}"
        )

    # Log coverage summary
    logger.info(
        f"Coverage validation complete: {len(test_cases)} test cases, "
        f"{len(examples)} examples, {len(warnings)} warnings"
    )

    for warning in warnings:
        logger.warning(f"Coverage: {warning}")

    return test_cases, examples, warnings


def check_referential_integrity(
    use_cases: list["UseCase"],
    test_cases: list["TestCase"],
    examples: list["DatasetExample"],
) -> list[str]:
    """Check all IDs reference valid parents.

    Validates referential integrity across the entire artifact chain:
    - Every test_case.use_case_id matches a use_case.id
    - Every example.test_case_id matches a test_case.id
    - Every example.use_case_id matches a use_case.id
    - Every example.policy_ids item starts with pol_ (format check only)

    Args:
        use_cases: List of use cases
        test_cases: List of test cases
        examples: List of dataset examples

    Returns:
        List of integrity violation messages (empty if all valid)

    Example:
        >>> from dataset_generator.models.use_case import UseCase
        >>> from dataset_generator.models.test_case import TestCase
        >>> from dataset_generator.models.dataset_example import DatasetExample, InputData, Message
        >>> ucs = [UseCase(id='uc_001', name='UC1', description='D', evidence=[])]
        >>> tcs = [TestCase(id='tc_001001', use_case_id='uc_001', name='TC1', description='D', parameter_variation_axes=['a','b'])]
        >>> exs = [DatasetExample(id='ex_001001', case='test', format='qa', use_case_id='uc_001', test_case_id='tc_001001', input=InputData(messages=[Message(role='user', content='Q')]), expected_output='A', evaluation_criteria=['c1','c2','c3'], policy_ids=['pol_001'])]
        >>> issues = check_referential_integrity(ucs, tcs, exs)
        >>> len(issues) == 0
        True
    """
    issues = []

    # Build ID sets
    use_case_ids = {uc.id for uc in use_cases}
    test_case_ids = {tc.id for tc in test_cases}

    # Check 1: Every test_case.use_case_id matches a use_case.id
    for tc in test_cases:
        if tc.use_case_id not in use_case_ids:
            issues.append(
                f"Test case {tc.id} references invalid use_case_id: {tc.use_case_id}"
            )

    # Check 2: Every example.test_case_id matches a test_case.id
    for ex in examples:
        if ex.test_case_id not in test_case_ids:
            issues.append(
                f"Example {ex.id} references invalid test_case_id: {ex.test_case_id}"
            )

    # Check 3: Every example.use_case_id matches a use_case.id
    for ex in examples:
        if ex.use_case_id not in use_case_ids:
            issues.append(
                f"Example {ex.id} references invalid use_case_id: {ex.use_case_id}"
            )

    # Check 4: Every example.policy_ids item starts with pol_
    for ex in examples:
        for policy_id in ex.policy_ids:
            if not policy_id.startswith("pol_"):
                issues.append(
                    f"Example {ex.id} has invalid policy_id format: {policy_id} "
                    f"(must start with pol_)"
                )

    # Log integrity check results
    if issues:
        logger.warning(f"Found {len(issues)} referential integrity issues")
        for issue in issues:
            logger.warning(f"Integrity: {issue}")
    else:
        logger.info("Referential integrity check passed: all IDs valid")

    return issues
