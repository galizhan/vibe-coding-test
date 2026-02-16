"""Use case model for extracted user scenarios."""

from pydantic import BaseModel, Field, field_validator

from .evidence import Evidence


class UseCase(BaseModel):
    """A use case extracted from the requirements document.

    Use case IDs must start with "uc_" prefix for traceability.
    """

    id: str = Field(..., description="Unique identifier with uc_ prefix")
    name: str = Field(..., description="Short name of the use case")
    description: str = Field(..., description="Detailed description of the use case")
    evidence: list[Evidence] = Field(
        ..., description="Evidence references to source document"
    )

    @field_validator("id")
    @classmethod
    def id_must_start_with_uc(cls, v: str) -> str:
        """Ensure ID starts with uc_ prefix."""
        if not v.startswith("uc_"):
            raise ValueError(f"UseCase ID must start with 'uc_', got: {v}")
        return v

    @field_validator("evidence")
    @classmethod
    def evidence_must_not_be_empty(cls, v: list[Evidence]) -> list[Evidence]:
        """Ensure at least one evidence item exists."""
        if not v or len(v) == 0:
            raise ValueError("UseCase must have at least 1 evidence item")
        return v


class UseCaseList(BaseModel):
    """Container for a list of use cases."""

    use_cases: list[UseCase] = Field(..., description="List of extracted use cases")
