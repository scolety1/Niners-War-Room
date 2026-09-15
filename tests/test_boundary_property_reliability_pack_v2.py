"""Prospective Outcomes V1 -- boundary/property reliability pack V2 (Work
Unit 18, per the directive's own numbering).

EXTENDS (never duplicates) `tests/test_boundary_property_reliability_pack_v1.py`
(built one cycle ago, 7 groups numbered 1-4/6/7). That pack targeted bug
classes recurring through the *live_player_intelligence* saga. THIS pack
targets bug classes THIS cycle (Prospective Outcomes V1, Workers 1-5) found
and specifically stressed:

- GROUP 8 -- a genuine, general SWEEP (not a hand-picked example) proving no
  dict anywhere in the real, serialized `redraft_decision_trace_history` /
  `redraft_decision_trace_outcome_summary` HTTP payloads is keyed by a real
  enum/status/disposition value or a real player-id/team-code -- the exact
  bug class this cycle found and fixed TWICE (once in the prior cycle's own
  `_points_by_player_list`, once in this cycle's own new
  `prospective_outcome_history_presentation_v1_service.py`'s first version
  of `class_specific_summaries`/`_as_count_pairs`).
- GROUP 9 -- idempotency, generalized across ALL 8 real evaluators
  (`evaluate_start_sit` / `evaluate_waiver` / `evaluate_add_drop` /
  `evaluate_faab` / `evaluate_trade` / `evaluate_trade_finder` (covers both
  TRADE_FINDER and TRADE_PACKAGE_SEARCH) / `evaluate_k_streamer` /
  `evaluate_dst_streamer`), not just Worker 4's own single orchestrator
  test.
- GROUP 10 -- hindsight-leakage, generalized across the same 8 evaluators:
  structurally proven for the 4 that accept no context/fetch parameter at
  all, and proven-against-a-fabricated-contradictory-future for the 4 that
  do.
- GROUP 11 -- the TRADE-family (TRADE / TRADE_FINDER / TRADE_PACKAGE_SEARCH)
  rejected/unaccepted-disposition guard, generalized into one sweep over a
  representative set of real and fabricated non-accepted disposition
  strings, rather than the one real `REJECTED` case Worker 3's own tests
  covered.

`hypothesis` was RE-CHECKED this pass (`pip show hypothesis` -> not found;
no reference in any requirements file) and is still NOT a dependency of
this repo -- per the directive's own instruction, no new dependency was
added. Group 8 is a genuine, general, automated SWEEP over the real
serialized JSON tree (not example-based at all -- it walks whatever the
real facade call actually produces). Groups 9-11 use a small number of
deliberately-chosen representative/adversarial cases per property (matching
V1's own established convention absent `hypothesis`), each clearly
commented as standing in for the general property it proves.
"""

from __future__ import annotations

import copy
import inspect
import re
from pathlib import Path
from typing import Any

import pytest

from src.application.contracts import camel_case_key, contract_envelope
from src.application.desktop_facade import DesktopBackendFacade
from src.services.in_season_decision_trace_service import (
    TOOL_TYPES,
    DecisionTraceRecord,
    record_decision_trace,
    record_outcome,
    record_owner_action,
)
from src.services.prospective_outcome_evaluation_v1_service import (
    EVALUATION_STATUSES,
    compute_outcome_evaluation,
)
from src.services.prospective_outcome_ingestion_v1_service import (
    ingest_add_drop_outcome,
    ingest_faab_outcome,
    ingest_start_sit_outcome,
    ingest_streamer_outcome,
    ingest_trade_finder_outcome,
    ingest_trade_outcome,
    ingest_waiver_outcome,
)
from src.services.prospective_outcome_source_adapter_v1_service import (
    RealizedOutcomeFetch,
    RecommendationTimeContext,
    recommendation_time_context_from_trace,
)
from src.services.prospective_outcome_add_drop_evaluator_v1_service import evaluate_add_drop
from src.services.prospective_outcome_dst_streamer_evaluator_v1_service import evaluate_dst_streamer
from src.services.prospective_outcome_faab_evaluator_v1_service import evaluate_faab
from src.services.prospective_outcome_k_streamer_evaluator_v1_service import evaluate_k_streamer
from src.services.prospective_outcome_start_sit_evaluator_v1_service import evaluate_start_sit
from src.services.prospective_outcome_trade_evaluator_v1_service import evaluate_trade
from src.services.prospective_outcome_trade_finder_evaluator_v1_service import evaluate_trade_finder
from src.services.prospective_outcome_waiver_evaluator_v1_service import evaluate_waiver

REPO_ROOT = Path(__file__).resolve().parents[1]


def _matchup(week: int, starters: list[str], points: dict[str, float], *, roster_id: int = 9) -> dict[str, Any]:
    return {"roster_id": roster_id, "starters": starters, "players_points": points, "points": sum(points.values())}


def _waiver_transaction(player_id: str, *, bid: float) -> dict[str, Any]:
    return {"type": "waiver", "status": "complete", "adds": {player_id: "9"}, "settings": {"waiver_bid": bid}}


def _trade_transaction(gives: list[str], receives: list[str]) -> dict[str, Any]:
    return {
        "type": "trade", "status": "complete",
        "adds": {pid: "9" for pid in receives}, "drops": {pid: "9" for pid in gives},
    }


