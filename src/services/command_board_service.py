from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.data.csv_schemas import CSV_SCHEMAS, REQUIRED_V1_FILES
from src.data.validators import ImportIssue, ValidatedDataPack, validate_data_pack
from src.models.keeper_scores import KeeperDecision, KeeperPressure, KeeperScoreInputs
from src.services.roster_service import keeper_pressure_by_team
from src.services.team_service import TeamKeeperBoard, build_team_keeper_board


@dataclass(frozen=True)
class TeamCommandRules:
    protect_limit: int
    official_top_five_keep_limit: int


@dataclass(frozen=True)
class ImportReviewBoard:
    data_pack_name: str
    snapshot_date: str | None
    source_rows: list[dict[str, object]]
    issue_rows: list[dict[str, object]]
    issue_counts: dict[str, int]
    row_counts: list[dict[str, object]]
    has_errors: bool


@dataclass(frozen=True)
class TeamCommandBoard:
    keeper_board: TeamKeeperBoard
    rules: TeamCommandRules
    roster_rows: list[dict[str, object]]
    top_five_rows: list[dict[str, object]]
    forced_release_rows: list[dict[str, object]]
    pressure_rows: list[dict[str, object]]


@dataclass(frozen=True)
class WarBoard:
    rows: list[dict[str, object]]
    positions: list[str]
    teams: list[str]
    recommendations: list[str]


def build_import_review_board(data_pack_path: str | Path) -> ImportReviewBoard:
    validated = _validate_for_command_boards(data_pack_path)
    return ImportReviewBoard(
        data_pack_name=validated.data_pack_name,
        snapshot_date=validated.snapshot_date,
        source_rows=_source_rows(validated),
        issue_rows=[_issue_row(issue) for issue in validated.issues],
        issue_counts=_issue_counts(validated.issues),
        row_counts=_row_counts(validated),
        has_errors=validated.has_errors,
    )


def build_team_command_board(
    data_pack_path: str | Path,
    *,
    team_id: str = "niners",
    protect_limit: int | None = None,
    official_top_five_keep_limit: int | None = None,
) -> TeamCommandBoard:
    rules = _team_command_rules(
        protect_limit=protect_limit,
        official_top_five_keep_limit=official_top_five_keep_limit,
    )
    validated = _validate_for_command_boards(data_pack_path)
    joined_rows = _joined_player_rows(validated)
    team_rows = [row for row in joined_rows if row["team_id"] == team_id]
    players = [_keeper_input(row) for row in team_rows]
    team_name = str(team_rows[0]["team_name"]) if team_rows else team_id
    keeper_board = build_team_keeper_board(
        players,
        team_id=team_id,
        team_name=team_name,
        protect_limit=rules.protect_limit,
        official_top_five_keep_limit=rules.official_top_five_keep_limit,
    )
    decision_by_player_id = {
        decision.player_id: decision for decision in keeper_board.decisions
    }
    forced_ids = {player.player_id for player in keeper_board.forced_release_candidates}
    return TeamCommandBoard(
        keeper_board=keeper_board,
        rules=rules,
        roster_rows=[
            _team_roster_row(row, decision_by_player_id.get(str(row["player_id"])), forced_ids)
            for row in team_rows
        ],
        top_five_rows=[
            _top_five_row(player, decision_by_player_id.get(player.player_id), forced_ids)
            for player in keeper_board.official_top_five
        ],
        forced_release_rows=[
            _top_five_row(player, decision_by_player_id.get(player.player_id), forced_ids)
            for player in keeper_board.forced_release_candidates
        ],
        pressure_rows=[
            _pressure_row(pressure)
            for pressure in keeper_pressure_by_team(
                joined_rows,
                protect_limit=rules.protect_limit,
                official_top_five_keep_limit=rules.official_top_five_keep_limit,
            )
        ],
    )


def build_war_board(data_pack_path: str | Path) -> WarBoard:
    validated = _validate_for_command_boards(data_pack_path)
    rows = sorted(
        [_war_row(row) for row in _joined_player_rows(validated)],
        key=lambda row: (-_sortable_score(row["war_score"]), str(row["player"])),
    )
    return WarBoard(
        rows=rows,
        positions=sorted({str(row["pos"]) for row in rows if row["pos"]}),
        teams=sorted({str(row["team"]) for row in rows if row["team"]}),
        recommendations=sorted(
            {str(row["recommendation"]) for row in rows if row["recommendation"]}
        ),
    )


def _source_rows(validated: ValidatedDataPack) -> list[dict[str, object]]:
    return [
        {
            "file": row.get("file_name"),
            "source": row.get("source_name"),
            "type": row.get("source_type"),
            "review": row.get("review_status"),
            "pulled_at": row.get("pulled_at"),
            "notes": row.get("notes"),
        }
        for row in validated.rows_by_table.get("metadata_sources", [])
    ]


