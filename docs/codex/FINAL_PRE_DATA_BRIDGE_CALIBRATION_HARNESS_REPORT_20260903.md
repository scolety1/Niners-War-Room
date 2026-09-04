# NWR Draft Upgrade HQ — Final Pre-Data Bridge + Calibration Harness

## Final verdict

**YELLOW_PRE_DATA_BACKEND_READY_WITH_NAMED_IMPLEMENTATION_GAPS**

Not GREEN: real, non-data-blocked code work remains (live-drafting
DecisionBundle wiring into Draft Room V2's HTTP surface, a rolling-
origin multi-season partition loop, provider-neutral player outcome
distributions, a generalized QB/format harness, a real AI News Scout
source adapter) — none of it requires the real historical dataset to
build, so GREEN would overclaim. Not BLOCKED: the primary named
blocker from the prior wave (historical-row → RankingResult) is closed
and proven end-to-end this wave, on both synthetic and real-shaped
data, through the full calibration pipeline.

## Exact branch / HEAD / tree

```
Branch: work/nwr-draft-upgrade-hq-v1-20260903
HEAD:   fe689dde (docs: DecisionBundle UI wiring deferred, section 21)
```

Tree: not fully clean — the same 5 pre-existing, unrelated
`docs/model_v4/*.md` edits flagged in every prior report are still
present, untouched, still awaiting owner review. One untracked file,
`desktop/launch-draft-upgrade-preview.bat` (deliberately untracked
preview launcher from an earlier wave). 11 commits this wave
(`9542b69c..fe689dde`).

## Historical row → RankingResult bridge

`src/services/historical_ranking_bridge_service.py`. Builds a real
`ProjectionSnapshot` from historical rows and calls the real,
unmodified `generate_rankings()` — not a second scoring engine. A
player whose row cannot supply real projection stat components (or a
real K/DST override) is EXCLUDED, never scored as an implicit zero,
and recorded with an explicit reason. Also builds a real `AdpSnapshot`
and populates the point-in-time feature store with market ADP and the
production-computed NWR rank/VOR — a real bug in this exact wiring
(ADP/rank features built into the wrong object, silently starving every
strategy) was caught by the tournament runner's own tests and fixed
within this wave, not missed. Full field map:
`docs/codex/HISTORICAL_RANKINGRESULT_FIELD_MAP_20260903.md`.

## HistoricalDecisionState

`src/services/historical_decision_state_service.py`. The one reusable
constructor: season, as_of, league profile, pick/round, owner slot,
rosters before the pick, available players, the bridged ranking/ADP/
feature store, strategy version — built only from what was knowable at
`as_of`. No realized-outcome input anywhere in the module.

## Team Score historical wiring

Real, via `evaluate_historical_candidates()` calling the unmodified
`team_score()` directly on before/after roster states — the same
isolation methodology the prior wave's QB pathology demo established.

## Championship Equity historical wiring

Real, via the unmodified `championship_equity()` on the same before/
after states, using a comparable-league population built from the
bridged ranking. Label stays SIMULATED RESEARCH throughout.

## Cost of Waiting historical wiring

Real, via a disclosed, versioned ADP-distance survival heuristic
(`estimate_historical_survival_probability`) — deliberately NOT the
live Draft Room's CPU Monte Carlo (that machinery is keyed to a
separate `draft_order()` implementation from this wave's replay
engine; bridging them without dedicated alignment testing was judged a
real risk and not attempted). Every `CandidateBundle.uncertainty` says
`HISTORICAL_PROXY` explicitly so it is never confused with the live
mechanism. Returns `None` (never fabricated) when no real market ADP
exists for a candidate.

## Pick Score historical wiring

Real, via the unmodified `pick_score()` over the before/after Team
Score/Championship Equity pairs — the same production ranking function,
not a parallel one.

## Raw Decision Utility

Made fully inspectable this wave: `CandidateBundle` now carries
`team_score_utility_component` and `equity_utility_component`
separately, not just the combined scalar.
`EQUITY_TO_PERCENTILE_WEIGHT = 100.0` is named, disclosed, and stated
to have no empirical basis — never disguised by normalization. Full
writeup: `docs/codex/RAW_DECISION_UTILITY_CONSTRUCTION_20260903.md`.

