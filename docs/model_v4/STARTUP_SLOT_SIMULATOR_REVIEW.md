# Startup Slot Simulator Review

## Scope

This review-only simulator combines existing Model v4 player, prospect, and pick values into an internal startup-style slot board. It is not ADP, not a market mock, and not a final recommendation layer.

## Outputs

- `startup_slot_review_rows.csv`
- `startup_slot_component_rows.csv`
- `startup_slot_pick_zone_rows.csv`
- `startup_slot_bucket_rows.csv`
- `startup_slot_receipts.csv`
- `startup_slot_warnings.csv`

## Top Internal Slots

| Slot | Asset | Type | Score | Nearby After |
|---:|---|---|---:|---|
| 1 | 2026 1.03 | owned_rookie_pick | 93.6 | 2026 1.04 |
| 2 | 2026 1.04 | owned_rookie_pick | 90.4 | Trey McBride |
| 3 | Trey McBride | available_or_context_player | 87.4776 | Puka Nacua |
| 4 | Puka Nacua | available_or_context_player | 83.0486 | Jaxon Smith-Njigba |
| 5 | Jaxon Smith-Njigba | available_or_context_player | 82.8713 | Christian McCaffrey |
| 6 | Christian McCaffrey | available_or_context_player | 82.8329 | Josh Allen |
| 7 | Josh Allen | available_or_context_player | 80.3133 | Jonathan Taylor |
| 8 | Jonathan Taylor | available_or_context_player | 80.1465 | Bijan Robinson |
| 9 | Bijan Robinson | available_or_context_player | 79.9939 | Jeremiyah Love |
| 10 | Jeremiyah Love | rookie_prospect | 75.3111 | Ja'Marr Chase |
| 11 | Ja'Marr Chase | available_or_context_player | 74.1258 | Jahmyr Gibbs |
| 12 | Jahmyr Gibbs | available_or_context_player | 73.9972 | 2026 2.04 |

## Pick Zones

| Pick | Baseline | Review Label | Nearby Model Neighbors | Trade Reality |
|---|---:|---|---|---|
| 2026 1.03 | 93.6 | review_trade_down_or_defer | Trey McBride (87.4776), Puka Nacua (83.0486), Jaxon Smith-Njigba (82.8713), Christian McCaffrey (82.8329), Josh Allen (80.3133), Jonathan Taylor (80.1465), Bijan Robinson (79.9939), Jeremiyah Love (75.3111) | 2026 1.03 is shown near elite/current assets by internal model score only. This is opportunity-cost context, not a claim that one pick can buy those players. |
| 2026 1.04 | 90.4 | review_trade_down_or_defer | Trey McBride (87.4776), Puka Nacua (83.0486), Jaxon Smith-Njigba (82.8713), Christian McCaffrey (82.8329), Josh Allen (80.3133), Jonathan Taylor (80.1465), Bijan Robinson (79.9939), Jeremiyah Love (75.3111) | 2026 1.04 is shown near elite/current assets by internal model score only. This is opportunity-cost context, not a claim that one pick can buy those players. |
| 2026 2.04 | 71.4 | review_trade_down_or_defer | Makai Lemon (69.2158), Jahmyr Gibbs (73.9972), Ja'Marr Chase (74.1258), Amon-Ra St. Brown (68.5918), Jeremiyah Love (75.3111), De'Von Achane (66.6696), Derrick Henry (66.2156), Jalen Hurts (65.098) | Nearby assets are internal value neighbors only; verify actual trade market separately. |
| 2026 2.08 | 58.6 | review_rookie_vs_drop_player | Josh Jacobs (58.5387), Chase Brown (58.299), Chris Brazzell (57.7934), Chris Olave (59.4933), Davante Adams (57.5485), Nico Collins (59.7382), Drake London (57.2578), Travis Kelce (57.1755) | Nearby assets are internal value neighbors only; verify actual trade market separately. |
| 2026 5.04 |  | manual_only_no_exact_model_baseline |  | Manual-only pick baseline; no trade-market equivalence or package context is admitted. |

## Outcome Bucket Guardrails

Low-confidence or missing historical profile buckets: `123`.

- Outcome buckets are display-only calibration context.
- Missing historical outcomes are unknown, not misses.
- Buckets do not feed back into rankings.
- Nearby model neighbors are not one-for-one trade-market equivalents.
- 2025 outcomes remain immature and are not treated as complete career outcomes.
- Market, ADP, projection, ranking, mock, and big-board inputs remain blocked from private value.
