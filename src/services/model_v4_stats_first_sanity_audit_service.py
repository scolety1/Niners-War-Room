from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.services.model_v4_fantasypros_identity_mapping_service import (
    normalize_player_name,
)

DEFAULT_STATS_FIRST_ROOT = Path(
    "local_exports/model_v4/stats_first_expected_value/latest"
)
DEFAULT_EXPECTED_VALUE_PATH = (
    DEFAULT_STATS_FIRST_ROOT / "stats_first_expected_value_rows.csv"
)
DEFAULT_COMPONENT_EVIDENCE_PATH = (
    DEFAULT_STATS_FIRST_ROOT / "stats_first_component_evidence_rows.csv"
)
DEFAULT_UNAVAILABLE_SECTIONS_PATH = (
    DEFAULT_STATS_FIRST_ROOT / "stats_first_unavailable_sections.csv"
)
DEFAULT_SOURCE_WARNINGS_PATH = (
    DEFAULT_STATS_FIRST_ROOT / "stats_first_source_warnings.csv"
)
DEFAULT_SUMMARY_PATH = DEFAULT_STATS_FIRST_ROOT / "stats_first_expected_value_summary.json"
DEFAULT_TRUTH_SET_PATH = Path("docs/model_v4/TRUTH_SET_PLAYER_UNIVERSE.csv")

PHASE_9D_STATS_FIRST_SANITY_AUDIT_CSV_PATH = Path(
    "docs/model_v4/PHASE_9D_STATS_FIRST_SANITY_AUDIT.csv"
)
PHASE_9D_STATS_FIRST_SANITY_AUDIT_MD_PATH = Path(
    "docs/model_v4/PHASE_9D_STATS_FIRST_SANITY_AUDIT.md"
)

DEEP_HISTORY_REVIEW_THRESHOLD = 15.0
HIGH_STATS_LAYER_QB_THRESHOLD = 70.0

ELITE_RBS = (
    "Bijan Robinson",
    "Jahmyr Gibbs",
    "De'Von Achane",
    "Christian McCaffrey",
    "Saquon Barkley",
    "Derrick Henry",
    "Jonathan Taylor",
    "Kyren Williams",
    "Josh Jacobs",
    "Breece Hall",
)

ELITE_WRS = (
    "Jaxon Smith-Njigba",
    "Puka Nacua",
    "Ja'Marr Chase",
    "Justin Jefferson",
    "Amon-Ra St. Brown",
    "CeeDee Lamb",
    "Malik Nabers",
    "Brian Thomas Jr.",
    "Tee Higgins",
)

QB_CONTROLS = (
    "Josh Allen",
    "Lamar Jackson",
    "Jalen Hurts",
    "Jayden Daniels",
    "Joe Burrow",
    "Patrick Mahomes",
    "Brock Purdy",
    "Caleb Williams",
    "Daniel Jones",
    "Jared Goff",
    "Matthew Stafford",
)

TE_CONTROLS = (
    "Brock Bowers",
    "Trey McBride",
    "Travis Kelce",
    "George Kittle",
    "Sam LaPorta",
    "Mark Andrews",
    "T.J. Hockenson",
    "Jake Ferguson",
)

AGING_OR_RETIRED_CONTROLS = (
    "Tom Brady",
    "Drew Brees",
    "Matt Ryan",
    "Ben Roethlisberger",
    "Rob Gronkowski",
    "Antonio Brown",
    "Julio Jones",
    "Todd Gurley",
    "Larry Fitzgerald",
    "Jarvis Landry",
    "Andrew Luck",
    "Cam Newton",
)

STATS_FIRST_SANITY_AUDIT_HEADER = (
    "group",
    "player",
    "matched_player",
    "match_status",
    "position",
    "latest_season",
    "stats_first_expected_value",
    "evidence_coverage",
    "weighted_seasons",
    "top_component",
    "component_summary",
    "missing_sections",
    "source_warning_count",
    "unavailable_section_count",
    "external_projection_context_status",
    "projection_core_value_status",
    "deep_history_status",
    "issue_type",
    "finding",
    "next_action",
)


