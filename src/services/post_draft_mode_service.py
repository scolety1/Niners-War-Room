from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pandas as pd

from src.services.draft_day_runtime_state_service import (
    RuntimeState,
    event_rows,
    normalize_runtime_state,
)
from src.services.market_baseline_service import (
    DISPLAY_LABEL as MARKET_BASELINE_DISPLAY_LABEL,
)
from src.services.market_baseline_service import (
    compute_market_sanity_flags,
)

NOT_ENOUGH_INFORMATION = "Not enough information"
RUNTIME_SOURCE_LABEL = "User-entered local draft runtime state"
MARKET_DISPLAY_ONLY_LABEL = f"{MARKET_BASELINE_DISPLAY_LABEL} / Display-Only"


@dataclass(frozen=True)
class PostDraftSummary:
    metrics: dict[str, str]
    draft_recap: pd.DataFrame
    trade_recap: pd.DataFrame
    value_audit: pd.DataFrame
    position_shape: pd.DataFrame
    next_actions: tuple[str, ...]
    event_log: pd.DataFrame
    missing_data_warnings: tuple[str, ...]


def build_post_draft_summary(
    state: RuntimeState,
    *,
    player_context: pd.DataFrame | None = None,
    include_market_context: bool = True,
) -> PostDraftSummary:
    """Build display-only post-draft recap frames from local runtime state."""

    normalized = normalize_runtime_state(
        state,
        mode=str(state.get("mode") or "live"),
        draft_id=str(state.get("draft_id") or "draft_day_v2"),
    )
    context = player_context.copy() if player_context is not None else pd.DataFrame()
    draft_recap = _draft_recap_frame(
        normalized,
        context,
        include_market_context=include_market_context,
    )
    trade_recap = _trade_recap_frame(normalized)
    value_audit = _value_audit_frame(draft_recap)
    position_shape = _position_shape_frame(draft_recap)
    event_frame = pd.DataFrame(event_rows(normalized))
    warnings = _missing_data_warnings(draft_recap, trade_recap, context)
    metrics = {
        "mode": str(normalized.get("mode") or "").title(),
        "draft_session_id": str(normalized.get("draft_session_id") or ""),
        "last_updated": str(normalized.get("updated_at_utc") or normalized.get("updated_at") or ""),
        "drafted_count": str(len(normalized["workflow_state"]["assignments"])),
        "trade_count": str(len(normalized["trade_events"])),
        "event_count": str(len(event_frame)),
        "runtime_source": RUNTIME_SOURCE_LABEL,
    }
    return PostDraftSummary(
        metrics=metrics,
        draft_recap=draft_recap,
        trade_recap=trade_recap,
        value_audit=value_audit,
        position_shape=position_shape,
        next_actions=_next_actions(warnings, trade_recap),
        event_log=event_frame,
        missing_data_warnings=warnings,
    )


