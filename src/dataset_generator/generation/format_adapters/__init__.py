"""Format-specific generation adapters for dataset examples."""

from dataset_generator.generation.format_adapters.base import FormatAdapter
from dataset_generator.generation.format_adapters.single_turn_qa import (
    SingleTurnQAAdapter,
)
from dataset_generator.generation.format_adapters.operator_corrections import (
    SingleUtteranceCorrectionAdapter,
    DialogLastTurnCorrectionAdapter,
)

__all__ = [
    "FormatAdapter",
    "SingleTurnQAAdapter",
    "SingleUtteranceCorrectionAdapter",
    "DialogLastTurnCorrectionAdapter",
    "get_adapter_for_format",
]


def get_adapter_for_format(format_name: str, case: str) -> FormatAdapter:
    """Return the appropriate adapter for a format.

    Args:
        format_name: Format identifier (single_turn_qa, single_utterance_correction, dialog_last_turn_correction)
        case: Case identifier (support_bot, operator_quality, doctor_booking)

    Returns:
        FormatAdapter instance for the specified format

    Raises:
        ValueError: If format_name is not recognized

    Example:
        >>> adapter = get_adapter_for_format('single_turn_qa', 'support_bot')
        >>> isinstance(adapter, SingleTurnQAAdapter)
        True
    """
    adapters = {
        "single_turn_qa": SingleTurnQAAdapter,
        "single_utterance_correction": SingleUtteranceCorrectionAdapter,
        "dialog_last_turn_correction": DialogLastTurnCorrectionAdapter,
    }

    if format_name not in adapters:
        raise ValueError(
            f"Unknown format '{format_name}'. Supported formats: {list(adapters.keys())}"
        )

    adapter_class = adapters[format_name]
    return adapter_class(case=case)
