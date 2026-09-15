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

## Worker 3 (this pass) -- Work Units 7-10: Trade, Trade Finder/Package
## Search, K Streamer, DST Streamer evaluators

Start HEAD `5ea0bc51` (Worker 2's closing commit). Not merged, not pushed,
not deployed. Verified live before writing any code: branch, clean
worktree, the 363-test targeted slice, `test_desktop_application_api.py`'s
same 4 pre-existing failures (`test_dynasty_facade_composes_real_governed_
workflows`, `test_desktop_rookie_veteran_bridge_is_source_separated_and_
trade_aware`, `test_redraft_bootstrap_seeds_once_and_matches_desktop_
contract`, `test_facade_has_no_streamlit_or_app_component_dependency`).

Read in full before writing any code: `PROSPECTIVE_OUTCOME_EVALUATION_
CONTRACT.md`, Worker 1/2's ledger entries above, both of Worker 1's
modules, Worker 2's shared module and all four of its evaluators (used as
the direct structural pattern), plus a real grep of
`src/application/desktop_facade.py`'s actual live TRADE/TRADE_FINDER/
TRADE_PACKAGE_SEARCH/K_STREAMER/DST_STREAMER trace call sites -- done
BEFORE writing any evaluator, to read the REAL recommendation-payload key
names each one actually records (not assumed from the schema alone; see
below, a real, useful finding). Nothing below re-derives a preregistered
window/threshold, bypasses `compute_outcome_evaluation`, or invents a new
identity-resolution/network path.

### Real findings from reading the live call sites first (before coding)

- **TRADE**'s real `recommendation` payload key names are `gives`/
  `receives` (already-resolved canonical player ids).
- **TRADE_FINDER**'s real payload uses SINGULAR `myGivePlayerId`/
  `opponentGivePlayerId` (one-for-one only).
- **TRADE_PACKAGE_SEARCH**'s real payload uses PLURAL `youSend`/
  `youReceive` (real multi-player packages) -- a genuinely different shape
  from TRADE_FINDER despite sharing the same `TradeFinderOutcomeDetail`
  schema kind. Both evaluators read the trace's own frozen keys verbatim,
  per-tool, never assuming one convention for both.
- **K_STREAMER/DST_STREAMER's real live call site does NOT resolve a
  Sleeper player id at all** -- `recommendation` only ever carries
  `playerName`/`team`/`ecr`/`tier` (confirmed by reading
  `desktop_facade.py` directly, matching the ingestion module's own prior
  disclosure). A real K_STREAMER/DST_STREAMER trace recorded by the live
  app today will therefore evaluate to `INSUFFICIENT_DECISION_CONTEXT`
  until identity resolution is wired for these two tool types (Worker 1's
  own Open Issue 3, still unresolved) -- this pass's evaluators are built
  and fully tested against the real schema/ingestion contract, but this is
  a real, disclosed gap for real K/DST trace evaluation specifically, not
  previously stated this precisely.
