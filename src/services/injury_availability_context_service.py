from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pandas as pd

from src.services.draft_day_app_v1_service import (
    NFLVERSE_PLAYER_CONTEXT_DISPLAY_PATH,
    NFLVERSE_PLAYER_CONTEXT_SAFE_STATUS,
    NFLVERSE_PLAYER_CONTEXT_SCHEMA_MANIFEST_PATH,
)

NOT_ENOUGH_INFORMATION: Final = "Not enough information"
WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN: Final = (
    "WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN"
)
SAFE_NOW: Final = "SAFE_NOW"
NEED_MODEL_GATE: Final = "NEED_MODEL_GATE"
BLOCKED: Final = "BLOCKED"
YELLOW_NEEDS_PLAYER_CONTEXT_ARTIFACT_EXTENSION: Final = (
    "YELLOW_NEEDS_PLAYER_CONTEXT_ARTIFACT_EXTENSION"
)
NEED_IDENTITY_REVIEW: Final = "NEED_IDENTITY_REVIEW"
REVIEW_NEEDED: Final = "Review needed"
AVAILABILITY_CONTEXT_PRESENT: Final = "Availability context present"
AVAILABILITY_CONTEXT_UNAVAILABLE: Final = NOT_ENOUGH_INFORMATION

SAFE_UPGRADE_VERSION: Final = "injury_availability_display_context_safe_upgrade_20260630"

WAITING_AVAILABILITY_FIELDS: Final = (
    "games_while_rostered",
    "games_with_snaps",
    "games_with_recorded_stats",
    "games_played_context",
    "games_missed_while_rostered",
    "per_game_denominator",
)

FORBIDDEN_DISPLAY_FIELDS: Final = (
    "injury_risk_score",
    "risk_score",
    "durability_score",
    "injury_durability",
    "medical_projection",
    "recovery_probability",
    "comeback_probability",
    "acl_comeback_projection",
    "achilles_comeback_projection",
    "rank_adjustment",
    "source_truth_override",
    "model_input_flag",
)

NFLVERSE_AVAILABILITY_SAFE_FIELDS: Final = (
    "identity_join_status",
    "identity_caveat",
    "roster_birth_date_derived_age",
    "age_source",
    "roster_status",
    "weekly_roster_status",
    "injury_report_status",
    "injury_report_date_week",
    "practice_status",
    "snap_count_recency",
    "latest_snap_season",
    "latest_snap_week",
    "snap_sample_size",
    "last_active_season",
    "last_active_week",
    "data_coverage_status",
)

UNAVAILABLE_TOKENS: Final = {
    "",
    NOT_ENOUGH_INFORMATION,
    WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN,
    NEED_IDENTITY_REVIEW,
    "NEED_DATASET_REFRESH",
    "NEED_SCHEMA_REVIEW",
    "BLOCKED_SOURCE_POLICY",
    "BLOCKED_VENDOR_OR_PRIVATE",
    "NOT_APPLICABLE",
    REVIEW_NEEDED,
}


@dataclass(frozen=True)
class AvailabilityDatasetStatus:
    dataset: str
    current_status: str
    classification: str
    safe_now_use: str
    active_compute_use: str
    caveat: str


@dataclass(frozen=True)
class ProposalClassification:
    proposal_id: str
    classification: str
    active_status: str
    note: str


