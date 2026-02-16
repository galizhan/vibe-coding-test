# Phase 4: All Use Cases - Research

**Researched:** 2026-02-16
**Domain:** Multi-case dataset generation with universal pipeline architecture
**Confidence:** HIGH

## Summary

Phase 4 extends the single-case pipeline from Phase 3 to support all three use cases (support bot, operator quality checker, doctor booking) through a universal, non-hardcoded generation architecture. The core technical challenge is implementing LLM-driven auto-detection of case and format fields while maintaining strict data contract compliance across diverse output formats.

The pipeline must generate three distinct dataset formats (single_turn_qa, single_utterance_correction, dialog_last_turn_correction) and classify metadata.source types (tickets, faq_paraphrase, corner) without explicit configuration. This requires structured LLM prompts with enum constraints, parameter variation combinatorics, and format-specific validation logic.

**Primary recommendation:** Use OpenAI structured outputs with Pydantic models for case/format auto-detection. Implement variation axis routing through combinatorial parameter generation. Build format-specific adapters that enforce tz.md canonical examples as validation templates.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Pipeline universality
- Generic pipeline only — no case-specific few-shot examples in generation prompts
- The extracted use cases and policies from Phase 2 guide generation, not hardcoded templates
- Pipeline should work on any document, not just the 3 known examples
- `case` field auto-detected from document content by LLM (not from filename or CLI flag)
- `format` field auto-detected from document content (not CLI flag)
- One document can produce examples in MULTIPLE formats (e.g. operator doc → both single_utterance_correction AND dialog_last_turn_correction)

#### Source type classification
- `metadata.source` (tickets, faq_paraphrase, corner) classified automatically by LLM based on use case context
- No explicit config or mapping needed

#### Operator corrections
- Follow tz.md examples exactly for correction formats
- Errors in generated operator messages are driven by test case parameter combinations (mixed errors, not one-at-a-time)
- Dialog length follows tz.md minimum (2+ messages for dialog_last_turn_correction)
- Escalation responses include full text as shown in tz.md canonical examples
- Variation axes from tz.md: длина фразы, пунктуация/опечатки, сленг/мат/эмодзи, медицинские термины, агрессия пользователя, необходимость эскалации

#### Output structure
- Follow tz.md strictly: pre-generated artifacts in out/support/ and out/operator_quality/ only
- Doctor booking is optional усложнённый пример — no committed output required
- Artifacts NOT committed to repo — generate on demand only
- Each output directory contains: run_manifest.json, use_cases.json, policies.json, test_cases.json, dataset.json

#### Validation rules
- Follow tz.md data contract exactly — all mandatory fields, ID conventions, evidence format
- All 3 cases share the same validation rules (same data contract)
- tz.md acceptance criteria are the minimum thresholds: 5+ use cases, 5+ policies, 3+ test cases per use case, 1+ example per test case
- evidence[] must pass exact quote matching (with fuzzy fallback from Phase 2)

### Claude's Discretion
- Implementation of auto-detection logic for case and format
- How to route test case generation across variation axes
- Internal structure of generation prompts (as long as pipeline stays generic)
- Doctor booking case handling (case value, format choice)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| OpenAI Python SDK | >=1.0 | Structured outputs with JSON schema | Industry standard for guaranteed schema compliance with enum validation |
| Pydantic | >=2.0 | Data validation and enum types | V2 adds strict mode support for OpenAI structured outputs |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| allpairspy | Latest | Pairwise combinatorial testing | When generating test case parameter combinations (reduces test explosion) |
| rapidfuzz | >=3.0 | Fuzzy string matching | Already used in Phase 2 for evidence validation |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| OpenAI structured outputs | Manual JSON parsing | Structured outputs guarantee schema compliance; manual parsing requires extensive validation code |
| Pairwise testing | Full combinatorial | Pairwise covers most bugs with fewer test cases (N² vs 2^N growth) |
| LLM auto-detection | Filename-based routing | LLM maintains universality; filenames create hardcoded dependencies |

