# Overnight run state (recovery artifact, not a narrative report)

Update this after every major commit. If this session crashes, recover
from this file + `LAST_GOOD_COMMIT` rather than restarting research from
scratch.

```
CURRENT_HEAD: fe689dded1... (see `git rev-parse HEAD`; docs commit,
  "DecisionBundle UI wiring deferred, section 21")
CURRENT_BRANCH: work/nwr-draft-upgrade-hq-v1-20260903
CLEAN_STATUS: not fully clean -- 5 pre-existing unrelated docs/model_v4/*.md
  edits (untouched by any session, still awaiting owner review) +
  1 untracked file (desktop/launch-draft-upgrade-preview.bat, deliberate)
LAST_GOOD_COMMIT: fe689dde
WORKTREE_ROOT: C:\Users\codex-agent\orca\workspaces\Niners-War-Room\draft-upgrade-hq
```

## Wave: FINAL PRE-DATA BRIDGE + CALIBRATION HARNESS V1 (this continuation)

Full report:
`docs/codex/FINAL_PRE_DATA_BRIDGE_CALIBRATION_HARNESS_REPORT_20260903.md`
(verdict: YELLOW_PRE_DATA_BACKEND_READY_WITH_NAMED_IMPLEMENTATION_GAPS).

11 commits this wave (`9542b69c..fe689dde`): historical row ->
RankingResult bridge (closes the prior wave's named blocker),
HistoricalDecisionState + Team Score/Championship Equity/Cost of
Waiting/Pick Score historical wiring, Raw Decision Utility made
inspectable, calibration toolkit (Pick Score/Team Score/Championship
Equity calibrators), a real bug fix (bridge never populated market/NWR-
rank/VOR features into the feature store -- caught by the tournament
runner's own tests), strategy tournament + pick-level counterfactual +
common-random-numbers, predeclared calibration acceptance gates,
failure analysis slicing, AI research-agent input contract, wiring all
of the above into the one-command entrypoint (proven against both
synthetic data with 6 injected bad cases and real-shaped CSV input),
DecisionBundle UI wiring deliberately deferred with the exact next
step named.

## Regression (this wave)

Consolidated run across every module touched this wave plus every
adjacent suite it exercises (~17 test files, 233 tests): **228 passed
/ 5 pre-existing baseline failures** (same 5 as every prior wave,
unchanged names/causes, in `tests/test_desktop_application_api.py`).
No frontend file touched this wave.

Two self-caught, self-fixed regressions this wave (both the same
class): a docstring in `model_health_dashboard_service.py` and later
`calibration_acceptance_gates_service.py` each named
"champion_challenger_registry_service" in prose, tripping that
module's own structural no-unexpected-references test -- reworded both
times, no actual import/call ever existed. Separately, a real
functional bug (not a test-naming issue): the historical ranking
bridge built ADP into the AdpSnapshot but never into the point-in-time
feature store, silently starving every PLATFORM_ADP/GREEDY_NWR/
STANDARD_VBD strategy lookup -- caught by the strategy tournament's own
tests within the same wave, fixed, and locked in with 2 new regression
tests.

## KNOWN_BASELINE_FAILURES (backend, pre-existing all session, do not
re-investigate unless behavior actually changes)
- `test_dynasty_facade_composes_real_governed_workflows`
- `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`
- `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`
- `test_redraft_league_switching_isolates_draft_state_and_persists_active_profile`
- `test_facade_has_no_streamlit_or_app_component_dependency`
All five are in `tests/test_desktop_application_api.py`, none touch a
file any session has modified, root cause (a hermetic-seed/environment
gap) established early in the original overnight session.

## BLOCKED_LANES (unchanged)
- **Formal Saturday NWR PURE 001 release**: player-universe approval
  needs fresh owner action --
  `docs/codex/PLAYER_UNIVERSE_SATURDAY_RENEWAL_PACKET.md`.
- Nothing in the calibration backend is blocked on real data anymore
  for MECHANICS -- see the final report's "exact remaining code work
  that does NOT require historical data" for what's left, all of it
  pure code work.

## CURRENT_TASK
None -- this wave's final report is written.

## NEXT_TASK
See the final report's "exact remaining code work that does NOT
require historical data" section (5 named items, priority order:
live-drafting DecisionBundle wiring, counterfactual-evaluator
entrypoint wiring, probability-calibration outcome bridge,
rolling-origin evaluation, then the remaining prior-wave gaps).
