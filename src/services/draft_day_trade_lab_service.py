from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import pandas as pd

from src.services.draft_day_runtime_state_service import parse_trade_assets
from src.services.market_baseline_service import (
    DISPLAY_LABEL as MARKET_BASELINE_DISPLAY_LABEL,
)
from src.services.market_baseline_service import (
    DISPLAY_ONLY_WARNING as MARKET_BASELINE_DISPLAY_ONLY_WARNING,
)
from src.services.market_baseline_service import (
    get_pick_market_value,
    join_market_to_players,
    load_market_freshness,
)

NOT_ENOUGH_INFORMATION = "Not enough information"
Side = Literal["give", "get"]
TradeState = dict[str, list[str]]

PLAYER_PREFIX = "player:"
PICK_CONTEXT_PREFIX = "pick_context:"

DISPLAY_ITEM_COLUMNS = (
    "side",
    "asset_type",
    "label",
    "player",
    "position",
    "nfl_team",
    "final_board_rank",
    "final_tier",
    "visible_score_for_context",
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
    "visible_score_sum",
    "top_tier",
    "tier_movement",
    "scarcity",
    "pick_context",
    "risk_notes",
)


@dataclass(frozen=True)
class TradeReview:
    status: str
    score_gap_display: str
    rank_context: str
    explanation: str


@dataclass(frozen=True)
class MarketPackageSummary:
    rows: pd.DataFrame
    totals: pd.DataFrame
    status: str
    difference_display: str
    freshness: dict[str, str]
    display_only_warning: str


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
            "player": _text(row.get("player")),
            "position": _text(row.get("position")),
            "nfl_team": _text(row.get("nfl_team")),
            "final_board_rank": row.get("final_board_rank", ""),
            "final_tier": _text(row.get("final_tier")),
            "visible_score_for_context": _number(
                context.get(
                    "visible_score_for_context",
                    row.get("final_board_score_visible", ""),
                )
            ),
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
            "player": _text(row.get("player")),
            "position": _text(row.get("position")),
            "nfl_team": _text(row.get("nfl_team")),
            "final_board_rank": row.get("final_board_rank", ""),
            "final_tier": _text(row.get("rookie_tier_display_only", NOT_ENOUGH_INFORMATION)),
            "visible_score_for_context": None,
            "tier_movement_note": NOT_ENOUGH_INFORMATION,
            "position_scarcity_note": NOT_ENOUGH_INFORMATION,
            "pick_window_note": pick_note,
            "risk_manual_review_notes": _note(row.get("caveat")),
            "data_status": "Display-only context; no standalone pick value",
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
            status=NOT_ENOUGH_INFORMATION,
            score_gap_display=NOT_ENOUGH_INFORMATION,
            rank_context=NOT_ENOUGH_INFORMATION,
            explanation="Add at least one item to each side before reviewing the package.",
        )
    if int(give["player_count"]) == 0 or int(get["player_count"]) == 0:
        return TradeReview(
            status=NOT_ENOUGH_INFORMATION,
            score_gap_display=NOT_ENOUGH_INFORMATION,
            rank_context=NOT_ENOUGH_INFORMATION,
            explanation="Standalone pick/context items do not carry approved trade value.",
        )

    give_score = float(give["visible_score_sum"])
    get_score = float(get["visible_score_sum"])
    gap = round(get_score - give_score, 2)
    give_rank = _maybe_float(give["best_rank"])
    get_rank = _maybe_float(get["best_rank"])
    rank_context = (
        f"Best get rank {int(get_rank)} vs best give rank {int(give_rank)}"
        if get_rank is not None and give_rank is not None
        else NOT_ENOUGH_INFORMATION
    )
    if gap >= 10 and (get_rank is None or give_rank is None or get_rank <= give_rank):
        status = "Looks favorable"
        explanation = "Get side improves visible score context without worsening best-rank context."
    elif gap <= -10:
        status = "Risky"
        explanation = "Give side is materially stronger by visible frozen-board score context."
    else:
        status = "Close / needs human judgment"
        explanation = (
            "Package sides are close enough that roster need, tier fit, and risk notes matter."
        )
    return TradeReview(
        status=status,
        score_gap_display=f"{gap:+.2f}",
        rank_context=rank_context,
        explanation=explanation,
    )


def parse_trade_asset_text(text: str) -> list[dict[str, Any]]:
    return parse_trade_assets(text)


