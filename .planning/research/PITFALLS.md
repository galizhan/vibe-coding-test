# Pitfalls Research

**Domain:** LLM-based synthetic dataset generation with document extraction
**Researched:** 2026-02-16
**Confidence:** MEDIUM

## Critical Pitfalls

### Pitfall 1: Evidence Traceability Degradation

**What goes wrong:**
LLMs hallucinate or paraphrase source text instead of extracting verbatim quotes, breaking the chain of evidence traceability. Line numbers become incorrect due to text preprocessing, or the model invents plausible-sounding quotes that don't exist in the source document.

**Why it happens:**
Foundational LLMs are trained to generate fluent text, not to perform precise text extraction. They excel at summarization and paraphrasing but struggle with exact string matching. Additionally, LLMs "erroneously invent citations in many cases" when asked to provide attribution. When documents are split across context windows or preprocessed (whitespace normalization, markdown parsing), original line numbers shift.

**How to avoid:**
- Embed explicit line number metadata directly into file content before submitting to the LLM (e.g., `<1> text</1>`, `<2> more text</2>`)
- Use structured output formats (JSON mode) to enforce exact quote extraction in a dedicated field
- Implement post-extraction validation: programmatically verify every extracted quote exists verbatim in the source document
- Consider two-pass extraction: (1) LLM identifies relevant sections, (2) rule-based exact match finds verbatim quotes
- Store original text with line numbers in metadata alongside extracted data for verification
- Use LangExtract or similar tools that "map every extraction to its exact location in the source text for traceability"

**Warning signs:**
- Validation failures show quotes not found in source documents
- Line numbers reference empty lines or incorrect content
- Extracted quotes have slightly different wording than source (punctuation, capitalization, extra words)
- High variance in quote accuracy across different document sections
- Model outputs like "approximately on line X" or "around line Y" instead of exact references

**Phase to address:**
Phase 1 (Core extraction) — Must establish evidence validation from the start, as later phases build on this foundation.

---

### Pitfall 2: Overfitting to Training Examples (Hardcoding by Proxy)

**What goes wrong:**
The extraction pipeline appears to work perfectly on provided examples but fails catastrophically on new, unseen documents. The LLM memorizes patterns specific to the training documents (e.g., always extracting 5 use cases, always finding "security" policies) rather than generalizing extraction logic.

**Why it happens:**
"LLMs exposed to repeated phrasing, structure, or content patterns can become overly reliant on these patterns, thereby reducing their generalization." When prompts include example outputs from specific documents, the model learns document-specific features instead of general extraction principles. Over 50% of fine-tuning data can be extracted from fine-tuned LLMs, indicating strong memorization. Special characters in JSON structure can trigger memorized patterns.

**How to avoid:**
- Test extraction on held-out documents NOT used during prompt development
- Use few-shot prompting with diverse example structures, not just the target documents
- Implement schema-driven extraction: define what to extract (JSON schema) without showing example outputs from target docs
- Vary prompt construction across runs to prevent pattern memorization
- Add explicit anti-hardcoding tests: create edge case documents with unusual structures
- Monitor for suspiciously consistent outputs (always same number of entities, same categories)
- Implement cross-validation: extract from multiple document types and measure consistency

**Warning signs:**
- 100% success on Case A & B, 0% on Case C (doctor booking) or other unseen inputs
- Extracted entity counts always match the minimum thresholds (exactly 5 use cases, exactly 5 policies)
- Failure modes appear only when document structure differs from examples (different heading styles, no numbered lists)
- Error messages contain references to specific domain terminology from training docs
- Test coverage metrics show high path coverage but low branch coverage

**Phase to address:**
Phase 1 (Core extraction) — Validate generalization early. Phase 2+ (Integration) — Add continuous testing with synthetic edge cases.

---

### Pitfall 3: Non-Deterministic Reproducibility Failure

**What goes wrong:**
Setting a seed parameter doesn't produce identical outputs across runs. Different hardware, API versions, or load balancing return different extractions despite identical inputs and seed values. Teams can't debug issues because they can't reproduce extraction runs.

**Why it happens:**
"LLMs are indeterministic even when a constant seed value, a temperature of 0, and identical prompts and documents are used." OpenAI states their API can only be "mostly deterministic" regardless of temperature due to "system updates and load balancing across different hardware." The `system_fingerprint` field changes when model weights or infrastructure update. Seeds are model-specific; different model versions produce different outputs with the same seed.