# =============================================================================
# GROUP 8 -- No dict anywhere in the real HTTP boundary payload is keyed by
# an enum/status/disposition value or a player-id/team-code.
#
# Real historical bug this targets (found and fixed TWICE): a dict keyed by
# literal DATA (a Sleeper DST team code like "NE"/"SF", or an enum value
# like "EVALUATED") survives `to_dict()`/`summarize_*` correctly in
# isolation, but `desktop_facade.py`'s own HTTP response envelope
# (`contracts.py::camel_case_key`) treats EVERY dict key -- including these
# -- as a schema field name and case-mangles it (`"NE"` -> `"nE"`,
# `"EVALUATED"` -> `"eVALUATED"`). Fixed once in the prior cycle's own
# `_points_by_player_list` (`actualPointsByPlayer` et al, now lists of
# `{playerId, points}` pairs); fixed again THIS cycle in this cycle's own
# NEW `prospective_outcome_history_presentation_v1_service.py`
# (`_as_count_pairs`, `class_specific_summaries` returning a LIST rather
# than a dict keyed by `decisionType`). This is a genuine, general SWEEP --
# not one more hand-picked example -- over the ACTUAL serialized JSON tree a
# real `DesktopBackendFacade` call produces, through the exact real HTTP
# boundary transform (`contract_envelope`).
# =============================================================================


def _build_group_8_profile(root: Path) -> tuple[DesktopBackendFacade, str]:
    """Builds one real, isolated redraft profile with one real trace per
    evaluated decision class PLUS a DRAFT trace (exercises the summary's
    own `{"NOT_APPLICABLE": n}` DRAFT branch -- the trickiest real case
    found while auditing this module for this sweep). Real Sleeper
    team-code ids ("SF") are used deliberately for K/DST -- the exact
    bare-identifier shape that triggered the historical bug."""

    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=root)
    facade.redraft_bootstrap()
    created = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name="Boundary Sweep League")
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)

    def trace(*, tool: str, week: int | None, recommendation: dict, roster_ids: tuple = ("p1", "p2", "p3")):
        return record_decision_trace(
            root, profile_id, league_id="sweep-league-1", season=2026, week=week, tool=tool,
            engine_version="sweep-v1", data_versions={}, roster_state_player_ids=roster_ids,
            recommendation=recommendation,
        )

    t1 = trace(tool="START_SIT", week=1, recommendation={"starters": ["ss-rec-1"]}, roster_ids=("ss-rec-1", "ss-owner-1"))
    d1 = ingest_start_sit_outcome(
        week=1, recommendation={"starters": ["ss-rec-1"]}, roster_state_player_ids=("ss-rec-1", "ss-owner-1"),
        actual_matchup_entry=_matchup(1, ["ss-owner-1"], {"ss-rec-1": 12.0, "ss-owner-1": 9.0}),
    )
    record_outcome(root, profile_id, t1.trace_id, outcome="OBSERVED", detail=d1.to_detail_dict())

    t2 = trace(tool="WAIVER", week=2, recommendation={"topAdd": "Waiver Guy", "topAddCanonicalId": "wv-1"})
    d2 = ingest_waiver_outcome(
        recommended_player_id="wv-1", owner_roster_id=9, transactions_for_period=[_waiver_transaction("wv-1", bid=12)],
        horizon_matchup_entries=[_matchup(3, ["wv-1"], {"wv-1": 9.0})],
    )
    record_outcome(root, profile_id, t2.trace_id, outcome="OBSERVED", detail=d2.to_detail_dict())

    t3 = trace(tool="FAAB", week=2, recommendation={"playerName": "FAAB Guy", "bidLowDollars": 15, "bidHighDollars": 21})
    d3 = ingest_faab_outcome(
        recommended_player_id="faab-1", owner_roster_id=9, suggested_bid_low=15, suggested_bid_high=21,
        transactions_for_period=[_waiver_transaction("faab-1", bid=18)],
        horizon_matchup_entries=[_matchup(3, ["faab-1"], {"faab-1": 8.0})],
    )
    record_outcome(root, profile_id, t3.trace_id, outcome="OBSERVED", detail=d3.to_detail_dict())

    t4 = trace(tool="ADD_DROP", week=2, recommendation={"addedPlayerId": "add-1", "droppedPlayerId": "drop-1"})
    d4 = ingest_add_drop_outcome(
        added_player_id="add-1", dropped_player_id="drop-1", owner_roster_id=9,
        transactions_for_period=[], horizon_matchup_entries=[_matchup(3, ["add-1"], {"add-1": 6.5})],
    )
    record_outcome(root, profile_id, t4.trace_id, outcome="OBSERVED", detail=d4.to_detail_dict())

    t5 = trace(tool="TRADE", week=3, recommendation={"gives": ["give-1"], "receives": ["recv-1"]})
    record_owner_action(root, profile_id, t5.trace_id, action="Followed it")
    d5 = ingest_trade_outcome(
        gives_ids=["give-1"], receives_ids=["recv-1"], owner_roster_id=9,
        transactions_for_period=[_trade_transaction(["give-1"], ["recv-1"])],
        gives_horizon_matchup_entries={"give-1": [_matchup(4, [], {"give-1": 4.0})]},
        receives_horizon_matchup_entries={"recv-1": [_matchup(4, ["recv-1"], {"recv-1": 10.5})]},
    )
    record_outcome(root, profile_id, t5.trace_id, outcome="OBSERVED", detail=d5.to_detail_dict())

    t6 = trace(tool="TRADE", week=3, recommendation={"gives": ["give-2"], "receives": ["recv-2"]})
    record_owner_action(root, profile_id, t6.trace_id, action="Did something else")
    d6 = ingest_trade_outcome(
        gives_ids=["give-2"], receives_ids=["recv-2"], owner_roster_id=9, transactions_for_period=[],
    )
    record_outcome(root, profile_id, t6.trace_id, outcome="OBSERVED", detail=d6.to_detail_dict())

    t7 = trace(tool="TRADE_FINDER", week=3, recommendation={"myGivePlayerId": "tf-give-1", "opponentGivePlayerId": "tf-recv-1"})
    record_owner_action(root, profile_id, t7.trace_id, action="SENT")
    d7 = ingest_trade_finder_outcome(
        gives_ids=["tf-give-1"], receives_ids=["tf-recv-1"], owner_roster_id=9, owner_action={"action": "SENT"},
        transactions_for_period=[_trade_transaction(["tf-give-1"], ["tf-recv-1"])],
        gives_horizon_matchup_entries={"tf-give-1": [_matchup(4, [], {"tf-give-1": 3.0})]},
        receives_horizon_matchup_entries={"tf-recv-1": [_matchup(4, ["tf-recv-1"], {"tf-recv-1": 9.5})]},
    )
    record_outcome(root, profile_id, t7.trace_id, outcome="OBSERVED", detail=d7.to_detail_dict())

    t8 = trace(tool="K_STREAMER", week=2, recommendation={"playerName": "Kicker Guy", "team": "SF"})
    d8 = ingest_streamer_outcome(
        position="K", week=2, recommended_player_id="k-rec-1", prior_roster_option_player_id="k-cur-1",
        available_alternative_ids_at_recommendation=["k-alt-1"],
        actual_matchup_entry=_matchup(2, ["k-rec-1"], {"k-rec-1": 12.0, "k-cur-1": 6.0}),
    )
    record_outcome(root, profile_id, t8.trace_id, outcome="OBSERVED", detail=d8.to_detail_dict())

    # Real Sleeper DST team-code id ("SF") as the recommended/actual id --
    # the exact bare-identifier shape that mangled to "nE"/"sF" before the
    # historical fix.
    t9 = trace(tool="DST_STREAMER", week=2, recommendation={"playerName": "Defense Guy", "team": "SF"})
    d9 = ingest_streamer_outcome(
        position="DST", week=2, recommended_player_id="SF", prior_roster_option_player_id="d-cur-1",
        available_alternative_ids_at_recommendation=["d-alt-1"],
        actual_matchup_entry=_matchup(2, ["SF"], {"SF": 11.0, "d-cur-1": 4.0}),
    )
    record_outcome(root, profile_id, t9.trace_id, outcome="OBSERVED", detail=d9.to_detail_dict())

    # DRAFT: no real evaluator this cycle -- exercises
    # `class_specific_summaries`'s own `{"NOT_APPLICABLE": n}` DRAFT branch.
    trace(tool="DRAFT", week=None, recommendation={"topCandidateId": "draft-1"})

    return facade, profile_id


