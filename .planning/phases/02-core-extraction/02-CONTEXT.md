# Phase 2: Core Extraction - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Extract structured use cases and policies from unstructured markdown text with complete evidence traceability. System must work on unseen inputs (anti-hardcoding). This phase improves/refines the extraction pipeline built in Phase 1.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
- Extraction strategy (single-pass vs multi-pass LLM, chunking approach)
- Evidence matching implementation (exact vs fuzzy, fallback strategies)
- Policy type classification approach (LLM-driven vs hybrid)
- Prompt design for generalization to unseen documents
- Error handling for edge cases in extraction

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

- Use DeepEval Synthesizer, Ragas, Giskard Hub for test/dataset generation — Phase 3
- OpenAI as orchestrator redirecting to external frameworks — Phase 3

</deferred>

---

*Phase: 02-core-extraction*
*Context gathered: 2026-02-16*
