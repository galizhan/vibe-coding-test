# Architecture Research

**Domain:** LLM-based Synthetic Dataset Generation Pipeline
**Researched:** 2026-02-16
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CLI INTERFACE LAYER                              │
│  (Typer: Commands, Parameters, Validation, Help)                    │
├─────────────────────────────────────────────────────────────────────┤
│                     PIPELINE ORCHESTRATION LAYER                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Document    │→ │   Use Case   │→ │  Policy      │              │
│  │  Parser      │  │  Extractor   │  │  Extractor   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│         ↓                  ↓                  ↓                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Test Case   │  │  Dataset     │  │  Manifest    │              │
│  │  Generator   │  │  Generator   │  │  Generator   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
├─────────────────────────────────────────────────────────────────────┤
│                     LLM INTERACTION LAYER                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  LLM Client (OpenAI Structured Outputs + Retry Logic)        │   │
│  └──────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────┤
│                     VALIDATION LAYER                                 │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  Schema         │  │  Evidence    │  │  ID/Prefix   │           │
│  │  Validator      │  │  Validator   │  │  Validator   │           │
│  │  (Pydantic)     │  │              │  │              │           │
│  └─────────────────┘  └──────────────┘  └──────────────┘           │
├─────────────────────────────────────────────────────────────────────┤
│                     OBSERVABILITY LAYER                              │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  Logging        │  │  Tracing     │  │  Metrics     │           │
│  │  (structlog)    │  │  (Langfuse)  │  │  (cost/time) │           │
│  └─────────────────┘  └──────────────┘  └──────────────┘           │
├─────────────────────────────────────────────────────────────────────┤
│                     STORAGE LAYER                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Input    │  │ Use Cases│  │ Test     │  │ Dataset  │            │
│  │ Docs     │  │ JSON     │  │ Cases    │  │ JSON     │            │
│  │ (.md)    │  │          │  │ JSON     │  │          │            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| CLI Interface | Command parsing, parameter validation, user feedback | Typer with type hints, auto-completion |
| Pipeline Orchestrator | Stage execution, dependency management, error recovery | Sequential stage runner with checkpointing |
| Document Parser | Markdown parsing, line tracking, section extraction | Python markdown library with line number preservation |
| LLM Extractor (Use Case/Policy) | Structured extraction via LLM with evidence | OpenAI Structured Outputs with Pydantic schemas |
| Test Case Generator | Parameter variation, test case creation | Combinatorial logic over extracted axes |
| Dataset Generator | Example generation with evaluation criteria | LLM-based generation with schema validation |
| Schema Validator | JSON schema validation, type checking | Pydantic models with custom validators |
| Evidence Validator | Line number verification, quote matching | String matching against source document |
| LLM Client | API calls, retry logic, structured output parsing | OpenAI Python SDK with exponential backoff |
| Tracing System | Distributed tracing, span tracking, performance | Langfuse SDK with OpenTelemetry |
| Manifest Generator | Run metadata, dataset lineage tracking | JSON serialization of run configuration |

## Recommended Project Structure

