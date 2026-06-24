from __future__ import annotations

from src.services.nfl_usage_derived_feature_service import (
    derive_usage_features,
    derived_field_inventory_rows,
    proxy_vs_true_rows,
)


def test_red_zone_inside_10_inside_5_thresholds_and_touch_formulas() -> None:
    rows = [
        {
            "season": "2025",
            "week": "1",
            "posteam": "SF",
            "yardline_100": "20",
            "play_type": "run",
            "rush_attempt": "1",
            "rusher_player_id": "rb1",
            "rusher_player_name": "Back One",
            "receiver_player_id": "",
            "receiver_player_name": "",
            "first_down_rush": "1",
        },
        {
            "season": "2025",
            "week": "1",
            "posteam": "SF",
            "yardline_100": "10",
            "pass_attempt": "1",
            "complete_pass": "1",
            "rusher_player_id": "",
            "rusher_player_name": "",
            "receiver_player_id": "wr1",
            "receiver_player_name": "Wide One",
            "first_down_pass": "1",
        },
        {
            "season": "2025",
            "week": "1",
            "posteam": "SF",
            "yardline_100": "5",
            "play_type": "run",
            "rush_attempt": "1",
            "rusher_player_id": "rb1",
            "rusher_player_name": "Back One",
            "receiver_player_id": "",
            "receiver_player_name": "",
        },
    ]

    result = derive_usage_features(rows)
    by_player = {row["player_name"]: row for row in result.rows}

    assert result.status == "AVAILABLE_REVIEW_ONLY"
    assert by_player["Back One"]["carries"] == 2
    assert by_player["Back One"]["touches"] == 2
    assert by_player["Back One"]["red_zone_carries"] == 2
    assert by_player["Back One"]["inside_10_carries"] == 1
    assert by_player["Back One"]["inside_5_carries"] == 1
    assert by_player["Wide One"]["targets"] == 1
    assert by_player["Wide One"]["receptions"] == 1
    assert by_player["Wide One"]["inside_10_targets"] == 1
    assert by_player["Wide One"]["inside_5_targets"] == 0
    assert by_player["Wide One"]["model_input_allowed"] == "no"
    assert by_player["Wide One"]["app_wiring_allowed"] == "no"


def test_missing_required_pbp_fields_fail_closed() -> None:
    result = derive_usage_features([{"season": "2025"}])

    assert result.status == "QUARANTINED_MISSING_REQUIRED_FIELDS"
    assert result.rows == ()
    assert result.validation_rows[0]["validation_status"] == "RED"


def test_proxy_labels_never_claim_true_tprr_or_yprr() -> None:
    text = " ".join(str(row) for row in proxy_vs_true_rows()).lower()

    assert "licensed-data gap" in text
    assert "blocked_label" in text
    assert "true tprr" in text
    assert "approved_label': 'targets per route proxy" in text


def test_derived_inventory_has_no_app_or_model_permission() -> None:
    rows = derived_field_inventory_rows()

    assert rows
    assert {row["model_input_allowed"] for row in rows} == {"no"}
    assert {row["app_wiring_allowed"] for row in rows} == {"no"}
    assert next(row for row in rows if row["field_name"] == "first_downs_per_touch")[
        "field_type"
    ] == "DERIVED_PROXY"