def availability_dataset_status_rows() -> list[dict[str, str]]:
    return [
        _dataset_status(
            "nflverse_injuries",
            "SAFE_NOW_DISPLAY_ONLY via tracked player context artifact",
            SAFE_NOW,
            "Factual injury report status, practice status, and report date/week.",
            "Display direct artifact values only for safe identity rows.",
            (
                "Missing report values remain "
                f"{NOT_ENOUGH_INFORMATION}."
            ),
        ),
        _dataset_status(
            "nflverse_weekly_rosters",
            "SAFE_NOW_DISPLAY_ONLY via tracked player context artifact",
            SAFE_NOW,
            "Weekly roster status display for safe identity rows.",
            "Do not compute games while rostered from app pages.",
            "Per-game denominators need a future artifact extension.",
        ),
        _dataset_status(
            "nflverse_rosters",
            "SAFE_NOW_DISPLAY_ONLY via tracked player context artifact",
            SAFE_NOW,
            "Roster status, age source, and identity caveat display.",
            "Display direct artifact values only for safe identity rows.",
            "Missing roster values remain Not enough information.",
        ),
        _dataset_status(
            "nflverse_schedules",
            "tracked artifact present; current/future schedule values unavailable",
            YELLOW_NEEDS_PLAYER_CONTEXT_ARTIFACT_EXTENSION,
            "Document schedule unavailable status.",
            "Do not display next game, opponent, bye, or per-game denominators.",
            "Schedule audit shows 0 current/future safe rows.",
        ),
        _dataset_status(
            "nflverse_snap_counts",
            "SAFE_NOW_DISPLAY_ONLY via tracked player context artifact",
            SAFE_NOW,
            "Snap recency, latest snap season/week, and sample size display.",
            "Do not treat missing snap data as zero.",
            "Games with snaps still needs a future denominator artifact.",
        ),
        _dataset_status(
            "nflverse_player_stats",
            "SAFE_NOW_DISPLAY_ONLY via tracked player context artifact",
            SAFE_NOW,
            "Last active season/week display.",
            "Do not compute games with recorded stats from app pages.",
            "Games-played denominators need a future artifact extension.",
        ),
        _dataset_status(
            "refresh_metadata",
            "tracked refresh-health contract present",
            YELLOW_NEEDS_PLAYER_CONTEXT_ARTIFACT_EXTENSION,
            "Document status only.",
            "Do not choose dynamic season anchors in this lane.",
            "Dynamic anchors need an explicit display artifact field.",
        ),
        _dataset_status(
            "ff_rankings",
            "blocked by source policy",
            BLOCKED,
            "None.",
            "Do not consume.",
            "Blocked and unused.",
        ),
    ]


def build_injury_availability_display_context(
    *,
    player_id: object = "",
    gsis_id: object = "",
    player_name: object = "",
    position: object = "",
    identity_match_status: object = "matched_exact",
    prior_season_injury_report_weeks: object = None,
    prior_season_out_or_doubtful_weeks: object = None,
    source_dataset_status: object = WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN,
) -> dict[str, str]:
    identity_status = _clean(identity_match_status, default=NOT_ENOUGH_INFORMATION)
    identity_supported = identity_status in {"matched_exact", "matched_approved"}
    report_weeks = _count_or_nei(prior_season_injury_report_weeks)
    out_or_doubtful = _count_or_nei(prior_season_out_or_doubtful_weeks)
    if not identity_supported:
        report_weeks = NOT_ENOUGH_INFORMATION
        out_or_doubtful = NOT_ENOUGH_INFORMATION

    context_available = "true"
    if report_weeks == NOT_ENOUGH_INFORMATION:
        context_available = NOT_ENOUGH_INFORMATION

    row = {
        "context_version": SAFE_UPGRADE_VERSION,
        "player_id": _clean(player_id),
        "gsis_id": _clean(gsis_id),
        "player_name": _clean(player_name),
        "position": _clean(position),
        "identity_match_status": identity_status,
        "injury_context_available": context_available,
        "prior_season_injury_report_weeks": report_weeks,
        "prior_season_out_or_doubtful_weeks": out_or_doubtful,
        "games_while_rostered": NOT_ENOUGH_INFORMATION,
        "games_with_snaps": NOT_ENOUGH_INFORMATION,
        "games_with_recorded_stats": NOT_ENOUGH_INFORMATION,
        "games_played_context": NOT_ENOUGH_INFORMATION,
        "games_missed_while_rostered": NOT_ENOUGH_INFORMATION,
        "per_game_denominator": NOT_ENOUGH_INFORMATION,
        "availability_context_status": AVAILABILITY_CONTEXT_PRESENT
        if context_available == "true"
        else NOT_ENOUGH_INFORMATION,
        "source_dataset_status": _clean(
            source_dataset_status,
            default=WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN,
        ),
        "season_total_caveat": (
            "Injury-report counts are season totals by report week. Per-game "
            "denominators wait for refreshed roster, schedule, snap, and stat coverage."
        ),
        "per_game_caveat": (
            "Per-game availability context waits for refreshed roster and schedule "
            "denominators; do not infer unavailable games from report counts."
        ),
        "availability_caveat": (
            "Display-only/review-only factual context. Missing availability context "
            f"remains {NOT_ENOUGH_INFORMATION}."
        ),
        "display_only": "true",
        "review_only": "true",
        "model_input_allowed": "false",
        "rank_use_allowed": "false",
        "source_truth_allowed": "false",
        "clinical_inference_allowed": "false",
    }
    _validate_display_row_contract(row)
    return row


