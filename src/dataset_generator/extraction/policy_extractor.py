"""Policy extraction from markdown using LLM structured outputs."""

import logging

from dataset_generator.models import PolicyList
from .markdown_parser import ParsedMarkdown, get_numbered_text
from .llm_client import call_openai_structured
from .evidence_validator import validate_all_evidence


logger = logging.getLogger(__name__)


def extract_policies(
    parsed: ParsedMarkdown,
    model: str = "gpt-4o-mini",
    seed: int | None = None,
    min_policies: int = 5,
) -> PolicyList:
    """Extract policies from parsed markdown using LLM.

    Args:
        parsed: ParsedMarkdown instance with source text
        model: OpenAI model name (default: gpt-4o-mini)
        seed: Random seed for reproducibility (optional)
        min_policies: Minimum number of policies to extract

    Returns:
        PolicyList with extracted policies and evidence

    Notes:
        - All content (name, description) will be in Russian per GEN-05
        - Evidence quotes must be EXACT text from source
        - Evidence validation runs after extraction with warnings logged
        - Uses temperature=0 for reproducibility
    """
    # Build system prompt
    system_prompt = f"""You are an expert requirements analyst. Extract policies/rules/constraints from the provided Russian-language requirements document.

CRITICAL INSTRUCTIONS:
1. Each policy must have a unique id starting with "pol_" (e.g., pol_001, pol_002, pol_003)
2. Each policy needs: id, name (Russian), description (Russian), type, evidence
3. ALL content (name, description) MUST be in Russian - do NOT translate to English
4. Extract at least {min_policies} policies from the document

POLICY TYPE CLASSIFICATION:
Classify each policy by type:
- "must": things the system must do (requirements, obligations)
- "must_not": things the system must not do (prohibitions, restrictions)
- "escalate": situations requiring escalation to a human agent
- "style": tone, language, communication style rules
- "format": output format requirements (structure, templates, formatting)

EVIDENCE REQUIREMENTS:
- Evidence must have: input_file, line_start (1-based), line_end (1-based), quote
- The quote field must contain the EXACT text from the specified lines
- Copy the text character-for-character. Do NOT paraphrase, modify, or translate
- Line numbers are shown at the start of each line as 'N: '
- Use these line numbers to set line_start and line_end
- Do NOT include the line number prefix in the quote - only the actual text after "N: "

EXAMPLE:
If the source shows:
20: Бот не должен давать медицинские рекомендации
21: При медицинских вопросах - переключить на врача

Your evidence should be:
{{
  "input_file": "filename.md",
  "line_start": 20,
  "line_end": 21,
  "quote": "Бот не должен давать медицинские рекомендации\\nПри медицинских вопросах - переключить на врача"
}}

And the policy type might be "must_not" (no medical advice) or "escalate" (transfer to doctor).
"""

    # Build user message with numbered text
    numbered_text = get_numbered_text(parsed)
    user_message = f"File: {parsed.file_path.name}\n\n{numbered_text}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    # Call LLM with structured output
    logger.info(f"Extracting policies from {parsed.file_path.name} with model={model}, seed={seed}")
    result = call_openai_structured(
        messages=messages,
        response_format=PolicyList,
        model=model,
        seed=seed,
        temperature=0,
    )

    # Validate evidence
    valid_count, invalid_count, errors = validate_all_evidence(parsed, result.policies)

    if invalid_count > 0:
        logger.warning(
            f"Evidence validation: {valid_count} valid, {invalid_count} invalid"
        )
        for error in errors:
            logger.warning(f"  {error}")
    else:
        logger.info(f"Evidence validation: all {valid_count} quotes valid")

    logger.info(f"Extracted {len(result.policies)} policies")

    return result
