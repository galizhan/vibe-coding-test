"""Test dataset generation package.

This package provides generators for creating test cases and dataset examples
from policy documents using various frameworks (DeepEval, Ragas, Giskard) and
a direct OpenAI fallback.
"""

from dataset_generator.generation.fallback import generate_with_openai_fallback

__all__ = ["generate_with_openai_fallback"]
