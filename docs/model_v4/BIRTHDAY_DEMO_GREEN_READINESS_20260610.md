# Birthday Demo Green Readiness - 2026-06-10

## Summary

This pass applies a narrow source-safe dynasty age sanity patch and demo-readability polish. It does not use market rank, league rank, ADP, projections, public rankings, prior draft history, RotoWire rankings/projections, trade calculators, ownership tags, or legacy active-pack scores as private NWR value.

## Active Source

- Active rankings export: `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv`
- Before hash: `73786d1f58f1ff8071839883b34f48eae239ea17ff9d98960fd65efc2928e006`
- After hash: `8fbae9d40181b9bf4fc64986afe527e5ebed2240dc89db41d37894fe089d8606`
- Diff CSV: `local_exports/model_v4/current_value/latest/birthday_demo_rankings_sanity_patch_diff.csv`
- Watch-row CSV: `local_exports/model_v4/current_value/latest/birthday_demo_watch_row_diff.csv`

## Coverage

Before: {'active_rows': 240, 'qb_rb_wr_te_rows': 232, 'k_rows': 8, 'nwr_scored_rows': 232, 'no_private_score_rows': 8, 'source_repair_needed_rows': 8}

After: {'active_rows': 240, 'qb_rb_wr_te_rows': 232, 'k_rows': 8, 'nwr_scored_rows': 232, 'no_private_score_rows': 8, 'source_repair_needed_rows': 8}

## Formula Patch Scope

- RB dynasty age curve ramps after age 27 and sharply after 30.
- WR dynasty age curve ramps after age 30 and more strongly in the mid-30s.
- TE no-premium age curve ramps after age 30 and very strongly after 33.
- Missing age does not create a made-up age penalty; it remains a warning/source-confidence issue.
- RB/WR/TE score changes are from admitted age sidecar evidence through the production lifecycle component.

Changed scored rows by position: {'RB': 32, 'WR': 12, 'TE': 9}

## Before Top 40

| rank | player | pos | score |
| --- | --- | --- | --- |
| 1 | Puka Nacua | WR | 83.0486 |
| 2 | Christian McCaffrey | RB | 82.8329 |
| 3 | Jaxon Smith-Njigba | WR | 82.5714 |
| 4 | Jonathan Taylor | RB | 79.051 |
| 5 | Bijan Robinson | RB | 78.4618 |
| 6 | Jahmyr Gibbs | RB | 70.7273 |
| 7 | Ja'Marr Chase | WR | 70.5399 |
| 8 | Amon-Ra St. Brown | WR | 65.9348 |
| 9 | Trey McBride | TE | 62.2578 |
| 10 | Derrick Henry | RB | 61.5505 |
| 11 | De'Von Achane | RB | 61.3322 |
| 12 | George Pickens | WR | 60.0258 |
| 13 | James Cook | RB | 59.664 |
| 14 | Zay Flowers | WR | 56.5344 |
| 15 | A.J. Brown | WR | 54.1764 |
| 16 | Chris Olave | WR | 54.0656 |
| 17 | Kyren Williams | RB | 53.9777 |
| 18 | Nico Collins | WR | 53.4085 |
| 19 | Kyle Pitts | TE | 53.3402 |
| 20 | Davante Adams | WR | 50.9317 |
| 21 | Josh Allen | QB | 50.3163 |
| 22 | Saquon Barkley | RB | 50.1053 |
| 23 | Drake London | WR | 49.4925 |
| 24 | Drake Maye | QB | 49.3504 |
| 25 | Travis Kelce | TE | 49.1903 |
| 26 | Chase Brown | RB | 49.1893 |
| 27 | CeeDee Lamb | WR | 48.5992 |
| 28 | Jameson Williams | WR | 48.4869 |
| 29 | Josh Jacobs | RB | 47.9566 |
| 30 | Justin Jefferson | WR | 47.7511 |
| 31 | Trevor Lawrence | QB | 47.4404 |
| 32 | DeVonta Smith | WR | 45.6246 |
| 33 | Alec Pierce | WR | 44.9537 |
| 34 | Courtland Sutton | WR | 44.7259 |
| 35 | Tetairoa McMillan | WR | 42.8331 |
| 36 | Breece Hall | RB | 41.9244 |
| 37 | Jaylen Waddle | WR | 41.1687 |
| 38 | Michael Wilson | WR | 40.1861 |
| 39 | D'Andre Swift | RB | 40.0144 |
| 40 | Tee Higgins | WR | 39.0127 |

