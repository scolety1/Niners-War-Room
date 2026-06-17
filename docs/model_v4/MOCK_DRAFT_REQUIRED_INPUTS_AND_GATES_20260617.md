# Mock Draft Required Inputs And Gates - 2026-06-17

## Current Full-Simulation Blockers
- Complete all-10-team post-drop rosters/managers are missing. Current local roster extraction has `294` rows but only `5` team names and `4` managers visible.
- Confirmed full post-drop draft order/pick ownership is not yet complete enough for all-team simulation confidence.
- Real dynasty ADP/market timing source is not imported. This is optional, but opponent behavior remains placeholder/fake-only without it.
- Approved NWR veteran/free-agent value/guidance export is not present. This is optional for visibility-only simulation, but required for value-aware veteran/free-agent comparisons.

## Required Input Groups

### Complete All-10-Team Post-Drop Rosters/Managers
Required columns:
- `team_name`
- `manager`
- `roster_slot`
- `player_name`
- `position`
- `nfl_team`
- `input_status`
- optional: `overall_rank`, `source_file`, `source_timestamp`

Accepted local-only destination:
- `local_exports/mock_draft/review_inputs/post_drop_rosters_20260617/post_drop_roster_rows.csv`

Can proceed without it:
- Phase 1 design, schema validation, local inventory, and manual review packet updates.

Must remain blocked without it:
- Full 10-team team-needs simulation.
- Opponent needs pressure.
- Roster construction driven pick behavior.

### Confirmed Full Post-Drop Draft Order/Pick Ownership
Required columns:
- `season`
- `overall_pick`
- `round`
- `round_pick`
- `pick_label`
- `current_owner`
- `original_owner`
- `manager`
- `is_niners_pick`
- `source_status`

Accepted local-only destination:
- `local_exports/mock_draft/review_inputs/post_drop_draft_order_20260617/post_drop_draft_order_rows.csv`

Can proceed without it:
- Phase 1 design and partial review using existing simulator-ready 2026 pick rows.

Must remain blocked without it:
- Final pick-window sequencing.
- All-team pick ownership simulation.
- Any claim that the draft order is complete.

### Real Dynasty ADP/Market Timing File
Status: optional and behavior-only.

Required columns if supplied:
- `asset_id`
- `player`
- `position`
- `source_name`
- `source_type`
- `source_timestamp`
- one of `market_adp`, `overall_adp`, or `expected_pick`
- `sample_size`
- `identity_match_method`
- `review_flags`

Accepted local-only destination:
- `local_exports/mock_draft/review_inputs/market_timing_20260617/market_timing_behavior_only_rows.csv`

Can proceed without it:
- Manual draft prep, fake-only timing plumbing, deterministic scenario variants, and visibility outputs.

Must remain blocked without it:
- Real calibrated opponent market behavior.
- Market-based likely pick timing claims.

### Approved NWR Veteran/Free-Agent Value/Guidance Export
Status: optional for visibility, required for value-aware veteran comparisons.

Required columns if supplied:
- `asset_id`
- `player`
- `position`
- `source_label`
- `nwr_value_status`
- `nwr_guidance_label`
- `nwr_warning`
- `draft_action`
- `source_status`
- optional: approved numeric NWR value field only if explicitly sourced inside this lane

Accepted local-only destination:
- `local_exports/mock_draft/review_inputs/nwr_veteran_guidance_20260617/nwr_veteran_guidance_rows.csv`

Can proceed without it:
- Value-neutral veteran/free-agent visibility.
- Manual review queues.

Must remain blocked without it:
- Value-aware veteran/free-agent comparisons.
- Any NWR quality ordering of dropped veterans/free agents.

## Contamination Guardrails
- ADP/market is behavior-only: opponent behavior, likely timing, availability pressure, and expected draft-room cost.
- No numeric NWR score may be invented from ADP, market rank, snapshot rank, rookie rank, or draft order.
- Value-neutral veterans/free agents must not be ranked against rookies as NWR quality.
- Rookie guidance remains read-only and frozen.
- `formula_name=cfbd_enriched_baseline_v1_1` and `board_order_frozen=yes` remain required for the provided rookie input.
- No app wiring, production ranking/sorting, hidden sort key, promoted artifact, Outcome HQ, Rookie HQ, or Drop Decision HQ change is allowed.

## Gate Table
| Gate | Current Status | Full Simulation Impact |
| --- | --- | --- |
| Phase 1 intake/design doc | GREEN | Can proceed |
| Rookie manual-use input readable | GREEN | Can proceed with frozen rookie guidance |
| Dropped veterans/free agents local snapshot | GREEN | Can proceed as value-neutral visibility |
| Complete all-10-team post-drop rosters | RED | Blocks full team-needs simulation |
| Confirmed full post-drop draft order | YELLOW | Blocks final pick-window confidence |
| Real ADP/market timing source | YELLOW | Blocks calibrated opponent market behavior only |
| Approved NWR veteran/free-agent guidance | YELLOW | Blocks value-aware veteran comparisons |
| Contamination firewall | GREEN | Must remain GREEN |

## Recommended First Input
Tim should provide the complete all-10-team post-drop roster/manager snapshot first. That unlocks team-needs pressure and is more foundational than optional market timing or optional NWR veteran guidance.

## Verdict
- Phase 1 readiness tooling: GREEN.
- Full simulation readiness: YELLOW/blocked by missing required roster and draft-order inputs.
- Contamination status: GREEN.
