"""Direct OpenAI generation fallback for when frameworks fail."""

import json
import logging
from typing import TYPE_CHECKING

from dataset_generator.extraction.llm_client import get_openai_client
from dataset_generator.models.test_case import TestCase
from dataset_generator.models.dataset_example import DatasetExample, InputData, Message

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def generate_with_openai_fallback(
    use_case_id: str,
    use_case_description: str,
    policies: list[dict],
    num_test_cases: int = 3,
    model: str = "gpt-4o-mini",
    seed: int | None = None,
) -> tuple[list[TestCase], list[DatasetExample]]:
    """Generate test cases and dataset examples using direct OpenAI calls.

    This is the LAST RESORT generator when framework calls fail. Uses
    OpenAI structured outputs to produce test cases and dataset examples
    without external framework dependencies.

    Args:
        use_case_id: Use case identifier (must start with uc_)
        use_case_description: Description of the use case
        policies: List of policy dicts with id, name, type, description
        num_test_cases: Number of test cases to generate (default: 3)
        model: Model name to use (default: gpt-4o-mini)
        seed: Random seed for reproducibility (optional)

    Returns:
        Tuple of (test_cases, dataset_examples)

    Raises:
        RuntimeError: If generation fails

    Example:
        >>> policies = [{"id": "pol_001", "name": "Refund Policy", ...}]
        >>> tcs, examples = generate_with_openai_fallback(
        ...     use_case_id="uc_001",
        ...     use_case_description="Handle refund requests",
        ...     policies=policies,
        ...     num_test_cases=3
        ... )
    """
    try:
        logger.info(
            f"Using OpenAI fallback to generate {num_test_cases} test cases for {use_case_id}"
        )

        # Build system prompt
        system_prompt = _build_system_prompt(
            use_case_id=use_case_id,
            use_case_description=use_case_description,
            policies=policies,
            num_test_cases=num_test_cases,
        )

        # Get OpenAI client
        client = get_openai_client()

        # Call OpenAI API with JSON mode
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Generate {num_test_cases} test cases and corresponding dataset examples.",
                },
            ],
            response_format={"type": "json_object"},
            temperature=0,
            seed=seed,
        )

        # Parse JSON response
        response_text = response.choices[0].message.content
        data = json.loads(response_text)

        # Construct TestCase objects
        test_cases = []
        for i, tc_data in enumerate(data.get("test_cases", []), start=1):
            tc = TestCase(
                id=tc_data.get("id", f"tc_{use_case_id.replace('uc_', '')}{i:03d}"),
                use_case_id=use_case_id,
                name=tc_data.get("name", f"Test case {i}"),
                description=tc_data.get("description", ""),
                parameter_variation_axes=tc_data.get(
                    "parameter_variation_axes", ["tone", "complexity"]
                ),
                metadata={
                    "generator": "openai_fallback",
                    "model": model,
                    **tc_data.get("metadata", {}),
                },
            )
            test_cases.append(tc)

        # Construct DatasetExample objects
        dataset_examples = []
        for i, ex_data in enumerate(data.get("dataset_examples", []), start=1):
            messages_data = ex_data.get("input", {}).get("messages", [])
            messages = [
                Message(role=msg.get("role", "user"), content=msg.get("content", ""))
                for msg in messages_data
            ]

            ex = DatasetExample(
                id=ex_data.get("id", f"ex_{use_case_id.replace('uc_', '')}{i:03d}"),
                case=ex_data.get("case", "support_bot"),
                format=ex_data.get("format", "single_turn_qa"),
                use_case_id=use_case_id,
                test_case_id=ex_data.get(
                    "test_case_id", test_cases[min(i - 1, len(test_cases) - 1)].id
                ),
                input=InputData(messages=messages),
                expected_output=ex_data.get("expected_output", ""),
                evaluation_criteria=ex_data.get(
                    "evaluation_criteria",
                    ["relevance", "policy_compliance", "response_completeness"],
                ),
                policy_ids=ex_data.get("policy_ids", ["pol_unknown"]),
                metadata={
                    "generator": "openai_fallback",
                    "model": model,
                    **ex_data.get("metadata", {}),
                },
            )
            dataset_examples.append(ex)

        logger.info(
            f"Successfully generated {len(test_cases)} test cases and "
            f"{len(dataset_examples)} dataset examples using OpenAI fallback"
        )

        return test_cases, dataset_examples

    except Exception as e:
        logger.error(f"OpenAI fallback generation failed: {e}", exc_info=True)
        raise RuntimeError(f"OpenAI fallback generation failed: {e}") from e


def _build_system_prompt(
    use_case_id: str,
    use_case_description: str,
    policies: list[dict],
    num_test_cases: int,
) -> str:
    """Build system prompt for test case generation.

    Args:
        use_case_id: Use case identifier
        use_case_description: Description of the use case
        policies: List of policy dicts
        num_test_cases: Number of test cases to generate

    Returns:
        System prompt string
    """
    policies_text = "\n".join(
        [
            f"- {p.get('id', 'N/A')}: {p.get('name', 'N/A')} ({p.get('type', 'N/A')}) - {p.get('description', 'N/A')}"
            for p in policies
        ]
    )

    return f"""You are a test case generation assistant. Generate test cases and dataset examples for customer support scenarios.

USE CASE:
ID: {use_case_id}
Description: {use_case_description}

POLICIES:
{policies_text}

TASK:
Generate {num_test_cases} test cases and corresponding dataset examples.

OUTPUT FORMAT (JSON):
{{
  "test_cases": [
    {{
      "id": "tc_XXX",
      "name": "Brief test case name",
      "description": "Detailed description of what this test covers",
      "parameter_variation_axes": ["axis1", "axis2"],  // MUST be 2-3 items
      "metadata": {{}}
    }}
  ],
  "dataset_examples": [
    {{
      "id": "ex_XXX",
      "case": "support_bot",
      "format": "single_turn_qa",
      "test_case_id": "tc_XXX",
      "input": {{
        "messages": [
          {{"role": "user", "content": "Customer question here"}}
        ]
      }},
      "expected_output": "Expected support response",
      "evaluation_criteria": ["criterion1", "criterion2", "criterion3"],  // MUST be 3+ items
      "policy_ids": ["pol_XXX"],  // MUST be 1+ items, all starting with pol_
      "metadata": {{}}
    }}
  ]
}}

REQUIREMENTS:
1. Each test case must have 2-3 parameter_variation_axes
2. Each dataset example must have 3+ evaluation_criteria
3. Each dataset example must reference 1+ policy_ids (all starting with pol_)
4. Create diverse scenarios covering different aspects of the use case
5. Generate realistic customer support conversations in Russian
6. Ensure expected outputs reference relevant policies

Generate the JSON output now."""


