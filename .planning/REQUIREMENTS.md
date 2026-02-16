# Requirements: Synthetic Dataset Generator

**Defined:** 2026-02-16
**Core Value:** From a single raw markdown document, produce a complete, validated chain of artifacts (use_cases → policies → test_cases → dataset) with full traceability back to source text

## v1 Requirements

### Core Pipeline (PIPE)

- [ ] **PIPE-01**: System reads a raw markdown document and parses it with line number tracking
- [ ] **PIPE-02**: System extracts structured use cases from unstructured text (without explicit lists) with evidence traceability
- [ ] **PIPE-03**: System extracts structured policies/rules/constraints from unstructured text with evidence traceability
- [ ] **PIPE-04**: System generates test cases with 2-3 parameter variation axes per use case
- [ ] **PIPE-05**: System generates dataset examples with input messages, expected_output, and evaluation_criteria for each test case
- [ ] **PIPE-06**: System works on unseen inputs (anti-hardcoding — no dependency on specific filenames or directories)

### Data Contract (DATA)

- [ ] **DATA-01**: All output files comply with strict JSON schema (use_cases.json, policies.json, test_cases.json, dataset.json)
- [ ] **DATA-02**: IDs follow prefix conventions: uc_, pol_, tc_, ex_ — unique within their file
- [ ] **DATA-03**: Evidence entries contain input_file, line_start (1-based), line_end (>=line_start), and verbatim quote
- [ ] **DATA-04**: Evidence quotes exactly match source text at specified line range (after newline normalization)
- [ ] **DATA-05**: Policy type is one of: must, must_not, escalate, style, format (extensible)
- [ ] **DATA-06**: Message roles are one of: user, operator, assistant, system
- [ ] **DATA-07**: Each dataset example has: id, case, format, use_case_id, test_case_id, input.messages[], expected_output, evaluation_criteria (3+), policy_ids (1+)
- [ ] **DATA-08**: run_manifest.json generated per run with: input_path, out_path, seed, timestamp, generator_version, llm block

### Validation (VALD)

- [ ] **VALD-01**: Built-in `validate` command checks data contract compliance and prints summary report
- [ ] **VALD-02**: `validate` exits with code 0 on success, >0 on errors
- [ ] **VALD-03**: Validation checks referential integrity (use_case_id, policy_ids, test_case_id links)

### CLI Interface (CLI)

- [ ] **CLI-01**: CLI supports `--input`, `--out`, `--seed` parameters
- [ ] **CLI-02**: CLI supports `--n-use-cases`, `--n-test-cases-per-uc`, `--n-examples-per-tc` parameters
- [ ] **CLI-03**: CLI supports `--model` parameter (default gpt-4o-mini, configurable to gpt-4o)
- [ ] **CLI-04**: CLI invoked as `python -m dataset_generator` with generate and validate subcommands

### Support Bot — Case A (SUPP)

- [ ] **SUPP-01**: System processes FAQ + ticket export markdown and extracts minimum 5 use cases
- [ ] **SUPP-02**: System extracts minimum 5 policies with at least 2 different types for support case
- [ ] **SUPP-03**: Policies include (by meaning): "no account access → escalate/provide contacts" and "tone-of-voice on aggression"
- [ ] **SUPP-04**: System generates minimum 3 test cases per use case with parameter variation
- [ ] **SUPP-05**: Dataset uses `single_turn_qa` format with `case = support_bot`
- [ ] **SUPP-06**: Dataset includes examples with `metadata.source` = tickets, faq_paraphrase, and corner
- [ ] **SUPP-07**: Tickets examples: 1 user message, expected_output respects constraints (no fabricated account data)
- [ ] **SUPP-08**: FAQ paraphrase examples: rephrased FAQ question with reference answer as expected_output
- [ ] **SUPP-09**: Corner case examples: garbage/off-topic/profanity/injection with safe response as expected_output

### Operator Quality — Case B (OPER)

- [ ] **OPER-01**: System processes operator quality checks markdown and extracts minimum 5 use cases
- [ ] **OPER-02**: System extracts minimum 5 policies with at least 2 different types for operator case
- [ ] **OPER-03**: Policies include (by meaning): "fix punctuation/typos", "no caps/!!!", "preserve medical terms", "no personal doctor phone", "escalate on complaint"
- [ ] **OPER-04**: System generates minimum 3 test cases per use case with parameter variation
- [ ] **OPER-05**: Dataset includes `single_utterance_correction` format: 1 operator message → corrected version
- [ ] **OPER-06**: Dataset includes `dialog_last_turn_correction` format: multi-message dialog → corrected last operator reply
- [ ] **OPER-07**: For `dialog_last_turn_correction`: target_message_index points to last message, which has role=operator

