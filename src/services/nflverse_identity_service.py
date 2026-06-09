from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack
from src.services.real_input_template_service import (
    NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS,
)

SUPPORTED_POSITIONS = {"QB", "RB", "WR", "TE"}
MATCH_METHOD_ORDER = (
    "player_id",
    "sleeper_id",
    "gsis_id",
    "fantasy_data_id",
    "espn_id",
    "pfr_id",
    "name_position_team",
)
ALLOWED_MATCH_METHODS = {
    *MATCH_METHOD_ORDER,
    "manual",
    "unmatched",
}
ALLOWED_REVIEW_STATUSES = {"ready", "review", "blocked", "ignored"}


@dataclass(frozen=True)
class NflverseIdentityIssue:
    severity: str
    row_number: int | None
    player_name: str
    issue: str
    suggested_fix: str


@dataclass(frozen=True)
class NflverseIdentityValidationReport:
    path: Path
    status: str
    row_count: int
    issues: tuple[NflverseIdentityIssue, ...]


@dataclass(frozen=True)
class NflverseIdentityReviewRow:
    player_id: str
    player_name: str
    position: str
    team: str
    match_status: str
    match_method: str
    sleeper_id: str
    gsis_id: str
    pfr_id: str
    match_confidence: str
    review_status: str
    candidate_player_ids: str
    issue: str
    suggested_fix: str


def validate_nflverse_identity_map(
    identity_map_path: str | Path,
) -> NflverseIdentityValidationReport:
    path = Path(identity_map_path)
    if not path.exists():
        return NflverseIdentityValidationReport(
            path=path,
            status="blocked",
            row_count=0,
            issues=(
                NflverseIdentityIssue(
                    "error",
                    None,
                    "",
                    "Identity map CSV is missing.",
                    "Create nflverse_identity_map.csv from the template.",
                ),
            ),
        )

    header, rows = _read_csv(path)
    expected_header = NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_identity_map.csv"]
    issues: list[NflverseIdentityIssue] = []
    if header != expected_header:
        issues.append(
            NflverseIdentityIssue(
                "error",
                None,
                "",
                "Identity map header does not match the Phase 2 contract.",
                "Regenerate the file from templates/real_data_inputs/nflverse_stats_upgrade.",
            )
        )

    for row_number, row in enumerate(rows, start=2):
        issues.extend(_validate_identity_row(row, row_number))

    issues.extend(_duplicate_identifier_issues(rows))
    status = _status_from_issues(issues)
    return NflverseIdentityValidationReport(
        path=path,
        status=status,
        row_count=len(rows),
        issues=tuple(issues),
    )


def build_nflverse_identity_review_rows(
    data_pack_path: str | Path,
    identity_map_path: str | Path,
) -> list[dict[str, object]]:
    validated_pack = validate_data_pack(data_pack_path)
    players = [
        row
        for row in validated_pack.rows_by_table.get("players", [])
        if str(row.get("position") or "") in SUPPORTED_POSITIONS
    ]
    _, identity_rows = _read_csv(Path(identity_map_path))
    return [
        _identity_review_row(player, identity_rows).__dict__
        for player in players
    ]


