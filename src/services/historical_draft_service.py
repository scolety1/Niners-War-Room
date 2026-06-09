from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

ROOKIE_DRAFT_PICK_COUNT = 5
ROOKIE_CONFIDENCE = "rough"
ROOKIE_PROVENANCE_NOTE = (
    "Platform final-five extraction; traded-pick ownership not preserved"
)
OFFLINE_NOTE_CONFIDENCE = "handwritten_note"
OFFLINE_NOTE_PROVENANCE_NOTE = (
    "Offline handwritten rookie draft note; verify traded-pick ownership manually"
)

REQUIRED_PLATFORM_DRAFT_COLUMNS = (
    "season",
    "overall_pick",
    "round",
    "slot",
    "team",
    "player",
    "position",
    "source",
)

REQUIRED_OFFLINE_NOTE_COLUMNS = (
    "season",
    "rookie_pick_number",
    "team",
    "player",
    "position",
    "source",
)

REQUIRED_MODEL_REPLAY_COLUMNS = (
    "season",
    "player",
    "position",
    "model_rank",
    "model_score",
    "model_recommendation",
    "outcome_label",
    "outcome_score",
    "source",
)


@dataclass(frozen=True)
class PlatformDraftPick:
    season: int
    overall_pick: int
    round: int
    slot: int
    team: str
    player: str
    position: str
    source: str
    row_number: int


@dataclass(frozen=True)
class HistoricalRookieDraftEntry:
    season: int
    rookie_pick_number: int
    platform_overall_pick: int | None
    drafted_player: str
    drafting_team: str
    position: str
    confidence: str
    provenance_note: str
    needs_traded_pick_review: bool
    source: str


@dataclass(frozen=True)
class HistoricalRookieDraftBoard:
    entries: list[HistoricalRookieDraftEntry]
    seasons: list[int]
    confidence_labels: list[str]
    review_warning: str


@dataclass(frozen=True)
class HistoricalRookieModelReplay:
    season: int
    player: str
    position: str
    model_rank: int
    model_score: float
    model_recommendation: str
    outcome_label: str
    outcome_score: float | None
    source: str
    row_number: int


@dataclass(frozen=True)
class HistoricalReplayComparison:
    season: int
    rookie_pick_number: int
    drafted_player: str
    drafting_team: str
    position: str
    model_rank: int | None
    model_score: float | None
    model_recommendation: str
    outcome_label: str
    outcome_score: float | None
    rank_delta: int | None
    replay_verdict: str
    calibration_note: str
    confidence: str
    source: str


@dataclass(frozen=True)
class HistoricalReplayComparisonBoard:
    rows: list[HistoricalReplayComparison]
    seasons: list[int]
    verdicts: list[str]
    missing_model_count: int
    review_warning: str


def reconstruct_historical_rookie_drafts(
    platform_draft_csv_path: str | Path,
    *,
    rookie_pick_count: int = ROOKIE_DRAFT_PICK_COUNT,
) -> HistoricalRookieDraftBoard:
    picks = load_platform_draft_results(platform_draft_csv_path)
    entries = extract_final_picks_as_rookie_drafts(
        picks,
        rookie_pick_count=rookie_pick_count,
    )
    return HistoricalRookieDraftBoard(
        entries=entries,
        seasons=sorted({entry.season for entry in entries}),
        confidence_labels=sorted({entry.confidence for entry in entries}),
        review_warning=ROOKIE_PROVENANCE_NOTE,
    )


def load_platform_draft_results(path: str | Path) -> list[PlatformDraftPick]:
    csv_path = Path(path)
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing_columns = [
            column
            for column in REQUIRED_PLATFORM_DRAFT_COLUMNS
            if column not in (reader.fieldnames or ())
        ]
        if missing_columns:
            raise ValueError(
                "Missing historical platform draft columns: "
                + ", ".join(missing_columns)
                + "."
            )
        return [
            _yahoo_pick_from_row(row, row_number)
            for row_number, row in enumerate(reader, start=2)
        ]


def load_yahoo_draft_results(path: str | Path) -> list[PlatformDraftPick]:
    return load_platform_draft_results(path)


def load_offline_rookie_notes(path: str | Path) -> HistoricalRookieDraftBoard:
    entries = _load_offline_rookie_note_entries(path)
    return HistoricalRookieDraftBoard(
        entries=entries,
        seasons=sorted({entry.season for entry in entries}),
        confidence_labels=sorted({entry.confidence for entry in entries}),
        review_warning=OFFLINE_NOTE_PROVENANCE_NOTE,
    )


def load_historical_rookie_model_replay(path: str | Path) -> list[HistoricalRookieModelReplay]:
    csv_path = Path(path)
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing_columns = [
            column
            for column in REQUIRED_MODEL_REPLAY_COLUMNS
            if column not in (reader.fieldnames or ())
        ]
        if missing_columns:
            raise ValueError(
                "Missing historical rookie model replay columns: "
                + ", ".join(missing_columns)
                + "."
            )
        return [
            _model_replay_entry(row, row_number)
            for row_number, row in enumerate(reader, start=2)
        ]