## Pick Score calibrator

`calibration_toolkit_service.fit_pick_score_calibrator` — a hand-
written, exact Pool Adjacent Violators isotonic fit (raw utility → 0-100
monotonic-by-construction). Every fit states `data_source`
(`PIPELINE_TEST_ONLY` or `REAL_EVIDENCE`); the synthetic run's fit
carries `PIPELINE_TEST_ONLY` visibly in its own `model_version` string
— never mistakable for a real calibration.

## Team Score calibrator

`calibration_toolkit_service.bucket_team_score_outcomes` — deciles/
buckets, mean realized value per bucket, a real monotonicity check, and
Spearman correlation (reused, not reimplemented). Run for real this
wave against the synthetic pipeline's own (Team Score, realized
production) pairs — `spearman` came back `None` (not a fabricated
number) because the tiny synthetic trial count produced tied
percentiles; an honest degenerate-case result, not a defect.

## Championship Equity calibrator

`calibration_toolkit_service.evaluate_probability_calibration` — Brier
score, reliability bins, expected calibration error. Requires an
explicit `label_source` (OBSERVED/SIMULATED) with no default; never
invents an observed win/loss label. Not yet run inside the one-command
entrypoint (no real or synthetic binary championship outcome exists to
feed it yet) — the tool is real and tested standalone
(`tests/test_calibration_toolkit_service.py`), wiring it into the
entrypoint is a small remaining step once a league-simulation-to-binary-
outcome bridge is built.

## Strategy tournament

`strategy_tournament_service.run_strategy_tournament` — every supplied
strategy runs through the same replay engine, historical state,
opponent model, league rules, and seed. Wired for real into the one-
command entrypoint this wave (`STRATEGY_TOURNAMENT` section, both
seasons, both strategies, real construction-failure counts and
runtimes).

## Counterfactual evaluator

`strategy_tournament_service.build_pick_counterfactual` — selected
player vs. the real top-ADP and top-NWR-rank alternatives, evaluated
through the roster-construction-aware Team Score/Championship Equity
machinery, never a bare point-total comparison. Realized outcomes,
when supplied, are a strictly separate field computed after the
pre-freeze evaluation. Not yet wired into the one-command entrypoint
(the entrypoint currently reports tournament/candidate results, not a
per-pick counterfactual table) — the module and its tests are real and
ready; wiring is a small remaining step.

## Common-random-numbers support

Every tournament entry shares one `seed` parameter (tested directly:
`test_tournament_uses_the_identical_seed_for_every_strategy`), and the
one-command entrypoint's bridge-dependent section builds ONE
`comparable_leagues` population per season and shares it across every
strategy's Championship Equity evaluation in that season, rather than
resampling per strategy.

## Calibration report generator

The one-command entrypoint now produces every section 15 asks for on a
successful bridge run: `DATASET_READINESS_REPORT`, `LEAKAGE_REPORT`,
`IDENTITY_REPORT`, `BASELINE_RESULTS`, `TEAM_SCORE_CALIBRATION`,
`CHAMPIONSHIP_EQUITY_CALIBRATION`, `COST_OF_WAITING_CALIBRATION`,
`PICK_SCORE_EVALUATION`/`PICK_SCORE_CALIBRATION`,
`STRATEGY_TOURNAMENT`, `CHALLENGER_COMPARISON`, `FAILURE_SLICES`,
`CALIBRATION_GATES`, `MODEL_HEALTH_REPORT`, `AI_RESEARCH_AGENT_INPUT` —
one JSON artifact
(`docs/codex/HISTORICAL_CALIBRATION_READINESS_REPORT.json`), no manual
assembly.

## Predeclared gates

`calibration_acceptance_gates_service.py` — every `GateSpec` for Team
Score/Championship Equity/Pick Score/Cost of Waiting/Rookie Challenger
declared before any real result was seen. Where no real prior basis
exists for a number, `threshold=None` is explicit, and
`evaluate_gate` returns `UNSCORABLE` rather than a fabricated
PASS — exercised for real in the entrypoint's `CALIBRATION_GATES`
section (mostly UNSCORABLE on the tiny synthetic run, honestly).

