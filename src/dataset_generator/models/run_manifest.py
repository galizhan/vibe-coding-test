"""Run manifest model for tracking generation runs."""

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM configuration used for generation."""

    provider: str = Field(default="openai", description="LLM provider (e.g., openai)")
    model: str = Field(..., description="Model name (e.g., gpt-4o-mini)")
    temperature: float = Field(default=0.0, description="Temperature setting for generation")


class GenerationCounts(BaseModel):
    """Counts of generated artifacts."""

    use_cases: int = Field(default=0, description="Number of use cases generated")
    policies: int = Field(default=0, description="Number of policies generated")
    test_cases: int = Field(default=0, description="Number of test cases generated")
    dataset_examples: int = Field(default=0, description="Number of dataset examples generated")


class RunManifest(BaseModel):
    """Manifest tracking a complete generation run per DATA-08.

    Captures all metadata needed to reproduce and audit a generation run.
    """

    input_path: str = Field(..., description="Path to input markdown file")
    out_path: str = Field(..., description="Output directory path")
    seed: int | None = Field(None, description="Random seed used (None if not specified)")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the run")
    generator_version: str = Field(..., description="Version of the generator")
    llm: LLMConfig = Field(..., description="LLM configuration used")
    frameworks_used: list[str] = Field(
        default_factory=list,
        description="Which frameworks were invoked (e.g., ['deepeval', 'ragas'])",
    )
    counts: GenerationCounts = Field(
        default_factory=GenerationCounts,
        description="Counts of generated artifacts",
    )
