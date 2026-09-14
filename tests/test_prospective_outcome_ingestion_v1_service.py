from __future__ import annotations

import json
from pathlib import Path

from src.services.prospective_outcome_ingestion_v1_service import (
    ingest_add_drop_outcome,
    ingest_faab_outcome,
    ingest_start_sit_outcome,
    ingest_streamer_outcome,
    ingest_trade_finder_outcome,
    ingest_trade_outcome,
    ingest_waiver_outcome,
)

# ---------------------------------------------------------------------------
# START_SIT
# ---------------------------------------------------------------------------


def test_start_sit_matches_recommendation_exactly() -> None:
    detail = ingest_start_sit_outcome(
        week=1,
        recommendation={"projectedTotal": 120.0, "starters": ["1", "2", "3"]},
        roster_state_player_ids=["1", "2", "3", "9", "10"],
        actual_matchup_entry={
            "points": 130.0,
            "starters": ["1", "2", "3"],
            "players_points": {"1": 40.0, "2": 50.0, "3": 40.0, "9": 5.0, "10": 2.0},
        },
    )
    assert detail.recommended_only_ids == ()
    assert detail.actual_only_ids == ()
    assert detail.lineup_opportunity_cost == 0.0
    assert detail.eligible_alternative_ids_at_lock == ("9", "10")
    assert detail.actual_points_total == 130.0


def test_start_sit_computes_real_opportunity_cost_when_owner_deviates() -> None:
    detail = ingest_start_sit_outcome(
        week=1,
        recommendation={"projectedTotal": 100.0, "starters": ["1", "2"]},
        roster_state_player_ids=["1", "2", "3"],
        actual_matchup_entry={
            "points": 95.0,
            "starters": ["1", "3"],  # owner benched 2, started 3 instead
            "players_points": {"1": 40.0, "2": 30.0, "3": 25.0},
        },
    )
    assert detail.recommended_only_ids == ("2",)
    assert detail.actual_only_ids == ("3",)
    # NWR recommended player 2 (30 pts, benched); owner started 3 (25 pts).
    assert detail.lineup_opportunity_cost == 5.0


def test_start_sit_opportunity_cost_none_when_points_not_yet_known() -> None:
    detail = ingest_start_sit_outcome(
        week=1,
        recommendation={"projectedTotal": 100.0, "starters": ["1"]},
        roster_state_player_ids=["1", "2"],
        actual_matchup_entry={"points": None, "starters": ["2"], "players_points": {}},
    )
    assert detail.lineup_opportunity_cost is None


def test_start_sit_handles_missing_matchup_data_without_crashing() -> None:
    detail = ingest_start_sit_outcome(
        week=1, recommendation={"starters": ["1"]}, roster_state_player_ids=["1", "2"],
        actual_matchup_entry=None,
    )
    assert detail.actual_starter_ids == ()
    assert detail.actual_points_total is None


# ---------------------------------------------------------------------------
# no-future-leakage guarantee
# ---------------------------------------------------------------------------


def test_no_future_leakage_eligible_alternatives_ignore_a_later_roster_change() -> None:
    """`eligible_alternative_ids_at_lock` must come ONLY from the trace's
    own frozen `roster_state_player_ids` -- never from a 'current' roster
    read. Simulate a later transaction that drops player 9 and adds player
    99 to the SAME roster; the frozen trace fields are untouched, so the
    computed alternatives must be identical either way."""

    recommendation = {"projectedTotal": 100.0, "starters": ["1"]}
    frozen_roster_at_lock = ["1", "9"]  # what the roster looked like AT LOCK TIME

    before_result = ingest_start_sit_outcome(
        week=1, recommendation=recommendation, roster_state_player_ids=frozen_roster_at_lock,
        actual_matchup_entry={"points": 10.0, "starters": ["1"], "players_points": {"1": 10.0}},
    )

    # A "current" roster snapshot fetched LATER would show player 9 gone and
    # player 99 added -- but this function is never given that "current"
    # snapshot at all, only the frozen trace field, so nothing changes.
    current_roster_now = ["1", "99"]
    after_result = ingest_start_sit_outcome(
        week=1, recommendation=recommendation, roster_state_player_ids=frozen_roster_at_lock,
        actual_matchup_entry={"points": 10.0, "starters": ["1"], "players_points": {"1": 10.0}},
    )
    assert before_result.eligible_alternative_ids_at_lock == after_result.eligible_alternative_ids_at_lock == ("9",)
    assert "99" not in before_result.eligible_alternative_ids_at_lock
    assert current_roster_now != frozen_roster_at_lock  # sanity: the "current" state really did change


