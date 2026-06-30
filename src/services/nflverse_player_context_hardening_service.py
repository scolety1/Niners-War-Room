from __future__ import annotations

import csv
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from src.services.nflverse_refresh_health_service import NOT_ENOUGH_INFORMATION

REPO_ROOT = Path(__file__).resolve().parents[2]
DISPLAY_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_player_context_display_20260630"
)
IDENTITY_REVIEW_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_player_context_identity_review_20260630"
)
DEFAULT_OUTPUT_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_player_context_hardening_20260630"
)
DEFAULT_SCHEDULE_SNAPSHOT_DIR = Path(
    r"C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_context_hardening_schedule_20260630"
)

ARTIFACT_PATH = DISPLAY_DIR / "nflverse_player_context_display_artifact.csv"
JOIN_HEALTH_PATH = DISPLAY_DIR / "nflverse_player_context_join_health.csv"
IDENTITY_QUEUE_PATH = (
    IDENTITY_REVIEW_DIR / "nflverse_player_context_identity_review_queue.csv"
)
IDENTITY_PROPOSALS_PATH = (
    IDENTITY_REVIEW_DIR / "nflverse_player_context_identity_resolution_proposals.csv"
)

DISPLAY_ONLY = "true"
DENY = "false"
SAFE_NOW_DISPLAY_ONLY = "SAFE_NOW_DISPLAY_ONLY"

HUMAN_REVIEW_COLUMNS = (
    "nwr_player_id",
    "nwr_player_name",
    "nwr_position",
    "nwr_team",
    "current_identity_status",
    "proposed_nflverse_id",
    "proposed_gsis_id",
    "proposed_sleeper_id",
    "proposed_source",
    "proposal_confidence",
    "decision_needed",
    "recommended_human_action",
    "approved_by_human",
    "display_only",
    "model_use_allowed",
    "training_allowed",
    "source_truth_allowed",
    "notes",
)

FORBIDDEN_FLAGS = (
    "model_use_allowed",
    "training_allowed",
    "source_truth_allowed",
    "rank_logic_allowed",
    "hidden_sort_allowed",
    "trade_value_allowed",
    "pick_value_allowed",
)

MISSING_AS_BAD_TERMS = (
    "healthy",
    "no-role",
    "zero snaps",
    "confirmed udfa",
    "round 8",
)


@dataclass(frozen=True)
class HardeningResult:
    artifact_rows: int
    safe_rows: int
    identity_review_rows: int
    identity_proposals: int
    schedule_safe_rows: int
    schedule_future_rows: int
    artifact_rebuilt: bool


def write_nflverse_player_context_hardening_docs(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    artifact_path: Path = ARTIFACT_PATH,
    join_health_path: Path = JOIN_HEALTH_PATH,
    identity_queue_path: Path = IDENTITY_QUEUE_PATH,
    identity_proposals_path: Path = IDENTITY_PROPOSALS_PATH,
    schedule_snapshot_dir: Path = DEFAULT_SCHEDULE_SNAPSHOT_DIR,
    as_of: date | None = None,
    artifact_rebuilt: bool = True,
) -> HardeningResult:
    as_of_date = as_of or datetime.now(UTC).date()
    artifact_rows = _read_csv(artifact_path)
    join_health_rows = _read_csv(join_health_path)
    identity_rows = _read_csv(identity_queue_path)
    proposal_rows = _read_csv(identity_proposals_path)
    schedule_rows = _read_csv(schedule_snapshot_dir / "schedules.csv")
    output_dir.mkdir(parents=True, exist_ok=True)

    human_packet = tuple(_human_review_row(row) for row in proposal_rows)
    _write_csv(
        output_dir / "identity_resolution_human_review_packet.csv",
        human_packet,
        HUMAN_REVIEW_COLUMNS,
    )
    (output_dir / "player_context_artifact_qa_report.md").write_text(
        _artifact_qa_report(artifact_rows, join_health_rows),
        encoding="utf-8",
    )
    (output_dir / "schedule_future_coverage_audit.md").write_text(
        _schedule_audit_markdown(schedule_rows, as_of_date),
        encoding="utf-8",
    )
    (output_dir / "APP_LANE_CONSUMPTION_GUIDE_20260630.md").write_text(
        _app_lane_guide_markdown(),
        encoding="utf-8",
    )

    safe_rows = _safe_rows(artifact_rows)
    schedule_safe_rows = sum(
        1
        for row in artifact_rows
        if row["identity_join_status"] == SAFE_NOW_DISPLAY_ONLY
        and row["review_required"] == "false"
        and row["next_game_context"] != NOT_ENOUGH_INFORMATION
    )
    future_rows = sum(
        1
        for row in schedule_rows
        if (_parse_date(row.get("gameday")) or date.min) >= as_of_date
    )
    return HardeningResult(
        artifact_rows=len(artifact_rows),
        safe_rows=safe_rows,
        identity_review_rows=len(identity_rows),
        identity_proposals=sum(
            1 for row in proposal_rows if row["proposed_decision"] == "SAFE_RESOLUTION_PROPOSED"
        ),
        schedule_safe_rows=schedule_safe_rows,
        schedule_future_rows=future_rows,
        artifact_rebuilt=artifact_rebuilt,
    )


