"""Langfuse integration for uploading datasets."""

from datetime import datetime
from typing import Optional

from ..models.dataset_example import DatasetExample


def upload_to_langfuse(
    dataset_name: str,
    examples: list[DatasetExample],
    public_key: str,
    secret_key: str,
    host: str | None = None,
) -> dict:
    """Upload dataset examples to Langfuse.

    Args:
        dataset_name: Name for the Langfuse dataset
        examples: List of dataset examples to upload
        public_key: Langfuse public API key
        secret_key: Langfuse secret API key
        host: Optional custom Langfuse host URL (defaults to https://cloud.langfuse.com)

    Returns:
        Dict with upload status: {"dataset_name": str, "items_uploaded": int, "status": str}

    Raises:
        ImportError: If langfuse package is not installed
        Exception: For any Langfuse API errors
    """
    # Lazy import to allow core functionality without langfuse installed
    try:
        from langfuse import Langfuse
    except ImportError:
        raise ImportError(
            "langfuse not installed. Run: pip install dataset-generator[langfuse]"
        )

    # Create Langfuse client
    client = Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=host,
    )

    # Create dataset with metadata
    timestamp = datetime.utcnow().isoformat()
    client.create_dataset(
        name=dataset_name,
        description=f"Generated dataset uploaded at {timestamp}",
        metadata={
            "generator": "dataset-generator",
            "version": "0.1.0",
            "timestamp": timestamp,
            "example_count": len(examples),
        },
    )

    # Upload each example as a dataset item
    for example in examples:
        # Prepare input structure with messages and case/format context
        input_data = {
            "messages": [msg.model_dump() for msg in example.input.messages],
            "case": example.case,
            "format": example.format,
        }

        # Add target_message_index if present (for dialog_last_turn_correction)
        if example.input.target_message_index is not None:
            input_data["target_message_index"] = example.input.target_message_index

        # Prepare metadata with evaluation context
        metadata = {
            "use_case_id": example.use_case_id,
            "test_case_id": example.test_case_id,
            "policy_ids": example.policy_ids,
            "evaluation_criteria": example.evaluation_criteria,
            **example.metadata,  # Include any additional metadata from example
        }

        # Create dataset item
        client.create_dataset_item(
            dataset_name=dataset_name,
            input=input_data,
            expected_output=example.expected_output,
            metadata=metadata,
        )

    # Flush to ensure all items are uploaded (SDK batches by default)
    client.flush()

    return {
        "dataset_name": dataset_name,
        "items_uploaded": len(examples),
        "status": "success",
    }
