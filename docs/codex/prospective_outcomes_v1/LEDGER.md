# NWR Prospective Outcomes V1 -- Ledger

Branch `upgrade/nwr-prospective-outcomes-v1-20260914`, worktree
`C:\NWR\prospective-outcomes-v1`.

## Worker 1 (this pass) -- Work Units 0-2: preregistered contract, canonical
## outcome-event contract, outcome source adapters

Start HEAD `cd1f78da`. Not merged, not pushed, not deployed.

**Existing foundation reused, not duplicated.** Read in full before writing
any code this pass: `docs/codex/prospective_outcome_v1/PROSPECTIVE_OUTCOME_V1.md`
(note: singular "prospective_outcome_v1", the prior cycle's own directory
name -- distinct from this cycle's plural
`docs/codex/prospective_outcomes_v1`) and the relevant closing entries in
`docs/codex/live_player_intelligence_v1/LEDGER.md` (Worker 5/6's
Prospective Outcome V1 sections, and Worker 7's cycle-closing summary).
Confirmed real and already-tested: `src/services/prospective_outcome_schema_v1_service.py`
(8 decision-type dataclasses), `src/services/prospective_outcome_ingestion_v1_service.py`
(pure ingestion functions, 1 real START_SIT outcome already ingested into
an isolated throwaway root), `src/services/in_season_decision_trace_service.py`
(`record_outcome` already had an optional `detail` param before this
pass), and History UI V2
(`desktop/apps/redraft/src/decision-history.tsx` /
`decision-history-format.ts`). None of this was rebuilt -- this pass
extends it additively.

### Work Unit 0 -- baseline + preregistration

Verified live (not trusted from the prior ledger alone): branch, HEAD
(`cd1f78dacb927c647c2470ab9cbee9f981877e38`), clean worktree, the targeted
269-test slice (`pytest -k "decision_trace or prospective_outcome or
live_player_intelligence or boundary_property_reliability or composition
or player_availability"`), and `tests/test_desktop_application_api.py`'s
same 4 pre-existing failures the prior cycle documented at this exact
worktree.

**`docs/codex/prospective_outcomes_v1/PROSPECTIVE_OUTCOME_EVALUATION_CONTRACT.md`**
committed FIRST, before any evaluation-logic code (its own commit,
`5e3f898`), per the directive's own instruction. Freezes: the 8 decision
classes (reused verbatim), per-class outcome definitions, exact
evaluation windows (**START_SIT/K_STREAMER/DST_STREAMER = 0-week
same-week; WAIVER/ADD_DROP/FAAB/TRADE-family = 4-week bounded horizon,
reusing the existing `DEFAULT_HORIZON_WEEKS` constant verbatim, not
re-derived; DRAFT = deferred, no window; no ROS window invented this
pass**), a closed 5-member `evaluationStatus` set with an explicit
"insufficient context vs. not applicable" distinction, hindsight rules
extended to the new evaluation layer, per-class-only aggregation rules, a
minimum-sample rule (**20**, matching the frontend's own
`MIN_SAMPLE_SIZE_FOR_PER_CLASS_ROLLUP`), and what is explicitly not
comparable across classes. Read that document in full before touching any
evaluation code -- these numbers are frozen and must not be silently
changed.

### Work Unit 1 -- canonical outcome event contract

**New**: `src/services/prospective_outcome_evaluation_v1_service.py`.
Builds `OutcomeEvaluation` (frozen dataclass, every field from the
directive's own list: `traceId`, `decisionType`, `leagueKey`/`leagueId`,
`leagueSnapshotId`, `recommendationGeneratedAt`, `outcomeObservedAt`,
`outcomeWindow` (label + horizonWeeks), `outcomeSource`,
`outcomeSourceAsOf`, `ownerAction`, `factualOutcome`, `evaluationStatus`,
`evaluationMetrics`, `issues`, `schemaVersion`) as a layer ON TOP OF the
existing 8 schema dataclasses -- **never a replacement, never a new
ledger line**. Decided and documented precisely (module docstring):
evaluation is a DERIVED VIEW, always recomputed on demand from the
immutable trace chain via `compute_outcome_evaluation(record)`, never
itself appended/stored. Proven pure/deterministic
(`test_compute_outcome_evaluation_is_pure_and_deterministic`) and
structurally incapable of accepting a "current state" parameter
(`_assert_no_current_state_parameter`, asserted at import time AND unit
tested to actually catch a violation, not just asserted once and trusted).

**Modified (additive only)**: `src/services/in_season_decision_trace_service.py`
-- `record_outcome` gains three new, independently-omittable keyword
parameters (`outcome_source`, `outcome_source_as_of`,
`outcome_observed_at`), stored under `outcome["source"]`/`["sourceAsOf"]`/
`["observedAt"]` ONLY when actually supplied -- exactly the same additive
pattern `detail` already established. Every pre-existing call site (every
one that predates this pass) round-trips byte-for-byte identical
(`test_record_outcome_without_provenance_fields_is_still_byte_identical`).
The original recommendation line is still never touched
(`test_record_outcome_provenance_never_touches_the_original_recommendation_line`).

**Real metric extraction, scoped honestly**: this pass extracts, per
class, ONLY the metric(s) the existing schema/ingestion layer already
computed -- it does NOT invent new per-class regret formulas (that is
explicitly the next worker's job, see below). The one exception,
disclosed in the contract (Section 2/5): K_STREAMER/DST_STREAMER get one
new, simple, transparent point-delta
(`recommendedPlayerActualPoints - actualStarterActualPoints`) that
mirrors START_SIT's own already-proven opportunity-cost formula --
**never** substituted with `bestAvailableAlternativeActualPoints` (the
hindsight-best pick), which is reported alongside but never promoted into
the primary metric. FAAB's two axes
(`playerDecisionQuality`/`bidRangeCalibration`) stay genuinely separate at
this layer too, proven by a test where the two axes actually disagree (a
good pickup, a bad bid range) and both facts survive intact. TRADE/
TRADE_FINDER never score an unaccepted/rejected package
(`NOT_APPLICABLE`, never a scored counterfactual). DRAFT is always
`NOT_APPLICABLE` (hard boundary).

### Work Unit 2 -- outcome source adapters

**New**: `src/services/prospective_outcome_source_adapter_v1_service.py`.
Two structurally separate frozen dataclasses:
- `RecommendationTimeContext` -- built ONLY from a trace's own frozen
  fields (`recommendation_time_context_from_trace`, PURE, zero network
  I/O, signature-checked at import time to accept no
  `SleeperHttpClient`/"current state" parameter, same defense pattern as
  Work Unit 1).
- `RealizedOutcomeFetch` -- built by real `fetch_*` functions that
  REQUIRE an explicit `client: SleeperHttpClient` parameter, reusing the
  exact same real, public, keyless, already-wired Sleeper endpoints every
  other real call site in this codebase uses (`league/{id}/matchups/{week}`,
  `league/{id}/transactions/{round}`) -- **no new projection source
  built**. `fetch_transactions_for_rounds` is a real, new fix for the
  prior cycle's own disclosed open issue (a caller must fetch every
  relevant round or a real claim could be missed and misreported as
  "never submitted") -- this function does that for real, combining
  every round the caller asks for into one real list.

One concrete, worked composition function this pass ships:
`adapt_and_ingest_start_sit_outcome` (START_SIT is the one decision type
with real, live-verified Week 1 2026 data) -- verified against the SAME
real, committed fixture
(`docs/codex/prospective_outcome_v1/real_data_v1/fantasy_gamers_week1_2026_owner_matchup.json`)
the prior cycle used, reusing it (not duplicating a second copy).

**The hindsight-leakage defense is structural, not just documented**,
proven three separate ways: (1) `recommendation_time_context_from_trace`'s
own signature cannot accept a client/`"current"`-named parameter
(import-time assertion + a test that actually triggers the guard on a
deliberately-bad function); (2) `RecommendationTimeContext` and
`RealizedOutcomeFetch` are two disjoint dataclasses that are never merged
into one mutable structure -- `test_context_is_structurally_immune_to_a_
later_contradictory_fetch` builds a context, then fabricates a
contradictory later fetch, and asserts the context's own fields are
unchanged; (3) `adapt_and_ingest_start_sit_outcome` reads each object's
fields independently, once, at the ingestion call boundary only.

### Tests

- `tests/test_prospective_outcome_evaluation_v1_service.py`: **28 passed,
  new.**
- `tests/test_prospective_outcome_source_adapter_v1_service.py`: **13
  passed, new.**
- `tests/test_in_season_decision_trace_service.py`: **27 passed** (3 new
  provenance-field tests added to the existing file, all passing; no
  pre-existing test in this file was changed).
- Wider targeted regression (`pytest -k "decision_trace or
  prospective_outcome or live_player_intelligence or
  boundary_property_reliability or composition or player_availability"`):
  **313 passed, 0 failed** (269 pre-existing + 44 new this pass -- 28 +
  13 + 3, matching exactly).
- `tests/test_desktop_application_api.py`: **46 passed / 4 failed** --
  the SAME 4 pre-existing failures documented in Work Unit 0's baseline
  and the prior cycle's own ledger. Re-confirmed live after this pass's
  changes, not merely assumed unaffected.
- `git diff` grepped for every hard-boundary term
  (`marginal_roster_utility_v2`, `LeagueSnapshot`, `LeagueWorkspaceContext`,
  `lifecycle_resolver`, `DecisionResultEnvelope`,
  `PlayerAvailabilityStatus`): **zero matches** in this pass's actual
  diff.

### Backend/model files changed this pass

- **Modified (additive only)**: `src/services/in_season_decision_trace_service.py`
  (`record_outcome` gains 3 new optional keyword parameters, proven
  byte-identical when omitted), `tests/test_in_season_decision_trace_service.py`
  (3 new tests appended).
- **New**: `src/services/prospective_outcome_evaluation_v1_service.py`,
  `src/services/prospective_outcome_source_adapter_v1_service.py`,
  `tests/test_prospective_outcome_evaluation_v1_service.py`,
  `tests/test_prospective_outcome_source_adapter_v1_service.py`,
  `docs/codex/prospective_outcomes_v1/PROSPECTIVE_OUTCOME_EVALUATION_CONTRACT.md`,
  this ledger.
- **Nothing in `desktop_facade.py`, `desktop_api/`, or any consumer/UI
  layer was wired this pass.** `redraft_record_decision_trace_outcome`
  (the facade endpoint) does not yet pass through the 3 new provenance
  keyword parameters, and nothing in production calls
  `compute_outcome_evaluation` or the source-adapter module yet -- see
  Open Issues below.

## OPEN ISSUES FOR THE NEXT WORKER (Work Units 3-6: Start/Sit, Waiver,
## Add/Drop, FAAB evaluators)

1. **Per-class AGGREGATION/SUMMARY does not exist yet.** This pass builds
   only the SINGLE-EVENT `OutcomeEvaluation` contract and metric
   extraction. A real per-class summary (mean/median opportunity cost, a
   calibration hit-rate for FAAB's bid-range axis, a claim-win-rate for
   WAIVER, etc.) -- gated by the contract's own Section 7 minimum-sample
   rule (20, `MIN_SAMPLE_SIZE_FOR_PER_CLASS_SUMMARY` in the new evaluation
   module) -- is real work still to be done, one class at a time, per the
   directive's own Work Unit numbering (3=Start/Sit, 4=Waiver, 5=Add/Drop,
   6=FAAB).
