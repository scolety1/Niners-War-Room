from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack
from src.services.player_feature_receipts_service import DEFAULT_RECEIPT_VETERAN_MODEL_DIR

SUPPORTED_POSITIONS = {"QB", "RB", "WR", "TE"}
HIGH_VALUE_IDENTITY_THRESHOLD = 85.0
LOW_IDENTITY_CONFIDENCE_THRESHOLD = 80.0
IDENTITY_BRIDGE_FILE = "sleeper_nflverse_identity_bridge.csv"
ACTIVE_IDENTITY_REVIEW_FILE = "active_roster_identity_review.csv"
STALE_ACTIVE_FLAGS = {"0", "false", "inactive", "retired", "stale"}
STALE_ROSTER_STATUSES = {"inactive", "retired", "stale", "deleted"}


@dataclass(frozen=True)
class IdentityAuditReport:
    rows: list[dict[str, object]]
    summary_rows: list[dict[str, object]]
    blocked_rows: list[dict[str, object]]
    statuses: list[str]
    match_methods: list[str]
    issues: list[str]
    source_root: str


def build_identity_audit(
    data_pack_path: str | Path,
    *,
    source_root: str | Path | None = None,
) -> IdentityAuditReport:
    root = Path(source_root) if source_root else DEFAULT_RECEIPT_VETERAN_MODEL_DIR
    validated = validate_data_pack(data_pack_path)
    if validated.has_errors:
        return _empty_report(root, ["Data pack has validation errors."])

    bridge_path = root / IDENTITY_BRIDGE_FILE
    active_path = root / ACTIVE_IDENTITY_REVIEW_FILE
    bridge_rows = _read_optional_csv(bridge_path)
    active_rows = _read_optional_csv(active_path)
    if not bridge_path.exists() and not active_path.exists():
        return _empty_report(root, ["No identity bridge or active identity review file found."])

    bridge_lookup = _identity_lookup(bridge_rows)
    active_lookup = _active_lookup(active_rows)
    players = [
        row
        for row in validated.rows_by_table.get("players", [])
        if str(row.get("position") or "") in SUPPORTED_POSITIONS
    ]
    roster_lookup = _roster_lookup(validated.rows_by_table.get("rosters", []))
    model_lookup = _model_lookup(validated.rows_by_table.get("model_outputs", []))
    duplicate_name_counts = _duplicate_name_counts(players)
    rows = [
        _audit_row(
            player,
            roster_lookup.get(str(player.get("player_id") or ""), {}),
            model_lookup.get(str(player.get("player_id") or ""), {}),
            bridge_lookup,
            active_lookup,
            duplicate_name_counts,
        )
        for player in players
    ]
    rows.sort(
        key=lambda row: (
            0 if row["ranking_trust_status"] == "blocked_identity_review" else 1,
            _status_priority(str(row["audit_status"])),
            _float(row["identity_confidence"]),
            str(row["player"]).lower(),
        )
    )
    blocked_rows = [row for row in rows if row["ranking_trust_status"] == "blocked_identity_review"]
    return IdentityAuditReport(
        rows=rows,
        summary_rows=_summary_rows(rows),
        blocked_rows=blocked_rows,
        statuses=sorted({str(row["audit_status"]) for row in rows}),
        match_methods=sorted({str(row["match_method"]) for row in rows if row["match_method"]}),
        issues=[],
        source_root=str(root),
    )


def _empty_report(root: Path, issues: list[str]) -> IdentityAuditReport:
    return IdentityAuditReport([], [], [], [], [], issues, str(root))


