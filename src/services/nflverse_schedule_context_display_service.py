from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

NOT_ENOUGH_INFORMATION = "Not enough information"
SAFE_NOW_DISPLAY_ONLY = "SAFE_NOW_DISPLAY_ONLY"
NEED_IDENTITY_REVIEW = "NEED_IDENTITY_REVIEW"
DISPLAY_POLICY = "Display-only / Review-only schedule context / Not model input"
SOURCE_LABEL = "NFLVerse player context display artifact"

REPO_ROOT = Path(__file__).resolve().parents[2]
PLAYER_CONTEXT_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_player_context_display_20260630"
)
DEFAULT_ARTIFACT_PATH = PLAYER_CONTEXT_DIR / "nflverse_player_context_display_artifact.csv"
DEFAULT_SCHEMA_PATH = PLAYER_CONTEXT_DIR / "nflverse_player_context_schema_manifest.csv"

SCHEDULE_SOURCE_FIELDS = (
    "next_game_context",
    "opponent_context",
    "bye_context",
)
SCHEDULE_DISPLAY_FIELDS = (
    *SCHEDULE_SOURCE_FIELDS,
    "game_date",
    "game_week",
    "home_away",
    "season",
    "team",
)
REQUIRED_ARTIFACT_COLUMNS = (
    "nwr_player_id",
    "nwr_player_name",
    "nwr_position",
    "nwr_team",
    "nflverse_team",
    "identity_join_status",
    "review_required",
    "display_only",
    "model_use_allowed",
    "training_allowed",
    "source_truth_allowed",
    "rank_logic_allowed",
    "hidden_sort_allowed",
    "trade_value_allowed",
    "pick_value_allowed",
    *SCHEDULE_SOURCE_FIELDS,
)
REQUIRED_SCHEMA_COLUMNS = (
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
)
FALSE_FLAG_FIELDS = (
    "model_use_allowed",
    "training_allowed",
    "source_truth_allowed",
    "rank_logic_allowed",
    "hidden_sort_allowed",
    "trade_value_allowed",
    "pick_value_allowed",
)
UNAVAILABLE_VALUES = {
    "",
    "nan",
    "none",
    "null",
    "n/a",
    "<na>",
    NOT_ENOUGH_INFORMATION.lower(),
    "review needed",
    "not_applicable",
}
UNAVAILABLE_PREFIXES = ("NEED_", "BLOCKED_")


@dataclass(frozen=True)
class ScheduleContextDisplay:
    status: str
    reason: str
    nwr_player_id: str
    player: str
    position: str
    next_game_context: str
    opponent_context: str
    bye_context: str
    game_date: str
    game_week: str
    home_away: str
    season: str
    team: str
    display_policy: str = DISPLAY_POLICY
    source: str = SOURCE_LABEL

    @property
    def available(self) -> bool:
        return self.status == SAFE_NOW_DISPLAY_ONLY

    def as_display_row(self) -> dict[str, str]:
        return {
            "NWR Player ID": self.nwr_player_id,
            "Player": self.player,
            "Position": self.position,
            "Team": self.team,
            "Season": self.season,
            "Game Week": self.game_week,
            "Game Date": self.game_date,
            "Home/Away": self.home_away,
            "Next Game Context": self.next_game_context,
            "Opponent Context": self.opponent_context,
            "Bye Context": self.bye_context,
            "Status": self.status,
            "Reason": self.reason,
            "Display Policy": self.display_policy,
        }


@dataclass(frozen=True)
class ScheduleContextIndex:
    artifact_rows: tuple[dict[str, str], ...]
    schema_safe_fields: frozenset[str]
    errors: tuple[str, ...]
    artifact_path: Path
    schema_path: Path

    @property
    def safe_schedule_rows(self) -> tuple[dict[str, str], ...]:
        return tuple(
            row
            for row in self.artifact_rows
            if schedule_context_display_for_row(row, self.schema_safe_fields).available
        )

    @property
    def identity_review_rows(self) -> tuple[dict[str, str], ...]:
        return tuple(
            row
            for row in self.artifact_rows
            if _value(row.get("identity_join_status")) == NEED_IDENTITY_REVIEW
            or _value(row.get("review_required")).lower() == "true"
        )


