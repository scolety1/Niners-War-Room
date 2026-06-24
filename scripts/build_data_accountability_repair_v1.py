from __future__ import annotations

# ruff: noqa: E402,E501
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.services.data_accountability_service import (
    HIDDEN_DEFAULT_POSITIONS,
    NOT_ENOUGH_INFORMATION,
    build_free_agent_pool_audit,
    build_identity_coverage_audit,
    build_status_context,
    read_csv_rows,
    rostered_player_ids,
    sleeper_lookup,
    sleeper_records,
    write_csv_rows,
)
from src.services.draft_day_app_v1_service import (
    EXPECTED_PINNED_MANIFEST_HASH,
    EXPECTED_ROW_COUNT,
    PINNED_SNAPSHOT_MANIFEST,
    REPO_SAFE_FROZEN_BOARD_PATH,
    file_sha256,
)
from src.services.sleeper_import_service import DEFAULT_LEAGUE_ID, SleeperHttpClient

DATA_ROOT = REPO_ROOT / "docs" / "hq" / "data_sources"
CURRENT_CONTEXT_ROOT = DATA_ROOT / "current_context"
IDENTITY_ROOT = DATA_ROOT / "identity"

PDF_FA_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "overnight_accuracy_max_20260622"
    / "free_agent_pdf_page3_draftable_pool.csv"
)
TUNED_OVERLAY_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "overnight_accuracy_max_20260622"
    / "tuned_v2_current_draft_pool_overlay.csv"
)
EMERGENCY_OVERLAY_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "overnight_8h_emergency_20260622"
    / "emergency_cross_asset_candidate_player_board.csv"
)
DP_CROSSWALK_AUDIT_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "dynastyprocess_market_baseline_20260622"
    / "dp_playerid_crosswalk_audit.csv"
)
OUTCOME_MATCH_TABLE_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "NWR_OUTCOME_COLUMNS_COVERAGE_MATCH_TABLE_20260622.csv"
)
CONTROL_DYNASTY_BOARD_PATH = (
    Path(r"C:\NWR\Niners-War-Room")
    / "local_exports"
    / "model_v4"
    / "current_value"
    / "latest"
    / "full_player_board_value_review_rows.csv"
)

FREE_AGENT_AUDIT_FIELDS = [
    "audit_scope",
    "player",
    "pos",
    "pdf_team",
    "sleeper_team",
    "pdf_overall_rank_or_number",
    "pdf_position_rank",
    "sleeper_player_id",
    "match_method",
    "match_confidence",
    "sleeper_current_roster_state",
    "include_default",
    "exclude_reason",
    "audit_category",
    "status_warning",
    "source_note",
]
STATUS_FIELDS = [
    "player",
    "pos",
    "nfl_team",
    "sleeper_player_id",
    "sleeper_team",
    "status",
    "injury_status",
    "injury_start_date",
    "practice_participation",
    "age",
    "years_exp",
    "warning_classification",
    "source_note",
]
IDENTITY_FIELDS = [
    "source_surface",
    "player_name",
    "position",
    "team",
    "existing_id_present",
    "sleeper_id",
    "dynastyprocess_id",
    "nflverse_id_or_gsis",
    "match_method",
    "match_confidence",
    "needs_manual_review",
    "reason",
]