def post_draft_summary_export(summary: PostDraftSummary) -> str:
    payload = {
        "metrics": summary.metrics,
        "draft_recap": summary.draft_recap.to_dict("records"),
        "trade_recap": summary.trade_recap.to_dict("records"),
        "value_audit": summary.value_audit.to_dict("records"),
        "position_shape": summary.position_shape.to_dict("records"),
        "next_actions": list(summary.next_actions),
        "missing_data_warnings": list(summary.missing_data_warnings),
        "guardrail_status": (
            "Post-draft summary is audit/display only. Runtime draft state is not "
            "source truth, and market context is display-only."
        ),
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def _draft_recap_frame(
    state: RuntimeState,
    player_context: pd.DataFrame,
    *,
    include_market_context: bool,
) -> pd.DataFrame:
    assignments = [
        row
        for row in state["workflow_state"]["assignments"]
        if isinstance(row, dict)
    ]
    if not assignments:
        return pd.DataFrame(
            columns=[
                "Pick",
                "Team",
                "Player",
                "Pos",
                "NFL Team",
                "NWR Rank",
                "Market Rank / Display-Only",
                "Market Gap / Display-Only",
                "Notes",
            ]
        )
    context_lookup = _player_context_lookup(player_context)
    rows: list[dict[str, Any]] = []
    for assignment in assignments:
        match = _find_player_context(assignment, context_lookup)
        row = _assignment_display_row(assignment, match)
        rows.append(row)

    frame = pd.DataFrame(rows)
    if include_market_context and not frame.empty:
        frame = _append_market_context(frame)
    return _order_draft_recap_columns(frame)


def _trade_recap_frame(state: RuntimeState) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for trade in state["trade_events"]:
        if not isinstance(trade, dict):
            continue
        review_assets = _review_needed_assets(trade)
        current_year = trade.get("current_year_pick_changes", [])
        pick_effect = _join_pick_changes(current_year)
        rows.append(
            {
                "Trade ID": str(trade.get("trade_id") or ""),
                "Team A": _text(trade.get("team_a")) or NOT_ENOUGH_INFORMATION,
                "Team B": _text(trade.get("team_b")) or NOT_ENOUGH_INFORMATION,
                "Team A Sends": _text(trade.get("team_a_sends") or trade.get("sends"))
                or NOT_ENOUGH_INFORMATION,
                "Team B Sends": _text(trade.get("team_b_sends") or trade.get("receives"))
                or NOT_ENOUGH_INFORMATION,
                "Parsed Current-Year Picks": _join_pick_changes(current_year),
                "Future Picks": _join_values(trade.get("future_picks")),
                "Review-Needed Assets": _join_values(review_assets),
                "Ownership Overrides": pick_effect,
                "Pick Ownership Effect": (
                    pick_effect or "No current-year pick ownership changes recorded."
                ),
                "Notes": _text(trade.get("notes")) or NOT_ENOUGH_INFORMATION,
                "Source": (
                    "Manually recorded runtime trade event; not official source truth"
                ),
                "Valuation Status": (
                    "No trade valuation or pick valuation; manual runtime event only."
                ),
            }
        )
    return pd.DataFrame(rows)


def _value_audit_frame(draft_recap: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    if draft_recap.empty:
        return pd.DataFrame(
            [
                {
                    "Audit Item": "Highest NWR-ranked player acquired",
                    "Result": NOT_ENOUGH_INFORMATION,
                    "Guardrail": "Runtime state has no pick events yet.",
                }
            ]
        )
    with_ranks = draft_recap.copy()
    with_ranks["_nwr_rank_numeric"] = pd.to_numeric(
        with_ranks.get("NWR Rank", pd.Series(dtype=str)),
        errors="coerce",
    )
    ranked = with_ranks.dropna(subset=["_nwr_rank_numeric"]).sort_values(
        "_nwr_rank_numeric",
        kind="stable",
    )
    if ranked.empty:
        rows.append(
            {
                "Audit Item": "Highest NWR-ranked player acquired",
                "Result": NOT_ENOUGH_INFORMATION,
                "Guardrail": "No drafted player matched an NWR rank.",
            }
        )
    else:
        best = ranked.iloc[0]
        rows.append(
            {
                "Audit Item": "Highest NWR-ranked player acquired",
                "Result": f"#{best['NWR Rank']} {best['Player']}",
                "Guardrail": "NWR rank is displayed only; no rank values changed.",
            }
        )
    market_column = "Market Gap / Display-Only"
    if market_column in draft_recap.columns:
        market_rows = draft_recap.loc[
            draft_recap[market_column].astype(str).str.strip().ne("")
        ]
        market_rows = market_rows.loc[
            ~market_rows[market_column].astype(str).eq(NOT_ENOUGH_INFORMATION)
        ]
        if market_rows.empty:
            rows.append(
                {
                    "Audit Item": "Biggest market-vs-NWR disagreement",
                    "Result": NOT_ENOUGH_INFORMATION,
                    "Guardrail": "Market baseline missing or unmatched for drafted players.",
                }
            )
        else:
            rows.append(
                {
                    "Audit Item": "Biggest market-vs-NWR disagreement",
                    "Result": str(market_rows.iloc[0][market_column]),
                    "Guardrail": "Market baseline is display-only and did not drive rank.",
                }
            )
    rows.append(
        {
            "Audit Item": "Runtime source status",
            "Result": RUNTIME_SOURCE_LABEL,
            "Guardrail": "Confirm final picks/trades against official league history later.",
        }
    )
    return pd.DataFrame(rows)


def _position_shape_frame(draft_recap: pd.DataFrame) -> pd.DataFrame:
    if draft_recap.empty or "Pos" not in draft_recap.columns:
        return pd.DataFrame(
            [
                {
                    "Position": NOT_ENOUGH_INFORMATION,
                    "Acquired Count": "0",
                    "Audit Note": "Roster context not loaded; no runtime picks recorded.",
                }
            ]
        )
    counts = (
        draft_recap["Pos"]
        .replace("", NOT_ENOUGH_INFORMATION)
        .fillna(NOT_ENOUGH_INFORMATION)
        .astype(str)
        .value_counts()
        .sort_index()
    )
    return pd.DataFrame(
        [
            {
                "Position": pos,
                "Acquired Count": str(count),
                "Audit Note": "Roster context not loaded; position count is draft-session only.",
            }
            for pos, count in counts.items()
        ]
    )


def _missing_data_warnings(
    draft_recap: pd.DataFrame,
    trade_recap: pd.DataFrame,
    player_context: pd.DataFrame,
) -> tuple[str, ...]:
    warnings: list[str] = []
    if player_context.empty:
        warnings.append("Player context not loaded; NWR rank and market joins may be missing.")
    if draft_recap.empty:
        warnings.append("No runtime pick events recorded for this mode.")
    elif "NWR Rank" in draft_recap.columns and draft_recap["NWR Rank"].astype(str).eq(
        NOT_ENOUGH_INFORMATION
    ).any():
        warnings.append("One or more picked players did not match an NWR rank.")
    if not trade_recap.empty and trade_recap["Review-Needed Assets"].astype(str).ne("").any():
        warnings.append("One or more trade assets need manual review.")
    warnings.append("Roster context not loaded unless a separate roster source is added.")
    return tuple(dict.fromkeys(warnings))


def _next_actions(warnings: tuple[str, ...], trade_recap: pd.DataFrame) -> tuple[str, ...]:
    actions = [
        "Confirm runtime picks against the official league draft log.",
        "Confirm manually recorded trades against Sleeper or commissioner history.",
        "Review selected players in Player Compare before making roster-cut decisions.",
        "Resolve missing player IDs, market joins, and roster context before model use.",
    ]
    if not trade_recap.empty:
        actions.insert(2, "Audit current-year pick ownership and future-pick inventory.")
    if warnings:
        actions.append("Clear the missing-data warnings before using this as backtest truth.")
    return tuple(actions)


def _player_context_lookup(frame: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    lookup: dict[str, list[dict[str, Any]]] = {}
    if frame.empty:
        return lookup
    for row in frame.to_dict("records"):
        for key in _row_keys(row):
            lookup.setdefault(key, []).append(row)
    return lookup


def _find_player_context(
    assignment: dict[str, Any],
    lookup: dict[str, list[dict[str, Any]]],
) -> dict[str, Any] | None:
    for key in _row_keys(assignment):
        matches = lookup.get(key)
        if matches:
            return matches[0]
    return None


def _assignment_display_row(
    assignment: dict[str, Any],
    match: dict[str, Any] | None,
) -> dict[str, str]:
    get = lambda key: _text(assignment.get(key))  # noqa: E731
    match_get = lambda key: _text(match.get(key)) if match else ""  # noqa: E731
    return {
        "Pick": get("pick_label") or get("overall_pick") or NOT_ENOUGH_INFORMATION,
        "Team": get("selecting_team") or get("pick_owner") or NOT_ENOUGH_INFORMATION,
        "Player": get("player")
        or get("player_name")
        or match_get("player")
        or match_get("player_name")
        or NOT_ENOUGH_INFORMATION,
        "Pos": get("position")
        or match_get("position")
        or match_get("pos")
        or NOT_ENOUGH_INFORMATION,
        "NFL Team": get("nfl_team") or match_get("nfl_team") or match_get("team")
        or NOT_ENOUGH_INFORMATION,
        "NWR Rank": get("final_board_rank") or match_get("final_board_rank")
        or match_get("cross_asset_candidate_rank")
        or match_get("nwr_rank")
        or NOT_ENOUGH_INFORMATION,
        "Market Rank / Display-Only": NOT_ENOUGH_INFORMATION,
        "Market Gap / Display-Only": NOT_ENOUGH_INFORMATION,
        "Notes": get("notes") or "Runtime pick event; verify against official league log.",
        "Runtime Source": RUNTIME_SOURCE_LABEL,
    }


def _append_market_context(frame: pd.DataFrame) -> pd.DataFrame:
    market_input = frame.rename(
        columns={
            "Player": "player",
            "Pos": "position",
            "NWR Rank": "final_board_rank",
        }
    )
    try:
        market = compute_market_sanity_flags(market_input)
    except (FileNotFoundError, ValueError, AssertionError):
        output = frame.copy()
        output["Market Rank / Display-Only"] = NOT_ENOUGH_INFORMATION
        output["Market Gap / Display-Only"] = NOT_ENOUGH_INFORMATION
        return output
    output = frame.copy()
    output["Market Rank / Display-Only"] = market.get(
        "dp_market_rank_1qb",
        pd.Series([NOT_ENOUGH_INFORMATION] * len(output)),
    ).replace("", NOT_ENOUGH_INFORMATION)
    output["Market Gap / Display-Only"] = market.get(
        "market_sanity_label",
        pd.Series([NOT_ENOUGH_INFORMATION] * len(output)),
    ).replace("", NOT_ENOUGH_INFORMATION)
    output["Market Baseline Label"] = MARKET_DISPLAY_ONLY_LABEL
    return output


def _order_draft_recap_columns(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "Pick",
        "Team",
        "Player",
        "Pos",
        "NFL Team",
        "NWR Rank",
        "Market Rank / Display-Only",
        "Market Gap / Display-Only",
        "Notes",
        "Runtime Source",
        "Market Baseline Label",
    ]
    for column in columns:
        if column not in frame.columns:
            frame[column] = ""
    return frame.loc[:, [column for column in columns if column in frame.columns]]


def _row_keys(row: dict[str, Any]) -> tuple[str, ...]:
    keys: list[str] = []
    for column in ("player_id", "player_key", "sleeper_id", "nwr_player_id"):
        value = _text(row.get(column))
        if value:
            keys.append(f"id:{value.casefold()}")
    name = _text(row.get("player") or row.get("player_name") or row.get("name"))
    pos = _text(row.get("position") or row.get("pos"))
    if name and pos:
        keys.append(f"namepos:{_normalize_name(name)}|{pos.upper()}")
    if name:
        keys.append(f"name:{_normalize_name(name)}")
    return tuple(keys)


def _review_needed_assets(trade: dict[str, Any]) -> list[str]:
    review: list[str] = []
    for asset in [
        *trade.get("team_a_assets", []),
        *trade.get("team_b_assets", []),
        *trade.get("affected_picks", []),
    ]:
        if not isinstance(asset, dict):
            continue
        if str(asset.get("status") or "").upper() == "REVIEW_NEEDED":
            review.append(_text(asset.get("display_label") or asset.get("raw_text")))
    return [item for item in review if item]


def _join_pick_changes(value: Any) -> str:
    if not isinstance(value, list) or not value:
        return ""
    labels = []
    for row in value:
        if not isinstance(row, dict):
            continue
        pick = _text(row.get("pick_label") or row.get("display_label"))
        owner = _text(row.get("new_owner"))
        direction = _text(row.get("direction"))
        labels.append(" ".join(part for part in (pick, direction, owner) if part))
    return "; ".join(labels)


def _join_values(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, list):
        return "; ".join(_text(item) for item in value if _text(item))
    return _text(value)


def _normalize_name(value: Any) -> str:
    return "".join(ch for ch in _text(value).casefold() if ch.isalnum())


def _text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.endswith(".0"):
        return text[:-2]
    return text
