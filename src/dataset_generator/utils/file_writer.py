"""JSON file output utilities for Pydantic models."""

import json
import sys
from pathlib import Path
from pydantic import BaseModel


def write_json_output(model: BaseModel, output_path: Path) -> None:
    """Write Pydantic model to JSON file with Russian text support.

    Args:
        model: Pydantic model instance to serialize
        output_path: Path where JSON file will be written

    Notes:
        - Creates parent directories if they don't exist
        - Uses ensure_ascii=False for readable Russian text
        - Uses indent=2 for human-readable formatting
        - Writes with utf-8 encoding
        - Prints confirmation to stderr (not stdout)
    """
    # Create parent directories
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Serialize with Russian text support
    # Pydantic v2 model_dump_json() doesn't support ensure_ascii parameter
    # so we use json.dumps with model.model_dump() instead
    json_data = json.dumps(
        model.model_dump(),
        indent=2,
        ensure_ascii=False
    )

    # Write to file
    output_path.write_text(json_data, encoding='utf-8')

    # Confirmation to stderr (not stdout)
    print(f"Wrote {output_path}", file=sys.stderr)
