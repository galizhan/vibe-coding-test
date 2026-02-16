# Phase 1: Foundation - Research

**Researched:** 2026-02-16
**Domain:** Python CLI tool for LLM-based structured extraction with evidence traceability
**Confidence:** MEDIUM

## Summary

Phase 1 requires building a Python CLI tool that uses OpenAI's LLM API to extract structured use cases and policies from markdown documents, with strict evidence traceability (line numbers + exact quotes) and Pydantic-based validation. The core technical challenge is implementing reliable evidence extraction where quotes must exactly match source text at specified line ranges, combined with LLM-driven structured output generation.

The standard stack is Python 3.10+ with Pydantic v2 for data validation, OpenAI Python SDK for structured outputs, and either Click or Typer for CLI. The architecture follows src-layout pattern with clear separation between CLI interface, extraction logic, and data contracts. Evidence quoting has no established library support and must be implemented custom, while Russian language extraction quality with gpt-4o-mini is unvalidated and may require fallback to gpt-4o.

**Primary recommendation:** Use Typer for CLI (modern, type-hint-driven), Pydantic v2 BaseModel with field validators for data contracts, OpenAI structured outputs API with Pydantic integration for extraction, and custom line-tracking during markdown parsing. Start with gpt-4o-mini but provide --model flag for gpt-4o fallback if Russian quality degrades.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.10+ | Runtime | Type hints, match statements, required for Pydantic v2 |
| Pydantic | 2.x | Data validation & contracts | Industry standard for Python data validation, 5-50x faster than v1, native JSON schema |
| openai | 1.x | LLM API client | Official OpenAI SDK, native Pydantic integration for structured outputs |
| Typer | 0.12+ | CLI framework | Modern, type-hint-driven, builds on Click, minimal boilerplate |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-dotenv | 1.x | Env var loading | Load OPENAI_API_KEY from .env files |
| tenacity | 8.x | Retry logic | Handle rate limits with exponential backoff |
| pathlib | stdlib | Path handling | Object-oriented path operations, cross-platform |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Typer | Click | Click is more mature and flexible, but more verbose; use if complex plugin system needed |
| Typer | argparse | argparse is stdlib (no dependency), but significantly more verbose; only if zero-dependency requirement |
| gpt-4o-mini | gpt-4o | gpt-4o has better reasoning and potentially better Russian support, but 16x more expensive ($2.50/$10 vs $0.15/$0.60 per million tokens) |

**Installation:**
```bash
python -m pip install pydantic openai typer python-dotenv tenacity
```

## Architecture Patterns

### Recommended Project Structure
```
vibe-coding-test/
├── src/
│   └── dataset_gen/           # Main package (or your chosen name)
│       ├── __init__.py
│       ├── __main__.py        # Entry point for `python -m dataset_gen`
│       ├── cli.py             # Typer app and commands
│       ├── models/            # Pydantic data models
│       │   ├── __init__.py
│       │   ├── use_case.py    # UseCase, Evidence models
│       │   ├── policy.py      # Policy model
│       │   ├── test_case.py   # TestCase model
│       │   └── dataset.py     # DatasetExample model
│       ├── extraction/        # LLM extraction logic
│       │   ├── __init__.py
│       │   ├── markdown_parser.py  # Line-tracking markdown reader
│       │   ├── use_case_extractor.py
│       │   └── policy_extractor.py
│       └── validation/        # Evidence validation
│           ├── __init__.py
│           └── evidence_validator.py
├── tests/
│   └── ...
├── example_input_raw_support_faq_and_tickets.md
├── example_input_raw_operator_quality_checks.md
├── example_input_raw_doctor_booking.md
├── pyproject.toml
├── README.md
└── .env.example
```

**Why src-layout:** Prevents accidental import of in-development code, enforces proper installation, standard for distributable tools.

