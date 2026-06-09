from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.config.constants import DEFAULT_DATA_PACK
from src.services.full_board_score_movement_audit_service import DEFAULT_MOVEMENT_AUDIT_ROWS
from src.services.full_player_board_value_service import (
    DEFAULT_FULL_PLAYER_BOARD_ROWS,
    FULL_BOARD_SCORE_COLUMN,
)
from src.services.model_v4_identity_join_gate_service import normalize_identity_name
from src.services.rotowire_local_team_status_service import (
    rotowire_team_status_lookup,
    select_rotowire_team_status_row,
)

DEFAULT_FULL_BOARD_CURRENT_VALUE_ROWS = Path(
    "local_exports/model_v4/current_value/latest/current_player_value_full_board_review_rows.csv"
)
DEFAULT_OLD_CHECKPOINT_ROWS = Path(
    "local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv"
)
DEFAULT_REPAIR_AUDIT_CSV = Path(
    "local_exports/model_v4/current_value/latest/full_board_identity_team_repair_audit.csv"
)
DEFAULT_REPAIR_REPORT = Path(
    "docs/model_v4/FULL_BOARD_IDENTITY_TEAM_SOURCE_REPAIR_20260608.md"
)

IDENTITY_REPAIR_HEADER = (
    "player",
    "position",
    "age",
    "active_board_team",
    "model_v4_export_team",
    "old_checkpoint_team",
    "dim_players_team",
    "injury_status_team",
    "roster_team",
    "chosen_canonical_team",
    "team_resolution_status",
    "identity_join_key",
    "canonical_player_id",
    "matched_source_count",
    "mismatched_source_count",
    "mismatch_type",
    "is_historical_only_mismatch",
    "is_current_source_conflict",
    "should_remain_quarantined",
    "trust_status_after_repair",
    "nwr_rank",
    "nwr_score",
    "league_rank",
    "market_rank",
    "warning_flags_before",
    "warning_flags_after",
    "human_readable_data_needed",
    "repair_note",
)

CURRENT_TEAM_PRECEDENCE = (
    "rotowire_nfl_team_status.nfl_team",
    "fact_rosters.nfl_team",
    "fact_official_rankings.nfl_team",
    "dim_players.nfl_team",
    "current_player_value_full_board.nfl_team",
)

SOURCE_WARNING_TOKENS = (
    "team_mismatch",
    "identity_review",
    "partial_or_quarantined",
    "stale_team",
    "stale_status",
    "missing_score_disclosure",
    "unmatched_identity",
    "duplicate_identity",
    "historical_team_context_warning",
)


@dataclass(frozen=True)
class IdentityTeamRepairAuditResult:
    rows: tuple[dict[str, object], ...]
    report_text: str
    summary: dict[str, object]


@dataclass(frozen=True)
class IdentityTeamRepairAuditPaths:
    audit_csv: Path
    report: Path


def build_identity_team_repair_audit(
    *,
    data_pack_path: str | Path = DEFAULT_DATA_PACK,
    full_board_path: str | Path = DEFAULT_FULL_PLAYER_BOARD_ROWS,
    full_current_value_path: str | Path = DEFAULT_FULL_BOARD_CURRENT_VALUE_ROWS,
    old_checkpoint_path: str | Path = DEFAULT_OLD_CHECKPOINT_ROWS,
    movement_path: str | Path = DEFAULT_MOVEMENT_AUDIT_ROWS,
) -> IdentityTeamRepairAuditResult:
    pack = Path(data_pack_path)
    full_rows = _read_rows(Path(full_board_path))
    full_current_rows = _lookup(_read_rows(Path(full_current_value_path)))
    old_rows = _lookup(_read_rows(Path(old_checkpoint_path)))
    movement_rows = _movement_lookup(_read_rows(Path(movement_path)))
    official_by_id = _by_player_id(_read_rows(pack / "fact_official_rankings.csv"))
    roster_by_id = _by_player_id(_read_rows(pack / "fact_rosters.csv"))
    dim_by_id = _by_player_id(_read_rows(pack / "dim_players.csv"))
    rotowire_lookup = rotowire_team_status_lookup()

    rows = tuple(
        _repair_row(
            row=row,
            official=official_by_id.get(str(row.get("player_id") or ""), {}),
            roster=roster_by_id.get(str(row.get("player_id") or ""), {}),
            dim=dim_by_id.get(str(row.get("player_id") or ""), {}),
            rotowire=select_rotowire_team_status_row(
                rotowire_lookup.get(_join_key(row), ())
            ),
            full_current=full_current_rows.get(_join_key(row), {}),
            old=old_rows.get(_join_key(row), {}),
            movement=movement_rows.get(_join_key(row), {}),
        )
        for row in full_rows
        if _repair_audit_required(row)
    )
    summary = _summary(rows)
    report = _report(summary)
    return IdentityTeamRepairAuditResult(rows=rows, report_text=report, summary=summary)