def load_schedule_context_index(
    *,
    artifact_path: Path = DEFAULT_ARTIFACT_PATH,
    schema_path: Path = DEFAULT_SCHEMA_PATH,
) -> ScheduleContextIndex:
    errors: list[str] = []
    artifact_rows = tuple(_read_csv_rows(artifact_path))
    schema_rows = tuple(_read_csv_rows(schema_path))
    if not artifact_rows:
        errors.append(f"{SOURCE_LABEL} rows were not found.")
    if not schema_rows:
        errors.append("NFLVerse player context schema manifest rows were not found.")
    if artifact_rows:
        missing = set(REQUIRED_ARTIFACT_COLUMNS) - set(artifact_rows[0])
        if missing:
            errors.append("Missing artifact columns: " + ", ".join(sorted(missing)))
    if schema_rows:
        missing = set(REQUIRED_SCHEMA_COLUMNS) - set(schema_rows[0])
        if missing:
            errors.append("Missing schema columns: " + ", ".join(sorted(missing)))
    safe_fields = frozenset(_schema_safe_fields(schema_rows)) if not errors else frozenset()
    return ScheduleContextIndex(
        artifact_rows=artifact_rows,
        schema_safe_fields=safe_fields,
        errors=tuple(errors),
        artifact_path=artifact_path,
        schema_path=schema_path,
    )


def schedule_context_display_for_player_id(
    nwr_player_id: object,
    index: ScheduleContextIndex,
) -> ScheduleContextDisplay:
    player_id = _value(nwr_player_id)
    if not _usable(player_id):
        return _unavailable(player_id=player_id, reason=NOT_ENOUGH_INFORMATION)
    for row in index.artifact_rows:
        if _value(row.get("nwr_player_id")) == player_id:
            return schedule_context_display_for_row(row, index.schema_safe_fields)
    return _unavailable(player_id=player_id, reason=NOT_ENOUGH_INFORMATION)


def schedule_context_display_for_row(
    row: dict[str, object],
    schema_safe_fields: set[str] | frozenset[str],
) -> ScheduleContextDisplay:
    player_id = _display_value(row.get("nwr_player_id"))
    player = _display_value(row.get("nwr_player_name"))
    position = _display_value(row.get("nwr_position"))
    if not _row_passes_display_gate(row):
        return _unavailable(
            player_id=player_id,
            player=player,
            position=position,
            reason=NOT_ENOUGH_INFORMATION,
        )

    missing_schema_fields = [
        field for field in SCHEDULE_SOURCE_FIELDS if field not in schema_safe_fields
    ]
    if missing_schema_fields:
        return _unavailable(
            player_id=player_id,
            player=player,
            position=position,
            reason=NOT_ENOUGH_INFORMATION,
        )

    next_game = _field_value(row, "next_game_context", schema_safe_fields)
    opponent = _field_value(row, "opponent_context", schema_safe_fields)
    bye = _field_value(row, "bye_context", schema_safe_fields)
    if all(value == NOT_ENOUGH_INFORMATION for value in (next_game, opponent, bye)):
        return _unavailable(
            player_id=player_id,
            player=player,
            position=position,
            reason=NOT_ENOUGH_INFORMATION,
        )

    next_game_parts = _parse_context_parts(next_game)
    opponent_parts = _parse_context_parts(opponent)
    team = _team_value(row, schema_safe_fields)
    return ScheduleContextDisplay(
        status=SAFE_NOW_DISPLAY_ONLY,
        reason=(
            "Factual schedule display only; no matchup, health, valuation, "
            "or recommendation inference."
        ),
        nwr_player_id=player_id,
        player=player,
        position=position,
        next_game_context=next_game,
        opponent_context=opponent,
        bye_context=bye,
        game_date=_display_value(next_game_parts.get("date")),
        game_week=_display_value(next_game_parts.get("week")),
        home_away=_display_value(opponent_parts.get("home_away")),
        season=_display_value(next_game_parts.get("season")),
        team=team,
    )


