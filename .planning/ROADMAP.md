# Roadmap: Synthetic Dataset Generator for LLM Agent Testing

## Overview

Transform raw markdown business requirements into validated synthetic test datasets through a 5-phase journey. Start with foundational pipeline infrastructure and data contracts (Phase 1), build core extraction capabilities (Phase 2), integrate external frameworks (DeepEval, Ragas, Giskard) for generation with OpenAI orchestration (Phase 3), configure and run all three use cases (Phase 4), and finalize with validation, Langfuse integration, and deliverables (Phase 5). Each phase delivers observable user value, building toward the core promise: full traceability from source markdown to evaluation-ready datasets.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation & Pipeline Setup** - Project structure, CLI scaffolding, data schemas, markdown parsing with line tracking
- [ ] **Phase 2: Core Extraction** - Use case and policy extraction from unstructured text with evidence traceability
- [ ] **Phase 3: Test & Dataset Generation** - Framework integration (DeepEval, Ragas, Giskard) with OpenAI function-calling orchestration
- [ ] **Phase 4: All Use Cases** - Support bot, operator quality checker, and doctor booking case configuration and execution
- [ ] **Phase 5: Validation & Delivery** - Validate command, Langfuse integration, README, pre-generated artifacts

## Phase Details

### Phase 1: Foundation & Pipeline Setup
**Goal**: Users can ingest a markdown document, extract structured use cases and policies with evidence traceability, and see validated JSON output via the CLI
**Depends on**: Nothing (first phase)
**Requirements**: PIPE-01, PIPE-02, PIPE-03, PIPE-06, DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, CLI-01, CLI-02, CLI-03, CLI-04, REPR-01, REPR-02, DLVR-03
**Success Criteria** (what must be TRUE):
  1. User can run CLI with --input pointing to a markdown file and see use_cases.json + policies.json in --out directory
  2. Evidence fields (line_start, line_end, quote) match actual source document text
  3. All output passes Pydantic validation with correct ID prefixes (uc_, pol_) and mandatory fields
  4. Running with --seed produces structurally consistent extraction results
  5. CLI reads OPENAI_API_KEY from env and supports --model switching
**Plans:** 3 plans (complete)

Plans:
- [x] 01-01-PLAN.md — Project structure, dependencies, Pydantic data contracts, CLI skeleton
- [x] 01-02-PLAN.md — Markdown parser, LLM client, use case and policy extractors
- [x] 01-03-PLAN.md — Pipeline orchestrator, CLI wiring, end-to-end verification

### Phase 2: Core Extraction
**Goal**: User can extract structured use cases and policies from unstructured markdown with complete evidence traceability
**Depends on**: Phase 1
**Requirements**: PIPE-02, PIPE-03, PIPE-06
**Success Criteria** (what must be TRUE):
  1. System identifies use cases from prose without requiring explicit list formatting
  2. System extracts policies with correct type classification (must, must_not, escalate, style, format)
  3. Every extracted use case and policy has evidence with verbatim quote matching source lines
  4. System works on unseen inputs (not hardcoded to specific filenames or directory structures)
**Plans:** 2 plans

Plans:
- [ ] 02-01-PLAN.md — Enhanced extraction prompts with structured examples and policy decision tree
- [ ] 02-02-PLAN.md — RapidFuzz fuzzy matching integration and anti-hardcoding verification

### Phase 3: Test & Dataset Generation
**Goal**: User can generate test cases and dataset examples using DeepEval Synthesizer, Ragas, and Giskard Hub with OpenAI function-calling orchestration
**Depends on**: Phase 2
**Requirements**: PIPE-04, PIPE-05, DATA-07, DATA-08, INTG-02, INTG-03, INTG-04
**Success Criteria** (what must be TRUE):
  1. Each use case produces minimum 3 test cases with 2-3 parameter variation axes
  2. Each test case produces dataset examples with input messages, expected_output, and evaluation_criteria (3+)
  3. Dataset examples reference policy_ids and maintain referential integrity
  4. Generated messages use correct role conventions (user, operator, assistant, system)
  5. DeepEval Synthesizer generates test scenarios and dataset examples as primary engine
  6. OpenAI function calling orchestrates framework routing (not a fixed pipeline)
  7. Hardcoded adapters convert framework outputs to Pydantic data contracts
  8. Generated items include `generator` field in metadata tracking which framework produced them
  9. Fallback to direct OpenAI generation if a framework call fails
**Plans:** 4 plans

**Risk flags:**
- Framework API compatibility — DeepEval/Ragas/Giskard may have breaking changes
- Data format mapping between framework outputs and project Pydantic schemas needs adapters
- Function calling routing logic needs clear tool definitions

Plans:
- [ ] 03-01-PLAN.md — Data contracts (TestCase, DatasetExample, RunManifest) and framework dependencies
- [ ] 03-02-PLAN.md — Framework generators (DeepEval, Ragas, Giskard) with hardcoded adapters and fallback
- [ ] 03-03-PLAN.md — OpenAI function-calling orchestrator, coverage enforcement, and pipeline integration
- [ ] 03-04-PLAN.md — Evidently quality reports and end-to-end verification

