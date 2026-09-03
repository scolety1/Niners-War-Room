from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.services.udk_unmodeled_skill_asset_service import (
    UNMODELED_SKILL_AUTHORITY,
    UdkUnmodeledSkillAssetError,
    merge_manual_assets,
    parse_udk_unmatched_skill_assets,
    write_manual_assets_file,
)

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "sample_data"
    / "kha_real_draft_2026"
    / "udk_skill_position_snapshot_with_identity_status.csv"
)

# Ground truth from sample_data/kha_real_draft_2026/RECONCILIATION_LEDGER.md
# -- the 5 real KHA draft picks that forced an owner placeholder
# substitution because NWR's universe had no match for them.
KHA_HISTORICAL_MISSING_PLAYERS = {
    ("Jonathon Brooks", "RB", "CAR"),
    ("MarShawn Lloyd", "RB", "GB"),
    ("Stefon Diggs", "WR", "WAS"),
    ("Tank Dell", "WR", "HOU"),
    ("Deebo Samuel Sr.", "WR", "SF"),
}


def test_parses_exactly_the_14_real_unmatched_skill_players() -> None:
    rows = parse_udk_unmatched_skill_assets(FIXTURE)
    assert len(rows) == 14
    for row in rows:
        assert row["position"] in {"QB", "RB", "WR", "TE"}
        assert row["authority"] == UNMODELED_SKILL_AUTHORITY
        assert row["player_id"].startswith("manual:")


def test_all_5_historical_kha_missing_player_picks_are_present() -> None:
    rows = parse_udk_unmatched_skill_assets(FIXTURE)
    found = {(row["player_name"], row["position"], row["team"]) for row in rows}
    missing = KHA_HISTORICAL_MISSING_PLAYERS - found
    assert not missing, f"historical missing-player picks not parsed: {missing}"


def test_travis_hunter_is_covered_too() -> None:
    # Confirmed separately (KHA anomaly investigation) as UNMATCHED with
    # offensive-role uncertainty -- not one of the 5 ledger rows (this
    # draft's live capture never reached his real pick, round 11), but the
    # same universe gap and worth a named regression on its own.
    rows = parse_udk_unmatched_skill_assets(FIXTURE)
    names = {row["player_name"] for row in rows}
    assert "Travis Hunter" in names


def test_skips_a_row_with_no_real_player_name(tmp_path: Path) -> None:
    # Reproduces the real defect noted in
    # docs/codex/KDST_AND_UNIVERSE_GAP_EVIDENCE_20260903.md: at least one
    # row in this source has commentary text merged into player_name_raw
    # instead of a real player. Must be skipped, not admitted as an
    # identity.
    csv_path = tmp_path / "broken.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["player_name_raw", "position", "team_raw", "identity_status"]
        )
        writer.writeheader()
        writer.writerow(
            {
                "player_name_raw": "",
                "position": "QB",
                "team_raw": "DAL",
                "identity_status": "UNMATCHED",
            }
        )
        writer.writerow(
            {
                "player_name_raw": "Real Player",
                "position": "RB",
                "team_raw": "SF",
                "identity_status": "UNMATCHED",
            }
        )
        writer.writerow(
            {
                "player_name_raw": "Matched Player",
                "position": "WR",
                "team_raw": "SEA",
                "identity_status": "MATCHED",
            }
        )
    rows = parse_udk_unmatched_skill_assets(csv_path)
    assert [row["player_name"] for row in rows] == ["Real Player"]


def test_missing_required_columns_raises() -> None:
    with pytest.raises(UdkUnmodeledSkillAssetError, match="missing required columns"):
        parse_udk_unmatched_skill_assets(__file__)  # not even a CSV with the right header


def test_missing_file_raises() -> None:
    with pytest.raises(UdkUnmodeledSkillAssetError, match="not found"):
        parse_udk_unmatched_skill_assets("Z:/does/not/exist.csv")


def test_merge_is_additive_and_idempotent() -> None:
    existing = [
        {
            "player_id": "MANUAL_K_DAL",
            "player_name": "Brandon Aubrey",
            "position": "K",
            "team": "DAL",
        }
    ]
    new_rows = parse_udk_unmatched_skill_assets(FIXTURE)
    merged_once = merge_manual_assets(existing, new_rows)
    assert len(merged_once) == 1 + 14
    # existing K row untouched
    assert any(row["player_id"] == "MANUAL_K_DAL" for row in merged_once)
    merged_twice = merge_manual_assets(merged_once, new_rows)
    assert len(merged_twice) == len(merged_once)  # idempotent, no duplicates


def test_merge_never_overwrites_an_existing_row() -> None:
    existing = [
        {
            "player_id": "manual:RB:jonathon-brooks",
            "player_name": "STALE NAME",
            "position": "RB",
            "team": "CAR",
        }
    ]
    new_rows = parse_udk_unmatched_skill_assets(FIXTURE)
    merged = merge_manual_assets(existing, new_rows)
    kept = next(row for row in merged if row["player_id"] == "manual:RB:jonathon-brooks")
    assert kept["player_name"] == "STALE NAME"


def test_write_manual_assets_file_round_trips(tmp_path: Path) -> None:
    import json

    target = tmp_path / "manual_assets" / "profile-1.json"
    rows = parse_udk_unmatched_skill_assets(FIXTURE)
    write_manual_assets_file(target, profile_id="profile-1", assets=rows)
    document = json.loads(target.read_text(encoding="utf-8"))
    assert document["schema_version"] == 1
    assert document["profile_id"] == "profile-1"
    assert len(document["assets"]) == 14
    assert not target.with_suffix(".tmp").exists()