def display_context_schema_rows() -> list[dict[str, str]]:
    rows = [
        _schema_row("player_id", "identity", SAFE_NOW, "Existing approved player identity."),
        _schema_row("gsis_id", "identity", SAFE_NOW, "Approved join key when exact."),
        _schema_row("player_name", "identity", SAFE_NOW, "Display label only."),
        _schema_row("position", "identity", SAFE_NOW, "Display label only."),
        _schema_row(
            "injury_context_available",
            "factual injury context",
            SAFE_NOW,
            "True only when approved injury report rows exist.",
        ),
        _schema_row(
            "prior_season_injury_report_weeks",
            "factual injury context",
            SAFE_NOW,
            "Season-total distinct report weeks, not a per-game denominator.",
        ),
        _schema_row(
            "prior_season_out_or_doubtful_weeks",
            "factual injury context",
            SAFE_NOW,
            "Season-total distinct report weeks with out/doubtful status.",
        ),
    ]
    rows.extend(
        _schema_row(
            field,
            "tracked nflverse player context",
            SAFE_NOW,
            "Safe direct display from tracked artifact for safe identity rows only.",
        )
        for field in NFLVERSE_AVAILABILITY_SAFE_FIELDS
    )
    rows.extend(
        _schema_row(
            field,
            "availability denominator context",
            YELLOW_NEEDS_PLAYER_CONTEXT_ARTIFACT_EXTENSION,
            (
                "Display field is reserved now and remains Not enough information "
                "until a tracked artifact provides an approved denominator."
            ),
        )
        for field in WAITING_AVAILABILITY_FIELDS
    )
    rows.extend(
        [
            _schema_row(
                "season_total_caveat",
                "caveat",
                SAFE_NOW,
                "Explains injury-report counts are season totals by report week.",
            ),
            _schema_row(
                "per_game_caveat",
                "caveat",
                SAFE_NOW,
                "Explains per-game denominators are blocked until refresh green.",
            ),
            _schema_row(
                "availability_caveat",
                "caveat",
                SAFE_NOW,
                "States display-only/review-only and keeps missing context as NEI.",
            ),
        ]
    )
    return rows