def write_identity_team_repair_audit(
    *,
    result: IdentityTeamRepairAuditResult | None = None,
    audit_csv: str | Path = DEFAULT_REPAIR_AUDIT_CSV,
    report_path: str | Path = DEFAULT_REPAIR_REPORT,
) -> IdentityTeamRepairAuditPaths:
    result = result or build_identity_team_repair_audit()
    csv_path = Path(audit_csv)
    doc_path = Path(report_path)
    _write_csv(csv_path, IDENTITY_REPAIR_HEADER, result.rows)
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(result.report_text, encoding="utf-8")
    return IdentityTeamRepairAuditPaths(audit_csv=csv_path, report=doc_path)


def _repair_row(
    *,
    row: dict[str, str],
    official: dict[str, str],
    roster: dict[str, str],
    dim: dict[str, str],
    rotowire: dict[str, str],
    full_current: dict[str, str],
    old: dict[str, str],
    movement: dict[str, str],
) -> dict[str, object]:
    current_sources = {
        "rotowire_nfl_team_status.nfl_team": rotowire.get("nfl_team", ""),
        "fact_rosters.nfl_team": roster.get("nfl_team", ""),
        "fact_official_rankings.nfl_team": official.get("nfl_team", ""),
        "dim_players.nfl_team": dim.get("nfl_team", ""),
        "current_player_value_full_board.nfl_team": full_current.get("nfl_team", ""),
    }
    chosen_source, canonical_team = _choose_canonical_team(current_sources)
    current_values = [_team_alias(team) for team in current_sources.values() if team]
    unique_current_values = set(current_values)
    warning_before = row.get("raw_model_warning_flags") or row.get("warning_flags", "")
    warning_after = row.get("warning_flags", "")
    old_team = movement.get("team_old") or old.get("nfl_team", "")
    active_team = (
        rotowire.get("nfl_team")
        or roster.get("nfl_team")
        or official.get("nfl_team")
        or dim.get("nfl_team")
        or row.get("nfl_team", "")
    )
    resolution = _resolution_status(
        canonical_team=canonical_team,
        current_unique=unique_current_values,
        row=row,
        warning_before=warning_before,
        rotowire=rotowire,
    )
    historical_only = _is_historical_only(
        old_team=old_team,
        canonical_team=canonical_team,
        resolution=resolution,
        warning_after=warning_after,
    )
    current_conflict = len(unique_current_values) > 1
    should_quarantine = resolution.startswith("unresolved") or (
        "missing_score_disclosure" in warning_after
    )
    return {
        "player": movement.get("player") or row.get("player_name", ""),
        "position": row.get("position", ""),
        "age": row.get("age", ""),
        "active_board_team": active_team,
        "model_v4_export_team": full_current.get("nfl_team") or row.get("nfl_team", ""),
        "old_checkpoint_team": old_team,
        "dim_players_team": dim.get("nfl_team", ""),
        "injury_status_team": rotowire.get("injury_status", ""),
        "roster_team": roster.get("nfl_team", ""),
        "chosen_canonical_team": canonical_team,
        "team_resolution_status": resolution,
        "identity_join_key": (
            f"{normalize_identity_name(row.get('player_name'))}:{row.get('position', '')}"
        ),
        "canonical_player_id": row.get("player_id", ""),
        "matched_source_count": sum(team == canonical_team for team in current_values),
        "mismatched_source_count": max(0, len(unique_current_values) - 1),
        "mismatch_type": _mismatch_type(resolution, historical_only, current_conflict),
        "is_historical_only_mismatch": "1" if historical_only else "0",
        "is_current_source_conflict": "1" if current_conflict else "0",
        "should_remain_quarantined": "1" if should_quarantine else "0",
        "trust_status_after_repair": row.get("trust_status", ""),
        "nwr_rank": row.get("nwr_rank", ""),
        "nwr_score": row.get(FULL_BOARD_SCORE_COLUMN, ""),
        "league_rank": row.get("league_rank", ""),
        "market_rank": row.get("market_rank", ""),
        "warning_flags_before": warning_before,
        "warning_flags_after": warning_after,
        "human_readable_data_needed": _data_needed(resolution, historical_only),
        "repair_note": _repair_note(resolution, chosen_source, historical_only),
    }