- **A real, disclosed owner-action vocabulary mismatch for the whole
  TRADE family**: the app's OWN live owner-action UI
  (`decision-history-format.ts`, `ownerActionOptionsForDecisionType`)
  currently offers TRADE/TRADE_FINDER/TRADE_PACKAGE_SEARCH the SAME
  generic 3-option vocabulary as WAIVER ("Followed it" / "Did something
  else" / "Didn't act"), not a trade-specific sent/accepted/rejected/
  cancelled vocabulary. `ingest_trade_finder_outcome` (unchanged, prior
  cycle) only maps `owner_action.action` onto a real disposition when it
  is EXACTLY `"SENT"`/`"CONSIDERED"`/`"IGNORED"` -- so a real owner-action
  append using the app's own real UI copy currently falls through to
  `"UNKNOWN"` rather than a matched disposition. This pass's evaluators do
  not attempt to bridge this gap by guessing a translation (that would be
  inventing a mapping); they report the real, verbatim `owner_action_raw`
  string alongside the schema-derived `acceptanceStatus`/
  `packageDisposition` so both real facts are visible side by side. A real
  fix (either widening `ownerActionOptionsForDecisionType` for the trade
  family, or widening `ingest_trade_finder_outcome`'s accepted action
  strings) is a `desktop_facade.py`/frontend change, out of this pass's
  scope.

### Work Unit 7 -- TRADE (`prospective_outcome_trade_evaluator_v1_service.py`)

Adds `owner_action_raw` (verbatim, never relabeled) and
`recommended_gives_ids`/`recommended_receives_ids` (read from the trace's
own frozen `recommendation.gives`/`recommendation.receives`) on top of
`compute_outcome_evaluation`. Ships the one new public helper
`trade_realized_metrics_from_detail` -- reads `realizedRosterOutcome`
verbatim, no new arithmetic -- reused (not duplicated) by the Trade Finder
evaluator (Work Unit 8). **The rejected-trade guarantee is proven at THREE
independent layers** in this pass's own tests: (1) `TradeOutcomeDetail.
__post_init__`'s own guard (a direct construction test expecting
`ValueError`), (2) the base `OutcomeEvaluation` layer (`NOT_APPLICABLE`,
zero metrics), (3) this evaluator's own extraction never fabricating a
number even reading the raw dict directly. A real test also proves a real
owner-action label ("Followed it") on a trade with no matching Sleeper
transaction still resolves to `REJECTED`, never inferring acceptance from
the free-text label alone.

12 new tests, all passing.

### Work Unit 8 -- TRADE FINDER / TRADE PACKAGE SEARCH
### (`prospective_outcome_trade_finder_evaluator_v1_service.py`)

One evaluator module handling BOTH real `TOOL_TYPES` (`TRADE_FINDER` and
`TRADE_PACKAGE_SEARCH`), gated only for the real per-tool recommendation
key-name lookup (see findings above) -- never inventing a third decision
class. Reuses Work Unit 7's `trade_realized_metrics_from_detail` directly
(imported, not duplicated) for an ACCEPTED package's realized outcome.
`summarize_trade_finder_evaluations` reports raw `packageDispositionCounts`
ONLY -- a real test asserts no key anywhere in the summary spells out
"rate"/"probability"/"likelihood"/"chance", a structural (not just
promised) proof that this pass never converts adoption into an
acceptance-probability prediction, per this whole project's standing
prohibition.

12 new tests, all passing.

### Work Unit 9 -- K STREAMER
### (`prospective_outcome_k_streamer_evaluator_v1_service.py`)

Adds `current_option_*` (a clearer name for the schema's own
`priorRosterOptionPlayerId`/`priorRosterOptionActualPoints`, read verbatim)
and ONE new, disclosed, simple number: `replacement_level_delta_points =
recommendedPlayerActualPoints - priorRosterOptionActualPoints` -- this
pass's own honest interpretation of the directive's "replacement-level
comparison" (the real replacement baseline this schema already tracks:
who would have stayed rostered/started absent the streaming pickup).
`regret_vs_actual_starter_points` is read verbatim from the base
evaluation's own `streamerOpportunityCostPoints` -- never recomputed, and
`replacement_level_delta_points` is never substituted into it (a real test
constructs a case where the two numbers genuinely differ and proves both
survive independently). `best_available_alternative_*` stays sourced only
from the trace's own frozen alternatives (reused, unchanged, from the base
ingestion layer's own no-hindsight guarantee).

13 new tests, all passing.

### Work Unit 10 -- DST STREAMER
### (`prospective_outcome_dst_streamer_evaluator_v1_service.py`)

The DST-side twin of Work Unit 9, in a genuinely SEPARATE module -- not a
shared `_evaluate_streamer(position=...)` helper. `evaluate_k_streamer`/
`evaluate_dst_streamer` are two independently-written functions in two
different modules, each with two hard gates (tool name, then the stored
detail's own `position` field). Proven genuinely separate, not merely
declared so, by real cross-contamination tests in BOTH test files (a
K-tagged trace passed to `evaluate_dst_streamer` is rejected and vice
versa; a defensive second test proves a trace whose `tool` string is
correct but whose stored detail's `position` disagrees is also rejected)
plus one structural test (`inspect.getsource` on each module, asserting
neither module's source text even mentions the other's function name).

13 new tests, all passing.

### Real data exercised this pass

- **DST_STREAMER**: the SAME real, committed Week 1 2026 Fantasy Gamers
  matchup fixture Worker 1/2 already used, reused (not re-pulled). `"NE"`
  is a real, unambiguous Sleeper DST team-code id (per the schema module's
  own documented precedent for DST identity) and a real, confirmed real
  starter that week -- `test_real_fixture_produces_a_real_zero_regret_dst_
  result` verifies a real zero-regret result computed from real points.
- **K_STREAMER**: honestly NOT exercised against real data this pass. The
  real fixture's `players` list carries no position label for any of its
  numeric ids, and no real Sleeper players-catalog/position crosswalk was
  fetched within this pass's scope to confirm which real id is a real K --
  guessing one would have been a fabricated real-data claim. The K
  evaluator's full pipeline is instead exercised against a clearly-labeled
  REALISTIC FIXTURE (synthetic ids), disclosed as such in the test file's
  own comment, not claimed as real. A future worker with a real Sleeper
  players-catalog fetch in scope can close this honestly.
- Trade/Trade Finder/Trade Package Search: per the directive's own
  instruction, evaluated against fixtures only this pass (the prior
  cycle's own finding stands unchanged: real transaction data exists
  league-wide but not yet touching the owner's own roster or any real
  trade) -- no new real-data attempt was made for these three this pass.

### Tests (full)

- 4 new test files, 50 new tests total (12 + 12 + 13 + 13), all passing.
- Targeted regression slice (`pytest -k "decision_trace or
  prospective_outcome or live_player_intelligence or
  boundary_property_reliability or composition or player_availability"`):
  **413 passed, 0 failed** (363 pre-existing + 50 new this pass).
- `tests/test_desktop_application_api.py`: **46 passed / 4 failed** -- the
  SAME 4 pre-existing failures documented in Worker 1/2's own baseline.
  Re-confirmed live after this pass's changes.
- `git diff`/new-file grep for every hard-boundary term
  (`marginal_roster_utility_v2`, `LeagueSnapshot`, `LeagueWorkspaceContext`,
  `lifecycle_resolver`, `DecisionResultEnvelope`,
  `PlayerAvailabilityStatus`) across every file this pass actually created:
  **zero matches**.

### Backend/model files changed this pass

**All new, zero modifications to any existing file** (not even Worker 1/2's
own modules -- Work Unit 8 imports Work Unit 7's `trade_realized_metrics_
from_detail` rather than editing it, and the K/DST evaluators import
nothing from each other):

- `src/services/prospective_outcome_trade_evaluator_v1_service.py`
- `src/services/prospective_outcome_trade_finder_evaluator_v1_service.py`
- `src/services/prospective_outcome_k_streamer_evaluator_v1_service.py`
- `src/services/prospective_outcome_dst_streamer_evaluator_v1_service.py`
- `tests/test_prospective_outcome_trade_evaluator_v1_service.py`
- `tests/test_prospective_outcome_trade_finder_evaluator_v1_service.py`
- `tests/test_prospective_outcome_k_streamer_evaluator_v1_service.py`
- `tests/test_prospective_outcome_dst_streamer_evaluator_v1_service.py`
- This ledger.

## OPEN ISSUES FOR THE NEXT WORKER (Work Units 11-12: Draft outcome
## foundation + automatic outcome ingestion orchestration)

1. **Orchestration wiring still does not exist** -- unchanged from Worker
   1/2's own Open Issue. Nothing in `desktop_facade.py` calls any
   `evaluate_*`/`summarize_*` function from either pass, or Worker 1's
   `compute_outcome_evaluation`/adapters. Work Unit 12 (per this pass's own
   directive framing) is the natural place to finally build this: a real,
   scheduled (or on-demand) job that loads completed-period traces, builds
   a `RecommendationTimeContext`, fetches the matching
   `RealizedOutcomeFetch`, calls the matching `ingest_*_outcome` function,
   and appends via `record_outcome(..., detail=..., outcome_source=
   "SLEEPER", ...)` -- now with EIGHT real, reusable, tested per-class
   evaluator functions (this pass's four plus Worker 2's four) to build
   summaries from afterward.
2. **K_STREAMER/DST_STREAMER identity resolution is the real, concrete
   blocker for real streamer evaluation** (sharpened from Worker 1/2's
   general Open Issue 3, see "Real findings" above): the live call site
   records `playerName`/`team` only, never a Sleeper id, so
   `evaluate_k_streamer`/`evaluate_dst_streamer` will read
   `INSUFFICIENT_DECISION_CONTEXT` for every real trace until an identity
   resolver is wired at that specific call site (or at ingestion time).
3. **The TRADE-family owner-action vocabulary mismatch** (see "Real
   findings" above) is a real, disclosed, NOT-fixed gap: the real app UI
   offers "Followed it"/"Did something else"/"Didn't act" for TRADE/
   TRADE_FINDER/TRADE_PACKAGE_SEARCH, but `ingest_trade_finder_outcome`
   only recognizes `"SENT"`/`"CONSIDERED"`/`"IGNORED"` as real owner-action
   strings. Fixing it touches `desktop_facade.py`/the frontend, out of this
   pass's scope -- flagged so it is not silently lost.
4. **Work Unit 11 (DRAFT outcome foundation)** was not started this pass,
   per this pass's own explicit assignment (Work Units 7-10 only).
   `DraftOutcomeDetail`/`build_deferred_draft_outcome_detail` already exist
   (prior cycle) as an intentionally-thin, deferred placeholder -- real
   season-long roster-utility computation still belongs to
   `marginal_roster_utility_v2`, outside this cycle's hard boundary. A
   future worker building real Draft outcome evaluation needs the hard
   boundary explicitly cleared/re-scoped first; this pass does not attempt
   that judgment call.
5. **History UI V3** (rendering any of these eight evaluators' output) was
   not attempted this pass either, unchanged from Worker 1/2's own
   disclosure -- backend evaluator logic only, per this pass's own explicit
   assignment.
6. **A real ROS window, the duplicated `MIN_SAMPLE_SIZE_FOR_PER_CLASS_*`
   constant, ADD_DROP's still-uncomputed `netRosterValuePoints`, and
   real owner (roster 9) WAIVER/ADD_DROP/FAAB outcome data** are all
   unchanged, inherited open items from Worker 1/2 -- see their own entries
   above for the full detail; none were touched this pass.
7. **This pass's own K_STREAMER real-data gap** (see "Real data exercised"
   above): a real Sleeper players-catalog/position crosswalk was not
   fetched to confirm a real K identity from the committed Week 1 2026
   fixture. Worth closing for real once that crosswalk is in scope --
   DST_STREAMER's own real exercise (`"NE"`) did not need one, since
   Sleeper's own DST ids are unambiguous team codes.

## Worker 4 (this pass) -- Work Units 11-12: DRAFT outcome foundation +
## automatic outcome ingestion orchestration

Start HEAD `41af0791` (Worker 3's closing commit). Not merged, not pushed,
not deployed. Verified live before writing any code: branch, clean
worktree, the 413-test targeted slice, `test_desktop_application_api.py`'s
same 4 pre-existing failures (`test_dynasty_facade_composes_real_governed_
workflows`, `test_desktop_rookie_veteran_bridge_is_source_separated_and_
trade_aware`, `test_redraft_bootstrap_seeds_once_and_matches_desktop_
contract`, `test_facade_has_no_streamlit_or_app_component_dependency`).

Read in full before writing any code: `PROSPECTIVE_OUTCOME_EVALUATION_
CONTRACT.md`, Worker 1/2/3's ledger entries above, all 8 evaluators, the
base evaluation/ingestion/source-adapter modules, and
`in_season_decision_trace_service.py` (confirmed live: `TOOL_TYPES`
already includes `"DRAFT"`, but a real grep of `desktop_facade.py` found
ZERO `tool="DRAFT"` call sites -- the schema exists, nothing populates it
yet, exactly as Worker 3 characterized it).

### Work Unit 11 -- DRAFT outcome FOUNDATION (schema + hooks only)

**New**: `src/services/prospective_outcome_draft_foundation_v1_service.py`.
Additive alongside (never replacing) the prior cycle's `DraftOutcomeDetail`
-- a new `DraftPickOutcomeDetail` (`KIND = "DRAFT_PICK_V1"`, a genuinely
different kind from `DRAFT_V1`) with every dimension the directive named:
`actual_chosen_player_id` (always required -- the one fact that's always
real), `recommended_player_id`/`recommendation_time_candidate_set_ids`
(the frozen recommendation-time facts), `season_points`/`starts`/
`weeks_usable`/`roster_utility`/`replacement_value` (always `None` this
cycle -- real computation stays out of this pass's hard boundary AND the
2026 season has only just started, so nothing honest to compute either
way), and a **structurally separate** `injury_designation`/
`weeks_missed_to_injury` pair that no code path in this module reads when
deciding `evaluation_method`.

**No retroactive reconstruction, enforced structurally, not just
documented**: `build_draft_pick_outcome_detail` -- the one real "future
ingestion hook" this pass ships -- returns
`DRAFT_EVALUATION_METHOD_INSUFFICIENT_CONTEXT` (a NEW constant this pass
adds, distinct from the prior cycle's `DRAFT_EVALUATION_METHOD_DEFERRED`)
whenever the caller cannot supply BOTH a real, non-empty `recommendation_
time_candidate_set_ids` AND a `recommended_player_id` that is a genuine
MEMBER of that same set -- `recommended_player_id` is forced back to `None`
in every such case even if the caller passed a real-looking guess, so a
guess can never leak into a field meaning "genuinely known at
recommendation time." `DraftPickOutcomeDetail.__post_init__` enforces the
same invariant on direct construction too (proven by a dedicated test,
not just the builder).

**Injury never proves a bad decision** -- proven three ways: (1) a direct
field-independence test (two picks, identical recommendation context,
different injury fields, identical `evaluation_method`), (2) a test that an
injured player with NO recorded recommendation-time context still resolves
to `INSUFFICIENT_DECISION_CONTEXT` (injury data never upgrades or
downgrades that verdict), (3) a structural source-text scan for forbidden
co-occurring phrase patterns (`"injury"` + `"proof of a bad"`, etc.) --
none found.

**Hard boundary respected structurally**: a real test parses this module's
own `import`/`from` lines and asserts none names
`marginal_roster_utility_v2`/`shadow_numeric_authorities_service`/
`league_workspace_context_service`/`lifecycle_resolver`/
`player_availability_status` -- the module DOCSTRING does discuss
`marginal_roster_utility_v2` in prose (disclosing why it's not touched, the
same way every prior worker's own ledger entry does), so the test checks
real imports, not a blanket ban on the word.

`draft_outcome_ready_for_season_long_evaluation` is a real, honest stub --
always `False` this cycle, mirroring the contract's own explicit deferral
of a real ROS window rather than inventing a season-readiness threshold
with no real basis yet.

13 new tests, all passing.

### Work Unit 12 -- automatic outcome INGESTION ORCHESTRATION

**New**: `src/services/prospective_outcome_ingestion_orchestrator_v1_
service.py` + `scripts/run_prospective_outcome_ingestion_v1.py` (the real,
callable CLI command the directive asked for).

**Real per-tool identity findings, read directly from `desktop_facade.py`
before writing any code** (same discipline Worker 3 used): WAIVER's real
live call site records `recommendation.topAddCanonicalId` (NWR's OWN
ranking-id space, not a Sleeper id); FAAB's real live call site records
only `playerName`/`bidLowDollars`/`bidHighDollars` (no id at all);
K_STREAMER/DST_STREAMER confirmed unchanged from Worker 3 (`playerName`/
`team` only); ADD_DROP has no live call site; TRADE/TRADE_FINDER/
TRADE_PACKAGE_SEARCH all record real `week=None` at their live call sites
(confirmed by reading each one directly this pass) AND record canonical
(not Sleeper) player ids in `gives`/`receives`/`myGivePlayerId`/etc.
**Only START_SIT's real live call site already records raw Sleeper ids
directly** (`recommendation.starters`) -- the ONE class this pass gives a
real, full, network-fetching pipeline. Building a brand-new canonical-id
-> Sleeper-id resolver for the other five was judged OUT of this pass's
scope (the directive's own framing is "reuse the existing adapters/
ingestion/evaluators," not "build new identity resolution" -- Worker 1's
own Open Issue 3, still explicitly unresolved, inherited unchanged).

**The real design, per class**:
- **START_SIT**: `plan_ingestion_action` gates on (a) no outcome yet, (b)
  `current_nfl_week > week` (the frozen `SAME_WEEK_LOCK_TO_FINAL` window,
  imported verbatim from Worker 1's `EVALUATION_WINDOWS` -- never
  re-derived), (c) a real, caller-supplied `owner_roster_id` for that
  `league_id`. When all three hold, `execute_plan_item` performs a REAL
  `fetch_owner_matchup_entry` + `adapt_and_ingest_start_sit_outcome` +
  `record_outcome(..., outcome_source="SLEEPER", ...)` + `evaluate_
  start_sit` -- exactly the same pieces Worker 1/2 already built and
  tested, composed for the first time into something that actually runs
  automatically.
- **WAIVER/FAAB/ADD_DROP/K_STREAMER/DST_STREAMER**: once their real,
  preregistered window has genuinely matured (BOUNDED_HORIZON 4 weeks for
  the first three, SAME_WEEK for the last two -- both imported from the
  SAME frozen `EVALUATION_WINDOWS`), this orchestrator calls the SAME
  `ingest_*_outcome` function every evaluator already trusts with the
  player-id argument(s) honestly `None`, then `record_outcome(outcome=
  "INSUFFICIENT_DECISION_CONTEXT", detail=...)`. This makes the gap a
  REAL, EXPLICIT, visible ledger fact -- not a silent skip indistinguishable
  from "not yet processed" (directive item 6, proven directly: a test
  asserts ZERO network calls happen on this path, since there is nothing
  honest to fetch without a resolved identity).
- **TRADE / TRADE_FINDER / TRADE_PACKAGE_SEARCH**: `week=None` means there
  is no real week to anchor a bounded-horizon maturity check to --
  `plan_ingestion_action` returns `SKIP_WINDOW_UNDETERMINABLE` for every
  one of these, genuinely untouched, rather than fabricating a week. A
  real, disclosed open issue (below), not silently dropped.
- **DRAFT**: always `SKIP_DEFERRED_DRAFT`.

**Idempotency -- the directive's own required proof, delivered for real,
twice over**: `plan_ingestion_action` checks `record.outcome is not None`
FIRST, unconditionally, before any maturity/identity logic -- the ONLY
thing that ever sets `record.outcome` is `record_outcome` itself, so a
trace this orchestrator (or any other real caller) already processed is
always `SKIP_ALREADY_PROCESSED` on every subsequent run.
`test_running_ingestion_twice_produces_byte_identical_ledger_state`
(pytest, hermetic) builds a 3-trace mixed store (one real-fixture
START_SIT, one insufficient-context WAIVER, one still-immature FAAB), runs
`run_ingestion` twice, and asserts the RAW ledger file text is
byte-for-byte identical after the second run, the second run's own
`SleeperHttpClient` double makes ZERO calls, and `load_decision_traces`
returns an equal tuple both times -- not merely "no crash." **Then proven
again for real, outside pytest, against genuinely live Sleeper data**: a
real isolated demo root (`scripts/run_prospective_outcome_ingestion_v1.py`
run four times in sequence against one real START_SIT trace (real Week 1
2026 Fantasy Gamers data, mechanism-demonstration baseline, same honest
framing as the prior cycle's own demo script), one real WAIVER trace, and
one real DST_STREAMER trace) -- run 1 processed START_SIT for real (a real
`GET league/.../matchups/1` call, `lineupOpportunityCostPoints: 0.0`,
`evaluationStatus: "EVALUATED"`) and left WAIVER genuinely immature; run 2
made a real, live, byte-for-byte-verified no-op (`diff` confirmed
identical); a real DST_STREAMER trace was then added and run 3 correctly
produced a real, explicit `INSUFFICIENT_DECISION_CONTEXT` (SAME_WEEK window
had matured, identity unresolved); run 4 again produced a real,
byte-for-byte-verified no-op across all three traces together.

**Maturity respected**: `test_immature_events_are_genuinely_untouched`
(WAIVER, week 5, current week 6 -- `5+4=9`, not yet `>`) proves the trace's
own `outcome` stays `None` and zero network calls are made; the real live
demo run above proves the same thing against a genuinely real WAIVER trace
(current real NFL week is only 2 as of this pass -- nothing bounded-horizon
CAN be real-matured yet, an honest, expected finding this early in the
2026 season, not a bug).

**`INSUFFICIENT_DECISION_CONTEXT` visibility**: proven both in pytest
(`test_run_ingestion_never_fetches_network_for_insufficient_context_path`)
and against real live data (the DST_STREAMER run above) -- the ledger's
`outcome.outcome` field literally reads `"INSUFFICIENT_DECISION_CONTEXT"`
and `outcome.detail.recommendedPlayerId` is `None`, visibly distinct from a
trace that's simply never been touched (`outcome is None` entirely).

**A real, honestly-scoped operational gap, distinguished from a decision-
context gap**: `SKIP_OWNER_ROSTER_UNKNOWN` -- a START_SIT trace whose
league has no caller-supplied `owner_roster_id` mapping is left genuinely
`PENDING_OUTCOME`, NEVER marked `INSUFFICIENT_DECISION_CONTEXT` (that
status is reserved for a genuine recommendation-time-context gap, not an
orchestration-configuration one). The CLI script's one real, built-in
mapping is the one real, confirmed pair this codebase has (`1312983576827
920384 -> 9`, Fantasy Gamers/`scolety`, matching the prior cycle's own demo
script) -- a general per-profile resolver is explicitly out of scope (open
issue below).

**Real production trace store checked directly**: `GET .../state/nfl`
confirmed the real current NFL week is `2` as of this pass (`display_week:
1`, `week: 2` -- Week 1's games have concluded). The REAL AppData redraft
root (`...\com.ninerswarroom.redraft\state\redraft`) has NO
`decision_traces/` directory at all -- confirmed via a real, read-only run
of the CLI script against that exact path: `countsByAction: {}`,
`processed: []`, zero files created. This is an honest finding (no live
call site has ever actually recorded a trace there yet, matching Worker
1/2/3's own accumulated findings about which call sites are truly wired
end-to-end), not a bug in this pass's own code.

`execute_plan_item` also gets two direct misuse-guard tests (rejecting a
`SKIP_*` action; rejecting a `PROCESS_FULL_START_SIT` item with no
`owner_roster_id` supplied) and a structural hindsight-leakage assertion
(`_assert_plan_function_is_safe`, asserted at import time on
`plan_ingestion_action`, plus a test that actually triggers it on a
deliberately-bad function -- the same pattern every module this cycle
uses).

26 new tests, all passing.

### Tests (full)

- 2 new test files (`test_prospective_outcome_draft_foundation_v1_
  service.py`, `test_prospective_outcome_ingestion_orchestrator_v1_
  service.py`), 39 new tests total (13 + 26), all passing.
- Targeted regression slice (`pytest -k "decision_trace or
  prospective_outcome or live_player_intelligence or
  boundary_property_reliability or composition or player_availability"`):
  **452 passed, 0 failed** (413 pre-existing + 39 new this pass).
- `tests/test_desktop_application_api.py`: **46 passed / 4 failed** -- the
  SAME 4 pre-existing failures documented in every prior worker's own
  baseline. Re-confirmed live after this pass's changes.
- Hard-boundary grep across every file this pass actually created: every
  match is disclosure prose (module docstrings explaining what was NOT
  touched and why) or a test assertion checking real `import` lines --
  zero real imports/modifications of any hard-boundary module.

### Backend/model files changed this pass

**All new. Zero modifications to any existing file** (confirmed via `git
status --porcelain` -- every changed path is untracked/new):

- `src/services/prospective_outcome_draft_foundation_v1_service.py`
- `src/services/prospective_outcome_ingestion_orchestrator_v1_service.py`
- `scripts/run_prospective_outcome_ingestion_v1.py`
- `tests/test_prospective_outcome_draft_foundation_v1_service.py`
- `tests/test_prospective_outcome_ingestion_orchestrator_v1_service.py`
- This ledger.

### Sleeper writes

**Zero.** Every real network call this pass made (or that the CLI script
makes) is a plain `GET` against a public, keyless Sleeper endpoint
(`state/nfl`, `league/{id}/matchups/{week}`) -- the same real, already-
wired endpoints every other real call site in this codebase uses. All real
LOCAL ledger writes this pass verified went to isolated scratch roots
(pytest's own `tmp_path`, and a real, disclosed demo root under this
session's scratchpad directory) -- NEVER the real production AppData
store, which this pass only ever READ from (confirmed empty of decision
traces, zero files created by that read).

## OPEN ISSUES FOR THE NEXT WORKER (Work Units 13-14: History UI V3 +
## class-specific summary)

1. **Identity resolution for WAIVER/FAAB/ADD_DROP/K_STREAMER/DST_STREAMER/
   TRADE-family remains the real, concrete blocker to real (non-
   insufficient-context) automatic evaluation for those six classes** --
   unchanged in substance from Worker 1's Open Issue 3, now sharpened with
   this pass's own confirmed real payload keys (`topAddCanonicalId` for
   WAIVER; no id at all for FAAB; `playerName`/`team` for K/DST; canonical
   ids for the whole TRADE family). Building a real canonical-id ->
   Sleeper-id crosswalk (via `resolve_roster_canonical_ids` + a fresh
   players-catalog/ranking-rows fetch) would let this orchestrator give
   these classes the same real, full pipeline START_SIT gets. Out of this
   pass's own scope.
2. **TRADE/TRADE_FINDER/TRADE_PACKAGE_SEARCH have no real week to anchor a
   maturity check to** -- their real live call sites record `week=None`.
   This orchestrator leaves them permanently `SKIP_WINDOW_UNDETERMINABLE`
   until a future pass either (a) adds a real week capture to those call
   sites, or (b) derives a week from the eventual matched Sleeper trade
   transaction's own real timing. Not fixed this pass (would touch
   `desktop_facade.py`, out of scope).
3. **`owner_roster_id` resolution is a real, caller-supplied mapping, not a
   general resolver** -- the CLI script ships the ONE real, confirmed pair
   (Fantasy Gamers `1312983576827920384 -> 9`). A future worker wanting
   this to work automatically for an arbitrary profile needs to read that
   profile's own stored Sleeper identity (would touch profile-loading code
   adjacent to, but not necessarily inside, the hard boundary) -- not
   attempted this pass.
