# NWR Overnight Accuracy Max Tuning - 2026-06-22

## Final Verdict: GREEN with YELLOW data caveat

Tuned V2 produced a materially better review-only rookie-veteran comparison layer and passed the requested sanity anchors. It remains a candidate/review overlay, not a source-truth or approval artifact, because no complete verified historical dropped-veteran panel exists.

## Tuned V2 Integrated

Yes. Tuned V2 is integrated as the app's Review-Only Candidate layer. It strengthens young established veteran anchors, confidence-caps uncertain rookies, discounts QBs in 10-team 1QB, and keeps ADP strictly display-only.

## PDF Free Agent Pool Addendum

`C:\Users\codex-agent\Downloads\LVE Rosters 061326.pdf` page 3 was parsed as the verified league Free Agents source for this draft and integrated as a draftable overlay. This does not mutate Frozen Final Draft Board V1 or any approved rank/source-truth field.

- Extracted free agents: 77
- Included by default: 63 QB/RB/WR/TE
- Hidden by default: 14 K/DST
- Frozen board rows remain: 66
- Expanded Live Draft Room loaded pool rows: 143
- Key parsed examples: Tyreek Hill, Dallas Goedert, Juwan Johnson, Tua Tagovailoa, Jaylen Wright, Isaac Guerendo, Darnell Mooney, Rashod Bateman, Bryce Young, Anthony Richardson, Austin Ekeler, Marquise Brown, Cedric Tillman, Jerome Ford, Justice Hill, Ben Sinnott, Michael Mayer, Geno Smith, Marcus Mariota, Mac Jones, Noah Gray.

Live Draft Room now has `Show PDF free agents` and `Show K/DST` controls. PDF-only players show `Not on frozen board` for Final Board Rank and remain selectable/draftable. Missing model/candidate values show `Not enough information`. ADP/range context remains display-only and does not drive internal value.

Detailed audit: `docs/hq/parallel_lanes/overnight_accuracy_max_20260622/NWR_PDF_FREE_AGENT_POOL_INTEGRATION_20260622.md`.

## Historical Data Found

The run used internal rookie replay fixtures, model v4 replay reports, current full dynasty board, current frozen board, current emergency/historical tuned overlays, and proxy dropped-veteran cohorts. No outside market/projection/trade-calculator sources were used.

## Historical Data Gaps

The missing piece remains a real historical league dropped-veteran panel with roster/drop truth, comparable pre-draft values, and future outcomes. Proxy cohorts are sensitivity-only.

## Formula Before vs After

Compared with the current historical tuned layer, V2:

- increases veteran dynasty anchor strength from 1.12 to 1.28;
- lowers rookie raw rank/tier strength from 0.86 to 0.80;
- raises rookie/manual/needs-data uncertainty penalties;
- strengthens 1QB QB discount;
- adds prior NFL production anchor support;
- keeps ADP weight at 0.00.

## Current Player-Order Changes

| player | pos | final_board_rank | current_candidate_rank | tuned_v2_cross_asset_rank | tuned_v2_cross_asset_value | rank_delta_vs_frozen | rank_delta_vs_current_candidate | confidence_band | horizon_2026_band | horizon_2027_band | horizon_next5y_band | human_review_priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Jeremiyah Love | RB | 1 | 1 | 1 | 62.86 | 0 | 0 | Medium-low | Strong | Priority | Priority | MEDIUM |
| Zay Flowers | WR | 31 | 10 | 2 | 59.26 | 29 | 8 | Medium-low | Priority | Priority | Priority | HIGH |
| Chris Olave | WR | 34 | 11 | 3 | 56.99 | 31 | 8 | Medium-low | Strong | Strong | Strong | HIGH |
| Makai Lemon | WR | 2 | 2 | 4 | 54.66 | -2 | -2 | Medium-low | Viable | Strong | Priority | MEDIUM |
| Carnell Tate | WR | 3 | 3 | 5 | 52.84 | -2 | -2 | Medium-low | Viable | Strong | Strong | MEDIUM |
| Jameson Williams | WR | 42 | 13 | 6 | 52.73 | 36 | 7 | Medium-low | Strong | Strong | Strong | HIGH |
| KC Concepcion | WR | 4 | 4 | 7 | 51.01 | -3 | -3 | Medium-low | Viable | Strong | Strong | MEDIUM |
| Jadarian Price | RB | 5 | 6 | 9 | 49.19 | -4 | -3 | Medium-low | Viable | Strong | Strong | MEDIUM |
| Drake Maye | QB | 40 | 20 | 20 | 30.48 | 20 | 0 | Medium-low | Long shot | Long shot | Long shot | HIGH |
| Jaylen Warren | RB | 54 | 24 | 25 | 22.99 | 29 | -1 | Medium-low | Not enough information | Not enough information | Not enough information | HIGH |
| Rashee Rice | WR | 62 | 26 | 26 | 22.45 | 36 | 0 | Medium-low | Not enough information | Not enough information | Not enough information | HIGH |
| Brian Thomas | WR | 63 | 28 | 29 | 19.48 | 34 | -1 | Medium-low | Not enough information | Not enough information | Not enough information | HIGH |
| Dak Prescott | QB | 60 | 32 | 53 | 5.78 | 7 | -21 | Medium-low | Not enough information | Not enough information | Not enough information | MEDIUM |
| Keenan Allen | WR | 64 | 64 | 64 | 0.0 | 0 | 0 | Low | Not enough information | Not enough information | Not enough information | HIGH |
| Brock Purdy | QB | 65 | 65 | 65 | 0.0 | 0 | 0 | Medium-low | Not enough information | Not enough information | Not enough information | MEDIUM |
| Darren Waller | TE | 66 | 66 | 66 | 0.0 | 0 | 0 | Low | Not enough information | Not enough information | Not enough information | HIGH |