```
src/
├── cli/
│   ├── __init__.py
│   ├── main.py              # Typer app entrypoint
│   ├── commands.py          # Command definitions
│   └── validators.py        # CLI parameter validators
├── pipeline/
│   ├── __init__.py
│   ├── orchestrator.py      # Pipeline execution coordinator
│   ├── stages.py            # Stage definitions and interfaces
│   └── context.py           # Pipeline context (shared state)
├── parsers/
│   ├── __init__.py
│   ├── markdown.py          # Markdown parser with line tracking
│   └── line_tracker.py      # Line number preservation utilities
├── extractors/
│   ├── __init__.py
│   ├── base.py              # Base extractor interface
│   ├── use_case.py          # Use case extraction logic
│   └── policy.py            # Policy extraction logic
├── generators/
│   ├── __init__.py
│   ├── test_case.py         # Test case generation
│   ├── dataset.py           # Dataset example generation
│   └── manifest.py          # Run manifest generation
├── llm/
│   ├── __init__.py
│   ├── client.py            # OpenAI client wrapper
│   ├── prompts.py           # Prompt templates
│   ├── retry.py             # Retry logic with backoff
│   └── seed_manager.py      # Seed management for reproducibility
├── schemas/
│   ├── __init__.py
│   ├── use_case.py          # UseCase Pydantic model
│   ├── policy.py            # Policy Pydantic model
│   ├── test_case.py         # TestCase Pydantic model
│   ├── dataset.py           # DatasetExample Pydantic model
│   └── manifest.py          # RunManifest Pydantic model
├── validators/
│   ├── __init__.py
│   ├── schema.py            # Pydantic-based schema validation
│   ├── evidence.py          # Evidence quote matching
│   └── ids.py               # ID prefix validation
├── observability/
│   ├── __init__.py
│   ├── logging.py           # Structured logging setup
│   ├── tracing.py           # Langfuse tracing setup
│   └── metrics.py           # Cost and performance metrics
└── utils/
    ├── __init__.py
    ├── file_io.py           # File reading/writing
    └── errors.py            # Custom exception classes
```

### Structure Rationale

- **cli/:** Separation of CLI concerns from business logic. Typer handles user interaction, delegates to pipeline.
- **pipeline/:** Orchestration logic separate from individual stages. Stages are composable and testable independently.
- **parsers/:** Document parsing isolated from extraction. Line tracking is critical for evidence validation.
- **extractors/:** LLM-based extraction logic. Each extractor type (use case, policy) has dedicated logic.
- **generators/:** Generation logic (test cases, datasets) separate from extraction. Different data transformation patterns.
- **llm/:** LLM interaction abstracted behind a client interface. Retry logic, seed management, and prompt templates centralized.
- **schemas/:** Pydantic models define data contracts. Single source of truth for validation.
- **validators/:** Validation logic beyond Pydantic's built-in capabilities. Evidence matching requires custom logic.
- **observability/:** Logging, tracing, metrics isolated. Easy to swap implementations or disable.
- **utils/:** Shared utilities avoid duplication.

## Architectural Patterns

### Pattern 1: Pipeline Orchestration with Sequential Stages

**What:** A pipeline orchestrator executes stages sequentially, passing context between stages. Each stage is idempotent and can be checkpointed.

**When to use:** Multi-step workflows where each stage depends on the previous stage's output. Needed when failure recovery is important.

**Trade-offs:**
- **Pros:** Clear separation of concerns, easy to test individual stages, supports checkpointing/resume
- **Cons:** Sequential execution (no parallelization), overhead of context passing

**Example:**
```python
# pipeline/orchestrator.py
class PipelineOrchestrator:
    def __init__(self, stages: List[Stage], context: PipelineContext):
        self.stages = stages
        self.context = context

    def run(self):
        for stage in self.stages:
            logger.info(f"Starting stage: {stage.name}")
            try:
                stage.execute(self.context)
                self.context.checkpoint(stage.name)
            except Exception as e:
                logger.error(f"Stage {stage.name} failed: {e}")
                raise PipelineError(f"Pipeline failed at stage: {stage.name}") from e

# Usage
stages = [
    ParseDocumentStage(),
    ExtractUseCasesStage(),
    ExtractPoliciesStage(),
    GenerateTestCasesStage(),
    GenerateDatasetStage(),
    GenerateManifestStage()
]
orchestrator = PipelineOrchestrator(stages, context)
orchestrator.run()
```

### Pattern 2: Structured Output with Schema Validation

**What:** Use OpenAI Structured Outputs to enforce JSON schema adherence, then validate with Pydantic. This provides double validation: LLM-side and application-side.

**When to use:** When LLM outputs must conform to strict schemas. Critical for downstream systems that expect specific formats.

