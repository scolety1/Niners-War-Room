from __future__ import annotations

# ruff: noqa: E402,I001

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODEL_PREVIEW_ROOT = ROOT / "local_exports" / "nflverse_model_previews"
REPORT_ROOT = ROOT / "local_exports" / "truth_set_lab" / "v3" / "reports"
DOCS_ROOT = ROOT / "docs" / "codex"

GAP_HEADER = (
    "gap_id",
    "field_or_bucket",
    "status_bucket",
    "affected_players",
    "affected_player_count",
    "model_impact",
    "agent_action",
    "do_not_do",
    "next_local_action",
)

PROMPT_HEADER = (
    "prompt_id",
    "gap_ids",
    "agent_task",
    "prompt_file",
)


def main() -> None:
    preview = _latest_preview()
    if preview is None:
        raise FileNotFoundError("No Truth Set Lab v3 preview folder found.")
    coverage_rows = _read_rows(preview / "truth_set_v3_source_coverage.csv")
    suspicious_rows = _read_rows(REPORT_ROOT / "truth_set_v3_audit_suspicious_rankings.csv")

    gaps = _gap_rows(coverage_rows, suspicious_rows)
    prompts = _agent_prompts()

    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    gap_path = REPORT_ROOT / "truth_set_v3_remaining_agent_gap_list.csv"
    prompt_index_path = REPORT_ROOT / "truth_set_v3_agent_prompt_index.csv"
    prompt_doc_path = REPORT_ROOT / "truth_set_v3_agent_prompts.md"
    summary_path = REPORT_ROOT / "truth_set_v3_remaining_agent_gap_summary.json"
    _write_csv(gap_path, GAP_HEADER, gaps)
    _write_csv(
        prompt_index_path,
        PROMPT_HEADER,
        tuple(
            {
                "prompt_id": prompt_id,
                "gap_ids": "|".join(prompt["gap_ids"]),
                "agent_task": prompt["title"],
                "prompt_file": str(prompt_doc_path),
            }
            for prompt_id, prompt in prompts.items()
        ),
    )
    prompt_doc_path.write_text(_prompt_markdown(prompts), encoding="utf-8")
    summary = _summary(preview, gaps, prompts)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    _write_note(
        preview=preview,
        gap_path=gap_path,
        prompt_doc_path=prompt_doc_path,
        summary=summary,
        gaps=gaps,
    )
    print(json.dumps(summary, indent=2))


def _gap_rows(
    coverage_rows: list[dict[str, str]],
    suspicious_rows: list[dict[str, str]],
) -> tuple[dict[str, object], ...]:
    by_bucket: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in coverage_rows:
        by_bucket[row.get("bucket", "")].append(row)
    suspicious_by_type: dict[str, set[str]] = defaultdict(set)
    for row in suspicious_rows:
        suspicious_by_type[row.get("suspicion_type", "")].add(
            _display_name(row.get("player_name", ""))
        )

    route_players = _players_matching(
        by_bucket["route_participation"],
        coverage_status="review",
    )
    missing_projection_players = suspicious_by_type["missing_valid_projection"]
    missing_production_players = suspicious_by_type["missing_native_production"]
    missing_usage_players = suspicious_by_type["missing_derived_usage"]
    low_confidence_players = suspicious_by_type["low_confidence_or_blocking_warning"]
    injury_review_players = _players_matching(by_bucket["injury"], coverage_status="review")
    missing_market_players = _players_matching(
        by_bucket["market_liquidity"],
        coverage_status="missing",
    )
    rows = [
        _gap(
            "gap_route_participation",
            "routes_run|route_participation|TPRR|YPRR",
            "possible_paid_only_field",
            route_players,
            "WR/TE route-dependent formulas remain capped/review-only.",
            (
                "Find legal structured/exportable sources and field definitions. "
                "Verify whether any free source exists; otherwise identify paid/API options."
            ),
            "Do not manually chart routes, copy tables by hand, or infer routes from snaps.",
            "Keep route_role neutral until a validated structured source exists.",
        ),
        _gap(
            "gap_direct_first_down_projection",
            "projected rushing/receiving first downs",
            "can_derive_locally",
            _all_players(coverage_rows),
            "Projection points omit direct first-down projection signal.",
            (
                "Do not collect player-by-player stats. Verify whether any public/exportable "
                "projection source provides direct first-down projections."
            ),
            "Do not make manual first-down projections.",
            "If no direct source exists, use local historical first-down estimator preview only.",
        ),
        _gap(
            "gap_missing_projection_rows",
            "missing valid projection rows",
            "agent_can_verify_source",
            missing_projection_players,
            "Projection value remains missing or baseline-only for affected players.",
            (
                "Verify whether public/exportable projection rows exist for affected players "
                "from legal downloadable sources."
            ),
            "Do not scrape restricted sites or invent projections.",
            "Import only validated raw stat columns and recompute LVE points locally.",
        ),
        _gap(
            "gap_incoming_rookie_nfl_evidence",
            "incoming rookie production/usage/snap evidence",
            "agent_should_not_collect_manually",
            missing_production_players | missing_usage_players,
            "Incoming rookies correctly lack NFL production/usage evidence.",
            (
                "No agent stat collection needed unless a legal structured rookie "
                "projection source exists."
            ),
            "Do not manually compile college/NFL hybrid stats into veteran evidence.",
            (
                "Handle through rookie/young bridge and keep confidence lower until "
                "NFL evidence exists."
            ),
        ),
        _gap(
            "gap_sourced_injury_context",
            "injury status/history",
            "agent_can_verify_source",
            injury_review_players | low_confidence_players,
            "Unsourced healthy/injury context should not raise confidence.",
            (
                "Find structured/exportable injury sources with URLs, fields, update cadence, "
                "and licensing notes."
            ),
            "Do not manually collect healthy statuses or infer durability from blurbs.",
            "Use sourced rows as confidence context only unless schema is validated.",
        ),
        _gap(
            "gap_market_liquidity_context",
            "market/liquidity values",
            "agent_should_not_collect_manually",
            missing_market_players,
            "Market edge is unavailable for many rows, but private value is unaffected.",
            "No agent chase needed unless a legal export/API source is identified.",
            "Do not manually copy trade values or feed market into private value.",
            "Keep market as trade context only.",
        ),
    ]
    return tuple(rows)


