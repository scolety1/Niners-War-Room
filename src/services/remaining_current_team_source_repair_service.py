from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.config.constants import DEFAULT_DATA_PACK
from src.services.full_board_identity_team_repair_service import (
    DEFAULT_REPAIR_AUDIT_CSV as DEFAULT_IDENTITY_TEAM_REPAIR_AUDIT_CSV,
)
from src.services.full_player_board_value_service import DEFAULT_FULL_PLAYER_BOARD_ROWS
from src.services.model_v4_identity_join_gate_service import normalize_identity_name
from src.services.rotowire_local_team_status_service import (
    DEFAULT_ROTOWIRE_TEAM_STATUS_ROWS,
    rotowire_team_status_lookup,
    select_rotowire_team_status_row,
)

DEFAULT_REMAINING_TEAM_REPAIR_CSV = Path(
    "local_exports/model_v4/current_value/latest/remaining_current_team_source_repair.csv"
)
DEFAULT_REMAINING_TEAM_REPAIR_REPORT = Path(
    "docs/model_v4/REMAINING_CURRENT_TEAM_SOURCE_REPAIR_20260608.md"
)

REMAINING_TEAM_REPAIR_HEADER = (
    "player",
    "position",
    "age",
    "nwr_rank",
    "nwr_score",
    "current_team_before",
    "rotowire_matched",
    "rotowire_match_method",
    "rotowire_team",
    "rotowire_status",
    "rotowire_injury_status",
    "candidate_team_sources",
    "selected_current_team",
    "selected_source_path",
    "selected_source_column",
    "selected_source_as_of_date",
    "source_agreement_status",
    "repair_status",
    "should_remain_quarantined",
    "trust_status_after_repair",
    "warning_flags_before",
    "warning_flags_after",
    "human_readable_data_needed",
    "repair_note",
)

NAMED_REMAINING_TEAM_PLAYERS = (
    "Stefon Diggs",
    "Joe Mixon",
    "Keenan Allen",
    "Jauan Jennings",
    "Kareem Hunt",
    "Gabe Davis",
    "Zach Ertz",
    "David Njoku",
    "Najee Harris",
    "Nick Chubb",
    "Darren Waller",
    "Aaron Rodgers",
    "Matt Prater",
    "Darius Slayton",
)

NON_KICKER_TARGETS = tuple(
    player
    for player in NAMED_REMAINING_TEAM_PLAYERS
    if player not in {"Matt Prater", "Darius Slayton"}
)

CURRENT_TEAM_SOURCE_SPECS = (
    (
        "fact_rosters.nfl_team",
        Path("fact_rosters.csv"),
        "nfl_team",
        ("snapshot_date", "season"),
        "current-team",
    ),
    (
        "fact_official_rankings.nfl_team",
        Path("fact_official_rankings.csv"),
        "nfl_team",
        ("rank_source_date", "snapshot_date", "season"),
        "current-team",
    ),
    (
        "dim_players.nfl_team",
        Path("dim_players.csv"),
        "nfl_team",
        ("updated_at", "created_at"),
        "current-team",
    ),
)

DERIVED_TEAM_SOURCE = "full_player_board_value_review_rows.nfl_team"


@dataclass(frozen=True)
class RemainingCurrentTeamSourceRepairResult:
    rows: tuple[dict[str, object], ...]
    report_text: str
    summary: dict[str, object]


@dataclass(frozen=True)
class RemainingCurrentTeamSourceRepairPaths:
    repair_csv: Path
    report: Path


def build_remaining_current_team_source_repair(
    *,
    data_pack_path: str | Path = DEFAULT_DATA_PACK,
    full_board_path: str | Path = DEFAULT_FULL_PLAYER_BOARD_ROWS,
    identity_team_repair_path: str | Path = DEFAULT_IDENTITY_TEAM_REPAIR_AUDIT_CSV,
) -> RemainingCurrentTeamSourceRepairResult:
    pack = Path(data_pack_path)
    full_rows = _by_name(_read_rows(Path(full_board_path)))
    identity_rows = _by_player(_read_rows(Path(identity_team_repair_path)))
    source_rows = {
        source: _by_player_id(_read_rows(pack / relative_path))
        for source, relative_path, _column, _dates, _kind in CURRENT_TEAM_SOURCE_SPECS
    }
    rotowire_lookup = rotowire_team_status_lookup()

    rows = tuple(
        _repair_row(
            player=player,
            full_row=full_rows.get(_name_key(player), {}),
            identity_row=identity_rows.get(_name_key(player), {}),
            source_rows=source_rows,
            rotowire_row=select_rotowire_team_status_row(
                rotowire_lookup.get(
                    (
                        normalize_identity_name(player),
                        str(
                            full_rows.get(_name_key(player), {}).get("position")
                            or identity_rows.get(_name_key(player), {}).get("position")
                            or ""
                        ).upper(),
                    ),
                    (),
                )
            ),
            pack=pack,
        )
        for player in NAMED_REMAINING_TEAM_PLAYERS
    )
    summary = _summary(rows)
    return RemainingCurrentTeamSourceRepairResult(
        rows=rows,
        report_text=_report(summary, rows),
        summary=summary,
    )


