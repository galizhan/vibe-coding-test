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
    case: str = "support_bot",
    formats: list[str] | None = None,
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
        case: Case identifier (default: support_bot)
        formats: List of formats to generate (default: None -> single_turn_qa for support_bot)

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
        ...     num_test_cases=3,
        ...     case="support_bot",
        ...     formats=["single_turn_qa"]
        ... )
    """
    try:
        logger.info(
            f"Using OpenAI fallback to generate {num_test_cases} test cases for {use_case_id} (case={case}, formats={formats})"
        )

        # Default formats if not provided
        if formats is None:
            if case == "operator_quality":
                formats = ["single_utterance_correction", "dialog_last_turn_correction"]
            else:
                formats = ["single_turn_qa"]

        # Build system prompt
        system_prompt = _build_system_prompt(
            use_case_id=use_case_id,
            use_case_description=use_case_description,
            policies=policies,
            num_test_cases=num_test_cases,
            case=case,
            formats=formats,
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
                case=case,
                parameters=tc_data.get("parameters", {}),
                policy_ids=tc_data.get("policy_ids", []),
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

            # Get format from LLM response or default to first format
            example_format = ex_data.get("format", formats[0] if formats else "single_turn_qa")

            # Get target_message_index if present in input
            target_message_index = ex_data.get("input", {}).get("target_message_index")

            # For correction formats, set target_message_index if not set by LLM
            if example_format == "single_utterance_correction" and target_message_index is None:
                target_message_index = 0
            elif example_format == "dialog_last_turn_correction" and target_message_index is None:
                target_message_index = len(messages) - 1

            ex = DatasetExample(
                id=ex_data.get("id", f"ex_{use_case_id.replace('uc_', '')}{i:03d}"),
                case=case,
                format=example_format,
                use_case_id=use_case_id,
                test_case_id=ex_data.get(
                    "test_case_id", test_cases[min(i - 1, len(test_cases) - 1)].id
                ),
                input=InputData(messages=messages, target_message_index=target_message_index),
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
    case: str = "support_bot",
    formats: list[str] | None = None,
) -> str:
    """Build system prompt for test case generation.

    Args:
        use_case_id: Use case identifier
        use_case_description: Description of the use case
        policies: List of policy dicts
        num_test_cases: Number of test cases to generate
        case: Case identifier (support_bot, operator_quality, doctor_booking)
        formats: List of formats to generate

    Returns:
        System prompt string
    """
    policies_text = "\n".join(
        [
            f"- {p.get('id', 'N/A')}: {p.get('name', 'N/A')} ({p.get('type', 'N/A')}) - {p.get('description', 'N/A')}"
            for p in policies
        ]
    )

    # Default formats if not provided
    if formats is None:
        formats = ["single_turn_qa"]

    # Build format-specific instructions
    format_instructions = _build_format_instructions(formats, case)

    return f"""You are a test case generation assistant. Generate test cases and dataset examples.

CASE: {case}
FORMATS: {', '.join(formats)}

USE CASE:
ID: {use_case_id}
Description: {use_case_description}

POLICIES:
{policies_text}

TASK:
Generate {num_test_cases} test cases and corresponding dataset examples.

{format_instructions}

OUTPUT FORMAT (JSON):
{{
  "test_cases": [
    {{
      "id": "tc_XXX",
      "name": "Brief test case name",
      "description": "Detailed description of what this test covers",
      "parameter_variation_axes": ["axis1", "axis2"],  // MUST be 2-3 items
      "parameters": {{"param1": "value1", "param2": "value2"}},  // Test parameters
      "policy_ids": ["pol_XXX"],  // Relevant policy IDs
      "metadata": {{}}
    }}
  ],
  "dataset_examples": [
    {{
      "id": "ex_XXX",
      "case": "{case}",
      "format": "{formats[0]}",
      "test_case_id": "tc_XXX",
      "input": {{
        "messages": [
          {{"role": "user", "content": "Message here"}}
        ]
      }},
      "expected_output": "Expected response or corrected message",
      "evaluation_criteria": ["criterion1", "criterion2", "criterion3"],  // MUST be 3+ items
      "policy_ids": ["pol_XXX"],  // MUST be 1+ items, all starting with pol_
      "metadata": {{}}
    }}
  ]
}}

REQUIREMENTS:
1. Each test case must have 2-3 parameter_variation_axes
2. Each test case must have parameters dict with test parameters
3. Each test case must have policy_ids list
4. Each dataset example must have 3+ evaluation_criteria
5. Each dataset example must reference 1+ policy_ids (all starting with pol_)
6. Each dataset example must have case="{case}"
7. Create diverse scenarios covering different aspects of the use case
8. Generate realistic conversations in Russian
9. Ensure expected outputs reference relevant policies

Generate the JSON output now."""


def _build_format_instructions(formats: list[str], case: str) -> str:
    """Build format-specific instructions for the prompt.

    Args:
        formats: List of format names
        case: Case identifier

    Returns:
        Format instructions text
    """
    instructions = []

    if "single_turn_qa" in formats:
        instructions.append("""
FORMAT: single_turn_qa (for support_bot)
- input.messages: exactly 1 message with role="user"
- expected_output: the support response
- No target_message_index field
""")

    if "single_utterance_correction" in formats:
        instructions.append("""
FORMAT: single_utterance_correction (for operator_quality)
- input.messages: exactly 1 message with role="operator" containing errors
- input.target_message_index: 0
- expected_output: the corrected operator message
""")

    if "dialog_last_turn_correction" in formats:
        instructions.append("""
FORMAT: dialog_last_turn_correction (for operator_quality)
- input.messages: 2+ messages, last message has role="operator" and contains errors
- input.target_message_index: index of last message (len(messages) - 1)
- expected_output: the corrected last operator message
- Example escalation response: "Понимаю ваше недовольство. Давайте отменим запись: подскажите, пожалуйста, вашу фамилию и время приёма. Если вам удобнее, могу передать диалог старшему специалисту."
""")

    return "\n".join(instructions)