def _audit_row(
    player: dict[str, object],
    roster_row: dict[str, object],
    model_row: dict[str, object],
    bridge_lookup: dict[str, dict[str, str]],
    active_lookup: dict[str, dict[str, str]],
    duplicate_name_counts: dict[tuple[str, str], int],
) -> dict[str, object]:
    player_id = str(player.get("player_id") or "")
    explicit_sleeper_id = str(player.get("sleeper_id") or "")
    sleeper_id = explicit_sleeper_id or player_id
    local_name = str(player.get("player_name") or roster_row.get("player_name") or "")
    local_position = str(player.get("position") or roster_row.get("position") or "")
    local_team = str(player.get("nfl_team") or roster_row.get("nfl_team") or "")
    duplicate_count = duplicate_name_counts.get((_name_key(local_name), local_position), 0)
    stale_reason = _stale_player_reason(player, roster_row)
    bridge_row = _match_bridge_row(player, sleeper_id, bridge_lookup)
    active_row = _match_active_row(
        sleeper_id,
        player_id,
        local_name,
        local_position,
        duplicate_count,
        active_lookup,
    )
    match_row = {**bridge_row, **active_row}
    match_method = _match_method(match_row, bridge_row, active_row)
    match_status = str(match_row.get("match_status") or "")
    external_ids = _external_ids(player, bridge_row, active_row)
    name_agreement = _name_agreement(local_name, match_row)
    position_agreement = _position_agreement(local_position, match_row)
    team_agreement = _team_agreement(local_team, match_row)
    identity_confidence = _identity_confidence(
        match_method,
        match_status,
        name_agreement,
        position_agreement,
        team_agreement,
        external_ids,
        duplicate_count,
        _boolish(match_row.get("manual_review_required")),
    )
    if stale_reason:
        identity_confidence = 0.0
    high_value_score = max(
        _float(model_row.get("war_score")),
        _float(model_row.get("private_score")),
        _float(model_row.get("keeper_score")),
    )
    audit_status, issue = _audit_status(
        identity_confidence,
        match_method,
        match_status,
        name_agreement,
        position_agreement,
        external_ids,
        duplicate_count,
        _boolish(match_row.get("manual_review_required")),
        stale_reason,
    )
    identity_status = _identity_status(
        audit_status=audit_status,
        match_method=match_method,
        match_status=match_status,
        external_ids=external_ids,
        duplicate_count=duplicate_count,
        active_manual_review=_boolish(match_row.get("manual_review_required")),
        stale_reason=stale_reason,
    )
    ranking_blocked = bool(
        stale_reason
        or (
            high_value_score >= HIGH_VALUE_IDENTITY_THRESHOLD
            and identity_confidence < LOW_IDENTITY_CONFIDENCE_THRESHOLD
        )
    )
    review_required = audit_status != "ready" or ranking_blocked
    return {
        "player_id": player_id,
        "sleeper_id": sleeper_id,
        "player": local_name,
        "position": local_position,
        "team": local_team,
        "local_player_id": player_id,
        "sleeper_gsis_id": external_ids["sleeper_gsis_id"],
        "nflverse_gsis_id": external_ids["nflverse_gsis_id"],
        "pfr_id": external_ids["pfr_id"],
        "matched_stat_player": match_row.get("stat_player_name")
        or match_row.get("bridge_name")
        or match_row.get("player_name", ""),
        "match_method": match_method,
        "match_status": match_status or ("matched" if bridge_row else "unmatched"),
        "identity_status": identity_status,
        "identity_confidence": round(identity_confidence, 2),
        "audit_status": audit_status,
        "ranking_trust_status": "blocked_identity_review" if ranking_blocked else audit_status,
        "high_value_score": high_value_score,
        "ranking_blocked": ranking_blocked,
        "name_agreement": name_agreement,
        "position_agreement": position_agreement,
        "team_agreement": team_agreement,
        "duplicate_name_count": duplicate_count,
        "duplicate_name_flag": duplicate_count > 1,
        "missing_sleeper_id": not explicit_sleeper_id,
        "missing_gsis_id": not external_ids["nflverse_gsis_id"],
        "missing_pfr_id": not external_ids["pfr_id"],
        "rookie_year": player.get("rookie_year", ""),
        "rookie_flag": _is_rookie(player),
        "stale_player_flag": bool(stale_reason),
        "manual_review_required": review_required,
        "manual_review_status": "needed" if review_required else "not_needed",
        "manual_resolution": "",
        "manual_review_note": issue,
        "review_owner": "",
        "review_updated_at": "",
    }


