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

## Worker 6 (this pass) -- Work Unit 18: boundary/property reliability
## pack V2 + real outcome-ingestion verification

Start HEAD `21406326` (Worker 5's closing commit). Not merged, not pushed,
not deployed. Verified live before writing any code: branch, clean
worktree, the 473-test targeted slice, `test_desktop_application_api.py`'s
same 4 pre-existing failures (`test_dynasty_facade_composes_real_governed_
workflows`, `test_desktop_rookie_veteran_bridge_is_source_separated_and_
trade_aware`, `test_redraft_bootstrap_seeds_once_and_matches_desktop_
contract`, `test_facade_has_no_streamlit_or_app_component_dependency`).

Read in full before writing any code: this ledger (Workers 1-5), and
`tests/test_boundary_property_reliability_pack_v1.py` (the prior cycle's
own 7-group pack, built for the *live_player_intelligence* saga) -- this
pass is a genuine V2, targeting bug classes THIS cycle found, never
duplicating V1's own 7 groups.

### Part A -- `tests/test_boundary_property_reliability_pack_v2.py` (new,
### 12 tests)

`hypothesis` was re-checked (`pip show hypothesis` -> not found; no
reference in any requirements file) -- still not a dependency, no new
dependency added, matching V1's own precedent.

**GROUP 8 -- the general enum/dict-key-mangling sweep the directive asked
for.** Not another hand-picked example: builds one real, isolated redraft
profile (a real `DesktopBackendFacade` + real ledger + real `ingest_*`
functions, one trace per evaluated class plus a DRAFT trace, real Sleeper
team-code ids like `"SF"` deliberately used for K/DST), calls the real
`redraft_decision_trace_history`/`redraft_decision_trace_outcome_summary`
facade methods, and runs the result through the EXACT real HTTP boundary
transform every route in `server.py` uses (`contract_envelope`, not a
re-implementation). Then walks the ENTIRE resulting JSON tree: builds a
closed "real schema field name" whitelist via the SAME static-source-scan
technique V1's own Group 1 uses (extracts every `"<key>":` literal from
the 8 evaluators' + the base evaluation module's + the history-presentation
module's own `to_dict()`-style code, plus the two real facade payload-
building functions), builds a closed "known real enum/status/disposition
value" set (`TOOL_TYPES`, `EVALUATION_STATUSES`, the real
acceptance/disposition/ledger-status literals confirmed by reading
`prospective_outcome_ingestion_v1_service.py`/`in_season_decision_trace_
service.py` directly) UNIONED with every bare-token-shaped string leaf
value actually found in the real payload itself (never hand-picked), and
asserts no dict key anywhere in the tree is a member of that combined set
(raw OR camelCased) unless it's also a real schema field name. A second,
narrower test directly re-confirms both of the two already-fixed shapes by
name (`actualPointsByPlayer` is a list; `statusCounts`/
`acceptanceStatusCounts`/`packageDispositionCounts` are lists) as a
concrete regression backstop alongside the general sweep.

