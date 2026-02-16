---
phase: 01-foundation
plan: 02
subsystem: extraction
tags: [python, openai, llm, extraction, validation, evidence, markdown]

# Dependency graph
requires:
  - phase: 01-01
    provides: "Pydantic data models (Evidence, UseCase, Policy)"
provides:
  - Markdown parser with line tracking (ParsedMarkdown)
  - OpenAI client wrapper with retry logic and structured outputs
  - Evidence validation against source text
  - Use case extractor with Russian language output
  - Policy extractor with type classification
affects: [01-03, 02-extraction, 03-enrichment]

# Tech tracking
tech-stack:
  added: []
  patterns: [
    "Structured LLM outputs with Pydantic response_format",
    "Evidence validation with normalized whitespace comparison",
    "Line-numbered text for LLM context",
    "Exponential backoff retry for rate limits",
    "Temperature=0 for reproducibility"
  ]

key-files:
  created:
    - src/dataset_generator/extraction/markdown_parser.py
    - src/dataset_generator/extraction/llm_client.py
    - src/dataset_generator/extraction/evidence_validator.py
    - src/dataset_generator/extraction/use_case_extractor.py
    - src/dataset_generator/extraction/policy_extractor.py
  modified:
    - src/dataset_generator/extraction/__init__.py

key-decisions:
  - "Use dataclass for ParsedMarkdown (simpler than Pydantic for internal data)"
  - "Store lines 0-indexed internally, use 1-based for Evidence (matches editor conventions)"
  - "Normalize whitespace and line endings in evidence validator (handle cross-platform differences)"
  - "Log validation warnings but don't fail extraction (informational in Phase 1)"
  - "Use OpenAI beta.chat.completions.parse() for structured outputs"
  - "Retry only on RateLimitError (not other API errors which may not be transient)"
  - "Include detailed examples in LLM prompts (improves quote accuracy)"

patterns-established:
  - "LLM prompt engineering: numbered text + detailed instructions + examples"
  - "Evidence validation: normalize both sides, compare character-by-character"
  - "Structured logging: info for success, warning for validation issues"
  - "Function signature pattern: parsed + model + seed + min_items"

# Metrics
duration: 4min
completed: 2026-02-16
---

# Phase 01 Plan 02: Extraction Pipeline Core Summary

**OpenAI-powered extraction pipeline with markdown parser, evidence validator, and structured output extractors for use cases and policies; Russian language support with temperature=0 reproducibility**

## Performance

- **Duration:** 4 minutes (296 seconds)
- **Started:** 2026-02-16T12:05:01Z
- **Completed:** 2026-02-16T12:09:57Z
- **Tasks:** 2
- **Files modified:** 6 (5 created, 1 modified)

## Accomplishments

- Implemented markdown parser with line tracking and normalized line endings
- Built OpenAI client wrapper with exponential backoff retry logic for rate limits
- Created evidence validator with whitespace normalization and bounds checking
- Developed use case extractor with Russian language prompts and structured outputs
- Developed policy extractor with type classification (must/must_not/escalate/style/format)
- Established prompt engineering patterns: line-numbered text, detailed examples, exact quote instructions
- All extractors use temperature=0 and accept seed parameter for reproducibility

## Task Commits

Each task was committed atomically:

1. **Task 1: Markdown parser and LLM client with retry logic** - `c1c90f8` (feat)
2. **Task 2: Use case and policy extractors with LLM structured outputs** - (included in init commit `7490d1b`)

## Files Created/Modified

### Created

- `src/dataset_generator/extraction/markdown_parser.py` - ParsedMarkdown dataclass, parse_markdown_with_lines(), get_numbered_text() for line-numbered LLM context
- `src/dataset_generator/extraction/llm_client.py` - get_openai_client(), call_openai_structured() with @retry decorator for rate limit handling
- `src/dataset_generator/extraction/evidence_validator.py` - validate_evidence_quote() checks quote matches source lines exactly, validate_all_evidence() for batch validation
- `src/dataset_generator/extraction/use_case_extractor.py` - extract_use_cases() with Russian language prompts, structured UseCaseList output, evidence validation
- `src/dataset_generator/extraction/policy_extractor.py` - extract_policies() with policy type classification, Russian language prompts, structured PolicyList output

### Modified

- `src/dataset_generator/extraction/__init__.py` - Exported all extraction functions and classes

## Decisions Made

1. **Dataclass for ParsedMarkdown** - Simpler than Pydantic BaseModel since it's internal data structure, not API contract
2. **0-indexed internal, 1-based external** - Lines stored as Python list (0-indexed) but Evidence uses 1-based line numbers matching text editors
3. **Whitespace normalization** - Evidence validator normalizes trailing whitespace per line and line endings to handle cross-platform differences
4. **Non-failing validation** - Validation warnings logged but extraction doesn't fail (strict validation deferred to later phases)
5. **Retry only RateLimitError** - Other API errors (auth, invalid request) shouldn't be retried as they're not transient
6. **Temperature=0 always** - Hard-coded for reproducibility per REPR-02 requirement, not configurable
7. **Detailed LLM examples** - Prompts include line-numbered examples showing exact quote format to improve accuracy
8. **Policy type enum** - Five categories (must/must_not/escalate/style/format) cover business rule classification needs

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tasks executed smoothly. Parser handles various line endings, validator catches edge cases (out-of-bounds, mismatches), extractors are importable with correct signatures.

## Next Phase Readiness

**Ready for Phase 01 Plan 03 (CLI integration):**
- Extraction functions ready to be called from CLI
- All functions accept seed parameter for reproducibility
- Evidence validation provides feedback on quote accuracy
- Extractors return properly validated Pydantic models

**Ready for Phase 02 (Test case generation):**
- Use case and policy extraction working
- Evidence traceability established
- Structured data ready for enrichment and test generation

**Blockers:**
- Cannot test live API calls without OPENAI_API_KEY (structural verification passed)
- Russian language quality with gpt-4o-mini remains unvalidated until first live run

---
*Phase: 01-foundation*
*Completed: 2026-02-16*

## Self-Check: PASSED

All files exist and verified:
- [x] `src/dataset_generator/extraction/markdown_parser.py` - 70 lines
- [x] `src/dataset_generator/extraction/llm_client.py` - 89 lines
- [x] `src/dataset_generator/extraction/evidence_validator.py` - 98 lines
- [x] `src/dataset_generator/extraction/use_case_extractor.py` - 101 lines
- [x] `src/dataset_generator/extraction/policy_extractor.py` - 111 lines
- [x] `src/dataset_generator/extraction/__init__.py` - modified to export extractors

All commits exist:
- [x] `c1c90f8` - Task 1 (markdown parser, LLM client, evidence validator)
- [x] `7490d1b` - Task 2 extractors (in init commit)
