"""Ragas generator using TestsetGenerator with distribution control."""

import logging
from typing import TYPE_CHECKING

from langchain_community.document_loaders import TextLoader
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas.testset import TestsetGenerator
from ragas.testset.synthesizers import (
    QueryDistribution,
    SingleHopSpecificQuerySynthesizer,
    MultiHopAbstractQuerySynthesizer,
    MultiHopSpecificQuerySynthesizer,
)

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


def generate_with_ragas(
    document_paths: list[str],
    test_size: int = 10,
    reasoning_ratio: float = 0.4,
    model: str = "gpt-4o-mini",
) -> "pd.DataFrame":
    """Generate RAG-specific test questions using Ragas TestsetGenerator.

    Uses knowledge graph transformations to produce diverse question types
    with configurable distributions.

    Args:
        document_paths: List of paths to document files
        test_size: Number of test questions to generate (default: 10)
        reasoning_ratio: Proportion of reasoning questions (default: 0.4)
        model: Model name to use (default: gpt-4o-mini)

    Returns:
        Ragas testset as pandas DataFrame with columns:
        - question
        - ground_truth
        - contexts
        - evolution_type
        - metadata

    Raises:
        RuntimeError: If generation fails

    Example:
        >>> df = generate_with_ragas(
        ...     document_paths=["policy.md"],
        ...     test_size=10,
        ...     reasoning_ratio=0.4
        ... )
    """
    try:
        logger.info(
            f"Generating {test_size} test questions from {len(document_paths)} documents using Ragas"
        )

        # Load documents using langchain loaders
        documents = []
        for doc_path in document_paths:
            loader = TextLoader(doc_path, encoding="utf-8")
            documents.extend(loader.load())

        logger.info(f"Loaded {len(documents)} document chunks")

        # Initialize langchain components for Ragas v0.4 API
        llm = ChatOpenAI(model=model)
        embeddings = OpenAIEmbeddings()

        # Create TestsetGenerator with langchain components
        generator = TestsetGenerator.from_langchain(
            llm=llm,
            embedding_model=embeddings,
        )

        # Configure question type distributions for Ragas v0.4
        # SingleHop: straightforward single-document questions
        # MultiHopAbstract: reasoning questions requiring inference
        # MultiHopSpecific: multi-context questions requiring combining contexts
        simple_ratio = 1.0 - reasoning_ratio - 0.2
        query_distribution = QueryDistribution(
            SingleHopSpecificQuerySynthesizer=simple_ratio,
            MultiHopAbstractQuerySynthesizer=reasoning_ratio,
            MultiHopSpecificQuerySynthesizer=0.2,
        )

        logger.info(
            f"Distributions: simple={simple_ratio}, reasoning={reasoning_ratio}, "
            f"multi_context=0.2"
        )
        logger.info("Starting Ragas testset generation...")

        # Generate testset with Ragas v0.4 API
        testset = generator.generate_with_langchain_docs(
            documents=documents,
            testset_size=test_size,
            query_distribution=query_distribution,
        )

        # Convert to pandas DataFrame
        df = testset.to_pandas()

        logger.info(f"Successfully generated {len(df)} test questions using Ragas")
        return df

    except Exception as e:
        logger.error(f"Ragas generation failed: {e}", exc_info=True)
        raise RuntimeError(f"Ragas generation failed: {e}") from e
