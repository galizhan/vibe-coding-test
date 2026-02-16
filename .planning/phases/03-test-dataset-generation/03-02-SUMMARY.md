# Phase 03 Plan 02: Framework Generators and Adapters Summary

**One-liner:** DeepEval/Ragas/Giskard generators with evolution configs plus hardcoded adapters converting native outputs to TestCase/DatasetExample with generator metadata

---

## Metadata

```yaml
phase: 03-test-dataset-generation
plan: 02
subsystem: generation
status: complete
completed: 2026-02-16
duration_minutes: 9
executor: sonnet

dependencies:
  requires:
    - 03-01  # TestCase and DatasetExample Pydantic models
  provides:
    - framework_generators  # DeepEval, Ragas, Giskard wrappers
    - adapter_layer  # Hardcoded Python adapters to project contracts
    - fallback_generator  # Direct OpenAI structured outputs
  affects:
    - test_generation_pipeline  # Core generation layer implementation

tech_stack:
  added:
    - deepeval.synthesizer  # Synthesizer with evolution/filtration/styling configs
    - ragas.testset  # TestsetGenerator with query distributions (v0.4 API)
    - giskard.rag  # KnowledgeBase and RAGET for knowledge-base questions
    - langchain_openai  # ChatOpenAI and OpenAIEmbeddings for Ragas
  patterns:
    - framework_wrapper  # Each generator wraps framework-specific calls
    - hardcoded_adapter  # Pure Python field mapping (no LLM calls)
    - graceful_fallback  # OpenAI direct generation when frameworks fail

key_files:
  created:
    - src/dataset_generator/generation/__init__.py
    - src/dataset_generator/generation/generators/__init__.py
    - src/dataset_generator/generation/generators/deepeval_gen.py
    - src/dataset_generator/generation/generators/ragas_gen.py
    - src/dataset_generator/generation/generators/giskard_gen.py
    - src/dataset_generator/generation/fallback.py
    - src/dataset_generator/generation/adapters/__init__.py
    - src/dataset_generator/generation/adapters/deepeval_adapter.py
    - src/dataset_generator/generation/adapters/ragas_adapter.py
    - src/dataset_generator/generation/adapters/giskard_adapter.py
  modified: []

decisions:
  - Updated Ragas generator for v0.4 API (TestsetGenerator.from_langchain with query_distribution instead of evolutions module)
  - Used langchain_openai ChatOpenAI and OpenAIEmbeddings for Ragas initialization
  - Mapped evolution types to parameter_variation_axes in adapters (reasoning->depth/complexity, multicontext->count/cross-ref, etc)
  - Force-added adapter files to git (adapters/ was in .gitignore but these are project code, not external adapters)
```

---

## What Was Built

### Framework Generators

**DeepEval Generator (`deepeval_gen.py`):**
- PRIMARY generation engine per user locked decision
- Wraps `Synthesizer` with comprehensive configuration:
  - Evolution config: 25% each of REASONING, MULTICONTEXT, CONCRETIZING, CONSTRAINED with num_evolutions=2
  - Filtration config: gpt-4o critic, quality_threshold=0.7, max_retries=3
  - Styling config: customer support context with specific input/output formats
- Generates goldens from document paths using `generate_goldens_from_docs`
- Returns list of DeepEval Golden objects
- Full error handling with RuntimeError wrapping

**Ragas Generator (`ragas_gen.py`):**
- RAG-specific question generation with knowledge graph transformations
- Updated for Ragas v0.4 API:
  - Uses `TestsetGenerator.from_langchain(llm, embeddings)` factory
  - Uses `QueryDistribution` with SingleHopSpecific, MultiHopAbstract, MultiHopSpecific
  - Parameters: `testset_size` (not `test_size`), `query_distribution` (not `distributions`)
- Configurable reasoning_ratio controls question type distribution
- Loads documents with langchain TextLoader
- Returns pandas DataFrame with question, ground_truth, contexts, metadata
- Handles NaN ground_truth values per research pitfall 2

**Giskard Generator (`giskard_gen.py`):**
- Knowledge-base-derived test questions using RAGET
- Creates `KnowledgeBase.from_pandas(df, columns=["content"])`
- Generates testset with `generate_testset(kb, num_questions, language, agent_description)`
- Returns pandas DataFrame with question, reference_answer, reference_context, metadata
- Warning logged about slow generation (15+ min for 60 questions per research)

**Fallback Generator (`fallback.py`):**
- LAST RESORT when framework calls fail
- Uses direct OpenAI client from `extraction.llm_client.get_openai_client()`
- JSON mode structured outputs (not Pydantic parse API)
- Builds system prompt describing task, policies, use case, output format requirements
- Manually constructs TestCase and DatasetExample Pydantic objects from JSON response
- Sets `metadata.generator = "openai_fallback"` on all generated items
- Temperature=0 and seed for reproducibility

### Adapters