@dataclass(frozen=True)
class ModelV4StatsFirstSanityAuditResult:
    csv_path: Path
    markdown_path: Path
    rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def run_model_v4_stats_first_sanity_audit(
    *,
    expected_value_path: str | Path = DEFAULT_EXPECTED_VALUE_PATH,
    component_evidence_path: str | Path = DEFAULT_COMPONENT_EVIDENCE_PATH,
    unavailable_sections_path: str | Path = DEFAULT_UNAVAILABLE_SECTIONS_PATH,
    source_warnings_path: str | Path = DEFAULT_SOURCE_WARNINGS_PATH,
    summary_path: str | Path = DEFAULT_SUMMARY_PATH,
    truth_set_path: str | Path = DEFAULT_TRUTH_SET_PATH,
    output_csv_path: str | Path = PHASE_9D_STATS_FIRST_SANITY_AUDIT_CSV_PATH,
    output_md_path: str | Path = PHASE_9D_STATS_FIRST_SANITY_AUDIT_MD_PATH,
    audit_groups: dict[str, tuple[str, ...]] | None = None,
) -> ModelV4StatsFirstSanityAuditResult:
    expected_rows = _read_dicts(Path(expected_value_path))
    component_rows = _read_dicts_if_exists(Path(component_evidence_path))
    unavailable_rows = _read_dicts_if_exists(Path(unavailable_sections_path))
    source_warning_rows = _read_dicts_if_exists(Path(source_warnings_path))
    layer_summary = _read_json_if_exists(Path(summary_path))

    expected_by_player = {
        normalize_player_name(row.get("matched_model_player")): row
        for row in expected_rows
    }
    components_by_player = _rows_by_player(component_rows)
    unavailable_by_player = _rows_by_player(unavailable_rows)
    warnings_by_player = _rows_by_player(source_warning_rows)
    groups = audit_groups or _default_audit_groups(Path(truth_set_path))
    guardrails = _guardrail_summary(layer_summary)

    rows: list[dict[str, object]] = []
    for group_name, players in groups.items():
        for player in players:
            rows.append(
                _audit_row(
                    group=group_name,
                    player=player,
                    expected_by_player=expected_by_player,
                    components_by_player=components_by_player,
                    unavailable_by_player=unavailable_by_player,
                    warnings_by_player=warnings_by_player,
                    guardrails=guardrails,
                )
            )

    summary = _summary(rows, guardrails, layer_summary)
    csv_path = Path(output_csv_path)
    md_path = Path(output_md_path)
    _write_csv(csv_path, STATS_FIRST_SANITY_AUDIT_HEADER, rows)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(_markdown(summary, rows), encoding="utf-8")

    return ModelV4StatsFirstSanityAuditResult(
        csv_path=csv_path,
        markdown_path=md_path,
        rows=tuple(rows),
        summary=summary,
    )


def _audit_row(
    *,
    group: str,
    player: str,
    expected_by_player: dict[str, dict[str, str]],
    components_by_player: dict[str, list[dict[str, str]]],
    unavailable_by_player: dict[str, list[dict[str, str]]],
    warnings_by_player: dict[str, list[dict[str, str]]],
    guardrails: dict[str, object],
) -> dict[str, object]:
    player_key = normalize_player_name(player)
    row = expected_by_player.get(player_key)
    if row is None:
        return _missing_row(group, player, guardrails)

    matched_player = str(row.get("matched_model_player") or player)
    matched_key = normalize_player_name(matched_player)
    unavailable = unavailable_by_player.get(matched_key, [])
    warnings = warnings_by_player.get(matched_key, [])
    value = _float(row.get("stats_first_expected_value"))
    latest_season = _int(row.get("latest_season"))
    deep_history_status = _deep_history_status(latest_season, value)
    projection_core_value_status = str(guardrails["projection_core_value_status"])
    issue_type = _issue_type(
        group=group,
        position=str(row.get("position") or ""),
        value=value,
        latest_season=latest_season,
        deep_history_status=deep_history_status,
        projection_core_value_status=projection_core_value_status,
        unavailable=unavailable,
    )
    finding, next_action = _finding_and_action(
        issue_type=issue_type,
        group=group,
        position=str(row.get("position") or ""),
        value=value,
        latest_season=latest_season,
        deep_history_status=deep_history_status,
        projection_core_value_status=projection_core_value_status,
    )
    return {
        "group": group,
        "player": player,
        "matched_player": matched_player,
        "match_status": "matched",
        "position": row.get("position", ""),
        "latest_season": row.get("latest_season", ""),
        "stats_first_expected_value": _format_number(value),
        "evidence_coverage": _format_number(row.get("evidence_coverage")),
        "weighted_seasons": row.get("weighted_seasons", ""),
        "top_component": _top_component(row.get("component_contributions")),
        "component_summary": _component_summary(row.get("component_contributions")),
        "missing_sections": _missing_sections(unavailable),
        "source_warning_count": len(warnings),
        "unavailable_section_count": len(unavailable),
        "external_projection_context_status": row.get(
            "external_projection_context_status",
            "",
        ),
        "projection_core_value_status": projection_core_value_status,
        "deep_history_status": deep_history_status,
        "issue_type": issue_type,
        "finding": finding,
        "next_action": next_action,
    }