**Installation:**
```bash
# Already in pyproject.toml from Phase 3
pip install pydantic>=2.0 openai>=1.0 rapidfuzz>=3.0
# Add for combinatorics
pip install allpairspy
```

## Architecture Patterns

### Recommended Project Structure
```
src/dataset_generator/
├── generation/
│   ├── case_detector.py       # LLM-based case/format detection
│   ├── variation_router.py    # Parameter axis routing
│   ├── format_adapters/       # Format-specific logic
│   │   ├── support_bot.py
│   │   ├── operator_quality.py
│   │   └── base.py
│   └── source_classifier.py   # metadata.source classification
├── models/
│   └── dataset_example.py     # Extended with target_message_index
└── pipeline.py                # Universal orchestrator
```

### Pattern 1: LLM-Based Case/Format Auto-Detection

**What:** Use OpenAI structured outputs with Pydantic enums to classify case and format fields without configuration.

**When to use:** When pipeline must remain universal and work on unknown documents.

**Example:**
```python
# Source: OpenAI Structured Outputs + Pydantic best practices
from pydantic import BaseModel, Field
from typing import Literal
from openai import OpenAI

class CaseFormatDetection(BaseModel):
    """Auto-detect case and format from document content."""
    case: Literal["support_bot", "operator_quality", "doctor_booking"] = Field(
        description="Type of use case based on domain"
    )
    formats: list[Literal[
        "single_turn_qa",
        "single_utterance_correction",
        "dialog_last_turn_correction"
    ]] = Field(
        description="Applicable formats for this document (can be multiple)"
    )
    reasoning: str = Field(
        description="Brief explanation of classification"
    )

def detect_case_and_format(use_case_description: str, policy_summaries: list[str]) -> CaseFormatDetection:
    """Detect case and format using structured outputs."""
    client = OpenAI()

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Classify the use case domain and applicable dataset formats."
            },
            {
                "role": "user",
                "content": f"Use case: {use_case_description}\nPolicies: {policy_summaries}"
            }
        ],
        response_format=CaseFormatDetection,
        temperature=0,
    )

    return completion.choices[0].message.parsed
```

### Pattern 2: Metadata Source Classification

**What:** Classify dataset example source types (tickets, faq_paraphrase, corner) based on generation context.

**When to use:** For support_bot case to meet tz.md requirement of all 3 source types.

**Example:**
```python
# Source: LLM metadata classification patterns 2025
class SourceTypeClassifier(BaseModel):
    """Classify the source type of a dataset example."""
    source: Literal["tickets", "faq_paraphrase", "corner"] = Field(
        description="tickets: from support ticket data, faq_paraphrase: rephrased FAQ, corner: edge/adversarial case"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Classification confidence")

def classify_source_type(
    use_case_context: str,
    generated_input: str,
    is_adversarial: bool = False
) -> str:
    """Classify metadata.source based on generation context."""
    if is_adversarial:
        return "corner"

    # Use LLM to distinguish tickets vs faq_paraphrase
    client = OpenAI()
    classification = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Classify whether this example came from real ticket data or FAQ paraphrasing."
            },
            {
                "role": "user",
                "content": f"Use case: {use_case_context}\nUser input: {generated_input}"
            }
        ],
        response_format=SourceTypeClassifier,
        temperature=0,
    )

    return classification.choices[0].message.parsed.source
```

### Pattern 3: Combinatorial Parameter Variation

**What:** Use pairwise testing to generate test case parameter combinations without combinatorial explosion.

**When to use:** When variation axes > 3 and full coverage would create thousands of test cases.