_KEY_LITERAL_RE = re.compile(r'"([a-zA-Z][a-zA-Z0-9]*)"\s*:')


def _extract_key_literals(source: str) -> set[str]:
    """Real, reproducible static scan (same technique V1's own Group 1
    uses) for every `"<camelCaseKey>":` literal in a module's source --
    the closed universe of real, intentional JSON field names this feature
    actually writes."""

    return {match for match in _KEY_LITERAL_RE.findall(source) if match[:1].islower()}


def _function_body(source: str, def_line_pattern: str) -> str:
    match = re.search(def_line_pattern, source)
    assert match, f"Expected to find {def_line_pattern!r} in the real source."
    rest = source[match.start() + 1:]
    next_def = re.search(r"\n(?:def |class )", rest)
    end = match.start() + 1 + (next_def.start() if next_def else len(rest))
    return source[match.start():end]


_SCHEMA_KEY_SOURCE_FILES = (
    "prospective_outcome_evaluation_v1_service.py",
    "prospective_outcome_start_sit_evaluator_v1_service.py",
    "prospective_outcome_waiver_evaluator_v1_service.py",
    "prospective_outcome_add_drop_evaluator_v1_service.py",
    "prospective_outcome_faab_evaluator_v1_service.py",
    "prospective_outcome_trade_evaluator_v1_service.py",
    "prospective_outcome_trade_finder_evaluator_v1_service.py",
    "prospective_outcome_k_streamer_evaluator_v1_service.py",
    "prospective_outcome_dst_streamer_evaluator_v1_service.py",
    "prospective_outcome_history_presentation_v1_service.py",
    "prospective_outcome_schema_v1_service.py",
)


