from __future__ import annotations

from src.services.dynasty_trade_counter_service import generate_dynasty_trade_counters


def _row(asset_id: str, name: str, rank: int, position: str, market_rank: int) -> dict[str, object]:
    return {
        "item_key": f"registry:{asset_id}",
        "asset_id": asset_id,
        "asset_type": "Player",
        "registry_asset_type": "Current Player",
        "label": name,
        "player": name,
        "position": position,
        "position_rank": f"{position}{rank}",
        "age": 25,
        "dynasty_rank": rank,
        "market_dp_rank": market_rank,
        "market_status": "Current display-only fixture",
        "owner_caveats": (),
        "outcome_signals": (),
        "redraft_available": True,
        "redraft_vbd": 50,
        "redraft_projected_points": 200,
        "research_outlook_3y": 60,
        "current_status_override": None,
    }


def _fixture():
    rows = [
        _row("current:o1", "Owner One", 12, "WR", 18),
        _row("current:o2", "Owner Two", 28, "RB", 30),
        _row("current:o3", "Owner Three", 42, "WR", 50),
        _row("current:o4", "Owner Four", 65, "TE", 62),
        _row("current:x1", "Target Anchor", 15, "RB", 10),
        _row("current:x2", "Opponent Two", 35, "WR", 44),
        _row("current:x3", "Opponent Three", 58, "TE", 55),
        _row("current:x4", "Opponent Four", 82, "WR", 90),
    ]
    lookup = {str(row["item_key"]): row for row in rows}
    key_for_id = {str(row["asset_id"]): str(row["item_key"]) for row in rows}
    return lookup, key_for_id


def test_dynasty_counters_preserve_anchor_and_never_cross_roster_ownership() -> None:
    lookup, key_for_id = _fixture()
    owner_ids = ("current:o1", "current:o2", "current:o3", "current:o4")
    opponent_ids = ("current:x1", "current:x2", "current:x3", "current:x4")
    result = generate_dynasty_trade_counters(
        original_give_ids=("current:o1", "current:o2"),
        original_receive_ids=("current:x1",),
        owner_asset_ids=owner_ids,
        opponent_asset_ids=opponent_ids,
        lookup=lookup,
        key_for_id=key_for_id,
        team_window="Balanced",
        owner_need_positions=("RB",),
        opponent_need_positions=("WR",),
    )
    assert 1 <= len(result.candidates) <= 5
    assert result.preserved_anchor_id == "current:x1"
    for candidate in result.candidates:
        assert "current:x1" in candidate.receive
        assert set(candidate.give).issubset(owner_ids)
        assert set(candidate.receive).issubset(opponent_ids)
        assert candidate.changes
        assert candidate.nwr_vs_market
        combined = (
            candidate.why_it_helps_you
            + candidate.why_it_may_make_sense_for_them
            + candidate.main_risk
        ).casefold()
        assert "acceptance probability" not in combined
        assert "likely to accept" not in combined


def test_dynasty_counters_reject_wrong_counterparty_assets() -> None:
    lookup, key_for_id = _fixture()
    try:
        generate_dynasty_trade_counters(
            original_give_ids=("current:o1",),
            original_receive_ids=("current:o2",),
            owner_asset_ids=("current:o1", "current:o2"),
            opponent_asset_ids=("current:x1", "current:x2"),
            lookup=lookup,
            key_for_id=key_for_id,
            team_window="Balanced",
        )
    except ValueError as exc:
        assert "selected opponent roster" in str(exc)
    else:
        raise AssertionError("wrong-counterparty incoming asset must be rejected")