def _report(summary: dict[str, object]) -> str:
    lines = [
        "# Full Board Identity Team Source Repair - 2026-06-08",
        "",
        "This source cleanup defines Rankings identity/team precedence and classifies "
        "team warnings. It does not tune formulas, change scores, mutate generated "
        "active rankings, or touch the Decision Board.",
        "",
        "## Canonical Source Precedence",
        "",
        "- Identity join key priority: `player_id` for source joins, then normalized "
        "`player_name + position` for Model v4 row joins.",
        "- Display name priority: movement-audit name when preserving old-vs-new audit "
        "context, then full-board `player_name`, then active pack name.",
        "- Current NFL team/status priority: normalized local "
        "`rotowire_nfl_team_status` exact match, then `fact_rosters.nfl_team`, "
        "then `fact_official_rankings.nfl_team`, then `dim_players.nfl_team`, "
        "then `current_player_value_full_board.nfl_team` as a derived fallback.",
        "- RotoWire `FA`/teamless rows verify no current team but cannot invent a team.",
        "- Historical/context teams: old 80-row checkpoint teams and imported component "
        "source teams are context only; they cannot override current-team sources.",
        "- Active-board team handling: `model_outputs.csv` has no NFL team field, so "
        "active-board current team is read from roster/official/dim sidecars.",
        "- Model v4 source team handling: full-board current-value team is derived from "
        "the active truth set and is not allowed to override conflicting current "
        "source files.",
        "- Injury/status team handling: no injury/status team file is present in the "
        "active pack; missing source stays blank.",
        "- Rookie/prospect team handling: rookie board does not provide current NFL "
        "team authority for active veteran Rankings rows.",
        "- True mismatch means two current-team sources conflict. Historical-only "
        "mismatch means current sources agree but old/context team differs.",
        "- Historical-only rows can rank with a visible context warning. Current-source "
        "conflicts, missing current team, missing canonical id, or missing disclosure "
        "stay quarantined.",
        "",
        "## Repair Summary",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
    ]
    for key in (
        "audit_rows",
        "resolved_current_team_verified",
        "resolved_historical_team_only",
        "unresolved_current_source_conflict",
        "unresolved_missing_current_team_source",
        "current_status_verified_no_team",
        "rows_should_remain_quarantined",
        "historical_only_downgraded",
    ):
        lines.append(f"| {key} | {summary.get(key, 0)} |")
    return "\n".join(lines) + "\n"


def _summary(rows: tuple[dict[str, object], ...]) -> dict[str, object]:
    statuses = [str(row.get("team_resolution_status") or "") for row in rows]
    return {
        "audit_rows": len(rows),
        "resolved_current_team_verified": statuses.count("resolved_current_team_verified"),
        "resolved_historical_team_only": statuses.count("resolved_historical_team_only"),
        "unresolved_current_source_conflict": statuses.count("unresolved_current_source_conflict"),
        "unresolved_missing_current_team_source": statuses.count(
            "unresolved_missing_current_team_source"
        ),
        "current_status_verified_no_team": statuses.count("current_status_verified_no_team"),
        "rows_should_remain_quarantined": sum(
            str(row.get("should_remain_quarantined")) == "1" for row in rows
        ),
        "historical_only_downgraded": sum(
            str(row.get("is_historical_only_mismatch")) == "1"
            and str(row.get("should_remain_quarantined")) == "0"
            for row in rows
        ),
    }


def _resolution_status(
    *,
    canonical_team: str,
    current_unique: set[str],
    row: dict[str, str],
    warning_before: str,
    rotowire: dict[str, str],
) -> str:
    if not row.get("player_id"):
        return "unresolved_missing_canonical_id"
    if (
        not canonical_team
        and rotowire.get("status") == "free_agent_or_no_team"
        and rotowire.get("source_file")
    ):
        return "current_status_verified_no_team"
    if not canonical_team:
        return "unresolved_missing_current_team_source"
    if len(current_unique) > 1:
        return "unresolved_current_source_conflict"
    if "historical_team_context_warning" in str(row.get("warning_flags") or ""):
        return "resolved_historical_team_only"
    if "team_mismatch_or_missing_model_team" in warning_before:
        return "resolved_historical_team_only"
    return "resolved_current_team_verified"


