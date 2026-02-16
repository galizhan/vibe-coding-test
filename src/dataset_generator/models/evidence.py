"""Evidence model for tracing requirements back to source document."""

from typing import Annotated
from pydantic import BaseModel, Field, field_validator, model_validator


class Evidence(BaseModel):
    """Evidence linking a requirement to specific lines in the source document.

    Uses 1-based line numbering (line_start=1 is the first line of the file).
    """

    input_file: str = Field(..., description="Path to the source document")
    line_start: Annotated[int, Field(ge=1)] = Field(
        ..., description="Starting line number (1-based, must be >= 1)"
    )
    line_end: int = Field(..., description="Ending line number (must be >= line_start)")
    quote: str = Field(..., description="Exact quote from the source document")

    @field_validator("quote")
    @classmethod
    def quote_must_not_be_empty(cls, v: str) -> str:
        """Ensure quote is not empty."""
        if not v or not v.strip():
            raise ValueError("quote must not be empty")
        return v

    @model_validator(mode="after")
    def line_end_must_be_gte_line_start(self) -> "Evidence":
        """Ensure line_end >= line_start."""
        if self.line_end < self.line_start:
            raise ValueError(
                f"line_end ({self.line_end}) must be >= line_start ({self.line_start})"
            )
        return self
