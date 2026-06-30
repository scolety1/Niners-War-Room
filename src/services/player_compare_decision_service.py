from __future__ import annotations

import csv
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

NOT_ENOUGH_INFORMATION = "Not enough information"
MARKET_DISPLAY_ONLY_NOTE = (
    "Market context is display-only and does not determine the compare readout, "
    "rankings, trade value, or draft decision."
)
MULTI_PLAYER_COMPARE_NOTE = (
    "For 3-4 player comparisons, this page narrows review context. It does not "
    "produce a final ranking or recommendation."
)
NFLVERSE_WAIT_STATUS = "WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN"
SAFE_NOW_DISPLAY_ONLY = "SAFE_NOW_DISPLAY_ONLY"
NEED_IDENTITY_REVIEW = "NEED_IDENTITY_REVIEW"
DISPLAY_ONLY_CONTEXT = "Display-only context"
MANUAL_REVIEW_ONLY = "Manual review only"
NEEDS_IDENTITY_REVIEW = "Needs identity review"
NO_RECOMMENDATION_CALCULATED = "No recommendation calculated"
NOT_MODEL_INPUT = "Not model input"

REPO_ROOT = Path(__file__).resolve().parents[2]
NFLVERSE_PLAYER_CONTEXT_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_player_context_display_20260630"
)
NFLVERSE_PLAYER_CONTEXT_ARTIFACT_PATH = (
    NFLVERSE_PLAYER_CONTEXT_DIR / "nflverse_player_context_display_artifact.csv"
)
NFLVERSE_PLAYER_CONTEXT_SCHEMA_MANIFEST_PATH = (
    NFLVERSE_PLAYER_CONTEXT_DIR / "nflverse_player_context_schema_manifest.csv"
)

UNAVAILABLE_CONTEXT_VALUES = {
    "",
    "nan",
    "none",
    "null",
    "n/a",
    "<na>",
    "not enough information",
    "review needed",
    "not_applicable",
}
UNAVAILABLE_CONTEXT_PREFIXES = ("NEED_", "BLOCKED_")

IDENTITY_CONTEXT_FIELDS = (
    ("NWR player id", "nwr_player_id"),
    ("NFLVerse/GSIS ID", "nflverse_gsis_id"),
    ("Sleeper ID", "nflverse_sleeper_id"),
    ("NFLVerse player", "nflverse_player_name"),
    ("NFLVerse team", "nflverse_team"),
    ("NFLVerse position", "nflverse_position"),
    ("Identity caveat", "identity_caveat"),
)
RECENT_ACTIVITY_CONTEXT_FIELDS = (
    ("Last active season", "last_active_season"),
    ("Last active week", "last_active_week"),
    ("Snap recency", "snap_count_recency"),
    ("Snap sample size", "snap_sample_size"),
    ("Weekly roster status", "weekly_roster_status"),
)
USAGE_ROLE_CONTEXT_FIELDS = (
    ("Depth chart position", "depth_chart_position"),
    ("Depth chart rank", "depth_chart_rank"),
    ("Depth chart role", "depth_chart_role"),
    ("Snap recency", "snap_count_recency"),
    ("Last active season", "last_active_season"),
    ("Last active week", "last_active_week"),
)
AVAILABILITY_CONTEXT_FIELDS = (
    ("Roster status", "roster_status"),
    ("Weekly roster status", "weekly_roster_status"),
    ("Injury report status", "injury_report_status"),
    ("Practice status", "practice_status"),
    ("Injury report date/week", "injury_report_date_week"),
)
ROSTER_WINDOW_CONTEXT_FIELDS = (
    ("Age", "roster_birth_date_derived_age"),
    ("Age source", "age_source"),
    ("Roster team", "nflverse_team"),
    ("Roster position", "nflverse_position"),
    ("Roster status", "roster_status"),
    ("Contract context", "contract_context"),
)
SCHEDULE_CONTEXT_FIELDS = (
    ("Next game context", "next_game_context"),
    ("Opponent context", "opponent_context"),
    ("Bye context", "bye_context"),
)

