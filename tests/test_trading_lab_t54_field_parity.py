from dataclasses import fields

from src.trading_lab.trade_lab_component import SCORE_LABELS
from src.trading_lab.trade_lab_fixtures import fixture_assets, fixture_team_contexts
from src.trading_lab.trade_lab_ui import TRADE_LAB_DATA_CHIPS
from src.trading_lab.trade_value_contracts import FantasyAsset, PackageScore, TeamContext


def test_fixture_objects_expose_required_contract_fields() -> None:
    asset_field_names = {field.name for field in fields(FantasyAsset)}
    team_field_names = {field.name for field in fields(TeamContext)}

    for expected in (
        "asset_id",
        "display_name",
        "asset_type",
        "nwr_value",
        "public_market_value",
        "keeper_status",
        "drop_pressure_tag",
        "rookie_pick_context",
    ):
        assert expected in asset_field_names

    for expected in ("team_name", "roster_needs", "surplus_tags", "trade_style"):
        assert expected in team_field_names


def test_fixture_instances_have_required_values() -> None:
    assets = fixture_assets()
    teams = fixture_team_contexts()

    assert all(asset.asset_id and asset.display_name for asset in assets)
    assert all(asset.nwr_value is not None for asset in assets)
    assert all(asset.public_market_value is not None for asset in assets)
    assert all(team.team_name for team in teams)


def test_every_ui_score_label_maps_to_fixture_or_contract_field() -> None:
    score_fields = {field.name for field in fields(PackageScore)}
    label_map = {
        "NWR Gain": "nwr_delta",
        "Market Fairness": "market_fairness",
        "Opponent Fit": "opponent_fit",
        "Roster Impact": "roster_impact",
        "Keeper/Drop Impact": "keeper_drop_impact",
        "Risk": "risk_label",
        "Verdict": "manual review verdict",
    }

    assert SCORE_LABELS == tuple(label_map)
    for label, mapped_field in label_map.items():
        assert label in SCORE_LABELS
        if mapped_field != "manual review verdict":
            assert mapped_field in score_fields


def test_future_only_fields_are_marked_placeholder_when_not_wired() -> None:
    text = " ".join(TRADE_LAB_DATA_CHIPS)

    assert "placeholder" in text
    assert "Manual review required" in text