def _agent_prompts() -> dict[str, dict[str, object]]:
    return {
        "agent_prompt_route_source_discovery": {
            "title": "Route/Participation Source Discovery",
            "gap_ids": ["gap_route_participation"],
            "body": ROUTE_SOURCE_PROMPT,
        },
        "agent_prompt_projection_gap_verification": {
            "title": "Projection Gap And First-Down Source Verification",
            "gap_ids": ["gap_direct_first_down_projection", "gap_missing_projection_rows"],
            "body": PROJECTION_SOURCE_PROMPT,
        },
        "agent_prompt_injury_source_discovery": {
            "title": "Structured Injury Source Discovery",
            "gap_ids": ["gap_sourced_injury_context"],
            "body": INJURY_SOURCE_PROMPT,
        },
    }


ROUTE_SOURCE_PROMPT = """
You are researching legal/exportable football role data sources.

Goal:
Find whether any free/public/exportable source provides structured route and
participation data for NFL fantasy modeling.

Need fields:
- routes run
- route participation / route share
- targets per route run
- yards per route run
- player ID fields
- season/week granularity
- CSV/API/download method
- update frequency
- licensing/terms risk

Rules:
- Do not manually compile player stats.
- Do not scrape forbidden or access-controlled pages.
- Do not infer routes from snaps or targets.
- Source discovery only: provide URLs, field lists, access method, cost/free status, and confidence.

Final output:
1. Best free/public structured source, if any.
2. Best low-cost/exportable source, if free sources do not exist.
3. Exact fields available and missing.
4. Whether this can safely feed a local-first model.
5. Recommendation: import now, preview only, paid trial, or do not use.
"""

PROJECTION_SOURCE_PROMPT = """
You are verifying projection source gaps for a local-first fantasy model.

Goal:
Find legal/exportable projection sources that provide raw stat projections, and
determine whether any source includes rushing/receiving first-down projections.

Need fields:
- games
- starts
- passing yards/TD/INT
- rushing attempts/yards/TD
- targets
- receptions
- receiving yards/TD
- rushing first downs if available
- receiving first downs if available
- player IDs or mapping fields
- CSV/API/download method
- update frequency
- licensing/terms risk

Specific check:
Public projections were missing or weak for some players. Verify whether a legal
downloadable/public source has raw stat rows for missing projection players, but
do not invent rows.

Rules:
- Do not manually compile player projections.
- Do not use supplied fantasy points unless raw stat scoring can be recomputed locally.
- Do not scrape forbidden sources.
- Report source availability and schema, not hand-entered stats.

Final output:
1. Sources with raw stat projection exports.
2. Whether direct first-down projections exist.
3. Exact fields and access method.
4. Missing players or fields.
5. Recommendation: import now, preview only, use local estimator, or do not use.
"""

INJURY_SOURCE_PROMPT = """
You are researching structured NFL injury data sources for a local-first fantasy model.

Goal:
Find legal/exportable injury sources that can be used as confidence context
without inventing healthy statuses.

Need fields:
- current injury status
- practice status
- body part / injury type
- IR/PUP/NFI
- game status
- games missed if available
- player ID fields
- source date
- CSV/API/download method
- update frequency
- licensing/terms risk

Rules:
- Do not manually collect healthy/active statuses from blurbs.
- Do not infer injury risk from news tone.
- Do not scrape forbidden sources.
- Source discovery only unless a clean export/API exists.

Final output:
1. Best free/public structured injury source.
2. Best low-cost/exportable source if free options are weak.
3. Exact fields and historical depth.
4. Which fields are reliable enough for confidence context.
5. Which fields should remain review-only.
6. Recommendation: import now, preview only, paid trial, or do not use.
"""