def nflverse_identity_review_summary_rows(
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    statuses = ("matched", "review", "blocked", "unmatched")
    output: list[dict[str, object]] = []
    for status in statuses:
        status_rows = [row for row in rows if row.get("match_status") == status]
        output.append(
            {
                "match_status": status,
                "rows": len(status_rows),
                "blocking": status in {"blocked", "unmatched"} and bool(status_rows),
                "next_action": _summary_next_action(status, len(status_rows)),
            }
        )
    return output


def identity_map_ready_player_ids(
    data_pack_path: str | Path,
    identity_map_path: str | Path,
) -> set[str]:
    rows = build_nflverse_identity_review_rows(data_pack_path, identity_map_path)
    return {
        str(row["player_id"])
        for row in rows
        if row["match_status"] == "matched"
        and row["review_status"] == "ready"
    }


def _validate_identity_row(
    row: dict[str, str],
    row_number: int,
) -> list[NflverseIdentityIssue]:
    issues: list[NflverseIdentityIssue] = []
    player_name = row.get("player_name", "")
    position = row.get("position", "")
    if not row.get("player_id"):
        issues.append(
            NflverseIdentityIssue(
                "error",
                row_number,
                player_name,
                "Identity row is missing player_id.",
                "Use the local dim_players player_id for the matched player.",
            )
        )
    if not player_name:
        issues.append(
            NflverseIdentityIssue(
                "error",
                row_number,
                player_name,
                "Identity row is missing player_name.",
                "Populate player_name for reviewability.",
            )
        )
    if position not in SUPPORTED_POSITIONS:
        issues.append(
            NflverseIdentityIssue(
                "warning",
                row_number,
                player_name,
                "Identity row has unsupported or blank position.",
                "Use QB, RB, WR, or TE for model-scored players.",
            )
        )
    if not _has_external_identifier(row):
        issues.append(
            NflverseIdentityIssue(
                "warning",
                row_number,
                player_name,
                "Identity row has no external ID.",
                "Add sleeper_id, gsis_id, fantasy_data_id, espn_id, or pfr_id.",
            )
        )
    if row.get("match_method") and row["match_method"] not in ALLOWED_MATCH_METHODS:
        issues.append(
            NflverseIdentityIssue(
                "error",
                row_number,
                player_name,
                "Identity row has invalid match_method.",
                "Use a supported deterministic match method.",
            )
        )
    if row.get("review_status") not in ALLOWED_REVIEW_STATUSES:
        issues.append(
            NflverseIdentityIssue(
                "error",
                row_number,
                player_name,
                "Identity row has invalid review_status.",
                "Use ready, review, blocked, or ignored.",
            )
        )
    confidence = row.get("match_confidence", "")
    if confidence and not _in_range(confidence, 0, 100):
        issues.append(
            NflverseIdentityIssue(
                "error",
                row_number,
                player_name,
                "match_confidence must be 0-100.",
                "Replace match_confidence with a normalized confidence score.",
            )
        )
    return issues


def _duplicate_identifier_issues(
    rows: list[dict[str, str]],
) -> list[NflverseIdentityIssue]:
    issues: list[NflverseIdentityIssue] = []
    for column in ("player_id", "sleeper_id", "gsis_id", "fantasy_data_id", "espn_id", "pfr_id"):
        seen: dict[str, list[dict[str, str]]] = {}
        for row in rows:
            value = row.get(column, "")
            if value:
                seen.setdefault(value, []).append(row)
        for value, duplicates in seen.items():
            if len(duplicates) > 1:
                issues.append(
                    NflverseIdentityIssue(
                        "error",
                        None,
                        value,
                        f"Duplicate {column} in identity map.",
                        "Keep one row per external identifier or send the duplicate to review.",
                    )
                )
    return issues


def _identity_review_row(
    player: dict[str, object],
    identity_rows: list[dict[str, str]],
) -> NflverseIdentityReviewRow:
    candidates_by_method: dict[str, list[dict[str, str]]] = {}
    for method in MATCH_METHOD_ORDER:
        candidates = _candidate_rows_for_method(player, identity_rows, method)
        if candidates:
            candidates_by_method[method] = candidates
            break

    if not candidates_by_method:
        return _unmatched_review_row(player)

    method, candidates = next(iter(candidates_by_method.items()))
    if len(candidates) > 1:
        return _ambiguous_review_row(player, method, candidates)

    candidate = candidates[0]
    review_status = candidate.get("review_status") or "review"
    if review_status == "blocked":
        match_status = "blocked"
        issue = "Identity match exists but is blocked for review."
        suggested_fix = "Resolve the blocked identity-map row before importing nflverse data."
    elif review_status == "ready":
        match_status = "matched"
        issue = ""
        suggested_fix = "No identity action needed."
    else:
        match_status = "review"
        issue = "Identity match exists but is not marked ready."
        suggested_fix = "Review the match and set review_status=ready when confirmed."

    return NflverseIdentityReviewRow(
        player_id=str(player.get("player_id") or ""),
        player_name=str(player.get("player_name") or ""),
        position=str(player.get("position") or ""),
        team=str(player.get("nfl_team") or ""),
        match_status=match_status,
        match_method=method,
        sleeper_id=candidate.get("sleeper_id", ""),
        gsis_id=candidate.get("gsis_id", ""),
        pfr_id=candidate.get("pfr_id", ""),
        match_confidence=candidate.get("match_confidence", ""),
        review_status=review_status,
        candidate_player_ids=candidate.get("player_id", ""),
        issue=issue,
        suggested_fix=suggested_fix,
    )


def _candidate_rows_for_method(
    player: dict[str, object],
    identity_rows: list[dict[str, str]],
    method: str,
) -> list[dict[str, str]]:
    if method == "player_id":
        value = str(player.get("player_id") or "")
        return [row for row in identity_rows if row.get("player_id") == value]
    if method in {"sleeper_id", "pfr_id"}:
        value = str(player.get(method) or "")
        if not value:
            return []
        return [row for row in identity_rows if row.get(method) == value]
    if method in {"gsis_id", "fantasy_data_id", "espn_id"}:
        return []
    if method == "name_position_team":
        player_name = _name_key(str(player.get("merge_name") or player.get("player_name") or ""))
        position = str(player.get("position") or "")
        team = str(player.get("nfl_team") or "")
        return [
            row
            for row in identity_rows
            if _name_key(row.get("normalized_name") or row.get("player_name", "")) == player_name
            and row.get("position") == position
            and (not row.get("team") or row.get("team") == team)
        ]
    return []


def _unmatched_review_row(player: dict[str, object]) -> NflverseIdentityReviewRow:
    return NflverseIdentityReviewRow(
        player_id=str(player.get("player_id") or ""),
        player_name=str(player.get("player_name") or ""),
        position=str(player.get("position") or ""),
        team=str(player.get("nfl_team") or ""),
        match_status="unmatched",
        match_method="",
        sleeper_id="",
        gsis_id="",
        pfr_id="",
        match_confidence="",
        review_status="blocked",
        candidate_player_ids="",
        issue="No identity-map row matches this rostered player.",
        suggested_fix="Add a reviewed nflverse_identity_map.csv row with a stable ID.",
    )


def _ambiguous_review_row(
    player: dict[str, object],
    method: str,
    candidates: list[dict[str, str]],
) -> NflverseIdentityReviewRow:
    return NflverseIdentityReviewRow(
        player_id=str(player.get("player_id") or ""),
        player_name=str(player.get("player_name") or ""),
        position=str(player.get("position") or ""),
        team=str(player.get("nfl_team") or ""),
        match_status="blocked",
        match_method=method,
        sleeper_id="",
        gsis_id="",
        pfr_id="",
        match_confidence="",
        review_status="blocked",
        candidate_player_ids="|".join(sorted(row.get("player_id", "") for row in candidates)),
        issue="Multiple identity-map rows match this rostered player.",
        suggested_fix="Add a unique Sleeper or GSIS ID and keep only one ready row.",
    )


def _has_external_identifier(row: dict[str, str]) -> bool:
    return any(
        row.get(column)
        for column in ("sleeper_id", "gsis_id", "nfl_id", "espn_id", "fantasy_data_id", "pfr_id")
    )


def _summary_next_action(status: str, count: int) -> str:
    if count == 0:
        return "No rows in this status."
    if status == "matched":
        return "These players are ready for local nflverse imports."
    if status == "review":
        return "Confirm the identity-map rows before feature derivation."
    return "Fix identity rows before importing or scoring nflverse-derived features."


def _status_from_issues(issues: list[NflverseIdentityIssue]) -> str:
    if any(issue.severity == "error" for issue in issues):
        return "blocked"
    if issues:
        return "review"
    return "ready"


def _read_csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return tuple(reader.fieldnames or ()), list(reader)


def _name_key(value: str) -> str:
    return "".join(character.lower() for character in value if character.isalnum())


def _in_range(value: str, minimum: float, maximum: float) -> bool:
    try:
        number = float(value)
    except ValueError:
        return False
    return minimum <= number <= maximum