**Trade-offs:**
- **Pros:** 100% schema adherence from LLM (per OpenAI docs), type safety in Python, automatic validation errors
- **Cons:** Schema must be JSON Schema compatible, slightly higher latency, limited to supported models (GPT-4o+)

**Example:**
```python
# llm/client.py
from openai import OpenAI
from pydantic import BaseModel

class LLMClient:
    def __init__(self, api_key: str, seed: Optional[int] = None):
        self.client = OpenAI(api_key=api_key)
        self.seed = seed

    def extract_structured(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        temperature: float = 0.0
    ) -> BaseModel:
        """Extract structured output using OpenAI Structured Outputs."""
        completion = self.client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[{"role": "user", "content": prompt}],
            response_format=response_model,
            temperature=temperature,
            seed=self.seed
        )

        # Returns parsed Pydantic model directly
        return completion.choices[0].message.parsed

# Usage
from schemas.use_case import UseCaseExtraction

client = LLMClient(api_key=os.getenv("OPENAI_API_KEY"), seed=42)
extraction = client.extract_structured(
    prompt=build_use_case_prompt(document),
    response_model=UseCaseExtraction
)
# extraction is already a validated Pydantic model
```

### Pattern 3: Evidence-Based Extraction with Line Tracking

**What:** Parse documents with line number preservation, extract structured data with LLM, validate that evidence quotes exactly match source lines.

**When to use:** When extraction claims must be verifiable against source documents. Essential for auditability and debugging.

**Trade-offs:**
- **Pros:** High confidence in extraction accuracy, debuggable (can trace back to source), prevents hallucination
- **Cons:** Additional validation overhead, requires careful line tracking during parsing

**Example:**
```python
# parsers/markdown.py
class MarkdownParser:
    def parse_with_lines(self, file_path: str) -> Document:
        """Parse markdown while preserving line numbers."""
        with open(file_path, 'r') as f:
            lines = f.readlines()

        return Document(
            content=''.join(lines),
            lines=[(i+1, line.rstrip()) for i, line in enumerate(lines)]
        )

# validators/evidence.py
class EvidenceValidator:
    def validate_evidence(self, evidence: Evidence, document: Document) -> bool:
        """Verify that evidence quotes match document lines exactly."""
        for line_num in evidence.line_numbers:
            if line_num > len(document.lines):
                raise ValidationError(f"Line {line_num} exceeds document length")

            actual_line = document.lines[line_num - 1][1]
            if evidence.quote not in actual_line:
                raise ValidationError(
                    f"Quote '{evidence.quote}' not found in line {line_num}: '{actual_line}'"
                )
        return True
```

### Pattern 4: Retry with Exponential Backoff

**What:** Wrap LLM calls with retry logic using exponential backoff for transient failures (rate limits, network issues).

**When to use:** All external API calls, especially to LLM providers. Essential for production reliability.

**Trade-offs:**
- **Pros:** Handles transient failures gracefully, improves reliability
- **Cons:** Increases total execution time on failures, can mask underlying issues if not logged

**Example:**
```python
# llm/retry.py
import time
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1.0, backoff_factor=2.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (RateLimitError, APIConnectionError) as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"Attempt {attempt+1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= backoff_factor
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Usage in LLMClient
@retry_with_backoff(max_retries=3)
def extract_structured(self, prompt, response_model):
    # ... API call
```

### Pattern 5: Observable Pipeline with Distributed Tracing

**What:** Instrument pipeline stages with distributed tracing (Langfuse/OpenTelemetry) to capture execution flow, timings, token usage, and costs.

**When to use:** Production pipelines where debugging, cost tracking, and performance optimization are important.

**Trade-offs:**
- **Pros:** Deep visibility into pipeline execution, cost attribution per stage, performance bottleneck identification
- **Cons:** Adds instrumentation overhead, requires trace collector setup

