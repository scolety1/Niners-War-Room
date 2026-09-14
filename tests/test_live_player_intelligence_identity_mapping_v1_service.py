"""Tests for the Work Unit 2/3 identity-mapping classification logic.

Proves the matched/unmatched/ambiguous/team-mismatch/name-mismatch/
provider-id-mismatch classification is correct on known, constructed
examples -- and that it reuses `_identity` (the SAME normalizer
`waiver_engine_service.resolve_roster_canonical_ids` already uses) rather
than a second heuristic, plus each real source adapter's extraction shape.
"""

from __future__ import annotations

from src.services.live_player_intelligence_identity_mapping_v1_service import (
    CommonSourceRow,
    classify_rows,
    common_rows_from_nflverse_depth_charts,
    common_rows_from_nflverse_injuries,
    common_rows_from_sleeper_catalog,
    latest_snapshot_only,
    quarantined_rows,
    summarize_identity_mapping,
)
from src.services.live_player_intelligence_shadow_v1_service import CanonicalPlayerRow

CANONICAL_ROWS = (
    CanonicalPlayerRow(player_id="00-0031234", player_name="Real Starter", position="RB", team="SF"),
    CanonicalPlayerRow(player_id="00-0039999", player_name="Backup Guy", position="WR", team="KC"),
    CanonicalPlayerRow(player_id="00-0040130", player_name="Jayden Higgins", position="WR", team="HOU"),
    CanonicalPlayerRow(player_id="00-0050001", player_name="Traded Wideout", position="WR", team="SEA"),
)


def _row(**kwargs) -> CommonSourceRow:
    defaults = dict(
        source="TEST_SOURCE",
        source_row_id="r1",
        player_name="",
        position="",
        team="",
        provider_id="",
        position_in_scope=True,
        raw={},
    )
    defaults.update(kwargs)
    return CommonSourceRow(**defaults)


def test_direct_id_match_is_matched_gsis_direct():
    rows = [_row(source_row_id="a", player_name="Real Starter", position="RB", team="SF", provider_id="00-0031234")]
    [result] = classify_rows(rows, CANONICAL_ROWS)
    assert result.primary_classification == "MATCHED_GSIS_DIRECT"
    assert result.matched_canonical_player_id == "00-0031234"
    assert not result.name_mismatch
    assert not result.provider_id_mismatch


def test_name_position_team_match_with_no_provider_id():
    rows = [_row(source_row_id="b", player_name="Backup Guy", position="WR", team="KC", provider_id="")]
    [result] = classify_rows(rows, CANONICAL_ROWS)
    assert result.primary_classification == "MATCHED_NAME_POSITION_TEAM"
    assert result.matched_canonical_player_id == "00-0039999"


def test_stale_foreign_provider_id_falls_back_to_name_match_and_flags_mismatch():
    rows = [
        _row(
            source_row_id="c",
            player_name="Backup Guy",
            position="WR",
            team="KC",
            provider_id="00-9999999",  # not in the canonical pool at all
        )
    ]
    [result] = classify_rows(rows, CANONICAL_ROWS)
    assert result.primary_classification == "MATCHED_NAME_POSITION_TEAM"
    assert result.matched_canonical_player_id == "00-0039999"
    assert result.provider_id_mismatch is True


def test_id_and_name_disagreement_is_ambiguous_and_quarantined():
    # provider_id resolves to "Real Starter" (SF RB) but name/position/team
    # independently resolve to "Backup Guy" (KC WR) -- two signals disagree.
    rows = [
        _row(
            source_row_id="d",
            player_name="Backup Guy",
            position="WR",
            team="KC",
            provider_id="00-0031234",
        )
    ]
    [result] = classify_rows(rows, CANONICAL_ROWS)
    assert result.primary_classification == "AMBIGUOUS_ID_NAME_DISAGREEMENT"
    assert result.matched_canonical_player_id is None
    quarantined = quarantined_rows([result])
    assert quarantined == (result,)


def test_canonical_pool_collision_is_ambiguous_even_with_no_provider_id():
    colliding_pool = CANONICAL_ROWS + (
        CanonicalPlayerRow(player_id="00-0099999", player_name="Real Starter", position="RB", team="SF"),
    )
    rows = [_row(source_row_id="e", player_name="Real Starter", position="RB", team="SF", provider_id="")]
    [result] = classify_rows(rows, colliding_pool)
    assert result.primary_classification == "AMBIGUOUS_CANONICAL_POOL_COLLISION"
    assert result.matched_canonical_player_id is None


def test_team_mismatch_is_quarantined_not_matched_and_not_a_plain_miss():
    rows = [
        _row(
            source_row_id="f",
            player_name="Traded Wideout",
            position="WR",
            team="LAC",  # canonical pool has this exact player at SEA
            provider_id="",
        )
    ]
    [result] = classify_rows(rows, CANONICAL_ROWS)
    assert result.primary_classification == "TEAM_MISMATCH"
    assert result.team_mismatch_candidate_team == "SEA"
    assert result.matched_canonical_player_id is None
    assert quarantined_rows([result]) == (result,)


def test_unmatched_no_team_is_distinct_from_plain_unmatched():
    rows = [_row(source_row_id="g", player_name="Nobody Real", position="WR", team="", provider_id="")]
    [result] = classify_rows(rows, CANONICAL_ROWS)
    assert result.primary_classification == "UNMATCHED_NO_TEAM"


