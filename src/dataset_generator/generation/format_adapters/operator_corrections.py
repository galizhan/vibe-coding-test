"""Operator correction format adapters (single utterance and dialog)."""

import logging
from pydantic import BaseModel, Field
from dataset_generator.generation.format_adapters.base import FormatAdapter
from dataset_generator.models.dataset_example import DatasetExample, InputData, Message
from dataset_generator.extraction.llm_client import get_openai_client

logger = logging.getLogger(__name__)


class SingleUtteranceCorrectionOutput(BaseModel):
    """Structured output for single utterance correction generation."""

    operator_message_with_errors: str = Field(
        ..., description="Operator message containing MIXED errors in Russian"
    )
    corrected_message: str = Field(
        ..., description="Corrected version of the message in Russian"
    )
    evaluation_criteria: list[str] = Field(
        ..., min_length=3, description="At least 3 evaluation criteria"
    )
    relevant_policy_ids: list[str] = Field(
        ..., min_length=1, description="At least 1 relevant policy ID"
    )


class DialogLastTurnCorrectionOutput(BaseModel):
    """Structured output for dialog last turn correction generation."""

    dialog_messages: list[dict] = Field(
        ...,
        min_length=2,
        description="Dialog messages with roles (user/operator), ending with operator",
    )
    corrected_last_turn: str = Field(
        ..., description="Corrected version of last operator message in Russian"
    )
    evaluation_criteria: list[str] = Field(
        ..., min_length=3, description="At least 3 evaluation criteria"
    )
    relevant_policy_ids: list[str] = Field(
        ..., min_length=1, description="At least 1 relevant policy ID"
    )


class SingleUtteranceCorrectionAdapter(FormatAdapter):
    """Adapter for generating single_utterance_correction format examples.

    Generates examples with 1 operator message containing MIXED errors
    and its corrected version.
    """

    def __init__(self, case: str = "operator_quality"):
        """Initialize adapter with case identifier.

        Args:
            case: Case identifier (default: operator_quality)
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
        """Generate a single_utterance_correction format example.

        Args:
            use_case_id: Use case identifier
            test_case_id: Test case identifier
            parameters: Test parameters (punctuation_errors, slang_profanity_emoji, etc.)
            policies: List of policy dicts
            model: Model to use for generation
            seed: Random seed for reproducibility

        Returns:
            DatasetExample in single_utterance_correction format
        """
        logger.info(
            f"Generating single_utterance_correction example for {test_case_id} with parameters: {parameters}"
        )

        policies_text = self._format_policies(policies)
        error_instructions = self._build_error_instructions(parameters)

        # Build system prompt
        system_prompt = f"""You are a dataset generation assistant. Generate an operator quality check example in RUSSIAN.

POLICIES AND QUALITY RULES:
{policies_text}

ERROR PARAMETERS (generate MIXED errors - include ALL non-default values simultaneously):
{error_instructions}

TASK:
Generate an operator message that contains MIXED ERRORS matching the parameters above, and provide the corrected version.

CRITICAL REQUIREMENTS:
1. The operator message MUST contain MULTIPLE error types from the parameters (NOT one at a time)
2. ALL non-default/non-neutral parameter values should manifest as simultaneous errors
3. Generate realistic operator response in Russian (e.g., booking confirmation, cancellation, clarification)
4. The corrected version must fix all errors while preserving meaning
5. Include 3+ evaluation criteria
6. Reference relevant policy IDs