**Example:**
```python
# observability/tracing.py
from langfuse.decorators import observe, langfuse_context

@observe(as_type="generation")
def extract_use_cases(document: str, llm_client: LLMClient) -> UseCaseExtraction:
    """Extract use cases with automatic tracing."""
    result = llm_client.extract_structured(
        prompt=build_use_case_prompt(document),
        response_model=UseCaseExtraction
    )

    # Langfuse automatically captures:
    # - Input (document)
    # - Output (result)
    # - Model used
    # - Tokens consumed
    # - Latency
    # - Cost

    langfuse_context.update_current_observation(
        metadata={"document_length": len(document)}
    )

    return result

# Pipeline stage with tracing
@observe(as_type="span")
def execute_extraction_stage(context: PipelineContext):
    """Execute extraction stage with span tracking."""
    with langfuse_context.observe(name="parse_document"):
        document = parse_document(context.input_file)

    with langfuse_context.observe(name="extract_use_cases"):
        use_cases = extract_use_cases(document.content, context.llm_client)

    context.use_cases = use_cases
```

## Data Flow

### Request Flow

```
[CLI Command]
    ↓
[Validate Parameters] (seed, input file, output dir)
    ↓
[Initialize Pipeline Context] (create context with config)
    ↓
[Stage 1: Parse Document]
    ↓ (Document with line tracking)
[Stage 2: Extract Use Cases]
    LLM Call (structured output) → Pydantic Validation → Evidence Validation
    ↓ (List[UseCase])
[Stage 3: Extract Policies]
    LLM Call (structured output) → Pydantic Validation → Evidence Validation
    ↓ (List[Policy])
[Stage 4: Generate Test Cases]
    Combinatorial Generation → ID Assignment → Validation
    ↓ (List[TestCase])
[Stage 5: Generate Dataset]
    For Each Test Case: LLM Call → Pydantic Validation
    ↓ (List[DatasetExample])
[Stage 6: Generate Manifest]
    Collect Metadata → Serialize to JSON
    ↓ (RunManifest)
[Stage 7: Write Outputs]
    JSON Serialization → File I/O
    ↓
[Return Success]
```

### State Management

```
PipelineContext (shared state across stages)
    ├── config: PipelineConfig (seed, model, temperature)
    ├── input_document: Document (parsed with line tracking)
    ├── use_cases: List[UseCase] (from extraction)
    ├── policies: List[Policy] (from extraction)
    ├── test_cases: List[TestCase] (generated)
    ├── dataset_examples: List[DatasetExample] (generated)
    ├── manifest: RunManifest (metadata)
    └── traces: Dict[str, TraceInfo] (for observability)
```

### Key Data Flows

1. **Document → Extraction:** Markdown file parsed with line numbers → LLM extracts structured data with evidence → Evidence validated against source lines → Pydantic validates schema
2. **Extraction → Generation:** Use cases and policies analyzed → Parameter variation axes identified → Test cases generated combinatorially → Each test case gets unique ID
3. **Test Cases → Dataset:** For each test case → LLM generates example conversation → Output includes messages, expected_output, evaluation_criteria → Pydantic validates against DatasetExample schema
4. **Pipeline → Observability:** Each stage wrapped in trace span → LLM calls captured with token usage → Costs calculated → Traces sent to Langfuse → Metrics aggregated in manifest

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1-10 documents | Sequential pipeline is fine. Single process handles everything. In-memory context sufficient. |
| 10-100 documents | Add parallel extraction (process documents concurrently). Use process pool for independent documents. Maintain sequential stages within each document. |
| 100+ documents | Add queue-based orchestration (Celery/RQ). Separate extraction workers from generation workers. Add persistent checkpointing (database instead of memory). Consider batch LLM API calls. |

### Scaling Priorities

1. **First bottleneck: LLM API calls** - Each document makes multiple LLM calls sequentially. Solution: Parallelize document processing (not stages), use async/await for LLM calls, batch where possible.
2. **Second bottleneck: File I/O** - Writing large JSON files can be slow. Solution: Stream JSON output, compress output files, use faster serialization (orjson instead of standard json).
3. **Third bottleneck: Evidence validation** - String matching against large documents is O(n*m). Solution: Build line index during parsing, use more efficient string matching algorithms, cache validation results.

