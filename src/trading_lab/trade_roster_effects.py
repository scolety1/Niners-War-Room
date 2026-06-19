from __future__ import annotations

from src.trading_lab.trade_lab_ui import RosterAftermath
from src.trading_lab.trade_value_contracts import TradeReview

REAL_ROSTER_INTEGRATION_WIRED = False
ROSTER_INTEGRATION_STATUS = "Real roster integrations are not wired yet."


def estimate_keeper_impact(review: TradeReview) -> str:
    received_core = [
        asset.display_name
        for asset in review.package.get_side.assets
        if "core" in asset.keeper_status
    ]
    given_core = [
        asset.display_name
        for asset in review.package.give_side.assets
        if asset.keeper_status == "core"
    ]
    if received_core and not given_core:
        return f"Keeper core improves with {', '.join(received_core)}."
    if given_core:
        return f"Keeper core risk from moving {', '.join(given_core)}."
    return "Keeper impact requires manual review."


def estimate_drop_pressure_impact(review: TradeReview) -> tuple[str, str, str]:
    given_high = [
        asset.display_name
        for asset in review.package.give_side.assets
        if asset.drop_pressure_tag == "high"
    ]
    received_high = [
        asset.display_name
        for asset in review.package.get_side.assets
        if asset.drop_pressure_tag == "high"
    ]
    before = "Fixture roster has one drop-pressure item to review."
    if given_high and not received_high:
        return before, "Drop pressure improves after moving high-pressure depth.", "improves"
    if received_high:
        return before, "Drop pressure increases after adding high-pressure depth.", "worsens"
    return before, "Drop pressure remains a manual review item.", "neutral"


def estimate_position_depth_impact(review: TradeReview) -> tuple[str, str, str]:
    give_positions = [asset.position for asset in review.package.give_side.assets if asset.position]
    get_positions = [asset.position for asset in review.package.get_side.assets if asset.position]
    before = f"Before: giving from {', '.join(give_positions) or 'no position'}."
    after = f"After: receiving {', '.join(get_positions) or 'no position'}."
    if len(get_positions) < len(give_positions):
        return before, after, "Depth consolidates into fewer roster slots."
    if len(get_positions) > len(give_positions):
        return before, after, "Depth volume increases and may need review."
    return before, after, "Depth count stays balanced."


def estimate_rookie_pick_context(review: TradeReview) -> str:
    pick_notes = [
        asset.rookie_pick_context
        for asset in (*review.package.give_side.assets, *review.package.get_side.assets)
        if asset.asset_type == "pick"
    ]
    if pick_notes:
        return "; ".join(pick_notes)
    return "Rookie/mock draft context placeholder; real integration not wired yet."


def build_roster_aftermath(review: TradeReview) -> RosterAftermath:
    drop_before, drop_after, drop_label = estimate_drop_pressure_impact(review)
    depth_before, depth_after, depth_label = estimate_position_depth_impact(review)
    give_names = tuple(asset.display_name for asset in review.package.give_side.assets)
    get_names = tuple(asset.display_name for asset in review.package.get_side.assets)
    return RosterAftermath(
        summary=f"Fixture aftermath for {review.package.mode}: review roster shape manually.",
        keeper_impact=estimate_keeper_impact(review),
        drop_pressure_impact=f"Drop pressure {drop_label}.",
        positional_depth_impact=depth_label,
        rookie_mock_context=estimate_rookie_pick_context(review),
        keeper_core_before=give_names or ("No outgoing assets",),
        keeper_core_after=get_names or ("No incoming assets",),
        drop_pressure_before=drop_before,
        drop_pressure_after=drop_after,
        positional_depth_before=depth_before,
        positional_depth_after=depth_after,
        mock_draft_placeholder="Mock draft context is not wired yet.",
        roster_risk_notes=("Fixture-only roster aftermath.", ROSTER_INTEGRATION_STATUS),
        needs_real_integration_note=ROSTER_INTEGRATION_STATUS,
    )