**How to avoid:**
- Record `system_fingerprint` from API responses in run_manifest.json to detect infrastructure changes
- Set temperature=0 AND seed for maximum reproducibility, understanding it's still "mostly" not "fully" deterministic
- Store exact model version (e.g., "gpt-4o-mini-2024-07-18") not just "gpt-4o-mini" in manifests
- Implement structural reproducibility tests: verify same entities extracted, not exact token-level output
- Use batch API endpoint for consistent infrastructure within a batch
- Add retry logic with seed+attempt_number to maintain audit trail when outputs differ
- Document acceptable variance thresholds (e.g., "90%+ entity overlap across runs is reproducible enough")

**Warning signs:**
- Same input+seed produces 5 use cases in run 1, 6 use cases in run 2
- CI pipeline tests fail randomly despite no code changes
- Different team members get different extraction results from identical commands
- run_manifest.json shows different system_fingerprint values between runs
- Customer reports "it worked yesterday, doesn't work today" without code deployment

**Phase to address:**
Phase 1 (Core extraction) — Implement fingerprint tracking. Phase 2+ (Integration) — Add Langfuse experiment tracking to monitor reproducibility drift over time.

---

### Pitfall 4: Prompt Context Overflow and Underflow

**What goes wrong:**
**Overflow:** Large documents exceed context windows, causing the model to ignore critical sections. Extraction silently fails for content beyond token limits. **Underflow:** Insufficient context causes hallucinations—the model guesses what policies might exist rather than extracting what actually exists.

**Why it happens:**
"Most language models have a limited context window, meaning they can only process a certain number of tokens at a time. If the document exceeds this limit, parts of it may be excluded from the prompt." Too little context leads to hallucination; "too much information causes context overflow, which overwhelms the LLM's attention span and lowers relevance across the whole context window, causing the model to struggle identifying which parts matter most."

**How to avoid:**
- Calculate document token count before extraction (tiktoken library for OpenAI)
- Implement chunking strategy for large documents with overlap to prevent context loss
- Use retrieval-augmented generation (RAG) for documents > 50% of context window: chunk document, embed chunks, retrieve relevant sections
- Add metadata to chunks (document section, page number) to maintain traceability across chunks
- Design prompts to explicitly handle "information not found" cases to prevent hallucination
- Monitor extraction completeness: flag when extracted entity count is suspiciously low for document size
- Set aggressive truncation for preamble/boilerplate, preserve core requirement sections

**Warning signs:**
- Long documents extract fewer entities than short documents of same complexity
- Entities extracted only from first half of documents
- Missing use cases that appear in later sections of input markdown
- Token usage in API responses approaches context window limits (e.g., 127k/128k tokens)
- Error logs show "context_length_exceeded" or silent truncation warnings
- Extraction quality degrades for documents > 10k tokens

**Phase to address:**
Phase 1 (Core extraction) — Implement token counting and chunking. Phase 2+ (Integration) — Add monitoring via Langfuse token usage tracking.

---

### Pitfall 5: Bias Amplification in Synthetic Data

**What goes wrong:**
Generated test cases exhibit systematic biases from the LLM's training data, creating test datasets that don't represent real-world distribution. For Russian-language generation, ideological biases "conditioned by the language of the prompt" produce different outputs than English prompts would generate. Self-improvement loops amplify existing biases in the source documents.

**Why it happens:**
"If the LLM's training data contained biases, hate speech, or private information, these could surface in synthetic outputs." Self-improvement methods like Self-Instruct "are limited by a model's capabilities and may suffer from amplified biases and errors." For multilingual contexts, "LLMs deployed across multilingual contexts may carry systematic biases conditioned by the language of the prompt."

**How to avoid:**
- Implement bias detection in generated datasets: check for demographic representation, sentiment skew, entity distribution
- Use Evidently integration to analyze synthetic data distributions and flag anomalies
- Generate test cases with explicit diversity requirements in prompts (vary user types, scenarios, edge cases)
- Cross-validate Russian outputs: have bilingual reviewer check for language-specific bias patterns
- Monitor for forbidden content in synthetic examples (hate speech, private info patterns)
- Compare synthetic data distributions to known ground truth or human-labeled samples
- Implement feedback loops: track which test cases catch real bugs vs. false positives

