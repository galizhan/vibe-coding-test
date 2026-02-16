"""Policy model for business rules and constraints."""

from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator

from .evidence import Evidence

PolicyType = Literal["must", "must_not", "escalate", "style", "format"]


class Policy(BaseModel):
    """A policy/business rule extracted from the requirements document.

    Policy IDs must start with "pol_" prefix for traceability.
    """

    id: str = Field(..., description="Unique identifier with pol_ prefix")
    name: str = Field(..., description="Short name of the policy")
    description: str = Field(..., description="Detailed description of the policy")
    type: PolicyType = Field(..., description="Policy type classification")
    evidence: list[Evidence] = Field(
        ..., description="Evidence references to source document"
    )
    case: str = Field(
        default="", description="Case identifier"
    )
    statement: str = Field(
        default="",
        description="Policy statement per tz.md contract (alias for description)",
    )

    @model_validator(mode="after")
    def populate_statement_from_description(self) -> "Policy":
        """Auto-populate statement from description if statement is empty."""
        if not self.statement and self.description:
            self.statement = self.description
        return self

    @field_validator("id")
    @classmethod
    def id_must_start_with_pol(cls, v: str) -> str:
        """Ensure ID starts with pol_ prefix."""
        if not v.startswith("pol_"):
            raise ValueError(f"Policy ID must start with 'pol_', got: {v}")
        return v

    @field_validator("evidence")
    @classmethod
    def evidence_must_not_be_empty(cls, v: list[Evidence]) -> list[Evidence]:
        """Ensure at least one evidence item exists."""
        if not v or len(v) == 0:
            raise ValueError("Policy must have at least 1 evidence item")
        return v


class PolicyList(BaseModel):
    """Container for a list of policies."""

    policies: list[Policy] = Field(..., description="List of extracted policies")
