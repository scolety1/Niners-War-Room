from pathlib import Path

import pytest

from src.services.kha_shadow_replay_reader_service import (
    HISTORICAL_REPLAY_LABEL,
    KhaShadowReplayUnavailable,
    kha_shadow_replay_payload,
    load_kha_shadow_replay_preview,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_loads_the_real_checked_in_replay_csv() -> None:
    preview = load_kha_shadow_replay_preview(REPO_ROOT)
    assert preview.label == HISTORICAL_REPLAY_LABEL == "HISTORICAL REPLAY — 2026-09-02"
    assert preview.source_relative_path == "docs/codex/KHA_SHADOW_OPTIMIZER_REPLAY.csv"
    assert len(preview.picks) > 0
    assert "disclosed rank-derived value proxy" in preview.disclosed_limitations
    first = preview.picks[0]
    assert first.pick_number > 0
    assert first.player_name
    assert first.position
    assert first.real_nwr_rank_at_time_of_pick > 0
    # A disclosed NOT_COMPUTABLE marker parses as text, never as a
    # fabricated numeric value.
    assert first.top_candidate_alternatives == "NOT_COMPUTABLE_WITHOUT_FULL_RANKING_UNIVERSE"


def test_never_upgrades_a_disclosed_marker_into_a_fabricated_number() -> None:
    preview = load_kha_shadow_replay_preview(REPO_ROOT)
    for pick in preview.picks:
        # value_proxy is always the disclosed marker string, never a bare
        # float this reader could be mistaken for a real magnitude.
        assert pick.value_proxy == "RANK_DERIVED_PROXY_NOT_REAL_MAGNITUDE"


def test_raises_an_explicit_error_rather_than_a_fabricated_empty_replay(tmp_path: Path) -> None:
    with pytest.raises(KhaShadowReplayUnavailable, match="does not exist"):
        load_kha_shadow_replay_preview(tmp_path)


def test_payload_is_camelcase_and_round_trips_every_pick() -> None:
    preview = load_kha_shadow_replay_preview(REPO_ROOT)
    payload = kha_shadow_replay_payload(preview)
    assert payload["label"] == HISTORICAL_REPLAY_LABEL
    assert len(payload["picks"]) == len(preview.picks)
    first = payload["picks"][0]
    assert set(first) == {
        "pickNumber", "round", "playerName", "position", "team",
        "realNwrRankAtTimeOfPick", "valueProxy", "teamScoreBefore", "teamScoreAfter",
        "champEquityBefore", "champEquityAfter", "starterHolesBefore", "starterHolesAfter",
        "startingLineupValueDelta", "topCandidateAlternatives", "costOfWaiting",
        "marketStateAdp", "productionNwrRecommendation",
    }