def _is_historical_only(
    *,
    old_team: str,
    canonical_team: str,
    resolution: str,
    warning_after: str,
) -> bool:
    if resolution == "resolved_historical_team_only":
        return True
    if old_team and canonical_team and _team_alias(old_team) != _team_alias(canonical_team):
        return "historical_team_context_warning" in warning_after
    return False


def _mismatch_type(resolution: str, historical_only: bool, current_conflict: bool) -> str:
    if current_conflict:
        return "current_source_conflict"
    if historical_only:
        return "historical_team_only"
    if resolution == "unresolved_missing_current_team_source":
        return "missing_current_team_source"
    if resolution == "current_status_verified_no_team":
        return "current_status_verified_no_team"
    if resolution.startswith("unresolved_identity"):
        return "identity_ambiguous"
    return "current_team_verified"


def _data_needed(resolution: str, historical_only: bool) -> str:
    if resolution == "unresolved_current_source_conflict":
        return "Need current-team source conflict resolved before clean trust."
    if resolution == "unresolved_missing_current_team_source":
        return "Need a current NFL team source from roster, official ranking, or dim player data."
    if resolution == "current_status_verified_no_team":
        return "Local RotoWire source verifies no current NFL team; do not invent a team."
    if resolution == "unresolved_missing_canonical_id":
        return "Need canonical player id before clean identity trust."
    if historical_only:
        return "Historical team differs from verified current team; keep context warning visible."
    return "No current-team repair needed from available sources."


def _repair_note(resolution: str, source: str, historical_only: bool) -> str:
    if historical_only:
        return f"Downgraded from severe mismatch; current team verified by {source}."
    if resolution.startswith("unresolved"):
        return "Kept quarantined pending stronger source evidence."
    if resolution == "current_status_verified_no_team":
        return "No team assigned; local RotoWire source verifies teamless/free-agent status."
    return f"Current team verified by {source}."


def _choose_canonical_team(sources: dict[str, str]) -> tuple[str, str]:
    for source in CURRENT_TEAM_PRECEDENCE:
        team = _team_alias(sources.get(source))
        if team:
            return source, team
    return "", ""


def _repair_audit_required(row: dict[str, str]) -> bool:
    text = "|".join(
        (
            row.get("raw_model_warning_flags", ""),
            row.get("warning_flags", ""),
        )
    ).lower()
    return any(token in text for token in SOURCE_WARNING_TOKENS)


def _lookup(rows: tuple[dict[str, str], ...]) -> dict[tuple[str, str], dict[str, str]]:
    return {_join_key(row): row for row in rows}


def _movement_lookup(rows: tuple[dict[str, str], ...]) -> dict[tuple[str, str], dict[str, str]]:
    lookup: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        lookup[_join_key_from_player(row.get("player"), row.get("position"))] = row
        lookup.setdefault(_suffix_stripped_join_key(row.get("player"), row.get("position")), row)
    return lookup


def _by_player_id(rows: tuple[dict[str, str], ...]) -> dict[str, dict[str, str]]:
    return {str(row.get("player_id") or ""): row for row in rows if row.get("player_id")}


def _join_key(row: dict[str, object]) -> tuple[str, str]:
    return _join_key_from_player(row.get("player_name"), row.get("position"))


def _join_key_from_player(player: object, position: object) -> tuple[str, str]:
    return (normalize_identity_name(str(player or "")), str(position or "").upper())


def _suffix_stripped_join_key(player: object, position: object) -> tuple[str, str]:
    normalized = normalize_identity_name(str(player or ""))
    for suffix in ("iii", "ii", "iv", "jr", "sr", "v"):
        if normalized.endswith(suffix):
            return (normalized[: -len(suffix)], str(position or "").upper())
    return (normalized, str(position or "").upper())


def _team_alias(value: object) -> str:
    team = str(value or "").strip().upper()
    return {"LA": "LAR"}.get(team, team)


def _read_rows(path: Path) -> tuple[dict[str, str], ...]:
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return tuple(csv.DictReader(handle))


def _write_csv(path: Path, header: tuple[str, ...], rows: tuple[dict[str, object], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