**Warning signs:**
- All generated support bot examples assume user is wrong, never support agent error
- Operator quality examples always correct grammar, never semantic/factual errors
- Test cases cluster around common scenarios, missing long-tail edge cases
- Russian language outputs contain political or cultural bias not present in source documents
- Synthetic dataset distribution differs significantly from production conversation data (when available for comparison)
- Exact match scores show synthetic records duplicating training examples

**Phase to address:**
Phase 2 (Integration) — Use Evidently for distribution analysis. Phase 3+ (Quality) — Add human review checkpoints via documentation for Surge/Scale integration.

---

### Pitfall 6: Schema Validation Theater

**What goes wrong:**
Generated JSON passes schema validation but violates semantic contracts. IDs follow prefix conventions but aren't actually unique. Evidence fields contain quotes that exist in the source but don't support the extracted claim. The pipeline reports "valid" but produces unusable data.

**Why it happens:**
"Early attempts at JSON output by requesting JSON directly within the prompt prove unreliable, as the model's interpretation can lead to malformed or incomplete JSON." Schema validation checks syntax and types but can't verify semantic correctness. LLMs can hallucinate plausible-looking valid JSON that's factually incorrect. Without separate semantic validation, "just prompting the schema has limitations—if the model isn't highly reliable or the schema is complex, it might still make mistakes in format."

**How to avoid:**
- Use OpenAI Structured Outputs feature: "ensures the model will always generate responses that adhere to your supplied JSON Schema"
- Implement two-stage validation: (1) schema validation for structure, (2) semantic validation for correctness
- Validate evidence quotes support their claims: programmatically check quote relevance to extracted entity
- Check ID uniqueness across entire output, not just per-entity-type
- Validate cross-references: if test case references use case ID, verify that use case exists
- Implement domain-specific validators: use case must have at least one policy, test case must have evaluation criteria
- Add "validate" CLI command that runs comprehensive checks beyond schema compliance
- Use ajv or jsonschema libraries for automated schema validation in test suites

**Warning signs:**
- Schema validation passes but official_validator.py fails
- Same ID appears multiple times across different entities
- Evidence quotes are accurate but irrelevant to extracted entity
- Required fields present but empty or contain placeholder text
- Cross-reference IDs point to non-existent entities
- Validation errors only discovered during integration testing, not during extraction

**Phase to address:**
Phase 1 (Core extraction) — Implement built-in validate command. Phase 3+ (Acceptance) — Integrate official_validator.py when provided.

---

### Pitfall 7: Multilingual Degradation (Russian-Specific)

**What goes wrong:**
Extraction quality degrades for Russian documents compared to English. Morphological complexity causes entity boundary errors (extracting part of a phrase due to case inflections). The LLM generates English responses despite Russian input, or mixes languages in outputs. Character encoding issues corrupt Cyrillic text.

**Why it happens:**
"Russian presents particular difficulty due to its morphological richness, with complex inflectional systems including multiple grammatical forms and cases that complicate tasks like extracting personal names from documents." While modern LLMs like GPT-4o support Russian, "applying them to specialized information extraction tasks for non-English historical or cultural content remains an experimental process." Prompt engineering tested primarily on English may not transfer to Russian.

**How to avoid:**
- Explicitly specify language in prompts: "Extract use cases in Russian. All outputs must be in Russian."
- Use Russian few-shot examples in prompts, not translated English examples
- Test character encoding end-to-end: UTF-8 from file read → API request → JSON output → file write
- Validate all text outputs are Russian using language detection libraries (langdetect)
- Handle morphological variants: don't expect exact string matching for entity recognition across different grammatical cases
- Use Russian-specific tokenizers for token counting (different from English token boundaries)
- Consider Russian-optimized models if quality issues persist (Qwen3 series has strong Russian support)
- Test with Russian edge cases: abbreviations, mixed Cyrillic/Latin, special characters

**Warning signs:**
- Extracted text contains English summaries of Russian content
- Entity boundaries cut mid-word due to case endings
- JSON schema validation fails due to unexpected characters despite valid UTF-8
- Token counts differ significantly from expected (Russian tokenizes differently than English)
- Generated test cases use English terminology mixed with Russian
- Line number references off by one due to different line ending conventions (CRLF vs LF)

