"""Hardcoded adapter for Giskard testset rows to project Pydantic models."""

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


def adapt_giskard_row_to_test_case(
    row: pd.Series,
    use_case_id: str,
    test_case_index: int,
) -> TestCase:
    """Adapt Giskard testset row to TestCase model.

    Args:
        row: Pandas Series from Giskard testset DataFrame
        use_case_id: Use case identifier (must start with uc_)
        test_case_index: Index for generating test case ID

    Returns:
        TestCase instance with generator metadata

    Note:
        Giskard rows contain: question, reference_answer, reference_context, metadata
    """
    try:
        # Generate test case ID
        tc_id = f"tc_{use_case_id.replace('uc_', '')}{test_case_index:03d}"

        # Extract name from question (first 80 chars)
        question = row.get("question", "")
        name = str(question)[:80] if question else f"Test case {test_case_index}"
        if len(str(question)) > 80:
            name = name.rsplit(" ", 1)[0] + "..."

        # Extract description from reference_answer or question
        reference_answer = row.get("reference_answer", "")
        if pd.notna(reference_answer) and reference_answer:
            description = str(reference_answer)[:200]
        else:
            description = str(question)[:200] if question else f"Test case for {use_case_id}"

        # Get question type from metadata
        question_type = "unknown"
        if hasattr(row, "metadata") and isinstance(row.metadata, dict):
            question_type = row.metadata.get("question_type", "unknown")

        # Map question type to parameter variation axes
        if "complex" in str(question_type).lower() or "multi" in str(question_type).lower():
            parameter_variation_axes = ["context_complexity", "knowledge_depth"]
        elif "simple" in str(question_type).lower() or "direct" in str(question_type).lower():
            parameter_variation_axes = ["tone", "specificity"]
        elif "conversational" in str(question_type).lower():
            parameter_variation_axes = ["conversation_style", "formality_level"]
        else:
            # Default axes for business/knowledge-base questions
            parameter_variation_axes = ["question_complexity", "knowledge_specificity"]

        # Get reference context (truncate for metadata)
        reference_context = row.get("reference_context", "")
        reference_context_preview = str(reference_context)[:200] if reference_context else ""

        # Build metadata with generator field
        metadata = {
            "generator": "giskard",
            "question_type": str(question_type),
            "reference_context": reference_context_preview,
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

        logger.debug(f"Adapted Giskard row to test case: {tc_id}")
        return test_case

    except Exception as e:
        logger.warning(f"Error adapting Giskard row to test case: {e}")
        # Return minimal valid test case as fallback
        return TestCase(
            id=f"tc_{use_case_id.replace('uc_', '')}{test_case_index:03d}",
            use_case_id=use_case_id,
            name=f"Test case {test_case_index}",
            description="Test case adapted from Giskard testset",
            parameter_variation_axes=["tone", "complexity"],
            metadata={"generator": "giskard", "adaptation_error": str(e)},
        )


def adapt_giskard_row_to_example(
    row: pd.Series,
    use_case_id: str,
    test_case_id: str,
    example_index: int,
    case: str = "support_bot",
    format: str = "single_turn_qa",
    policy_ids: list[str] | None = None,
) -> DatasetExample:
    """Adapt Giskard testset row to DatasetExample model.

    Args:
        row: Pandas Series from Giskard testset DataFrame
        use_case_id: Use case identifier (must start with uc_)
        test_case_id: Test case identifier (must start with tc_)
        example_index: Index for generating example ID
        case: Case identifier (default: support_bot)
        format: Format type (default: single_turn_qa)
        policy_ids: List of policy IDs (if None, will attempt to extract from reference_context)

    Returns:
        DatasetExample instance with generator metadata

    Note:
        Giskard may have missing reference_answer - handled with default
    """
    try:
        # Generate example ID
        ex_id = f"ex_{use_case_id.replace('uc_', '')}{example_index:03d}"

        # Extract input (question)
        input_text = row.get("question", "")
        messages = [Message(role="user", content=str(input_text))]
        input_data = InputData(messages=messages)

        # Extract expected output (handle missing reference_answer)
        expected_output = row.get("reference_answer", "")
        if pd.isna(expected_output) or not expected_output:
            logger.warning(f"Giskard row has missing reference_answer for {ex_id}, using empty string")
            expected_output = ""
        else:
            expected_output = str(expected_output)

        # Get question type from metadata
        question_type = "unknown"
        if hasattr(row, "metadata") and isinstance(row.metadata, dict):
            question_type = row.metadata.get("question_type", "unknown")

        # Generate evaluation criteria based on question type (must be 3+)
        if "complex" in str(question_type).lower() or "multi" in str(question_type).lower():
            evaluation_criteria = [
                "knowledge_accuracy",
                "context_relevance",
                "answer_completeness",
                "policy_compliance",
            ]
        elif "conversational" in str(question_type).lower():
            evaluation_criteria = [
                "conversation_naturalness",
                "answer_relevance",
                "policy_compliance",
            ]
        else:
            # Default criteria for business/knowledge-base questions
            evaluation_criteria = [
                "knowledge_accuracy",
                "answer_relevance",
                "policy_compliance",
            ]

        # Extract policy IDs from reference_context if not provided
        if policy_ids is None:
            policy_ids = []
            reference_context = row.get("reference_context", "")
            if isinstance(reference_context, str):
                # Look for pol_ pattern
                matches = re.findall(r'pol_\w+', reference_context)
                policy_ids.extend(matches)

            # Remove duplicates
            policy_ids = list(set(policy_ids))

            # Default to unknown if no policies found
            if not policy_ids:
                logger.warning(f"No policy IDs found in Giskard reference_context for {ex_id}, using pol_unknown")
                policy_ids = ["pol_unknown"]

        # Get reference context (truncate for metadata)
        reference_context = row.get("reference_context", "")
        reference_context_preview = str(reference_context)[:200] if reference_context else ""

        # Build metadata with generator field
        metadata = {
            "generator": "giskard",
            "question_type": str(question_type),
            "reference_context": reference_context_preview,
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

        logger.debug(f"Adapted Giskard row to example: {ex_id}")
        return example

    except Exception as e:
        logger.warning(f"Error adapting Giskard row to example: {e}")
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
            metadata={"generator": "giskard", "adaptation_error": str(e)},
        )