### Pattern 1: CLI Entry Point with Typer
**What:** Type-hint-driven command definition with automatic validation
**When to use:** All CLI commands; Typer converts type hints to CLI arguments
**Example:**
```python
# cli.py
import typer
from pathlib import Path

app = typer.Typer()

@app.command()
def extract(
    input: Path = typer.Option(..., "--input", help="Input markdown file"),
    out: Path = typer.Option("./out", "--out", help="Output directory"),
    seed: int = typer.Option(None, "--seed", help="Random seed for reproducibility"),
    n_use_cases: int = typer.Option(5, "--n-use-cases", help="Minimum use cases"),
    model: str = typer.Option("gpt-4o-mini", "--model", help="OpenAI model name"),
):
    """Extract use cases and policies from markdown requirements."""
    # Implementation here
    pass

# __main__.py
from .cli import app

if __name__ == "__main__":
    app()
```

### Pattern 2: Pydantic Models with Custom Validators
**What:** BaseModel with field validators for ID prefixes and evidence validation
**When to use:** All data contracts (use cases, policies, test cases, dataset)
**Example:**
```python
# models/use_case.py
from pydantic import BaseModel, field_validator
from typing import Literal

class Evidence(BaseModel):
    input_file: str
    line_start: int  # 1-based
    line_end: int    # 1-based, >= line_start
    quote: str

    @field_validator('line_end')
    @classmethod
    def line_end_must_be_gte_start(cls, v, info):
        if 'line_start' in info.data and v < info.data['line_start']:
            raise ValueError('line_end must be >= line_start')
        return v

class UseCase(BaseModel):
    id: str
    case: Literal["support_bot", "operator_quality"]
    name: str
    description: str
    evidence: list[Evidence]

    @field_validator('id')
    @classmethod
    def id_must_have_uc_prefix(cls, v):
        if not v.startswith('uc_'):
            raise ValueError('use_case_id must start with uc_')
        return v

    @field_validator('evidence')
    @classmethod
    def must_have_at_least_one_evidence(cls, v):
        if len(v) < 1:
            raise ValueError('must have at least one evidence')
        return v
```

### Pattern 3: OpenAI Structured Outputs with Pydantic
**What:** Use response_format parameter with Pydantic models for guaranteed JSON structure
**When to use:** All LLM extraction calls that need structured JSON
**Example:**
```python
# extraction/use_case_extractor.py
from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()  # Reads OPENAI_API_KEY from env

class UseCaseList(BaseModel):
    use_cases: list[UseCase]

def extract_use_cases(markdown_text: str, model: str = "gpt-4o-mini", seed: int = None) -> UseCaseList:
    response = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": "Extract use cases from requirements document..."},
            {"role": "user", "content": markdown_text}
        ],
        response_format=UseCaseList,
        temperature=0,
        seed=seed,
    )
    return response.choices[0].message.parsed
```

### Pattern 4: Line-Tracking Markdown Parser
**What:** Read markdown file with line number tracking for evidence extraction
**When to use:** Initial file load; maintain line metadata for all text spans
**Example:**
```python
# extraction/markdown_parser.py
from pathlib import Path
from dataclasses import dataclass

@dataclass
class LineSpan:
    text: str
    line_start: int  # 1-based
    line_end: int    # 1-based

def parse_markdown_with_lines(file_path: Path) -> tuple[str, list[str]]:
    """
    Returns: (full_text, lines_list)
    lines_list is 0-indexed for programming, but evidence uses 1-based indexing
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Normalize line endings
    lines = [line.rstrip('\r\n') for line in lines]
    full_text = '\n'.join(lines)

    return full_text, lines

def validate_evidence_quote(lines: list[str], evidence: Evidence) -> bool:
    """
    Validate that evidence.quote exactly matches lines[line_start-1:line_end]
    """
    start_idx = evidence.line_start - 1  # Convert to 0-based
    end_idx = evidence.line_end  # line_end is inclusive, but slice is exclusive

    actual_text = '\n'.join(lines[start_idx:end_idx])
    return actual_text == evidence.quote
```

### Pattern 5: Retry Logic for Rate Limits
**What:** Exponential backoff for OpenAI API rate limit errors
**When to use:** Wrap all OpenAI API calls
**Example:**
```python
from tenacity import retry, stop_after_attempt, wait_random_exponential
from openai import RateLimitError

@retry(
    wait=wait_random_exponential(min=1, max=60),
    stop=stop_after_attempt(6),
    retry=retry_if_exception_type(RateLimitError)
)
def call_openai_with_retry(client, **kwargs):
    return client.beta.chat.completions.parse(**kwargs)
```

