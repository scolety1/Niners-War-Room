from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack

DEFAULT_ROTOWIRE_DYNASTY_ADP_PATH = Path(
    "local_exports/model_v4/raw_user_exports/rotowire_manual/2026/"
    "market_context/rotowire_early_adp_all.csv"
)

MODEL_HIGH_THRESHOLD = 65.0
MODEL_LOW_THRESHOLD = 40.0
MARKET_LOW_THRESHOLD = 35.0
MARKET_HIGH_THRESHOLD = 75.0
MARKET_DISPLAY_ALLOWED_USE = "display_only_market_context_review"
MARKET_DISPLAY_BLOCKED_USE = (
    "primary_review_score|private_value_inputs|decision_inputs|review_label|"
    "review_band|trade_label|pick_label|default_sort"
)


@dataclass(frozen=True)
class MarketGapReport:
    rows: list[dict[str, object]]
    trade_for_rows: list[dict[str, object]]
    trade_away_rows: list[dict[str, object]]
    issues: list[str]
    source_summary: dict[str, object]


def build_market_gap_report(
    data_pack_path: str | Path,
    *,
    adp_path: str | Path = DEFAULT_ROTOWIRE_DYNASTY_ADP_PATH,
    team_id: str = "niners",
) -> MarketGapReport:
    validated = validate_data_pack(data_pack_path)
    if validated.has_errors:
        return MarketGapReport(
            rows=[],
            trade_for_rows=[],
            trade_away_rows=[],
            issues=["Data pack validation errors block market-gap review."],
            source_summary={},
        )

    rows_by_table = validated.rows_by_table
    roster_lookup = _by_player_id(rows_by_table.get("rosters", []))
    ranking_lookup = _by_player_id(rows_by_table.get("official_rankings", []))
    dim_lookup = _by_player_id(rows_by_table.get("players", []))
    model_rows = rows_by_table.get("model_outputs", [])
    resolved_team_id = _resolve_team_id(
        rows_by_table.get("rosters", []),
        team_id,
    )

    adp_rows, adp_issues = load_dynasty_adp_rows(adp_path)
    adp_lookup = _adp_lookup(adp_rows)
    max_league_rank = _max_rank(
        _first_number(row, "league_rank", "official_rank")
        for row in rows_by_table.get("official_rankings", [])
    )
    max_adp = _max_rank(row["dynasty_startup_adp"] for row in adp_rows)

    rows = [
        _market_gap_row(
            model_row,
            roster_lookup=roster_lookup,
            ranking_lookup=ranking_lookup,
            dim_lookup=dim_lookup,
            adp_lookup=adp_lookup,
            max_league_rank=max_league_rank,
            max_adp=max_adp,
            resolved_team_id=resolved_team_id,
        )
        for model_row in model_rows
        if model_row.get("player_id")
    ]
    rows = sorted(
        rows,
        key=lambda row: (
            _hint_sort(str(row["application_hint"])),
            -abs(float(row["model_vs_reference_gap"] or 0.0)),
            str(row["player"]),
        ),
    )
    return MarketGapReport(
        rows=rows,
        trade_for_rows=[
            row
            for row in rows
            if row["application_hint"] == "opponent_roster_model_gap_context_review"
        ],
        trade_away_rows=[
            row
            for row in rows
            if row["application_hint"] == "my_roster_market_premium_context_review"
        ],
        issues=adp_issues,
        source_summary={
            "league_rank_rows": len(rows_by_table.get("official_rankings", [])),
            "adp_rows": len(adp_rows),
            "max_league_rank": max_league_rank,
            "max_dynasty_startup_adp": max_adp,
            "adp_source": str(adp_path),
            "allowed_use": MARKET_DISPLAY_ALLOWED_USE,
            "blocked_use": MARKET_DISPLAY_BLOCKED_USE,
            "market_display_only": True,
        },
    )


def normalize_rank_score(rank: object, max_rank: object) -> float | None:
    """Convert an ordinal rank or ADP to 0-100, where rank/adp 1.0 is 100."""
    rank_number = _to_float(rank)
    max_number = _to_float(max_rank)
    if rank_number is None or max_number is None:
        return None
    if max_number <= 1:
        return 100.0
    score = 100.0 * ((max_number - rank_number) / (max_number - 1.0))
    return round(max(0.0, min(100.0, score)), 2)