2. **No orchestration wiring exists yet** -- `desktop_facade.py` does not
   call `compute_outcome_evaluation`, `recommendation_time_context_from_trace`,
   or any `fetch_*`/`adapt_and_ingest_*` function. A real, scheduled (or
   on-demand) job that (a) loads every `RECOMMENDED`/`OWNER_ACTION_RECORDED`
   trace whose week/period has completed, (b) builds a
   `RecommendationTimeContext`, (c) fetches the matching
   `RealizedOutcomeFetch` via this pass's real adapters, (d) calls the
   matching `ingest_*_outcome` function, and (e) calls
   `record_outcome(..., detail=..., outcome_source="SLEEPER",
   outcome_source_as_of=..., outcome_observed_at=...)` is the natural next
   step -- inherited unchanged from the prior cycle's own Open Issue 1,
   now with real, reusable adapter functions available to build it from
   (rather than the prior cycle's ad hoc demo-script pattern).
3. **Identity resolution for canonical-id decision types**
   (WAIVER/ADD_DROP/FAAB/TRADE/TRADE_FINDER/TRADE_PACKAGE_SEARCH/
   K_STREAMER/DST_STREAMER) is still a real, undone dependency, unchanged
   from the prior cycle's own Open Issue 2 -- this pass's source adapters
   only built the one concrete, worked composition function for
   START_SIT (the identity-resolution-free case); WAIVER/ADD_DROP/FAAB/
   TRADE composition functions are real, straightforward extensions of
   the same pattern (`fetch_transactions_for_rounds` +
   `fetch_horizon_matchup_entries` already exist and are tested) but were
   not written this pass, to keep this pass's own scope to what Work
   Units 0-2 actually asked for.
4. **`redraft_record_decision_trace_outcome`'s facade endpoint does not
   yet accept the 3 new provenance parameters.** A real orchestrator
   calling `record_outcome` directly (in-process, e.g. from a background
   job) does not need the HTTP facade at all; but if a future pass wants
   an HTTP-triggered outcome-recording path to carry real provenance too,
   the facade method needs the same 3 additive parameters threaded
   through.
5. **A real ROS (rest-of-season) evaluation window** is explicitly NOT
   defined this pass (contract Section 3) -- only the two numbers that
   already existed in tested code (0-week same-week, 4-week bounded) are
   preregistered. Worth defining for real once enough of the 2026 season
   has actually elapsed to derive a number honestly, rather than
   speculating now.
6. **The duplicated `MIN_SAMPLE_SIZE_FOR_PER_CLASS_*` constant** (20, in
   both `decision-history-format.ts` and this pass's new
   `prospective_outcome_evaluation_v1_service.py`) has no single source of
   truth across the Python/TypeScript boundary -- disclosed, not fixed
   (would need either an API-exposed constant or a build-time sharing
   mechanism, neither of which exists).
7. **`AddDropOutcomeDetail.dropped_player_subsequent_points`** is still
   honestly left `None`-producing (inherited, unchanged, from the prior
   cycle's own Open Issue 3) -- needs a leaguewide roster-membership-over-
   time feed this codebase doesn't have yet.
8. **History UI V3** (the directive's own broader framing for this
   cycle) -- rendering `OutcomeEvaluation`'s `evaluationStatus`/
   `evaluationMetrics`/`issues` in the History page, upgrading History UI
   V2's existing per-decision-type detail sections rather than replacing
   them -- was not attempted this pass (Work Units 0-2 only, per this
   pass's own explicit assignment). A future worker doing this should
   reuse `hasOutcomeDetail`/`buildOutcomeDetailSections` (existing,
   unchanged) as the pattern to extend, and must preserve the existing
   "no aggregate accuracy score" rule.
9. **New benchmark work named by the directive (trade packages, K/DST)**
   that "didn't exist before" was not started this pass -- Work Units
   0-2 as literally assigned did not include it; flagged here so it isn't
   silently dropped from the cycle's own stated ambitions.

## Worker 2 (this pass) -- Work Units 3-6: Start/Sit, Waiver, Add/Drop,
## FAAB evaluators

Start HEAD `e4de619b` (Worker 1's closing commit). Not merged, not pushed,
not deployed. Verified live before writing any code: branch, clean
worktree, the 313-test targeted slice, `test_desktop_application_api.py`'s
same 4 pre-existing failures (`test_dynasty_facade_composes_real_governed_
workflows`, `test_desktop_rookie_veteran_bridge_is_source_separated_and_
trade_aware`, `test_redraft_bootstrap_seeds_once_and_matches_desktop_
contract`, `test_facade_has_no_streamlit_or_app_component_dependency`).

Read in full before writing any code: `PROSPECTIVE_OUTCOME_EVALUATION_
CONTRACT.md`, Worker 1's ledger entry above, and both of Worker 1's new
modules (`prospective_outcome_evaluation_v1_service.py`,
`prospective_outcome_source_adapter_v1_service.py`) plus the schema/
ingestion modules they build on. Nothing below re-derives a preregistered
window/threshold, bypasses `compute_outcome_evaluation`, or invents a new
identity-resolution/network path -- every evaluator's `evaluate_*` function
CALLS `compute_outcome_evaluation` first and only ADDS metrics on top.

### New shared module

`src/services/prospective_outcome_evaluator_shared_v1_service.py` -- three
tiny functions (`summary_status`, `mean_of`, `rate_of`) reused by all four
evaluators' summary functions, importing (not redefining)
`MIN_SAMPLE_SIZE_FOR_PER_CLASS_SUMMARY` (20) from Worker 1's evaluation
module.

### A real, disclosed refinement found and applied consistently

Worker 1's own `_extract_waiver`/`_extract_add_drop` intentionally blank
ALL of a class's metrics (including real, already-known booleans like
`claimSubmitted`/`claimWon`/`addedPlayerId`) whenever the SINGLE combined
`evaluationStatus` is `PENDING_WINDOW` -- a necessary side effect of
`OutcomeEvaluation.__post_init__`'s own invariant (contract Section 4)
applied to one status field per record. This worker's WAIVER/ADD_DROP
evaluators read those specific fields directly from the already-stored
`outcome.detail` payload instead (never from `evaluation.evaluation_
metrics`), so a real, already-observed fact (a claim was submitted and won;
an add/drop pair's identity; whether a drop was reversed) is never lost
just because the bounded-horizon VALUE metric hasn't been observed yet.
Directly implements the directive's own instruction: "If a claim was never
submitted, that's adoption/follow-through information, not automatic
recommendation failure -- keep these conceptually distinct." No change was
made to Worker 1's own module to do this -- the refinement lives entirely
at this new evaluator layer.

### Work Unit 3 -- START/SIT (`prospective_outcome_start_sit_evaluator_v1_service.py`)

Decomposes the already-computed `lineupOpportunityCostPoints` into its two
real components (recommended-player vs owner-selected-player realized
points) and adds `bestLegalAlternative*` -- real "regret versus legal
recommendation-time alternatives," computed ONLY from
`eligibleAlternativeIdsAtLock` (the trace's own frozen field) and a
caller-supplied `RealizedOutcomeFetch` (the SAME matchup fetch Worker 1's
own adapter already fetches -- no new network call). Never substituted
into the primary metric (extends contract Section 5 rule 4's STREAMER
discipline to START_SIT). A real, disclosed simplification: whole-bench
maximum, not position-slot-aware (the trace's frozen fields carry no
lineup-slot-eligibility data).

**Real data**: one test runs the full pipeline against the SAME real,
committed Week 1 2026 Fantasy Gamers fixture Worker 1 used (reused, not
re-pulled), verifying a real best-legal-alternative computed from real
`players_points` against the real bench.

13 new tests, all passing.

### Work Unit 4 -- WAIVER (`prospective_outcome_waiver_evaluator_v1_service.py`)

Adds `claimableAtRecommendationTime` (was the recommended player actually
in the trace's own frozen `free_agent_state_player_ids`, via
`recommendation_time_context_from_trace` -- zero network I/O) -- honestly
`None` when a real call site never recorded a free-agent snapshot (a real,
disclosed gap: the live FAAB trace call site in `desktop_facade.py` does
NOT populate this field; only WAIVER's does). `recommendedDropPlayerId` is
read only from real, already-used `recommendation` payload keys -- `None`
when absent, since `WaiverOutcomeDetail` itself carries no structured drop
field. `summarize_waiver_evaluations` gates THREE axes independently
(claim-submission rate, claim-win rate, mean subsequent value).

15 new tests, all passing.

### Work Unit 5 -- ADD/DROP (`prospective_outcome_add_drop_evaluator_v1_service.py`)

Same PENDING_WINDOW refinement as WAIVER. `netRosterValuePoints` stays
honestly `None` with a disclosed issue this entire pass (unchanged
dependency: `droppedPlayerSubsequentPoints`, the prior cycle's own Open
Issue 3, still has no leaguewide roster-membership-over-time feed to
compute it from) -- never approximated as "added value only" pretending to
be a complete net figure. Every real result carries a fixed
`CAUSAL_ISOLATION_DISCLOSURE` string (one add/drop is one transaction among
potentially many, never scored as the sole driver of a roster's later real
results).

11 new tests, all passing.

### Work Unit 6 -- FAAB (`prospective_outcome_faab_evaluator_v1_service.py`)

Reuses `FaabPlayerDecisionQuality`/`FaabBidRangeCalibration` verbatim.
Independence is PROVEN, not merely structural: a good-pickup/bad-calibration
test, a bad-pickup/good-calibration test, and a test that widens only the
suggested bid range between two otherwise-identical evaluations and asserts
`playerDecisionQuality` is byte-identical while `bidRangeCalibration`
changes. `summarize_faab_evaluations` gates the two axes INDEPENDENTLY,
proven by a test where 20 quality samples clear the bar while only 5 of
them also carry a real calibration observation.

11 new tests, all passing.

### Real data exercised this pass

- START_SIT: the same real, committed Week 1 2026 Fantasy Gamers fixture
  Worker 1 used (reused, not re-pulled) -- see Work Unit 3 above.
- A genuine, real, READ-ONLY `GET league/1312983576827920384/
  transactions/{1,2}` call was made against the real Fantasy Gamers league
  this pass (zero writes) to check whether real waiver/FAAB transaction
  volume now exists, per this pass's own directive. **Finding, disclosed
  honestly**: it partially UPDATES the prior cycle's own expectation --
  real transactions DO now exist league-wide (5 real `free_agent`-type
  add/drop transactions across rounds 1-2, from other real rosters), but
  **none touch roster 9 (owner `scolety`) and none carry a real
  `waiver_bid` value yet** (all are the instant, un-bid `free_agent` type,
  not a `waiver`-type FAAB claim). So a real, live WAIVER/FAAB evaluation
  for the actual owner-facing trace this app would record is still not yet
  possible from real data -- WAIVER/ADD_DROP/FAAB evaluators were exercised
  against realistic fixtures this pass, honestly disclosed as fixtures, not
  claimed as real-owner-data. Worth a real re-check once the owner's own
  roster (9) has a real waiver/FAAB transaction.

### Tests (full)

- 4 new test files, 50 new tests total (13 + 15 + 11 + 11), all passing.
- Targeted regression slice (`pytest -k "decision_trace or
  prospective_outcome or live_player_intelligence or
  boundary_property_reliability or composition or player_availability"`):
  **363 passed, 0 failed** (313 pre-existing + 50 new this pass).
- `tests/test_desktop_application_api.py`: **46 passed / 4 failed** -- the
  SAME 4 pre-existing failures documented in Worker 1's own baseline.
  Re-confirmed live after this pass's changes.
- `git diff` grepped for every hard-boundary term
  (`marginal_roster_utility_v2`, `LeagueSnapshot`, `LeagueWorkspaceContext`,
  `lifecycle_resolver`, `DecisionResultEnvelope`,
  `PlayerAvailabilityStatus`): **zero matches**.

### Backend/model files changed this pass

**All new, zero modifications to any existing file** (not even Worker 1's
own modules -- every refinement lives at this new evaluator layer, reading
`outcome.detail` directly rather than editing `_extract_waiver`/
`_extract_add_drop`):

- `src/services/prospective_outcome_evaluator_shared_v1_service.py`
- `src/services/prospective_outcome_start_sit_evaluator_v1_service.py`
- `src/services/prospective_outcome_waiver_evaluator_v1_service.py`
- `src/services/prospective_outcome_add_drop_evaluator_v1_service.py`
- `src/services/prospective_outcome_faab_evaluator_v1_service.py`
- `tests/test_prospective_outcome_start_sit_evaluator_v1_service.py`
- `tests/test_prospective_outcome_waiver_evaluator_v1_service.py`
- `tests/test_prospective_outcome_add_drop_evaluator_v1_service.py`
- `tests/test_prospective_outcome_faab_evaluator_v1_service.py`
- This ledger.

## OPEN ISSUES FOR THE NEXT WORKER (Work Units 7-10: Trade, Trade
## Finder/Package, K, DST evaluators)

1. **Orchestration wiring still does not exist** -- unchanged from Worker
   1's own Open Issue 2. Nothing in `desktop_facade.py` calls any
   `evaluate_*`/`summarize_*` function from this pass, or Worker 1's
   `compute_outcome_evaluation`/adapters. A real, scheduled (or on-demand)
   job remains the natural next integration step, now with real,
   reusable, TESTED per-class evaluator functions to call into (not only
   the raw ingestion functions).
2. **Position-slot-aware START_SIT regret** is a real, disclosed
   simplification this pass leaves open: `bestLegalAlternative*` is a
   whole-bench maximum, not aware of which specific lineup SLOT the
   deviation happened in (the trace's own frozen fields carry no
   positional lineup-slot-eligibility data). A future pass wanting a
   slot-exact regret number needs that data added to the trace/recommendation
   payload upstream first -- not fabricated here.
3. **ADD_DROP's `netRosterValuePoints` remains uncomputable** -- inherited,
   unchanged, from the prior cycle's own Open Issue 3
   (`droppedPlayerSubsequentPoints`). This pass's evaluator surfaces the gap
   honestly (a disclosed issue string on every real result) rather than
   silently reporting an incomplete "net" as if it were complete.
4. **WAIVER's `claimableAtRecommendationTime` is `None` for FAAB-family
   traces by construction** -- the real, live FAAB trace call site in
   `desktop_facade.py` does not record `free_agent_state_player_ids` at
   all (only WAIVER's call site does). Closing this is a real, small,
   additive fix to that one call site (out of this pass's own scope: it
   would touch `desktop_facade.py`, not a hard-boundary file, but still
   outside Work Units 3-6 as literally assigned).
5. **Real owner (roster 9) WAIVER/ADD_DROP/FAAB outcome data still does
   not exist** as of this pass (see "Real data exercised" above) -- this
   pass's evaluators for those three classes are tested against realistic
   fixtures only, honestly disclosed as such. Worth a real re-check once
   the real Fantasy Gamers league produces its first real waiver/FAAB
   transaction for the owner's own roster.
6. **History UI V3** -- rendering these evaluators' output in the History
   page -- was not attempted this pass either (still Work Units 3-6 as
   literally assigned: backend evaluator logic, not UI). A future worker
   should reuse each evaluator's `to_dict()` method as the payload shape
   and preserve the existing "no aggregate accuracy score across classes"
   rule.
7. **A real ROS window, the duplicated `MIN_SAMPLE_SIZE_FOR_PER_CLASS_*`
   constant, and the still-missing identity resolver for canonical-id
   decision types** are all unchanged, inherited open items from Worker 1
   (see above) -- WAIVER/ADD_DROP/FAAB traces recorded by real production
   call sites already carry Sleeper-resolved ids for the one live call
   site (WAIVER) that exists; ADD_DROP/K_STREAMER/DST_STREAMER have NO
   live trace call site in `desktop_facade.py` at all yet (confirmed via a
   real grep this pass) -- a real, disclosed finding, not previously
   stated this precisely.
8. **Work Units 7-10 (Trade, Trade Finder/Package, K, DST evaluators)**
   were not started this pass, per this pass's own explicit assignment
   (Work Units 3-6 only). `ingest_trade_outcome`/`ingest_trade_finder_
   outcome`/`ingest_streamer_outcome` and their matching
   `_extract_trade`/`_extract_trade_finder`/`_extract_streamer` base-layer
   extraction already exist (Worker 1) and are the natural starting point
   for those four evaluators, following the exact same
   `evaluate_*`/`summarize_*` pattern this pass established.
