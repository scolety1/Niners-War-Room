from __future__ import annotations

from src.services.draft_day_trade_lab_service import (
    add_trade_item,
    build_registry_trade_item_lookup,
    empty_trade_state,
    pick_context_options,
    player_options,
    review_trade_package,
    trade_item_rows,
)


def _asset(asset_id: str, asset_type: str, name: str, rank: str = "") -> dict[str, str]:
    return {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "asset_name": name,
        "position": "WR" if "pick:" not in asset_id else "PICK",
        "team": "SFO",
        "source_label": "Test governed source",
        "authority_status": "Context-Only" if "Pick" in asset_type else "Review-Only",
        "rank_label": "Source rank",
        "rank_value": rank,
        "tier": "",
        "score_label": "No common value",
        "score_value": "",
        "confidence": "High",
        "warnings": "",
        "blocking_reason": "",
        "comparison_scope": "Source-separated only; no player-value equivalence",
    }


def test_governed_trade_builder_supports_veteran_rookie_and_future_pick() -> None:
    rows = (
        _asset("current:v1", "Current Player", "Veteran One", "12"),
        _asset("rookie:r1", "Rookie Review", "Rookie One", "4"),
        _asset("pick:2027:1st", "Future Pick", "2027 1st"),
    )
    lookup = build_registry_trade_item_lookup(rows)
    players = player_options(lookup)
    picks = pick_context_options(lookup)

    state = empty_trade_state()
    state = add_trade_item(state, "give", players[next(k for k in players if "Veteran" in k)])
    state = add_trade_item(state, "get", players[next(k for k in players if "Rookie" in k)])
    state = add_trade_item(state, "get", picks[next(k for k in picks if "2027 1st" in k)])

    selected = trade_item_rows(state, lookup)
    assert set(selected["asset_id"]) == {"current:v1", "rookie:r1", "pick:2027:1st"}
    assert review_trade_package(state, lookup).status == "Context ready for manual review"
    assert selected.loc[selected["asset_id"] == "pick:2027:1st", "dynasty_rank"].iloc[0] == ""