def load_dynasty_adp_rows(
    adp_path: str | Path,
) -> tuple[list[dict[str, object]], list[str]]:
    path = Path(adp_path)
    if not path.exists():
        return [], [f"ADP source missing: {path}"]

    rows: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        all_rows = list(reader)
    if len(all_rows) < 3:
        return [], [f"ADP source has too few rows: {path}"]

    for raw in all_rows[2:]:
        if len(raw) < 9:
            continue
        player = raw[1].strip()
        if not player or player.lower() == "name":
            continue
        dynasty_sleeper = _to_float(raw[7])
        dynasty_mfl = _to_float(raw[8])
        redraft_sleeper = _to_float(raw[5])
        adp_value = _first_not_none(dynasty_sleeper, dynasty_mfl, redraft_sleeper)
        if adp_value is None:
            continue
        rows.append(
            {
                "player": player,
                "normalized_name": _normalize_name(player),
                "team": raw[2].strip(),
                "position": raw[3].strip(),
                "dynasty_startup_adp": adp_value,
                "dynasty_sleeper_adp": dynasty_sleeper,
                "dynasty_mfl_adp": dynasty_mfl,
                "source": "RotoWire early ADP all",
                "source_file": str(path),
            }
        )
    return rows, []


def _market_gap_row(
    model_row: dict[str, object],
    *,
    roster_lookup: dict[str, dict[str, object]],
    ranking_lookup: dict[str, dict[str, object]],
    dim_lookup: dict[str, dict[str, object]],
    adp_lookup: dict[tuple[str, str], dict[str, object]],
    max_league_rank: float | None,
    max_adp: float | None,
    resolved_team_id: str,
) -> dict[str, object]:
    player_id = str(model_row.get("player_id") or "")
    roster_row = roster_lookup.get(player_id, {})
    ranking_row = ranking_lookup.get(player_id, {})
    dim_row = dim_lookup.get(player_id, {})
    player = str(
        model_row.get("player_name")
        or ranking_row.get("player_name")
        or dim_row.get("player_name")
        or player_id
    )
    position = str(
        model_row.get("position")
        or ranking_row.get("position")
        or dim_row.get("position")
        or ""
    )
    league_rank = _first_number(ranking_row, "league_rank", "official_rank")
    if league_rank is None:
        league_rank = _first_number(roster_row, "league_rank", "official_rank")
    model_value = _first_number(
        model_row,
        "private_score",
        "private_lve_value",
        "veteran_base_value",
    )
    adp_row = adp_lookup.get((_normalize_name(player), position.upper()))
    if adp_row is None:
        adp_row = adp_lookup.get((_normalize_name(player), ""))
    adp_value = adp_row.get("dynasty_startup_adp") if adp_row else None
    league_score = normalize_rank_score(league_rank, max_league_rank)
    adp_score = normalize_rank_score(adp_value, max_adp)
    reference_score = _market_reference_score(league_score, adp_score)
    gap = (
        round(float(model_value) - reference_score, 2)
        if model_value is not None and reference_score is not None
        else None
    )
    owner_side = _owner_side(roster_row, resolved_team_id)
    application_hint = _application_hint(
        owner_side=owner_side,
        model_value=model_value,
        league_score=league_score,
        adp_score=adp_score,
        reference_score=reference_score,
        gap=gap,
    )
    warnings = _warnings(
        league_score=league_score,
        adp_score=adp_score,
        model_value=model_value,
        adp_row=adp_row,
    )
    return {
        "player_id": player_id,
        "player": player,
        "position": position,
        "nfl_team": model_row.get("nfl_team") or ranking_row.get("nfl_team") or "",
        "owner_team": roster_row.get("team_name", ""),
        "owner_side": owner_side,
        "model_value": round(float(model_value), 2) if model_value is not None else "",
        "league_rank": league_rank if league_rank is not None else "",
        "league_rank_normalized_score": league_score if league_score is not None else "",
        "dynasty_startup_adp": adp_value if adp_value is not None else "",
        "adp_normalized_score": adp_score if adp_score is not None else "",
        "market_reference_score": (
            round(reference_score, 2) if reference_score is not None else ""
        ),
        "model_vs_reference_gap": round(gap, 2) if gap is not None else "",
        "application_hint": application_hint,
        "disagreement_band": _disagreement_band(gap),
        "market_display_only": True,
        "primary_review_score": "",
        "review_label": "",
        "allowed_use": MARKET_DISPLAY_ALLOWED_USE,
        "blocked_use": MARKET_DISPLAY_BLOCKED_USE,
        "warning_flags": "|".join(warnings),
        "adp_source": adp_row.get("source", "") if adp_row else "",
    }


def _market_reference_score(
    league_score: float | None,
    adp_score: float | None,
) -> float | None:
    values = [value for value in (league_score, adp_score) if value is not None]
    if not values:
        return None
    return sum(values) / len(values)


