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
    system_prompt = f"""You are an expert requirements analyst. Extract use cases from Russian-language requirements.

TASK DEFINITION (structured for clarity):
{{
  "objective": "Extract {min_use_cases}+ use_cases from prose, FAQs, tables, or implicit requirements",
  "id_format": "uc_NNN (e.g., uc_001, uc_002)",
  "content_language": "Russian",
  "evidence_accuracy": "CHARACTER-EXACT quotes required"
}}

USE CASE IDENTIFICATION RULES:
1. Look for patterns indicating actions/scenarios:
   - Action patterns: "может...", "должен...", "если...то..."
   - Question-answer pairs (FAQ sections)
   - Table rows with operator responses or scenarios
   - Implicit use cases in prose (extract intent from context)
2. Each distinct user goal or system behavior is ONE use case
3. Use cases can be IMPLICIT — extract intent from context, not just explicit lists

EVIDENCE EXTRACTION (CRITICAL FOR VALIDATION):
- Your evidence quote must be CHARACTER-FOR-CHARACTER EXACT
- Include ALL markdown formatting: *, **, bullets, table pipes |, etc.
- Preserve ALL whitespace at start/end of lines
- Do NOT clean up, normalize, or "fix" the quote
- Multi-line quotes: use \\n between lines, preserve each line exactly
- Line numbers shown as "N: " prefix — use these for line_start/line_end
- Do NOT include the "N: " prefix in your quote — only the actual text after it
- Extract the COMPLETE quote — do not truncate or summarize

FEW-SHOT EXAMPLES:

[Example 1: Explicit use case from bullet list]
Source text:
5: * Клиент может запросить статус заказа

Your extraction:
{{
  "id": "uc_001",
  "name": "Запрос статуса заказа",
  "description": "Клиент запрашивает текущий статус своего заказа",
  "evidence": [{{
    "input_file": "requirements.md",
    "line_start": 5,
    "line_end": 5,
    "quote": "* Клиент может запросить статус заказа"
  }}]
}}

[Example 2: Implicit use case from prose spanning 2 lines]
Source text:
12: Если вопрос требует данных из личного кабинета — бот должен
13: передать на оператора или дать телефон поддержки.

Your extraction:
{{
  "id": "uc_002",
  "name": "Эскалация на оператора при вопросах о личном кабинете",
  "description": "При вопросах требующих доступа к личному кабинету бот эскалирует обращение на оператора",
  "evidence": [{{
    "input_file": "requirements.md",
    "line_start": 12,
    "line_end": 13,
    "quote": "Если вопрос требует данных из личного кабинета — бот должен\\nпередать на оператора или дать телефон поддержки."
  }}]
}}

[Example 3: Use case from table row preserving pipe characters]
Source text:
32: | 1001 | «Где мой заказ???» | «Понимаю. Уточните номер заказа...» |

Your extraction:
{{
  "id": "uc_003",
  "name": "Запрос информации о заказе",
  "description": "Пользователь спрашивает о местоположении или статусе заказа",
  "evidence": [{{
    "input_file": "requirements.md",
    "line_start": 32,
    "line_end": 32,
    "quote": "| 1001 | «Где мой заказ???» | «Понимаю. Уточните номер заказа...» |"
  }}]
}}

Now extract use cases from the following document (all content must be in Russian):
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
