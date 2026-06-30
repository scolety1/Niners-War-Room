from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.services.draft_day_app_v1_service import (
    NFLVERSE_PLAYER_CONTEXT_DISPLAY_PATH,
    NFLVERSE_PLAYER_CONTEXT_SAFE_STATUS,
    NFLVERSE_PLAYER_CONTEXT_SCHEMA_MANIFEST_PATH,
    OUTCOME_NOT_ENOUGH_INFORMATION,
    file_sha256,
    outcome_v2_text_display,
    validate_nflverse_player_context_display,
)

NEED_IDENTITY_REVIEW = "NEED_IDENTITY_REVIEW"
DISPLAY_STATUS = "Display-only / Review-only context / Not model input"
SOURCE_LABEL = "NFLVerse player context display artifact"
AS_OF_LABEL = "2026-06-30 tracked NFLVerse player context display artifact"

UNAVAILABLE_TOKENS = {
    "",
    OUTCOME_NOT_ENOUGH_INFORMATION,
    "NEED_DATASET_REFRESH",
    "NEED_IDENTITY_REVIEW",
    "NEED_SCHEMA_REVIEW",
    "BLOCKED_SOURCE_POLICY",
    "BLOCKED_VENDOR_OR_PRIVATE",
    "Review needed",
}


@dataclass(frozen=True)
class DraftDayPlayerContextSection:
    title: str
    rows: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class DraftDayPlayerContextResult:
    status: str
    message: str
    source: str
    as_of: str
    nwr_player_id: str
    player_label: str
    source_path: Path | None
    source_hash: str | None
    sections: tuple[DraftDayPlayerContextSection, ...]
    errors: tuple[str, ...] = ()

    @property
    def available(self) -> bool:
        return self.status == "available"


def build_player_context_options(frame: pd.DataFrame) -> dict[str, str]:
    if frame.empty:
        return {}
    options: dict[str, str] = {}
    for _, row in frame.iterrows():
        player_id = _value(row, "nwr_player_id") or _value(row, "player_id")
        if not player_id:
            continue
        name = _value(row, "nwr_player_name") or _value(row, "player_name") or _value(row, "player")
        position = _value(row, "nwr_position") or _value(row, "position")
        team = _value(row, "nwr_team") or _value(row, "nfl_team") or _value(row, "team")
        rank = _value(row, "nwr_rank") or _value(row, "final_board_rank")
        label_parts = []
        if rank:
            label_parts.append(f"#{rank}")
        label_parts.append(name or f"Player {player_id}")
        side = ", ".join(part for part in (position, team) if part)
        label = " - ".join(label_parts)
        if side:
            label = f"{label} ({side})"
        options[label] = player_id
    return options