def _missing_row(
    group: str,
    player: str,
    guardrails: dict[str, object],
) -> dict[str, object]:
    return {
        "group": group,
        "player": player,
        "matched_player": "",
        "match_status": "missing_stats_first_row",
        "position": "",
        "latest_season": "",
        "stats_first_expected_value": "",
        "evidence_coverage": "",
        "weighted_seasons": "",
        "top_component": "",
        "component_summary": "",
        "missing_sections": "stats_first_expected_value",
        "source_warning_count": "",
        "unavailable_section_count": "",
        "external_projection_context_status": "",
        "projection_core_value_status": guardrails["projection_core_value_status"],
        "deep_history_status": "missing_player",
        "issue_type": "data_issue",
        "finding": "No stats-first evidence row was generated for this audit player.",
        "next_action": (
            "Check identity mapping, source availability, and whether this player is "
            "an incoming rookie or outside historical data."
        ),
    }


def _default_audit_groups(truth_set_path: Path) -> dict[str, tuple[str, ...]]:
    return {
        "elite_rbs": ELITE_RBS,
        "elite_wrs": ELITE_WRS,
        "niners_roster": _niners_truth_set_players(truth_set_path),
        "qb_controls": QB_CONTROLS,
        "te_controls": TE_CONTROLS,
        "aging_retired_historical": AGING_OR_RETIRED_CONTROLS,
    }


def _niners_truth_set_players(truth_set_path: Path) -> tuple[str, ...]:
    if not truth_set_path.exists():
        return ()
    players: list[str] = []
    for row in _read_dicts(truth_set_path):
        roster_context = str(row.get("roster_context") or "").lower()
        truth_set_group = str(row.get("truth_set_group") or "").lower()
        if "niners" in roster_context or truth_set_group == "niners_roster":
            players.append(str(row.get("player_name") or ""))
    return tuple(player for player in players if player)


def _guardrail_summary(layer_summary: dict[str, Any]) -> dict[str, object]:
    projection_rows = _int(layer_summary.get("projection_context_rows_used_for_core_value"))
    route_metrics_used = _bool(layer_summary.get("route_metrics_used"))
    market_value_used = _bool(layer_summary.get("market_value_used"))
    league_rank_used = _bool(layer_summary.get("league_rank_used"))
    active_rankings_overwritten = _bool(layer_summary.get("active_rankings_overwritten"))
    return {
        "projection_core_value_rows": projection_rows,
        "projection_core_value_status": (
            "passes_no_projection_core_value"
            if projection_rows == 0
            else "fails_projection_used_in_core_value"
        ),
        "route_metrics_used": route_metrics_used,
        "market_value_used": market_value_used,
        "league_rank_used": league_rank_used,
        "active_rankings_overwritten": active_rankings_overwritten,
        "guardrail_status": (
            "passes"
            if projection_rows == 0
            and not route_metrics_used
            and not market_value_used
            and not league_rank_used
            and not active_rankings_overwritten
            else "review"
        ),
    }


def _deep_history_status(latest_season: int, value: float) -> str:
    if latest_season <= 0:
        return "missing_player"
    if latest_season <= 2022:
        if value > DEEP_HISTORY_REVIEW_THRESHOLD:
            return "deep_history_only_too_high"
        return "deep_history_only_not_boosted"
    return "current_or_recent_evidence"


