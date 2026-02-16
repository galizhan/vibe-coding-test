"""LLM-based case and format auto-detection from document content."""

import logging
from typing import Literal

from pydantic import BaseModel, Field

from ..extraction.llm_client import get_openai_client

logger = logging.getLogger(__name__)


class CaseFormatDetection(BaseModel):
    """Detection result for case and applicable dataset formats."""

    case: Literal["support_bot", "operator_quality", "doctor_booking"] = Field(
        ..., description="Detected case/domain"
    )
    formats: list[
        Literal[
            "single_turn_qa",
            "single_utterance_correction",
            "dialog_last_turn_correction",
        ]
    ] = Field(
        ...,
        description="List of applicable dataset formats (can be multiple)",
        min_length=1,
    )
    reasoning: str = Field(..., description="Brief explanation of classification")


def detect_case_and_formats(
    use_cases: list, policies: list, model: str = "gpt-4o-mini"
) -> CaseFormatDetection:
    """Detect case and applicable formats from extracted use cases and policies.

    This function uses OpenAI structured outputs to classify a document's case
    (support_bot, operator_quality, doctor_booking) and determine which dataset
    formats are applicable based ONLY on content - never using filename.

    Args:
        use_cases: List of extracted UseCase objects
        policies: List of extracted Policy objects
        model: OpenAI model to use (default: gpt-4o-mini)

    Returns:
        CaseFormatDetection with case, formats, and reasoning

    Notes:
        - Classification is based ONLY on content (use cases, policies)
        - Multiple formats can be returned (e.g., operator_quality uses both
          single_utterance_correction and dialog_last_turn_correction)
        - If LLM returns empty formats, defaults to ["single_turn_qa"]
        - If parsing fails, returns default: case="support_bot", formats=["single_turn_qa"]
    """
    # Build summary string from use cases and policies
    use_case_summary = "\n".join(
        [
            f"- {uc.name}: {uc.description[:100]}"
            for uc in use_cases[:10]  # Limit to first 10 to avoid token limits
        ]
    )

    policy_summary = "\n".join(
        [
            f"- [{pol.type}] {pol.name}: {pol.description[:100]}"
            for pol in policies[:10]  # Limit to first 10
        ]
    )

    # System prompt for classification
    system_prompt = """You are a document classification expert. Your task is to:
1. Classify the domain/case as one of: support_bot, operator_quality, or doctor_booking
2. Determine ALL applicable dataset formats for this case

CLASSIFICATION RULES:
- support_bot: FAQ, customer support tickets, help desk scenarios
  → Formats: ["single_turn_qa"]
- operator_quality: Message correction, quality checks, operator training
  → Formats: ["single_utterance_correction", "dialog_last_turn_correction"]
- doctor_booking: Medical appointment booking, healthcare scheduling
  → Formats: ["single_turn_qa"]

CRITICAL:
- Base your decision ONLY on the content provided (use cases and policies)
- NEVER reference or use filenames
- If multiple formats apply, include ALL of them
- Provide brief reasoning for your classification
"""

    user_prompt = f"""Analyze this document content and classify it:

USE CASES:
{use_case_summary}

POLICIES:
{policy_summary}

Classify the case and determine all applicable formats based on the content above."""

    try:
        client = get_openai_client()

        # Call structured output API with temperature=0 for reproducibility
        response = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=CaseFormatDetection,
            temperature=0,
        )

        detection = response.choices[0].message.parsed

        # Handle edge case: empty formats list (should not happen with min_length=1, but defensive)
        if not detection.formats:
            logger.warning(
                "LLM returned empty formats list, defaulting to ['single_turn_qa']"
            )
            detection.formats = ["single_turn_qa"]

        logger.info(
            f"Detected case={detection.case}, formats={detection.formats}, "
            f"reasoning={detection.reasoning[:50]}..."
        )

        return detection

    except Exception as e:
        logger.warning(
            f"Case detection failed: {e}. Returning default: case=support_bot, formats=['single_turn_qa']"
        )
        # Return safe default
        return CaseFormatDetection(
            case="support_bot",
            formats=["single_turn_qa"],
            reasoning=f"Default fallback due to detection error: {str(e)[:50]}",
        )