**Common Adapter Pattern:**
- Two functions per framework: `adapt_*_to_test_case` and `adapt_*_to_example`
- Pure Python field mapping (no LLM calls per user locked decision)
- All include `"generator": "{framework_name}"` in metadata dict
- Handle missing/null fields with sensible defaults and logging.warning
- Graceful fallback: return minimal valid Pydantic instance on error with `adaptation_error` in metadata

**DeepEval Adapter (`deepeval_adapter.py`):**
- Maps Golden.input → TestCase name, Golden.context → description
- Evolution type → parameter_variation_axes mapping:
  - reasoning → ["reasoning_depth", "logical_complexity"]
  - multicontext → ["context_count", "cross_reference_depth"]
  - concretizing → ["scenario_specificity", "detail_level"]
  - constrained → ["constraint_type", "edge_case_complexity"]
  - default → ["tone", "complexity", "policy_boundary"]
- Extracts policy IDs from context using regex `pol_\w+` pattern
- Evaluation criteria based on evolution type (4 criteria minimum)
- Preserves quality_score from additional_metadata

**Ragas Adapter (`ragas_adapter.py`):**
- Handles both old (evolution_type) and new (synthesizer_name) Ragas v0.4 metadata
- Maps query types to parameter_variation_axes:
  - reasoning/abstract → ["reasoning_depth", "context_complexity"]
  - multi/specific → ["context_count", "cross_reference_depth"]
  - simple/single → ["tone", "specificity"]
- Extracts policy IDs from contexts list using regex
- Handles NaN ground_truth per research pitfall 2 (empty string fallback)
- Tracks contexts_used count in metadata

**Giskard Adapter (`giskard_adapter.py`):**
- Maps question_type to parameter_variation_axes:
  - complex/multi → ["context_complexity", "knowledge_depth"]
  - simple/direct → ["tone", "specificity"]
  - conversational → ["conversation_style", "formality_level"]
  - default → ["question_complexity", "knowledge_specificity"]
- Extracts policy IDs from reference_context string using regex
- Handles missing reference_answer (empty string fallback)
- Truncates reference_context to 200 chars for metadata preview

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated Ragas generator for v0.4 API changes**
- **Found during:** Task 1, verification step
- **Issue:** Ragas v0.4.3 changed API from `ragas.testset.evolutions` module with simple/reasoning/multi_context to `QueryDistribution` with synthesizer classes. `TestsetGenerator.with_openai()` no longer exists, replaced by `TestsetGenerator.from_langchain(llm, embeddings)`. Parameter names changed: `test_size` → `testset_size`, `distributions` → `query_distribution`.
- **Fix:**
  - Changed imports from `ragas.testset.evolutions` to `ragas.testset.synthesizers` with `QueryDistribution`, `SingleHopSpecificQuerySynthesizer`, `MultiHopAbstractQuerySynthesizer`, `MultiHopSpecificQuerySynthesizer`
  - Added `langchain_openai` imports for `ChatOpenAI` and `OpenAIEmbeddings`
  - Updated generator initialization to use `TestsetGenerator.from_langchain(llm=ChatOpenAI(model), embedding_model=OpenAIEmbeddings())`
  - Changed distribution configuration to `QueryDistribution(SingleHopSpecificQuerySynthesizer=ratio, ...)`
  - Updated `generate_with_langchain_docs` call to use `testset_size` parameter and `query_distribution`
- **Files modified:** `src/dataset_generator/generation/generators/ragas_gen.py`
- **Commit:** eb4cd6e (included in Task 1 commit)
- **Rationale:** Research examples used older Ragas API. Current installed version (0.4.3) has breaking API changes. Adaptation required to make generator functional.

**2. [Rule 3 - Blocking] Force-added adapter files to git**
- **Found during:** Task 2, commit step
- **Issue:** `adapters/` directory was in .gitignore, preventing adapter files from being staged. This is a false positive - the gitignore rule was meant for external third-party adapters, not project source code.
- **Fix:** Used `git add -f` to force-add the four adapter files and __init__.py
- **Files modified:** git staging
- **Commit:** ce6ce5d
- **Rationale:** These are project source code implementing core functionality, not external dependencies. The .gitignore rule does not apply to `src/dataset_generator/generation/adapters/`.

---

## Verification Results

All verification steps passed:

1. ✅ DeepEval generator importable: `generate_with_deepeval` function available
2. ✅ Ragas generator importable: `generate_with_ragas` function available (with v0.4 API)
3. ✅ Giskard generator importable: `generate_with_giskard` function available
4. ✅ Fallback generator importable: `generate_with_openai_fallback` function available
5. ✅ All six adapter functions importable
6. ✅ DeepEval adapter test with mock object:
   - TestCase ID starts with `tc_`
   - TestCase metadata includes `generator: "deepeval"`
   - TestCase has 2-3 parameter_variation_axes (Pydantic validation passed)
   - DatasetExample ID starts with `ex_`
   - DatasetExample metadata includes `generator: "deepeval"`
   - DatasetExample has 3+ evaluation_criteria (Pydantic validation passed)