### Phase 4: All Use Cases
**Goal**: User can generate complete datasets for all three use cases (support bot, operator quality checker, doctor booking) using the framework-powered pipeline
**Depends on**: Phase 3
**Requirements**: SUPP-01, SUPP-02, SUPP-03, SUPP-04, SUPP-05, SUPP-06, SUPP-07, SUPP-08, SUPP-09, OPER-01, OPER-02, OPER-03, OPER-04, OPER-05, OPER-06, OPER-07, BOOK-01, BOOK-02, BOOK-03
**Success Criteria** (what must be TRUE):
  1. Support Bot: extracts 5+ use cases and 5+ policies (2+ types), includes "no account access -> escalate" and "tone-of-voice on aggression" policies
  2. Support Bot: generates dataset in `single_turn_qa` format with `case = support_bot`, with ticket/faq_paraphrase/corner source types
  3. Operator Quality: extracts 5+ use cases and 5+ policies, includes "fix punctuation/typos", "no caps/!!!", "preserve medical terms", "no personal doctor phone", "escalate on complaint"
  4. Operator Quality: generates `single_utterance_correction` examples (1 operator message -> corrected) and `dialog_last_turn_correction` examples (multi-message dialog -> corrected last reply)
  5. Operator Quality: for dialog corrections, target_message_index points to last message with role=operator
  6. Doctor Booking: processes mixed memo/FAQ/instructions/tickets markdown and generates complete dataset
  7. All generated artifacts pass same validation rules across all three cases
**Plans:** 3 plans

**Risk flags:**
- Operator Quality correction formats are less documented than single-turn Q&A — may need prompt experimentation
- Doctor Booking validates algorithm generalization — pipeline must work on unseen inputs

Plans:
- [ ] 04-01-PLAN.md — Data model updates for tz.md contract and LLM-based case/format auto-detection
- [ ] 04-02-PLAN.md — Format-specific generation adapters, pairwise variation routing, and source classification
- [ ] 04-03-PLAN.md — Pipeline wiring with auto-detection, multi-format generation, and coverage enforcement

### Phase 5: Validation & Delivery
**Goal**: User can validate generated artifacts, export to Langfuse, and receive complete project deliverables
**Depends on**: Phase 4
**Requirements**: VALD-01, VALD-02, VALD-03, INTG-01, DLVR-01, DLVR-02
**Success Criteria** (what must be TRUE):
  1. User can invoke `python -m dataset_generator validate --out <dir>` to check data contract compliance
  2. Validation prints summary report (counts, errors, warnings) and exits 0 on success, >0 on errors
  3. Validation checks referential integrity (use_case_id, policy_ids, test_case_id links) and evidence quote matching
  4. User can upload generated dataset to Langfuse as dataset items with experiment tracking
  5. Pre-generated output artifacts exist in out/support/ and out/operator_quality/ directories
  6. README provides complete setup instructions, dependencies, and environment variable configuration
**Plans:** 3 plans

Plans:
- [ ] 05-01-PLAN.md — Validation command with referential integrity checks and exit codes
- [ ] 05-02-PLAN.md — Langfuse integration for dataset upload with experiment tracking
- [ ] 05-03-PLAN.md — Pre-generated artifacts and comprehensive README documentation

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Pipeline Setup | 3/3 | Complete | 2026-02-16 |
| 2. Core Extraction | 0/2 | Planned | - |
| 3. Test & Dataset Generation | 0/4 | Planned | - |
| 4. All Use Cases | 0/3 | Planned | - |
| 5. Validation & Delivery | 0/3 | Planned | - |

## Coverage

All 48 v1 requirements mapped to phases with zero orphans.

| Category | Count | Phase(s) |
|----------|-------|----------|
| PIPE (6) | 6 | Phase 1 (PIPE-01), Phase 2 (PIPE-02, PIPE-03, PIPE-06), Phase 3 (PIPE-04, PIPE-05) |
| DATA (8) | 8 | Phase 1 (DATA-01 to DATA-06), Phase 3 (DATA-07, DATA-08) |
| VALD (3) | 3 | Phase 5 (VALD-01, VALD-02, VALD-03) |
| CLI (4) | 4 | Phase 1 (CLI-01, CLI-02, CLI-03, CLI-04) |
| SUPP (9) | 9 | Phase 4 (SUPP-01 to SUPP-09) |
| OPER (7) | 7 | Phase 4 (OPER-01 to OPER-07) |
| BOOK (3) | 3 | Phase 4 (BOOK-01, BOOK-02, BOOK-03) |
| REPR (2) | 2 | Phase 1 (REPR-01, REPR-02) |
| INTG (4) | 4 | Phase 3 (INTG-02, INTG-03, INTG-04), Phase 5 (INTG-01) |
| DLVR (3) | 3 | Phase 1 (DLVR-03), Phase 5 (DLVR-01, DLVR-02) |

**Total: 48/48 mapped**

---
*Roadmap created: 2026-02-16*
*Depth: standard (5 phases, consolidated from 8)*
*Last updated: 2026-02-16*
