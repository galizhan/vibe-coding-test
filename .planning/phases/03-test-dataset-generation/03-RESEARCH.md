# Phase 3: Test & Dataset Generation - Research

**Researched:** 2026-02-16
**Domain:** LLM evaluation frameworks, synthetic data generation, function calling orchestration
**Confidence:** MEDIUM-HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Framework selection:**
- DeepEval Synthesizer is the primary generation engine for both test cases and dataset examples
- All three frameworks (DeepEval, Ragas, Giskard Hub) are used in this phase, not deferred to Phase 8
- DeepEval handles generation; Claude decides the specific roles for Ragas and Giskard based on research into their capabilities

**Orchestration pattern:**
- OpenAI function calling routes between frameworks (not a fixed pipeline)
- OpenAI acts as orchestrator deciding which framework to call based on the task
- Hardcoded Python adapters convert between framework output formats and Pydantic data contracts (not LLM-driven conversion)
- If a framework call fails or returns low-quality output, fall back to direct OpenAI generation to ensure pipeline always completes
- Each generated item records which framework produced it in metadata (e.g., `generator: deepeval`) for traceability/debugging

### Claude's Discretion

- Specific roles for Ragas and Giskard Hub (evaluate, test, generate — research and assign)
- Output format mapping details (adapter implementation)
- Coverage enforcement strategy (ensuring minimums: 3 test cases/UC, 3+ eval criteria)
- OpenAI function definitions and routing logic

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

</user_constraints>

## Summary

Phase 3 implements a multi-framework test and dataset generation pipeline using DeepEval Synthesizer as the primary engine, with OpenAI function calling as the orchestrator and Ragas/Giskard providing complementary capabilities. The architecture uses hardcoded Pydantic adapters to convert between framework outputs and project schemas, with fallback to direct OpenAI generation for resilience.

Based on research into capabilities, the recommended framework roles are:
- **DeepEval Synthesizer**: Primary generation engine for test cases and dataset examples from documents/contexts
- **Ragas**: Complementary test data generation with quality evaluation using RAG-specific metrics
- **Giskard RAGET**: Knowledge base integration and business test generation with component-level evaluation

All three frameworks are mature (2025-2026 releases), pytest-compatible, and support OpenAI models. The main integration challenges are output format mapping (each framework has different schemas) and quality control (deduplication, coverage enforcement).

**Primary recommendation:** Use DeepEval Synthesizer for bulk generation with evolution techniques, Ragas TestsetGenerator for RAG-specific question types, and Giskard RAGET for knowledge base validation. Implement adapters as standalone functions that map framework outputs to project Pydantic contracts.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| deepeval | 3.8.4 | Primary test/dataset generation engine | Pytest-compatible, 50+ metrics, evolution techniques for synthetic data |
| ragas | 0.4.3 | RAG evaluation and test generation | RAG-specific question types, knowledge graph transformations |
| giskard | 2.19.0 | Knowledge base testing and RAGET | Component-level RAG evaluation, business test generation |
| openai | 2.21.0 | LLM provider and orchestrator | Function calling for routing, structured outputs |
| pydantic | 2.12.5 | Data validation and contracts | BaseModel validation, v2 syntax (5-50x faster than v1) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| langchain | latest | Document loading | When integrating with Ragas/Giskard document loaders |
| tiktoken | latest | Token counting | For Giskard knowledge base processing |
| pandas | latest | Dataset export/analysis | Converting to DataFrames for analysis |
| pytest | latest | Test framework integration | Running DeepEval evaluations in CI/CD |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Multi-framework | Single framework (DeepEval only) | Lose RAG-specific question types and component evaluation |
| OpenAI orchestration | Hardcoded pipeline | Lose routing flexibility, can't adapt to task complexity |
| Hardcoded adapters | LLM-driven conversion | Unpredictable outputs, higher cost, slower |

**Installation:**
```bash
pip install deepeval==3.8.4 ragas==0.4.3 "giskard[llm]==2.19.0" openai==2.21.0 pydantic==2.12.5
```

**Python Requirements:** Python >=3.9, <4.0 (all frameworks support 3.9-3.11)

## Architecture Patterns

### Recommended Project Structure
```
src/
├── generation/
│   ├── orchestrator.py      # OpenAI function calling router
│   ├── adapters/
│   │   ├── deepeval_adapter.py
│   │   ├── ragas_adapter.py
│   │   └── giskard_adapter.py
│   ├── generators/
│   │   ├── deepeval_gen.py
│   │   ├── ragas_gen.py
│   │   └── giskard_gen.py
│   └── fallback.py          # Direct OpenAI generation fallback
├── schemas/
│   ├── test_case.py         # Pydantic TestCase model
│   ├── dataset_example.py   # Pydantic DatasetExample model
│   └── run_manifest.py      # Pydantic RunManifest model
└── utils/
    ├── coverage_tracker.py  # Enforce 3 test cases/UC, 3+ criteria
    └── quality_control.py   # Deduplication, validation
```

### Pattern 1: OpenAI Function Calling Orchestrator

**What:** OpenAI decides which framework to call based on task context using function calling
**When to use:** When task complexity varies (simple vs multi-context questions, document-based vs scratch generation)

