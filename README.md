# Synthetic Dataset Generator for LLM Agent Testing

A pipeline that transforms raw markdown business requirements into validated synthetic test datasets with full traceability. Designed for evaluating LLM-based agents across customer support, operator quality control, and appointment booking use cases.

## Features

- Extract use cases and policies from unstructured markdown documents
- Generate test cases with parameter variations using pairwise combinatorial testing
- Produce evaluation-ready dataset examples in multiple formats
- Multi-format support: `single_turn_qa`, `single_utterance_correction`, `dialog_last_turn_correction`
- Auto-detect case type: `support_bot`, `operator_quality`, `doctor_booking`
- Built-in validation with referential integrity checks
- Optional Langfuse integration for dataset upload and experiment tracking
- Evidence traceability with line-number references back to source document
- Quality reporting with Evidently for duplicate detection and data profiling

## Quick Start

```bash
# Clone and navigate to project
cd vibe-coding-test

# Install dependencies
pip install -e .

# Set your OpenAI API key
export OPENAI_API_KEY=sk-proj-...

# Generate a dataset from markdown requirements
python -m dataset_generator generate \
  --input example_input_raw_support_faq_and_tickets.md \
  --out out/my_dataset \
  --seed 42

# Validate the generated artifacts
python -m dataset_generator validate --out out/my_dataset
```

## Installation

**Basic installation:**
```bash
pip install -e .
```

**With optional Langfuse support:**
```bash
pip install -e ".[langfuse]"
```

## Environment Variables

### Required

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for LLM generation | `sk-proj-...` |

### Optional (Langfuse Integration)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `LANGFUSE_PUBLIC_KEY` | No | Langfuse public API key | `pk-lf-...` |
| `LANGFUSE_SECRET_KEY` | No | Langfuse secret API key | `sk-lf-...` |
| `LANGFUSE_HOST` | No | Custom Langfuse instance URL | `https://cloud.langfuse.com` |

**Example `.env` file:**
```bash
# Required
OPENAI_API_KEY=sk-proj-...

# Optional: Langfuse Integration
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

## Usage

### Generate

Generate a synthetic dataset from a markdown requirements document:

```bash
python -m dataset_generator generate \
  --input <file.md> \
  --out <output_dir> \
  [--seed 42] \
  [--model gpt-4o-mini] \
  [--n-use-cases 5] \
  [--n-test-cases-per-uc 3] \
  [--n-examples-per-tc 1]
```

**Parameters:**

- `--input`: Path to input markdown file (required)
- `--out`: Output directory for generated artifacts (default: `./out`)
- `--seed`: Random seed for reproducible generation (optional)
- `--model`: OpenAI model name (default: `gpt-4o-mini`)
- `--n-use-cases`: Minimum number of use cases to extract (default: 5)
- `--n-test-cases-per-uc`: Number of test cases per use case (default: 3)
- `--n-examples-per-tc`: Number of dataset examples per test case (default: 1)

**Example:**
```bash
python -m dataset_generator generate \
  --input example_input_raw_support_faq_and_tickets.md \
  --out out/support \
  --seed 42 \
  --model gpt-4o-mini
```

**Output files:**
- `use_cases.json` - Extracted use cases with evidence
- `policies.json` - Extracted policies with types and evidence
- `test_cases.json` - Generated test cases with parameter variations
- `dataset.json` - Evaluation-ready dataset examples
- `run_manifest.json` - Run metadata and configuration
- `quality_report.html` - Data quality analysis (if Evidently succeeds)

### Validate

Validate generated dataset files for schema compliance and referential integrity:

```bash
python -m dataset_generator validate --out <output_dir>
```

**Checks performed:**
- All required JSON files exist (use_cases, policies, test_cases, dataset, run_manifest)
- Schema compliance via Pydantic models
- Referential integrity: test case IDs, use case IDs, policy IDs are valid references
- Policy ID references point to actual loaded policies

**Exit codes:**
- `0` - All validation checks passed
- `1` - Validation errors found

**Note:** Evidence quote mismatches generate warnings but do not fail validation.

**Example:**
```bash
python -m dataset_generator validate --out out/support
```

### Upload to Langfuse

Upload a generated dataset to Langfuse for experiment tracking:

```bash
python -m dataset_generator upload \
  --out <output_dir> \
  --dataset-name <name> \
  [--langfuse-host <url>]