FIELD_GROUPS = {
    "Identity / Join Transparency": IDENTITY_CONTEXT_FIELDS,
    "Recent Production / Activity Context": RECENT_ACTIVITY_CONTEXT_FIELDS,
    "Usage / Role Context": USAGE_ROLE_CONTEXT_FIELDS,
    "Availability Timeline": AVAILABILITY_CONTEXT_FIELDS,
    "Roster-Window Context": ROSTER_WINDOW_CONTEXT_FIELDS,
    "Schedule Context": SCHEDULE_CONTEXT_FIELDS,
}


@dataclass(frozen=True)
class PlayerCompareNflverseContext:
    artifact_available: bool
    artifact_path: str
    schema_path: str
    artifact_rows: int
    safe_display_rows: int
    identity_review_rows: int
    schedule_available_rows: int
    identity_rows: tuple[dict[str, str], ...]
    recent_activity_rows: tuple[dict[str, str], ...]
    usage_role_rows: tuple[dict[str, str], ...]
    availability_rows: tuple[dict[str, str], ...]
    roster_window_rows: tuple[dict[str, str], ...]
    schedule_rows: tuple[dict[str, str], ...]
    dataset_badge_rows: tuple[dict[str, str], ...]
    deferred_rows: tuple[dict[str, str], ...]
    caveat: str


@dataclass(frozen=True)
class PlayerDecisionSummary:
    """Visible Player Compare context summary with legacy accessors."""

    visible_context_read: str
    evidence_coverage: str
    context_note: str
    open_review_flags: tuple[str, ...]
    context_bullets: tuple[str, ...]
    display_only_market_note: str
    multi_player_note: str

    @property
    def lean(self) -> str:
        return self.visible_context_read

    @property
    def confidence(self) -> str:
        return self.evidence_coverage

    @property
    def best_use_case(self) -> str:
        return self.context_note

    @property
    def data_quality(self) -> str:
        return f"{len(self.open_review_flags)} open flag(s)"

    @property
    def reason_bullets(self) -> tuple[str, ...]:
        return self.context_bullets

    @property
    def red_flags(self) -> tuple[str, ...]:
        return self.open_review_flags


def build_player_compare_decision_summary(
    player_a: dict[str, Any],
    player_b: dict[str, Any],
    extra_players: list[dict[str, Any]] | None = None,
) -> PlayerDecisionSummary:
    """Build a visible-context readout without hidden sorting or recommendations."""

    candidates = [player_a, player_b, *(extra_players or [])]
    usable = [row for row in candidates if _player_name(row) != NOT_ENOUGH_INFORMATION]
    if len(usable) < 2:
        return PlayerDecisionSummary(
            visible_context_read=NOT_ENOUGH_INFORMATION,
            evidence_coverage=NOT_ENOUGH_INFORMATION,
            context_note="Select at least two players with visible context.",
            open_review_flags=(NOT_ENOUGH_INFORMATION,),
            context_bullets=("Select at least two players with visible context.",),
            display_only_market_note=MARKET_DISPLAY_ONLY_NOTE,
            multi_player_note="",
        )

    positions = {_field(row, "position").upper() for row in usable}
    same_position = len(positions) == 1
    context_read = _visible_context_read(usable, same_position=same_position)
    flags = _open_review_flags(usable)
    bullets = _context_bullets(usable, same_position=same_position)
    if not flags:
        flags.append("No major open review flag in visible context.")

    return PlayerDecisionSummary(
        visible_context_read=context_read,
        evidence_coverage=_evidence_coverage(usable),
        context_note=_context_note(usable, same_position=same_position),
        open_review_flags=tuple(flags[:8]),
        context_bullets=tuple(bullets[:8]) or (NOT_ENOUGH_INFORMATION,),
        display_only_market_note=MARKET_DISPLAY_ONLY_NOTE,
        multi_player_note=MULTI_PLAYER_COMPARE_NOTE if len(usable) > 2 else "",
    )


def decision_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for row in rows:
        output.append(
            {
                "Player": _player_name(row),
                "Position": _field(row, "position"),
                "Read-only board context": _rank_signal(row),
                "Age": _field(row, "age"),
                "Tier / band": _tier_signal(row),
                "Outcome support": _outcome_signal(row),
                "Stability evidence": _stability_evidence(row),
                "Ceiling evidence": _ceiling_evidence(row),
                "Roster-window context": _roster_window_context(row),
                "Main review flags": _review_flag_signal(row),
            }
        )
    return output