**Phase to address:**
Phase 1 (Core extraction) — Implement language validation and encoding checks. All phases — Continuous testing with Russian-specific edge cases.

---

### Pitfall 8: Test Case Generation Quality Collapse

**What goes wrong:**
Generated test cases have high false positive rate (defective code passes erroneous tests) or false negative rate (correct code fails due to flawed tests). The model generates invalid test inputs that violate specified constraints. As problem difficulty increases, test case quality degrades significantly.

**Why it happens:**
"Invalid or hallucinated tests pose two major challenges in LLM-based code generation: false positives, where defective code passes erroneous tests, and false negatives, where correct code fails due to flawed tests." Studies show "the average illegal test input ratio is 40.1%" when LLMs generate test inputs directly according to constraints. "As problem difficulty increases, state-of-the-art LLMs struggle to generate correct test cases, largely due to their inherent limitations in computation and reasoning."

**How to avoid:**
- Implement Generator-Validator pattern: separate model generates test cases, validator checks correctness
- Use entropy-based validation (VALTEST approach) to identify hallucinated or invalid tests
- Validate test case inputs against constraints programmatically before including in dataset
- Generate multiple test case candidates, filter for quality rather than using first output
- Include explicit evaluation criteria in test case schema to catch missing verification logic
- Test the tests: run generated test cases against known-good and known-bad implementations
- Monitor true positive rate and true negative rate for generated test cases
- Start with simple test cases, increase complexity gradually while monitoring quality

**Warning signs:**
- Test cases pass trivial implementations that shouldn't pass
- Generated examples contain input values that violate documented constraints
- Evaluation criteria field empty or contains generic "check if works" descriptions
- Test case variety low: many generated cases differ only in superficial details
- Complex use cases generate simpler test cases than simpler use cases
- Manual review shows test cases don't actually test the stated scenario