def main() -> int:
    CURRENT_CONTEXT_ROOT.mkdir(parents=True, exist_ok=True)
    IDENTITY_ROOT.mkdir(parents=True, exist_ok=True)

    run_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    runtime_status = "GREEN_RUNTIME_PULL"
    runtime_error = ""
    rosters: list[dict[str, Any]] = []
    sleeper_players: dict[str, dict[str, Any]] = {}
    try:
        client = SleeperHttpClient()
        rosters = client.get_json(f"league/{DEFAULT_LEAGUE_ID}/rosters")
        sleeper_players = client.get_json("players/nfl")
    except Exception as exc:  # pragma: no cover - exercised only when network is unavailable
        runtime_status = "YELLOW_NOT_RUN"
        runtime_error = f"{type(exc).__name__}: {exc}"

    sleeper_rows = sleeper_records(sleeper_players) if sleeper_players else []
    rostered_ids = rostered_player_ids(rosters)
    sleeper_by_key = sleeper_lookup(sleeper_rows)

    frozen_rows = read_csv_rows(REPO_SAFE_FROZEN_BOARD_PATH)
    pdf_rows = read_csv_rows(PDF_FA_PATH)
    dp_rows = read_csv_rows(DP_CROSSWALK_AUDIT_PATH)
    full_dynasty_rows = read_csv_rows(CONTROL_DYNASTY_BOARD_PATH)
    tuned_rows = read_csv_rows(TUNED_OVERLAY_PATH)
    emergency_rows = read_csv_rows(EMERGENCY_OVERLAY_PATH)
    outcome_rows = read_csv_rows(OUTCOME_MATCH_TABLE_PATH)

    free_agent_audit = (
        build_free_agent_pool_audit(
            pdf_rows=pdf_rows,
            sleeper_rows=sleeper_rows,
            rostered_ids=rostered_ids,
        )
        if sleeper_rows
        else _yellow_free_agent_rows(pdf_rows, runtime_error)
    )
    status_context_source = _dedupe_status_source(frozen_rows + pdf_rows + tuned_rows)
    status_context = (
        build_status_context(status_context_source, sleeper_by_key)
        if sleeper_rows
        else _yellow_status_rows(status_context_source, runtime_error)
    )
    surfaces = {
        "frozen_final_board_v1": frozen_rows,
        "lve_pdf_page3_free_agents": pdf_rows,
        "outcome_numeric_display_support": outcome_rows,
        "dynastyprocess_market_baseline_crosswalk": dp_rows,
        "tuned_v2_candidate_overlay": tuned_rows,
        "emergency_cross_asset_candidate_overlay": emergency_rows,
    }
    if full_dynasty_rows:
        surfaces["full_dynasty_board_model_v4"] = full_dynasty_rows
    identity_audit = build_identity_coverage_audit(
        surfaces=surfaces,
        sleeper_rows=sleeper_rows,
        dynastyprocess_rows=dp_rows,
    )
    manual_review = [
        row for row in identity_audit if row.get("needs_manual_review") == "yes"
    ]

    write_csv_rows(
        CURRENT_CONTEXT_ROOT / "sleeper_pdf_free_agent_pool_audit_v1.csv",
        free_agent_audit,
        FREE_AGENT_AUDIT_FIELDS,
    )
    write_csv_rows(
        CURRENT_CONTEXT_ROOT / "sleeper_player_status_context_sample_or_current_v1.csv",
        status_context,
        STATUS_FIELDS,
    )
    write_csv_rows(
        IDENTITY_ROOT / "player_id_coverage_audit_v1.csv",
        identity_audit,
        IDENTITY_FIELDS,
    )
    write_csv_rows(
        IDENTITY_ROOT / "player_identity_manual_review_queue_v1.csv",
        manual_review,
        IDENTITY_FIELDS,
    )
    _write_status_schema(CURRENT_CONTEXT_ROOT / "sleeper_player_status_context_schema_v1.json")

    health = _health_summary(
        runtime_status=runtime_status,
        runtime_error=runtime_error,
        frozen_rows=frozen_rows,
        pdf_rows=pdf_rows,
        free_agent_audit=free_agent_audit,
        status_context=status_context,
        identity_audit=identity_audit,
        outcome_rows=outcome_rows,
        run_at=run_at,
    )
    _write_free_agent_report(
        path=CURRENT_CONTEXT_ROOT / "NWR_SLEEPER_FREE_AGENT_POOL_VERIFICATION_V1_20260623.md",
        health=health,
        free_agent_audit=free_agent_audit,
    )
    _write_status_report(
        path=CURRENT_CONTEXT_ROOT / "NWR_SLEEPER_STATUS_CONTEXT_V1_20260623.md",
        health=health,
        status_context=status_context,
    )
    _write_identity_report(
        path=IDENTITY_ROOT / "NWR_PLAYER_ID_COVERAGE_AUDIT_V1_20260623.md",
        health=health,
        identity_audit=identity_audit,
        manual_review=manual_review,
    )
    _write_accountability_report(
        path=DATA_ROOT / "NWR_DATA_ACCOUNTABILITY_REPAIR_REPORT_20260623.md",
        health=health,
    )
    _write_gap_resolution_plan(
        path=DATA_ROOT / "NWR_DATA_GAP_RESOLUTION_PLAN_20260623.md",
        health=health,
    )

    print(json.dumps(health, indent=2, sort_keys=True))
    return 0