def nflverse_spec_panel_rows() -> list[dict[str, str]]:
    return [
        _nflverse_spec_row(
            "Recent production",
            "player_stats weekly / seasonal",
            "Disabled until player_stats status, schema, coverage, freshness, and policy pass.",
        ),
        _nflverse_spec_row(
            "Usage / role",
            "snap_counts; player_stats weekly; depth_charts",
            "Disabled until usage datasets pass. Depth chart remains a review-only snapshot.",
        ),
        _nflverse_spec_row(
            "Availability transparency",
            "injuries; weekly_rosters; rosters; schedules; ID bridge",
            "Existing approved injury context may display; expanded nflverse panel waits.",
        ),
        _nflverse_spec_row(
            "Roster-window context",
            "ff_playerids; rosters; weekly_rosters; schedules",
            "Disabled until identity and roster-window statuses pass.",
        ),
        _nflverse_spec_row(
            "Identity and data coverage",
            "ff_playerids; rosters; weekly_rosters; player_stats; snap_counts",
            "Current page can show fallback-match notes only; deterministic bridge waits.",
        ),
    ]


def _nflverse_spec_row(panel: str, dataset: str, fallback: str) -> dict[str, str]:
    return {
        "Panel": panel,
        "Dataset dependency": dataset,
        "Status": NFLVERSE_WAIT_STATUS,
        "Safe to wire now": "No",
        "Current behavior": fallback,
    }


def build_player_compare_nflverse_context(
    records: Sequence[dict[str, Any]],
    *,
    artifact_path: Path = NFLVERSE_PLAYER_CONTEXT_ARTIFACT_PATH,
    schema_path: Path = NFLVERSE_PLAYER_CONTEXT_SCHEMA_MANIFEST_PATH,
) -> PlayerCompareNflverseContext:
    artifact_rows = _read_csv_dicts(artifact_path)
    schema_rows = _read_csv_dicts(schema_path)
    artifact_available = bool(artifact_rows and schema_rows)
    safe_fields = _safe_nflverse_schema_fields(schema_rows)
    selected = _selected_nflverse_views(records, artifact_rows, safe_fields)
    schedule_available_rows = _schedule_available_rows(artifact_rows, safe_fields)

    return PlayerCompareNflverseContext(
        artifact_available=artifact_available,
        artifact_path=str(artifact_path),
        schema_path=str(schema_path),
        artifact_rows=len(artifact_rows),
        safe_display_rows=sum(1 for row in artifact_rows if _is_safe_nflverse_row(row)),
        identity_review_rows=sum(
            1 for row in artifact_rows if _raw_context_value(row, "identity_join_status")
            == NEED_IDENTITY_REVIEW
        ),
        schedule_available_rows=schedule_available_rows,
        identity_rows=tuple(_identity_context_row(view, safe_fields) for view in selected),
        recent_activity_rows=tuple(
            _field_group_context_row(view, safe_fields, RECENT_ACTIVITY_CONTEXT_FIELDS)
            for view in selected
        ),
        usage_role_rows=tuple(
            _field_group_context_row(view, safe_fields, USAGE_ROLE_CONTEXT_FIELDS)
            for view in selected
        ),
        availability_rows=tuple(
            _field_group_context_row(view, safe_fields, AVAILABILITY_CONTEXT_FIELDS)
            for view in selected
        ),
        roster_window_rows=tuple(
            _field_group_context_row(view, safe_fields, ROSTER_WINDOW_CONTEXT_FIELDS)
            for view in selected
        ),
        schedule_rows=tuple(
            _field_group_context_row(view, safe_fields, SCHEDULE_CONTEXT_FIELDS)
            for view in selected
        ),
        dataset_badge_rows=tuple(_dataset_badge_rows(schema_rows)),
        deferred_rows=tuple(_nflverse_deferred_rows(schedule_available_rows)),
        caveat=(
            "Display-only context from the tracked NFLVerse player-context artifact. "
            "No recommendation calculated. Not model input."
            if artifact_available
            else "Not enough information: tracked NFLVerse player-context artifact is unavailable."
        ),
    )


