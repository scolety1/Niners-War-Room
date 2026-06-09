from __future__ import annotations

import scripts.backfill_active_pack_public_veteran_model as backfill


def test_nflverse_players_identity_matches_rookie_suffix_by_team() -> None:
    lookup = backfill._nflverse_player_identity_lookup(
        [
            {
                "gsis_id": "00-0040735",
                "display_name": "Luther Burden III",
                "pfr_id": "BurdLu00",
                "espn_id": "4685278",
                "position": "WR",
                "latest_team": "CHI",
                "rookie_season": "2025",
                "draft_year": "2025",
            }
        ]
    )

    match, method = backfill._resolve_player_identity(
        position="WR",
        sleeper_player={"full_name": "Luther Burden", "team": "CHI"},
        identity_lookup=lookup,
    )

    assert method == "nflverse_players_name_position_team"
    assert match is not None
    assert match["gsis_id"] == "00-0040735"
    assert match["pfr_id"] == "BurdLu00"


def test_nflverse_players_identity_requires_unique_name_position_team() -> None:
    lookup = backfill._nflverse_player_identity_lookup(
        [
            {
                "gsis_id": "00-1111111",
                "display_name": "Fixture Player",
                "pfr_id": "FixPl00",
                "espn_id": "1",
                "position": "WR",
                "latest_team": "CHI",
                "rookie_season": "2025",
                "draft_year": "2025",
            },
            {
                "gsis_id": "00-2222222",
                "display_name": "Fixture Player",
                "pfr_id": "FixPl01",
                "espn_id": "2",
                "position": "WR",
                "latest_team": "CHI",
                "rookie_season": "2025",
                "draft_year": "2025",
            },
        ]
    )

    match, method = backfill._resolve_player_identity(
        position="WR",
        sleeper_player={"full_name": "Fixture Player", "team": "CHI"},
        identity_lookup=lookup,
    )

    assert match is None
    assert method == "unmatched"


def test_identity_audit_row_can_use_external_bridge_without_stat_profile() -> None:
    row = backfill._identity_audit_row(
        sleeper_id="12530",
        player={"full_name": "Travis Hunter"},
        position="WR",
        sleeper_gsis="",
        bridge_gsis="00-0040718",
        bridge_pfr="HuntTr00",
        bridge_name="Travis Hunter",
        stat_row={
            "gsis_id": "00-0040718",
            "display_name": "Travis Hunter",
            "pfr_id": "HuntTr00",
        },
        match_method="dynastyprocess_sleeper_to_gsis",
    )

    assert row["matched_gsis_id"] == "00-0040718"
    assert row["bridge_pfr_id"] == "HuntTr00"
    assert row["match_status"] == "matched"
    assert row["manual_review_required"] == "false"


def test_missing_nflverse_stats_do_not_market_gap_fill_private_features() -> None:
    value, source_key, confidence, missing_reason = backfill._gap_fill_tuple(
        98.0,
        "fantasycalc_redraft_value_20260505",
        stat_source_missing=True,
    )

    assert value is None
    assert source_key == "fantasycalc_redraft_value_20260505"
    assert confidence == "estimated"
    assert "no market gap-fill applied" in missing_reason


def test_nflverse_source_rows_are_stats_sources_with_detected_coverage_date() -> None:
    previous = backfill.NFLVERSE_LATEST_STATS_SEASON
    try:
        backfill.NFLVERSE_LATEST_STATS_SEASON = 2024
        row = backfill._source_row(
            "nflverse_player_stats_recent_lve_20260506",
            "nflverse player stats recent weighted LVE scoring",
            "player_stats",
            backfill.NFLVERSE_PLAYER_STATS_URL,
            92,
            1,
            source_date=backfill._nflverse_stats_source_date(),
            notes_extra=backfill._nflverse_stats_coverage_note(),
        )
    finally:
        backfill.NFLVERSE_LATEST_STATS_SEASON = previous

    assert row["source_type"] == "player_stats"
    assert row["source_family"] == "football_stats"
    assert row["source_domain"] == "production"
    assert row["authority_tier"] == "tier_b_official_public"
    assert row["source_date"] == "2025-01-15"
    assert "Latest covered nflverse player_stats season detected at import time: 2024" in str(
        row["source_notes"]
    )
