"""Base abstract class for format-specific dataset generation adapters."""

from abc import ABC, abstractmethod
from dataset_generator.models.dataset_example import DatasetExample


class FormatAdapter(ABC):
    """Abstract base class for format-specific generation adapters.

    Each adapter implements generation logic for a specific dataset format
    (e.g., single_turn_qa, single_utterance_correction, dialog_last_turn_correction).
    """

    @abstractmethod
    def generate_example(
        self,
        use_case_id: str,
        test_case_id: str,
        parameters: dict,
        policies: list[dict],
        model: str = "gpt-4o-mini",
        seed: int | None = None,
    ) -> DatasetExample:
        """Generate a dataset example in the format-specific structure.

        Args:
            use_case_id: Use case identifier (uc_ prefix)
            test_case_id: Test case identifier (tc_ prefix)
            parameters: Test case parameters driving the scenario
            policies: List of policy dicts with id, type, description, statement
            model: Model name to use for generation
            seed: Random seed for reproducibility

        Returns:
            DatasetExample with format-specific structure
        """
        pass

    @abstractmethod
    def validate_format(self, example: DatasetExample) -> list[str]:
        """Validate that example matches format-specific requirements.

        Args:
            example: Dataset example to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        pass

    @abstractmethod
    def get_format_name(self) -> str:
        """Get the format name this adapter handles.

        Returns:
            Format name (e.g., 'single_turn_qa')
        """
        pass
