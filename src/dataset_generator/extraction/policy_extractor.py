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
    system_prompt = f"""You are an expert requirements analyst. Extract policies with CORRECT type classification from Russian-language requirements.

TASK DEFINITION (structured for clarity):
{{
  "objective": "Extract {min_policies}+ policies from document with accurate type classification",
  "id_format": "pol_NNN (e.g., pol_001, pol_002)",
  "content_language": "Russian",
  "evidence_accuracy": "CHARACTER-EXACT quotes required"
}}

POLICY TYPE DECISION TREE (check in this order for disambiguation):

Step 1: Is this a prohibition/restriction (MUST NOT do)?
→ type: "must_not"
Examples: "не должен давать медицинские рекомендации", "нельзя использовать капслок"

Step 2: Does this trigger human escalation (escalate to agent/specialist)?
→ type: "escalate"
Examples: "при медицинских вопросах — переключить на врача", "если клиент сильно недоволен — эскалация"

Step 3: Is this about communication tone/style (how to communicate)?
→ type: "style"
Examples: "сообщение должно быть вежливым", "избегать восклицательных знаков"

Step 4: Is this about output format/structure/templates (how to format)?
→ type: "format"
Examples: "исправлять опечатки и пунктуацию", "использовать маркированные списки"

Step 5: Otherwise (obligation/requirement to DO something)?
→ type: "must"
Examples: "система должна проверять корректность промокода", "бот отвечает на общие вопросы"

CLASSIFICATION PROCESS:
For each policy, analyze its nature and explain your reasoning in 1 sentence before assigning the type.
The order matters: check must_not and escalate BEFORE must, since they're special cases that need priority.

EVIDENCE EXTRACTION (CRITICAL FOR VALIDATION):
- Your evidence quote must be CHARACTER-FOR-CHARACTER EXACT
- Include ALL markdown formatting: *, **, bullets, table pipes |, etc.
- Preserve ALL whitespace at start/end of lines
- Do NOT clean up, normalize, or "fix" the quote
- Multi-line quotes: use \\n between lines, preserve each line exactly
- Line numbers shown as "N: " prefix — use these for line_start/line_end
- Do NOT include the "N: " prefix in your quote — only the actual text after it
- Extract the COMPLETE quote — do not truncate or summarize

FEW-SHOT EXAMPLES WITH CLASSIFICATION REASONING:

[Example 1: must_not type]
Source text:
20: * Бот не должен давать **медицинские рекомендации**

Your extraction:
{{
  "id": "pol_001",
  "name": "Запрет медицинских рекомендаций",
  "description": "Бот не должен давать медицинские советы или рекомендации",
  "type": "must_not",
  "evidence": [{{
    "input_file": "requirements.md",
    "line_start": 20,
    "line_end": 20,
    "quote": "* Бот не должен давать **медицинские рекомендации**"
  }}]
}}
Reasoning: This is a prohibition (not allowed to give medical advice).

[Example 2: escalate type]
Source text:
21: * При медицинских вопросах - переключить на врача

Your extraction:
{{
  "id": "pol_002",
  "name": "Эскалация медицинских вопросов",
  "description": "При вопросах медицинского характера необходимо переключить на врача",
  "type": "escalate",
  "evidence": [{{
    "input_file": "requirements.md",
    "line_start": 21,
    "line_end": 21,
    "quote": "* При медицинских вопросах - переключить на врача"
  }}]
}}
Reasoning: This describes when to escalate to a human specialist (doctor).

[Example 3: style type]
Source text:
15: Если пользователь матерится — оператор сохраняет нейтральный тон

Your extraction:
{{
  "id": "pol_003",
  "name": "Нейтральный тон при ненормативной лексике",
  "description": "Оператор должен сохранять нейтральный тон даже если пользователь использует ненормативную лексику",
  "type": "style",
  "evidence": [{{
    "input_file": "requirements.md",
    "line_start": 15,
    "line_end": 15,
    "quote": "Если пользователь матерится — оператор сохраняет нейтральный тон"
  }}]
}}
Reasoning: This is about communication style and tone rules.

[Example 4: format type]
Source text:
8: Нужно исправлять явные опечатки и пунктуацию

Your extraction:
{{
  "id": "pol_004",
  "name": "Исправление опечаток",
  "description": "Система должна автоматически исправлять очевидные опечатки и пунктуацию",
  "type": "format",
  "evidence": [{{
    "input_file": "requirements.md",
    "line_start": 8,
    "line_end": 8,
    "quote": "Нужно исправлять явные опечатки и пунктуацию"
  }}]
}}
Reasoning: This is about output formatting and text correction.

[Example 5: must type]
Source text:
12: Система должна проверять корректность промокода перед применением

Your extraction:
{{
  "id": "pol_005",
  "name": "Проверка промокода",
  "description": "Система обязана проверять корректность промокода перед его применением к заказу",
  "type": "must",
  "evidence": [{{
    "input_file": "requirements.md",
    "line_start": 12,
    "line_end": 12,
    "quote": "Система должна проверять корректность промокода перед применением"
  }}]
}}
Reasoning: This is a general requirement/obligation (not a prohibition, escalation, style, or format rule).

Now extract policies from the following document (all content must be in Russian):
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
