from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from src.services.nflverse_player_context_display_service import (
    NEED_IDENTITY_REVIEW,
    SAFE_NOW_DISPLAY_ONLY,
)
from src.services.nflverse_refresh_health_service import NOT_ENOUGH_INFORMATION

REPO_ROOT = Path(__file__).resolve().parents[2]
PLAYER_CONTEXT_DIR = (
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
REFRESH_HEALTH_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_dataset_level_refresh_health_20260630"
)
ARTIFACT_PATH = PLAYER_CONTEXT_DIR / "nflverse_player_context_display_artifact.csv"
SCHEMA_MANIFEST_PATH = PLAYER_CONTEXT_DIR / "nflverse_player_context_schema_manifest.csv"
IDENTITY_REVIEW_QUEUE_PATH = (
    IDENTITY_REVIEW_DIR / "nflverse_player_context_identity_review_queue.csv"
)
DATASET_REGISTRY_PATH = REFRESH_HEALTH_DIR / "nflverse_dataset_registry_v1.csv"
DATASET_COVERAGE_PATH = REFRESH_HEALTH_DIR / "nflverse_dataset_coverage_matrix_v1.csv"

NEEDS_IDENTITY_REVIEW_LABEL = "Needs identity review"
SAFE_CONTEXT_READY = "SAFE_REFRESH_CONTEXT_READY_DISPLAY_ONLY"
SCHEDULE_UNAVAILABLE = "SCHEDULE_CONTEXT_UNAVAILABLE"
FF_RANKINGS_BLOCKED = "BLOCKED_VENDOR_OR_PRIVATE"

UNAVAILABLE_VALUES = {
    "",
    NOT_ENOUGH_INFORMATION,
    NEED_IDENTITY_REVIEW,
    "NEED_DATASET_REFRESH",
    "NEED_SCHEMA_REVIEW",
    "BLOCKED_SOURCE_POLICY",
    "BLOCKED_VENDOR_OR_PRIVATE",
    "Review needed",
}

CONTEXT_FIELD_LABELS = {
    "nwr_player_id": "NWR Player ID",
    "nwr_player_name": "Player",
    "nwr_position": "NWR Position",
    "nwr_team": "NWR Team",
    "nflverse_team": "NFLVerse Team",
    "nflverse_position": "NFLVerse Position",
    "roster_birth_date_derived_age": "Age",
    "age_source": "Age Source",
    "roster_status": "Roster Status",
    "weekly_roster_status": "Weekly Roster Status",
    "injury_report_status": "Injury Report Status",
    "injury_report_date_week": "Injury Report Date/Week",
    "practice_status": "Practice Status",
    "depth_chart_position": "Depth Chart Position",
    "depth_chart_rank": "Depth Chart Slot",
    "depth_chart_role": "Depth Chart Role",
    "snap_count_recency": "Snap Recency",
    "latest_snap_season": "Latest Snap Season",
    "latest_snap_week": "Latest Snap Week",
    "snap_sample_size": "Snap Sample",
    "last_active_season": "Last Active Season",
    "last_active_week": "Last Active Week",
    "draft_year": "NFL Draft Year",
    "draft_round": "NFL Draft Round",
    "draft_pick": "NFL Draft Pick",
    "drafted_team": "Drafted Team",
    "contract_context": "Contract Context",
    "per_field_dataset_source": "Source Label",
    "per_field_freshness_source_status": "Freshness Label",
    "data_coverage_status": "Coverage Label",
}

ROSTER_CONTEXT_FIELDS = (
    "nwr_player_id",
    "nwr_player_name",
    "nwr_position",
    "nwr_team",
    "nflverse_team",
    "nflverse_position",
    "roster_birth_date_derived_age",
    "age_source",
    "roster_status",
    "weekly_roster_status",
    "injury_report_status",
    "injury_report_date_week",
    "practice_status",
    "last_active_season",
    "last_active_week",
    "snap_count_recency",
    "snap_sample_size",
    "per_field_dataset_source",
    "per_field_freshness_source_status",
    "data_coverage_status",
)

DEADLINE_CONTEXT_FIELDS = (
    "nwr_player_id",
    "nwr_player_name",
    "nwr_position",
    "nwr_team",
    "nflverse_team",
    "roster_status",
    "weekly_roster_status",
    "injury_report_status",
    "practice_status",
    "depth_chart_position",
    "depth_chart_rank",
    "depth_chart_role",
    "last_active_season",
    "last_active_week",
    "contract_context",
    "per_field_dataset_source",
    "per_field_freshness_source_status",
    "data_coverage_status",
)

