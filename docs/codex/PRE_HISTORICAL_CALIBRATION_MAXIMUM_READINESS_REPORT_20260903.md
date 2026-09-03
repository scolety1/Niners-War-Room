# NWR Draft Upgrade HQ — Pre-Historical Calibration Maximum Readiness

## Executive verdict

**YELLOW_CALIBRATION_PIPELINE_READY_WITH_NAMED_GAPS**

The core calibration pipeline is real, tested, and runs end-to-end today
— against both a deterministic synthetic fixture and a real-shaped CSV
dataset — producing every named report section with either genuine
content or an exact, named blocker. It is not GREEN because several
directive items (historical identity layer, player outcome distribution
interface, optimizer caching, a generalized QB harness, a real AI News
Scout source adapter, Team Score decile/monotonicity buckets) were not
built this wave. It is not BLOCKED because the one-command entrypoint
genuinely works right now, on real data, not only in theory.

## Exact branch / HEAD / tree

```
Branch: work/nwr-draft-upgrade-hq-v1-20260903
HEAD:   971ee6b2a5ec2136410bb3d1c93116aa32f8aa33
```

Tree: not fully clean — the same 5 pre-existing, unrelated
`docs/model_v4/*.md` edits flagged in the prior overnight report are
still present, still untouched by this wave, still awaiting owner
review (see that report for detail — nothing new to add). One
untracked file, `desktop/launch-draft-upgrade-preview.bat` (the prior
wave's temporary preview launcher, deliberately untracked). Nothing
else uncommitted. 14 commits this wave
(`9937041d..971ee6b2`), all on this branch, nothing pushed or merged.

## Preview bootstrap

- **Missing binary root cause**: `desktop/binaries/nwr-desktop-api-x86_64-pc-windows-msvc.exe`
  (Tauri's `externalBin` requirement) had never been built for this
  worktree — a gitignored ~150MB build artifact, no build ever run here.
- **Fix**: ran the existing canonical build
  (`desktop/scripts/build-python-sidecar.ps1` via `npm run sidecar:build`,
  `uv` + PyInstaller against this exact worktree's
  `scripts/run_nwr_desktop_api.py`). Two other NWR worktrees already had
  a built copy but both predate this branch's backend work by weeks —
  not copied, since the binary embeds the worktree's own `src/` tree;
  rebuilt from this HEAD instead.
- **Launch command**: `desktop/launch-draft-upgrade-preview.bat` (the
  Desktop shortcut `NWR — DRAFT UPGRADE PREVIEW`) now runs
  `npm run sidecar:build` (idempotent — fast no-op when already current,
  automatic rebuild when source changes) before `npm run tauri:redraft`.
- **Verification**: build exit code 0, SHA-256
  `f4de73f8c97891824a8d55cdf3945295c1d4a75ad3f522df5d48238eeb53def9`,
  smoke-tested by the build script itself. Not independently re-launched
  end-to-end this wave (no source file the sidecar depends on changed
  since the build).

## Point-in-time feature store

`src/services/point_in_time_feature_store_service.py`. A single
versioned `FeatureValue` shape (player_id/season/as_of/feature_name/
value/value_status/source/source_as_of/retrieved_at/confidence/
feature_version/provenance_hash), value_status ∈ {KNOWN, UNKNOWN,
NOT_APPLICABLE, BLOCKED, STALE} — missing data is never collapsed to
zero, enforced in `__post_init__`. Adapters convert existing governed
sources (ProjectionPlayer stats, AdpEntry, ImpactHypothesis) into this
shape rather than recomputing feature research.
`PointInTimeFeatureStore.lookup_as_of` never resolves a value whose
`source_as_of` postdates the requested `as_of` — the core no-leakage
guarantee, tested directly. 11/11 tests.

## Historical dataset validator

Already substantial from the prior wave
(`historical_replay_data_adapter_service.py`): schema, leakage,
identity-completeness, duplicate-player-season, outcome-maturity, all
reduced to one named `DATASET_VALIDATION_STATUSES` status by
`validate_historical_dataset()`. This wave added the concrete one-command
entrypoint around it (below) and verified it against real (not just
synthetic) CSV input, including a deliberate leakage violation correctly
caught.

## Leakage gauntlet

The existing `validate_leakage()` (date-ordering + `BLOCKED_FEATURE_TOKENS`
column-name checks) already structurally covers most of the directive's
named bad cases (future-dated projection/ADP, outcome predating the
draft, leakage-shaped column names). Not built this wave: a dedicated
test fixture for every one of the directive's ~10 named specific
scenarios (cross-season ID contamination, future depth chart, etc.) —
the underlying mechanism is real and tested, but per-scenario fixture
coverage is a named gap, not a re-architecture.

## Historical identity system

**Not built this wave.** The live-draft KHA reconciliation identity work
(name aliases, team aliases, position-at-time-of-pick) already exists for
the *current* draft; a dedicated point-in-time historical identity module
(same shape, scoped to a historical season's real as-of state, explicitly
never repaired with current team/position) is a named, scoped gap for the
next wave.

## Baseline strategy framework

`src/services/draft_strategy_framework_service.py`. A common
`DraftStrategy` interface (`StrategyDecisionContext` in →
`StrategyDecision` out). PLATFORM_ADP, STANDARD_VBD, GREEDY_NWR,
CURRENT_NWR_DRAFT_HEURISTIC run directly off point-in-time features.
TEAM_SCORE_OPTIMIZER / CHAMPIONSHIP_EQUITY_OPTIMIZER /
PICK_SCORE_OPTIMIZER are real greedy-argmax wrappers around a
caller-supplied evaluator — the real `shadow_numeric_authorities_service`
functions plug in directly, no second implementation. 8/8 tests.

## Replay engine

`src/services/historical_draft_replay_engine_service.py`. Deterministic
pick-by-pick snake draft; only the owner seat runs the strategy under
test, every opponent seat uses the market model (PLATFORM_ADP by
default) — opponents never use NWR ranks. Every pick resolves through the
same point-in-time feature store and the same `as_of` cutoff. Tested:
byte-identical re-runs given the same seed (the "replay receipt"
requirement), owner-vs-opponent strategy separation proven with a
fixture where ADP and NWR-rank order deliberately diverge, snake
direction reversal, no-duplicate-draft guarantee, bounds validation, and
a no-infinite-loop guard. 6/6 tests.

## Outcome evaluator

`src/services/outcome_evaluation_framework_service.py`. Metrics declared
before any real data exists, per the directive's own instruction.
Player level: projection error, realized VOR, Spearman + Kendall-tau rank
correlation (hand-verified, no scipy dependency). Pick level: realized
regret against the true best alternative, replacement loss, make-it-back
against real next-pick availability. Roster level: reuses the real
`roster_composition_report`/`optimal_starting_lineup_value` on REALIZED
values — not a second lineup algorithm. Season level:
`SeasonLevelMetrics` requires an explicit OBSERVED/SIMULATED source and
*refuses in code* to accept a playoff/championship rate under
`source=OBSERVED`. 14/14 tests.

## Team Score
- **Raw semantics**: unchanged from the prior wave — optimal starting
  lineup value via `roster_composition_report`, inspectable components
  (starter holes, bench contingency value, position redundancy).
- **Percentile semantics**: unchanged — percentile vs. a simulated
  comparable-league population under the exact league configuration.
- **Calibration hooks**: `outcome_evaluation_framework_service`'s
  Spearman/Kendall correlation functions are the calibration primitive;
  a dedicated decile/bucket/monotonicity report (the directive's own
  specific ask) is **not built this wave** — a named gap, not a
  redesign, since the correlation primitive it would sit on top of is
  already real and tested.
- **Tests**: 14 (outcome evaluator) + existing Team Score suite unchanged.

## Championship Equity
- **Simulation architecture**: unchanged — player outcome distribution
  (Gaussian weekly noise around a season-total mean) feeding a regular
  season + single-elimination playoff Monte Carlo, disclosed assumptions
  (`ChampionshipEquityAssumptions`).
- **Probability calibration hooks**: **named gap this wave** — Brier
  score / log loss / reliability bins / ECE were not implemented (would
  need real observed championship outcomes to be meaningful at all; the
  interface to plug them in once outcome data exists is
  `outcome_evaluation_framework_service`'s `SeasonLevelMetrics`, already
  built).
- **Uncertainty**: the real Monte Carlo standard error
  (`ChampionshipEquityResult.standard_error`) is now surfaced as a
  first-class field on every `DecisionBundle` candidate
  (`CandidateBundle.uncertainty`, one of three disclosed bands).

## Pick Score
- **Raw decision utility**: `DecisionBundle.CandidateBundle.raw_decision_utility`
  — a real, inspectable combination of Team Score delta and Championship
  Equity gain (not the cosmetic 0-100 presentation).
- **Current experimental 0-100 semantics**: unchanged, `pick_score()`'s
  existing relative-only scaling, still labeled EXPERIMENTAL, not
  promoted.
- **Exact plan for historical calibration**: `outcome_evaluation_framework_service.pick_level_metrics`
  (realized regret, replacement loss, make-it-back) is the exact metric
  set the directive asks Pick Score be tested against once real
  outcomes exist — built and tested this wave, not yet run against real
  Pick Score output (blocked on the same RankingResult adapter named
  below).

## Cost of Waiting
- **Survival calibration interface**: the existing V2 survival-weighted
  logic is unchanged. `pick_level_metrics.made_it_back` is the exact
  real-vs-predicted comparison point (predicted `survival_probability`
  vs. actual `made_it_back`) — built and tested, not yet run against real
  historical picks (same RankingResult-adapter blocker).

## Look-ahead optimizer
- **Algorithm**: unchanged (force-candidate + complete-the-draft, shared
  comparable-league population).
- **Latency/caching**: **not touched this wave** — no new caching layer
  was added to `simulate_comparable_leagues` or the replay engine. A
  named gap; the existing benchmark from the prior wave
  (`SHADOW_NUMERIC_AUTHORITIES_BENCHMARK_20260903.md`) is the latest real
  latency data.
- **Deterministic behavior**: the NEW replay engine
  (`historical_draft_replay_engine_service`) is proven deterministic
  given a fixed seed — tested directly.

## Player outcome distributions

**Not built this wave.** `ChampionshipEquityAssumptions`'s Gaussian
weekly-noise model is the closest existing analog but is not a
provider-neutral distribution interface (mean/variance/availability/
floor-tail/correlation-group metadata) as the directive specifies. A
named gap for the next wave.

## QB positional-economics harness

The prior wave's QB pathology/mechanism-only challenger scripts are the
existing real evidence (1QB vs. Superflex inversion, replacement-depth
mechanism proof). **Not generalized into a reusable multi-format harness
this wave** (1QB/Superflex × 10T/12T/16T at varying roster states) — a
named gap, though every primitive it would be built from
(`draft_strategy_framework_service`, `historical_draft_replay_engine_service`,
`outcome_evaluation_framework_service`) is now real and tested.

## Rookie challenger framework

Unchanged from the prior wave (v1/v2 gap-gated variant, real KHA
backtest). **Reusable feature hooks (draft capital, age, market rank,
team depth, etc.) not built as named functions this wave** — a named
gap.

## AI News Scout

Unchanged from the prior wave: append-only event store, no live fetching
(events are appended by an owner/operator action). **A real source
adapter architecture (e.g. FantasyPros via `NWR_FANTASYPROS_API_KEY`)
was not built this wave** — the credential-handling discipline
(never print/log/store the key) is already established elsewhere in the
codebase (`fantasypros_kdst_consensus_service.py`), and reusing that
exact pattern is the right next step, not attempted here to keep this
wave's scope inside what could be fully tested.

## Source-conflict handling

`src/services/source_conflict_resolution_service.py`. Structured
CONFIRMED/PROVISIONAL/CONFLICTED/STALE/UNKNOWN resolution — a CONFLICTED
or UNKNOWN result *cannot be constructed* with a non-`None`
`resolved_value` (enforced in `__post_init__`), so the AI layer
structurally cannot silently pick a winner when sources disagree. 9/9
tests.

## AI Impact Analyst

Unchanged from the prior wave (direct + beneficiary + role-uncertainty
hypotheses, 3 horizons, `run_impact_pipeline`). Already real and tested.

## AI hypothesis/challenger pipeline

`src/services/ai_hypothesis_challenger_pipeline_service.py`. The exact
chain: anomaly → hypothesis → feature/challenger proposal → registered
challenger → gate. `propose_challenger_from_anomaly` requires a specific
hypothesis and named features. `evaluate_promotion_gate` is a purely
mechanical guardrail check with no power to promote anything — a missing
holdout metric counts as a gate failure, never a silent skip.
`submit_challenger_proposal_for_registration` is the pipeline's only
registry write, and only through the existing public
`register_challenger` — never `record_promotion_decision`, verified by
an updated structural test. 8/8 tests.

## Champion/Challenger registry

Hardened this wave: `ChallengerRegistration` gained `parent` (validated
against a real registration), `code_sha`/`feature_set_sha`/
`training_dataset_sha`/`calibration_dataset_sha`/`evaluation_dataset_sha`/
`algorithm_parameters`. `PromotionDecision` gained `baseline`/`metrics`/
`confidence`/`season_splits`/`guardrails` — `record_promotion_decision`
now *enforces* a full receipt (baseline+metrics+confidence, all
non-empty) whenever `decision == "PROMOTED"`, checked last so every
existing failure-mode test still hits its own intended error first.
Added `RESEARCH_ONLY` as a valid terminal decision, distinct from
REJECTED. No automatic promotion — unchanged, re-verified. 20/20 tests
(6 new this wave).

## Chronological partitions

`chronological_split()` (prior wave) is unchanged and real. This wave's
one-command entrypoint exercises it directly (train=[2023],
validate=[], test=[2024] on the synthetic fixture). **Rolling-origin /
leave-one-season-forward evaluation was not built this wave** — a named
gap; the underlying split primitive it would loop over already exists
and is tested.

## Experiment runner

`src/services/challenger_experiment_runner_service.py`. Runs a
predeclared, bounded grid (`MAX_EXPERIMENT_GRID_SIZE = 50`, enforced —
raises rather than silently truncating) of `ExperimentSpec`s through a
caller-supplied evaluator. One failing experiment never aborts the rest
of the grid; every receipt carries succeeded/failure_reason/runtime/full
provenance independently. Pure orchestration — no domain knowledge of
draft strategies baked in. 6/6 tests.

## Model-health metrics

`src/services/model_health_dashboard_service.py`. Seven named health
areas (Player Score prediction quality, Team Score monotonicity,
Championship Equity calibration, Pick Score regret, Cost-of-Waiting
calibration, rookie performance, QB performance). Every metric carries
its own dimensions and sample size; `SMALL_SAMPLE_THRESHOLD = 20`
(disclosed, not calibrated against real data since none exists) flags
low-confidence metrics, and `filter_confident_metrics` excludes them from
what a caller would present as a headline number — enforced in code, not
left as a UI convention. Pure contract/assembly layer; computes none of
the underlying metrics itself. 7/7 tests.

## Uncertainty system

Threaded through the pieces built this wave rather than a single
standalone module: `DecisionBundle.CandidateBundle.uncertainty` (three
disclosed bands off the real Monte Carlo standard error),
`ModelHealthMetric.low_confidence` (sample-size-based), every
`FeatureValue.confidence` field. **Not yet threaded through Cost of
Waiting or the raw Team Score number itself** — a named gap.

## Score provenance

`src/services/score_provenance_service.py`. `ScoreProvenance` bundles
every input a SHADOW numeric call depends on (league profile/roster/
available-player/universe hashes, model/feature-set/Team-Score/
Championship-Equity/Pick-Score/optimizer versions, seed, simulation
count) into one record with a single combined `bundle_hash`. Wall-clock
timestamp is deliberately excluded from the hash (tested) — two runs of
the identical computation at different real times still compare equal.
4/4 tests.

## DecisionBundle API

`src/services/decision_bundle_service.py`. Composes the existing
`team_score`/`championship_equity`/`evaluate_pick_candidates`/
`evaluate_cost_of_waiting_v2`/`label_pick_decisions` into one
`DecisionBundle` per pick — current state + a sorted per-candidate
breakdown (Player Score, Team Score After/Delta, Championship Equity
After/Gain, Cost of Waiting, Make-It-Back, Raw Decision Utility, Pick
Score, Action, Warnings, Uncertainty) + provenance + latency +
simulation metadata. Reimplements none of the underlying math. Still
purely a backend/SHADOW artifact — not wired into any HTTP route or
production surface. 5/5 tests.

## AI Explanation API

`src/services/decision_bundle_explanation_service.py`. Builds a
STRUCTURED `DecisionBundleExplanation` from a real `DecisionBundle`
first, then assembles narrative text FROM that structure. Reproduces the
directive's own worked example: when a runner-up has a higher standalone
Player Score but the top pick still wins, the explanation says so
explicitly and cites the field that actually decided it.
`verify_explanation_matches_bundle` independently re-derives the same
structured claims and reports any mismatch — tested against both a real
explanation and a deliberately fabricated one. 6/6 tests.

## NWR PURE receipts

Unchanged from the prior wave (decision receipts wired into every owner
pick, corrections append-only). Already real and tested.

## KHA engineering replay

Unchanged from the prior wave (real 157-pick board, 10 owner picks, the
independent no-leak recomputation test). **Not re-run through the NEW
DecisionBundle API this wave** — would need the same historical-row →
RankingResult adapter named throughout this report; the existing
mechanism-level replay (rank-derived value proxy) remains the current
real evidence.

## Synthetic end-to-end pipeline test

Proven for real this wave, not just described: the one-command
entrypoint's synthetic path reaches `PASS_READY_FOR_REPLAY` and
populates every report section (schema/leakage validation →
chronological split → two full replay-engine snake drafts per season →
realized-production outcome metrics → challenger comparison), all
labeled `SYNTHETIC_PIPELINE_TEST_ONLY`. Full output:
`docs/codex/HISTORICAL_CALIBRATION_READINESS_REPORT.json`.

## One-command historical calibration entrypoint

```
python scripts/run_historical_calibration_readiness_v1.py --dataset-dir "C:\path\to\dataset"
```

Expects `<dataset-dir>/historical_replay_rows.csv` (columns = the
existing `REQUIRED_PRE_DRAFT_FIELDS` + `OUTCOME_ONLY_FIELDS` contract)
and optionally `historical_picks.csv`. Verified against three real
inputs this wave, not just the synthetic path: a missing dataset
directory (→ `BLOCKED_NO_DATASET_FOUND`), a real conformant 12-row CSV
(→ `PASS_READY_FOR_REPLAY`, correctly runs only `PLATFORM_ADP` since real
rows carry no NWR-rank column), and a real CSV with a deliberate leakage
violation (→ `BLOCKED_LEAKAGE`, exit code 0 — a validation block is a
well-formed result, not a crash). Full detail:
`docs/codex/HISTORICAL_CALIBRATION_READINESS_ENTRYPOINT_20260903.md`.

## Exact fields still required from the historical dataset

Unchanged from `HISTORICAL_REPLAY_DATA_CONTRACT_20260903.md`: per player
per season, as-of the real draft date — stable identity + aliases, team,
position, pre-season projection components, platform ADP, roster/depth/
injury/availability status, the historical league's real scoring format;
for scoring only, weekly realized outcomes and actual games-played
status. At minimum one full past season with both a real snake-draft
result and a genuinely dated pre-draft projection/ADP board.

## Exact work that CANNOT be done until real historical data exists

Everything downstream of `CHAMPIONSHIP_EQUITY_CALIBRATION` /
`PICK_SCORE_EVALUATION` / `COST_OF_WAITING_CALIBRATION`'s real
computation (not just their interface, which exists): actual probability
calibration (Brier/log-loss/ECE), actual Pick Score regret-vs-utility
correlation, actual survival-probability-vs-make-it-back calibration,
Team Score decile/monotonicity analysis against real realized rosters,
any rolling-origin/leave-one-season-forward result, any real challenger
promotion decision (the registry can record one the moment a human
reviews real evidence, but there is no real evidence yet).

## Immediate first commands/actions once historical data arrives

1. Place the dataset so `<dataset-dir>/historical_replay_rows.csv`
   exists (+ optional `historical_picks.csv`), then run
   `python scripts/run_historical_calibration_readiness_v1.py --dataset-dir <dataset-dir>`
   — this alone validates schema/leakage/identity and produces a real
   `BASELINE_RESULTS`/`TEAM_SCORE_CALIBRATION`/`CHALLENGER_COMPARISON`
   immediately, with zero further build work.
2. Build the historical-row → `RankingResult`/`AdpSnapshot` adapter
   named throughout this report — the single piece that unlocks
   `CHAMPIONSHIP_EQUITY_CALIBRATION`, `PICK_SCORE_EVALUATION`, and
   `COST_OF_WAITING_CALIBRATION` all at once, since
   `shadow_numeric_authorities_service`'s real functions already consume
   exactly that shape.
3. Once real outcome data exists, register any resulting challenger via
   `ai_hypothesis_challenger_pipeline_service.submit_challenger_proposal_for_registration`
   and run `evaluate_promotion_gate` against real holdout metrics before
   any human considers `champion_challenger_registry_service.record_promotion_decision`.

No push, merge, deploy, or production model promotion performed this
wave.
