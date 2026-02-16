"""Parameter variation router using pairwise combinatorial testing."""

import logging
from allpairspy import AllPairs

logger = logging.getLogger(__name__)


# Default variation axes per case
VARIATION_AXES = {
    "support_bot": {
        "tone": ["neutral", "negative", "aggressive"],
        "has_order_id": [True, False],
        "requires_account_access": [True, False],
        "language": ["ru", "en"],
        "adversarial": ["none", "profanity", "injection", "garbage"],
    },
    "operator_quality": {
        "phrase_length": ["short", "medium", "long"],
        "punctuation_errors": ["none", "minor", "severe"],
        "slang_profanity_emoji": ["none", "moderate", "excessive"],
        "medical_terms": ["none", "present"],
        "user_aggression": ["neutral", "frustrated", "angry"],
        "escalation_needed": ["no", "yes"],
    },
    "doctor_booking": {
        # Reuse support_bot axes for doctor booking (similar domain)
        "tone": ["neutral", "negative", "aggressive"],
        "has_order_id": [True, False],
        "requires_account_access": [True, False],
        "language": ["ru", "en"],
        "adversarial": ["none", "profanity", "injection", "garbage"],
    },
}


def generate_variations(
    case: str, use_case_description: str, policies: list, min_test_cases: int = 3
) -> list[dict]:
    """Generate pairwise parameter variations for test cases.

    Uses allpairspy for pairwise combinatorial testing to generate efficient
    parameter combinations that cover all pairwise interactions without
    full combinatorial explosion.

    Args:
        case: Case identifier (support_bot, operator_quality, doctor_booking)
        use_case_description: Use case description (currently unused, for future context-aware generation)
        policies: List of policies (currently unused, for future policy-aware generation)
        min_test_cases: Minimum number of test cases to generate (default: 3)

    Returns:
        List of parameter dictionaries, each with axis_name -> value mappings

    Example:
        >>> variations = generate_variations('support_bot', 'FAQ queries', [], min_test_cases=3)
        >>> len(variations) >= 3
        True
        >>> all(isinstance(v, dict) for v in variations)
        True
    """
    logger.info(f"Generating parameter variations for case '{case}'")

    # Get variation axes for this case
    axes = VARIATION_AXES.get(case)
    if not axes:
        logger.warning(
            f"Unknown case '{case}', defaulting to support_bot variation axes"
        )
        axes = VARIATION_AXES["support_bot"]

    # Prepare axes for AllPairs
    # AllPairs expects list of lists [[value1, value2], [value3, value4], ...]
    axis_names = list(axes.keys())
    axis_values = [axes[name] for name in axis_names]

    # Generate pairwise combinations
    pairwise_combinations = []
    for combination in AllPairs(axis_values):
        # Combine axis names with values
        param_dict = {
            axis_names[i]: combination[i] for i in range(len(axis_names))
        }
        pairwise_combinations.append(param_dict)

    logger.info(
        f"Generated {len(pairwise_combinations)} pairwise combinations for {case}"
    )

    # If pairwise produces fewer than min_test_cases, pad with additional combinations
    if len(pairwise_combinations) < min_test_cases:
        logger.info(
            f"Pairwise generated {len(pairwise_combinations)} combinations, padding to {min_test_cases}"
        )
        import random

        # Generate additional random combinations
        while len(pairwise_combinations) < min_test_cases:
            random_combo = {
                name: random.choice(values) for name, values in axes.items()
            }
            # Avoid duplicates
            if random_combo not in pairwise_combinations:
                pairwise_combinations.append(random_combo)

    # For each combination, identify which axes have non-default values
    # This will be used for parameter_variation_axes on TestCase
    result = []
    for param_dict in pairwise_combinations:
        # Identify 2-3 axes with non-default/non-neutral values
        variation_axes = _select_variation_axes(param_dict, case)

        # Add variation_axes to the dict (will be extracted when creating TestCase)
        enriched_dict = param_dict.copy()
        enriched_dict["_variation_axes"] = variation_axes
        result.append(enriched_dict)

    logger.info(
        f"Generated {len(result)} parameter variations with selected axes"
    )
    return result


def _select_variation_axes(parameters: dict, case: str) -> list[str]:
    """Select 2-3 axes that have non-default values for parameter_variation_axes.

    Args:
        parameters: Parameter dictionary
        case: Case identifier

    Returns:
        List of 2-3 axis names representing main variations
    """
    # Define default/neutral values per axis
    defaults = {
        "tone": "neutral",
        "has_order_id": True,
        "requires_account_access": False,
        "language": "ru",
        "adversarial": "none",
        "phrase_length": "medium",
        "punctuation_errors": "none",
        "slang_profanity_emoji": "none",
        "medical_terms": "none",
        "user_aggression": "neutral",
        "escalation_needed": "no",
    }

    # Find axes with non-default values
    non_default_axes = []
    for key, value in parameters.items():
        if key in defaults and value != defaults[key]:
            non_default_axes.append(key)

    # If we have 2-3 non-default axes, use them
    if 2 <= len(non_default_axes) <= 3:
        return non_default_axes

    # If less than 2, pad with some default axes
    if len(non_default_axes) < 2:
        # Add most distinctive axes for this case
        if case == "support_bot":
            default_axes = ["tone", "adversarial"]
        else:  # operator_quality
            default_axes = ["punctuation_errors", "user_aggression"]

        for axis in default_axes:
            if axis not in non_default_axes and axis in parameters:
                non_default_axes.append(axis)
                if len(non_default_axes) >= 2:
                    break

    # If more than 3, take first 3 most significant
    if len(non_default_axes) > 3:
        # Priority order for significance
        priority = [
            "adversarial",
            "escalation_needed",
            "user_aggression",
            "tone",
            "punctuation_errors",
            "slang_profanity_emoji",
            "requires_account_access",
        ]

        # Sort by priority
        sorted_axes = []
        for p in priority:
            if p in non_default_axes:
                sorted_axes.append(p)
        # Add any remaining
        for axis in non_default_axes:
            if axis not in sorted_axes:
                sorted_axes.append(axis)

        non_default_axes = sorted_axes[:3]

    return non_default_axes[:3]  # Ensure max 3