def _validate_for_command_boards(data_pack_path: str | Path) -> ValidatedDataPack:
    try:
        return validate_data_pack(data_pack_path)
    except ValueError as exc:
        path = Path(data_pack_path).resolve()
        rows_by_table, issues = _read_data_pack_rows(path)
        issues.insert(
            0,
            ImportIssue(
                severity="error",
                file_name=None,
                issue="Data pack validation failed before command board build.",
                suggested_fix=str(exc),
            ),
        )
        return ValidatedDataPack(
            data_pack_path=path,
            data_pack_name=path.name,
            snapshot_date=_first_snapshot_date(rows_by_table),
            rows_by_table=rows_by_table,
            issues=tuple(issues),
        )


def _read_data_pack_rows(
    data_pack_path: Path,
) -> tuple[dict[str, list[dict[str, object]]], list[ImportIssue]]:
    rows_by_table: dict[str, list[dict[str, object]]] = {}
    issues: list[ImportIssue] = []
    for file_name in REQUIRED_V1_FILES:
        schema = CSV_SCHEMAS[file_name]
        csv_path = data_pack_path / file_name
        if not csv_path.exists():
            issues.append(
                ImportIssue(
                    severity="error",
                    file_name=file_name,
                    issue="Required CSV file is missing.",
                    suggested_fix=f"Add {file_name} to the data pack.",
                )
            )
            rows_by_table[schema.table_name] = []
            continue
        with csv_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            rows_by_table[schema.table_name] = [
                _coerce_command_row(file_name, row) for row in reader
            ]
    return rows_by_table, issues


def _coerce_command_row(file_name: str, raw_row: dict[str, object]) -> dict[str, object]:
    schema = CSV_SCHEMAS[file_name]
    row = {
        column: _clean_command_value(raw_row.get(column))
        for column in schema.all_columns
    }
    for column in schema.integer_columns:
        if row.get(column) is not None:
            row[column] = int(str(row[column]))
    for column in schema.float_columns:
        if row.get(column) is not None:
            row[column] = float(str(row[column]))
    return row


def _clean_command_value(value: object) -> object:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first_snapshot_date(rows_by_table: dict[str, list[dict[str, object]]]) -> str | None:
    for rows in rows_by_table.values():
        for row in rows:
            value = row.get("snapshot_date")
            if value is not None:
                return str(value)
    return None


def _team_command_rules(
    *,
    protect_limit: int | None,
    official_top_five_keep_limit: int | None,
) -> TeamCommandRules:
    configured = _configured_team_rules()
    return TeamCommandRules(
        protect_limit=protect_limit
        if protect_limit is not None
        else configured.protect_limit,
        official_top_five_keep_limit=official_top_five_keep_limit
        if official_top_five_keep_limit is not None
        else configured.official_top_five_keep_limit,
    )


def _configured_team_rules() -> TeamCommandRules:
    rules_path = Path(__file__).resolve().parents[2] / "src" / "config" / "league_rules.yaml"
    values = _read_simple_yaml_ints(
        rules_path,
        ("roster.declaration_protect_limit", "keeper_rules.official_top_five_keep_limit"),
    )
    return TeamCommandRules(
        protect_limit=values.get("roster.declaration_protect_limit", 23),
        official_top_five_keep_limit=values.get(
            "keeper_rules.official_top_five_keep_limit",
            4,
        ),
    )


def _read_simple_yaml_ints(path: Path, keys: tuple[str, ...]) -> dict[str, int]:
    wanted = set(keys)
    values: dict[str, int] = {}
    section: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith(" ") and line.endswith(":"):
            section = line[:-1]
            continue
        if section is None or ":" not in line:
            continue
        key, raw_value = line.strip().split(":", 1)
        dotted_key = f"{section}.{key}"
        if dotted_key not in wanted:
            continue
        value = raw_value.strip().strip('"')
        if value:
            values[dotted_key] = int(value)
    return values


def _issue_row(issue: ImportIssue) -> dict[str, object]:
    return {
        "severity": issue.severity,
        "file": issue.file_name,
        "row": issue.row_number,
        "entity": issue.entity_name,
        "issue": issue.issue,
        "fix": issue.suggested_fix,
    }


def _issue_counts(issues: tuple[ImportIssue, ...]) -> dict[str, int]:
    counts = {"error": 0, "warning": 0}
    for issue in issues:
        counts[issue.severity] = counts.get(issue.severity, 0) + 1
    return counts


def _row_counts(validated: ValidatedDataPack) -> list[dict[str, object]]:
    return [
        {"table": table_name, "rows": len(rows)}
        for table_name, rows in sorted(validated.rows_by_table.items())
    ]


