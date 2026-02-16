"""DeepEval generator using Synthesizer with evolution techniques."""

import logging
from typing import Any

from deepeval.synthesizer import Synthesizer
from deepeval.synthesizer.config import (
    EvolutionConfig,
    FiltrationConfig,
    StylingConfig,
)
from deepeval.synthesizer.types import Evolution

logger = logging.getLogger(__name__)


def generate_with_deepeval(
    document_paths: list[str],
    num_goldens: int = 10,
    include_expected_output: bool = True,
    model: str = "gpt-4o-mini",
) -> list[Any]:
    """Generate test goldens from documents using DeepEval Synthesizer.

    This is the PRIMARY generation engine for the pipeline. Uses evolution
    techniques to create diverse test cases from policy documents.

    Args:
        document_paths: List of paths to document files
        num_goldens: Number of goldens to generate (default: 10)
        include_expected_output: Whether to include expected outputs (default: True)
        model: Model name to use (default: gpt-4o-mini)

    Returns:
        List of DeepEval Golden objects

    Raises:
        RuntimeError: If generation fails

    Example:
        >>> goldens = generate_with_deepeval(
        ...     document_paths=["policy.md"],
        ...     num_goldens=10,
        ...     model="gpt-4o-mini"
        ... )
    """
    try:
        logger.info(
            f"Generating {num_goldens} goldens from {len(document_paths)} documents using DeepEval"
        )

        # Configure evolution for diverse test case generation
        # Per research Pattern 2: use multiple evolution types
        evolution_config = EvolutionConfig(
            evolutions={
                Evolution.REASONING: 0.25,  # why does policy X apply?
                Evolution.MULTICONTEXT: 0.25,  # combine multiple policy sections
                Evolution.CONCRETIZING: 0.25,  # specific scenarios
                Evolution.CONSTRAINED: 0.25,  # edge cases with limitations
            },
            num_evolutions=2,
        )

        # Configure filtration for quality control
        filtration_config = FiltrationConfig(
            critic_model="gpt-4o",
            quality_threshold=0.7,
            max_quality_retries=3,
        )

        # Configure styling for customer support context
        styling_config = StylingConfig(
            input_format="Customer support message asking about specific policy or procedure",
            expected_output_format="Support response referencing relevant policies",
            task="Customer support query handling",
        )

        # Create synthesizer instance
        # Using async_mode=False for simpler initial implementation
        synthesizer = Synthesizer(
            model=model,
            async_mode=False,
            evolution_config=evolution_config,
            filtration_config=filtration_config,
            styling_config=styling_config,
        )

        logger.info("DeepEval Synthesizer configured, starting generation...")

        # Generate goldens from documents
        goldens = synthesizer.generate_goldens_from_docs(
            document_paths=document_paths,
            max_goldens_per_context=num_goldens,
            include_expected_output=include_expected_output,
        )

        logger.info(f"Successfully generated {len(goldens)} goldens using DeepEval")
        return goldens

    except Exception as e:
        logger.error(f"DeepEval generation failed: {e}", exc_info=True)
        raise RuntimeError(f"DeepEval generation failed: {e}") from e
