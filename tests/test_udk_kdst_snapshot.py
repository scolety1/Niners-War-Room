"""Tests for parse_udk_kdst_snapshot() -- the CURRENT K/DST source that
closes the Harrison Mevis / stale Joshua Karty gap (section 1B of the
Saturday NWR PURE release-candidate wave).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.services.udk_unmodeled_skill_asset_service import (
    KDST_AUTHORITY,
    UdkKdstSnapshotError,
    parse_udk_kdst_snapshot,
)

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "sample_data"
    / "kha_real_draft_2026"
    / "udk_kdst_snapshot_20260902.csv"
)


def test_parses_exactly_32_kickers_and_32_dst() -> None:
    rows = parse_udk_kdst_snapshot(FIXTURE)
    kickers = [r for r in rows if r["position"] == "K"]
    dst = [r for r in rows if r["position"] == "DST"]
    assert len(kickers) == 32
    assert len(dst) == 32
    assert len(rows) == 64
    for row in rows:
        assert row["authority"] == KDST_AUTHORITY
        assert row["player_id"].startswith("manual:")
        assert row["team"]  # every row resolved a team code


def test_rams_kicker_is_the_current_correct_player_not_the_stale_one() -> None:
    """The exact gap this file exists to close: the real live-draft-night
    manual asset pool had the stale 'Joshua Karty' for the Rams; this
    CURRENT source has the real Harrison Mevis."""
    rows = parse_udk_kdst_snapshot(FIXTURE)
    lar_kicker = next(r for r in rows if r["position"] == "K" and r["team"] == "LAR")
    assert lar_kicker["player_name"] == "Harrison Mevis"
    assert lar_kicker["player_name"] != "Joshua Karty"


def test_dst_rows_get_a_team_code_derived_from_the_full_team_name() -> None:
    rows = parse_udk_kdst_snapshot(FIXTURE)
    texans = next(
        r for r in rows if r["position"] == "DST" and r["player_name"] == "Houston Texans D/ST"
    )
    assert texans["team"] == "HOU"


def test_all_32_teams_covered_for_both_positions_no_duplicates() -> None:
    rows = parse_udk_kdst_snapshot(FIXTURE)
    k_teams = {r["team"] for r in rows if r["position"] == "K"}
    dst_teams = {r["team"] for r in rows if r["position"] == "DST"}
    assert len(k_teams) == 32
    assert len(dst_teams) == 32


def test_missing_file_raises() -> None:
    with pytest.raises(UdkKdstSnapshotError, match="not found"):
        parse_udk_kdst_snapshot("Z:/does/not/exist.csv")


def test_missing_required_columns_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.csv"
    bad.write_text("player_name_raw,position\nFoo,K\n", encoding="utf-8")
    with pytest.raises(UdkKdstSnapshotError, match="missing required columns"):
        parse_udk_kdst_snapshot(bad)
