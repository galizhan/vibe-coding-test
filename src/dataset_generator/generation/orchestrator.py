"""OpenAI function calling orchestrator for framework routing."""

import json
import logging
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dataset_generator.extraction.llm_client import get_openai_client
from dataset_generator.generation.generators.deepeval_gen import generate_with_deepeval
from dataset_generator.generation.generators.ragas_gen import generate_with_ragas
from dataset_generator.generation.generators.giskard_gen import generate_with_giskard
from dataset_generator.generation.adapters.deepeval_adapter import (
    adapt_deepeval_golden_to_test_case,
    adapt_deepeval_golden_to_example,
)
from dataset_generator.generation.adapters.ragas_adapter import (
    adapt_ragas_row_to_test_case,
    adapt_ragas_row_to_example,
)
from dataset_generator.generation.adapters.giskard_adapter import (
    adapt_giskard_row_to_test_case,
    adapt_giskard_row_to_example,
)
from dataset_generator.generation.fallback import generate_with_openai_fallback
from dataset_generator.models.test_case import TestCase
from dataset_generator.models.dataset_example import DatasetExample

if TYPE_CHECKING:
    from dataset_generator.models.use_case import UseCase
    from dataset_generator.models.policy import Policy

logger = logging.getLogger(__name__)


def orchestrate_generation(
    use_case: "UseCase",
    policies: list["Policy"],
    document_path: str,
    model: str = "gpt-4o-mini",
    seed: int | None = None,
    min_test_cases: int = 3,
    case: str = "support_bot",
    formats: list[str] | None = None,
) -> tuple[list[TestCase], list[DatasetExample]]:
    """Orchestrate test case and dataset example generation using format adapters.

    This orchestrator uses format-specific adapters as the PRIMARY generation path,
    with framework-based generation (DeepEval, Ragas, Giskard) as SUPPLEMENTARY.

    Generation flow:
    1. Generate parameter variations using variation router
    2. For each format in formats, iterate all parameter combinations:
       - Get format adapter
       - Generate example using adapter
       - Classify metadata.source for support_bot
       - Validate format
    3. Supplement with framework-based generation if needed to reach min_test_cases
    4. Fall back to OpenAI direct generation if adapters fail

    Args:
        use_case: UseCase object to generate tests for
        policies: List of Policy objects relevant to the use case
        document_path: Path to original markdown document
        model: OpenAI model to use for orchestration (default: gpt-4o-mini)
        seed: Random seed for reproducibility (optional)
        min_test_cases: Minimum test cases required (default: 3)
        case: Case identifier (support_bot, operator_quality, doctor_booking)
        formats: List of formats to generate (e.g., ["single_turn_qa"])

    Returns:
        Tuple of (test_cases, dataset_examples)

    Example:
        >>> from dataset_generator.models.use_case import UseCase
        >>> from dataset_generator.models.policy import Policy
        >>> uc = UseCase(id="uc_001", name="Test", description="Test UC", evidence=[], case="support_bot")
        >>> policies = [Policy(id="pol_001", name="Test", type="must", description="Test", evidence=[])]
        >>> test_cases, examples = orchestrate_generation(uc, policies, "doc.md", case="support_bot", formats=["single_turn_qa"])
    """
    logger.info(f"Orchestrating generation for use case: {use_case.id} (case={case}, formats={formats})")

    # Default formats if not provided
    if formats is None:
        if case == "operator_quality":
            formats = ["single_utterance_correction", "dialog_last_turn_correction"]
        else:  # support_bot, doctor_booking
            formats = ["single_turn_qa"]

    # Import format-specific modules
    from dataset_generator.generation.format_adapters import get_adapter_for_format
    from dataset_generator.generation.variation_router import generate_variations
    from dataset_generator.generation.source_classifier import classify_source_type

    test_cases = []
    dataset_examples = []
    policy_ids = [p.id for p in policies]

    # Convert policies to dicts once for adapter calls
    policy_dicts = []
    for p in policies:
        policy_dicts.append({
            "id": p.id,
            "name": p.name,
            "type": p.type,
            "description": p.description,
            "statement": getattr(p, "statement", p.description),
        })

    try:
        # Step 1: Generate parameter variations using pairwise combinatorics
        logger.info(f"Generating parameter variations for case={case}")
        variations = generate_variations(
            case=case,
            use_case_description=use_case.description,
            policies=policies,
            min_test_cases=min_test_cases,
        )
        logger.info(f"Generated {len(variations)} parameter variations")

        # Step 2: For each format, generate examples for each parameter combination
        for format_name in formats:
            logger.info(f"Generating examples for format={format_name}")

            try:
                # Get adapter for this format
                adapter = get_adapter_for_format(format_name, case)

                # Generate examples for each parameter variation
                for idx, params in enumerate(variations, start=1):
                    try:
                        # Extract variation axes (will be 2-3 axes with non-default values)
                        variation_axes = params.pop("_variation_axes", [])

                        # Create test case ID
                        tc_id = f"tc_{use_case.id.replace('uc_', '')}_{format_name}_{idx:03d}"

                        # Create TestCase object
                        tc = TestCase(
                            id=tc_id,
                            use_case_id=use_case.id,
                            case=case,
                            name=f"{use_case.name} - {format_name} - variation {idx}",
                            description=f"Test case for {use_case.name} with parameters: {params}",
                            parameter_variation_axes=variation_axes[:3] if len(variation_axes) >= 2 else variation_axes + ["default", "default"][:3-len(variation_axes)],
                            parameters=params,
                            policy_ids=policy_ids,
                            metadata={"generator": "format_adapter"},
                        )
                        test_cases.append(tc)

                        # Generate dataset example using adapter
                        logger.debug(f"Generating example for test case {tc_id}")
                        example = adapter.generate_example(
                            use_case_id=use_case.id,
                            test_case_id=tc_id,
                            parameters=params,
                            policies=policy_dicts,
                            model=model,
                            seed=seed,
                        )

                        # Set case field
                        example.case = case

                        # For support_bot, classify metadata.source
                        if case == "support_bot":
                            # Extract first user message content
                            user_content = ""
                            for msg in example.input.messages:
                                if msg.role == "user":
                                    user_content = msg.content
                                    break

                            source_type = classify_source_type(
                                use_case_description=use_case.description,
                                generated_input=user_content,
                                parameters=params,
                                model=model,
                            )
                            if not example.metadata:
                                example.metadata = {}
                            example.metadata["source"] = source_type
                            logger.debug(f"Classified example {example.id} as source={source_type}")

                        # Validate format
                        validation_errors = adapter.validate_format(example)
                        if validation_errors:
                            logger.warning(f"Format validation errors for {example.id}: {validation_errors}")

                        dataset_examples.append(example)

                    except Exception as e:
                        logger.warning(f"Failed to generate example for variation {idx} in format {format_name}: {e}", exc_info=True)
                        continue

            except Exception as e:
                logger.warning(f"Failed to get adapter for format {format_name}: {e}", exc_info=True)
                continue

        logger.info(f"Format adapter generation: {len(test_cases)} test cases, {len(dataset_examples)} examples")

    except Exception as e:
        logger.error(f"Format adapter generation failed: {e}", exc_info=True)
        # Fall back to OpenAI fallback
        logger.warning("Falling back to OpenAI direct generation")
        return _generate_with_fallback_only(use_case, policies, min_test_cases, model, seed, case, formats)

    # Step 3: If we don't have enough test cases, supplement with framework-based generation
    if len(test_cases) < min_test_cases:
        logger.info(f"Supplementing with framework-based generation ({len(test_cases)}/{min_test_cases} generated)")

        # Try framework-based generation as supplementary source
        try:
            tools = _build_tool_definitions()
            messages = _build_orchestration_messages(use_case, policies, document_path)
            client = get_openai_client()

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0,
                seed=seed,
            )

            tool_calls = response.choices[0].message.tool_calls if response.choices[0].message.tool_calls else []

            if tool_calls:
                policy_doc_path = prepare_policy_documents(policies, document_path)

                for tool_call in tool_calls:
                    try:
                        function_name = tool_call.function.name
                        arguments = json.loads(tool_call.function.arguments)

                        if function_name == "generate_with_deepeval":
                            tcs, exs = _invoke_deepeval(use_case, policies, policy_doc_path, arguments, model)
                            test_cases.extend(tcs)
                            dataset_examples.extend(exs)
                        elif function_name == "generate_with_ragas":
                            tcs, exs = _invoke_ragas(use_case, policies, policy_doc_path, arguments, model)
                            test_cases.extend(tcs)
                            dataset_examples.extend(exs)
                        elif function_name == "generate_with_giskard":
                            tcs, exs = _invoke_giskard(use_case, policies, policy_doc_path, arguments, model)
                            test_cases.extend(tcs)
                            dataset_examples.extend(exs)
                    except Exception as e:
                        logger.warning(f"Framework call {function_name} failed: {e}")
                        continue

                try:
                    Path(policy_doc_path).unlink()
                except Exception:
                    pass

        except Exception as e:
            logger.warning(f"Framework-based supplementary generation failed: {e}")

    # Step 4: Final fallback if still insufficient
    if len(test_cases) < min_test_cases:
        logger.warning(f"Still insufficient test cases ({len(test_cases)}/{min_test_cases}), using OpenAI fallback")
        fallback_tcs, fallback_exs = _generate_with_fallback_only(
            use_case, policies, min_test_cases - len(test_cases), model, seed, case, formats
        )
        test_cases.extend(fallback_tcs)
        dataset_examples.extend(fallback_exs)

    logger.info(
        f"Generated {len(test_cases)} test cases and {len(dataset_examples)} examples "
        f"for use case {use_case.id} (case={case}, formats={formats})"
    )

    return test_cases, dataset_examples


