from __future__ import annotations

import csv
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

NOT_ENOUGH_INFORMATION = "Not enough information"
FANTASY_POSITIONS = {"QB", "RB", "WR", "TE"}
HIDDEN_DEFAULT_POSITIONS = {"K", "DEF", "DST"}
STATUS_REVIEW_VALUES = {
    "injured reserve",
    "ir",
    "out",
    "pup",
    "nfi",
    "suspended",
    "doubtful",
    "questionable",
}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv_rows(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def normalize_name(value: object) -> str:
    text = str(value or "").lower()
    text = text.replace(" jr.", " jr").replace(" sr.", " sr")
    text = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", text)
    return re.sub(r"[^a-z0-9]+", "", text)


def normalize_position(value: object) -> str:
    text = str(value or "").upper().strip()
    return "DST" if text in {"D/ST", "DEF"} else text


def normalize_team(value: object) -> str:
    return str(value or "").upper().strip()


def row_value(row: Mapping[str, Any], *columns: str) -> str:
    for column in columns:
        value = str(row.get(column, "") or "").strip()
        if value:
            return value
    return ""


def is_hidden_default_position(position: object) -> bool:
    return normalize_position(position) in HIDDEN_DEFAULT_POSITIONS


def is_included_default_position(position: object) -> bool:
    return normalize_position(position) in FANTASY_POSITIONS


def rostered_player_ids(rosters: Iterable[Mapping[str, Any]]) -> set[str]:
    ids: set[str] = set()
    for roster in rosters:
        for player_id in roster.get("players") or []:
            if player_id is not None:
                ids.add(str(player_id))
    return ids


def sleeper_records(players: Mapping[str, Mapping[str, Any]]) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for player_id, player in players.items():
        position = normalize_position(player.get("position"))
        if position not in FANTASY_POSITIONS | HIDDEN_DEFAULT_POSITIONS:
            continue
        name = (
            player.get("full_name")
            or player.get("search_full_name")
            or " ".join(
                part
                for part in (
                    str(player.get("first_name") or ""),
                    str(player.get("last_name") or ""),
                )
                if part.strip()
            )
        )
        records.append(
            {
                "sleeper_player_id": str(player_id),
                "full_name": str(name or ""),
                "position": position,
                "team": normalize_team(player.get("team")),
                "status": str(player.get("status") or ""),
                "injury_status": str(player.get("injury_status") or ""),
                "injury_start_date": str(player.get("injury_start_date") or ""),
                "practice_participation": str(player.get("practice_participation") or ""),
                "age": str(player.get("age") or ""),
                "years_exp": str(player.get("years_exp") or ""),
                "active": str(player.get("active") if player.get("active") is not None else ""),
            }
        )
    return records


def sleeper_lookup(records: Iterable[Mapping[str, str]]) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for record in records:
        player_id = str(record.get("sleeper_player_id") or "").strip()
        if player_id:
            lookup[f"id:{player_id}"] = dict(record)
        key = _identity_key(record.get("full_name"), record.get("position"))
        if key:
            lookup.setdefault(key, dict(record))
    return lookup


def classify_status_warning(
    *,
    player: Mapping[str, str] | None,
    expected_team: str = "",
) -> str:
    if not player:
        return "missing status metadata"
    team = normalize_team(player.get("team"))
    expected = normalize_team(expected_team)
    if expected and team and expected not in {team, "FA"}:
        return "team/status mismatch"
    status_values = " ".join(
        str(player.get(column, "") or "").lower()
        for column in ("status", "injury_status", "injury_start_date", "practice_participation")
    )
    if any(value in status_values for value in STATUS_REVIEW_VALUES):
        return "injury/status review"
    if not str(player.get("status") or player.get("injury_status") or "").strip():
        return "missing status metadata"
    return "clean"


def build_status_context(
    rows: Iterable[Mapping[str, Any]],
    sleeper_lookup_rows: Mapping[str, dict[str, str]],
) -> list[dict[str, str]]:
    context: list[dict[str, str]] = []
    for row in rows:
        name = row_value(row, "player", "player_name", "full_name")
        position = row_value(row, "pos", "position")
        team = row_value(row, "nfl_team", "team")
        match = match_sleeper_player(row, sleeper_lookup_rows)
        context.append(
            {
                "player": name,
                "pos": normalize_position(position),
                "nfl_team": normalize_team(team),
                "sleeper_player_id": str((match or {}).get("sleeper_player_id") or ""),
                "sleeper_team": str((match or {}).get("team") or ""),
                "status": str((match or {}).get("status") or NOT_ENOUGH_INFORMATION),
                "injury_status": str((match or {}).get("injury_status") or NOT_ENOUGH_INFORMATION),
                "injury_start_date": str(
                    (match or {}).get("injury_start_date") or NOT_ENOUGH_INFORMATION
                ),
                "practice_participation": str(
                    (match or {}).get("practice_participation") or NOT_ENOUGH_INFORMATION
                ),
                "age": str((match or {}).get("age") or NOT_ENOUGH_INFORMATION),
                "years_exp": str((match or {}).get("years_exp") or NOT_ENOUGH_INFORMATION),
                "warning_classification": classify_status_warning(
                    player=match,
                    expected_team=team,
                ),
                "source_note": (
                    "Sleeper provides status flags, not full injury/news analysis."
                    if match
                    else "No Sleeper metadata match; do not infer clean health."
                ),
            }
        )
    return context


def build_free_agent_pool_audit(
    *,
    pdf_rows: list[Mapping[str, Any]],
    sleeper_rows: list[Mapping[str, str]],
    rostered_ids: set[str],
) -> list[dict[str, str]]:
    lookup = sleeper_lookup(sleeper_rows)
    pdf_keys = {
        _identity_key(row_value(row, "player", "player_name"), row_value(row, "pos", "position"))
        for row in pdf_rows
    }
    rows: list[dict[str, str]] = []
    for row in pdf_rows:
        match = match_sleeper_player(row, lookup)
        player_id = str((match or {}).get("sleeper_player_id") or "")
        position = normalize_position(row_value(row, "pos", "position"))
        is_rostered = bool(player_id and player_id in rostered_ids)
        rows.append(
            {
                "audit_scope": "pdf_page3_free_agent",
                "player": row_value(row, "player", "player_name"),
                "pos": position,
                "pdf_team": normalize_team(row_value(row, "nfl_team", "team")),
                "sleeper_team": str((match or {}).get("team") or ""),
                "pdf_overall_rank_or_number": row_value(row, "pdf_overall_rank_or_number"),
                "pdf_position_rank": row_value(row, "pdf_position_rank"),
                "sleeper_player_id": player_id,
                "match_method": "exact_name_position" if match else "unmatched",
                "match_confidence": "HIGH" if match else "LOW",
                "sleeper_current_roster_state": (
                    "rostered_conflict" if is_rostered else "unrostered"
                ),
                "include_default": "no" if is_hidden_default_position(position) else "yes",
                "exclude_reason": (
                    "K/DST hidden by default"
                    if is_hidden_default_position(position)
                    else ""
                ),
                "audit_category": _pdf_audit_category(position, match, is_rostered),
                "status_warning": classify_status_warning(
                    player=match,
                    expected_team=row_value(row, "nfl_team", "team"),
                ),
                "source_note": (
                    "LVE PDF page 3 remains human-confirmed draftable pool; "
                    "Sleeper is verifier/update layer."
                ),
            }
        )
    for sleeper in sleeper_rows:
        position = normalize_position(sleeper.get("position"))
        if position not in FANTASY_POSITIONS | HIDDEN_DEFAULT_POSITIONS:
            continue
        if str(sleeper.get("sleeper_player_id") or "") in rostered_ids:
            continue
        if _identity_key(sleeper.get("full_name"), position) in pdf_keys:
            continue
        rows.append(
            {
                "audit_scope": "sleeper_unrostered_not_pdf",
                "player": str(sleeper.get("full_name") or ""),
                "pos": position,
                "pdf_team": "",
                "sleeper_team": str(sleeper.get("team") or ""),
                "pdf_overall_rank_or_number": "",
                "pdf_position_rank": "",
                "sleeper_player_id": str(sleeper.get("sleeper_player_id") or ""),
                "match_method": "sleeper_unrostered",
                "match_confidence": "SOURCE_ONLY",
                "sleeper_current_roster_state": "unrostered",
                "include_default": "yes" if is_included_default_position(position) else "no",
                "exclude_reason": (
                    "K/DST hidden by default"
                    if is_hidden_default_position(position)
                    else "Not in LVE PDF page 3 human-confirmed draftable pool"
                ),
                "audit_category": "SLEEPER_FA_NOT_IN_PDF",
                "status_warning": classify_status_warning(player=sleeper),
                "source_note": (
                    "Sleeper unrostered verifier row; not draftable source truth "
                    "unless policy changes."
                ),
            }
        )
    return rows


def build_identity_coverage_audit(
    *,
    surfaces: Mapping[str, list[Mapping[str, Any]]],
    sleeper_rows: list[Mapping[str, str]],
    dynastyprocess_rows: list[Mapping[str, Any]],
) -> list[dict[str, str]]:
    sleeper_by_key = sleeper_lookup(sleeper_rows)
    dp_by_key = _dynastyprocess_lookup(dynastyprocess_rows)
    rows: list[dict[str, str]] = []
    for surface, source_rows in surfaces.items():
        for source_row in source_rows:
            name = row_value(source_row, "player", "player_name", "full_name", "nwr_name")
            position = normalize_position(row_value(source_row, "pos", "position", "nwr_pos"))
            team = normalize_team(row_value(source_row, "nfl_team", "team"))
            existing_id = row_value(source_row, "player_id", "nwr_player_id", "sleeper_id")
            sleeper_match = match_sleeper_player(source_row, sleeper_by_key)
            dp_match = _match_dynastyprocess(source_row, dp_by_key)
            match_method = _identity_match_method(existing_id, sleeper_match, dp_match)
            match_confidence = _identity_confidence(match_method, position, sleeper_match, dp_match)
            reason = _identity_reason(
                existing_id=existing_id,
                sleeper_match=sleeper_match,
                dp_match=dp_match,
                match_method=match_method,
            )
            rows.append(
                {
                    "source_surface": surface,
                    "player_name": name,
                    "position": position,
                    "team": team,
                    "existing_id_present": "yes" if existing_id else "no",
                    "sleeper_id": str((sleeper_match or {}).get("sleeper_player_id") or ""),
                    "dynastyprocess_id": row_value(dp_match or {}, "fp_id", "nwr_player_id"),
                    "nflverse_id_or_gsis": row_value(source_row, "gsis_id")
                    or row_value(dp_match or {}, "gsis_id"),
                    "match_method": match_method,
                    "match_confidence": match_confidence,
                    "needs_manual_review": "yes" if match_confidence != "HIGH" else "no",
                    "reason": reason,
                }
            )
    return rows


def match_sleeper_player(
    row: Mapping[str, Any],
    sleeper_lookup_rows: Mapping[str, dict[str, str]],
) -> dict[str, str] | None:
    for column in ("sleeper_player_id", "sleeper_id", "player_id"):
        player_id = str(row.get(column, "") or "").strip()
        if player_id and f"id:{player_id}" in sleeper_lookup_rows:
            return sleeper_lookup_rows[f"id:{player_id}"]
    key = _identity_key(
        row_value(row, "player", "player_name", "full_name", "nwr_name"),
        row_value(row, "pos", "position", "nwr_pos"),
    )
    return sleeper_lookup_rows.get(key)


def _identity_key(name: object, position: object) -> str:
    clean_name = normalize_name(name)
    clean_pos = normalize_position(position)
    if not clean_name or not clean_pos:
        return ""
    return f"{clean_name}|{clean_pos}"


def _pdf_audit_category(position: str, match: Mapping[str, str] | None, is_rostered: bool) -> str:
    if is_hidden_default_position(position):
        return "PDF_KDST_HIDDEN_DEFAULT"
    if not match:
        return "PDF_UNMATCHED_TO_SLEEPER"
    if is_rostered:
        return "PDF_MATCHED_BUT_ROSTERED_CONFLICT"
    return "PDF_MATCHED_SLEEPER_FA"


def _dynastyprocess_lookup(rows: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for row in rows:
        record = {str(key): str(value or "") for key, value in row.items()}
        for column in ("sleeper_id", "nwr_player_id"):
            value = str(row.get(column, "") or "").strip()
            if value:
                lookup[f"id:{value}"] = record
        key = _identity_key(row_value(row, "player", "nwr_name"), row_value(row, "pos", "nwr_pos"))
        if key:
            lookup.setdefault(key, record)
    return lookup


def _match_dynastyprocess(
    row: Mapping[str, Any],
    dp_by_key: Mapping[str, dict[str, str]],
) -> dict[str, str] | None:
    for column in ("sleeper_id", "player_id", "nwr_player_id"):
        value = str(row.get(column, "") or "").strip()
        if value and f"id:{value}" in dp_by_key:
            return dp_by_key[f"id:{value}"]
    key = _identity_key(
        row_value(row, "player", "player_name", "full_name", "nwr_name"),
        row_value(row, "pos", "position", "nwr_pos"),
    )
    return dp_by_key.get(key)


def _identity_match_method(
    existing_id: str,
    sleeper_match: Mapping[str, str] | None,
    dp_match: Mapping[str, str] | None,
) -> str:
    if existing_id and sleeper_match:
        return "existing_id_to_sleeper"
    if existing_id and dp_match:
        return "existing_id_to_dynastyprocess"
    if sleeper_match and dp_match:
        return "exact_name_position_sleeper_and_dynastyprocess"
    if sleeper_match:
        return "exact_name_position_sleeper"
    if dp_match:
        return "exact_name_position_dynastyprocess"
    if existing_id:
        return "existing_id_unverified"
    return "unresolved"


def _identity_confidence(
    match_method: str,
    position: str,
    sleeper_match: Mapping[str, str] | None,
    dp_match: Mapping[str, str] | None,
) -> str:
    if match_method in {
        "existing_id_to_sleeper",
        "existing_id_to_dynastyprocess",
        "exact_name_position_sleeper_and_dynastyprocess",
    }:
        return "HIGH"
    if match_method.startswith("exact_name_position") and position in FANTASY_POSITIONS:
        return "MEDIUM"
    if sleeper_match or dp_match:
        return "LOW"
    return "LOW"


def _identity_reason(
    *,
    existing_id: str,
    sleeper_match: Mapping[str, str] | None,
    dp_match: Mapping[str, str] | None,
    match_method: str,
) -> str:
    if match_method == "unresolved":
        return "No stable ID or exact name+position match; keep visible but require manual review."
    parts: list[str] = []
    if existing_id:
        parts.append("existing_id_present")
    if sleeper_match:
        parts.append("sleeper_match")
    if dp_match:
        parts.append("dynastyprocess_crosswalk_candidate")
    if match_method.endswith("unverified"):
        parts.append("existing ID was not found in admitted crosswalks")
    return "; ".join(parts)