DRAFT_CONTEXT_FIELDS = (
    "nwr_player_id",
    "nwr_player_name",
    "nwr_position",
    "nwr_team",
    "nflverse_team",
    "nflverse_position",
    "draft_year",
    "draft_round",
    "draft_pick",
    "drafted_team",
    "per_field_dataset_source",
    "per_field_freshness_source_status",
    "data_coverage_status",
)


@dataclass(frozen=True)
class DevelopmentLabNflverseContext:
    artifact_rows: tuple[dict[str, str], ...]
    schema_rows: tuple[dict[str, str], ...]
    identity_review_rows: tuple[dict[str, str], ...]
    dataset_registry_rows: tuple[dict[str, str], ...]
    dataset_coverage_rows: tuple[dict[str, str], ...]

    @property
    def safe_rows(self) -> tuple[dict[str, str], ...]:
        return tuple(
            row
            for row in self.artifact_rows
            if row.get("identity_join_status") == SAFE_NOW_DISPLAY_ONLY
            and row.get("review_required") == "false"
            and row.get("display_only") == "true"
            and _all_guardrail_flags_false(row)
        )

    @property
    def needs_identity_review_rows(self) -> tuple[dict[str, str], ...]:
        return tuple(
            row
            for row in self.artifact_rows
            if row.get("identity_join_status") == NEED_IDENTITY_REVIEW
            or row.get("review_required") == "true"
        )

    @property
    def allowed_fields(self) -> set[str]:
        return {
            row["column_name"]
            for row in self.schema_rows
            if row.get("field_status") == SAFE_NOW_DISPLAY_ONLY
            and row.get("display_only") == "true"
            and row.get("model_use_allowed") == "false"
            and row.get("training_allowed") == "false"
            and row.get("source_truth_allowed") == "false"
            and row.get("rank_logic_allowed") == "false"
            and row.get("hidden_sort_allowed") == "false"
            and row.get("trade_value_allowed") == "false"
            and row.get("pick_value_allowed") == "false"
        }


def load_development_lab_nflverse_context() -> DevelopmentLabNflverseContext:
    return DevelopmentLabNflverseContext(
        artifact_rows=tuple(_load_csv_rows(ARTIFACT_PATH)),
        schema_rows=tuple(_load_csv_rows(SCHEMA_MANIFEST_PATH)),
        identity_review_rows=tuple(_load_csv_rows(IDENTITY_REVIEW_QUEUE_PATH)),
        dataset_registry_rows=tuple(_load_csv_rows(DATASET_REGISTRY_PATH)),
        dataset_coverage_rows=tuple(_load_csv_rows(DATASET_COVERAGE_PATH)),
    )


def player_context_artifact_status_rows(
    context: DevelopmentLabNflverseContext | None = None,
) -> list[dict[str, str]]:
    context = context or load_development_lab_nflverse_context()
    proposal_counts = _identity_proposal_counts(context.identity_review_rows)
    ff_rankings = next(
        (
            row
            for row in context.dataset_registry_rows
            if row.get("dataset_id") == "ff_rankings"
        ),
        {},
    )
    return [
        _status_row("Player context artifact rows", str(len(context.artifact_rows))),
        _status_row("Safe display rows", str(len(context.safe_rows))),
        _status_row("Identity review rows", str(len(context.needs_identity_review_rows))),
        _status_row("Identity proposals", proposal_counts["SAFE_RESOLUTION_PROPOSED"]),
        _status_row("Identity rows needing human review", proposal_counts["NEEDS_HUMAN_REVIEW"]),
        _status_row(
            "Identity rows kept for future review",
            proposal_counts["KEEP_NEED_IDENTITY_REVIEW"],
        ),
        _status_row("next game / opponent / bye", NOT_ENOUGH_INFORMATION),
        _status_row(
            "ff_rankings",
            ff_rankings.get("policy_status") or FF_RANKINGS_BLOCKED,
            note="Blocked; not consumed by Development Lab.",
        ),
    ]