def _issue_type(
    *,
    group: str,
    position: str,
    value: float,
    latest_season: int,
    deep_history_status: str,
    projection_core_value_status: str,
    unavailable: list[dict[str, str]],
) -> str:
    if projection_core_value_status != "passes_no_projection_core_value":
        return "data_issue"
    if deep_history_status == "deep_history_only_too_high":
        return "formula_data_issue"
    if group == "qb_controls" and position == "QB" and value >= HIGH_STATS_LAYER_QB_THRESHOLD:
        return "formula_context_needed"
    if latest_season <= 2022:
        return "no_issue"
    unavailable_sections = {row.get("component_or_section", "") for row in unavailable}
    if "route_metrics" in unavailable_sections and position in {"RB", "WR", "TE"}:
        return "source_limitation"
    return "no_issue"


def _finding_and_action(
    *,
    issue_type: str,
    group: str,
    position: str,
    value: float,
    latest_season: int,
    deep_history_status: str,
    projection_core_value_status: str,
) -> tuple[str, str]:
    if projection_core_value_status != "passes_no_projection_core_value":
        return (
            "Projection rows appear to be used in the stats-first core value.",
            "Block promotion and inspect the stats-first build inputs.",
        )
    if issue_type == "data_issue":
        return (
            "This player is missing stats-first evidence or has a guardrail failure.",
            "Repair identity/source mapping before using this layer for formula work.",
        )
    if deep_history_status == "deep_history_only_too_high":
        return (
            f"Only old evidence is present, but the stats-first value is {value:.2f}.",
            "Keep review-only and tighten recency weighting before formula integration.",
        )
    if issue_type == "formula_context_needed":
        return (
            "QB historical production can score highly in this evidence layer.",
            "Final v4 formula must apply 10-team 1QB positional suppression and receipts.",
        )
    if issue_type == "source_limitation":
        return (
            "Historical evidence is available, but licensed route metrics remain unavailable.",
            "Use as stats-first evidence and keep route-data limitation visible in receipts.",
        )
    if latest_season <= 2022:
        return (
            "Deep-history-only evidence is present but no longer creates current-asset value.",
            "No data repair needed; final formula should still handle retirement/"
            "current-status context.",
        )
    return (
        f"{group} {position} row has current/recent stats-first evidence.",
        "Use receipts and later formula tests before promotion.",
    )


def _summary(
    rows: list[dict[str, object]],
    guardrails: dict[str, object],
    layer_summary: dict[str, Any],
) -> dict[str, object]:
    issue_counts = Counter(str(row["issue_type"]) for row in rows)
    group_counts = Counter(str(row["group"]) for row in rows)
    deep_history_rows = [
        row
        for row in rows
        if str(row["deep_history_status"]).startswith("deep_history_only")
    ]
    top_deep_history = _top_value_row(deep_history_rows)
    return {
        "audit_rows": len(rows),
        "groups": dict(sorted(group_counts.items())),
        "issue_counts": dict(sorted(issue_counts.items())),
        "guardrails": guardrails,
        "layer_players": layer_summary.get("players", ""),
        "layer_component_rows": layer_summary.get("component_evidence_rows", ""),
        "layer_unavailable_rows": layer_summary.get("unavailable_rows", ""),
        "layer_source_warning_rows": layer_summary.get("source_warning_rows", ""),
        "top_deep_history_player": top_deep_history.get("matched_player", ""),
        "top_deep_history_value": top_deep_history.get("stats_first_expected_value", ""),
        "top_deep_history_status": top_deep_history.get("deep_history_status", ""),
    }