### Pattern 6: File Output with Pydantic
**What:** Serialize Pydantic models to JSON files with proper formatting
**When to use:** Writing all output JSON files
**Example:**
```python
from pathlib import Path
from pydantic import BaseModel

def write_json_output(model: BaseModel, output_path: Path):
    """Write Pydantic model to JSON file with indent."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(model.model_dump_json(indent=2, exclude_none=True))
```

### Anti-Patterns to Avoid

- **Hardcoding filenames:** Anti-hardcoding requirement means solution must work with renamed files and different directories
- **Using .json() method:** Deprecated in Pydantic v2, use model_dump_json() instead
- **Using .dict() method:** Deprecated in Pydantic v2, use model_dump() instead
- **String path manipulation:** Use pathlib.Path instead of os.path string operations for cross-platform compatibility
- **Ignoring rate limits:** Always implement retry logic with exponential backoff for OpenAI API calls
- **Assuming determinism:** Even with seed + temperature=0, OpenAI outputs are mostly but not completely deterministic; don't rely on byte-identical outputs

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CLI argument parsing | Manual sys.argv parsing, custom arg validators | Typer (or Click) | Type conversion, validation, help generation, error messages all handled automatically |
| Data validation | Manual dict checking, isinstance chains, custom validators | Pydantic v2 BaseModel | Handles type coercion, nested validation, JSON schema generation, 5-50x faster than v1 |
| Retry logic | Manual sleep + loop with counters | tenacity library | Handles exponential backoff, max attempts, exception filtering, jitter for thundering herd |
| JSON serialization | json.dumps with custom encoders | Pydantic model_dump_json() | Handles nested models, datetime, enums automatically; fast Rust-based serializer |
| Path joining | String concatenation, os.path.join | pathlib.Path / operator | Cross-platform, prevents double slashes, type-safe, chainable operations |

**Key insight:** LLM structured extraction combines well-solved problems (CLI, validation, serialization) with novel problems (evidence quoting, line tracking). Use mature libraries for solved problems to focus effort on novel extraction logic.

## Common Pitfalls

### Pitfall 1: Evidence Quote Mismatch
**What goes wrong:** LLM hallucinates quotes that don't exist in source, or line numbers don't match actual text location
**Why it happens:** LLMs don't have access to original line numbers; they see only concatenated text. When asked to provide line numbers + quotes, they estimate or invent.
**How to avoid:**
1. Two-phase extraction: first extract concepts without evidence, then separately prompt for evidence with line-numbered source
2. Post-extraction validation: verify every evidence.quote exactly matches lines[line_start:line_end] from source
3. If validation fails, retry extraction or discard invalid evidence
**Warning signs:** Evidence validation failures during testing, quotes with minor variations from source text

### Pitfall 2: Russian Language Quality Degradation
**What goes wrong:** gpt-4o-mini produces lower-quality extractions for Russian text (poor paraphrasing, incorrect use case identification, unnatural language in generated content)
**Why it happens:** GPT-4o-mini is optimized for cost/speed over quality; Russian is lower-resource than English in training data
**How to avoid:**
1. Implement --model flag to allow switching to gpt-4o
2. Test with actual Russian example files early
3. Consider hybrid approach: use gpt-4o-mini for initial extraction, gpt-4o for validation/refinement
**Warning signs:** Extracted use cases don't match human understanding, generated Russian content sounds unnatural, policies miss nuances

### Pitfall 3: LLM Hallucination on Required Fields
**What goes wrong:** When schema marks field as required but information isn't in source, LLM invents data to satisfy schema
**Why it happens:** Structured output API enforces schema compliance; LLM will hallucinate rather than fail
**How to avoid:**
1. Make fields optional where appropriate (e.g., `description: str | None`)
2. Use separate validation pass to check if required info exists before extraction
3. Provide explicit prompt instruction: "If information is not present, use placeholder 'NOT_FOUND' rather than inventing"
**Warning signs:** Generated IDs that don't follow pattern, policies extracted from FAQ questions rather than constraints, test cases with parameters not mentioned in requirements