### Doctor Booking — Case C (BOOK)

- [ ] **BOOK-01**: System processes doctor booking markdown (mixed memo/FAQ/instructions/tickets) and extracts use cases
- [ ] **BOOK-02**: System extracts policies from the doctor booking document with evidence
- [ ] **BOOK-03**: System generates test cases and dataset for the doctor booking case

### Reproducibility (REPR)

- [ ] **REPR-01**: Same input + seed produces structurally consistent output (stable structure/validity/coverage)
- [ ] **REPR-02**: LLM calls use temperature=0 for determinism

### Integrations (INTG)

- [ ] **INTG-01**: Langfuse integration: upload generated dataset as dataset items, support experiment tracking
- [ ] **INTG-02**: DeepEval Synthesizer integration: generate goldens from FAQ documents with evolutions
- [ ] **INTG-03**: Evidently integration: generate data quality reports (duplicates, distributions, placeholders)
- [ ] **INTG-04**: Giskard Hub integration: import FAQ as knowledge base, generate document-based business tests

### Deliverables (DLVR)

- [ ] **DLVR-01**: Pre-generated output artifacts in out/support/ and out/operator_quality/ directories
- [ ] **DLVR-02**: README with setup instructions, dependencies, and environment variable configuration
- [ ] **DLVR-03**: API keys via environment variables only (OPENAI_API_KEY), never committed

## v2 Requirements

### Enhanced Generation

- **EGEN-01**: Advanced quality scoring with multi-dimensional filtering (clarity, relevance, depth)
- **EGEN-02**: DeepEval evolution types (reasoning, comparative, hypothetical complexity variations)
- **EGEN-03**: Adversarial/edge-case focused generation mode
- **EGEN-04**: CSV export option alongside JSON

### Extended Validation

- **EVAL-01**: Compatibility with official_validator.py (when provided)
- **EVAL-02**: JSON Schema file validation using provided schema files

## Out of Scope

| Feature | Reason |
|---------|--------|
| Building actual LLM agents (support bot, quality checker) | Only the test data pipeline — agents are separate |
| Official validator (official_validator.py) | Provided separately later by evaluators |
| Surge/Scale human review integration | Manual process, not automated |
| Patronus guardrails integration | Can add later if needed |
| Mobile/web UI | CLI only per spec |
| Real-time streaming generation | Batch mode sufficient for this use case |
| Multi-format input (PDF, DOCX) | Markdown only per spec |
| Built-in LLM model hosting | Use OpenAI API — don't host models |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PIPE-01 | — | Pending |
| PIPE-02 | — | Pending |
| PIPE-03 | — | Pending |
| PIPE-04 | — | Pending |
| PIPE-05 | — | Pending |
| PIPE-06 | — | Pending |
| DATA-01 | — | Pending |
| DATA-02 | — | Pending |
| DATA-03 | — | Pending |
| DATA-04 | — | Pending |
| DATA-05 | — | Pending |
| DATA-06 | — | Pending |
| DATA-07 | — | Pending |
| DATA-08 | — | Pending |
| VALD-01 | — | Pending |
| VALD-02 | — | Pending |
| VALD-03 | — | Pending |
| CLI-01 | — | Pending |
| CLI-02 | — | Pending |
| CLI-03 | — | Pending |
| CLI-04 | — | Pending |
| SUPP-01 | — | Pending |
| SUPP-02 | — | Pending |
| SUPP-03 | — | Pending |
| SUPP-04 | — | Pending |
| SUPP-05 | — | Pending |
| SUPP-06 | — | Pending |
| SUPP-07 | — | Pending |
| SUPP-08 | — | Pending |
| SUPP-09 | — | Pending |
| OPER-01 | — | Pending |
| OPER-02 | — | Pending |
| OPER-03 | — | Pending |
| OPER-04 | — | Pending |
| OPER-05 | — | Pending |
| OPER-06 | — | Pending |
| OPER-07 | — | Pending |
| BOOK-01 | — | Pending |
| BOOK-02 | — | Pending |
| BOOK-03 | — | Pending |
| REPR-01 | — | Pending |
| REPR-02 | — | Pending |
| INTG-01 | — | Pending |
| INTG-02 | — | Pending |
| INTG-03 | — | Pending |
| INTG-04 | — | Pending |
| DLVR-01 | — | Pending |
| DLVR-02 | — | Pending |
| DLVR-03 | — | Pending |

**Coverage:**
- v1 requirements: 48 total
- Mapped to phases: 0
- Unmapped: 48 (will be mapped during roadmap creation)

---
*Requirements defined: 2026-02-16*
*Last updated: 2026-02-16 after initial definition*