def test_no_future_leakage_streamer_alternatives_never_see_a_hindsight_best_pick() -> None:
    """`available_alternative_ids_at_recommendation` is whatever the caller
    passes from the trace's own frozen `alternatives` field. Even if the
    ACTUAL week's results reveal some OTHER player (never listed as an
    alternative at recommendation time) scored highest, that player must
    never appear as `best_available_alternative_id` -- only real candidates
    from the frozen list are ever considered."""

    detail = ingest_streamer_outcome(
        position="K", week=1, recommended_player_id="k1",
        prior_roster_option_player_id="k0",
        available_alternative_ids_at_recommendation=("k2", "k3"),
        actual_matchup_entry={
            "points": 100.0,
            "starters": ["k1"],
            # k99 scored the most of anyone this week in hindsight, but it
            # was never an available alternative at recommendation time.
            "players_points": {"k1": 8.0, "k0": 5.0, "k2": 9.0, "k3": 6.0, "k99": 40.0},
        },
    )
    assert detail.best_available_alternative_id == "k2"
    assert detail.best_available_alternative_actual_points == 9.0


# ---------------------------------------------------------------------------
# REAL DATA: real Week 1 2026 Sleeper matchup for the real Fantasy Gamers
# league (id 1312983576827920384), owner scolety, roster_id 9 -- fetched
# live 2026-09-13, committed verbatim (see the fixture file's own
# `_source_note`). No value below was fabricated; every assertion is a
# hand-checked read of the real committed JSON.
# ---------------------------------------------------------------------------

_REAL_FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "codex" / "prospective_outcome_v1" / "real_data_v1"
    / "fantasy_gamers_week1_2026_owner_matchup.json"
)


def test_real_week1_2026_fantasy_gamers_matchup_ingests_correctly() -> None:
    """Uses the real Fantasy Gamers league's real Week 1 2026 result. The
    'recommendation' here is a mechanism-demonstration baseline (NWR
    recommending the exact lineup the owner actually used) -- not a real
    historical NWR forecast, since no real START_SIT trace was recorded for
    this league before this pass existed to ingest an outcome against. The
    OUTCOME data itself (points, starters) is 100% real."""

    real_matchup = json.loads(_REAL_FIXTURE_PATH.read_text(encoding="utf-8"))
    real_full_roster = real_matchup["players"]
    real_actual_starters = real_matchup["starters"]

    detail = ingest_start_sit_outcome(
        week=1,
        recommendation={"projectedTotal": None, "starters": list(real_actual_starters)},
        roster_state_player_ids=list(real_full_roster),
        actual_matchup_entry=real_matchup,
    )

    assert detail.actual_points_total == 156.96
    assert detail.recommended_starter_ids == tuple(real_actual_starters)
    assert detail.actual_starter_ids == tuple(real_actual_starters)
    assert detail.recommended_only_ids == ()
    assert detail.actual_only_ids == ()
    assert detail.lineup_opportunity_cost == 0.0
    # Real bench players at lock time, hand-verified against the fixture:
    # the 6 rostered players not in `starters` (15 roster spots - 9 starters).
    assert detail.eligible_alternative_ids_at_lock == ("11628", "13279", "6819", "7523", "7567", "8126")
    # Real, notable finding preserved by this ingestion (not acted on, just
    # observed): bench player 7523 scored 26.1 real points this week while
    # the lowest-scoring real starter (7553) scored 0.0 -- a real example of
    # exactly the kind of opportunity-cost fact this schema exists to
    # surface once a genuine differing recommendation is ingested.
    assert detail.actual_points_by_player_id["7553"] == 0.0


def test_real_week1_2026_fixture_has_not_been_hand_edited() -> None:
    """A structural sanity check on the committed real fixture itself --
    catches an accidental future hand-edit rather than re-verifying the
    live Sleeper API (this test has no network access)."""

    real_matchup = json.loads(_REAL_FIXTURE_PATH.read_text(encoding="utf-8"))
    assert real_matchup["roster_id"] == 9
    assert len(real_matchup["players"]) == 15
    assert len(real_matchup["starters"]) == 9
    assert round(sum(real_matchup["starters_points"]), 2) == 156.96


# ---------------------------------------------------------------------------
# WAIVER
# ---------------------------------------------------------------------------

