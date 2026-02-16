# Roadmap: Synthetic Dataset Generator for LLM Agent Testing

## Overview

Transform raw markdown business requirements into validated synthetic test datasets through an 8-phase journey. Start with foundational pipeline infrastructure and data contracts (Phase 1), build core extraction and generation capabilities (Phases 2-3), implement three progressively complex use cases (Phases 4-6), add validation systems (Phase 7), and complete with external integrations and deliverables (Phase 8). Each phase delivers observable user value, building toward the core promise: full traceability from source markdown to evaluation-ready datasets.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation & Pipeline Setup** - Project structure, CLI scaffolding, data schemas, markdown parsing with line tracking
- [ ] **Phase 2: Core Extraction** - Use case and policy extraction from unstructured text with evidence traceability
- [ ] **Phase 3: Test & Dataset Generation** - Test case generation with parameter variation and dataset example synthesis
- [ ] **Phase 4: Support Bot Case** - Complete implementation of single-turn Q&A for support bot use case
- [ ] **Phase 5: Operator Quality Case** - Utterance correction and dialog correction datasets for quality checker
- [ ] **Phase 6: Doctor Booking Case** - Third use case demonstrating algorithm generalization
- [ ] **Phase 7: Validation System** - Built-in validation command with data contract compliance checks
- [ ] **Phase 8: Integrations & Deliverables** - External platform integrations and final deliverables

## Phase Details

### Phase 1: Foundation & Pipeline Setup
**Goal**: Users can ingest a markdown document, extract structured use cases and policies with evidence traceability, and see validated JSON output via the CLI
**Depends on**: Nothing (first phase)
**Requirements**: PIPE-01, PIPE-02, PIPE-03, PIPE-06, DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, CONTRACT-01, CONTRACT-02, CONTRACT-03, CLI-01, CLI-02, CLI-03, CLI-04, CLI-05, CLI-07, GEN-05, REPR-01, REPR-02
**Success Criteria** (what must be TRUE):
  1. User can run CLI with --input pointing to a markdown file and see use_cases.json + policies.json in --out directory
  2. Evidence fields (line_start, line_end, quote) match actual source document text
  3. All output passes Pydantic validation with correct ID prefixes (uc_, pol_) and mandatory fields
  4. Running with --seed produces structurally consistent extraction results
  5. CLI reads OPENAI_API_KEY from env and supports --model switching
**Plans:** 3 plans

Plans:
- [ ] 01-01-PLAN.md — Project structure, dependencies, Pydantic data contracts, CLI skeleton
- [ ] 01-02-PLAN.md — Markdown parser, LLM client, use case and policy extractors
- [ ] 01-03-PLAN.md — Pipeline orchestrator, CLI wiring, end-to-end verification

### Phase 2: Core Extraction
**Goal**: User can extract structured use cases and policies from unstructured markdown with complete evidence traceability
**Depends on**: Phase 1
**Requirements**: PIPE-02, PIPE-03, PIPE-06
**Success Criteria** (what must be TRUE):
  1. System identifies use cases from prose without requiring explicit list formatting
  2. System extracts policies with correct type classification (must, must_not, escalate, style, format)
  3. Every extracted use case and policy has evidence with verbatim quote matching source lines
  4. System works on unseen inputs (not hardcoded to specific filenames or directory structures)
**Plans**: TBD

Plans:
- [ ] TBD

### Phase 3: Test & Dataset Generation
**Goal**: User can generate test cases and dataset examples from extracted use cases with parameter variation
**Depends on**: Phase 2
**Requirements**: PIPE-04, PIPE-05
**Success Criteria** (what must be TRUE):
  1. Each use case produces minimum 3 test cases with 2-3 parameter variation axes
  2. Each test case produces dataset examples with input messages, expected_output, and evaluation_criteria (3+)
  3. Dataset examples reference policy_ids and maintain referential integrity
  4. Generated messages use correct role conventions (user, operator, assistant, system)
**Plans**: TBD

Plans:
- [ ] TBD

### Phase 4: Support Bot Case
**Goal**: User can generate complete support bot test dataset in single_turn_qa format from FAQ + ticket markdown
**Depends on**: Phase 3
**Requirements**: SUPP-01, SUPP-02, SUPP-03, SUPP-04, SUPP-05, SUPP-06, SUPP-07, SUPP-08, SUPP-09
**Success Criteria** (what must be TRUE):
  1. System extracts minimum 5 use cases and 5 policies (2+ types) from support bot input
  2. Policies include "no account access -> escalate" and "tone-of-voice on aggression" constraints
  3. Dataset includes ticket examples (1 user message, constrained response), FAQ paraphrases (rephrased question + answer), and corner cases (garbage/profanity/injection with safe responses)
  4. All examples use `single_turn_qa` format with `case = support_bot`
  5. Examples have correct `metadata.source` values (tickets, faq_paraphrase, corner)
**Plans**: TBD

Plans:
- [ ] TBD

