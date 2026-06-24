from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.services.market_baseline_registry import (
    DISPLAY_LABEL,
    PAGE_USAGE,
    validate_market_baseline_registry,
)
from src.services.market_baseline_service import (
    DEFAULT_ARTIFACT_DIR,
    FRESH_STATUSES,
    compute_market_sanity_flags,
    get_pick_market_value,
    join_market_to_players,
    load_market_freshness,
    load_market_pick_context,
    load_market_player_context,
    summarize_market_gap,
)


@pytest.mark.skipif(
    not (DEFAULT_ARTIFACT_DIR / "dp_market_baseline_context.csv").exists(),
    reason="DynastyProcess derived artifacts have not been built",
)
def test_market_player_schema_required_columns() -> None:
    frame = load_market_player_context()
    expected = {
        "player",
        "pos",
        "dp_market_rank_1qb",
        "dp_value_1qb",
        "join_method",
        "join_confidence",
        "dp_display_only_warning",
        "freshness_status",
        "market_baseline_label",
    }
    assert expected.issubset(set(frame.columns))
    assert frame["market_baseline_label"].eq(DISPLAY_LABEL).all()


@pytest.mark.skipif(
    not (DEFAULT_ARTIFACT_DIR / "dp_pick_value_context.csv").exists(),
    reason="DynastyProcess derived artifacts have not been built",
)
def test_market_pick_schema_required_columns() -> None:
    frame = load_market_pick_context()
    expected = {"pick_label", "value_1qb", "ecr_1qb", "freshness_status"}
    assert expected.issubset(set(frame.columns))


@pytest.mark.skipif(
    not (DEFAULT_ARTIFACT_DIR / "dp_freshness_report.csv").exists(),
    reason="DynastyProcess freshness artifact has not been built",
)
def test_market_freshness_status_loading() -> None:
    freshness = load_market_freshness()
    assert freshness["freshness_status"] in FRESH_STATUSES
    assert freshness["upstream_scrape_date"]


@pytest.mark.skipif(
    not (DEFAULT_ARTIFACT_DIR / "dp_market_baseline_context.csv").exists(),
    reason="DynastyProcess derived artifacts have not been built",
)
def test_market_sanity_flag_computation_does_not_mutate_rank_columns() -> None:
    players = pd.DataFrame(
        [
            {"player": "Zay Flowers", "position": "WR", "nwr_candidate_rank": "2"},
            {"player": "Unknown Player", "position": "RB", "nwr_candidate_rank": "55"},
        ]
    )

    result = compute_market_sanity_flags(players)

    assert result.loc[0, "market_sanity_label"] in {
        "NWR much higher",
        "Aligned",
        "Market data stale",
    }
    assert result.loc[1, "market_sanity_label"] == "No market match"
    assert result["nwr_candidate_rank"].tolist() == ["2", "55"]


@pytest.mark.skipif(
    not (DEFAULT_ARTIFACT_DIR / "dp_market_baseline_context.csv").exists(),
    reason="DynastyProcess derived artifacts have not been built",
)
def test_join_market_to_players_preserves_order_and_adds_display_fields() -> None:
    players = pd.DataFrame(
        [
            {"player": "Unknown Player", "position": "RB"},
            {"player": "Brock Purdy", "position": "QB"},
        ]
    )

    result = join_market_to_players(players)

    assert result["player"].tolist() == ["Unknown Player", "Brock Purdy"]
    assert result["market_baseline_label"].eq(DISPLAY_LABEL).all()
    assert result.loc[0, "market_sanity_label"] == "No market match"


@pytest.mark.skipif(
    not (DEFAULT_ARTIFACT_DIR / "dp_pick_value_context.csv").exists(),
    reason="DynastyProcess pick artifact has not been built",
)
@pytest.mark.parametrize("pick_label", ["2026 1.04", "2026 2.03", "2028 1st"])
def test_pick_label_lookup_for_known_labels_if_data_exists(pick_label: str) -> None:
    picks = load_market_pick_context()
    if pick_label not in set(picks["pick_label"]):
        pytest.skip(f"{pick_label} is not in the current DynastyProcess pick artifact")

    row = get_pick_market_value(pick_label)

    assert row is not None
    assert row["pick_label"] == pick_label
    assert row["value_1qb"]


def test_registry_config_validity() -> None:
    assert validate_market_baseline_registry() == []
    assert PAGE_USAGE["player_compare"].model_input_allowed is False
    assert PAGE_USAGE["trading_lab"].sort_allowed is False


def test_no_market_fields_used_as_rank_or_model_inputs() -> None:
    for usage in PAGE_USAGE.values():
        assert usage.model_input_allowed is False
        assert usage.sort_allowed is False
        assert "candidate_rank_override" not in usage.fields_allowed
        assert "model_input" not in usage.fields_allowed


def test_service_rejects_forbidden_market_input_columns(tmp_path: Path) -> None:
    artifact_dir = tmp_path
    pd.DataFrame(
        [
            {
                "player": "Example",
                "pos": "WR",
                "dp_market_rank_1qb": "1",
                "dp_value_1qb": "9999",
                "join_method": "exact_name_position",
                "join_confidence": "medium",
                "dp_display_only_warning": "display-only",
                "freshness_status": "GREEN_CURRENT",
                "model_input": "true",
            }
        ]
    ).to_csv(artifact_dir / "dp_player_market_context.csv", index=False)

    with pytest.raises(ValueError, match="forbidden input columns"):
        load_market_player_context(artifact_dir)


def test_market_gap_summary_uses_display_language() -> None:
    summary = summarize_market_gap(
        {
            "nwr_candidate_rank": "2",
            "dp_market_rank_1qb": "41",
            "freshness_status": "GREEN_CURRENT",
        }
    )
    assert summary.startswith("NWR much higher")
