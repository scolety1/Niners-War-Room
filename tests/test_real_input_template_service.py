from __future__ import annotations

from src.services.real_input_template_service import (
    expected_template_headers,
    validate_real_input_templates,
)


def test_real_input_templates_match_runtime_headers() -> None:
    assert validate_real_input_templates() == ()


def test_real_input_templates_cover_all_input_groups() -> None:
    headers = expected_template_headers()

    assert set(headers) == {
        "data_pack",
        "veteran_model",
        "rookie_model",
        "historical_replay",
        "public_sources",
        "nflverse_stats_upgrade",
    }
    assert "model_outputs.csv" in headers["data_pack"]
    assert "veteran_feature_scores.csv" in headers["veteran_model"]
    assert "rookie_raw_metrics.csv" in headers["rookie_model"]
    assert "model_replay_inputs.csv" in headers["historical_replay"]
    assert "player_projection_inputs.csv" in headers["public_sources"]
    assert "nflverse_player_stats_weekly.csv" in headers["nflverse_stats_upgrade"]
    assert "lve_normalized_veteran_features.csv" in headers["nflverse_stats_upgrade"]
    assert "lve_normalized_feature_receipts.csv" in headers["nflverse_stats_upgrade"]
