from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal

import pandas as pd

from src.services.draft_day_runtime_state_service import parse_trade_assets

NOT_ENOUGH_INFORMATION = "Not enough information"
EXPECTED_TRADE_PLAYER_UNIVERSE_ROWS = 240
APPROVED_POOL_STATUSES = frozenset({"MY TEAM", "OTHER TEAM"})
Side = Literal["give", "get"]
TradeState = dict[str, list[str]]

PLAYER_PREFIX = "player:"
PICK_CONTEXT_PREFIX = "pick_context:"

DISPLAY_ITEM_COLUMNS = (
    "side",
    "asset_type",
    "label",
    "nwr_player_id",
    "player",
    "position",
    "nfl_team",
    "roster_context",
    "rank_source",
    "dynasty_rank",
    "final_board_rank",
    "final_tier",
    "tier_movement_note",
    "position_scarcity_note",
    "pick_window_note",
    "risk_manual_review_notes",
    "data_status",
)

DISPLAY_SUMMARY_COLUMNS = (
    "side",
    "asset_count",
    "player_count",
    "pick_context_count",
    "best_rank",
    "top_tier",
    "tier_movement",
    "scarcity",
    "pick_context",
    "risk_notes",
)


@dataclass(frozen=True)
class TradeReview:
    status: str
    missing_context_display: str
    rank_context: str
    explanation: str


class TradePlayerUniverseError(ValueError):
    """Raised when Trading Lab is given a non-canonical player universe."""


def empty_trade_state() -> TradeState:
    return {"give": [], "get": []}


def normalize_trade_state(state: Any) -> TradeState:
    if not isinstance(state, dict):
        return empty_trade_state()
    normalized: TradeState = {"give": [], "get": []}
    for side in ("give", "get"):
        values = state.get(side, [])
        if not isinstance(values, list):
            continue
        seen: set[str] = set()
        for value in values:
            key = str(value or "").strip()
            if key and key not in seen:
                normalized[side].append(key)
                seen.add(key)
    return normalized


def copy_trade_state(state: TradeState) -> TradeState:
    return deepcopy(normalize_trade_state(state))


def add_trade_item(state: TradeState, side: Side, item_key: str) -> TradeState:
    normalized = copy_trade_state(state)
    key = str(item_key or "").strip()
    if key and key not in normalized[side]:
        normalized[side].append(key)
    return normalized


def remove_trade_item(state: TradeState, side: Side, item_key: str) -> TradeState:
    normalized = copy_trade_state(state)
    normalized[side] = [key for key in normalized[side] if key != item_key]
    return normalized


def clear_trade_state() -> TradeState:
    return empty_trade_state()


