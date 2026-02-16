# Phase 2 Plan 1: Enhanced Extraction Prompts Summary

**One-liner:** Enhanced use case and policy extraction prompts with structured JSON format, decision tree classification, and CHARACTER-EXACT evidence preservation instructions

---

## Frontmatter

```yaml
phase: 02-core-extraction
plan: 01
subsystem: extraction
tags: [prompts, llm, extraction, evidence-validation]
completed: 2026-02-16T13:32:58Z
duration_minutes: 3

dependency_graph:
  requires:
    - 01-foundation (Phase 1 complete)
    - src/dataset_generator/extraction/use_case_extractor.py (baseline)
    - src/dataset_generator/extraction/policy_extractor.py (baseline)
  provides:
    - Enhanced use case extraction with prose/table/implicit pattern recognition
    - Enhanced policy extraction with decision tree classification
    - Improved evidence accuracy through explicit formatting preservation
  affects:
    - All downstream extraction operations
    - Evidence validation accuracy

tech_stack:
  added: []
  patterns:
    - Structured JSON prompt formatting
    - Few-shot learning with Russian examples
    - Chain-of-thought classification
    - Decision tree for policy type disambiguation

key_files:
  created: []
  modified:
    - src/dataset_generator/extraction/use_case_extractor.py
    - src/dataset_generator/extraction/policy_extractor.py

decisions:
  - Use structured JSON task definition in prompts for clarity
  - Include 3 few-shot examples for use cases (bullet, prose, table)
  - Include 5 few-shot examples for policies (one per type)
  - Prioritize must_not and escalate before generic must in decision tree
  - Preserve ALL markdown formatting in evidence quotes (CHARACTER-EXACT)
  - Use generic terms (document, text, requirements) not document-specific references
```

---

## What Was Built

Enhanced extraction prompts for use case and policy extractors to improve evidence accuracy and policy type classification when handling unstructured text.

### Use Case Extractor Enhancements

**File:** `src/dataset_generator/extraction/use_case_extractor.py`

**Changes:**
1. Structured JSON task definition replacing free-form instructions
2. USE CASE IDENTIFICATION RULES section with generic patterns:
   - Action patterns: "может...", "должен...", "если...то..."
   - Question-answer pairs (FAQ sections)
   - Table rows with operator responses
   - Implicit use cases in prose
3. Enhanced EVIDENCE EXTRACTION section emphasizing CHARACTER-EXACT quotes:
   - Preserve ALL markdown formatting (*, **, bullets, pipes)
   - Preserve ALL whitespace
   - Extract COMPLETE quotes without truncation
4. Three few-shot examples covering:
   - Explicit use case from bullet list (1 line)
   - Implicit use case from prose (2 lines)
   - Use case from table row (preserving pipe characters)

### Policy Extractor Enhancements

**File:** `src/dataset_generator/extraction/policy_extractor.py`

**Changes:**
1. Structured JSON task definition
2. POLICY TYPE DECISION TREE with ordered steps for disambiguation:
   - Step 1: must_not (prohibitions)
   - Step 2: escalate (human escalation triggers)
   - Step 3: style (communication tone/style)
   - Step 4: format (output format/structure)
   - Step 5: must (general requirements)
3. CLASSIFICATION PROCESS instruction for chain-of-thought reasoning
4. Enhanced EVIDENCE EXTRACTION section (same as use case extractor)
5. Five few-shot examples with Russian text (one per type):
   - must_not: prohibition of medical advice
   - escalate: transfer to doctor for medical questions
   - style: neutral tone when user uses profanity
   - format: typo and punctuation correction
   - must: promo code validation requirement

---

## Deviations from Plan

None - plan executed exactly as written.

---

## Challenges & Solutions

**Challenge 1: Balancing generic patterns with concrete examples**
- **Issue:** Prompt needed to avoid document-specific references while still providing clear examples
- **Solution:** Used generic terms in instructions (document, text, requirements) but showed concrete Russian examples in few-shot section
- **Impact:** Examples provide clarity without hardcoding assumptions

**Challenge 2: Decision tree ordering for policy types**
- **Issue:** Some policy statements could fit multiple types (e.g., "must not give medical advice" could be must_not OR escalate)
- **Solution:** Ordered decision tree to check must_not and escalate BEFORE generic must, treating them as special cases with priority
- **Impact:** Reduces ambiguity in classification

---

## Testing & Verification

All verification checks from plan passed:

1. **Import verification:** Both extractors import successfully without errors
2. **Prompt content verification:**
   - Use case extractor contains "IDENTIFICATION RULES" section
   - Use case extractor contains "CHARACTER-FOR-CHARACTER" emphasis
   - Policy extractor contains "DECISION TREE" section
   - Policy extractor contains "CLASSIFICATION PROCESS" instruction
3. **Few-shot examples:** 3 examples in use case extractor, 5 examples (one per type) in policy extractor
4. **No hardcoded document references:** No occurrences of "ticket" or "support" in prompt templates (mentions of "FAQ" only as generic pattern type alongside prose and tables)
5. **Decision tree order:** must_not and escalate checked before must

---

## Known Limitations

1. **Evidence accuracy not yet measured:** Enhanced prompts should improve accuracy from ~80% to >90%, but requires testing against all three example documents to validate
2. **No fuzzy matching fallback yet:** Evidence validation still uses exact matching only; fuzzy fallback (RapidFuzz) deferred to future plan if needed
3. **Russian language nuances:** Policy type classification may require iteration based on testing with real documents
4. **Cross-platform whitespace:** Evidence validation normalizes line endings but LLM may still drop trailing whitespace in some cases

---

## Next Steps

From ROADMAP.md Phase 2 plans:

1. **Test extraction on all three documents** (support FAQ, operator quality, doctor booking) to validate generalization and measure evidence accuracy improvement
2. **Add fuzzy matching fallback** to evidence validator if accuracy remains <90% after prompt improvements (using RapidFuzz with 90%+ threshold)
3. **Measure policy type classification accuracy** on known examples from Phase 1

---

## Commits

| Task | Commit | Files Modified |
|------|--------|----------------|
| Task 1: Enhanced use case extractor | b82b634 | src/dataset_generator/extraction/use_case_extractor.py |
| Task 2: Enhanced policy extractor | ba92522 | src/dataset_generator/extraction/policy_extractor.py |

---

## Self-Check

Verifying all claimed artifacts exist and commits are recorded.

**Created files:** None (only modifications)

**Modified files:**
- FOUND: src/dataset_generator/extraction/use_case_extractor.py
- FOUND: src/dataset_generator/extraction/policy_extractor.py

**Commits:**
- FOUND: b82b634
- FOUND: ba92522

**Result:** PASSED - All artifacts and commits verified.