def _human_review_row(row: dict[str, str]) -> dict[str, str]:
    decision = row.get("proposed_decision", "")
    if decision == "SAFE_RESOLUTION_PROPOSED":
        action = "approve_or_reject_exact_local_identity_proposal"
    elif decision == "NEEDS_HUMAN_REVIEW":
        action = "review_ambiguous_or_incomplete_identity_evidence"
    else:
        action = "keep_need_identity_review_until_new_source_evidence_exists"
    return _ordered(
        {
            "nwr_player_id": row.get("nwr_player_id", NOT_ENOUGH_INFORMATION),
            "nwr_player_name": row.get("nwr_player_name", NOT_ENOUGH_INFORMATION),
            "nwr_position": row.get("nwr_position", NOT_ENOUGH_INFORMATION),
            "nwr_team": row.get("nwr_team", NOT_ENOUGH_INFORMATION),
            "current_identity_status": "NEED_IDENTITY_REVIEW",
            "proposed_nflverse_id": row.get("candidate_gsis_id", NOT_ENOUGH_INFORMATION),
            "proposed_gsis_id": row.get("candidate_gsis_id", NOT_ENOUGH_INFORMATION),
            "proposed_sleeper_id": row.get("candidate_sleeper_id", NOT_ENOUGH_INFORMATION),
            "proposed_source": row.get("candidate_source", NOT_ENOUGH_INFORMATION),
            "proposal_confidence": row.get("confidence", NOT_ENOUGH_INFORMATION),
            "decision_needed": row.get("proposed_decision", NOT_ENOUGH_INFORMATION),
            "recommended_human_action": action,
            "approved_by_human": DENY,
            "display_only": DISPLAY_ONLY,
            "model_use_allowed": DENY,
            "training_allowed": DENY,
            "source_truth_allowed": DENY,
            "notes": (
                row.get("notes", "")
                + " Identity proposal is not an approved join and is not exposed as safe."
            ).strip(),
        },
        HUMAN_REVIEW_COLUMNS,
    )


