# Roadmap: Synthetic Dataset Generator

## Overview

This roadmap delivers a Python CLI tool that transforms raw business requirement documents into validated synthetic datasets for LLM agent evaluation. The journey progresses from foundational infrastructure (parsing, extraction, data contracts) through two mandatory use case pipelines (support bot, operator quality checker), an optional third case with validation tooling, external platform integrations, and final delivery polish. Each phase delivers a complete, verifiable capability that builds on the previous.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation** - Document ingestion, extraction pipeline, data contracts, CLI skeleton, and LLM client
- [ ] **Phase 2: Support Bot Pipeline** - Test case and dataset generation for Case A with single_turn_qa format
- [ ] **Phase 3: Operator Quality Checker** - Correction dataset formats and Case B end-to-end pipeline
- [ ] **Phase 4: Doctor Booking + Validation** - Case C bonus pipeline and the validate CLI command
- [ ] **Phase 5: External Integrations** - Langfuse, DeepEval, Evidently, and Giskard Hub connections
- [ ] **Phase 6: Polish and Delivery** - README, pre-generated artifacts verification, final validation pass

## Phase Details

### Phase 1: Foundation
**Goal**: Users can ingest a markdown document, extract structured use cases and policies with evidence traceability, and see validated JSON output via the CLI
**Depends on**: Nothing (first phase)
**Requirements**: INGEST-01, INGEST-02, INGEST-03, EXTRACT-01, EXTRACT-02, EXTRACT-03, EXTRACT-04, GEN-05, CONTRACT-01, CONTRACT-02, CONTRACT-03, CLI-01, CLI-02, CLI-03, CLI-04, CLI-05, CLI-07
**Success Criteria** (what must be TRUE):
  1. User can run the CLI with --input pointing to a markdown file and see structured use_cases.json and policies.json output in the --out directory
  2. Each extracted use case and policy contains evidence fields (line_start, line_end, quote) that match the actual source document text
  3. All output artifacts pass Pydantic schema validation with correct ID prefixes (uc_, pol_) and mandatory fields
  4. Running with --seed produces structurally consistent extraction results across repeated runs
  5. The CLI reads OPENAI_API_KEY from environment and supports --model to switch between gpt-4o-mini and gpt-4o
**Plans**: TBD

**Risk flags:**
- Evidence quoting implementation has no established pattern to copy -- will need custom solution (research confidence: MEDIUM)
- Russian language extraction quality with gpt-4o-mini is unvalidated -- test early
- Chunking strategy for requirement documents may need experimentation

Plans:
- [ ] 01-01: TBD
- [ ] 01-02: TBD
- [ ] 01-03: TBD

### Phase 2: Support Bot Pipeline
**Goal**: Users can run the complete end-to-end pipeline for Case A (support bot) and receive a validated dataset in single_turn_qa format
**Depends on**: Phase 1
**Requirements**: GEN-01, GEN-02, GEN-03, GEN-04, GEN-06, CONTRACT-04, CONTRACT-05, CASE-01, DELIVER-01, DELIVER-04
**Success Criteria** (what must be TRUE):
  1. User can run the CLI against the support bot markdown document and receive four output files: use_cases.json, policies.json, test_cases.json, dataset.json
  2. Test cases have tc_ prefix IDs with at least 3 test cases per use case, each containing parameter variation axes
  3. Dataset examples have ex_ prefix IDs in single_turn_qa format with input message, expected output, and evaluation criteria fields
  4. A run_manifest.json is generated containing seed, model, timestamp, and output file paths
  5. Pre-generated artifacts exist in out/support/ and produce valid output when regenerated with the same seed
**Plans**: TBD

**Risk flags:**
- Low risk -- single-turn Q&A generation is well-established pattern
- Minimum coverage thresholds (5+ use cases, 3+ test cases per UC, 1+ example per TC) need enforcement

Plans:
- [ ] 02-01: TBD
- [ ] 02-02: TBD

### Phase 3: Operator Quality Checker
**Goal**: Users can run the complete end-to-end pipeline for Case B (operator quality checker) and receive datasets in both correction formats
**Depends on**: Phase 2
**Requirements**: GEN-07, GEN-08, CASE-02, DELIVER-02
**Success Criteria** (what must be TRUE):
  1. User can run the CLI against the operator quality checker markdown document and receive complete output including correction-format datasets
  2. Dataset examples include single_utterance_correction format entries with original utterance, corrected utterance, and correction rationale
  3. Dataset examples include dialog_last_turn_correction format entries with dialog context, last turn, and corrected version
  4. Pre-generated artifacts exist in out/operator_quality/ and produce valid output when regenerated
**Plans**: TBD

