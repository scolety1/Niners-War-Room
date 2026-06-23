from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest

from scripts.build_dynastyprocess_market_baseline_v1 import (
    DEFAULT_OUTPUT_DIR,
    DISPLAY_ONLY_WARNING,
)
from src.connectors.dynastyprocess_connector import (
    DynastyProcessSchemaError,
    FetchedFile,
    SnapshotResult,
    build_raw_url,
    evaluate_freshness,
    parse_upstream_cron_metadata,
    validate_schema,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _snapshot(
    *,
    scrape_date: str,
    sha256: str = "sha-current",
    commit_date: str = "2026-06-19T07:33:57Z",
) -> SnapshotResult:
    return SnapshotResult(
        snapshot_dir=r"C:\NWR_SHARED_DATA\market_sources\dynastyprocess\test",
        metadata_path=r"C:\NWR_SHARED_DATA\market_sources\dynastyprocess\test\snapshot_metadata.json",
        branch="master",
        fetched_at_utc="2026-06-23T12:00:00+00:00",
        files=(
            FetchedFile(
                file_name="values.csv",
                source_url="https://raw.githubusercontent.com/dynastyprocess/data/master/files/values.csv",
                cache_path=r"C:\NWR_SHARED_DATA\market_sources\dynastyprocess\test\values.csv",
                fetched_at_utc="2026-06-23T12:00:00+00:00",
                sha256=sha256,
                byte_count=10,
                row_count=1,
                scrape_date=scrape_date,
                etag='"etag"',
                upstream_commit_sha="abc123",
                upstream_commit_date=commit_date,
            ),
        ),
        warnings=(),
    )


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


def test_dynastyprocess_cron_metadata_is_recorded() -> None:
    metadata = parse_upstream_cron_metadata()
    assert metadata["upstream_workflow_name"] == "weekly-playervalues"
    assert metadata["upstream_expected_cron"] == "23 2 * * 5"
    assert metadata["upstream_expected_utc"] == "Friday 02:23 UTC"


def test_dynastyprocess_freshness_current() -> None:
    freshness = evaluate_freshness(
        _snapshot(scrape_date="2026-06-19"),
        now_utc=datetime(2026, 6, 23, tzinfo=UTC),
    )
    assert freshness.freshness_status == "GREEN_CURRENT"


def test_dynastyprocess_freshness_same_week_no_change() -> None:
    freshness = evaluate_freshness(
        _snapshot(scrape_date="2026-06-19", sha256="same"),
        previous_snapshot=_snapshot(scrape_date="2026-06-19", sha256="same"),
        now_utc=datetime(2026, 6, 23, tzinfo=UTC),
    )
    assert freshness.freshness_status == "GREEN_SAME_WEEK_NO_CHANGE"


def test_dynastyprocess_freshness_yellow_after_8_days() -> None:
    freshness = evaluate_freshness(
        _snapshot(scrape_date="2026-06-14", commit_date="2026-06-14T07:33:57Z"),
        now_utc=datetime(2026, 6, 23, tzinfo=UTC),
    )
    assert freshness.freshness_status == "YELLOW_STALE"
    assert "Market baseline stale" in freshness.freshness_warning


def test_dynastyprocess_freshness_red_after_14_days() -> None:
    freshness = evaluate_freshness(
        _snapshot(scrape_date="2026-06-08", commit_date="2026-06-08T07:33:57Z"),
        now_utc=datetime(2026, 6, 23, tzinfo=UTC),
    )
    assert freshness.freshness_status == "RED_STALE"


def test_dynastyprocess_fetch_failure_with_cache_is_yellow() -> None:
    freshness = evaluate_freshness(
        _snapshot(scrape_date="2026-06-19"),
        fetch_failed=True,
        now_utc=datetime(2026, 6, 23, tzinfo=UTC),
    )
    assert freshness.freshness_status == "YELLOW_FETCH_FAILED_USING_LAST_CACHE"


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
        "dp_freshness_report.csv",
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


@pytest.mark.skipif(
    not (DEFAULT_OUTPUT_DIR / "dp_market_baseline_context.csv").exists(),
    reason="DynastyProcess market artifact has not been built",
)
def test_dynastyprocess_derived_context_includes_freshness_fields() -> None:
    market = pd.read_csv(DEFAULT_OUTPUT_DIR / "dp_market_baseline_context.csv")
    expected = {
        "nwr_fetch_timestamp",
        "upstream_scrape_date",
        "upstream_latest_commit_sha",
        "upstream_latest_commit_timestamp",
        "upstream_workflow_name",
        "upstream_expected_cron",
        "local_cache_path",
        "derived_artifact_path",
        "freshness_status",
        "market_baseline_stale_warning",
    }
    assert expected.issubset(set(market.columns))


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