def test_plain_unmatched_when_team_present_but_nothing_matches():
    rows = [_row(source_row_id="h", player_name="Nobody Real", position="WR", team="DAL", provider_id="")]
    [result] = classify_rows(rows, CANONICAL_ROWS)
    assert result.primary_classification == "UNMATCHED"


def test_position_out_of_scope_short_circuits_before_name_matching():
    # A punter is not in NWR's fantasy-position vocabulary at all; even if
    # its name/team happened to line up with something, it must never be
    # silently treated as a normal miss.
    rows = [_row(source_row_id="i", player_name="Real Starter", position="P", team="SF", provider_id="", position_in_scope=False)]
    [result] = classify_rows(rows, CANONICAL_ROWS)
    assert result.primary_classification == "UNMATCHED_POSITION_OUT_OF_SCOPE"


def test_name_mismatch_flag_is_informational_and_does_not_change_match_outcome():
    rows = [
        _row(
            source_row_id="j",
            player_name="R. Starter",  # differs from canonical "Real Starter"
            position="RB",
            team="SF",
            provider_id="00-0031234",
        )
    ]
    [result] = classify_rows(rows, CANONICAL_ROWS)
    assert result.primary_classification == "MATCHED_GSIS_DIRECT"
    assert result.matched_canonical_player_id == "00-0031234"
    assert result.name_mismatch is True


def test_summarize_identity_mapping_counts_every_bucket_and_diagnostic_flag():
    rows = [
        _row(source_row_id="a", player_name="Real Starter", position="RB", team="SF", provider_id="00-0031234"),
        _row(source_row_id="b", player_name="Backup Guy", position="WR", team="KC", provider_id=""),
        _row(source_row_id="d", player_name="Backup Guy", position="WR", team="KC", provider_id="00-0031234"),
        _row(source_row_id="f", player_name="Traded Wideout", position="WR", team="LAC", provider_id=""),
        _row(source_row_id="g", player_name="Nobody Real", position="WR", team="", provider_id=""),
        _row(source_row_id="h", player_name="Nobody Real", position="WR", team="DAL", provider_id=""),
    ]
    results = classify_rows(rows, CANONICAL_ROWS)
    summary = summarize_identity_mapping(results)
    assert summary["totalRows"] == 6
    assert summary["matchedUniquely"] == 2  # a, b
    assert summary["ambiguous"] == 1  # d
    assert summary["teamMismatch"] == 1  # f
    assert summary["unmatched"] == 2  # g, h (UNMATCHED_NO_TEAM + UNMATCHED)
    assert summary["primaryClassificationCounts"]["UNMATCHED_NO_TEAM"] == 1
    assert summary["primaryClassificationCounts"]["UNMATCHED"] == 1
    assert len(quarantined_rows(results)) == 2  # d (ambiguous) + f (team mismatch)


# ---------------------------------------------------------------------------
# Real-source adapter shape tests -- proves each adapter extracts the SAME
# common shape from each source's real, distinct raw schema.
# ---------------------------------------------------------------------------

def test_common_rows_from_nflverse_injuries_real_shape():
    rows = [
        {
            "gsis_id": "00-0031234",
            "position": "rb",
            "full_name": "Real Starter",
            "team": "sf",
        }
    ]
    [common] = common_rows_from_nflverse_injuries(rows)
    assert common.source == "NFLVERSE_OFFICIAL_INJURY_REPORT"
    assert common.provider_id == "00-0031234"
    assert common.position == "RB"
    assert common.team == "SF"
    assert common.position_in_scope is True


def test_common_rows_from_nflverse_depth_charts_maps_known_positions_and_flags_out_of_scope():
    rows = [
        {"dt": "2026-09-13T12:00:00Z", "gsis_id": "00-0039999", "player_name": "Backup Guy", "pos_name": "Wide Receiver", "team": "KC"},
        {"dt": "2026-09-13T12:00:00Z", "gsis_id": "00-0000001", "player_name": "Some Tackle", "pos_name": "Left Tackle", "team": "KC"},
    ]
    wr_row, ol_row = common_rows_from_nflverse_depth_charts(rows)
    assert wr_row.position == "WR"
    assert wr_row.position_in_scope is True
    assert ol_row.position_in_scope is False  # real, disclosed: OL roles are not in NWR's fantasy-position vocabulary


def test_latest_snapshot_only_keeps_only_the_max_dt():
    rows = [
        {"dt": "2026-09-01T00:00:00Z", "player_name": "Old"},
        {"dt": "2026-09-13T12:00:00Z", "player_name": "New1"},
        {"dt": "2026-09-13T12:00:00Z", "player_name": "New2"},
    ]
    latest = latest_snapshot_only(rows)
    assert len(latest) == 2
    assert {row["player_name"] for row in latest} == {"New1", "New2"}


def test_common_rows_from_sleeper_catalog_real_shape_and_gsis_whitespace_is_stripped():
    catalog = {
        "6462": {
            "full_name": "Backup Guy",
            "position": "WR",
            "team": "KC",
            "gsis_id": " 00-0039999",  # real Sleeper rows carry a leading space
        }
    }
    [common] = common_rows_from_sleeper_catalog(catalog)
    assert common.provider_id == "00-0039999"
    assert common.player_name == "Backup Guy"
    assert common.position_in_scope is True


def test_common_rows_from_sleeper_catalog_maps_def_to_dst_like_the_rest_of_the_app():
    catalog = {"999": {"full_name": "", "position": "DEF", "team": "SF"}}
    [common] = common_rows_from_sleeper_catalog(catalog)
    assert common.position == "DST"
    assert common.player_name == "SF D/ST"
