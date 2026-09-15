# NWR Prospective Outcome Evaluation Contract V1

Branch `upgrade/nwr-prospective-outcomes-v1-20260914`, worktree
`C:\NWR\prospective-outcomes-v1`. Start HEAD for this pass: `cd1f78da`.
Not merged, not pushed, not deployed.

This document is **preregistered and frozen before any evaluation-logic
implementation code is written** (Work Unit 0, per the governing
directive). Everything below is a commitment: later work units in this
cycle (or a future worker's cycle) may **extend** this contract with new,
clearly-labeled additions, but may not silently change a number or rule
already frozen here to flatter a result. Any genuine revision must be a
new, dated section that says explicitly what changed and why -- never a
silent edit.

## 0. Baseline verified before writing this document

- Branch: `upgrade/nwr-prospective-outcomes-v1-20260914` (confirmed via
  `git branch --show-current`).
- HEAD: `cd1f78dacb927c647c2470ab9cbee9f981877e38` (matches the directive's
  Start HEAD exactly).
- Worktree: clean (`git status` -> "nothing to commit, working tree
  clean").
- Targeted pre-existing test slice (`pytest -k "decision_trace or
  prospective_outcome or live_player_intelligence or
  boundary_property_reliability or composition or player_availability"`):
  **269 passed, 0 failed** -- identical to the prior cycle's own
  documented count in `docs/codex/live_player_intelligence_v1/LEDGER.md`
  (Worker 7's closing entry).
- `tests/test_desktop_application_api.py`: **46 passed / 4 failed** --
  the same 4 pre-existing failures the prior cycle documented at this
  exact worktree (`test_dynasty_facade_composes_real_governed_workflows`,
  `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`,
  `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`,
  `test_facade_has_no_streamlit_or_app_component_dependency`). Confirmed
  live this pass, not merely trusted from the ledger.
- Existing trace schema: `src/services/in_season_decision_trace_service.py`
  -- `DecisionTraceRecord` (append-only JSONL, one file per profile,
  `record_decision_trace` / `record_owner_action` / `record_outcome`, the
  last already carrying an optional `detail` payload).
- Existing outcome schema: `src/services/prospective_outcome_schema_v1_service.py`
  -- 8 decision-type dataclasses (`StartSitOutcomeDetail`,
  `WaiverOutcomeDetail`, `AddDropOutcomeDetail`, `FaabOutcomeDetail` with
  its two separate nested axes, `TradeOutcomeDetail`,
  `TradeFinderOutcomeDetail`, `StreamerOutcomeDetail`, `DraftOutcomeDetail`).
  Confirmed read in full this pass.
- Existing ingestion mechanism:
  `src/services/prospective_outcome_ingestion_v1_service.py` -- pure
  functions, zero network I/O of their own, one real START_SIT outcome
  already ingested (into an isolated throwaway root via
  `scripts/build_prospective_outcome_ingestion_v1_startsit_demo.py`, real
  Fantasy Gamers Week 1 2026 data).
- Existing outcome endpoints:
  `DesktopApplicationFacade.redraft_record_decision_trace_owner_action` /
  `.redraft_record_decision_trace_outcome` / `.redraft_decision_trace_history`
  in `src/application/desktop_facade.py` (lines ~4440-4538), all already
  wired to real HTTP routes.
- Existing History UI: `desktop/apps/redraft/src/decision-history.tsx` +
  `decision-history-format.ts` (History UI V2) -- per-decision-type
  progressive detail sections, explicitly **no aggregate accuracy score**
  anywhere, and a named, unused, disclosed rollup-sample-size gate
  (`MIN_SAMPLE_SIZE_FOR_PER_CLASS_ROLLUP = 20`).

This pass reuses every one of the above as its starting point. It does
**not** rebuild the schema, the ingestion functions, or the History UI
list view from scratch.

## 1. Decision classes (confirmed, reused verbatim)

The 8 decision-type `KIND`s already defined in
`prospective_outcome_schema_v1_service.py`, mapped 1:1 onto the 10
`TOOL_TYPES` the decision-trace ledger already records (`TRADE_FINDER` and
`TRADE_PACKAGE_SEARCH` both reuse `TradeFinderOutcomeDetail`; `DRAFT` is
schema-only/deferred):

| `TOOL_TYPES` value | Outcome schema `KIND` |
|---|---|
| `START_SIT` | `START_SIT_LINEUP_V1` |
| `WAIVER` | `WAIVER_V1` |
| `ADD_DROP` | `ADD_DROP_V1` |
| `FAAB` | `FAAB_V1` |
| `TRADE` | `TRADE_V1` |
| `TRADE_FINDER` | `TRADE_FINDER_V1` |
| `TRADE_PACKAGE_SEARCH` | `TRADE_FINDER_V1` (reused) |
| `K_STREAMER` | `STREAMER_V1` (`position="K"`) |
| `DST_STREAMER` | `STREAMER_V1` (`position="DST"`), evaluated INDEPENDENTLY of `K_STREAMER` |
| `DRAFT` | `DRAFT_V1` (deliberately thin/deferred -- see Section 8) |

No new decision class is introduced this pass. This directive's own
framing ("different decision classes need different outcome definitions,
evaluated separately") is honored by keeping this exact table -- never
collapsed into one generic score.

## 2. Outcome definitions per class -- what "evaluated" means

For every class, "evaluated" means: a real `OutcomeEvaluation` record (new
this pass, Work Unit 1, `prospective_outcome_evaluation_v1_service.py`)
could be computed from the trace's own already-recorded, real
`outcome.detail` payload, producing one or more real, already-computed
numbers or booleans -- **never a synthesized 0-100 score**, and never one
merged across classes.

- **START_SIT**: the primary evaluation metric is `lineupOpportunityCost`
  (already computed by `ingest_start_sit_outcome`) -- real points the
  recommended-but-benched players scored minus real points the
  started-but-not-recommended players scored, `None` when not honestly
  computable. Positive means following the recommendation would have
  outscored the owner's real deviation.
- **WAIVER**: `claimSubmitted` / `claimWon` (real booleans, `False` is a
  real observed fact, not "unknown") plus, only when the claim was
  actually won, `subsequentTotalPoints` / `subsequentRosterUsageWeeks`
  over the bounded horizon (Section 3).
- **ADD_DROP**: `addedPlayerSubsequentPoints` /
  `addedPlayerSubsequentRosterUsageWeeks` over the bounded horizon, plus
  `droppedPlayerReversed` (a real, observed later re-add). The dropped
  player's own subsequent value is honestly left uncomputed this pass
  (Section 8, Open Issue 1 -- unchanged from the prior cycle's own
  disclosure).
- **FAAB**: TWO structurally separate metrics, never merged into one
  figure, per the existing dataclass split:
  - `playerDecisionQuality` (was the pickup itself good -- subsequent
    points/usage over the bounded horizon).
  - `bidRangeCalibration` (was the suggested `$` range accurate --
    `bidWithinSuggestedRange`, `marginVsActualWinningBid`).
- **TRADE**: `acceptanceStatus` always; `netSubsequentPointsDelta`
  (realized-roster-outcome) computed ONLY when `tradeAccepted is True`.
  A rejected/unknown trade's evaluation status is `NOT_APPLICABLE` for
  the realized-outcome metric -- never a scored counterfactual.
- **TRADE_FINDER / TRADE_PACKAGE_SEARCH**: `packageDisposition` always;
  reuses TRADE's own realized-outcome metric ONLY when
  `packageDisposition == "ACCEPTED"`.
- **K_STREAMER / DST_STREAMER**: a real point-delta between the
  recommended player's actual points and the actually-started player's
  actual points at that position for that week (mirrors START_SIT's own
  opportunity-cost formula, the one new derived number this pass
  computes at the evaluation layer -- see Work Unit 1's code comments).
  `None` when either side's actual points are not observable.
  `bestAvailableAlternativeActualPoints` is reported alongside but never
  substituted into the opportunity-cost formula (the recommendation is
  compared to what the owner actually started, not to a hindsight-best
  alternative -- see Section 5).
- **DRAFT**: deliberately **NOT_APPLICABLE this entire cycle**. Real
  season-long roster-utility evaluation belongs to
  `marginal_roster_utility_v2`, outside this cycle's hard boundary. The
  schema exists (`DraftOutcomeDetail`, `evaluation_method =
  "DEFERRED_TO_SEASON_LONG_ROSTER_UTILITY_ENGINE"`); no draft outcome is
  computed here.

## 3. Evaluation windows -- exact numbers, preregistered

These numbers are frozen. A later work unit may add a NEW, clearly-labeled
window for a new use case, but must not silently change one of these.

| Decision class | Window label | Horizon (weeks) | Rationale |
|---|---|---|---|
| `START_SIT` | `SAME_WEEK_LOCK_TO_FINAL` | 0 (single week, the recommendation's own week) | A lineup decision resolves entirely within its own week -- there is no multi-week horizon to bound. |
| `K_STREAMER` / `DST_STREAMER` | `SAME_WEEK` | 0 | Same reasoning as START_SIT -- a streamer pick resolves within its own week. |
| `WAIVER` | `BOUNDED_HORIZON` | **4** (`DEFAULT_HORIZON_WEEKS`, already coded in `prospective_outcome_ingestion_v1_service.py`, reused verbatim -- not re-derived) | Matches the prior cycle's own disclosed, "reasonable but arbitrary" choice (its own Open Issue 5). This pass does not re-justify it with new analysis; it is preregistered here as the number, not silently changed. |
| `ADD_DROP` | `BOUNDED_HORIZON` | **4** | Same as WAIVER. |
| `FAAB` | `BOUNDED_HORIZON` | **4** (applies only to `playerDecisionQuality`; `bidRangeCalibration` has no horizon at all -- it resolves at the moment the waiver period closes) | Same as WAIVER. |
| `TRADE` / `TRADE_FINDER` / `TRADE_PACKAGE_SEARCH` | `BOUNDED_HORIZON_ACCEPTED_ONLY` | **4** | Same numeric horizon, reused for consistency; gated additionally on `tradeAccepted is True` (Section 2). |
| `DRAFT` | `DEFERRED_SEASON_LONG` | not defined this cycle | Out of hard boundary. |

**A real ROS ("rest-of-season") horizon is explicitly NOT built this
pass.** The directive names it as a real option ("1 week / 3 weeks /
ROS-where-season-permits"); this pass preregisters only the two numbers
that already exist in real, tested code (0-week same-week, 4-week
bounded) rather than inventing a ROS number with no real basis yet this
early in the season (Week 1-2 of 2026 at the time of this pass). A future
worker may add a real ROS window once enough of the season has actually
elapsed to define one honestly -- flagged in Section 9 as an open item,
not decided here.

## 4. Missing-data semantics -- `evaluationStatus`

Every `OutcomeEvaluation` (Work Unit 1) carries one status from this
closed, frozen set. **`EVALUATED` is the only status that carries a real
computed metric value for its class's primary metric; every other status
means the metric field is honestly `None`/absent, never fabricated:**

- **`PENDING_OUTCOME`** -- no `outcome` has been recorded on this trace
  yet (`record.outcome is None`). The recommendation and, if present, the
  owner's action are real; no outcome data exists to evaluate.
- **`PENDING_WINDOW`** -- an outcome WAS recorded, but the specific
  evaluation window's data was not supplied to the ingestion function that
  produced it (e.g. `ADD_DROP`'s `added_player_subsequent_points` is
  `None` because no `horizon_matchup_entries` were supplied at all -- the
  horizon has not yet been observed/fetched, not structurally unknowable).
- **`EVALUATED`** -- a real, structured `outcome.detail` payload exists
  and this class's primary metric was computed to a real, non-`None`
  value.
  - **`INSUFFICIENT_DECISION_CONTEXT`** -- an outcome was recorded, but
  the recommendation-time context needed to honestly compute a metric
  could not be reconstructed (e.g. no structured `detail` payload was
  ever attached -- only the legacy free-text `outcome`/`notes` pair; or a
  decision type that requires resolved player identity never received
  one, per the ingestion module's own "identity resolution out of scope"
  precedent). **This status must never be used as a synonym for "the
  answer was that nothing happened"** -- see `NOT_APPLICABLE` below for
  that case. This is the status this cycle's own directive calls for
  explicitly: "never fabricate regret."
- **`NOT_APPLICABLE`** -- the decision type or the real, observed outcome
  structurally has no metric to compute, as a matter of the CONTRACT'S
  OWN RULES, not missing data: a rejected/unknown TRADE's realized-outcome
  metric (Section 2), a `TRADE_FINDER` package that was never accepted,
  or `DRAFT` (deferred for the whole cycle).

**The critical distinction, restated once more for absolute clarity**:
`INSUFFICIENT_DECISION_CONTEXT` says "we cannot honestly know," while
`NOT_APPLICABLE` says "we honestly know that no such metric exists for
this real outcome." Confusing the two in either direction is the single
most dangerous failure mode this contract exists to prevent.

## 5. Hindsight rules

Restated and EXTENDED to the new evaluation layer (Work Unit 1) on top of
the ingestion module's own already-proven no-future-leakage guarantee:

1. Every "what was known/eligible/recommended AT THE TIME" fact an
   `OutcomeEvaluation` uses comes ONLY from the trace's own frozen fields
   (`recommendation`, `alternatives`, `roster_state_player_ids`,
   `free_agent_state_player_ids`, `owner_action`) or from the already-
   ingested `outcome.detail` payload -- never from a fresh "current"
   roster/free-agent/market read performed at evaluation time.
2. `OutcomeEvaluation` computation performs **zero network I/O** and
   accepts **zero "current state" parameter of any kind** -- it operates
   purely over an already-loaded `DecisionTraceRecord`. This is enforced
   structurally in Work Unit 1's tests (a function-signature check, not
   only a docstring promise).
3. A "best available alternative" (STREAMER) or "eligible alternative"
   (START_SIT) is always drawn from the trace's own frozen, at-recommend-
   -time set -- never recomputed from the full week's real hindsight
   results. This is the ingestion module's own already-proven guarantee
   (`test_no_future_leakage_streamer_alternatives_never_see_a_hindsight_
   best_pick`), reused unchanged, not re-implemented.
4. The evaluation layer NEVER promotes `bestAvailableAlternativeActualPoints`
   (STREAMER) into the class's primary opportunity-cost metric -- doing so
   would silently substitute a hindsight-best comparison for a
   recommendation-vs-actual one. This is a NEW, explicit rule this
   contract adds (Section 2's K/DST_STREAMER definition) to prevent a
   future worker from taking an easy-looking shortcut.
5. Real, dated, AFTER-recommendation data (a matchup entry for the
   recommendation's own week or later, a transaction log for the period
   after the recommendation, horizon matchup entries for subsequent weeks)
   is the ONLY category of information the evaluation layer is allowed to
   treat as "the outcome" -- and only ever data that was fetched with a
   real, recorded `outcomeSourceAsOf` timestamp strictly at or after
   `recommendationGeneratedAt` (Work Unit 1's canonical event contract,
   Section 6).

## 6. Aggregation rules

- **Per-class only.** No cross-class leaderboard, index, or blended score
  is ever computed -- not in the backend, not in the History UI. A
  START_SIT opportunity-cost point-delta and a FAAB bid-calibration dollar
  margin are not commensurate and must never be added, averaged, or
  ranked together.
- Aggregation (a per-class summary: hit rate, mean opportunity cost,
  calibration accuracy, etc.) is explicitly **NOT built by this pass**
  (Work Unit 1 only builds the single-event `OutcomeEvaluation` contract
  and its per-event metric extraction). Real per-class summaries are the
  next worker's job (Section 9, Work Units 3-6).
- When a future per-class summary IS built, it must independently apply
  the Section 7 minimum-sample rule for THAT class -- a class clearing the
  bar never implies another class does.

## 7. Minimum sample rules

The History UI (V2, prior cycle) already names a real, disclosed,
deliberately-conservative constant:
`MIN_SAMPLE_SIZE_FOR_PER_CLASS_ROLLUP = 20` in
`desktop/apps/redraft/src/decision-history-format.ts`. This pass:

- **Reuses the same number, 20**, as the backend-side constant
  (`MIN_SAMPLE_SIZE_FOR_PER_CLASS_SUMMARY` in
  `prospective_outcome_evaluation_v1_service.py`) for consistency between
  frontend and backend -- both are disclosed-arbitrary, not statistically
  derived, exactly as the frontend constant's own comment already says.
- **Flags, as an open issue (Section 9), the duplicated-constant risk**:
  the same number now exists in two languages/files with no single source
  of truth. Not fixed this pass (would require either the backend
  exposing it over the API for the frontend to read, or a build-time
  constant-sharing mechanism neither of which exists yet) -- a real,
  disclosed gap, not silently left undocumented.
- Below 20 real outcomes for a given class, any future per-class summary
  UI/computation MUST show "NOT ENOUGH DATA YET" (or an equivalent honest
  message) rather than a number. This pass's own `OutcomeEvaluation`
  layer operates on ONE event at a time and is exempt from this rule
  (it never aggregates) -- the rule applies to any future SUMMARY/rollup
  built on top of it.

## 8. What is explicitly NOT comparable across classes

- START_SIT/K_STREAMER/DST_STREAMER's opportunity-cost is measured in
  **fantasy points**, is bounded to a single week, and can be `None` for
  reasons unrelated to a good/bad recommendation (missing real points
  data for one side of the comparison).
- WAIVER/ADD_DROP/FAAB's subsequent-value metrics are measured in
  **fantasy points over a 4-week bounded horizon** -- NOT the same
  quantity as START_SIT's single-week point delta, even though both are
  "points." A 4-week cumulative total and a 1-week delta must never be
  placed on the same axis or chart.
- FAAB's `bidRangeCalibration` is measured in **dollars**, a completely
  different unit from every points-based metric above -- and is itself
  never merged with FAAB's own `playerDecisionQuality` (Section 2).
- TRADE's `netSubsequentPointsDelta` is a **net** (received minus given)
  points figure over the bounded horizon -- not comparable to WAIVER's
  gross subsequent-points total, since a trade always has an offsetting
  cost side that a waiver claim does not.
- DRAFT has no live metric this cycle at all -- it is not "0" or
  "unavailable" on the same axis as any other class; it is
  `NOT_APPLICABLE` by design (Section 2), a structurally different
  category from every other class's real number.
- `evaluationStatus` counts (how many traces are `PENDING_OUTCOME` vs.
  `EVALUATED` vs. `NOT_APPLICABLE`, etc.) are themselves per-class-only
  bookkeeping, never combined into a single "X% of recommendations have
  been evaluated" figure across classes -- doing so would imply the
  classes are counted in comparable units, which Section 8 as a whole
  exists to rule out.

## 9. Open items this contract deliberately defers (for the next worker)

Per the directive's own explicit framing, this pass (Worker 1) builds
Work Units 0-2 only -- the preregistered contract, the canonical
single-event outcome-evaluation contract/schema, and the outcome-source
adapters. Real per-class EVALUATORS (Work Units 3-6: Start/Sit, Waiver,
Add/Drop, FAAB) -- meaning per-class AGGREGATION/SUMMARY across many real
outcomes, gated by Section 7's minimum-sample rule, plus any deeper
regret-quality judgment beyond the single already-computed metric this
pass exposes -- are explicitly the next worker's job. See
`docs/codex/prospective_outcomes_v1/LEDGER.md` for the exact handoff.

A real ROS evaluation window (Section 3), the duplicated
minimum-sample-size constant (Section 7), ADD_DROP's still-uncomputed
dropped-player subsequent value (Section 2, inherited from the prior
cycle), and the still-missing identity resolver for canonical-id decision
types (inherited from the prior cycle, unchanged) are also carried
forward, unresolved, into that same ledger.