**Example:**
```python
# Source: allpairspy for pairwise combinatorics
from allpairspy import AllPairs

def generate_operator_quality_variations() -> list[dict]:
    """Generate test case parameter combinations for operator quality."""
    # Variation axes from tz.md
    axes = {
        "phrase_length": ["short", "medium", "long"],
        "punctuation_errors": ["none", "minor", "severe"],
        "slang_profanity_emoji": ["none", "moderate", "excessive"],
        "medical_terms": ["none", "present"],
        "user_aggression": ["neutral", "frustrated", "angry"],
        "escalation_needed": ["no", "yes"]
    }

    # Pairwise combinations (covers most interactions with fewer cases)
    combinations = []
    for combo in AllPairs(list(axes.values())):
        param_dict = {k: v for k, v in zip(axes.keys(), combo)}
        combinations.append(param_dict)

    return combinations
```

### Pattern 4: Format-Specific Adapter Pattern

**What:** Separate adapters for each dataset format handle format-specific logic and validation.

**When to use:** When different formats have different structural requirements (e.g., target_message_index for dialog corrections).

**Example:**
```python
# Source: Adapter pattern for format-specific dataset generation
from abc import ABC, abstractmethod

class FormatAdapter(ABC):
    """Base adapter for dataset format generation."""

    @abstractmethod
    def generate_example(
        self,
        use_case_id: str,
        test_case_id: str,
        parameters: dict,
        policies: list[Policy]
    ) -> DatasetExample:
        """Generate a dataset example in this format."""
        pass

    @abstractmethod
    def validate_format(self, example: DatasetExample) -> list[str]:
        """Validate format-specific requirements. Returns list of errors."""
        pass

class DialogLastTurnCorrectionAdapter(FormatAdapter):
    """Adapter for dialog_last_turn_correction format."""

    def generate_example(self, use_case_id, test_case_id, parameters, policies):
        # Generate multi-turn dialog with operator as last message
        messages = self._generate_dialog(parameters)

        # Ensure last message is operator
        assert messages[-1].role == "operator"

        input_data = InputData(
            messages=messages,
            target_message_index=len(messages) - 1  # Format-specific field
        )

        # Generate corrected version based on policies
        expected_output = self._generate_correction(messages[-1].content, policies)

        return DatasetExample(
            id=self._generate_id(),
            case="operator_quality",
            format="dialog_last_turn_correction",
            use_case_id=use_case_id,
            test_case_id=test_case_id,
            input=input_data,
            expected_output=expected_output,
            evaluation_criteria=self._generate_criteria(parameters),
            policy_ids=[p.id for p in policies],
            metadata={}
        )

    def validate_format(self, example: DatasetExample) -> list[str]:
        """Validate dialog_last_turn_correction requirements."""
        errors = []

        # tz.md requirement: target_message_index must exist
        if not hasattr(example.input, 'target_message_index'):
            errors.append("Missing target_message_index for dialog_last_turn_correction")

        # tz.md requirement: must point to last operator message
        if example.input.messages:
            if example.input.target_message_index != len(example.input.messages) - 1:
                errors.append("target_message_index must point to last message")

            if example.input.messages[-1].role != "operator":
                errors.append("Last message must have role=operator")

        # tz.md requirement: minimum 2 messages
        if len(example.input.messages) < 2:
            errors.append("dialog_last_turn_correction requires minimum 2 messages")

        return errors
```

### Anti-Patterns to Avoid

- **Hardcoded case routing:** `if filename == "support": case = "support_bot"` — violates universality requirement
- **Single-format assumption:** Generating only one format per document — operator docs need BOTH correction formats
- **Sequential error generation:** One error type per example — tz.md requires mixed parameter variations
- **Filename-based classification:** Using input path to determine case/format — must work with renamed files

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pairwise combinatorial generation | Custom combination logic | allpairspy library | Pairwise testing is mathematically proven to cover most defects with minimal cases; custom logic often misses edge interactions |
| Case/format enum validation | String parsing + manual checks | OpenAI structured outputs with Pydantic Literal types | Structured outputs guarantee only valid enum values; manual validation requires extensive error handling |
| Dialog message role validation | Custom validators | Pydantic field_validator with Literal["user", "operator", "assistant", "system"] | Type system enforces valid roles at parse time; custom checks happen after invalid data enters system |
| Evidence quote validation | New matching algorithm | Existing fuzzy_matcher.py from Phase 2 | Already battle-tested with 90%+ threshold; rewriting risks introducing new bugs |