## Anti-Patterns

### Anti-Pattern 1: Embedding LLM Calls Directly in Business Logic

**What people do:** Mix LLM API calls with extraction/generation logic in the same function.

**Why it's wrong:** Makes testing impossible without hitting API, couples business logic to specific LLM provider, no retry/rate limiting abstraction.

**Do this instead:** Abstract LLM client behind an interface. Inject client into extractors/generators. Makes testing easy (mock client), allows provider switching, centralizes retry logic.

```python
# BAD
def extract_use_cases(document: str) -> List[UseCase]:
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": f"Extract use cases from: {document}"}]
    )
    # ... parsing logic

# GOOD
class UseCaseExtractor:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def extract(self, document: str) -> List[UseCase]:
        return self.llm_client.extract_structured(
            prompt=build_use_case_prompt(document),
            response_model=UseCaseExtraction
        ).use_cases
```

### Anti-Pattern 2: Validating After Writing to Disk

**What people do:** Generate output, write to JSON files, then validate. If validation fails, outputs are already written.

**Why it's wrong:** Leaves invalid files on disk, confuses downstream consumers, makes cleanup complex, violates fail-fast principle.

**Do this instead:** Validate in memory before writing. Use Pydantic's validation during object construction. Only write after full validation passes.

```python
# BAD
def generate_dataset(test_cases):
    examples = []
    for tc in test_cases:
        example = llm_generate_example(tc)
        examples.append(example)

    # Write first
    with open("dataset.json", "w") as f:
        json.dump(examples, f)

    # Validate after (too late!)
    validate_dataset(examples)

# GOOD
def generate_dataset(test_cases):
    examples = []
    for tc in test_cases:
        raw_example = llm_generate_example(tc)
        # Validate immediately (Pydantic raises on invalid)
        validated = DatasetExample(**raw_example)
        examples.append(validated)

    # Only write after all validation passes
    with open("dataset.json", "w") as f:
        json.dump([e.model_dump() for e in examples], f)
```

### Anti-Pattern 3: Ignoring Reproducibility Constraints

**What people do:** Don't set seed, use default temperature (1.0), ignore model version updates.

**Why it's wrong:** Same inputs produce different outputs each run, impossible to debug, can't reproduce issues, breaks testing.

**Do this instead:** Accept seed as CLI parameter, set temperature=0 for deterministic outputs, pin model versions, document that "mostly deterministic" is OpenAI's limit.

```python
# BAD
client = OpenAI(api_key=api_key)
response = client.chat.completions.create(
    model="gpt-4o",  # version not pinned
    messages=[...],
    # no seed, no temperature
)

# GOOD
client = OpenAI(api_key=api_key)
response = client.chat.completions.create(
    model="gpt-4o-2024-08-06",  # version pinned
    messages=[...],
    temperature=0.0,  # deterministic
    seed=context.seed  # reproducible across runs
)
```

### Anti-Pattern 4: Losing Line Number Context During Parsing

**What people do:** Parse markdown into plain text or HTML, lose original line numbers, can't validate evidence later.

**Why it's wrong:** Evidence validation becomes impossible, can't trace quotes back to source, debugging is painful.

**Do this instead:** Preserve line numbers during parsing. Store tuples of (line_number, content). Include line numbers in all intermediate representations.

```python
# BAD
def parse_markdown(file_path: str) -> str:
    with open(file_path) as f:
        return f.read()  # loses line numbers

# GOOD
def parse_markdown(file_path: str) -> Document:
    with open(file_path) as f:
        lines = [(i+1, line.rstrip()) for i, line in enumerate(f)]

    return Document(
        content='\n'.join(line for _, line in lines),
        lines=lines,  # preserved for evidence validation
        metadata={"file_path": file_path}
    )
```

### Anti-Pattern 5: Hardcoding Prompt Templates

