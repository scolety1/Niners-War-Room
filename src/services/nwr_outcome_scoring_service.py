from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCORING_VERSION_ID = "nwr_1qb_nonppr_fd_v1"
DEFAULT_SCORING_CONFIG_PATH = Path("config/nwr_scoring_rules_nwr_1qb_nonppr_fd_v1.json")
QUALIFIED_GAMES_MIN = 8
MODELED_POSITIONS = ("QB", "RB", "WR", "TE")
FLEX_POSITIONS = ("RB", "WR", "TE")
REQUIRED_STARTERS = {"QB": 10, "RB": 20, "WR": 30, "TE": 10}
FLEX_STARTERS = 20

FORBIDDEN_INPUT_FIELDS = (
    "adp",
    "fantasypros",
    "public_rank",
    "public_projection",
    "consensus",
    "startup",
    "dynasty_rank",
    "trade_calculator",
    "market_rank",
    "league_rank",
    "rotowire_projection",
    "rotowire_ranking",
    "rotowire_outlook",
    "rotowire_value",
    "prior_draft_history",
    "prior_fantasy_draft_history",
    "acquisition_cost",
    "legacy_private_score",
    "private_score",
    "hindsight_note",
)

FINISH_BANDS = {
    "QB": (6, 12, 18, 24),
    "RB": (6, 12, 24, 36, 48),
    "WR": (6, 12, 24, 36, 48),
    "TE": (3, 6, 12, 18, 24),
}

APP_TIER_THRESHOLDS = {
    "QB": {"difference_maker": 6, "starter": 12, "useful": 18},
    "RB": {"difference_maker": 12, "starter": 24, "useful": 36},
    "WR": {"difference_maker": 12, "starter": 24, "useful": 36},
    "TE": {"difference_maker": 3, "starter": 6, "useful": 12},
}


@dataclass(frozen=True)
class ScoringRules:
    scoring_version_id: str = SCORING_VERSION_ID
    pass_yd_pt: float = 1 / 30
    pass_td_pt: float = 3.0
    pass_int_pt: float = -1.0
    pass_1d_pt: float = 0.0
    pass_2pt_pt: float = 2.0
    sack_suffered_pt: float = 0.0
    carry_pt: float = 0.0
    rush_yd_pt: float = 0.1
    rush_td_pt: float = 4.0
    rush_1d_pt: float = 0.4
    rush_2pt_pt: float = 2.0
    rec_pt: float = 0.0
    rec_yd_pt: float = 0.1
    rec_td_pt: float = 4.0
    rec_1d_pt: float = 0.4
    rec_2pt_pt: float = 2.0
    fumble_lost_pt: float = -1.0
    return_yd_pt: float = 1 / 30
    return_td_pt: float = 4.0
    special_td_pt: float = 4.0
    fumble_recovery_td_pt: float = 4.0
    misc_yd_pt: float = 0.0
    qualified_games_min: int = QUALIFIED_GAMES_MIN


def load_scoring_rules(path: str | Path = DEFAULT_SCORING_CONFIG_PATH) -> ScoringRules:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    scoring = payload.get("scoring", {})
    qualified = payload.get("qualified_ppg", {})
    return ScoringRules(
        scoring_version_id=str(payload.get("scoring_version_id", SCORING_VERSION_ID)),
        qualified_games_min=int(qualified.get("min_games", QUALIFIED_GAMES_MIN)),
        **{key: float(value) for key, value in scoring.items() if hasattr(ScoringRules, key)},
    )