def _real_schema_field_keys() -> set[str]:
    keys: set[str] = {"contractVersion", "mode", "data", "warnings", "errors"}
    for filename in _SCHEMA_KEY_SOURCE_FILES:
        source = (REPO_ROOT / "src" / "services" / filename).read_text(encoding="utf-8")
        keys |= _extract_key_literals(source)
    facade_source = (REPO_ROOT / "src" / "application" / "desktop_facade.py").read_text(encoding="utf-8")
    keys |= _extract_key_literals(_function_body(facade_source, r"def _decision_trace_history_event_payload\("))
    keys |= _extract_key_literals(_function_body(facade_source, r"def redraft_decision_trace_outcome_summary\("))
    keys |= _extract_key_literals(_function_body(facade_source, r"def redraft_decision_trace_history\("))
    return keys


_BARE_TOKEN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,24}$")

# Real, closed enum/status/disposition vocabularies this feature is known
# to produce as DATA (never legitimately as a dict KEY) -- imported
# constants where they exist, plus the real literal values confirmed by
# reading `prospective_outcome_ingestion_v1_service.py` directly (Worker 3's
# own finding, reused here rather than re-derived).
_KNOWN_ENUM_DATA_VALUES = (
    set(TOOL_TYPES)
    | set(EVALUATION_STATUSES)
    | {"ACCEPTED", "REJECTED", "SENT", "CONSIDERED", "IGNORED", "UNKNOWN"}
    | {"RECOMMENDED", "OWNER_ACTION_RECORDED", "OUTCOME_RECORDED"}  # DecisionTraceRecord.status values
)


def _collect_bare_leaf_strings(node: Any, out: set[str]) -> None:
    if isinstance(node, str):
        if _BARE_TOKEN_RE.match(node):
            out.add(node)
    elif isinstance(node, dict):
        for value in node.values():
            _collect_bare_leaf_strings(value, out)
    elif isinstance(node, (list, tuple)):
        for item in node:
            _collect_bare_leaf_strings(item, out)


def _walk_dicts(node: Any, path: str, out: list[tuple[str, dict]]) -> None:
    if isinstance(node, dict):
        out.append((path, node))
        for key, value in node.items():
            _walk_dicts(value, f"{path}.{key}", out)
    elif isinstance(node, (list, tuple)):
        for index, item in enumerate(node):
            _walk_dicts(item, f"{path}[{index}]", out)


def test_no_dict_anywhere_in_the_real_history_or_summary_payload_is_enum_or_id_keyed(tmp_path: Path) -> None:
    """The general sweep. Real `DesktopBackendFacade` call, real ledger,
    real evaluators, real `contract_envelope` (the exact real HTTP boundary
    transform every route in `server.py` applies) -- walks the ENTIRE
    resulting JSON tree and asserts no dict key anywhere is a member of the
    closed real enum/status/disposition vocabulary (raw OR camelCased) and
    is not also a real, statically-verified schema field name."""

    facade, profile_id = _build_group_8_profile(tmp_path)
    history_data = facade.redraft_decision_trace_history().data
    summary_data = facade.redraft_decision_trace_outcome_summary().data
    history_envelope = contract_envelope("redraft", data=history_data)
    summary_envelope = contract_envelope("redraft", data=summary_data)

    schema_keys = _real_schema_field_keys()

    candidates: set[str] = set(_KNOWN_ENUM_DATA_VALUES)
    _collect_bare_leaf_strings(history_envelope, candidates)
    _collect_bare_leaf_strings(summary_envelope, candidates)
    # Only the values that AREN'T themselves legitimate real field names
    # matter here -- the goal is catching DATA leaking into KEY position.
    suspicious_candidates = candidates - schema_keys
    forbidden_keys = suspicious_candidates | {camel_case_key(value) for value in suspicious_candidates}

    dict_nodes: list[tuple[str, dict]] = []
    _walk_dicts(history_envelope, "history", dict_nodes)
    _walk_dicts(summary_envelope, "summary", dict_nodes)

    violations = [
        (path, key)
        for path, node in dict_nodes
        for key in node
        if key in forbidden_keys and key not in schema_keys
    ]
    assert not violations, (
        f"Found {len(violations)} real dict key(s) in the actual serialized HTTP payload that are "
        f"enum/id-mangled or enum/id-keyed data rather than a real schema field name: {violations[:20]}"
    )


def test_the_two_previously_fixed_bug_instances_stay_fixed_as_concrete_regressions(tmp_path: Path) -> None:
    """Belt-and-suspenders alongside the general sweep above: directly
    re-confirms both real, already-fixed shapes by name, so a future
    refactor that broke either one specifically fails loudly even if the
    general sweep's own logic ever had a gap."""

    facade, profile_id = _build_group_8_profile(tmp_path)
    history_events = facade.redraft_decision_trace_history().data["events"]
    summaries = facade.redraft_decision_trace_outcome_summary().data["summaries"]

    start_sit_event = next(event for event in history_events if event["decisionType"] == "START_SIT")
    detail = start_sit_event["evaluationDetail"]
    # `actualPointsByPlayer` etc. must be LISTS of {playerId, points} pairs,
    # never a dict keyed by a raw player id (the prior cycle's own fix).
    assert isinstance(detail["evaluation"]["factualOutcome"]["detail"]["actualPointsByPlayer"], list)

    for summary in summaries:
        for field_name in ("statusCounts", "acceptanceStatusCounts", "packageDispositionCounts"):
            if field_name in summary:
                # This cycle's own fix: a LIST of {status|disposition, count}
                # pairs, never a dict keyed by a raw enum string.
                assert isinstance(summary[field_name], list), (summary["decisionType"], field_name)