4. **The real production trace store has zero decision traces recorded
   in it** (confirmed this pass, not merely assumed) -- every real, live
   call site this codebase has (START_SIT, WAIVER, FAAB, K_STREAMER,
   DST_STREAMER, TRADE, TRADE_FINDER, TRADE_PACKAGE_SEARCH) exists in code
   but has apparently never actually fired against the owner's real
   production profile/root yet (or a different root than the one this pass
   checked is in use -- worth confirming with the owner directly). The
   orchestrator and CLI script are real and ready the moment real traces
   start accumulating there.
5. **DRAFT's real live call site still does not exist** -- Work Unit 11
   built the schema/hooks a future wiring pass needs
   (`build_draft_pick_outcome_detail`), but no code anywhere calls
   `record_decision_trace(..., tool="DRAFT", ...)` yet. That wiring (and
   the real season-long roster-utility computation `roster_utility`/
   `season_points`/etc. are placeholders for) is explicitly out of this
   cycle's hard boundary.
6. **History UI V3** (Work Unit 13) and **class-specific summary
   surfacing** (Work Unit 14) were not attempted this pass, per this pass's
   own explicit Work Unit 11-12 assignment. Every evaluator's `to_dict()`
   (Workers 2/3) and this pass's own `IngestionRunReport.to_dict()`/
   `ExecutedIngestionResult.to_dict()` are the real, tested payload shapes
   to build on.