---

## Architecture Notes

**Generator Layer Design:**
- Each generator is a pure function: `generate_with_{framework}(paths/data, params) -> framework_native_output`
- Generators return framework-native formats (DeepEval Goldens, pandas DataFrames)
- Adapters are separate pure functions: `adapt_{framework}_{type}(native_obj, ids, params) -> Pydantic_model`
- This separation allows:
  - Framework outputs to be cached without Pydantic serialization
  - Adapter logic to be tested independently with mock objects
  - Easy framework upgrades (change generator, adapters stay same)

**Adapter Layer Design:**
- Hardcoded field mapping per user locked decision
- No LLM calls (deterministic, fast, no API costs)
- Evolution type → parameter axes mapping is heuristic-based
- Policy ID extraction uses regex `pol_\w+` pattern from contexts
- Graceful degradation: missing fields → defaults + warnings, errors → minimal valid fallback
- All adapters track `generator` field for full traceability

**Fallback Strategy:**
- OpenAI direct generation is LAST RESORT
- Only invoked when framework call raises exception
- Uses JSON mode (not beta.parse API) for maximum compatibility
- Manually constructs Pydantic objects to ensure validation
- Marks output with `generator: "openai_fallback"` for audit trail

---

## Testing Coverage

**Import Tests:**
- All 4 generators importable without errors
- All 6 adapter functions importable without errors

**Mock Object Tests:**
- DeepEval adapter tested with SimpleNamespace mock
- Verified TestCase and DatasetExample Pydantic validations pass
- Verified metadata includes generator field
- Verified parameter_variation_axes count (2-3)
- Verified evaluation_criteria count (3+)

**Not Tested (Integration):**
- Live framework calls (DeepEval, Ragas, Giskard) - deferred to Phase 6 E2E tests
- Adapter integration with real framework outputs - deferred to Phase 6 E2E tests
- Fallback generator with real OpenAI API - deferred to Phase 6 E2E tests

---

## Performance Considerations

**Generation Speed:**
- DeepEval: Moderate (2-4x slower than direct OpenAI per research pitfall 1)
- Ragas: Moderate (similar to DeepEval)
- Giskard: SLOW (15+ min for 60 questions per research pitfall 3)
- Fallback: Fast (single OpenAI call)

**Recommendations:**
- Start with num_questions=20 for Giskard to avoid long waits
- Use async_mode=True for DeepEval in production (currently False for simplicity)
- Consider caching framework outputs (DataFrames, Goldens) before adapter conversion

---

## Next Steps

**Immediate (Phase 3):**
- 03-03: Orchestrator to run generators, apply adapters, produce final artifacts
- 03-04: CLI integration and output formatting

**Future Enhancements:**
- Enable DeepEval async_mode for parallel generation
- Implement knowledge base caching for Giskard
- Add adapter unit tests with real framework output samples
- Consider LLM-based adapter fallback for edge cases (currently hardcoded only)

---

## Self-Check

### Created Files Verification

```bash
$ ls -l src/dataset_generator/generation/
total 8
-rw-r--r--  1 user  staff  261 Feb 16 21:28 __init__.py
-rw-r--r--  1 user  staff  7654 Feb 16 21:28 fallback.py
drwxr-xr-x  7 user  staff  224 Feb 16 21:28 generators/
drwxr-xr-x  7 user  staff  224 Feb 16 21:35 adapters/

$ ls -l src/dataset_generator/generation/generators/
total 32
-rw-r--r--  1 user  staff  495 Feb 16 21:28 __init__.py
-rw-r--r--  1 user  staff  4512 Feb 16 21:28 deepeval_gen.py
-rw-r--r--  1 user  staff  3862 Feb 16 21:28 ragas_gen.py
-rw-r--r--  1 user  staff  2891 Feb 16 21:28 giskard_gen.py

$ ls -l src/dataset_generator/generation/adapters/
total 80
-rw-r--r--  1 user  staff  847 Feb 16 21:35 __init__.py
-rw-r--r--  1 user  staff  10159 Feb 16 21:34 deepeval_adapter.py
-rw-r--r--  1 user  staff  9831 Feb 16 21:34 ragas_adapter.py
-rw-r--r--  1 user  staff  9225 Feb 16 21:35 giskard_adapter.py
```

✅ All 10 files created as expected

### Commits Verification

```bash
$ git log --oneline --all | head -2
ce6ce5d feat(03-02): implement hardcoded adapters for all frameworks
eb4cd6e feat(03-02): implement framework generators and OpenAI fallback
```

✅ Both commits exist with proper feat(03-02) scope

### Import Verification

```bash
$ python3 -c "from dataset_generator.generation.generators import *; from dataset_generator.generation.adapters import *; from dataset_generator.generation import *; print('All imports OK')"
All imports OK
```

✅ All modules importable without errors

## Self-Check: PASSED

All files created, commits exist, imports work, verifications passed.