def dataset_readiness_rows(
    context: DevelopmentLabNflverseContext | None = None,
) -> list[dict[str, str]]:
    context = context or load_development_lab_nflverse_context()
    coverage_by_id = {
        row.get("dataset_id", ""): row for row in context.dataset_coverage_rows
    }
    output: list[dict[str, str]] = []
    for row in context.dataset_registry_rows:
        dataset_id = row.get("dataset_id", NOT_ENOUGH_INFORMATION)
        coverage = coverage_by_id.get(dataset_id, {})
        output.append(
            {
                "Dataset": dataset_id,
                "Default mode": row.get("default_mode") or NOT_ENOUGH_INFORMATION,
                "Policy": row.get("policy_status") or NOT_ENOUGH_INFORMATION,
                "Runner status": row.get("runner_status") or NOT_ENOUGH_INFORMATION,
                "Coverage check": coverage.get("primary_coverage_check")
                or NOT_ENOUGH_INFORMATION,
                "Missing rule": _missing_rule(coverage.get("missing_semantics", "")),
                "Model input": row.get("model_use_allowed") or "false",
                "Rank logic": row.get("rank_logic_allowed") or "false",
            }
        )
    return output


def development_lab_context_status_rows() -> list[dict[str, str]]:
    return [
        {
            "Item": "F2 auto roster snapshot",
            "Status": SAFE_CONTEXT_READY,
            "Display": "Safe artifact rows only",
            "Remaining caveat": "Manual roster rows need NWR Player ID to join directly.",
        },
        {
            "Item": "F3 roster/status/depth/snap/contract context",
            "Status": SAFE_CONTEXT_READY,
            "Display": "Roster, weekly status, report status, depth, snap, and contract labels",
            "Remaining caveat": "next game / opponent / bye stays Not enough information.",
        },
        {
            "Item": "F4 NFL draft context",
            "Status": SAFE_CONTEXT_READY,
            "Display": "NFL draft year/round/pick/team when present",
            "Remaining caveat": "Does not alter fantasy pick ownership.",
        },
        {
            "Item": "F5 Upcoming Draft Prep context",
            "Status": SAFE_CONTEXT_READY,
            "Display": "Readiness labels and draft-capital display rows",
            "Remaining caveat": "Manual planning remains separate.",
        },
        {
            "Item": "F6 identity proposals",
            "Status": NEEDS_IDENTITY_REVIEW_LABEL,
            "Display": "Identity-review status only",
            "Remaining caveat": "Proposals are not approved joins.",
        },
        {
            "Item": "F7 deadline roster/status context",
            "Status": SAFE_CONTEXT_READY,
            "Display": "Roster/status/availability labels for manual checklists",
            "Remaining caveat": "No automatic action output.",
        },
        {
            "Item": "F10 refresh adapter consumption",
            "Status": SAFE_CONTEXT_READY,
            "Display": "Tracked artifact and schema manifest only",
            "Remaining caveat": "No raw shared/cache files read by app pages.",
        },
        {
            "Item": "Schedule next game / opponent / bye",
            "Status": SCHEDULE_UNAVAILABLE,
            "Display": NOT_ENOUGH_INFORMATION,
            "Remaining caveat": "No current/future schedule rows in the approved artifact.",
        },
    ]


def roster_status_context_rows(
    player_ids: Iterable[str] = (),
    *,
    limit: int = 25,
    context: DevelopmentLabNflverseContext | None = None,
) -> list[dict[str, str]]:
    return _player_context_rows(
        ROSTER_CONTEXT_FIELDS,
        player_ids=player_ids,
        limit=limit,
        context=context,
    )


def deadline_status_context_rows(
    *,
    limit: int = 25,
    context: DevelopmentLabNflverseContext | None = None,
) -> list[dict[str, str]]:
    return _player_context_rows(
        DEADLINE_CONTEXT_FIELDS,
        player_ids=(),
        limit=limit,
        context=context,
    )


def draft_capital_context_rows(
    *,
    limit: int = 25,
    context: DevelopmentLabNflverseContext | None = None,
) -> list[dict[str, str]]:
    context = context or load_development_lab_nflverse_context()
    rows = [
        row
        for row in context.safe_rows
        if _display_value(row.get("draft_year", "")) != NOT_ENOUGH_INFORMATION
    ]
    return _sanitize_rows(rows, DRAFT_CONTEXT_FIELDS, context.allowed_fields, limit=limit)


def identity_review_status_rows(
    *,
    limit: int = 25,
    context: DevelopmentLabNflverseContext | None = None,
) -> list[dict[str, str]]:
    context = context or load_development_lab_nflverse_context()
    output: list[dict[str, str]] = []
    for row in context.needs_identity_review_rows[:limit]:
        output.append(
            {
                "NWR Player ID": _display_value(row.get("nwr_player_id", "")),
                "Player": _display_value(row.get("nwr_player_name", "")),
                "NWR Position": _display_value(row.get("nwr_position", "")),
                "NWR Team": _display_value(row.get("nwr_team", "")),
                "Identity Status": NEEDS_IDENTITY_REVIEW_LABEL,
                "Review Note": _display_value(row.get("identity_caveat", "")),
            }
        )
    return output


