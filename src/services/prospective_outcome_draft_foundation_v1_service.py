"""Prospective Outcomes V1 -- Work Unit 11: DRAFT outcome FOUNDATION
(schema + future ingestion hooks only -- NOT a full implementation).

Per the governing directive: DRAFT is long-horizon. The real 2026 season
just started (Week 1), so this pass does NOT force a season-long
conclusion. It builds the outcome SCHEMA that a future, boundary-cleared
pass will fill in for real, plus the pure "hook" functions a future
ingestion job calls once (a) a live DRAFT trace call site actually exists
(it does not yet -- see `_ASSERTED_NO_LIVE_DRAFT_CALL_SITE_EXISTS` below)
and (b) enough of a season has genuinely elapsed to compute real
season-long numbers honestly.

=== EXTENDS, DOES NOT REPLACE, THE PRIOR CYCLE'S `DraftOutcomeDetail` ===

`prospective_outcome_schema_v1_service.DraftOutcomeDetail` is the
deliberately-thin envelope the prior cycle shipped
(`evaluation_method`/`season_long_roster_utility`/`injury_luck_adjustment`/
`notes`) -- it stays exactly as-is, still the `DRAFT_V1` `KIND` the base
evaluation layer (`prospective_outcome_evaluation_v1_service._extract_draft`)
already maps to a frozen `NOT_APPLICABLE` for this entire cycle (contract
Section 2, a hard boundary this pass does not touch). This module adds a
NEW, richer, SEPARATE dataclass (`DraftPickOutcomeDetail`, `KIND =
"DRAFT_PICK_V1"`) alongside it -- a real per-pick outcome shape with the
dimensions the governing directive names explicitly: actual chosen player,
recommended player (from the FROZEN recommendation-time candidate set),
season points, starts, weeks usable, roster utility, replacement value --
plus a SEPARATE, DISTINCT injury dimension (see below). This is additive,
not a replacement: nothing about `DraftOutcomeDetail`'s own `KIND`/mapping
in the base evaluation layer changes.

=== INJURY IS NEVER CONFLATED WITH DECISION QUALITY ===

`injury_designation`/`weeks_missed_to_injury` are their OWN fields,
structurally separate from `evaluation_method`/`recommended_player_id`/
`recommendation_time_candidate_set_ids` (the fields that determine whether
a pick's DECISION QUALITY can honestly be judged at all). No code path in
this module reads an injury field when deciding `evaluation_method`, and no
docstring/comment/label anywhere in this module (or produced by it) ever
asserts that a player getting injured is proof the underlying pick was a
bad decision -- see `test_prospective_outcome_draft_foundation_v1_service.py`
for a structural (not just promised) proof of both claims.

=== NO RETROACTIVE RECONSTRUCTION ===

`build_draft_pick_outcome_detail` NEVER backfills a "recommended player" for
a real historical pick whose recommendation-time candidate set was never
actually captured. If the caller cannot supply a real, non-empty
`recommendation_time_candidate_set_ids` AND a `recommended_player_id` that
is genuinely a MEMBER of that same set, the result is unconditionally
`DRAFT_EVALUATION_METHOD_INSUFFICIENT_CONTEXT` -- `recommended_player_id`
is forced to `None` in that case even if the caller passed a non-`None`
value, so a guess can never leak into a field that is supposed to mean "this
was genuinely known at recommendation time."

=== HARD BOUNDARY, RESPECTED STRUCTURALLY ===

This module never imports `shadow_numeric_authorities_service`
(`marginal_roster_utility_v2`) or any draft RECOMMENDATION-generation
module. `season_points`/`starts`/`weeks_usable`/`roster_utility`/
`replacement_value` are always `None` this cycle -- real season-long
computation belongs to a future, boundary-cleared pass, and the 2026 season
having only just started means there is nothing honest to compute yet
either way. `roster_utility` is deliberately NOT the same field as
`marginal_roster_utility_v2`'s own output -- it is a placeholder this
module never populates, not a duplicate/parallel implementation of that
closed model.

=== THE STILL-UNWIRED DRAFT CALL SITE ===

Confirmed by a real grep of `src/application/desktop_facade.py` this pass
(`grep -n 'tool="DRAFT"'` -- zero matches, mirroring `TOOL_TYPES`'s own
membership test in `in_season_decision_trace_service.py`, which DOES
already include `"DRAFT"`): no live code path in this repository has ever
called `record_decision_trace(..., tool="DRAFT", ...)`. The schema exists
now so a future draft-recommendation wiring pass (explicitly out of THIS
pass's hard boundary) has a real, tested shape to record into from day one
-- this module does not add that call site itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

DRAFT_EVALUATION_METHOD_DEFERRED = "DEFERRED_TO_SEASON_LONG_ROSTER_UTILITY_ENGINE"
# NEW this pass -- distinct from the prior cycle's single deferred value.
# Never a synonym for "deferred because the season hasn't finished yet";
# it specifically means "the recommendation-time context needed to judge
# this pick's decision quality was never genuinely captured," mirroring the
# base contract's own INSUFFICIENT_DECISION_CONTEXT distinction (Section 4)
# extended here to the DRAFT class's own foundation layer.
DRAFT_EVALUATION_METHOD_INSUFFICIENT_CONTEXT = "INSUFFICIENT_DECISION_CONTEXT"

DRAFT_PICK_EVALUATION_METHODS = frozenset(
    {DRAFT_EVALUATION_METHOD_DEFERRED, DRAFT_EVALUATION_METHOD_INSUFFICIENT_CONTEXT}
)


class ProspectiveDraftOutcomeError(ValueError):
    pass


@dataclass(frozen=True)
class DraftPickOutcomeDetail:
    """One real draft pick's outcome-evaluation FOUNDATION -- a schema and
    frozen recommendation-time facts only, never a computed season-long
    verdict this cycle (see module docstring). `KIND` is deliberately
    DIFFERENT from `DraftOutcomeDetail.KIND` ("DRAFT_V1") -- this is an
    ADDITIVE new shape, not a silent replacement."""

    KIND = "DRAFT_PICK_V1"

    pick_number: int | None
    round_number: int | None
    # The real, factual player the roster actually drafted -- always
    # knowable once a real DRAFT trace/outcome exists, independent of
    # whether recommendation-time context was ever captured.
    actual_chosen_player_id: str

    # Recommendation-time facts -- BOTH fields are `None`/empty unless a
    # real, frozen recommendation-time candidate set was genuinely captured
    # (never reconstructed after the fact -- see `build_draft_pick_
    # outcome_detail`).
    recommended_player_id: str | None
    recommendation_time_candidate_set_ids: tuple[str, ...]

    evaluation_method: str

    # Season-long dimensions the governing directive names explicitly.
    # Always `None` this cycle -- see module docstring (hard boundary +
    # "do not force a 2026 season-long conclusion this session").
    season_points: float | None
    starts: int | None
    weeks_usable: int | None
    roster_utility: float | None
    replacement_value: float | None

    # A SEPARATE, DISTINCT dimension -- see module docstring's own section
    # on this. Never read by, or fed into, `evaluation_method`.
    injury_designation: str | None
    weeks_missed_to_injury: int | None

    notes: str

    def __post_init__(self) -> None:
        if self.evaluation_method not in DRAFT_PICK_EVALUATION_METHODS:
            raise ProspectiveDraftOutcomeError(
                f"Unknown DRAFT_PICK_V1 evaluation_method: {self.evaluation_method!r}. Must be one of "
                f"{sorted(DRAFT_PICK_EVALUATION_METHODS)}."
            )
        if not self.actual_chosen_player_id:
            raise ProspectiveDraftOutcomeError(
                "actual_chosen_player_id is required -- the real, factual pick is always the one fact "
                "a DRAFT_PICK_V1 outcome can never honestly omit."
            )
        candidate_set = set(self.recommendation_time_candidate_set_ids)
        context_genuinely_captured = bool(candidate_set) and self.recommended_player_id is not None
        if context_genuinely_captured and self.recommended_player_id not in candidate_set:
            raise ProspectiveDraftOutcomeError(
                "recommended_player_id must be a genuine member of recommendation_time_candidate_set_ids "
                "-- a 'recommended' player who was never actually a recorded candidate is not a real "
                "recommendation-time fact."
            )
        if not context_genuinely_captured and self.evaluation_method != DRAFT_EVALUATION_METHOD_INSUFFICIENT_CONTEXT:
            raise ProspectiveDraftOutcomeError(
                "A pick with no genuinely-captured recommendation-time candidate set (and/or no "
                "recommended_player_id) must use DRAFT_EVALUATION_METHOD_INSUFFICIENT_CONTEXT -- never "
                "a backfilled/guessed recommendation."
            )

    def to_detail_dict(self) -> dict[str, Any]:
        return {
            "kind": self.KIND,
            "pickNumber": self.pick_number,
            "roundNumber": self.round_number,
            "actualChosenPlayerId": self.actual_chosen_player_id,
            "recommendedPlayerId": self.recommended_player_id,
            "recommendationTimeCandidateSetIds": list(self.recommendation_time_candidate_set_ids),
            "evaluationMethod": self.evaluation_method,
            "seasonPoints": self.season_points,
            "starts": self.starts,
            "weeksUsable": self.weeks_usable,
            "rosterUtility": self.roster_utility,
            "replacementValue": self.replacement_value,
            # A SEPARATE dimension -- never a proxy for, or a component of,
            # decision quality. See module docstring.
            "injuryDesignation": self.injury_designation,
            "weeksMissedToInjury": self.weeks_missed_to_injury,
            "notes": self.notes,
        }


def build_draft_pick_outcome_detail(
    *,
    actual_chosen_player_id: str,
    pick_number: int | None = None,
    round_number: int | None = None,
    recommended_player_id: str | None = None,
    recommendation_time_candidate_set_ids: Sequence[str] = (),
    injury_designation: str | None = None,
    weeks_missed_to_injury: int | None = None,
    notes: str = "",
) -> DraftPickOutcomeDetail:
    """The real FUTURE INGESTION HOOK this pass ships: the one function a
    later pass calls once a live DRAFT trace exists. Never computes
    `season_points`/`starts`/`weeks_usable`/`roster_utility`/
    `replacement_value` itself (always `None` -- see module docstring);
    never backfills `recommended_player_id`/`recommendation_time_
    candidate_set_ids` from anything other than what the caller genuinely
    captured at recommendation time.
    """

    if not actual_chosen_player_id:
        raise ProspectiveDraftOutcomeError("actual_chosen_player_id is required.")

    candidate_set = tuple(str(pid) for pid in recommendation_time_candidate_set_ids)
    resolved_recommended_id: str | None = None
    evaluation_method = DRAFT_EVALUATION_METHOD_INSUFFICIENT_CONTEXT
    if candidate_set and recommended_player_id is not None:
        candidate = str(recommended_player_id)
        if candidate in candidate_set:
            # A genuinely captured recommendation-time fact.
            resolved_recommended_id = candidate
            evaluation_method = DRAFT_EVALUATION_METHOD_DEFERRED
        # else: a "recommended" id that was never actually a member of the
        # real frozen candidate set is not a genuine recommendation-time
        # fact -- falls through to INSUFFICIENT_DECISION_CONTEXT below,
        # `resolved_recommended_id` stays None (never guessed).

    return DraftPickOutcomeDetail(
        pick_number=pick_number,
        round_number=round_number,
        actual_chosen_player_id=str(actual_chosen_player_id),
        recommended_player_id=resolved_recommended_id,
        recommendation_time_candidate_set_ids=candidate_set,
        evaluation_method=evaluation_method,
        season_points=None,
        starts=None,
        weeks_usable=None,
        roster_utility=None,
        replacement_value=None,
        injury_designation=injury_designation,
        weeks_missed_to_injury=weeks_missed_to_injury,
        notes=notes,
    )


def draft_outcome_ready_for_season_long_evaluation(*, season: int, current_season: int) -> bool:
    """A real, honest STUB hook -- always `False` this cycle. A real
    "has enough of the season elapsed to compute season-long numbers
    honestly" criterion is explicitly NOT defined this pass (mirrors the
    contract's own explicit deferral of a real ROS window rather than
    inventing one this early in a season -- contract Section 3's own
    reasoning, applied here to DRAFT). A future worker defines the real
    check once there is a real, non-speculative basis for one."""

    return False
