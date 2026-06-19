from __future__ import annotations

from collections.abc import Sequence

from src.services.mock_draft_readiness_service import ReadinessReport


def render_readiness_report(report: ReadinessReport) -> str:
    lines = [
        "Mock Draft readiness preflight",
        f"Overall readiness: {report.readiness}",
        f"Fixture readiness: {report.fixture_readiness}",
        f"Real input readiness: {report.real_input_readiness}",
        f"Manifest readiness: {report.manifest_readiness}",
        f"ADP/market separation: {report.market_separation_readiness}",
        "No simulations run: yes",
        "No files written: yes",
        "Draft output produced: no",
    ]
    lines.extend(_section("Missing inputs", report.missing_real_inputs))
    lines.extend(_section("Schema errors", report.schema_violations))
    lines.extend(
        [
            "Next manual actions:",
            "- Provide local-only real input paths when ready.",
            "- Validate headers and row counts before any draft-room use.",
            "- Keep ADP/market behavior context separate from NWR private value.",
            "- Keep the no-simulation gate active until real inputs validate.",
        ]
    )
    return "\n".join(lines)


def _section(title: str, values: Sequence[str]) -> list[str]:
    if not values:
        return [f"{title}: none"]
    return [f"{title}:"] + [f"- {value}" for value in values]
