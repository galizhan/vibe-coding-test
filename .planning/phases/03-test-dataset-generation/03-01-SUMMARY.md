---
phase: 03-test-dataset-generation
plan: 01
subsystem: dataset-generation
tags:
  - data-models
  - pydantic-v2
  - framework-dependencies
  - test-cases
  - dataset-examples
dependency_graph:
  requires:
    - 02-01 (Use case and policy Pydantic models)
    - 02-02 (Evidence validation patterns)
  provides:
    - TestCase and DatasetExample Pydantic v2 models
    - RunManifest tracking model
    - Framework dependencies (deepeval, ragas, giskard, evidently)
  affects:
    - 03-02 (Test case generation will use TestCase model)
    - 03-03 (Dataset generation will use DatasetExample model)
    - 03-04 (Framework exports will use RunManifest model)
tech_stack:
  added:
    - deepeval>=3.0 (DeepEval Synthesizer - primary generation engine)
    - ragas>=0.4 (RAG evaluation and test generation)
    - giskard[llm]>=2.0 (Knowledge base testing, RAGET)
    - evidently>=0.4 (Data quality reports)
    - langchain>=0.2 (Document loading for framework integration)
    - pandas>=2.0 (DataFrame operations for framework exports)
  patterns:
    - Pydantic v2 field validators for ID prefix enforcement (tc_, ex_, uc_, pol_)
    - Nested models (Message, InputData, LLMConfig, GenerationCounts)
    - Field-level constraints (min_length, default_factory)
    - Literal types for role validation
key_files:
  created:
    - src/dataset_generator/models/test_case.py
    - src/dataset_generator/models/dataset_example.py
    - src/dataset_generator/models/run_manifest.py
  modified:
    - src/dataset_generator/models/__init__.py
    - pyproject.toml
decisions:
  - key: "Parameter variation axes constraint"
    choice: "2-3 axes per TestCase (PIPE-04)"
    rationale: "Balances coverage (not too narrow) with focus (not too broad)"
  - key: "Evaluation criteria constraint"
    choice: "Minimum 3 criteria per DatasetExample (DATA-07)"
    rationale: "Ensures comprehensive evaluation coverage"
  - key: "Message role validation"
    choice: "Literal['user', 'operator', 'assistant', 'system']"
    rationale: "Provides type safety for conversation structure"
  - key: "Framework version constraints"
    choice: "Minimum versions specified (>=) for all frameworks"
    rationale: "Allows patch updates while ensuring core features available"
metrics:
  duration: 7
  tasks_completed: 2
  files_created: 3
  files_modified: 2
  commits: 2
  lines_added: 237
  completion_date: "2026-02-16"
---

# Phase 03 Plan 01: Test Dataset Generation Models Summary

**One-liner:** Pydantic v2 models for test cases (tc_ prefix, 2-3 axes), dataset examples (ex_ prefix, 3+ criteria, role-validated messages), and run manifests, with deepeval/ragas/giskard/evidently frameworks installed

## What Was Built

Created the complete data model foundation for test dataset generation with three new Pydantic v2 models and six framework dependencies.

### New Models

1. **TestCase** (`test_case.py`)
   - Validates `tc_` prefix for test case IDs
   - References use case with `uc_` prefix validation
   - Enforces 2-3 parameter variation axes per PIPE-04
   - Metadata dict for framework tracking

2. **DatasetExample** (`dataset_example.py`)
   - Validates `ex_` prefix for example IDs
   - Nested Message and InputData models with role validation (user/operator/assistant/system)
   - Enforces minimum 3 evaluation criteria (DATA-07)
   - Enforces minimum 1 policy ID with `pol_` prefix validation
   - References both use_case_id and test_case_id with prefix validation