### Pitfall 4: Line Ending Normalization Failure
**What goes wrong:** Evidence validation fails because source file has CRLF line endings but validation expects LF, or vice versa
**Why it happens:** Windows uses \r\n, Unix uses \n; text comparison fails if not normalized
**How to avoid:**
1. Normalize all line endings to \n when reading files: `line.rstrip('\r\n')`
2. Document that evidence.quote must use \n line endings
3. Validation logic should normalize before comparing
**Warning signs:** Evidence validation fails on Windows but passes on Mac/Linux, quote text matches visually but comparison returns False

### Pitfall 5: Seed Reproducibility Misconception
**What goes wrong:** Developers expect identical outputs with same seed, but outputs vary slightly
**Why it happens:** OpenAI seed + temperature=0 provides "mostly deterministic" results, not perfect determinism; infrastructure changes affect outputs
**How to avoid:**
1. Document that seed provides consistency, not identity
2. Check system_fingerprint in response; outputs should match if fingerprint matches
3. Use structural validation (same use case count, same ID patterns) rather than byte-identical comparison
**Warning signs:** Tests fail intermittently despite same seed, generated content varies slightly between runs

### Pitfall 6: Over-Complex JSON Schema
**What goes wrong:** Pydantic model with many optional fields, nested structures, and union types produces inconsistent LLM extractions
**Why it happens:** Complex schemas increase LLM uncertainty about which fields to populate; optional field explosion leads to sparse, inconsistent outputs
**How to avoid:**
1. Start minimal: only required fields in initial models
2. Avoid deeply nested structures in extraction (max 2-3 levels)
3. Prefer Literal types over string enums for constrained fields
4. Split complex extractions into multiple simpler prompts
**Warning signs:** Some extractions have rich detail, others minimal; LLM populates different optional fields in different runs

### Pitfall 7: No Rate Limit Handling
**What goes wrong:** Script fails with RateLimitError during bulk extraction, especially when iterating over multiple test cases
**Why it happens:** OpenAI enforces RPM (requests per minute) and TPM (tokens per minute) limits; rapid sequential calls exceed limits
**How to avoid:**
1. Always wrap OpenAI calls with tenacity retry decorator
2. Use exponential backoff with jitter: wait_random_exponential(min=1, max=60)
3. Monitor rate limit headers: x-ratelimit-remaining-requests, x-ratelimit-reset-requests
4. For bulk operations, consider batching or rate limiting on client side
**Warning signs:** Script fails midway through large input, 429 errors in logs, inconsistent failures that succeed on retry

## Code Examples

Verified patterns from official sources:

### Complete CLI Setup (Typer)
```python
# __main__.py
from .cli import app

if __name__ == "__main__":
    app()

# cli.py
import typer
from pathlib import Path
import os

app = typer.Typer(help="Generate synthetic datasets from requirements documents")

@app.command()
def extract(
    input: Path = typer.Option(..., "--input", exists=True, file_okay=True, dir_okay=False),
    out: Path = typer.Option(Path("./out"), "--out"),
    seed: int = typer.Option(None, "--seed"),
    n_use_cases: int = typer.Option(5, "--n-use-cases", min=1),
    model: str = typer.Option("gpt-4o-mini", "--model"),
):
    """Extract use cases, policies, test cases, and generate dataset."""

    # Validate API key
    if not os.getenv("OPENAI_API_KEY"):
        typer.echo("Error: OPENAI_API_KEY environment variable not set", err=True)
        raise typer.Exit(code=1)

    # Ensure output directory exists
    out.mkdir(parents=True, exist_ok=True)

    typer.echo(f"Processing: {input}")
    typer.echo(f"Output directory: {out}")
    typer.echo(f"Model: {model}")
    if seed:
        typer.echo(f"Seed: {seed}")

    # Call extraction logic here
    # ...

    typer.echo("✓ Extraction complete")

if __name__ == "__main__":
    app()
```

