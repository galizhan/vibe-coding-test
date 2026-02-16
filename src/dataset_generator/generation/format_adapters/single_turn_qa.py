"""Single-turn QA format adapter for support bot examples."""

import logging
from pydantic import BaseModel, Field
from dataset_generator.generation.format_adapters.base import FormatAdapter
from dataset_generator.models.dataset_example import DatasetExample, InputData, Message
from dataset_generator.extraction.llm_client import get_openai_client

logger = logging.getLogger(__name__)


class SingleTurnQAGenerationOutput(BaseModel):
    """Structured output for single-turn QA generation."""

    user_message: str = Field(
        ..., description="Customer question or message in Russian"
    )
    expected_response: str = Field(
        ..., description="Ideal support response in Russian"
    )
    evaluation_criteria: list[str] = Field(
        ..., min_length=3, description="At least 3 evaluation criteria"
    )
    relevant_policy_ids: list[str] = Field(
        ..., min_length=1, description="At least 1 relevant policy ID"
    )


class SingleTurnQAAdapter(FormatAdapter):
    """Adapter for generating single_turn_qa format examples (support bot).

    Generates examples with 1 user message and expected response.
    """

    def __init__(self, case: str = "support_bot"):
        """Initialize adapter with case identifier.

        Args:
            case: Case identifier (default: support_bot)
        """
        self.case = case

    def generate_example(
        self,
        use_case_id: str,
        test_case_id: str,
        parameters: dict,
        policies: list[dict],
        model: str = "gpt-4o-mini",
        seed: int | None = None,
    ) -> DatasetExample:
        """Generate a single_turn_qa format example.

        Args:
            use_case_id: Use case identifier
            test_case_id: Test case identifier
            parameters: Test parameters (tone, has_order_id, etc.)
            policies: List of policy dicts
            model: Model to use for generation
            seed: Random seed for reproducibility

        Returns:
            DatasetExample in single_turn_qa format
        """
        logger.info(
            f"Generating single_turn_qa example for {test_case_id} with parameters: {parameters}"
        )

        # Build use case context from policies
        use_case_description = self._extract_use_case_description(policies)
        policies_text = self._format_policies(policies)
        parameters_text = self._format_parameters(parameters)

        # Build system prompt
        system_prompt = f"""You are a dataset generation assistant. Generate a realistic customer support example in RUSSIAN.

USE CASE CONTEXT:
{use_case_description}

POLICIES AND CONSTRAINTS:
{policies_text}

TEST PARAMETERS:
{parameters_text}

TASK:
Generate a customer support example that:
1. Creates a realistic user question/message in Russian matching the parameters
2. Provides the ideal support response respecting all policies
3. Lists 3+ evaluation criteria for assessing response quality
4. Identifies which policies are relevant (use policy IDs from above)

IMPORTANT:
- All text must be in RUSSIAN
- The user message should match the tone and scenario from parameters
- The expected response must respect policy constraints (e.g., don't fabricate data if no access)
- Include specific, actionable evaluation criteria"""

        # Call OpenAI structured outputs
        client = get_openai_client()

        kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": "Generate the single-turn QA example now.",
                },
            ],
            "temperature": 0,
        }

        if seed is not None:
            kwargs["seed"] = seed

        response = client.beta.chat.completions.parse(
            response_format=SingleTurnQAGenerationOutput, **kwargs
        )

        output = response.choices[0].message.parsed

        # Generate unique example ID
        example_id = self._generate_example_id(test_case_id)

        # Create DatasetExample
        example = DatasetExample(
            id=example_id,
            case=self.case,
            format="single_turn_qa",
            use_case_id=use_case_id,
            test_case_id=test_case_id,
            input=InputData(
                messages=[Message(role="user", content=output.user_message)]
            ),
            expected_output=output.expected_response,
            evaluation_criteria=output.evaluation_criteria,
            policy_ids=output.relevant_policy_ids,
            metadata={
                "source": "",  # Will be classified later by source_classifier
                "generator": "single_turn_qa_adapter",
                "model": model,
            },
        )

        logger.info(f"Generated example {example_id}")
        return example

    def validate_format(self, example: DatasetExample) -> list[str]:
        """Validate single_turn_qa format requirements.

        Args:
            example: Dataset example to validate

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Check format field
        if example.format != "single_turn_qa":
            errors.append(
                f"Format must be 'single_turn_qa', got '{example.format}'"
            )

        # Check messages count
        if len(example.input.messages) != 1:
            errors.append(
                f"single_turn_qa must have exactly 1 message, got {len(example.input.messages)}"
            )

        # Check message role
        if example.input.messages and example.input.messages[0].role != "user":
            errors.append(
                f"single_turn_qa message role must be 'user', got '{example.input.messages[0].role}'"
            )

        # Check target_message_index should not be set
        if example.input.target_message_index is not None:
            errors.append(
                "single_turn_qa should not have target_message_index"
            )

        return errors

    def get_format_name(self) -> str:
        """Get format name.

        Returns:
            'single_turn_qa'
        """
        return "single_turn_qa"

    def _extract_use_case_description(self, policies: list[dict]) -> str:
        """Extract use case description from policies context.

        Args:
            policies: List of policy dicts

        Returns:
            Use case description summary
        """
        if not policies:
            return "General customer support scenario"

        # Build context from policy names and types
        policy_context = ", ".join([p.get("name", "") for p in policies[:3]])
        return f"Customer support scenario involving: {policy_context}"

    def _format_policies(self, policies: list[dict]) -> str:
        """Format policies for prompt.

        Args:
            policies: List of policy dicts

        Returns:
            Formatted policies text
        """
        if not policies:
            return "No specific policies provided."

        lines = []
        for p in policies:
            policy_id = p.get("id", "pol_unknown")
            policy_type = p.get("type", "unknown")
            statement = p.get("statement") or p.get("description", "")
            lines.append(f"- {policy_id} ({policy_type}): {statement}")

        return "\n".join(lines)

    def _format_parameters(self, parameters: dict) -> str:
        """Format test parameters for prompt.

        Args:
            parameters: Parameter dict

        Returns:
            Formatted parameters text
        """
        if not parameters:
            return "Default scenario (neutral tone, standard case)"

        lines = []
        for key, value in parameters.items():
            lines.append(f"- {key}: {value}")

        return "\n".join(lines)

    def _generate_example_id(self, test_case_id: str) -> str:
        """Generate unique example ID from test case ID.

        Args:
            test_case_id: Test case identifier

        Returns:
            Example ID with ex_ prefix
        """
        # Extract base from test_case_id and create example ID
        base = test_case_id.replace("tc_", "")
        import uuid

        unique_suffix = str(uuid.uuid4())[:8]
        return f"ex_{base}_{unique_suffix}"
