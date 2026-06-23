from __future__ import annotations

import subprocess
from pathlib import Path

import pandas as pd
import pytest

from scripts.build_dynastyprocess_market_baseline_v1 import (
    DEFAULT_OUTPUT_DIR,
    DISPLAY_ONLY_WARNING,
)
from src.connectors.dynastyprocess_connector import (
    DynastyProcessSchemaError,
    build_raw_url,
    validate_schema,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_dynastyprocess_url_construction_is_explicit() -> None:
    assert (
        build_raw_url("values-players.csv")
        == "https://raw.githubusercontent.com/dynastyprocess/data/master/files/values-players.csv"
    )
    with pytest.raises(ValueError):
        build_raw_url("../values-players.csv")


def test_dynastyprocess_schema_validation_fails_clearly() -> None:
    with pytest.raises(DynastyProcessSchemaError, match="schema changed"):
        validate_schema(["player", "pos"], "values-players.csv")


@pytest.mark.skipif(
    not (DEFAULT_OUTPUT_DIR / "dp_market_baseline_context.csv").exists(),
    reason="DynastyProcess derived artifacts have not been built",
)
def test_dynastyprocess_derived_csvs_load() -> None:
    expected = [
        "dp_market_baseline_context.csv",
        "dp_pick_value_context.csv",
        "dp_playerid_crosswalk_audit.csv",
        "dp_nwr_join_coverage.csv",
    ]
    for file_name in expected:
        frame = pd.read_csv(DEFAULT_OUTPUT_DIR / file_name)
        assert not frame.empty, file_name


@pytest.mark.skipif(
    not (DEFAULT_OUTPUT_DIR / "dp_nwr_join_coverage.csv").exists(),
    reason="DynastyProcess coverage artifact has not been built",
)
def test_dynastyprocess_join_coverage_has_matches() -> None:
    coverage = pd.read_csv(DEFAULT_OUTPUT_DIR / "dp_nwr_join_coverage.csv")
    combined = coverage.loc[coverage["source_name"].eq("combined_nwr_universe")].iloc[0]
    assert combined["dp_matched_rows"] > 0
    assert combined["dp_match_rate"] > 0


@pytest.mark.skipif(
    not (DEFAULT_OUTPUT_DIR / "dp_market_baseline_context.csv").exists(),
    reason="DynastyProcess market artifact has not been built",
)
def test_dynastyprocess_fields_are_display_only() -> None:
    market = pd.read_csv(DEFAULT_OUTPUT_DIR / "dp_market_baseline_context.csv")
    assert market["dp_display_only_warning"].eq(DISPLAY_ONLY_WARNING).all()
    forbidden = {
        "hidden_sort",
        "candidate_rank_override",
        "model_input",
        "private_value",
    }
    assert forbidden.isdisjoint(set(market.columns))


def test_dynastyprocess_raw_files_not_tracked() -> None:
    tracked = subprocess.check_output(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        text=True,
    ).splitlines()
    raw_paths = [
        path
        for path in tracked
        if "market_sources/dynastyprocess" in path.replace("\\", "/")
        or path.startswith("C:/NWR_SHARED_DATA")
    ]
    assert raw_paths == []
