"""Evidently-based data quality report generator for dataset analysis."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING
import pandas as pd

if TYPE_CHECKING:
    from ..models.dataset_example import DatasetExample

logger = logging.getLogger(__name__)


def _generate_html_report(df: pd.DataFrame, summary: dict) -> str:
    """Generate HTML quality report from DataFrame and summary metrics.

    Args:
        df: DataFrame with dataset examples
        summary: Summary metrics dict

    Returns:
        HTML content as string
    """
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dataset Quality Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .metric {{ background-color: #f9f9f9; padding: 15px; margin: 10px 0; border-left: 4px solid #4CAF50; }}
        .metric-label {{ font-weight: bold; color: #666; }}
        .metric-value {{ font-size: 1.2em; color: #333; }}
        .warning {{ background-color: #fff3cd; border-left-color: #ffc107; }}
        .error {{ background-color: #f8d7da; border-left-color: #dc3545; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .good {{ color: #28a745; }}
        .warning-text {{ color: #ffc107; }}
        .error-text {{ color: #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Dataset Quality Report</h1>
        <p>Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <h2>Overview</h2>
        <div class="metric">
            <span class="metric-label">Total Examples:</span>
            <span class="metric-value">{summary['total']}</span>
        </div>
        <div class="metric {'warning' if summary['duplicates'] > 0 else ''}">
            <span class="metric-label">Duplicate Input Messages:</span>
            <span class="metric-value">{summary['duplicates']}</span>
        </div>
        <div class="metric {'warning' if summary['placeholder_count'] > 0 else ''}">
            <span class="metric-label">Placeholder Content:</span>
            <span class="metric-value">{summary['placeholder_count']}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Average Evaluation Criteria:</span>
            <span class="metric-value">{summary['avg_criteria_count']}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Average Policy References:</span>
            <span class="metric-value">{summary['avg_policy_count']}</span>
        </div>

        {'<h2>Warnings</h2>' + ''.join([f'<div class="metric warning">{w}</div>' for w in summary["warnings"]]) if summary["warnings"] else ''}

        <h2>Distribution Analysis</h2>

        <h3>Cases</h3>
        <table>
            <tr><th>Case</th><th>Count</th><th>Percentage</th></tr>
"""

    # Add case distribution
    for case, count in summary["case_distribution"].items():
        pct = (count / summary["total"]) * 100
        html += f"            <tr><td>{case}</td><td>{count}</td><td>{pct:.1f}%</td></tr>\n"

    html += """
        </table>

        <h3>Formats</h3>
        <table>
            <tr><th>Format</th><th>Count</th><th>Percentage</th></tr>
"""

    # Add format distribution
    for fmt, count in summary["format_distribution"].items():
        pct = (count / summary["total"]) * 100
        html += f"            <tr><td>{fmt}</td><td>{count}</td><td>{pct:.1f}%</td></tr>\n"

    html += """
        </table>

        <h3>Generators</h3>
        <table>
            <tr><th>Generator</th><th>Count</th><th>Percentage</th></tr>
"""

    # Add generator distribution
    for gen, count in summary["generator_distribution"].items():
        pct = (count / summary["total"]) * 100
        html += f"            <tr><td>{gen}</td><td>{count}</td><td>{pct:.1f}%</td></tr>\n"

    html += """
        </table>

        <h2>Dataset Statistics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
"""

    # Add basic statistics
    stats = {
        "Total Examples": summary["total"],
        "Unique Cases": len(summary["case_distribution"]),
        "Unique Formats": len(summary["format_distribution"]),
        "Unique Generators": len(summary["generator_distribution"]),
        "Min Criteria Count": int(df["criteria_count"].min()),
        "Max Criteria Count": int(df["criteria_count"].max()),
        "Min Policy Count": int(df["policy_count"].min()),
        "Max Policy Count": int(df["policy_count"].max()),
        "Avg Input Length": int(df["input_text"].str.len().mean()),
        "Avg Output Length": int(df["expected_output"].str.len().mean()),
    }

    for metric, value in stats.items():
        html += f"            <tr><td>{metric}</td><td>{value}</td></tr>\n"

    html += """
        </table>
    </div>
</body>
</html>
"""

    return html