**Example:**
```python
# Source: https://platform.openai.com/docs/guides/function-calling
from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()

# Define tools for each framework
tools = [
    {
        "type": "function",
        "function": {
            "name": "generate_with_deepeval",
            "description": "Generate test cases and dataset examples from documents using evolution techniques. Use when: generating from documents, need complexity evolution, bulk generation required.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_paths": {"type": "array", "items": {"type": "string"}},
                    "num_goldens": {"type": "integer"},
                    "include_expected_output": {"type": "boolean"}
                },
                "required": ["document_paths"]
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_with_ragas",
            "description": "Generate RAG-specific test questions with knowledge graph transformations. Use when: need multi-context questions, reasoning questions, RAG pipeline evaluation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "documents": {"type": "array"},
                    "test_size": {"type": "integer"},
                    "question_types": {"type": "object"}
                },
                "required": ["documents", "test_size"]
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_with_giskard",
            "description": "Generate business tests from knowledge base with component evaluation. Use when: need knowledge base validation, component-level testing, business test scenarios.",
            "parameters": {
                "type": "object",
                "properties": {
                    "knowledge_base": {"type": "object"},
                    "num_questions": {"type": "integer"},
                    "agent_description": {"type": "string"}
                },
                "required": ["knowledge_base"]
            },
            "strict": True
        }
    }
]

# Orchestration loop
messages = [
    {"role": "system", "content": "You are a test generation orchestrator. Select the appropriate framework based on the task requirements."},
    {"role": "user", "content": "Generate test cases for use case X with policies from documents Y."}
]

response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
    tool_choice="auto"  # Let model decide
)

# Handle tool calls
for tool_call in response.choices[0].message.tool_calls or []:
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)

    # Route to appropriate generator
    if function_name == "generate_with_deepeval":
        result = deepeval_generator.generate(**arguments)
    elif function_name == "generate_with_ragas":
        result = ragas_generator.generate(**arguments)
    elif function_name == "generate_with_giskard":
        result = giskard_generator.generate(**arguments)
```

### Pattern 2: DeepEval Synthesizer with Evolution

**What:** Generate synthetic goldens from documents using evolution techniques for complexity
**When to use:** Primary generation engine for test cases and dataset examples

**Example:**
```python
# Source: https://deepeval.com/docs/synthesizer-introduction
from deepeval.synthesizer import Synthesizer, Evolution
from deepeval.synthesizer.config import EvolutionConfig, FiltrationConfig, StylingConfig

# Configure evolution for complexity
evolution_config = EvolutionConfig(
    evolutions={
        Evolution.REASONING: 0.25,
        Evolution.MULTICONTEXT: 0.25,
        Evolution.CONCRETIZING: 0.25,
        Evolution.CONSTRAINED: 0.25
    },
    num_evolutions=2  # Balance quality vs speed
)

# Configure filtration for quality
filtration_config = FiltrationConfig(
    critic_model="gpt-4o",
    synthetic_input_quality_threshold=0.7,  # Higher threshold for quality
    max_quality_retries=3
)

# Configure styling for use case format
styling_config = StylingConfig(
    input_format="Customer support messages with specific policy questions",
    expected_output_format="Support response with policy_id references",
    task="Customer support query handling",
    scenario="User asks about policies, system responds with correct information"
)

synthesizer = Synthesizer(
    model="gpt-4o-mini",  # Use project default
    async_mode=True,
    max_concurrent=10,
    evolution_config=evolution_config,
    filtration_config=filtration_config,
    styling_config=styling_config
)

# Generate goldens from documents
goldens = synthesizer.generate_goldens_from_docs(
    document_paths=['policies/policy_doc.txt'],
    include_expected_output=True
)

# Export to DataFrame for adapter processing
df = synthesizer.to_pandas()
```

### Pattern 3: Ragas TestsetGenerator for RAG

**What:** Generate RAG-specific test questions using knowledge graph transformations
**When to use:** Complementary generation for RAG evaluation metrics

**Example:**
```python
# Source: https://docs.ragas.io/en/stable/getstarted/rag_testset_generation/
from ragas.testset.generator import TestsetGenerator
from ragas.testset.evolutions import simple, reasoning, multi_context

# Initialize with OpenAI
generator = TestsetGenerator.with_openai()

# Define question type distribution
distributions = {
    simple: 0.4,              # Direct questions
    reasoning: 0.3,            # Multi-hop reasoning
    multi_context: 0.3         # Require multiple contexts
}

# Generate testset from documents
testset = generator.generate_with_langchain_docs(
    documents=langchain_docs,
    test_size=10,
    distributions=distributions
)

# Export to DataFrame for adapter processing
df = testset.to_pandas()
# Columns: question, ground_truth, contexts, evolution_type, metadata
```

### Pattern 4: Giskard RAGET for Knowledge Base

**What:** Generate business tests from knowledge base with component-level evaluation
**When to use:** Validate knowledge base and generate business test scenarios

**Example:**
```python
# Source: https://docs.giskard.ai/oss/sdk/business.html
from giskard.rag import KnowledgeBase, generate_testset

# Initialize knowledge base from documents
kb = KnowledgeBase.from_pandas(
    df=policies_df,
    columns=["policy_id", "content"]
)

# Generate testset with RAGET
testset = generate_testset(
    kb,
    num_questions=30,
    language='en',
    agent_description="Customer support agent with access to policy database"
)

# Export to DataFrame for adapter processing
df = testset.to_pandas()
# Columns: question, reference_context, reference_answer, conversation_history, metadata
```

### Pattern 5: Hardcoded Pydantic Adapters

**What:** Convert framework outputs to project Pydantic data contracts
**When to use:** After every framework generation call (mandatory for consistency)