7. **A real ROS window, the duplicated `MIN_SAMPLE_SIZE_FOR_PER_CLASS_*`
   constant, ADD_DROP's still-uncomputed `netRosterValuePoints`, and real
   owner (roster 9) WAIVER/ADD_DROP/FAAB outcome data** are all unchanged,
   inherited open items from Worker 1/2/3 -- none were touched this pass.

## Worker 5 (this pass) -- Work Units 13-14: History UI V3 + class-specific
## summary

Start HEAD `9038d1fd` (Worker 4's closing commit). Not merged, not pushed,
not deployed. Verified live before writing any code: branch, clean
worktree, the 452-test targeted slice, `test_desktop_application_api.py`'s
same 4 pre-existing failures (`test_dynasty_facade_composes_real_governed_
workflows`, `test_desktop_rookie_veteran_bridge_is_source_separated_and_
trade_aware`, `test_redraft_bootstrap_seeds_once_and_matches_desktop_
contract`, `test_facade_has_no_streamlit_or_app_component_dependency`).

Read in full before writing any code: `PROSPECTIVE_OUTCOME_EVALUATION_
CONTRACT.md`, Worker 1-4's ledger entries above, all 8 evaluators' real
`to_dict()` field names and `evaluate_*`/`summarize_*` signatures, and the
existing History UI V2 (`decision-history.tsx`/`decision-history-format.ts`,
an earlier session's own prior pass) -- upgraded in place, never rebuilt.

### The real, concrete gap found before writing any UI code

Nothing in `desktop_facade.py` or any HTTP route called `compute_outcome_
evaluation` or any of the 8 real `evaluate_*`/`summarize_*` functions
(Worker 1-4's own Open Issue, restated in every prior ledger entry). History
UI V2's `redraft_decision_trace_history` only ever returned the raw
ingestion-layer `outcome.detail` (the 8 schema dataclasses), never the
richer `OutcomeEvaluation` contract (`evaluationStatus`/`evaluationMetrics`/
`issues`) or any per-class evaluator's own extra fields
(`lineupOpportunityCostPoints`, `bidRangeCalibration`, etc.). Building
History UI V3 as specified required real, additive backend wiring first --
this pass's own judgment call, not a silent scope expansion: the directive's
own hard-boundary text allows "render their output, don't modify it,"
and rendering requires the output to actually reach the frontend first.

### New backend module: `src/services/prospective_outcome_history_presentation_v1_service.py`

Pure composition, zero new evaluation logic -- imports and calls the 8 real
`evaluate_*` functions (never re-implements one), dispatched by
`record.tool`, and each 8 real `summarize_*` functions for the class
summary. Two public functions:

- `evaluation_payload_for_record(record)` -- the real per-row evaluation
  payload for History UI V3, one evaluator's own `to_dict()` verbatim.
  DRAFT (no real evaluator this cycle, hard boundary) and any unrecognized
  tool fall back to the base `compute_outcome_evaluation(record).to_dict()`
  wrapped in the same `{traceId, evaluation}` envelope every evaluator uses.
- `class_specific_summaries(records)` -- Work Unit 14's real per-class
  summary, one independent entry per class (`CLASS_SUMMARY_DECISION_TYPES`,
  9 real values -- the 8 evaluated classes plus DRAFT, which always reports
  a real, structurally-distinct "deferred to `marginal_roster_utility_v2`"
  note, never `NOT_ENOUGH_DATA_YET`). TRADE_FINDER and TRADE_PACKAGE_SEARCH
  are summarized TOGETHER under one shared `"TRADE_FINDER"` entry (Worker
  3's own established design), never merged with plain TRADE. Every
  `summarize_*` function's own minimum-sample gate
  (`MIN_SAMPLE_SIZE_FOR_PER_CLASS_SUMMARY = 20`, Worker 1's own constant) is
  reused verbatim, never re-derived.

### A real, disclosed bug found and fixed THIS pass -- discovered by the
### real Chrome dogfood, not by code review alone

Wiring `class_specific_summaries` to a real HTTP response and actually
rendering it in a real browser tab (not just pytest) surfaced a real bug:
`desktop_facade.py`'s response envelope runs every dict KEY in the JSON
response through a generic snake_case/ENUM -> camelCase transform
(`contracts.py::camel_case_key`) -- the SAME real bug class already
disclosed and fixed for player-id dict keys in `prospective_outcome_
schema_v1_service.py` (`_points_by_player_list`, e.g. Sleeper DST code
`"NE"` -> `"nE"`). Worker 2/3's own `summarize_*_evaluations` functions
(correct, fully tested in isolation -- pytest never exercises the HTTP
envelope) build real `statusCounts`/`acceptanceStatusCounts`/
`packageDispositionCounts` dicts KEYED BY a real enum string
(`"EVALUATED"` -> mangled to `"eVALUATED"` over HTTP); this pass's own
first version of `class_specific_summaries` made the exact same mistake at
its own top level (a dict keyed by `decisionType`, e.g. `"START_SIT"` ->
`"startSit"`). Real, live proof: a real Chrome tab rendered the Class-
Specific Summary panel as a visibly EMPTY grid with a real 200 OK network
response underneath it -- `curl` against the real live endpoint confirmed
the exact mangled JSON. **Fixed narrowly, at this pass's own new
presentation layer only** (never touching Worker 2/3's `summarize_*`
functions' own dict-returning code): `_as_count_pairs` reshapes every
enum-keyed dict into a `[{status|disposition, count}]` LIST before it
leaves this module, and `class_specific_summaries` itself now returns a
LIST (each entry already carrying its own real `decisionType` field)
instead of a dict keyed by decisionType. Re-verified live in the same
Chrome tab after the fix: all 9 real class cards render correctly. A new
test (`test_status_counts_and_disposition_counts_never_carry_a_raw_enum_
keyed_dict`) proves this can't silently regress.

### Facade/HTTP wiring (additive only)

- `_decision_trace_history_event_payload` (existing function) gains one new
  key, `evaluationDetail` -- the real per-row payload from
  `evaluation_payload_for_record`. Every pre-existing key is unchanged.
- New facade method `redraft_decision_trace_outcome_summary()` -- loads the
  active profile's own real ledger, calls `class_specific_summaries`, scoped
  identically to `redraft_decision_trace_history` (same active-profile
  requirement, same never-cross-league guarantee, proven by a real test).
- New route `GET /api/v1/redraft/decision-trace-outcome-summary` wired in
  `src/desktop_api/server.py`, following the exact existing pattern.

### History UI V3 (Work Unit 13)

`desktop/apps/redraft/src/decision-history.tsx` /
`decision-history-format.ts` upgraded IN PLACE (V2's `hasOutcomeDetail`/
`buildOutcomeDetailSections`/`OwnerActionCell`/owner-action capture flow all
reused unchanged). The exact 6 columns: DATE / LEAGUE (new in V3 -- V2
omitted it, relying on the page's own single-league scoping) / DECISION
TYPE / NWR RECOMMENDATION / OWNER ACTION / OUTCOME STATUS. Outcome Status
now shows the real `OutcomeEvaluation.evaluationStatus` (the 5 real, closed
values -- `PENDING_OUTCOME`/`PENDING_WINDOW`/`EVALUATED`/
`INSUFFICIENT_DECISION_CONTEXT`/`NOT_APPLICABLE`, confirmed directly from
`EVALUATION_STATUSES` in `prospective_outcome_evaluation_v1_service.py`,
never the directive's own paraphrased guesses and never a parallel
vocabulary), replacing V2's ledger-append status
(`RECOMMENDED`/`OWNER_ACTION_RECORDED`/`OUTCOME_RECORDED`, which answered
"has this been appended to" rather than "could this be evaluated" -- no
longer shown anywhere on this page). A real, honest one-line class-specific
headline (`formatClassSpecificHeadline`) sits under the badge, built ONLY
from real evaluator fields -- verified live to produce the directive's own
worked examples verbatim: `"+4.8 pts over chosen starter"` (START_SIT),
`"Won at $18; suggested $15-$21"` (FAAB), `"Rejected — no evaluation"` /
`"Accepted; net +6.5 pts over 4wk horizon"` (TRADE -- the "still open"
variant is real too, rendered whenever `netSubsequentPointsDeltaPoints` is
genuinely still `null`), `"Recommended 12.0 actual pts; current roster K
scored 6.0"` (K/DST). The expandable "View outcome detail" affordance
(`buildEvaluationDetailSections`) now renders from the real
`evaluationDetail` payload for all 8 classes (an `Evaluation` section with
the real window/status/issues, plus each class's own real fields -- FAAB's
two axes stay genuinely separate sections, TRADE's realized-outcome section
only appears for an actually-accepted trade), falling back to V2's own raw
`outcome.detail` rendering only for a legacy event with no `evaluationDetail`
at all. **No aggregate "NWR ACCURACY: X%" figure anywhere -- confirmed by a
real test that greps the rendered output for forbidden terms.**

### Class-specific summary (Work Unit 14)

A new `ClassSummaryPanel` on the SAME History page (not a new page/app),
fetching `redraftDecisionTraceOutcomeSummary()` and rendering one
independent card per real class (`buildClassSummaryDisplay`), each reading
ONLY that class's own real `summarize_*` fields -- proven live: at 24 real
EVALUATED START_SIT samples (above the real 20-sample threshold), the card
shows a real computed `"Average lineup opportunity cost (regret): +0.81
pts"`; every other class, genuinely below threshold in the same real
fixture data, honestly shows `"NOT ENOUGH DATA YET (n=X, need 20)"` per
axis, never a number computed from too few points. TRADE's real
`acceptanceStatusCounts` (`"ACCEPTED: 1, REJECTED: 1"`) render as raw counts,
never a rate -- matching Worker 3's own standing prohibition. DRAFT renders
its structurally-distinct deferred note. **Never one combined grid/score --
each card is visually and structurally independent, confirmed by a
real test that asserts no card ever references another class's own
decisionType or numeric value.**

### Real-data honesty (confirmed, not merely asserted)

The real production AppData trace store's own confirmed-empty state
(Worker 4's finding) is unchanged and is NOT contradicted by anything this
pass renders -- every real number shown live in this pass's own Chrome
dogfood (the `+0.81 pts` START_SIT mean, the `+4.8`/`Won at $18` headlines,
etc.) comes from a clearly-disclosed FIXTURE root
(`scripts/build_history_ui_v3_demo_root_v1.py`, its own module docstring
states this explicitly), never the real production store. That script was
never pointed at the real owner AppData path. Against the real, empty
production store, every class on this page will honestly show
`NOT_ENOUGH_DATA_YET`/`PENDING_OUTCOME` -- exactly the directive's own
stated expectation, not a defect.

### New demo/dogfood script: `scripts/build_history_ui_v3_demo_root_v1.py`

Zero network I/O (every `ingest_*_outcome` call is a pure function over
fabricated, schema-shaped JSON) -- builds one real, isolated redraft
profile with 35 real trace records spanning: 24 real EVALUATED START_SIT
traces (22 bulk + the 2 directive-worked-example ones, clearing the real
20-sample summary threshold live), one genuinely `PENDING_OUTCOME` trace,
one genuinely `INSUFFICIENT_DECISION_CONTEXT` legacy bare-outcome trace, one
real accepted + one real rejected TRADE, one accepted TRADE_FINDER, one
K_STREAMER + one DST_STREAMER (both matching the directive's own worked
example numbers exactly), one WAIVER won + one WAIVER not-submitted, one
FAAB win (`$18` vs suggested `$15-$21`, the directive's own exact example),
one ADD_DROP. Writes only to an isolated temp `redraft_root`, never the
real production AppData store. A committed disclosure summary lives at
`docs/codex/prospective_outcomes_v1/history_ui_v3_demo_v1/summary.json`.

### Real Chrome dogfood (not just unit tests)

A real, live desktop-API standalone process (`scripts/run_nwr_desktop_api.py
--port 18742 --mode redraft`, `NWR_REDRAFT_HOME` pointed at the demo root
above) plus a real Vite dev server (`--port 1422`) plus a real Chrome MCP
tab, exactly the pattern the "Draft Room GUI consolidation" session
established (`HashRouter`, real route `#/decision-history` ->
auto-redirects to `#/league/<profileId>/decision-history`). Confirmed live:
all 35 rows render with real headlines matching every one of the
directive's own worked examples verbatim (quoted above); the FAAB row's
expandable detail renders both axes correctly (`Player decision quality`/
`Bid range calibration` as genuinely separate sections); all 9 class-summary
cards render (only after the bug fix above); zero console errors on a
clean page load (one transient error WAS observed mid-development, tied to
a Vite HMR hot-update race against stale in-memory state from BEFORE the
backend bug fix was deployed -- confirmed self-resolved by a full reload,
not present in the final code, disclosed here rather than omitted). Both
dev processes were cleanly shut down afterward (`netstat` confirmed ports
1422/18742 clear).

### Tests

- New: `tests/test_prospective_outcome_history_presentation_v1_service.py`
  -- 21 passed (dispatch correctness for all 8 classes + DRAFT/unknown-tool
  fallback, per-class summary independence, TRADE_FINDER/
  TRADE_PACKAGE_SEARCH combination, the enum-keyed-dict bug fix proven at
  the source, and 8 facade-level wiring tests including a real
  never-leaks-across-leagues check for the new summary endpoint).
- Targeted regression slice (`pytest -k "decision_trace or
  prospective_outcome or live_player_intelligence or
  boundary_property_reliability or composition or player_availability"`):
  **473 passed, 0 failed** (452 pre-existing + 21 new this pass).
- `tests/test_desktop_application_api.py`: **46 passed / 4 failed** -- the
  SAME 4 pre-existing failures documented in every prior worker's own
  baseline. Re-confirmed live after this pass's changes.
- Frontend: `desktop/apps/redraft/src/decision-history-format.test.ts`
  extended with a full History UI V3 / Work Unit 14 test block (55 tests in
  that file total, up from 31) -- `evaluationStatusLabel`/`evaluationStatusTone`
  over the real closed 5-status set, `formatClassSpecificHeadline` for
  every one of the 8 classes (including the directive's own exact worked
  examples), `buildOutcomeDetailSections`'s new evaluationDetail-sourced
  path (with a test proving it's preferred over the legacy raw-detail path
  when both are present), and `buildClassSummaryDisplay` (threshold gating,
  cross-class independence, DRAFT's structural distinctness, the real
  `{status, count}` list shape).
- Full monorepo `npx vitest run` (from `desktop/`): **410 passed, 28 test
  files, 0 failed.**
- `npm run typecheck` (`tsc -b apps/dynasty/tsconfig.json apps/redraft/
  tsconfig.json`): **clean, zero errors.**
- Hard-boundary grep (`marginal_roster_utility_v2`, `LeagueSnapshot`,
  `LeagueWorkspaceContext`, `lifecycle_resolver`, `DecisionResultEnvelope`,
  `PlayerAvailabilityStatus`) across this pass's ENTIRE diff: every match is
  disclosure prose (this module's own docstring, a DRAFT summary note, a
  pre-existing `leagueSnapshotId` field name) -- zero real imports/
  modifications of any hard-boundary module or semantic.

### Backend/model files changed this pass

- **New**: `src/services/prospective_outcome_history_presentation_v1_
  service.py`, `tests/test_prospective_outcome_history_presentation_v1_
  service.py`, `scripts/build_history_ui_v3_demo_root_v1.py`,
  `docs/codex/prospective_outcomes_v1/history_ui_v3_demo_v1/summary.json`.
- **Modified (additive only)**: `src/application/desktop_facade.py`
  (`_decision_trace_history_event_payload` gains one new key,
  `evaluationDetail`; new method `redraft_decision_trace_outcome_summary`),
  `src/desktop_api/server.py` (one new route constant + GET dispatch line).
  **None of the 8 evaluators' or the orchestrator's own computation logic
  was touched** -- every evaluator/summarizer function is called, never
  edited (the one genuine bug fix lives entirely in this pass's own new
  module, reshaping OUTPUT for the frontend, never evaluation logic).
- **Frontend, modified**: `desktop/packages/contracts/src/index.ts` (new
  `OutcomeEvaluation`/8 evaluator-payload/`DecisionClassSummary` types, all
  additive), `desktop/packages/api-client/src/index.ts` (new
  `redraftDecisionTraceOutcomeSummary` method), `desktop/apps/redraft/src/
  decision-history-format.ts` (History UI V3 additions, V2's own exports
  unchanged), `desktop/apps/redraft/src/decision-history.tsx` (League
  column, evaluationStatus-based Outcome Status cell, new
  `ClassSummaryPanel`), `desktop/apps/redraft/src/redraft.css` (new rules,
  additive), `desktop/apps/redraft/src/decision-history-format.test.ts`
  (extended, not replaced).

## OPEN ISSUES FOR THE NEXT WORKER (Work Units 15+18: real outcome
## ingestion for matured recommendations + boundary property test pack V2)

1. **The real production trace store still has zero decision traces
   recorded in it** -- unchanged from Worker 4's own finding; nothing this
   pass did writes to or reads from that real path. History UI V3 and the
   class-specific summary are real and ready the moment real traces start
   accumulating there; today they will honestly show
   `PENDING_OUTCOME`/`NOT_ENOUGH_DATA_YET` throughout.
2. **The orchestrator (`prospective_outcome_ingestion_orchestrator_v1_
   service.py`, Worker 4) is still not wired to run automatically** -- it
   exists and is tested/demoed via its own CLI script, but nothing schedules
   or triggers it from the live app. Work Unit 15's own "real outcome
   ingestion for matured recommendations" is the natural place to close
   this, now with a real, live-verified UI on the other end to actually see
   the results land.
3. **Identity resolution for WAIVER/FAAB/ADD_DROP/K_STREAMER/DST_STREAMER/
   TRADE-family** remains the real, concrete blocker to real (non-
   insufficient-context) automatic evaluation for those six classes --
   unchanged, inherited from Worker 1/3/4. History UI V3 will correctly
   render `INSUFFICIENT_DECISION_CONTEXT` for these once real traces exist,
   which is the honest, expected behavior until that resolver is built.
4. **TRADE/TRADE_FINDER/TRADE_PACKAGE_SEARCH have no real week to anchor a
   maturity check to** -- unchanged from Worker 4's own Open Issue 2.
5. **`owner_roster_id` resolution is a real, caller-supplied mapping, not a
   general resolver** -- unchanged from Worker 4's own Open Issue 3.
6. **A real, disclosed presentation-layer bug class was found and fixed
   THIS pass** (enum-keyed dicts mangled by the HTTP camelCase-key
   transform) -- fixed at this pass's own new module only. Any FUTURE
   backend surface that puts a real enum/status string as a JSON object KEY
   (not just this cycle's own modules) is at risk of the exact same bug;
   worth a wider, deliberate audit some session, though out of this pass's
   own scope to do exhaustively.
7. **A real ROS window, the duplicated `MIN_SAMPLE_SIZE_FOR_PER_CLASS_*`
   constant, ADD_DROP's still-uncomputed `netRosterValuePoints`, and real
   owner (roster 9) WAIVER/ADD_DROP/FAAB outcome data** are all unchanged,
   inherited open items from Worker 1/2/3 -- none were touched this pass.
8. **Boundary property test pack V2** (Work Unit 18, per the directive's own
   numbering) was not started this pass, per this pass's own explicit
   Work Unit 13-14 assignment.