def generate_quality_report(
    examples: list["DatasetExample"],
    output_path: Path,
) -> dict:
    """Generate Evidently data quality report on generated dataset.

    Analyzes:
    - Duplicate detection (near-duplicate input messages)
    - Distribution of cases, formats, evaluation criteria counts
    - Placeholder detection (empty/template content)
    - Policy ID distribution

    Args:
        examples: List of generated DatasetExample objects
        output_path: Directory to write quality_report.html

    Returns:
        Dict with summary metrics: {duplicates, total, distribution, warnings}
    """
    try:
        # Step 1: Convert DatasetExample list to pandas DataFrame
        logger.info(f"Converting {len(examples)} examples to DataFrame for analysis")

        data_rows = []
        for ex in examples:
            # Extract input text from first message
            input_text = ex.input.messages[0].content if ex.input.messages else ""

            data_rows.append({
                "id": ex.id,
                "case": ex.case,
                "format": ex.format,
                "use_case_id": ex.use_case_id,
                "test_case_id": ex.test_case_id,
                "input_text": input_text,
                "expected_output": ex.expected_output,
                "criteria_count": len(ex.evaluation_criteria),
                "policy_count": len(ex.policy_ids),
                "generator": ex.metadata.get("generator", "unknown"),
            })

        df = pd.DataFrame(data_rows)

        # Step 2: Generate quality report using pandas analysis
        # (Evidently 0.7.20 API has changed significantly - using direct pandas for now)
        logger.info("Generating data quality report using pandas analysis")

        # Step 3: Extract summary metrics from DataFrame
        logger.info("Analyzing dataset quality")

        # Duplicate detection (exact duplicate input_text)
        duplicates = df["input_text"].duplicated().sum()

        # Distribution of cases and formats
        case_distribution = df["case"].value_counts().to_dict()
        format_distribution = df["format"].value_counts().to_dict()
        generator_distribution = df["generator"].value_counts().to_dict()

        # Average criteria and policy counts
        avg_criteria = df["criteria_count"].mean()
        avg_policies = df["policy_count"].mean()

        # Placeholder detection
        def is_placeholder(text: str) -> bool:
            """Check if text is a placeholder."""
            if not text or len(text) < 10:
                return True
            placeholder_patterns = ["TODO", "TBD", "placeholder", "PLACEHOLDER", "XXX"]
            return any(pattern in text for pattern in placeholder_patterns)

        placeholder_count = df["expected_output"].apply(is_placeholder).sum()

        # Step 4: Build summary dict
        summary = {
            "total": len(examples),
            "duplicates": int(duplicates),
            "case_distribution": case_distribution,
            "format_distribution": format_distribution,
            "generator_distribution": generator_distribution,
            "avg_criteria_count": round(avg_criteria, 2),
            "avg_policy_count": round(avg_policies, 2),
            "placeholder_count": int(placeholder_count),
            "warnings": [],
        }

        # Add warnings for issues
        if duplicates > 0:
            summary["warnings"].append(f"{duplicates} duplicate input messages detected")
        if placeholder_count > 0:
            summary["warnings"].append(f"{placeholder_count} examples with placeholder content")
        if avg_criteria < 3:
            summary["warnings"].append(f"Average criteria count ({avg_criteria:.1f}) below minimum 3")

        # Log key findings
        logger.info(f"Quality analysis: {len(examples)} examples, {duplicates} duplicates, "
                   f"{placeholder_count} placeholders")
        logger.info(f"Distributions - Cases: {case_distribution}, Formats: {format_distribution}")
        logger.info(f"Generators: {generator_distribution}")

        for warning in summary["warnings"]:
            logger.warning(f"Quality issue: {warning}")

        # Generate simple HTML report
        try:
            html_content = _generate_html_report(df, summary)
            report_path = output_path / "quality_report.html"
            report_path.write_text(html_content, encoding="utf-8")
            logger.info(f"Quality report saved to {report_path}")
        except Exception as e_html:
            logger.warning(f"HTML report generation failed: {e_html}")

        return summary

    except Exception as e:
        # Non-blocking: log warning and return minimal summary
        logger.warning(f"Quality report generation failed (non-blocking): {e}")
        return {
            "total": len(examples),
            "duplicates": 0,
            "warnings": [f"Report generation failed: {str(e)}"],
            "error": str(e),
        }
