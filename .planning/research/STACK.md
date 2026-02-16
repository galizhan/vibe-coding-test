# Technology Stack

**Project:** Synthetic Dataset Generator for LLM Agent Testing
**Researched:** 2026-02-16
**Confidence:** HIGH

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.10+ | Runtime environment | Industry standard for AI/ML tools, excellent OpenAI SDK support, mature type hinting (3.10+), pathlib improvements. Python 3.9+ required by OpenAI SDK, but 3.10+ recommended for better type hints and pattern matching. |
| Typer | 0.23.1+ | CLI framework | Modern type-hint-driven CLI builder on top of Click. Zero boilerplate—function signatures become CLI interfaces. Built by FastAPI creator, excellent autocompletion, automatic help generation. Superior DX over raw Click for new projects. |
| Pydantic | 2.12.5+ | Data validation & contracts | Industry standard for structured data validation. 5-50x faster than v1. Native OpenAI structured output support. Perfect for enforcing ID conventions, evidence traceability, JSON schema generation. Used by FastAPI, LangChain, 466k+ repos. |

### LLM Integration

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| OpenAI Python SDK | 2.21.0+ | OpenAI API client | Official SDK with native Pydantic support for structured outputs. gpt-4o/gpt-4o-mini support with 100% schema adherence. Synchronous/async clients, comprehensive type hints. Python 3.9+ support. |

### Data & Configuration

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| pathlib | stdlib | File path operations | Modern OOP approach to paths, cross-platform by default, cleaner than os.path. Built into Python 3.4+, community consensus for new projects. |
| python-dotenv | 1.0.0+ | Environment variables | Standard for .env file management, 12-factor principles, keeps secrets out of code. Python 3.9+ support. |
| PyYAML | 6.0.2+ | YAML parsing | For markdown frontmatter or config if needed. Complete YAML 1.1 parser, Unicode support. TOML (tomllib) built into Python 3.11+ for simpler configs. |

### Output & UX

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Rich | 14.3.2+ | Terminal output | Beautiful CLI output with progress bars, tables, syntax highlighting, markup. Production-stable, no flickering progress bars, Python 3.8+. Already a Typer dependency. |
| Loguru | 0.7.3+ | Logging | Stupidly simple logging with rotation, compression, structured context. 10x faster than stdlib logging. Auto-catching decorators, thread-safe. Python 3.5+ support. |

### Testing & Quality

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| pytest | 9.0.2+ | Testing framework | Industry standard test framework. Fixtures for test data isolation, parametrize for test matrices, excellent plugin ecosystem. Python 3.10+ required. |
| pytest-asyncio | Latest | Async test support | If async/await patterns used. Official pytest plugin for async testing. |
| pytest-mock | Latest | Mocking | Thin wrapper around unittest.mock, cleaner syntax for pytest fixtures. |

### LLM Evaluation Integrations

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| langfuse | Latest | Observability & tracing | Production LLM observability. 19k+ GitHub stars, MIT license, self-hostable. Native Python SDK, 50+ framework integrations. Use for tracing generation pipeline. |
| deepeval | Latest | Evaluation metrics | Open-source LLM testing framework. Langfuse integration available. Use for computing evaluation metrics on generated datasets. |
| evidently | Latest | Testing & monitoring | 20M+ downloads, 100+ built-in metrics. Use for data quality validation and drift detection on synthetic datasets. |
| giskard | Latest | LLM/RAG testing | Comprehensive testing for LLM systems. Use for validating generated test cases against quality criteria. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv | Package manager | 10-100x faster than pip/poetry. Single binary replaces pip, pip-tools, virtualenv, pyenv. Use for CI/CD and fast dev iteration. Still maturing (2 years old), so use Poetry for team projects requiring stability. |
| Poetry | Package manager (alternative) | More mature (if team stability preferred). Complete ecosystem: lock files, publishing, dependency groups. Use if team needs proven tooling over performance. |
| ruff | Linting & formatting | Rust-based linter/formatter, 10-100x faster than flake8/black. Single tool replaces multiple. Python 3.7+ support. |
| mypy | Type checking | Static type checker for Python. Catches type errors before runtime. Essential with Pydantic models. |
| pre-commit | Git hooks | Auto-run ruff, mypy, tests before commits. Prevents broken code from being committed. |

## Installation

### Using uv (Recommended for Speed)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project with uv
uv init synthetic-dataset-generator
cd synthetic-dataset-generator

