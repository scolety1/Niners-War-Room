from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.services.dynastyprocess_generation_service import (
    OUTPUT_FILE_NAMES,
    expected_safe_root,
    publish_generation,
)
from src.services.market_baseline_registry import (
    DISPLAY_LABEL,
    PAGE_USAGE,
    validate_market_baseline_registry,
)
from src.services.market_baseline_service import (
    FRESH_STATUSES,
    compute_market_sanity_flags,
    get_pick_market_value,
    join_market_to_players,
    load_market_freshness,
    load_market_pick_context,
    load_market_player_context,
    summarize_market_gap,
)


@pytest.fixture
def market_generation(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    root = expected_safe_root(repo)
    market = pd.DataFrame(
        [
            {
                "player": "Zay Flowers",
                "pos": "WR",
                "nwr_name": "Zay Flowers",
                "nwr_pos": "WR",
                "dp_market_rank_1qb": "22",
                "dp_value_1qb": "5100",
                "ecr_pos": "WR11",
                "age": "25",
                "join_method": "exact_name_position",
                "join_confidence": "medium",
                "dp_display_only_warning": "display-only",
                "freshness_status": "GREEN_CURRENT",
            },
            {
                "player": "Brock Purdy",
                "pos": "QB",
                "nwr_name": "Brock Purdy",
                "nwr_pos": "QB",
                "dp_market_rank_1qb": "45",
                "dp_value_1qb": "3800",
                "ecr_pos": "QB9",
                "age": "26",
                "join_method": "exact_name_position",
                "join_confidence": "medium",
                "dp_display_only_warning": "display-only",
                "freshness_status": "GREEN_CURRENT",
            },
        ]
    )
    picks = pd.DataFrame(
        [
            {
                "pick_label": label,
                "value_1qb": str(4000 - index * 500),
                "ecr_1qb": str(index + 1),
                "freshness_status": "GREEN_CURRENT",
            }
            for index, label in enumerate(("2026 1.04", "2026 2.03", "2028 1st"))
        ]
    )
    freshness = pd.DataFrame(
        [
            {
                "nwr_fetch_timestamp": "2026-07-29T00:00:00+00:00",
                "upstream_scrape_date": "2026-07-25",
                "upstream_latest_commit_sha": "synthetic",
                "upstream_latest_commit_timestamp": "2026-07-25T00:00:00+00:00",
                "freshness_status": "GREEN_CURRENT",
            }
        ]
    )
    frames = {
        "dp_market_baseline_context.csv": market,
        "dp_pick_value_context.csv": picks,
        "dp_freshness_report.csv": freshness,
        "dp_nwr_join_coverage.csv": pd.DataFrame([{"source_name": "synthetic"}]),
        "dp_playerid_crosswalk_audit.csv": pd.DataFrame([{"player": "synthetic"}]),
    }
    assert set(frames) == set(OUTPUT_FILE_NAMES)
    publish_generation(
        {
            name: frame.to_csv(index=False).encode()
            for name, frame in frames.items()
        },
        safe_root=root,
        repo_root=repo,
        run_id="market-test",
        generation_id="market-test-generation",
    )
    return root


def test_market_player_schema_required_columns(market_generation: Path) -> None:
    frame = load_market_player_context(market_generation)
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


def test_market_pick_schema_required_columns(market_generation: Path) -> None:
    frame = load_market_pick_context(market_generation)
    expected = {"pick_label", "value_1qb", "ecr_1qb", "freshness_status"}
    assert expected.issubset(set(frame.columns))


def test_market_freshness_status_loading(market_generation: Path) -> None:
    freshness = load_market_freshness(market_generation)
    assert freshness["freshness_status"] in FRESH_STATUSES
    assert freshness["upstream_scrape_date"]


def test_market_sanity_flag_computation_does_not_mutate_rank_columns(
    market_generation: Path,
) -> None:
    players = pd.DataFrame(
        [
            {"player": "Zay Flowers", "position": "WR", "nwr_candidate_rank": "2"},
            {"player": "Unknown Player", "position": "RB", "nwr_candidate_rank": "55"},
        ]
    )

    result = compute_market_sanity_flags(players, market_generation)

    assert result.loc[0, "market_sanity_label"] in {
        "NWR much higher",
        "Aligned",
        "Market data stale",
    }
    assert result.loc[1, "market_sanity_label"] == "No market match"
    assert result["nwr_candidate_rank"].tolist() == ["2", "55"]


def test_join_market_to_players_preserves_order_and_adds_display_fields(
    market_generation: Path,
) -> None:
    players = pd.DataFrame(
        [
            {"player": "Unknown Player", "position": "RB"},
            {"player": "Brock Purdy", "position": "QB"},
        ]
    )

    result = join_market_to_players(players, market_generation)

    assert result["player"].tolist() == ["Unknown Player", "Brock Purdy"]
    assert result["market_baseline_label"].eq(DISPLAY_LABEL).all()
    assert result.loc[0, "market_sanity_label"] == "No market match"


@pytest.mark.parametrize("pick_label", ["2026 1.04", "2026 2.03", "2028 1st"])
def test_pick_label_lookup_for_known_labels_if_data_exists(
    pick_label: str,
    market_generation: Path,
) -> None:
    picks = load_market_pick_context(market_generation)
    assert pick_label in set(picks["pick_label"])

    row = get_pick_market_value(pick_label, market_generation)

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
    repo = tmp_path / "repo"
    repo.mkdir()
    artifact_dir = expected_safe_root(repo)
    market = pd.DataFrame(
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
    )
    frames = {
        "dp_market_baseline_context.csv": market,
        "dp_pick_value_context.csv": pd.DataFrame(
            [
                {
                    "pick_label": "2026 1.01",
                    "value_1qb": "5000",
                    "ecr_1qb": "1",
                    "freshness_status": "GREEN_CURRENT",
                }
            ]
        ),
        "dp_freshness_report.csv": pd.DataFrame(
            [
                {
                    "nwr_fetch_timestamp": "2026-07-29T00:00:00+00:00",
                    "upstream_scrape_date": "2026-07-25",
                    "upstream_latest_commit_sha": "synthetic",
                    "upstream_latest_commit_timestamp": "2026-07-25T00:00:00+00:00",
                    "freshness_status": "GREEN_CURRENT",
                }
            ]
        ),
        "dp_nwr_join_coverage.csv": pd.DataFrame([{"source_name": "synthetic"}]),
        "dp_playerid_crosswalk_audit.csv": pd.DataFrame([{"player": "synthetic"}]),
    }
    publish_generation(
        {
            name: frame.to_csv(index=False).encode()
            for name, frame in frames.items()
        },
        safe_root=artifact_dir,
        repo_root=repo,
        run_id="forbidden-test",
        generation_id="forbidden-test-generation",
    )

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
