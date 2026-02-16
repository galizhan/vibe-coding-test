"""Hardcoded adapter for DeepEval Golden objects to project Pydantic models."""

import logging
import re
from typing import Any

from dataset_generator.models.test_case import TestCase
from dataset_generator.models.dataset_example import (
    DatasetExample,
    InputData,
    Message,
)

logger = logging.getLogger(__name__)


def adapt_deepeval_golden_to_test_case(
    golden: Any,
    use_case_id: str,
    test_case_index: int,
) -> TestCase:
    """Adapt DeepEval Golden object to TestCase model.

    Args:
        golden: DeepEval Golden object with input, expected_output, context, metadata
        use_case_id: Use case identifier (must start with uc_)
        test_case_index: Index for generating test case ID

    Returns:
        TestCase instance with generator metadata

    Example:
        >>> from types import SimpleNamespace
        >>> golden = SimpleNamespace(
        ...     input='Test question',
        ...     expected_output='Test answer',
        ...     context=['Policy context'],
        ...     additional_metadata={'evolution_type': 'reasoning', 'quality_score': 0.85}
        ... )
        >>> tc = adapt_deepeval_golden_to_test_case(golden, 'uc_001', 1)
        >>> assert tc.id.startswith('tc_')
        >>> assert tc.metadata.get('generator') == 'deepeval'
    """
    try:
        # Generate test case ID
        tc_id = f"tc_{use_case_id.replace('uc_', '')}{test_case_index:03d}"

        # Extract name from input (first 80 chars or meaningful summary)
        input_text = getattr(golden, "input", "")
        name = input_text[:80] if input_text else f"Test case {test_case_index}"
        if len(input_text) > 80:
            name = name.rsplit(" ", 1)[0] + "..."

        # Extract description from context or input
        context = getattr(golden, "context", [])
        if context and isinstance(context, list) and len(context) > 0:
            description = context[0][:200] if isinstance(context[0], str) else str(context[0])[:200]
        else:
            description = input_text[:200] if input_text else f"Test case for {use_case_id}"

        # Get evolution type from metadata to determine parameter variation axes
        additional_metadata = getattr(golden, "additional_metadata", {})
        evolution_type = additional_metadata.get("evolution_type", "unknown") if isinstance(additional_metadata, dict) else "unknown"

        # Map evolution type to parameter variation axes
        if evolution_type == "reasoning":
            parameter_variation_axes = ["reasoning_depth", "logical_complexity"]
        elif evolution_type == "multicontext" or evolution_type == "multi_context":
            parameter_variation_axes = ["context_count", "cross_reference_depth"]
        elif evolution_type == "concretizing":
            parameter_variation_axes = ["scenario_specificity", "detail_level"]
        elif evolution_type == "constrained":
            parameter_variation_axes = ["constraint_type", "edge_case_complexity"]
        else:
            # Default axes per plan specification
            parameter_variation_axes = ["tone", "complexity", "policy_boundary"]

        # Ensure 2-3 axes (validation will check)
        parameter_variation_axes = parameter_variation_axes[:3]

        # Build metadata with generator field
        quality_score = additional_metadata.get("quality_score") if isinstance(additional_metadata, dict) else None
        metadata = {
            "generator": "deepeval",
            "evolution_type": evolution_type,
            "quality_score": quality_score,
        }

        # Create TestCase instance
        test_case = TestCase(
            id=tc_id,
            use_case_id=use_case_id,
            name=name,
            description=description,
            parameter_variation_axes=parameter_variation_axes,
            metadata=metadata,
        )

        logger.debug(f"Adapted DeepEval golden to test case: {tc_id}")
        return test_case

    except Exception as e:
        logger.warning(f"Error adapting DeepEval golden to test case: {e}")
        # Return minimal valid test case as fallback
        return TestCase(
            id=f"tc_{use_case_id.replace('uc_', '')}{test_case_index:03d}",
            use_case_id=use_case_id,
            name=f"Test case {test_case_index}",
            description="Test case adapted from DeepEval golden",
            parameter_variation_axes=["tone", "complexity"],
            metadata={"generator": "deepeval", "adaptation_error": str(e)},
        )