def _identity_lookup(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for row in rows:
        for key in (
            row.get("sleeper_id", ""),
            row.get("player_id", ""),
            row.get("bridge_gsis_id", ""),
            row.get("matched_gsis_id", ""),
            row.get("bridge_pfr_id", ""),
        ):
            if key and key not in lookup:
                lookup[key] = row
    return lookup


def _active_lookup(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for row in rows:
        key = row.get("sleeper_id") or row.get("player_id")
        if key:
            lookup[key] = row
        name_key = _name_key(row.get("player_name", ""))
        position = row.get("position", "")
        if name_key and position:
            lookup[f"name::{name_key}::{position}"] = row
    return lookup


def _match_bridge_row(
    player: dict[str, object],
    sleeper_id: str,
    bridge_lookup: dict[str, dict[str, str]],
) -> dict[str, str]:
    for key in (
        sleeper_id,
        str(player.get("player_id") or ""),
        str(player.get("pfr_id") or ""),
    ):
        if key and key in bridge_lookup:
            return bridge_lookup[key]
    return {}


def _match_active_row(
    sleeper_id: str,
    player_id: str,
    local_name: str,
    local_position: str,
    duplicate_count: int,
    active_lookup: dict[str, dict[str, str]],
) -> dict[str, str]:
    direct = active_lookup.get(sleeper_id) or active_lookup.get(player_id)
    if direct:
        return direct
    if duplicate_count > 1:
        return {}
    return active_lookup.get(f"name::{_name_key(local_name)}::{local_position}", {})


def _match_method(
    match_row: dict[str, str],
    bridge_row: dict[str, str],
    active_row: dict[str, str],
) -> str:
    if active_row.get("match_method"):
        return active_row["match_method"]
    if bridge_row.get("match_method"):
        return bridge_row["match_method"]
    return ""


def _external_ids(
    player: dict[str, object],
    bridge_row: dict[str, str],
    active_row: dict[str, str],
) -> dict[str, str]:
    return {
        "sleeper_gsis_id": str(
            active_row.get("sleeper_gsis_id")
            or bridge_row.get("sleeper_gsis_id")
            or ""
        ),
        "nflverse_gsis_id": str(
            active_row.get("matched_gsis_id")
            or bridge_row.get("matched_gsis_id")
            or bridge_row.get("bridge_gsis_id")
            or ""
        ),
        "pfr_id": str(player.get("pfr_id") or bridge_row.get("bridge_pfr_id") or ""),
    }


def _name_agreement(local_name: str, match_row: dict[str, str]) -> str:
    candidates = [
        match_row.get("stat_player_name", ""),
        match_row.get("bridge_name", ""),
        match_row.get("player_name", ""),
    ]
    if not local_name or not any(candidates):
        return "missing"
    local_key = _name_key(local_name)
    local_loose = _loose_name_key(local_name)
    for candidate in candidates:
        if candidate == local_name:
            return "exact"
        if _name_key(candidate) == local_key:
            return "normalized"
        if _loose_name_key(candidate) == local_loose:
            return "suffix_or_punctuation_variant"
    return "mismatch"


def _position_agreement(local_position: str, match_row: dict[str, str]) -> str:
    matched_position = match_row.get("position", "")
    if not matched_position:
        return "missing"
    return "match" if local_position == matched_position else "mismatch"


def _team_agreement(local_team: str, match_row: dict[str, str]) -> str:
    matched_team = match_row.get("team", "")
    if not matched_team:
        return "not_available"
    if not local_team:
        return "missing_local_team"
    return "match" if local_team == matched_team else "team_change_or_mismatch"


def _identity_confidence(
    match_method: str,
    match_status: str,
    name_agreement: str,
    position_agreement: str,
    team_agreement: str,
    external_ids: dict[str, str],
    duplicate_count: int,
    active_manual_review: bool,
) -> float:
    base_by_method = {
        "sleeper_gsis_exact": 98.0,
        "player_id": 94.0,
        "sleeper_id": 94.0,
        "dynastyprocess_sleeper_to_gsis": 92.0,
        "pfr_id": 88.0,
        "manual": 85.0,
        "name_position_team": 72.0,
        "name_fallback": 58.0,
        "unmatched": 0.0,
    }
    confidence = base_by_method.get(match_method, 82.0 if match_status == "matched" else 0.0)
    if match_status in {"unmatched", "blocked"}:
        confidence = 0.0
    if match_status == "ambiguous":
        confidence = min(confidence, 45.0)
    if name_agreement == "mismatch":
        confidence -= 35.0
    elif name_agreement == "missing":
        confidence -= 12.0
    elif name_agreement == "suffix_or_punctuation_variant":
        confidence -= 2.0
    if position_agreement == "mismatch":
        confidence -= 50.0
    elif position_agreement == "missing":
        confidence -= 5.0
    if team_agreement == "team_change_or_mismatch":
        confidence -= 4.0
    if not external_ids["nflverse_gsis_id"]:
        confidence -= 18.0
    if not external_ids["pfr_id"]:
        confidence -= 4.0
    if duplicate_count > 1 and match_method in {"name_position_team", "name_fallback", ""}:
        confidence = min(confidence, 55.0)
    if active_manual_review:
        confidence = min(confidence, 45.0)
    return max(0.0, min(100.0, confidence))


def _audit_status(
    identity_confidence: float,
    match_method: str,
    match_status: str,
    name_agreement: str,
    position_agreement: str,
    external_ids: dict[str, str],
    duplicate_count: int,
    active_manual_review: bool,
    stale_reason: str = "",
) -> tuple[str, str]:
    if stale_reason:
        return "blocked", stale_reason
    if not match_method or match_status in {"unmatched", "blocked"}:
        return "blocked", "No trusted Sleeper-to-nflverse match exists."
    if match_status == "ambiguous":
        return "review", "Identity bridge has an ambiguous match."
    if position_agreement == "mismatch":
        return "blocked", "Position does not agree between local and matched identity."
    if not external_ids["nflverse_gsis_id"]:
        return "blocked", "Missing nflverse/GSIS ID for stat joins."
    if identity_confidence < 50:
        return "blocked", "Identity confidence is too low for stat-backed scoring."
    if active_manual_review:
        return "review", "Identity bridge marked this player for manual review."
    if name_agreement == "mismatch":
        return "review", "Name mismatch requires manual review."
    if duplicate_count > 1 and match_method in {"name_position_team", "name_fallback", ""}:
        return "review", "Duplicate local names require a stable external ID."
    if identity_confidence < LOW_IDENTITY_CONFIDENCE_THRESHOLD:
        return "review", "Identity confidence is below the trust threshold."
    return "ready", ""


def _identity_status(
    *,
    audit_status: str,
    match_method: str,
    match_status: str,
    external_ids: dict[str, str],
    duplicate_count: int,
    active_manual_review: bool,
    stale_reason: str,
) -> str:
    if stale_reason:
        return "stale_player"
    if not match_method or match_status in {"unmatched", "blocked"}:
        return "missing_match"
    if match_status == "ambiguous" or active_manual_review:
        return "ambiguous_match"
    if duplicate_count > 1 and match_method in {"name_position_team", "name_fallback", ""}:
        return "ambiguous_match"
    if audit_status == "blocked":
        return "missing_match"
    if match_method in {"sleeper_gsis_exact", "sleeper_id", "player_id"} and external_ids[
        "nflverse_gsis_id"
    ]:
        return "exact_id_match"
    if match_method in {"dynastyprocess_sleeper_to_gsis", "pfr_id", "manual"}:
        return "crosswalk_match"
    if match_method in {"name_position_team", "name_fallback"}:
        return "name_team_position_match"
    return "crosswalk_match" if external_ids["nflverse_gsis_id"] else "missing_match"


def _summary_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for status in ("ready", "review", "blocked"):
        status_rows = [row for row in rows if row["audit_status"] == status]
        output.append(
            {
                "audit_status": status,
                "rows": len(status_rows),
                "high_value_blocked": sum(
                    1
                    for row in status_rows
                    if row["ranking_trust_status"] == "blocked_identity_review"
                ),
                "manual_review_required": sum(
                    1 for row in status_rows if row["manual_review_required"]
                ),
                "missing_gsis": sum(1 for row in status_rows if row["missing_gsis_id"]),
                "duplicate_names": sum(1 for row in status_rows if row["duplicate_name_flag"]),
                "stale_players": sum(1 for row in status_rows if row["stale_player_flag"]),
            }
        )
    return output


def _roster_lookup(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(row.get("player_id") or ""): row for row in rows if row.get("player_id")}


def _model_lookup(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(row.get("player_id") or ""): row for row in rows if row.get("player_id")}


def _duplicate_name_counts(players: list[dict[str, object]]) -> dict[tuple[str, str], int]:
    counts: dict[tuple[str, str], int] = {}
    for player in players:
        key = (
            _name_key(str(player.get("merge_name") or player.get("player_name") or "")),
            str(player.get("position") or ""),
        )
        counts[key] = counts.get(key, 0) + 1
    return counts


def _is_rookie(player: dict[str, object]) -> bool:
    try:
        return int(str(player.get("rookie_year") or "0")) >= 2025
    except ValueError:
        return False


def _stale_player_reason(
    player: dict[str, object],
    roster_row: dict[str, object],
) -> str:
    active_flag_value = player.get("active_flag")
    active_flag = "" if active_flag_value is None else str(active_flag_value).strip().lower()
    if active_flag in STALE_ACTIVE_FLAGS:
        return "Player is marked inactive/stale in the local player table."
    roster_status = str(roster_row.get("roster_status") or "").strip().lower()
    if roster_status in STALE_ROSTER_STATUSES:
        return "Player has a stale/retired roster status."
    return ""


def _status_priority(status: str) -> int:
    return {"blocked": 0, "review": 1, "ready": 2}.get(status, 9)


def _read_optional_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _name_key(value: str) -> str:
    return "".join(character.lower() for character in value if character.isalnum())


def _loose_name_key(value: str) -> str:
    suffixes = {"jr", "sr", "ii", "iii", "iv", "v"}
    compact = _name_key(value)
    for suffix in suffixes:
        if compact.endswith(suffix):
            return compact[: -len(suffix)]
    return compact


def _float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value)
        if text == "":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def _boolish(value: object) -> bool:
    return str(value).lower() in {"1", "true", "yes"}