# =============================================================================
# GROUP 9 -- Idempotency, generalized across all 8 real evaluators.
#
# Real historical proof this generalizes: Worker 4's own
# `test_running_ingestion_twice_produces_byte_identical_ledger_state`
# (orchestrator-level, one integration path). This group proves the
# UNDERLYING property directly at the evaluator layer, for every one of the
# 8 real `evaluate_*` functions: calling the SAME evaluator twice on the
# SAME already-recorded trace must produce byte-identical `to_dict()`
# output -- never merely "doesn't crash the second time."
# =============================================================================


def _base_record(*, tool: str, recommendation: dict, week: int | None, roster_ids: tuple = ("p1", "p2"), outcome=None) -> DecisionTraceRecord:
    return DecisionTraceRecord(
        trace_id=f"prop-{tool.lower()}", league_id="lg-prop", profile_id="profile-prop",
        season=2026, week=week, tool=tool, engine_version="v1", data_versions={},
        roster_state_player_ids=roster_ids, free_agent_state_player_ids=None,
        recommendation=recommendation, alternatives=(), recorded_at_utc="2026-09-08T00:00:00+00:00",
        outcome=outcome,
    )


def _representative_evaluated_records() -> dict[str, DecisionTraceRecord]:
    """One deliberately-chosen, fully-EVALUATED real record per class --
    standing in for the general property (no `hypothesis` in this repo, see
    module docstring). Reused by GROUP 9 and (as a baseline) GROUP 10."""

    records: dict[str, DecisionTraceRecord] = {}

    ss_detail = ingest_start_sit_outcome(
        week=1, recommendation={"starters": ["ss-rec-1"]}, roster_state_player_ids=("ss-rec-1", "ss-owner-1"),
        actual_matchup_entry=_matchup(1, ["ss-owner-1"], {"ss-rec-1": 12.0, "ss-owner-1": 9.0}),
    )
    records["START_SIT"] = _base_record(
        tool="START_SIT", recommendation={"starters": ["ss-rec-1"]}, week=1, roster_ids=("ss-rec-1", "ss-owner-1"),
        outcome={"outcome": "OBSERVED", "detail": ss_detail.to_detail_dict()},
    )

    w_detail = ingest_waiver_outcome(
        recommended_player_id="wv-1", owner_roster_id=9, transactions_for_period=[_waiver_transaction("wv-1", bid=12)],
        horizon_matchup_entries=[_matchup(3, ["wv-1"], {"wv-1": 9.0})],
    )
    records["WAIVER"] = _base_record(
        tool="WAIVER", recommendation={"topAddCanonicalId": "wv-1"}, week=2,
        outcome={"outcome": "OBSERVED", "detail": w_detail.to_detail_dict()},
    )

    ad_detail = ingest_add_drop_outcome(
        added_player_id="add-1", dropped_player_id="drop-1", owner_roster_id=9,
        transactions_for_period=[], horizon_matchup_entries=[_matchup(3, ["add-1"], {"add-1": 6.5})],
    )
    records["ADD_DROP"] = _base_record(
        tool="ADD_DROP", recommendation={"addedPlayerId": "add-1", "droppedPlayerId": "drop-1"}, week=2,
        outcome={"outcome": "OBSERVED", "detail": ad_detail.to_detail_dict()},
    )

    f_detail = ingest_faab_outcome(
        recommended_player_id="faab-1", owner_roster_id=9, suggested_bid_low=15, suggested_bid_high=21,
        transactions_for_period=[_waiver_transaction("faab-1", bid=18)],
        horizon_matchup_entries=[_matchup(3, ["faab-1"], {"faab-1": 8.0})],
    )
    records["FAAB"] = _base_record(
        tool="FAAB", recommendation={"playerName": "FAAB Guy", "bidLowDollars": 15, "bidHighDollars": 21}, week=2,
        outcome={"outcome": "OBSERVED", "detail": f_detail.to_detail_dict()},
    )

    tr_detail = ingest_trade_outcome(
        gives_ids=["give-1"], receives_ids=["recv-1"], owner_roster_id=9,
        transactions_for_period=[_trade_transaction(["give-1"], ["recv-1"])],
        gives_horizon_matchup_entries={"give-1": [_matchup(4, [], {"give-1": 4.0})]},
        receives_horizon_matchup_entries={"recv-1": [_matchup(4, ["recv-1"], {"recv-1": 10.5})]},
    )
    records["TRADE"] = _base_record(
        tool="TRADE", recommendation={"gives": ["give-1"], "receives": ["recv-1"]}, week=3,
        outcome={"outcome": "OBSERVED", "detail": tr_detail.to_detail_dict()},
    )

    tf_detail = ingest_trade_finder_outcome(
        gives_ids=["tf-give-1"], receives_ids=["tf-recv-1"], owner_roster_id=9, owner_action={"action": "SENT"},
        transactions_for_period=[_trade_transaction(["tf-give-1"], ["tf-recv-1"])],
        gives_horizon_matchup_entries={"tf-give-1": [_matchup(4, [], {"tf-give-1": 3.0})]},
        receives_horizon_matchup_entries={"tf-recv-1": [_matchup(4, ["tf-recv-1"], {"tf-recv-1": 9.5})]},
    )
    records["TRADE_FINDER"] = _base_record(
        tool="TRADE_FINDER", recommendation={"myGivePlayerId": "tf-give-1", "opponentGivePlayerId": "tf-recv-1"}, week=3,
        outcome={"outcome": "OBSERVED", "detail": tf_detail.to_detail_dict()},
    )

    k_detail = ingest_streamer_outcome(
        position="K", week=2, recommended_player_id="k-rec-1", prior_roster_option_player_id="k-cur-1",
        available_alternative_ids_at_recommendation=["k-alt-1"],
        actual_matchup_entry=_matchup(2, ["k-rec-1"], {"k-rec-1": 12.0, "k-cur-1": 6.0}),
    )
    records["K_STREAMER"] = _base_record(
        tool="K_STREAMER", recommendation={"playerName": "Kicker Guy", "team": "SF"}, week=2,
        outcome={"outcome": "OBSERVED", "detail": k_detail.to_detail_dict()},
    )

    d_detail = ingest_streamer_outcome(
        position="DST", week=2, recommended_player_id="SF", prior_roster_option_player_id="d-cur-1",
        available_alternative_ids_at_recommendation=["d-alt-1"],
        actual_matchup_entry=_matchup(2, ["SF"], {"SF": 11.0, "d-cur-1": 4.0}),
    )
    records["DST_STREAMER"] = _base_record(
        tool="DST_STREAMER", recommendation={"playerName": "Defense Guy", "team": "SF"}, week=2,
        outcome={"outcome": "OBSERVED", "detail": d_detail.to_detail_dict()},
    )

    return records