def lookup_pick_market_value(
    asset_text: str,
    *,
    artifact_dir: str | Path | None = None,
) -> dict[str, str]:
    parsed = parse_trade_assets(asset_text)
    if not parsed:
        return _missing_market_lookup(asset_text, "unknown", "REVIEW_NEEDED")
    asset = parsed[0]
    if asset.get("asset_type") not in {"pick", "future_pick"}:
        return _missing_market_lookup(
            asset_text,
            str(asset.get("asset_type") or "unknown"),
            "REVIEW_NEEDED",
        )
    label = str(asset.get("display_label") or asset.get("pick_label") or asset_text)
    try:
        match = (
            get_pick_market_value(label, artifact_dir=artifact_dir)
            if artifact_dir is not None
            else get_pick_market_value(label)
        )
    except (FileNotFoundError, TypeError, ValueError):
        match = None
    if not match:
        return _missing_market_lookup(
            label,
            str(asset.get("asset_type") or "pick"),
            "No market match",
        )
    return {
        "asset": label,
        "parsed_type": str(asset.get("asset_type") or "pick"),
        "dp_value": _text(match.get("value_1qb")),
        "match_status": "Matched pick market value",
        "notes": _text(match.get("source_note")) or MARKET_BASELINE_DISPLAY_ONLY_WARNING,
        "market_baseline_label": MARKET_BASELINE_DISPLAY_LABEL,
    }


def lookup_player_market_value(
    player_row: dict[str, object],
    *,
    artifact_dir: str | Path | None = None,
) -> dict[str, str]:
    frame = pd.DataFrame([player_row])
    try:
        enriched = (
            join_market_to_players(frame, artifact_dir=artifact_dir)
            if artifact_dir is not None
            else join_market_to_players(frame)
        )
    except (FileNotFoundError, TypeError, ValueError):
        enriched = frame.copy()
    row = enriched.iloc[0].to_dict() if not enriched.empty else player_row
    player = _text(
        row.get("player")
        or row.get("player_name")
        or row.get("name")
        or player_row.get("player")
        or player_row.get("label")
    )
    value = _text(row.get("dp_value_1qb"))
    if not value:
        return _missing_market_lookup(player or NOT_ENOUGH_INFORMATION, "player", "No market match")
    return {
        "asset": player,
        "parsed_type": "player",
        "dp_value": value,
        "match_status": _text(row.get("market_join_confidence")) or "Matched player market value",
        "notes": _text(row.get("dp_display_only_warning")) or MARKET_BASELINE_DISPLAY_ONLY_WARNING,
        "market_baseline_label": MARKET_BASELINE_DISPLAY_LABEL,
    }


def summarize_trade_package_market(
    state: TradeState,
    lookup: dict[str, dict[str, object]],
    *,
    give_assets_text: str = "",
    get_assets_text: str = "",
    artifact_dir: str | Path | None = None,
) -> MarketPackageSummary:
    rows: list[dict[str, str]] = []
    normalized = normalize_trade_state(state)
    for side in ("give", "get"):
        for key in normalized[side]:
            item = lookup.get(key, _missing_item(key))
            rows.append(
                _market_row_for_lookup_item(
                    "NWR gives" if side == "give" else "NWR gets",
                    item,
                    artifact_dir=artifact_dir,
                )
            )
    rows.extend(
        _manual_market_rows("NWR gives", give_assets_text, artifact_dir=artifact_dir)
    )
    rows.extend(
        _manual_market_rows("NWR gets", get_assets_text, artifact_dir=artifact_dir)
    )
    frame = pd.DataFrame(
        rows,
        columns=[
            "side",
            "asset",
            "parsed_type",
            "dp_value",
            "match_status",
            "notes",
            "market_baseline_label",
        ],
    )
    totals = _market_totals(frame)
    status, difference_display = classify_market_trade_gap(totals)
    try:
        freshness = (
            load_market_freshness(artifact_dir=artifact_dir)
            if artifact_dir is not None
            else load_market_freshness()
        )
    except (FileNotFoundError, TypeError, ValueError):
        freshness = {
            "freshness_status": "RED_NO_VALID_CACHE",
            "upstream_scrape_date": "",
            "market_baseline_stale_warning": "Market baseline unavailable.",
        }
    return MarketPackageSummary(
        rows=frame,
        totals=totals,
        status=status,
        difference_display=difference_display,
        freshness=freshness,
        display_only_warning=MARKET_BASELINE_DISPLAY_ONLY_WARNING,
    )


def classify_market_trade_gap(totals: pd.DataFrame) -> tuple[str, str]:
    if totals.empty:
        return NOT_ENOUGH_INFORMATION, NOT_ENOUGH_INFORMATION
    values = {
        str(row.get("side")): _maybe_float(row.get("dp_market_total"))
        for row in totals.to_dict("records")
    }
    give = values.get("NWR gives")
    get = values.get("NWR gets")
    if give is None or get is None:
        return NOT_ENOUGH_INFORMATION, NOT_ENOUGH_INFORMATION
    difference = round(get - give, 2)
    if abs(difference) <= 250:
        status = "Market says close"
    elif difference > 0:
        status = "Market says get side higher"
    else:
        status = "Market says give side higher"
    return status, f"{difference:+.2f}"