def _selected_nflverse_views(
    records: Sequence[dict[str, Any]],
    artifact_rows: list[dict[str, str]],
    safe_fields: set[str],
) -> list[dict[str, Any]]:
    rows_by_id = {
        _raw_context_value(row, "nwr_player_id"): row
        for row in artifact_rows
        if not _is_unavailable_context_value(_raw_context_value(row, "nwr_player_id"))
    }
    views: list[dict[str, Any]] = []
    for record in records:
        player = _field(record, "player")
        position = _field(record, "position")
        nwr_player_id = _field(record, "player_id")
        artifact_row = rows_by_id.get(nwr_player_id, {})
        identity_status = _raw_context_value(artifact_row, "identity_join_status")
        if nwr_player_id == NOT_ENOUGH_INFORMATION or not artifact_row:
            context_status = NOT_ENOUGH_INFORMATION
            safe = False
        elif identity_status == NEED_IDENTITY_REVIEW or _review_required(artifact_row):
            context_status = NEEDS_IDENTITY_REVIEW
            safe = False
        elif _is_safe_nflverse_row(artifact_row):
            context_status = DISPLAY_ONLY_CONTEXT
            safe = True
        else:
            context_status = MANUAL_REVIEW_ONLY
            safe = False
        views.append(
            {
                "player": player,
                "position": position,
                "nwr_player_id": nwr_player_id,
                "artifact_row": artifact_row,
                "identity_status": identity_status or NOT_ENOUGH_INFORMATION,
                "context_status": context_status,
                "safe": safe and bool(safe_fields),
            }
        )
    return views


def _identity_context_row(view: dict[str, Any], safe_fields: set[str]) -> dict[str, str]:
    row = _base_nflverse_context_row(view)
    if not view["safe"]:
        row.update(
            {
                "NFLVerse/GSIS ID": NOT_ENOUGH_INFORMATION,
                "Sleeper ID": NOT_ENOUGH_INFORMATION,
                "NFLVerse player": NOT_ENOUGH_INFORMATION,
                "NFLVerse team": NOT_ENOUGH_INFORMATION,
                "NFLVerse position": NOT_ENOUGH_INFORMATION,
                "Identity caveat": _identity_restricted_note(view),
                "Source/as-of": _source_as_of(view, safe_fields),
                "No recommendation": NO_RECOMMENDATION_CALCULATED,
                "Model use": NOT_MODEL_INPUT,
            }
        )
        return row

    artifact_row = view["artifact_row"]
    for label, field in IDENTITY_CONTEXT_FIELDS:
        row[label] = _safe_context_value(artifact_row, field, safe_fields)
    row["Source/as-of"] = _source_as_of(view, safe_fields)
    row["No recommendation"] = NO_RECOMMENDATION_CALCULATED
    row["Model use"] = NOT_MODEL_INPUT
    return row


def _field_group_context_row(
    view: dict[str, Any],
    safe_fields: set[str],
    fields: tuple[tuple[str, str], ...],
) -> dict[str, str]:
    row = _base_nflverse_context_row(view)
    if not view["safe"]:
        for label, _field_name in fields:
            row[label] = NOT_ENOUGH_INFORMATION
        row["Missing-data rule"] = _restricted_missing_data_rule(view)
        row["No recommendation"] = NO_RECOMMENDATION_CALCULATED
        row["Model use"] = NOT_MODEL_INPUT
        return row

    artifact_row = view["artifact_row"]
    for label, field in fields:
        row[label] = _safe_context_value(artifact_row, field, safe_fields)
    row["Missing-data rule"] = (
        "Missing data remains Not enough information; it is not zero, not no-role, "
        "not healthy, not clean, not safe, not bad, and not confirmed UDFA."
    )
    row["No recommendation"] = NO_RECOMMENDATION_CALCULATED
    row["Model use"] = NOT_MODEL_INPUT
    return row


def _base_nflverse_context_row(view: dict[str, Any]) -> dict[str, str]:
    identity_status = view["identity_status"]
    if view["context_status"] == NEEDS_IDENTITY_REVIEW:
        identity_status = NEED_IDENTITY_REVIEW
    return {
        "Player": view["player"],
        "Pos": view["position"],
        "NWR player id": view["nwr_player_id"],
        "Context status": view["context_status"],
        "Identity join status": identity_status,
    }


