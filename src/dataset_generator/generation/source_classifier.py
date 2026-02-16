"""Metadata source classification for support bot examples."""

import logging
from typing import Literal
from pydantic import BaseModel, Field
from dataset_generator.extraction.llm_client import get_openai_client

logger = logging.getLogger(__name__)


class SourceClassification(BaseModel):
    """Source classification result."""

    source: Literal["tickets", "faq_paraphrase", "corner"] = Field(
        ..., description="Source type classification"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Classification confidence (0-1)"
    )


def classify_source_type(
    use_case_description: str,
    generated_input: str,
    parameters: dict,
    model: str = "gpt-4o-mini",
) -> str:
    """Classify metadata.source for support bot examples.

    This classifier is ONLY used for support_bot case. For other cases,
    metadata.source is not set (or empty).

    Uses heuristic checks first (fast), then LLM classification for
    non-obvious cases.

    Args:
        use_case_description: Use case description
        generated_input: The generated user input message
        parameters: Test case parameters
        model: Model to use for LLM classification (default: gpt-4o-mini)

    Returns:
        Source type: 'tickets', 'faq_paraphrase', or 'corner'

    Example:
        >>> classify_source_type('FAQ support', 'test', {'adversarial': 'profanity'})
        'corner'
        >>> classify_source_type('FAQ about delivery', 'test', {})
        'faq_paraphrase'
    """
    logger.debug(
        f"Classifying source for input: {generated_input[:50]}... with params: {parameters}"
    )

    # Quick heuristic checks (avoid LLM call when obvious)

    # Check for adversarial parameters -> corner
    adversarial = parameters.get("adversarial")
    if adversarial and adversarial in ["profanity", "injection", "garbage"]:
        logger.debug(f"Classified as 'corner' due to adversarial={adversarial}")
        return "corner"

    # Check for FAQ in use case description -> faq_paraphrase
    if ("FAQ" in use_case_description or "faq" in use_case_description) and (
        not adversarial or adversarial == "none"
    ):
        logger.debug(
            "Classified as 'faq_paraphrase' due to FAQ in use case description"
        )
        return "faq_paraphrase"

    # For non-obvious cases, use LLM classification
    logger.debug("Using LLM for source classification")

    try:
        system_prompt = """You are a dataset source classifier. Classify the source type of customer support examples.

SOURCE TYPES:
- tickets: Example derived from real customer ticket data (realistic customer inquiries)
- faq_paraphrase: Example is a paraphrase of FAQ content (questions covered in FAQs)
- corner: Adversarial or edge case (profanity, prompt injection, garbage input, off-topic)

TASK:
Analyze the use case description, generated input, and parameters to classify the source type."""

        user_prompt = f"""USE CASE: {use_case_description}

GENERATED INPUT: {generated_input}

PARAMETERS: {parameters}

Classify the source type and provide confidence."""

        client = get_openai_client()

        response = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=SourceClassification,
            temperature=0,
        )

        result = response.choices[0].message.parsed
        logger.debug(
            f"LLM classified as '{result.source}' with confidence {result.confidence}"
        )
        return result.source

    except Exception as e:
        # Fallback to 'tickets' if LLM fails
        logger.warning(f"LLM classification failed: {e}, defaulting to 'tickets'")
        return "tickets"