**Example:**
```python
# Source: Pydantic v2 patterns
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal

# Project data contracts
class DatasetExample(BaseModel):
    id: str
    case: Literal["single", "multi"]
    format: str
    use_case_id: str
    test_case_id: str
    input_messages: List[dict]
    expected_output: str
    evaluation_criteria: List[str]
    policy_ids: List[str]
    metadata: dict = Field(default_factory=dict)

    @field_validator('evaluation_criteria')
    @classmethod
    def validate_criteria_count(cls, v):
        if len(v) < 3:
            raise ValueError("Minimum 3 evaluation criteria required")
        return v

# DeepEval adapter
def adapt_deepeval_golden(golden, use_case_id: str, test_case_id: str) -> DatasetExample:
    """Convert DeepEval Golden to project DatasetExample schema."""
    return DatasetExample(
        id=f"ex_{uuid4()}",
        case="single",  # DeepEval default
        format="conversational",
        use_case_id=use_case_id,
        test_case_id=test_case_id,
        input_messages=[{"role": "user", "content": golden.input}],
        expected_output=golden.expected_output or "",
        evaluation_criteria=extract_criteria_from_context(golden.context),
        policy_ids=extract_policy_ids(golden.context),
        metadata={
            "generator": "deepeval",
            "evolution_type": golden.additional_metadata.get("evolution_type"),
            "quality_score": golden.additional_metadata.get("quality_score")
        }
    )

# Ragas adapter
def adapt_ragas_testset(row, use_case_id: str, test_case_id: str) -> DatasetExample:
    """Convert Ragas testset row to project DatasetExample schema."""
    return DatasetExample(
        id=f"ex_{uuid4()}",
        case="multi" if row.evolution_type == "multi_context" else "single",
        format="conversational",
        use_case_id=use_case_id,
        test_case_id=test_case_id,
        input_messages=[{"role": "user", "content": row.question}],
        expected_output=row.ground_truth,
        evaluation_criteria=generate_criteria_from_evolution(row.evolution_type),
        policy_ids=extract_policy_ids_from_contexts(row.contexts),
        metadata={
            "generator": "ragas",
            "evolution_type": row.evolution_type,
            "contexts_used": len(row.contexts)
        }
    )

# Giskard adapter
def adapt_giskard_testset(row, use_case_id: str, test_case_id: str) -> DatasetExample:
    """Convert Giskard RAGET row to project DatasetExample schema."""
    return DatasetExample(
        id=f"ex_{uuid4()}",
        case="single",
        format="conversational",
        use_case_id=use_case_id,
        test_case_id=test_case_id,
        input_messages=[{"role": "user", "content": row.question}],
        expected_output=row.reference_answer,
        evaluation_criteria=generate_criteria_from_question_type(row.metadata.get("question_type")),
        policy_ids=extract_policy_ids_from_context(row.reference_context),
        metadata={
            "generator": "giskard",
            "question_type": row.metadata.get("question_type"),
            "reference_context": row.reference_context
        }
    )
```

### Pattern 6: Fallback to Direct OpenAI Generation

**What:** Use direct OpenAI generation if framework call fails or returns low quality
**When to use:** Circuit breaker pattern when framework errors or quality threshold not met

**Example:**
```python
# Source: OpenAI structured outputs pattern
from openai import OpenAI

def generate_with_fallback(task: dict) -> List[DatasetExample]:
    """Try framework generation, fall back to OpenAI if needed."""
    try:
        # Try primary framework
        result = orchestrator.route_and_generate(task)

        # Quality check
        if quality_score(result) < 0.7:
            raise ValueError("Quality threshold not met")

        return result

    except Exception as e:
        logger.warning(f"Framework generation failed: {e}. Falling back to OpenAI.")

        # Direct OpenAI generation with structured output
        completion = client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Generate dataset examples with evaluation criteria."},
                {"role": "user", "content": json.dumps(task)}
            ],
            response_format=DatasetExample
        )

        return [completion.choices[0].message.parsed]
```

### Pattern 7: Coverage Enforcement

**What:** Ensure minimum coverage requirements (3 test cases per use case, 3+ evaluation criteria)
**When to use:** After generation, before persisting to dataset

**Example:**
```python
def enforce_coverage(use_case_id: str, test_cases: List[TestCase], examples: List[DatasetExample]):
    """Enforce minimum coverage requirements."""

    # Check test case minimum
    if len(test_cases) < 3:
        raise ValueError(f"Use case {use_case_id} has {len(test_cases)} test cases, minimum 3 required")

    # Check parameter variation axes
    for tc in test_cases:
        axes = tc.parameter_variation_axes
        if len(axes) < 2 or len(axes) > 3:
            raise ValueError(f"Test case {tc.id} has {len(axes)} variation axes, expected 2-3")

    # Check evaluation criteria
    for ex in examples:
        if len(ex.evaluation_criteria) < 3:
            raise ValueError(f"Example {ex.id} has {len(ex.evaluation_criteria)} criteria, minimum 3 required")

    # Check dataset example per test case
    for tc in test_cases:
        tc_examples = [ex for ex in examples if ex.test_case_id == tc.id]
        if len(tc_examples) == 0:
            raise ValueError(f"Test case {tc.id} has no dataset examples")
```

### Anti-Patterns to Avoid

- **LLM-driven adapters:** Using LLM to convert between formats is unpredictable and expensive. Use hardcoded functions.
- **Single framework:** Don't rely only on DeepEval. Each framework has strengths (DeepEval: bulk generation, Ragas: RAG metrics, Giskard: component testing).
- **No fallback:** Framework APIs can fail. Always implement fallback to direct OpenAI generation.
- **Ignoring quality scores:** DeepEval and other frameworks provide quality metrics. Use them to filter low-quality outputs.
- **Missing metadata:** Always record `generator` field in metadata for debugging and traceability.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Synthetic test data generation | Custom question/answer generator with templates | DeepEval Synthesizer with evolution techniques | Evolution techniques (reasoning, multi-context, constrained) handle complexity; filtration ensures quality; custom solutions miss edge cases |
| RAG-specific question types | Manual question categorization | Ragas TestsetGenerator with distributions | Knowledge graph transformations ensure diversity; handles simple, reasoning, multi-context automatically |
| Knowledge base validation | Custom document parser + Q&A generator | Giskard RAGET | Automatically extracts questions from KB; handles 6+ question types; component-level evaluation built-in |
| LLM function calling orchestration | If-else routing logic | OpenAI function calling with tool definitions | Model intelligently routes based on context; adapts to task complexity; extensible with new tools |
| Dataset deduplication | String matching or embeddings | Framework-built quality filters + post-processing | DeepEval has filtration_config; Ragas has quality metrics; frameworks handle near-duplicates |
| Schema validation | Manual dict checking | Pydantic v2 BaseModel | 5-50x faster than v1; field validators; automatic type coercion; JSON schema generation |