## Pick-Window Recommendations

| pick | top_candidate_players | value_players | reach_players | avoid_or_human_review_players | best_rookie | best_veteran | best_positional_need_if_known | confidence | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.03 | Jeremiyah Love | Zay Flowers | Chris Olave | Makai Lemon | Carnell Tate | Jeremiyah Love | Zay Flowers | Chris Olave | Denzel Boston | Jadarian Price | Germie Bernard | Chris Bell | Zachariah Branch | Zay Flowers | Chris Olave | Jameson Williams | Alec Pierce | Antonio Williams | Jeremiyah Love | Zay Flowers | Roster dependent; RB/WR/TE scarcity over QB in 10-team 1QB. | MEDIUM | ADP/range is display-only; human-review priority remains active. |
| 1.04 | Jeremiyah Love | Zay Flowers | Chris Olave | Makai Lemon | Carnell Tate | Jeremiyah Love | Zay Flowers | Chris Olave | Makai Lemon | Jadarian Price | Germie Bernard | Chris Bell | Zachariah Branch | Alec Pierce | Zay Flowers | Chris Olave | Jameson Williams | Alec Pierce | Antonio Williams | Jeremiyah Love | Zay Flowers | Roster dependent; RB/WR/TE scarcity over QB in 10-team 1QB. | MEDIUM | ADP/range is display-only; human-review priority remains active. |
| 1.09 | Jeremiyah Love | Zay Flowers | Chris Olave | Makai Lemon | Carnell Tate | Jeremiyah Love | Zay Flowers | Chris Olave | Makai Lemon | Carnell Tate | Jonah Coleman | Zay Flowers | Chris Olave | Jameson Williams | Alec Pierce | Antonio Williams | Jeremiyah Love | Zay Flowers | Roster dependent; RB/WR/TE scarcity over QB in 10-team 1QB. | MEDIUM | ADP/range is display-only; human-review priority remains active. |
| 2.04 | Jeremiyah Love | Zay Flowers | Chris Olave | Makai Lemon | Carnell Tate | Jeremiyah Love | Zay Flowers | Chris Olave | Makai Lemon | Carnell Tate | Not enough information | Zay Flowers | Chris Olave | Jameson Williams | Alec Pierce | Antonio Williams | Jeremiyah Love | Zay Flowers | Roster dependent; RB/WR/TE scarcity over QB in 10-team 1QB. | MEDIUM-LOW | ADP/range is display-only; human-review priority remains active. |
| 2.08 | Jeremiyah Love | Zay Flowers | Chris Olave | Makai Lemon | Carnell Tate | Jeremiyah Love | Zay Flowers | Chris Olave | Makai Lemon | Carnell Tate | Not enough information | Zay Flowers | Chris Olave | Jameson Williams | Alec Pierce | Antonio Williams | Jeremiyah Love | Zay Flowers | Roster dependent; RB/WR/TE scarcity over QB in 10-team 1QB. | MEDIUM-LOW | ADP/range is display-only; human-review priority remains active. |

## Outcome / Horizon Result

Tuned V2 adds categorical review-only horizon bands for 2026, 2027, and Next-5Y. These are not exact probabilities. Same-position missing Outcome remains `Not enough information`; wrong-position Outcome behavior remains app-controlled.

## Sanity Anchor Result

| Anchor | Result |
| --- | --- |
| Zay/Olave cannot be buried | PASS |
| Jameson Williams review-visible | PASS |
| Drake Maye 1QB-discounted but not useless | PASS |
| Dak Prescott 1QB-discounted | PASS |
| Keenan/Waller age-risk constrained | PASS |
| Jeremiyah Love can remain top with explanation | PASS |
| Top rookies visible with caveats | PASS |
| K excluded by default | PASS |
| Missing Outcome is not zero | PASS |
| Startup ADP not model input | PASS |