## Failure slicing

`failure_analysis_service.py` — real slicing by position/strategy/
season this wave (via the entrypoint's tournament results), flagging
any slice under 3 samples as low-confidence rather than hiding it.
Ready for any dimension a future real run supplies (rookie/veteran,
league size, format, market tier, ...).

## AI research-agent input contract

`ai_research_agent_input_service.py` — bounded structured evidence
only. `validate_ai_research_agent_response` mechanically enforces the
directive's three hard rules: no historical-evidence mutation
(structural), no promotion (rejects promotion-shaped response fields),
no favorable-only slicing (requires acknowledging a real worst slice
when one exists).

## Synthetic full-pipeline result

Real, this wave: `PASS_READY_FOR_REPLAY`, every report section
populated with genuine (labeled `SYNTHETIC_PIPELINE_TEST_ONLY`)
content end-to-end — rows → feature store → RankingResult bridge →
HistoricalDecisionState → strategies → replay → Team Score →
Championship Equity → Cost of Waiting → Pick Score → calibration →
challenger comparison → model health → report. Six deliberately
injected bad cases (missing required field, unparseable date,
duplicate player-season, stale/immature outcome, unresolved identity
conflict, missing projection stats) each proven to block or degrade
safely — never a crash, never a silent pass
(`tests/test_run_historical_calibration_readiness_v1.py`).

## Real-shaped input result

Proven this wave, not just asserted: a plain CSV (not the synthetic
generator's in-memory shape) with real stat-category columns reaches
the exact same real (non-blocked) `CHAMPIONSHIP_EQUITY_CALIBRATION`
path the synthetic run does — the bridge is not secretly overfit to
synthetic-only formatting. A real-shaped CSV WITHOUT stat columns
correctly stays honestly blocked for those sections. Never interpreted
as evidence about anything real — parsing/shape only.

## One-command entrypoint

Unchanged command:
```
python scripts/run_historical_calibration_readiness_v1.py --dataset-dir "C:\path\to\dataset"
```
Now genuinely exercises everything built this wave when a real dataset
carries real projection stat components; degrades to honest
`blocked_reason` placeholders when it doesn't.

## Exact fields still missing from the real historical dataset

Unchanged from the prior wave's contract: per player per season, as-of
the real draft date — identity/aliases, team, position, pre-season
projection (now specifically: either full stat-category components
matching `PROJECTION_STAT_FIELDS`, or a real `projected_points_override`
for K/DST — the bridge cannot reconstruct points any other way without
fabricating them), platform ADP, roster/depth/injury/availability
status, the historical league's real scoring format; for scoring only,
weekly realized outcomes.

## Exact remaining code work that does NOT require historical data

1. **Live-drafting DecisionBundle wiring** (section 21, deferred this
   wave with the exact recipe named):
   `docs/codex/DECISION_BUNDLE_UI_WIRING_DEFERRED_20260903.md` — a
   facade method building the live `RankingResult`/`comparable_leagues`
   state, an HTTP route, an API client method, real Draft Room V2 UI.
2. **Wire the pick-level counterfactual evaluator into the one-command
   entrypoint** — the module (`build_pick_counterfactual`) and its
   tests are real and ready; the entrypoint does not yet call it.
3. **A league-simulation-to-binary-outcome bridge for
   `evaluate_probability_calibration`** — the calibrator itself is real
   and tested; nothing yet turns a simulated season into the 0/1
   outcome label it consumes.
4. **Rolling-origin / leave-one-season-forward evaluation** — the
   `chronological_split` primitive it would loop over is real; the loop
   itself is not built.
5. **A generalized QB/format economics harness, a provider-neutral
   player outcome distribution interface, real rookie-challenger
   feature hooks, and a real AI News Scout source adapter** — all
   named gaps carried forward from the prior wave's report, still
   real code work, still not attempted (scope discipline, not
   forgotten).

No push, merge, deploy, or production promotion performed this wave.
