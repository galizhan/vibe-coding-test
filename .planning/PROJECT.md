# Synthetic Dataset Generator for LLM Agent Testing

## What This Is

A Python CLI tool that reads raw business requirement documents (markdown) and automatically extracts use cases and policies, then generates test cases and synthetic datasets for evaluating LLM agents. Designed for teams building LLM agents who lack real-world test data due to NDAs, data sensitivity, or manual effort constraints.

## Core Value

From a single raw markdown document, produce a complete, validated chain of artifacts (use_cases → policies → test_cases → dataset) with full traceability back to source text — ready for eval pipelines.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Read raw markdown documents and extract structured use cases with evidence traceability
- [ ] Extract policies/rules/constraints from unstructured text with evidence traceability
- [ ] Generate test cases with parameter variation axes per use case
- [ ] Generate dataset examples with input messages, expected output, and evaluation criteria
- [ ] Support Case A: support bot (FAQ + tickets) — single_turn_qa format
- [ ] Support Case B: operator quality checker — single_utterance_correction and dialog_last_turn_correction formats
- [ ] Support Case C: doctor booking (optional/bonus case for algorithm validation)
- [ ] Strict data contract compliance (ID conventions, evidence format, required fields)
- [ ] CLI interface with configurable parameters (--input, --out, --seed, --n-use-cases, etc.)
- [ ] Built-in validate command (exit code 0 on success)
- [ ] run_manifest.json generation per run (seed, model, timestamp, paths)
- [ ] OpenAI API integration (default gpt-4o-mini, configurable to gpt-4o)
- [ ] Langfuse integration for dataset upload and experiment tracking
- [ ] DeepEval Synthesizer integration for golden generation from FAQ docs
- [ ] Evidently integration for data quality reports (duplicates, distributions)
- [ ] Giskard Hub integration for document-based business test generation
- [ ] Pre-generated output artifacts in out/support/ and out/operator_quality/
- [ ] README with setup, dependencies, env configuration

### Out of Scope

- Building the actual LLM agents (support bot, operator quality checker) — only the test data pipeline
- Official validator (official_validator.py) — provided separately later
- Surge/Scale human review integration — manual process, not automated
- Patronus guardrails integration — can add later if needed
- Mobile/web UI — CLI only

## Context

- The project addresses a common pain point: teams building LLM agents can't use real conversations (NDA/privacy) and manually creating test data is slow and misses edge cases
- The hypothesis: business requirements contain enough signal to auto-generate meaningful test datasets
- Two mandatory example inputs already exist as markdown files in the repo
- An official validator (official_validator.py) and JSON schemas will be provided later for acceptance testing
- Anti-hardcoding requirement: the system must work on unseen inputs, not just the provided examples
- All output must be in Russian (matching the input documents)

## Constraints

- **Language**: Python 3.10+ — specified in the tech spec
- **LLM Provider**: OpenAI API (gpt-4o-mini default, gpt-4o configurable) — user choice
- **Data Contract**: Strict JSON schema compliance — IDs with prefixes (uc_, pol_, tc_, ex_), evidence with exact quote matching, mandatory fields
- **Minimum Coverage**: Per case: 5+ use cases, 5+ policies (2+ types), 3+ test cases per UC, 1+ example per TC
- **Reproducibility**: Same input + seed should produce structurally consistent output
- **No Secrets**: API keys via environment variables, never committed

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| OpenAI as LLM provider | User preference | — Pending |
| gpt-4o-mini as default model | Balance cost/quality, with gpt-4o override | — Pending |
| All 4 optional integrations (Langfuse, DeepEval, Evidently, Giskard) | Maximize "productness" and tooling coverage | — Pending |
| Support all 3 input cases including doctor booking | Extra validation of algorithm generalizability | — Pending |
| Core only first, then integrations | Ship working pipeline before adding external services | — Pending |

---
*Last updated: 2026-02-16 after initialization*
