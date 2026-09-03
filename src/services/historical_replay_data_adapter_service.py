"""Historical redraft replay -- data adapter (section 18).

Consumer-side of docs/codex/HISTORICAL_REPLAY_DATA_CONTRACT_20260903.md.
Draft Upgrade HQ does not implement the Dataset Research Engine that
would produce a real conformant dataset --
docs/codex/HISTORICAL_REPLAY_SUBSTRATE_INVENTORY_20260903.md found no
such dataset is buildable from data in this repo today. This module is
the adapter that WOULD consume one once it exists: schema/identity/
leakage validators, a loader that returns an explicit "unavailable"
result rather than fabricating data when no real dataset is on disk, a
chronological splitter, and an evaluation runner that scores arbitrary
caller-supplied draft strategies against realized outcomes.

Leakage guard: BLOCKED_FEATURE_TOKENS below is a deliberate, literal copy
of scripts/build_backtest_dataset_v0.py's own BLOCKED_FEATURE_TOKENS --
reusing that established pattern rather than inventing a new one, per
the data contract's own instruction. It is copied rather than imported
because src/services/ modules do not depend on scripts/ (a different,
heavier-dependency layer); the two are kept in sync intentionally, not
accidentally duplicated.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any

# Deliberately mirrors scripts/build_backtest_dataset_v0.py's own
# BLOCKED_FEATURE_TOKENS -- see module docstring.
BLOCKED_FEATURE_TOKENS = (
    "adp",
    "market",
    "ranking",
    "projection",
    "fantasy_points",
    "fantasy_points_ppr",
    "trade_calculator",
    "sleeper_adp",
)

# Every pre-draft (ranking-input-eligible) field this contract requires.
# Any row key outside this set (and outside OUTCOME_ONLY_FIELDS) is
# subject to the BLOCKED_FEATURE_TOKENS check -- an unexpected column
# with a leakage-shaped name is refused rather than silently admitted.
REQUIRED_PRE_DRAFT_FIELDS = (
    "player_id",
    "player_name",
    "position",
    "team",
    "season",
    "draft_date",
    "projection_as_of",
    "platform_adp",
    "adp_as_of",
    "status_as_of",
    "scoring_format",
)
# Outcome-only fields: usable ONLY for scoring a replay after the fact,
# never as a ranking input. Kept in a strictly separate namespace from
# the pre-draft fields above -- see HistoricalReplayRow.
OUTCOME_ONLY_FIELDS = ("realized_weekly_points", "outcome_as_of")


class HistoricalReplayDataError(ValueError):
    """Raised for schema/leakage/identity contract violations."""


@dataclass(frozen=True)
class HistoricalReplayRow:
    """One player, one historical season, as-of the real draft date.
    pre_draft holds only REQUIRED_PRE_DRAFT_FIELDS (ranking-input-eligible);
    outcome holds only OUTCOME_ONLY_FIELDS (scoring-only, never a ranking
    input) -- the split itself is the leakage guard for this shape."""

    player_id: str
    season: int
    pre_draft: Mapping[str, Any]
    outcome: Mapping[str, Any]


@dataclass(frozen=True)
class SchemaValidationResult:
    valid: bool
    row_count: int
    missing_field_rows: tuple[tuple[str, tuple[str, ...]], ...]  # (player_id, missing fields)
    unparseable_date_rows: tuple[tuple[str, str], ...]  # (player_id, field name)


def validate_schema(rows: Sequence[Mapping[str, Any]]) -> SchemaValidationResult:
    """Every row must carry every REQUIRED_PRE_DRAFT_FIELDS key with a
    non-empty value, and every *_as_of / draft_date field must be a real,
    parseable ISO date -- never silently coerced or skipped."""
    missing: list[tuple[str, tuple[str, ...]]] = []
    bad_dates: list[tuple[str, str]] = []
    date_fields = ("draft_date", "projection_as_of", "adp_as_of", "status_as_of")
    for row in rows:
        player_id = str(row.get("player_id") or "<missing player_id>")
        gaps = tuple(
            field_name
            for field_name in REQUIRED_PRE_DRAFT_FIELDS
            if not str(row.get(field_name) or "").strip()
        )
        if gaps:
            missing.append((player_id, gaps))
        for field_name in date_fields:
            value = row.get(field_name)
            if value is None:
                continue
            try:
                date.fromisoformat(str(value))
            except ValueError:
                bad_dates.append((player_id, field_name))
    return SchemaValidationResult(
        valid=not missing and not bad_dates,
        row_count=len(rows),
        missing_field_rows=tuple(missing),
        unparseable_date_rows=tuple(bad_dates),
    )


@dataclass(frozen=True)
class LeakageValidationResult:
    valid: bool
    blocked_column_rows: tuple[tuple[str, tuple[str, ...]], ...]  # (player_id, blocked columns)
    future_dated_rows: tuple[tuple[str, str], ...]  # (player_id, which as-of field is >= draft_date)  # noqa: E501
    outcome_before_draft_rows: tuple[str, ...]  # player_ids where outcome_as_of < draft_date


def validate_leakage(rows: Sequence[Mapping[str, Any]]) -> LeakageValidationResult:
    """Two independent checks, both hard requirements from the data
    contract:
    1. Column-name check (BLOCKED_FEATURE_TOKENS): any row key outside
       REQUIRED_PRE_DRAFT_FIELDS/OUTCOME_ONLY_FIELDS whose lowercased
       name contains a blocked token is refused -- an unexpected
       leakage-shaped column never gets silently admitted.
    2. Date check: projection_as_of and adp_as_of must be strictly before
       draft_date, and status_as_of no later than draft_date -- "as of
       the draft date," not after it. outcome_as_of (if present) must be
       on or after draft_date -- an outcome cannot predate the draft it
       scores.
    """
    allowed = set(REQUIRED_PRE_DRAFT_FIELDS) | set(OUTCOME_ONLY_FIELDS)
    blocked_rows: list[tuple[str, tuple[str, ...]]] = []
    future_dated: list[tuple[str, str]] = []
    outcome_before_draft: list[str] = []
    for row in rows:
        player_id = str(row.get("player_id") or "<missing player_id>")
        extra_keys = [key for key in row if key not in allowed]
        blocked = tuple(
            key
            for key in extra_keys
            if any(token in key.lower() for token in BLOCKED_FEATURE_TOKENS)
        )
        if blocked:
            blocked_rows.append((player_id, blocked))
        draft_date_value = _safe_date(row.get("draft_date"))
        if draft_date_value is not None:
            for field_name in ("projection_as_of", "adp_as_of"):
                as_of = _safe_date(row.get(field_name))
                if as_of is not None and as_of >= draft_date_value:
                    future_dated.append((player_id, field_name))
            status_as_of = _safe_date(row.get("status_as_of"))
            if status_as_of is not None and status_as_of > draft_date_value:
                future_dated.append((player_id, "status_as_of"))
            outcome_as_of = _safe_date(row.get("outcome_as_of"))
            if outcome_as_of is not None and outcome_as_of < draft_date_value:
                outcome_before_draft.append(player_id)
    return LeakageValidationResult(
        valid=not blocked_rows and not future_dated and not outcome_before_draft,
        blocked_column_rows=tuple(blocked_rows),
        future_dated_rows=tuple(future_dated),
        outcome_before_draft_rows=tuple(outcome_before_draft),
    )


def _safe_date(value: Any) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


@dataclass(frozen=True)
class IdentityValidationResult:
    valid: bool
    resolved_pick_count: int
    unresolved_picks: tuple[dict[str, Any], ...]


def validate_identity_completeness(
    historical_picks: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
) -> IdentityValidationResult:
    """Every real historical pick must resolve to exactly one player_id in
    `rows`, or be explicitly present in `unresolved_picks` with an
    identity_status -- the same identity-completeness bar the live-draft
    KHA reconciliation work holds itself to (never a silent gap)."""
    known_ids = {str(row.get("player_id") or "") for row in rows}
    unresolved: list[dict[str, Any]] = []
    resolved = 0
    for pick in historical_picks:
        identity_status = str(pick.get("identity_status") or "").strip()
        player_id = str(pick.get("player_id") or "")
        if player_id and player_id in known_ids:
            resolved += 1
            continue
        if identity_status:
            unresolved.append(dict(pick))
            continue
        unresolved.append({**dict(pick), "identity_status": "UNFLAGGED_UNRESOLVED"})
    return IdentityValidationResult(
        valid=not any(
            row.get("identity_status") == "UNFLAGGED_UNRESOLVED" for row in unresolved
        ),
        resolved_pick_count=resolved,
        unresolved_picks=tuple(unresolved),
    )


@dataclass(frozen=True)
class HistoricalReplayDataset:
    rows: tuple[HistoricalReplayRow, ...]
    seasons: tuple[int, ...]
    schema: SchemaValidationResult
    leakage: LeakageValidationResult


@dataclass(frozen=True)
class HistoricalReplayUnavailable:
    reason: str


def load_historical_replay_dataset(
    raw_rows: Sequence[Mapping[str, Any]] | None,
) -> HistoricalReplayDataset | HistoricalReplayUnavailable:
    """The loader. Returns HistoricalReplayUnavailable -- never a faked
    or backfilled dataset -- when no rows are supplied or every row fails
    schema/leakage validation. This is the honest, expected result in
    this repo today: no real conformant dataset exists yet (see the
    substrate inventory doc)."""
    if not raw_rows:
        return HistoricalReplayUnavailable(
            "No historical replay rows supplied -- no Dataset Research Engine handoff "
            "exists in this repo yet."
        )
    schema = validate_schema(raw_rows)
    leakage = validate_leakage(raw_rows)
    if not schema.valid or not leakage.valid:
        return HistoricalReplayUnavailable(
            f"Historical replay data failed validation: "
            f"schema_valid={schema.valid}, leakage_valid={leakage.valid}. "
            "Refusing to load a non-conformant dataset rather than using it anyway."
        )
    rows = tuple(
        HistoricalReplayRow(
            player_id=str(row["player_id"]),
            season=int(row["season"]),
            pre_draft={key: row.get(key) for key in REQUIRED_PRE_DRAFT_FIELDS},
            outcome={key: row.get(key) for key in OUTCOME_ONLY_FIELDS if key in row},
        )
        for row in raw_rows
    )
    seasons = tuple(sorted({row.season for row in rows}))
    return HistoricalReplayDataset(rows=rows, seasons=seasons, schema=schema, leakage=leakage)


@dataclass(frozen=True)
class DatasetSplit:
    train: tuple[HistoricalReplayRow, ...]
    validate: tuple[HistoricalReplayRow, ...]
    test: tuple[HistoricalReplayRow, ...]
    train_seasons: tuple[int, ...]
    validate_seasons: tuple[int, ...]
    test_seasons: tuple[int, ...]


def chronological_split(
    dataset: HistoricalReplayDataset,
    *,
    train_seasons: Sequence[int],
    validate_seasons: Sequence[int],
    test_seasons: Sequence[int],
) -> DatasetSplit:
    """Splits by explicit season assignment -- the caller states which
    seasons go where; nothing here guesses a split automatically. Refuses
    overlapping assignments and refuses any dataset season left
    unassigned, so a split can never silently drop or double-count a
    season. General chronological-split discipline (earlier seasons never
    used to evaluate a later one) rather than a literal spec drawn from
    docs/codex/CALIBRATION_PLAN.md, which states calibration principles,
    not split mechanics."""
    train_set, validate_set, test_set = set(train_seasons), set(validate_seasons), set(test_seasons)
    overlap = (train_set & validate_set) | (train_set & test_set) | (validate_set & test_set)
    if overlap:
        raise HistoricalReplayDataError(
            f"Season(s) assigned to more than one split: {sorted(overlap)}"
        )
    assigned = train_set | validate_set | test_set
    unassigned = set(dataset.seasons) - assigned
    if unassigned:
        raise HistoricalReplayDataError(
            f"Dataset season(s) not assigned to any split: {sorted(unassigned)}"
        )
    if train_set and validate_set and max(train_set) >= min(validate_set):
        raise HistoricalReplayDataError(
            "train_seasons must be strictly earlier than validate_seasons "
            "(chronological split, no future-leaks-into-past)."
        )
    if validate_set and test_set and max(validate_set) >= min(test_set):
        raise HistoricalReplayDataError(
            "validate_seasons must be strictly earlier than test_seasons "
            "(chronological split, no future-leaks-into-past)."
        )
    return DatasetSplit(
        train=tuple(row for row in dataset.rows if row.season in train_set),
        validate=tuple(row for row in dataset.rows if row.season in validate_set),
        test=tuple(row for row in dataset.rows if row.season in test_set),
        train_seasons=tuple(sorted(train_set)),
        validate_seasons=tuple(sorted(validate_set)),
        test_seasons=tuple(sorted(test_set)),
    )


# --- Evaluation runner ---------------------------------------------------
# A "strategy" is any caller-supplied function that orders a season's
# available players for one team's pick -- this runner does not hardcode
# PLATFORM ADP / GREEDY NWR / STANDARD VBD / etc. internally; the six
# methodologies docs/codex/HISTORICAL_REPLAY_DATA_CONTRACT_20260903.md
# names are each just a different strategy function a caller registers.
DraftStrategy = Callable[[Sequence[HistoricalReplayRow]], Sequence[HistoricalReplayRow]]


@dataclass(frozen=True)
class StrategyReplayResult:
    strategy_name: str
    season: int
    team_count: int
    rounds: int
    total_realized_points: float
    mean_realized_points_per_team: float
    per_team_points: tuple[float, ...]


def run_replay_evaluation(
    season_rows: Sequence[HistoricalReplayRow],
    *,
    season: int,
    team_count: int,
    rounds: int,
    strategies: Mapping[str, DraftStrategy],
) -> tuple[StrategyReplayResult, ...]:
    """Runs each named strategy as a simple round-by-round snake draft
    over `season_rows` (already the correct single season -- callers
    combine this with chronological_split), scoring every team's roster
    by summed realized_weekly_points from the OUTCOME-only fields.
    Refuses a strategy result set with fewer picks than team_count *
    rounds can supply rather than silently scoring a partial roster as if
    it were complete."""
    if len(season_rows) < team_count:
        raise HistoricalReplayDataError(
            f"Season {season} has {len(season_rows)} available players, fewer than "
            f"team_count={team_count} -- cannot run a replay."
        )
    results: list[StrategyReplayResult] = []
    for name, strategy in strategies.items():
        available = list(season_rows)
        rosters: list[list[HistoricalReplayRow]] = [[] for _ in range(team_count)]
        total_slots = min(team_count * rounds, len(available))
        for pick_index in range(total_slots):
            round_number = pick_index // team_count
            position_in_round = pick_index % team_count
            team_index = (
                position_in_round if round_number % 2 == 0 else team_count - 1 - position_in_round
            )
            ordered = strategy(available)
            if not ordered:
                break
            chosen = ordered[0]
            rosters[team_index].append(chosen)
            available = [row for row in available if row.player_id != chosen.player_id]
        per_team_points = tuple(
            round(sum(_realized_points(row) for row in roster), 2) for roster in rosters
        )
        total = round(sum(per_team_points), 2)
        results.append(
            StrategyReplayResult(
                strategy_name=name,
                season=season,
                team_count=team_count,
                rounds=rounds,
                total_realized_points=total,
                mean_realized_points_per_team=round(total / team_count, 2) if team_count else 0.0,
                per_team_points=per_team_points,
            )
        )
    return tuple(results)


def _realized_points(row: HistoricalReplayRow) -> float:
    value = row.outcome.get("realized_weekly_points")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Sequence) and not isinstance(value, str):
        return float(sum(float(v) for v in value))
    return 0.0