def compare_historical_rookie_replay(
    actual_board: HistoricalRookieDraftBoard,
    model_replay_rows: list[HistoricalRookieModelReplay],
) -> HistoricalReplayComparisonBoard:
    replay_by_key = {
        (_match_key(row.season, row.player)): row
        for row in model_replay_rows
    }
    comparisons = [
        _comparison_row(entry, replay_by_key.get(_match_key(entry.season, entry.drafted_player)))
        for entry in actual_board.entries
    ]
    return HistoricalReplayComparisonBoard(
        rows=comparisons,
        seasons=sorted({row.season for row in comparisons}),
        verdicts=sorted({row.replay_verdict for row in comparisons}),
        missing_model_count=sum(1 for row in comparisons if row.model_rank is None),
        review_warning=(
            "Historical replay is calibration-only. It must use as-of draft data "
            "and must not feed current rankings directly."
        ),
    )


def extract_final_picks_as_rookie_drafts(
    picks: list[PlatformDraftPick],
    *,
    rookie_pick_count: int = ROOKIE_DRAFT_PICK_COUNT,
) -> list[HistoricalRookieDraftEntry]:
    picks_by_season: dict[int, list[PlatformDraftPick]] = defaultdict(list)
    for pick in picks:
        picks_by_season[pick.season].append(pick)

    entries: list[HistoricalRookieDraftEntry] = []
    for season in sorted(picks_by_season):
        ordered_picks = sorted(
            picks_by_season[season],
            key=lambda pick: (pick.overall_pick, pick.round, pick.slot, pick.row_number),
        )
        final_picks = ordered_picks[-rookie_pick_count:]
        for rookie_pick_number, pick in enumerate(final_picks, start=1):
            entries.append(_rookie_entry(rookie_pick_number, pick))
    return entries


def _load_offline_rookie_note_entries(path: str | Path) -> list[HistoricalRookieDraftEntry]:
    csv_path = Path(path)
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing_columns = [
            column
            for column in REQUIRED_OFFLINE_NOTE_COLUMNS
            if column not in (reader.fieldnames or ())
        ]
        if missing_columns:
            raise ValueError(
                "Missing offline rookie note columns: "
                + ", ".join(missing_columns)
                + "."
            )
        entries = [
            _offline_note_entry(row, row_number)
            for row_number, row in enumerate(reader, start=2)
        ]
    return sorted(
        entries,
        key=lambda entry: (entry.season, entry.rookie_pick_number, entry.drafted_player),
    )


def _yahoo_pick_from_row(row: dict[str, str], row_number: int) -> PlatformDraftPick:
    return PlatformDraftPick(
        season=_required_int(row, "season", row_number),
        overall_pick=_required_int(row, "overall_pick", row_number),
        round=_required_int(row, "round", row_number),
        slot=_required_int(row, "slot", row_number),
        team=_required_text(row, "team", row_number),
        player=_required_text(row, "player", row_number),
        position=_required_text(row, "position", row_number),
        source=_required_text(row, "source", row_number),
        row_number=row_number,
    )


def _rookie_entry(
    rookie_pick_number: int, pick: PlatformDraftPick
) -> HistoricalRookieDraftEntry:
    return HistoricalRookieDraftEntry(
        season=pick.season,
        rookie_pick_number=rookie_pick_number,
        platform_overall_pick=pick.overall_pick,
        drafted_player=pick.player,
        drafting_team=pick.team,
        position=pick.position,
        confidence=ROOKIE_CONFIDENCE,
        provenance_note=ROOKIE_PROVENANCE_NOTE,
        needs_traded_pick_review=True,
        source=pick.source,
    )


def _offline_note_entry(
    row: dict[str, str], row_number: int
) -> HistoricalRookieDraftEntry:
    return HistoricalRookieDraftEntry(
        season=_required_int(row, "season", row_number),
        rookie_pick_number=_required_int(row, "rookie_pick_number", row_number),
        platform_overall_pick=None,
        drafted_player=_required_text(row, "player", row_number),
        drafting_team=_required_text(row, "team", row_number),
        position=_required_text(row, "position", row_number),
        confidence=_optional_text(row, "confidence") or OFFLINE_NOTE_CONFIDENCE,
        provenance_note=_optional_text(row, "provenance_note")
        or OFFLINE_NOTE_PROVENANCE_NOTE,
        needs_traded_pick_review=_optional_bool(row, "needs_traded_pick_review", True),
        source=_required_text(row, "source", row_number),
    )