def score_player_week(
    row: Mapping[str, Any],
    rules: ScoringRules | None = None,
) -> dict[str, float | str]:
    rules = rules or ScoringRules()
    pts_passing = (
        _number(row, "pass_yds", "passing_yards") * rules.pass_yd_pt
        + _number(row, "pass_td", "passing_tds") * rules.pass_td_pt
        + _number(row, "pass_int", "interceptions") * rules.pass_int_pt
        + _number(row, "pass_first_downs", "passing_first_downs") * rules.pass_1d_pt
        + _number(row, "pass_2pt", "passing_2pt") * rules.pass_2pt_pt
        + _number(row, "sacks_suffered") * rules.sack_suffered_pt
    )
    pts_rushing = (
        _number(row, "carries", "rush_att") * rules.carry_pt
        + _number(row, "rush_yds", "rushing_yards") * rules.rush_yd_pt
        + _number(row, "rush_td", "rushing_tds") * rules.rush_td_pt
        + _number(row, "rush_first_downs", "rushing_first_downs") * rules.rush_1d_pt
        + _number(row, "rush_2pt", "rushing_2pt") * rules.rush_2pt_pt
    )
    pts_receiving = (
        _number(row, "receptions", "rec") * rules.rec_pt
        + _number(row, "rec_yds", "receiving_yards") * rules.rec_yd_pt
        + _number(row, "rec_td", "receiving_tds") * rules.rec_td_pt
        + _number(row, "rec_first_downs", "receiving_first_downs") * rules.rec_1d_pt
        + _number(row, "rec_2pt", "receiving_2pt") * rules.rec_2pt_pt
    )
    pts_turnovers = _number(row, "fumbles_lost", "fumble_lost") * rules.fumble_lost_pt
    pts_misc = (
        _number(row, "return_yds", "return_yards") * rules.return_yd_pt
        + _number(row, "return_td", "return_tds") * rules.return_td_pt
        + _number(row, "special_td", "special_tds") * rules.special_td_pt
        + _number(row, "fumble_recovery_td", "fumble_recovery_tds")
        * rules.fumble_recovery_td_pt
        + _number(row, "misc_yds", "misc_yards") * rules.misc_yd_pt
    )
    total = pts_passing + pts_rushing + pts_receiving + pts_turnovers + pts_misc
    return {
        "scoring_version_id": rules.scoring_version_id,
        "pts_passing": round(pts_passing, 4),
        "pts_rushing": round(pts_rushing, 4),
        "pts_receiving": round(pts_receiving, 4),
        "pts_turnovers": round(pts_turnovers, 4),
        "pts_misc": round(pts_misc, 4),
        "week_score_total": round(total, 4),
    }


