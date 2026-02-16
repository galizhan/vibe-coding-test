# Phase 4: All Use Cases - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Generate complete datasets for all three use cases (support bot, operator quality checker, doctor booking) using the framework-powered pipeline from Phase 3. The pipeline must be universal — not hardcoded to specific cases or formats.

**Primary reference:** `tz.md` — the technical specification is the source of truth for all data contracts, formats, acceptance criteria, and case-specific requirements.

</domain>

<decisions>
## Implementation Decisions

### Pipeline universality
- Generic pipeline only — no case-specific few-shot examples in generation prompts
- The extracted use cases and policies from Phase 2 guide generation, not hardcoded templates
- Pipeline should work on any document, not just the 3 known examples
- `case` field auto-detected from document content by LLM (not from filename or CLI flag)
- `format` field auto-detected from document content (not CLI flag)
- One document can produce examples in MULTIPLE formats (e.g. operator doc → both single_utterance_correction AND dialog_last_turn_correction)

### Source type classification
- `metadata.source` (tickets, faq_paraphrase, corner) classified automatically by LLM based on use case context
- No explicit config or mapping needed

### Operator corrections
- Follow tz.md examples exactly for correction formats
- Errors in generated operator messages are driven by test case parameter combinations (mixed errors, not one-at-a-time)
- Dialog length follows tz.md minimum (2+ messages for dialog_last_turn_correction)
- Escalation responses include full text as shown in tz.md canonical examples
- Variation axes from tz.md: длина фразы, пунктуация/опечатки, сленг/мат/эмодзи, медицинские термины, агрессия пользователя, необходимость эскалации

### Output structure
- Follow tz.md strictly: pre-generated artifacts in out/support/ and out/operator_quality/ only
- Doctor booking is optional усложнённый пример — no committed output required
- Artifacts NOT committed to repo — generate on demand only
- Each output directory contains: run_manifest.json, use_cases.json, policies.json, test_cases.json, dataset.json

### Validation rules
- Follow tz.md data contract exactly — all mandatory fields, ID conventions, evidence format
- All 3 cases share the same validation rules (same data contract)
- tz.md acceptance criteria are the minimum thresholds: 5+ use cases, 5+ policies, 3+ test cases per use case, 1+ example per test case
- evidence[] must pass exact quote matching (with fuzzy fallback from Phase 2)

### Claude's Discretion
- Implementation of auto-detection logic for case and format
- How to route test case generation across variation axes
- Internal structure of generation prompts (as long as pipeline stays generic)
- Doctor booking case handling (case value, format choice)

</decisions>

<specifics>
## Specific Ideas

- tz.md appendix contains canonical examples for all 3 dataset formats — use these as ground truth for format compliance
- The official_validator.py will be used for final verification — ensure output matches its expectations
- Anti-hardcoding: evaluators may run with different filenames and hidden inputs of the same type
- Support bot requires all 3 metadata.source types: tickets, faq_paraphrase, corner
- Operator quality requires both formats: single_utterance_correction AND dialog_last_turn_correction
- For dialog_last_turn_correction: target_message_index must point to last message with role=operator

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-all-use-cases*
*Context gathered: 2026-02-16*