_ALL_EVALUATORS: dict[str, Any] = {
    "START_SIT": evaluate_start_sit,
    "WAIVER": evaluate_waiver,
    "ADD_DROP": evaluate_add_drop,
    "FAAB": evaluate_faab,
    "TRADE": evaluate_trade,
    "TRADE_FINDER": evaluate_trade_finder,
    "K_STREAMER": evaluate_k_streamer,
    "DST_STREAMER": evaluate_dst_streamer,
}


def test_every_evaluator_is_idempotent_across_a_representative_sweep() -> None:
    """GENERALIZES the orchestrator's own single idempotency test across all
    8 real evaluator functions: calling `evaluate_*` twice (three times,
    the third against a fully independent deep-copied record) on the SAME
    already-recorded trace must produce byte-identical `to_dict()` output
    every time."""

    records = _representative_evaluated_records()
    for tool, evaluator in _ALL_EVALUATORS.items():
        record = records[tool]
        first = evaluator(record).to_dict()
        second = evaluator(record).to_dict()
        third = evaluator(copy.deepcopy(record)).to_dict()
        assert first == second == third, f"evaluate_* for {tool!r} is not idempotent."


def test_class_specific_summaries_is_idempotent_over_the_same_result_set() -> None:
    """The one real aggregation layer this cycle built
    (`class_specific_summaries`) is itself a pure function of its inputs --
    calling it twice over the exact same evaluated records must also
    produce byte-identical output."""

    from src.services.prospective_outcome_history_presentation_v1_service import class_specific_summaries

    records = list(_representative_evaluated_records().values())
    first = class_specific_summaries(records)
    second = class_specific_summaries(records)
    assert first == second


# =============================================================================
# GROUP 10 -- Hindsight-leakage, generalized across all 8 real evaluators.
#
# Real historical proof this generalizes: Worker 1's own
# `test_context_is_structurally_immune_to_a_later_contradictory_fetch` (one
# adapter-layer test) plus Workers 2/3's own individual per-evaluator
# no-hindsight tests. This group proves it as ONE property that runs
# against all 8: for the 4 evaluators with no context/fetch parameter at
# all, the guarantee is STRUCTURAL (proven by signature introspection --
# there is no parameter through which a future fact could leak); for the 4
# that DO accept an optional context/fetch, a deliberately fabricated,
# CONTRADICTORY "future" object is passed in and the already-recorded
# realized-outcome facts (read only from the trace's own immutable
# `outcome.detail`) are proven unchanged.
# =============================================================================


_CONTEXT_FREE_EVALUATORS = {
    "ADD_DROP": evaluate_add_drop,
    "FAAB": evaluate_faab,
    "K_STREAMER": evaluate_k_streamer,
    "DST_STREAMER": evaluate_dst_streamer,
}


def test_context_free_evaluators_structurally_cannot_accept_a_future_state_parameter() -> None:
    for tool, evaluator in _CONTEXT_FREE_EVALUATORS.items():
        params = set(inspect.signature(evaluator).parameters)
        assert params == {"record"}, (
            f"evaluate_* for {tool!r} accepts parameter(s) beyond `record` ({params - {'record'}}) -- "
            "a future data point could leak in through one."
        )


