# NWR nflverse Missing Dataset Expansion Plan - 2026-06-20

Owner: Master/Main HQ

Status: Implementation plan only. No model features are approved.

## Purpose

Expand nflverse local-only scheduled pulls so NWR can review role and usage context as display/stat candidates. This plan does not approve private value, hidden sort, recommendations, simulations, or final draft-day decisions.

## Target Datasets

| Dataset | Purpose | Output scope |
| --- | --- | --- |
| `rosters` | player identity, age, experience, team, position | display/stat context only |
| `weekly_rosters` | weekly team/active-status context | display/stat context only |
| `participation` | routes, snaps, participation context if available | display/stat context only |
| `opportunity` | targets, carries, air yards, role volume if available | display/stat context only |

## Implementation Prompt

Use this prompt for the next implementation lane:

```text
You are Master/Main HQ for Niners War Room.

Repo: C:\NWR\Niners-War-Room
Branch: work/hq-parallel-control

Task: Expand nflverse Scheduled Puller/Normalizer V0 to fully support rosters, weekly_rosters, participation, and opportunity datasets as local-only display/stat-context latest_candidate packages.

Hard guardrails:
- Do not create latest_approved.
- Do not use stats as private value.
- Do not add stats to veteran_private_values.
- Do not create hidden rank/sort/model behavior.
- Do not run simulations.
- Do not deploy.
- Do not push.
- Do not touch other lane worktrees.
- Do not commit C:\NWR_SHARED_DATA contents or raw stats data.

Requirements:
- Pull datasets into C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\ only.
- Normalize safe display fields only.
- Quarantine advanced, fantasy, expected/diff, share, and model-like fields.
- Write candidates only with explicit --write-candidates.
- Keep all packages approval_status=candidate.
- Add tests with fake snapshots.
- Run focused tests, Ruff, git diff --check, and unsafe tracked path scan.
```

## Safety Rules

- `latest_candidate` may be generated only by explicit command.
- `latest_approved` remains Tim/Master/QA gated.
- Raw stats remain outside Git.
- Quarantined fields may remain in raw local snapshots but must not enter display candidates without policy approval.

## Master Verdict

GREEN for planning.

YELLOW-HOLD for implementation until a separate prompt is approved.