EXAMPLES OF MIXED ERRORS:
- If punctuation_errors=severe AND slang_profanity_emoji=excessive: "Окей отменил запись хорошо да??!!! 👍"
- If caps_exclamation=true AND medical_terms=present: "ИЗВИНИТЕ!!! Доктор примет вас В КАРДИОЛОГИЧЕСКОМ ОТДЕЛЕНИИ!!!"
- Mix errors naturally - the message should feel realistic but flawed"""

        # Call OpenAI structured outputs
        client = get_openai_client()

        kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": "Generate the single utterance correction example with MIXED errors now.",
                },
            ],
            "temperature": 0,
        }

        if seed is not None:
            kwargs["seed"] = seed

        response = client.beta.chat.completions.parse(
            response_format=SingleUtteranceCorrectionOutput, **kwargs
        )

        output = response.choices[0].message.parsed

        # Generate unique example ID
        example_id = self._generate_example_id(test_case_id)

        # Create DatasetExample
        example = DatasetExample(
            id=example_id,
            case=self.case,
            format="single_utterance_correction",
            use_case_id=use_case_id,
            test_case_id=test_case_id,
            input=InputData(
                messages=[
                    Message(
                        role="operator", content=output.operator_message_with_errors
                    )
                ],
                target_message_index=0,
            ),
            expected_output=output.corrected_message,
            evaluation_criteria=output.evaluation_criteria,
            policy_ids=output.relevant_policy_ids,
            metadata={
                "generator": "single_utterance_correction_adapter",
                "model": model,
            },
        )

        logger.info(f"Generated example {example_id}")
        return example

    def validate_format(self, example: DatasetExample) -> list[str]:
        """Validate single_utterance_correction format requirements.

        Args:
            example: Dataset example to validate

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Check format field
        if example.format != "single_utterance_correction":
            errors.append(
                f"Format must be 'single_utterance_correction', got '{example.format}'"
            )

        # Check messages count
        if len(example.input.messages) != 1:
            errors.append(
                f"single_utterance_correction must have exactly 1 message, got {len(example.input.messages)}"
            )

        # Check message role
        if example.input.messages and example.input.messages[0].role != "operator":
            errors.append(
                f"single_utterance_correction message role must be 'operator', got '{example.input.messages[0].role}'"
            )

        # Check target_message_index
        if example.input.target_message_index != 0:
            errors.append(
                f"single_utterance_correction target_message_index must be 0, got {example.input.target_message_index}"
            )

        return errors

    def get_format_name(self) -> str:
        """Get format name.

        Returns:
            'single_utterance_correction'
        """
        return "single_utterance_correction"

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

    def _build_error_instructions(self, parameters: dict) -> str:
        """Build error generation instructions from parameters.

        Args:
            parameters: Test parameters

        Returns:
            Error instruction text
        """
        instructions = []

        # Punctuation errors
        if parameters.get("punctuation_errors") in ["minor", "severe"]:
            level = parameters["punctuation_errors"]
            instructions.append(
                f"- Punctuation errors ({level}): missing commas/periods, incorrect spacing"
            )

        # Slang/profanity/emoji
        if parameters.get("slang_profanity_emoji") in ["moderate", "excessive"]:
            level = parameters["slang_profanity_emoji"]
            instructions.append(
                f"- Slang/emoji ({level}): informal language, excessive emojis"
            )

        # Caps/exclamation
        if parameters.get("caps_exclamation"):
            instructions.append(
                "- Excessive caps and exclamation marks: КАПСЛОК!!! and multiple !!!"
            )

        # Medical terms
        if parameters.get("medical_terms") == "present":
            instructions.append(
                "- Include medical terms but DON'T corrupt them (they should remain correct)"
            )

        # Phrase length
        phrase_length = parameters.get("phrase_length", "medium")
        instructions.append(f"- Message length: {phrase_length}")

        if not instructions:
            return "Generate typical operator errors (punctuation, tone, formatting)"

        return "\n".join(instructions)

    def _generate_example_id(self, test_case_id: str) -> str:
        """Generate unique example ID from test case ID.

        Args:
            test_case_id: Test case identifier

        Returns:
            Example ID with ex_ prefix
        """
        base = test_case_id.replace("tc_", "")
        import uuid

        unique_suffix = str(uuid.uuid4())[:8]
        return f"ex_{base}_{unique_suffix}"


class DialogLastTurnCorrectionAdapter(FormatAdapter):
    """Adapter for generating dialog_last_turn_correction format examples.

    Generates multi-turn dialogs (2+ messages) ending with an operator message
    that contains errors, and its corrected version.
    """

    def __init__(self, case: str = "operator_quality"):
        """Initialize adapter with case identifier.

        Args:
            case: Case identifier (default: operator_quality)
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
        """Generate a dialog_last_turn_correction format example.

        Args:
            use_case_id: Use case identifier
            test_case_id: Test case identifier
            parameters: Test parameters (user_aggression, escalation_needed, etc.)
            policies: List of policy dicts
            model: Model to use for generation
            seed: Random seed for reproducibility

        Returns:
            DatasetExample in dialog_last_turn_correction format
        """
        logger.info(
            f"Generating dialog_last_turn_correction example for {test_case_id} with parameters: {parameters}"
        )

        policies_text = self._format_policies(policies)
        error_instructions = self._build_error_instructions(parameters)
        context_instructions = self._build_context_instructions(parameters)

        # Build system prompt
        system_prompt = f"""You are a dataset generation assistant. Generate a customer-operator dialog in RUSSIAN.

POLICIES AND QUALITY RULES:
{policies_text}

DIALOG CONTEXT:
{context_instructions}

ERROR PARAMETERS (for last operator message - generate MIXED errors):
{error_instructions}

TASK:
Generate a realistic dialog between customer and operator (minimum 2 messages, can be 3-5 for realism).

CRITICAL REQUIREMENTS:
1. Dialog MUST end with an operator message (last role must be 'operator')
2. The last operator message MUST contain MIXED ERRORS matching the parameters
3. Dialog should reflect the context (user aggression, escalation scenarios, etc.)
4. If escalation_needed=yes: the corrected message should offer escalation
5. Generate 2-5 messages total (realistic dialog flow)
6. All messages in Russian
7. Return messages as list of dicts with 'role' and 'content' keys
8. Provide corrected version of the last operator message
9. Include 3+ evaluation criteria considering CONTEXT
10. Reference relevant policy IDs

EXAMPLE STRUCTURE:
[
  {{"role": "user", "content": "Customer question or complaint"}},
  {{"role": "operator", "content": "Operator response with errors (last message)"}}
]

