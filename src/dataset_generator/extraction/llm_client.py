"""OpenAI client wrapper with structured outputs and retry logic."""

import os
from typing import TypeVar

from openai import OpenAI, RateLimitError
from pydantic import BaseModel
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
)


T = TypeVar("T", bound=BaseModel)


def get_openai_client() -> OpenAI:
    """Get OpenAI client instance.

    Returns:
        OpenAI client

    Raises:
        ValueError: If OPENAI_API_KEY is not set
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please set it in your .env file or environment."
        )
    return OpenAI(api_key=api_key)


@retry(
    wait=wait_random_exponential(min=1, max=60),
    stop=stop_after_attempt(6),
    retry=retry_if_exception_type(RateLimitError),
)
def call_openai_structured(
    messages: list[dict],
    response_format: type[T],
    model: str = "gpt-4o-mini",
    seed: int | None = None,
    temperature: float = 0,
) -> T:
    """Call OpenAI API with structured output format.

    Args:
        messages: List of message dicts with role and content
        response_format: Pydantic model class for structured output
        model: Model name (default: gpt-4o-mini)
        seed: Random seed for reproducibility (optional)
        temperature: Temperature for sampling (default: 0 for reproducibility)

    Returns:
        Parsed response as instance of response_format

    Raises:
        RateLimitError: If rate limit exceeded after retries
        OpenAI API errors: Various OpenAI API exceptions

    Notes:
        - Uses @retry decorator with exponential backoff for rate limits
        - Temperature is always 0 for reproducibility (per REPR-02 requirement)
        - Seed is passed if provided for deterministic outputs
    """
    client = get_openai_client()

    # Build API call kwargs
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    # Add seed if provided
    if seed is not None:
        kwargs["seed"] = seed

    # Call structured output API
    response = client.beta.chat.completions.parse(
        response_format=response_format,
        **kwargs
    )

    return response.choices[0].message.parsed