**Risk flags:**
- Medium risk -- multi-turn dialog correction generation is less documented than single-turn Q&A
- Research recommends studying DeepEval evolution prompts and Evidently multi-turn patterns before implementation
- May need prompt engineering experimentation for correction quality

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD

### Phase 4: Doctor Booking + Validation
**Goal**: Users can run Case C (doctor booking) as a bonus pipeline and validate any generated output via the CLI validate command
**Depends on**: Phase 3
**Requirements**: CASE-03, CLI-06
**Success Criteria** (what must be TRUE):
  1. User can run the CLI against a doctor booking markdown document and receive complete dataset output, proving the pipeline generalizes beyond the two mandatory cases
  2. User can run `synth-data validate --out <dir>` and get exit code 0 for valid output or non-zero with error details for invalid output
  3. The validate command checks schema compliance, ID conventions, evidence format, and minimum coverage thresholds
**Plans**: TBD

**Risk flags:**
- Case C is an optional/bonus case -- validates algorithm generalizability but is not strictly required
- Anti-hardcoding concern: pipeline must work on unseen inputs, not just the provided examples
- Validate command must anticipate the official_validator.py schema that will be provided later

Plans:
- [ ] 04-01: TBD

### Phase 5: External Integrations
**Goal**: Users can push generated datasets to Langfuse, DeepEval, Evidently, and Giskard Hub for evaluation and quality analysis
**Depends on**: Phase 2 (needs stable dataset output; can run in parallel with Phase 4 if needed)
**Requirements**: INTEG-01, INTEG-02, INTEG-03, INTEG-04
**Success Criteria** (what must be TRUE):
  1. User can upload generated datasets to Langfuse for experiment tracking via a CLI command or flag
  2. User can generate golden datasets using DeepEval Synthesizer from FAQ documents
  3. User can generate Evidently data quality reports showing duplicate detection and distribution analysis
  4. User can export generated test cases to Giskard Hub for document-based business test evaluation
**Plans**: TBD

**Risk flags:**
- Low implementation risk -- all platforms have documented SDKs and standard adapter patterns
- Platform-specific schema requirements may need trial-and-error (exact field mappings not fully documented in research)
- Each integration should be independently toggleable -- user may not have all platform credentials

Plans:
- [ ] 05-01: TBD
- [ ] 05-02: TBD

### Phase 6: Polish and Delivery
**Goal**: The project is ready for handoff with documentation, verified pre-generated artifacts, and passing validation
**Depends on**: Phase 5
**Requirements**: DELIVER-03
**Success Criteria** (what must be TRUE):
  1. README contains setup instructions (Python version, dependencies, pip install), environment variable configuration (OPENAI_API_KEY, optional integration keys), and usage examples for all CLI commands
  2. Running the full pipeline on both mandatory cases with default settings produces valid output that passes the validate command
  3. All pre-generated artifacts in out/ directories are current and match what the pipeline produces with the documented seed
**Plans**: TBD

**Risk flags:**
- Low risk -- documentation and verification work
- Official validator (official_validator.py) may arrive during this phase and require adjustments

Plans:
- [ ] 06-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 0/3 | Not started | - |
| 2. Support Bot Pipeline | 0/2 | Not started | - |
| 3. Operator Quality Checker | 0/2 | Not started | - |
| 4. Doctor Booking + Validation | 0/1 | Not started | - |
| 5. External Integrations | 0/2 | Not started | - |
| 6. Polish and Delivery | 0/1 | Not started | - |

## Coverage

All 38 v1 requirements mapped to phases with zero orphans.

| Category | Count | Phase(s) |
|----------|-------|----------|
| INGEST (3) | 3 | Phase 1 |
| EXTRACT (4) | 4 | Phase 1 |
| GEN (8) | 8 | Phase 1 (GEN-05), Phase 2 (GEN-01 to GEN-04, GEN-06), Phase 3 (GEN-07, GEN-08) |
| CONTRACT (5) | 5 | Phase 1 (CONTRACT-01 to CONTRACT-03), Phase 2 (CONTRACT-04, CONTRACT-05) |
| CLI (7) | 7 | Phase 1 (CLI-01 to CLI-05, CLI-07), Phase 4 (CLI-06) |
| CASE (3) | 3 | Phase 2 (CASE-01), Phase 3 (CASE-02), Phase 4 (CASE-03) |
| INTEG (4) | 4 | Phase 5 |
| DELIVER (4) | 4 | Phase 2 (DELIVER-01, DELIVER-04), Phase 3 (DELIVER-02), Phase 6 (DELIVER-03) |

**Total: 38/38 mapped**

---
*Roadmap created: 2026-02-16*
*Depth: standard (6 phases)*
*Last updated: 2026-02-16*