def test_start_sit_matchup_fetch_never_overrides_the_already_recorded_outcome() -> None:
    record = _representative_evaluated_records()["START_SIT"]
    baseline = evaluate_start_sit(record)
    contradictory_fetch = RealizedOutcomeFetch(
        source="FABRICATED_FUTURE", league_id=record.league_id, fetched_at_utc="2099-01-01T00:00:00+00:00",
        payload={"players_points": {"ss-rec-1": 999.0, "ss-owner-1": -999.0}},
    )
    contaminated = evaluate_start_sit(record, matchup_fetch=contradictory_fetch)
    assert contaminated.evaluation.to_dict() == baseline.evaluation.to_dict()
    assert contaminated.lineup_opportunity_cost_points == baseline.lineup_opportunity_cost_points
    assert contaminated.recommended_player_realized_points == baseline.recommended_player_realized_points
    assert contaminated.owner_selected_player_realized_points == baseline.owner_selected_player_realized_points


def test_waiver_contradictory_context_never_changes_the_already_recorded_realized_facts() -> None:
    record = _representative_evaluated_records()["WAIVER"]
    baseline = evaluate_waiver(record)
    real_ctx = recommendation_time_context_from_trace(record)
    # A fabricated future context flatly contradicts reality (claims a
    # totally different free-agent snapshot) -- this MAY legitimately
    # change `claimableAtRecommendationTime` (a real, recommendation-TIME
    # field, not a hindsight fact), but must never touch the already-
    # recorded realized facts (all read only from the immutable
    # `outcome.detail`).
    contradictory_ctx = RecommendationTimeContext(
        trace_id=real_ctx.trace_id, decision_type=real_ctx.decision_type, league_id=real_ctx.league_id,
        profile_id=real_ctx.profile_id, week=real_ctx.week, recommendation=real_ctx.recommendation,
        roster_state_player_ids=real_ctx.roster_state_player_ids,
        free_agent_state_player_ids=("some-other-player-entirely",),
        alternatives=real_ctx.alternatives, owner_action=real_ctx.owner_action,
    )
    contaminated = evaluate_waiver(record, context=contradictory_ctx)
    assert contaminated.evaluation.to_dict() == baseline.evaluation.to_dict()
    assert contaminated.claim_submitted == baseline.claim_submitted
    assert contaminated.claim_won == baseline.claim_won
    assert contaminated.faab_paid == baseline.faab_paid
    assert contaminated.subsequent_total_points == baseline.subsequent_total_points


def test_trade_contradictory_context_never_changes_the_already_recorded_realized_delta() -> None:
    record = _representative_evaluated_records()["TRADE"]
    baseline = evaluate_trade(record)
    real_ctx = recommendation_time_context_from_trace(record)
    contradictory_ctx = RecommendationTimeContext(
        trace_id=real_ctx.trace_id, decision_type=real_ctx.decision_type, league_id=real_ctx.league_id,
        profile_id=real_ctx.profile_id, week=real_ctx.week,
        recommendation={"gives": ["future-give"], "receives": ["future-recv"]},
        roster_state_player_ids=real_ctx.roster_state_player_ids,
        free_agent_state_player_ids=real_ctx.free_agent_state_player_ids,
        alternatives=real_ctx.alternatives, owner_action={"action": "REJECTED_LATER_SOMEHOW"},
    )
    contaminated = evaluate_trade(record, context=contradictory_ctx)
    assert contaminated.evaluation.to_dict() == baseline.evaluation.to_dict()
    assert contaminated.net_subsequent_points_delta_points == baseline.net_subsequent_points_delta_points
    assert contaminated.trade_accepted == baseline.trade_accepted
    # The contradictory context's `recommendation`/`owner_action` DO
    # legitimately flow into these recommendation-time-only fields -- proves
    # the isolation is real (only the realized-outcome facts are immune),
    # not that the context is silently ignored altogether.
    assert contaminated.recommended_gives_ids == ("future-give",)
    assert contaminated.owner_action_raw == "REJECTED_LATER_SOMEHOW"


def test_trade_finder_contradictory_context_never_changes_the_already_recorded_realized_delta() -> None:
    record = _representative_evaluated_records()["TRADE_FINDER"]
    baseline = evaluate_trade_finder(record)
    real_ctx = recommendation_time_context_from_trace(record)
    contradictory_ctx = RecommendationTimeContext(
        trace_id=real_ctx.trace_id, decision_type=real_ctx.decision_type, league_id=real_ctx.league_id,
        profile_id=real_ctx.profile_id, week=real_ctx.week,
        recommendation={"myGivePlayerId": "future-give", "opponentGivePlayerId": "future-recv"},
        roster_state_player_ids=real_ctx.roster_state_player_ids,
        free_agent_state_player_ids=real_ctx.free_agent_state_player_ids,
        alternatives=real_ctx.alternatives, owner_action={"action": "IGNORED"},
    )
    contaminated = evaluate_trade_finder(record, context=contradictory_ctx)
    assert contaminated.evaluation.to_dict() == baseline.evaluation.to_dict()
    assert contaminated.net_subsequent_points_delta_points == baseline.net_subsequent_points_delta_points
    assert contaminated.package_disposition == baseline.package_disposition


# =============================================================================
# GROUP 11 -- TRADE-family rejected/unaccepted-disposition guard, swept over
# a representative set of real and fabricated non-accepted dispositions.
#
# Real historical proof this generalizes: Worker 3's own per-tool tests
# (one real `REJECTED` TRADE case, one real non-`ACCEPTED` package-
# disposition case per tool). This sweep proves the SAME guard holds across
# a wider representative set of disposition strings (including deliberately
# fabricated/inconsistent ones no real ingestion function would produce, to
# prove the EVALUATION layer's own guard -- not just the ingestion layer's
# own discipline -- is what actually blocks a scored counterfactual).
# =============================================================================


