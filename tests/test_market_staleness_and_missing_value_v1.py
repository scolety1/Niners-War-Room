"""Full Trust Hardening V1 (Worker 2), Part C.

Two owner-facing failure modes the dispatch specifically asked to be
proven, not just asserted from reading code:

1. Genuinely stale market data must be labeled stale and must never
   masquerade as current -- and, specifically, must never silently produce
   a confident-looking "current arbitrage" (NWR-vs-market gap) claim.

2. A missing market value must be honestly represented as missing/unknown,
   never silently treated as zero (which could fabricate a fake NWR-vs-
   market gap in the other direction).

`test_market_sanity_label_treats_genuinely_old_snapshot_as_stale_not_aligned`
is a real regression test for a genuine bug this worker found and fixed
this pass: `compute_market_sanity_flags()` (`market_baseline_service.py`)
only ever read each row's RAW, write-time `freshness_status` column and
never re-checked it against today's date -- unlike `load_market_freshness()`
and `owner_asset_evidence_service._market_status()`, which both dynamically
recompute staleness from `upstream_scrape_date` on every call. A real
admitted DynastyProcess snapshot in this worktree was independently
confirmed (this session, via a direct call to `load_market_freshness()`
against the actual runtime artifact directory) to be 73 days old and
correctly reported `YELLOW_STALE` by the aggregate freshness path -- but
`compute_market_sanity_flags()` on that SAME real snapshot still returned
`market_sanity_label="Aligned"` for a real matched player, because its
own per-row status column ("GREEN_SAME_WEEK_NO_CHANGE") was frozen at
connector-fetch time and never re-evaluated. That is exactly the failure
mode this file's first test guards against, using a synthetic, clearly-
labeled fixture (never real data) so the test does not rot with the
calendar.

None of these tests mock `load_market_freshness`/`join_market_to_players` --
they build a real, synthetic DynastyProcess generation on disk via
`publish_generation` (the exact harness `test_market_baseline_service.py`
already uses) and exercise the real production code path end to end.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from src.services.dynastyprocess_generation_service import (
    OUTPUT_FILE_NAMES,
    expected_safe_root,
    publish_generation,
)
from src.services.market_baseline_service import (
    compute_market_sanity_flags,
    load_market_freshness,
)
from src.services.owner_asset_evidence_service import NOT_AVAILABLE, compose_owner_asset_evidence


def _iso_date_days_ago(days: int) -> str:
    return (datetime.now(UTC) - timedelta(days=days)).date().isoformat()


def _publish_generation(
    tmp_path: Path,
    *,
    generation_id: str,
    scrape_date: str,
    row_freshness_status: str,
    report_freshness_status: str,
    include_market_value: bool = True,
) -> Path:
    """Build a real, synthetic-but-schema-valid DynastyProcess generation on
    disk. `scrape_date`/`report_freshness_status`/`row_freshness_status` are
    exactly what a real connector fetch would have written at THAT fetch
    time -- deliberately independent of how old `scrape_date` actually is
    relative to "today," mirroring how a real admitted snapshot can sit
    untouched long after its original fetch.
    """

    repo = tmp_path / f"repo-{generation_id}"
    repo.mkdir()
    root = expected_safe_root(repo)

    market_row = {
        "player": "Synthetic Fixture Player",
        "pos": "WR",
        "nwr_name": "Synthetic Fixture Player",
        "nwr_pos": "WR",
        "join_method": "exact_name_position",
        "join_confidence": "medium",
        "dp_display_only_warning": "display-only",
        "freshness_status": row_freshness_status,
        "upstream_scrape_date": scrape_date,
    }
    if include_market_value:
        market_row.update(
            {
                "dp_market_rank_1qb": "10",
                "dp_value_1qb": "5000",
                "ecr_pos": "WR5",
                "age": "24",
            }
        )
    else:
        # A real "no market data point exists for this row" case -- the
        # columns are present (schema-required) but genuinely empty, never
        # a fabricated "0".
        market_row.update(
            {
                "dp_market_rank_1qb": "",
                "dp_value_1qb": "",
                "ecr_pos": "",
                "age": "",
            }
        )
    market = pd.DataFrame([market_row])
    picks = pd.DataFrame(
        [{"pick_label": "2026 1.01", "value_1qb": "5000", "ecr_1qb": "1", "freshness_status": row_freshness_status}]
    )
    freshness = pd.DataFrame(
        [
            {
                "nwr_fetch_timestamp": f"{scrape_date}T00:00:00+00:00",
                "upstream_scrape_date": scrape_date,
                "upstream_latest_commit_sha": "synthetic",
                "upstream_latest_commit_timestamp": f"{scrape_date}T00:00:00+00:00",
                "freshness_status": report_freshness_status,
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
        {name: frame.to_csv(index=False).encode() for name, frame in frames.items()},
        safe_root=root,
        repo_root=repo,
        run_id=f"{generation_id}-run",
        generation_id=f"{generation_id}-generation",
    )
    return root


# ---------------------------------------------------------------------------
# 1. Genuinely stale market data must be labeled stale, never "current."
# ---------------------------------------------------------------------------


def test_market_sanity_label_treats_genuinely_old_snapshot_as_stale_not_aligned(
    tmp_path: Path,
) -> None:
    # Regression test for a real bug found and fixed this pass: a snapshot
    # that was GREEN at connector-fetch time but is now, by real elapsed
    # calendar time, 90 days old must not keep reporting "Aligned" --
    # that would be a genuinely stale gap masquerading as a current one.
    root = _publish_generation(
        tmp_path,
        generation_id="stale-sanity",
        scrape_date=_iso_date_days_ago(90),
        row_freshness_status="GREEN_SAME_WEEK_NO_CHANGE",
        report_freshness_status="GREEN_SAME_WEEK_NO_CHANGE",
    )

    # Sanity-check the underlying recompute this fix relies on: the
    # aggregate freshness report is NOT trusted verbatim either.
    freshness = load_market_freshness(root)
    assert freshness["freshness_status"] == "YELLOW_STALE"
    assert "90 days old" in freshness["market_baseline_stale_warning"]

    players = pd.DataFrame(
        [{"player": "Synthetic Fixture Player", "position": "WR", "nwr_candidate_rank": "2"}]
    )
    result = compute_market_sanity_flags(players, root)

    assert result.loc[0, "market_sanity_label"] == "Market data stale"
    # No numeric gap must ever be displayed alongside a stale label --
    # that would still look like a live, actionable arbitrage number.
    assert result.loc[0, "market_gap"] == ""


def test_market_sanity_label_still_computes_a_real_gap_for_genuinely_fresh_data(
    tmp_path: Path,
) -> None:
    # Control case: the fix must not make freshly-fetched data look stale.
    root = _publish_generation(
        tmp_path,
        generation_id="fresh-sanity",
        scrape_date=_iso_date_days_ago(1),
        row_freshness_status="GREEN_CURRENT",
        report_freshness_status="GREEN_CURRENT",
    )

    freshness = load_market_freshness(root)
    assert freshness["freshness_status"] == "GREEN_CURRENT"

    players = pd.DataFrame(
        [{"player": "Synthetic Fixture Player", "position": "WR", "nwr_candidate_rank": "2"}]
    )
    result = compute_market_sanity_flags(players, root)

    assert result.loc[0, "market_sanity_label"] != "Market data stale"
    assert result.loc[0, "market_gap"] != ""


def test_market_sanity_label_leaves_unmatched_players_as_no_market_match_not_stale(
    tmp_path: Path,
) -> None:
    # A player who was never matched to any market row must stay "No
    # market match" -- the stale-recompute fix must not repaint an
    # unmatched player as "stale," which would wrongly imply a match
    # exists somewhere in the data.
    root = _publish_generation(
        tmp_path,
        generation_id="unmatched-sanity",
        scrape_date=_iso_date_days_ago(90),
        row_freshness_status="GREEN_SAME_WEEK_NO_CHANGE",
        report_freshness_status="GREEN_SAME_WEEK_NO_CHANGE",
    )

    players = pd.DataFrame(
        [{"player": "Nobody DynastyProcess Has Ever Heard Of", "position": "RB", "nwr_candidate_rank": "40"}]
    )
    result = compute_market_sanity_flags(players, root)

    assert result.loc[0, "market_sanity_label"] == "No market match"
    assert result.loc[0, "market_gap"] == ""


def test_owner_asset_evidence_market_status_is_stale_end_to_end_for_old_snapshot(
    tmp_path: Path,
) -> None:
    # The Dynasty Trade Decision Lab's real evidence composer must reach
    # the same honest conclusion through its own separate code path
    # (owner_asset_evidence_service._market_status), exercised here with
    # the REAL load_market_freshness/join_market_to_players -- no mocks.
    root = _publish_generation(
        tmp_path,
        generation_id="stale-evidence",
        scrape_date=_iso_date_days_ago(90),
        row_freshness_status="GREEN_SAME_WEEK_NO_CHANGE",
        report_freshness_status="GREEN_SAME_WEEK_NO_CHANGE",
    )
    registry = ({"asset_id": "current:1001", "asset_type": "Current Player", "asset_name": "Synthetic Fixture Player"},)
    dynasty = pd.DataFrame(
        [
            {
                "player_id": "1001",
                "player_name": "Synthetic Fixture Player",
                "position": "WR",
                "nwr_rank": "2",
            }
        ]
    )

    bundle = compose_owner_asset_evidence(registry, dynasty_frame=dynasty, market_artifact_dir=root)

    row = bundle.by_id["current:1001"]
    assert row["market_status"].startswith("Stale as of")
    assert not row["market_status"].startswith("Current as of")


# ---------------------------------------------------------------------------
# 2. A missing market value must be UNKNOWN, never a silent zero.
# ---------------------------------------------------------------------------


def test_owner_asset_evidence_missing_market_value_is_not_available_not_zero(
    tmp_path: Path,
) -> None:
    root = _publish_generation(
        tmp_path,
        generation_id="missing-value",
        scrape_date=_iso_date_days_ago(1),
        row_freshness_status="GREEN_CURRENT",
        report_freshness_status="GREEN_CURRENT",
        include_market_value=False,
    )
    registry = ({"asset_id": "current:1001", "asset_type": "Current Player", "asset_name": "Synthetic Fixture Player"},)
    dynasty = pd.DataFrame(
        [
            {
                "player_id": "1001",
                "player_name": "Synthetic Fixture Player",
                "position": "WR",
                "nwr_rank": "2",
            }
        ]
    )

    bundle = compose_owner_asset_evidence(registry, dynasty_frame=dynasty, market_artifact_dir=root)

    row = bundle.by_id["current:1001"]
    assert row["market_status"] == NOT_AVAILABLE
    assert row["market_status"] == "Not available"
    # Never a fabricated numeric zero standing in for "no data."
    assert row["market_dp_value"] == ""
    assert row["market_dp_rank"] == ""
    assert row["market_dp_value"] != "0"
    assert row["market_dp_rank"] != "0"


def test_market_sanity_flags_never_reports_a_zero_gap_for_an_unmatched_player(
    tmp_path: Path,
) -> None:
    root = _publish_generation(
        tmp_path,
        generation_id="missing-gap",
        scrape_date=_iso_date_days_ago(1),
        row_freshness_status="GREEN_CURRENT",
        report_freshness_status="GREEN_CURRENT",
    )
    players = pd.DataFrame(
        [{"player": "Nobody DynastyProcess Has Ever Heard Of", "position": "RB", "nwr_candidate_rank": "40"}]
    )

    result = compute_market_sanity_flags(players, root)

    assert result.loc[0, "market_sanity_label"] == "No market match"
    # `market_gap` must be the empty-string "unknown" sentinel this module
    # already uses elsewhere, never a numeric 0 that could read as "even
    # with the market."
    assert result.loc[0, "market_gap"] == ""
    assert result.loc[0, "market_gap"] != 0
