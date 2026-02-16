"""Dataset example model for test data instances."""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class Message(BaseModel):
    """A single message in a conversation."""

    role: Literal["user", "operator", "assistant", "system"] = Field(
        ..., description="Role of the message sender"
    )
    content: str = Field(..., description="Content of the message")


class InputData(BaseModel):
    """Input data structure containing conversation messages."""

    messages: list[Message] = Field(
        ..., min_length=1, description="List of conversation messages"
    )
    target_message_index: Optional[int] = Field(
        default=None,
        description="For dialog_last_turn_correction: index of operator message to correct",
    )

    @model_validator(mode="after")
    def validate_target_message_index(self) -> "InputData":
        """Validate target_message_index if set."""
        if self.target_message_index is not None:
            # Check it's within range
            if not (0 <= self.target_message_index < len(self.messages)):
                raise ValueError(
                    f"target_message_index={self.target_message_index} is out of range "
                    f"for messages list of length {len(self.messages)}"
                )
            # Check that the target message is from operator
            target_msg = self.messages[self.target_message_index]
            if target_msg.role != "operator":
                raise ValueError(
                    f"target_message_index must point to an operator message, "
                    f"but messages[{self.target_message_index}].role={target_msg.role}"
                )
        return self


class DatasetExample(BaseModel):
    """A dataset example instance with inputs, expected outputs, and evaluation criteria.

    Dataset example IDs must start with "ex_" prefix for traceability.
    Must have 3+ evaluation_criteria and 1+ policy_ids per DATA-07.
    """

    id: str = Field(..., description="Unique identifier with ex_ prefix")
    case: str = Field(
        ..., description="Case identifier (e.g., support_bot, operator_quality)"
    )
    format: str = Field(
        ...,
        description="Format type (e.g., single_turn_qa, single_utterance_correction, dialog_last_turn_correction)",
    )
    use_case_id: str = Field(
        ..., description="Reference to the use case (must start with uc_)"
    )
    test_case_id: str = Field(
        ..., description="Reference to the test case (must start with tc_)"
    )
    input: InputData = Field(..., description="Input data with conversation messages")
    expected_output: str = Field(..., description="Expected response")
    evaluation_criteria: list[str] = Field(
        ..., description="List of evaluation criteria (minimum 3 per DATA-07)"
    )
    policy_ids: list[str] = Field(
        ..., description="List of policy IDs (minimum 1, must start with pol_)"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata including generator field for framework tracking",
    )

    @field_validator("id")
    @classmethod
    def id_must_start_with_ex(cls, v: str) -> str:
        """Ensure ID starts with ex_ prefix."""
        if not v.startswith("ex_"):
            raise ValueError(f"DatasetExample ID must start with 'ex_', got: {v}")
        return v

    @field_validator("use_case_id")
    @classmethod
    def use_case_id_must_start_with_uc(cls, v: str) -> str:
        """Ensure use_case_id starts with uc_ prefix."""
        if not v.startswith("uc_"):
            raise ValueError(
                f"DatasetExample use_case_id must start with 'uc_', got: {v}"
            )
        return v

    @field_validator("test_case_id")
    @classmethod
    def test_case_id_must_start_with_tc(cls, v: str) -> str:
        """Ensure test_case_id starts with tc_ prefix."""
        if not v.startswith("tc_"):
            raise ValueError(
                f"DatasetExample test_case_id must start with 'tc_', got: {v}"
            )
        return v

    @field_validator("evaluation_criteria")
    @classmethod
    def evaluation_criteria_min_3(cls, v: list[str]) -> list[str]:
        """Ensure at least 3 evaluation criteria per DATA-07."""
        if len(v) < 3:
            raise ValueError(
                f"DatasetExample must have at least 3 evaluation_criteria, got: {len(v)}"
            )
        return v

    @field_validator("policy_ids")
    @classmethod
    def policy_ids_min_1_and_start_with_pol(cls, v: list[str]) -> list[str]:
        """Ensure at least 1 policy_id and all start with pol_ prefix."""
        if len(v) < 1:
            raise ValueError(
                f"DatasetExample must have at least 1 policy_id, got: {len(v)}"
            )
        for policy_id in v:
            if not policy_id.startswith("pol_"):
                raise ValueError(
                    f"All policy_ids must start with 'pol_', got: {policy_id}"
                )
        return v


class DatasetExampleList(BaseModel):
    """Container for a list of dataset examples."""

    examples: list[DatasetExample] = Field(..., description="List of dataset examples")
