---
phase: 03-test-dataset-generation
plan: 03
subsystem: generation
tags: [openai-function-calling, orchestrator, coverage-enforcement, deepeval, ragas, giskard, run-manifest]

# Dependency graph
requires:
  - phase: 03-02
    provides: Framework generators and adapters for DeepEval, Ragas, Giskard
provides:
  - OpenAI function-calling orchestrator routing between frameworks
  - Coverage enforcement ensuring minimum thresholds
  - Full pipeline producing 5 output files (use_cases, policies, test_cases, dataset, manifest)
  - run_manifest.json tracking per DATA-08 specification
affects: [03-04, validation, integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "OpenAI function calling for dynamic framework selection"
    - "Fallback pattern for framework failures"
    - "Coverage enforcement with Pydantic validation"
    - "Referential integrity checks across artifact chain"

key-files:
  created:
    - src/dataset_generator/generation/orchestrator.py
    - src/dataset_generator/generation/coverage.py
  modified:
    - src/dataset_generator/pipeline.py
    - src/dataset_generator/cli.py

key-decisions:
  - "OpenAI function calling selects framework based on task context (not fixed pipeline)"
  - "Fallback to direct OpenAI generation if all frameworks fail or insufficient results"
  - "Coverage enforcement validates minimums: 3 test cases per UC, 3+ criteria per example"
  - "run_manifest.json includes frameworks_used tracking for audit trail"

patterns-established:
  - "Pattern 1: Orchestrator routes via OpenAI function calling with tool definitions"
  - "Pattern 2: Coverage enforcer validates after generation, raises on critical failures"
  - "Pattern 3: Referential integrity checked across use_case_id → test_case_id → example chains"

# Metrics
duration: 6min
completed: 2026-02-16
---

# Phase 03 Plan 03: Orchestration and Pipeline Integration Summary

**OpenAI function-calling orchestrator routes between DeepEval, Ragas, Giskard with fallback, integrated into full pipeline producing 5 output files including run_manifest.json**

## Performance

- **Duration:** 6 minutes
- **Started:** 2026-02-16T16:39:28Z
- **Completed:** 2026-02-16T16:46:02Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- OpenAI function calling orchestrator with 3 tool definitions routes to appropriate framework based on task context
- Coverage enforcement validates minimum 3 test cases per use case, 3+ evaluation criteria, 1+ policy_ids
- Pipeline extended to generate test cases and dataset examples, producing test_cases.json and dataset.json
- run_manifest.json captures complete generation metadata per DATA-08 (input_path, out_path, seed, timestamp, generator_version, llm config, frameworks_used, counts)
- Fallback to direct OpenAI generation ensures pipeline always completes even on framework failures

## Task Commits

Each task was committed atomically:

1. **Task 1: Create OpenAI function-calling orchestrator and coverage enforcer** - `f5d2760` (feat)
   - orchestrator.py: OpenAI function calling routing, tool definitions, framework invocation
   - coverage.py: enforce_coverage, check_referential_integrity functions

2. **Task 2: Wire orchestrator into pipeline and update CLI** - `82453fd` (feat)
   - pipeline.py: Extended with generation steps, run_manifest output
   - cli.py: Updated to display new output paths and frameworks used

## Files Created/Modified

**Created:**
- `src/dataset_generator/generation/orchestrator.py` - OpenAI function calling router with tool definitions for DeepEval, Ragas, Giskard; orchestrate_generation function; fallback logic; temporary policy document preparation
- `src/dataset_generator/generation/coverage.py` - enforce_coverage validates minimum test cases, criteria, policy_ids; check_referential_integrity validates ID chains

**Modified:**
- `src/dataset_generator/pipeline.py` - Extended PipelineResult with test_cases_path, dataset_path, manifest_path, counts, frameworks_used; added Steps 5-6 (generation, integrity checks); added Steps 9-11 (write test_cases, dataset, manifest); updated summary output
- `src/dataset_generator/cli.py` - Updated result display to show test case count, dataset example count, frameworks used, and all 5 output file paths

## Decisions Made

1. **OpenAI function calling for framework selection** - Uses tool_choice="auto" to let LLM decide which framework(s) to invoke based on use case and policy context (per user locked decision)

2. **Fallback on framework failure** - If all framework calls fail OR result count < min_test_cases, calls generate_with_openai_fallback to ensure pipeline always completes

3. **Coverage enforcement per use case** - enforce_coverage called after each use case generation to validate minimums before aggregating results

4. **Temporary policy document creation** - prepare_policy_documents writes policies to temp markdown file since DeepEval/Ragas expect file paths, cleaned up after generation

5. **Frameworks_used tracking in metadata** - Extracts "generator" field from test case metadata to populate run_manifest.json frameworks_used list for audit trail

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. All imports resolved correctly, function names matched between orchestrator and adapters, nested Pydantic models serialized correctly via model_dump().

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Full generation pipeline operational: markdown → use_cases → policies → test_cases → dataset → manifest
- OpenAI function calling orchestrator routes between frameworks dynamically
- Coverage enforcement ensures minimum quality thresholds
- Referential integrity validated across artifact chain
- Ready for Phase 03-04 (CLI enhancements) or validation/integration phases

**Blockers:** None

## Self-Check: PASSED

All created files verified:
- FOUND: orchestrator.py
- FOUND: coverage.py

All commits verified:
- FOUND: f5d2760 (Task 1)
- FOUND: 82453fd (Task 2)

---
*Phase: 03-test-dataset-generation*
*Completed: 2026-02-16*
