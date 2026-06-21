# NWR Stats Pipeline Agent Chat Start - 2026-06-20

Owner: Master/Main HQ

Status: GREEN handoff. Master remains coordinator and approval gate.

## Repo / Branch

```text
Repo: C:\NWR\Niners-War-Room
Branch: work/hq-parallel-control
Expected starting HEAD: 3b83de6310e87173c8651412d59d9c0e4188ded9 or newer if the only newer commit is this Master handoff.
```

## Exclusive Worktree Rule

Only one Codex agent may actively edit `C:\NWR\Niners-War-Room` at a time. Start the Stats Pipeline Agent only after Master/Main HQ has stopped active work in this repo, or explicitly coordinate a pause.

The Stats Pipeline Agent must not touch other lane worktrees:

- Mock Draft
- Rookie HQ
- Drop Decision
- Outcome V1
- Deployment V2
- Trading Lab
- QA/Data Hygiene

## Pre-Expansion Freeze Status

The remote-backed freeze checkpoint exists:

```text
docs/hq/parallel_lanes/NWR_PRE_NFLVERSE_DATASET_EXPANSION_FREEZE_20260620.md
```

Freeze HEAD:

```text
3b83de6310e87173c8651412d59d9c0e4188ded9
```

At handoff creation, local Master/Main was clean and `origin/work/hq-parallel-control` pointed to the same HEAD.

## Pinned Snapshot Status

The controlled simulation pinned snapshot remains present and immutable:

```text
C:\NWR_SHARED_DATA\lane_exchange\pinned_live_snapshots\20260620_controlled_sim_v1\pinned_snapshot_manifest.json
```

The nflverse expansion must not mutate this pinned snapshot.

## Stats Policy Summary

Current policy docs:

- `docs/hq/parallel_lanes/NWR_NFL_STATS_FIELD_POLICY_V1.md`
- `docs/hq/parallel_lanes/NWR_NFLVERSE_MISSING_DATASET_EXPANSION_PLAN_20260620.md`
- `docs/hq/parallel_lanes/NWR_STATS_MODEL_BACKTEST_BACKLOG_20260620.md`

Policy summary:

- nflverse stats are display/stat-context only.
- Expanded stats may create `latest_candidate` packages only.
- No stats are approved for private value, hidden ranking/sort, model training, recommendations, simulations, final draft-day decisions, or Mock Draft direct decision logic.
- `latest_approved` remains manual Tim/Master/QA gated.
- `20260620_controlled_sim_v1` remains immutable.

## Target Datasets

Expand V1 support for these datasets if supported by `nflreadpy` and current local runtime:

- `rosters`
- `weekly_rosters`
- `participation`
- `opportunity`

Unsupported datasets should soft-skip with a YELLOW report instead of failing the entire run, unless the failure indicates schema corruption, unsafe output, or policy leakage.

## Exact Stats Pipeline Agent Prompt

```text
You are Stats Pipeline Agent for Niners War Room.

Repo:
C:\NWR\Niners-War-Room

Branch:
work/hq-parallel-control

Expected starting HEAD:
3b83de6310e87173c8651412d59d9c0e4188ded9 or newer if the only newer commit is the Master handoff commit `Record stats pipeline agent handoff`.

Mission:
Implement nflverse dataset expansion V1 in the Master/Main repo. Expand local-only nflverse puller/normalizer support for rosters, weekly_rosters, participation, and opportunity datasets if supported by the current nflreadpy/local runtime.

Master remains the coordinator and approval gate.

Exclusive worktree rule:
Do not start if another Codex agent is actively editing C:\NWR\Niners-War-Room. Do not touch any other lane worktrees.

Required context docs:
- docs/hq/parallel_lanes/NWR_PRE_NFLVERSE_DATASET_EXPANSION_FREEZE_20260620.md
- docs/hq/parallel_lanes/NWR_NFL_STATS_FIELD_POLICY_V1.md
- docs/hq/parallel_lanes/NWR_NFLVERSE_MISSING_DATASET_EXPANSION_PLAN_20260620.md
- docs/hq/parallel_lanes/NWR_STATS_MODEL_BACKTEST_BACKLOG_20260620.md

Hard guardrails:
- Do not create latest_approved.
- Do not mutate pinned snapshot 20260620_controlled_sim_v1.
- Do not update or alter existing approved Mock Draft packages.
- Do not use stats for rankings, private value, hidden sort, recommendations, simulations, final draft decisions, or model training.
- Do not touch Mock Draft, Rookie, Drop Decision, Outcome, Deployment V2, Trading Lab, or QA/Data Hygiene worktrees.
- Do not deploy.
- Do not run simulations.
- Do not create scheduled tasks.
- Do not commit C:\NWR_SHARED_DATA contents.
- Do not commit raw stats/API data.
- Do not commit secrets, .env files, data/, local_exports/, .venv/, caches, generated artifacts, or local reports.
- Do not push unless Tim/Master explicitly approves after review.

Implementation targets:
1. Review scripts/nflverse_scheduled_pull_v0.py and scripts/nflverse_normalize_snapshot_v0.py.
2. Expand puller support for rosters, weekly_rosters, participation, and opportunity datasets if available.
3. Expand normalizer support for display-only latest_candidate packages for the new datasets or dataset-derived display contexts.
4. Soft-skip unsupported datasets with clear YELLOW warnings and report rows/skips.
5. Preserve existing weekly_stats, season_stats, usage, and crosscheck behavior.
6. Keep candidate manifests approval_status=candidate.
7. Ensure contains_private_value=false, contains_market_data=false, contains_adp=false for stats display packages.
8. Ensure forbidden_use blocks private_value, hidden_sort, hidden_rank, draft_recommendation, final_draft_decision, model_training, simulation, deployment, production, and latest_approved.
9. Quarantine/exclude fantasy_points, fantasy_points_ppr, EPA, CPOE, PACR, RACR, WOPR, expected/diff fields, share fields, rank/value/ADP/market/tier/sort/probability/projection-like fields unless policy explicitly allows display-only inclusion.
10. Add focused tests with fake snapshots/responses; tests must not require network.
11. Run local dry-run(s). If live/local runtime pull is used, write only under C:\NWR_SHARED_DATA and do not commit those outputs.

Validation:
- Run focused tests.
- Run Ruff on changed scripts/tests.
- Run git diff --check.
- Confirm no C:\NWR_SHARED_DATA files are tracked.
- Confirm no raw stats, data, local_exports, .env, .venv, caches, generated artifacts, or secrets are tracked.
- Confirm latest_approved was not created/updated.
- Confirm pinned snapshot was not changed.
- Confirm no simulations, deployments, app wiring, or scheduled tasks were created.

Commit rules:
If validation passes and changes are limited to safe repo code/docs/tests, commit with:
Implement nflverse dataset expansion v1

Final report back:
- Starting branch/head/status.
- Files changed.
- Datasets pulled, normalized, skipped, or unsupported.
- Candidate packages created or updated, with row counts and SHA values.
- Tests/Ruff/diff-check results.
- Confirmation latest_approved untouched.
- Confirmation pinned snapshot untouched.
- Commit hash if created.
- Final git status.
- Final GREEN/YELLOW/RED verdict.
```

## Master Verdict

GREEN to start a separate Stats Pipeline Agent after Master/Main HQ stops active edits in this repo.
