# NWR Parallel Lane Status Checkpoint

## Scope

This is a Master/Main HQ docs-only coordination checkpoint for active and sealed
Niners War Room lanes. It is not feature work. It does not touch Mock Draft,
Rookie, Outcome, Deployment V2, app/source behavior, `data/`, `local_exports/`,
or `.venv/`.

## No-Overlap Coordination Rule

Never run two Codex sessions in the same worktree at the same time.

If a lane Codex is active, Master HQ must not edit, stage, commit, inspect, or
clean files in that lane's worktree unless the active lane is paused and HQ
explicitly approves the handoff.

## Outcome V1 Status

Worktree:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome
```

Branch:

```text
main
```

Latest pushed main closeout:

```text
6e47932 Record Outcome numeric columns V1 local release closeout
```

Status:

- Outcome numeric columns are GREEN for local/main readiness.
- Approved displayed heads:
  - QB T12
  - RB T12
  - RB T24
  - WR T12
  - WR T24
  - WR T36
  - TE T12
- No Top 6 or unapproved heads.
- No sorting/ranking effects.
- No hidden sort keys.
- No promoted artifacts.
- V1 deploy is not applicable because repo docs say No deployment in V1.

Touch status:

```text
Do not touch from Master HQ unless explicitly requested.
```

Recommended next action:

- Use as the normal local operator path for Streamlit V1.
- Keep Outcome behavior/display/sorting/hidden-key/promoted-artifact work
  frozen unless separately approved.

## Deployment V2 Status

Worktree:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-deploy-v2
```

Branch:

```text
work/deployment-v2-discovery
```

Latest pushed branch commit:

```text
04dda41 Prepare deployment v2 local-only review hold
```

Later local commits may include:

```text
f73eb9f Update quick start with selected operator path
```

Status:

- V1 remains `local_only`.
- Hosted deployment remains blocked.
- Normal operator path recommended:
  `C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome`
- Normal operator branch: `main`

Touch status:

```text
Do not touch from Master HQ unless explicitly requested.
```

Recommended next action:

- Deployment V2 lane should handle any push/review/PR follow-up itself.
- No hosted deployment, deploy command, public port, secret, container, or CI/CD
  work without explicit approval.

## Rookie HQ Status

Repo:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-rookies
```

Branch:

```text
work/rookie-framework-path
```

Latest Rookie commit:

```text
07d27b70aaa30f2e637733c5f19d3ac6ca0c7777
```

Expected Rookie status:

```text
?? data/
```

Status:

- Rookie HQ is paused/frozen.
- Do not reopen Rookie HQ except for:
  - factual correction
  - player update
  - broken export
  - push/backup request
  - later explicit production integration request

Touch status:

```text
Unsafe to touch from Master HQ.
```

Recommended next action:

- Leave Rookie HQ paused/frozen.
- Treat final Rookie outputs as manual-use inputs only.

## Mock Draft HQ Status

Worktree:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-mock-draft
```

Branch:

```text
work/mock-draft-simulator
```

Status:

- Mock Draft Codex is active right now.
- Mock Draft HQ is separate from Rookie HQ.
- Do not touch this worktree from Master HQ while Mock Draft Codex is running.

Approved read-only Rookie input:

```text
local_exports/rookie_framework/final_post_fill_runway_20260616/rookie_2026_mock_draft_input_20260616.csv
```

Use classification:

- manual-use only
- not production rankings
- not app rankings
- not a new Rookie model
- not a hidden sort key source
- not a source of probabilities/bands unless separately approved later

Touch status:

```text
Unsafe to touch from Master HQ while active.
```

Recommended next action:

- Let Mock Draft Codex resolve its own worktree status and Phase 1 runway.
- Master HQ should monitor only.

## Safe / Unsafe Worktree Summary

Safe for this Master HQ checkpoint:

- `C:\Users\smcol\Documents\Vacation\Niners-War-Room`
  on `work/hq-parallel-control`, docs-only coordination file only.

Unsafe to touch from Master HQ right now:

- `C:\Users\smcol\Documents\Vacation\Niners-War-Room-mock-draft`
  because Mock Draft Codex is active.
- `C:\Users\smcol\Documents\Vacation\Niners-War-Room-rookies`
  because Rookie HQ is frozen.
- `C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome`
  unless explicit Outcome work is requested.
- `C:\Users\smcol\Documents\Vacation\Niners-War-Room-deploy-v2`
  unless explicit Deployment V2 work is requested.

## Active Blockers And Intentionally Blocked Work

Active coordination blocker:

- Do not overlap Codex sessions in the same worktree.
- Do not touch the active Mock Draft worktree from Master HQ.

Intentionally blocked:

- production/app rankings
- probabilities or exact percentages
- coarse bands
- hidden sort keys
- promoted artifacts
- app wiring/display changes
- Outcome model/display behavior changes
- Rookie repo/artifact changes
- Deployment V2 hosted deployment or deploy commands
- `data/`, `local_exports/`, or `.venv/` commits
- Mock Draft simulations from Master HQ

## Master HQ Recommendation

Master HQ should remain in monitor/control mode.

Next actions by lane:

- Outcome V1: remain sealed for local/main use.
- Deployment V2: lane-owned follow-up only; hosted deployment remains blocked.
- Rookie HQ: remain paused/frozen.
- Mock Draft HQ: continue only in its separate worktree/branch.

This checkpoint is docs-only coordination, not feature work.
