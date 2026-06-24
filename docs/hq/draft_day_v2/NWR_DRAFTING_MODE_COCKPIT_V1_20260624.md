# NWR Drafting Mode Cockpit V1

Date: 2026-06-24
Branch: `codex/drafting-mode-cockpit-v1-overnight`

## What Changed

`/drafting-mode` is now an on-clock cockpit instead of a navigation hub. The page opens directly into live draft operations: status summary, local runtime controls, owned pick context, available board, selected-player decision context, and an inline trade recorder.

The previous route-code/tab hub pattern was removed from the primary workspace. Existing deep tools remain available through compact cockpit buttons and direct routes.

## Why This Is A Cockpit

Drafting Mode should feel like the app has switched modes. The center of the screen is now the draftable board, with left-side draft context and right-side decision context. Deep tools are secondary actions instead of the main content.

## Layout

Top bar:

- Drafting Mode / On-Clock Cockpit header.
- Current pick and on-clock team.
- Drafted count and trade count.
- Autosave status and timestamp help text.
- Compact controls for Refresh Data, Save State, Load Latest, Export, Settings/Data Health, and Normal App View.

Left rail:

- Owned picks from the adjusted pick frame.
- Recent pick/trade runtime events.
- Recent trade records.
- Pick ownership overrides.
- Secondary links to Full Rankings, Full Player Compare, Full Trading Lab, Post-Draft Mode, and Settings/Data Health.

Center board:

- Available players only by default.
- Drafted players hidden via persisted runtime state.
- K/DST hidden by default.
- PDF free agents shown by default with a toggle.
- Search, position, and tier filters.
- Existing `Dynasty Asset Tier/Rank` sort reused as the default.
- Tier count rows above the board.
- Compact action path for Mark Drafted, Open Full Compare, Open Trade Lab, and Add Note.

Right decision panel:

- Selected player details.
- Position, NFL team, age.
- NWR rank/tier and frozen baseline rank.
- Why-draft and caveat fields when available.
- Market sanity context as display-only.
- Red flags for missing IDs, missing age, no market match, unsupported outcome, and role/depth/manual review caveats.
- Compare summary when a second player is selected.

Trade recorder:

- Inline `Record Trade` expander.
- Uses existing Live Draft V2 runtime trade event service/schema.
- Parseable current-year picks update ownership overrides.
- Future picks are logged.
- Unparseable assets remain review-needed through the existing runtime schema.

Deep tools/back links:

- Added `Back to Drafting Mode` links to Cheat Sheets, Dynasty Rankings, Player Compare, Trading Lab, Post-Draft Mode, and Settings/Data Health.
- Direct routes are preserved.
- Full custom navigation hiding was not forced in this V1.

## Data Sources Used

- Frozen Final Draft Board V1 as baseline/checkpoint context.
- Existing draftable player pool overlay through `load_expanded_draftable_player_pool`.
- Existing mock pick context for pick order/ownership context.
- Existing local runtime draft state for drafted rows, events, trades, save/load/export.
- Existing Player Compare decision service for compare summaries.
- Existing DynastyProcess/ADP/market fields only where already present as display-only context.

## Runtime State Behavior

Drafting Mode uses local runtime state loaded in live mode. Save, Load Latest, Export, Mark Drafted, Add Note, and Record Trade all go through existing runtime services. Runtime JSON stays in the ignored local runtime root, not in the repo.

The cockpit does not auto-run refresh on page load. The Refresh Data control is shown when the existing refresh orchestrator service is present and routes to `/refresh-data`.

## Display-Only Guardrails

This implementation does not:

- mutate Frozen Final Draft Board V1.
- change `final_board_rank`.
- overwrite Dynasty Rank.
- change tier assignments.
- update `latest_candidate` or `latest_approved`.
- mutate pinned snapshots.
- change model/rank logic.
- make DynastyProcess, ADP, or market fields model inputs.
- use market/ADP fields for the default cockpit sort.
- track runtime JSON, `C:\NWR_SHARED_DATA`, raw vendor files, email bodies, or prediction dumps.

## What Remains Future

- Full custom navigation compression/hiding while in Drafting Mode.
- Official Sleeper live sync.
- Deeper roster-needs engine.
- More polished note/flag management.
- More direct page-to-page player handoff from cockpit selections.

## Tests And Checks

Focused automated coverage added:

- Cockpit summary empty state.
- Cockpit summary reads runtime state counts.
- Drafted rows hidden from board.
- K/DST hidden by default.
- Tier counts and compact display columns.
- No-selection and valid-player decision panel.
- Compare summary path.
- Trade recorder path through existing schema.
- Current-year pick overrides and future pick logging.
- No market-sort fallback to ADP default.
- No rank/model/source-truth mutation fields.
- Deep pages expose Back to Drafting Mode links.
- Runtime/shared raw files are not tracked.

Validation run at implementation checkpoint:

- Ruff on touched Python files.
- Python compile on touched Python files.
- Focused pytest covering cockpit, runtime state, post-draft mode, player compare decision, draft workflow, and data health.

## Browser Smoke

Browser smoke targets:

- `/drafting-mode`
- `/live-draft-room`
- `/cheat-sheets`
- `/rankings`
- `/player-compare`
- `/trading-lab`
- `/mock-draft`
- `/post-draft-mode`
- `/settings-data-health`

Specific cockpit smoke points:

- Cockpit opens as operational workspace, not navigation hub.
- Top bar shows current pick, drafted count, trade count, and autosave status.
- Center board appears immediately.
- Drafted rows and K/DST are hidden by default.
- Tier counts are visible.
- Selecting a player updates the decision panel.
- Mark Drafted persists through runtime state.
- Record Trade handles `2026 1.04` for `2026 2.03, 2028 1st`.
- Left rail recent events update.
- Deep tool and back links work.
- Frozen board wording remains baseline/checkpoint.
- Market context remains display-only.

## Known Caveats

The cockpit currently uses Streamlit dataframe selection through a selectbox rather than row-click selection inside the dataframe. Navigation hiding was intentionally left as a future phase to avoid destabilizing Streamlit routing during the overnight pass.