def prepare_policy_documents(policies: list["Policy"], document_path: str) -> str:
    """Prepare a temporary document from policies for framework consumption.

    Frameworks like DeepEval and Ragas expect file paths, but we have in-memory
    policy objects. This function writes policies to a temporary file.

    Args:
        policies: List of Policy objects
        document_path: Original document path (used as context)

    Returns:
        Path to temporary policy document file
    """
    # Create temporary file
    fd, temp_path = tempfile.mkstemp(suffix=".md", prefix="policies_")

    # Build markdown content from policies
    content = "# Policies\n\n"
    for policy in policies:
        content += f"## {policy.id}: {policy.name}\n\n"
        content += f"**Type:** {policy.type}\n\n"
        content += f"{policy.description}\n\n"
        if policy.evidence:
            content += "**Evidence:**\n"
            for ev in policy.evidence:
                content += f"- {ev.quote}\n"
        content += "\n---\n\n"

    # Write to temporary file
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.debug(f"Created temporary policy document at {temp_path}")
    return temp_path


def _build_tool_definitions() -> list[dict[str, Any]]:
    """Build OpenAI function calling tool definitions."""
    return [
        {
            "type": "function",
            "function": {
                "name": "generate_with_deepeval",
                "description": (
                    "Generate test cases and dataset examples from documents using evolution techniques. "
                    "Use when: generating from policy documents, need diverse question types, "
                    "bulk generation required."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "document_paths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of document file paths",
                        },
                        "num_goldens": {
                            "type": "integer",
                            "description": "Number of golden test cases to generate",
                        },
                        "include_expected_output": {
                            "type": "boolean",
                            "description": "Whether to include expected outputs",
                        },
                    },
                    "required": ["document_paths"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "generate_with_ragas",
                "description": (
                    "Generate RAG-specific test questions with knowledge graph transformations. "
                    "Use when: need multi-context questions, reasoning questions, "
                    "evaluating retrieval quality."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "test_size": {
                            "type": "integer",
                            "description": "Number of test questions to generate",
                        },
                        "reasoning_ratio": {
                            "type": "number",
                            "description": "Ratio of reasoning-based questions (0.0-1.0)",
                        },
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "generate_with_giskard",
                "description": (
                    "Generate business tests from knowledge base with component evaluation. "
                    "Use when: need knowledge base validation, business test scenarios."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "num_questions": {
                            "type": "integer",
                            "description": "Number of questions to generate",
                        },
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
    ]


def _build_orchestration_messages(
    use_case: "UseCase",
    policies: list["Policy"],
    document_path: str,
) -> list[dict[str, str]]:
    """Build orchestration messages for OpenAI function calling."""
    # Build policy summaries
    policy_summaries = []
    for policy in policies[:5]:  # First 5 policies
        summary = f"{policy.id} ({policy.type}): {policy.description[:200]}"
        policy_summaries.append(summary)

    policy_text = "\n".join(f"- {s}" for s in policy_summaries)
    if len(policies) > 5:
        policy_text += f"\n- ... and {len(policies) - 5} more policies"

    system_message = (
        "You are a test generation orchestrator. Given a use case and its policies, "
        "select the appropriate framework(s) to generate test cases and dataset examples. "
        "Consider the nature of the content when choosing: document-heavy content benefits "
        "from DeepEval evolution, multi-context reasoning benefits from Ragas, and knowledge "
        "base validation benefits from Giskard. You may call multiple tools."
    )

    user_message = f"""Use Case: {use_case.name}

Description: {use_case.description}

Policies ({len(policies)} total):
{policy_text}

Document: {document_path}

Generate test cases and dataset examples for this use case."""

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


def _invoke_deepeval(
    use_case: "UseCase",
    policies: list["Policy"],
    policy_doc_path: str,
    arguments: dict[str, Any],
    model: str,
) -> tuple[list[TestCase], list[DatasetExample]]:
    """Invoke DeepEval generator and adapt results."""
    # Extract arguments
    document_paths = arguments.get("document_paths", [policy_doc_path])
    num_goldens = arguments.get("num_goldens", 10)
    include_expected_output = arguments.get("include_expected_output", True)

    # Call generator
    goldens = generate_with_deepeval(
        document_paths=document_paths,
        num_goldens=num_goldens,
        include_expected_output=include_expected_output,
        model=model,
    )

    # Adapt to our models
    test_cases = []
    dataset_examples = []

    policy_ids = [p.id for p in policies]

    for idx, golden in enumerate(goldens, start=1):
        tc = adapt_deepeval_golden_to_test_case(golden, use_case.id, idx)
        test_cases.append(tc)

        ex = adapt_deepeval_golden_to_example(
            golden, use_case.id, tc.id, idx, policy_ids=policy_ids
        )
        dataset_examples.append(ex)

    return test_cases, dataset_examples


def _invoke_ragas(
    use_case: "UseCase",
    policies: list["Policy"],
    policy_doc_path: str,
    arguments: dict[str, Any],
    model: str,
) -> tuple[list[TestCase], list[DatasetExample]]:
    """Invoke Ragas generator and adapt results."""
    # Extract arguments
    test_size = arguments.get("test_size", 10)
    reasoning_ratio = arguments.get("reasoning_ratio", 0.4)

    # Call generator
    testset = generate_with_ragas(
        document_paths=[policy_doc_path],
        test_size=test_size,
        reasoning_ratio=reasoning_ratio,
        model=model,
    )

    # Adapt to our models
    test_cases = []
    dataset_examples = []

    policy_ids = [p.id for p in policies]

    for idx, row in enumerate(testset.to_pandas().itertuples(), start=1):
        tc = adapt_ragas_row_to_test_case(row, use_case.id, idx)
        test_cases.append(tc)

        ex = adapt_ragas_row_to_example(
            row, use_case.id, tc.id, idx, policy_ids=policy_ids
        )
        dataset_examples.append(ex)

    return test_cases, dataset_examples


def _invoke_giskard(
    use_case: "UseCase",
    policies: list["Policy"],
    policy_doc_path: str,
    arguments: dict[str, Any],
    model: str,
) -> tuple[list[TestCase], list[DatasetExample]]:
    """Invoke Giskard generator and adapt results."""
    # Extract arguments
    num_questions = arguments.get("num_questions", 20)

    # Call generator
    testset = generate_with_giskard(
        document_paths=[policy_doc_path],
        num_questions=num_questions,
        model=model,
    )

    # Adapt to our models
    test_cases = []
    dataset_examples = []

    policy_ids = [p.id for p in policies]

    for idx, row in enumerate(testset.to_pandas().itertuples(), start=1):
        tc = adapt_giskard_row_to_test_case(row, use_case.id, idx)
        test_cases.append(tc)

        ex = adapt_giskard_row_to_example(
            row, use_case.id, tc.id, idx, policy_ids=policy_ids
        )
        dataset_examples.append(ex)

    return test_cases, dataset_examples


def _generate_with_fallback_only(
    use_case: "UseCase",
    policies: list["Policy"],
    num_test_cases: int,
    model: str,
    seed: int | None,
    case: str = "support_bot",
    formats: list[str] | None = None,
) -> tuple[list[TestCase], list[DatasetExample]]:
    """Generate using only the OpenAI fallback."""
    policy_dicts = [
        {
            "id": p.id,
            "name": p.name,
            "type": p.type,
            "description": p.description,
        }
        for p in policies
    ]

    return generate_with_openai_fallback(
        use_case_id=use_case.id,
        use_case_description=use_case.description,
        policies=policy_dicts,
        num_test_cases=num_test_cases,
        model=model,
        seed=seed,
        case=case,
        formats=formats,
    )
