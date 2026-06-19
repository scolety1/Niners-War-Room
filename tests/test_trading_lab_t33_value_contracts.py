from dataclasses import fields

from src.trading_lab.trade_value_contracts import (
    PackageScore,
    PickAsset,
    PlayerAsset,
    TeamContext,
    TradePackage,
    TradeReview,
    TradeSide,
    ValueSnapshot,
)


def test_value_contracts_instantiate_with_fake_fantasy_values() -> None:
    player = PlayerAsset(
        asset_id="player-target",
        display_name="Target Player",
        position="WR",
        team_name="Team Alpha",
        nwr_value=88.0,
        public_market_value=72.0,
        scarcity_tag="starter",
        keeper_status="core",
        drop_pressure_tag="low",
        notes=("fake fixture",),
    )
    pick = PickAsset(
        asset_id="pick-2026-2",
        display_name="2026 2nd",
        team_name="NWR",
        nwr_value=23.0,
        public_market_value=25.0,
        rookie_pick_context="mid rookie pick",
    )

    assert player.display_name == "Target Player"
    assert pick.asset_type == "pick"
    assert player.nwr_value != player.public_market_value


def test_trade_package_supports_give_and_get_sides() -> None:
    give = TradeSide(
        team_name="NWR",
        assets=(
            PlayerAsset(
                asset_id="player-a",
                display_name="Player A",
                nwr_value=40.0,
                public_market_value=42.0,
            ),
        ),
    )
    get = TradeSide(
        team_name="Team Alpha",
        assets=(
            PlayerAsset(
                asset_id="target-player",
                display_name="Target Player",
                nwr_value=63.0,
                public_market_value=45.0,
            ),
        ),
    )
    package = TradePackage(
        package_id="pkg-1",
        mode="Trade For Player",
        give_side=give,
        get_side=get,
        opponent_context=TeamContext(team_name="Team Alpha"),
    )

    assert package.give_side.nwr_value_total == 40.0
    assert package.get_side.public_market_value_total == 45.0


def test_review_keeps_nwr_and_public_values_separate() -> None:
    package = TradePackage(
        package_id="pkg-2",
        mode="Trade Away Player",
        give_side=TradeSide(team_name="NWR", assets=()),
        get_side=TradeSide(team_name="Team Bravo", assets=()),
        opponent_context=TeamContext(team_name="Team Bravo"),
    )
    score = PackageScore(
        nwr_delta=12.0,
        public_market_delta=-1.0,
        market_fairness="fair",
        opponent_fit="medium",
        roster_impact="positive",
        keeper_drop_impact="neutral",
        risk_label="review",
    )
    review = TradeReview(package=package, score=score, verdict="manual review")

    assert review.score.nwr_delta == 12.0
    assert review.score.public_market_delta == -1.0
    assert review.review_status == "review"


def test_snapshot_has_fixture_only_source_note() -> None:
    snapshot = ValueSnapshot(
        snapshot_id="fixture-snapshot",
        assets=(),
        team_contexts=(TeamContext(team_name="Team Alpha"),),
    )

    assert snapshot.source_note == "fixture-only values"


def test_no_real_data_path_or_source_endpoint_field_exists() -> None:
    names = {
        field.name
        for cls in (PlayerAsset, PickAsset, TeamContext, TradePackage, ValueSnapshot)
        for field in fields(cls)
    }

    for blocked in ("path", "file", "url", "endpoint", "token", "secret", "key"):
        assert blocked not in names


def test_no_wall_street_language_exists_in_contract_repr() -> None:
    text = repr(
        PlayerAsset(
            asset_id="player-a",
            display_name="Player A",
            nwr_value=10.0,
            public_market_value=9.0,
        )
    ).lower()

    for blocked in ("stock", "broker", "equity", "crypto", "order execution"):
        assert blocked not in text