## After Top 40

| rank | player | pos | score |
| --- | --- | --- | --- |
| 1 | Puka Nacua | WR | 83.0486 |
| 2 | Jaxon Smith-Njigba | WR | 82.5714 |
| 3 | Bijan Robinson | RB | 78.4618 |
| 4 | Jonathan Taylor | RB | 74.308 |
| 5 | Jahmyr Gibbs | RB | 70.7273 |
| 6 | Ja'Marr Chase | WR | 70.5399 |
| 7 | Amon-Ra St. Brown | WR | 65.9348 |
| 8 | Trey McBride | TE | 62.2578 |
| 9 | De'Von Achane | RB | 61.3322 |
| 10 | George Pickens | WR | 60.0258 |
| 11 | James Cook | RB | 59.664 |
| 12 | Zay Flowers | WR | 56.5344 |
| 13 | A.J. Brown | WR | 54.1764 |
| 14 | Chris Olave | WR | 54.0656 |
| 15 | Kyren Williams | RB | 53.9777 |
| 16 | Nico Collins | WR | 53.4085 |
| 17 | Kyle Pitts | TE | 53.3402 |
| 18 | Christian McCaffrey | RB | 53.0131 |
| 19 | Josh Allen | QB | 50.3163 |
| 20 | Drake London | WR | 49.4925 |
| 21 | Drake Maye | QB | 49.3504 |
| 22 | Chase Brown | RB | 49.1893 |
| 23 | CeeDee Lamb | WR | 48.5992 |
| 24 | Jameson Williams | WR | 48.4869 |
| 25 | Justin Jefferson | WR | 47.7511 |
| 26 | Trevor Lawrence | QB | 47.4404 |
| 27 | DeVonta Smith | WR | 45.6246 |
| 28 | Alec Pierce | WR | 44.9537 |
| 29 | Courtland Sutton | WR | 42.9369 |
| 30 | Tetairoa McMillan | WR | 42.8331 |
| 31 | Breece Hall | RB | 41.9244 |
| 32 | Josh Jacobs | RB | 41.2427 |
| 33 | Jaylen Waddle | WR | 41.1687 |
| 34 | Michael Wilson | WR | 40.1861 |
| 35 | Tee Higgins | WR | 39.0127 |
| 36 | DK Metcalf | WR | 38.9005 |
| 37 | Javonte Williams | RB | 38.8681 |
| 38 | Saquon Barkley | RB | 38.08 |
| 39 | D'Andre Swift | RB | 37.6135 |
| 40 | Matthew Stafford | QB | 37.1191 |

## Watch Rows

