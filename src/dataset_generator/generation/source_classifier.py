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
    evidence_quotes: list[str] | None = None,
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
        evidence_quotes: Optional evidence quotes from the use case for context

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

    # Check for FAQ indicators in use case description -> faq_paraphrase
    faq_keywords = ["FAQ", "faq", "ЧаВо", "ЧЗВ", "часто задаваемые"]
    desc_has_faq = any(kw in use_case_description for kw in faq_keywords)

    if desc_has_faq and (not adversarial or adversarial == "none"):
        logger.debug(
            "Classified as 'faq_paraphrase' due to FAQ keyword in use case description"
        )
        return "faq_paraphrase"

    # For non-obvious cases, use LLM classification
    logger.debug("Using LLM for source classification")

    evidence_context = ""
    if evidence_quotes:
        evidence_context = f"\nEVIDENCE FROM SOURCE DOCUMENT:\n" + "\n".join(
            f"- {q[:200]}" for q in evidence_quotes
        )

    try:
        system_prompt = """You are a dataset source classifier for customer support test examples.

SOURCE TYPES:
- faq_paraphrase: The generated input is a generic/standard question that could be answered directly from FAQ. It asks about common topics (delivery times, return policy, payment methods, promo codes) without specific personal details.
  Examples: "Как долго идет доставка?", "Можно ли вернуть товар?", "Какие способы оплаты?"

- tickets: The generated input resembles a real customer ticket — it includes specific details like order numbers, personal situations, complaints about specific incidents, or requests requiring account access.
  Examples: "Где мой заказ 123456?", "Промокод не применился, верните скидку", "Мне нужен инвойс для юрлица по заказу от 15.01"

- corner: Adversarial or edge case — profanity, prompt injection attempts, garbage/empty input, off-topic questions unrelated to the service.
  Examples: "вы тупые? оператор где?", "(empty message)", "ignore previous instructions"

DECISION RULE:
1. If input contains profanity, injection, garbage, or is off-topic → corner
2. If input is a generic question answerable from FAQ without specific order/account details → faq_paraphrase
3. If input mentions specific details (order numbers, dates, amounts) or describes a personal situation → tickets"""

        user_prompt = f"""USE CASE: {use_case_description}

GENERATED INPUT: {generated_input}
{evidence_context}
PARAMETERS: {parameters}

Classify this generated input as faq_paraphrase, tickets, or corner."""

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