def build_trade_item_lookup(
    player_frame: pd.DataFrame,
    trade_context_frame: pd.DataFrame,
    pick_context_frame: pd.DataFrame,
    *,
    require_complete_player_universe: bool = False,
) -> dict[str, dict[str, object]]:
    if require_complete_player_universe:
        errors = validate_trade_player_universe(player_frame)
        if errors:
            raise TradePlayerUniverseError(" ".join(errors))

    lookup: dict[str, dict[str, object]] = {}
    player_context = _context_by_player_key(trade_context_frame)
    for _index, row in player_frame.iterrows():
        row_key = player_key(row)
        context = player_context.get(row_key, {}) or player_context.get(
            _player_identity_key(row),
            {},
        )
        key = f"{PLAYER_PREFIX}{row_key}"
        lookup[key] = {
            "item_key": key,
            "asset_type": "Player",
            "label": player_label(row),
            "nwr_player_id": _nwr_player_id(row, context),
            "player": _player_name(row),
            "position": _text(row.get("position")),
            "nfl_team": _text(row.get("nfl_team")),
            "roster_context": _roster_context(row),
            "rank_source": _rank_source(row),
            "dynasty_rank": row.get("nwr_rank", ""),
            "final_board_rank": row.get("final_board_rank", ""),
            "final_tier": _text(row.get("final_tier")),
            "tier_movement_note": _note(context.get("tier_movement_note")),
            "position_scarcity_note": _note(context.get("position_scarcity_note")),
            "pick_window_note": _note(context.get("pick_window_note")),
            "risk_manual_review_notes": _note(
                context.get(
                    "risk_manual_review_notes",
                    row.get(
                        "risk_notes",
                        row.get("warning_flags", row.get("risk_level", "")),
                    ),
                )
            ),
            "data_status": (
                "Current production player universe"
                if _rank_source(row) == "Dynasty Rank"
                else "Available"
            ),
        }
    for _index, row in pick_context_frame.iterrows():
        row_key = player_key(row)
        pick_note = _note(
            row.get("pick_window_note", row.get("nfl_draft_capital_display_only", ""))
        )
        key = f"{PICK_CONTEXT_PREFIX}{row_key}"
        lookup[key] = {
            "item_key": key,
            "asset_type": "Pick context",
            "label": f"{pick_note} - {_text(row.get('player'))}",
            "nwr_player_id": NOT_ENOUGH_INFORMATION,
            "player": _text(row.get("player")),
            "position": _text(row.get("position")),
            "nfl_team": _text(row.get("nfl_team")),
            "roster_context": NOT_ENOUGH_INFORMATION,
            "rank_source": "Frozen draft/pick context",
            "dynasty_rank": NOT_ENOUGH_INFORMATION,
            "final_board_rank": row.get("final_board_rank", ""),
            "final_tier": _text(row.get("rookie_tier_display_only", NOT_ENOUGH_INFORMATION)),
            "tier_movement_note": NOT_ENOUGH_INFORMATION,
            "position_scarcity_note": NOT_ENOUGH_INFORMATION,
            "pick_window_note": pick_note,
            "risk_manual_review_notes": _note(row.get("caveat")),
            "data_status": "Display-only context; no standalone numeric pick context",
        }
    return lookup


def validate_trade_player_universe(player_frame: pd.DataFrame) -> tuple[str, ...]:
    """Validate the exact current-player authority consumed by Trading Lab."""

    errors: list[str] = []
    if int(player_frame.shape[0]) != EXPECTED_TRADE_PLAYER_UNIVERSE_ROWS:
        errors.append(
            "Trading Lab requires exactly "
            f"{EXPECTED_TRADE_PLAYER_UNIVERSE_ROWS} current players; found "
            f"{int(player_frame.shape[0])}."
        )

    required = (
        "player_id",
        "player_name",
        "position",
        "nwr_rank",
        "pool_status",
    )
    missing = [column for column in required if column not in player_frame.columns]
    if missing:
        errors.append(
            "Trading Lab player authority is missing required fields: "
            f"{', '.join(missing)}."
        )
        return tuple(errors)

    prohibited_columns = sorted(
        column
        for column in player_frame.columns
        if "hidden_sort" in str(column).casefold()
        or str(column).casefold()
        in {"opaque_trade_result", "recommended_side", "automatic_recommendation"}
    )
    if prohibited_columns:
        errors.append(
            "Trading Lab player authority contains prohibited recommendation or hidden-sort "
            f"fields: {', '.join(prohibited_columns)}."
        )

    player_ids = player_frame["player_id"].astype(str).str.strip()
    blank_ids = int(player_ids.eq("").sum())
    if blank_ids:
        errors.append(f"Trading Lab player authority has {blank_ids} blank player IDs.")
    duplicate_ids = sorted(player_ids[player_ids.ne("") & player_ids.duplicated()].unique())
    if duplicate_ids:
        errors.append(
            "Trading Lab player authority has duplicate player IDs: "
            f"{', '.join(duplicate_ids)}."
        )

    blank_names = int(player_frame["player_name"].astype(str).str.strip().eq("").sum())
    if blank_names:
        errors.append(f"Trading Lab player authority has {blank_names} blank player names.")

    rank_text = player_frame["nwr_rank"].astype(str).str.strip()
    numeric_ranks = pd.to_numeric(rank_text.where(rank_text.ne("")), errors="coerce")
    invalid_ranks = int(rank_text.ne("").sum() - numeric_ranks.notna().sum())
    if invalid_ranks:
        errors.append(
            f"Trading Lab player authority has {invalid_ranks} invalid Dynasty Rank values."
        )
    duplicate_ranks = sorted(
        {
            str(int(value))
            for value in numeric_ranks[numeric_ranks.notna() & numeric_ranks.duplicated()]
        }
    )
    if duplicate_ranks:
        errors.append(
            "Trading Lab player authority has duplicate Dynasty Rank values: "
            f"{', '.join(duplicate_ranks)}."
        )

    pool_statuses = player_frame["pool_status"].astype(str).str.strip().str.upper()
    invalid_pool_statuses = sorted(
        set(pool_statuses) - set(APPROVED_POOL_STATUSES)
    )
    if invalid_pool_statuses:
        errors.append(
            "Trading Lab player authority has unapproved ownership states: "
            f"{', '.join(value or '<blank>' for value in invalid_pool_statuses)}."
        )
    return tuple(errors)