# Add dependencies
uv add "openai>=2.21.0" \
       "pydantic>=2.12.5" \
       "typer[all]>=0.23.1" \
       "rich>=14.3.2" \
       "loguru>=0.7.3" \
       "python-dotenv>=1.0.0" \
       "pyyaml>=6.0.2"

# Add evaluation integrations
uv add langfuse deepeval evidently giskard

# Add dev dependencies
uv add --dev "pytest>=9.0.2" \
             pytest-asyncio \
             pytest-mock \
             ruff \
             mypy \
             pre-commit
```

### Using Poetry (Recommended for Team Stability)

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Create project
poetry new synthetic-dataset-generator
cd synthetic-dataset-generator

# Add dependencies
poetry add "openai>=2.21.0" \
           "pydantic>=2.12.5" \
           "typer[all]>=0.23.1" \
           "rich>=14.3.2" \
           "loguru>=0.7.3" \
           "python-dotenv>=1.0.0" \
           "pyyaml>=6.0.2"

# Add evaluation integrations
poetry add langfuse deepeval evidently giskard

# Add dev dependencies
poetry add --group dev "pytest>=9.0.2" \
                       pytest-asyncio \
                       pytest-mock \
                       ruff \
                       mypy \
                       pre-commit
```

## Alternatives Considered

| Category | Recommended | Alternative | When to Use Alternative |
|----------|-------------|-------------|-------------------------|
| CLI Framework | Typer | Click | If you prefer explicit decorator-based configuration over type hints. Click is more mature and Typer is built on it. |
| CLI Framework | Typer | argparse | Never for new projects. argparse is verbose, lacks modern features. Only if stdlib-only requirement exists. |
| Data Validation | Pydantic | Marshmallow | If you need complex serialization to non-JSON formats. Marshmallow better for web APIs with custom serialization. |
| Data Validation | Pydantic | dataclasses + typeguard | If you want lightweight validation without dependencies. Not suitable for complex schema generation or OpenAI integration. |
| Package Manager | uv | Poetry | Use Poetry if team needs proven stability over speed. Poetry is 5+ years mature vs uv's 2 years. |
| Package Manager | uv/Poetry | pip + venv | Never for new projects. Manual dependency management is error-prone. No lock files. |
| Logging | Loguru | structlog | If you need deep OpenTelemetry integration or complex log processing pipelines. structlog more flexible but requires more setup. |
| Logging | Loguru | stdlib logging | Never for new projects. Stdlib logging is verbose, harder to configure. Loguru is drop-in replacement. |
| LLM Client | OpenAI SDK | LangChain | Only if building complex agent orchestration. LangChain is heavyweight, adds abstraction overhead. Direct SDK better for focused use cases. |
| LLM Client | OpenAI SDK | litellm | If you need multi-provider support (Anthropic, Cohere, etc). Not needed if OpenAI-only. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| os.path | Legacy string-based API, not cross-platform by default, verbose | pathlib (stdlib, Python 3.4+) |
| argparse | Extremely verbose, no type safety, manual help text, poor DX | Typer (type-hint driven, auto-help) |
| configparser (INI) | Limited data types, no nesting, outdated format | YAML (PyYAML) or TOML (tomllib in 3.11+) |
| Pydantic v1 | 5-50x slower than v2, no native OpenAI structured output support | Pydantic v2 (2.12.5+) |
| requests | Not async-capable, slower than httpx, no HTTP/2 | Use OpenAI SDK directly (handles HTTP) |
| setup.py | Deprecated in favor of pyproject.toml (PEP 621) | pyproject.toml with uv or Poetry |
| black + flake8 + isort | Multiple tools, slower, more config | ruff (single tool, 10-100x faster) |

## Stack Patterns by Use Case

### If Building for Production Team:
- Use Poetry for package management (maturity, stability)
- Use pre-commit hooks for code quality gates
- Use mypy strict mode for type safety
- Use structlog if you need OpenTelemetry integration
- Set up pytest with coverage thresholds

### If Building for Fast Prototyping:
- Use uv for package management (speed)
- Use Loguru for quick logging setup
- Skip mypy initially, add later
- Use Rich for beautiful output without config
- Use Typer for instant CLI with minimal code

### If Building for Russian Language:
- OpenAI SDK handles Unicode natively
- Pydantic handles Cyrillic in JSON schemas
- Rich supports Unicode output (ensure terminal encoding)
- Use UTF-8 encoding for all file I/O
- Test with actual Cyrillic strings in pytest fixtures