3. **RunManifest** (`run_manifest.py`)
   - Captures complete generation run metadata per DATA-08
   - Nested LLMConfig (provider, model, temperature)
   - Nested GenerationCounts (use_cases, policies, test_cases, dataset_examples)
   - Tracks input_path, out_path, seed, timestamp, generator_version, frameworks_used

### Framework Dependencies

Added to `pyproject.toml`:
- **deepeval>=3.0** - Primary generation engine (DeepEval Synthesizer)
- **ragas>=0.4** - RAG evaluation and test generation
- **giskard[llm]>=2.0** - Knowledge base testing (RAGET)
- **evidently>=0.4** - Data quality reports (INTG-03)
- **langchain>=0.2** - Document loading for Ragas/Giskard integration
- **pandas>=2.0** - DataFrame operations for framework exports

All frameworks successfully installed and importable.

## Deviations from Plan

None - plan executed exactly as written. All validations passed on first attempt.

## Verification Results

All 7 verification checks passed:
- ✓ All 3 model files importable
- ✓ TestCase tc_ prefix enforced
- ✓ TestCase 2-3 axes constraint enforced
- ✓ DatasetExample ex_ prefix, 3+ criteria, 1+ policy_ids, role validation
- ✓ RunManifest captures all DATA-08 fields
- ✓ models/__init__.py exports all new types
- ✓ All framework dependencies installed and importable
- ✓ Existing models (Evidence, UseCase, Policy) still work unchanged

## Task Completion

| Task | Name | Status | Commit | Files |
|------|------|--------|--------|-------|
| 1 | Create TestCase and DatasetExample models | ✓ Complete | c3fb2e3 | test_case.py, dataset_example.py |
| 2 | Create RunManifest, update __init__, install frameworks | ✓ Complete | f294d8a | run_manifest.py, __init__.py, pyproject.toml |

## Technical Notes

### Pydantic v2 Patterns Followed

All models follow existing patterns from `evidence.py`, `use_case.py`, and `policy.py`:
- `field_validator` decorator (not v1 `validator`)
- `model_dump` method (not v1 `dict`)
- `Field(default_factory=dict)` for mutable defaults
- Consistent docstrings and field descriptions

### Framework Installation Notes

- All frameworks installed successfully via `pip3 install -e .`
- PyTorch warnings present but non-critical (optional dependency for some framework features)
- No version conflicts encountered
- Total install time: ~5 minutes

### Validation Coverage

Each model includes comprehensive field validation:
- **ID prefix validation** - tc_, ex_, uc_, pol_ prefixes enforced
- **Constraint validation** - min/max lengths, count requirements
- **Type validation** - Literal types for role field
- **Referential integrity** - cross-references validated at field level

## Impact on Downstream Work

This plan establishes the complete schema foundation for Phase 03:

- **Plan 03-02** (Test Case Generation) can now use TestCase model with validated structure
- **Plan 03-03** (Dataset Generation) can now use DatasetExample model with role-validated messages
- **Plan 03-04** (Framework Export) can now use RunManifest model to track generation metadata
- All three frameworks (deepeval, ragas, giskard) are available for generation engines

## Next Steps

Ready to proceed to **03-02-PLAN.md** (Test Case Generation via DeepEval Synthesizer):
- Will use TestCase model to generate parameterized test cases
- Will leverage deepeval framework for generation
- Depends on use case extraction from Phase 02

---

**Self-Check:** PASSED

Verification of created files:
```
✓ FOUND: src/dataset_generator/models/test_case.py
✓ FOUND: src/dataset_generator/models/dataset_example.py
✓ FOUND: src/dataset_generator/models/run_manifest.py
✓ FOUND: src/dataset_generator/models/__init__.py (modified)
✓ FOUND: pyproject.toml (modified)
```

Verification of commits:
```
✓ FOUND: c3fb2e3 (Task 1: TestCase and DatasetExample models)
✓ FOUND: f294d8a (Task 2: RunManifest and framework dependencies)
```

All claims in SUMMARY verified against actual artifacts.