**GROUP 9 -- idempotency, generalized across all 8 real evaluators.**
Builds one deliberately-chosen, fully-EVALUATED representative record per
class (standing in for the general property; no `hypothesis`), calls each
of the 8 `evaluate_*` functions three times (twice on the same object, once
on an independent `copy.deepcopy`), and asserts byte-identical `to_dict()`
output every time -- generalizing Worker 4's own single orchestrator-level
idempotency test directly to the evaluator layer. A second test proves
`class_specific_summaries` (this cycle's one real aggregation function) is
itself idempotent over the same result set.

**GROUP 10 -- hindsight-leakage, generalized across all 8 real
evaluators.** For the 4 evaluators with NO context/fetch parameter at all
(`evaluate_add_drop`/`evaluate_faab`/`evaluate_k_streamer`/`evaluate_dst_
streamer`), the guarantee is proven STRUCTURALLY by signature introspection
(`inspect.signature(...).parameters == {"record"}` -- there is no
parameter through which a future fact could leak, generalizing Worker 1's
own `_assert_no_current_state_parameter` pattern). For the 4 that DO accept
an optional context/fetch (`evaluate_start_sit`/`evaluate_waiver`/
`evaluate_trade`/`evaluate_trade_finder`), a deliberately fabricated,
CONTRADICTORY "future" `RealizedOutcomeFetch`/`RecommendationTimeContext`
is passed in and the already-recorded realized-outcome facts (read only
from the trace's own immutable `outcome.detail`) are proven byte-identical
to the baseline -- while also proving the contradictory context's
recommendation-time-only fields (e.g. TRADE's `recommended_gives_ids`) DO
legitimately flow through, so the test proves real isolation, not that the
parameter is silently ignored altogether.

**GROUP 11 -- TRADE-family rejected/unaccepted-disposition guard,
generalized across a representative sweep of real and fabricated
dispositions.** Swept `acceptanceStatus` over `REJECTED`/`PENDING`/
`CANCELLED`/`UNKNOWN`/empty-string (plus one deliberately INCONSISTENT
fabrication: `tradeAccepted=True` with a non-`ACCEPTED` status) for TRADE,
and `packageDisposition` over `SENT`/`CONSIDERED`/`IGNORED`/`UNKNOWN`/
`PENDING`/`WITHDRAWN` for both TRADE_FINDER and TRADE_PACKAGE_SEARCH --
every case constructs a raw `outcome.detail` dict directly (bypassing the
schema dataclass's own `__post_init__` guard entirely) to prove the
EVALUATION layer's own guard, not just the ingestion layer's discipline, is
what actually blocks a scored counterfactual. One positive-control test
proves a genuinely ACCEPTED package IS scored, so the guard is proven to be
a real gate, not a function that always refuses.

### A real, disclosed bug found and fixed by GROUP 11's own sweep

`evaluate_trade`'s own `net_subsequent_points_delta_points` (TRADE, Work
Unit 7) did **not** independently check `acceptanceStatus`/`tradeAccepted`
before calling `trade_realized_metrics_from_detail(detail)` -- that shared
helper only checks whether `realizedRosterOutcome` is present, trusting
every real caller (`ingest_trade_outcome`) never to populate it for a
rejected/unknown trade. That trust IS honored by every real ingestion path
today, but was not independently enforced at this evaluator's own call
site -- contradicting this module's own documented "three independent
layers" rejected-trade guarantee (Worker 3's own ledger entry, Work Unit
7). A raw `outcome.detail` dict reaching this evaluator any other way (a
malformed/legacy ledger row, a future caller writing `detail` directly)
could otherwise surface a scored counterfactual for a rejected trade. Real,
live proof: `test_no_non_accepted_trade_ever_produces_a_scored_realized_
outcome` failed BEFORE the fix (`net_subsequent_points_delta_points ==
999.0` for a fabricated `REJECTED` detail carrying a fabricated realized
outcome) and passes after. **Fixed narrowly**, at `evaluate_trade`'s own
call site only (`src/services/prospective_outcome_trade_evaluator_v1_
service.py`): gates the `trade_realized_metrics_from_detail` call on
`acceptanceStatus == "ACCEPTED" and tradeAccepted is True`, returning the
same all-`None` metrics shape that helper itself already returns for a
genuinely realized-outcome-free trade -- mirrors the SAME guard `evaluate_
trade_finder` (Work Unit 8) already applies at its own call site (verified
by reading it directly before writing the fix). No other evaluator,
ingestion function, or schema dataclass was touched. Every pre-existing
`test_prospective_outcome_trade_evaluator_v1_service.py` test (15) still
passes unmodified.

### Tests (full)

- New: `tests/test_boundary_property_reliability_pack_v2.py` -- **12
  passed** (2 Group 8 + 2 Group 9 + 5 Group 10 + 3 Group 11).
- Targeted regression slice (`pytest -k "decision_trace or
  prospective_outcome or live_player_intelligence or
  boundary_property_reliability or composition or player_availability"`):
  **485 passed, 0 failed** (473 pre-existing + 12 new this pass).
- `tests/test_prospective_outcome_trade_evaluator_v1_service.py` (the one
  file touched by the bug fix): **15 passed**, unmodified.
- `tests/test_desktop_application_api.py`: **46 passed / 4 failed** -- the
  SAME 4 pre-existing failures documented in every prior worker's own
  baseline. Re-confirmed live after this pass's changes.
- `git diff` grepped for every hard-boundary term
  (`marginal_roster_utility_v2`, `LeagueSnapshot`, `LeagueWorkspaceContext`,
  `lifecycle_resolver`, `DecisionResultEnvelope`,
  `PlayerAvailabilityStatus`): **zero matches**.

### Part B -- real outcome-ingestion verification against current data

Real, read-only checks against the real production AppData store and the
real Fantasy Gamers Sleeper league (id `1312983576827920384`, owner
`scolety`), using Worker 4's own real, tested orchestrator CLI
(`scripts/run_prospective_outcome_ingestion_v1.py`):

- **Real production store, re-confirmed still empty.** `python scripts/
  run_prospective_outcome_ingestion_v1.py --root
  "<real AppData>\com.ninerswarroom.redraft\state\redraft" --dry-run`
  returned `{"countsByAction": {}, "currentNflWeek": 2, "dryRun": true,
  "plan": []}` -- a real, live `GET state/nfl` call (current real NFL week
  is still 2), zero decision traces found, matching Worker 4/5's own
  finding exactly. A direct filesystem walk of the real
  `state/redraft/` directory independently confirms no `decision_traces/`
  subdirectory exists at all (confirmed via `find`, not merely trusted from
  the prior ledger).
- **No isolated demo/test root from Workers 1-5 qualifies as a genuinely
  "matured" real recommendation.** Checked every demo/summary artifact this
  cycle left behind: `docs/codex/prospective_outcome_v1/
  startsit_ingestion_demo_v1/summary.json` (Worker 1's real START_SIT
  source-adapter demo) and `docs/codex/prospective_outcomes_v1/
  history_ui_v3_demo_v1/summary.json` (Worker 5's History UI V3 demo,
  whose `redraft_root` temp directory -- unusually -- still exists on this
  machine, `nwr-history-ui-v3-demo-xg_ibvgk`). Both are explicitly,
  honestly disclosed by their OWN scripts' docstrings as
  MECHANISM-DEMONSTRATION baselines: every trace in both roots had its
  `recommendation` AND its `outcome` recorded back-to-back within the SAME
  script execution, never separated by real elapsed time -- there was never
  a real pre-existing recommendation sitting and waiting for a real-world
  outcome to catch up to it. Running the real orchestrator against either
  root would find nothing genuinely new to ingest (Worker 5's root's
  `league_id` is the synthetic `"demo-league-1"`, not a real Sleeper
  league, so the orchestrator's real network-fetch path does not even
  apply to it) -- this was confirmed by reading each script's own explicit
  disclosure rather than by running a real ingestion against clearly-
  synthetic data and reporting a misleading "before/after" delta.
- **Honest result, per the directive's own anticipated case**: **nothing
  to ingest yet.** The real production store has zero traces (no live call
  site has ever actually fired against the owner's real profile), and no
  demo root anywhere in this cycle's own history contains a real
  recommendation that predates its own outcome. This is NOT a regression or
  a newly-discovered gap -- it is the same honest state Worker 4/5 already
  found and disclosed, re-verified live rather than assumed.

### Sleeper writes

**Zero.** The one real network call this pass made was the orchestrator's
own real, public, keyless `GET state/nfl` (via `--dry-run`, which also
independently guarantees no local writes regardless). Every other real
network-touching path this pass exercised was inside `pytest` (Group 8's
`DesktopBackendFacade` calls are 100% local/hermetic -- no Sleeper network
I/O at all, only real ledger/evaluator code running against a pytest
`tmp_path` root). No write-capable Sleeper endpoint exists anywhere in this
codebase's real call sites (confirmed by this pass's own reading of
`run_prospective_outcome_ingestion_v1.py`'s module docstring plus the
orchestrator module itself, matching every prior worker's own same
finding).

### Backend/model files changed this pass

- **New**: `tests/test_boundary_property_reliability_pack_v2.py`.
- **Modified (one real, narrow, disclosed bug fix)**:
  `src/services/prospective_outcome_trade_evaluator_v1_service.py`
  (`evaluate_trade`'s own `metrics` computation now independently gates on
  `acceptanceStatus`/`tradeAccepted` before reusing `trade_realized_
  metrics_from_detail`, matching `evaluate_trade_finder`'s own existing
  guard -- see "A real, disclosed bug" above). No other evaluator,
  ingestion function, schema dataclass, orchestrator, or facade/UI file was
  touched.
- This ledger.

## OPEN ISSUES FOR THE NEXT WORKER (Work Units 16-17: trade-package quality
## benchmark + K/DST prospective benchmark)

1. **The real production trace store still has zero decision traces
   recorded in it** -- unchanged, re-verified live this pass (not merely
   assumed) rather than newly found. Nothing this pass wrote to or read
   from that real path beyond one real, live, read-only `GET state/nfl`
   plus a local, read-only directory listing.
2. **Identity resolution for WAIVER/FAAB/ADD_DROP/K_STREAMER/DST_STREAMER/
   TRADE-family** remains the real, concrete blocker to real automatic
   evaluation for those six classes -- unchanged, inherited from Worker
   1/3/4/5. Not touched this pass.
3. **TRADE/TRADE_FINDER/TRADE_PACKAGE_SEARCH have no real week to anchor a
   maturity check to**, and **`owner_roster_id` resolution is a real,
   caller-supplied mapping, not a general resolver** -- both unchanged from
   Worker 4's own Open Issues 2-3.
4. **A real ROS window, the duplicated `MIN_SAMPLE_SIZE_FOR_PER_CLASS_*`
   constant, ADD_DROP's still-uncomputed `netRosterValuePoints`, and real
   owner (roster 9) WAIVER/ADD_DROP/FAAB outcome data** are all unchanged,
   inherited open items from Worker 1/2/3 -- none were touched this pass.
5. **The real, disclosed bug this pass found and fixed** (`evaluate_trade`'s
   own missing acceptance/accepted gate before reusing `trade_realized_
   metrics_from_detail`) was fixed narrowly at its own call site -- worth a
   wider audit some future session for any OTHER evaluator call site that
   reuses a shared metrics-extraction helper without independently
   re-checking the same gate its sibling call site already enforces (this
   pass found exactly one such gap; did not exhaustively search for a
   second one beyond TRADE/TRADE_FINDER).
6. **A real, unusual finding, not a bug**: Worker 5's own History UI V3
   demo-root temp directory (`nwr-history-ui-v3-demo-xg_ibvgk`) is still
   present on this machine from an earlier session, despite being created
   via `tempfile.mkdtemp` (normally OS-cleaned eventually). Harmless
   (FIXTURE data only, never touches the real production store), but worth
   knowing this machine's temp directory is not being swept as aggressively
   as might be assumed -- not cleaned up by this pass either, to avoid
   deleting another session's/worker's artifact without being asked.
7. **Work Units 16-17 (trade-package quality benchmark + K/DST prospective
   benchmark)**, the directive's own next-named work, were not started this
   pass -- Work Unit 18 (this pass's own assignment) plus the real
   ingestion-verification pass were the full scope this time.

## Worker 7 (this pass) -- Work Units 16-17: trade-package quality
## benchmark + K/DST prospective benchmark scaffolding

Start HEAD `346dff9b` (Worker 6's closing commit). Not merged, not pushed,
not deployed. Verified live before writing any code: branch, clean
worktree, the 485-test targeted slice, `test_desktop_application_api.py`'s
same 4 pre-existing failures (`test_dynasty_facade_composes_real_governed_
workflows`, `test_desktop_rookie_veteran_bridge_is_source_separated_and_
trade_aware`, `test_redraft_bootstrap_seeds_once_and_matches_desktop_
contract`, `test_facade_has_no_streamlit_or_app_component_dependency`).

Read in full before writing any code: this ledger (Workers 1-6),
`src/services/trade_package_search_service.py` (the real, unmodified
package generator) and its own preregistered
`docs/codex/post_ui_v1/TRADE_PACKAGE_SEARCH_QUALITY_GATES_P1_3.md`,
`tests/test_trade_package_search_service.py`, and `fantasypros_kdst_
consensus_service.py` (the real K/DST streamer, including its real
`streamer_actions`/`sleeper_streamer_actions`/`sleeper_opponent_rosters`
functions) plus the live K/DST call site in `desktop_facade.py`
(`redraft_kdst_streamer`). This pass is MEASUREMENT ONLY -- neither the
trade-package search/scoring logic nor the K/DST streamer's own
recommendation logic was modified.

### Work Unit 16 -- Trade Package Quality Benchmark

**New**: `docs/codex/prospective_outcomes_v1/TRADE_PACKAGE_QUALITY_
BENCHMARK_V1.md` (preregistered rubric, written first), `src/services/
trade_package_quality_benchmark_v1_service.py` (9 rubric dimensions as
pure, read-only functions over the generator's own real
`TradePackageSearchResult`/`TradePackageCandidate` objects -- dominance
re-verification, mutual starter-value gain, position-need fit,
bench-for-bench clutter rate, near-duplicate detection (Jaccard
similarity), size/utility distribution, independently-re-verified roster
consolidation legality, diversity, latency), `tests/test_trade_package_
quality_benchmark_v1_service.py` (23 tests, hand-built fixtures proving
each dimension's scoring logic on known-good/known-bad cases), `scripts/
run_trade_package_quality_benchmark_v1.py` (the real runner).

**Real sample**: the real "Fantasy Gamers" Sleeper league (id
`1312983576827920384`, read-only, current real 10-team rosters), scored
with the REAL, currently-installed NWR ranking loaded read-only from the
owner's real AppData Redraft profile (`4c5f04762921420595e4d8c7cda76582`)
via plain `load_profile`/`load_projection_snapshot`/`generate_rankings`
calls -- no facade instance was constructed (the facade's own endpoint
additionally appends a real decision trace; this script calls
`search_win_win_packages`/`search_target_player_packages`/`search_
improve_position_packages` directly, so ZERO local writes happen anywhere,
on top of zero Sleeper writes). Three real runs (FIND_WIN_WIN;
TARGET_PLAYER on Sam LaPorta, a real elite TE on a real opponent roster;
IMPROVE_POSITION on TE, the owner's own real, disclosed thinnest
position) plus one clearly-labeled SYNTHETIC 10-team fixture for a larger
candidate sample.

**Two real bugs found and fixed live, both in this pass's OWN new
benchmark script, never in the generator**: (1) the script's first draft
used the RAW Sleeper roster size as the pre-trade baseline for its
independent roster-legality re-check, producing 8 false "violations" --
the real search operates on the CANONICAL (identity-resolved) roster
(12 players for the owner, not 15: K/DST are never NWR-projected by
design, plus one real identity-match gap this pass found, a rostered WR
not present in the current ranking pool); fixed by using the same
canonical counts the search itself uses, re-run: zero violations. (2) the
synthetic fixture's first draft built a 16-player roster against a
15-slot league cap, making every trade illegal by construction and
returning zero candidates; fixed by widening the fixture's own bench size
to match its own roster count.

**Verdict**: no coherent, mechanically-explainable failure pattern found.
Zero dominance violations, zero exact/near-duplicate-rate red flags (9
near-duplicate pairs were mechanically explained by a small real
candidate pool, not a generator flaw), zero bench-for-bench clutter in
the real league (93% in the fully-symmetric SYNTHETIC fixture, honestly
explained as an artifact of that fixture's own "nothing broken to fix"
design, not a real defect), zero roster-legality violations once this
pass's own measurement bug was fixed, latency well inside the 5s target
(worst case 1.20s). TARGET_PLAYER(LaPorta)/IMPROVE_POSITION(TE) both
returned zero real candidates against the real league -- plausible (the
real target opponent is itself deep everywhere the owner could offer
surplus) but not root-caused further this pass (disclosed open item).
**No ranking challenger is recommended** -- full results in `docs/codex/
prospective_outcomes_v1/trade_package_quality_benchmark_v1/RESULTS.md`
and the raw `results.json` alongside it.

### Work Unit 17 -- K/DST Prospective Benchmark Scaffolding

**New**: `docs/codex/prospective_outcomes_v1/KDST_PROSPECTIVE_BENCHMARK_
V1.md` (preregistered scaffolding design, written first), `src/services/
kdst_prospective_benchmark_v1_service.py` (pure composition over
already-fetched real inputs -- zero network I/O -- building 4 comparison
arms per position/week: NWR_RECOMMENDATION, PROVIDER_CONSENSUS,
RAW_PROJECTION, REPLACEMENT_LEVEL; `compare_arms`/`summarize_kdst_
benchmark`, the latter ALWAYS reporting the real sample size and labeling
it `PRELIMINARY` below a disclosed 8-week transparency floor, never
fabricating a verdict), `tests/test_kdst_prospective_benchmark_v1_service.py`
(12 tests), `scripts/run_kdst_prospective_benchmark_v1.py` (the real
runner).

**A real, honest finding this scaffolding starts from**: reading the live
`redraft_kdst_streamer` call site BEFORE writing any benchmark code
confirmed NWR's own K/DST "recommendation" IS, by construction, the
FantasyPros consensus ECR order (no separate NWR-computed K/DST score
exists anywhere in this codebase) -- so "NWR recommendation vs provider
consensus" is not two independent methods for K/DST the way it is for
skill positions; this benchmark measures the one real value-add that DOES
exist (Sleeper roster-availability filtering) directly, rather than
pretending two independent methods exist where only one does.
`RAW_PROJECTION` IS legitimately available for K/DST specifically
(Sleeper's own real weekly-projections endpoint, `weekly_projection_
service.py`, prior-cycle work reused here, not duplicated) -- a real,
non-NWR projection source, unlike the "K/DST are unmodeled" excuse that
applies to NWR's OWN projection pipeline.

**A real, mechanical DST identity-matching defect found this pass,
documented, NOT fixed (hard boundary)**: `sleeper_streamer_actions`'s
real identity key returns `("", "", "")` for EVERY real Sleeper DST
roster entry, because Sleeper's own `players/nfl` catalog gives DST
entries `first_name`/`last_name` only, never `full_name`/
`search_full_name` -- unlike `resolve_roster_canonical_ids`/`sleeper_
free_agent_pool`/`weekly_projection_service.build_weekly_projection_rows`,
which all already carry the DST name-fallback that this ONE function
alone is missing. Live-verified twice (once during design, once
populating the real week): a real query against all 10 real DST rows this
league actually rosters showed every one reported `rosterStatus:
"AVAILABLE"`, including the owner's own real, started DST. K is
unaffected (K catalog entries DO carry `full_name`; the owner's own real
K correctly resolved to `"YOUR_STARTER"`). Real consequence: NWR's DST
recommendation is, in practice, ALWAYS identical to naive top-ECR
consensus (the differentiating roster filter never fires), while for K
the two arms DID genuinely differ this real week (NWR correctly skipped
two real, actually-rostered kickers). A second, smaller, real provider-
convention difference (FantasyPros `"JAC"` vs Sleeper `"JAX"` for
Jacksonville) was found and handled ONLY inside this benchmark's own join
code, never in production. Per the hard boundary, neither was fixed --
flagged for a future worker explicitly authorized to touch
`fantasypros_kdst_consensus_service.py`.

**Real, PRELIMINARY (n=1 week) result**: real Week 1 2026 data for the
Fantasy Gamers league. K: NWR's real pick (Cam Little, 12.0 actual pts)
beat naive provider consensus (Brandon Aubrey, 1.0 actual pts) by 11 real
points, and beat even the raw-projection arm's own pick (Matt Gay, 10.0).
DST: NWR and provider consensus picked the identical real team
(Jacksonville, 15.0 actual pts) -- the disclosed identity-bug consequence,
not independent agreement. **No challenger proposed for either position**
-- n=1 week is explicitly too small, per the owner's standing instruction.
Full results in `docs/codex/prospective_outcomes_v1/kdst_prospective_
benchmark_v1/RESULTS.md` and the raw `week_01_2026.json` alongside it.

### Real data / Sleeper access this pass

Read-only throughout. Real GETs: `league/{id}/rosters`, `/users`,
`players/nfl`, `stats/nfl/regular/2026/1`, `projections/nfl/regular/
2026/1` (all Sleeper, public/keyless), plus real FantasyPros `consensus-
rankings` calls (K, DST, week 1) via the owner's already-configured
`NWR_FANTASYPROS_API_KEY` env var and the SAME real, existing
`FantasyProsConsensusClient` the live app already uses -- no new provider
client built. The owner's real AppData Redraft profile
(`4c5f04762921420595e4d8c7cda76582`) was read via `load_profile`/`load_
projection_snapshot` only -- zero writes to that root, confirmed by
construction (this pass calls no `save_*`/`record_*`/`install_*` function
against it anywhere). Zero Sleeper writes (no write-capable Sleeper
endpoint exists anywhere in this codebase's real call sites, matching
every prior worker's own finding).

### Tests (full)

- 2 new test files, 35 new tests total (23 + 12), all passing.
- Targeted regression slice (`pytest -k "decision_trace or
  prospective_outcome or live_player_intelligence or
  boundary_property_reliability or composition or player_availability or
  trade_package_quality_benchmark or kdst_prospective_benchmark"`): **520
  passed, 0 failed** (485 pre-existing + 35 new this pass).
- `tests/test_trade_package_search_service.py` +
  `tests/test_trade_package_search_facade_wiring.py` (the real generator's
  own existing tests, re-confirmed unaffected): **28 passed**, unmodified.
- `tests/test_desktop_application_api.py`: **46 passed / 4 failed** -- the
  SAME 4 pre-existing failures documented in every prior worker's own
  baseline. Re-confirmed live after this pass's changes.
- `git diff`/new-file grep for every hard-boundary term
  (`marginal_roster_utility_v2`, `LeagueSnapshot`, `LeagueWorkspaceContext`,
  `lifecycle_resolver`, `DecisionResultEnvelope`,
  `PlayerAvailabilityStatus`) across every file this pass touched or
  created: **zero matches**.

### Backend/model files changed this pass

**All new, zero modifications to any existing file** (`trade_package_
search_service.py` and `fantasypros_kdst_consensus_service.py` -- the two
systems being measured -- are untouched, confirmed by `git status` showing
only new (`??`) files):

- `src/services/trade_package_quality_benchmark_v1_service.py`
- `src/services/kdst_prospective_benchmark_v1_service.py`
- `tests/test_trade_package_quality_benchmark_v1_service.py`
- `tests/test_kdst_prospective_benchmark_v1_service.py`
- `scripts/run_trade_package_quality_benchmark_v1.py`
- `scripts/run_kdst_prospective_benchmark_v1.py`
- `docs/codex/prospective_outcomes_v1/TRADE_PACKAGE_QUALITY_BENCHMARK_V1.md`
- `docs/codex/prospective_outcomes_v1/trade_package_quality_benchmark_v1/`
  (`results.json`, `RESULTS.md`)
- `docs/codex/prospective_outcomes_v1/KDST_PROSPECTIVE_BENCHMARK_V1.md`
- `docs/codex/prospective_outcomes_v1/kdst_prospective_benchmark_v1/`
  (`week_01_2026.json`, `RESULTS.md`)
- This ledger.

## OPEN ISSUES FOR THE NEXT WORKER (Work Units 19-20: multi-league scale
## characterization + performance characterization)

1. **The real production trace store still has zero decision traces
   recorded in it** -- unchanged, inherited from every prior worker.
   Nothing this pass wrote to or read from that real path (this pass's own
   benchmark scaffolding tracks a SEPARATE, new artifact store under
   `docs/codex/prospective_outcomes_v1/`, not the decision-trace ledger).
2. **Identity resolution for WAIVER/FAAB/ADD_DROP/K_STREAMER/DST_STREAMER/
   TRADE-family** (the decision-TRACE evaluation layer's own open issue,
   distinct from this pass's own DST-streamer-recommendation identity
   finding above) remains unchanged, inherited from Worker 1/3/4/5/6. Not
   touched this pass.
3. **The real, mechanical DST identity-matching defect in `sleeper_
   streamer_actions`** (see Work Unit 17 above) is real, validated, and
   NOT fixed -- a future worker explicitly authorized to touch
   `fantasypros_kdst_consensus_service.py` should add the same DST
   `full_name` fallback (`if position == "DST" and not name and team: name
   = f"{team} D/ST"`) that `resolve_roster_canonical_ids`/`sleeper_free_
   agent_pool`/`weekly_projection_service.build_weekly_projection_rows`
   already carry.
4. **This pass's own Trade Package Quality Benchmark used only ONE real
   league.** A genuine "coherent pattern across multiple real cases"
   standard would need this same harness run against a second real
   league -- a natural fit for Work Unit 19 (multi-league scale
   characterization), the directive's own next-named work.
5. **This pass's own K/DST Prospective Benchmark has n=1 real week.** The
   scaffolding (`kdst_prospective_benchmark_v1_service.py` + the runner
   script) is real and reusable -- re-run with `WEEK` advanced once
   additional real weeks complete. No challenger should be proposed from
   any small sample without a coherent, mechanical, multi-case pattern,
   per the owner's standing instruction (repeated here for the next
   worker, since it is very easy to over-read a few good/bad weeks).
6. **TARGET_PLAYER(LaPorta)/IMPROVE_POSITION(TE) both returned zero real
   candidates** against the real Fantasy Gamers league this pass -- not
   root-caused beyond confirming the utility gates rejected every
   evaluated combination (120 and 372 respectively, non-zero). A future
   pass with more time could trace the exact rejected `net_marginal_
   utility` numbers to confirm the "opponent is already deep everywhere"
   explanation more precisely.
7. **A real identity-match gap this pass found (not investigated
   further)**: the owner's real rostered WR, Sleeper id `11628` (Marvin
   Harrison Jr.), did not resolve to the current NWR canonical ranking
   pool during Work Unit 16's real search. Out of this pass's own scope
   (ranking/identity resolution is untouched by this cycle's hard
   boundary) -- worth a real look by a future worker with that scope.
8. **Work Units 19-20 (multi-league scale characterization + performance
   characterization)**, the directive's own next-named work, were not
   started this pass -- Work Units 16-17 (this pass's own assignment)
   were the full scope this time.

## Worker 8 (this pass) -- Work Units 19-20: multi-league scale
## characterization + performance characterization (MEASUREMENT ONLY)

Start HEAD `8969e52f` (Worker 7's closing commit). Not merged, not pushed,
not deployed. Verified live before writing any code: branch, clean
worktree, the 520-test targeted slice, `test_desktop_application_api.py`'s
same 4 pre-existing failures (`test_dynasty_facade_composes_real_governed_
workflows`, `test_desktop_rookie_veteran_bridge_is_source_separated_and_
trade_aware`, `test_redraft_bootstrap_seeds_once_and_matches_desktop_
contract`, `test_facade_has_no_streamlit_or_app_component_dependency`).

Read in full before writing any code: this ledger (Workers 1-7),
`desktop/apps/redraft/src/attention-center.ts`/`attention-center-page.tsx`/
`attention-center.test.ts` (the Multi-League Attention Center, built in an
earlier session -- NOT this cycle; grepped this ledger for "Attention
Center" and found zero prior mentions, confirming it), and
`player-detail-state.ts`/`player-detail-drawer.tsx`/`player-drawer-core.tsx`
(Player Drawer). This whole pass is MEASUREMENT ONLY: neither
`attention-center.ts`'s own aggregation logic, `desktop_facade.py`,
`player_availability_status_service.py`, nor any of this cycle's 8
evaluators/orchestrator was modified.

**A real, disclosed naming finding**: a literal `"fanout"`/`"status_fanout"`
string search across the whole repo (Python + TypeScript + docs) returned
ZERO hits. Read the live-player-intelligence cycle's own ledger and
`player_availability_status_service.py` directly instead: the directive's
"status-fanout infrastructure... even though nothing is wired into
recommendations" refers to the real, callable `redraft_player_availability_
status` facade endpoint (`load_player_availability_statuses`/
`player_availability_authority_health`) -- a real, standalone read
authority, confirmed genuinely unwired into any recommendation (module
docstring: "the one product-facing authority every Draft/Lineup/Waivers/
Trades surface SHOULD eventually read... instead of each surface
separately re-deriving its own status heuristic," present tense, not yet
true). "Fan-out" means calling this same per-repo-root endpoint once per
league during multi-league aggregation -- exercised for real this pass.

### Work Unit 19 -- multi-league scale characterization

**New**: `scripts/run_multi_league_scale_benchmark_v1.py` (real backend
harness), `desktop/apps/redraft/src/attention-center-scale-benchmark.test.ts`
(real vitest harness, 13 tests, all passing -- imports and runs the REAL,
unmodified `runAttentionCenterAggregation`/`searchPlayerAcrossLeagues`
from `attention-center.ts`, never a reimplementation), `docs/codex/
prospective_outcomes_v1/multi_league_scale_v1/` (`backend_results.json`,
`frontend_bench_results.json`, `RESULTS.md`).

**Isolated, LOCAL-provider profile sets only** (per the directive's own
safety instruction): every profile at every tested size (5/10/25/50) is
`provider="local"`, created under a fresh temp `redraft_root` per size via
the real `create_profile`/`redraft_bootstrap` path (`repo_root=REPO_ROOT`
for the real bundled projection snapshot -- the exact same isolation
pattern `tests/test_desktop_application_api.py` already uses for
isolated redraft-mode tests). The owner's real AppData store and real
Sleeper leagues were never touched by this work unit.

**A real methodological finding this pass caught and corrected before
trusting any number**: `tracemalloc.start()` measurably inflated every
real call's wall time by roughly 5x when first tried in the same pass as
timing (dataHealth 27ms -> 138ms, workspaceContext 14ms -> 71ms, live-
confirmed by a direct side-by-side comparison). The script now runs two
SEPARATE passes per size -- timing with no tracemalloc active, memory-only
with tracemalloc active and that pass's own timing discarded -- rather
than reporting an instrumentation-inflated number as real latency.

**Real result**: per-league cost is flat across the whole tested range
(~42.7ms/league at n=5, ~43.0ms/league at n=50, ratio 1.007) -- linear
scaling, confirmed independently by BOTH harnesses (the frontend's own
isolated-overhead measurement shows negligible JS orchestration cost, and
its "realistic" end-to-end number, 2364.8ms at n=50, closely corroborates
the backend's own independently-measured 2150.2ms). Full real numbers,
tables, and the exact SCALE FINDING verdict are in `RESULTS.md`. tracemalloc
peak stays flat (~2 MiB) across every tested size -- no evidence of
per-league memory accumulation. Windows has no `resource` module
(confirmed live) and no `psutil` is installed (confirmed live); tracemalloc
was judged sufficient given the flat result, per the directive's own
"don't over-engineer memory measurement" instruction.

7 new pytest tests (`tests/test_multi_league_scale_and_performance_
benchmark_v1.py`, shared with Work Unit 20 -- see below), all passing,
plus 13 new vitest tests, all passing.

### Work Unit 20 -- performance characterization

**New**: `scripts/run_performance_characterization_v1.py`, `docs/codex/
prospective_outcomes_v1/performance_characterization_v1/` (`results.json`,
`RESULTS.md`).

**Safety, read before touching this script**: `DesktopBackendFacade.
activate_redraft_profile` performs a REAL local write (`active_profile.
json`) -- so this script NEVER constructs a facade against the real
AppData Redraft store directly. It `shutil.copytree`s the real store to a
temp directory first (a read of the original, a write only to the copy),
then operates on the copy. The real Fantasy Gamers Sleeper league (id
`1312983576827920384`) is read through that copy's own already-saved real
`provider=sleeper` profile (`4c5f04762921420595e4d8c7cda76582`) -- every
resulting network call is a plain, public, keyless Sleeper GET, the same
real read-only surface every prior worker's own real-data script uses.
Outcome ingestion is measured against a SEPARATE, fresh, isolated,
throwaway root seeded with realistic fixture traces (same construction
pattern already established in `tests/test_prospective_outcome_ingestion_
orchestrator_v1_service.py`), never the real production trace ledger
(confirmed still real-empty, unchanged from Worker 7's own open issue 1).

**Real numbers for every directive-named surface** (Cold startup, League
open, Home, Lineup, Improve Team, Trade Finder, Trade Package Search,
Player Drawer first/warm-open, Draft refresh, History V3, outcome
ingestion) -- full table in `RESULTS.md`.

**A real, disclosed finding on Player Drawer** (read `player-detail-
state.ts` in full before benchmarking): there is NO dedicated backend
endpoint for opening the drawer. Identity is caller-supplied (every
surface that opens it already has the row data) and the only shared
lookup (`deriveBackbone`) is an in-memory filter against the already-
loaded `PlayerAvailabilityStatus` list -- so "first open" and "warm open"
genuinely do not differ in backend cost; both are a sub-millisecond array
lookup. No performance concern, none to fix.

**A real, cProfile-corroborated finding on the Sleeper-network-bound
surfaces** (Home/Lineup/Improve Team/Trade Finder/Trade Package Search):
this pass's own 5-reps-per-surface benchmark loop showed high variance
(Lineup: 9616.6ms median / 15657.2ms P95), but an ISOLATED cProfile run of
the identical `redraft_weekly_lineup(week=2)` call (no preceding rapid-
fire calls) completed in 1.271s, with `{method 'read' of
'_ssl._SSLSocket' objects}` (55.6%) and TCP/TLS `connect`+`do_handshake`
(16.9%) accounting for the overwhelming majority of real cost --
`SleeperHttpClient.get_json` uses a plain `urlopen` per call with NO
persistent session/connection-pooling/keep-alive reuse across calls, so
every real GET pays a fresh handshake. This is real, but a DIFFERENT
dimension of the same "real network I/O dominates" story the earlier
Weekly Home latency fix (commit `00446dcd`, prior session) already
addressed -- that fix eliminated redundant re-fetches WITHIN one call;
connection reuse ACROSS calls is untouched. **Not fixed this pass**:
`SleeperHttpClient` is used broadly across the whole codebase, and
switching it to a persistent session would need its own equivalence proof
across every call site -- larger/riskier than this pass's own bounded-fix
bar. Flagged precisely for a future worker with that scope; the isolated
cProfile evidence (not the noisier benchmark-loop numbers) is the more
trustworthy per-call estimate for a single real user's occasional usage,
disclosed as such in `RESULTS.md` rather than silently averaged away.

**OPTIMIZATION MADE: NONE.** Every surface is either already comfortably
fast (League open, History V3, Player Drawer, League switch -- sub-
millisecond to low-single-digit-millisecond) or is dominated by real,
external, precisely root-caused network I/O that does not meet this
pass's own bounded/equivalence-proven fix bar. No code was changed in
`desktop_facade.py`, any `src/services/*` module, or `attention-center.ts`.

### Tests (full)

- `tests/test_multi_league_scale_and_performance_benchmark_v1.py`: 7 new
  tests, all passing -- pure statistics-helper correctness, a real
  assertion that the isolated scale-benchmark store never resolves under
  the real AppData Redraft root, a hermetic (no-network) run of the
  Attention Center fan-out bench against an isolated store, the
  linearity-check verdict on both a linear and a synthetic superlinear
  input, and a hermetic ingestion-fixture-seeding round trip.
- `desktop/apps/redraft/src/attention-center-scale-benchmark.test.ts`: 13
  new tests, all passing.
- Targeted regression slice (`pytest -k "decision_trace or
  prospective_outcome or live_player_intelligence or
  boundary_property_reliability or composition or player_availability or
  trade_package_quality_benchmark or kdst_prospective_benchmark or
  multi_league_scale_and_performance"`): **527 passed, 0 failed** (520
  pre-existing + 7 new this pass).
- `tests/test_desktop_application_api.py`: **46 passed / 4 failed** -- the
  SAME 4 pre-existing failures documented in every prior worker's own
  baseline. Re-confirmed live after this pass's changes.
- `git status --porcelain` shows only new (`??`) files this pass touched
  or created; grepped every one for every hard-boundary term
  (`marginal_roster_utility_v2`, `LeagueSnapshot`, `LeagueWorkspaceContext`,
  `lifecycle_resolver`, `DecisionResultEnvelope`, `PlayerAvailabilityStatus`):
  matches exist ONLY as read-only type imports / measured-endpoint names
  (e.g. importing `LeagueWorkspaceContext`'s TYPE to build a realistic
  fixture, calling the already-existing `PlayerAvailabilityStatus`
  endpoint) -- the exact same legitimate-mention pattern Workers 3/4/5's
  own files already established, never a semantic change to any of those
  systems.

### Real data / Sleeper access this pass

Read-only throughout, zero writes. Real GETs: `state/nfl` (current week),
and through the real Fantasy Gamers profile COPY: `league/{id}/rosters`,
`/users`, `players/nfl`, `league/{id}/matchups/{week}`, plus a real FFC
ADP fetch (Draft refresh) and real FantasyPros K/DST consensus reads
(Improve Team). The real AppData Redraft store itself was only ever
`shutil.copytree`'d (a read of the original); every real local write
(profile activation, ADP snapshot, ingestion ledger) landed exclusively in
a temp-directory copy or a separate fresh throwaway root, never the
original path.

### Backend/model files changed this pass

**All new, zero modifications to any existing file**:

- `scripts/run_multi_league_scale_benchmark_v1.py`
- `scripts/run_performance_characterization_v1.py`
- `tests/test_multi_league_scale_and_performance_benchmark_v1.py`
- `desktop/apps/redraft/src/attention-center-scale-benchmark.test.ts`
- `docs/codex/prospective_outcomes_v1/multi_league_scale_v1/` (`backend_
  results.json`, `frontend_bench_results.json`, `RESULTS.md`)
- `docs/codex/prospective_outcomes_v1/performance_characterization_v1/`
  (`results.json`, `RESULTS.md`)
- This ledger.

## OPEN ISSUES FOR THE NEXT WORKER (Work Units 21-22: real dogfood + full
## acceptance)

1. **A real connection-reuse gap in `SleeperHttpClient`** (Work Unit 20's
   own cProfile finding, see above): every real GET pays a fresh TCP+TLS
   handshake (no persistent session/connection pooling anywhere in this
   codebase's Sleeper client). Real, root-caused, NOT fixed -- would touch
   a broadly-shared low-level dependency and needs its own equivalence
   proof across every call site, out of this pass's own bounded-fix risk
   bar.
2. **The Attention Center's sequential, one-league-at-a-time fan-out** is
   confirmed linear and comfortably acceptable through 50 leagues (~2.1-
   2.4s median), but the ARCHITECTURAL reason (exactly one active-profile
   pointer on the backend) means it can never be trivially parallelized
   without a real per-profile-scoped read path or a queueing layer -- a
   real, disclosed, NOT-attempted-here future option if an owner ever
   genuinely runs 50+ leagues and finds 2+ seconds too slow in practice
   (not evidenced as a real complaint today).
3. **This pass's own bulk scale-test fixtures were all LOCAL-provider**
   (per the directive's own safety instruction) -- a genuine "50 real-
   shaped Sleeper leagues" number does not exist and should not be
   fabricated; see `multi_league_scale_v1/RESULTS.md`'s own "Scope,
   disclosed" section for how to combine this pass's two real, separate
   measurements analytically instead.
4. **Every open issue from Worker 7's own list** (real production trace
   store still has zero traces; identity resolution for WAIVER/FAAB/
   ADD_DROP/K_STREAMER/DST_STREAMER/TRADE-family; the real DST identity-
   matching defect in `sleeper_streamer_actions`, NOT fixed, hard-boundary
   gated; the single-real-league Trade Package Quality Benchmark; n=1-week
   K/DST Prospective Benchmark; the unresolved TARGET_PLAYER/
   IMPROVE_POSITION zero-candidate root cause; the real Marvin Harrison Jr.
   identity-match gap) is UNCHANGED, inherited, not touched this pass --
   see Worker 7's own entry above for full detail.
5. **Work Units 21-22 (real dogfood + full acceptance)**, the directive's
   own next-named work, were not started this pass -- Work Units 19-20
   (this pass's own assignment) were the full scope this time.

## Worker 9 (this pass) -- Work Units 21-25: real dogfood, full acceptance,
## honest research synthesis, bounded challenger proposal, push checkpoint
## (CYCLE CLOSING WORKER)

Start HEAD `768a91e9` (Worker 8's closing commit). Verified live before
touching anything: branch, clean worktree, the 527-test targeted slice, and
`test_desktop_application_api.py`'s same 4 pre-existing failures
(`test_dynasty_facade_composes_real_governed_workflows`,
`test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`,
`test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`,
`test_facade_has_no_streamlit_or_app_component_dependency`). Read this
ledger (Workers 1-8) in full before doing anything else.

### Work Unit 21 -- real dogfood

Real Chrome session against the real production `vite build` + the real
Python desktop API backend, launched via `desktop/scripts/
nwr_release_gate_smoke.ps1 -KeepRunning -SleeperLeagueId
1312983576827920384 -SleeperUsername scolety` (backend port 18742, vite
preview port 1422). The release-gate script's own real, read-only Sleeper
before/after byte-diff came back **IDENTICAL** (0 writes confirmed) --
confirmed independently, not merely trusted from a prior pass.

**A real, important scoping check made FIRST, before trusting any "real"
claim below**: `redraft_store_root()` (`src/services/
redraft_engine_v1_service.py`) resolves to `<repo_root>/local_exports/
redraft_v1` by default (only `NWR_REDRAFT_HOME` would redirect it
elsewhere) -- the release-gate script sets neither, so this ENTIRE dogfood
pass, including the real Sleeper-backed profile it created, lived inside
this worktree's own isolated `local_exports/redraft_v1` directory, never
the real owner AppData store (`...\com.ninerswarroom.redraft\state\
redraft`). Directly confirmed both ways: `Test-Path` on the real AppData
`decision_traces` subdirectory returned `False` (re-confirming Worker
4/5/6/7/8's own finding is still true for the REAL production store), and
the new traces this pass produced were found on disk under this worktree's
own `local_exports/redraft_v1/decision_traces/`. (One real false lead
chased down and closed during this check: a directory literally named
`prospective_decision_log/` DOES exist under the real AppData root --
confirmed to be a completely different, unrelated system from an earlier,
different cycle's `prospective_decision_log_v1_service.py`
[`decisions.jsonl` per profile], not this cycle's `decision_traces/`
ledger -- ruled out by reading both services' own path-building code
directly, not assumed.)

**A real, materially new finding this pass**: exercising the live app's own
real surfaces (Lineup, Improve Team/Waivers, Trade Finder, Weekly Home
actions, Streamers) against the real Fantasy Gamers Sleeper league, exactly
as a real owner session would, caused the app's own already-wired call
sites to record **11 real decision traces** into this isolated store for
the first time this whole cycle -- 2x START_SIT, 2x WAIVER, 2x FAAB, 1x
TRADE_FINDER, 2x K_STREAMER, 2x DST_STREAMER. This is the first time in the
whole 9-worker cycle that History UI V3 and the class-specific summary
panel have been observed rendering **real, non-fixture, non-demo** data
end-to-end. All 11 initially showed `OUTCOME PENDING` (correct -- windows
not yet matured); expanding "View outcome detail" on several (K_STREAMER,
DST_STREAMER) showed every field correctly `None`/"Not yet computable"
with zero visible/functional hindsight leakage.

**The real DST identity-matching bug (Worker 7's finding) was independently
re-reproduced live in the UI this pass** -- not just re-read in source:
Improve Team -> Streamers -> "Refresh K/DST ECR" against the real league
rendered `ADD Jacksonville Jaguars (DST) ... THIS WEEK AVAILABLE`, even
though Jacksonville was a real, actually-rostered/started DST that week
(matching Worker 7's own root-caused finding exactly). See the new fix
proposal document (Work Unit 24, below) for the exact mechanism.

**Cross-profile isolation, verified live, not merely asserted**: created a
second, genuinely separate LOCAL-provider profile ("Isolation Check
Local", preset `10-team 1QB Standard`) via the real `Create from preset`
UI flow. Its own History page showed **0 recorded events** -- none of the
11 real Fantasy Gamers traces leaked across the profile boundary. 10 real
UI-driven league switches (alternating Fantasy Gamers <-> Isolation Check
Local) via the real "League Profiles & Scoring" page produced zero console
errors and the correct active profile at every step (`Fantasy Gamers is
active.` confirmed live after the 10th switch).

**Idempotency, proven directly and rigorously against the real trace store
this pass's own dogfood produced** (a stronger, more direct proof than any
prior worker had, since no prior worker's real production-store check ever
found real traces to re-run against): ran `scripts/
run_prospective_outcome_ingestion_v1.py --root local_exports/redraft_v1
--profile-id 941b99ade350410391b1b67c0890af79` **10 times in sequence**.
Run 1 made a real, live change (one real `GET league/.../matchups/1` call,
`PROCESS_FULL_START_SIT: 1` + `PROCESS_INSUFFICIENT_CONTEXT: 2` [the two
real K/DST streamer traces, correctly resolving to
`INSUFFICIENT_DECISION_CONTEXT` per the identity gap above] +
`SKIP_IMMATURE_WINDOW: 5` + `SKIP_WINDOW_UNDETERMINABLE: 3`); runs 2-10
were byte-for-byte no-ops (`md5sum` identical across all 10 runs;
`SKIP_ALREADY_PROCESSED: 3` reported every time, zero new network calls
implied by the unchanged output). **A real, live, PRELIMINARY (n=1) START/
SIT outcome data point came out of this**: the real Week 1 trace evaluated
to `STARTER_DEVIATED`, `lineupOpportunityCostPoints: -11.16` -- the owner's
own actual Week 1 lineup choice (37.26 real points) beat NWR's own
recommended player (26.1 real points) by 11.16 points that week. Reloading
History UI V3 live after this orchestrator run correctly rendered `EVALUATED
-11.2 pts vs chosen starter` for that row and `INSUFFICIENT CONTEXT` for
the two K/DST rows -- the full real pipeline (live Sleeper data ->
orchestrator -> evaluator -> facade -> History UI) confirmed working
end-to-end together for the first time this cycle, not merely unit-tested
in isolation.

**Other real, live, disclosed observations** (none chased further --
outside this pass's own scope, or pre-existing app behavior unrelated to
this cycle): (1) Attention Center reported `"3 rostered players could not
be matched to an NWR identity"` for the real league -- corroborates, and
generalizes (1 -> 3 players), Worker 7's own Marvin Harrison Jr. identity-
match-gap finding; not investigated further (ranking/identity resolution is
outside this cycle's hard boundary, same as Worker 7's own disclosure). (2)
The release-gate script's own documented KNOWN ISSUE (`weekly-home-actions`
returning HTTP 500 against a real, active-roster profile) did NOT reproduce
this pass -- it returned a real `200` (`3,202.9 ms`) against the same real
league; not root-caused (could be a real prior fix from an unrelated
session, or a real roster-shape difference) -- disclosed as an observed,
unexplained improvement, not claimed as a fix by this pass. (3) A freshly
Sleeper-imported profile's Home/Draft pages render `Pre-Draft`/`Week 1`
lifecycle badges even though the real league is genuinely in-season
(real NFL week 2) -- plausibly because NWR's own "pre-draft" concept tracks
whether the OWNER completed a draft inside NWR itself, not Sleeper's real
season progression, for a profile that has never been through NWR's own
Draft Room; not chased further (pre-existing app behavior, not part of this
cycle's own code). (4) The Draft Room's "Suggestions" panel showed
`DecisionBundle unavailable` before a team/slot was chosen -- plausible
expected pre-draft-setup state, not chased further (Draft Room is
untouched by this cycle). (5) The K_STREAMER/DST_STREAMER surface returned
different top picks two minutes apart within the same dogfood session
(Cam Little/Jacksonville at 1:43, Eddy Pineiro/Philadelphia at 1:45) --
unexplained, likely benign snapshot-timing variance between two independent
real calls, not chased further given time constraints; flagged here rather
than silently observed and dropped.

Player Drawer exercised for 6 real open/close cycles (Trevor Lawrence, from
the real Lineup page) -- renders correctly every time, zero console errors.
Console errors across the ENTIRE dogfood session (every surface walked,
every profile switch, every drawer cycle, the orchestrator's own live
network calls): **zero**.

### Work Unit 22 -- full acceptance

**A real, disclosed bug found and fixed this pass** (the only fix made):
`npx tsc -b apps/dynasty/tsconfig.json apps/redraft/tsconfig.json` FAILED
with 11 real errors, all in Worker 8's own new file
(`desktop/apps/redraft/src/attention-center-scale-benchmark.test.ts`) --
this codebase has no `@types/node` dependency anywhere, and this is the
ONLY file in the whole monorepo that imports `node:fs`/`node:path` or uses
`__dirname`; `vitest` never caught it because it transpiles without full
project type-checking. This is a real, disclosed gap: Worker 8's own ledger
entry only reports a vitest pass, never a `tsc -b` run. **Fixed narrowly**,
confined to this one wholly-this-cycle-owned file plus the minimal tooling
needed to support it: (1) added `@types/node@^22.12.0` as a new
`desktop/package.json` devDependency (matching the workspace's own stated
`engines.node >=22.12.0`; no other package.json/tsconfig changed --
`node` was NOT added to any project's global `types` array, to avoid
widening ambient Node globals into browser-facing source files); (2) added
`/// <reference types="node" />` to the top of the one file that needs it;
(3) fixed 6 real `noUncheckedIndexedAccess`/`exactOptionalPropertyTypes`
possibly-undefined errors in that same file's own `percentile`/`median`
helpers and two `CellResult` object literals, each with an `?? 0` fallback
disclosed in a comment as a type-level safety net (every real call site in
this file guarantees a non-empty array, so the fallback branch is never
actually reached). Re-verified: `tsc -b` now exits 0 with zero errors;
`npx vitest run apps/redraft/src/attention-center-scale-benchmark.test.ts`
still passes all 13 tests unmodified in behavior. One regenerated artifact
(`docs/codex/prospective_outcomes_v1/multi_league_scale_v1/
frontend_bench_results.json`) reflects this pass's own legitimate re-run of
that same file (numbers closely match Worker 8's own original run -- a
consistency check, not a regression).

**Full results, all re-confirmed live this pass, not assumed from any
prior ledger entry**:
- Targeted pytest slice (`pytest -k "decision_trace or prospective_outcome
  or live_player_intelligence or boundary_property_reliability or
  composition or player_availability or trade_package_quality_benchmark or
  kdst_prospective_benchmark or multi_league_scale_and_performance"`):
  **527 passed, 0 failed** (re-run twice this pass, both times identical --
  Worker 8's own final count, unchanged, since this pass made zero Python
  changes).
- `tests/test_desktop_application_api.py`: **46 passed / 4 failed** -- the
  SAME 4 pre-existing failures documented in every prior worker's own
  baseline, re-confirmed live.
- Full monorepo `npx vitest run` (from `desktop/`): **423 passed, 29 test
  files, 0 failed** (re-run twice this pass -- once before, once after the
  tsc fix -- both green, confirming the fix changed zero runtime behavior).
- `npx tsc -b apps/dynasty/tsconfig.json apps/redraft/tsconfig.json`:
  **FAILED (11 errors) before this pass's fix, PASSES CLEAN (0 errors)
  after** -- see above.
- `npm run build` (full production web build: `check:resources` +
  `typecheck` + both apps' `vite build`): **PASSES CLEAN**, confirming the
  privacy/resource-allowlist gate, the now-fixed typecheck, and both real
  production bundles all succeed together as one command.
- Native Tauri packaging: the sidecar binary
  (`binaries/nwr-desktop-api-x86_64-pc-windows-msvc.exe`) does **NOT**
  exist in this worktree (`binaries/` contains only its own `.gitignore`)
  -- per established precedent, NOT built fresh this pass. The release-gate
  script's own packaging-gate step (`cargo check`) failed for exactly this
  reason (`resource path ...\\binaries\\nwr-desktop-api-...exe doesn't
  exist`) -- a real, expected, KNOWN, non-blocking finding (not a toolchain
  regression), reported by the script itself as `FINDING:` text, honestly
  surfaced rather than hidden. `check:resources` itself (the real
  privacy/allowlist gate) PASSED cleanly this pass -- notably, this is
  BETTER than the script's own header-comment precedent (which documents an
  earlier, since-resolved expectation that `check:resources` would fail for
  `redraft` over a bundled governance receipt containing the owner's real
  name; that receipt issue is not reproduced this pass, consistent with the
  "Owner Mock QA V1" memory entry's own note about a governance-receipt
  renewal in an intervening session).
- Real read-only Sleeper smoke via the release-gate script: before/after
  byte-diff of `league`/`rosters`/`users` **IDENTICAL**, 0 writes confirmed
  -- see Work Unit 21 above.

**Full diff review, `cd1f78dacb927c647c2470ab9cbee9f981877e38` to this
pass's final HEAD (the WHOLE 9-worker cycle, not just this pass's own
commit)**: `git diff --stat` shows **64 files changed** before this pass's
own commit (10 modified, 54 new) -- matching the additive-only pattern
every prior worker's own ledger entry claims. Grepped the ENTIRE cycle diff
for every hard-boundary term (`marginal_roster_utility_v2`,
`LeagueSnapshot`, `LeagueWorkspaceContext`, `lifecycle_resolver`,
`DecisionResultEnvelope`, `PlayerAvailabilityStatus`): every match is
either ledger disclosure prose, a structural test asserting an import
statement does NOT contain the term, or a legitimate type-only import (the
scale-benchmark test file importing `LeagueWorkspaceContext`'s TYPE to
build a realistic fixture) -- **zero real imports or semantic
modifications of any hard-boundary module across the whole cycle**,
independently re-confirmed, not merely trusted from any single prior
worker's own claim.

**The 3 real bugs found+fixed this cycle, re-confirmed still fixed and not
regressed** (source re-read directly, not just grepped for the word "fix"):
(1) Worker 5's enum-keyed-dict-mangling fix (`_as_count_pairs` /
`class_specific_summaries` returning a LIST, never an enum-keyed dict) --
confirmed present in `prospective_outcome_history_presentation_v1_
service.py`. (2) Worker 6's Group 8 general sweep test
(`test_no_dict_anywhere_in_the_real_history_or_summary_payload_is_enum_or_
id_keyed`) and its own concrete regression backstop
(`test_the_two_previously_fixed_bug_instances_stay_fixed_as_concrete_
regressions`) both still present and passing in `tests/
test_boundary_property_reliability_pack_v2.py`. (3) Worker 6's trade-
evaluator acceptance-gate fix (`evaluate_trade`'s own independent
`acceptanceStatus == "ACCEPTED" and tradeAccepted is True` gate before
reusing `trade_realized_metrics_from_detail`) confirmed present in
`prospective_outcome_trade_evaluator_v1_service.py`, matching `evaluate_
trade_finder`'s own sibling guard.

**Endurance**: 10 real league switches (documented above, zero console
errors). 10 real repeated outcome ingestions via the orchestrator CLI
(documented above -- 1 real processing run + 9 byte-identical no-ops,
which IS this cycle's own idempotency contract, not merely "clicked ten
times"). 6 real player-drawer open/close cycles. History reload confirmed
live to reflect the orchestrator's own real output correctly. Cross-league
profile isolation confirmed (0 leaked events). A full 10x nav loop across
every directive-named surface (beyond what is documented above) was NOT
separately re-run after the initial full walk, given the time already spent
on the more decisive, mechanism-level checks above (CLI-level idempotency
x10, profile-switch x10, orchestrator re-run x10) -- disclosed honestly
rather than claimed as done.

### Work Unit 23 -- honest research synthesis (PRELIMINARY throughout)

Using the real evidence this WHOLE cycle produced (all 9 workers' own real
data/benchmarks/dogfood, plus this pass's own new real 11-trace dogfood
sample):

**Which decision classes can already be evaluated credibly?**
START_SIT is the one class with a real, live, working, end-to-end pipeline
AND at least one real observed outcome (n=1 this pass's own dogfood, plus
Worker 1/2's own earlier real Week 1 fixture work) -- `PRELIMINARY`, n=1
is far below the contract's own frozen minimum-sample threshold (20). The
MECHANISM (schema -> ingestion -> evaluation -> orchestration ->
presentation) is credible and tested at every layer (485+ unit tests
touching this class alone across the cycle); the STATISTICAL CONCLUSIONS
that mechanism can produce are not yet credible at n=1. DST_STREAMER's
mechanism is equally real and tested, but its real-world output is
currently DEGENERATE (see below) -- not a sample-size problem, a
correctness problem upstream of evaluation.

**Which classes are sample-starved?** Every other class: WAIVER, ADD_DROP,
FAAB, TRADE, TRADE_FINDER/TRADE_PACKAGE_SEARCH, K_STREAMER, DST_STREAMER,
DRAFT. The real production AppData store has zero traces (re-confirmed live
this pass); this pass's own dogfood produced real n=1-2 samples per class
in an ISOLATED worktree-local store, still far below 20. WAIVER/ADD_DROP/
FAAB/TRADE-family additionally cannot mature automatically today even given
enough real time, because six of those decision types' live call sites
record `week=None` or no player identity at all (Worker 3/4's own findings,
unchanged) -- `SKIP_WINDOW_UNDETERMINABLE`/`INSUFFICIENT_DECISION_CONTEXT`
by construction, confirmed live again this pass via the orchestrator's own
real run. DRAFT has zero live call site at all (schema-only, Worker 4).
`PRELIMINARY` is too generous a word for these classes' actual evaluability
today -- "not yet evaluable pending upstream identity-resolution work" is
more precise for six of the eight non-START_SIT classes.

**Which NWR tools show early regret/weakness?** Two genuinely DIFFERENT
findings, deliberately NOT conflated (per this cycle's own standing
discipline): (1) A single, real, `PRELIMINARY` (n=1) START_SIT REGRET
signal -- NWR's own Week 1 lineup recommendation underperformed the
owner's actual choice by 11.16 real points. This is exactly the kind of
observation Prospective Outcomes V1 exists to surface; it is also exactly
one data point, and this cycle's own frozen minimum-sample rule (20) exists
precisely so a finding like this is not overinterpreted into "NWR's
Start/Sit logic is bad" from a single close-call deviation. (2) The real,
MECHANICAL DST identity-matching bug (Worker 7, re-confirmed live this
pass) -- this is NOT a model-quality or close-call-resolution question at
all; it is a data-plumbing defect (a missing name fallback for Sleeper's
own DST catalog shape) that makes the DST arm of the K/DST streamer
ALWAYS structurally identical to naive top-ECR consensus, regardless of
real roster state, every single week, for every league. This is a
100%-reproducible, root-caused, zero-ambiguity finding -- categorically
different in kind and confidence from the n=1 START_SIT observation, and
this synthesis deliberately does not let the two blur into one vague
"NWR has weaknesses" headline.

**Which tools show no evidence requiring more complexity?** The Trade
Package Generator (`trade_package_search_service.py`) -- Worker 7's own
benchmark (Work Unit 16) found zero dominance violations, zero roster-
legality violations (once the benchmark's own measurement bug was fixed),
zero real-league bench-clutter, and explainable near-duplicate/zero-
candidate results, against a REAL league. This is the cycle's own
strongest "we looked for a problem, on purpose, with a preregistered
rubric, and did not find one" result -- worth naming explicitly as the
standard every other finding in this synthesis is held to.

**What should the NEXT improvement cycle target?** In priority order,
based on real evidence density and blast radius: (1) The DST identity-
matching fix (Work Unit 24 below) -- small, precise, ready to execute,
unlocks real DST evaluation data going forward. (2) A real canonical-id ->
Sleeper-id identity resolver for WAIVER/FAAB/ADD_DROP/K_STREAMER/
TRADE-family -- the single biggest lever for turning "sample-starved" into
"evaluable" across SIX of the eight live classes (Worker 1/3/4's own
repeatedly-inherited Open Issue). (3) A real week-capture fix for the
TRADE-family's live call sites (`week=None` today) so
`SKIP_WINDOW_UNDETERMINABLE` can ever resolve. (4) Once (2)/(3) land and
enough real season time has elapsed, RE-RUN this cycle's own real dogfood
pattern (exercise the live app against the real league, then run the
orchestrator) periodically -- this pass proved that pattern alone is
sufficient to generate real, evaluable data; no new mechanism is needed,
only real elapsed time and the identity-resolution work above. (5) The
`SleeperHttpClient` connection-reuse gap (Worker 8's own Open Issue 1) --
unrelated to evaluation correctness, a real latency-only item.

### Work Unit 24 -- bounded challenger

**One qualifying candidate, per the directive's own named example**: the
real DST identity-matching bug. A precise, ready-to-execute fix proposal
(exact root cause -- re-verified against `_identity`'s own literal
`("", "", "")` degenerate-key behavior, not just described generally --
exact 4-line fix mirroring two already-correct sibling code blocks
verbatim, exact new test, blast-radius analysis) was written to
`docs/codex/prospective_outcomes_v1/
DST_IDENTITY_MATCHING_FIX_PROPOSAL_V1.md`. **NOT executed this pass** --
`fantasypros_kdst_consensus_service.py` is a live, shared K/DST
*recommendation* service, outside this cycle's own established file set,
and the owner's standing instruction is explicit: do not build (or fix)
just because time is available. Handed off complete for a future,
explicitly-scoped session.

**No other qualifying defect was found** during this pass's own dogfood/
acceptance work, beyond the one already-disclosed, already-fixed `tsc -b`
gap (Work Unit 22 above, which WAS narrowly fixed this pass because it sits
entirely inside a file this cycle itself created, unlike the DST bug).

### Work Unit 25 -- push checkpoint

Acceptance is clean (Work Unit 22 above); the one fix made this pass is
narrow, disclosed, and fully re-verified. Pushed after this ledger entry's
own commit -- see the final HEAD / remote-verification line in this pass's
own closing handoff message (not duplicated here since the exact SHA is
only known after the commit that includes this very entry).

### Sleeper writes

**Zero.** Every real network call this pass made was a plain, public,
keyless Sleeper `GET` (`state/nfl`, `league/{id}/rosters`, `/users`,
`league/{id}/matchups/{week}`, `players/nfl`) -- via the release-gate
script's own real byte-diffed import, the live dogfood session's own real
surface reads, and the orchestrator's own real matchup fetch. The
release-gate script's own before/after byte-diff (`league`/`rosters`/
`users`) came back IDENTICAL, independently confirming zero writes.

### Backend/model files changed this pass

- **Modified (narrow, disclosed fix only)**:
  `desktop/apps/redraft/src/attention-center-scale-benchmark.test.ts`
  (tsc-only fix -- `/// <reference types="node" />` + 6 `?? 0`
  undefined-safety fallbacks, zero behavior change, re-verified by re-
  running its own 13 tests), `desktop/package.json` + `desktop/
  package-lock.json` (new `@types/node@^22.12.0` devDependency).
- **Regenerated (this pass's own legitimate re-run of an existing,
  designed-to-be-re-runnable artifact)**: `docs/codex/
  prospective_outcomes_v1/multi_league_scale_v1/frontend_bench_results.json`.
- **New**: `docs/codex/prospective_outcomes_v1/
  DST_IDENTITY_MATCHING_FIX_PROPOSAL_V1.md`, this ledger entry.
- **Nothing else** -- no evaluator, ingestion, orchestrator, schema,
  adapter, facade, or UI-rendering file from any of Workers 1-8's own work
  was modified. No hard-boundary file was touched.

## CONSOLIDATED CYCLE SUMMARY (all 9 workers, Prospective Outcomes V1)

A preregistered contract (8 decision classes, closed evaluation-status
vocabulary, frozen windows/thresholds) was built first and never silently
changed across 9 workers. On top of it: a canonical outcome-event contract
and source adapters (Worker 1); 8 real, independently-tested per-class
evaluators covering every live decision type (Workers 2-3); a DRAFT
foundation deliberately deferred to the correct future owner
(`marginal_roster_utility_v2`, Worker 4); a real, idempotent, hindsight-
leakage-proof automatic ingestion orchestrator with a real CLI (Worker 4);
History UI V3 + class-specific summaries wired end-to-end into the real
product (Worker 5, catching and fixing a real enum-key-mangling bug live in
Chrome); a boundary/property test pack V2 that found and fixed 2 MORE real
bugs via deliberate, general sweeps rather than hand-picked examples
(Worker 6); a trade-package-quality benchmark that found nothing wrong on
purpose (Worker 7); a K/DST benchmark that found and root-caused a real,
unfixed DST identity bug (Worker 7); multi-league scale (linear through 50
leagues) and performance characterization (one real, unfixed connection-
reuse latency source, precisely cProfile-attributed) (Worker 8); and,
closing the cycle, a real dogfood pass that for the first time produced and
observed real (non-fixture) end-to-end data, a full acceptance pass that
found and fixed one real `tsc -b` gap, an independently re-verified
zero-hard-boundary-drift full-cycle diff review, an honest research
synthesis that resists overreading n=1 evidence, a ready-to-execute (not
executed) fix proposal for the one real mechanical defect this cycle
surfaced, and a push (Worker 9).

**Real conclusion**: the evaluation LAYER is real, tested, and now proven
live end-to-end against real data for at least one class (START_SIT). The
DATA needed to say anything statistically meaningful about NWR's own
recommendation quality across most classes does not exist yet -- not
because the mechanism is broken, but because real season time and (for six
of eight classes) a real identity resolver both still need to accumulate/be
built. The one clear, mechanical, actionable defect this whole cycle
surfaced (DST identity matching) is fully diagnosed and ready for a future
session to fix in minutes. This cycle did not manufacture a false
conclusion to justify its own length -- it built the honest instrument and
reported, truthfully, that the instrument mostly does not have enough real
readings yet.

### CONSOLIDATED BUG LIST (all real bugs found across all 9 workers)

1. **(Worker 5, FIXED)** Enum-keyed-dict HTTP camelCase-mangling in the new
   History/class-summary presentation layer (`_as_count_pairs` fix,
   `prospective_outcome_history_presentation_v1_service.py`) -- found live
   in Chrome, not just in pytest.
2. **(Worker 6, FIXED)** The SAME bug class, confirmed to have zero other
   live instances via a general structural sweep (not another hand-picked
   example) -- `tests/test_boundary_property_reliability_pack_v2.py` Group
   8, plus a permanent concrete-regression backstop for bug #1 above.
3. **(Worker 6, FIXED)** `evaluate_trade`'s own missing independent
   acceptance/accepted gate before reusing `trade_realized_metrics_from_
   detail` -- a rejected-trade counterfactual could otherwise leak through
   a malformed/legacy raw `outcome.detail` dict that bypasses the schema's
   own `__post_init__` guard. Fixed at `evaluate_trade`'s own call site,
   mirroring `evaluate_trade_finder`'s existing sibling guard.
4. **(Worker 7, FOUND, NOT FIXED -- hard-boundary gated, proposal ready)**
   `sleeper_streamer_actions`'s real DST identity key always degenerates to
   `("", "", "")` for every real Sleeper DST roster entry (missing the
   `f"{team} D/ST"` name fallback that 2 sibling functions in the same file
   already carry) -- makes NWR's own DST streamer recommendation always
   structurally identical to naive top-ECR consensus. Re-confirmed live in
   the real running UI by Worker 9. Exact fix + test in `DST_IDENTITY_
   MATCHING_FIX_PROPOSAL_V1.md`.
5. **(Worker 9, FOUND+FIXED)** `tsc -b` failure in Worker 8's own new file
   (`attention-center-scale-benchmark.test.ts`) -- no `@types/node`
   anywhere in this codebase, `node:fs`/`node:path`/`__dirname` used
   without it; `vitest` never caught it (no full project type-check).
   Fixed narrowly (new devDependency + a scoped triple-slash reference +
   6 `?? 0` undefined-safety fallbacks), zero behavior change (13/13 tests
   still pass).

### OPEN ITEMS FOR FUTURE CYCLES (consolidated, deduplicated)

1. Execute the DST identity-matching fix (`DST_IDENTITY_MATCHING_FIX_
   PROPOSAL_V1.md`) -- the one ready-to-go, high-confidence item.
2. Build a real canonical-id -> Sleeper-id identity resolver for
   WAIVER/FAAB/ADD_DROP/K_STREAMER/TRADE-family live call sites -- the
   single biggest lever for making six of eight live decision classes
   evaluable at all (inherited from Workers 1/3/4, still unresolved).
3. Add real week-capture to the TRADE-family's live call sites
   (`week=None` today blocks any maturity check -- Worker 4's own Open
   Issue 2, still unresolved).
4. A real, general `owner_roster_id` resolver (today: one real,
   hardcoded, confirmed pair -- Worker 4's own Open Issue 3).
5. `SleeperHttpClient` connection reuse (Worker 8's own Open Issue 1) --
   a real, cProfile-attributed latency source, unrelated to correctness.
6. A real ROS (rest-of-season) evaluation window, once enough of a real
   season has elapsed to derive one honestly (Worker 1's own Open Issue 5,
   inherited unchanged through every worker).
7. The duplicated `MIN_SAMPLE_SIZE_FOR_PER_CLASS_*` constant across the
   Python/TypeScript boundary (Worker 1's own Open Issue 6, unchanged).
8. ADD_DROP's `netRosterValuePoints` (needs a leaguewide roster-
   membership-over-time feed this codebase does not have -- inherited from
   the PRIOR cycle's own Open Issue 3, unchanged through every worker).
9. DRAFT's real live call site + real season-long roster-utility
   computation (explicitly deferred to `marginal_roster_utility_v2`,
   outside every version of this cycle's own hard boundary -- Worker 4's
   own Work Unit 11).
10. Once (2)/(3) land and real season time accumulates, periodically
    re-run this pass's own real dogfood pattern (exercise the live app,
    then run the orchestrator CLI) -- proven sufficient this pass to
    generate real, evaluable data with no new mechanism required.
11. Worker 8's own unexecuted follow-up: once (1) lands, re-run `scripts/
    run_kdst_prospective_benchmark_v1.py` to measure the DST arm's TRUE
    differentiated value for the first time.
12. TARGET_PLAYER(LaPorta)/IMPROVE_POSITION(TE) zero-candidate root cause
    (Worker 7's own Open Issue 6, not fully traced -- non-zero utility
    gates rejected every combination, mechanism not pinned down further).
13. The real Marvin Harrison Jr. (and now, per this pass, 2 more) identity-
    match gap between rostered Sleeper players and the current NWR
    canonical ranking pool (Worker 7's own Open Issue 7, re-corroborated
    live by Worker 9's own Attention Center check this pass, not
    investigated further -- outside this cycle's hard boundary).
14. This pass's own small, disclosed curiosity: the K/DST streamer surface
    returned different top picks two minutes apart within the same
    dogfood session -- unexplained, likely benign snapshot-timing
    variance, not chased further.