def _application_hint(
    *,
    owner_side: str,
    model_value: float | None,
    league_score: float | None,
    adp_score: float | None,
    reference_score: float | None,
    gap: float | None,
) -> str:
    if model_value is None or reference_score is None or gap is None:
        return "missing_inputs_review"
    if league_score is None or adp_score is None:
        return "partial_market_context_review"
    both_market_low = _is_low(league_score) and _is_low(adp_score)
    both_market_high = _is_high(league_score) and _is_high(adp_score)
    model_high = model_value >= MODEL_HIGH_THRESHOLD
    model_low = model_value <= MODEL_LOW_THRESHOLD
    if owner_side == "opponent_roster" and model_high and both_market_low:
        return "opponent_roster_model_gap_context_review"
    if owner_side == "my_roster" and model_low and both_market_high:
        return "my_roster_market_premium_context_review"
    if owner_side == "my_roster" and model_high and both_market_low:
        return "my_roster_model_gap_context_review"
    if owner_side == "opponent_roster" and model_low and both_market_high:
        return "opponent_roster_market_premium_context_review"
    if gap >= 15:
        return "model_higher_market_context_review"
    if gap <= -15:
        return "market_higher_model_context_review"
    return "roughly_aligned_review"


def _disagreement_band(gap: float | None) -> str:
    if gap is None:
        return "missing_inputs"
    if gap >= 25:
        return "major_model_higher"
    if gap >= 15:
        return "model_higher"
    if gap <= -25:
        return "major_market_higher"
    if gap <= -15:
        return "market_higher"
    return "near_aligned"


def _warnings(
    *,
    league_score: float | None,
    adp_score: float | None,
    model_value: float | None,
    adp_row: dict[str, object] | None,
) -> list[str]:
    warnings = ["review_only_no_trade_recommendation"]
    if model_value is None:
        warnings.append("missing_model_value")
    if league_score is None:
        warnings.append("missing_league_rank_normalized_score")
    if adp_score is None:
        warnings.append("missing_adp_normalized_score")
    if adp_row is None:
        warnings.append("no_direct_adp_match")
    if league_score is not None or adp_score is not None:
        warnings.append("market_context_excluded_from_private_value")
    return warnings


def _adp_lookup(rows: list[dict[str, object]]) -> dict[tuple[str, str], dict[str, object]]:
    lookup: dict[tuple[str, str], dict[str, object]] = {}
    name_counts: dict[str, int] = {}
    for row in rows:
        name = str(row["normalized_name"])
        name_counts[name] = name_counts.get(name, 0) + 1
    for row in rows:
        name = str(row["normalized_name"])
        position = str(row.get("position") or "").upper()
        lookup[(name, position)] = row
        if name_counts.get(name, 0) == 1:
            lookup[(name, "")] = row
    return lookup


def _owner_side(roster_row: dict[str, object], resolved_team_id: str) -> str:
    if not roster_row:
        return "unknown_owner"
    return (
        "my_roster"
        if str(roster_row.get("team_id") or "") == resolved_team_id
        else "opponent_roster"
    )


def _resolve_team_id(rows: list[dict[str, object]], requested_team_id: str) -> str:
    if any(str(row.get("team_id") or "") == requested_team_id for row in rows):
        return requested_team_id
    normalized = _normalize_name(requested_team_id)
    for row in rows:
        team_id = str(row.get("team_id") or "")
        team_name = str(row.get("team_name") or "")
        if _normalize_name(team_name) == normalized:
            return team_id
    return requested_team_id


def _by_player_id(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {
        str(row.get("player_id")): row
        for row in rows
        if row.get("player_id") not in {None, ""}
    }


def _max_rank(values: Iterable[object]) -> float | None:
    numbers = [_to_float(value) for value in values]
    numbers = [value for value in numbers if value is not None]
    return max(numbers) if numbers else None


def _first_number(row: dict[str, object], *keys: str) -> float | None:
    for key in keys:
        value = _to_float(row.get(key))
        if value is not None:
            return value
    return None


def _to_float(value: object) -> float | None:
    if value in {None, "", "-"}:
        return None
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _first_not_none(*values: float | None) -> float | None:
    return next((value for value in values if value is not None), None)


def _normalize_name(value: object) -> str:
    text = str(value or "").lower()
    suffixes = {"jr", "sr", "ii", "iii", "iv", "v"}
    parts = [
        "".join(character for character in part if character.isalnum())
        for part in text.replace(".", " ").replace("'", "").split()
    ]
    parts = [part for part in parts if part and part not in suffixes]
    return "".join(parts)


def _is_low(value: float | None) -> bool:
    return value is not None and value <= MARKET_LOW_THRESHOLD


def _is_high(value: float | None) -> bool:
    return value is not None and value >= MARKET_HIGH_THRESHOLD


def _hint_sort(hint: str) -> int:
    order = {
        "opponent_roster_model_gap_context_review": 0,
        "my_roster_market_premium_context_review": 1,
        "my_roster_model_gap_context_review": 2,
        "opponent_roster_market_premium_context_review": 3,
        "model_higher_market_context_review": 4,
        "market_higher_model_context_review": 5,
        "roughly_aligned_review": 6,
        "missing_inputs_review": 7,
        "partial_market_context_review": 8,
    }
    return order.get(hint, 99)