**Phase to address:**
Phase 1 (Core extraction) — Include evaluation criteria in schema. Phase 2+ (Quality) — Implement automated test case validation before dataset finalization.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip post-extraction quote verification | Faster pipeline, simpler code | Silent hallucination in evidence, fails official validator | Never — traceability is core requirement |
| Use temperature > 0 for "creativity" | More varied outputs, less repetitive | Non-reproducible results, inconsistent quality | Only in exploratory phase, never in production |
| Ignore system_fingerprint field | Simpler manifest, less logging | Can't diagnose reproducibility issues, no audit trail | Never — needed for debugging |
| Batch all documents in single API call | Cost savings (50% discount), faster throughput | Loses individual document error handling, harder to debug | Only for production runs after per-document validation works |
| Prompt with target doc examples | Higher extraction accuracy on examples | Overfitting to examples, fails on new docs | Only during initial prompt development, must remove before testing |
| Skip token counting before API calls | Simpler code, faster execution | Silent context truncation, missing extractions | Never for large documents (>10k tokens) |
| Use default model without version pinning | Automatic improvements from OpenAI | Breaking changes, reproducibility issues across time | Never — always pin to specific version |
| Validate schema only, skip semantic checks | Fast validation, easy to implement | Invalid data passes validation, fails downstream | Only in MVP, must add semantic validation before v1.0 |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| OpenAI API | Not handling rate limits or retries | Use tenacity library for exponential backoff, respect rate limit headers |
| OpenAI API | Hardcoding model="gpt-4o-mini" without version | Use model="gpt-4o-mini-2024-07-18" or specific version, allow config override |
| OpenAI API | Exposing API keys in code or logs | Environment variables only, add .env to .gitignore, validate OPENAI_API_KEY set before running |
| Langfuse | Uploading datasets before validation | Validate all data contracts first, then upload to prevent polluting experiment tracking |
| Langfuse | Not tracking run_manifest.json metadata | Include seed, model, system_fingerprint in Langfuse traces for full reproducibility |
| DeepEval | Assuming synthesizer output is always valid | DeepEval generates from FAQ structure; still validate against schemas |
| Evidently | Running quality reports only at the end | Generate reports during development to catch distribution issues early |
| Giskard Hub | Uploading raw documents without preprocessing | Ensure documents are properly formatted, check encoding, validate structure first |
| JSON Schema Validation | Using Pydantic instead of JSON Schema | Use official JSON Schema validator (ajv, jsonschema) matching official_validator.py expectations |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Loading entire document into memory | Simple code, works in development | Memory errors on large docs, slow processing | Documents > 1MB or corpus > 100 docs |
| Sequential API calls for each extraction | Easy to debug, straightforward code | Cost explosion, slow pipelines | Processing > 10 documents or production use |
| No caching of API responses | Always fresh data, simpler logic | Repeated costs for same input, rate limit hits | Development iteration or CI pipeline runs |
| Storing all extracted data in single JSON file | Easy to read, simple file management | Slow parsing, memory issues, version control conflicts | Dataset > 1000 examples or team collaboration |
| Re-extracting everything on validation failure | Ensures consistency, simple retry logic | Wastes API calls, time, and money | More than 10% validation failure rate |
| No batching for large document sets | Simpler code, immediate feedback | High cost, slow throughput, API quota exhaustion | Processing > 50 documents |
| Synchronous processing without streaming | Simple code flow, easy error handling | Users wait minutes for large docs, no progress feedback | Documents taking > 30s to process |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Logging extracted content with PII | Privacy violation, NDA breach, GDPR issues | Sanitize logs: log only metadata (IDs, counts), never full extracted text |
| Storing API keys in run_manifest.json | Key leakage, unauthorized API usage costs | Store only model name, timestamp, seed — never keys or tokens |
| Uploading sensitive source documents to Langfuse/external services | Data breach, compliance violation | Add explicit flag for external upload, default to local-only, document data handling |
| Extracting and generating datasets without content filtering | Hate speech, PII, secrets in synthetic data | Implement content filters before dataset generation, validate outputs |
| Not validating extracted quotes contain PII | Real customer data leaks into test datasets | Add PII detection (emails, phone numbers, names) before including in output |
| Using public OpenAI API for confidential documents | Data retention, privacy policy violations | Document data handling policy, consider Azure OpenAI for enterprise data protection |
| Committing .env files with API keys | Key exposure, GitHub secret scanning alerts | .gitignore .env files, use environment variables, document setup in README |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Silent failures when extraction fails | User thinks it worked, gets invalid data downstream | Explicit error messages with context: "Failed to extract use cases from section 'Requirements' (line 45)" |
| No progress indication for long-running extractions | User assumes CLI hung, kills process prematurely | Add progress bars or step indicators: "Extracting use cases (1/3)...", "Validating evidence (2/3)..." |
| Cryptic validation errors from JSON schema | User doesn't know how to fix issues | Human-readable errors: "Use case 'uc_001' missing required field 'name'" not "Required property missing" |
| No way to preview extraction before full run | User wastes API calls on broken inputs | Add --dry-run or --preview flag showing token count, document structure, estimated cost |
| Binary success/fail with no quality metrics | User can't assess if output is actually good | Include quality report: "Extracted 7 use cases, 12 policies, 95% quotes verified, confidence: HIGH" |
| Overwriting previous runs without confirmation | User loses prior work, can't compare versions | Use timestamped output directories or --force flag requirement for overwrites |
| No way to incrementally fix validation failures | Must re-run entire expensive pipeline for small fixes | Support partial re-extraction or manual correction with re-validation |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Evidence Validation:** Extraction passes schema validation — verify every quote exists verbatim in source document with line numbers
- [ ] **Reproducibility:** Same seed produces same output in testing — verify system_fingerprint tracking and document version/config differences
- [ ] **Generalization:** Works on Case A & B — verify works on completely unseen document structure (Case C or synthetic edge case)
- [ ] **Multilingual Support:** Extracts Russian text — verify output is pure Russian, no English contamination, correct encoding
- [ ] **Token Overflow Handling:** Small test docs extract correctly — verify large documents (>50k tokens) chunk properly without data loss
- [ ] **Semantic Validation:** JSON validates against schema — verify IDs are unique, cross-references valid, evidence supports claims
- [ ] **Cost Optimization:** Pipeline works — verify batch API usage, caching strategy, not redundant API calls
- [ ] **Error Messages:** Failures produce errors — verify errors are actionable with context, not just stack traces
- [ ] **Data Quality:** Dataset generated — verify Evidently reports show reasonable distributions, no systematic bias, adequate variety
- [ ] **Integration Testing:** Each component works in isolation — verify end-to-end pipeline from raw markdown to validated dataset upload

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Evidence traceability broken | MEDIUM | 1. Implement quote verification script 2. Re-extract with line number tagging 3. Compare old vs new outputs 4. Update validation pipeline |
| Overfitting to examples | HIGH | 1. Create held-out test set 2. Re-engineer prompts without example outputs 3. Implement cross-validation 4. Re-extract all datasets |
| Reproducibility failure | LOW | 1. Add system_fingerprint logging 2. Pin model versions 3. Document acceptable variance 4. Implement structural equivalence tests |
| Context overflow | MEDIUM | 1. Implement token counting 2. Add document chunking 3. Re-extract affected documents 4. Validate completeness |
| Bias amplification | MEDIUM | 1. Run Evidently distribution analysis 2. Identify biased patterns 3. Adjust prompts with diversity requirements 4. Re-generate affected portions |
| Schema validation theater | LOW | 1. Implement semantic validators 2. Run on existing data to find issues 3. Fix and re-validate 4. Add to CI pipeline |
| Multilingual degradation | MEDIUM | 1. Add language detection 2. Use Russian examples in prompts 3. Re-extract with language-specific handling 4. Test character encoding |
| Test case quality collapse | HIGH | 1. Implement Generator-Validator pattern 2. Filter existing test cases for quality 3. Re-generate low-quality cases 4. Add automated quality checks |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Evidence traceability degradation | Phase 1: Core Extraction | Run validate command, check all quotes exist verbatim in source |
| Overfitting to training examples | Phase 1: Core Extraction | Extract from Case C (doctor booking) successfully without prompt changes |
| Non-deterministic reproducibility failure | Phase 1: Core Extraction | Check run_manifest.json contains system_fingerprint, test runs with same seed |
| Prompt context overflow/underflow | Phase 1: Core Extraction | Test with large document (>50k tokens), verify no silent truncation |
| Bias amplification in synthetic data | Phase 2: Integration (Evidently) | Evidently report shows no systematic distribution anomalies |
| Schema validation theater | Phase 1: Core Extraction + Phase 3: Acceptance | Built-in validate passes AND official_validator.py passes |
| Multilingual degradation (Russian) | Phase 1: Core Extraction | Language detection confirms 100% Russian output, encoding tests pass |
| Test case generation quality collapse | Phase 1: Core Extraction + Phase 2: Quality | Test case constraint validation, evaluation criteria non-empty checks |

