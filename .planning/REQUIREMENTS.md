# Requirements: Synthetic Dataset Generator

**Defined:** 2026-02-16
**Core Value:** From a single raw markdown document, produce a complete, validated chain of artifacts (use_cases → policies → test_cases → dataset) with full traceability back to source text

## v1 Requirements

### Document Ingestion (INGEST)

- [ ] **INGEST-01**: Read raw markdown documents and parse into structured sections with line number tracking
- [ ] **INGEST-02**: Extract text chunks with configurable boundaries preserving paragraph/section context
- [ ] **INGEST-03**: Maintain line-to-content mapping for evidence traceability throughout pipeline

### Extraction (EXTRACT)

- [ ] **EXTRACT-01**: Extract structured use cases from unstructured text with evidence (line_start, line_end, quote)
- [ ] **EXTRACT-02**: Extract policies/rules/constraints from unstructured text with evidence traceability
- [ ] **EXTRACT-03**: Generate at least 5 use cases per input document (uc_ prefix IDs)
- [ ] **EXTRACT-04**: Generate at least 5 policies per input document with 2+ policy types (pol_ prefix IDs)

### Generation (GEN)

- [ ] **GEN-01**: Generate test cases with parameter variation axes per use case (tc_ prefix IDs)
- [ ] **GEN-02**: Generate at least 3 test cases per use case
- [ ] **GEN-03**: Generate dataset examples with input messages, expected output, and evaluation criteria (ex_ prefix IDs)
- [ ] **GEN-04**: Generate at least 1 example per test case
- [ ] **GEN-05**: All generated content must be in Russian (matching input documents)
- [ ] **GEN-06**: Support single_turn_qa format for support bot case
- [ ] **GEN-07**: Support single_utterance_correction format for operator quality checker case
- [ ] **GEN-08**: Support dialog_last_turn_correction format for operator quality checker case

### Data Contract (CONTRACT)

- [ ] **CONTRACT-01**: Enforce ID conventions with prefixes (uc_, pol_, tc_, ex_) validated at generation time
- [ ] **CONTRACT-02**: Enforce evidence format with exact quote matching (line_start, line_end, quote fields)
- [ ] **CONTRACT-03**: Enforce all mandatory fields per artifact type via Pydantic schema validation
- [ ] **CONTRACT-04**: Output valid JSON files: use_cases.json, policies.json, test_cases.json, dataset.json
- [ ] **CONTRACT-05**: Generate run_manifest.json per run (seed, model, timestamp, file paths)

### CLI Interface (CLI)

- [ ] **CLI-01**: Accept --input parameter for source markdown document path
- [ ] **CLI-02**: Accept --out parameter for output directory path
- [ ] **CLI-03**: Accept --seed parameter for reproducible generation
- [ ] **CLI-04**: Accept --n-use-cases parameter to control extraction count
- [ ] **CLI-05**: Accept --model parameter (default gpt-4o-mini, allow gpt-4o)
- [ ] **CLI-06**: Provide `validate` command that exits code 0 on valid output, non-zero on failure
- [ ] **CLI-07**: OpenAI API key via OPENAI_API_KEY environment variable (never hardcoded)

### Use Case Coverage (CASE)

- [ ] **CASE-01**: Support Case A — support bot (FAQ + tickets) end-to-end pipeline producing single_turn_qa dataset
- [ ] **CASE-02**: Support Case B — operator quality checker end-to-end pipeline producing correction datasets
- [ ] **CASE-03**: Support Case C — doctor booking (bonus case) end-to-end pipeline for algorithm validation

### Integrations (INTEG)

- [ ] **INTEG-01**: Langfuse integration for dataset upload and experiment tracking
- [ ] **INTEG-02**: DeepEval Synthesizer integration for golden dataset generation from FAQ docs
- [ ] **INTEG-03**: Evidently integration for data quality reports (duplicates, distributions)
- [ ] **INTEG-04**: Giskard Hub integration for document-based business test generation

### Deliverables (DELIVER)

- [ ] **DELIVER-01**: Pre-generated output artifacts in out/support/ directory
- [ ] **DELIVER-02**: Pre-generated output artifacts in out/operator_quality/ directory
- [ ] **DELIVER-03**: README with setup instructions, dependencies, and env configuration
- [ ] **DELIVER-04**: Same input + seed produces structurally consistent output (reproducibility)

## v2 Requirements

### Advanced Capabilities

- **ADV-01**: Anti-hardcoding validation mode — verify generator works on unseen inputs
- **ADV-02**: Evolution/complexity control — reasoning, comparative, hypothetical variations (DeepEval pattern)
- **ADV-03**: Quality filtering pre-generation — clarity, relevance, depth scoring before LLM calls
- **ADV-04**: Advanced quality scoring — multi-dimensional assessment of generated artifacts
- **ADV-05**: Multi-format input support — PDF, DOCX, HTML ingestion beyond markdown

## Out of Scope

| Feature | Reason |
|---------|--------|
| Building actual LLM agents | Only the test data pipeline, not the agents being tested |
| Official validator (official_validator.py) | Provided separately later for acceptance testing |
| Surge/Scale human review | Manual process, not automated in this tool |
| Patronus guardrails integration | Can add later if needed |
| GUI/web interface | CLI-first, separate product if demand validates |
| Built-in LLM model hosting | Support APIs, don't host models |
| Built-in evaluation/scoring | Langfuse/DeepEval excel here — integrate, don't compete |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INGEST-01 | Phase 1 | Pending |
| INGEST-02 | Phase 1 | Pending |
| INGEST-03 | Phase 1 | Pending |
| EXTRACT-01 | Phase 1 | Pending |
| EXTRACT-02 | Phase 1 | Pending |
| EXTRACT-03 | Phase 1 | Pending |
| EXTRACT-04 | Phase 1 | Pending |
| GEN-01 | Phase 2 | Pending |
| GEN-02 | Phase 2 | Pending |
| GEN-03 | Phase 2 | Pending |
| GEN-04 | Phase 2 | Pending |
| GEN-05 | Phase 1 | Pending |
| GEN-06 | Phase 2 | Pending |
| GEN-07 | Phase 3 | Pending |
| GEN-08 | Phase 3 | Pending |
| CONTRACT-01 | Phase 1 | Pending |
| CONTRACT-02 | Phase 1 | Pending |
| CONTRACT-03 | Phase 1 | Pending |
| CONTRACT-04 | Phase 2 | Pending |
| CONTRACT-05 | Phase 2 | Pending |
| CLI-01 | Phase 1 | Pending |
| CLI-02 | Phase 1 | Pending |
| CLI-03 | Phase 1 | Pending |
| CLI-04 | Phase 1 | Pending |
| CLI-05 | Phase 1 | Pending |
| CLI-06 | Phase 4 | Pending |
| CLI-07 | Phase 1 | Pending |
| CASE-01 | Phase 2 | Pending |
| CASE-02 | Phase 3 | Pending |
| CASE-03 | Phase 4 | Pending |
| INTEG-01 | Phase 5 | Pending |
| INTEG-02 | Phase 5 | Pending |
| INTEG-03 | Phase 5 | Pending |
| INTEG-04 | Phase 5 | Pending |
| DELIVER-01 | Phase 2 | Pending |
| DELIVER-02 | Phase 3 | Pending |
| DELIVER-03 | Phase 6 | Pending |
| DELIVER-04 | Phase 2 | Pending |

**Coverage:**
- v1 requirements: 38 total
- Mapped to phases: 38
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-16*
*Last updated: 2026-02-16 after initial definition*
