---
phase: 04-all-use-cases
plan: 02
subsystem: format-adapters-and-variation
tags:
  - format-adapters
  - pairwise-testing
  - source-classification
  - llm-generation
dependency_graph:
  requires:
    - Phase 04-01 (data models, case detection)
    - extraction.llm_client (get_openai_client)
    - models.dataset_example (DatasetExample, InputData, Message)
    - models.test_case (TestCase)
    - allpairspy (pairwise combinatorial testing)
  provides:
    - FormatAdapter base class
    - SingleTurnQAAdapter for support_bot
    - SingleUtteranceCorrectionAdapter for operator_quality
    - DialogLastTurnCorrectionAdapter for operator_quality
    - get_adapter_for_format factory function
    - generate_variations with pairwise parameter combinations
    - classify_source_type for metadata.source
    - Format-aware fallback generator
  affects:
    - Future pipeline integration (Phase 04-03)
    - Dataset generation with multiple formats
tech_stack:
  added:
    - allpairspy: Pairwise combinatorial testing library (already added in 04-01)
  patterns:
    - OpenAI structured outputs for format-specific generation
    - Pydantic models for LLM response schemas
    - Factory pattern for adapter selection
    - Heuristic + LLM fallback for classification
    - Mixed error generation driven by parameter combinations
key_files:
  created:
    - src/dataset_generator/generation/format_adapters/__init__.py
    - src/dataset_generator/generation/format_adapters/base.py
    - src/dataset_generator/generation/format_adapters/single_turn_qa.py
    - src/dataset_generator/generation/format_adapters/operator_corrections.py
    - src/dataset_generator/generation/variation_router.py
    - src/dataset_generator/generation/source_classifier.py
  modified:
    - src/dataset_generator/generation/fallback.py
decisions:
  - title: "Generic prompts with parameter-driven generation"
    rationale: "User locked decision: no case-specific few-shot examples. Use case description and policies guide generation, not hardcoded templates. This ensures generalization across different input documents."
    alternatives: "Hardcoded templates per case (rejected - not universal)"
    impact: "All adapters use generic prompts; LLM interprets use case context and parameters to generate appropriate examples"
  - title: "Mixed error generation for operator corrections"
    rationale: "User decision: operator messages must contain MULTIPLE error types simultaneously (not one at a time). Parameters drive which errors appear together."
    alternatives: "One error type per example (rejected - not realistic)"
    impact: "Error instructions explicitly state 'MIXED errors' and list ALL non-default parameters as simultaneous errors"
  - title: "Pairwise combinatorial testing with allpairspy"
    rationale: "Full combinatorial testing would produce exponential explosion (e.g., 3x2x2x2x5 = 120 combinations). Pairwise covers all 2-way interactions with far fewer test cases."
    alternatives: "Full combinatorial (too many), random sampling (no coverage guarantee)"
    impact: "Efficient test case generation covering edge cases without explosion; min_test_cases padding if pairwise produces too few"
  - title: "Heuristic + LLM fallback for source classification"
    rationale: "Obvious cases (adversarial=profanity -> corner, FAQ in description -> faq_paraphrase) can be classified instantly without LLM call. Only use LLM for ambiguous cases."
    alternatives: "Always use LLM (slower, more expensive)"
    impact: "Fast classification for common cases; LLM only for edge cases; fallback to 'tickets' if LLM fails"
  - title: "Format-aware fallback generator with backward compatibility"
    rationale: "Phase 3 code calls fallback without case/formats parameters. Need to add new parameters while maintaining backward compatibility (default to support_bot/single_turn_qa)."
    alternatives: "Breaking change requiring all callers to update (high risk)"
    impact: "Gradual migration path; existing Phase 3 code works unchanged; new Phase 4 code can use case/formats"
metrics:
  duration: 6
  completed_at: "2026-02-16T17:59:55Z"
  tasks_completed: 2
  files_modified: 1
  files_created: 6
  commits: 2