def draft_day_player_context_for_player(
    nwr_player_id: object,
    *,
    artifact_path: Path = NFLVERSE_PLAYER_CONTEXT_DISPLAY_PATH,
    schema_path: Path = NFLVERSE_PLAYER_CONTEXT_SCHEMA_MANIFEST_PATH,
) -> DraftDayPlayerContextResult:
    player_id = str(nwr_player_id or "").strip()
    if not player_id:
        return _unavailable("Not enough information", player_id=player_id)

    source = _load_source(artifact_path=artifact_path, schema_path=schema_path)
    if source["errors"]:
        return _unavailable(
            "Not enough information",
            player_id=player_id,
            source_path=artifact_path if artifact_path.exists() else None,
            source_hash=source["source_hash"],
            errors=tuple(source["errors"]),
        )

    frame: pd.DataFrame = source["frame"]
    row_frame = frame.loc[frame["nwr_player_id"].astype(str).str.strip().eq(player_id)]
    if row_frame.empty:
        return _unavailable(
            "Not enough information",
            player_id=player_id,
            source_path=artifact_path,
            source_hash=source["source_hash"],
        )
    row = row_frame.iloc[0].to_dict()
    player_label = _player_label(row)
    if not _safe_identity_row(row):
        return DraftDayPlayerContextResult(
            status="needs_identity_review",
            message="Needs identity review",
            source=SOURCE_LABEL,
            as_of=AS_OF_LABEL,
            nwr_player_id=player_id,
            player_label=player_label,
            source_path=artifact_path,
            source_hash=source["source_hash"],
            sections=(
                DraftDayPlayerContextSection(
                    "Identity / Status",
                    (
                        ("NWR player id", player_id),
                        ("Identity status", "Needs identity review"),
                        ("Display status", DISPLAY_STATUS),
                        ("Source", SOURCE_LABEL),
                        ("As of", AS_OF_LABEL),
                    ),
                ),
            ),
        )

    safe_fields: set[str] = source["safe_fields"]
    sections = (
        DraftDayPlayerContextSection(
            "Identity / Status",
            _section_rows(
                row,
                safe_fields,
                (
                    ("NWR player id", "nwr_player_id"),
                    ("NFLVerse GSIS id", "nflverse_gsis_id"),
                    ("NFLVerse Sleeper id", "nflverse_sleeper_id"),
                    ("Player", "nflverse_player_name"),
                    ("Team", "nflverse_team"),
                    ("Position", "nflverse_position"),
                    ("Identity join status", "identity_join_status"),
                    ("Roster status", "roster_status"),
                    ("Weekly roster status", "weekly_roster_status"),
                    ("Display status", None),
                    ("Source", None),
                    ("As of", None),
                ),
            ),
        ),
        DraftDayPlayerContextSection(
            "Availability Context",
            _section_rows(
                row,
                safe_fields,
                (
                    ("Injury report status", "injury_report_status"),
                    ("Practice status", "practice_status"),
                    ("Report week/date", "injury_report_date_week"),
                    ("Roster status", "roster_status"),
                    ("Weekly roster status", "weekly_roster_status"),
                    ("Missing data policy", None),
                ),
            ),
        ),
        DraftDayPlayerContextSection(
            "Role / Depth Context",
            _section_rows(
                row,
                safe_fields,
                (
                    ("Depth chart position", "depth_chart_position"),
                    ("Depth chart rank", "depth_chart_rank"),
                    ("Depth chart role", "depth_chart_role"),
                    ("Snap recency", "snap_count_recency"),
                    ("Snap sample size", "snap_sample_size"),
                    ("Last active season", "last_active_season"),
                    ("Last active week", "last_active_week"),
                    ("Missing data policy", None),
                ),
            ),
        ),
        DraftDayPlayerContextSection(
            "Production / Activity Context",
            _section_rows(
                row,
                safe_fields,
                (
                    ("Last active season", "last_active_season"),
                    ("Last active week", "last_active_week"),
                    ("Latest snap season", "latest_snap_season"),
                    ("Latest snap week", "latest_snap_week"),
                    ("Snap sample size", "snap_sample_size"),
                    ("Missing data policy", None),
                ),
            ),
        ),
        DraftDayPlayerContextSection(
            "Draft Capital Context",
            _section_rows(
                row,
                safe_fields,
                (
                    ("NFL draft year", "draft_year"),
                    ("Round", "draft_round"),
                    ("Overall pick", "draft_pick"),
                    ("Draft team", "drafted_team"),
                    ("Missing data policy", None),
                ),
            ),
        ),
        DraftDayPlayerContextSection(
            "Contract Context",
            _section_rows(
                row,
                safe_fields,
                (
                    ("Non-financial contract context", "contract_context"),
                    ("Missing data policy", None),
                ),
            ),
        ),
        DraftDayPlayerContextSection(
            "Schedule Context",
            (
                ("Next game", OUTCOME_NOT_ENOUGH_INFORMATION),
                ("Opponent", OUTCOME_NOT_ENOUGH_INFORMATION),
                ("Bye", OUTCOME_NOT_ENOUGH_INFORMATION),
                ("Status", "Not enough information"),
                ("Reason", "Current artifact has no current/future safe schedule rows."),
            ),
        ),
    )
    return DraftDayPlayerContextResult(
        status="available",
        message="Display-only NFLVerse player context loaded.",
        source=SOURCE_LABEL,
        as_of=AS_OF_LABEL,
        nwr_player_id=player_id,
        player_label=player_label,
        source_path=artifact_path,
        source_hash=source["source_hash"],
        sections=sections,
    )


