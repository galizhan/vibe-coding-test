"""Giskard generator using RAGET for knowledge base test generation."""

import logging
from typing import TYPE_CHECKING

from giskard.rag import KnowledgeBase, generate_testset

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


def generate_with_giskard(
    knowledge_base_df: "pd.DataFrame",
    num_questions: int = 20,
    agent_description: str = "Customer support agent with policy knowledge base access",
    language: str = "ru",
) -> "pd.DataFrame":
    """Generate knowledge-base-derived test questions using Giskard RAGET.

    Uses knowledge base to produce business-oriented test questions for
    validating RAG system behavior.

    Args:
        knowledge_base_df: DataFrame with knowledge base content
        num_questions: Number of questions to generate (default: 20)
        agent_description: Description of agent role (default: customer support)
        language: Language code for questions (default: ru)

    Returns:
        Giskard testset as pandas DataFrame with columns:
        - question
        - reference_answer
        - reference_context
        - metadata

    Raises:
        RuntimeError: If generation fails

    Warning:
        Giskard generation is SLOW (15+ min for 60 questions per research).
        Start with smaller num_questions for testing.

    Example:
        >>> import pandas as pd
        >>> kb_df = pd.DataFrame({"content": ["Policy text..."]})
        >>> df = generate_with_giskard(
        ...     knowledge_base_df=kb_df,
        ...     num_questions=20,
        ...     language="ru"
        ... )
    """
    try:
        logger.info(
            f"Generating {num_questions} test questions from knowledge base using Giskard RAGET"
        )
        logger.warning(
            f"Giskard generation is slow (~15+ min for 60 questions). "
            f"Current request: {num_questions} questions"
        )

        # Create knowledge base from DataFrame
        # Assuming DataFrame has a 'content' column with text data
        kb = KnowledgeBase.from_pandas(knowledge_base_df, columns=["content"])

        logger.info(f"Knowledge base created with {len(knowledge_base_df)} entries")
        logger.info("Starting Giskard testset generation (this may take several minutes)...")

        # Generate testset
        testset = generate_testset(
            kb,
            num_questions=num_questions,
            language=language,
            agent_description=agent_description,
        )

        # Convert to pandas DataFrame
        df = testset.to_pandas()

        logger.info(f"Successfully generated {len(df)} test questions using Giskard")
        return df

    except Exception as e:
        logger.error(f"Giskard generation failed: {e}", exc_info=True)
        raise RuntimeError(f"Giskard generation failed: {e}") from e