**What people do:** Embed prompt text directly in extraction/generation functions as f-strings.

**Why it's wrong:** Prompts are hard to version, can't A/B test, no reuse across functions, difficult to optimize.

**Do this instead:** Centralize prompts in dedicated module. Use template system (Jinja2). Version prompts with metadata. Inject prompts into extractors/generators.

```python
# BAD
def extract_use_cases(document: str):
    prompt = f"""Extract use cases from this document.
    Document:
    {document}

    Return JSON with use_cases array."""
    return llm_call(prompt)

# GOOD
# llm/prompts.py
USE_CASE_EXTRACTION_TEMPLATE = """
Extract use cases from the following document.
For each use case, include:
- Name
- Description
- Evidence (line numbers and exact quotes)

Document:
{{ document }}

Return structured output following the UseCaseExtraction schema.
"""

def build_use_case_prompt(document: str) -> str:
    template = Template(USE_CASE_EXTRACTION_TEMPLATE)
    return template.render(document=document)
```

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| OpenAI API | OpenAI Python SDK with Structured Outputs | Use `client.beta.chat.completions.parse()` for schema enforcement. Set temperature=0, seed for reproducibility. |
| Langfuse | OpenTelemetry-based SDK v3 | Use `@observe` decorator for automatic tracing. Captures tokens, cost, latency automatically. |
| DeepEval | Direct Python integration | Import metrics, create test cases with Dataset class. Use for post-generation validation. |
| Evidently | Dataset export to Evidently format | Generate Evidently-compatible JSON after dataset creation. |
| Giskard | Export as Giskard dataset | Similar to Evidently - format transformation layer. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| CLI ↔ Pipeline | Direct function call with PipelineContext | CLI creates context, passes to orchestrator. Orchestrator returns success/failure. |
| Pipeline ↔ Stages | Context injection pattern | Each stage receives context, modifies it, returns. Context is mutable shared state. |
| Stages ↔ LLM Client | Dependency injection | Stages receive LLM client via constructor. Allows testing with mock client. |
| Stages ↔ Validators | Direct function call | Validators are pure functions. Take data + rules, return boolean or raise exception. |
| LLM Client ↔ OpenAI | REST API via SDK | SDK handles serialization, auth, retry. Client wraps SDK for structured outputs. |
| Pipeline ↔ Langfuse | Decorator-based tracing | `@observe` decorator intercepts function calls. Automatic span creation, no explicit API calls needed. |

## Build Order Recommendations

Based on dependency analysis, suggested implementation order:

### Phase 1: Foundation (Week 1)
1. **Project structure setup** - Create folder structure, setup.py/pyproject.toml
2. **Schema definitions** - Define all Pydantic models (Document, UseCase, Policy, TestCase, DatasetExample, Manifest)
3. **Basic CLI skeleton** - Typer app with placeholder commands, parameter parsing
4. **File I/O utilities** - Read markdown, write JSON, path handling

**Why this order:** Schemas are the contract for everything else. CLI provides the user interface. File I/O is needed by all stages.

### Phase 2: Document Processing (Week 1-2)
1. **Markdown parser with line tracking** - Parse markdown, preserve line numbers
2. **Document model** - Wrap parsed content with line index
3. **Evidence validator** - Verify quotes match source lines

**Why this order:** Can't extract until documents are parsed. Evidence validation depends on line tracking.

### Phase 3: LLM Integration (Week 2)
1. **LLM client abstraction** - Wrapper around OpenAI SDK
2. **Structured output implementation** - Use OpenAI's parse() method
3. **Retry logic** - Exponential backoff for API calls
4. **Seed management** - Handle reproducibility parameter

**Why this order:** LLM client is needed by extraction stages. Structured outputs simplify validation. Retry logic is critical for reliability.

### Phase 4: Extraction (Week 2-3)
1. **Prompt templates** - Centralize extraction prompts
2. **Use case extractor** - LLM-based use case extraction with evidence
3. **Policy extractor** - LLM-based policy extraction with evidence
4. **Schema validators** - Pydantic validation for extracted data