For escalation scenarios, the corrected message should include full text like:
"Понимаю ваше недовольство. Давайте отменим запись: подскажите, пожалуйста, вашу фамилию и время приёма. Если вам удобнее, могу передать диалог старшему специалисту."
"""

        # Call OpenAI structured outputs
        client = get_openai_client()

        kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": "Generate the dialog last turn correction example with context-aware MIXED errors now.",
                },
            ],
            "temperature": 0,
        }

        if seed is not None:
            kwargs["seed"] = seed

        response = client.beta.chat.completions.parse(
            response_format=DialogLastTurnCorrectionOutput, **kwargs
        )

        output = response.choices[0].message.parsed

        # Convert dialog messages to Message objects
        messages = [
            Message(role=msg["role"], content=msg["content"])
            for msg in output.dialog_messages
        ]

        # Generate unique example ID
        example_id = self._generate_example_id(test_case_id)

        # Create DatasetExample
        example = DatasetExample(
            id=example_id,
            case=self.case,
            format="dialog_last_turn_correction",
            use_case_id=use_case_id,
            test_case_id=test_case_id,
            input=InputData(
                messages=messages,
                target_message_index=len(messages) - 1,
            ),
            expected_output=output.corrected_last_turn,
            evaluation_criteria=output.evaluation_criteria,
            policy_ids=output.relevant_policy_ids,
            metadata={
                "generator": "dialog_last_turn_correction_adapter",
                "model": model,
            },
        )

        logger.info(f"Generated example {example_id}")
        return example

    def validate_format(self, example: DatasetExample) -> list[str]:
        """Validate dialog_last_turn_correction format requirements.

        Args:
            example: Dataset example to validate

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Check format field
        if example.format != "dialog_last_turn_correction":
            errors.append(
                f"Format must be 'dialog_last_turn_correction', got '{example.format}'"
            )

        # Check messages count (minimum 2)
        if len(example.input.messages) < 2:
            errors.append(
                f"dialog_last_turn_correction must have at least 2 messages, got {len(example.input.messages)}"
            )

        # Check last message role
        if example.input.messages and example.input.messages[-1].role != "operator":
            errors.append(
                f"dialog_last_turn_correction last message role must be 'operator', got '{example.input.messages[-1].role}'"
            )

        # Check target_message_index points to last message
        expected_index = len(example.input.messages) - 1
        if example.input.target_message_index != expected_index:
            errors.append(
                f"dialog_last_turn_correction target_message_index must be {expected_index}, got {example.input.target_message_index}"
            )

        return errors

    def get_format_name(self) -> str:
        """Get format name.

        Returns:
            'dialog_last_turn_correction'
        """
        return "dialog_last_turn_correction"

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

    def _build_context_instructions(self, parameters: dict) -> str:
        """Build dialog context instructions from parameters.

        Args:
            parameters: Test parameters

        Returns:
            Context instruction text
        """
        instructions = []

        # User aggression
        user_aggression = parameters.get("user_aggression", "neutral")
        if user_aggression in ["frustrated", "angry"]:
            instructions.append(
                f"- Customer tone: {user_aggression} (use appropriate language and urgency)"
            )

        # Escalation needed
        if parameters.get("escalation_needed") == "yes":
            instructions.append(
                "- Escalation scenario: customer complaint requires escalation to senior specialist"
            )

        if not instructions:
            return "Standard customer support dialog"

        return "\n".join(instructions)

    def _build_error_instructions(self, parameters: dict) -> str:
        """Build error generation instructions from parameters.

        Args:
            parameters: Test parameters

        Returns:
            Error instruction text
        """
        instructions = []

        # Punctuation errors
        if parameters.get("punctuation_errors") in ["minor", "severe"]:
            level = parameters["punctuation_errors"]
            instructions.append(
                f"- Punctuation errors ({level}): missing commas/periods, incorrect spacing"
            )

        # Slang/profanity/emoji
        if parameters.get("slang_profanity_emoji") in ["moderate", "excessive"]:
            level = parameters["slang_profanity_emoji"]
            instructions.append(
                f"- Slang/emoji ({level}): informal language, excessive emojis"
            )

        # Caps/exclamation
        if parameters.get("caps_exclamation"):
            instructions.append(
                "- Excessive caps and exclamation marks: КАПСЛОК!!! and multiple !!!"
            )

        # Medical terms
        if parameters.get("medical_terms") == "present":
            instructions.append(
                "- Include medical terms but DON'T corrupt them (they should remain correct)"
            )

        # Phrase length
        phrase_length = parameters.get("phrase_length", "medium")
        instructions.append(f"- Message length: {phrase_length}")

        if not instructions:
            return "Generate typical operator errors (punctuation, tone, formatting)"

        return "\n".join(instructions)

    def _generate_example_id(self, test_case_id: str) -> str:
        """Generate unique example ID from test case ID.

        Args:
            test_case_id: Test case identifier

        Returns:
            Example ID with ex_ prefix
        """
        base = test_case_id.replace("tc_", "")
        import uuid

        unique_suffix = str(uuid.uuid4())[:8]
        return f"ex_{base}_{unique_suffix}"
