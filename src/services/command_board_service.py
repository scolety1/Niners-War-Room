from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.data.csv_schemas import CSV_SCHEMAS, REQUIRED_V1_FILES
from src.data.validators import ImportIssue, ValidatedDataPack, validate_data_pack
from src.models.keeper_scores import KeeperDecision, KeeperPressure, KeeperScoreInputs
from src.services.forced_release_strategy_service import team_release_pressure_profile
from src.services.market_influence_policy_service import (
    first_market_value,
    market_edge_classification,
    market_status_warning,
    market_value_status,
    safe_market_edge_score,
)
from src.services.player_lifecycle_service import (
    lifecycle_from_lookup,
    load_active_lifecycle_lookup,
)
from src.services.roster_service import keeper_pressure_by_team
from src.services.table_sort_service import SortSpec
from src.services.team_service import TeamKeeperBoard, build_team_keeper_board
from src.services.warning_language_service import (
    NO_ACTIVE_WARNING,
    confidence_explanation,
    confidence_label,
    warning_summary,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ACTIVE_STATS_FIRST_MODEL_DIR = (
    PROJECT_ROOT / "local_exports" / "active_veteran_model_public_sources"
)
STATS_FIRST_NORMALIZED_FEATURE_FILE = "stats_first_normalized_features.csv"
STATS_FIRST_PREVIEW_OUTPUT_FILE = "stats_first_veteran_model_preview_outputs.csv"

WAR_BOARD_DISPLAY_COLUMNS: tuple[str, ...] = (
    "overall_rank",
    "position_rank_label",
    "player",
    "pos",
    "asset_lifecycle_label",
    "team",
    "action",
    "stats_value",
    "market_value",
    "market_edge",
    "confidence",
    "confidence_label",
    "warning_reason",
)
WAR_BOARD_COLUMN_LABELS: dict[str, str] = {
    "overall_rank": "Overall Rank",
    "position_rank_label": "Position Rank",
    "player": "Player",
    "pos": "Pos",
    "asset_lifecycle_label": "Lifecycle",
    "team": "Fantasy Team",
    "action": "Action",
    "stats_value": "Model Value",
    "market_value": "Trade Market",
    "market_edge": "Model vs Market",
    "confidence": "Confidence",
    "confidence_label": "Confidence Label",
    "warning_reason": "Warning Reason",
}

WAR_BOARD_SORT = SortSpec(
    table_key="war_board",
    label="Best overall rank",
    sort_columns=("overall_rank", "player"),
    directions=("asc", "asc"),
    meaning="Best overall model rank appears first; player name is the stable tiebreaker.",
)
WAR_BOARD_ACTION_QUEUE_SORT = SortSpec(
    table_key="war_board_action_queue",
    label="Action priority, then overall rank",
    sort_columns=("action", "overall_rank", "player"),
    directions=("custom", "asc", "asc"),
    meaning=(
        "Actionable review rows appear first; within each action, better overall "
        "model rank appears first."
    ),
)
TEAM_ROSTER_SORT = SortSpec(
    table_key="team_roster",
    label="Team section, then action urgency",
    sort_columns=(
        "team_section",
        "recommendation",
        "cut_risk",
        "keep_priority",
        "league_rank",
        "player",
    ),
    directions=("custom", "custom", "desc", "desc", "asc", "asc"),
    meaning=(
        "Rows are grouped into the My Team decision sections; within each section, "
        "higher cut risk appears first."
    ),
)
TEAM_TOP_FIVE_SORT = SortSpec(
    table_key="team_top_five",
    label="League rank ascending",
    sort_columns=("league_rank", "player"),
    directions=("asc", "asc"),
    meaning=(
        "This roster's five highest league-ranked players are shown in "
        "league-rank order."
    ),
)
TEAM_FORCED_RELEASE_SORT = SortSpec(
    table_key="team_forced_release",
    label="Lowest keep priority inside roster's league-rank top five",
    sort_columns=("keep_priority", "cut_risk", "league_rank", "player"),
    directions=("asc", "desc", "asc", "asc"),
    meaning=(
        "The current rule cut is the lowest model/player value inside this "
        "roster's league-rank top five; cut risk is only a tiebreaker."
    ),
)
TEAM_PRESSURE_SORT = SortSpec(
    table_key="team_pressure",
    label="Pressure descending, then team",
    sort_columns=("pressure", "team"),
    directions=("desc", "asc"),
    meaning="Teams with more roster top-five rule pressure appear first.",
)

TEAM_SECTION_ORDER: tuple[str, ...] = (
    "Core Holds",
    "Forced-Release Decision",
    "Needs Data Review",
    "Bubble Players",
    "Shop Candidates",
    "Bench/Stash",
)
TEAM_DECISION_COLUMNS: tuple[str, ...] = (
    "player",
    "pos",
    "nfl_team",
    "asset_lifecycle_label",
    "league_rank",
    "top_five_rule",
    "model_recommendation",
    "keep_priority",
    "cut_risk",
    "stats_value",
    "market_edge",
    "release_pain",
    "decision_explanation",
    "confidence",
    "confidence_label",
    "receipt_link",
    "compare_link",
)
TEAM_COLUMN_LABELS: dict[str, str] = {
    "player": "Player",
    "pos": "Pos",
    "nfl_team": "NFL Team",
    "asset_lifecycle_label": "Lifecycle",
    "league_rank": "League Rank",
    "top_five_rule": "Top-Five Rule Status",
    "model_recommendation": "Model Recommendation",
    "keep_priority": "Keep Priority",
    "cut_risk": "Cut Risk",
    "stats_value": "Model Value",
    "market_edge": "Model vs Market",
    "release_pain": "Release Pain",
    "decision_explanation": "Explanation",
    "confidence": "Confidence",
    "confidence_label": "Confidence Label",
    "receipt_link": "Receipts",
    "compare_link": "Compare",
}


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
    rows_by_section: dict[str, list[dict[str, object]]]
    top_five_rows: list[dict[str, object]]
    forced_release_rows: list[dict[str, object]]
    pressure_rows: list[dict[str, object]]
    section_order: tuple[str, ...]
    sort_metadata: dict[str, SortSpec]


@dataclass(frozen=True)
class WarBoard:
    rows: list[dict[str, object]]
    data_source_audit_rows: list[dict[str, object]]
    positions: list[str]
    teams: list[str]
    actions: list[str]
    recommendations: list[str]
    edge_types: list[str]
    confidence_buckets: list[str]
    sort_metadata: dict[str, SortSpec]


@dataclass(frozen=True)
class ActiveStatsFirstSync:
    rows_by_sleeper_id: dict[str, dict[str, object]]
    preview_timestamp: str
    preview_row_count: int
    matched_row_count: int
    unmapped_row_count: int
    identity_match_method: str
    warning: str


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
    resolved_team_id = _resolve_team_id(joined_rows, team_id)
    team_rows = [row for row in joined_rows if row["team_id"] == resolved_team_id]
    players = [_keeper_input(row) for row in team_rows]
    team_name = str(team_rows[0]["team_name"]) if team_rows else resolved_team_id
    keeper_board = build_team_keeper_board(
        players,
        team_id=resolved_team_id,
        team_name=team_name,
        protect_limit=rules.protect_limit,
        official_top_five_keep_limit=rules.official_top_five_keep_limit,
    )
    decision_by_player_id = {
        decision.player_id: decision for decision in keeper_board.decisions
    }
    pressure_profile = team_release_pressure_profile(
        team_rows,
        official_top_five_keep_limit=rules.official_top_five_keep_limit,
    )
    has_scored_outputs = _has_scored_model_outputs(team_rows)
    if has_scored_outputs:
        top_five_joined_rows = _visible_top_five_rows(team_rows)
        forced_joined_rows = pressure_profile.default_release_rows
        top_five_ids = {str(row.get("player_id") or "") for row in top_five_joined_rows}
        forced_ids = {str(row.get("player_id") or "") for row in forced_joined_rows}
        top_five_rows = [
            _top_five_model_row(row, forced_ids, pressure_profile=pressure_profile)
            for row in top_five_joined_rows
        ]
        forced_release_rows = [
            _top_five_model_row(row, forced_ids, pressure_profile=pressure_profile)
            for row in forced_joined_rows
        ]
    else:
        top_five_ids = {player.player_id for player in keeper_board.official_top_five}
        forced_ids = {player.player_id for player in keeper_board.forced_release_candidates}
        top_five_rows = [
            _top_five_row(player, decision_by_player_id.get(player.player_id), forced_ids)
            for player in keeper_board.official_top_five
        ]
        forced_release_rows = [
            _top_five_row(player, decision_by_player_id.get(player.player_id), forced_ids)
            for player in keeper_board.forced_release_candidates
        ]
    roster_rows = sorted(
        [
            _team_roster_row(
                row,
                decision_by_player_id.get(str(row["player_id"])),
                top_five_ids,
                forced_ids,
                use_model_outputs=has_scored_outputs,
                release_pain=pressure_profile.forced_release_pain,
                release_explanation=_top_five_release_explanation(
                    row,
                    pressure_profile,
                ),
            )
            for row in team_rows
        ],
        key=_team_roster_sort_key,
    )
    rows_by_section = {
        section: [row for row in roster_rows if row.get("team_section") == section]
        for section in TEAM_SECTION_ORDER
    }
    pressure_rows = [
        _pressure_row(pressure)
        for pressure in keeper_pressure_by_team(
            joined_rows,
            protect_limit=rules.protect_limit,
            official_top_five_keep_limit=rules.official_top_five_keep_limit,
        )
    ]
    return TeamCommandBoard(
        keeper_board=keeper_board,
        rules=rules,
        roster_rows=roster_rows,
        rows_by_section=rows_by_section,
        top_five_rows=top_five_rows,
        forced_release_rows=forced_release_rows,
        section_order=TEAM_SECTION_ORDER,
        pressure_rows=sorted(
            pressure_rows,
            key=lambda row: (-int(row["pressure"]), str(row["team"])),
        ),
        sort_metadata={
            "roster_rows": TEAM_ROSTER_SORT,
            "top_five_rows": TEAM_TOP_FIVE_SORT,
            "forced_release_rows": TEAM_FORCED_RELEASE_SORT,
            "pressure_rows": TEAM_PRESSURE_SORT,
        },
    )


def build_war_board(data_pack_path: str | Path) -> WarBoard:
    validated = _validate_for_command_boards(data_pack_path)
    active_sync = _active_stats_first_sync()
    joined_rows = _joined_player_rows(validated, active_sync=active_sync)
    visible_joined_rows = _normal_ranking_rows(joined_rows)
    rows = _ranked_war_rows([_war_row(row) for row in visible_joined_rows])
    return WarBoard(
        rows=rows,
        data_source_audit_rows=[
            _data_source_audit_row(validated, active_sync, joined_rows)
        ],
        positions=sorted({str(row["pos"]) for row in rows if row["pos"]}),
        teams=sorted({str(row["team"]) for row in rows if row["team"]}),
        actions=sorted(
            {str(row["action"]) for row in rows if row["action"]},
            key=_action_sort_order,
        ),
        recommendations=sorted(
            {str(row["recommendation"]) for row in rows if row["recommendation"]}
        ),
        edge_types=sorted({str(row["edge_type"]) for row in rows if row["edge_type"]}),
        confidence_buckets=sorted(
            {str(row["confidence_bucket"]) for row in rows if row["confidence_bucket"]},
            key=_confidence_bucket_sort_order,
        ),
        sort_metadata={
            "rows": WAR_BOARD_SORT,
            "action_queue_rows": WAR_BOARD_ACTION_QUEUE_SORT,
        },
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


def _joined_player_rows(
    validated: ValidatedDataPack,
    *,
    active_sync: ActiveStatsFirstSync | None = None,
) -> list[dict[str, object]]:
    rankings = _by_player_id(validated.rows_by_table.get("official_rankings", []))
    outputs = _by_player_id(validated.rows_by_table.get("model_outputs", []))
    resolved_active_sync = active_sync or _active_stats_first_sync()
    active_outputs = resolved_active_sync.rows_by_sleeper_id
    active_preview_is_newer = _is_newer_timestamp(
        resolved_active_sync.preview_timestamp,
        _latest_model_output_timestamp(validated),
    )
    lifecycle_lookup = load_active_lifecycle_lookup()
    player_lookup = _by_player_id(validated.rows_by_table.get("players", []))
    roster_player_id_counts = _player_id_counts(validated.rows_by_table.get("rosters", []))
    rows: list[dict[str, object]] = []
    for roster_row in validated.rows_by_table.get("rosters", []):
        if str(roster_row.get("position") or "").upper() == "K":
            continue
        player_id = str(roster_row.get("player_id") or "")
        ranking_row = rankings.get(player_id, {})
        active_output_row = active_outputs.get(player_id)
        output_row = active_output_row or outputs.get(player_id, {})
        player_row = player_lookup.get(player_id, {})
        row = dict(roster_row)
        for column in ("active_flag", "sleeper_id", "pfr_id"):
            row[column] = player_row.get(column)
        row["identity_cleanup_status"], row["identity_cleanup_reason"] = (
            _identity_cleanup_status(row, roster_player_id_counts.get(player_id, 0))
        )
        row["league_rank"] = _first_present(
            roster_row.get("league_rank"),
            ranking_row.get("league_rank"),
            roster_row.get("official_rank"), ranking_row.get("official_rank")
        )
        row["official_rank"] = row["league_rank"]
        for column in (
            "overall_rank",
            "position_rank",
            "position_rank_label",
            "private_score",
            "market_score",
            "market_value_status",
            "market_trade_value",
            "market_edge_score",
            "market_edge_label",
            "market_edge_warning",
            "war_score",
            "keeper_score",
            "drop_candidate_score",
            "confidence_score",
            "risk_level",
            "warning_status",
            "warning_reasons",
            "recommendation",
            "do_not_draft_before_pick",
            "experience_bucket",
            "young_nfl_bridge_prior_score",
            "young_nfl_bridge_weight",
            "young_nfl_bridge_source",
            "asset_lifecycle",
            "notes",
            "model_version",
            "computed_at",
            "score_source",
            "identity_match_method",
            "score_source_warning",
        ):
            row[column] = output_row.get(column)
        if not active_output_row:
            row["score_source"] = row.get("score_source") or "data_pack_model_outputs"
            row["identity_match_method"] = row.get("identity_match_method") or "player_id"
            if active_preview_is_newer and output_row:
                row["score_source_warning"] = (
                    "Active stats-first preview is newer, but this player did not "
                    "map through the Sleeper/nflverse identity bridge; showing data-pack "
                    "model output for review."
                )
        rows.append(lifecycle_from_lookup(row, lifecycle_lookup))
    return rows


def _normal_ranking_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        row
        for row in rows
        if row.get("identity_cleanup_status")
        not in {"stale_player", "duplicate_player_id"}
    ]


def _identity_cleanup_status(row: dict[str, object], player_id_count: int) -> tuple[str, str]:
    if player_id_count > 1:
        return (
            "duplicate_player_id",
            "Duplicate player ID on active roster rows; excluded from normal rankings.",
        )
    active_flag_value = row.get("active_flag")
    active_flag = "" if active_flag_value is None else str(active_flag_value).strip().lower()
    if active_flag in {
        "0",
        "false",
        "inactive",
        "retired",
        "stale",
    }:
        return (
            "stale_player",
            "Player is marked inactive/stale in the local player table.",
        )
    if str(row.get("roster_status") or "").strip().lower() in {
        "inactive",
        "retired",
        "stale",
        "deleted",
    }:
        return ("stale_player", "Player has a stale/retired roster status.")
    return ("ready", "")


def _player_id_counts(rows: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        player_id = str(row.get("player_id") or "")
        if player_id:
            counts[player_id] = counts.get(player_id, 0) + 1
    return counts


def _active_stats_first_sync(
    model_dir: str | Path | None = None,
) -> ActiveStatsFirstSync:
    root = Path(model_dir or ACTIVE_STATS_FIRST_MODEL_DIR)
    output_path = root / STATS_FIRST_PREVIEW_OUTPUT_FILE
    normalized_path = root / STATS_FIRST_NORMALIZED_FEATURE_FILE
    if not output_path.exists() or not normalized_path.exists():
        return ActiveStatsFirstSync(
            rows_by_sleeper_id={},
            preview_timestamp="",
            preview_row_count=0,
            matched_row_count=0,
            unmapped_row_count=0,
            identity_match_method="not_available",
            warning="Active stats-first preview or normalized identity file is missing.",
        )
    sleeper_by_gsis, sleeper_ids = _active_sleeper_identity_lookup(normalized_path)
    if not sleeper_by_gsis and not sleeper_ids:
        return ActiveStatsFirstSync(
            rows_by_sleeper_id={},
            preview_timestamp="",
            preview_row_count=0,
            matched_row_count=0,
            unmapped_row_count=0,
            identity_match_method="not_available",
            warning=(
                "Active stats-first preview exists, but no Sleeper IDs were found "
                "in normalized features."
            ),
        )
    rows: dict[str, dict[str, object]] = {}
    preview_timestamp = ""
    preview_row_count = 0
    unmapped_row_count = 0
    used_direct_match = False
    used_gsis_match = False
    with output_path.open(newline="", encoding="utf-8") as handle:
        for preview_row in csv.DictReader(handle):
            preview_row_count += 1
            preview_player_id = str(preview_row.get("player_id") or "")
            preview_timestamp = max(
                preview_timestamp,
                str(preview_row.get("computed_at") or ""),
            )
            if preview_player_id in sleeper_ids:
                sleeper_id = preview_player_id
                match_method = "sleeper_id"
                used_direct_match = True
            else:
                sleeper_id = sleeper_by_gsis.get(preview_player_id, "")
                match_method = "gsis_to_sleeper_from_normalized_features"
                used_gsis_match = bool(sleeper_id) or used_gsis_match
            if not sleeper_id:
                unmapped_row_count += 1
                continue
            rows[sleeper_id] = _live_model_row_from_active_preview(
                preview_row,
                identity_match_method=match_method,
            )
    identity_method = _identity_method_label(used_direct_match, used_gsis_match)
    warning = (
        ""
        if rows
        else "Active stats-first preview could not map to Sleeper roster IDs."
    )
    if unmapped_row_count:
        warning = (
            f"{unmapped_row_count} active stats-first preview rows could not map "
            "to Sleeper roster IDs."
        )
    return ActiveStatsFirstSync(
        rows_by_sleeper_id=rows,
        preview_timestamp=preview_timestamp,
        preview_row_count=preview_row_count,
        matched_row_count=len(rows),
        unmapped_row_count=unmapped_row_count,
        identity_match_method=identity_method,
        warning=warning,
    )


def _active_sleeper_identity_lookup(
    normalized_path: Path,
) -> tuple[dict[str, str], set[str]]:
    sleeper_by_gsis: dict[str, str] = {}
    sleeper_ids: set[str] = set()
    with normalized_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            sleeper_id = str(row.get("sleeper_id") or "").strip()
            gsis_id = str(row.get("gsis_id") or row.get("player_id") or "").strip()
            if not sleeper_id:
                continue
            sleeper_ids.add(sleeper_id)
            if gsis_id:
                sleeper_by_gsis[gsis_id] = sleeper_id
    return sleeper_by_gsis, sleeper_ids


def _live_model_row_from_active_preview(
    preview_row: dict[str, object],
    *,
    identity_match_method: str,
) -> dict[str, object]:
    keeper = _optional_float(preview_row.get("keeper_score"), 0.0) or 0.0
    trade = _optional_float(preview_row.get("trade_value"), keeper) or keeper
    private = _optional_float(preview_row.get("private_lve_value"), keeper) or keeper
    market = _optional_float(preview_row.get("market_trade_value"), trade) or trade
    market_status = market_value_status(preview_row)
    warning_status = str(preview_row.get("warning_status") or "")
    risk_flags = str(preview_row.get("risk_flags") or "")
    return {
        "overall_rank": preview_row.get("overall_rank"),
        "position_rank": preview_row.get("position_rank"),
        "position_rank_label": preview_row.get("position_rank_label"),
        "private_score": private,
        "market_score": market,
        "market_value_status": market_status,
        "market_trade_value": market,
        "market_edge_score": preview_row.get("market_edge_score"),
        "market_edge_label": preview_row.get("market_edge_label"),
        "market_edge_warning": preview_row.get("market_edge_warning"),
        "war_score": keeper,
        "keeper_score": keeper,
        "drop_candidate_score": preview_row.get("drop_candidate_score"),
        "confidence_score": preview_row.get("confidence_score"),
        "risk_level": _preview_risk_level(warning_status, risk_flags),
        "warning_status": warning_status,
        "warning_reasons": preview_row.get("warning_reasons"),
        "recommendation": _preview_recommendation(
            _optional_float(preview_row.get("drop_candidate_score"), 0.0) or 0.0,
            keeper,
            warning_status=warning_status,
            confidence=_optional_float(preview_row.get("confidence_score")),
        ),
        "do_not_draft_before_pick": preview_row.get("do_not_draft_before_pick"),
        "experience_bucket": preview_row.get("experience_bucket"),
        "young_nfl_bridge_prior_score": preview_row.get(
            "young_nfl_bridge_prior_score"
        ),
        "young_nfl_bridge_weight": preview_row.get("young_nfl_bridge_weight"),
        "young_nfl_bridge_source": preview_row.get("young_nfl_bridge_source"),
        "asset_lifecycle": preview_row.get("asset_lifecycle"),
        "notes": (
            "Displayed from active stats-first preview output matched through "
            "Sleeper/nflverse identity. Data-pack model_outputs.csv was not "
            "mutated."
        ),
        "model_version": preview_row.get("model_version"),
        "computed_at": preview_row.get("computed_at"),
        "score_source": "active_stats_first_preview",
        "identity_match_method": identity_match_method,
        "score_source_warning": "",
    }


def _identity_method_label(used_direct_match: bool, used_gsis_match: bool) -> str:
    if used_direct_match and used_gsis_match:
        return "sleeper_id_or_gsis_to_sleeper"
    if used_direct_match:
        return "sleeper_id"
    if used_gsis_match:
        return "gsis_to_sleeper_from_normalized_features"
    return "not_available"


def _data_source_audit_row(
    validated: ValidatedDataPack,
    active_sync: ActiveStatsFirstSync,
    joined_rows: list[dict[str, object]],
) -> dict[str, object]:
    pack_timestamp = _latest_model_output_timestamp(validated)
    active_newer = _is_newer_timestamp(active_sync.preview_timestamp, pack_timestamp)
    active_visible_count = sum(
        1 for row in joined_rows if row.get("score_source") == "active_stats_first_preview"
    )
    data_pack_visible_count = sum(
        1 for row in joined_rows if row.get("score_source") == "data_pack_model_outputs"
    )
    stale_fallback_count = sum(1 for row in joined_rows if row.get("score_source_warning"))
    market_status_counts: dict[str, int] = {}
    for row in joined_rows:
        status_key = market_value_status(row)
        market_status_counts[status_key] = market_status_counts.get(status_key, 0) + 1
    if active_newer and stale_fallback_count:
        warning = (
            f"{stale_fallback_count} visible rows are falling back to older data-pack "
            "outputs because active preview rows did not map to Sleeper IDs."
        )
    elif active_sync.unmapped_row_count and not stale_fallback_count:
        warning = (
            f"{active_sync.unmapped_row_count} active stats-first preview rows could "
            "not map to current Sleeper roster IDs. They are not visible stale rows "
            "on this board; visible roster rows are synced."
        )
    elif active_sync.warning:
        warning = active_sync.warning
    else:
        warning = "Active stats-first preview is synced to visible board rows."
    visible_source = (
        "active_stats_first_preview"
        if active_visible_count
        else "data_pack_model_outputs"
    )
    status = (
        "warning"
        if (active_newer and stale_fallback_count) or active_sync.warning
        else "ready"
    )
    return {
        "active_pack_model_output_timestamp": pack_timestamp,
        "active_stats_first_preview_timestamp": active_sync.preview_timestamp,
        "visible_score_source": visible_source,
        "identity_match_method": active_sync.identity_match_method,
        "active_preview_rows": active_sync.preview_row_count,
        "active_preview_matched_rows": active_sync.matched_row_count,
        "active_preview_unmapped_rows": active_sync.unmapped_row_count,
        "visible_active_preview_rows": active_visible_count,
        "visible_data_pack_rows": data_pack_visible_count,
        "stale_pack_fallback_rows": stale_fallback_count,
        "market_value_status_counts": ";".join(
            f"{key}:{value}" for key, value in sorted(market_status_counts.items())
        ),
        "status": status,
        "warning": warning,
    }


def _latest_model_output_timestamp(validated: ValidatedDataPack) -> str:
    return _latest_row_timestamp(validated.rows_by_table.get("model_outputs", []))


def _latest_row_timestamp(rows: list[dict[str, object]]) -> str:
    timestamps = [str(row.get("computed_at") or "") for row in rows]
    return max(timestamps, default="")


def _is_newer_timestamp(candidate: str, baseline: str) -> bool:
    if not candidate:
        return False
    if not baseline:
        return True
    return candidate > baseline


def _preview_risk_level(warning_status: str, risk_flags: str) -> str:
    if warning_status in {"blocking", "review_needed"}:
        return "high"
    if warning_status == "model_warning" or risk_flags:
        return "medium"
    return "low"


def _preview_recommendation(
    drop_score: float,
    keeper_score: float,
    *,
    warning_status: str = "",
    confidence: float | None = None,
) -> str:
    if warning_status == "blocking" or (confidence is not None and confidence < 50):
        return "review"
    if keeper_score >= 70 and drop_score <= 30:
        return "keep"
    if keeper_score >= 65 and drop_score <= 25:
        return "keep"
    if drop_score >= 55:
        return "shop/release"
    if drop_score >= 40 or keeper_score < 58:
        return "shop"
    return "bubble"


def _by_player_id(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(row.get("player_id")): row for row in rows if row.get("player_id")}


def _resolve_team_id(rows: list[dict[str, object]], requested_team_id: str) -> str:
    if any(str(row.get("team_id") or "") == requested_team_id for row in rows):
        return requested_team_id
    normalized_request = _normalize_name(requested_team_id)
    for row in rows:
        team_id = str(row.get("team_id") or "")
        team_name = str(row.get("team_name") or "")
        if _normalize_name(team_name) == normalized_request:
            return team_id
    if normalized_request == "niners":
        for row in rows:
            team_id = str(row.get("team_id") or "")
            team_name = str(row.get("team_name") or "")
            if _normalize_name(team_name) == "niners":
                return team_id
    return requested_team_id


def _normalize_name(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _keeper_input(row: dict[str, object]) -> KeeperScoreInputs:
    formula_value = _optional_float(row.get("keeper_score"))
    if formula_value is None:
        formula_value = _optional_float(row.get("private_score"), 50.0)
    confidence_value = _optional_float(row.get("confidence_score"), 0.0)
    return KeeperScoreInputs(
        player_id=str(row.get("player_id") or ""),
        player_name=str(row.get("player_name") or row.get("player_id") or ""),
        position=str(row.get("position") or ""),
        official_rank=_optional_int(row.get("official_rank")),
        private_score=_optional_float(row.get("private_score"), 50.0),
        market_score=_optional_float(row.get("market_score")),
        confidence_score=_optional_float(row.get("confidence_score"), 0.6),
        roster_status=str(row.get("roster_status") or "rostered"),
        long_term_private_value=_optional_float(
            row.get("long_term_private_value"), formula_value
        ),
        next_2_year_starter_value=_optional_float(
            row.get("next_2_year_starter_value"), formula_value
        ),
        scarcity_bonus=_optional_float(row.get("scarcity_bonus"), formula_value),
        trade_liquidity=_optional_float(row.get("trade_liquidity"), formula_value),
        age_curve=_optional_float(row.get("age_curve"), formula_value),
        risk_adj=_optional_float(row.get("risk_adj"), formula_value),
        build_fit=_optional_float(row.get("build_fit"), formula_value),
        roster_redundancy=_optional_float(row.get("roster_redundancy"), 0.0) or 0.0,
        decline_risk=_optional_float(row.get("decline_risk"), 0.0) or 0.0,
        data_completeness=_optional_float(
            row.get("data_completeness"), confidence_value
        ),
        historical_cohort_size=_optional_float(
            row.get("historical_cohort_size"), confidence_value
        ),
        market_agreement=_optional_float(row.get("market_agreement"), confidence_value),
        model_separation=_optional_float(row.get("model_separation"), confidence_value),
    )


def _team_roster_row(
    row: dict[str, object],
    decision: KeeperDecision | None,
    top_five_ids: set[str],
    forced_ids: set[str],
    *,
    use_model_outputs: bool = False,
    release_pain: float = 0.0,
    release_explanation: str = "",
) -> dict[str, object]:
    player_id = str(row.get("player_id") or "")
    is_top_five = player_id in top_five_ids
    is_forced_release = player_id in forced_ids
    keeper_score = _optional_float(row.get("keeper_score")) if use_model_outputs else None
    drop_score = _optional_float(row.get("drop_candidate_score")) if use_model_outputs else None
    visible_keeper_score = (
        keeper_score if keeper_score is not None else _decision_value(decision, "keeper_score")
    )
    visible_drop_score = (
        drop_score
        if drop_score is not None
        else _decision_value(decision, "drop_candidate_score")
    )
    model_recommendation = (
        _model_recommendation(row, is_forced_release)
        if use_model_outputs
        else _recommendation(decision, is_forced_release)
    )
    stats_value = _optional_float(row.get("private_score"))
    market_context = _market_context(row, stats_value)
    top_five_rule = _top_five_rule_label(
        row,
        is_top_five=is_top_five,
        is_forced_release=is_forced_release,
    )
    team_section = _team_section(
        model_recommendation,
        visible_keeper_score,
        visible_drop_score,
        is_forced_release,
        confidence=_confidence_value(row.get("confidence_score")),
        warning_status=str(row.get("warning_status") or ""),
    )
    confidence = _confidence_value(row.get("confidence_score"))
    return {
        "player": row.get("player_name"),
        "pos": row.get("position"),
        "nfl_team": row.get("nfl_team"),
        "asset_lifecycle": row.get("asset_lifecycle"),
        "asset_lifecycle_label": row.get("asset_lifecycle_label"),
        "league_rank": row.get("league_rank"),
        "official_rank": row.get("league_rank"),
        "market_score": row.get("market_score"),
        "market_value_status": market_context["market_value_status"],
        "market_trade_value": market_context["market_value"],
        "market_edge_score": market_context["market_edge"],
        "market_edge_label": market_context["market_edge_label"],
        "market_edge_warning": market_context["market_edge_warning"],
        "war_score": row.get("war_score"),
        "stats_value": stats_value,
        "market_value": market_context["market_value"],
        "market_edge": market_context["market_edge"],
        "release_pain": round(release_pain, 2) if is_forced_release else None,
        "decision_explanation": release_explanation
        if is_forced_release
        else _non_forced_explanation(top_five_rule, model_recommendation),
        "keeper_score": visible_keeper_score,
        "drop_score": visible_drop_score,
        "keep_priority": visible_keeper_score,
        "cut_risk": visible_drop_score,
        "model_recommendation": model_recommendation,
        "recommendation": model_recommendation,
        "team_section": team_section,
        "top_five_rule": top_five_rule,
        "top_five_rule_note": _top_five_rule_note(row, is_top_five, is_forced_release),
        "confidence": confidence,
        "confidence_label": confidence_label(confidence),
        "confidence_explanation": confidence_explanation(
            confidence,
            row.get("warning_reasons"),
            market_context["market_edge_warning"],
        ),
        "receipt_link": "/my-team",
        "compare_link": "/war-board",
        "shield": bool(
            decision and decision.top_five_shield_eligible and player_id not in forced_ids
        ),
    }


def _top_five_rule_label(
    row: dict[str, object],
    *,
    is_top_five: bool,
    is_forced_release: bool,
) -> str:
    _ = row
    if not is_top_five:
        return "Not in Roster's League-Rank Top Five"
    if is_forced_release:
        return "Required Top-Five Release Slot"
    return "Roster Top-Five Protected Slot"


def _top_five_rule_note(
    row: dict[str, object],
    is_top_five: bool,
    is_forced_release: bool,
) -> str:
    _ = row
    if not is_top_five:
        return "Top-five rule does not apply to this player."
    if is_forced_release:
        return (
            "This row currently satisfies the Required Top-Five Release Slot "
            "for this roster."
        )
    return (
        "This player is inside this roster's five highest league-ranked players "
        "but is not the current required release slot."
    )


def _non_forced_explanation(top_five_rule: str, model_recommendation: str) -> str:
    if top_five_rule == "Not in Roster's League-Rank Top Five":
        return (
            f"Not part of this roster's top-five rule group; model bucket is "
            f"{model_recommendation}."
        )
    return (
        "Inside this roster's five highest league-ranked players, but not the "
        f"current required release slot; model bucket is {model_recommendation}."
    )


def _team_section(
    recommendation: str,
    keep_priority: float | None,
    cut_risk: float | None,
    is_forced_release: bool,
    *,
    confidence: float | None = None,
    warning_status: str = "",
) -> str:
    if is_forced_release:
        return "Forced-Release Decision"
    normalized = recommendation.lower()
    if normalized == "review" or _requires_decision_review(confidence, warning_status):
        return "Needs Data Review"
    if normalized in {"shop", "shop/release"}:
        return "Shop Candidates"
    if normalized in {"drop", "release", "release/drop"}:
        return "Bench/Stash"
    if normalized == "keep" and (
        (keep_priority or 0.0) >= 70
        or ((keep_priority or 0.0) >= 65 and (cut_risk or 100.0) <= 25)
    ):
        return "Core Holds"
    if normalized == "keep":
        return "Bubble Players"
    if normalized == "bubble":
        if (cut_risk or 0.0) >= 40 or (keep_priority or 0.0) < 58:
            return "Bench/Stash"
        return "Bubble Players"
    if (cut_risk or 0.0) >= 35 or (keep_priority or 0.0) < 65:
        return "Bench/Stash"
    return "Bubble Players"


def _requires_decision_review(confidence: float | None, warning_status: str) -> bool:
    if confidence is not None and confidence < 78:
        return True
    return warning_status.lower() in {"data_warning", "model_warning", "review_needed", "blocking"}


def _top_five_row(
    player: KeeperScoreInputs,
    decision: KeeperDecision | None,
    forced_ids: set[str],
) -> dict[str, object]:
    is_forced_release = player.player_id in forced_ids
    action = _recommendation(decision, is_forced_release)
    keeper_score = _decision_value(decision, "keeper_score")
    drop_score = _decision_value(decision, "drop_candidate_score")
    confidence = _confidence_value(player.confidence_score)
    return {
        "rank": player.official_rank,
        "league_rank": player.official_rank,
        "player": player.player_name,
        "pos": player.position,
        "keep_priority": keeper_score,
        "cut_risk": drop_score,
        "keeper_score": keeper_score,
        "drop_score": drop_score,
        "confidence": confidence,
        "confidence_label": confidence_label(confidence),
        "confidence_explanation": confidence_explanation(confidence),
        "top_five_rule": _top_five_rule_label(
            {"league_rank": player.official_rank},
            is_top_five=True,
            is_forced_release=is_forced_release,
        ),
        "model_recommendation": action,
        "action": action,
    }


def _top_five_model_row(
    row: dict[str, object],
    forced_ids: set[str],
    *,
    pressure_profile=None,
) -> dict[str, object]:
    player_id = str(row.get("player_id") or "")
    is_forced_release = player_id in forced_ids
    action = _model_recommendation(row, is_forced_release)
    keeper_score = _optional_float(row.get("keeper_score"))
    drop_score = _optional_float(row.get("drop_candidate_score"))
    release_pain = (
        round(pressure_profile.forced_release_pain, 2)
        if is_forced_release and pressure_profile is not None
        else None
    )
    explanation = (
        _top_five_release_explanation(row, pressure_profile)
        if is_forced_release and pressure_profile is not None
        else _top_five_rule_note(row, True, is_forced_release)
    )
    stats_value = _optional_float(row.get("private_score"))
    market_context = _market_context(row, stats_value)
    confidence = _confidence_value(row.get("confidence_score"))
    return {
        "rank": row.get("league_rank"),
        "league_rank": row.get("league_rank"),
        "player": row.get("player_name"),
        "pos": row.get("position"),
        "nfl_team": row.get("nfl_team"),
        "asset_lifecycle": row.get("asset_lifecycle"),
        "asset_lifecycle_label": row.get("asset_lifecycle_label"),
        "stats_value": stats_value,
        "market_value_status": market_context["market_value_status"],
        "market_edge": market_context["market_edge"],
        "confidence": confidence,
        "confidence_label": confidence_label(confidence),
        "confidence_explanation": confidence_explanation(
            confidence,
            row.get("warning_reasons"),
            market_context["market_edge_warning"],
        ),
        "keep_priority": keeper_score,
        "cut_risk": drop_score,
        "keeper_score": keeper_score,
        "drop_score": drop_score,
        "release_pain": release_pain,
        "decision_explanation": explanation,
        "top_five_rule": _top_five_rule_label(
            row,
            is_top_five=True,
            is_forced_release=is_forced_release,
        ),
        "top_five_rule_note": _top_five_rule_note(row, True, is_forced_release),
        "model_recommendation": action,
        "action": action,
    }


def _visible_top_five_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    ranked_rows = [row for row in rows if _optional_int(row.get("league_rank")) is not None]
    return sorted(
        ranked_rows,
        key=lambda row: (_optional_int(row.get("league_rank")) or 999, str(row.get("player_name"))),
    )[:5]


def _visible_forced_release_rows(
    top_five_rows: list[dict[str, object]],
    official_top_five_keep_limit: int,
) -> list[dict[str, object]]:
    release_count = max(0, len(top_five_rows) - official_top_five_keep_limit)
    if release_count == 0:
        return []
    return sorted(
        top_five_rows,
        key=lambda row: (
            _visible_player_value(row),
            -_visible_drop_score(row),
            _optional_int(row.get("league_rank")) or 999,
            str(row.get("player_name")),
        ),
    )[:release_count]


def _top_five_release_explanation(
    row: dict[str, object],
    pressure_profile,
) -> str:
    player = str(row.get("player_name") or row.get("player") or "This player")
    keeper = _optional_float(row.get("keeper_score"))
    cut_risk = _optional_float(row.get("drop_candidate_score"))
    league_rank = row.get("league_rank")
    pain = round(float(pressure_profile.forced_release_pain), 2)
    top_five_rows = list(getattr(pressure_profile, "top_five_rows", []) or [])
    release_id = str(row.get("player_id") or "")
    other_rows = [
        candidate
        for candidate in top_five_rows
        if str(candidate.get("player_id") or "") != release_id
    ]
    next_row = min(other_rows, key=_top_five_candidate_sort_key) if other_rows else None
    next_text = ""
    if next_row:
        next_name = str(next_row.get("player_name") or next_row.get("player_id") or "")
        next_keeper = _optional_float(next_row.get("keeper_score"))
        if next_keeper is not None:
            gap = (next_keeper - keeper) if keeper is not None else 0.0
            next_text = (
                f" Next closest protected roster top-five option: {next_name} "
                f"at {next_keeper:.2f} Keep Priority"
                f" ({gap:.2f} higher)."
            )
        else:
            next_text = f" Next closest protected roster top-five option: {next_name}."
    keeper_text = "unknown"
    if keeper is not None:
        keeper_text = f"{keeper:.2f}"
    cut_text = "unknown"
    if cut_risk is not None:
        cut_text = f"{cut_risk:.2f}"
    return (
        f"{player} is the current Required Top-Five Release Slot because he has "
        f"the lowest Keep Priority ({keeper_text}) inside this roster's five "
        "highest league-ranked players. "
        f"League rank: {league_rank}. Cut Risk: {cut_text}. Release Pain: {pain:.2f}."
        f"{next_text} Secondary roster-cut context is available only in Advanced."
    )


def _top_five_candidate_sort_key(row: dict[str, object]) -> tuple[float, float, int, str]:
    keeper = _optional_float(row.get("keeper_score"))
    cut_risk = _optional_float(row.get("drop_candidate_score"))
    return (
        keeper if keeper is not None else 50.0,
        -(cut_risk if cut_risk is not None else 50.0),
        _optional_int(row.get("league_rank")) or 999,
        str(row.get("player_name") or row.get("player_id") or ""),
    )


def _team_roster_sort_key(row: dict[str, object]) -> tuple[object, ...]:
    return (
        _team_section_sort_order(str(row.get("team_section") or "")),
        _recommendation_sort_order(str(row.get("recommendation") or "")),
        -_sortable_score(row.get("cut_risk")),
        -_sortable_score(row.get("keep_priority")),
        _optional_int(row.get("league_rank")) or 999,
        str(row.get("player") or ""),
    )


def _team_section_sort_order(section: str) -> int:
    try:
        return TEAM_SECTION_ORDER.index(section)
    except ValueError:
        return 99


def _recommendation_sort_order(recommendation: str) -> int:
    return {
        "shop/release": 0,
        "release": 1,
        "drop": 1,
        "shop": 2,
        "bubble": 3,
        "review": 4,
        "hold": 5,
        "risk": 6,
        "keep": 7,
    }.get(recommendation.lower(), 99)


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
    stats_value = _optional_float(row.get("private_score"))
    market_context = _market_context(row, stats_value)
    market_value = market_context["market_value"]
    market_edge = market_context["market_edge"]
    confidence = _confidence_value(row.get("confidence_score"))
    action = _model_recommendation(row, is_forced_release=False)
    edge_type = market_context["edge_type"]
    warning_reason = _warning_reason(row)
    return {
        "player_id": row.get("player_id"),
        "overall_rank": _optional_int(row.get("overall_rank")),
        "position_rank": _optional_int(row.get("position_rank")),
        "position_rank_label": row.get("position_rank_label"),
        "player": row.get("player_name"),
        "pos": row.get("position"),
        "team": row.get("team_name"),
        "asset_lifecycle": row.get("asset_lifecycle"),
        "asset_lifecycle_label": row.get("asset_lifecycle_label"),
        "league_rank": row.get("league_rank"),
        "official_rank": row.get("league_rank"),
        "market_score": row.get("market_score"),
        "market_value_status": market_context["market_value_status"],
        "market_trade_value": market_value,
        "market_edge_score": market_edge,
        "market_edge_label": market_context["market_edge_label"],
        "market_edge_warning": market_context["market_edge_warning"],
        "war_score": row.get("war_score"),
        "private_score": row.get("private_score"),
        "stats_value": stats_value,
        "market_value": market_value,
        "market_edge": market_edge,
        "edge_type": edge_type,
        "keeper_score": row.get("keeper_score"),
        "drop_score": row.get("drop_candidate_score"),
        "confidence": confidence,
        "confidence_bucket": _confidence_bucket(confidence),
        "confidence_label": confidence_label(confidence),
        "confidence_explanation": confidence_explanation(
            confidence,
            row.get("warning_reasons"),
            row.get("market_edge_warning"),
        ),
        "risk": row.get("risk_level"),
        "warning_status": row.get("warning_status"),
        "warning_reasons": row.get("warning_reasons"),
        "warning_reason": warning_reason,
        "score_source": row.get("score_source"),
        "identity_match_method": row.get("identity_match_method"),
        "score_source_warning": row.get("score_source_warning"),
        "model_version": row.get("model_version"),
        "computed_at": row.get("computed_at"),
        "action": action,
        "recommendation": action,
        "do_not_draft_before": row.get("do_not_draft_before_pick"),
        "notes": row.get("notes"),
        "why_ranked_here": _why_ranked_here(
            row,
            action=action,
            stats_value=stats_value,
            market_value=market_value,
            market_edge=market_edge,
            edge_type=edge_type,
            confidence=confidence,
            warning_reason=warning_reason,
        ),
    }


def _ranked_war_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    score_ranked = sorted(
        rows,
        key=lambda row: (-_sortable_score(row.get("war_score")), str(row.get("player"))),
    )
    position_counts: dict[str, int] = {}
    for index, row in enumerate(score_ranked, start=1):
        if row.get("overall_rank") is None:
            row["overall_rank"] = index
        position = str(row.get("pos") or "")
        if not position:
            continue
        position_counts[position] = position_counts.get(position, 0) + 1
        if row.get("position_rank") is None:
            row["position_rank"] = position_counts[position]
        if not row.get("position_rank_label"):
            row["position_rank_label"] = f"{position}{row['position_rank']}"
    return sorted(score_ranked, key=_war_board_sort_key)


def _war_board_sort_key(row: dict[str, object]) -> tuple[object, ...]:
    return (
        _optional_int(row.get("overall_rank")) or 9999,
        str(row.get("player") or ""),
    )


def _action_sort_order(action: str) -> int:
    return {
        "shop/release": 0,
        "release": 1,
        "drop": 1,
        "release/drop": 1,
        "shop": 2,
        "bubble": 3,
        "review": 4,
        "risk": 5,
        "hold": 6,
        "keep": 7,
    }.get(action.lower(), 99)


def _confidence_bucket_sort_order(bucket: str) -> int:
    return {
        "blocked": 0,
        "weak": 1,
        "review": 2,
        "usable": 3,
        "strong": 4,
        "unknown": 5,
    }.get(bucket.lower(), 99)


def _confidence_value(value: object) -> float | None:
    numeric = _optional_float(value)
    if numeric is None:
        return None
    if 0 < numeric <= 1:
        return round(numeric * 100, 2)
    return round(numeric, 2)


def _confidence_bucket(confidence: float | None) -> str:
    return "unknown" if confidence is None else confidence_label(confidence)


def _market_context(
    row: dict[str, object],
    stats_value: float | None,
) -> dict[str, object]:
    status = market_value_status(row)
    market_value = first_market_value(row)
    edge = safe_market_edge_score(
        stats_value,
        market_value,
        status,
        explicit_edge=row.get("market_edge_score"),
    )
    label = market_edge_classification(status, edge)
    if status == "real_imported_market" and edge is not None and row.get("market_edge_label"):
        label = str(row.get("market_edge_label"))
    warning = str(row.get("market_edge_warning") or "")
    status_warning = market_status_warning(status)
    if status_warning != "none":
        warning = status_warning
    return {
        "market_value_status": status,
        "market_value": market_value,
        "market_edge": edge,
        "market_edge_label": label,
        "market_edge_warning": warning,
        "edge_type": _edge_type(label, edge),
    }


def _edge_type(label: object, market_edge: float | None) -> str:
    normalized_label = _clean_slug_text(label)
    label_map = {
        "near market": "market close",
        "positive edge model higher": "model higher than market",
        "strong positive edge model higher": "model higher than market",
        "negative edge market higher": "market higher than model",
        "strong negative edge market higher": "market higher than model",
    }
    if normalized_label:
        return label_map.get(normalized_label, normalized_label)
    if market_edge is None:
        return "unknown"
    if market_edge >= 5:
        return "model higher than market"
    if market_edge <= -5:
        return "market higher than model"
    return "market close"


def _warning_reason(row: dict[str, object]) -> str:
    specific = warning_summary(
        row.get("warning_reasons"),
        row.get("market_edge_warning"),
        default="",
    )
    if specific:
        return specific
    return warning_summary(
        row.get("warning_status"),
    )


def _why_ranked_here(
    row: dict[str, object],
    *,
    action: str,
    stats_value: float | None,
    market_value: float | None,
    market_edge: float | None,
    edge_type: str,
    confidence: float | None,
    warning_reason: str,
) -> str:
    parts = [
        f"Action is {action or 'review'} based on keeper/drop pressure and model score.",
        f"Model value {_format_score(stats_value)} vs trade market {_format_score(market_value)}.",
    ]
    if market_edge is not None:
        parts.append(f"Model vs market {_format_signed_score(market_edge)} ({edge_type}).")
    elif edge_type and edge_type != "unknown":
        parts.append(f"Model vs market is review-only ({edge_type}).")
    if confidence is not None:
        parts.append(
            f"Confidence {_format_score(confidence)} ({confidence_label(confidence)})."
        )
    if warning_reason != NO_ACTIVE_WARNING:
        parts.append(f"Review note: {warning_reason}.")
    note = str(row.get("notes") or "").strip()
    if note:
        parts.append(note.rstrip(".") + ".")
    return " ".join(parts)


def _format_score(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1f}"


def _format_signed_score(value: float) -> str:
    return f"{value:+.1f}"


def _clean_slug_text(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    chunks = [
        chunk.strip().replace("_", " ")
        for item in text.replace(";", "|").replace(",", "|").split("|")
        for chunk in [item]
        if chunk.strip()
    ]
    return "; ".join(chunks)


def _war_recommendation(row: dict[str, object]) -> str:
    confidence = _optional_float(row.get("confidence_score"))
    if str(row.get("warning_status") or "") == "blocking" or (
        confidence is not None and confidence < 50
    ):
        return "review"
    drop_score = _optional_float(row.get("drop_candidate_score"), 0.0) or 0.0
    keeper_score = _optional_float(row.get("keeper_score"), 0.0) or 0.0
    if keeper_score >= 70 and drop_score <= 30:
        return "keep"
    if keeper_score >= 65 and drop_score <= 25:
        return "keep"
    if drop_score >= 55:
        return "drop"
    if drop_score >= 40 or keeper_score < 58:
        return "shop"
    return "bubble"


def _visible_drop_score(row: dict[str, object]) -> float:
    return (
        _optional_float(row.get("drop_candidate_score"))
        or _optional_float(row.get("drop_score"))
        or 0.0
    )


def _visible_player_value(row: dict[str, object]) -> float:
    for column in ("keeper_score", "private_score", "war_score"):
        value = _optional_float(row.get(column))
        if value is not None:
            return value
    return max(0.0, 100.0 - _visible_drop_score(row))


def _model_recommendation(row: dict[str, object], is_forced_release: bool) -> str:
    if is_forced_release:
        return "shop/release"
    if row.get("score_source") == "active_stats_first_preview":
        return _war_recommendation(row)
    recommendation = str(row.get("recommendation") or "")
    if recommendation:
        return recommendation
    return _war_recommendation(row)


def _has_scored_model_outputs(rows: list[dict[str, object]]) -> bool:
    return bool(rows) and all(
        row.get("model_version") and "Neutral placeholder" not in str(row.get("notes") or "")
        for row in rows
    )


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
