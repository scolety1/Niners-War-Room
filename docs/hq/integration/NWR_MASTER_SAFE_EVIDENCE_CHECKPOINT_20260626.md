# NWR Master Safe Evidence Checkpoint

Date: 2026-06-26

Verdict: GREEN

## Recovery Point

- Branch: `work/hq-parallel-control`
- Checkpoint HEAD before final validation: `7bb5f034355f304b2d19c8cb5d75f519be5e0fd7`
- Worktree: `C:\NWR\Niners-War-Room-master-cfbd-identity-final-integration`
- Safe rollback point: the latest pushed `origin/work/hq-parallel-control` after Phase 5.

## How To Start The App

From the Master worktree:

```powershell
cd C:\NWR\Niners-War-Room-master-cfbd-identity-final-integration
.\scripts\start_draft_day_app.ps1 -Port 8531
```

Open:

`http://127.0.0.1:8531/drafting-mode`

## Core Routes

- `/drafting-mode`
- `/rankings`
- `/settings-data-health`
- `/player-compare`
- `/trading-lab`
- `/post-draft-mode`
- `/live-draft-room`
- `/cheat-sheets`

## Evidence Review Routes

- `/unified-universe-review`
- `/nfl-usage-evidence-review`
- `/evidence-integration-review`

These routes are review/status surfaces only. They do not feed rankings, Drafting Mode, Player Compare, Trading Lab, Post-Draft, Cheat Sheets, hidden sorts, or model features.

## Current Evidence Lane Statuses

- CFBD Identity Matching V1: review-only.
- NFL Usage Evidence Layer V0: review-only.
- NFL Usage Promotion Gate V0: review-only.
- Historical NFL Usage Panel V0: review-only.
- NFL Usage Target Backtest V0: review-only.
- Unified Player Universe Review V1: review-only and app wiring blocked.
- RotoWire Usage Lane: blocked/manual.
- DynastyProcess Market Baseline: display-only market context.
- Outcome Columns V1: partial display-only context.
- Historical Drop Lists / Proxy Evidence: sensitivity-only unless actual evidence confirms rows.
- Sleeper League Truth: league-fact source only, not rank/model mutation.

## Raw Data / Cache Locations That Must Remain Untracked

- `C:\NWR_SHARED_DATA\nfl_usage_cache\`
- `C:\NWR_SHARED_DATA\public_sources\cfbd\`
- `C:\NWR_SHARED_DATA\draft_runtime_state\`
- `C:\NWR_SHARED_DATA\draft_day_runtime\`
- `local_exports\`

## Review-Only

- CFBD review artifacts.
- NFL usage field inventories, validation summaries, promotion gate outputs, target/backtest outputs.
- Unified Player Universe consolidated review artifact.
- Evidence Integration Review registry/status page.

## Display-Only

- DynastyProcess market baseline.
- ADP/market timing context.
- Outcome columns.
- NFL usage field summaries unless explicitly approved later.

## Blocked

- CFBD model/training use.
- NFL usage active model input.
- Unified Universe app wiring into Dynasty Rankings/Drafting Mode.
- RotoWire live scraping.
- Proxy/LOW historical evidence as training truth.
- True routes, TPRR, and YPRR without a licensed/safe source.

## Not Model Input

No Phase 0-5 artifact enables model input. Registry rows keep `model_input_allowed=no` and `training_allowed=no` for evidence lanes that might otherwise be confused with features.

## Recommended Next Gates

1. CFBD human review gate.
2. Unified Universe source-quality gate.
3. NFL Usage model integration gate.
4. Settings/Data Health status-summary gate.
5. Evidence review-page UI polish gate.

## Known Caveats

- Unified Universe still has identity/age blockers.
- Full Dynasty source previously documented 0 rookie/prospect rows.
- CFBD has useful review artifacts but no model-use approval.
- NFL usage target/backtest outputs are not active model features.
- Existing app previews may be running from older worktrees; use a fresh port from this Master worktree for acceptance.