### Phase 5: Operator Quality Case
**Goal**: User can generate operator quality checker datasets in both single_utterance_correction and dialog_last_turn_correction formats
**Depends on**: Phase 4
**Requirements**: OPER-01, OPER-02, OPER-03, OPER-04, OPER-05, OPER-06, OPER-07
**Success Criteria** (what must be TRUE):
  1. System extracts minimum 5 use cases and 5 policies (2+ types) from operator quality input
  2. Policies include "fix punctuation/typos", "no caps/!!!", "preserve medical terms", "no personal doctor phone", "escalate on complaint"
  3. Dataset includes single_utterance_correction examples (1 operator message -> corrected version)
  4. Dataset includes dialog_last_turn_correction examples (multi-message dialog -> corrected last operator reply)
  5. For dialog corrections, target_message_index points to last message with role=operator
**Plans**: TBD

Plans:
- [ ] TBD

### Phase 6: Doctor Booking Case
**Goal**: User can generate doctor booking test dataset, validating algorithm generalization to mixed document types
**Depends on**: Phase 5
**Requirements**: BOOK-01, BOOK-02, BOOK-03
**Success Criteria** (what must be TRUE):
  1. System processes doctor booking markdown (mixed memo/FAQ/instructions/tickets format) without failure
  2. System extracts use cases and policies from doctor booking document with evidence
  3. System generates test cases and dataset examples for doctor booking case
  4. Generated artifacts pass same validation as support bot and operator quality cases
**Plans**: TBD

Plans:
- [ ] TBD

### Phase 7: Validation System
**Goal**: User can validate generated artifacts and receive actionable compliance reports
**Depends on**: Phase 6
**Requirements**: VALD-01, VALD-02, VALD-03
**Success Criteria** (what must be TRUE):
  1. User can invoke `python -m dataset_generator validate --out <dir>` to check data contract compliance
  2. Validation command prints summary report (counts, errors, warnings) to console
  3. Validation exits with code 0 on success, >0 on errors (CI/CD friendly)
  4. Validation checks referential integrity (use_case_id, policy_ids, test_case_id links exist)
  5. Validation reports evidence quote mismatches (quote doesn't match source lines)
**Plans**: TBD

Plans:
- [ ] TBD

### Phase 8: Integrations & Deliverables
**Goal**: User can export datasets to major evaluation platforms and receive complete project deliverables
**Depends on**: Phase 7
**Requirements**: INTG-01, INTG-02, INTG-03, INTG-04, DLVR-01, DLVR-02
**Success Criteria** (what must be TRUE):
  1. User can upload generated dataset to Langfuse as dataset items with experiment tracking
  2. User can invoke DeepEval Synthesizer integration to generate goldens from FAQ documents with evolution types
  3. User can generate Evidently data quality reports showing duplicates, distributions, and placeholder detection
  4. User can import FAQ to Giskard Hub and generate document-based business tests
  5. Pre-generated output artifacts exist in out/support/ and out/operator_quality/ directories
  6. README provides complete setup instructions, dependencies, and environment variable configuration
**Plans**: TBD

Plans:
- [ ] TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Pipeline Setup | 0/3 | Planning complete | - |
| 2. Core Extraction | 0/TBD | Not started | - |
| 3. Test & Dataset Generation | 0/TBD | Not started | - |
| 4. Support Bot Case | 0/TBD | Not started | - |
| 5. Operator Quality Case | 0/TBD | Not started | - |
| 6. Doctor Booking Case | 0/TBD | Not started | - |
| 7. Validation System | 0/TBD | Not started | - |
| 8. Integrations & Deliverables | 0/TBD | Not started | - |

## Coverage

All 48 v1 requirements mapped to phases with zero orphans.

| Category | Count | Phase(s) |
|----------|-------|----------|
| PIPE (6) | 6 | Phase 1 (PIPE-01), Phase 2 (PIPE-02, PIPE-03, PIPE-06), Phase 3 (PIPE-04, PIPE-05) |
| DATA (8) | 8 | Phase 1 (DATA-01 to DATA-08) |
| VALD (3) | 3 | Phase 7 (VALD-01, VALD-02, VALD-03) |
| CLI (4) | 4 | Phase 1 (CLI-01, CLI-02, CLI-03, CLI-04) |
| SUPP (9) | 9 | Phase 4 (SUPP-01 to SUPP-09) |
| OPER (7) | 7 | Phase 5 (OPER-01 to OPER-07) |
| BOOK (3) | 3 | Phase 6 (BOOK-01, BOOK-02, BOOK-03) |
| REPR (2) | 2 | Phase 1 (REPR-01, REPR-02) |
| INTG (4) | 4 | Phase 8 (INTG-01, INTG-02, INTG-03, INTG-04) |
| DLVR (3) | 3 | Phase 1 (DLVR-03), Phase 8 (DLVR-01, DLVR-02) |

**Total: 48/48 mapped**

---
*Roadmap created: 2026-02-16*
*Depth: standard (8 phases)*
*Last updated: 2026-02-16*