def aggregate_season_scores(
    week_rows: list[Mapping[str, Any]],
    *,
    qualified_games_min: int = QUALIFIED_GAMES_MIN,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in week_rows:
        if not _bool(row.get("include_in_scoring"), default=True):
            continue
        position = _position(row)
        if position not in MODELED_POSITIONS:
            continue
        key = (
            str(row.get("scoring_version_id") or SCORING_VERSION_ID),
            str(row.get("season", "")),
            _player_id(row),
            position,
        )
        grouped[key].append(row)

    output: list[dict[str, Any]] = []
    for key, rows in grouped.items():
        scoring_version_id, season, player_id, position = key
        total = sum(_score(row) for row in rows)
        ppg_games = sum(1 for row in rows if _bool(row.get("ppg_game_eligible"), default=True))
        qualified_ppg = round(total / ppg_games, 4) if ppg_games >= qualified_games_min else None
        output.append(
            {
                "scoring_version_id": scoring_version_id,
                "season": season,
                "player_id": player_id,
                "player_name": _player_name(rows[0]),
                "fantasy_position": position,
                "ppg_game_count": ppg_games,
                "qualified_games_min": qualified_games_min,
                "season_total_score": round(total, 4),
                "qualified_ppg": qualified_ppg,
            }
        )
    return output


def duplicate_player_week_keys(week_rows: list[Mapping[str, Any]]) -> tuple[str, ...]:
    seen: set[tuple[str, str, str, str]] = set()
    duplicates: list[str] = []
    for row in week_rows:
        key = (
            str(row.get("scoring_version_id") or SCORING_VERSION_ID),
            str(row.get("season", "")),
            str(row.get("week", "")),
            _player_id(row),
        )
        if key in seen:
            duplicates.append("|".join(key))
        else:
            seen.add(key)
    return tuple(duplicates)


def add_position_ranks(
    season_rows: list[Mapping[str, Any]],
    *,
    value_column: str,
    rank_column: str,
) -> list[dict[str, Any]]:
    output = [dict(row) for row in season_rows]
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in output:
        groups[(str(row.get("season", "")), _position(row))].append(row)

    for rows in groups.values():
        ranked = sorted(
            rows,
            key=lambda row: (
                -_ranking_value(row.get(value_column)),
                str(row.get("player_name") or row.get("player_id", "")),
            ),
        )
        last_value: float | None = None
        last_rank = 0
        for index, row in enumerate(ranked, start=1):
            value = _optional_float(row.get(value_column))
            if value is None:
                row[rank_column] = None
                continue
            if last_value is None or value != last_value:
                last_rank = index
                last_value = value
            row[rank_column] = last_rank
    return output


def finish_flags(
    position: str,
    *,
    total_rank: int | None = None,
    qualified_ppg_rank: int | None = None,
) -> dict[str, bool]:
    position = position.upper()
    output: dict[str, bool] = {}
    for band in FINISH_BANDS.get(position, ()):
        output[f"total_top_{band}"] = bool(total_rank and total_rank <= band)
        output[f"qppg_top_{band}"] = bool(qualified_ppg_rank and qualified_ppg_rank <= band)
    return output


def app_tier_labels(
    position: str,
    *,
    total_rank: int | None = None,
    qualified_ppg_rank: int | None = None,
) -> dict[str, bool]:
    position = position.upper()
    best_rank = _best_rank(total_rank, qualified_ppg_rank)
    thresholds = APP_TIER_THRESHOLDS.get(position)
    if best_rank is None or thresholds is None:
        return {"is_difference_maker": False, "is_starter": False, "is_useful": False}
    is_difference_maker = best_rank <= thresholds["difference_maker"]
    is_starter = is_difference_maker or best_rank <= thresholds["starter"]
    is_useful = is_starter or best_rank <= thresholds["useful"]
    return {
        "is_difference_maker": is_difference_maker,
        "is_starter": is_starter,
        "is_useful": is_useful,
    }


def companion_labels(
    *,
    opportunity_evidence: bool,
    injury_lost: bool = False,
    ambiguous: bool = False,
    useful: bool = False,
    replacement_level: bool = False,
) -> dict[str, bool | str]:
    if injury_lost:
        return {
            "is_injury_lost": True,
            "is_ambiguous": False,
            "is_replacement_level": False,
            "is_bust": False,
            "label_status": "injury_lost_supersedes_bust",
        }
    if ambiguous:
        return {
            "is_injury_lost": False,
            "is_ambiguous": True,
            "is_replacement_level": False,
            "is_bust": False,
            "label_status": "ambiguous_supersedes_bust",
        }
    is_replacement_level = bool(replacement_level and not useful)
    is_bust = bool(opportunity_evidence and not useful and not is_replacement_level)
    return {
        "is_injury_lost": False,
        "is_ambiguous": False,
        "is_replacement_level": is_replacement_level,
        "is_bust": is_bust,
        "label_status": "computed",
    }


def future_window_label(
    *,
    anchor_season: int,
    latest_observed_season: int,
    window_years: int,
    observed_value: bool | None,
) -> bool | None:
    if latest_observed_season < anchor_season + window_years:
        return None
    return observed_value


def compute_weekly_replacement_lines(
    week_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in week_rows:
        if not _bool(row.get("include_in_scoring"), default=True):
            continue
        position = _position(row)
        if position in MODELED_POSITIONS:
            groups[
                (
                    str(row.get("scoring_version_id") or SCORING_VERSION_ID),
                    str(row.get("season", "")),
                    str(row.get("week", "")),
                )
            ].append(row)

    output: list[dict[str, Any]] = []
    for key, rows in groups.items():
        scoring_version_id, season, week = key
        selected_required: dict[str, set[str]] = {}
        required_lines: dict[str, dict[str, float | int | None]] = {}
        for position, count in REQUIRED_STARTERS.items():
            ranked = _rank_week_rows([row for row in rows if _position(row) == position])
            selected_required[position] = {_player_id(row) for row in ranked[:count]}
            required_lines[position] = {
                "line": _nth_score(ranked, count),
                "next": _nth_score(ranked, count + 1),
            }

        flex_candidates = [
            row
            for row in rows
            if _position(row) in FLEX_POSITIONS
            and _player_id(row) not in selected_required[_position(row)]
        ]
        flex_ranked = _rank_week_rows(flex_candidates)
        flex_selected = flex_ranked[:FLEX_STARTERS]
        flex_selected_ids = {_player_id(row) for row in flex_selected}
        flex_cut_score = _nth_score(flex_ranked, FLEX_STARTERS)

        for position in MODELED_POSITIONS:
            final_selected = [
                row
                for row in rows
                if _position(row) == position
                and (
                    _player_id(row) in selected_required[position]
                    or _player_id(row) in flex_selected_ids
                )
            ]
            selected_scores = [_score(row) for row in final_selected]
            final_line = (
                min(selected_scores) if selected_scores else required_lines[position]["line"]
            )
            non_selected_scores = [
                _score(row)
                for row in rows
                if _position(row) == position and row not in final_selected
            ]
            output.append(
                {
                    "scoring_version_id": scoring_version_id,
                    "season": season,
                    "week": week,
                    "position": position,
                    "include_in_scoring": True,
                    "required_slots_nominal": REQUIRED_STARTERS[position],
                    "required_line_score": _blank(required_lines[position]["line"]),
                    "required_next_up_score": _blank(required_lines[position]["next"]),
                    "flex_global_cut_score": _blank(flex_cut_score),
                    "flex_selected_count_position": sum(
                        1 for row in flex_selected if _position(row) == position
                    ),
                    "final_started_count_position": len(final_selected),
                    "final_replacement_line_score": _blank(final_line),
                    "final_next_up_score": _blank(max(non_selected_scores, default=None)),
                    "cutoff_tie_count": _tie_count(
                        [row for row in rows if _position(row) == position],
                        final_line,
                    ),
                    "data_quality_code": "computed_threshold_line",
                }
            )
    return output


def forbidden_input_violations(field_names: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    normalized = "|".join(field.lower() for field in field_names)
    return tuple(fragment for fragment in FORBIDDEN_INPUT_FIELDS if fragment in normalized)


def _rank_week_rows(rows: list[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return sorted(rows, key=lambda row: (-_score(row), _player_id(row)))


def _nth_score(rows: list[Mapping[str, Any]], n: int) -> float | None:
    if n <= 0 or len(rows) < n:
        return None
    return _score(rows[n - 1])


def _tie_count(rows: list[Mapping[str, Any]], threshold: float | int | None) -> int:
    if threshold is None:
        return 0
    return sum(1 for row in rows if _score(row) == float(threshold))


def _best_rank(*ranks: int | None) -> int | None:
    available = [rank for rank in ranks if rank is not None]
    return min(available) if available else None


def _ranking_value(value: object) -> float:
    parsed = _optional_float(value)
    return parsed if parsed is not None else float("-inf")


def _score(row: Mapping[str, Any]) -> float:
    return _number(row, "week_score_total", "score", "points")


def _position(row: Mapping[str, Any]) -> str:
    return str(row.get("fantasy_position") or row.get("position") or "").upper()


def _player_id(row: Mapping[str, Any]) -> str:
    return str(row.get("player_id") or row.get("player_name") or row.get("player") or "")


def _player_name(row: Mapping[str, Any]) -> str:
    return str(row.get("player_name") or row.get("player") or row.get("player_id") or "")


def _number(row: Mapping[str, Any], *keys: str) -> float:
    for key in keys:
        parsed = _optional_float(row.get(key))
        if parsed is not None:
            return parsed
    return 0.0


def _optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bool(value: object, *, default: bool = False) -> bool:
    if value in (None, ""):
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _blank(value: object) -> object:
    return "" if value is None else round(float(value), 4)
