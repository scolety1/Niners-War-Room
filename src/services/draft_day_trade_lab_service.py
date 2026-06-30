from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal

import pandas as pd

from src.services.draft_day_runtime_state_service import parse_trade_assets

NOT_ENOUGH_INFORMATION = "Not enough information"
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
    board_frame: pd.DataFrame,
    trade_context_frame: pd.DataFrame,
    pick_context_frame: pd.DataFrame,
) -> dict[str, dict[str, object]]:
    lookup: dict[str, dict[str, object]] = {}
    player_context = _context_by_player_key(trade_context_frame)
    for _index, row in board_frame.iterrows():
        row_key = player_key(row)
        context = player_context.get(row_key, {})
        key = f"{PLAYER_PREFIX}{row_key}"
        lookup[key] = {
            "item_key": key,
            "asset_type": "Player",
            "label": player_label(row),
            "nwr_player_id": _nwr_player_id(row, context),
            "player": _text(row.get("player")),
            "position": _text(row.get("position")),
            "nfl_team": _text(row.get("nfl_team")),
            "final_board_rank": row.get("final_board_rank", ""),
            "final_tier": _text(row.get("final_tier")),
            "tier_movement_note": _note(context.get("tier_movement_note")),
            "position_scarcity_note": _note(context.get("position_scarcity_note")),
            "pick_window_note": _note(context.get("pick_window_note")),
            "risk_manual_review_notes": _note(
                context.get("risk_manual_review_notes", row.get("risk_notes", ""))
            ),
            "data_status": "Available",
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
            "final_board_rank": row.get("final_board_rank", ""),
            "final_tier": _text(row.get("rookie_tier_display_only", NOT_ENOUGH_INFORMATION)),
            "tier_movement_note": NOT_ENOUGH_INFORMATION,
            "position_scarcity_note": NOT_ENOUGH_INFORMATION,
            "pick_window_note": pick_note,
            "risk_manual_review_notes": _note(row.get("caveat")),
            "data_status": "Display-only context; no standalone numeric pick context",
        }
    return lookup


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
        "Board-rank labels present"
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
    board_frame: pd.DataFrame,
    trade_context_frame: pd.DataFrame,
    pick_context_frame: pd.DataFrame,
    tier_frame: pd.DataFrame,
) -> dict[str, int]:
    return {
        "frozen_board_rows": int(board_frame.shape[0]),
        "trade_helper_rows": int(trade_context_frame.shape[0]),
        "pick_context_rows": int(pick_context_frame.shape[0]),
        "tier_context_rows": int(tier_frame.shape[0]),
    }


def player_key(row: pd.Series | dict[str, object]) -> str:
    get = row.get
    return "|".join(
        str(get(column, "") or "").strip()
        for column in ("final_board_rank", "player", "position", "nfl_team")
    )


def player_label(row: pd.Series | dict[str, object]) -> str:
    get = row.get
    return (
        f"#{get('final_board_rank', '')} - {get('player', '')} "
        f"({get('position', '')}, {get('nfl_team', '')})"
    )


def _context_by_player_key(frame: pd.DataFrame) -> dict[str, dict[str, object]]:
    context: dict[str, dict[str, object]] = {}
    if frame.empty:
        return context
    for _index, row in frame.iterrows():
        context[player_key(row)] = row.to_dict()
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
        float(item["final_board_rank"])
        for item in players
        if _maybe_float(item.get("final_board_rank")) is not None
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
        context.get("nwr_player_id"),
        get("nwr_player_id", ""),
        context.get("player_id"),
        get("player_id", ""),
    ):
        value = _note(source)
        if value != NOT_ENOUGH_INFORMATION:
            return value
    return NOT_ENOUGH_INFORMATION


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
        "best_rank": "Best Board Rank",
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
        "final_board_rank": "Final Board Rank",
        "final_tier": "Final Tier",
        "tier_movement_note": "Tier Movement",
        "position_scarcity_note": "Position Scarcity",
        "pick_window_note": "Pick Context",
        "risk_manual_review_notes": "Risk / Manual Review",
        "data_status": "Data Status",
    }