def display_market_package_rows(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.rename(
        columns={
            "side": "Side",
            "asset": "Asset",
            "parsed_type": "Parsed Type",
            "dp_value": "DP Value / Display-Only",
            "match_status": "Match Status",
            "notes": "Notes",
            "market_baseline_label": "Market Baseline Label",
        }
    )


def display_market_totals(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.rename(
        columns={
            "side": "Side",
            "dp_market_total": "DP Market Total / Display-Only",
            "matched_assets": "Matched Assets",
            "unknown_assets": "Unknown / Review Assets",
        }
    )


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
    scores = [
        float(item["visible_score_for_context"])
        for item in players
        if _maybe_float(item.get("visible_score_for_context")) is not None
    ]
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
        "visible_score_sum": round(sum(scores), 2) if scores else 0.0,
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
        "player": NOT_ENOUGH_INFORMATION,
        "position": NOT_ENOUGH_INFORMATION,
        "nfl_team": NOT_ENOUGH_INFORMATION,
        "final_board_rank": NOT_ENOUGH_INFORMATION,
        "final_tier": NOT_ENOUGH_INFORMATION,
        "visible_score_for_context": None,
        "tier_movement_note": NOT_ENOUGH_INFORMATION,
        "position_scarcity_note": NOT_ENOUGH_INFORMATION,
        "pick_window_note": NOT_ENOUGH_INFORMATION,
        "risk_manual_review_notes": NOT_ENOUGH_INFORMATION,
        "data_status": NOT_ENOUGH_INFORMATION,
    }


def _market_row_for_lookup_item(
    side_label: str,
    item: dict[str, object],
    *,
    artifact_dir: str | Path | None,
) -> dict[str, str]:
    if str(item.get("asset_type")) == "Player":
        row = lookup_player_market_value(item, artifact_dir=artifact_dir)
    else:
        row = _missing_market_lookup(
            _text(item.get("label")) or NOT_ENOUGH_INFORMATION,
            str(item.get("asset_type") or "unknown"),
            "Not a market-valued pick/player asset",
        )
    row["side"] = side_label
    return row


def _manual_market_rows(
    side_label: str,
    text: str,
    *,
    artifact_dir: str | Path | None,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for asset in parse_trade_assets(text):
        raw = _text(asset.get("raw_text") or asset.get("display_label"))
        if asset.get("asset_type") in {"pick", "future_pick"}:
            row = lookup_pick_market_value(raw, artifact_dir=artifact_dir)
        else:
            row = _missing_market_lookup(
                raw,
                str(asset.get("asset_type") or "unknown"),
                str(asset.get("status") or "REVIEW_NEEDED"),
            )
        row["side"] = side_label
        rows.append(row)
    return rows


def _market_totals(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for side in ("NWR gives", "NWR gets"):
        side_frame = frame.loc[frame.get("side", pd.Series(dtype=str)).astype(str).eq(side)]
        values = pd.to_numeric(side_frame.get("dp_value", pd.Series(dtype=str)), errors="coerce")
        matched = int(values.notna().sum())
        unknown = int(values.isna().sum()) if not side_frame.empty else 0
        rows.append(
            {
                "side": side,
                "dp_market_total": round(float(values.dropna().sum()), 2)
                if matched
                else NOT_ENOUGH_INFORMATION,
                "matched_assets": matched,
                "unknown_assets": unknown,
            }
        )
    return pd.DataFrame(rows)


def _missing_market_lookup(asset: str, parsed_type: str, status: str) -> dict[str, str]:
    return {
        "asset": asset or NOT_ENOUGH_INFORMATION,
        "parsed_type": parsed_type or "unknown",
        "dp_value": NOT_ENOUGH_INFORMATION,
        "match_status": status or NOT_ENOUGH_INFORMATION,
        "notes": "Market value missing; do not treat as zero.",
        "market_baseline_label": MARKET_BASELINE_DISPLAY_LABEL,
    }


def _join_unique(values: Any) -> str:
    clean = sorted({_note(value) for value in values if _note(value) != NOT_ENOUGH_INFORMATION})
    return " | ".join(clean) if clean else NOT_ENOUGH_INFORMATION


def _note(value: object) -> str:
    text = _text(value)
    if text.lower() in {"", "nan", "none", "null", "n/a"}:
        return NOT_ENOUGH_INFORMATION
    return text


def _text(value: object) -> str:
    return str(value or "").strip()


def _number(value: object) -> float | None:
    maybe = _maybe_float(value)
    return round(maybe, 2) if maybe is not None else None


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
        "visible_score_sum": "Visible Score Sum",
        "top_tier": "Tier Context",
        "tier_movement": "Tier Movement",
        "scarcity": "Position Scarcity",
        "pick_context": "Pick Context",
        "risk_notes": "Risk Notes",
        "asset_type": "Asset Type",
        "label": "Asset",
        "player": "Player",
        "position": "Pos",
        "nfl_team": "NFL Team",
        "final_board_rank": "Final Board Rank",
        "final_tier": "Final Tier",
        "visible_score_for_context": "Visible Score Context",
        "tier_movement_note": "Tier Movement",
        "position_scarcity_note": "Position Scarcity",
        "pick_window_note": "Pick Context",
        "risk_manual_review_notes": "Risk / Manual Review",
        "data_status": "Data Status",
    }
