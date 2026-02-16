# Phase 2: Core Extraction - Research

**Researched:** 2026-02-16
**Domain:** LLM-based extraction improvement for unstructured text with evidence traceability
**Confidence:** MEDIUM-HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
None — no decisions locked by user.

### Claude's Discretion
- Extraction strategy (single-pass vs multi-pass LLM, chunking approach)
- Evidence matching implementation (exact vs fuzzy, fallback strategies)
- Policy type classification approach (LLM-driven vs hybrid)
- Prompt design for generalization to unseen documents
- Error handling for edge cases in extraction

### Deferred Ideas (OUT OF SCOPE)
- Use DeepEval Synthesizer, Ragas, Giskard Hub for test/dataset generation — Phase 3
- OpenAI as orchestrator redirecting to external frameworks — Phase 3
</user_constraints>

## Summary

Phase 2 focuses on refining and improving the extraction pipeline built in Phase 1 to handle truly unstructured text (not relying on explicit lists), improve evidence matching accuracy, and ensure policy type classification works reliably. The current Phase 1 implementation achieves 80-100% evidence validation accuracy on structured markdown with explicit lists and tables, but Phase 2 must generalize to prose-heavy, implicit requirements.

The key technical challenges are: (1) improving evidence quote matching accuracy from ~80% to >95% through better prompt engineering and optional fuzzy matching fallbacks, (2) extracting use cases from prose without explicit list formatting, (3) reliably classifying policy types (must/must_not/escalate/style/format) from natural language constraints, and (4) ensuring the system works on unseen inputs with different structures.

Research indicates that multi-pass extraction with separate evidence-finding steps, structured JSON prompts with explicit examples, and careful whitespace/formatting preservation in LLM instructions significantly improve accuracy. For evidence matching, RapidFuzz provides fast fuzzy matching as a fallback when exact matching fails. The anti-hardcoding requirement is best served by testing against diverse document structures and using generic prompt patterns rather than document-specific instructions.

**Primary recommendation:** Implement enhanced prompt engineering with explicit formatting preservation instructions, add optional fuzzy matching fallback (RapidFuzz with 90%+ similarity threshold) for evidence validation, use structured JSON prompt format for policy type classification with few-shot examples, and test against all three provided example documents to ensure generalization.

## Standard Stack

### Core (Unchanged from Phase 1)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.10+ | Runtime | Type hints, match statements, Pydantic v2 compatibility |
| Pydantic | 2.x | Data validation | Industry standard, native OpenAI structured outputs support |
| openai | 1.x | LLM API client | Official SDK with structured outputs API (93%+ accuracy on benchmarks, 100% with constrained decoding) |
| Typer | 0.12+ | CLI framework | Type-hint-driven, minimal boilerplate |

### Supporting (New for Phase 2)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| RapidFuzz | 3.x | Fuzzy string matching | Fallback when exact evidence quote matching fails, whitespace-tolerant comparison |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| RapidFuzz | thefuzz (fuzzywuzzy) | thefuzz has GPL license (less permissive), slower (Python-based vs C++), moved to RapidFuzz by community |
| Single-pass extraction | Multi-pass with separate evidence step | Multi-pass increases recall but also confabulations and processing time; use single-pass first, only switch if evidence accuracy <80% |
| Exact matching only | Fuzzy matching only | Fuzzy matching can mask real prompt issues; use exact first with fuzzy as fallback |

**Installation:**
```bash
pip install rapidfuzz>=3.0
```

Add to `pyproject.toml`:
```toml
dependencies = [
    # ... existing deps ...
    "rapidfuzz>=3.0",
]
```

## Architecture Patterns

### Recommended Enhancements to Phase 1 Structure
```
src/dataset_generator/
├── extraction/
│   ├── markdown_parser.py       # ✓ Exists (Phase 1)
│   ├── llm_client.py             # ✓ Exists (Phase 1)
│   ├── use_case_extractor.py    # ✓ Exists - ENHANCE prompts
│   ├── policy_extractor.py      # ✓ Exists - ENHANCE prompts
│   └── evidence_validator.py    # ✓ Exists - ADD fuzzy fallback
└── utils/
    ├── file_writer.py            # ✓ Exists (Phase 1)
    └── fuzzy_matcher.py          # NEW - Fuzzy matching utilities
```

