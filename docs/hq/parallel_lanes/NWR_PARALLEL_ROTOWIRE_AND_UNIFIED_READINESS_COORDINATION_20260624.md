# NWR Parallel RotoWire and Unified Readiness Coordination

Date: 2026-06-24

## Master Starting Point

- Master repo: `C:\NWR\Niners-War-Room`
- Master branch: `work/hq-parallel-control`
- Master starting HEAD: `80ab3b93da8e8dfaa6883a4d13a67ec1f720bb56`
- Source ref used for both lanes: `origin/work/hq-parallel-control`
- Current unified universe snapshot:
  - Consolidated rows: 368
  - Missing player_id blockers: 5
  - Missing age blockers: 16
  - `model_input_allowed=no` for all rows
  - `app_wiring_allowed=no` for all rows
  - App wiring remains blocked

Note: the Master working tree had pre-existing untracked RotoWire research files at lane setup time. They were not touched, staged, committed, or copied into either lane. Both worktrees were created from the committed remote Master ref.

## Worktrees Created

| Lane | Worktree | Branch | Base |
|---|---|---|---|
| RotoWire source-repair research | `C:\NWR\Niners-War-Room-rotowire-scraper` | `codex/rotowire-scraper-source-repair-20260624` | `origin/work/hq-parallel-control` at `80ab3b9` |
| Unified universe readiness gate | `C:\NWR\Niners-War-Room-unified-readiness-gate` | `codex/unified-universe-readiness-gate-20260624` | `origin/work/hq-parallel-control` at `80ab3b9` |

## Lane Purposes

### Lane 1: RotoWire Source-Repair Research

Purpose: investigate whether RotoWire or existing RotoWire-related local artifacts can safely help repair remaining missing IDs or ages.

Allowed output:

- Candidate/source-repair research artifacts.
- Evidence tables, provenance notes, and safety classifications.
- No app wiring.
- No model input changes.
- No mutation of approved unified universe artifacts.

### Lane 2: Unified Universe Readiness Gate

Purpose: create a docs/CSV readiness matrix based on the current unified universe snapshot.

Allowed output:

- Readiness gate report.
- Readiness matrix CSV.
- Blocker classification and recommended next steps.
- No app wiring.
- No model input changes.
- Treat the unified universe state as a lane-start snapshot unless explicitly amended after Master integration of other lanes.

## Shared Guardrails

- Do not mutate Frozen Final Draft Board V1.
- Do not change `final_board_rank`.
- Do not overwrite Dynasty Rank.
- Do not change tier assignments.
- Do not update `latest_candidate` or `latest_approved`.
- Do not mutate pinned snapshot.
- Do not change model/rank logic.
- Do not make RotoWire, DynastyProcess, ADP, market, or vendor data model truth.
- Do not wire unified universe into Dynasty Rankings, Drafting Mode, Player Compare, Trading Lab, or any app page.
- Do not flip `model_input_allowed` or `app_wiring_allowed` to `yes` without a later explicit integration gate.
- Do not track raw scraped/vendor dumps.
- Do not track `C:\NWR_SHARED_DATA`.
- Do not track `local_exports`.
- Do not track runtime JSON.
- Do not scrape or ingest paywalled/blocked/vendor data unless already licensed/configured and explicitly safe in local project context.
- Do not expose credentials or API keys.
- Do not push either lane unless validation passes.

## Integration Order

1. Keep both lanes isolated while work is underway.
2. Validate each lane independently in its own worktree.
3. Integrate completed clean commits one at a time into `work/hq-parallel-control`.
4. If the RotoWire lane produces safe source-repair candidates, Master must validate and integrate those candidates before the readiness gate is rerun or amended.
5. RotoWire findings must not automatically upgrade the readiness gate.
6. The readiness gate must explicitly state the snapshot date and whether it predates any source-repair integration.

## Staleness Warning

The readiness gate lane starts from the unified universe snapshot at `80ab3b9`. If the RotoWire lane later changes the safe source-repair state, the readiness matrix may become stale and must be rerun or amended after those changes are integrated into Master.

## Final Setup Status

- RotoWire lane worktree created: yes
- RotoWire lane branch created: yes
- Unified readiness lane worktree created: yes
- Unified readiness lane branch created: yes
- Master source-truth/model/rank files changed by this coordination setup: no
- Master untracked files at setup time: yes, pre-existing RotoWire research files remained untouched
- Coordination report location: readiness-gate worktree only