```

**Parameters:**

- `--out`: Output directory containing `dataset.json` (required)
- `--dataset-name`: Name for the Langfuse dataset (required)
- `--langfuse-host`: Custom Langfuse host URL (optional, defaults to `LANGFUSE_HOST` env var)

**Requirements:**
- `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` must be set in environment
- Install with `pip install -e ".[langfuse]"` to enable this command

**Example:**
```bash
python -m dataset_generator upload \
  --out out/support \
  --dataset-name "support-bot-v1" \
  --langfuse-host https://cloud.langfuse.com
```

## Pre-generated Artifacts

This repository includes pre-generated datasets for two use cases, ready for immediate exploration:

### `out/support/`
Support bot dataset for FAQ and ticket-based customer support.
- 60 dataset examples
- 5 use cases
- 5 policies
- Format: `single_turn_qa`

### `out/operator_quality/`
Operator quality dataset for message correction and quality control.
- 84 dataset examples
- 7 use cases
- 7 policies
- Format: `single_utterance_correction`

**Files in each directory:**
- `use_cases.json` - Extracted use cases
- `policies.json` - Extracted policies
- `test_cases.json` - Generated test cases
- `dataset.json` - Evaluation-ready examples
- `run_manifest.json` - Run metadata
- `quality_report.html` - Data quality analysis

**Validate pre-generated artifacts:**
```bash
python -m dataset_generator validate --out out/support
python -m dataset_generator validate --out out/operator_quality
```

## Supported Use Cases

### Support Bot (`support_bot`)
Customer support scenarios with FAQ and ticket-based interactions. Generates single-turn question-answer pairs for evaluating support agent responses.

### Operator Quality (`operator_quality`)
Message correction for customer service operators. Generates utterance correction examples where the system suggests improvements to operator messages.

### Doctor Booking (`doctor_booking`)
Medical appointment booking scenarios. Generates dialog examples for scheduling appointments with slot selection and confirmation flows.

## Architecture

The pipeline follows a four-stage extraction and generation process:

1. **Markdown Parsing** - Extract raw text with line numbers for evidence tracing
2. **Use Case Extraction** - LLM-powered extraction of business scenarios from markdown
3. **Policy Extraction** - Extract business rules and constraints, classified by type
4. **Test Case Generation** - Generate parameter variations using pairwise combinatorial testing
5. **Dataset Example Generation** - Produce format-specific examples via adapters and optional framework integration

**Traceability:**
- Evidence quotes include line number ranges from source markdown
- ID references: `uc_*` (use cases) -> `tc_*` (test cases) -> `ex_*` (examples)
- Policy references: test cases link to relevant policies via `policy_ids`

**Framework integration:**
- DeepEval, Ragas, and Giskard can supplement dataset generation
- Fallback to direct OpenAI function calling if frameworks fail
- Framework selection based on case type and format

## Dependencies

**Python version:** >= 3.10

**Core libraries:**
- `pydantic` >= 2.0 - Data validation and schema enforcement
- `openai` >= 1.0 - LLM API for generation
- `typer` >= 0.12 - CLI framework
- `python-dotenv` >= 1.0 - Environment variable management
- `tenacity` >= 8.0 - Retry logic for API calls
- `rapidfuzz` >= 3.0 - Fuzzy string matching for evidence validation

**Generation frameworks:**
- `deepeval` >= 3.0 - Synthetic test generation
- `ragas` >= 0.4 - RAG evaluation dataset generation
- `giskard[llm]` >= 2.0 - LLM test generation
- `langchain` >= 0.2 - Framework integration
- `chromadb` >= 1.0 - Vector storage for DeepEval

**Quality and utilities:**
- `evidently` >= 0.4 - Data quality reporting
- `pandas` >= 2.0 - Data manipulation
- `allpairspy` - Pairwise combinatorial testing

**Optional:**
- `langfuse` >= 2.0 - Dataset upload and experiment tracking (install with `pip install -e ".[langfuse]"`)
