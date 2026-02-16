# Phase 3: Test & Dataset Generation - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Generate test cases with parameter variation axes and dataset examples (input messages, expected_output, evaluation_criteria) from extracted use cases and policies. Use external frameworks instead of custom generation logic.

</domain>

<decisions>
## Implementation Decisions

### Framework selection
- DeepEval Synthesizer is the primary generation engine for both test cases and dataset examples
- All three frameworks (DeepEval, Ragas, Giskard Hub) are used in this phase, not deferred to Phase 8
- DeepEval handles generation; Claude decides the specific roles for Ragas and Giskard based on research into their capabilities

### Orchestration pattern
- OpenAI function calling routes between frameworks (not a fixed pipeline)
- OpenAI acts as orchestrator deciding which framework to call based on the task
- Hardcoded Python adapters convert between framework output formats and Pydantic data contracts (not LLM-driven conversion)
- If a framework call fails or returns low-quality output, fall back to direct OpenAI generation to ensure pipeline always completes
- Each generated item records which framework produced it in metadata (e.g., `generator: deepeval`) for traceability/debugging

### Claude's Discretion
- Specific roles for Ragas and Giskard Hub (evaluate, test, generate — research and assign)
- Output format mapping details (adapter implementation)
- Coverage enforcement strategy (ensuring minimums: 3 test cases/UC, 3+ eval criteria)
- OpenAI function definitions and routing logic

</decisions>

<specifics>
## Specific Ideas

- "Don't write custom solutions for these tasks" — leverage existing frameworks
- "OpenAI should act as an orchestrator that redirects" — function calling pattern, not hardcoded pipeline
- Framework source tracking in metadata for debugging

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-test-dataset-generation*
*Context gathered: 2026-02-16*
