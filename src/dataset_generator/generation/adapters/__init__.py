"""Framework output adapters package.

Provides hardcoded Python adapters that convert framework-native outputs
to project Pydantic data contracts (TestCase and DatasetExample).
"""

from dataset_generator.generation.adapters.deepeval_adapter import (
    adapt_deepeval_golden_to_test_case,
    adapt_deepeval_golden_to_example,
)
from dataset_generator.generation.adapters.ragas_adapter import (
    adapt_ragas_row_to_test_case,
    adapt_ragas_row_to_example,
)
from dataset_generator.generation.adapters.giskard_adapter import (
    adapt_giskard_row_to_test_case,
    adapt_giskard_row_to_example,
)

__all__ = [
    "adapt_deepeval_golden_to_test_case",
    "adapt_deepeval_golden_to_example",
    "adapt_ragas_row_to_test_case",
    "adapt_ragas_row_to_example",
    "adapt_giskard_row_to_test_case",
    "adapt_giskard_row_to_example",
]