def write_remaining_current_team_source_repair(
    *,
    result: RemainingCurrentTeamSourceRepairResult | None = None,
    repair_csv: str | Path = DEFAULT_REMAINING_TEAM_REPAIR_CSV,
    report_path: str | Path = DEFAULT_REMAINING_TEAM_REPAIR_REPORT,
) -> RemainingCurrentTeamSourceRepairPaths:
    result = result or build_remaining_current_team_source_repair()
    csv_path = Path(repair_csv)
    doc_path = Path(report_path)
    _write_csv(csv_path, REMAINING_TEAM_REPAIR_HEADER, result.rows)
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(result.report_text, encoding="utf-8")
    return RemainingCurrentTeamSourceRepairPaths(repair_csv=csv_path, report=doc_path)


def _repair_row(
    *,
    player: str,
    full_row: dict[str, str],
    identity_row: dict[str, str],
    source_rows: dict[str, dict[str, dict[str, str]]],
    rotowire_row: dict[str, str],
    pack: Path,
) -> dict[str, object]:
    player_id = str(full_row.get("player_id") or identity_row.get("canonical_player_id") or "")
    candidates = _candidate_sources(player_id, source_rows, pack)
    if rotowire_row:
        candidates.insert(
            0,
            {
                "source": "rotowire_nfl_team_status",
                "path": rotowire_row.get("source_file", str(DEFAULT_ROTOWIRE_TEAM_STATUS_ROWS)),
                "column": "nfl_team/status",
                "value": rotowire_row.get("nfl_team", ""),
                "as_of": rotowire_row.get("source_as_of_date", ""),
                "kind": "current-team-status",
                "status": rotowire_row.get("status", ""),
            },
        )
    derived_team = str(full_row.get("nfl_team") or "").strip()
    if derived_team:
        candidates.append(
            {
                "source": DERIVED_TEAM_SOURCE,
                "path": str(Path(DEFAULT_FULL_PLAYER_BOARD_ROWS)),
                "column": "nfl_team",
                "value": derived_team,
                "as_of": str(full_row.get("score_as_of_date") or ""),
                "kind": "derived-current-team",
            }
        )
    selected = _select_source(candidates)
    position = str(full_row.get("position") or identity_row.get("position") or "")
    is_kicker = position == "K"
    repair_status = _repair_status(selected, candidates, is_kicker)
    should_quarantine = repair_status in {
        "unresolved_missing_current_team_source",
        "unresolved_conflicting_current_team_sources",
        "unresolved_identity_ambiguous",
        "inactive_or_retirement_status_needs_source",
        "keep_quarantined_pending_source",
        "intentionally_hidden_kicker",
        "current_status_verified_no_team",
    }
    warning_before = str(
        full_row.get("raw_model_warning_flags")
        or identity_row.get("warning_flags_before")
        or full_row.get("warning_flags")
        or ""
    )
    warning_after = str(
        full_row.get("warning_flags") or identity_row.get("warning_flags_after") or ""
    )
    return {
        "player": player,
        "position": position,
        "age": full_row.get("age") or identity_row.get("age") or "",
        "nwr_rank": full_row.get("nwr_rank") or identity_row.get("nwr_rank") or "",
        "nwr_score": full_row.get("nwr_dynasty_score") or identity_row.get("nwr_score") or "",
        "current_team_before": (
            full_row.get("nfl_team") or identity_row.get("chosen_canonical_team") or ""
        ),
        "rotowire_matched": "yes" if rotowire_row else "no",
        "rotowire_match_method": "exact_normalized_full_name_position" if rotowire_row else "",
        "rotowire_team": rotowire_row.get("nfl_team", ""),
        "rotowire_status": rotowire_row.get("status", ""),
        "rotowire_injury_status": rotowire_row.get("injury_status", ""),
        "candidate_team_sources": _candidate_summary(candidates),
        "selected_current_team": selected.get("value", ""),
        "selected_source_path": selected.get("path", ""),
        "selected_source_column": selected.get("column", ""),
        "selected_source_as_of_date": selected.get("as_of", ""),
        "source_agreement_status": _agreement_status(candidates, selected),
        "repair_status": repair_status,
        "should_remain_quarantined": "1" if should_quarantine else "0",
        "trust_status_after_repair": full_row.get("trust_status")
        or identity_row.get("trust_status_after_repair")
        or "",
        "warning_flags_before": warning_before,
        "warning_flags_after": warning_after,
        "human_readable_data_needed": _data_needed(repair_status),
        "repair_note": _repair_note(repair_status, selected),
    }