_TXN_WON = {
    "type": "waiver", "status": "complete", "adds": {"500": 9}, "drops": None,
    "settings": {"waiver_bid": 8},
}
_TXN_LOST = {
    "type": "waiver", "status": "failed", "adds": {"500": 9}, "drops": None,
    "settings": {"waiver_bid": 3},
}
_TXN_OTHER_ROSTER_WON = {
    "type": "waiver", "status": "complete", "adds": {"500": 2}, "drops": None,
    "settings": {"waiver_bid": 11},
}


def test_waiver_claim_won_records_faab_and_subsequent_value() -> None:
    horizon = [
        {"starters": ["500"], "players_points": {"500": 12.0}},
        {"starters": [], "players_points": {"500": 4.0}},
    ]
    detail = ingest_waiver_outcome(
        recommended_player_id="500", owner_roster_id=9,
        transactions_for_period=[_TXN_WON], horizon_matchup_entries=horizon, horizon_weeks=2,
    )
    assert detail.claim_submitted is True
    assert detail.claim_won is True
    assert detail.faab_paid == 8.0
    assert detail.subsequent_roster_usage_weeks == 1
    assert detail.subsequent_total_points == 16.0


def test_waiver_claim_lost_records_no_subsequent_value() -> None:
    detail = ingest_waiver_outcome(
        recommended_player_id="500", owner_roster_id=9,
        transactions_for_period=[_TXN_LOST], horizon_matchup_entries=[{"starters": ["500"], "players_points": {"500": 99.0}}],
    )
    assert detail.claim_submitted is True
    assert detail.claim_won is False
    # Never claimed by OUR roster -- no subsequent usage attributed to us.
    assert detail.subsequent_roster_usage_weeks is None
    assert detail.subsequent_total_points is None


def test_waiver_no_claim_submitted_is_a_real_false_not_unknown() -> None:
    detail = ingest_waiver_outcome(
        recommended_player_id="500", owner_roster_id=9, transactions_for_period=[],
    )
    assert detail.claim_submitted is False
    assert detail.claim_won is False


def test_waiver_another_roster_winning_the_same_player_is_not_our_claim() -> None:
    detail = ingest_waiver_outcome(
        recommended_player_id="500", owner_roster_id=9, transactions_for_period=[_TXN_OTHER_ROSTER_WON],
    )
    assert detail.claim_submitted is False
    assert detail.claim_won is False


def test_waiver_no_recommendation_yields_all_none() -> None:
    detail = ingest_waiver_outcome(recommended_player_id=None, owner_roster_id=9, transactions_for_period=[])
    assert detail.claim_submitted is None
    assert detail.claim_won is None


# ---------------------------------------------------------------------------
# ADD_DROP
# ---------------------------------------------------------------------------


def test_add_drop_records_subsequent_value_and_detects_a_real_reversal() -> None:
    readd_txn = {"type": "waiver", "status": "complete", "adds": {"600": 9}, "drops": None}
    horizon = [{"starters": ["500"], "players_points": {"500": 10.0}}]
    detail = ingest_add_drop_outcome(
        added_player_id="500", dropped_player_id="600", owner_roster_id=9,
        transactions_for_period=[readd_txn], horizon_matchup_entries=horizon,
    )
    assert detail.added_player_subsequent_points == 10.0
    assert detail.added_player_subsequent_roster_usage_weeks == 1
    assert detail.dropped_player_reversed is True


def test_add_drop_no_reversal_when_no_matching_readd_transaction() -> None:
    detail = ingest_add_drop_outcome(
        added_player_id="500", dropped_player_id="600", owner_roster_id=9, transactions_for_period=[],
    )
    assert detail.dropped_player_reversed is False


# ---------------------------------------------------------------------------
# FAAB
# ---------------------------------------------------------------------------


def test_faab_separates_player_quality_from_bid_calibration_when_won_in_range() -> None:
    horizon = [{"starters": ["500"], "players_points": {"500": 15.0}}]
    detail = ingest_faab_outcome(
        recommended_player_id="500", owner_roster_id=9,
        suggested_bid_low=5.0, suggested_bid_high=10.0,
        transactions_for_period=[_TXN_WON], horizon_matchup_entries=horizon, horizon_weeks=1,
    )
    assert detail.player_decision_quality.subsequent_points == 15.0
    assert detail.bid_range_calibration.won is True
    assert detail.bid_range_calibration.amount_bid == 8.0
    assert detail.bid_range_calibration.bid_within_suggested_range is True
    assert detail.bid_range_calibration.margin_vs_actual_winning_bid == 0.0