## Human Decisions Needed

- Whether to trust Tuned V2 over the current tuned layer for draft-day Candidate Best Available.
- Whether Zay/Olave/Jamo should influence early picks despite frozen ranks.
- Whether top rookies with medium-low confidence fit the roster build.

## Validation Results

- CSV load and required-column validation: PASS.
- Python compile/import checks for touched app/service/test files: PASS.
- Direct service assertions: PASS. The app-loaded candidate board shows Jeremiyah Love 1, Zay Flowers 2, Chris Olave 3, Jameson Williams 6, Drake Maye 20, Dak Prescott 53, Keenan Allen 64, and Darren Waller 66.
- Frozen board row count: PASS, 66.
- Pinned manifest hash: PASS, `5780156F09FBDA61FB906715C7341DB1B6D320C8D8EFA588070F19C4C50F45CE`.
- `git diff --check`: PASS.
- Focused pytest: BLOCKED by local environment because `pytest` is not installed.
- Ruff: BLOCKED by local environment because `ruff` is not installed.
- Browser smoke: PASS for `/live-draft-room`, `/rankings`, `/player-compare`, `/mock-draft`, and `/trading-lab`.
- Live Draft workflow proof: PASS. Assigning 1.01 advanced the current pick to 1.02; Undo restored current pick to 1.01.
- Rankings page: PASS. Opens cleanly and shows no kickers by default.
- Player Compare: PASS by route smoke and shared service proof. Tuned V2 candidate/horizon metrics are available after player selection through the same enriched frozen-board frame.

## Exact App Command / Path

Start:

```powershell
.\scripts\start_draft_day_app.ps1
```

Open:

`http://127.0.0.1:8501/live-draft-room`

## Guardrail Confirmation

No frozen board mutation, no final_board_rank change, no Dynasty Rank overwrite, no latest_candidate/latest_approved update, no pinned snapshot mutation, no vendor CSV, no raw prediction dump, and no `C:\NWR_SHARED_DATA` tracking.


## Follow-Up Addendum: Formula Comparison And Iteration

The addendum pass compared emergency pre-tuning, historical tuned V1, tuned V2 internal-only, tuned V2 low-weight proxy, and tuned V2 medium-weight proxy. The selected formula remains **tuned_v2_verified_plus_proxy_low_weight** because it passed all 10 sanity anchors while keeping proxy rows sensitivity-only.

### Key Side-By-Side

