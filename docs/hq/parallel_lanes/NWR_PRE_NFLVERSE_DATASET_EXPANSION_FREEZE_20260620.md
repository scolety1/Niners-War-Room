# NWR Pre-nflverse Dataset Expansion Freeze - 2026-06-20

Owner: Master/Main HQ

Status: GREEN remote-backed freeze before nflverse dataset intake expansion.

## Purpose

This checkpoint records the current Master/Main and local-only stats candidate state before any nflverse puller, normalizer, or dataset intake upgrades.

This freeze is not a new draft snapshot. It does not create, mutate, or approve any Lane Exchange package.

The pinned controlled simulation snapshot remains immutable:

```text
C:\NWR_SHARED_DATA\lane_exchange\pinned_live_snapshots\20260620_controlled_sim_v1\pinned_snapshot_manifest.json
```

## Master Remote-Backed State

| Check | Result |
| --- | --- |
| Repo | `C:\NWR\Niners-War-Room` |
| Branch | `work/hq-parallel-control` |
| Local HEAD at freeze start | `cee1343accfbd3e5b6cd8a61427a867a4834b1ae` |
| Upstream | `origin/work/hq-parallel-control` |
| Remote ref at freeze start | `cee1343accfbd3e5b6cd8a61427a867a4834b1ae` |
| Ahead/behind at freeze start | `0 behind / 0 ahead` |
| Git status at freeze start | clean |

## Pinned Snapshot Status

| Artifact | Status | Path |
| --- | --- | --- |
| Pinned controlled simulation snapshot | present | `C:\NWR_SHARED_DATA\lane_exchange\pinned_live_snapshots\20260620_controlled_sim_v1\pinned_snapshot_manifest.json` |
| Controlled simulation report | present | `C:\NWR_SHARED_DATA\live_test_reports\mock_draft_controlled_sim\controlled_sim_pinned_snapshot_20260620_155537.md` |

The pinned snapshot remains fixed for controlled simulation/rehearsal only. It must not be mutated by nflverse dataset expansion work.

## Current stats_context latest_candidate State

These are display/stat-context candidates only. They are not `latest_approved`, not pinned, not private value, and not approved for model, recommendation, simulation, or final draft-day decision use.

| Package | Pointer | Manifest | Rows | SHA256 |
| --- | --- | --- | ---: | --- |
| `stats_context/player_weekly_stats_display_context` | `C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_weekly_stats_display_context\latest_candidate.json` | `C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_weekly_stats_display_context\20260620_214500_season_stats_live\manifest.json` | 38402 | `473a357aa569793b4b246c6055f48fc51eb9c4b5709657efeee27d3d6aa4b613` |
| `stats_context/player_season_stats_display_context` | `C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_season_stats_display_context\latest_candidate.json` | `C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_season_stats_display_context\20260620_214500_season_stats_live\manifest.json` | 4017 | `28b31fd59c68d69376cc3f7be5011c0715aa980991318c28410d0b3ea6f13f3e` |
| `stats_context/player_usage_context` | `C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_usage_context\latest_candidate.json` | `C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_usage_context\20260620_214500_season_stats_live\manifest.json` | 53227 | `30ea72437ac93ae1958a979404d3cea6455c9ecf3f01817c2762a6989eabd058` |
| `stats_context/player_stats_crosscheck_report` | `C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_stats_crosscheck_report\latest_candidate.json` | `C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_stats_crosscheck_report\20260620_214500_season_stats_live\manifest.json` | 5 | `b4535684c853cedc6062783667d68a5782ca04d97b51e2bb4ddc4b2457513ccf` |

All four current stats candidates had:

- `approval_status: candidate`
- no UTF-8 BOM in `latest_candidate.json`
- allowed use limited to display/stat context, source audit, identity crosscheck, and future candidate review
- forbidden use blocking private value, veteran private values, hidden sort/rank, draft recommendation, final draft decision, model training, simulation, production deployment, and `latest_approved`

## Current Stats Policy Docs

| Policy doc | Status |
| --- | --- |
| `docs/hq/parallel_lanes/NWR_NFL_STATS_FIELD_POLICY_V1.md` | present |
| `docs/hq/parallel_lanes/NWR_NFLVERSE_MISSING_DATASET_EXPANSION_PLAN_20260620.md` | present |
| `docs/hq/parallel_lanes/NWR_STATS_MODEL_BACKTEST_BACKLOG_20260620.md` | present |

Current policy summary:

- nflverse stats remain display-only `latest_candidate` context.
- No nflverse fields are approved for private value, hidden ranking/sort, model training, recommendations, simulations, final draft-day decisions, or Mock Draft direct decision logic.
- GREEN future-test categories are role, volume, availability, roster, participation, opportunity, and basic counting/usage signals.
- YELLOW fields remain backtest-only, including EPA, CPOE, WOPR, PACR, RACR, share, expected/diff, and advanced efficiency fields.
- RED fields remain blocked for model/private-value use, including `fantasy_points`, `fantasy_points_ppr`, modeling use of `headshot_url`, and other low-fit fields identified in policy.

## Comparison / Rollback Instructions

If nflverse dataset expansion goes wrong:

1. Stop before creating or promoting any `latest_approved`.
2. Compare branch state to this freeze start HEAD:

   ```powershell
   git diff cee1343accfbd3e5b6cd8a61427a867a4834b1ae...HEAD -- scripts docs tests
   ```

3. Compare stats candidate pointers against the table above.
4. Verify the pinned snapshot hash/path remains unchanged.
5. Verify no stats candidate was promoted to `latest_approved`.
6. Verify no raw nflverse data, `C:\NWR_SHARED_DATA`, secrets, `.env`, `data/`, `local_exports/`, `.venv`, caches, or generated artifacts entered Git.
7. If any expansion candidate violates field policy, discard or quarantine the local-only candidate and leave current approvals/pinned snapshot untouched.

Do not use `git reset --hard` or revert user work without explicit Tim/Master approval.

## Master Verdict

GREEN for pre-expansion freeze.

Dataset expansion may proceed in a later task if it preserves this checkpoint boundary and remains candidate/display-only.