**Why this order:** Prompts are required by extractors. Each extractor builds on LLM client and schemas.

### Phase 5: Generation (Week 3-4)
1. **Test case generator** - Combinatorial generation from use cases + policies
2. **ID assignment logic** - Prefix-based ID generation (uc_, pol_, tc_, ex_)
3. **Dataset generator** - LLM-based example generation
4. **Manifest generator** - Collect run metadata

**Why this order:** Test cases depend on extraction outputs. Dataset generation depends on test cases. Manifest is last (needs all other data).

### Phase 6: Pipeline Orchestration (Week 4)
1. **Pipeline context** - Shared state container
2. **Stage interface** - Abstract base class for stages
3. **Pipeline orchestrator** - Sequential stage execution
4. **Checkpointing** - Save intermediate state for resume

**Why this order:** Context and interface enable all stages. Orchestrator ties everything together. Checkpointing is an enhancement.

### Phase 7: Observability (Week 4-5)
1. **Structured logging** - Setup structlog or similar
2. **Langfuse integration** - Add @observe decorators
3. **Metrics collection** - Track costs, tokens, timing
4. **Error handling** - Custom exceptions, error recovery

**Why this order:** Can build pipeline first, add observability after. Tracing and metrics enhance existing functionality.

### Phase 8: Integration & Testing (Week 5-6)
1. **Integration with DeepEval** - Export to DeepEval format
2. **Integration with Evidently** - Export to Evidently format
3. **Integration with Giskard** - Export to Giskard format
4. **End-to-end tests** - Full pipeline tests with real documents
5. **Documentation** - Usage guide, architecture docs

**Why this order:** Integrations require complete pipeline. Testing validates everything works. Documentation captures learnings.

### Critical Path Dependencies

```
Schemas → LLM Client → Extractors → Generators → Pipeline → CLI
   ↓                      ↓              ↓
Validators             Prompts      Manifest
```

**Key insight:** Schemas are foundational. LLM client is a critical dependency. Pipeline orchestration comes late (ties it all together).

## Sources