def _gap(
    gap_id: str,
    field: str,
    status: str,
    players: set[str],
    impact: str,
    action: str,
    do_not_do: str,
    next_action: str,
) -> dict[str, object]:
    return {
        "gap_id": gap_id,
        "field_or_bucket": field,
        "status_bucket": status,
        "affected_players": "|".join(sorted(player for player in players if player)),
        "affected_player_count": len({player for player in players if player}),
        "model_impact": impact,
        "agent_action": action,
        "do_not_do": do_not_do,
        "next_local_action": next_action,
    }


def _players_matching(
    rows: list[dict[str, str]],
    *,
    coverage_status: str,
) -> set[str]:
    return {
        _display_name(row.get("player_name", ""))
        for row in rows
        if row.get("coverage_status") == coverage_status
    }


def _all_players(rows: list[dict[str, str]]) -> set[str]:
    return {_display_name(row.get("player_name", "")) for row in rows}


def _display_name(value: object) -> str:
    text = " ".join(str(value or "").replace("\u00a0", " ").split()).strip()
    for suffix in (" III",):
        if text.endswith(suffix):
            text = text[: -len(suffix)]
    return text


def _summary(
    preview: Path,
    gaps: tuple[dict[str, object], ...],
    prompts: dict[str, dict[str, object]],
) -> dict[str, object]:
    status_counts = Counter(row["status_bucket"] for row in gaps)
    return {
        "v3_preview": str(preview),
        "gap_rows": len(gaps),
        "agent_prompt_count": len(prompts),
        "can_derive_locally": status_counts["can_derive_locally"],
        "unavailable_free_public": status_counts["unavailable_free_public"],
        "agent_can_verify_source": status_counts["agent_can_verify_source"],
        "agent_should_not_collect_manually": status_counts["agent_should_not_collect_manually"],
        "possible_paid_only_field": status_counts["possible_paid_only_field"],
        "manual_player_stat_compilation_requested": False,
        "review_status": "review_only",
    }


def _prompt_markdown(prompts: dict[str, dict[str, object]]) -> str:
    sections = [
        "# Truth Set Lab v3 Agent Prompts",
        "",
        (
            "Use these only for unresolved source discovery. Do not ask agents to "
            "manually compile player stats."
        ),
        "",
    ]
    for prompt_id, prompt in prompts.items():
        sections.extend(
            [
                f"## {prompt_id}",
                "",
                f"Gap IDs: `{'|'.join(prompt['gap_ids'])}`",
                "",
                "```text",
                str(prompt["body"]).strip(),
                "```",
                "",
            ]
        )
    return "\n".join(sections)


def _write_note(
    *,
    preview: Path,
    gap_path: Path,
    prompt_doc_path: Path,
    summary: dict[str, object],
    gaps: tuple[dict[str, object], ...],
) -> None:
    gap_lines = "\n".join(
        f"- `{row['gap_id']}`: {row['field_or_bucket']} "
        f"({row['status_bucket']}, {row['affected_player_count']} players)"
        for row in gaps
    )
    note = "\n".join(
        [
            "# Truth Set Lab v3 Remaining Agent Gap List",
            "",
            "Status: review-only. This phase does not change model scores.",
            "",
            "## Files",
            "",
            f"- v3 preview: `{preview}`",
            f"- gap list: `{gap_path}`",
            f"- agent prompts: `{prompt_doc_path}`",
            "",
            "## Summary",
            "",
            f"- Gap rows: {summary['gap_rows']}",
            f"- Agent prompts: {summary['agent_prompt_count']}",
            "- Manual player-stat compilation requested: false",
            "",
            "## Remaining Gaps",
            "",
            gap_lines,
            "",
            "## Guidance",
            "",
            "Agents should only verify legal/exportable source availability or schema. "
            "They should not manually compile player-stat tables, chart routes, infer "
            "healthy statuses, or scrape forbidden sources. Local code should continue "
            "to derive first-down estimates and LVE scoring where needed.",
            "",
        ]
    )
    (DOCS_ROOT / "TRUTH_SET_LAB_V3_REMAINING_AGENT_GAP_LIST.md").write_text(
        note,
        encoding="utf-8",
    )


def _latest_preview() -> Path | None:
    candidates = [
        path for path in MODEL_PREVIEW_ROOT.glob("truth_set_lab_v3_preview_*") if path.is_dir()
    ]
    return sorted(candidates, key=lambda path: path.stat().st_mtime)[-1] if candidates else None


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