**Key insight:** OpenAI structured outputs with Pydantic v2 provide guaranteed schema compliance. Attempting to validate LLM outputs manually creates hundreds of lines of error-prone validation code. The framework handles enum validation, required fields, and type coercion automatically.

## Common Pitfalls

### Pitfall 1: Discriminated Union Incompatibility with OpenAI Structured Outputs

**What goes wrong:** Using Pydantic discriminated unions with OpenAI structured outputs causes "objects provided via 'anyOf' must not share identical first keys" errors.

**Why it happens:** OpenAI's Context Free Grammar constraint model needs to identify union subtypes from the first field, creating conflicts with standard discriminated union patterns.

**How to avoid:**
- Use separate detection calls rather than union types for case/format classification
- If unions needed, ensure discriminator field is truly unique across all union members
- Consider `make_openai_compatible` adapter pattern to transform schemas before API calls

**Warning signs:** Schema validation errors mentioning "anyOf" or "first keys" when using union types.

**Source:** [OpenAI Structured Output + Pydantic fixes](https://engineering.fractional.ai/openai-structured-output-fixes), [OpenAI Community: Discriminated Unions](https://community.openai.com/t/structured-outputs-pydantic-schema/911450)

### Pitfall 2: Missing target_message_index Validation

**What goes wrong:** Generating dialog_last_turn_correction examples without target_message_index field or with incorrect index values causes validation failures.

**Why it happens:** InputData base model doesn't include target_message_index by default; format-specific fields require conditional logic.

**How to avoid:**
- Extend InputData model to include optional target_message_index field
- Add format-specific validators that enforce field presence for dialog formats
- Use tz.md canonical examples as test fixtures to catch missing fields

**Warning signs:** Official validator failures on dialog_last_turn_correction format; examples missing required fields.

### Pitfall 3: Case Detection Overfitting to Filenames

**What goes wrong:** Pipeline works on example_input_raw_support.md but fails when file is renamed or new documents provided.

**Why it happens:** Developer accidentally uses filename in detection logic instead of content-based classification.

**How to avoid:**
- Test pipeline with renamed input files during development
- Pass only document content to detection functions, never filenames
- Add integration test that renames files and verifies consistent output

**Warning signs:** Different outputs when same document is provided with different filename.

### Pitfall 4: Single-Format Generation per Document

**What goes wrong:** Operator quality document generates only single_utterance_correction OR dialog_last_turn_correction, not both.

**Why it happens:** Assuming one document → one format rather than detecting ALL applicable formats.

**How to avoid:**
- Detection function returns list[format] not single format
- Generation loop iterates over all detected formats
- Coverage enforcement checks that operator_quality case has both correction formats

**Warning signs:** Missing formats in dataset.json; official validator failing format coverage requirements.

### Pitfall 5: Sequential Parameter Variation (One Error at a Time)

**What goes wrong:** Operator quality examples have one error type per example rather than mixed variations.

**Why it happens:** Generating examples with single-axis variation instead of combinatorial parameter sets.

**How to avoid:**
- Use pairwise testing to combine multiple variation axes
- Generate test cases with parameter dictionaries containing multiple non-default values
- Verify tz.md variation axes (punctuation + slang + aggression in same example)

**Warning signs:** Dataset examples feel repetitive; each example tests only one dimension.

### Pitfall 6: Insufficient metadata.source Coverage

**What goes wrong:** Support bot dataset has only "tickets" source type, missing faq_paraphrase and corner.

**Why it happens:** Not tracking source type distribution during generation; relying on frameworks that don't produce all types.

**How to avoid:**
- Track metadata.source counts during generation
- Add coverage enforcement that requires all 3 types for support_bot
- Generate corner cases explicitly rather than hoping frameworks produce them

**Warning signs:** Official validator fails with "missing source types"; dataset lacks adversarial examples.

## Code Examples

Verified patterns from official sources and tz.md:

### Auto-Detection with Structured Outputs
```python
# Source: OpenAI Structured Outputs documentation
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Literal

class CaseDetection(BaseModel):
    case: Literal["support_bot", "operator_quality", "doctor_booking"]
    reasoning: str

def detect_case(use_case_description: str) -> str:
    """Auto-detect case field using structured outputs."""
    client = OpenAI()

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Classify the use case domain."},
            {"role": "user", "content": f"Use case: {use_case_description}"}
        ],
        response_format=CaseDetection,
        temperature=0,
    )

    return completion.choices[0].message.parsed.case
```

### Format-Specific InputData Extension
```python
# Source: tz.md data contract requirements
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class InputData(BaseModel):
    """Input data with optional format-specific fields."""
    messages: list[Message] = Field(min_length=1)
    target_message_index: Optional[int] = Field(
        default=None,
        description="For dialog_last_turn_correction: index of operator message to correct"
    )

    @field_validator("target_message_index")
    @classmethod
    def validate_target_index(cls, v, info):
        """Validate target_message_index points to operator message."""
        if v is not None:
            messages = info.data.get('messages', [])
            if v >= len(messages):
                raise ValueError("target_message_index out of range")
            if messages[v].role != "operator":
                raise ValueError("target_message_index must point to operator message")
        return v
```

### Pairwise Test Case Generation
```python
# Source: allpairspy library usage patterns
from allpairspy import AllPairs

def generate_test_case_variations(use_case: UseCase) -> list[dict]:
    """Generate parameter combinations using pairwise testing."""
    # Define variation axes based on case
    if use_case.case == "support_bot":
        axes = {
            "tone": ["neutral", "negative", "aggressive"],
            "has_order_id": [True, False],
            "requires_account_access": [True, False],
            "language": ["ru", "en"]
        }
    elif use_case.case == "operator_quality":
        axes = {
            "phrase_length": ["short", "medium", "long"],
            "punctuation_errors": ["none", "minor", "severe"],
            "user_aggression": ["neutral", "frustrated", "angry"],
            "escalation_needed": [True, False]
        }
    else:
        axes = {}

    # Generate pairwise combinations
    combinations = []
    for combo in AllPairs(list(axes.values())):
        param_dict = {k: v for k, v in zip(axes.keys(), combo)}
        combinations.append(param_dict)

    return combinations
```

### Coverage Enforcement for Multiple Formats
```python
# Source: Phase 4 requirements for operator_quality case
def enforce_format_coverage(
    examples: list[DatasetExample],
    case: str
) -> list[str]:
    """Ensure all required formats are present."""
    warnings = []

    if case == "operator_quality":
        formats = {ex.format for ex in examples}
        required = {"single_utterance_correction", "dialog_last_turn_correction"}

        missing = required - formats
        if missing:
            warnings.append(
                f"operator_quality case missing formats: {missing}"
            )

    return warnings
```

### Source Type Distribution Tracking
```python
# Source: tz.md support_bot requirements
def enforce_source_coverage(
    examples: list[DatasetExample],
    case: str
) -> list[str]:
    """Ensure all required metadata.source types are present."""
    warnings = []

    if case == "support_bot":
        sources = {ex.metadata.get("source") for ex in examples}
        required = {"tickets", "faq_paraphrase", "corner"}

        missing = required - sources
        if missing:
            warnings.append(
                f"support_bot case missing source types: {missing}"
            )

    return warnings
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual JSON validation | OpenAI Structured Outputs | August 2024 | Guaranteed schema compliance; no hallucinated enum values |
| Filename-based routing | LLM content classification | 2025 trend | Universal pipelines work on any input; no hardcoded mappings |
| Full combinatorial testing | Pairwise testing (allpairspy) | Established practice | Reduces test cases from exponential to quadratic growth |
| String-based enum validation | Pydantic v2 Literal types | Pydantic v2 release | Type safety at parse time; IDE autocomplete support |

**Deprecated/outdated:**
- OpenAI function calling without strict mode — use structured outputs instead for guaranteed schema compliance
- Manual enum validation with if/else chains — Pydantic Literal types enforce at parse time
- Generating all parameter combinations — pairwise testing covers 90%+ of defects with far fewer cases

## Open Questions

1. **How to handle doctor_booking case value and format?**
   - What we know: tz.md says it's an optional "усложнённый пример" with no committed output required
   - What's unclear: Should it use support_bot format (single_turn_qa) or a new format?
   - Recommendation: Detect as separate case="doctor_booking", use format="single_turn_qa" similar to support_bot. Generate but don't commit to out/ directory.

2. **Should variation axes be case-specific or use case-specific?**
   - What we know: tz.md lists specific axes for operator quality; support bot implied from ticket examples
   - What's unclear: Whether each use case should define its own axes or inherit from case defaults
   - Recommendation: Define default axes per case (support_bot, operator_quality), then allow use case-specific overrides via policy analysis. Use LLM to extract relevant axes from use case description.

3. **How to ensure mixed error generation for operator corrections?**
   - What we know: tz.md requires mixed errors (not one-at-a-time); driven by test case parameter combinations
   - What's unclear: Exact prompt strategy to ensure multiple error types in single example
   - Recommendation: Pass test case parameter dictionary directly to generation prompt; instruct LLM to include ALL non-default parameter values in the example. Validate generated examples have multiple error types.

## Sources

### Primary (HIGH confidence)
- [OpenAI Structured Outputs Documentation](https://platform.openai.com/docs/guides/structured-outputs) - Core API for case/format auto-detection
- tz.md (local file) - Data contract, canonical examples, variation axes, acceptance criteria
- pyproject.toml (local) - Current dependencies and version constraints
- Phase 3 implementation (local) - Existing pipeline architecture to extend

### Secondary (MEDIUM confidence)
- [Engineering.Fractional.ai: OpenAI Structured Output Fixes](https://engineering.fractional.ai/openai-structured-output-fixes) - Discriminated union workarounds
- [OpenAI Community: Structured Outputs Pydantic Schema](https://community.openai.com/t/structured-outputs-pydantic-schema/911450) - Enum validation patterns
- [allpairspy GitHub](https://github.com/thombashi/allpairspy) - Pairwise combinatorial testing implementation
- [SDialog Toolkit](https://arxiv.org/abs/2512.09142) - Dialog format standards and quality evaluation criteria
- [Evidently Synthetic Data Generator](https://www.evidentlyai.com/blog/synthetic-data-generator-python) - Synthetic data generation patterns for LLMs

### Tertiary (LOW confidence - for context only)
- [LLM Metadata Classification at Grab](https://engineering.grab.com/llm-powered-data-classification) - Source type classification approaches
- [Confident AI: Synthetic Data Generation Guide](https://www.confident-ai.com/blog/the-definitive-guide-to-synthetic-data-generation-using-llms) - General synthetic data patterns
- [Langfuse Synthetic Datasets](https://langfuse.com/guides/cookbook/example_synthetic_datasets) - Dataset generation workflows

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - OpenAI structured outputs and Pydantic v2 are proven, stable technologies
- Architecture: HIGH - Patterns verified against tz.md requirements and Phase 3 implementation
- Pitfalls: MEDIUM - Based on community reports and documentation, not personal experience with exact combination

**Research date:** 2026-02-16
**Valid until:** 2026-03-16 (30 days - stable domain with established tools)