### If Building for Reproducibility:
- Use temperature=0 in OpenAI calls
- Use seed parameter for consistent outputs (OpenAI SDK)
- Pin all dependencies in lock file (Poetry/uv)
- Use pytest-random-order with fixed seed
- Log all OpenAI requests with Langfuse for replay

### If Building for Dataset Validation:
- Use Pydantic for schema validation
- Use Evidently for data quality metrics
- Use pytest parametrize for test matrices
- Use jsonschema for validating against external schemas
- Use Giskard for LLM-specific test cases

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| Typer 0.23.1 | Click 8.1+, Rich 10.11+ | Typer depends on both, versions managed automatically |
| Pydantic 2.12.5 | Python 3.9-3.14 | v2 not compatible with v1 (breaking changes) |
| OpenAI SDK 2.21.0 | Python 3.9-3.14, Pydantic 2.x | Native Pydantic v2 support for structured outputs |
| pytest 9.0.2 | Python 3.10-3.14 | Requires Python 3.10+, not compatible with 3.9 |
| Loguru 0.7.3 | Python 3.5+ | Compatible with all modern Python versions |
| Rich 14.3.2 | Python 3.8+ | Already included via Typer dependency |
| python-dotenv 1.0.0+ | Python 3.9-3.13 | No conflicts with other packages |

**Important:** If using pytest 9.x, you MUST use Python 3.10+. If you need Python 3.9 support, use pytest 8.x instead.

## Sources

**High Confidence (Official Docs & PyPI):**
- [Pydantic 2.12.5 - PyPI](https://pypi.org/project/pydantic/) - Verified version, features, performance claims
- [Typer 0.23.1 - PyPI](https://pypi.org/project/typer/) - Verified version, dependencies, CLI features
- [OpenAI Python SDK 2.21.0 - PyPI](https://pypi.org/project/openai/) - Verified version, Python support
- [OpenAI Structured Outputs Guide](https://platform.openai.com/docs/guides/structured-outputs) - Native Pydantic integration
- [pytest 9.0.2 - PyPI](https://pypi.org/project/pytest/) - Verified version, Python 3.10+ requirement
- [Loguru 0.7.3 - PyPI](https://pypi.org/project/loguru/) - Verified features, performance claims
- [Rich 14.3.2 - PyPI](https://pypi.org/project/rich/) - Verified version, features
- [python-dotenv - PyPI](https://pypi.org/project/python-dotenv/) - Verified 12-factor principles

**Medium Confidence (Verified with Multiple Sources):**
- [Typer vs Click Comparison](https://typer.tiangolo.com/alternatives/) - Official Typer docs
- [Click vs Typer 2025](https://www.pyinns.com/tools/click-vs-typer) - Community comparison
- [Poetry vs UV 2025](https://medium.com/@hitorunajp/poetry-vs-uv-which-python-package-manager-should-you-use-in-2025-4212cb5e0a14) - Performance analysis
- [UV Package Manager Guide](https://www.analyticsvidhya.com/blog/2025/08/uv-python-package-manager/) - Speed benchmarks
- [Pydantic vs Marshmallow Comparison](https://www.augmentedmind.de/2020/10/25/marshmallow-vs-pydantic-python/) - Use case analysis
- [Python pathlib vs os.path Best Practices](https://medium.com/@rashmi.rout76/stop-using-os-path-pathlib-will-change-your-life-5b0d12a236c8) - Modern Python patterns
- [Loguru vs structlog Comparison](https://betterstack.com/community/guides/logging/structlog/) - Logging framework comparison
- [LLM Evaluation Tools 2025](https://medium.com/@mkmanjula96/top-17-widely-used-llm-evaluation-tools-frameworks-in-industry-d1b7576f3080) - Industry tool landscape
- [Langfuse GitHub](https://github.com/langfuse/langfuse) - 19k+ stars, MIT license, verified features
- [Best LLM Observability Tools 2025](https://www.firecrawl.dev/blog/best-llm-observability-tools) - Tool comparison
- [pytest Fixtures Guide](https://docs.pytest.org/en/stable/how-to/fixtures.html) - Official best practices

---
*Stack research for: Synthetic Dataset Generator for LLM Agent Testing*
*Researched: 2026-02-16*
*Confidence: HIGH - All core libraries verified via official PyPI pages and documentation*
