"""Test case model for parameterized test scenarios."""

from pydantic import BaseModel, Field, field_validator


class TestCase(BaseModel):
    """A test case representing a parameterized variation of a use case.

    Test case IDs must start with "tc_" prefix for traceability.
    Each test case must have 2-3 parameter variation axes per PIPE-04.
    """

    id: str = Field(..., description="Unique identifier with tc_ prefix")
    use_case_id: str = Field(
        ..., description="Reference to the use case (must start with uc_)"
    )
    name: str = Field(..., description="Short descriptive name of the test case")
    description: str = Field(
        ..., description="Detailed description of what this test case covers"
    )
    parameter_variation_axes: list[str] = Field(
        ...,
        description="Dimensions along which the test varies (e.g., tone, language complexity, policy boundary)",
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata including generator field for framework tracking",
    )
    case: str = Field(
        default="", description="Case identifier"
    )
    parameters: dict = Field(
        default_factory=dict,
        description="Test case parameter values per tz.md (e.g., tone=negative, has_order_id=true)",
    )
    policy_ids: list[str] = Field(
        default_factory=list, description="List of relevant policy IDs"
    )

    @field_validator("id")
    @classmethod
    def id_must_start_with_tc(cls, v: str) -> str:
        """Ensure ID starts with tc_ prefix."""
        if not v.startswith("tc_"):
            raise ValueError(f"TestCase ID must start with 'tc_', got: {v}")
        return v

    @field_validator("use_case_id")
    @classmethod
    def use_case_id_must_start_with_uc(cls, v: str) -> str:
        """Ensure use_case_id starts with uc_ prefix."""
        if not v.startswith("uc_"):
            raise ValueError(
                f"TestCase use_case_id must start with 'uc_', got: {v}"
            )
        return v

    @field_validator("parameter_variation_axes")
    @classmethod
    def axes_must_be_2_to_3(cls, v: list[str]) -> list[str]:
        """Ensure 2-3 parameter variation axes per PIPE-04."""
        if not (2 <= len(v) <= 3):
            raise ValueError(
                f"TestCase must have 2-3 parameter_variation_axes, got: {len(v)}"
            )
        return v

    @field_validator("policy_ids")
    @classmethod
    def policy_ids_must_start_with_pol(cls, v: list[str]) -> list[str]:
        """Ensure all policy_ids start with pol_ prefix (if list is non-empty)."""
        for policy_id in v:
            if not policy_id.startswith("pol_"):
                raise ValueError(
                    f"All policy_ids must start with 'pol_', got: {policy_id}"
                )
        return v


class TestCaseList(BaseModel):
    """Container for a list of test cases."""

    test_cases: list[TestCase] = Field(..., description="List of test cases")