**Key insight:** LLM evaluation frameworks have spent years handling edge cases in synthetic data generation. Custom solutions typically miss: quality scoring, deduplication, evolution techniques, distribution balancing, referential integrity, and framework-specific optimizations. The complexity of generating realistic, diverse test data is vastly underestimated.

## Common Pitfalls

### Pitfall 1: DeepEval Generates Duplicate Data

**What goes wrong:** DeepEval's `generate_goldens_from_docs()` can generate duplicate or near-duplicate goldens, especially with default configuration.

**Why it happens:** Evolution techniques can converge on similar questions; filtration threshold too low; same context extracted multiple times from documents.

**How to avoid:**
- Set higher `synthetic_input_quality_threshold` (0.7+ instead of default 0.5)
- Implement post-generation deduplication using embeddings
- Use `num_evolutions=1-2` to reduce convergence
- Check `synthesizer.synthetic_goldens` for duplicates before export

**Warning signs:** Generated dataset has many similar questions; quality scores cluster around threshold.

**Code pattern:**
```python
# Source: https://github.com/confident-ai/deepeval/issues/1925
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI

def deduplicate_goldens(goldens: List[Golden], threshold: float = 0.9) -> List[Golden]:
    """Remove near-duplicate goldens using embedding similarity."""
    client = OpenAI()

    # Get embeddings
    texts = [g.input for g in goldens]
    embeddings = client.embeddings.create(input=texts, model="text-embedding-3-small").data
    vectors = [e.embedding for e in embeddings]

    # Compute similarity matrix
    sim_matrix = cosine_similarity(vectors)

    # Keep only unique
    keep = []
    seen = set()
    for i, golden in enumerate(goldens):
        if i in seen:
            continue
        keep.append(golden)
        # Mark similar items as seen
        for j in range(i+1, len(goldens)):
            if sim_matrix[i][j] > threshold:
                seen.add(j)

    return keep
```

### Pitfall 2: Ragas Generates Questions for Short/Poor Contexts

**What goes wrong:** Ragas generates simple questions even for long contexts, or generates questions for short, unattractive contexts that don't provide enough information.

**Why it happens:** Document quality issues; chunks don't contain sufficient information; transformations can't extract meaningful relationships; question complexity depends on context richness.

**How to avoid:**
- Preprocess documents to ensure high-quality chunks with sufficient information
- Filter chunks by length and information density before generation
- Use `distributions` parameter to control question complexity
- Validate generated questions against minimum quality criteria

**Warning signs:** Generated questions are too generic; questions don't match context complexity; frequent NaN values for ground_truth.

**Code pattern:**
```python
# Source: https://pixion.co/blog/ragas-test-set-generation-breakdown
def preprocess_documents(documents: List[Document]) -> List[Document]:
    """Filter and enrich documents for quality testset generation."""
    filtered = []

    for doc in documents:
        # Filter by length
        if len(doc.page_content) < 100:
            continue

        # Check information density (simple heuristic)
        words = doc.page_content.split()
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.3:  # Too repetitive
            continue

        # Add topic metadata to guide generation
        doc.metadata["topic"] = extract_topic(doc.page_content)
        filtered.append(doc)

    return filtered

# Use filtered documents
testset = generator.generate_with_langchain_docs(
    documents=preprocess_documents(raw_docs),
    test_size=10,
    distributions={reasoning: 0.5, multi_context: 0.5}  # Force complexity
)
```

### Pitfall 3: Giskard RAGET Takes Very Long

**What goes wrong:** RAGET test generation and evaluation can take 15+ minutes for moderate datasets (60 questions).

**Why it happens:** LLM calls for each question; embedding generation for knowledge base; neighbor search for contexts; no batching optimization.

**How to avoid:**
- Start with smaller `num_questions` (10-20) for testing
- Use faster embedding models (text-embedding-3-small)
- Run generation asynchronously if possible
- Cache knowledge base embeddings between runs
- Monitor API rate limits

**Warning signs:** Generation hangs; API rate limit errors; high token consumption.

**Code pattern:**
```python
# Source: https://www.cohorte.co/blog/rag-testing-and-diagnosis-platform-using-giskard
from giskard.rag import KnowledgeBase, generate_testset
import pickle
from pathlib import Path

def generate_with_cache(policies_df, cache_path: str = ".cache/kb.pkl"):
    """Generate testset with knowledge base caching."""
    cache_file = Path(cache_path)

    # Load cached KB if exists
    if cache_file.exists():
        with open(cache_file, 'rb') as f:
            kb = pickle.load(f)
    else:
        kb = KnowledgeBase.from_pandas(policies_df, columns=["content"])
        cache_file.parent.mkdir(exist_ok=True)
        with open(cache_file, 'wb') as f:
            pickle.dump(kb, f)

    # Generate with reasonable limits
    testset = generate_testset(
        kb,
        num_questions=20,  # Start small
        language='en'
    )

    return testset
```

### Pitfall 4: OpenAI Function Calling Returns Wrong Tool

