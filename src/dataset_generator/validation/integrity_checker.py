"""Cross-model referential integrity checking."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dataset_generator.models import UseCaseList, PolicyList, TestCaseList, DatasetExampleList


def check_referential_integrity(
    use_cases: "UseCaseList",
    policies: "PolicyList",
    test_cases: "TestCaseList",
    examples: "DatasetExampleList",
) -> list[str]:
    """Check referential integrity across all artifact types.

    Validates that all ID references point to existing entities:
    - test_case.use_case_id -> use_case.id
    - example.use_case_id -> use_case.id
    - example.test_case_id -> test_case.id
    - example.policy_ids items -> policy.id

    This differs from coverage.py:check_referential_integrity which only
    checks policy_id format (pol_ prefix). This function validates against
    the ACTUAL set of loaded policy IDs.

    Args:
        use_cases: Loaded UseCaseList
        policies: Loaded PolicyList
        test_cases: Loaded TestCaseList
        examples: Loaded DatasetExampleList

    Returns:
        List of error messages (empty if all valid)

    Example:
        >>> from dataset_generator.models import UseCaseList, PolicyList, TestCaseList, DatasetExampleList
        >>> from dataset_generator.models import UseCase, Policy, TestCase, DatasetExample, InputData, Message
        >>> ucs = UseCaseList(use_cases=[UseCase(id='uc_001', name='UC1', description='D', evidence=[])])
        >>> pols = PolicyList(policies=[Policy(id='pol_001', name='P1', description='D', type='must', evidence=[])])
        >>> tcs = TestCaseList(test_cases=[TestCase(id='tc_001', use_case_id='uc_001', name='TC1', description='D', parameter_variation_axes=['a','b'])])
        >>> exs = DatasetExampleList(examples=[DatasetExample(id='ex_001', case='test', format='qa', use_case_id='uc_001', test_case_id='tc_001', input=InputData(messages=[Message(role='user', content='Q')]), expected_output='A', evaluation_criteria=['c1','c2','c3'], policy_ids=['pol_001'])])
        >>> errors = check_referential_integrity(ucs, pols, tcs, exs)
        >>> len(errors) == 0
        True
    """
    errors = []

    # Build lookup sets
    use_case_ids = {uc.id for uc in use_cases.use_cases}
    policy_ids = {pol.id for pol in policies.policies}
    test_case_ids = {tc.id for tc in test_cases.test_cases}

    # Check 1: test_case.use_case_id -> use_case.id
    for tc in test_cases.test_cases:
        if tc.use_case_id not in use_case_ids:
            errors.append(
                f"Test case '{tc.id}' references non-existent use_case_id: '{tc.use_case_id}'"
            )

    # Check 2: example.use_case_id -> use_case.id
    for ex in examples.examples:
        if ex.use_case_id not in use_case_ids:
            errors.append(
                f"Example '{ex.id}' references non-existent use_case_id: '{ex.use_case_id}'"
            )

    # Check 3: example.test_case_id -> test_case.id
    for ex in examples.examples:
        if ex.test_case_id not in test_case_ids:
            errors.append(
                f"Example '{ex.id}' references non-existent test_case_id: '{ex.test_case_id}'"
            )

    # Check 4: example.policy_ids items -> policy.id (actual policy existence check)
    for ex in examples.examples:
        for policy_id in ex.policy_ids:
            if policy_id not in policy_ids:
                errors.append(
                    f"Example '{ex.id}' references non-existent policy_id: '{policy_id}'"
                )

    return errors