def proposal_classification_rows() -> list[dict[str, str]]:
    rows = [
        ProposalClassification(
            "IAC-01",
            SAFE_NOW,
            "Preserve current source gate.",
            "Existing nflreadpy injuries gate remains factual review-only context.",
        ),
        ProposalClassification(
            "IAC-02",
            SAFE_NOW,
            "Continue V0 display in Rankings Outcome Context and Player Compare.",
            "Existing display surfaces remain review-only and unchanged by this lane.",
        ),
        ProposalClassification(
            "IAC-03",
            SAFE_NOW,
            "Show injury-report counts and caveats.",
            "Season-total report-week counts are factual display context.",
        ),
        ProposalClassification(
            "IAC-04",
            SAFE_NOW,
            "Add display-only specs for roster, schedule, snap, and stat datasets.",
            "Tracked player context artifact supports safe direct display fields now.",
        ),
        ProposalClassification(
            "IAC-05",
            YELLOW_NEEDS_PLAYER_CONTEXT_ARTIFACT_EXTENSION,
            "Compute games while rostered.",
            "Requires a tracked denominator artifact; not computed in app pages.",
        ),
        ProposalClassification(
            "IAC-06",
            YELLOW_NEEDS_PLAYER_CONTEXT_ARTIFACT_EXTENSION,
            "Compute games with snaps and games with recorded stats.",
            "Snap recency/sample display is safe; game counts need an artifact extension.",
        ),
        ProposalClassification(
            "IAC-07",
            YELLOW_NEEDS_PLAYER_CONTEXT_ARTIFACT_EXTENSION,
            "Compute games played context.",
            "Last active season/week display is safe; games played remains uncomputed.",
        ),
        ProposalClassification(
            "IAC-08",
            YELLOW_NEEDS_PLAYER_CONTEXT_ARTIFACT_EXTENSION,
            "Compute games missed while rostered.",
            "Requires rostered-game denominator artifact and must not infer cause.",
        ),
        ProposalClassification(
            "IAC-09",
            YELLOW_NEEDS_PLAYER_CONTEXT_ARTIFACT_EXTENSION,
            "Populate per-game denominator labels.",
            "Labels/spec safe now; populated values need an artifact extension.",
        ),
        ProposalClassification(
            "IAC-10",
            YELLOW_NEEDS_PLAYER_CONTEXT_ARTIFACT_EXTENSION,
            "Use dynamic season anchors.",
            "Requires explicit tracked artifact support.",
        ),
        ProposalClassification(
            "IAC-11",
            NEED_MODEL_GATE,
            "Use availability context in rankings, model, outcome, trade, or pick logic.",
            "Requires separate model/rank gate and is not approved here.",
        ),
        ProposalClassification(
            "IAC-12",
            BLOCKED,
            "Reuse LVE durability scoring outputs.",
            "Blocked by HQ; this lane does not import or call that service.",
        ),
        ProposalClassification(
            "IAC-13",
            BLOCKED,
            "Treat missing injury or availability data as an affirmative status.",
            f"Missing context remains {NOT_ENOUGH_INFORMATION}.",
        ),
        ProposalClassification(
            "IAC-14",
            BLOCKED,
            "Use scraped, vendor, Gmail, or rumor sources.",
            "Only approved public NFLVerse factual sources are in scope.",
        ),
    ]
    return [row.__dict__ for row in rows]


def lve_injury_durability_reuse_allowed() -> bool:
    return False