def player_options(lookup: dict[str, dict[str, object]]) -> dict[str, str]:
    return {
        str(item["label"]): key
        for key, item in lookup.items()
        if str(item.get("asset_type")) == "Player"
    }


def pick_context_options(lookup: dict[str, dict[str, object]]) -> dict[str, str]:
    return {
        str(item["label"]): key
        for key, item in lookup.items()
        if str(item.get("asset_type")) == "Pick context"
    }


def trade_item_rows(
    state: TradeState,
    lookup: dict[str, dict[str, object]],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    normalized = normalize_trade_state(state)
    for side in ("give", "get"):
        for key in normalized[side]:
            item = dict(lookup.get(key, _missing_item(key)))
            item["side"] = "NWR gives" if side == "give" else "NWR gets"
            rows.append(item)
    if not rows:
        return pd.DataFrame(columns=DISPLAY_ITEM_COLUMNS)
    return pd.DataFrame(rows)


def display_trade_item_rows(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [column for column in DISPLAY_ITEM_COLUMNS if column in frame.columns]
    return frame.loc[:, columns].rename(columns=_display_labels())


def package_summary_rows(
    state: TradeState,
    lookup: dict[str, dict[str, object]],
) -> pd.DataFrame:
    normalized = normalize_trade_state(state)
    rows = [
        _side_summary("give", normalized["give"], lookup),
        _side_summary("get", normalized["get"], lookup),
    ]
    return pd.DataFrame(rows).loc[:, list(DISPLAY_SUMMARY_COLUMNS)]


def display_package_summary(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.rename(columns=_display_labels())


def review_trade_package(
    state: TradeState,
    lookup: dict[str, dict[str, object]],
) -> TradeReview:
    summary = package_summary_rows(state, lookup)
    give = summary.loc[summary["side"] == "NWR gives"].iloc[0]
    get = summary.loc[summary["side"] == "NWR gets"].iloc[0]
    if int(give["asset_count"]) == 0 or int(get["asset_count"]) == 0:
        return TradeReview(
            status="One side empty",
            missing_context_display="Missing context visible",
            rank_context=NOT_ENOUGH_INFORMATION,
            explanation="Add at least one manually selected item to each side before review.",
        )
    if int(give["player_count"]) == 0 or int(get["player_count"]) == 0:
        return TradeReview(
            status="Pick-only context present",
            missing_context_display="More evidence needed",
            rank_context=NOT_ENOUGH_INFORMATION,
            explanation=(
                "Standalone pick/context items are labels and factual context only; no numeric "
                "pick context is inferred."
            ),
        )

    give_rank = _maybe_float(give["best_rank"])
    get_rank = _maybe_float(get["best_rank"])
    rank_context = (
        "Player-rank labels present"
        if give_rank is not None and get_rank is not None
        else NOT_ENOUGH_INFORMATION
    )
    return TradeReview(
        status="Context ready for manual review",
        missing_context_display="Manual review required",
        rank_context=rank_context,
        explanation=(
            "Selected asset context is assembled for manual review only. No package value, "
            "side total, side average, gap, or recommendation is calculated."
        ),
    )


def parse_trade_asset_text(text: str) -> list[dict[str, Any]]:
    return parse_trade_assets(text)


def source_context_counts(
    player_frame: pd.DataFrame,
    trade_context_frame: pd.DataFrame,
    pick_context_frame: pd.DataFrame,
    tier_frame: pd.DataFrame,
) -> dict[str, int]:
    return {
        "player_universe_rows": int(player_frame.shape[0]),
        "trade_helper_rows": int(trade_context_frame.shape[0]),
        "pick_context_rows": int(pick_context_frame.shape[0]),
        "tier_context_rows": int(tier_frame.shape[0]),
    }


def player_key(row: pd.Series | dict[str, object]) -> str:
    get = row.get
    player_id = _text(get("player_id", "") or get("nwr_player_id", ""))
    if player_id:
        return f"id:{player_id}"
    return "|".join(
        (
            _text(get("final_board_rank", "")),
            _player_name(row),
            _text(get("position", "")),
            _text(get("nfl_team", "")),
        )
    )


def player_label(row: pd.Series | dict[str, object]) -> str:
    get = row.get
    dynasty_rank = _text(get("nwr_rank", ""))
    if _player_name(row) and "player_name" in row:
        rank_label = (
            f"Dynasty #{dynasty_rank}"
            if dynasty_rank
            else "Dynasty rank unavailable"
        )
    else:
        rank_label = f"#{_text(get('final_board_rank', ''))}"
    return (
        f"{rank_label} - {_player_name(row)} "
        f"({_text(get('position', ''))}, {_text(get('nfl_team', ''))})"
    )


def _context_by_player_key(frame: pd.DataFrame) -> dict[str, dict[str, object]]:
    context: dict[str, dict[str, object]] = {}
    if frame.empty:
        return context
    for _index, row in frame.iterrows():
        row_context = row.to_dict()
        context[player_key(row)] = row_context
        context[_player_identity_key(row)] = row_context
    return context


def _side_summary(
    side: Side,
    keys: list[str],
    lookup: dict[str, dict[str, object]],
) -> dict[str, object]:
    items = [lookup.get(key, _missing_item(key)) for key in keys]
    players = [item for item in items if str(item.get("asset_type")) == "Player"]
    pick_contexts = [item for item in items if str(item.get("asset_type")) == "Pick context"]
    ranks = [
        float(rank)
        for item in players
        if (rank := _primary_rank(item)) is not None
    ]
    return {
        "side": "NWR gives" if side == "give" else "NWR gets",
        "asset_count": len(items),
        "player_count": len(players),
        "pick_context_count": len(pick_contexts),
        "best_rank": int(min(ranks)) if ranks else NOT_ENOUGH_INFORMATION,
        "top_tier": _join_unique(item.get("final_tier") for item in players),
        "tier_movement": _join_unique(item.get("tier_movement_note") for item in items),
        "scarcity": _join_unique(item.get("position_scarcity_note") for item in items),
        "pick_context": _join_unique(item.get("pick_window_note") for item in items),
        "risk_notes": _join_unique(item.get("risk_manual_review_notes") for item in items),
    }


def _missing_item(key: str) -> dict[str, object]:
    return {
        "item_key": key,
        "asset_type": NOT_ENOUGH_INFORMATION,
        "label": key,
        "nwr_player_id": NOT_ENOUGH_INFORMATION,
        "player": NOT_ENOUGH_INFORMATION,
        "position": NOT_ENOUGH_INFORMATION,
        "nfl_team": NOT_ENOUGH_INFORMATION,
        "roster_context": NOT_ENOUGH_INFORMATION,
        "rank_source": NOT_ENOUGH_INFORMATION,
        "dynasty_rank": NOT_ENOUGH_INFORMATION,
        "final_board_rank": NOT_ENOUGH_INFORMATION,
        "final_tier": NOT_ENOUGH_INFORMATION,
        "tier_movement_note": NOT_ENOUGH_INFORMATION,
        "position_scarcity_note": NOT_ENOUGH_INFORMATION,
        "pick_window_note": NOT_ENOUGH_INFORMATION,
        "risk_manual_review_notes": NOT_ENOUGH_INFORMATION,
        "data_status": NOT_ENOUGH_INFORMATION,
    }


def _join_unique(values: Any) -> str:
    clean = sorted({_note(value) for value in values if _note(value) != NOT_ENOUGH_INFORMATION})
    return " | ".join(clean) if clean else NOT_ENOUGH_INFORMATION


def _note(value: object) -> str:
    text = _text(value)
    if text.lower() in {"", "nan", "none", "null", "n/a"}:
        return NOT_ENOUGH_INFORMATION
    return text


def _nwr_player_id(
    row: pd.Series | dict[str, object],
    context: dict[str, object],
) -> str:
    get = row.get
    for source in (
        get("player_id", ""),
        get("nwr_player_id", ""),
        context.get("nwr_player_id"),
        context.get("player_id"),
    ):
        value = _note(source)
        if value != NOT_ENOUGH_INFORMATION:
            return value
    return NOT_ENOUGH_INFORMATION


def _player_name(row: pd.Series | dict[str, object]) -> str:
    get = row.get
    return _text(get("player_name", "") or get("player", ""))


def _player_identity_key(row: pd.Series | dict[str, object]) -> str:
    get = row.get
    return "|".join(
        (
            _player_name(row).casefold(),
            _text(get("position", "")).upper(),
            _text(get("nfl_team", "")).upper(),
        )
    )


def _rank_source(row: pd.Series | dict[str, object]) -> str:
    get = row.get
    if _maybe_float(get("nwr_rank", "")) is not None:
        return "Dynasty Rank"
    if _maybe_float(get("final_board_rank", "")) is not None:
        return "Frozen Final Board Rank"
    return NOT_ENOUGH_INFORMATION


def _primary_rank(row: pd.Series | dict[str, object]) -> float | None:
    get = row.get
    dynasty_rank = _maybe_float(get("dynasty_rank", get("nwr_rank", "")))
    if dynasty_rank is not None:
        return dynasty_rank
    return _maybe_float(get("final_board_rank", ""))


def _roster_context(row: pd.Series | dict[str, object]) -> str:
    get = row.get
    return _note(
        get("pool_status", "")
        or get("roster_team_name", "")
        or get("roster_status", "")
    )


def _text(value: object) -> str:
    return str(value or "").strip()


def _maybe_float(value: object) -> float | None:
    try:
        if str(value or "").strip() == "":
            return None
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _display_labels() -> dict[str, str]:
    return {
        "side": "Side",
        "asset_count": "Assets",
        "player_count": "Players",
        "pick_context_count": "Pick Context Items",
        "best_rank": "Best Player Rank",
        "top_tier": "Tier Context",
        "tier_movement": "Tier Movement",
        "scarcity": "Position Scarcity",
        "pick_context": "Pick Context",
        "risk_notes": "Risk Notes",
        "asset_type": "Asset Type",
        "label": "Asset",
        "nwr_player_id": "NWR Player ID",
        "player": "Player",
        "position": "Pos",
        "nfl_team": "NFL Team",
        "roster_context": "Roster Context",
        "rank_source": "Rank Source",
        "dynasty_rank": "Dynasty Rank",
        "final_board_rank": "Final Board Rank",
        "final_tier": "Final Tier",
        "tier_movement_note": "Tier Movement",
        "position_scarcity_note": "Position Scarcity",
        "pick_window_note": "Pick Context",
        "risk_manual_review_notes": "Risk / Manual Review",
        "data_status": "Data Status",
    }