**Changes:**
- Enhance existing extractors with improved prompts (no new files)
- Add fuzzy matching fallback to evidence_validator.py
- Optional: Create utils/fuzzy_matcher.py for reusable fuzzy matching logic

### Pattern 1: Enhanced Prompt Engineering for Unstructured Text
**What:** Structured JSON prompts with explicit formatting preservation and few-shot examples
**When to use:** All extraction prompts where evidence must match source text
**Example:**
```python
# Enhanced prompt structure for use case extraction
system_prompt = """You are an expert requirements analyst. Extract use cases from unstructured Russian text.

TASK DEFINITION (JSON format for clarity):
{
  "objective": "Extract use_cases from prose, FAQs, examples, and tables",
  "constraints": {
    "minimum_count": 5,
    "id_format": "uc_001, uc_002, etc.",
    "content_language": "Russian",
    "evidence_required": true
  }
}

USE CASE IDENTIFICATION RULES:
1. Look for patterns indicating actions/scenarios:
   - "клиент может..." (client can...)
   - "система должна..." (system must...)
   - "если ... то ..." (if ... then ...)
   - Question-answer pairs in FAQ sections
   - Operator responses in ticket tables
2. Each distinct user goal or system behavior is one use case
3. Use cases can be implicit — extract intent from context

EVIDENCE EXTRACTION (CRITICAL):
- Your evidence quote must be CHARACTER-FOR-CHARACTER EXACT
- Include ALL markdown formatting: *, **, bullets, table pipes
- Preserve ALL whitespace at start/end of lines
- Do NOT clean up, normalize, or "fix" the quote
- Line numbers are shown as "N: " prefix — use these for line_start/line_end
- Do NOT include the "N: " prefix in your quote

FEW-SHOT EXAMPLES:
[Example 1: Explicit use case in list]
Source text:
5: * Клиент может запросить статус заказа
Your extraction:
{
  "id": "uc_001",
  "name": "Запрос статуса заказа",
  "description": "Клиент запрашивает текущий статус своего заказа",
  "evidence": [{
    "input_file": "requirements.md",
    "line_start": 5,
    "line_end": 5,
    "quote": "* Клиент может запросить статус заказа"
  }]
}

[Example 2: Implicit use case in prose]
Source text:
12: Если вопрос требует данных из личного кабинета — бот должен
13: передать на оператора или дать телефон поддержки.
Your extraction:
{
  "id": "uc_002",
  "name": "Эскалация на оператора",
  "description": "При вопросах требующих доступа к личному кабинету бот эскалирует обращение",
  "evidence": [{
    "input_file": "requirements.md",
    "line_start": 12,
    "line_end": 13,
    "quote": "Если вопрос требует данных из личного кабинета — бот должен\\nпередать на оператора или дать телефон поддержки."
  }]
}

Now extract use cases from the following document.
"""
```