def _joined_player_rows(validated: ValidatedDataPack) -> list[dict[str, object]]:
    rankings = _by_player_id(validated.rows_by_table.get("official_rankings", []))
    outputs = _by_player_id(validated.rows_by_table.get("model_outputs", []))
    rows: list[dict[str, object]] = []
    for roster_row in validated.rows_by_table.get("rosters", []):
        player_id = str(roster_row.get("player_id") or "")
        ranking_row = rankings.get(player_id, {})
        output_row = outputs.get(player_id, {})
        row = dict(roster_row)
        row["official_rank"] = _first_present(
            roster_row.get("official_rank"), ranking_row.get("official_rank")
        )
        for column in (
            "private_score",
            "market_score",
            "war_score",
            "keeper_score",
            "drop_candidate_score",
            "confidence_score",
            "risk_level",
            "recommendation",
            "do_not_draft_before_pick",
            "notes",
        ):
            row[column] = output_row.get(column)
        rows.append(row)
    return rows


def _by_player_id(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(row.get("player_id")): row for row in rows if row.get("player_id")}


def _keeper_input(row: dict[str, object]) -> KeeperScoreInputs:
    return KeeperScoreInputs(
        player_id=str(row.get("player_id") or ""),
        player_name=str(row.get("player_name") or row.get("player_id") or ""),
        position=str(row.get("position") or ""),
        official_rank=_optional_int(row.get("official_rank")),
        private_score=_optional_float(row.get("private_score"), 50.0),
        market_score=_optional_float(row.get("market_score")),
        confidence_score=_optional_float(row.get("confidence_score"), 0.6),
        roster_status=str(row.get("roster_status") or "rostered"),
    )


def _team_roster_row(
    row: dict[str, object],
    decision: KeeperDecision | None,
    forced_ids: set[str],
) -> dict[str, object]:
    player_id = str(row.get("player_id") or "")
    return {
        "player": row.get("player_name"),
        "pos": row.get("position"),
        "official_rank": row.get("official_rank"),
        "market_score": row.get("market_score"),
        "war_score": row.get("war_score"),
        "keeper_score": _decision_value(decision, "keeper_score"),
        "drop_score": _decision_value(decision, "drop_candidate_score"),
        "recommendation": _recommendation(decision, player_id in forced_ids),
        "shield": bool(decision and decision.top_five_shield_eligible),
    }


def _top_five_row(
    player: KeeperScoreInputs,
    decision: KeeperDecision | None,
    forced_ids: set[str],
) -> dict[str, object]:
    return {
        "rank": player.official_rank,
        "player": player.player_name,
        "pos": player.position,
        "keeper_score": _decision_value(decision, "keeper_score"),
        "drop_score": _decision_value(decision, "drop_candidate_score"),
        "action": _recommendation(decision, player.player_id in forced_ids),
    }


def _pressure_row(pressure: KeeperPressure) -> dict[str, object]:
    return {
        "team": pressure.team_name,
        "roster": pressure.roster_count,
        "top_5": pressure.official_top_five_count,
        "forced_release": pressure.forced_release_count,
        "pressure": pressure.pressure_count,
        "level": pressure.pressure_level,
    }


def _war_row(row: dict[str, object]) -> dict[str, object]:
    return {
        "player": row.get("player_name"),
        "pos": row.get("position"),
        "team": row.get("team_name"),
        "official_rank": row.get("official_rank"),
        "market_score": row.get("market_score"),
        "war_score": row.get("war_score"),
        "private_score": row.get("private_score"),
        "keeper_score": row.get("keeper_score"),
        "drop_score": row.get("drop_candidate_score"),
        "confidence": row.get("confidence_score"),
        "risk": row.get("risk_level"),
        "recommendation": row.get("recommendation") or _war_recommendation(row),
        "do_not_draft_before": row.get("do_not_draft_before_pick"),
        "notes": row.get("notes"),
    }


def _war_recommendation(row: dict[str, object]) -> str:
    drop_score = _optional_float(row.get("drop_candidate_score"), 0.0) or 0.0
    keeper_score = _optional_float(row.get("keeper_score"), 0.0) or 0.0
    if drop_score >= 35:
        return "drop"
    if drop_score >= 20:
        return "shop"
    if keeper_score >= 80:
        return "keep"
    return "bubble"


def _recommendation(decision: KeeperDecision | None, is_forced_release: bool) -> str:
    if is_forced_release:
        return "shop/release"
    if decision is None:
        return "review"
    if decision.drop_candidate_score >= 35:
        return "drop"
    if decision.drop_candidate_score >= 20:
        return "shop"
    return "keep"


def _decision_value(decision: KeeperDecision | None, attribute: str) -> float | None:
    if decision is None:
        return None
    return getattr(decision, attribute)


def _first_present(*values: object) -> object:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _optional_float(value: object, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    return float(value)


def _sortable_score(value: object) -> float:
    return _optional_float(value, 0.0) or 0.0
