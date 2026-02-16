"""Hardcoded adapter for Ragas testset rows to project Pydantic models."""

import logging
import re
from typing import Any
import pandas as pd

from dataset_generator.models.test_case import TestCase
from dataset_generator.models.dataset_example import (
    DatasetExample,
    InputData,
    Message,
)

logger = logging.getLogger(__name__)


def adapt_ragas_row_to_test_case(
    row: pd.Series,
    use_case_id: str,
    test_case_index: int,
) -> TestCase:
    """Adapt Ragas testset row to TestCase model.

    Args:
        row: Pandas Series from Ragas testset DataFrame
        use_case_id: Use case identifier (must start with uc_)
        test_case_index: Index for generating test case ID

    Returns:
        TestCase instance with generator metadata

    Note:
        Ragas rows contain: question, ground_truth, contexts, evolution_type, metadata
    """
    try:
        # Generate test case ID
        tc_id = f"tc_{use_case_id.replace('uc_', '')}{test_case_index:03d}"

        # Extract name from question (first 80 chars)
        question = row.get("question", row.get("user_input", ""))
        name = str(question)[:80] if question else f"Test case {test_case_index}"
        if len(str(question)) > 80:
            name = name.rsplit(" ", 1)[0] + "..."

        # Extract description from ground_truth or question
        ground_truth = row.get("ground_truth", row.get("reference", ""))
        if pd.notna(ground_truth) and ground_truth:
            description = str(ground_truth)[:200]
        else:
            description = str(question)[:200] if question else f"Test case for {use_case_id}"

        # Get evolution/query type from metadata
        # Ragas v0.4 may use 'synthesizer_name' instead of 'evolution_type'
        evolution_type = None
        if hasattr(row, "metadata") and isinstance(row.metadata, dict):
            evolution_type = row.metadata.get("evolution_type") or row.metadata.get("synthesizer_name")

        # Try to get from row attributes directly
        if not evolution_type:
            evolution_type = row.get("evolution_type", row.get("synthesizer_name", "unknown"))

        # Map evolution type to parameter variation axes
        if "reasoning" in str(evolution_type).lower() or "abstract" in str(evolution_type).lower():
            parameter_variation_axes = ["reasoning_depth", "context_complexity"]
        elif "multi" in str(evolution_type).lower() or "specific" in str(evolution_type).lower():
            parameter_variation_axes = ["context_count", "cross_reference_depth"]
        elif "simple" in str(evolution_type).lower() or "single" in str(evolution_type).lower():
            parameter_variation_axes = ["tone", "specificity"]
        else:
            # Default axes
            parameter_variation_axes = ["tone", "complexity"]

        # Get context count
        contexts = row.get("contexts", row.get("reference_contexts", []))
        contexts_used = len(contexts) if isinstance(contexts, (list, tuple)) else 0

        # Build metadata with generator field
        metadata = {
            "generator": "ragas",
            "evolution_type": str(evolution_type) if evolution_type else "unknown",
            "contexts_used": contexts_used,
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

        logger.debug(f"Adapted Ragas row to test case: {tc_id}")
        return test_case

    except Exception as e:
        logger.warning(f"Error adapting Ragas row to test case: {e}")
        # Return minimal valid test case as fallback
        return TestCase(
            id=f"tc_{use_case_id.replace('uc_', '')}{test_case_index:03d}",
            use_case_id=use_case_id,
            name=f"Test case {test_case_index}",
            description="Test case adapted from Ragas testset",
            parameter_variation_axes=["tone", "complexity"],
            metadata={"generator": "ragas", "adaptation_error": str(e)},
        )


def adapt_ragas_row_to_example(
    row: pd.Series,
    use_case_id: str,
    test_case_id: str,
    example_index: int,
    case: str = "support_bot",
    format: str = "single_turn_qa",
    policy_ids: list[str] | None = None,
) -> DatasetExample:
    """Adapt Ragas testset row to DatasetExample model.

    Args:
        row: Pandas Series from Ragas testset DataFrame
        use_case_id: Use case identifier (must start with uc_)
        test_case_id: Test case identifier (must start with tc_)
        example_index: Index for generating example ID
        case: Case identifier (default: support_bot)
        format: Format type (default: single_turn_qa)
        policy_ids: List of policy IDs (if None, will attempt to extract from contexts)

    Returns:
        DatasetExample instance with generator metadata

    Note:
        Ragas research pitfall 2: "Occasional NaN values for ground_truth" - handled
    """
    try:
        # Generate example ID
        ex_id = f"ex_{use_case_id.replace('uc_', '')}{example_index:03d}"

        # Extract input (question/user_input)
        input_text = row.get("question", row.get("user_input", ""))
        messages = [Message(role="user", content=str(input_text))]
        input_data = InputData(messages=messages)

        # Extract expected output (handle NaN per research pitfall 2)
        expected_output = row.get("ground_truth", row.get("reference", ""))
        if pd.isna(expected_output) or not expected_output:
            logger.warning(f"Ragas row has NaN/empty ground_truth for {ex_id}, using empty string")
            expected_output = ""
        else:
            expected_output = str(expected_output)

        # Get evolution/query type
        evolution_type = None
        if hasattr(row, "metadata") and isinstance(row.metadata, dict):
            evolution_type = row.metadata.get("evolution_type") or row.metadata.get("synthesizer_name")

        if not evolution_type:
            evolution_type = row.get("evolution_type", row.get("synthesizer_name", "unknown"))

        # Generate evaluation criteria based on evolution type (must be 3+)
        if "reasoning" in str(evolution_type).lower() or "abstract" in str(evolution_type).lower():
            evaluation_criteria = [
                "reasoning_correctness",
                "logical_flow",
                "policy_compliance",
                "answer_completeness",
            ]
        elif "multi" in str(evolution_type).lower() or "specific" in str(evolution_type).lower():
            evaluation_criteria = [
                "context_integration",
                "cross_reference_accuracy",
                "policy_compliance",
                "response_completeness",
            ]
        else:
            # Simple/single-hop questions
            evaluation_criteria = [
                "relevance_to_query",
                "answer_accuracy",
                "policy_compliance",
            ]

        # Extract policy IDs from contexts if not provided
        if policy_ids is None:
            policy_ids = []
            contexts = row.get("contexts", row.get("reference_contexts", []))
            if isinstance(contexts, (list, tuple)):
                for context in contexts:
                    if isinstance(context, str):
                        # Look for pol_ pattern
                        matches = re.findall(r'pol_\w+', context)
                        policy_ids.extend(matches)

            # Remove duplicates
            policy_ids = list(set(policy_ids))

            # Default to unknown if no policies found
            if not policy_ids:
                logger.warning(f"No policy IDs found in Ragas contexts for {ex_id}, using pol_unknown")
                policy_ids = ["pol_unknown"]

        # Get context count
        contexts = row.get("contexts", row.get("reference_contexts", []))
        contexts_used = len(contexts) if isinstance(contexts, (list, tuple)) else 0

        # Build metadata with generator field
        metadata = {
            "generator": "ragas",
            "evolution_type": str(evolution_type) if evolution_type else "unknown",
            "contexts_used": contexts_used,
        }

        # Preserve row metadata if available
        if hasattr(row, "metadata") and isinstance(row.metadata, dict):
            for key, value in row.metadata.items():
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

        logger.debug(f"Adapted Ragas row to example: {ex_id}")
        return example

    except Exception as e:
        logger.warning(f"Error adapting Ragas row to example: {e}")
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
            metadata={"generator": "ragas", "adaptation_error": str(e)},
        )