def _dataset_badge_rows(schema_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    labels_by_field = {
        field: label
        for fields in FIELD_GROUPS.values()
        for label, field in fields
    }
    rows: list[dict[str, str]] = []
    for schema_row in schema_rows:
        column = _raw_context_value(schema_row, "column_name")
        if column not in labels_by_field:
            continue
        rows.append(
            {
                "Field": labels_by_field[column],
                "Column": column,
                "Source dataset": _safe_schema_text(schema_row, "source_dataset"),
                "Artifact status": _safe_schema_text(schema_row, "field_status"),
                "Display caveat": "Display-only context; Manual review only if not safely joined.",
                "Missing-data rule": _safe_schema_text(schema_row, "missing_value_policy"),
                "Model use": NOT_MODEL_INPUT,
            }
        )
    return _dedupe_dict_rows(rows)


def _nflverse_deferred_rows(schedule_available_rows: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if schedule_available_rows == 0:
        rows.append(
            {
                "Item": "Next game / opponent / bye context",
                "Status": NOT_ENOUGH_INFORMATION,
                "Reason": (
                    "Tracked artifact has 0 safe current/future schedule context rows; "
                    "schedule context remains unavailable."
                ),
            }
        )
    rows.extend(
        [
            {
                "Item": "Identity proposal rows",
                "Status": MANUAL_REVIEW_ONLY,
                "Reason": (
                    "Identity proposals are not approved joins and are not shown as player context."
                ),
            },
            {
                "Item": "ff_rankings",
                "Status": MANUAL_REVIEW_ONLY,
                "Reason": "Blocked by source policy for Player Compare display.",
            },
        ]
    )
    return rows


def _safe_nflverse_schema_fields(schema_rows: list[dict[str, str]]) -> set[str]:
    return {
        _raw_context_value(row, "column_name")
        for row in schema_rows
        if _raw_context_value(row, "field_status") == SAFE_NOW_DISPLAY_ONLY
        and _raw_context_value(row, "display_only").lower() == "true"
        and _raw_context_value(row, "model_use_allowed").lower() == "false"
        and _raw_context_value(row, "training_allowed").lower() == "false"
        and _raw_context_value(row, "source_truth_allowed").lower() == "false"
        and _raw_context_value(row, "rank_logic_allowed").lower() == "false"
        and _raw_context_value(row, "hidden_sort_allowed").lower() == "false"
        and _raw_context_value(row, "trade_value_allowed").lower() == "false"
        and _raw_context_value(row, "pick_value_allowed").lower() == "false"
    }


def _safe_context_value(
    row: dict[str, str],
    field: str,
    safe_fields: set[str],
) -> str:
    if field not in safe_fields:
        return NOT_ENOUGH_INFORMATION
    value = _raw_context_value(row, field)
    if _is_unavailable_context_value(value):
        return NOT_ENOUGH_INFORMATION
    return value


def _source_as_of(view: dict[str, Any], safe_fields: set[str]) -> str:
    if not view["safe"]:
        if view["context_status"] == NEEDS_IDENTITY_REVIEW:
            return MANUAL_REVIEW_ONLY
        return NOT_ENOUGH_INFORMATION
    row = view["artifact_row"]
    source = _safe_context_value(row, "per_field_dataset_source", safe_fields)
    freshness = _safe_context_value(row, "per_field_freshness_source_status", safe_fields)
    if source == NOT_ENOUGH_INFORMATION and freshness == NOT_ENOUGH_INFORMATION:
        return NOT_ENOUGH_INFORMATION
    return f"Source: {source}; As-of/freshness: {freshness}"


def _identity_restricted_note(view: dict[str, Any]) -> str:
    if view["context_status"] == NEEDS_IDENTITY_REVIEW:
        return MANUAL_REVIEW_ONLY
    return NOT_ENOUGH_INFORMATION


def _restricted_missing_data_rule(view: dict[str, Any]) -> str:
    if view["context_status"] == NEEDS_IDENTITY_REVIEW:
        return "Needs identity review; player context details are not displayed."
    return "Not enough information; missing data is not interpreted."


def _is_safe_nflverse_row(row: dict[str, str]) -> bool:
    return (
        _raw_context_value(row, "identity_join_status") == SAFE_NOW_DISPLAY_ONLY
        and _raw_context_value(row, "review_required").lower() == "false"
        and _raw_context_value(row, "display_only").lower() == "true"
        and _raw_context_value(row, "model_use_allowed").lower() == "false"
        and _raw_context_value(row, "source_truth_allowed").lower() == "false"
        and _raw_context_value(row, "rank_logic_allowed").lower() == "false"
        and _raw_context_value(row, "hidden_sort_allowed").lower() == "false"
        and _raw_context_value(row, "trade_value_allowed").lower() == "false"
        and _raw_context_value(row, "pick_value_allowed").lower() == "false"
    )


def _review_required(row: dict[str, str]) -> bool:
    return _raw_context_value(row, "review_required").lower() == "true"


def _schedule_available_rows(
    artifact_rows: list[dict[str, str]],
    safe_fields: set[str],
) -> int:
    return sum(
        1
        for row in artifact_rows
        if _is_safe_nflverse_row(row)
        and any(
            _safe_context_value(row, field, safe_fields) != NOT_ENOUGH_INFORMATION
            for _label, field in SCHEDULE_CONTEXT_FIELDS
        )
    )


def _safe_schema_text(row: dict[str, str], field: str) -> str:
    value = _raw_context_value(row, field)
    return value if value else NOT_ENOUGH_INFORMATION


def _raw_context_value(row: dict[str, str], field: str) -> str:
    return str(row.get(field, "") if row else "").strip()


def _is_unavailable_context_value(value: str) -> bool:
    text = str(value or "").strip()
    if text.lower() in UNAVAILABLE_CONTEXT_VALUES:
        return True
    return any(text.startswith(prefix) for prefix in UNAVAILABLE_CONTEXT_PREFIXES)


def _read_csv_dicts(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _dedupe_dict_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[tuple[str, str], ...]] = set()
    output: list[dict[str, str]] = []
    for row in rows:
        key = tuple(sorted(row.items()))
        if key not in seen:
            output.append(row)
            seen.add(key)
    return output


def _visible_context_read(rows: list[dict[str, Any]], *, same_position: bool) -> str:
    if not same_position:
        return "Different positions / roster-fit decision"
    ranks = [_visible_rank_value(row) for row in rows]
    available = [rank for rank in ranks if rank is not None]
    if len(available) < 2:
        return NOT_ENOUGH_INFORMATION
    if max(available) - min(available) <= 4:
        return "Too close to call from visible context"
    return "Visible board context differs"


def _evidence_coverage(rows: list[dict[str, Any]]) -> str:
    total = len(rows)
    if total == 0:
        return NOT_ENOUGH_INFORMATION
    rank_count = sum(1 for row in rows if _visible_rank_value(row) is not None)
    age_count = sum(1 for row in rows if _field(row, "age") != NOT_ENOUGH_INFORMATION)
    outcome_count = sum(1 for row in rows if _outcome_signal(row) != NOT_ENOUGH_INFORMATION)
    return (
        f"Visible fields: board context {rank_count}/{total}; age {age_count}/{total}; "
        f"Outcome support {outcome_count}/{total}"
    )


def _context_note(rows: list[dict[str, Any]], *, same_position: bool) -> str:
    if len(rows) > 2:
        return "Review context only; no final ranking is produced."
    if same_position:
        return "Same-position factual review; human roster fit still decides."
    return "Cross-position review; compare facts by position and roster need."


def _context_bullets(rows: list[dict[str, Any]], *, same_position: bool) -> list[str]:
    bullets = [
        "Player Compare shows visible context only.",
        "Read-only board ranks may be shown below but do not create a recommendation.",
    ]
    if same_position:
        bullets.append("Same-position rows can be reviewed side by side without a hidden ladder.")
    else:
        bullets.append("Different positions are not converted into a single player preference.")
    if len(rows) > 2:
        bullets.append(MULTI_PLAYER_COMPARE_NOTE)
    return bullets


def _open_review_flags(rows: list[dict[str, Any]]) -> list[str]:
    flags: list[str] = []
    for row in rows:
        player = _player_name(row)
        if _field(row, "age") == NOT_ENOUGH_INFORMATION:
            flags.append(f"{player}: age is {NOT_ENOUGH_INFORMATION}.")
        if _visible_rank_value(row) is None:
            flags.append(f"{player}: read-only board context is {NOT_ENOUGH_INFORMATION}.")
        if _outcome_signal(row) == NOT_ENOUGH_INFORMATION:
            flags.append(f"{player}: outcome support is {NOT_ENOUGH_INFORMATION}.")
        if _has_review_notes(row):
            flags.append(f"{player}: review notes available below.")
    return _dedupe(flags)


def _visible_rank_value(row: dict[str, Any]) -> float | None:
    for key in ("dynasty_asset_rank", "cross_asset_candidate_rank", "final_board_rank"):
        value = _float_or_none(row.get(key))
        if value is not None:
            return value
    return None


def _rank_signal(row: dict[str, Any]) -> str:
    for label, key in (
        ("NWR/Dynasty Candidate Rank (Read-Only)", "dynasty_asset_rank"),
        ("Tuned Candidate Rank (Read-Only)", "cross_asset_candidate_rank"),
        ("Frozen Baseline Rank (Read-Only)", "final_board_rank"),
    ):
        value = _field(row, key)
        if value != NOT_ENOUGH_INFORMATION:
            return f"{label}: {value}"
    return NOT_ENOUGH_INFORMATION


def _tier_signal(row: dict[str, Any]) -> str:
    for key in (
        "dynasty_asset_tier",
        "on_clock_decision_tier",
        "candidate_value_band",
        "final_tier",
    ):
        value = _field(row, key)
        if value != NOT_ENOUGH_INFORMATION:
            return value
    return NOT_ENOUGH_INFORMATION


def _outcome_signal(row: dict[str, Any]) -> str:
    value = _field(row, "outcome_applicable_summary")
    if value.lower() in {"unsupported", "no", "none"}:
        return NOT_ENOUGH_INFORMATION
    return value


def _stability_evidence(row: dict[str, Any]) -> str:
    age = _field(row, "age")
    if _has_review_notes(row):
        return "Review notes available below"
    if age != NOT_ENOUGH_INFORMATION:
        return f"Age shown: {age}"
    return NOT_ENOUGH_INFORMATION


def _ceiling_evidence(row: dict[str, Any]) -> str:
    outcome = _outcome_signal(row)
    if outcome != NOT_ENOUGH_INFORMATION:
        return outcome
    band = _field(row, "candidate_value_band")
    if band != NOT_ENOUGH_INFORMATION:
        return "Review band shown below"
    return NOT_ENOUGH_INFORMATION


def _roster_window_context(row: dict[str, Any]) -> str:
    position = _field(row, "position")
    age = _float_or_none(row.get("age"))
    if age is None:
        return NOT_ENOUGH_INFORMATION
    if age >= 30:
        return "Age-window review"
    if position == "QB":
        return "1QB format context requires human roster fit"
    return "Age context shown; roster fit is a human decision"


def _review_flag_signal(row: dict[str, Any]) -> str:
    flags: list[str] = []
    if _field(row, "age") == NOT_ENOUGH_INFORMATION:
        flags.append("age missing")
    if _outcome_signal(row) == NOT_ENOUGH_INFORMATION:
        flags.append("outcome support missing")
    if _visible_rank_value(row) is None:
        flags.append("board context missing")
    if _has_review_notes(row):
        flags.append("review notes available below")
    return "; ".join(flags) if flags else "No major open review flag in visible context."


def _has_review_notes(row: dict[str, Any]) -> bool:
    for key in (
        "risk_notes",
        "candidate_key_caveat",
        "needs_manual_review",
        "human_review_flag",
        "on_clock_warning",
    ):
        if _field(row, key) != NOT_ENOUGH_INFORMATION:
            return True
    return False


def _player_name(row: dict[str, Any]) -> str:
    return _field(row, "player")


def _field(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    text = str(value if value is not None else "").strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a", "<na>"}:
        return NOT_ENOUGH_INFORMATION
    return text


def _float_or_none(value: Any) -> float | None:
    text = str(value if value is not None else "").strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a", "<na>"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value not in seen:
            output.append(value)
            seen.add(value)
    return output
