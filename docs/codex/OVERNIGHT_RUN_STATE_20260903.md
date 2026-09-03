# Overnight run state (recovery artifact, not a narrative report)

Update this after every major commit. If this session crashes, recover
from this file + `LAST_GOOD_COMMIT` rather than restarting research from
scratch.

```
CURRENT_HEAD: 971ee6b2a5ec2136410bb3d1c93116aa32f8aa33
CURRENT_BRANCH: work/nwr-draft-upgrade-hq-v1-20260903
CLEAN_STATUS: not fully clean -- 5 pre-existing unrelated docs/model_v4/*.md
  edits (untouched by this session, still awaiting owner review) +
  1 untracked file (desktop/launch-draft-upgrade-preview.bat, deliberate)
LAST_GOOD_COMMIT: 971ee6b2 "fix: reword model_health_dashboard_service docstring..."
WORKTREE_ROOT: C:\Users\codex-agent\orca\workspaces\Niners-War-Room\draft-upgrade-hq
```

## Wave: PRE-HISTORICAL CALIBRATION MAXIMUM READINESS V1 (this continuation)

Full report: `docs/codex/PRE_HISTORICAL_CALIBRATION_MAXIMUM_READINESS_REPORT_20260903.md`
(verdict: YELLOW_CALIBRATION_PIPELINE_READY_WITH_NAMED_GAPS).

14 commits this wave (`9937041d..971ee6b2`): preview bootstrap sidecar
fix, point-in-time feature store, baseline strategy framework, outcome
evaluation framework, score provenance + DecisionBundle API, AI
Explanation API over DecisionBundle, historical draft replay engine,
Champion/Challenger registry hardening (parent/code_sha/feature_set_sha/
training-calibration-evaluation dataset sha/algorithm_parameters,
promotion-receipt enforcement, RESEARCH_ONLY status), one-command
historical calibration readiness entrypoint (proven against synthetic
AND real-shaped CSV data), source conflict resolution, AI
hypothesis-to-challenger pipeline, bounded challenger experiment runner,
model health dashboard data contract.

## Regression (this wave)

Consolidated run across every module touched this wave plus every
adjacent prior-wave suite (27 test files, ~355+ tests): **355 passed / 5
pre-existing baseline failures** (same 5 as every prior wave, unchanged
names/causes, in `tests/test_desktop_application_api.py`). No frontend
file touched this wave -- last verified frontend state (40/40 vitest,
clean tsc/build) stands unchanged.

One real (self-caught, self-fixed) regression this wave: a docstring in
`model_health_dashboard_service.py` named
"champion_challenger_registry_service" in prose, tripping that module's
own structural no-unexpected-references test. Fixed by rewording (commit
`971ee6b2`); the registry's actual write-path guarantee was never
actually violated (no import, no call).

## KNOWN_BASELINE_FAILURES (backend, pre-existing all session, do not
re-investigate unless behavior actually changes)
- `test_dynasty_facade_composes_real_governed_workflows`
- `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`
- `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`
- `test_redraft_league_switching_isolates_draft_state_and_persists_active_profile`
- `test_facade_has_no_streamlit_or_app_component_dependency`
All five are in `tests/test_desktop_application_api.py`, none touch a
file any session this branch has modified, root cause (a hermetic-seed/
environment gap) established early in the original overnight session.

## BLOCKED_LANES (unchanged from the prior wave's report)
- **Formal Saturday NWR PURE 001 release**: player-universe approval
  needs fresh owner action -- `docs/codex/PLAYER_UNIVERSE_SATURDAY_RENEWAL_PACKET.md`.
- **CHAMPIONSHIP_EQUITY_CALIBRATION / PICK_SCORE_EVALUATION /
  COST_OF_WAITING_CALIBRATION real computation**: blocked on a
  historical-row -> RankingResult/AdpSnapshot adapter (named exactly in
  this wave's final report) -- the single next task, not attempted this
  wave to avoid a rushed, undertested bridge.

## CURRENT_TASK
None -- this wave's final report is written
(`PRE_HISTORICAL_CALIBRATION_MAXIMUM_READINESS_REPORT_20260903.md`).

## NEXT_TASK
See that report's "Immediate first commands/actions once historical data
arrives" section.