---

# Phase 04 Plan 02: Format Adapters and Variation Summary

**One-liner:** Built format-specific generation adapters with OpenAI structured outputs, pairwise parameter variation using allpairspy, and metadata.source classification for support bot examples.

## Context

Phase 04-02 builds the generation layer that produces dataset examples in 3 different formats:
1. `single_turn_qa` for support_bot (1 user message, expected response)
2. `single_utterance_correction` for operator_quality (1 operator message with errors)
3. `dialog_last_turn_correction` for operator_quality (multi-turn dialog ending with operator)

Each format has specific structural requirements (message counts, roles, target_message_index) that must be enforced during generation. Test case parameter variations use pairwise combinatorics to avoid exponential explosion while covering all 2-way interactions.

## Tasks Completed

### Task 1: Create format-specific generation adapters
**Status:** ✅ Complete
**Commit:** 3315a39

**Created Files:**
- **format_adapters/base.py** - Abstract FormatAdapter base class:
  - `generate_example()` - Generate format-specific DatasetExample
  - `validate_format()` - Validate example matches format requirements
  - `get_format_name()` - Return format identifier

- **format_adapters/single_turn_qa.py** - SingleTurnQAAdapter:
  - Generates single_turn_qa format (1 user message + expected response)
  - Uses OpenAI structured outputs with SingleTurnQAGenerationOutput schema
  - System prompt includes use case context, policies, and test parameters
  - Generates text in RUSSIAN per tz.md requirements
  - Sets metadata.source to empty string (classified later by source_classifier)
  - Validation: exactly 1 message with role="user", no target_message_index

- **format_adapters/operator_corrections.py** - Two adapter classes:

  **SingleUtteranceCorrectionAdapter:**
  - Generates single_utterance_correction format
  - Input: 1 operator message WITH MIXED ERRORS driven by parameters
  - Critical: errors are MIXED (multiple types simultaneously), not one at a time
  - Parameters drive which errors appear: punctuation_errors, slang_profanity_emoji, caps_exclamation, medical_terms
  - System prompt explicitly instructs: "generate MIXED errors - include ALL non-default values simultaneously"
  - target_message_index = 0
  - expected_output = corrected version
  - Validation: exactly 1 message with role="operator", target_message_index=0

  **DialogLastTurnCorrectionAdapter:**
  - Generates dialog_last_turn_correction format
  - Input: 2+ messages, last message is operator with errors
  - Dialog can be 2-5 messages for realism (per tz.md: minimum 2, typically 3-5)
  - Parameters drive dialog context (user_aggression, escalation_needed) AND errors
  - Escalation responses include full text per tz.md canonical example
  - target_message_index = len(messages) - 1
  - expected_output = corrected last operator message
  - Validation: 2+ messages, last role="operator", target_message_index=len-1

- **format_adapters/__init__.py** - Factory function:
  - `get_adapter_for_format(format_name, case)` returns appropriate adapter
  - Mapping: single_turn_qa -> SingleTurnQAAdapter, etc.
  - Exports all adapter classes and base class

**Key Design Decisions:**
- ALL generation prompts are GENERIC (per user locked decision): no case-specific few-shot examples
- Use case description and policies guide generation, not hardcoded templates
- ALL text generated in RUSSIAN (matching input documents)
- Mixed error generation for operator corrections (not one error at a time)
- Temperature=0 for all LLM calls (reproducibility)

**Verification:**
```python
from dataset_generator.generation.format_adapters import get_adapter_for_format
qa = get_adapter_for_format('single_turn_qa', 'support_bot')
assert isinstance(qa, SingleTurnQAAdapter)  # ✅ Passed
```

### Task 2: Build variation router, source classifier, and update fallback generator
**Status:** ✅ Complete
**Commit:** 206e59b

**Created Files:**

