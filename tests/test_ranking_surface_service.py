from __future__ import annotations

from src.services.ranking_surface_audit_service import build_ranking_surface_audit
from src.services.ranking_surface_service import (
    DRAFT_AVAILABLE,
    FORCED_RELEASE_PAIN,
    KEEPER_DECISION,
    PURE_MODEL_VALUE,
    TRADE_LIQUIDITY,
    apply_ranking_surface,
    surface_for_id,
    surface_rows,
)

SAMPLE_PACK = "sample_data/2026_pre_declaration"


def test_ranking_surfaces_declare_rank_source_and_use() -> None:
    rows = surface_rows()

    assert {row["surface_id"] for row in rows} == {
        PURE_MODEL_VALUE,
        KEEPER_DECISION,
        TRADE_LIQUIDITY,
        FORCED_RELEASE_PAIN,
        DRAFT_AVAILABLE,
    }
    for row in rows:
        assert row["rank_source"]
        assert row["intended_use"]
        assert row["review_status"] == "review_only"


def test_pure_model_value_ignores_keeper_market_and_forced_release_context() -> None:
    rows = [
        _row("Market Darling", stats=70, market=100, edge=-30, action="keep"),
        _row("Best Football Row", stats=91, market=50, edge=41, action="shop"),
        _row("Keeper Context Row", stats=82, market=45, edge=37, action="drop"),
    ]

    ranked = apply_ranking_surface(rows, PURE_MODEL_VALUE)

    assert [row["player"] for row in ranked] == [
        "Best Football Row",
        "Keeper Context Row",
        "Market Darling",
    ]
    assert surface_for_id(PURE_MODEL_VALUE).rank_source == (
        "stats_value/private_lve_value descending"
    )


def test_keeper_decision_uses_roster_action_context_separately() -> None:
    rows = [
        _row("Pure Star", stats=95, action="keep", keeper=95, drop=5),
        _row("Forced Shop", stats=70, action="shop/release", keeper=62, drop=45),
        _row("Bubble", stats=80, action="bubble", keeper=70, drop=35),
    ]

    ranked = apply_ranking_surface(rows, KEEPER_DECISION)

    assert [row["player"] for row in ranked] == ["Forced Shop", "Bubble", "Pure Star"]


def test_trade_liquidity_surface_uses_market_disagreement_not_private_rank() -> None:
    rows = [
        _row("Small Gap Star", stats=95, market=94, edge=1),
        _row("Big Positive Gap", stats=80, market=55, edge=25),
        _row("Big Negative Gap", stats=75, market=98, edge=-23),
    ]

    ranked = apply_ranking_surface(rows, TRADE_LIQUIDITY)

    assert [row["player"] for row in ranked] == [
        "Big Positive Gap",
        "Big Negative Gap",
        "Small Gap Star",
    ]


def test_forced_release_pain_surface_only_ranks_team_top_five_candidates() -> None:
    rows = [
        _row("Team A Easy Drop", team="A", league_rank=5, keeper=45, drop=55),
        _row("Team A Non Top Five", team="A", league_rank=90, keeper=10, drop=95),
        _row("Team A Stud", team="A", league_rank=10, keeper=95, drop=5),
        _row("Team A Fourth", team="A", league_rank=20, keeper=80, drop=12),
        _row("Team A Fifth", team="A", league_rank=30, keeper=75, drop=14),
        _row("Team A Fifth Better Rank", team="A", league_rank=35, keeper=74, drop=13),
        _row("Team A Sixth", team="A", league_rank=40, keeper=70, drop=15),
        _row("Team B Painful", team="B", league_rank=1, keeper=88, drop=35),
    ]

    ranked = apply_ranking_surface(rows, FORCED_RELEASE_PAIN)
    players = [row["player"] for row in ranked]

    assert "Team A Non Top Five" not in players
    assert "Team A Sixth" not in players
    assert players[0] == "Team A Easy Drop"


def test_draft_available_surface_excludes_drafted_players() -> None:
    rows = [
        {"player": "Available Rookie", "draft_status": "available", "draft_value": 90},
        {"player": "Drafted Rookie", "draft_status": "drafted", "draft_value": 99},
    ]

    ranked = apply_ranking_surface(rows, DRAFT_AVAILABLE)

    assert [row["player"] for row in ranked] == ["Available Rookie"]


def test_ranking_surface_audit_exports_included_excluded_and_leakage_rows() -> None:
    report = build_ranking_surface_audit(SAMPLE_PACK)

    assert report.surface_rows
    assert report.excluded_rows
    assert report.summary_rows
    assert {row["board_name"] for row in report.summary_rows} >= {
        "Pure Model Value",
        "Keeper Decision",
        "Trade/Liquidity",
        "Forced-Release Pain",
        "Draft Board / Available Players Only",
    }
    assert not report.leakage_rows


def test_ranking_surface_audit_proves_forced_release_excludes_non_top_five() -> None:
    report = build_ranking_surface_audit(SAMPLE_PACK)

    forced_exclusions = [
        row
        for row in report.excluded_rows
        if row["surface_id"] == FORCED_RELEASE_PAIN
    ]
    assert forced_exclusions
    assert all("not inside" in str(row["excluded_reason"]) for row in forced_exclusions)


def _row(
    player: str,
    *,
    stats: float = 50,
    market: float = 50,
    edge: float = 0,
    action: str = "keep",
    keeper: float = 50,
    drop: float = 50,
    team: str = "T",
    league_rank: int = 1,
) -> dict[str, object]:
    return {
        "player": player,
        "stats_value": stats,
        "market_value": market,
        "market_edge": edge,
        "action": action,
        "keeper_score": keeper,
        "drop_score": drop,
        "team": team,
        "league_rank": league_rank,
    }