def _trade_record_with_raw_detail(*, tool: str, detail: dict) -> DecisionTraceRecord:
    recommendation = (
        {"gives": ["g"], "receives": ["r"]}
        if tool == "TRADE"
        else {"myGivePlayerId": "g", "opponentGivePlayerId": "r"}
    )
    return _base_record(
        tool=tool, recommendation=recommendation, week=3,
        outcome={"outcome": "OBSERVED", "detail": detail},
    )


_NON_ACCEPTED_TRADE_ACCEPTANCE_STATUSES = ("REJECTED", "PENDING", "CANCELLED", "UNKNOWN", "")
_NON_ACCEPTED_PACKAGE_DISPOSITIONS = ("SENT", "CONSIDERED", "IGNORED", "UNKNOWN", "PENDING", "WITHDRAWN")


def test_no_non_accepted_trade_ever_produces_a_scored_realized_outcome() -> None:
    for status in _NON_ACCEPTED_TRADE_ACCEPTANCE_STATUSES:
        detail = {
            "kind": "TRADE_V1", "acceptanceStatus": status, "tradeAccepted": False,
            # A caller could (maliciously or by bug) fabricate realized data
            # alongside a non-accepted status -- it must never be scored.
            "realizedRosterOutcome": {
                "netSubsequentPointsDelta": 999.0,
                "givesSubsequentPointsByPlayer": [{"playerId": "g", "points": 1.0}],
                "receivesSubsequentPointsByPlayer": [{"playerId": "r", "points": 500.0}],
            },
        }
        record = _trade_record_with_raw_detail(tool="TRADE", detail=detail)
        evaluation = compute_outcome_evaluation(record)
        assert evaluation.evaluation_status == "NOT_APPLICABLE", status
        assert evaluation.evaluation_metrics == {}, status
        result = evaluate_trade(record)
        assert result.net_subsequent_points_delta_points is None, status
        assert result.trade_accepted is not True, status

    # A deliberately INCONSISTENT fabrication (tradeAccepted=True but
    # acceptanceStatus not ACCEPTED) must also refuse to score -- the guard
    # checks BOTH fields, never just one.
    inconsistent_detail = {
        "kind": "TRADE_V1", "acceptanceStatus": "REJECTED", "tradeAccepted": True,
        "realizedRosterOutcome": {"netSubsequentPointsDelta": 42.0},
    }
    record = _trade_record_with_raw_detail(tool="TRADE", detail=inconsistent_detail)
    evaluation = compute_outcome_evaluation(record)
    assert evaluation.evaluation_status == "NOT_APPLICABLE"
    assert evaluation.evaluation_metrics == {}


def test_no_non_accepted_trade_package_ever_produces_a_scored_realized_outcome() -> None:
    for disposition in _NON_ACCEPTED_PACKAGE_DISPOSITIONS:
        for tool in ("TRADE_FINDER", "TRADE_PACKAGE_SEARCH"):
            detail = {
                "kind": "TRADE_FINDER_V1", "packageDisposition": disposition,
                # Even a LINKED, genuinely-accepted-looking trade outcome
                # must never be surfaced when the package's own disposition
                # itself is not ACCEPTED.
                "linkedTradeOutcome": {
                    "kind": "TRADE_V1", "acceptanceStatus": "ACCEPTED", "tradeAccepted": True,
                    "realizedRosterOutcome": {"netSubsequentPointsDelta": 999.0},
                },
            }
            record = _trade_record_with_raw_detail(tool=tool, detail=detail)
            evaluation = compute_outcome_evaluation(record)
            assert evaluation.evaluation_status == "NOT_APPLICABLE", (tool, disposition)
            assert evaluation.evaluation_metrics == {}, (tool, disposition)
            result = evaluate_trade_finder(record)
            assert result.net_subsequent_points_delta_points is None, (tool, disposition)
            assert result.trade_accepted is not True, (tool, disposition)


def test_a_genuinely_accepted_trade_package_is_the_one_real_case_that_does_score() -> None:
    """The positive control for GROUP 11 -- proves the guard is a real gate,
    not a function that always returns NOT_APPLICABLE regardless of input."""

    detail = {
        "kind": "TRADE_FINDER_V1", "packageDisposition": "ACCEPTED",
        "linkedTradeOutcome": {
            "kind": "TRADE_V1", "acceptanceStatus": "ACCEPTED", "tradeAccepted": True,
            "realizedRosterOutcome": {
                "netSubsequentPointsDelta": 6.5,
                "givesSubsequentPointsByPlayer": [{"playerId": "g", "points": 4.0}],
                "receivesSubsequentPointsByPlayer": [{"playerId": "r", "points": 10.5}],
            },
        },
    }
    record = _trade_record_with_raw_detail(tool="TRADE_FINDER", detail=detail)
    evaluation = compute_outcome_evaluation(record)
    assert evaluation.evaluation_status == "EVALUATED"
    result = evaluate_trade_finder(record)
    assert result.net_subsequent_points_delta_points == 6.5
    assert result.trade_accepted is True
