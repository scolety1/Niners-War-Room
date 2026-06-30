from __future__ import annotations

from dataclasses import dataclass
from typing import Final

NOT_ENOUGH_INFORMATION: Final = "Not enough information"
WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN: Final = (
    "WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN"
)
SAFE_NOW: Final = "SAFE_NOW"
NEED_MODEL_GATE: Final = "NEED_MODEL_GATE"
BLOCKED: Final = "BLOCKED"

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
            "APPROVE_INJURY_CONTEXT_REVIEW_ONLY",
            SAFE_NOW,
            "Factual injury report counts and status context already used by V0.",
            "Review-only display context only.",
            (
                "Report rows vary by season and week. Missing rows remain "
                f"{NOT_ENOUGH_INFORMATION}."
            ),
        ),
        _wait_dataset_status(
            "nflverse_weekly_rosters",
            "Do not compute games while rostered until refresh health is green.",
            "Needed for rostered-game denominators and team-change handling.",
        ),
        _wait_dataset_status(
            "nflverse_rosters",
            "Do not use as active availability context until refresh health is green.",
            "Needed for identity/team context and season anchors.",
        ),
        _wait_dataset_status(
            "nflverse_schedules",
            "Do not compute schedule denominators until refresh health is green.",
            "Needed for per-game, bye-week, and team-game denominators.",
        ),
        _wait_dataset_status(
            "nflverse_snap_counts",
            "Do not compute games with snaps until refresh health is green.",
            "Needed for factual participation context.",
        ),
        _wait_dataset_status(
            "nflverse_player_stats",
            "Do not compute games with recorded stats until refresh health is green.",
            "Needed for factual recorded-stat participation context.",
        ),
        _wait_dataset_status(
            "refresh_metadata",
            "Do not choose dynamic season anchors until refresh health is green.",
            "Needed before switching from fixed V0 season context to refreshed anchors.",
            safe_now_use="Document expected season-anchor behavior only.",
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
        "availability_context_status": WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN,
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
            "availability denominator context",
            WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN,
            (
                "Display field is reserved now and remains Not enough information "
                "until refreshed NFLVerse coverage is green."
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
            "Docs/schema safe now; active data use waits for refresh health green.",
        ),
        ProposalClassification(
            "IAC-05",
            WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN,
            "Compute games while rostered.",
            "Requires refreshed weekly_rosters and schedules coverage.",
        ),
        ProposalClassification(
            "IAC-06",
            WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN,
            "Compute games with snaps and games with recorded stats.",
            "Requires refreshed snap_counts and player_stats coverage.",
        ),
        ProposalClassification(
            "IAC-07",
            WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN,
            "Compute games played context.",
            "Requires refreshed participation inputs and denominator validation.",
        ),
        ProposalClassification(
            "IAC-08",
            WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN,
            "Compute games missed while rostered.",
            "Requires refreshed roster and schedule denominators.",
        ),
        ProposalClassification(
            "IAC-09",
            WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN,
            "Populate per-game denominator labels.",
            "Label/spec safe now; populated values wait for refresh health green.",
        ),
        ProposalClassification(
            "IAC-10",
            WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN,
            "Use dynamic season anchors.",
            "Requires refreshed metadata and explicit green health status.",
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
