---
phase: 05-validation-delivery
plan: 01
subsystem: validation
tags: [validation, cli, referential-integrity, pydantic]
dependency_graph:
  requires: [04-03]
  provides: [validate-command]
  affects: [cli]
tech_stack:
  added: []
  patterns: [pydantic-validation, typer-exit-codes, structured-reporting]
key_files:
  created:
    - src/dataset_generator/validation/__init__.py
    - src/dataset_generator/validation/validator.py
    - src/dataset_generator/validation/integrity_checker.py
    - src/dataset_generator/validation/report.py
  modified:
    - src/dataset_generator/cli.py
decisions:
  - Validator stores loaded models as instance attributes for potential reuse by Langfuse upload
  - Evidence validation not implemented (would require input source file)
  - Referential integrity now validates policy_ids against ACTUAL loaded policies, not just prefix format
  - Exit code 0 on success, 1 on errors (Typer convention)
metrics:
  duration: 327
  completed: 2026-02-16T19:56:26Z
---

# Phase 05 Plan 01: Validation Command Summary

**One-liner:** Standalone `validate` command that loads JSON artifacts, validates schema and referential integrity (including policy_ids against actual policies), and prints structured reports with proper exit codes.

## What Was Built

Implemented the `validate` CLI command that provides post-generation verification of dataset artifacts without requiring re-execution of the pipeline.

### Task 1: Validation Module (commit e453f83)

Created `src/dataset_generator/validation/` package with three modules:

**report.py:**
- `ValidationResult` class with errors, warnings, counts, and formats lists
- `is_valid` property returns True only if no errors exist
- `print_report()` method outputs structured summary to stdout, errors to stderr
- Separates errors (structural/integrity issues causing exit 1) from warnings (informational)

**integrity_checker.py:**
- `check_referential_integrity()` function that validates ALL cross-model ID references
- Builds lookup sets from loaded UseCaseList, PolicyList, TestCaseList, DatasetExampleList
- Checks forward references:
  - test_case.use_case_id → use_case.id
  - example.use_case_id → use_case.id
  - example.test_case_id → test_case.id
  - example.policy_ids items → policy.id (validates against ACTUAL loaded policies)
- Key improvement over `coverage.py:check_referential_integrity()`: validates policy_ids against the actual set of policy IDs loaded from policies.json, not just pol_ prefix format

**validator.py:**
- `DatasetValidator` orchestrator class
- Loads all 4 JSON files via Pydantic's `model_validate_json()` for efficiency
- Catches `ValidationError` per-file and reports field-level errors with file path context
- Runs referential integrity checks if all models loaded successfully
- Records artifact counts and detected formats
- Stores loaded models as instance attributes for potential reuse (e.g., Langfuse upload in Phase 7)

### Task 2: CLI Integration (commit 03cffa0)

Replaced validate command stub with full implementation:

- Added `--out` parameter with `exists=True` validation (Typer checks directory exists before code runs)
- Imports `DatasetValidator` from validation module
- Creates validator instance, runs validation, prints report
- Exits with code 0 on success, code 1 on validation errors using `typer.Exit()`
- No `--input` parameter required (validation only needs output directory)
- Comprehensive docstring documenting checks and exit codes

## Verification Results

All verification criteria passed:

1. `python -m dataset_generator validate --out out/support` — prints summary with 60 examples, 5 policies, 60 test cases, 5 use cases, exits 0
2. `python -m dataset_generator validate --help` — shows --out parameter documentation
3. Missing file test: Created temp directory with partial files, confirmed exit code 1 with clear error messages
4. Referential integrity: check_referential_integrity validates policy_ids against actual loaded policies (tested via code inspection and successful validation of real data)

## Deviations from Plan

None - plan executed exactly as written.

## Technical Notes

**Pydantic ValidationError handling:**
- `_add_validation_errors()` helper extracts field-level errors from Pydantic's error dict
- Error location (loc) joined into readable path (e.g., "dataset.json: examples -> 0 -> policy_ids: field required")

**Exit code strategy:**
- Using `typer.Exit(code=N)` instead of `sys.exit(N)` for better Typer integration and testability
- Typer's `exists=True` validation provides exit code 2 for non-existent directories (before our code runs)
- Our validation returns exit code 1 for schema/integrity errors

**Evidence validation deferred:**
- Plan mentioned evidence validation as "optional, only if input source available"
- Not implemented in this plan because validate command doesn't receive --input parameter
- Evidence validation during generation already happens in pipeline (Task 01-02)
- Could be added later if needed for re-validation scenarios

**Integration with existing coverage checks:**
- `coverage.py:check_referential_integrity()` runs during generation (warns but doesn't fail)
- `validation/integrity_checker.py:check_referential_integrity()` runs post-generation (fails validation on errors)
- Policy ID validation enhanced: coverage.py only checks prefix format, validation checks actual existence

## Files Changed

**Created:**
- `src/dataset_generator/validation/__init__.py` (11 lines)
- `src/dataset_generator/validation/report.py` (66 lines)
- `src/dataset_generator/validation/integrity_checker.py` (87 lines)
- `src/dataset_generator/validation/validator.py` (161 lines)

**Modified:**
- `src/dataset_generator/cli.py` (+37 lines, -3 lines)

Total: 362 lines added, 3 lines removed

## Success Criteria Status

- ✓ validate command is a working Typer command with --out parameter
- ✓ Validation loads all 4 JSON files via Pydantic model_validate_json
- ✓ Referential integrity checks policy_ids against actual loaded policies (not just prefix format)
- ✓ Evidence validation deferred (no input source in validate command)
- ✓ Exit code 0 on success, 1 on validation errors
- ✓ Summary report shows counts, errors, and warnings

## Self-Check: PASSED

**Created files verified:**
```
FOUND: src/dataset_generator/validation/__init__.py
FOUND: src/dataset_generator/validation/validator.py
FOUND: src/dataset_generator/validation/integrity_checker.py
FOUND: src/dataset_generator/validation/report.py
```

**Modified files verified:**
```
FOUND: src/dataset_generator/cli.py (modified)
```

**Commits verified:**
```
FOUND: e453f83 (Task 1: Create validation module)
FOUND: 03cffa0 (Task 2: Wire validate command into CLI)
```

**Functional verification:**
```
✓ python3 -m dataset_generator validate --out out/support exits with code 0
✓ Validation report shows: 60 examples, 5 policies, 60 test cases, 5 use cases
✓ Missing file scenario exits with code 1
✓ Help text displays --out parameter documentation
```