| player | position | before_rank | after_rank | rank_delta | before_score | after_score | score_delta | trust_status | lineage_class | legacy_active_pack_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Christian McCaffrey | RB | 2 | 18 | 16 | 82.8329 | 53.0131 | -29.8198 | Capped Score | review_v4_current_player | 74.6 |
| Derrick Henry | RB | 10 | 66 | 56 | 61.5505 | 28.3132 | -33.2373 | Capped Score | review_v4_current_player | 72.65 |
| Travis Kelce | TE | 25 | 150 | 125 | 49.1903 | 14.7571 | -34.4332 | Capped Score | review_v4_current_player | 88.61 |
| Davante Adams | WR | 20 | 48 | 28 | 50.9317 | 33.1056 | -17.8261 | Capped Score | review_v4_current_player | 87.64 |
| Chase Brown | RB | 26 | 22 | -4 | 49.1893 | 49.1893 | 0.0 | Capped Score | review_v4_current_player | 80.41 |
| CeeDee Lamb | WR | 27 | 23 | -4 | 48.5992 | 48.5992 | 0.0 | Capped Score | review_v4_current_player | 93.24 |
| Jaylen Waddle | WR | 37 | 33 | -4 | 41.1687 | 41.1687 | 0.0 | Capped Score | review_v4_current_player | 88.71 |
| Trey McBride | TE | 9 | 8 | -1 | 62.2578 | 62.2578 | 0.0 | Capped Score | review_v4_current_player | 95.57 |
| Brock Bowers | TE | 54 | 46 | -8 | 34.0184 | 34.0184 | 0.0 | Capped Score | review_v4_current_player | 93.03 |
| Josh Allen | QB | 21 | 19 | -2 | 50.3163 | 50.3163 | 0.0 | Capped Score | review_v4_current_player | 98.31 |
| Patrick Mahomes | QB | 89 | 84 | -5 | 24.1863 | 24.1863 | 0.0 | Scored + Warnings | review_v4_current_player | 96.31 |
| Lamar Jackson | QB | 152 | 144 | -8 | 15.0935 | 15.0935 | 0.0 | Scored + Warnings | review_v4_current_player | 96.24 |
| Keenan Allen | WR | 58 | 124 | 66 | 33.1581 | 17.2422 | -15.9159 | Capped Score | review_v4_current_player | 82.4 |
| Darius Slayton | WR | 94 | 90 | -4 | 23.6148 | 23.6148 | 0.0 | Capped Score | review_v4_current_player | 78.88 |

## Guardrail Verification

- Full-board coverage remains 232 scored QB/RB/WR/TE rows and 8 unscored kickers.
- K rows remain de-emphasized/unscored.
- Legal draft pool remains pending; dropped/released veterans were not invented.
- 2026 5.04 remains No Baseline / Manual late-round watchlist / No exact equivalence.
- Outcome percentages remain blank/in development.
- Legacy active-pack `private_score` remains comparison-only.
- Keenan Allen legacy 82.4 remains comparison-only; current NWR score comes from `review_v4_current_player` lineage.
- Darius Slayton legacy 78.88 remains comparison-only; current NWR score comes from `review_v4_current_player` lineage.
- Team tags, ownership tags, keeper/roster state, and prior draft history remain display/context only.
- Demo-facing source labels hide local filesystem paths in the patched default/advanced surfaces.

## Remaining Suspicious Rows

| row | why |
| --- | --- |
| Chase Brown / CeeDee Lamb | Scores unchanged by this patch; cross-player shape still needs human review, not a hardcoded fix. |
| Trey McBride | Still top-10 TE exception in no-TE-premium; requires human review of TE evidence receipts. |
| Patrick Mahomes / Lamar Jackson | QB shape watch remains after older RB/TE demotion; do not tune to public rank targets. |
| Jaylen Waddle | Still outside top 30; score unchanged, source/trust context should remain visible. |
| Christian McCaffrey | No longer #2, but still top 20; age curve is active and human review should decide whether window risk is enough. |

## Demo Polish Notes

- Draft Prep and Live Draft Room status cards now use wrapping source cards so `My Picks` and `Legal Pool: Pending` do not truncate like metric cards.
- Live Draft Room advanced session details hide raw session key and source path labels.
- Shared Player Detail Card source receipts use demo-safe source labels.
- Streamlit status/menu/footer controls are hidden with best-effort CSS. Streamlit may still show browser/runtime chrome in some dev-server states; chasing deeper runtime toolbar hacks before the birthday demo is not recommended.

## Verdict

The app is closer to birthday-demo Green. Remaining suspicious rows are human-review/model-review items, not quick one-off patches.