### Pydantic Model with Validators
```python
# models/use_case.py
from pydantic import BaseModel, field_validator, model_validator
from typing import Literal

class Evidence(BaseModel):
    input_file: str
    line_start: int
    line_end: int
    quote: str

    @field_validator('line_start', 'line_end')
    @classmethod
    def must_be_positive(cls, v):
        if v < 1:
            raise ValueError('line numbers must be >= 1 (1-based indexing)')
        return v

    @model_validator(mode='after')
    def line_end_gte_start(self):
        if self.line_end < self.line_start:
            raise ValueError(f'line_end ({self.line_end}) must be >= line_start ({self.line_start})')
        return self

class UseCase(BaseModel):
    id: str
    case: Literal["support_bot", "operator_quality"]
    name: str
    description: str
    evidence: list[Evidence]

    @field_validator('id')
    @classmethod
    def must_have_uc_prefix(cls, v):
        if not v.startswith('uc_'):
            raise ValueError(f'use_case id must start with uc_, got: {v}')
        return v

    @field_validator('evidence')
    @classmethod
    def must_have_evidence(cls, v):
        if len(v) < 1:
            raise ValueError('use case must have at least one evidence')
        return v

class UseCaseList(BaseModel):
    """Wrapper for list of use cases (for JSON file output)."""
    use_cases: list[UseCase]
```

### OpenAI Structured Output with Error Handling
```python
# extraction/use_case_extractor.py
from openai import OpenAI, RateLimitError
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception_type
from .models.use_case import UseCaseList

client = OpenAI()  # Reads OPENAI_API_KEY from environment

@retry(
    wait=wait_random_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(6),
    retry=retry_if_exception_type(RateLimitError)
)
def extract_use_cases(
    markdown_text: str,
    model: str = "gpt-4o-mini",
    seed: int | None = None,
    min_use_cases: int = 5,
) -> UseCaseList:
    """Extract use cases from markdown requirements with structured output."""

    system_prompt = f"""You are an expert at analyzing business requirements documents.
Extract structured use cases from the provided markdown document.

REQUIREMENTS:
- Extract at least {min_use_cases} use cases
- Each use case must have evidence (quote + line numbers) from the source
- All content must be in Russian
- IDs must start with 'uc_' and be unique
- Quotes must be exact text from the source (1-5 lines each)

OUTPUT:
Return a JSON object with a 'use_cases' array containing:
- id: string starting with 'uc_'
- case: either 'support_bot' or 'operator_quality'
- name: short name for the use case
- description: detailed description
- evidence: array of at least one evidence object with:
  - input_file: filename (extract from context if available)
  - line_start: 1-based line number where evidence starts
  - line_end: 1-based line number where evidence ends (>= line_start)
  - quote: exact text from those lines
"""

    params = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": markdown_text}
        ],
        "response_format": UseCaseList,
        "temperature": 0,
    }

    if seed is not None:
        params["seed"] = seed

    response = client.beta.chat.completions.parse(**params)

    # Log system_fingerprint for reproducibility tracking
    print(f"system_fingerprint: {response.system_fingerprint}")

    return response.choices[0].message.parsed
```