def _candidate_sources(
    player_id: str,
    source_rows: dict[str, dict[str, dict[str, str]]],
    pack: Path,
) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    if not player_id:
        return candidates
    for source, relative_path, column, date_columns, kind in CURRENT_TEAM_SOURCE_SPECS:
        row = source_rows.get(source, {}).get(player_id, {})
        if not row:
            continue
        value = str(row.get(column) or "").strip()
        candidates.append(
            {
                "source": source,
                "path": str(pack / relative_path),
                "column": column,
                "value": _team_alias(value),
                "as_of": _first_value(row, date_columns),
                "kind": kind,
            }
        )
    return candidates


def _select_source(candidates: list[dict[str, str]]) -> dict[str, str]:
    nonblank = [candidate for candidate in candidates if candidate.get("value")]
    values = {_team_alias(candidate.get("value")) for candidate in nonblank}
    if len(values) != 1:
        return {}
    for candidate in nonblank:
        if candidate.get("source") == "rotowire_nfl_team_status":
            return candidate
    for source, _relative_path, _column, _dates, _kind in CURRENT_TEAM_SOURCE_SPECS:
        for candidate in nonblank:
            if candidate.get("source") == source:
                return candidate
    return nonblank[0] if nonblank else {}


def _repair_status(
    selected: dict[str, str],
    candidates: list[dict[str, str]],
    is_kicker: bool,
) -> str:
    if is_kicker:
        return "intentionally_hidden_kicker"
    if any(
        candidate.get("source") == "rotowire_nfl_team_status"
        and candidate.get("status") == "free_agent_or_no_team"
        for candidate in candidates
    ):
        return "current_status_verified_no_team"
    nonblank = [candidate for candidate in candidates if candidate.get("value")]
    values = {_team_alias(candidate.get("value")) for candidate in nonblank}
    if len(values) > 1:
        return "unresolved_conflicting_current_team_sources"
    if selected.get("value"):
        return "resolved_current_team_verified"
    return "unresolved_missing_current_team_source"


def _agreement_status(
    candidates: list[dict[str, str]],
    selected: dict[str, str],
) -> str:
    nonblank = [candidate for candidate in candidates if candidate.get("value")]
    values = {_team_alias(candidate.get("value")) for candidate in nonblank}
    if len(values) > 1:
        return "conflicting_current_team_sources"
    if selected.get("value") and len(nonblank) > 1:
        return "current_sources_agree"
    if selected.get("value"):
        return "single_current_source_found"
    if candidates:
        return "sources_present_but_team_blank"
    return "no_candidate_source_rows"


def _candidate_summary(candidates: list[dict[str, str]]) -> str:
    parts = []
    for candidate in candidates:
        value = candidate.get("value") or "<blank>"
        parts.append(
            f"{candidate.get('source')}={value}"
            f" ({candidate.get('kind')}; {candidate.get('path')}; "
            f"{candidate.get('column')}; as_of={candidate.get('as_of') or '<blank>'})"
        )
    return " | ".join(parts)


def _data_needed(repair_status: str) -> str:
    if repair_status == "resolved_current_team_verified":
        return "No current-team repair needed from available local sources."
    if repair_status == "intentionally_hidden_kicker":
        return (
            "Kicker hidden by default; current-team repair is not required for default "
            "QB/RB/WR/TE Rankings review."
        )
    if repair_status == "current_status_verified_no_team":
        return "Local RotoWire source verifies no current NFL team; do not invent a team."
    if repair_status == "unresolved_conflicting_current_team_sources":
        return "Need conflicting current NFL team/status sources reconciled."
    if repair_status == "unresolved_identity_ambiguous":
        return "Need canonical player identity source before current-team repair."
    if repair_status == "inactive_or_retirement_status_needs_source":
        return "Need active/free-agent/retirement status source for this player."
    return "Need current NFL team/status source for this player."


def _repair_note(repair_status: str, selected: dict[str, str]) -> str:
    if repair_status == "resolved_current_team_verified":
        return (
            f"Selected {selected.get('value')} from {selected.get('source')} with "
            "source path and column receipt."
        )
    if repair_status == "intentionally_hidden_kicker":
        return "Left as hidden/default-off kicker; no team guessed."
    if repair_status == "current_status_verified_no_team":
        return "Selected local RotoWire team/status source; no NFL team is listed."
    return "Kept formally quarantined; no current team guessed from context-only data."


