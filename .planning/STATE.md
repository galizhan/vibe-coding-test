# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-16)

**Core value:** From a single raw markdown document, produce a complete, validated chain of artifacts (use_cases → policies → test_cases → dataset) with full traceability back to source text
**Current focus:** Phase 2: Core Extraction Enhancement

## Current Position

Phase: 3 of 8 (Test Dataset Generation)
Plan: 1 of 4 in current phase (completed)
Status: Phase 3 in progress
Last activity: 2026-02-16 — Completed 03-01-PLAN.md

Progress: [█████░░░░░] 46%

## Performance Metrics

**Velocity:**
- Total plans completed: 6
- Average duration: 4 min
- Total execution time: 0.40 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation | 3 | 9 min | 3 min |
| 02-core-extraction | 2 | 8 min | 4 min |
| 03-test-dataset-generation | 1 | 7 min | 7 min |

**Recent Trend:**
- Last 5 plans: 01-03 (3min), 02-01 (3min), 02-02 (5min), 03-01 (7min)
- Trend: Slightly increasing (framework installation overhead)

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- OpenAI as LLM provider (user preference) — affects Phase 1 integration setup
- gpt-4o-mini as default model with gpt-4o override — affects CLI parameter design
- All 4 integrations (Langfuse, DeepEval, Evidently, Giskard Hub) — deferred to Phase 8
- Support all 3 input cases including doctor booking — validates algorithm generalization
- Core only first, then integrations — influences phase ordering (1-6 core, 7-8 validation+integrations)
- Use Pydantic v2 syntax throughout (01-01) — ensures future compatibility
- Enforce uc_ and pol_ ID prefixes (01-01) — provides traceability
- 1-based line numbering for Evidence (01-01) — matches text editor conventions
- Policy type as Literal enum (01-01) — provides compile-time type safety
- Dataclass for ParsedMarkdown (01-02) — simpler than Pydantic for internal data
- Whitespace normalization in evidence validation (01-02) — handles cross-platform differences
- Temperature=0 always for LLM calls (01-02) — ensures reproducibility per REPR-02
- Retry only RateLimitError (01-02) — other errors not transient
- Use json.dumps with ensure_ascii=False for Russian text (01-03) — Pydantic v2 model_dump_json lacks this parameter
- Check OPENAI_API_KEY before pipeline execution (01-03) — early failure with clear error message
- Enhanced LLM prompts to preserve markdown formatting (01-03) — improves evidence validation accuracy
- Use structured JSON task definition in prompts (02-01) — improves clarity and reduces ambiguity
- Include 3 few-shot examples for use cases (02-01) — covers bullet, prose, and table patterns
- Include 5 few-shot examples for policies (02-01) — one per type for clear classification
- Prioritize must_not and escalate before generic must in decision tree (02-01) — reduces type classification ambiguity
- Preserve ALL markdown formatting in evidence quotes (02-01) — CHARACTER-EXACT matching for validation
- Use generic terms not document-specific references in prompts (02-01) — ensures generalization
- Exact match is ALWAYS tried first, fuzzy matching is fallback only at 90%+ similarity (02-02) — prevents masking prompt problems
- Shared normalize_for_comparison function eliminates code duplication (02-02) — used by both exact and fuzzy matching
- Evidence validator accepts enable_fuzzy and fuzzy_threshold parameters for flexibility (02-02) — allows control over matching behavior
- TestCase must have 2-3 parameter_variation_axes per PIPE-04 (03-01) — balances coverage with focus
- DatasetExample must have 3+ evaluation_criteria per DATA-07 (03-01) — ensures comprehensive evaluation
- Message role validated as Literal['user', 'operator', 'assistant', 'system'] (03-01) — provides type safety for conversation structure
- Framework dependencies use minimum version constraints (>=) (03-01) — allows patch updates while ensuring features

### Pending Todos

None yet.

### Blockers/Concerns

- ✓ RESOLVED: Russian language generation quality validated with gpt-4o-mini in 01-03 (working correctly)
- ✓ RESOLVED: OPENAI_API_KEY setup completed by user in 01-03
- Evidence quoting implementation complete — validation warns but doesn't fail (strict mode deferred)
- Known limitation: Markdown table trailing pipes sometimes truncated by LLM (affects ~20% of table-based evidence)
- Official validator (official_validator.py) schema not yet available (may require Phase 7 adjustments)

## Session Continuity

Last session: 2026-02-16 (plan execution)
Stopped at: Completed 03-01-PLAN.md — Phase 3 in progress (test dataset generation models and framework dependencies)
Resume file: None
