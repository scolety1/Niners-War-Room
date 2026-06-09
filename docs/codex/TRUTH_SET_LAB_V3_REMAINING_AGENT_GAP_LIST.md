# Truth Set Lab v3 Remaining Agent Gap List

Status: review-only. This phase does not change model scores.

## Files

- v3 preview: `C:\Dev\niners-war-room\local_exports\nflverse_model_previews\truth_set_lab_v3_preview_20260515T084959`
- gap list: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3\reports\truth_set_v3_remaining_agent_gap_list.csv`
- agent prompts: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3\reports\truth_set_v3_agent_prompts.md`

## Summary

- Gap rows: 6
- Agent prompts: 3
- Manual player-stat compilation requested: false

## Remaining Gaps

- `gap_route_participation`: routes_run|route_participation|TPRR|YPRR (possible_paid_only_field, 27 players)
- `gap_direct_first_down_projection`: projected rushing/receiving first downs (can_derive_locally, 40 players)
- `gap_missing_projection_rows`: missing valid projection rows (agent_can_verify_source, 3 players)
- `gap_incoming_rookie_nfl_evidence`: incoming rookie production/usage/snap evidence (agent_should_not_collect_manually, 5 players)
- `gap_sourced_injury_context`: injury status/history (agent_can_verify_source, 33 players)
- `gap_market_liquidity_context`: market/liquidity values (agent_should_not_collect_manually, 35 players)

## Guidance

Agents should only verify legal/exportable source availability or schema. They should not manually compile player-stat tables, chart routes, infer healthy statuses, or scrape forbidden sources. Local code should continue to derive first-down estimates and LVE scoring where needed.
