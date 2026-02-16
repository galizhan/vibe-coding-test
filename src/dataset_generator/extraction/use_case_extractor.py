"""Use case extraction from markdown using LLM structured outputs."""

import logging

from dataset_generator.models import UseCaseList
from .markdown_parser import ParsedMarkdown, get_numbered_text
from .llm_client import call_openai_structured
from .evidence_validator import validate_all_evidence


logger = logging.getLogger(__name__)


def extract_use_cases(
    parsed: ParsedMarkdown,
    model: str = "gpt-4o-mini",
    seed: int | None = None,
    min_use_cases: int = 5,
) -> UseCaseList:
    """Extract use cases from parsed markdown using LLM.

    Args:
        parsed: ParsedMarkdown instance with source text
        model: OpenAI model name (default: gpt-4o-mini)
        seed: Random seed for reproducibility (optional)
        min_use_cases: Minimum number of use cases to extract

    Returns:
        UseCaseList with extracted use cases and evidence

    Notes:
        - All content (name, description) will be in Russian per GEN-05
        - Evidence quotes must be EXACT text from source
        - Evidence validation runs after extraction with warnings logged
        - Uses temperature=0 for reproducibility
    """
    # Build system prompt
    system_prompt = f"""You are an expert requirements analyst. Extract structured use cases from the provided Russian-language requirements document.

CRITICAL INSTRUCTIONS:
1. Each use case must have a unique id starting with "uc_" (e.g., uc_001, uc_002, uc_003)
2. Each use case needs: id, name (Russian), description (Russian), evidence
3. ALL content (name, description) MUST be in Russian - do NOT translate to English
4. Extract at least {min_use_cases} use cases from the document

EVIDENCE REQUIREMENTS:
- Evidence must have: input_file, line_start (1-based), line_end (1-based), quote
- The quote field must contain the EXACT text from the specified lines
- Copy the text character-for-character. Do NOT paraphrase, modify, or translate
- Line numbers are shown at the start of each line as 'N: '
- Use these line numbers to set line_start and line_end
- Do NOT include the line number prefix in the quote - only the actual text after "N: "

EXAMPLE:
If the source shows:
15: Клиент может запросить информацию о статусе заказа
16: Система должна предоставить актуальный статус

Your evidence should be:
{{
  "input_file": "filename.md",
  "line_start": 15,
  "line_end": 16,
  "quote": "Клиент может запросить информацию о статусе заказа\\nСистема должна предоставить актуальный статус"
}}
"""

    # Build user message with numbered text
    numbered_text = get_numbered_text(parsed)
    user_message = f"File: {parsed.file_path.name}\n\n{numbered_text}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    # Call LLM with structured output
    logger.info(f"Extracting use cases from {parsed.file_path.name} with model={model}, seed={seed}")
    result = call_openai_structured(
        messages=messages,
        response_format=UseCaseList,
        model=model,
        seed=seed,
        temperature=0,
    )

    # Validate evidence
    valid_count, invalid_count, errors = validate_all_evidence(parsed, result.use_cases)

    if invalid_count > 0:
        logger.warning(
            f"Evidence validation: {valid_count} valid, {invalid_count} invalid"
        )
        for error in errors:
            logger.warning(f"  {error}")
    else:
        logger.info(f"Evidence validation: all {valid_count} quotes valid")

    logger.info(f"Extracted {len(result.use_cases)} use cases")

    return result
