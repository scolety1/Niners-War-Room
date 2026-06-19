from __future__ import annotations

from src.trading_lab.trade_value_contracts import (
    FantasyAsset,
    PickAsset,
    PlayerAsset,
    TeamContext,
    ValueSnapshot,
)

FIXTURE_SOURCE_NOTE = "fixture-only fake fantasy trade values"

FAKE_PLAYER_ASSETS = (
    PlayerAsset(
        asset_id="target-player",
        display_name="Target Player",
        position="WR",
        team_name="Team Alpha",
        nwr_value=82.0,
        public_market_value=70.0,
        scarcity_tag="starter-upside",
        keeper_status="core candidate",
        drop_pressure_tag="low",
        notes=("fake target",),
    ),
    PlayerAsset(
        asset_id="player-a",
        display_name="Player A",
        position="RB",
        team_name="NWR",
        nwr_value=45.0,
        public_market_value=44.0,
        scarcity_tag="depth",
        keeper_status="fringe keeper",
        drop_pressure_tag="medium",
    ),
    PlayerAsset(
        asset_id="player-b",
        display_name="Player B",
        position="WR",
        team_name="NWR",
        nwr_value=60.0,
        public_market_value=58.0,
        scarcity_tag="scarce starter",
        keeper_status="core",
        drop_pressure_tag="low",
    ),
    PlayerAsset(
        asset_id="player-c",
        display_name="Player C",
        position="TE",
        team_name="Team Bravo",
        nwr_value=34.0,
        public_market_value=38.0,
        scarcity_tag="volatile depth",
        keeper_status="review",
        drop_pressure_tag="medium",
    ),
    PlayerAsset(
        asset_id="player-d",
        display_name="Player D",
        position="RB",
        team_name="Team Charlie",
        nwr_value=21.0,
        public_market_value=24.0,
        scarcity_tag="bench",
        keeper_status="not core",
        drop_pressure_tag="high",
    ),
)

FAKE_PICK_ASSETS = (
    PickAsset(
        asset_id="pick-2026-2",
        display_name="2026 2nd",
        team_name="NWR",
        nwr_value=27.0,
        public_market_value=29.0,
        scarcity_tag="rookie capital",
        drop_pressure_tag="none",
        rookie_pick_context="mid rookie pick placeholder",
    ),
    PickAsset(
        asset_id="pick-2026-3",
        display_name="2026 3rd",
        team_name="NWR",
        nwr_value=13.0,
        public_market_value=14.0,
        scarcity_tag="rookie depth",
        drop_pressure_tag="none",
        rookie_pick_context="late rookie pick placeholder",
    ),
)

FAKE_TEAM_CONTEXTS = (
    TeamContext(
        team_name="Team Alpha",
        roster_needs=("RB depth", "future pick"),
        surplus_tags=("WR starter",),
        trade_style="values depth packages",
        notes=("fake opponent context",),
    ),
    TeamContext(
        team_name="Team Bravo",
        roster_needs=("WR starter",),
        surplus_tags=("rookie pick", "TE depth"),
        trade_style="prefers balanced offers",
        notes=("fake contender context",),
    ),
    TeamContext(
        team_name="Team Charlie",
        roster_needs=("bench depth",),
        surplus_tags=("RB depth",),
        trade_style="open to pick conversion",
        notes=("fake rebuilding context",),
    ),
)


def fixture_assets() -> tuple[FantasyAsset, ...]:
    return (*FAKE_PLAYER_ASSETS, *FAKE_PICK_ASSETS)


def fixture_players() -> tuple[PlayerAsset, ...]:
    return FAKE_PLAYER_ASSETS


def fixture_picks() -> tuple[PickAsset, ...]:
    return FAKE_PICK_ASSETS


def fixture_team_contexts() -> tuple[TeamContext, ...]:
    return FAKE_TEAM_CONTEXTS


def fixture_value_snapshot() -> ValueSnapshot:
    return ValueSnapshot(
        snapshot_id="trade-lab-fixture-snapshot",
        assets=fixture_assets(),
        team_contexts=fixture_team_contexts(),
        source_note=FIXTURE_SOURCE_NOTE,
    )


def asset_by_name(display_name: str) -> FantasyAsset:
    for asset in fixture_assets():
        if asset.display_name == display_name:
            return asset
    raise ValueError(f"Unknown fixture asset: {display_name}")


def team_context_by_name(team_name: str) -> TeamContext:
    for context in fixture_team_contexts():
        if context.team_name == team_name:
            return context
    raise ValueError(f"Unknown fixture team: {team_name}")