def _load_source(*, artifact_path: Path, schema_path: Path) -> dict[str, Any]:
    if not artifact_path.exists() or not schema_path.exists():
        return {
            "frame": pd.DataFrame(),
            "safe_fields": set(),
            "source_hash": None,
            "errors": (f"{SOURCE_LABEL} was not found.",),
        }
    frame = pd.read_csv(artifact_path, dtype=str).fillna("")
    schema = pd.read_csv(schema_path, dtype=str).fillna("")
    errors = validate_nflverse_player_context_display(frame, schema)
    safe_fields = {
        str(row.get("column_name", "")).strip()
        for row in schema.to_dict("records")
        if str(row.get("field_status", "")).strip() == NFLVERSE_PLAYER_CONTEXT_SAFE_STATUS
        and str(row.get("display_only", "")).strip().lower() == "true"
        and str(row.get("model_use_allowed", "")).strip().lower() == "false"
        and str(row.get("source_truth_allowed", "")).strip().lower() == "false"
        and str(row.get("rank_logic_allowed", "")).strip().lower() == "false"
        and str(row.get("hidden_sort_allowed", "")).strip().lower() == "false"
        and str(row.get("trade_value_allowed", "")).strip().lower() == "false"
        and str(row.get("pick_value_allowed", "")).strip().lower() == "false"
    }
    return {
        "frame": frame,
        "safe_fields": safe_fields,
        "source_hash": file_sha256(artifact_path),
        "errors": tuple(errors),
    }


def _section_rows(
    row: dict[str, Any],
    safe_fields: set[str],
    fields: tuple[tuple[str, str | None], ...],
) -> tuple[tuple[str, str], ...]:
    rows: list[tuple[str, str]] = []
    for label, field in fields:
        if field is None:
            rows.append((label, _static_value(label)))
            continue
        if field not in safe_fields:
            rows.append((label, OUTCOME_NOT_ENOUGH_INFORMATION))
            continue
        rows.append((label, _display_value(row.get(field))))
    return tuple(rows)


def _safe_identity_row(row: dict[str, Any]) -> bool:
    return (
        str(row.get("identity_join_status", "")).strip() == NFLVERSE_PLAYER_CONTEXT_SAFE_STATUS
        and str(row.get("review_required", "")).strip().lower() == "false"
    )


def _display_value(value: object) -> str:
    text = outcome_v2_text_display(value)
    return OUTCOME_NOT_ENOUGH_INFORMATION if text in UNAVAILABLE_TOKENS else text


def _static_value(label: str) -> str:
    if label == "Display status":
        return DISPLAY_STATUS
    if label == "Source":
        return SOURCE_LABEL
    if label == "As of":
        return AS_OF_LABEL
    if label == "Missing data policy":
        return "Missing data is not negative evidence; use Not enough information."
    return OUTCOME_NOT_ENOUGH_INFORMATION


def _player_label(row: dict[str, Any]) -> str:
    name = _display_value(row.get("nwr_player_name"))
    position = _display_value(row.get("nwr_position"))
    team = _display_value(row.get("nwr_team"))
    side = ", ".join(
        part for part in (position, team) if part != OUTCOME_NOT_ENOUGH_INFORMATION
    )
    return f"{name} ({side})" if side else name


def _unavailable(
    message: str,
    *,
    player_id: str,
    source_path: Path | None = None,
    source_hash: str | None = None,
    errors: tuple[str, ...] = (),
) -> DraftDayPlayerContextResult:
    return DraftDayPlayerContextResult(
        status="unavailable",
        message=message,
        source=SOURCE_LABEL,
        as_of=AS_OF_LABEL,
        nwr_player_id=player_id,
        player_label=OUTCOME_NOT_ENOUGH_INFORMATION,
        source_path=source_path,
        source_hash=source_hash,
        sections=(
            DraftDayPlayerContextSection(
                "Identity / Status",
                (
                    ("NWR player id", player_id or OUTCOME_NOT_ENOUGH_INFORMATION),
                    ("Status", OUTCOME_NOT_ENOUGH_INFORMATION),
                    ("Display status", DISPLAY_STATUS),
                    ("Source", SOURCE_LABEL),
                    ("As of", AS_OF_LABEL),
                ),
            ),
        ),
        errors=errors,
    )


def _value(row: pd.Series, column: str) -> str:
    return str(row.get(column, "") or "").strip()
