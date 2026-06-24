# NWR Drafting Mode Cockpit V1 Overnight Plan

Date: 2026-06-24
Branch: `codex/drafting-mode-cockpit-v1-overnight`
Starting HEAD: `9d24c1d62546366cf7fc4064e18f898e34fbb100`

## Preflight

- Base branch `work/hq-parallel-control` was clean and synced with origin.
- Refresh Data is already merged into the base branch and must be preserved.
- Worktree: `C:\NWR\Niners-War-Room-drafting-mode-cockpit`.

## Current Finding

`/drafting-mode` is still a workflow shell: it shows route codes, tabs for deep tools, and sidebar context. The real operational board/runtime behavior already exists in `app/components/draft_workflow.py`, `src/services/draft_day_workflow_service.py`, and `src/services/draft_day_runtime_state_service.py`.

## Implementation Phases

1. Create a cockpit service that builds:
   - top-bar summary from runtime state and adjusted pick frame.
   - available board using existing workflow helpers.
   - tier counts and compact board display.
   - selected-player decision panel.
   - left-rail event/pick/trade summaries.
   - trade recorder result using existing runtime trade schema.

2. Replace `/drafting-mode` page:
   - compact title/status top bar.
   - left rail for picks/events/deep links.
   - center available board with search/position/tier controls.
   - right selected-player panel and action buttons.
   - inline Record Trade expander.
   - runtime save/load/export controls.

3. Add back links to deep pages touched by the cockpit:
   - Dynasty Rankings.
   - Cheat Sheets.
   - Player Compare.
   - Trading Lab.
   - Post-Draft Mode.
   - Settings/Data Health.

4. Add focused tests:
   - cockpit empty/runtime summaries.
   - board hides drafted players and K/DST by default.
   - tier counts.
   - selected-player empty/valid panel.
   - trade recorder schema behavior.
   - back-link text.
   - guardrails against market-sort/model/source-truth mutation.

5. Validate:
   - focused pytest.
   - runtime state/trade tests if touched.
   - Ruff and compile on touched Python.
   - `git diff --check`.
   - tracked-file guardrails.
   - frozen board row count and pinned hash.
   - browser smoke on `/drafting-mode` plus existing routes.

## Guardrails

No implementation step may mutate frozen board files, ranks, tiers, latest pointers, pinned snapshots, runtime JSON tracked by git, shared raw data, vendor dumps, or source-truth/model logic. Market and ADP context remains display-only and cannot drive the default cockpit sort.

## Stop Conditions

Stop and report rather than push if:

- `/drafting-mode` or existing direct routes break.
- runtime persistence regresses.
- hidden/default sort starts using market fields.
- frozen board/pinned/source-truth guardrails fail.