def manual_nwr_player_ids(rows: Iterable[dict[str, str]]) -> tuple[str, ...]:
    return tuple(
        value
        for value in (_clean(row.get("nwr_player_id", "")) for row in rows)
        if value and value != NOT_ENOUGH_INFORMATION
    )


def schedule_unavailable_rows() -> list[dict[str, str]]:
    return [
        {
            "Field": "next_game_context",
            "Status": NOT_ENOUGH_INFORMATION,
            "Reason": "No current/future safe schedule rows in approved artifact.",
        },
        {
            "Field": "opponent_context",
            "Status": NOT_ENOUGH_INFORMATION,
            "Reason": "No current/future safe schedule rows in approved artifact.",
        },
        {
            "Field": "bye_context",
            "Status": NOT_ENOUGH_INFORMATION,
            "Reason": "No current/future safe schedule rows in approved artifact.",
        },
    ]


def _player_context_rows(
    fields: tuple[str, ...],
    *,
    player_ids: Iterable[str],
    limit: int,
    context: DevelopmentLabNflverseContext | None,
) -> list[dict[str, str]]:
    context = context or load_development_lab_nflverse_context()
    requested_ids = {_clean(value) for value in player_ids if _clean(value)}
    rows = [
        row
        for row in context.safe_rows
        if not requested_ids or row.get("nwr_player_id") in requested_ids
    ]
    if requested_ids and not rows:
        return [
            {
                "NWR Player ID": player_id,
                "Player": NOT_ENOUGH_INFORMATION,
                "Identity Status": NOT_ENOUGH_INFORMATION,
                "Source Label": NOT_ENOUGH_INFORMATION,
                "Freshness Label": NOT_ENOUGH_INFORMATION,
                "Coverage Label": NOT_ENOUGH_INFORMATION,
            }
            for player_id in sorted(requested_ids)
        ]
    return _sanitize_rows(rows, fields, context.allowed_fields, limit=limit)


def _sanitize_rows(
    rows: Iterable[dict[str, str]],
    fields: tuple[str, ...],
    allowed_fields: set[str],
    *,
    limit: int,
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for row in rows:
        if len(output) >= limit:
            break
        sanitized: dict[str, str] = {}
        for field in fields:
            if field not in allowed_fields:
                sanitized[CONTEXT_FIELD_LABELS[field]] = NOT_ENOUGH_INFORMATION
                continue
            sanitized[CONTEXT_FIELD_LABELS[field]] = _display_value(row.get(field, ""))
        sanitized["Identity Status"] = SAFE_NOW_DISPLAY_ONLY
        sanitized["Display Policy"] = "display-only/manual context"
        output.append(sanitized)
    return output


def _status_row(
    label: str,
    status: str,
    *,
    note: str = "Display-only/manual context",
) -> dict[str, str]:
    return {
        "Check": label,
        "Status": status or NOT_ENOUGH_INFORMATION,
        "Missing rule": NOT_ENOUGH_INFORMATION,
        "Guardrail": note,
    }


def _identity_proposal_counts(rows: tuple[dict[str, str], ...]) -> dict[str, str]:
    counts = {
        "SAFE_RESOLUTION_PROPOSED": 0,
        "NEEDS_HUMAN_REVIEW": 0,
        "KEEP_NEED_IDENTITY_REVIEW": 0,
    }
    for row in rows:
        decision = row.get("proposed_decision", "")
        if decision in counts:
            counts[decision] += 1
    return {key: str(value) for key, value in counts.items()}


def _missing_rule(value: str) -> str:
    cleaned = _clean(value)
    if not cleaned:
        return NOT_ENOUGH_INFORMATION
    if "Not enough information" in cleaned:
        return cleaned
    return f"{cleaned}; missing display is {NOT_ENOUGH_INFORMATION}"


def _display_value(value: str) -> str:
    cleaned = _clean(value)
    if cleaned == NEED_IDENTITY_REVIEW:
        return NEEDS_IDENTITY_REVIEW_LABEL
    if cleaned in UNAVAILABLE_VALUES:
        return NOT_ENOUGH_INFORMATION
    return cleaned


def _all_guardrail_flags_false(row: dict[str, str]) -> bool:
    return all(
        row.get(field) == "false"
        for field in (
            "model_use_allowed",
            "training_allowed",
            "source_truth_allowed",
            "rank_logic_allowed",
            "hidden_sort_allowed",
            "trade_value_allowed",
            "pick_value_allowed",
        )
    )


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _clean(value: object) -> str:
    return str(value or "").strip()
