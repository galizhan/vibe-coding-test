---
phase: 04-all-use-cases
plan: 01
subsystem: models-and-detection
tags:
  - data-models
  - tz-contract
  - case-detection
  - llm-integration
dependency_graph:
  requires:
    - Phase 01 models (UseCase, Policy, TestCase, InputData)
    - Phase 02 extractors (use_case_extractor, policy_extractor)
    - extraction.llm_client (get_openai_client)
  provides:
    - target_message_index field on InputData
    - case field on UseCase, Policy, TestCase
    - statement field on Policy
    - parameters dict on TestCase
    - policy_ids list on TestCase
    - case_detector.detect_case_and_formats function
    - CaseFormatDetection Pydantic model
    - allpairspy dependency for pairwise testing
  affects:
    - Future pipeline integration (Phase 04-02)
    - Dataset generation (Phase 04-03)
tech_stack:
  added:
    - allpairspy: pairwise testing library
  patterns:
    - OpenAI structured outputs for case/format detection
    - Pydantic v2 model_validator for cross-field validation
    - Content-only classification (no filename dependencies)
key_files:
  created:
    - src/dataset_generator/generation/case_detector.py
  modified:
    - src/dataset_generator/models/dataset_example.py
    - src/dataset_generator/models/use_case.py
    - src/dataset_generator/models/policy.py
    - src/dataset_generator/models/test_case.py
    - pyproject.toml
decisions:
  - title: "Use model_validator(mode='after') for cross-field validation"
    rationale: "InputData.target_message_index validation requires access to messages list; field_validator can't reliably access other fields in Pydantic v2"
    alternatives: "Custom __init__ or root_validator (deprecated)"
    impact: "Cleaner validation code, follows Pydantic v2 best practices"
  - title: "Auto-populate Policy.statement from description"
    rationale: "tz.md uses 'statement' but existing code uses 'description'; keeping both ensures backward compatibility and tz.md compliance"
    alternatives: "Rename description to statement (breaking change)"
    impact: "Zero breaking changes to existing Phase 1-3 code"
  - title: "All new fields have default values"
    rationale: "Phase 2-3 extractors don't populate case/parameters/policy_ids yet; defaults prevent breaking changes"
    alternatives: "Make fields required and update all existing code (high risk)"
    impact: "Gradual migration path - Phase 4 pipeline will populate these fields"
  - title: "Content-only classification in case detector"
    rationale: "User locked decision (per 04-CONTEXT.md): ensures universality - same document renamed produces same classification"
    alternatives: "Use filename patterns (rejected - not universal)"
    impact: "Detector works on any document structure; requires LLM but provides true generalization"
metrics:
  duration: 3
  completed_at: "2026-02-16T17:50:54Z"
  tasks_completed: 2
  files_modified: 5
  files_created: 1
  commits: 2
---

# Phase 04 Plan 01: Data Models and Case Detection Summary

**One-liner:** Updated Pydantic models to match tz.md data contract (case, target_message_index, statement, parameters, policy_ids) and built LLM-based case/format auto-detection using OpenAI structured outputs.

## Context

Phase 04 focuses on enabling the pipeline to handle all 3 use cases (support_bot, operator_quality, doctor_booking) with multiple dataset formats. Plan 01 lays the foundation by:

1. Updating data models to include ALL fields required by tz.md data contract
2. Building universal case/format detection that works on any document without filename dependencies

This enables Phase 04-02 (pipeline integration) to auto-detect case/format and Phase 04-03 (multi-format generation) to produce examples in the correct format.

## Tasks Completed

### Task 1: Update data models to match tz.md data contract
**Status:** ✅ Complete
**Commit:** 4725a71

**Changes:**
- **InputData (dataset_example.py):**
  - Added `target_message_index: Optional[int]` for dialog_last_turn_correction format
  - Added `model_validator(mode='after')` to validate:
    - Index is within range of messages list
    - Messages[target_message_index].role == "operator"

- **UseCase (use_case.py):**
  - Added `case: str` field with default="" for case identifier

- **Policy (policy.py):**
  - Added `case: str` field with default=""
  - Added `statement: str` field with default="" (tz.md contract field)
  - Added `model_validator(mode='after')` to auto-populate statement from description

- **TestCase (test_case.py):**
  - Added `case: str` field with default=""
  - Added `parameters: dict` with default_factory=dict for test parameters
  - Added `policy_ids: list[str]` with default_factory=list for policy references
  - Added `field_validator` to ensure all policy_ids start with "pol_"

**Backward Compatibility:**
All new fields have defaults, so existing Phase 1-3 code that constructs these models without the new fields continues to work. This provides a gradual migration path - Phase 4 pipeline will populate these fields after extraction.

**Verification:**
```python
# New fields work
uc = UseCase(id='uc_test', name='Test', description='Test', evidence=[ev], case='support_bot')
assert uc.case == 'support_bot'

# Backward compatibility maintained
uc_old = UseCase(id='uc_old', name='Old', description='Old', evidence=[ev])
assert uc_old.case == ''  # Default value
```