## Sources

**LLM Synthetic Data Generation Challenges:**
- [Challenges and Pitfalls of Using Synthetic Data for LLMs | Medium](https://medium.com/foundation-models-deep-dive/challenges-and-pitfalls-of-using-synthetic-data-for-llms-7337fcda1316)
- [Using LLMs for Synthetic Data Generation: The Definitive Guide | Confident AI](https://www.confident-ai.com/blog/the-definitive-guide-to-synthetic-data-generation-using-llms)
- [Synthetic Data Generation Using Large Language Models | arXiv](https://arxiv.org/html/2503.14023v2)
- [OpenAI Cookbook: Synthetic Data Generation](https://cookbook.openai.com/examples/sdg1)

**Evidence Traceability & Document Extraction:**
- [Consensus uses GPT-5 and the Responses API | OpenAI](https://openai.com/index/consensus/)
- [Document Data Extraction in 2026: LLMs vs OCRs | Vellum](https://www.vellum.ai/blog/document-data-extraction-llms-vs-ocrs)
- [LangExtract: Extracting structured information with source grounding | Google GitHub](https://github.com/google/langextract)
- [A Method for Line Number Referencing in Large Language Models | TD Commons](https://www.tdcommons.org/cgi/viewcontent.cgi?article=9830&context=dpubs_series)

**Hallucination Prevention:**
- [Hallucination Detection and Mitigation in Large Language Models | arXiv](https://arxiv.org/pdf/2601.09929)
- [Hallucination-Free LLMs: The future of OCR and data extraction | Cradl AI](https://www.cradl.ai/post/hallucination-free-llm-data-extraction)
- [It's 2026. Why Are LLMs Still Hallucinating? | Duke University](https://blogs.library.duke.edu/blog/2026/01/05/its-2026-why-are-llms-still-hallucinating/)

**JSON Schema Validation:**
- [How To Ensure LLM Output Adheres to a JSON Schema | Modelmetry](https://modelmetry.com/blog/how-to-ensure-llm-output-adheres-to-a-json-schema)
- [Structured Outputs | OpenAI API](https://platform.openai.com/docs/guides/structured-outputs)
- [LLM evaluation techniques for JSON outputs | Promptfoo](https://www.promptfoo.dev/docs/guides/evaluate-json/)

**Reproducibility & Seeding:**
- [Controlling Creativity: How to Get Reproducible Outcomes from LLMs | Medium](https://medium.com/@prabhavithreddy/controlling-creativity-how-to-get-reproducible-outcomes-from-llms-016ec0991891)
- [How to get consistent and reproducible LLM outputs in 2025 | Keywords AI](https://www.keywordsai.co/blog/llm_consistency_2025)
- [Why is deterministic output from LLMs nearly impossible? | Unstract](https://unstract.com/blog/understanding-why-deterministic-output-from-llms-is-nearly-impossible/)

**Overfitting & Training Data Extraction:**
- [Extracting Training Data from Large Language Models | USENIX](https://www.usenix.org/system/files/sec21-carlini-extracting.pdf)
- [Understanding LLM Memorization | Tonic.ai](https://www.tonic.ai/guides/understanding-model-memorization-in-machine-learning)
- [Data Deduplication at Trillion Scale | Zilliz](https://zilliz.com/blog/data-deduplication-at-trillion-scale-solve-the-biggest-bottleneck-of-llm-training)

**Multilingual & Russian Language Challenges:**
- [10 Best Multilingual LLMs for 2026 | Azumo](https://azumo.com/artificial-intelligence/ai-insights/multilingual-llms)
- [Best Open Source LLM For Russian In 2026 | SiliconFlow](https://www.siliconflow.com/articles/en/best-open-source-LLM-for-Russian)
- [Evaluating Named Entity Recognition Models for Russian Cultural News | arXiv](https://arxiv.org/html/2506.02589v1)

**Prompt Engineering Challenges:**
- [What are the challenges with Prompt Engineering for document extraction?](https://anupupadhyay.com/what-all-are-the-challenges-with-prompt-engineering-with-extracting-information-from-a-document/)
- [Common LLM Prompt Engineering Challenges and Solutions | Latitude](https://latitude.so/blog/common-llm-prompt-engineering-challenges-and-solutions)
- [Context Engineering vs. Prompt Engineering | Elasticsearch Labs](https://www.elastic.co/search-labs/blog/context-engineering-vs-prompt-engineering)

**Test Case Generation Quality:**
- [LLM-Powered Test Case Generation for Detecting Tricky Bugs | arXiv](https://arxiv.org/html/2404.10304v1)
- [VALTEST: Automated Validation of Language Model Generated Test Cases | arXiv](https://arxiv.org/html/2411.08254v1)
- [Large Language Models as Test Case Generators | arXiv](https://arxiv.org/html/2404.13340v1)

**Cost Optimization & Token Management:**
- [OpenAI API Token Usage: Tracking and Optimization Guide | AI Infra Link](https://www.ai-infra-link.com/mastering-openai-api-token-usage-a-comprehensive-guide-to-tracking-and-optimization/)
- [OpenAI Pricing in 2026 | Finout](https://www.finout.io/blog/openai-pricing-in-2026)
- [Managing costs | OpenAI API](https://platform.openai.com/docs/guides/realtime-costs)

**Synthetic Data Quality Assessment:**
- [How to evaluate the quality of synthetic data | AWS ML Blog](https://aws.amazon.com/blogs/machine-learning/how-to-evaluate-the-quality-of-the-synthetic-data-measuring-from-the-perspective-of-fidelity-utility-and-privacy/)
- [Synthetic Data Validation: Methods & Best Practices | Qualtrics](https://www.qualtrics.com/articles/strategy-research/synthetic-data-validation/)
- [How good is your synthetic data? SynthRO dashboard | PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11837667/)

---
*Pitfalls research for: LLM-based synthetic dataset generation with document extraction*
*Researched: 2026-02-16*