def _artifact_qa_report(
    artifact_rows: list[dict[str, str]],
    join_health_rows: list[dict[str, str]],
) -> str:
    safe = [row for row in artifact_rows if row["identity_join_status"] == SAFE_NOW_DISPLAY_ONLY]
    safe_and_unreviewed = [row for row in safe if row["review_required"] == "false"]
    nwr_ids = [row["nwr_player_id"] for row in artifact_rows]
    missing_ids = sum(1 for value in nwr_ids if value == NOT_ENOUGH_INFORMATION)
    duplicate_non_missing = [
        player_id
        for player_id, count in Counter(
            value for value in nwr_ids if value != NOT_ENOUGH_INFORMATION
        ).items()
        if count > 1
    ]
    missing_core = sum(
        1
        for row in safe_and_unreviewed
        if any(
            row[column] == NOT_ENOUGH_INFORMATION
            for column in (
                "nflverse_gsis_id",
                "nflverse_sleeper_id",
                "nflverse_player_name",
                "nflverse_team",
                "nflverse_position",
            )
        )
    )
    team_mismatch = _team_mismatch_rows(safe_and_unreviewed)
    contract_anomalies = _contract_anomaly_count(safe_and_unreviewed)
    flag_true = sum(
        1
        for row in artifact_rows
        for column in FORBIDDEN_FLAGS
        if row.get(column) == "true"
    )
    wording_hits = _wording_hits(artifact_rows)
    draft_missing = sum(
        1 for row in safe_and_unreviewed if row["draft_round"] == NOT_ENOUGH_INFORMATION
    )
    schedule_gate = next(row for row in join_health_rows if row["gate"] == "next_game_bye_gate")
    injury_years = Counter(
        _context_year(row["injury_report_date_week"]) for row in safe_and_unreviewed
    )
    snap_years = Counter(row["latest_snap_season"] for row in safe_and_unreviewed)
    return "\n".join(
        [
            "# NFLVerse Player Context Artifact QA Report",
            "",
            f"Artifact rows: `{len(artifact_rows)}`",
            f"Safe display rows: `{len(safe_and_unreviewed)}`",
            f"Identity review rows: `{len(artifact_rows) - len(safe_and_unreviewed)}`",
            f"Duplicate non-missing `nwr_player_id` values: `{len(duplicate_non_missing)}`",
            f"Missing `nwr_player_id` values: `{missing_ids}`",
            f"Safe rows with missing core nflverse identity fields: `{missing_core}`",
            f"Safe rows with suspicious team mismatch after alias normalization: `{team_mismatch}`",
            f"Contract context anomalies: `{contract_anomalies}`",
            f"Safe rows missing draft capital context: `{draft_missing}`",
            f"Forbidden flag true count: `{flag_true}`",
            f"Missing-as-zero/healthy/no-role/UDFA wording hits: `{wording_hits}`",
            "",
            "## Freshness",
            "",
            f"Injury context season counts: `{dict(injury_years)}`",
            "Depth context source freshness: `depth_charts remains review-only/status-only; "
            "source coverage is 2024 in the underlying refresh-health record`",
            f"Snap recency season counts: `{dict(snap_years)}`",
            f"Schedule safe rows after hardening overlay: `{schedule_gate['clean_join_rows']}`",
            "",
            "## Decision",
            "",
            "No identity proposals were approved. The artifact was rebuilt only to add "
            "approved current/future team-level schedule display context to rows that were "
            "already `SAFE_NOW_DISPLAY_ONLY` and `review_required=false`.",
        ]
    )


def _schedule_audit_markdown(rows: list[dict[str, str]], as_of: date) -> str:
    seasons = sorted({row["season"] for row in rows if row.get("season")})
    weeks = sorted({int(row["week"]) for row in rows if row.get("week")})
    dates = sorted(
        _parse_date(row.get("gameday")) for row in rows if _parse_date(row.get("gameday"))
    )
    future = [row for row in rows if (_parse_date(row.get("gameday")) or date.min) >= as_of]
    teams = sorted(
        {
            team
            for row in rows
            for team in (row.get("home_team"), row.get("away_team"))
            if team
        }
    )
    return "\n".join(
        [
            "# NFLVerse Schedule Future Coverage Audit",
            "",
            f"As-of date: `{as_of.isoformat()}`",
            f"Schedule rows refreshed by approved runner: `{len(rows)}`",
            f"Schedule seasons: `{';'.join(seasons)}`",
            f"Schedule weeks: `{weeks[0]}-{weeks[-1]}`",
            "Max game date before hardening packet: `2026-02-08`",
            f"Max game date after targeted 2026 schedules refresh: `{dates[-1].isoformat()}`",
            f"Current/future rows as of {as_of.isoformat()}: `{len(future)}`",
            f"Teams covered: `{len(teams)}`",
            "",
            "The approved safe runner can refresh schedules without scraping or private data. "
            "This lane ran `scripts/run_nflverse_refresh_v0.ps1 -Seasons 2026 -Datasets "
            "schedules -SnapshotLabel player_context_hardening_schedule_20260630`.",
            "",
            "The runner is not configured to pull 2026 by default; its default seasons are "
            "2024 and 2025. A targeted safe refresh fixed the schedule blocker for display "
            "context, while keeping raw output under `C:\\NWR_SHARED_DATA`.",
            "",
            "Team aliases are not the main blocker. The artifact uses nflverse team codes "
            "for safe rows; `LAR` maps to `LA` and `JAC` maps to `JAX` when NWR team values "
            "are needed.",
            "",
            "Allowed output remains team-level display context only: next game week/date, "
            "opponent, and bye week. No matchup strength, projected points, start/sit, win "
            "probability, rank/model input, hidden sort, trade value, or pick value is added.",
        ]
    )