def _model_replay_entry(
    row: dict[str, str], row_number: int
) -> HistoricalRookieModelReplay:
    return HistoricalRookieModelReplay(
        season=_required_int(row, "season", row_number),
        player=_required_text(row, "player", row_number),
        position=_required_text(row, "position", row_number),
        model_rank=_required_int(row, "model_rank", row_number),
        model_score=_required_float(row, "model_score", row_number),
        model_recommendation=_required_text(row, "model_recommendation", row_number),
        outcome_label=_optional_text(row, "outcome_label") or "unknown",
        outcome_score=_optional_float(row, "outcome_score", row_number),
        source=_required_text(row, "source", row_number),
        row_number=row_number,
    )


def _comparison_row(
    actual: HistoricalRookieDraftEntry,
    replay: HistoricalRookieModelReplay | None,
) -> HistoricalReplayComparison:
    if replay is None:
        return HistoricalReplayComparison(
            season=actual.season,
            rookie_pick_number=actual.rookie_pick_number,
            drafted_player=actual.drafted_player,
            drafting_team=actual.drafting_team,
            position=actual.position,
            model_rank=None,
            model_score=None,
            model_recommendation="missing",
            outcome_label="unknown",
            outcome_score=None,
            rank_delta=None,
            replay_verdict="missing_model_replay",
            calibration_note="Add an as-of model replay row before judging this pick.",
            confidence=actual.confidence,
            source=actual.source,
        )

    rank_delta = replay.model_rank - actual.rookie_pick_number
    verdict = _replay_verdict(rank_delta, replay.outcome_score)
    return HistoricalReplayComparison(
        season=actual.season,
        rookie_pick_number=actual.rookie_pick_number,
        drafted_player=actual.drafted_player,
        drafting_team=actual.drafting_team,
        position=actual.position,
        model_rank=replay.model_rank,
        model_score=round(replay.model_score, 2),
        model_recommendation=replay.model_recommendation,
        outcome_label=replay.outcome_label,
        outcome_score=(
            round(replay.outcome_score, 2)
            if replay.outcome_score is not None
            else None
        ),
        rank_delta=rank_delta,
        replay_verdict=verdict,
        calibration_note=_calibration_note(verdict, rank_delta),
        confidence=actual.confidence,
        source=f"{actual.source}|{replay.source}",
    )


def _replay_verdict(rank_delta: int, outcome_score: float | None) -> str:
    if outcome_score is None:
        if abs(rank_delta) <= 1:
            return "rank_aligned_needs_outcome"
        return "rank_gap_needs_outcome"
    if rank_delta < -1 and outcome_score >= 70:
        return "model_found_value"
    if rank_delta > 1 and outcome_score < 50:
        return "model_correctly_faded"
    if rank_delta > 1 and outcome_score >= 70:
        return "model_missed_hit"
    if rank_delta < -1 and outcome_score < 50:
        return "model_overrated_miss"
    return "model_aligned"


def _calibration_note(verdict: str, rank_delta: int | None) -> str:
    if verdict == "missing_model_replay":
        return "No comparison until the historical model score is supplied."
    if rank_delta is None:
        return "No rank delta available."
    if verdict == "model_found_value":
        return "Model ranked this player earlier than the room and outcome supported it."
    if verdict == "model_correctly_faded":
        return "Model ranked this player later than the room and outcome supported caution."
    if verdict == "model_missed_hit":
        return "Model ranked this player too low despite a strong later outcome."
    if verdict == "model_overrated_miss":
        return "Model ranked this player too high despite a weak later outcome."
    if rank_delta == 0:
        return "Model matched the actual draft slot."
    if rank_delta > 0:
        return "Model was lower than the actual draft room."
    return "Model was higher than the actual draft room."


def _match_key(season: int, player: str) -> tuple[int, str]:
    cleaned = "".join(character.lower() for character in player if character.isalnum())
    return season, cleaned


def _required_int(row: dict[str, str], column: str, row_number: int) -> int:
    text = _required_text(row, column, row_number)
    try:
        return int(text)
    except ValueError as exc:
        raise ValueError(
            f"Historical draft row {row_number} has non-integer {column}."
        ) from exc


def _required_float(row: dict[str, str], column: str, row_number: int) -> float:
    text = _required_text(row, column, row_number)
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(
            f"Historical draft row {row_number} has non-numeric {column}."
        ) from exc


def _required_text(row: dict[str, str], column: str, row_number: int) -> str:
    value = (row.get(column) or "").strip()
    if not value:
        raise ValueError(f"Historical draft row {row_number} is missing {column}.")
    return value


def _optional_text(row: dict[str, str], column: str) -> str | None:
    value = (row.get(column) or "").strip()
    return value or None


def _optional_float(
    row: dict[str, str], column: str, row_number: int
) -> float | None:
    value = _optional_text(row, column)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(
            f"Historical draft row {row_number} has non-numeric {column}."
        ) from exc


def _optional_bool(row: dict[str, str], column: str, default: bool) -> bool:
    value = _optional_text(row, column)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "y"}