**What goes wrong:** Model selects inappropriate framework for the task, or calls tool with invalid arguments.

**Why it happens:** Tool descriptions not clear enough; arguments schema too permissive; model hallucination; lack of constraints.

**How to avoid:**
- Write specific, action-oriented tool descriptions with "Use when:" clauses
- Use `"strict": true` for structured outputs (enforces schema)
- Validate tool arguments before calling framework
- Implement retry logic with corrected context
- Provide examples in system prompt

**Warning signs:** Wrong framework called repeatedly; framework errors due to invalid arguments; routing doesn't match task context.

**Code pattern:**
```python
# Source: https://medium.com/@laurentkubaski/openai-tool-calling-using-the-python-sdk-full-example-with-best-practices-29af7c651f08
def validate_and_route(tool_call) -> dict:
    """Validate tool call and route to framework with error handling."""
    function_name = tool_call.function.name

    try:
        arguments = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in tool call: {e}")
        return {"error": "Invalid arguments format"}

    # Validate arguments match tool schema
    if function_name == "generate_with_deepeval":
        if "document_paths" not in arguments:
            return {"error": "Missing required field: document_paths"}
        if not isinstance(arguments["document_paths"], list):
            return {"error": "document_paths must be a list"}

    # Call framework with error handling
    try:
        result = call_framework(function_name, arguments)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Framework call failed: {e}")
        # Trigger fallback
        return {"error": str(e), "fallback_needed": True}
```

### Pitfall 5: Adapter Loses Critical Fields

**What goes wrong:** Converting from framework output to Pydantic model loses important fields like context, metadata, or quality scores.

**Why it happens:** Framework schemas don't map 1:1 to project schemas; assumptions about field presence; missing null checks.

**How to avoid:**
- Document framework output schemas explicitly
- Use Pydantic `Field(default=...)` for optional fields
- Preserve all metadata in `metadata` dict
- Write adapter unit tests with real framework outputs
- Log warnings when expected fields are missing

**Warning signs:** Dataset examples missing evaluation criteria; policy_ids empty when they should exist; metadata incomplete.

**Code pattern:**
```python
# Source: Pydantic v2 validation patterns
from pydantic import BaseModel, Field, field_validator
import logging

class DatasetExample(BaseModel):
    # ... other fields ...
    evaluation_criteria: List[str] = Field(min_length=3)
    policy_ids: List[str] = Field(min_length=1)
    metadata: dict = Field(default_factory=dict)

    @field_validator('policy_ids', mode='before')
    @classmethod
    def extract_policy_ids(cls, v, info):
        """Extract policy IDs from various sources."""
        if not v or len(v) == 0:
            # Try to extract from context or metadata
            context = info.data.get('metadata', {}).get('context', '')
            extracted = re.findall(r'policy_(\d+)', context)
            if extracted:
                return [f"policy_{id}" for id in extracted]
            logging.warning("No policy_ids found, using default")
            return ["policy_unknown"]
        return v

def safe_adapt_deepeval(golden, use_case_id: str, test_case_id: str) -> Optional[DatasetExample]:
    """Adapter with comprehensive null checking and logging."""
    try:
        # Extract with defaults
        input_content = golden.input if hasattr(golden, 'input') else ""
        expected_output = golden.expected_output if hasattr(golden, 'expected_output') else ""
        context = golden.context if hasattr(golden, 'context') else []

        # Warn if critical fields missing
        if not input_content:
            logging.warning(f"Golden has no input content: {golden}")
            return None

        # Build with full metadata preservation
        return DatasetExample(
            id=f"ex_{uuid4()}",
            case="single",
            format="conversational",
            use_case_id=use_case_id,
            test_case_id=test_case_id,
            input_messages=[{"role": "user", "content": input_content}],
            expected_output=expected_output,
            evaluation_criteria=extract_criteria_from_context(context) or generate_default_criteria(),
            policy_ids=extract_policy_ids(context),
            metadata={
                "generator": "deepeval",
                "raw_context": context,
                "evolution_type": getattr(golden, 'additional_metadata', {}).get('evolution_type'),
                "quality_score": getattr(golden, 'additional_metadata', {}).get('quality_score'),
                # Preserve everything for debugging
                "raw_golden": str(golden)
            }
        )
    except Exception as e:
        logging.error(f"Adapter failed for golden {golden}: {e}")
        return None
```

### Pitfall 6: Missing Coverage Enforcement

**What goes wrong:** Generated dataset doesn't meet minimum requirements (3 test cases per use case, 3+ evaluation criteria).

**Why it happens:** Framework generates variable amounts; no validation before persistence; coverage checks happen too late.

