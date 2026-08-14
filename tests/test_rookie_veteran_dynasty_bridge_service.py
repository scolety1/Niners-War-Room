from __future__ import annotations

from src.services.rookie_veteran_dynasty_bridge_service import (
    INSUFFICIENT,
    PRODUCTION,
    RESEARCH_ONLY,
    RedraftBridgeContext,
    build_rookie_veteran_bridge,
    load_redraft_bridge_context,
    owner_redraft_profile,
)


def _row(
    asset_id: str,
    player: str,
    asset_type: str,
    player_id: str,
    *,
    research_rank: object = 10,
    outlook_3y: object = 80,
    outlook_5y: object = 180,
    ceiling: object = 0.8,
) -> dict[str, object]:
    return {
        "asset_id": asset_id,
        "player": player,
        "compare_asset_type": asset_type,
        "governed_player_id": player_id,
        "nwr_rank": 20 if asset_type == "Current Player" else "",
        "research_rank": research_rank,
        "research_outlook_3y": outlook_3y,
        "research_outlook_5y": outlook_5y,
        "research_ceiling_signal": ceiling,
        "model_score_eligible": asset_type != "Blocked Rookie",
        "draft_round": 1 if asset_type != "Current Player" else "",
        "overall_pick": 8 if asset_type != "Current Player" else "",
    }


def _context() -> RedraftBridgeContext:
    return RedraftBridgeContext(
        by_player_id={
            "00-vet": {
                "player": "Veteran",
                "projected_points": 210.0,
                "overall_rank": 15,
                "position_rank": 8,
                "replacement_points": 150.0,
                "replacement_adjusted_value": 60.0,
                "confidence": "HIGH",
                "rookie": False,
                "source_as_of": "2026-08-09",
                "availability_probability": 0.9,
            },
            "00-rook": {
                "player": "Rookie",
                "projected_points": 180.0,
                "overall_rank": 35,
                "position_rank": 18,
                "replacement_points": 150.0,
                "replacement_adjusted_value": 30.0,
                "confidence": "LOW",
                "rookie": True,
                "source_as_of": "2026-08-09",
                "availability_probability": 0.75,
            },
        },
        source_sha256="test",
        source_as_of="2026-08-09",
        errors=(),
    )


def test_owner_profile_is_exactly_ten_team_one_qb_and_not_superflex() -> None:
    profile = owner_redraft_profile()

    assert profile.team_count == 10
    assert profile.roster.qb == 1
    assert profile.roster.superflex == 0
    assert profile.roster.rb == 2
    assert profile.roster.wr == 3
    assert profile.roster.te == 1
    assert profile.roster.flex == 2
    assert profile.scoring.passing_yards == 1.0 / 30.0
    assert profile.scoring.rushing_first_down == 0.4
    assert profile.scoring.receiving_first_down == 0.4


def test_mixed_pair_uses_production_only_for_win_now() -> None:
    rows = [
        _row("veteran", "Veteran", "Current Player", "00-vet", research_rank=15),
        _row("rookie", "Rookie", "Rookie Review", "00-rook", research_rank=5),
    ]

    first = build_rookie_veteran_bridge(rows, redraft_context=_context())
    second = build_rookie_veteran_bridge(rows, redraft_context=_context())

    assert first is not None
    assert first == second
    decisions = {row.key: row for row in first.decisions}
    assert decisions["win_now"].preferred == "Veteran"
    assert decisions["win_now"].badge == PRODUCTION
    assert decisions["dynasty_today"].preferred == "Rookie"
    assert decisions["dynasty_today"].badge == RESEARCH_ONLY
    assert decisions["long_term"].label == "LONG-TERM / 5Y"
    assert decisions["safety"].preferred == "Veteran"
    assert decisions["uncertainty"].preferred == "Rookie"
    assert "players" in first.as_payload()
    assert any("not directly comparable" in warning for warning in first.warnings)


def test_refresh_candidate_evidence_is_disclosed_without_changing_review_authority() -> None:
    veteran = _row("veteran", "Veteran", "Current Player", "00-vet")
    rookie = _row("rookie", "Rookie", "Rookie Review", "00-rook")
    rookie["refresh_available"] = True

    bridge = build_rookie_veteran_bridge([veteran, rookie], redraft_context=_context())

    assert bridge is not None
    assert any("refresh-candidate" in warning for warning in bridge.warnings)
    assert next(row for row in bridge.decisions if row.key == "safety").badge == "REVIEW"


def test_missing_redraft_and_research_remain_unavailable_not_zero() -> None:
    rows = [
        _row("veteran", "Veteran", "Current Player", "", research_rank="", outlook_3y=""),
        _row("rookie", "Manual Rookie", "Blocked Rookie", "", research_rank="", outlook_3y=""),
    ]
    bridge = build_rookie_veteran_bridge(
        rows,
        redraft_context=RedraftBridgeContext({}, "", "", ()),
    )

    assert bridge is not None
    decisions = {row.key: row for row in bridge.decisions}
    assert decisions["win_now"].preferred == INSUFFICIENT
    assert decisions["three_year"].preferred == INSUFFICIENT
    assert all(row.projected_points is None for row in bridge.immediate_production)
    assert decisions["uncertainty"].preferred == "Manual Rookie"
    assert "manual-review" in decisions["uncertainty"].reason


def test_same_authority_pairs_do_not_activate_bridge_mode() -> None:
    veterans = [
        _row("a", "A", "Current Player", "00-vet"),
        _row("b", "B", "Current Player", "00-rook"),
    ]
    rookies = [
        _row("a", "A", "Rookie Review", "00-vet"),
        _row("b", "B", "Rookie Review", "00-rook"),
    ]

    assert build_rookie_veteran_bridge(veterans, redraft_context=_context()) is None
    assert build_rookie_veteran_bridge(rookies, redraft_context=_context()) is None


def test_exact_governed_ids_do_not_require_a_gsis_prefix() -> None:
    context = RedraftBridgeContext(
        {
            "MEN516487": {
                "player": "Fernando Mendoza",
                "projected_points": 149.5,
                "overall_rank": 379,
                "position_rank": 25,
                "replacement_points": 182.47,
                "replacement_adjusted_value": -32.97,
                "confidence": "LOW",
                "rookie": True,
                "source_as_of": "2026-07-30",
                "availability_probability": 0.7647,
            }
        },
        "test",
        "2026-07-30",
        (),
    )
    row = _row("mendoza", "Fernando Mendoza", "Rookie Review", "MEN516487")
    veteran = _row("veteran", "Veteran", "Current Player", "00-vet")
    context = RedraftBridgeContext(
        {**_context().by_player_id, **context.by_player_id}, "test", "", ()
    )

    bridge = build_rookie_veteran_bridge([row, veteran], redraft_context=context)

    assert bridge is not None
    mendoza = next(
        value
        for value in bridge.immediate_production
        if value.player == "Fernando Mendoza"
    )
    assert mendoza.available is True
    assert mendoza.replacement_adjusted_value == -32.97


def test_tracked_redraft_bridge_is_currently_computable() -> None:
    context = load_redraft_bridge_context()

    assert context.errors == ()
    assert len(context.by_player_id) == 608
    assert context.source_sha256