### Line-Tracking Parser with Validation
```python
# extraction/markdown_parser.py
from pathlib import Path
from typing import NamedTuple

class ParsedMarkdown(NamedTuple):
    full_text: str
    lines: list[str]  # 0-indexed for Python, but evidence uses 1-based
    file_path: Path

def parse_markdown_with_lines(file_path: Path) -> ParsedMarkdown:
    """
    Parse markdown file and track line numbers for evidence validation.

    Returns:
        ParsedMarkdown with normalized line endings (LF only)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_lines = f.readlines()

    # Normalize line endings: strip \r\n or \n, store as LF-joined
    lines = [line.rstrip('\r\n') for line in raw_lines]
    full_text = '\n'.join(lines)

    return ParsedMarkdown(full_text=full_text, lines=lines, file_path=file_path)

def validate_evidence_quote(parsed: ParsedMarkdown, evidence) -> tuple[bool, str]:
    """
    Validate that evidence.quote exactly matches source lines.

    Returns:
        (is_valid, error_message)
    """
    # Convert 1-based to 0-based indexing
    start_idx = evidence.line_start - 1
    end_idx = evidence.line_end  # Python slice is exclusive at end

    if start_idx < 0 or end_idx > len(parsed.lines):
        return False, f"Line range {evidence.line_start}-{evidence.line_end} out of bounds (file has {len(parsed.lines)} lines)"

    # Extract actual text from source
    actual_lines = parsed.lines[start_idx:end_idx]
    actual_text = '\n'.join(actual_lines)

    # Normalize evidence quote (in case it came with different line endings)
    normalized_quote = evidence.quote.replace('\r\n', '\n').replace('\r', '\n')

    if actual_text == normalized_quote:
        return True, ""
    else:
        return False, f"Quote mismatch at lines {evidence.line_start}-{evidence.line_end}:\nExpected: {actual_text!r}\nGot: {normalized_quote!r}"

def validate_all_evidence(parsed: ParsedMarkdown, items_with_evidence: list) -> bool:
    """
    Validate all evidence objects from extracted items.

    Returns:
        True if all evidence is valid, False otherwise (logs errors)
    """
    all_valid = True
    for item in items_with_evidence:
        for evidence in item.evidence:
            is_valid, error_msg = validate_evidence_quote(parsed, evidence)
            if not is_valid:
                print(f"ERROR validating {item.id}: {error_msg}")
                all_valid = False
    return all_valid
```