**Source:** Based on [Prompt Patterns for Structured Data Extraction from Unstructured Text](https://www.dre.vanderbilt.edu/~schmidt/PDF/Prompt_Patterns_for_Structured_Data_Extraction_from_Unstructured_Text.pdf) and [Best practices for prompt engineering with the OpenAI API](https://help.openai.com/en/articles/6654000-best-practices-for-prompt-engineering-with-the-openai-api)

### Pattern 2: Fuzzy Matching Fallback for Evidence Validation
**What:** Try exact match first, fall back to high-threshold fuzzy match if exact fails
**When to use:** Evidence validation when LLM occasionally drops trailing whitespace or markdown formatting
**Example:**
```python
# In evidence_validator.py
from rapidfuzz import fuzz

def validate_evidence_quote(
    parsed: ParsedMarkdown,
    evidence: Evidence,
    fuzzy_threshold: float = 90.0  # Require 90%+ similarity
) -> tuple[bool, str]:
    """Validate evidence quote with optional fuzzy fallback."""

    # Extract actual text from source
    start_idx = evidence.line_start - 1
    end_idx = evidence.line_end
    actual_text = '\n'.join(parsed.lines[start_idx:end_idx])

    # Normalize both sides
    normalized_actual = normalize(actual_text)
    normalized_quote = normalize(evidence.quote)

    # Try exact match first
    if normalized_actual == normalized_quote:
        return True, ""

    # Fall back to fuzzy matching
    similarity = fuzz.ratio(normalized_actual, normalized_quote)

    if similarity >= fuzzy_threshold:
        return True, f"Fuzzy match ({similarity:.1f}% similarity)"

    # Both failed
    return False, (
        f"Quote mismatch at lines {evidence.line_start}-{evidence.line_end}:\n"
        f"Similarity: {similarity:.1f}%\n"
        f"Expected: {normalized_actual[:100]!r}...\n"
        f"Got:      {normalized_quote[:100]!r}..."
    )
```

**Source:** [RapidFuzz 3.14.3 documentation](https://rapidfuzz.github.io/RapidFuzz/) and [Fuzzy String Matching in Python](https://www.datacamp.com/tutorial/fuzzy-string-python)

**Note on RapidFuzz 3.0+:** Strings are NOT preprocessed by default (no automatic lowercasing/whitespace trimming). Use explicit normalization before comparison or pass `processor` parameter.

### Pattern 3: Policy Type Classification with Structured Examples
**What:** Few-shot prompting with explicit type definitions and decision tree
**When to use:** Policy extraction where type must be classified reliably
**Example:**
```python
system_prompt = """Extract policies with CORRECT type classification.

POLICY TYPE DECISION TREE:
1. Does it describe something the system MUST do?
   → type: "must"
   Example: "Система должна проверять корректность промокода"

2. Does it describe something the system MUST NOT do?
   → type: "must_not"
   Example: "Бот не должен придумывать данные из личного кабинета"

3. Does it describe when to escalate to human?
   → type: "escalate"
   Example: "При медицинских вопросах — передать на врача"

4. Does it describe tone, language, communication style?
   → type: "style"
   Example: "Сообщение должно быть вежливым, без грубости"

5. Does it describe output format, structure, templates?
   → type: "format"
   Example: "Нужно исправлять явные опечатки и пунктуацию"

TYPE CLASSIFICATION EXAMPLES:
Policy: "Если пользователь матерится — оператор сохраняет нейтральный тон"
Analysis: Describes communication style rules
Type: "style"

Policy: "Оператор не должен давать личный номер врача"
Analysis: Describes prohibition (must not)
Type: "must_not"

Policy: "При сильном недовольстве — эскалация на старшего"
Analysis: Describes escalation trigger
Type: "escalate"

Now classify policies in the following document.
"""
```

**Source:** [LLMs for Classification | Prompt Engineering Guide](https://www.promptingguide.ai/prompts/classification) and [Prompt Optimization with Two Gradients for Classification](https://www.mdpi.com/2673-2688/6/8/182)

### Pattern 4: Multi-Pass Extraction (Optional Fallback)
**What:** Two-phase approach: (1) extract concepts without evidence, (2) find evidence for each concept
**When to use:** Only if single-pass evidence accuracy remains <80% after prompt improvements
**Example:**
```python
def extract_use_cases_multipass(parsed: ParsedMarkdown, model: str, seed: int) -> UseCaseList:
    """Two-pass extraction: concepts first, then evidence."""

    # Pass 1: Extract use case concepts (no evidence required)
    concepts_prompt = "Extract use case names and descriptions. Do NOT extract evidence."
    concepts_response = call_openai_structured(
        messages=[{"role": "system", "content": concepts_prompt}, ...],
        response_format=UseCaseConceptList,  # No evidence field
        model=model,
        seed=seed
    )

    # Pass 2: Find evidence for each concept
    numbered_text = get_numbered_text(parsed)
    use_cases = []

    for concept in concepts_response.concepts:
        evidence_prompt = f"""Find EXACT quotes from the source that support this use case:
Name: {concept.name}
Description: {concept.description}

Source with line numbers:
{numbered_text}

Return evidence with exact quote and line numbers."""

        evidence_response = call_openai_structured(
            messages=[{"role": "system", "content": evidence_prompt}],
            response_format=EvidenceList,
            model=model,
            seed=seed
        )

        use_cases.append(UseCase(
            id=concept.id,
            name=concept.name,
            description=concept.description,
            evidence=evidence_response.evidence
        ))

    return UseCaseList(use_cases=use_cases)
```

**Source:** [Multi-Step LLM Chains: Best Practices](https://www.deepchecks.com/orchestrating-multi-step-llm-chains-best-practices/) and [LLMs for Structured Data Extraction from PDFs in 2026](https://unstract.com/blog/comparing-approaches-for-using-llms-for-structured-data-extraction-from-pdfs/)

**Trade-offs:**
- **Pros:** Higher evidence recall (catches missing facts), can revisit document
- **Cons:** 2x LLM calls = 2x cost/latency, increased confabulation risk, lower precision

### Pattern 5: Chunking Strategy for Long Documents (Future-Proofing)
**What:** Document structure-based chunking that respects semantic boundaries
**When to use:** Only if document exceeds practical context limits (>50KB or >10,000 lines)
**Current status:** NOT NEEDED — example documents are 31-81 lines, well within context limits

**For reference (if needed in future phases):**
```python
def chunk_by_structure(parsed: ParsedMarkdown, max_lines: int = 500) -> list[ParsedMarkdown]:
    """Chunk document by headers/sections, not arbitrary line counts."""
    chunks = []
    current_chunk = []

    for i, line in enumerate(parsed.lines):
        # Detect section headers (markdown # headers)
        if line.startswith('#') and len(current_chunk) > max_lines:
            # Save current chunk
            chunks.append(ParsedMarkdown(
                full_text='\n'.join(current_chunk),
                lines=current_chunk,
                file_path=parsed.file_path
            ))
            current_chunk = [line]
        else:
            current_chunk.append(line)

    # Save final chunk
    if current_chunk:
        chunks.append(ParsedMarkdown(...))

    return chunks
```

**Source:** [Chunking Strategies for LLM Applications | Pinecone](https://www.pinecone.io/learn/chunking-strategies/) and [Context Window Overflow in 2026: Fix LLM Errors Fast](https://redis.io/blog/context-window-overflow/)

### Anti-Patterns to Avoid

- **Over-aggressive fuzzy matching:** Using fuzzy matching as primary strategy masks prompt engineering issues; always try exact match first
- **Lowercasing before comparison:** Destroys case information needed for accurate matching (e.g., names, acronyms); preserve case, normalize whitespace only
- **Document-specific prompts:** Hardcoding "look for FAQ section" or "find table with ticket_id column" violates anti-hardcoding requirement; use generic patterns
- **Multi-pass by default:** Doubles cost and latency; only use if evidence accuracy is unacceptable with single-pass
- **Ignoring LLM formatting instructions:** Phase 1 found LLMs drop markdown trailing pipes ~20% of the time; explicit "preserve ALL formatting" instructions reduce this

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Fuzzy string matching | Custom Levenshtein distance, manual similarity scoring | RapidFuzz library | Handles 10+ algorithms (Levenshtein, Jaro-Winkler, token-based), C++ performance (100x faster than Python), battle-tested edge cases |
| Whitespace normalization | Manual regex, string.strip() chains | RapidFuzz processor parameter or explicit normalize function | Handles cross-platform line endings, Unicode whitespace, consistent behavior |
| Prompt templates | String concatenation, f-strings scattered across code | Centralized prompt builder or template system | Maintainability, A/B testing, version control of prompts |
| Document chunking | Arbitrary line-count splits | Document structure-based chunking (headers, sections) | Preserves semantic coherence, avoids mid-sentence cuts |

**Key insight:** Phase 2 is about prompt engineering and validation refinement, not novel algorithm development. Use proven libraries (RapidFuzz) for fuzzy matching, focus effort on crafting better prompts and testing generalization.

## Common Pitfalls

### Pitfall 1: Fuzzy Matching Hides Prompt Problems
**What goes wrong:** Developer adds fuzzy matching to "fix" low evidence accuracy, but real issue is LLM prompt doesn't emphasize character-exact quotes
**Why it happens:** Fuzzy matching is easier to implement than prompt iteration; masks symptom instead of fixing root cause
**How to avoid:**
1. Start with exact matching only
2. Log all evidence validation failures with actual vs expected text
3. If failures show consistent patterns (e.g., missing trailing whitespace), fix prompt first
4. Only add fuzzy matching after prompt is optimized and failures are random
**Warning signs:** Fuzzy matching threshold keeps dropping (started at 95%, now at 80%), lots of "fuzzy match" messages in logs, evidence quotes have obvious differences from source

### Pitfall 2: Policy Type Misclassification
**What goes wrong:** LLM classifies escalation policies as "must" or style policies as "must_not" because type definitions are ambiguous
**Why it happens:** Natural language policy statements can fit multiple types; without explicit decision tree, LLM guesses
**How to avoid:**
1. Provide decision tree with exclusive criteria in prompt
2. Include 2-3 few-shot examples per type
3. Ask LLM to explain its reasoning before choosing type (chain-of-thought)
4. Validate against known examples from Phase 1 verification
**Warning signs:** Same policy classified differently across runs, unexpected type distributions (e.g., zero "escalate" policies when document clearly has escalation rules)

### Pitfall 3: Extraction Doesn't Generalize to Unseen Inputs
**What goes wrong:** System works on support FAQ example but fails on operator quality example because prompts reference "FAQ section" or "ticket table"
**Why it happens:** Developer optimizes prompts for single example document, introduces document-specific assumptions
**How to avoid:**
1. Test extraction on ALL THREE example documents during development
2. Use generic terms in prompts: "text", "document", "requirements" (not "FAQ", "tickets", "table")
3. Identify use cases by semantic patterns (actions, scenarios) not structural markers (headers, lists)
4. Review prompts for hardcoded assumptions before finalizing
**Warning signs:** Extraction works perfectly on one document but produces empty/minimal results on others, error messages reference missing sections

### Pitfall 4: Evidence Quote Truncation
**What goes wrong:** LLM extracts correct line range but truncates quote at 100-200 characters, validation fails
**Why it happens:** LLM models have implicit output length biases; without explicit "extract FULL quote" instruction, they summarize
**How to avoid:**
1. Add explicit instruction: "Extract the COMPLETE quote — do not truncate, do not summarize"
2. Specify expected quote length range: "Quotes should be 1-10 lines, approximately 50-500 characters"
3. If document has very long lines (>1000 chars), consider splitting at sentence boundaries
4. Log quote lengths in validation to detect systematic truncation
**Warning signs:** Validation failures show quotes ending mid-sentence, all failed quotes are approximately same length (e.g., ~150 chars), success rate inversely correlates with source text line length

### Pitfall 5: Temperature=0 Doesn't Guarantee Consistency
**What goes wrong:** Developer expects identical outputs with same seed, but extractions vary slightly across runs
**Why it happens:** OpenAI's temperature=0 + seed provides "mostly deterministic" results, not perfect determinism; infrastructure changes affect outputs
**How to avoid:**
1. Document that seed provides structural consistency, not byte-identical outputs
2. Use structural validation: same counts, same ID patterns, same types
3. Check system_fingerprint in API response; outputs should match if fingerprint matches
4. Don't fail tests on minor wording variations in descriptions
**Warning signs:** CI tests fail intermittently with same inputs/seed, manual comparison shows ~90% similarity but not exact match

### Pitfall 6: RapidFuzz Default Behavior Change (3.0+)
**What goes wrong:** Fuzzy matching fails because developer expects automatic lowercasing/whitespace-stripping (old fuzzywuzzy behavior)
**Why it happens:** RapidFuzz 3.0+ removed automatic preprocessing for performance; requires explicit normalization
**How to avoid:**
1. Normalize text explicitly before passing to RapidFuzz functions
2. OR use processor parameter: `fuzz.ratio(a, b, processor=default_process)` from rapidfuzz.utils
3. Document normalization strategy in code comments
4. Test with varied whitespace/case in unit tests
**Warning signs:** Identical text with different case/whitespace shows low similarity scores, fuzzy matching worked in development but fails in production with RapidFuzz 3.x

## Code Examples

Verified patterns from research and Phase 1 implementation:

### Enhanced Use Case Extractor with Improved Prompt
```python
# In use_case_extractor.py (enhance existing)
def extract_use_cases(
    parsed: ParsedMarkdown,
    model: str = "gpt-4o-mini",
    seed: int | None = None,
    min_use_cases: int = 5,
) -> UseCaseList:
    """Extract use cases with enhanced prompt for unstructured text."""

    system_prompt = f"""You are an expert requirements analyst. Extract use cases from Russian-language requirements.

TASK (structured for clarity):
{{
  "objective": "Extract {min_use_cases}+ use_cases from prose, FAQs, tables, or examples",
  "id_format": "uc_NNN (e.g., uc_001, uc_002)",
  "content_language": "Russian",
  "evidence_accuracy": "CHARACTER-EXACT quotes required"
}}

USE CASE IDENTIFICATION:
- Look for actions, scenarios, user goals, system behaviors
- Patterns: "может...", "должен...", "если...то...", question-answer pairs
- Use cases can be IMPLICIT in prose — extract intent from context
- Each distinct goal/behavior is ONE use case

EVIDENCE RULES (CRITICAL FOR VALIDATION):
1. Quote must be CHARACTER-FOR-CHARACTER EXACT from source
2. Include ALL markdown: *, **, bullets, table pipes |, etc.
3. Preserve ALL whitespace at line starts/ends
4. Do NOT clean, normalize, or reformat the quote
5. Line numbers shown as "N: " — use these for line_start/line_end
6. Do NOT include "N: " prefix in quote — only text after it
7. Multi-line quotes: use \\n between lines, preserve each line exactly

EXAMPLES:
[Table row use case]
Source:
32: | 1001 | «Где мой заказ???» | «Понимаю. Уточните номер заказа...» |
Quote: "| 1001 | «Где мой заказ???» | «Понимаю. Уточните номер заказа...» |"

[Prose use case]
Source:
14: * У бота **нет доступа** к личному кабинету.
15: * Если требуется ЛК — **передать на оператора**.
Quote: "* У бота **нет доступа** к личному кабинету.\\n* Если требуется ЛК — **передать на оператора**."

Now extract use cases from this document (all content must be in Russian):
"""

    # Build numbered text
    numbered_text = get_numbered_text(parsed)
    user_message = f"File: {parsed.file_path.name}\\n\\n{numbered_text}"

    # Call LLM (existing code)
    result = call_openai_structured(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        response_format=UseCaseList,
        model=model,
        seed=seed,
        temperature=0,
    )

    # Validate evidence (existing code)
    valid_count, invalid_count, errors = validate_all_evidence(parsed, result.use_cases)

    if invalid_count > 0:
        logger.warning(f"Evidence validation: {valid_count} valid, {invalid_count} invalid")
        for error in errors:
            logger.warning(f"  {error}")

    return result
```

### Evidence Validator with Fuzzy Fallback
```python
# In evidence_validator.py (enhance existing validate_evidence_quote)
from rapidfuzz import fuzz

def validate_evidence_quote(
    parsed: ParsedMarkdown,
    evidence: Evidence,
    enable_fuzzy: bool = True,
    fuzzy_threshold: float = 90.0
) -> tuple[bool, str]:
    """Validate evidence quote with optional fuzzy matching fallback.

    Args:
        parsed: ParsedMarkdown with source lines
        evidence: Evidence to validate
        enable_fuzzy: Enable fuzzy matching fallback (default: True)
        fuzzy_threshold: Minimum similarity % for fuzzy match (default: 90.0)

    Returns:
        (is_valid, message)
        - (True, "") for exact match
        - (True, "Fuzzy match (92.3%)") for fuzzy match
        - (False, "error details") for failure
    """
    # Convert 1-based to 0-based indices
    start_idx = evidence.line_start - 1
    end_idx = evidence.line_end

    # Check bounds
    if start_idx < 0:
        return False, f"line_start={evidence.line_start} is invalid (must be >= 1)"

    if end_idx > len(parsed.lines):
        return False, (
            f"line_end={evidence.line_end} exceeds file length "
            f"({len(parsed.lines)} lines)"
        )

    # Extract actual text from source
    actual_lines = parsed.lines[start_idx:end_idx]
    actual_text = '\\n'.join(actual_lines)

    # Normalize both sides (existing code)
    def normalize(text: str) -> str:
        lines = text.replace('\\r\\n', '\\n').replace('\\r', '\\n').split('\\n')
        return '\\n'.join(line.rstrip() for line in lines)

    normalized_actual = normalize(actual_text)
    normalized_quote = normalize(evidence.quote)

    # Try exact match first
    if normalized_actual == normalized_quote:
        return True, ""

    # Try fuzzy matching if enabled
    if enable_fuzzy:
        similarity = fuzz.ratio(normalized_actual, normalized_quote)

        if similarity >= fuzzy_threshold:
            return True, f"Fuzzy match ({similarity:.1f}% similarity)"

    # Both failed
    similarity = fuzz.ratio(normalized_actual, normalized_quote) if enable_fuzzy else 0
    return False, (
        f"Quote mismatch at lines {evidence.line_start}-{evidence.line_end}:\\n"
        f"Similarity: {similarity:.1f}%\\n"
        f"Expected: {normalized_actual[:100]!r}...\\n"
        f"Got:      {normalized_quote[:100]!r}..."
    )
```

### Policy Type Classification with Decision Tree
```python
# In policy_extractor.py (enhance existing prompt)
system_prompt = f"""You are an expert requirements analyst. Extract policies with CORRECT type classification.

POLICY TYPE DECISION TREE (choose ONE type per policy):

1. "must" — System MUST do something (requirements, obligations)
   Example: "Система должна проверять корректность промокода"

2. "must_not" — System MUST NOT do something (prohibitions, restrictions)
   Example: "Бот не должен придумывать данные из личного кабинета"

3. "escalate" — Situations requiring human escalation
   Example: "При медицинских вопросах — переключить на врача"

4. "style" — Tone, language, communication style rules
   Example: "Сообщение должно быть вежливым, без грубости"

5. "format" — Output format, structure, templates
   Example: "Нужно исправлять опечатки и пунктуацию"

CLASSIFICATION PROCESS:
1. Read the policy statement
2. Ask: Is this a prohibition? → must_not
3. Ask: Does this trigger escalation? → escalate
4. Ask: Is this about communication style? → style
5. Ask: Is this about output formatting? → format
6. Otherwise → must

FEW-SHOT EXAMPLES:
Policy: "Оператор не должен давать личный номер врача"
Reasoning: Prohibition (not allowed to give phone)
Type: "must_not"

Policy: "Если пользователь жалуется и сильно недоволен — эскалация"
Reasoning: Describes escalation trigger
Type: "escalate"

Policy: "Нельзя использовать капслок и много восклицательных знаков"
Reasoning: Communication style rule
Type: "style"

Now extract policies with types. Extract at least {min_policies} policies.
EVIDENCE RULES: (same as use case extractor...)
"""
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single composite prompt | Task-specific sub-prompts when needed | 2025-2026 research | Improves recall for complex data but increases confabulation risk |
| JSON mode without validation | Structured outputs with strict:true | OpenAI Aug 2024 | 93% → 100% schema compliance with constrained decoding |
| Temperature tuning | Always temperature=0 for extraction | Best practice 2025+ | Maximizes consistency, only use temperature>0 for creative generation |
| Generic prompts | JSON-formatted prompts with examples | 2026 prompt engineering trend | Adds clarity, makes expectations explicit |
| Exact matching only | Exact + fuzzy fallback | Common pattern 2025+ | Handles edge cases without masking prompt issues |
| Manual prompt iteration | LLM-based prompt optimization | Emerging 2026 | Meta-prompting where LLM refines its own prompts |

**Deprecated/outdated:**
- Using temperature>0 for factual extraction — reduces consistency
- Ignoring whitespace in evidence validation — leads to false negatives
- Document-specific prompts — violates generalization requirement
- thefuzz (fuzzywuzzy) library — community moved to RapidFuzz for performance and licensing

## Open Questions

1. **Optimal Evidence Accuracy Target**
   - What we know: Phase 1 achieves 80-100% evidence validation accuracy; research shows multi-pass can improve recall but increases confabulation
   - What's unclear: Whether 80% is acceptable or if >95% is required for downstream use
   - Recommendation: Target 90%+ with enhanced prompts + fuzzy fallback; only use multi-pass if single-pass fails to reach 90% after prompt optimization

2. **Fuzzy Matching Threshold**
   - What we know: RapidFuzz fuzz.ratio() returns 0-100 similarity score; 90%+ is generally considered high similarity
   - What's unclear: Optimal threshold for this use case (too high = false negatives, too low = masks real issues)
   - Recommendation: Start at 92% threshold, adjust based on validation logs; track false positive/negative rates

3. **Multi-Pass Necessity**
   - What we know: Multi-pass improves recall but doubles cost/latency and increases confabulation; single-pass is simpler
   - What's unclear: Whether enhanced prompts alone can achieve target accuracy or if multi-pass is required
   - Recommendation: Implement enhanced prompts + fuzzy fallback first; defer multi-pass to optional fallback if accuracy remains <80%

4. **Document Chunking Trigger**
   - What we know: Example documents are 31-81 lines (well within context limits); gpt-4o-mini supports 128K tokens
   - What's unclear: At what document size chunking becomes necessary (lost-in-the-middle problem)
   - Recommendation: No chunking needed for Phase 2; revisit if Phase 4 Doctor Booking example is significantly larger (>10,000 lines or >50KB)

5. **Generalization Testing Coverage**
   - What we know: Three example documents exist (support FAQ, operator quality, doctor booking); PIPE-06 requires anti-hardcoding
   - What's unclear: Whether testing on all three is sufficient to prove generalization
   - Recommendation: Test extraction on all three documents; if accuracy varies by >20% across documents, prompts likely have hardcoded assumptions

## Sources

### Primary (HIGH confidence)
- [OpenAI Structured Outputs Documentation](https://platform.openai.com/docs/guides/structured-outputs) - 93% benchmark accuracy, 100% with constrained decoding
- [RapidFuzz 3.14.3 Documentation](https://rapidfuzz.github.io/RapidFuzz/) - Official API and usage patterns
- [Best practices for prompt engineering with the OpenAI API](https://help.openai.com/en/articles/6654000-best-practices-for-prompt-engineering-with-the-openai-api) - Official OpenAI guidance

### Secondary (MEDIUM confidence)
- [Prompt Patterns for Structured Data Extraction from Unstructured Text (Vanderbilt)](https://www.dre.vanderbilt.edu/~schmidt/PDF/Prompt_Patterns_for_Structured_Data_Extraction_from_Unstructured_Text.pdf) - Academic catalog of extraction patterns
- [Multi-Step LLM Chains: Best Practices](https://www.deepchecks.com/orchestrating-multi-step-llm-chains-best-practices/) - Multi-pass trade-offs
- [LLMs for Structured Data Extraction from PDFs in 2026](https://unstract.com/blog/comparing-approaches-for-using-llms-for-structured-data-extraction-from-pdfs/) - Recent comparative analysis
- [The guide to structured outputs and function calling with LLMs](https://agenta.ai/blog/the-guide-to-structured-outputs-and-function-calling-with-llms) - Hallucination pitfalls
- [LLMs for Classification | Prompt Engineering Guide](https://www.promptingguide.ai/prompts/classification) - Classification techniques
- [Fuzzy String Matching in Python Tutorial | DataCamp](https://www.datacamp.com/tutorial/fuzzy-string-python) - RapidFuzz vs thefuzz comparison
- [Chunking Strategies for LLM Applications | Pinecone](https://www.pinecone.io/learn/chunking-strategies/) - Document chunking best practices
- [Hallucination Detection and Mitigation in Large Language Models (arXiv 2026)](https://arxiv.org/pdf/2601.09929) - Detection methods and mitigation

### Tertiary (LOW confidence - for reference)
- [Better Generalizing to Unseen Concepts (arXiv Jan 2026)](https://arxiv.org/html/2601.16711) - LLM-based auto-labeled data for generalization
- [Using LLMs for Automated Privacy Policy Analysis (arXiv Mar 2026)](https://arxiv.org/html/2503.16516v1) - Policy classification with fine-tuning
- [Evaluating Chunking Strategies for Retrieval | Chroma Research](https://research.trychroma.com/evaluating-chunking) - Chunking evaluation study

## Metadata

**Confidence breakdown:**
- Enhanced prompt engineering: HIGH - Well-documented patterns from academic and industry sources, verified with Phase 1 implementation
- Fuzzy matching integration: HIGH - RapidFuzz is mature library with clear API, straightforward integration
- Policy type classification: MEDIUM - Few-shot prompting is proven technique but Russian language policy nuances may require iteration
- Multi-pass extraction: MEDIUM - Research shows mixed results (better recall, worse precision); defer until needed
- Anti-hardcoding testing: MEDIUM - Generalization is testable with three examples, but "unseen inputs" definition is subjective

**Research date:** 2026-02-16
**Valid until:** ~2026-03-16 (30 days) for stable components; ~2026-02-23 (7 days) for LLM prompt engineering claims (fast-moving field)

**Key risk areas requiring validation:**
1. Evidence accuracy improvement from enhanced prompts (needs empirical testing)
2. Policy type classification accuracy on Russian text (language-specific nuances)
3. Generalization across all three example documents (anti-hardcoding verification)
4. Fuzzy matching threshold tuning (requires validation log analysis)
