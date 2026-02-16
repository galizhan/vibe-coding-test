"""Framework-specific generators package.

Provides wrappers for DeepEval Synthesizer, Ragas TestsetGenerator, and
Giskard RAGET for generating test cases from documents.
"""

from dataset_generator.generation.generators.deepeval_gen import (
    generate_with_deepeval,
)
from dataset_generator.generation.generators.ragas_gen import generate_with_ragas
from dataset_generator.generation.generators.giskard_gen import generate_with_giskard

__all__ = [
    "generate_with_deepeval",
    "generate_with_ragas",
    "generate_with_giskard",
]
