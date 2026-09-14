# NWR Prospective Outcome V1

Branch `upgrade/nwr-live-player-intelligence-v1-20260913`, worktree
`C:\NWR\live-player-intelligence-v1`. Start HEAD for this pass: `828b00b1`
(the Live Player Intelligence V1 cycle's own closing commit -- that cycle is
DONE and was not reopened; this pass builds the SEPARATE prospective
outcome-evaluation foundation the same governing directive calls "the
second major remaining frontier"). Not merged, not pushed, not deployed.

## What this pass is, in one paragraph

`in_season_decision_trace_service.py` already recorded every live
recommendation (`record_decision_trace`) and could append an owner's real
action (`record_owner_action`); its `record_outcome` append-path existed
but was an unimplemented gap -- callable, but with no real ingestion
mechanism deciding WHAT actually gets written into it. This pass closes
that gap: (1) a decision-type-specific outcome SCHEMA
(`prospective_outcome_schema_v1_service.py`) -- eight genuinely distinct
dataclasses, not one generic accuracy score; (2) an INGESTION mechanism
(`prospective_outcome_ingestion_v1_service.py`) -- pure functions that turn
a trace's own frozen fields plus real, already-fetched, after-the-fact
Sleeper data into one of those schema instances; (3) a small, additive,
fully backward-compatible extension to `record_outcome` itself (an optional
`detail` payload) so the schema's output can actually be appended to the
ledger.

## Decision-type schemas built (all in `prospective_outcome_schema_v1_service.py`)

Every one of these is a distinct dataclass with its own `KIND` string and
its own field set -- see `test_every_decision_type_has_a_genuinely_distinct_
kind` for the structural proof there are 8 of them, not 1:

1. **`StartSitOutcomeDetail`** -- recommended vs. actual starting lineup
   (both full lineups, matching the REAL recorded shape --
   `weekly_lineup_optimizer_service` records a full 9-slot `starters` list,
   not a single player), the bench at lock time
   (`eligible_alternative_ids_at_lock`, derived only from the trace's own
   frozen `roster_state_player_ids`), the players that differ each way
   (`recommended_only_ids`/`actual_only_ids`), and a real point-delta
   `lineup_opportunity_cost` (`None` when not yet computable, `0.0` when
   the lineups genuinely matched -- never conflated).
2. **`WaiverOutcomeDetail`** -- `claim_submitted`/`claim_won` (a real
   `False` when the full supplied transaction period shows no matching
   claim -- not an `None`-shaped "unknown"), `faab_paid`, and a bounded-
   horizon `subsequent_roster_usage_weeks`/`subsequent_total_points`.
3. **`AddDropOutcomeDetail`** -- added-player subsequent value/usage,
   dropped-player subsequent value (honestly left `None` when the dropped
   player leaves the observable roster -- see Open Issue 3 below),
   `dropped_player_reversed` (a real, observed later re-add, never
   inferred).
4. **`FaabOutcomeDetail`** -- KEEPS `player_decision_quality`
   (`FaabPlayerDecisionQuality`) and `bid_range_calibration`
   (`FaabBidRangeCalibration`) as two structurally separate nested
   dataclasses (disjoint field sets, proven by
   `test_faab_keeps_player_decision_quality_and_bid_calibration_separate`)
   per the directive's explicit instruction not to conflate "was the pickup
   good" with "was the suggested $ range accurate" --
   `test_faab_flags_out_of_range_suggestion_even_when_pickup_was_good`
   proves the two axes can disagree at the same time.
5. **`TradeOutcomeDetail`** -- `acceptance_status`
   (`ACCEPTED`/`REJECTED`/`UNKNOWN`) plus `realized_roster_outcome`, which
   the dataclass's own `__post_init__` REFUSES to populate unless
   `trade_accepted is True` (raises `ValueError` otherwise) -- a rejected
   trade never gets scored against an unobserved counterfactual, enforced
   structurally, not just by convention.
6. **`TradeFinderOutcomeDetail`** -- `package_disposition`
   (`IGNORED`/`CONSIDERED`/`SENT`/`ACCEPTED`/`UNKNOWN`); `linked_trade_
   outcome` is likewise structurally refused unless the disposition is
   exactly `ACCEPTED`, and reuses `TradeOutcomeDetail` itself so an accepted
   package is scored identically to a direct accepted trade.
7. **`StreamerOutcomeDetail`** -- one instance per position (`K` or `DST`)
   per week, evaluated independently (a K_STREAMER trace and a DST_STREAMER
   trace never share a record): recommended vs. actual starter vs. the
   prior roster option vs. what was genuinely available AT RECOMMENDATION
   TIME (`available_alternative_ids_at_recommendation`, from the trace's
   own frozen `alternatives` -- `test_no_future_leakage_streamer_
   alternatives_never_see_a_hindsight_best_pick` proves a real hindsight-
   best player absent from that frozen list can never appear as
   `best_available_alternative_id`, even when it demonstrably outscored
   everyone that week).
8. **`DraftOutcomeDetail`** -- deliberately THIN this pass.
   `build_deferred_draft_outcome_detail` returns every real field `None`
   and names `evaluation_method = "DEFERRED_TO_SEASON_LONG_ROSTER_UTILITY_
   ENGINE"` rather than silently defaulting to nothing. Real season-long
   roster-utility computation (season-long value evaluated separately from
   injury luck, chronological/no-hindsight, per
   `nwr-post-draft-engine-forensics-v1`'s convention) lives in
   `marginal_roster_utility_v2`, explicitly forbidden to this pass's hard
   boundary -- a future, boundary-cleared pass fills this schema in for
   real; this pass does not compute a draft outcome.

## Ingestion mechanism (`prospective_outcome_ingestion_v1_service.py`)

Pure functions, **zero network I/O of their own** (the same division of
labor `sleeper_league_context_service.py` already established: "the facade
performs the actual HTTP reads"). One `ingest_*_outcome` function per
decision type, each taking (a) the trace's own already-recorded, frozen
fields as explicit keyword arguments and (b) real, already-fetched,
after-the-fact Sleeper JSON (a matchup entry, a transaction list, bounded-
horizon matchup entries). Real Sleeper endpoints referenced (all already
public/read-only/keyless, the same ones this codebase's other Sleeper call
sites already use): `league/{id}/matchups/{week}` (real per-player
`players_points`, real `starters`), `league/{id}/transactions/{round}`
(real `adds`/`drops`/`status`/`settings.waiver_bid`).

**Identity resolution is explicitly out of scope for this module** (see its
own docstring): START_SIT and K/DST_STREAMER traces already record raw
Sleeper player ids directly (confirmed by reading the real
`desktop_facade.py` call sites), so those ingestion functions consume
Sleeper ids with zero extra resolution. WAIVER/ADD_DROP/FAAB/TRADE/
TRADE_FINDER/TRADE_PACKAGE_SEARCH traces record the app's own canonical
player-id space instead -- those ingestion functions accept
ALREADY-RESOLVED Sleeper ids as plain arguments; this pass does not build a
second identity matcher (consistent with every earlier worker's precedent
in this cycle: reuse `_identity`, never fork it). Wiring a real
canonical->Sleeper resolver into a live orchestrator is an open item below.

## What's genuinely available for Week 1 2026, and what was ingested

Real, live-checked 2026-09-13 against the real Fantasy Gamers league
(Sleeper id `1312983576827920384`, owner `scolety`, `roster_id` 9,
`GET /v1/state/nfl` confirms `week=1`, `season_has_scores=true`):

- **START_SIT**: real, scored Week 1 matchup data exists
  (`docs/codex/prospective_outcome_v1/real_data_v1/
  fantasy_gamers_week1_2026_owner_matchup.json`, committed verbatim, real
  `_source_note`). `test_real_week1_2026_fantasy_gamers_matchup_ingests_
  correctly` ingests it and hand-verifies every field against the real
  fixture. `scripts/build_prospective_outcome_ingestion_v1_startsit_demo.py`
  additionally ran the FULL real pipeline live (fetch -> `record_decision_
  trace` -> `ingest_start_sit_outcome` -> `record_outcome(...,
  detail=...)`, isolated throwaway root, zero Sleeper writes) --
  `docs/codex/prospective_outcome_v1/startsit_ingestion_demo_v1/
  summary.json` is the real, committed result, including a live
  append-only proof (`originalRecommendationLineByteIdentical: true`).
- **WAIVER/ADD_DROP**: real Week 1 transactions exist for this league (4
  real `free_agent`-type adds, one with a real drop) -- none are `WAIVER`-
  type with a real FAAB bid yet (this league's `waiver_day_of_week`
  processing had not yet run as of the live check). The ingestion
  mechanism is real and fixture-tested; zero real WAIVER/ADD_DROP outcomes
  were ingested this session because no real historical WAIVER/ADD_DROP
  START_SIT-equivalent trace + a real completed FAAB-bid transaction pair
  yet coexists to attach one to.
- **FAAB/TRADE/TRADE_FINDER/TRADE_PACKAGE_SEARCH/K_STREAMER/DST_STREAMER**:
  zero real transactions of the relevant type (`waiver` with a bid,
  `trade`) exist yet this early in the real season. Zero real outcomes
  ingested for these this session -- honestly expected, per the directive's
  own framing ("It's fully expected that most decision types will have
  zero or very few real outcomes to actually ingest this session").
- **DRAFT**: zero -- this pass performs no draft outcome computation at
  all (see schema section above); out of the hard boundary entirely.

**Honest count of "real outcomes ingested this session": 1** (START_SIT,
via the live demo script above, into an isolated throwaway root -- NOT the
owner's real production ledger, and its `recommendation` is a mechanism-
demonstration baseline, not a genuine historical NWR forecast, since no
real START_SIT trace existed yet in production to attach a real outcome
to). The real, hand-verified fixture-based test is a second, independent
real-data proof of the same mechanism, without writing any ledger row.

## Append-only guarantee

`record_outcome`'s new `detail` parameter is purely additive: omitted
(`None`, the default), the outcome payload is byte-identical to this
function's behavior before this pass
(`test_record_outcome_without_detail_is_byte_identical_to_pre_existing_
behavior`). When supplied, it is stored as a defensive copy under
`outcome["detail"]` on a NEW appended line -- the original recommendation
line is read back and asserted to still lack any `outcome` key at all
(`test_record_outcome_with_detail_appends_a_new_line_never_mutates_the_
original`). The live real-data demo script performs the same proof against
a real file on disk (`appendOnlyProof.originalRecommendationLineByteIdentical:
true` in its committed summary).

## No-future-leakage guarantee

Structural, not just conventional: every ingestion function's signature
only accepts the trace's own already-recorded fields (`recommendation`,
`roster_state_player_ids`, `alternatives`-derived arguments, `owner_action`)
for "what was known/eligible/recommended at the time" -- no function in
`prospective_outcome_ingestion_v1_service.py` accepts a "current roster" or
"current free agents" parameter for that purpose at all. Two tests make
this concrete:
`test_no_future_leakage_eligible_alternatives_ignore_a_later_roster_change`
(a simulated later roster change is never visible to the computed
eligible-alternatives set, because the function was never given that
"current" snapshot) and
`test_no_future_leakage_streamer_alternatives_never_see_a_hindsight_best_
pick` (a player who scored the most of anyone that week in hindsight, but
was never a recorded alternative at recommendation time, can never surface
as `best_available_alternative_id`).

## Tests

`tests/test_in_season_decision_trace_service.py` (24, 3 new),
`tests/test_prospective_outcome_schema_v1_service.py` (11, new),
`tests/test_prospective_outcome_ingestion_v1_service.py` (22, new, includes
the 2 real-data tests above) -- 57 total in this pass's own files, all
green. Wider regression check: `pytest -k "decision_trace or
prospective_outcome or player_availability or live_player_intelligence"` ->
158 passed. `test_desktop_application_api.py`: 46 passed / 4 failed --
confirmed pre-existing at this worktree's Start HEAD per the prior cycle's
own `LEDGER.md` entry (this pass touched neither `desktop_facade.py` nor
`desktop_api/`, `git status` confirms zero modification to either).

## Hard boundary respected

Nothing under `marginal_roster_utility_v2`, draft recommendation logic,
scoring, roster legality, `LeagueSnapshot`/`LeagueWorkspaceContext`/
lifecycle-resolver/`DecisionResultEnvelope`/`PlayerAvailabilityStatus`
semantics, or the just-completed Live Player Intelligence V1 admission/
composition code was touched -- `git diff --stat` against Start HEAD
`828b00b1` shows only additive new files plus the two additive edits to
`in_season_decision_trace_service.py`/its own test file (a new optional
`record_outcome` parameter and its tests; no existing behavior changed,
proven by the backward-compatibility test above). `desktop_facade.py`,
`desktop_api/server.py`, and every draft/scoring/roster-legality module are
untouched (`git status --porcelain` confirms no `M` against any of them).

## Backend/model files changed or added this pass

- **Modified (additive only)**: `src/services/in_season_decision_trace_
  service.py` -- `record_outcome` gains one optional keyword parameter
  (`detail`); every existing call site/behavior is unchanged (proven by
  the backward-compat test).
- **New**: `src/services/prospective_outcome_schema_v1_service.py` (the
  eight schema dataclasses), `src/services/prospective_outcome_ingestion_
  v1_service.py` (the pure ingestion functions), `scripts/build_
  prospective_outcome_ingestion_v1_startsit_demo.py` (real-data demo
  script, not exercised by pytest, same convention as this cycle's other
  real-network scripts), three new test files, one committed real-data
  fixture, one committed real-data demo summary, and this doc.
- **Nothing in `desktop_facade.py`, `desktop_api/`, or any consumer/UI
  layer was wired this pass** -- `record_outcome`'s `detail` payload and
  every ingestion function are real and callable, but nothing in
  production calls them yet. That wiring (a real facade endpoint/background
  job that fetches Sleeper data, calls the right `ingest_*_outcome`
  function, and appends via `record_outcome`) is explicitly left to the
  next worker, alongside History UI V2.

## Open issues for the next worker (History UI V2 + boundary property tests)

1. **No facade/orchestration wiring exists yet.** This pass built and
   proved the schema + ingestion mechanism; a real, scheduled (or
   on-demand) job that (a) fetches real Sleeper matchup/transaction data
   for the active profile's league, (b) calls the matching `ingest_*_
   outcome` function for each `RECOMMENDED`/`OWNER_ACTION_RECORDED` trace
   whose week/period has since completed, and (c) calls `record_outcome`
   is the natural next step -- deliberately not built this pass to keep the
   schema/mechanism design and its wiring as separable, reviewable units.
2. **Identity resolution for the canonical-id decision types** (WAIVER/
   ADD_DROP/FAAB/TRADE/TRADE_FINDER/TRADE_PACKAGE_SEARCH/K_STREAMER/
   DST_STREAMER) is a real, undone dependency: those traces record the
   app's own canonical player-id space (or, for K/DST, only `playerName`/
   `team`), while Sleeper transactions/matchups are keyed by Sleeper's own
   ids. A real orchestrator needs to resolve one to the other (reusing
   `resolve_roster_canonical_ids`/the ranking-row crosswalk this codebase
   already has, per the existing `_identity` precedent) BEFORE calling
   these ingestion functions -- this pass's functions accept
   already-resolved ids and do not perform that resolution themselves.
3. **`AddDropOutcomeDetail.dropped_player_subsequent_points` is honestly
   left `None`-producing in this pass's `ingest_add_drop_outcome`** -- once
   a player is dropped, their subsequent value is only observable from
   WHICHEVER roster (if any) picks them up next, which this function's
   inputs don't carry. A future pass with access to a leaguewide
   roster-membership-over-time feed could compute this for real.
4. **`WaiverOutcomeDetail`/`FaabOutcomeDetail`'s `claim_submitted=False`/
   `won=False` results are only as complete as the `transactions_for_
   period` the caller supplies.** These functions assume the caller passed
   the FULL relevant transaction window; a real orchestrator must fetch
   every relevant `round`/week of `league/{id}/transactions/{round}`, not
   just one, or a real claim could be missed and misreported as "never
   submitted."
5. **Bounded horizon length (`DEFAULT_HORIZON_WEEKS = 4`) is a reasonable
   but arbitrary choice this pass made**, not derived from any real
   analysis of how long a waiver-wire pickup's value takes to resolve --
   worth revisiting once real horizon data actually exists to check against.
6. **History UI V2**: the owner-facing read of these new `detail` payloads
   (`_decision_trace_history_event_payload` in `desktop_facade.py` already
   passes through `record.outcome` verbatim, so the new `detail` key
   already reaches the JSON payload with zero facade change needed -- but
   no frontend surface renders it yet). Per-decision-type presentation
   (e.g. showing `lineupOpportunityCost` distinctly from
   `bidRangeCalibration`) is this next worker's to design.
7. **Boundary property tests** (per the governing directive's own framing
   of this next phase): a property-based test that no `ingest_*_outcome`
   function's output ever depends on argument ORDER/mutation of the input
   collections it's given, and a property-based sweep over the
   no-future-leakage guarantee (arbitrary "current" vs. "at lock time"
   roster/alternatives divergence) would strengthen the guarantees this
   pass proved with example-based tests only.