def _markdown(summary: dict[str, object], rows: list[dict[str, object]]) -> str:
    guardrails = summary["guardrails"]
    issue_counts = summary["issue_counts"]
    review_rows = [
        row
        for row in rows
        if row["issue_type"] not in {"no_issue", "source_limitation"}
    ]
    lines = [
        "# Phase 9D Stats-First Sanity Audit",
        "",
        "## Summary",
        "",
        f"- Audit rows: {summary['audit_rows']}",
        f"- Layer players: {summary['layer_players']}",
        f"- Component evidence rows: {summary['layer_component_rows']}",
        f"- Unavailable rows: {summary['layer_unavailable_rows']}",
        f"- Source warning rows: {summary['layer_source_warning_rows']}",
        f"- Issue counts: {json.dumps(issue_counts, sort_keys=True)}",
        "",
        "## Guardrails",
        "",
        f"- Overall guardrail status: {guardrails['guardrail_status']}",
        (
            "- Projection rows used for core value: "
            f"{guardrails['projection_core_value_rows']}"
        ),
        f"- Route metrics used: {guardrails['route_metrics_used']}",
        f"- Market value used: {guardrails['market_value_used']}",
        f"- League rank used: {guardrails['league_rank_used']}",
        f"- Active rankings overwritten: {guardrails['active_rankings_overwritten']}",
        "",
        "## Deep-History Check",
        "",
        (
            "- Top deep-history-only audit row: "
            f"{summary['top_deep_history_player']} "
            f"({summary['top_deep_history_value']}, "
            f"{summary['top_deep_history_status']})"
        ),
        "",
        "Deep-history-only players are not treated as current assets if their latest "
        "evidence ends in 2022 or earlier and their value remains below the review "
        f"threshold of {DEEP_HISTORY_REVIEW_THRESHOLD}.",
        "",
        "## Interpretation",
        "",
        "- This is a stats-evidence layer, not a final dynasty ranking.",
        "- High QB rows are expected here; the final v4 formula still has to apply "
        "10-team 1QB suppression.",
        "- Route metrics remain unavailable unless a licensed structured source is added.",
        "- 2026 imported projections are comparison-only and do not drive this layer.",
        "- Market value and league-rank rule context do not drive this layer.",
        "- Component evidence rows may show per-season deep-history evidence, while "
        "player rows collapse 2022-and-older evidence into one deep-history bucket.",
        "",
        "## Review Rows",
        "",
    ]
    if not review_rows:
        lines.append("No formula/data review rows were found beyond accepted source limitations.")
    else:
        lines.extend(_review_table(review_rows))
    return "\n".join(lines) + "\n"


def _review_table(rows: list[dict[str, object]]) -> list[str]:
    table = [
        "| Group | Player | Issue | Finding | Next action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        table.append(
            "| "
            + " | ".join(
                _md_cell(row.get(key, ""))
                for key in ("group", "matched_player", "issue_type", "finding", "next_action")
            )
            + " |"
        )
    return table


def _top_value_row(rows: list[dict[str, object]]) -> dict[str, object]:
    if not rows:
        return {}
    return max(rows, key=lambda row: _float(row.get("stats_first_expected_value")))


def _top_component(component_contributions: object) -> str:
    contributions = _json_dict(component_contributions)
    if not contributions:
        return ""
    name, value = max(contributions.items(), key=lambda item: _float(item[1]))
    return f"{name}:{_format_number(value)}"


def _component_summary(component_contributions: object) -> str:
    contributions = _json_dict(component_contributions)
    if not contributions:
        return ""
    parts = [
        f"{name}={_format_number(value)}"
        for name, value in sorted(
            contributions.items(),
            key=lambda item: _float(item[1]),
            reverse=True,
        )
    ]
    return "; ".join(parts)


def _missing_sections(rows: list[dict[str, str]]) -> str:
    sections = [
        str(row.get("component_or_section") or "")
        for row in rows
        if str(row.get("severity") or "") != "source_limitation"
    ]
    route_limited = any(
        row.get("component_or_section") == "route_metrics"
        for row in rows
    )
    if route_limited:
        sections.append("route_metrics_unavailable")
    return "|".join(section for section in sections if section)


def _rows_by_player(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    by_player: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_player[normalize_player_name(row.get("matched_model_player"))].append(row)
    return by_player


def _json_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_dicts(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _read_dicts_if_exists(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return _read_dicts(path)


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _format_number(value: object) -> str:
    if value in {None, ""}:
        return ""
    return f"{_float(value):.4f}".rstrip("0").rstrip(".")


def _float(value: object) -> float:
    try:
        return float(str(value or "0"))
    except ValueError:
        return 0.0


def _int(value: object) -> int:
    try:
        return int(float(str(value or "0")))
    except ValueError:
        return 0


def _bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _md_cell(value: object) -> str:
    return str(value).replace("|", "/").replace("\n", " ")