def _app_lane_guide_markdown() -> str:
    return "\n".join(
        [
            "# App Lane Consumption Guide - NFLVerse Player Context",
            "",
            "All app lanes must read only the tracked player context artifact:",
            "",
            "`docs/hq/data_sources/nflverse_player_context_display_20260630/"
            "nflverse_player_context_display_artifact.csv`",
            "",
            "Never read raw `C:\\NWR_SHARED_DATA` from app pages.",
            "",
            "## Required Row Filter",
            "",
            "- Join by `nwr_player_id`.",
            "- Require `identity_join_status=SAFE_NOW_DISPLAY_ONLY`.",
            "- Require `review_required=false`.",
            "- Treat `Not enough information` as missing, not false/healthy/no-role/zero/UDFA.",
            "- Identity proposals are not approved joins.",
            "",
            "## Forbidden Uses",
            "",
            "Do not use NFLVerse player context for model input, rank logic, source truth, "
            "hidden sort, trade value, pick value, recommendations, start/sit, or "
            "valuation logic.",
            "",
            "## Lane Notes",
            "",
            "- Rankings / Outcome Lens: display-only fields may be shown after the required "
            "row filter; never sort/rank by them.",
            "- Player Compare: display only; do not score players from the fields.",
            "- Trading Lab: display only; no trade value or pick value use.",
            "- Development Lab: diagnostics/review only; no model promotion.",
            "- Draft Room / Analyzer: display context only; no recommendations or hidden sort.",
            "- Injury Availability: missing injury remains `Not enough information`, not healthy.",
            "- Rookie Outcomes: identity proposals remain review-only and are not current-player "
            "activation.",
            "",
            "Schedule/opponent/bye fields are available only when populated in the tracked "
            "artifact for safe identity rows. Missing schedule remains `Not enough information`.",
        ]
    )


def _team_mismatch_rows(rows: list[dict[str, str]]) -> int:
    aliases = {"LAR": "LA", "JAC": "JAX"}
    count = 0
    for row in rows:
        nwr_team = aliases.get(row["nwr_team"], row["nwr_team"])
        nflverse_team = aliases.get(row["nflverse_team"], row["nflverse_team"])
        if nwr_team not in {NOT_ENOUGH_INFORMATION, "needs_data"} and nwr_team != nflverse_team:
            count += 1
    return count


def _contract_anomaly_count(rows: list[dict[str, str]]) -> int:
    forbidden_terms = ("value=", "apy=", "guaranteed=", "cap=")
    return sum(
        1
        for row in rows
        if any(term in row["contract_context"].lower() for term in forbidden_terms)
    )


def _wording_hits(rows: list[dict[str, str]]) -> int:
    return sum(
        1
        for row in rows
        for value in row.values()
        for term in MISSING_AS_BAD_TERMS
        if term in value.lower()
    )


def _context_year(value: str) -> str:
    if value == NOT_ENOUGH_INFORMATION:
        return NOT_ENOUGH_INFORMATION
    for part in value.split(";"):
        text = part.strip()
        if text.startswith("season="):
            return text.removeprefix("season=")
    return NOT_ENOUGH_INFORMATION


def _safe_rows(rows: list[dict[str, str]]) -> int:
    return sum(
        1
        for row in rows
        if row["identity_join_status"] == SAFE_NOW_DISPLAY_ONLY
        and row["review_required"] == "false"
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: Iterable[dict[str, str]], columns: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _ordered(row: dict[str, Any], columns: tuple[str, ...]) -> dict[str, str]:
    return {column: str(row.get(column, "")) for column in columns}


def _parse_date(value: Any) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None