### Task 2: Build case/format auto-detection module and add allpairspy dependency
**Status:** ✅ Complete
**Commit:** b7adcd2

**Created:**
- **case_detector.py** - New module with:
  - `CaseFormatDetection` Pydantic model:
    - `case: Literal["support_bot", "operator_quality", "doctor_booking"]`
    - `formats: list[Literal["single_turn_qa", "single_utterance_correction", "dialog_last_turn_correction"]]`
    - `reasoning: str` for explainability

  - `detect_case_and_formats(use_cases, policies, model)` function:
    - Takes extracted use cases and policies (NOT filename)
    - Builds content summary from use case names/descriptions and policy types/descriptions
    - Calls OpenAI `client.beta.chat.completions.parse()` with structured outputs
    - System prompt instructs LLM on classification rules:
      - support_bot → ["single_turn_qa"]
      - operator_quality → ["single_utterance_correction", "dialog_last_turn_correction"]
      - doctor_booking → ["single_turn_qa"]
    - Temperature=0 for reproducibility
    - Returns CaseFormatDetection with case + formats + reasoning
    - Error handling: defaults to case="support_bot", formats=["single_turn_qa"] if LLM fails
    - Edge case: defaults to ["single_turn_qa"] if LLM returns empty formats

**Added Dependency:**
- **allpairspy** - Pairwise testing library for efficient parameter combination generation (needed for Plan 02)

**Key Design Decision:**
The detection function receives ONLY content (use case descriptions, policy descriptions). It must NOT receive or use the input filename. This ensures universality - same document renamed produces same classification. This is a locked user decision per 04-CONTEXT.md.

**Verification:**
```python
from dataset_generator.generation.case_detector import detect_case_and_formats, CaseFormatDetection

# Model works
det = CaseFormatDetection(
    case='operator_quality',
    formats=['single_utterance_correction', 'dialog_last_turn_correction'],
    reasoning='test'
)
assert det.case == 'operator_quality'
assert len(det.formats) == 2

# allpairspy available
from allpairspy import AllPairs
```

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

All verification criteria passed:

1. ✅ All 4 model files have new fields matching tz.md data contract
2. ✅ InputData.target_message_index validates role=operator and index range
3. ✅ Policy.statement auto-populated from description
4. ✅ TestCase has case, parameters, policy_ids fields with proper validation
5. ✅ case_detector.py importable with CaseFormatDetection model
6. ✅ allpairspy importable
7. ✅ Backward compatibility maintained - existing model construction without new fields works

## Integration Points

**Upstream dependencies:**
- Phase 01 models (Evidence, UseCase, Policy, TestCase, InputData, Message)
- Phase 02 extractors (use_case_extractor, policy_extractor)
- extraction.llm_client.get_openai_client

**Downstream impacts:**
- Phase 04-02 (pipeline integration) will use `detect_case_and_formats` after Phase 2 extraction
- Phase 04-03 (multi-format generation) will use `case` and `format` fields to produce correct output
- All future generators will populate `parameters` and `policy_ids` on TestCase per tz.md contract

**Breaking changes:** None - all changes are additive with defaults

## Technical Notes

**Pydantic v2 Patterns:**
- Used `model_validator(mode='after')` instead of deprecated `root_validator`
- Cross-field validation (target_message_index checking messages list) requires model_validator
- field_validator used for single-field checks (policy_ids prefix validation)

**OpenAI Structured Outputs:**
- `client.beta.chat.completions.parse()` with Pydantic models ensures type-safe responses
- Temperature=0 for reproducibility per project convention (REPR-02)
- Response parsing handled automatically by OpenAI SDK

**Error Handling:**
- Case detection has safe defaults if LLM fails
- All validators provide clear error messages with actual vs expected values
- Logging added to track detection results and failures

## Success Criteria Met

- ✅ All Pydantic models pass validation with new fields
- ✅ Existing code (pipeline.py, orchestrator.py, fallback.py) still works without changes
- ✅ case_detector.py provides detect_case_and_formats that returns case + list of formats
- ✅ allpairspy available for Plan 02

## Next Steps

**Phase 04-02 (Pipeline Integration):**
- Integrate `detect_case_and_formats` into orchestrator after Phase 2 extraction
- Populate `case` field on extracted UseCase/Policy/TestCase models
- Store detected formats in run context for Plan 03 to use

**Phase 04-03 (Multi-Format Generation):**
- Use detected formats to generate dataset examples in correct format(s)
- Populate `parameters` and `policy_ids` on TestCase during generation
- Set `target_message_index` on InputData for dialog_last_turn_correction format

## Self-Check: PASSED

**Created files exist:**
```
FOUND: src/dataset_generator/generation/case_detector.py
```

**Modified files exist:**
```
FOUND: src/dataset_generator/models/dataset_example.py
FOUND: src/dataset_generator/models/use_case.py
FOUND: src/dataset_generator/models/policy.py
FOUND: src/dataset_generator/models/test_case.py
FOUND: pyproject.toml
```

**Commits exist:**
```
FOUND: 4725a71 (Task 1: Update data models)
FOUND: b7adcd2 (Task 2: Add case detector)
```

All artifacts verified and present.