def unsafe_availability_field_names(fields: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    normalized = {field.strip().lower() for field in fields}
    return tuple(field for field in FORBIDDEN_DISPLAY_FIELDS if field in normalized)


def load_tracked_nflverse_availability_sources(
    *,
    artifact_path: str | Path = NFLVERSE_PLAYER_CONTEXT_DISPLAY_PATH,
    schema_path: str | Path = NFLVERSE_PLAYER_CONTEXT_SCHEMA_MANIFEST_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    artifact = Path(artifact_path)
    schema = Path(schema_path)
    if not artifact.exists() or not schema.exists():
        return pd.DataFrame(), pd.DataFrame()
    return (
        pd.read_csv(artifact, dtype=str).fillna(""),
        pd.read_csv(schema, dtype=str).fillna(""),
    )


def nflverse_availability_artifact_counts(
    artifact_frame: pd.DataFrame | None = None,
) -> dict[str, int]:
    if artifact_frame is None:
        artifact_frame, _schema = load_tracked_nflverse_availability_sources()
    rows = int(artifact_frame.shape[0])
    if artifact_frame.empty:
        return {
            "rows": 0,
            "safe_display_rows": 0,
            "identity_review_rows": 0,
            "schedule_current_future_rows": 0,
        }
    safe = _safe_identity_mask(artifact_frame)
    schedule_columns = ("next_game_context", "opponent_context", "bye_context")
    schedule_rows = 0
    if set(schedule_columns).issubset(artifact_frame.columns):
        schedule_rows = int(
            artifact_frame.loc[safe, list(schedule_columns)]
            .apply(
                lambda row: any(_display_value(value) != NOT_ENOUGH_INFORMATION for value in row),
                axis=1,
            )
            .sum()
        )
    return {
        "rows": rows,
        "safe_display_rows": int(safe.sum()),
        "identity_review_rows": int(
            artifact_frame["identity_join_status"].astype(str).eq(NEED_IDENTITY_REVIEW).sum()
        ),
        "schedule_current_future_rows": schedule_rows,
    }


def nflverse_availability_status_rows(
    artifact_frame: pd.DataFrame | None = None,
) -> list[dict[str, str]]:
    counts = nflverse_availability_artifact_counts(artifact_frame)
    return [
        {
            "Question": "NFLVerse player context artifact",
            "Status": (
                f"{counts['safe_display_rows']}/{counts['rows']} safe display rows; "
                f"{counts['identity_review_rows']} identity review rows"
            ),
            "Guardrail": "Join by nwr_player_id; safe rows only for detailed context.",
        },
        {
            "Question": "Identity review rows",
            "Status": REVIEW_NEEDED,
            "Guardrail": "Show review status only; do not expose detailed NFLVerse context.",
        },
        {
            "Question": "Schedule next game/opponent/bye",
            "Status": NOT_ENOUGH_INFORMATION,
            "Guardrail": (
                "Current/future schedule rows available: "
                f"{counts['schedule_current_future_rows']}; do not infer."
            ),
        },
        {
            "Question": "Missing NFLVerse values",
            "Status": NOT_ENOUGH_INFORMATION,
            "Guardrail": "Never zero, clean, inactive, or safe by assumption.",
        },
    ]


def build_nflverse_availability_panel_rows(
    records: list[dict[str, object]],
    *,
    artifact_frame: pd.DataFrame | None = None,
    schema_frame: pd.DataFrame | None = None,
) -> list[dict[str, str]]:
    if artifact_frame is None or schema_frame is None:
        artifact_frame, schema_frame = load_tracked_nflverse_availability_sources()
    schema_safe_fields = _schema_safe_fields(schema_frame)
    return [
        _nflverse_availability_panel_row(record, artifact_frame, schema_safe_fields)
        for record in records
    ]


def _nflverse_availability_panel_row(
    record: dict[str, object],
    artifact_frame: pd.DataFrame,
    schema_safe_fields: set[str],
) -> dict[str, str]:
    player = _clean(record.get("player"), default=NOT_ENOUGH_INFORMATION)
    position = _clean(record.get("position"), default=NOT_ENOUGH_INFORMATION)
    base = _empty_panel_row(player, position)
    context_row = _artifact_row_for_record(record, artifact_frame)
    if context_row is None:
        return base
    identity_status = _clean(context_row.get("identity_join_status"))
    review_required = _clean(context_row.get("review_required")).lower() == "true"
    if identity_status != NFLVERSE_PLAYER_CONTEXT_SAFE_STATUS or review_required:
        base["NFLVerse Availability Context"] = REVIEW_NEEDED
        base["NFLVerse Identity Status"] = REVIEW_NEEDED
        base["Identity Caveat"] = REVIEW_NEEDED
        return base

    base["NFLVerse Availability Context"] = AVAILABILITY_CONTEXT_PRESENT
    base["NFLVerse Identity Status"] = "Matched"
    base["Identity Caveat"] = _field_value(context_row, "identity_caveat", schema_safe_fields)
    base["Roster Status"] = _field_value(context_row, "roster_status", schema_safe_fields)
    base["Weekly Roster Status"] = _field_value(
        context_row,
        "weekly_roster_status",
        schema_safe_fields,
    )
    base["Injury Report Status"] = _field_value(
        context_row,
        "injury_report_status",
        schema_safe_fields,
    )
    base["Practice Status"] = _field_value(context_row, "practice_status", schema_safe_fields)
    base["Injury Report Date / Week"] = _field_value(
        context_row,
        "injury_report_date_week",
        schema_safe_fields,
    )
    base["Last Active"] = _last_active_value(context_row, schema_safe_fields)
    base["Snap Recency"] = _field_value(context_row, "snap_count_recency", schema_safe_fields)
    base["Snap Sample Size"] = _field_value(context_row, "snap_sample_size", schema_safe_fields)
    base["Age Context"] = _age_context_value(context_row, schema_safe_fields)
    base["Schedule Context"] = NOT_ENOUGH_INFORMATION
    base["Data Coverage"] = _field_value(context_row, "data_coverage_status", schema_safe_fields)
    return base


def _wait_dataset_status(
    dataset: str,
    active_compute_use: str,
    caveat: str,
    *,
    safe_now_use: str = "Schema and labels only.",
) -> dict[str, str]:
    return _dataset_status(
        dataset,
        "nflverse pull/status is YELLOW in the current completion gate",
        WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN,
        safe_now_use,
        active_compute_use,
        caveat,
    )


def _schema_safe_fields(schema_frame: pd.DataFrame) -> set[str]:
    if schema_frame.empty:
        return set()
    required = {
        "column_name",
        "field_status",
        "display_only",
        "model_use_allowed",
        "training_allowed",
        "source_truth_allowed",
        "rank_logic_allowed",
        "hidden_sort_allowed",
        "trade_value_allowed",
        "pick_value_allowed",
    }
    if not required.issubset(schema_frame.columns):
        return set()
    safe = schema_frame.loc[
        schema_frame["field_status"].astype(str).eq(NFLVERSE_PLAYER_CONTEXT_SAFE_STATUS)
        & schema_frame["display_only"].astype(str).str.lower().eq("true")
        & schema_frame["model_use_allowed"].astype(str).str.lower().eq("false")
        & schema_frame["training_allowed"].astype(str).str.lower().eq("false")
        & schema_frame["source_truth_allowed"].astype(str).str.lower().eq("false")
        & schema_frame["rank_logic_allowed"].astype(str).str.lower().eq("false")
        & schema_frame["hidden_sort_allowed"].astype(str).str.lower().eq("false")
        & schema_frame["trade_value_allowed"].astype(str).str.lower().eq("false")
        & schema_frame["pick_value_allowed"].astype(str).str.lower().eq("false")
    ]
    return set(safe["column_name"].astype(str))


def _safe_identity_mask(frame: pd.DataFrame) -> pd.Series:
    return frame["identity_join_status"].astype(str).eq(
        NFLVERSE_PLAYER_CONTEXT_SAFE_STATUS
    ) & frame["review_required"].astype(str).str.lower().eq("false")


def _artifact_row_for_record(
    record: dict[str, object],
    artifact_frame: pd.DataFrame,
) -> dict[str, object] | None:
    if artifact_frame.empty or "nwr_player_id" not in artifact_frame.columns:
        return None
    player_id = _clean(record.get("player_id"), default="")
    if not player_id:
        return None
    matches = artifact_frame.loc[artifact_frame["nwr_player_id"].astype(str).eq(player_id)]
    if len(matches) != 1:
        return None
    return matches.iloc[0].to_dict()


def _empty_panel_row(player: str, position: str) -> dict[str, str]:
    return {
        "Player": player,
        "Pos": position,
        "NFLVerse Availability Context": NOT_ENOUGH_INFORMATION,
        "NFLVerse Identity Status": NOT_ENOUGH_INFORMATION,
        "Identity Caveat": NOT_ENOUGH_INFORMATION,
        "Roster Status": NOT_ENOUGH_INFORMATION,
        "Weekly Roster Status": NOT_ENOUGH_INFORMATION,
        "Injury Report Status": NOT_ENOUGH_INFORMATION,
        "Practice Status": NOT_ENOUGH_INFORMATION,
        "Injury Report Date / Week": NOT_ENOUGH_INFORMATION,
        "Last Active": NOT_ENOUGH_INFORMATION,
        "Snap Recency": NOT_ENOUGH_INFORMATION,
        "Snap Sample Size": NOT_ENOUGH_INFORMATION,
        "Age Context": NOT_ENOUGH_INFORMATION,
        "Schedule Context": NOT_ENOUGH_INFORMATION,
        "Data Coverage": NOT_ENOUGH_INFORMATION,
    }


def _field_value(
    row: dict[str, object],
    field_name: str,
    schema_safe_fields: set[str],
) -> str:
    if field_name not in schema_safe_fields:
        return NOT_ENOUGH_INFORMATION
    return _display_value(row.get(field_name))


def _display_value(value: object) -> str:
    text = _clean(value, default="")
    if text in UNAVAILABLE_TOKENS or text.lower() in {"nan", "none", "null", "n/a", "<na>"}:
        return NOT_ENOUGH_INFORMATION
    return text


def _last_active_value(row: dict[str, object], schema_safe_fields: set[str]) -> str:
    season = _field_value(row, "last_active_season", schema_safe_fields)
    week = _field_value(row, "last_active_week", schema_safe_fields)
    if season == NOT_ENOUGH_INFORMATION:
        return NOT_ENOUGH_INFORMATION
    if week == NOT_ENOUGH_INFORMATION:
        return f"season={season}"
    return f"season={season}; week={week}"


def _age_context_value(row: dict[str, object], schema_safe_fields: set[str]) -> str:
    age = _field_value(row, "roster_birth_date_derived_age", schema_safe_fields)
    source = _field_value(row, "age_source", schema_safe_fields)
    if age == NOT_ENOUGH_INFORMATION and source == NOT_ENOUGH_INFORMATION:
        return NOT_ENOUGH_INFORMATION
    if source == NOT_ENOUGH_INFORMATION:
        return age
    if age == NOT_ENOUGH_INFORMATION:
        return source
    return f"{age} ({source})"


def _dataset_status(
    dataset: str,
    current_status: str,
    classification: str,
    safe_now_use: str,
    active_compute_use: str,
    caveat: str,
) -> dict[str, str]:
    return AvailabilityDatasetStatus(
        dataset=dataset,
        current_status=current_status,
        classification=classification,
        safe_now_use=safe_now_use,
        active_compute_use=active_compute_use,
        caveat=caveat,
    ).__dict__


def _schema_row(
    field_name: str,
    field_group: str,
    status: str,
    notes: str,
) -> dict[str, str]:
    return {
        "field_name": field_name,
        "field_group": field_group,
        "status": status,
        "notes": notes,
    }


def _clean(value: object, *, default: str = NOT_ENOUGH_INFORMATION) -> str:
    text = str(value if value is not None else "").strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a", "<na>"}:
        return default
    return text


def _count_or_nei(value: object) -> str:
    text = _clean(value)
    if text == NOT_ENOUGH_INFORMATION:
        return text
    try:
        numeric = int(float(text))
    except ValueError:
        return NOT_ENOUGH_INFORMATION
    if numeric < 0:
        return NOT_ENOUGH_INFORMATION
    return str(numeric)


def _validate_display_row_contract(row: dict[str, str]) -> None:
    unsafe = unsafe_availability_field_names(tuple(row))
    if unsafe:
        raise ValueError(f"Forbidden display fields present: {unsafe}")
    if any(row[field] != NOT_ENOUGH_INFORMATION for field in WAITING_AVAILABILITY_FIELDS):
        raise ValueError("Availability denominator fields must remain Not enough information")
    for field in ("model_input_allowed", "rank_use_allowed", "source_truth_allowed"):
        if row.get(field) != "false":
            raise ValueError(f"{field} must be false")