def adapt_deepeval_golden_to_example(
    golden: Any,
    use_case_id: str,
    test_case_id: str,
    example_index: int,
    case: str = "support_bot",
    format: str = "single_turn_qa",
    policy_ids: list[str] | None = None,
) -> DatasetExample:
    """Adapt DeepEval Golden object to DatasetExample model.

    Args:
        golden: DeepEval Golden object with input, expected_output, context, metadata
        use_case_id: Use case identifier (must start with uc_)
        test_case_id: Test case identifier (must start with tc_)
        example_index: Index for generating example ID
        case: Case identifier (default: support_bot)
        format: Format type (default: single_turn_qa)
        policy_ids: List of policy IDs (if None, will attempt to extract from context)

    Returns:
        DatasetExample instance with generator metadata

    Example:
        >>> from types import SimpleNamespace
        >>> golden = SimpleNamespace(
        ...     input='Test question',
        ...     expected_output='Test answer',
        ...     context=['Policy pol_001 applies here'],
        ...     additional_metadata={'evolution_type': 'reasoning'}
        ... )
        >>> ex = adapt_deepeval_golden_to_example(
        ...     golden, 'uc_001', 'tc_001_001', 1, policy_ids=['pol_001']
        ... )
        >>> assert ex.id.startswith('ex_')
        >>> assert ex.metadata.get('generator') == 'deepeval'
        >>> assert len(ex.evaluation_criteria) >= 3
    """
    try:
        # Generate example ID
        ex_id = f"ex_{use_case_id.replace('uc_', '')}{example_index:03d}"

        # Extract input
        input_text = getattr(golden, "input", "")
        messages = [Message(role="user", content=input_text)]
        input_data = InputData(messages=messages)

        # Extract expected output
        expected_output = getattr(golden, "expected_output", "")
        if not expected_output:
            logger.warning(f"Golden has no expected_output, using empty string for {ex_id}")
            expected_output = ""

        # Extract or generate evaluation criteria (must be 3+)
        context = getattr(golden, "context", [])
        additional_metadata = getattr(golden, "additional_metadata", {})
        evolution_type = additional_metadata.get("evolution_type", "unknown") if isinstance(additional_metadata, dict) else "unknown"

        # Generate criteria based on evolution type
        if evolution_type == "reasoning":
            evaluation_criteria = [
                "logical_correctness",
                "reasoning_clarity",
                "policy_compliance",
                "response_completeness",
            ]
        elif evolution_type in ["multicontext", "multi_context"]:
            evaluation_criteria = [
                "context_integration",
                "cross_reference_accuracy",
                "policy_compliance",
                "response_completeness",
            ]
        else:
            # Default criteria
            evaluation_criteria = [
                "relevance_to_query",
                "policy_compliance",
                "response_completeness",
                "answer_accuracy",
            ]

        # Extract policy IDs from context if not provided
        if policy_ids is None:
            policy_ids = []
            if context and isinstance(context, list):
                for ctx_item in context:
                    if isinstance(ctx_item, str):
                        # Look for pol_ pattern
                        matches = re.findall(r'pol_\w+', ctx_item)
                        policy_ids.extend(matches)

            # Remove duplicates
            policy_ids = list(set(policy_ids))

            # Default to unknown if no policies found
            if not policy_ids:
                logger.warning(f"No policy IDs found in golden context for {ex_id}, using pol_unknown")
                policy_ids = ["pol_unknown"]

        # Build metadata with generator field
        metadata = {
            "generator": "deepeval",
            "evolution_type": evolution_type,
            "context_count": len(context) if isinstance(context, list) else 0,
        }

        # Preserve additional metadata from golden
        if isinstance(additional_metadata, dict):
            for key, value in additional_metadata.items():
                if key not in metadata:
                    metadata[key] = value

        # Create DatasetExample instance
        example = DatasetExample(
            id=ex_id,
            case=case,
            format=format,
            use_case_id=use_case_id,
            test_case_id=test_case_id,
            input=input_data,
            expected_output=expected_output,
            evaluation_criteria=evaluation_criteria,
            policy_ids=policy_ids,
            metadata=metadata,
        )

        logger.debug(f"Adapted DeepEval golden to example: {ex_id}")
        return example

    except Exception as e:
        logger.warning(f"Error adapting DeepEval golden to example: {e}")
        # Return minimal valid example as fallback
        return DatasetExample(
            id=f"ex_{use_case_id.replace('uc_', '')}{example_index:03d}",
            case=case,
            format=format,
            use_case_id=use_case_id,
            test_case_id=test_case_id,
            input=InputData(messages=[Message(role="user", content="")]),
            expected_output="",
            evaluation_criteria=["relevance", "policy_compliance", "completeness"],
            policy_ids=policy_ids or ["pol_unknown"],
            metadata={"generator": "deepeval", "adaptation_error": str(e)},
        )