- **variation_router.py** - Pairwise parameter variation:
  - `generate_variations(case, use_case_description, policies, min_test_cases)` function
  - Defines variation axes per case:
    - support_bot: tone, has_order_id, requires_account_access, language, adversarial
    - operator_quality: phrase_length, punctuation_errors, slang_profanity_emoji, medical_terms, user_aggression, escalation_needed
    - doctor_booking: reuses support_bot axes (similar domain)
  - Uses `allpairspy.AllPairs` for pairwise combinatorial generation
  - If pairwise produces fewer than min_test_cases, pads with random combinations
  - For each parameter dict, selects 2-3 axes with non-default values for parameter_variation_axes
  - Returns list of dicts with `_variation_axes` field for TestCase construction

- **source_classifier.py** - Metadata source classification:
  - `classify_source_type(use_case_description, generated_input, parameters, model)` function
  - Quick heuristic checks (avoid LLM when obvious):
    - adversarial in (profanity, injection, garbage) -> "corner"
    - "FAQ" in use_case_description + no adversarial -> "faq_paraphrase"
  - For non-obvious cases: use OpenAI structured outputs with SourceClassification schema
  - System prompt: classify as tickets/faq_paraphrase/corner with confidence
  - Temperature=0 for reproducibility
  - Fallback to "tickets" if LLM fails
  - ONLY used for support_bot case (other cases don't need metadata.source)

**Modified Files:**

- **fallback.py** - Format-aware fallback generator:
  - Added `case` parameter (default="support_bot") for backward compatibility
  - Added `formats` parameter (default=None -> single_turn_qa for support_bot)
  - Default formats: operator_quality gets both correction formats
  - Updated `_build_system_prompt` to include case and formats
  - Added `_build_format_instructions()` helper for format-specific prompt sections
  - TestCase construction now populates case, parameters, policy_ids fields
  - DatasetExample construction:
    - Sets case from parameter (not hardcoded "support_bot")
    - Sets format from LLM response or formats list
    - Sets target_message_index for correction formats (0 for single_utterance, len-1 for dialog)
  - Format instructions include target_message_index examples for each format
  - Escalation response example text included in prompt per tz.md

**Key Design Decisions:**
- Pairwise combinatorics instead of full combinatorial (avoids exponential explosion)
- Heuristic + LLM fallback pattern (fast for obvious cases, accurate for edge cases)
- Backward compatibility for fallback.py (existing code works unchanged)
- Format-specific instructions in prompts (clear requirements for each format)

**Verification:**
```python
from dataset_generator.generation.variation_router import generate_variations
vars_support = generate_variations('support_bot', 'FAQ', [], min_test_cases=3)
assert len(vars_support) >= 3  # ✅ Passed

from dataset_generator.generation.source_classifier import classify_source_type
source = classify_source_type('FAQ', 'test', {'adversarial': 'profanity'})
assert source == 'corner'  # ✅ Passed

import inspect
from dataset_generator.generation.fallback import generate_with_openai_fallback
sig = inspect.signature(generate_with_openai_fallback)
assert 'case' in sig.parameters  # ✅ Passed
assert 'formats' in sig.parameters  # ✅ Passed
```

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

All verification criteria passed:

1. ✅ All 3 format adapters importable and produce structurally correct examples
2. ✅ SingleTurnQAAdapter: 1 user message, no target_message_index
3. ✅ SingleUtteranceCorrectionAdapter: 1 operator message, target_message_index=0
4. ✅ DialogLastTurnCorrectionAdapter: 2+ messages, last is operator, target_message_index=len-1
5. ✅ Factory function `get_adapter_for_format` works correctly
6. ✅ Variation router generates 3+ parameter combinations using allpairspy pairwise
7. ✅ Source classifier heuristics work for obvious cases (corner, faq_paraphrase)
8. ✅ Fallback generator accepts case/formats parameters
9. ✅ Format-specific validation methods implemented for all adapters

## Integration Points

**Upstream dependencies:**
- Phase 04-01 (DatasetExample, InputData, Message models with target_message_index)
- extraction.llm_client.get_openai_client for OpenAI API calls
- allpairspy library for pairwise combinations

**Downstream impacts:**
- Phase 04-03 (pipeline integration) will:
  - Call `generate_variations` to create test case parameter combinations
  - Use `get_adapter_for_format` to select adapter based on detected formats
  - Call adapter.generate_example() to produce dataset examples
  - Use `classify_source_type` to set metadata.source for support_bot examples
  - Validate examples with adapter.validate_format()

**Breaking changes:** None - all changes are additive with backward compatibility

## Technical Notes

**OpenAI Structured Outputs:**
- All adapters use `client.beta.chat.completions.parse()` with Pydantic models
- Schemas: SingleTurnQAGenerationOutput, SingleUtteranceCorrectionOutput, DialogLastTurnCorrectionOutput
- Response parsing handled automatically by OpenAI SDK
- Temperature=0 for reproducibility per project convention

**Pairwise Combinatorial Testing:**
- AllPairs generates minimal set covering all 2-way interactions
- Example: 6 axes with 2-5 values each -> ~20 combinations instead of 720 (full combinatorial)
- min_test_cases ensures minimum coverage even if pairwise produces fewer
- _select_variation_axes identifies 2-3 most significant axes per combination

**Error Handling:**
- Source classifier falls back to "tickets" if LLM fails
- Adapters log generation steps for debugging
- Factory function raises ValueError for unknown formats
- All LLM calls include try/except with logging

**Format-Specific Validation:**
- Each adapter implements validate_format() checking:
  - Correct format field value
  - Message count requirements
  - Message role requirements
  - target_message_index value (when applicable)
- Returns list of error messages (empty if valid)

## Success Criteria Met

- ✅ All format adapters generate examples in correct structure per tz.md canonical examples
- ✅ SingleUtteranceCorrectionAdapter: 1 operator message, target_message_index=0
- ✅ DialogLastTurnCorrectionAdapter: 2+ messages, last is operator, target_message_index=len-1
- ✅ SingleTurnQAAdapter: 1 user message, no target_message_index
- ✅ Variation router produces pairwise combinations, not full combinatorial
- ✅ Source classifier returns tickets/faq_paraphrase/corner for support_bot case
- ✅ Fallback generator accepts case/formats parameters with backward compatibility

## Next Steps

**Phase 04-03 (Pipeline Integration):**
- Integrate format adapters into orchestrator after case detection
- Use `generate_variations` to create test case parameter combinations
- For each detected format, use appropriate adapter to generate examples
- Classify metadata.source for support_bot examples
- Validate all generated examples with adapter.validate_format()
- Store generated dataset examples in dataset.json

**Expected Flow:**
1. Orchestrator calls `detect_case_and_formats` (from 04-01)
2. For each use case, call `generate_variations(case, ...)` to get parameter combinations
3. For each variation, create TestCase with parameters and _variation_axes
4. For each test case + format combo, call `get_adapter_for_format(format, case).generate_example(...)`
5. If case=support_bot, call `classify_source_type` and set metadata.source
6. Validate example with adapter.validate_format()
7. Write to dataset.json

## Self-Check: PASSED

**Created files exist:**
```
FOUND: src/dataset_generator/generation/format_adapters/__init__.py
FOUND: src/dataset_generator/generation/format_adapters/base.py
FOUND: src/dataset_generator/generation/format_adapters/single_turn_qa.py
FOUND: src/dataset_generator/generation/format_adapters/operator_corrections.py
FOUND: src/dataset_generator/generation/variation_router.py
FOUND: src/dataset_generator/generation/source_classifier.py
```

**Modified files exist:**
```
FOUND: src/dataset_generator/generation/fallback.py
```

**Commits exist:**
```
FOUND: 3315a39 (Task 1: Format-specific generation adapters)
FOUND: 206e59b (Task 2: Variation router, source classifier, format-aware fallback)
```

All artifacts verified and present.