**How to avoid:**
- Enforce coverage after generation, before writing to disk
- Generate extra items to account for filtering (generate 5, keep best 3)
- Track coverage metrics in real-time during generation
- Fail loudly if minimums not met (don't silently accept incomplete datasets)

**Warning signs:** Some use cases have <3 test cases; evaluation criteria too generic or too few; test cases without examples.

**Code pattern:**
```python
def generate_with_coverage(use_case_id: str, policies: List[str], min_test_cases: int = 3):
    """Generate with coverage enforcement."""
    test_cases = []
    examples = []

    # Generate extra to account for filtering
    target = min_test_cases * 2

    while len(test_cases) < min_test_cases:
        batch_test_cases, batch_examples = orchestrator.generate_batch(
            use_case_id=use_case_id,
            policies=policies,
            count=target - len(test_cases)
        )

        # Filter quality
        filtered_tcs = [tc for tc in batch_test_cases if tc.quality_score > 0.7]
        filtered_exs = [ex for ex in batch_examples if len(ex.evaluation_criteria) >= 3]

        test_cases.extend(filtered_tcs)
        examples.extend(filtered_exs)

        if len(test_cases) < min_test_cases:
            logging.warning(f"Generated {len(test_cases)}/{min_test_cases} test cases, retrying...")

    # Final validation
    enforce_coverage(use_case_id, test_cases[:min_test_cases], examples)

    return test_cases[:min_test_cases], examples
```

## Code Examples

Verified patterns from official sources:

### Complete Generation Pipeline with Orchestration

```python
# Source: OpenAI Cookbook + DeepEval + Ragas + Giskard docs
from openai import OpenAI
from deepeval.synthesizer import Synthesizer, Evolution
from ragas.testset.generator import TestsetGenerator
from giskard.rag import KnowledgeBase, generate_testset
from pydantic import BaseModel
from typing import List, Literal
import json

# Initialize clients
openai_client = OpenAI()

# Initialize generators
deepeval_synth = Synthesizer(model="gpt-4o-mini", async_mode=True)
ragas_gen = TestsetGenerator.with_openai()
giskard_kb = KnowledgeBase.from_pandas(policies_df, columns=["content"])

# Define Pydantic contracts
class TestCase(BaseModel):
    id: str
    use_case_id: str
    description: str
    parameter_variation_axes: List[str]
    metadata: dict

class DatasetExample(BaseModel):
    id: str
    test_case_id: str
    input_messages: List[dict]
    expected_output: str
    evaluation_criteria: List[str]
    policy_ids: List[str]
    metadata: dict

# OpenAI function calling orchestrator
def orchestrate_generation(use_case_id: str, policies: List[str]) -> tuple[List[TestCase], List[DatasetExample]]:
    """Orchestrate multi-framework generation with OpenAI function calling."""

    # Define tools
    tools = [
        {
            "type": "function",
            "function": {
                "name": "generate_with_deepeval",
                "description": "Generate test cases from documents using evolution. Use when: bulk generation needed, have policy documents.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "document_paths": {"type": "array", "items": {"type": "string"}},
                        "num_goldens": {"type": "integer", "default": 10}
                    },
                    "required": ["document_paths"]
                },
                "strict": True
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generate_with_ragas",
                "description": "Generate RAG questions with reasoning. Use when: need multi-context questions, reasoning scenarios.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "test_size": {"type": "integer", "default": 10},
                        "reasoning_ratio": {"type": "number", "default": 0.5}
                    }
                },
                "strict": True
            }
        }
    ]

    # Orchestration messages
    messages = [
        {
            "role": "system",
            "content": "You are a test generation orchestrator. Select appropriate frameworks based on task requirements."
        },
        {
            "role": "user",
            "content": f"Generate test cases for use_case {use_case_id} with {len(policies)} policy documents. Need both document-based and reasoning questions."
        }
    ]

    # Call OpenAI with tools
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        temperature=0
    )

    test_cases = []
    examples = []

    # Process tool calls
    for tool_call in response.choices[0].message.tool_calls or []:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        try:
            if function_name == "generate_with_deepeval":
                # Generate with DeepEval
                goldens = deepeval_synth.generate_goldens_from_docs(
                    document_paths=arguments["document_paths"],
                    include_expected_output=True
                )
                # Adapt to project schema
                for golden in goldens:
                    tc, ex = adapt_deepeval_golden(golden, use_case_id)
                    test_cases.append(tc)
                    examples.append(ex)

            elif function_name == "generate_with_ragas":
                # Generate with Ragas
                testset = ragas_gen.generate_with_langchain_docs(
                    documents=langchain_docs,
                    test_size=arguments["test_size"],
                    distributions={
                        reasoning: arguments.get("reasoning_ratio", 0.5),
                        simple: 1 - arguments.get("reasoning_ratio", 0.5)
                    }
                )
                # Adapt to project schema
                for row in testset.to_pandas().itertuples():
                    tc, ex = adapt_ragas_testset(row, use_case_id)
                    test_cases.append(tc)
                    examples.append(ex)

        except Exception as e:
            # Fallback to direct OpenAI generation
            logging.warning(f"Framework {function_name} failed: {e}. Using fallback.")
            fallback_tcs, fallback_exs = generate_with_openai_fallback(use_case_id, policies)
            test_cases.extend(fallback_tcs)
            examples.extend(fallback_exs)

    # Enforce coverage
    enforce_coverage(use_case_id, test_cases, examples)

    return test_cases, examples

# Run generation
test_cases, examples = orchestrate_generation("uc_001", ["policy_1.txt", "policy_2.txt"])

# Write run manifest
manifest = {
    "input_path": "policies/",
    "out_path": "datasets/run_001/",
    "seed": 42,
    "timestamp": datetime.now().isoformat(),
    "generator_version": "1.0.0",
    "llm": {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "temperature": 0
    },
    "frameworks_used": ["deepeval", "ragas"],
    "test_cases_generated": len(test_cases),
    "examples_generated": len(examples)
}

with open("datasets/run_001/run_manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)
```

### DeepEval Evolution Configuration

```python
# Source: https://deepeval.com/docs/synthesizer-introduction
from deepeval.synthesizer import Synthesizer, Evolution
from deepeval.synthesizer.config import EvolutionConfig, FiltrationConfig, StylingConfig

# Configure for customer support use case
evolution_config = EvolutionConfig(
    evolutions={
        Evolution.REASONING: 0.3,        # "Why does policy X apply?"
        Evolution.MULTICONTEXT: 0.2,     # Combine multiple policy sections
        Evolution.CONCRETIZING: 0.3,     # Specific scenarios
        Evolution.CONSTRAINED: 0.2       # With limitations/edge cases
    },
    num_evolutions=2
)

filtration_config = FiltrationConfig(
    critic_model="gpt-4o",
    synthetic_input_quality_threshold=0.75,  # High quality
    max_quality_retries=3
)

styling_config = StylingConfig(
    input_format="Customer support message asking about specific policy",
    expected_output_format="Support response with policy_id reference and explanation",
    task="Customer support query resolution",
    scenario="Customer needs help understanding policies"
)

synthesizer = Synthesizer(
    model="gpt-4o-mini",
    async_mode=True,
    max_concurrent=10,
    evolution_config=evolution_config,
    filtration_config=filtration_config,
    styling_config=styling_config,
    cost_tracking=True  # Monitor costs
)

goldens = synthesizer.generate_goldens_from_docs(
    document_paths=['policies/all_policies.txt'],
    include_expected_output=True
)

print(f"Generated {len(goldens)} goldens")
synthesizer.save_as(file_type='json', directory='./datasets', file_name='deepeval_goldens')
```

### Ragas Multi-Context Questions

```python
# Source: https://docs.ragas.io/en/stable/getstarted/rag_testset_generation/
from ragas.testset.generator import TestsetGenerator
from ragas.testset.evolutions import simple, reasoning, multi_context
from langchain.document_loaders import TextLoader

# Load documents
docs = TextLoader('policies/all_policies.txt').load()

# Initialize generator
generator = TestsetGenerator.with_openai()

# Generate with emphasis on complex questions
testset = generator.generate_with_langchain_docs(
    documents=docs,
    test_size=30,
    distributions={
        simple: 0.2,           # 6 simple questions
        reasoning: 0.4,        # 12 reasoning questions
        multi_context: 0.4     # 12 multi-context questions
    }
)

# Export and analyze
df = testset.to_pandas()
print(df[['question', 'evolution_type', 'ground_truth']].head())
```

### Giskard Knowledge Base Testing

```python
# Source: https://docs.giskard.ai/oss/sdk/business.html
from giskard.rag import KnowledgeBase, generate_testset, evaluate

# Create knowledge base from policies
policies_df = pd.DataFrame({
    'policy_id': ['P001', 'P002', 'P003'],
    'content': ['Policy 1 content...', 'Policy 2 content...', 'Policy 3 content...']
})

kb = KnowledgeBase.from_pandas(
    policies_df,
    columns=['policy_id', 'content']
)

# Generate testset with RAGET
testset = generate_testset(
    kb,
    num_questions=30,
    language='en',
    agent_description="Customer support agent with policy knowledge base access"
)

# Export for adapter
df = testset.to_pandas()
print(df[['question', 'reference_answer', 'metadata']].head())

# Optionally evaluate a RAG model
def my_rag_agent(question: str) -> str:
    # Your RAG implementation
    pass

report = evaluate(
    my_rag_agent,
    testset=testset,
    knowledge_base=kb
)
print(report)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual test case writing | Automated synthesis with evolution | 2024-2025 | DeepEval/Ragas enable 90% time reduction in test data creation |
| Template-based generation | LLM-powered with complexity control | 2024 | Evolution techniques (reasoning, multi-context) create realistic scenarios |
| Single framework evaluation | Multi-framework orchestration | 2025-2026 | Combine strengths: DeepEval (bulk), Ragas (RAG), Giskard (components) |
| Hardcoded pipelines | Function calling orchestration | 2025 | OpenAI routes dynamically based on task context |
| JSON Schema definitions | Pydantic v2 with strict mode | 2023-2024 | Structured outputs guarantee schema conformance, 5-50x faster |
| Functions parameter | Tools parameter | 2024 | Modern OpenAI API uses `tools`, `functions` is legacy |

**Deprecated/outdated:**
- Pydantic v1 syntax: Replaced by v2 (2023), significantly faster, use v2 syntax throughout
- OpenAI `functions` parameter: Use `tools` parameter instead (legacy as of 2024)
- Single-turn only datasets: Multi-turn conversational goldens now standard (DeepEval 2026)
- Manual deduplication: Framework-level quality filters now standard practice

## Recommended Framework Roles

Based on capability research:

### DeepEval Synthesizer (Primary Engine)
**Role:** Bulk test case and dataset example generation from documents
**Strengths:**
- Evolution techniques for complexity (7 types: reasoning, multi-context, concretizing, constrained, comparative, hypothetical, in-breadth)
- Filtration config for quality control
- Styling config for format customization
- Async mode for speed (max_concurrent=100)
- Pytest integration for CI/CD

**Use when:**
- Generating from policy documents
- Need bulk generation (10+ items)
- Want complexity evolution
- Require custom output formats

**Limitations:**
- Can generate duplicates (needs deduplication)
- Quality depends on filtration threshold
- Document-dependent (needs good source material)

### Ragas TestsetGenerator (RAG Evaluation)
**Role:** RAG-specific question generation with knowledge graph transformations
**Strengths:**
- RAG-specific question types (simple, reasoning, multi-context)
- Knowledge graph construction from documents
- Distribution control (specify ratio of question types)
- Evaluation metrics (faithfulness, context relevancy, answer relevancy)

**Use when:**
- Need RAG pipeline evaluation
- Want multi-hop reasoning questions
- Require question type diversity
- Evaluating retrieval quality

**Limitations:**
- Document quality critical (fails on poor chunks)
- Can generate generic questions for complex contexts
- Occasional NaN values for ground_truth
- 12 prompts = high token cost

### Giskard RAGET (Knowledge Base Validation)
**Role:** Knowledge base testing and component-level RAG evaluation
**Strengths:**
- Automatic question generation from KB
- 6+ question types targeting specific components
- Component scoring (generator, retriever, knowledge base)
- Business test scenarios

**Use when:**
- Validating knowledge base quality
- Need component-level evaluation
- Want business test scenarios
- Testing retriever vs generator separately

**Limitations:**
- Slow (15+ minutes for 60 questions)
- External embedding dependency (OpenAI default)
- Creates challenging questions (may expose many issues)
- Privacy concerns (sends to LLM provider)

### Orchestration Strategy

**Routing logic (Claude's recommendation):**

```python
def route_task(task_context: dict) -> str:
    """
    Decide which framework to use based on task context.
    OpenAI function calling implements this logic.
    """
    # Primary: DeepEval for document-based bulk generation
    if task_context.get("source") == "documents" and task_context.get("count", 0) > 5:
        return "generate_with_deepeval"

    # Secondary: Ragas for RAG-specific evaluation questions
    if task_context.get("purpose") == "rag_evaluation":
        return "generate_with_ragas"

    # Tertiary: Giskard for knowledge base validation
    if task_context.get("purpose") == "kb_validation":
        return "generate_with_giskard"

    # Default: DeepEval
    return "generate_with_deepeval"
```

## Open Questions

1. **How to handle framework version conflicts?**
   - What we know: All frameworks support Python 3.9+, use OpenAI models
   - What's unclear: Dependency conflicts between langchain versions used by different frameworks
   - Recommendation: Use separate virtual environments for testing, pin all versions in requirements.txt

2. **What's the optimal balance between frameworks?**
   - What we know: DeepEval is primary, Ragas/Giskard are complementary
   - What's unclear: Ideal ratio of DeepEval vs Ragas vs Giskard generated items
   - Recommendation: Start with 70% DeepEval, 20% Ragas, 10% Giskard; adjust based on quality metrics

3. **How to validate evaluation criteria quality?**
   - What we know: Need minimum 3 criteria per example, criteria should be specific
   - What's unclear: How to programmatically assess criteria quality
   - Recommendation: Use LLM-as-judge to score criteria on specificity/measurability (0-1 scale), reject <0.7

4. **Should adapters be per-framework or per-output-type?**
   - What we know: Each framework has different output schema
   - What's unclear: Whether to adapt by framework or by output type (test case vs dataset example)
   - Recommendation: Adapter per framework (deepeval_adapter.py, ragas_adapter.py, giskard_adapter.py) - clearer separation of concerns

5. **How to handle multi-turn conversational datasets?**
   - What we know: DeepEval supports `generate_conversational_goldens_from_docs()`
   - What's unclear: Whether Phase 3 scope includes multi-turn or only single-turn
   - Recommendation: Implement single-turn first (simpler), add multi-turn if requirements specify

## Sources

### Primary (HIGH confidence)
- [DeepEval Synthesizer Introduction](https://deepeval.com/docs/synthesizer-introduction) - API reference, evolution techniques
- [Ragas Test Data Generation](https://docs.ragas.io/en/stable/concepts/test_data_generation/) - Testset generation concepts
- [Giskard RAGET Documentation](https://docs.giskard.ai/oss/sdk/business.html) - Business test generation
- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling) - Function calling patterns
- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/) - BaseModel and validation
- [deepeval PyPI 3.8.4](https://pypi.org/project/deepeval/) - Version and dependencies
- [ragas PyPI 0.4.3](https://pypi.org/project/ragas/) - Version and dependencies
- [giskard PyPI 2.19.0](https://pypi.org/project/giskard/) - Version and dependencies
- [openai PyPI 2.21.0](https://pypi.org/project/openai/) - Version and installation
- [pydantic PyPI 2.12.5](https://pypi.org/project/pydantic/) - Version and installation

### Secondary (MEDIUM confidence)
- [DeepEval vs Ragas Comparison](https://deepeval.com/blog/deepeval-vs-ragas) - Framework strengths
- [LLM Evaluation Frameworks 2025](https://medium.com/@mahernaija/choosing-the-right-llm-evaluation-framework-in-2025-deepeval-ragas-giskard-langsmith-and-c7133520770c) - Framework comparison
- [Tool Calling Best Practices](https://medium.com/@laurentkubaski/openai-tool-calling-using-the-python-sdk-full-example-with-best-practices-29af7c651f08) - OpenAI patterns
- [Pydantic Complete Guide 2026](https://devtoolbox.dedyn.io/blog/pydantic-complete-guide) - v2 features
- [Ragas Test Set Generation Breakdown](https://pixion.co/blog/ragas-test-set-generation-breakdown) - Generation pipeline
- [RAG Evaluation Tools Comparison](https://research.aimultiple.com/rag-evaluation-tools/) - Tool capabilities

### Tertiary (LOW confidence - needs validation)
- [DeepEval Duplication Issue](https://github.com/confident-ai/deepeval/issues/1925) - GitHub issue (user report, not official)
- [Ragas Quality Issues](https://github.com/explodinggradients/ragas/issues/1568) - GitHub issue (user report)
- WebSearch results for common pitfalls (multiple sources, needs cross-verification)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All versions verified from PyPI, official docs confirm capabilities
- Architecture: MEDIUM-HIGH - Patterns based on official docs, some integration details inferred
- Pitfalls: MEDIUM - Based on GitHub issues and user reports, not official documentation
- Framework roles: MEDIUM-HIGH - Based on official capabilities, but optimal balance needs validation

**Research date:** 2026-02-16
**Valid until:** 2026-03-16 (30 days - frameworks stable but fast-moving ecosystem)

**Notes:**
- All frameworks actively maintained (2025-2026 releases)
- Python 3.9+ required across all frameworks
- OpenAI models used throughout (gpt-4o, gpt-4o-mini)
- Temperature=0 for reproducibility (matches project requirement REPR-02)
- Pydantic v2 syntax verified (matches project requirement)