**CLI Architecture & Best Practices:**
- [Best Practices for Structuring a Python CLI Application](https://medium.com/@ernestwinata/best-practices-for-structuring-a-python-cli-application-1bc8f8a57369)
- [Python Application Layouts: A Reference – Real Python](https://realpython.com/python-application-layouts/)
- [10+ Best Python CLI Libraries for Developers | Medium](https://medium.com/@wilson79/10-best-python-cli-libraries-for-developers-picking-the-right-one-for-your-project-cefb0bd41df1)
- [Mastering CLI Design: Best Practices for Powerful Command-Line Tools](https://jsschools.com/programming/mastering-cli-design-best-practices-for-powerful-/)

**LLM Pipeline Architecture:**
- [Efficient and Verified Extraction of the Research Data Using LLM](https://www.preprints.org/manuscript/202511.2140/v1/download)
- [Ultimate Guide to Preprocessing Pipelines for LLMs | Latitude](https://latitude.so/blog/ultimate-guide-to-preprocessing-pipelines-for-llms)
- [Building Data Pipelines to Create Apps with Large Language Models - KDnuggets](https://www.kdnuggets.com/building-data-pipelines-to-create-apps-with-large-language-models)
- [LLM Apps Are Mostly Data Pipelines](https://meltano.com/blog/llm-apps-are-mostly-data-pipelines/)

**Structured Outputs & Validation:**
- [How JSON Schema Works for LLM Tools & Structured Outputs](https://blog.promptlayer.com/how-json-schema-works-for-structured-outputs-and-tool-integration/)
- [Structured Outputs (JSON Mode) | liteLLM](https://docs.litellm.ai/docs/completion/json_mode)
- [The guide to structured outputs and function calling with LLMs](https://agenta.ai/blog/the-guide-to-structured-outputs-and-function-calling-with-llms)
- [LLM Structured Outputs: Schema Validation for Real Pipelines | Collin Wilkins](https://collinwilkins.com/articles/structured-output)

**Pydantic Architecture:**
- [Welcome to Pydantic - Pydantic Validation](https://docs.pydantic.dev/latest/)
- [Architecture - Pydantic Validation](https://docs.pydantic.dev/latest/internals/architecture/)
- [Pydantic: The Complete Guide for 2026 | DevToolbox Blog](https://devtoolbox.dedyn.io/blog/pydantic-complete-guide)

**Reproducibility & Determinism:**
- [Seed vs. Temperature in Language Models - by Daniel Kleine](https://dkleine.substack.com/p/seed-vs-temperature-in-language-models)
- [Controlling randomness in LLMs: Temperature and Seed – Dylan Castillo](https://dylancastillo.co/posts/seed-temperature-llms.html)
- [How to get consistent and reproducible LLM outputs in 2025](https://www.keywordsai.co/blog/llm_consistency_2025)
- [Does Temperature 0 Guarantee Deterministic LLM Outputs? - Vincent Schmalbach](https://www.vincentschmalbach.com/does-temperature-0-guarantee-deterministic-llm-outputs/)

**Evidence Extraction & Citation:**
- [Improved Evidence Extraction for Document Inconsistency Detection with LLMs](https://arxiv.org/abs/2601.02627)
- [Document Extraction Software: Confidence Scores & Citations | LlamaExtract](https://www.llamaindex.ai/llamaextract)
- [Automating Data Extraction From Scientific Literature Using LLMs](https://wires.onlinelibrary.wiley.com/doi/10.1002/wcms.70047)

**Observability & Tracing:**
- [LLM Observability & Application Tracing (Open Source) - Langfuse](https://langfuse.com/docs/observability/overview)
- [Tracing Data Model in Langfuse](https://langfuse.com/docs/observability/data-model)
- [Get Started with Tracing - Langfuse](https://langfuse.com/docs/observability/get-started)
- [Open Source LLM Observability via OpenTelemetry - Langfuse](https://langfuse.com/integrations/native/opentelemetry)

**Testing & Evaluation:**
- [GitHub - confident-ai/deepeval: The LLM Evaluation Framework](https://github.com/confident-ai/deepeval)
- [DeepEval by Confident AI - The LLM Evaluation Framework](https://deepeval.com/)
- [Quick Introduction | DeepEval](https://deepeval.com/docs/getting-started)

**Pipeline Orchestration:**
- [How to Implement Data Pipeline Orchestration with Airflow](https://oneuptime.com/blog/post/2026-02-02-airflow-data-pipelines/view)
- [Error Handling and Logging in Data Pipelines | Towards Data Engineering](https://medium.com/towards-data-engineering/error-handling-and-logging-in-data-pipelines-ensuring-data-reliability-227df82ba782)
- [Data Pipelines with Python: 6 Frameworks & Quick Tutorial | Dagster](https://dagster.io/guides/data-pipelines-with-python-6-frameworks-quick-tutorial)

**Synthetic Data Generation:**
- [Best synthetic data generation tools for 2026](https://www.k2view.com/blog/best-synthetic-data-generation-tools/)
- [Synthetic Data Generation Benchmark in 2026](https://research.aimultiple.com/synthetic-data-generation/)
- [A Systematic Review of Synthetic Data Generation Techniques Using Generative AI](https://www.mdpi.com/2079-9292/13/17/3509)

**Dataset Metadata & Manifests:**
- [ML Metadata | TFX | TensorFlow](https://www.tensorflow.org/tfx/guide/mlmd)
- [Data Versioning: ML Best Practices Checklist 2026 | Label Your Data](https://labelyourdata.com/articles/machine-learning/data-versioning)

---
*Architecture research for: LLM-based Synthetic Dataset Generation Pipeline*
*Researched: 2026-02-16*
*Confidence: HIGH (verified with official docs, recent research, multiple sources)*