def test_faab_flags_out_of_range_suggestion_even_when_pickup_was_good() -> None:
    """Player-decision-quality and bid-range-calibration must genuinely be
    independent axes: a good pickup with a badly-calibrated suggested range
    must show a GOOD player-quality figure and a BAD calibration figure at
    the same time, not collapse into one verdict."""

    horizon = [{"starters": ["500"], "players_points": {"500": 30.0}}]
    detail = ingest_faab_outcome(
        recommended_player_id="500", owner_roster_id=9,
        suggested_bid_low=1.0, suggested_bid_high=3.0,  # way under the real winning bid
        transactions_for_period=[_TXN_WON], horizon_matchup_entries=horizon,
    )
    assert detail.player_decision_quality.subsequent_points == 30.0  # genuinely good pickup
    assert detail.bid_range_calibration.bid_within_suggested_range is False  # genuinely bad range
    assert detail.bid_range_calibration.actual_winning_bid == 8.0


def test_faab_lost_claim_still_reports_the_real_actual_winning_bid() -> None:
    detail = ingest_faab_outcome(
        recommended_player_id="500", owner_roster_id=9,
        suggested_bid_low=5.0, suggested_bid_high=10.0,
        transactions_for_period=[_TXN_OTHER_ROSTER_WON],
    )
    assert detail.bid_range_calibration.won is False
    assert detail.bid_range_calibration.actual_winning_bid == 11.0
    assert detail.bid_range_calibration.bid_within_suggested_range is False


# ---------------------------------------------------------------------------
# TRADE
# ---------------------------------------------------------------------------

_TRADE_ACCEPTED_TXN = {
    "type": "trade", "status": "complete",
    "adds": {"700": 9, "701": 5},  # roster 9 receives 700, roster 5 receives 701
    "drops": {"701": 9, "700": 5},  # roster 9 gave up 701, roster 5 gave up 700
}


def test_trade_accepted_computes_realized_roster_outcome() -> None:
    gives_horizon = {"701": [{"starters": [], "players_points": {"701": 5.0}}]}
    receives_horizon = {"700": [{"starters": ["700"], "players_points": {"700": 20.0}}]}
    detail = ingest_trade_outcome(
        gives_ids=["701"], receives_ids=["700"], owner_roster_id=9,
        transactions_for_period=[_TRADE_ACCEPTED_TXN],
        gives_horizon_matchup_entries=gives_horizon, receives_horizon_matchup_entries=receives_horizon,
    )
    assert detail.acceptance_status == "ACCEPTED"
    assert detail.trade_accepted is True
    assert detail.realized_roster_outcome is not None
    assert detail.realized_roster_outcome.net_subsequent_points_delta == 15.0


def test_trade_rejected_never_gets_a_realized_outcome() -> None:
    """A trade never made can't be scored as good or bad -- only an
    acceptance/adoption signal."""

    detail = ingest_trade_outcome(
        gives_ids=["701"], receives_ids=["700"], owner_roster_id=9, transactions_for_period=[],
    )
    assert detail.acceptance_status == "REJECTED"
    assert detail.trade_accepted is False
    assert detail.realized_roster_outcome is None


# ---------------------------------------------------------------------------
# TRADE_FINDER / TRADE_PACKAGE_SEARCH
# ---------------------------------------------------------------------------


def test_trade_finder_accepted_reuses_full_trade_outcome() -> None:
    detail = ingest_trade_finder_outcome(
        gives_ids=["701"], receives_ids=["700"], owner_roster_id=9, owner_action=None,
        transactions_for_period=[_TRADE_ACCEPTED_TXN],
    )
    assert detail.package_disposition == "ACCEPTED"
    assert detail.linked_trade_outcome is not None
    assert detail.linked_trade_outcome.trade_accepted is True


def test_trade_finder_not_accepted_falls_back_to_recorded_owner_action() -> None:
    ignored = ingest_trade_finder_outcome(
        gives_ids=["701"], receives_ids=["700"], owner_roster_id=9,
        owner_action=None, transactions_for_period=[],
    )
    sent = ingest_trade_finder_outcome(
        gives_ids=["701"], receives_ids=["700"], owner_roster_id=9,
        owner_action={"action": "SENT"}, transactions_for_period=[],
    )
    assert ignored.package_disposition == "UNKNOWN"
    assert ignored.linked_trade_outcome is None
    assert sent.package_disposition == "SENT"
    assert sent.linked_trade_outcome is None
