from __future__ import annotations

from src.services.player_lifecycle_service import (
    ESTABLISHED_VETERAN,
    INCOMING_ROOKIE,
    RELEASED_VETERAN,
    YEAR_ONE_NFL_BRIDGE,
    YEAR_THREE_NFL_BRIDGE,
    YEAR_TWO_NFL_BRIDGE,
    YOUNG_NFL_BRIDGE,
    add_lifecycle_fields,
    asset_lifecycle_for_row,
    asset_lifecycle_label,
    is_young_nfl_bridge_lifecycle,
)


def test_luther_kaleb_and_jayden_are_young_bridge_assets() -> None:
    for player_name, position in (
        ("Luther Burden", "WR"),
        ("Kaleb Johnson", "RB"),
        ("Jayden Higgins", "WR"),
    ):
        assert (
            asset_lifecycle_for_row(
                {
                    "player_name": player_name,
                    "position": position,
                    "experience_bucket": "year_one_nfl_player",
                    "young_nfl_bridge_weight": "0.35",
                }
            )
            == YEAR_ONE_NFL_BRIDGE
        )


def test_incoming_rookies_and_available_veterans_keep_separate_lanes() -> None:
    assert asset_lifecycle_for_row({"asset_type": "rookie"}) == INCOMING_ROOKIE
    assert asset_lifecycle_for_row({"asset_type": "released_veteran"}) == RELEASED_VETERAN
    assert (
        asset_lifecycle_for_row({"experience_bucket": "established_veteran"})
        == ESTABLISHED_VETERAN
    )


def test_lifecycle_fields_include_user_facing_label() -> None:
    row = add_lifecycle_fields({"asset_type": "rookie"})

    assert row["asset_lifecycle"] == "incoming_rookie"
    assert row["asset_lifecycle_label"] == "Incoming Rookie"


def test_young_bridge_lifecycle_labels_are_year_specific() -> None:
    assert (
        asset_lifecycle_for_row({"experience_bucket": "year_one_nfl_player"})
        == YEAR_ONE_NFL_BRIDGE
    )
    assert (
        asset_lifecycle_for_row({"experience_bucket": "year_two_nfl_player"})
        == YEAR_TWO_NFL_BRIDGE
    )
    assert (
        asset_lifecycle_for_row({"experience_bucket": "year_three_nfl_player"})
        == YEAR_THREE_NFL_BRIDGE
    )
    assert asset_lifecycle_label(YEAR_ONE_NFL_BRIDGE) == "Year-One NFL Bridge"
    assert asset_lifecycle_label(YEAR_TWO_NFL_BRIDGE) == "Year-Two NFL Bridge"
    assert asset_lifecycle_label(YEAR_THREE_NFL_BRIDGE) == "Year-Three NFL Bridge"


def test_legacy_young_bridge_label_still_counts_as_bridge_family() -> None:
    assert is_young_nfl_bridge_lifecycle(YOUNG_NFL_BRIDGE) is True
    assert is_young_nfl_bridge_lifecycle(YEAR_ONE_NFL_BRIDGE) is True
    assert is_young_nfl_bridge_lifecycle(ESTABLISHED_VETERAN) is False