def _dedupe_status_source(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    output: list[dict[str, str]] = []
    for row in rows:
        name = str(row.get("player") or row.get("player_name") or "").strip()
        position = str(row.get("pos") or row.get("position") or "").strip().upper()
        key = (name.lower(), position)
        if not name or not position or key in seen:
            continue
        seen.add(key)
        output.append(row)
    return output


def _yellow_free_agent_rows(pdf_rows: list[dict[str, str]], error: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in pdf_rows:
        pos = str(row.get("pos") or row.get("position") or "").upper()
        rows.append(
            {
                "audit_scope": "pdf_page3_free_agent",
                "player": str(row.get("player") or ""),
                "pos": pos,
                "pdf_team": str(row.get("nfl_team") or ""),
                "sleeper_team": "",
                "pdf_overall_rank_or_number": str(row.get("pdf_overall_rank_or_number") or ""),
                "pdf_position_rank": str(row.get("pdf_position_rank") or ""),
                "sleeper_player_id": "",
                "match_method": "runtime_not_run",
                "match_confidence": "LOW",
                "sleeper_current_roster_state": NOT_ENOUGH_INFORMATION,
                "include_default": "no" if pos in HIDDEN_DEFAULT_POSITIONS else "yes",
                "exclude_reason": "K/DST hidden by default" if pos in HIDDEN_DEFAULT_POSITIONS else "",
                "audit_category": "YELLOW_NOT_RUN",
                "status_warning": "missing status metadata",
                "source_note": f"Sleeper runtime unavailable; schema/docs emitted. {error}",
            }
        )
    return rows


def _yellow_status_rows(rows: list[dict[str, str]], error: str) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for row in rows:
        output.append(
            {
                "player": str(row.get("player") or row.get("player_name") or ""),
                "pos": str(row.get("pos") or row.get("position") or "").upper(),
                "nfl_team": str(row.get("nfl_team") or row.get("team") or "").upper(),
                "sleeper_player_id": "",
                "sleeper_team": "",
                "status": NOT_ENOUGH_INFORMATION,
                "injury_status": NOT_ENOUGH_INFORMATION,
                "injury_start_date": NOT_ENOUGH_INFORMATION,
                "practice_participation": NOT_ENOUGH_INFORMATION,
                "age": NOT_ENOUGH_INFORMATION,
                "years_exp": NOT_ENOUGH_INFORMATION,
                "warning_classification": "missing status metadata",
                "source_note": f"Sleeper runtime unavailable; do not infer clean health. {error}",
            }
        )
    return output


def _write_status_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "NWR Sleeper Player Status Context V1",
        "type": "object",
        "required": STATUS_FIELDS,
        "properties": {
            field: {"type": "string", "description": _schema_description(field)}
            for field in STATUS_FIELDS
        },
        "additionalProperties": False,
        "guardrail": (
            "Sleeper status fields are warning/diagnostic context only and are not "
            "full injury/news analysis or rank/model inputs."
        ),
    }
    path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")


def _schema_description(field: str) -> str:
    descriptions = {
        "sleeper_player_id": "Sleeper identity key when matched safely.",
        "status": "Raw Sleeper player status flag when available.",
        "injury_status": "Raw Sleeper injury_status flag when available.",
        "warning_classification": "clean, injury/status review, team/status mismatch, or missing status metadata.",
        "source_note": "Required warning that Sleeper is not a full injury/news feed.",
    }
    return descriptions.get(field, "Display-only status context field.")


def _health_summary(
    *,
    runtime_status: str,
    runtime_error: str,
    frozen_rows: list[dict[str, str]],
    pdf_rows: list[dict[str, str]],
    free_agent_audit: list[dict[str, str]],
    status_context: list[dict[str, str]],
    identity_audit: list[dict[str, str]],
    outcome_rows: list[dict[str, str]],
    run_at: str,
) -> dict[str, Any]:
    fa_categories = Counter(row["audit_category"] for row in free_agent_audit)
    status_counts = Counter(row["warning_classification"] for row in status_context)
    missing_age = sum(
        1
        for row in status_context
        if str(row.get("age") or "").strip() in {"", NOT_ENOUGH_INFORMATION}
    )
    missing_team = sum(
        1
        for row in status_context
        if str(row.get("sleeper_team") or row.get("nfl_team") or "").strip()
        in {"", NOT_ENOUGH_INFORMATION}
    )
    identity_confidence = Counter(row["match_confidence"] for row in identity_audit)
    source_surface_counts = Counter(row["source_surface"] for row in identity_audit)
    manual_review_count = sum(
        1 for row in identity_audit if row.get("needs_manual_review") == "yes"
    )
    outcome_support = sum(
        1
        for row in outcome_rows
        if str(row.get("prop_match_status") or "").startswith("matched")
    )
    outcome_missing = sum(
        1
        for row in outcome_rows
        if not str(row.get("prop_match_status") or "").startswith("matched")
    )
    pinned_hash = (
        file_sha256(PINNED_SNAPSHOT_MANIFEST).upper()
        if PINNED_SNAPSHOT_MANIFEST.exists()
        else NOT_ENOUGH_INFORMATION
    )
    return {
        "run_at": run_at,
        "runtime_status": runtime_status,
        "runtime_error": runtime_error,
        "frozen_board_rows": len(frozen_rows),
        "expected_frozen_board_rows": EXPECTED_ROW_COUNT,
        "pinned_hash": pinned_hash,
        "expected_pinned_hash": EXPECTED_PINNED_MANIFEST_HASH,
        "pdf_free_agent_rows": len(pdf_rows),
        "pdf_include_default_yes": sum(1 for row in pdf_rows if row.get("include_default") == "yes"),
        "pdf_kdst_hidden_default": sum(
            1
            for row in pdf_rows
            if str(row.get("pos") or "").upper() in HIDDEN_DEFAULT_POSITIONS
            or row.get("include_default") == "no"
        ),
        "sleeper_pdf_audit_rows": len(free_agent_audit),
        "sleeper_pdf_audit_categories": dict(fa_categories),
        "status_context_rows": len(status_context),
        "status_warning_counts": dict(status_counts),
        "status_missing_age_rows": missing_age,
        "status_missing_team_rows": missing_team,
        "identity_audit_rows": len(identity_audit),
        "identity_confidence_counts": dict(identity_confidence),
        "identity_manual_review_count": manual_review_count,
        "identity_surface_counts": dict(source_surface_counts),
        "outcome_rows": len(outcome_rows),
        "outcome_supported_rows": outcome_support,
        "outcome_not_enough_information_rows": outcome_missing,
        "not_enough_information_policy": (
            "Missing Outcome, status, age, role, injury, and ID data remain "
            f"`{NOT_ENOUGH_INFORMATION}` and must not be converted to zero/blank."
        ),
        "market_policy": "DynastyProcess/ADP/vendor/market fields remain display-only.",
    }


def _write_free_agent_report(
    *,
    path: Path,
    health: dict[str, Any],
    free_agent_audit: list[dict[str, str]],
) -> None:
    categories = health["sleeper_pdf_audit_categories"]
    examples = _sample_rows(
        free_agent_audit,
        lambda row: row.get("audit_scope") == "pdf_page3_free_agent",
        ["player", "pos", "audit_category", "sleeper_current_roster_state", "status_warning"],
    )
    _write_markdown(
        path,
        f"""# NWR Sleeper Free-Agent Pool Verification V1 - 20260623

## Verdict
{health['runtime_status']}

Sleeper is used here as a current league-state verifier and metadata layer. The LVE PDF page 3 free-agent list remains the human-confirmed 2026 draftable pool unless Tim/Master changes policy.

## Counts
- PDF page 3 rows: {health['pdf_free_agent_rows']}
- PDF include-default rows: {health['pdf_include_default_yes']}
- PDF K/DST hidden/excluded by default: {health['pdf_kdst_hidden_default']}
- Sleeper/PDF audit rows: {health['sleeper_pdf_audit_rows']}
- Audit categories: `{categories}`

## Sample PDF Audit Rows
{examples}

## Guardrails
- PDF ranks and Sleeper metadata are display/source context only.
- Sleeper unrostered rows that are not in the PDF are verifier/update candidates, not draftable source truth.
- K/DST are retained in audit where present but hidden by default.
- No rank, model, frozen board, latest, approved, or pinned artifact was mutated.
""",
    )


def _write_status_report(
    *,
    path: Path,
    health: dict[str, Any],
    status_context: list[dict[str, str]],
) -> None:
    examples = _sample_rows(
        status_context,
        lambda row: row.get("warning_classification") != "clean",
        ["player", "pos", "nfl_team", "warning_classification", "source_note"],
    )
    _write_markdown(
        path,
        f"""# NWR Sleeper Status Context V1 - 20260623

## Verdict
{health['runtime_status']}

Sleeper provides status flags, not full injury/news analysis. These fields are warning and diagnostic context only; they are not model inputs and do not change NWR rank/value.

## Warning Counts
`{health['status_warning_counts']}`

## Sample Warning Rows
{examples}

## Required Missing-Data Behavior
Missing injury/status/age metadata means `{NOT_ENOUGH_INFORMATION}`. It does not mean clean health.
""",
    )


def _write_identity_report(
    *,
    path: Path,
    health: dict[str, Any],
    identity_audit: list[dict[str, str]],
    manual_review: list[dict[str, str]],
) -> None:
    examples = _sample_rows(
        manual_review,
        lambda _row: True,
        ["source_surface", "player_name", "position", "match_method", "reason"],
    )
    _write_markdown(
        path,
        f"""# NWR Player ID Coverage Audit V1 - 20260623

## Verdict
YELLOW-GREEN

The audit now covers frozen board, PDF free agents, Outcome support rows, DynastyProcess crosswalk rows, and current candidate/live draft overlays. High-confidence matches require existing ID evidence or exact name+position support from admitted crosswalks. No silent fuzzy join is trusted.

## Counts
- Identity rows audited: {health['identity_audit_rows']}
- Confidence counts: `{health['identity_confidence_counts']}`
- Manual review rows: {health['identity_manual_review_count']}
- Surface counts: `{health['identity_surface_counts']}`

## Manual Review Sample
{examples}

## Guardrail
Unresolved players remain visible in reports/app contexts, but must carry manual review / `{NOT_ENOUGH_INFORMATION}` instead of fabricated evidence.
""",
    )


def _write_accountability_report(path: Path, health: dict[str, Any]) -> None:
    verdict = "GREEN" if health["runtime_status"] == "GREEN_RUNTIME_PULL" else "YELLOW"
    _write_markdown(
        path,
        f"""# NWR Data Accountability Repair Report - 20260623

## Final Verdict
{verdict}

## What Was Fixed
- Built Sleeper current free-agent verification against the LVE PDF page 3 pool.
- Built Sleeper status/injury metadata warning context with explicit partial-source language.
- Built player ID coverage audit and manual review queue across key surfaces.
- Preserved K/DST hidden-by-default behavior in the audit.
- Preserved `{NOT_ENOUGH_INFORMATION}` for missing Outcome/status/injury/ID evidence.

## Data Health Snapshot
- Frozen board rows: {health['frozen_board_rows']} / expected {health['expected_frozen_board_rows']}
- Pinned hash: `{health['pinned_hash']}`
- Source freshness status: {health['runtime_status']} at {health['run_at']}
- PDF rows: {health['pdf_free_agent_rows']}
- PDF include-default rows: {health['pdf_include_default_yes']}
- PDF K/DST hidden default rows: {health['pdf_kdst_hidden_default']}
- Sleeper/PDF audit categories: `{health['sleeper_pdf_audit_categories']}`
- Status warning counts: `{health['status_warning_counts']}`
- Missing Sleeper age rows in status context: {health['status_missing_age_rows']}
- Missing team rows in status context: {health['status_missing_team_rows']}
- Identity confidence counts: `{health['identity_confidence_counts']}`
- Manual identity review rows: {health['identity_manual_review_count']}
- Outcome support rows: {health['outcome_supported_rows']}
- Outcome `{NOT_ENOUGH_INFORMATION}` rows: {health['outcome_not_enough_information_rows']}

## Remaining Caveats
- Sleeper status flags are not full injury/news analysis.
- Sleeper unrostered rows not present in LVE PDF page 3 are verifier/update candidates only.
- DynastyProcess/ADP/vendor/market fields remain display-only and cannot drive NWR value.
- Complete historical trade history and verified historical dropped-veteran truth remain research gaps.

## Outputs
- `docs/hq/data_sources/current_context/sleeper_pdf_free_agent_pool_audit_v1.csv`
- `docs/hq/data_sources/current_context/sleeper_player_status_context_sample_or_current_v1.csv`
- `docs/hq/data_sources/current_context/sleeper_player_status_context_schema_v1.json`
- `docs/hq/data_sources/identity/player_id_coverage_audit_v1.csv`
- `docs/hq/data_sources/identity/player_identity_manual_review_queue_v1.csv`

## Guardrail Confirmation
No frozen board, final_board_rank, Dynasty Rank, latest_candidate, latest_approved, pinned snapshot, model logic, market input, or raw shared-data artifact is intentionally mutated by this lane.
""",
    )


def _write_gap_resolution_plan(path: Path, health: dict[str, Any]) -> None:
    _write_markdown(
        path,
        f"""# NWR Data Gap Resolution Plan - 20260623

## Fix Now
- Current PDF/Sleeper free-agent verification: implemented as derived audit.
- Sleeper player status metadata warning context: implemented as display-only diagnostics.
- Player ID coverage audit/manual review queue: implemented.
- K/DST hidden-by-default audit: implemented.

## Partially Fix Now
- Current team/status repair: Sleeper metadata helps identify mismatches but does not replace manual/official review.
- Rookie age/DOB gap: Sleeper age metadata is available when matched; missing age remains `{NOT_ENOUGH_INFORMATION}`.
- Outcome support gaps: current app/data must keep same-position missing values as `{NOT_ENOUGH_INFORMATION}`.

## Cannot Fix Without Old Archives/API/License
- Complete historical trade history.
- Complete historical dropped-veteran league truth.
- Full injury/news/role context.
- Approved 2026/2027/next-5-year Outcome probability artifacts.
- Exact ADP for this specific rookie/free-agent keeper draft.

## Defer To Research Lane
- nflverse participation/routes/snaps and first-down reconstruction.
- CollegeFootballData rookie production intake after identity gates.
- Licensed factual route/red-zone/role fields after policy approval.
- DynastyProcess app wiring after Master accepts the market-baseline contract lane.

## Current Status
Runtime status: {health['runtime_status']}. Manual identity-review rows: {health['identity_manual_review_count']}.
""",
    )


def _sample_rows(
    rows: list[dict[str, str]],
    predicate: Any,
    columns: list[str],
    limit: int = 8,
) -> str:
    selected = [row for row in rows if predicate(row)][:limit]
    if not selected:
        return "_No sample rows._"
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| "
        + " | ".join(str(row.get(column, "")).replace("|", "/") for column in columns)
        + " |"
        for row in selected
    ]
    return "\n".join([header, sep, *body])


def _write_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
