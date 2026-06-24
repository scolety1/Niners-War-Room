# NWR Draft-Day App V2 Current Route Map

Date: 2026-06-24
Branch: `work/hq-parallel-control`
Checkpoint HEAD: `539463a41f063b9c9995c198e138c1d8676fca3e`

## Core Routes

| Route | Navigation title | Page file | Visibility | Purpose |
| --- | --- | --- | --- | --- |
| `/drafting-mode` | Drafting Mode V2 | `app/pages/19_drafting_mode_v2.py` | visible | On-clock cockpit with top-bar status, Live/Mock session selector, board, rail, decision panel, trade recorder, and cockpit controls. |
| `/refresh-data` | Refresh Data | `app/pages/24_refresh_data_v1.py` | visible | Manual source refresh orchestrator for safe configured sources, with skipped/blocked/manual source reporting. |
| `/settings-data-health` | Settings / Data Health | `app/pages/28_settings_data_health_v1.py` | visible | Data-health dashboard, guardrail checks, and Refresh Data Run Status reader. |
| `/settings` | Settings Data Health Legacy Alias | `app/pages/30_settings_data_health_alias.py` | hidden | Legacy alias to Settings/Data Health. |
| `/live-draft-room` | Live Draft Room | `app/pages/21_live_draft_room_v1.py` | visible | Live Draft V2 workflow with persisted local runtime state and trade events. |
| `/cheat-sheets` | Cheat Sheets V2 | `app/pages/18_cheat_sheets_v2.py` | visible | Tiered draft board with runtime drafted filtering, K/DST hidden by default, and display-only market/source context. |
| `/rankings` | Dynasty Rankings Home | `app/pages/20_final_board_v1.py` | hidden | Direct alias for the full Dynasty Rankings board. |
| `/player-compare` | Player Compare | `app/pages/22_player_compare_v1.py` | visible | Player Compare Decision Mode with comparison summaries and caveats. |
| `/trading-lab` | Trading Lab | `app/pages/23_trading_lab_v1.py` | visible | Trade package review and display-only DynastyProcess market sanity context. |
| `/mock-draft` | Mock Draft | `app/pages/24_mock_draft_v1.py` | visible | Dedicated mock draft deep tool. Drafting Mode also has its own Mock Draft / Practice session state. |
| `/post-draft-mode` | Post-Draft Mode V2 | `app/pages/29_post_draft_mode_v2.py` | visible | Post-draft summary and review mode. Defaults to live runtime state. |
| `/post-draft` | Post-Draft Mode Legacy Alias | `app/pages/29_post_draft_mode_v2.py` | hidden | Legacy alias to Post-Draft Mode V2. |

## Related Aliases

| Route | Page file | Purpose |
| --- | --- | --- |
| `/home` | `app/pages/20_final_board_v1.py` | Default visible Dynasty Rankings route. |
| `/draft-day-home` | `app/pages/20_final_board_v1.py` | Hidden Dynasty Rankings alias. |
| `/draft-room` | `app/pages/25_draft_prep_v1.py` | Visible Draft Prep page. |
| `/outcome-columns` | `app/pages/26_outcome_columns_v1.py` | Visible Outcome Diagnostics page. |
| `/decision-board` | `app/pages/27_decision_board_v1.py` | Visible Decision Board page. |

## Stable Navigation Notes

- `Refresh Data` remains immediately before `Mock Draft` in the visible navigation registry.
- Drafting Mode links to `Refresh Data`, `Settings/Data Health`, Rankings, Cheat Sheets, Player Compare, Trading Lab, and Post-Draft Mode as secondary cockpit tools.
- Cheat Sheets can receive `session_type=live` or `session_type=mock` when opened from Drafting Mode.
- Post-Draft Mode defaults to `Live` state even though it can inspect mock state when deliberately selected.
- Hidden aliases remain route-stable for direct links but are not primary navigation items.

## Source And Runtime Guardrails

- Frozen Final Draft Board V1 remains a baseline/checkpoint.
- `final_board_rank`, Dynasty Rank, tier assignments, latest files, pinned snapshots, and model logic are unchanged by route registration.
- Runtime draft JSON remains local-only under `C:\NWR_SHARED_DATA\draft_runtime_state`.
- Refresh status JSON remains local-only under `local_exports/refresh_data/latest_refresh_status.json`.
- Market, ADP, DynastyProcess, vendor, and projection context remain display-only unless separately approved.