| player | pos | frozen_final_board_rank | current_app_candidate_rank_at_head | emergency_pre_tuning_rank | historical_tuned_rank | tuned_v2_rank | rank_delta_v2_vs_frozen | rank_delta_v2_vs_historical | confidence | reason_formula_moved_player_up_down | human_decision_note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Jeremiyah Love | RB | 1 | 1 | 1 | 1 | 1 | 0 | 0 | Medium-low | rookie_rank_crosswalk_confidence_capped; rb_wr_flex_scarcity; manual_review_penalty; outcome_missing_confidence_only; top_rookie_can_remain_top_with_explanation | Can stay top, but only as review-only with medium-low confidence. |
| Makai Lemon | WR | 2 | 4 | 4 | 2 | 4 | -2 | -2 | Medium-low | rookie_rank_crosswalk_confidence_capped; rb_wr_flex_scarcity; manual_review_penalty; outcome_missing_confidence_only; top_rookie_visible_but_uncertain | Top rookie remains visible, but uncertainty must be obvious. |
| Carnell Tate | WR | 3 | 5 | 7 | 3 | 5 | -2 | -2 | Medium-low | rookie_rank_crosswalk_confidence_capped; rb_wr_flex_scarcity; manual_review_penalty; outcome_missing_confidence_only; top_rookie_visible_but_uncertain | Top rookie remains visible, but uncertainty must be obvious. |
| KC Concepcion | WR | 4 | 7 | 8 | 4 | 7 | -3 | -3 | Medium-low | rookie_rank_crosswalk_confidence_capped; rb_wr_flex_scarcity; manual_review_penalty; outcome_missing_confidence_only; top_rookie_visible_but_uncertain | Top rookie remains visible, but uncertainty must be obvious. |
| Jadarian Price | RB | 5 | 9 | 9 | 6 | 9 | -4 | -3 | Medium-low | rookie_rank_crosswalk_confidence_capped; rb_wr_flex_scarcity; manual_review_penalty; outcome_missing_confidence_only; top_rookie_visible_but_uncertain | Top rookie remains visible, but uncertainty must be obvious. |
| Zay Flowers | WR | 31 | 2 | 2 | 10 | 2 | 29 | 8 | Medium-low | full_dynasty_anchor_strengthened; rb_wr_flex_scarcity; manual_review_penalty; outcome_missing_confidence_only; young_established_wr_not_buried_anchor | Young established WR anchor says compare seriously against top rookies. |
| Chris Olave | WR | 34 | 3 | 3 | 11 | 3 | 31 | 8 | Medium-low | full_dynasty_anchor_strengthened; rb_wr_flex_scarcity; manual_review_penalty; outcome_missing_confidence_only; young_established_wr_not_buried_anchor | Young established WR anchor says compare seriously against top rookies. |
| Jameson Williams | WR | 42 | 6 | 5 | 13 | 6 | 36 | 7 | Medium-low | full_dynasty_anchor_strengthened; rb_wr_flex_scarcity; manual_review_penalty; outcome_missing_confidence_only; young_established_wr_not_buried_anchor | Young established WR anchor says compare seriously against top rookies. |
| Drake Maye | QB | 40 | 20 | 11 | 20 | 20 | 20 | 0 | Medium-low | full_dynasty_anchor_strengthened; 1qb_qb_discount; manual_review_penalty; outcome_missing_confidence_only; young_qb_review_visible_after_1qb_discount | 1QB discount applies, but age/upside keeps him review-visible. |
| Dak Prescott | QB | 60 | 53 | 57 | 32 | 53 | 7 | -21 | Medium-low | full_dynasty_anchor_strengthened; 1qb_qb_discount; manual_review_penalty; outcome_missing_confidence_only | Useful QB, but 10-team 1QB context suppresses draft urgency. |
| Jaylen Warren | RB | 54 | 25 | 19 | 24 | 25 | 29 | -1 | Medium-low | full_dynasty_anchor_strengthened; rb_wr_flex_scarcity; manual_review_penalty; outcome_missing_confidence_only | Use as review-only context beside Final Board Rank. |
| Brian Thomas | WR | 63 | 29 | 22 | 28 | 29 | 34 | -1 | Medium-low | full_dynasty_anchor_strengthened; rb_wr_flex_scarcity; manual_review_penalty; outcome_missing_confidence_only | Use as review-only context beside Final Board Rank. |
| Rashee Rice | WR | 62 | 26 | 20 | 26 | 26 | 36 | 0 | Medium-low | full_dynasty_anchor_strengthened; rb_wr_flex_scarcity; manual_review_penalty; outcome_missing_confidence_only | Use as review-only context beside Final Board Rank. |
| Brock Purdy | QB | 65 | 65 | 63 | 65 | 65 | 0 | 0 | Medium-low | full_dynasty_anchor_strengthened; 1qb_qb_discount; manual_review_penalty; outcome_missing_confidence_only | Useful QB, but 10-team 1QB context suppresses draft urgency. |
| Keenan Allen | WR | 64 | 64 | 65 | 64 | 64 | 0 | 0 | Low | full_dynasty_anchor_strengthened; rb_wr_flex_scarcity; unknown_team_role_penalty; manual_review_penalty; outcome_missing_confidence_only; older_veteran_age_role_constraint | Do not blindly trust; age/team/role risk dominates. |
| Darren Waller | TE | 66 | 66 | 66 | 66 | 66 | 0 | 0 | Low | full_dynasty_anchor_strengthened; unknown_team_role_penalty; manual_review_penalty; outcome_missing_confidence_only; older_veteran_age_role_constraint | Do not blindly trust; age/team/role risk dominates. |

### Sensitivity Result

| sensitivity_version | proxy_use | result | zay_rank | olave_rank | jamo_rank | love_rank | why_not_selected |
| --- | --- | --- | --- | --- | --- | --- | --- |
| verified_internal_only | none | stable but conservative | 5 | 7 | 10 | 1 | Does not make the young-veteran correction actionable enough. |
| verified_plus_proxy_low_weight | sensitivity_only_low_weight | best stability | 2 | 3 | 6 | 1 | Selected. |
| verified_plus_proxy_medium_weight | sensitivity_only_medium_weight | overcorrected | 2 | 3 | 4 | 3 | Lets proxy cohorts dominate too much; weakens top rookie visibility. |

### Additional Outputs

- `formula_side_by_side_key_players.csv`
- `sanity_anchor_gate.csv`
- `formula_iteration_trials.csv`
- `proxy_sensitivity_comparison.csv`
- `DRAFT_DECISION_CHEAT_SHEET_20260622.md`

### Integration Decision

No app code change was required after this addendum because the already-integrated Tuned V2 low-weight proxy formula remained the best selected version. The app remains on Tuned V2 Candidate Best Available, Review-Only.
