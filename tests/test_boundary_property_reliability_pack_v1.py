"""History UI V2 / Work Unit 15 -- boundary/property reliability pack.

Per the governing directive: a SMALL NUMBER of STRONG, GENERAL property/
contract tests targeting the SAME recurring bug classes this whole
multi-session saga has hit repeatedly, rather than more example-based
fixtures for individual features. Each test group below names the real,
already-fixed (or, in one case, found-and-fixed-BY-this-pass) historical
bug it targets.

`hypothesis` was checked and is NOT a dependency of this repo (`pip show
hypothesis` -> not found; no reference in any requirements file). Per the
directive's own instruction, no new dependency was added -- every
"property" test below instead uses either (a) EXHAUSTIVE enumeration over
a small, real input space (`itertools.permutations` over a handful of
observations -- genuinely exhaustive, not merely random-sampled, for the
sizes used here), or (b) a small number of deliberately-chosen
representative/adversarial cases, each commented as standing in for the
general property it proves.
"""

from __future__ import annotations

import itertools
import re
from pathlib import Path

import pytest

from src.application.contracts import camel_case_key, contract_envelope, public_json_value
from src.services.in_season_decision_trace_service import (
    TOOL_TYPES,
    load_decision_traces,
    record_decision_trace,
    record_outcome,
)
from src.services.live_player_intelligence_composition_v1_service import (
    PRECEDENCE_ADMITTED_AUTOMATED_FACTUAL_SOURCE,
    PRECEDENCE_MANUAL_VERIFIED_OVERRIDE,
    PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
    ComposedField,
    FieldObservation,
    compose_field,
)
from src.services.prospective_outcome_ingestion_v1_service import (
    ingest_add_drop_outcome,
    ingest_start_sit_outcome,
    ingest_waiver_outcome,
)
from src.services.prospective_outcome_schema_v1_service import (
    AddDropOutcomeDetail,
    DraftOutcomeDetail,
    FaabOutcomeDetail,
    StartSitOutcomeDetail,
    StreamerOutcomeDetail,
    TradeFinderOutcomeDetail,
    TradeOutcomeDetail,
    WaiverOutcomeDetail,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DESKTOP_FACADE_SOURCE = (REPO_ROOT / "src" / "application" / "desktop_facade.py").read_text(encoding="utf-8")
TS_CONTRACTS_SOURCE = (
    REPO_ROOT / "desktop" / "packages" / "contracts" / "src" / "index.ts"
).read_text(encoding="utf-8")


# =============================================================================
# GROUP 1 -- Decision-type registry completeness.
#
# Real historical bug this targets: TRADE_FINDER/TRADE_PACKAGE_SEARCH were
# called with `tool="TRADE_FINDER"`/`tool="TRADE_PACKAGE_SEARCH"` at real
# facade call sites, but neither string was a member of the OLD
# `TOOL_TYPES` set -- every such call silently raised `DecisionTraceError`,
# caught by `_record_decision_trace_safe`'s best-effort wrapper, so both
# tools recorded ZERO real traces in production despite looking wired.
# =============================================================================


def _literal_tool_call_sites() -> set[str]:
    """Every `tool="LITERAL"` string passed to `record_decision_trace`/
    `_record_decision_trace_safe` anywhere in the facade -- a real,
    reproducible static scan, not a hand-maintained list."""

    return set(re.findall(r'tool="([A-Z_]+)"', DESKTOP_FACADE_SOURCE))


def _dynamic_tool_name_call_site_values() -> set[str]:
    """The one real dynamic call site (`tool=tool_name`, the K/DST Streamer
    loop) -- resolved from its own real source tuple
    (`for position, tool_name in (("K", "K_STREAMER"), ("DST",
    "DST_STREAMER")):`) rather than skipped just because it isn't a bare
    string literal at the call site itself."""

    match = re.search(
        r'for position, tool_name in (.+?):\n',
        DESKTOP_FACADE_SOURCE,
    )
    assert match, "Expected to find the real K/DST Streamer tool_name loop in desktop_facade.py"
    pairs = re.findall(r'\("[A-Z]+",\s*"([A-Z_]+)"\)', match.group(1))
    assert pairs, "Expected at least one (position, tool_name) pair"
    return set(pairs)


def test_every_literal_tool_call_site_in_the_facade_is_a_registered_tool_type() -> None:
    """The exact bug class that silently dropped TRADE_FINDER/
    TRADE_PACKAGE_SEARCH traces: a real call site's `tool=` value must be a
    member of `TOOL_TYPES`, or `record_decision_trace` raises
    `DecisionTraceError` and the best-effort wrapper silently swallows it."""

    literal_sites = _literal_tool_call_sites()
    assert literal_sites, "Expected to find real tool=\"...\" call sites in desktop_facade.py"
    unregistered = literal_sites - TOOL_TYPES
    assert not unregistered, (
        f"Real facade call site(s) use unregistered tool type(s) {unregistered} -- "
        f"every real recommendation for that tool silently fails to record."
    )


def test_the_dynamic_streamer_tool_name_call_site_is_also_fully_registered() -> None:
    dynamic_values = _dynamic_tool_name_call_site_values()
    assert dynamic_values == {"K_STREAMER", "DST_STREAMER"}
    unregistered = dynamic_values - TOOL_TYPES
    assert not unregistered, f"Dynamic tool_name value(s) {unregistered} are not registered TOOL_TYPES members"


def test_every_real_facade_tool_call_site_round_trips_through_a_real_record_decision_trace_call(tmp_path) -> None:
    """Stronger than the string-membership check above: every real literal
    tool used at a facade call site must ALSO actually succeed as a real
    `record_decision_trace` call (not merely be present in the `TOOL_TYPES`
    set by coincidence) -- proves the registry is genuinely load-bearing,
    not just a matching string."""

    all_real_tools = _literal_tool_call_sites() | _dynamic_tool_name_call_site_values()
    assert all_real_tools, "Expected at least one real tool to check"
    for tool in sorted(all_real_tools):
        trace = record_decision_trace(
            tmp_path, "registry-completeness-probe", league_id="lg1", season=2026, week=1,
            tool=tool, engine_version="test", data_versions={}, roster_state_player_ids=["1"],
            recommendation={},
        )
        assert trace.tool == tool


# =============================================================================
# GROUP 2 -- Backend enum -> API -> TS contract round-trip.
#
# Real historical bug class this targets: the backend once emitted FAAB
# urgency values (`STARTER_UPGRADE`/`BENCH_DEPTH`/`LOW_VALUE`) that the
# frontend's lookup table never recognized (see
# `weekly-shared.test.ts`'s own `FAAB_URGENCY_TONE` regression test for
# that specific, already-fixed case). This group targets the SAME class for
# every real enum this pass's own work introduced: `TOOL_TYPES`'s
# `DecisionTraceToolType` mirror, the outcome-detail `KIND` constants'
# `DecisionTraceOutcomeDetail` union, `TRADE_ACCEPTANCE_STATUSES`, and
# `TRADE_PACKAGE_DISPOSITIONS`.
# =============================================================================


def _ts_string_union_literals(type_name: str) -> set[str]:
    """Extracts every quoted string literal from a TS `export type
    <type_name> = "A" | "B" | ...;` declaration in the real contracts
    source -- a real, reproducible static parse, not a hand-copied list
    that could silently drift from the actual file."""

    match = re.search(rf"export type {re.escape(type_name)} =([^;]+);", TS_CONTRACTS_SOURCE)
    assert match, f"Expected to find `export type {type_name} = ...` in contracts/src/index.ts"
    return set(re.findall(r'"([A-Za-z0-9_]+)"', match.group(1)))


def _ts_kind_literals() -> set[str]:
    """Every `kind: "LITERAL";` discriminant across the outcome-detail
    interfaces in the real contracts source."""

    literals = set(re.findall(r'kind:\s*"([A-Z0-9_]+)";', TS_CONTRACTS_SOURCE))
    assert literals, "Expected to find at least one `kind: \"...\";` TS discriminant"
    return literals


def test_tool_types_round_trips_into_the_ts_decision_trace_tool_type_union() -> None:
    assert TOOL_TYPES == _ts_string_union_literals("DecisionTraceToolType")


def test_every_real_outcome_detail_kind_round_trips_into_the_ts_contract() -> None:
    python_kinds = {
        StartSitOutcomeDetail.KIND, WaiverOutcomeDetail.KIND, AddDropOutcomeDetail.KIND,
        FaabOutcomeDetail.KIND, TradeOutcomeDetail.KIND, TradeFinderOutcomeDetail.KIND,
        StreamerOutcomeDetail.KIND, DraftOutcomeDetail.KIND,
    }
    assert len(python_kinds) == 8  # genuinely distinct, per prospective_outcome_schema_v1_service's own test
    assert python_kinds == _ts_kind_literals()


def test_trade_acceptance_statuses_round_trip_into_the_ts_contract() -> None:
    from src.services.prospective_outcome_schema_v1_service import TRADE_ACCEPTANCE_STATUSES

    assert TRADE_ACCEPTANCE_STATUSES == _ts_string_union_literals("TradeAcceptanceStatus")


def test_trade_package_dispositions_round_trip_into_the_ts_contract() -> None:
    from src.services.prospective_outcome_schema_v1_service import TRADE_PACKAGE_DISPOSITIONS

    assert TRADE_PACKAGE_DISPOSITIONS == _ts_string_union_literals("TradePackageDisposition")


def test_decision_trace_status_values_round_trip_into_the_ts_contract() -> None:
    """`in_season_decision_trace_service.py` has no single named STATUS
    constant (status is computed inline as one of three literal strings) --
    scanned directly from its own real source rather than invented here."""

    trace_service_source = (
        REPO_ROOT / "src" / "services" / "in_season_decision_trace_service.py"
    ).read_text(encoding="utf-8")
    python_statuses = {
        status for status in ("RECOMMENDED", "OWNER_ACTION_RECORDED", "OUTCOME_RECORDED")
        if f'"{status}"' in trace_service_source
    }
    assert python_statuses == {"RECOMMENDED", "OWNER_ACTION_RECORDED", "OUTCOME_RECORDED"}
    assert python_statuses == _ts_string_union_literals("DecisionTraceStatus")


# =============================================================================
# GROUP 3 -- snake_case <-> camelCase JSON-boundary property.
#
# Real bug FOUND AND FIXED by this same pass (see
# `prospective_outcome_schema_v1_service.py`'s `_points_by_player_list` and
# its own docstring for the full account, and the already-existing
# precedent this pass followed: `test_desktop_application_api.py`'s /
# `test_redraft_draft_room_v1_service.py`'s own real "K"/"DST"/"QB"
# key-mangling regressions from earlier in this saga): the shared
# `camel_case_key` (`application/contracts.py`) treats EVERY dict key as a
# schema field name, not literal data -- a dict keyed by a literal,
# all-caps, no-separator player/position id (e.g. Sleeper's DST team-code
# ids) gets its first letter lowercased ("NE" -> "nE", "WR" -> "wR").
# =============================================================================


@pytest.mark.parametrize(
    "raw_key, expected_camel",
    [
        ("player_id", "playerId"),
        ("actual_points_total", "actualPointsTotal"),
        ("week_1_total", "week1Total"),
        ("alreadyCamel", "alreadyCamel"),
        ("Already-Kebab-ish", "alreadyKebabIsh"),
        ("", ""),  # no separators present at all -> the no-separator branch, unchanged (empty stays empty)
        ("___", "value"),  # all-separator key with zero real parts -> the documented "value" fallback
    ],
)
def test_camel_case_key_transforms_real_schema_field_names_correctly(raw_key: str, expected_camel: str) -> None:
    assert camel_case_key(raw_key) == expected_camel


def test_camel_case_key_is_idempotent_on_its_own_output() -> None:
    """A key that has ALREADY been camelCased must be unchanged by a second
    pass -- this is exactly what makes it safe for `public_json_value` to
    be applied more than once to the same payload at different layers
    (e.g. `_decision_trace_history_event_payload` builds an already-
    camelCase dict, which is then run through `public_json_value` AGAIN by
    `contract_envelope` at the HTTP boundary)."""

    for raw_key in ["player_id", "actual_points_total", "recommendedStarterIds", "NE", "WR", "11560"]:
        once = camel_case_key(raw_key)
        twice = camel_case_key(once)
        assert once == twice, f"camel_case_key is not idempotent for {raw_key!r}: {once!r} -> {twice!r}"


@pytest.mark.parametrize("literal_id", ["NE", "WR", "QB", "DST", "SF", "TB", "A", "Z"])
def test_a_literal_all_caps_id_used_as_a_dict_KEY_is_silently_mangled_this_is_the_real_bug_class(
    literal_id: str,
) -> None:
    """This is NOT a bug in `camel_case_key` itself -- it is documenting,
    with a real assertion, exactly why a literal value may never be used as
    a JSON dict key anywhere data crosses this boundary. Several
    representative all-caps ids (real Sleeper DST team codes and position
    codes among them) are swept here, standing in for the general
    property: ANY all-caps, no-separator string used as a dict key is
    corrupted. This is the same conclusion `_points_by_player_list`'s own
    docstring reaches and fixes for real, live data (see the next test)."""

    mangled = camel_case_key(literal_id)
    assert mangled != literal_id
    assert mangled[0].islower()


def test_real_player_points_map_survives_the_full_http_json_boundary_intact(tmp_path) -> None:
    """The real, end-to-end regression proof: a `StartSitOutcomeDetail`
    whose `actual_points_by_player_id` includes a real Sleeper DST team-
    code id ("NE") is recorded via `record_outcome`, read back, projected
    through the EXACT `_decision_trace_history_event_payload` shape the
    facade uses, and then run through `contract_envelope` -- the SAME
    function that puts every real HTTP response through `public_json_value`
    a SECOND time. Before this pass's fix (a dict keyed by player id), "NE"
    would have arrived at the frontend as "nE". After the fix (a list of
    {playerId, points} objects), it survives intact."""

    from src.application.desktop_facade import _decision_trace_history_event_payload
    from src.services.prospective_outcome_schema_v1_service import StartSitOutcomeDetail

    trace = record_decision_trace(
        tmp_path, "camel-case-boundary-probe", league_id="lg1", season=2026, week=1,
        tool="START_SIT", engine_version="test", data_versions={},
        roster_state_player_ids=["100", "NE"], recommendation={"starters": ["100", "NE"]},
    )
    detail = StartSitOutcomeDetail(
        week=1, recommended_starter_ids=("100", "NE"), actual_starter_ids=("100", "NE"),
        eligible_alternative_ids_at_lock=(), recommended_only_ids=(), actual_only_ids=(),
        recommended_projected_total=None, actual_points_total=20.0,
        actual_points_by_player_id={"100": 14.0, "NE": 6.0}, lineup_opportunity_cost=0.0,
    )
    updated = record_outcome(
        tmp_path, "camel-case-boundary-probe", trace.trace_id,
        outcome="STARTER_MATCHED_RECOMMENDATION", detail=detail.to_detail_dict(),
    )
    reloaded = load_decision_traces(tmp_path, "camel-case-boundary-probe")[0]

    facade_payload = _decision_trace_history_event_payload(reloaded)
    envelope = contract_envelope("redraft", data=facade_payload)

    points_list = envelope["data"]["outcome"]["detail"]["actualPointsByPlayer"]
    ids_seen = {entry["playerId"] for entry in points_list}
    assert "NE" in ids_seen, f"Real player id 'NE' was corrupted -- got ids {ids_seen}"
    assert "nE" not in ids_seen
    ne_entry = next(entry for entry in points_list if entry["playerId"] == "NE")
    assert ne_entry["points"] == 6.0
    assert updated.trace_id == trace.trace_id  # sanity: same trace, outcome appended not replaced


def test_public_json_value_transforms_keys_correctly_at_every_nesting_depth() -> None:
    """A few representative nesting shapes standing in for the general
    property "every nested dict's keys are transformed, no matter how
    deep" -- a dict-in-list-in-dict-in-dict, four levels."""

    nested = {
        "top_level_field": {
            "second_level": [
                {"third_level_id": "abc", "fourth_level": {"deep_field_name": 1}},
            ],
        },
    }
    result = public_json_value(nested)
    assert "topLevelField" in result
    assert "secondLevel" in result["topLevelField"]
    inner = result["topLevelField"]["secondLevel"][0]
    assert inner["thirdLevelId"] == "abc"
    assert inner["fourthLevel"]["deepField_name".replace("_name", "Name")] == 1
    assert inner["fourthLevel"] == {"deepFieldName": 1}


# =============================================================================
# GROUP 4 -- Canonical ID / provider ID invariant.
#
# Real historical bug this targets: the old Find Trades "Open in Analyze"
# button passed NWR's own canonical (GSIS-style) player ids into
# `redraft_trade_analysis`, which requires real raw Sleeper ids -- an
# always-fails path for the real opponent side (see
# `test_redraft_identity_boundary_opponent_and_trade_finder.py`, the
# existing example-based fix/proof this test generalizes). This group
# statically enumerates EVERY real facade decision-trace call site (not
# just the one Trade Finder surface the earlier fix targeted) and checks
# each records the id-space Worker 5's own ingestion module docstring
# says it must: START_SIT/K_STREAMER/DST_STREAMER get raw Sleeper ids
# (`weekly_lineup_optimizer_service`/a raw Sleeper roster read), every
# other real tool gets NWR's own resolved canonical ids.
# =============================================================================

# (tool, expected id-space marker actually present in its real
# `roster_state_player_ids=` expression). Real source lines this was
# derived from are quoted in the assertion failure message on mismatch.
_EXPECTED_ROSTER_ID_SPACE = {
    "START_SIT": "sleeper",
    "K_STREAMER": "sleeper",  # own_roster_player_ids <- own_roster.get("players"), a raw Sleeper roster read
    "DST_STREAMER": "sleeper",
    "WAIVER": "canonical",
    "FAAB": "canonical",
    "TRADE": "canonical",
    "TRADE_FINDER": "canonical",
    "TRADE_PACKAGE_SEARCH": "canonical",
}


def _roster_state_expression_for_tool(tool_literal_or_marker: str) -> str:
    """Finds the real `roster_state_player_ids=<expr>` text on the line(s)
    immediately following a real `tool="..."` (or the K/DST streamer's own
    `tool=tool_name,` line) call-site marker in the real facade source."""

    if tool_literal_or_marker in ("K_STREAMER", "DST_STREAMER"):
        anchor = "week=week, tool=tool_name,"
    else:
        anchor = f'tool="{tool_literal_or_marker}"'
    index = DESKTOP_FACADE_SOURCE.index(anchor)
    window = DESKTOP_FACADE_SOURCE[index:index + 700]
    match = re.search(r"roster_state_player_ids=([^\n,]+(?:\([^)]*\))?)", window)
    assert match, f"Expected a roster_state_player_ids= expression near tool marker {tool_literal_or_marker!r}"
    return match.group(1)


@pytest.mark.parametrize("tool, expected_space", sorted(_EXPECTED_ROSTER_ID_SPACE.items()))
def test_each_real_decision_trace_call_site_uses_the_documented_id_space(tool: str, expected_space: str) -> None:
    expression = _roster_state_expression_for_tool(tool)
    if expected_space == "canonical":
        assert "canonical" in expression, (
            f"{tool}'s real roster_state_player_ids expression {expression!r} does not reference a "
            f"canonical id resolution -- a real regression risk for the exact 'Open in Analyze' "
            f"canonical-vs-provider-id bug class."
        )
        assert "sleeper_player_id" not in expression
    else:
        assert "sleeper" in expression or "own_roster" in expression, (
            f"{tool}'s real roster_state_player_ids expression {expression!r} does not reference a raw "
            f"Sleeper id source."
        )
        assert "canonical" not in expression


def test_ingestion_module_explicitly_documents_which_decision_types_need_no_resolution_step() -> None:
    """START_SIT and K/DST_STREAMER's ingestion functions consume raw
    Sleeper ids directly (matching the facade's real recorded id space,
    proven above) -- `ingest_start_sit_outcome` must never be handed a
    canonical id disguised as a Sleeper id and silently "succeed" by
    coincidence. Real, minimal-shape proof: a canonical-style id
    ("00-0023459") passed where a real matchup's `starters` are Sleeper
    numeric ids simply never matches -- an honest zero-overlap outcome,
    never a silently-wrong one."""

    detail = ingest_start_sit_outcome(
        week=1,
        recommendation={"starters": ["00-0023459"]},  # a canonical id, WRONG for this decision type
        roster_state_player_ids=["00-0023459"],
        actual_matchup_entry={"starters": ["9997"], "players_points": {"9997": 12.0}},
    )
    # No crash, no silently-fabricated match -- honestly disjoint.
    assert detail.recommended_only_ids == ("00-0023459",)
    assert detail.actual_only_ids == ("9997",)


# =============================================================================
# GROUP 6 -- Status freshness monotonicity property (extends Worker 4's
# example-based `live_player_intelligence_composition_v1_service.py`
# tests into an EXHAUSTIVE-permutation property test).
#
# Property: for ANY arrival order of a fixed set of observations for one
# field, folding them through `compose_field` produces the SAME final
# result -- the composed value always reflects the most authoritative
# (lowest precedence_tier), and among equally-authoritative observations,
# the most recent, regardless of the order they arrived in.
# =============================================================================


def _fold(observations: list[FieldObservation]) -> ComposedField | None:
    existing: ComposedField | None = None
    for observation in observations:
        existing = compose_field(existing, observation)
    return existing


def _assert_order_independent(observations: list[FieldObservation]) -> ComposedField:
    """EXHAUSTIVE over every permutation of a small observation set -- not
    a random sample. For n<=5 (every case below), this checks ALL n!
    possible arrival orders, a strictly stronger guarantee than a
    property-testing library's random sampling would give for the same
    set."""

    results = [_fold(list(permutation)) for permutation in itertools.permutations(observations)]
    first = results[0]
    for other in results[1:]:
        assert other == first, (
            f"compose_field's fold is order-DEPENDENT for this observation set -- "
            f"got {other} vs {first} across two different arrival orders."
        )
    assert first is not None
    return first


def test_higher_precedence_always_wins_regardless_of_arrival_order() -> None:
    observations = [
        FieldObservation(field="injury_designation", value="OUT", precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE, source="NFLVERSE_INJURIES", source_as_of="2026-09-10T00:00:00+00:00"),
        FieldObservation(field="injury_designation", value="QUESTIONABLE", precedence_tier=PRECEDENCE_MANUAL_VERIFIED_OVERRIDE, source="MANUAL_OVERRIDE", source_as_of="2026-09-09T00:00:00+00:00"),
        FieldObservation(field="injury_designation", value="DOUBTFUL", precedence_tier=PRECEDENCE_ADMITTED_AUTOMATED_FACTUAL_SOURCE, source="ADMITTED_SOURCE", source_as_of="2026-09-11T00:00:00+00:00"),
    ]
    result = _assert_order_independent(observations)
    # Manual override wins even though it is the OLDEST and arrived in any
    # position -- authority beats recency across tiers, always.
    assert result.value == "QUESTIONABLE"
    assert result.source == "MANUAL_OVERRIDE"


def test_same_tier_freshest_timestamp_always_wins_regardless_of_arrival_order() -> None:
    observations = [
        FieldObservation(field="depth_chart_position", value="RB2", precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE, source="NFLVERSE_DEPTH_CHARTS", fetched_at="2026-09-10T08:00:00+00:00"),
        FieldObservation(field="depth_chart_position", value="RB1", precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE, source="NFLVERSE_DEPTH_CHARTS", fetched_at="2026-09-12T08:00:00+00:00"),
        FieldObservation(field="depth_chart_position", value="RB3", precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE, source="NFLVERSE_DEPTH_CHARTS", fetched_at="2026-09-11T08:00:00+00:00"),
    ]
    result = _assert_order_independent(observations)
    assert result.value == "RB1"  # 09-12 is the freshest, regardless of fold order


def test_a_genuinely_older_same_tier_observation_never_regresses_the_composed_value() -> None:
    """The exact monotonicity guarantee named by the directive: an
    out-of-order-arriving OLDER same-tier observation is REJECTED, even
    when it arrives last (the adversarial ordering most likely to expose a
    naive "last write wins" bug)."""

    newer = FieldObservation(field="current_team", value="KC", precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE, source="SLEEPER_PUBLIC_PLAYERS_CATALOG", fetched_at="2026-09-12T00:00:00+00:00")
    older = FieldObservation(field="current_team", value="NE", precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE, source="SLEEPER_PUBLIC_PLAYERS_CATALOG", fetched_at="2026-09-01T00:00:00+00:00")

    newer_then_older = _fold([newer, older])
    older_then_newer = _fold([older, newer])
    assert newer_then_older is not None and older_then_newer is not None
    assert newer_then_older.value == "KC"
    assert older_then_newer.value == "KC"  # same result either way -- the older one never regresses it


def test_an_unknown_field_stays_unknown_across_every_arrival_order_of_all_none_observations() -> None:
    observations = [
        FieldObservation(field="game_status", value=None, precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE, source="A"),
        FieldObservation(field="game_status", value=None, precedence_tier=PRECEDENCE_ADMITTED_AUTOMATED_FACTUAL_SOURCE, source="B"),
    ]
    for permutation in itertools.permutations(observations):
        result = _fold(list(permutation))
        assert result is not None
        assert result.value is None
        assert result.source == "NONE"


# =============================================================================
# GROUP 7 -- Malformed/degraded provider payload handling (extends the
# P0-1 null-safety fixes -- see `NWR_POST_UI_WORKDAY_LEDGER.md`'s "Bug 1"/
# "Bug 2" for the original frontend-side examples this generalizes to the
# BACKEND'S own real Sleeper-payload consumers) into a broader sweep.
#
# Property: for a range of realistically-malformed real Sleeper API
# response shapes (missing keys, wrong types, None where a dict/list was
# expected, non-dict entries inside a list, booleans where numbers were
# expected), no real ingestion consumer crashes with an unhandled
# exception -- it degrades to an honest `None`/empty result instead.
# =============================================================================

_MALFORMED_MATCHUP_ENTRIES = [
    None,
    {},
    {"starters": None},
    {"starters": "not-a-list"},
    {"starters": [1, 2, None]},
    {"starters": ["1", "2"], "players_points": None},
    {"starters": ["1", "2"], "players_points": "not-a-dict"},
    {"starters": ["1", "2"], "players_points": {"1": True}},  # bool, not a real number
    {"starters": ["1", "2"], "players_points": {"1": "12.5"}},  # string, not a real number
    {"points": "not-a-number"},
    {"points": float("nan")},
    123,  # not even a mapping
    "also-not-a-mapping",
]


@pytest.mark.parametrize("malformed_entry", _MALFORMED_MATCHUP_ENTRIES)
def test_start_sit_ingestion_never_crashes_on_a_malformed_sleeper_matchup_entry(malformed_entry) -> None:
    detail = ingest_start_sit_outcome(
        week=1, recommendation={"starters": ["1", "2"]}, roster_state_player_ids=["1", "2", "3"],
        actual_matchup_entry=malformed_entry,
    )
    assert isinstance(detail, StartSitOutcomeDetail)


_MALFORMED_RECOMMENDATIONS = [
    {},
    {"starters": None},
    {"starters": "not-a-list"},
    {"starters": [None, 1, True]},
    {"projectedTotal": "not-a-number"},
    {"projectedTotal": True},
]


@pytest.mark.parametrize("malformed_recommendation", _MALFORMED_RECOMMENDATIONS)
def test_start_sit_ingestion_never_crashes_on_a_malformed_recommendation_payload(malformed_recommendation) -> None:
    detail = ingest_start_sit_outcome(
        week=1, recommendation=malformed_recommendation, roster_state_player_ids=["1"],
        actual_matchup_entry={"starters": ["1"], "players_points": {"1": 10.0}},
    )
    assert isinstance(detail, StartSitOutcomeDetail)


_MALFORMED_TRANSACTION_LISTS = [
    [],
    [None],
    ["not-a-dict"],
    [{}],
    [{"adds": None}],
    [{"adds": "not-a-dict"}],
    [{"adds": {"1": None}}],
    [{"adds": {"1": "2"}, "status": None}],
    [{"adds": {"1": "2"}, "status": "complete", "settings": None}],
    [{"adds": {"1": "2"}, "status": "complete", "settings": "not-a-dict"}],
    [{"adds": {"1": "2"}, "status": "complete", "settings": {"waiver_bid": "not-a-number"}}],
    [None, {"adds": {"1": "2"}, "status": "complete"}, "garbage"],  # mixed-validity list
]


@pytest.mark.parametrize("malformed_transactions", _MALFORMED_TRANSACTION_LISTS)
def test_waiver_ingestion_never_crashes_on_a_malformed_sleeper_transaction_list(malformed_transactions) -> None:
    detail = ingest_waiver_outcome(
        recommended_player_id="1", owner_roster_id="2", transactions_for_period=malformed_transactions,
    )
    assert isinstance(detail, WaiverOutcomeDetail)


@pytest.mark.parametrize("malformed_transactions", _MALFORMED_TRANSACTION_LISTS)
def test_add_drop_ingestion_never_crashes_on_a_malformed_sleeper_transaction_list(malformed_transactions) -> None:
    detail = ingest_add_drop_outcome(
        added_player_id="1", dropped_player_id="2", owner_roster_id="9",
        transactions_for_period=malformed_transactions, horizon_matchup_entries=[],
    )
    assert isinstance(detail, AddDropOutcomeDetail)


def test_waiver_ingestion_never_crashes_when_recommended_player_id_is_genuinely_none() -> None:
    """A real, honest degraded case (no player was ever recommended) --
    never a crash trying to look one up."""

    detail = ingest_waiver_outcome(
        recommended_player_id=None, owner_roster_id="2", transactions_for_period=_MALFORMED_TRANSACTION_LISTS[-1],
    )
    assert detail.recommended_player_id is None
    assert detail.claim_submitted is None


@pytest.mark.parametrize(
    "malformed_horizon_entries",
    [
        [],
        [None],
        ["not-a-dict"],
        [{}],
        [{"starters": None}],
        [{"starters": "nope"}, {"players_points": None}],
        [None, {"starters": ["1"], "players_points": {"1": True}}],
    ],
)
def test_add_drop_ingestion_never_crashes_on_malformed_horizon_matchup_entries(malformed_horizon_entries) -> None:
    detail = ingest_add_drop_outcome(
        added_player_id="1", dropped_player_id="2", owner_roster_id="9",
        transactions_for_period=[], horizon_matchup_entries=malformed_horizon_entries,
    )
    assert isinstance(detail, AddDropOutcomeDetail)