def schedule_context_counts(index: ScheduleContextIndex) -> dict[str, int]:
    safe_displays = index.safe_schedule_rows
    return {
        "artifact_rows": len(index.artifact_rows),
        "safe_schedule_rows": len(safe_displays),
        "identity_review_rows": len(index.identity_review_rows),
        "safe_next_game_rows": sum(
            1
            for row in safe_displays
            if _field_value(row, "next_game_context", index.schema_safe_fields)
            != NOT_ENOUGH_INFORMATION
        ),
        "safe_opponent_rows": sum(
            1
            for row in safe_displays
            if _field_value(row, "opponent_context", index.schema_safe_fields)
            != NOT_ENOUGH_INFORMATION
        ),
        "safe_bye_rows": sum(
            1
            for row in safe_displays
            if _field_value(row, "bye_context", index.schema_safe_fields)
            != NOT_ENOUGH_INFORMATION
        ),
    }


def unavailable_schedule_context_row(player_id: object = "") -> dict[str, str]:
    return _unavailable(
        player_id=_value(player_id),
        reason=NOT_ENOUGH_INFORMATION,
    ).as_display_row()


def _row_passes_display_gate(row: dict[str, object]) -> bool:
    if not _usable(row.get("nwr_player_id")):
        return False
    if _value(row.get("identity_join_status")) != SAFE_NOW_DISPLAY_ONLY:
        return False
    if _value(row.get("review_required")).lower() != "false":
        return False
    if _value(row.get("display_only")).lower() != "true":
        return False
    return all(_value(row.get(field)).lower() == "false" for field in FALSE_FLAG_FIELDS)


def _schema_safe_fields(schema_rows: tuple[dict[str, str], ...]) -> set[str]:
    safe_fields: set[str] = set()
    for row in schema_rows:
        if _value(row.get("field_status")) != SAFE_NOW_DISPLAY_ONLY:
            continue
        if _value(row.get("display_only")).lower() != "true":
            continue
        if not all(_value(row.get(field)).lower() == "false" for field in FALSE_FLAG_FIELDS):
            continue
        safe_fields.add(_value(row.get("column_name")))
    return safe_fields


def _field_value(
    row: dict[str, object],
    field_name: str,
    schema_safe_fields: set[str] | frozenset[str],
) -> str:
    if field_name not in schema_safe_fields:
        return NOT_ENOUGH_INFORMATION
    return _display_value(row.get(field_name))


def _team_value(
    row: dict[str, object],
    schema_safe_fields: set[str] | frozenset[str],
) -> str:
    for field_name in ("nflverse_team", "nwr_team"):
        value = _field_value(row, field_name, schema_safe_fields)
        if value != NOT_ENOUGH_INFORMATION:
            return value
    return NOT_ENOUGH_INFORMATION


def _parse_context_parts(value: str) -> dict[str, str]:
    if _display_value(value) == NOT_ENOUGH_INFORMATION:
        return {}
    parts: dict[str, str] = {}
    for chunk in value.split(";"):
        if "=" not in chunk:
            continue
        key, parsed_value = chunk.split("=", 1)
        parts[_value(key)] = _value(parsed_value)
    return parts


def _unavailable(
    *,
    player_id: str = "",
    player: str = NOT_ENOUGH_INFORMATION,
    position: str = NOT_ENOUGH_INFORMATION,
    reason: str,
) -> ScheduleContextDisplay:
    return ScheduleContextDisplay(
        status=NOT_ENOUGH_INFORMATION,
        reason=reason or NOT_ENOUGH_INFORMATION,
        nwr_player_id=_display_value(player_id),
        player=_display_value(player),
        position=_display_value(position),
        next_game_context=NOT_ENOUGH_INFORMATION,
        opponent_context=NOT_ENOUGH_INFORMATION,
        bye_context=NOT_ENOUGH_INFORMATION,
        game_date=NOT_ENOUGH_INFORMATION,
        game_week=NOT_ENOUGH_INFORMATION,
        home_away=NOT_ENOUGH_INFORMATION,
        season=NOT_ENOUGH_INFORMATION,
        team=NOT_ENOUGH_INFORMATION,
    )


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [
            {key: _value(value) for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def _display_value(value: object) -> str:
    text = _value(value)
    if text.lower() in UNAVAILABLE_VALUES:
        return NOT_ENOUGH_INFORMATION
    if any(text.startswith(prefix) for prefix in UNAVAILABLE_PREFIXES):
        return NOT_ENOUGH_INFORMATION
    return text


def _usable(value: object) -> bool:
    return _display_value(value) != NOT_ENOUGH_INFORMATION


def _value(value: object) -> str:
    return str(value if value is not None else "").strip()