def _summary(rows: tuple[dict[str, object], ...]) -> dict[str, object]:
    non_kicker_rows = [row for row in rows if row.get("position") != "K"]
    resolved_non_kickers = [
        row
        for row in non_kicker_rows
        if row.get("repair_status") == "resolved_current_team_verified"
        and row.get("player") in NON_KICKER_TARGETS
    ]
    unresolved_non_kickers = [
        row
        for row in non_kicker_rows
        if str(row.get("should_remain_quarantined")) == "1"
        and row.get("player") in NON_KICKER_TARGETS
    ]
    statuses: dict[str, int] = {}
    for row in rows:
        status = str(row.get("repair_status") or "")
        statuses[status] = statuses.get(status, 0) + 1
    return {
        "named_rows": len(rows),
        "named_non_kicker_targets": len(NON_KICKER_TARGETS),
        "named_non_kicker_rows_resolved": len(resolved_non_kickers),
        "named_non_kicker_rows_still_quarantined": len(unresolved_non_kickers),
        "intentionally_hidden_kickers": statuses.get("intentionally_hidden_kicker", 0),
        "status_counts": statuses,
    }


def _report(summary: dict[str, object], rows: tuple[dict[str, object], ...]) -> str:
    lines = [
        "# Remaining Current Team Source Repair - 2026-06-08",
        "",
        "This pass resolves or formally quarantines the remaining named current-team "
        "source gaps in Dynasty Rankings. It does not tune formulas, change NWR "
        "scores, modify ranking math, use market/league/legacy values, or touch the "
        "Decision Board.",
        "",
        "## Local Sources Searched",
        "",
        "- Active pack `fact_rosters.csv` `nfl_team`.",
        "- Active pack `fact_official_rankings.csv` `nfl_team`.",
        "- Active pack `dim_players.csv` `nfl_team`.",
        "- Normalized local RotoWire team/status rows.",
        "- Derived full-board `full_player_board_value_review_rows.csv` `nfl_team`.",
        "- Existing identity repair audit receipts.",
        "- Broader local CSV/export scan for named players. Historical/component "
        "team hits were treated as context-only unless they came from the active "
        "current-team precedence above.",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| named rows | {summary['named_rows']} |",
        f"| named non-kicker targets | {summary['named_non_kicker_targets']} |",
        f"| named non-kicker rows resolved | {summary['named_non_kicker_rows_resolved']} |",
        "| named non-kicker rows still quarantined | "
        f"{summary['named_non_kicker_rows_still_quarantined']} |",
        f"| intentionally hidden kickers | {summary['intentionally_hidden_kickers']} |",
        "",
        "## Status Counts",
        "",
        "| Repair status | Count |",
        "| --- | ---: |",
    ]
    for status, count in sorted(dict(summary["status_counts"]).items()):
        lines.append(f"| {status} | {count} |")
    lines.extend(
        [
            "",
            "## Named Rows",
            "",
            "| Player | Pos | Selected team | Repair status | Quarantine | Data needed |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| {player} | {position} | {team} | {status} | {quarantine} | {needed} |".format(
                player=row.get("player", ""),
                position=row.get("position", ""),
                team=row.get("selected_current_team", "")
                or row.get("rotowire_team", "")
                or "-",
                status=row.get("repair_status", ""),
                quarantine=row.get("should_remain_quarantined", ""),
                needed=row.get("human_readable_data_needed", ""),
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Rows with `unresolved_missing_current_team_source` remain capped/quarantined "
            "until a local current NFL team/status source is imported or repaired. "
            "Historical stats, old checkpoints, fantasy roster/team names, and component "
            "context were not allowed to clear the current-team source gap.",
        ]
    )
    return "\n".join(lines) + "\n"


def _by_name(rows: tuple[dict[str, str], ...]) -> dict[str, dict[str, str]]:
    return {
        _name_key(row.get("player_name") or row.get("player") or ""): row
        for row in rows
        if row.get("player_name") or row.get("player")
    }


def _by_player(rows: tuple[dict[str, str], ...]) -> dict[str, dict[str, str]]:
    return {
        _name_key(row.get("player") or row.get("player_name") or ""): row
        for row in rows
        if row.get("player") or row.get("player_name")
    }


def _by_player_id(rows: tuple[dict[str, str], ...]) -> dict[str, dict[str, str]]:
    return {str(row.get("player_id") or ""): row for row in rows if row.get("player_id")}


def _name_key(value: object) -> str:
    return normalize_identity_name(str(value or ""))


def _first_value(row: dict[str, str], columns: tuple[str, ...]) -> str:
    for column in columns:
        value = str(row.get(column) or "").strip()
        if value:
            return value
    return ""


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
