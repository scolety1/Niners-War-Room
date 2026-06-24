# NWR Master All-Upgrades Integration Sweep Plan - 20260623

## Starting Master State
- Repo: `C:\NWR\Niners-War-Room`
- Branch: `work/hq-parallel-control`
- Starting HEAD: `59494119837b7d29a96192ef2b1671dea0241efe`
- Origin HEAD: `59494119837b7d29a96192ef2b1671dea0241efe`
- Status: clean and synced before sweep.

## Already Integrated In Master
- Cheat Sheet polish.
- Frozen board demotion to baseline/checkpoint wording.
- Draft-Day V2 persistent state, trade events, Drafting Mode sidebar, Player Compare decision summary, Trade Finder / Trade For basics.
- Player Compare injury/per-game display.
- 240-row Dynasty Rankings default.
- DynastyProcess Market Baseline display-only context in Dynasty Rankings.

## Candidate Worktrees And Branches
| Worktree | Branch | Clean? | Ahead Of Master | Classification | Sweep Decision |
|---|---:|---:|---:|---|---|
| `C:\NWR\Niners-War-Room-cheat-sheet-polish` | `codex/cheat-sheet-tiered-board-polish-20260623` | clean | 1 | app/test/doc | Skip: already integrated into Master as `5967f1d`/`5e0b6f3` path. |
| `C:\NWR\Niners-War-Room-cross-asset-fair-value-candidate` | `codex/cross-asset-fair-value-candidate-20260622` | clean | 1 | candidate-only report/artifact | Skip: older review-only candidate work, superseded by later emergency/historical tuning and not a current app upgrade. |
| `C:\NWR\Niners-War-Room-data-accountability-repair` | `codex/data-accountability-repair-20260623` | clean | 1 | data-health docs/service/tests | Integrate: GREEN report, scoped to data accountability audits, no rank/model/source-truth mutation. |
| `C:\NWR\Niners-War-Room-deploy-v2` | `work/deployment-v2-discovery` | clean | 185 | broad deployment/outcome history | Skip: too broad, includes deployment/outcome app surfaces and raw generated outcome artifact; outside this sweep's safe-upgrade scope. |
| `C:\NWR\Niners-War-Room-draft-day-v2` | `codex/draft-day-app-v2` | clean | 0 | old integrated V2 branch | Skip: no commits ahead of Master. |
| `C:\NWR\Niners-War-Room-drop-decision` | `work/drop-decision-day-review` | clean | 8 | drop-decision docs | Skip: historical/drop-decision docs, not requested app upgrade and not validated against current Master. |
| `C:\NWR\Niners-War-Room-dynasty-outcome-player-board` | `codex/dynasty-outcome-player-board-20260622` | clean | 1 | old app workflow lane | Skip: superseded by current Dynasty Rankings/Outcome integration work. |
| `C:\NWR\Niners-War-Room-dynasty-rankings-page` | `codex/dynasty-rankings-page-20260623` | clean | 2 | rankings app lane | Skip: `91d039f` integrated as `f2619bc`; market baseline lane functionality superseded by Master `5949411`. |
| `C:\NWR\Niners-War-Room-live-mock-draft-workflow` | `codex/live-mock-draft-workflow-20260622` | clean | 1 | old app workflow lane | Skip: superseded by current Draft-Day V2/live draft workflow commits on Master. |
| `C:\NWR\Niners-War-Room-mock-draft` | `work/mock-draft-simulator` | clean | 38 | broad mock-draft lane history | Skip: broad simulator/lane-exchange history; not safe to integrate blindly. |
| `C:\NWR\Niners-War-Room-model-data-candidate-sanity` | `codex/model-data-candidate-sanity-20260622` | clean | 1 | candidate report | Skip: review-only candidate report, not an app upgrade. |
| `C:\NWR\Niners-War-Room-outcome` | `main` | clean | 101 | separate outcome repo/history | Skip: separate outcome lane, broad model/outcome history. |
| `C:\NWR\Niners-War-Room-parallel-tuning-candidate` | `codex/parallel-tuning-candidate-20260622` | clean | 1 | candidate report/artifacts | Skip: older review-only tuning candidate, not a current app upgrade. |
| `C:\NWR\Niners-War-Room-trading-lab` | `work/trading-lab` | clean | 180 | broad Trading Lab/outcome history | Skip: too broad and not the small current Trading Lab market-sanity lane requested by this sweep. |

## Planned Safe Integration
1. Cherry-pick `3ccd59725d904febbb14a5614a202f0bcdb6c863` from `codex/data-accountability-repair-20260623`.
2. Validate after cherry-pick:
   - focused data-accountability tests;
   - app/service tests touched by current Master if needed;
   - Ruff on touched Python files;
   - Python compile;
   - `git diff --check`;
   - frozen board row count remains 66;
   - pinned manifest hash unchanged;
   - no `C:\NWR_SHARED_DATA`, raw vendor CSV, or prediction dump tracked.
3. Browser smoke core app pages after integration:
   - `/rankings`;
   - `/cheat-sheets`;
   - `/drafting-mode`;
   - `/live-draft-room`;
   - `/player-compare`;
   - `/trading-lab`;
   - `/mock-draft`.

## Guardrail Notes
- The sweep will not integrate broad deployment, outcome, mock-draft simulator, trading-lab legacy, or candidate-tuning branches.
- DynastyProcess remains display-only.
- Frozen board remains a baseline/checkpoint, not source truth.
- No final rank, Dynasty Rank, Candidate Rank, model input, hidden sort, latest-approved, latest-candidate, pinned snapshot, or source-truth mutation is permitted.
