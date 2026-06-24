# NWR Cockpit P3 And Navigation Polish

Date: 2026-06-24
Branch: `codex/cockpit-p3-overall-polish-20260624`
Base: `origin/work/hq-parallel-control`

## Summary

Drafting Mode remains the on-clock cockpit. This pass reduces top-level navigation clutter and makes secondary tools feel like tools behind the cockpit instead of peer top-level modes.

A separate data loader / refresh lane appears active in `C:\NWR\Niners-War-Room-full-safe-data-loader-v1`, so this branch should stay isolated and should not merge until that lane returns.

## Cockpit Polish

- Tier-count rows now render friendly availability labels, such as `Tier 1A - 4 available`, instead of raw technical tier strings.
- The player selector is labeled `Select player for Decision Panel` with help text that explains it drives the right-side summary.
- The Decision Panel now renders a selected-player header, compact NWR/market metrics, a why-this-player section, and review checks instead of only a raw dataframe.
- The no-selection empty state now tells the user to choose a player to see rank, reasons, and review flags.
- `Settings / Data Health` label spacing is consistent in the cockpit top bar and docs touched by this lane.
- Refresh Data stays visible in the cockpit top bar.
- Live Draft / Mock Draft session selector is unchanged and still clear.

## Navigation Clutter Reduced

Visible primary navigation is now compact:

- Drafting Mode
- Refresh Data
- Settings / Data Health

Secondary tools are registered as hidden Streamlit pages so direct routes remain live:

- `/rankings`
- `/cheat-sheets`
- `/live-draft-room`
- `/mock-draft`
- `/player-compare`
- `/trading-lab`
- `/post-draft-mode`
- `/unified-universe-review`

Other existing advanced / legacy direct routes remain registered through `ALL_NAVIGATION_PAGES`.

## Demoted / Grouped Tools

Drafting Mode now exposes secondary tools through a collapsed `Tools / Review` expander:

- Rankings
- Cheat Sheets
- Live Draft Room
- Mock Draft
- Player Compare
- Trading Lab
- Post-Draft Mode
- Unified Universe Review

Full hiding was safe here because the app already uses `st.Page(..., visibility=...)`; no page files or route specs were deleted.

## Review-Only Labels

- Unified Universe Review says it is review-only and not used by rankings, model, or Drafting Mode.
- Trading Lab says market context is display-only and not a trade model, rank input, or source of truth.
- Player Compare says it is a decision aid only and does not mutate ranks, tiers, model values, or source-truth files.
- Post-Draft Mode says runtime state is audit/recap data, not official source truth.
- Rankings says market and Outcome context are display-only and never replace Dynasty Rank, Final Board Rank, tiers, or model values.

## Tests

Focused pytest:

`64 passed`

Covered:

- Drafting Mode cockpit page still renders expected cockpit copy.
- Live / Mock selector remains present.
- Refresh Data remains present.
- Required direct routes remain registered.
- Secondary tools are demoted from visible navigation.
- Back to Drafting Mode links are present on expected deep tools.
- `Settings / Data Health` label spacing is consistent in cockpit code.
- Friendly tier count labels render.
- Decision Panel empty state is readable.
- No model/rank/source-truth mutation fields are introduced by cockpit service paths.

## Browser Smoke

Status: GREEN after fresh-server / fresh-tab verification on Streamlit port `8527`.

Smoke targets:

- `/drafting-mode`
- `/refresh-data`
- `/settings-data-health`
- `/rankings`
- `/cheat-sheets`
- `/live-draft-room`
- `/mock-draft`
- `/player-compare`
- `/trading-lab`
- `/post-draft-mode`
- `/unified-universe-review`

Checks:

- Drafting Mode opens as the cockpit at `/drafting-mode`.
- Visible navigation is compact: Drafting Mode, Refresh Data, Settings / Data Health.
- Secondary tools remain reachable through the cockpit and direct URLs.
- Back to Drafting Mode links are present where practical and use same-tab anchors.
- Rankings -> Back to Drafting Mode click returned to `/drafting-mode` with the cockpit visible.
- Refresh Data and Mock Draft routes still open.
- Live / Mock selector remains in the cockpit.
- No Streamlit page-not-found errors.

Implementation note: Streamlit needs a root/default page. This lane uses a hidden root shim,
`pages/32_drafting_mode_root_v1.py`, that switches to the real Drafting Mode page. That keeps
the primary visible Drafting Mode route stable at `/drafting-mode` while avoiding a duplicate-page
route conflict.

## Guardrails

This lane does not:

- change model/rank logic.
- mutate Frozen Final Draft Board V1.
- change `final_board_rank`.
- overwrite Dynasty Rank.
- change tier assignments.
- update `latest_candidate` or `latest_approved`.
- mutate pinned snapshots.
- wire Unified Universe into Drafting Mode or Dynasty Rankings.
- make market, ADP, or DynastyProcess model inputs.
- track runtime JSON, `C:\NWR_SHARED_DATA`, `local_exports`, raw vendor files, or email files.

## Remaining Polish Backlog

- Consider row-click dataframe selection only after Streamlit row-selection behavior is verified stable in this app shell.
- Consider a small selected-player handoff query string from cockpit to Player Compare.
- Continue coordinating Refresh Data / Settings navigation copy with the separate data loader lane before merge.