### Writing Output Files
```python
# utils/file_writer.py
from pathlib import Path
from pydantic import BaseModel

def write_json_output(model: BaseModel, output_path: Path, indent: int = 2):
    """
    Write Pydantic model to JSON file with formatting.

    Args:
        model: Pydantic BaseModel instance
        output_path: Path where JSON will be written
        indent: JSON indentation level
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write with proper encoding and formatting
    with open(output_path, 'w', encoding='utf-8') as f:
        # Use model_dump_json (v2) not .json() (deprecated)
        json_str = model.model_dump_json(indent=indent, exclude_none=True)
        f.write(json_str)

    print(f"✓ Wrote {output_path} ({len(json_str)} bytes)")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pydantic v1 .json() / .dict() | Pydantic v2 model_dump_json() / model_dump() | Pydantic v2 release (2023) | v2 is 5-50x faster; old methods deprecated |
| JSON mode with manual parsing | Structured outputs with Pydantic | OpenAI Aug 2024 | Guaranteed schema compliance, native Pydantic integration |
| Click for CLIs | Typer for CLIs | Typer 0.3+ (2020+, mature 2023+) | Type hints eliminate boilerplate, better DX |
| os.path string operations | pathlib Path objects | Python 3.4+ (standard by 2020+) | Cross-platform, chainable, type-safe |
| Manual retry loops | tenacity library | Tenacity 8.x (mature 2023+) | Declarative, handles edge cases (jitter, backoff) |
| response_format: "json" | response_format: PydanticModel | OpenAI structured outputs API (2024) | Type-safe, validated, no manual parsing |

**Deprecated/outdated:**
- Pydantic v1 syntax (.json(), .dict(), Config class) - v2 uses model_dump_json(), model_dump(), model_config
- OpenAI JSON mode without structured outputs - replaced by beta.chat.completions.parse with response_format=Model
- argparse for new CLI tools - Typer/Click are now standard for developer experience
- String-based path manipulation - pathlib is standard library and preferred

## Open Questions

1. **Russian Language Quality with gpt-4o-mini**
   - What we know: gpt-4o-mini is 16x cheaper than gpt-4o but documented to have lower non-English performance
   - What's unclear: Whether quality degradation is acceptable for this use case (extraction vs generation)
   - Recommendation: Implement --model flag from start; test with actual Russian inputs in first sprint; be prepared to default to gpt-4o if quality issues surface

2. **Evidence Extraction Strategy**
   - What we know: No established pattern for LLM-based evidence extraction with exact line number matching
   - What's unclear: Whether one-shot extraction (use cases + evidence in single prompt) or two-phase (extract concepts, then find evidence) produces more accurate results
   - Recommendation: Start with one-shot approach (simpler); if evidence validation failure rate >20%, switch to two-phase

3. **Chunking Strategy for Large Documents**
   - What we know: gpt-4o-mini and gpt-4o support 128K context window
   - What's unclear: Whether example documents exceed practical limits, and whether chunking would hurt evidence extraction accuracy
   - Recommendation: Check example file sizes first; if <100KB, use full document; if chunking needed, overlap chunks and handle cross-chunk evidence

4. **Reproducibility Requirements**
   - What we know: OpenAI seed + temperature=0 provides "mostly" deterministic output, not perfect
   - What's unclear: How strict the reproducibility requirement is (byte-identical vs structurally identical)
   - Recommendation: Implement seed support; document limitations; use structural validation (same count, same IDs pattern) not byte comparison

## Sources

### Primary (HIGH confidence)
- [Pydantic Official Docs - Validators](https://docs.pydantic.dev/latest/concepts/validators/) - Field and model validation patterns
- [Pydantic Official Docs - Serialization](https://docs.pydantic.dev/latest/concepts/serialization/) - model_dump_json() API
- [OpenAI Official Docs - Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs) - response_format with Pydantic
- [OpenAI Official Docs - Rate Limits](https://platform.openai.com/docs/guides/rate-limits) - RPM/TPM limits and handling
- [Python Docs - pathlib](https://docs.python.org/3/library/pathlib.html) - Path API reference

### Secondary (MEDIUM confidence)
- [Real Python - Pydantic Tutorial](https://realpython.com/python-pydantic/) - Practical examples and patterns
- [Medium - Pydantic v2 Best Practices](https://medium.com/algomart/working-with-pydantic-v2-the-best-practices-i-wish-i-had-known-earlier-83da3aa4d17a) - Migration and optimization tips
- [OpenAI Cookbook - Reproducible Outputs with Seed](https://cookbook.openai.com/examples/reproducible_outputs_with_the_seed_parameter) - Seed parameter behavior and limitations
- [OpenAI Cookbook - Rate Limit Handling](https://cookbook.openai.com/examples/how_to_handle_rate_limits) - Retry patterns with tenacity
- [Python Packaging Guide - src-layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/) - Project structure rationale
- [Real Python - Project Layout Best Practices](https://realpython.com/ref/best-practices/project-layout/) - Structure recommendations

### Tertiary (LOW confidence - requires validation)
- [Medium - Python CLI Comparison](https://medium.com/@mohd_nass/navigating-the-cli-landscape-in-python-a-comparative-study-of-argparse-click-and-typer-480ebbb7172f) - argparse vs Click vs Typer comparison
- [Community - GPT-4 Russian Support](https://community.openai.com/t/do-gpt-4-support-russian-language-in-pdfs/463831) - Anecdotal reports of Russian language support
- [PyPI - markdown-to-data](https://pypi.org/project/markdown-to-data/) - Library with line tracking (needs evaluation)
- [Agenta Blog - Structured Outputs Guide](https://agenta.ai/blog/the-guide-to-structured-outputs-and-function-calling-with-llms) - Pitfalls and best practices
- [PricePerToken - GPT-4o-mini Pricing](https://pricepertoken.com/pricing-page/model/openai-gpt-4o-mini) - Cost comparison (2026 rates)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Pydantic, OpenAI SDK, Typer are all well-documented with official guides and stable APIs
- Architecture: HIGH - src-layout, Pydantic models, Typer CLI are established patterns with clear documentation
- Evidence extraction: LOW - No established pattern for LLM-based line-number-accurate evidence extraction; custom implementation required
- Russian language quality: LOW - General documentation confirms support but no specific benchmarks for extraction quality with gpt-4o-mini
- Pitfalls: MEDIUM - Rate limiting, validation, and LLM hallucination pitfalls are well-documented; evidence quote matching pitfall is project-specific

**Research date:** 2026-02-16
**Valid until:** ~2026-03-16 (30 days) for stable components (Pydantic, OpenAI SDK); shorter (7 days) for LLM model quality claims

**Key risk areas requiring early validation:**
1. Evidence extraction accuracy (no established pattern)
2. Russian language quality with gpt-4o-mini (unvalidated for this use case)
3. Quote matching implementation (custom logic, edge cases unclear)
