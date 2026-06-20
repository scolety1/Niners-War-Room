# NWR NFL Stats Field Policy V1

Date: 2026-06-20

Owner: Master/Main HQ

Status: YELLOW. nflverse stats remain display-only/latest-candidate context. No nflverse field is approved for private value, hidden ranking/sort, model training, recommendations, simulations, final draft-day decisions, or direct Mock Draft use.

## Research Basis

Deep Research reviewed the current nflverse field inventory and concluded:

- Current kept/display fields are enough for basic stat display.
- Current kept/display fields are not enough for strong dynasty sustainability, role quality, breakout probability, decline risk, or opportunity durability.
- The biggest missing signals are role-context fields and missing datasets, especially `rosters`, `weekly_rosters`, `participation`, and `opportunity`.
- EPA/CPOE/WOPR/PACR/RACR/share metrics may be useful, but should remain display-only or backtest-only until proven.
- `fantasy_points` and `fantasy_points_ppr` should remain quarantined.
- No field is approved yet for private value, hidden rank/sort, recommendations, simulations, or final draft decisions.

## Current Approved Status

| Area | Status |
| --- | --- |
| nflverse raw snapshots | Local-only source material |
| `stats_context` Lane Exchange packages | `latest_candidate` display/stat context only |
| Private value | Not approved |
| Hidden ranking/sort | Not approved |
| Model training | Not approved |
| Recommendations | Not approved |
| Simulations | Not approved |
| Final draft-day decisions | Not approved |
| Mock Draft direct use | Not approved |

The current `stats_context` packages may support human-readable stat display and source review only. They must not be merged into `model_value/veteran_private_values`, Rookie rankings, Mock Draft recommendations, Outcome modeling, or hidden sort/rank logic without a later Tim/Master/QA-approved source policy.

## GREEN Future-Test Fields And Categories

GREEN means suitable to expand into local-only display candidates and backtest inventories. It does not mean approved for private value or model use.

| Field/category | Status | Rationale |
| --- | --- | --- |
| Games played | GREEN future-test | Basic availability/durability context. |
| Age / experience / roster metadata | GREEN future-test | Necessary for lifecycle and identity context, but not a standalone value signal. |
| `rosters` dataset | GREEN future-test | Needed for age, experience, team, position, and player metadata. |
| `weekly_rosters` dataset | GREEN future-test | Needed for weekly team/role availability context. |
| `participation` dataset | GREEN future-test | Needed for routes/participation and role quality. |
| `opportunity` dataset | GREEN future-test | Needed for targets/carries/routes-like opportunity context. |
| Air yards | GREEN future-test | Useful role-context candidate if kept separate from private value. |
| YAC | GREEN future-test | Useful display and role-quality candidate. |
| Sack metrics | GREEN future-test | Useful QB risk/context candidate. |
| Fumble metrics | GREEN future-test | Useful risk/context candidate, not standalone valuation. |
| Return stats | GREEN future-test | Useful for context where scoring/settings care about return role. |
| First-down production/rates | GREEN future-test | Stronger role-quality candidate than raw yards alone. |
| Snap share trends | GREEN future-test | Important playing-time/role trend context. |
| Target/carry trends | GREEN future-test | Important opportunity trend context. |

## YELLOW Backtest-Only Fields And Categories

YELLOW means research/backtest only. These fields must remain excluded from display candidates or clearly labeled if shown, and they are not approved for private value, hidden sorting, or recommendations.

| Field/category | Status | Required gate |
| --- | --- | --- |
| `passing_epa` | YELLOW backtest-only | Prove incremental signal beyond simple QB usage/counting stats. |
| `rushing_epa` | YELLOW backtest-only | Prove stable position-specific value beyond volume and first downs. |
| `receiving_epa` | YELLOW backtest-only | Prove stable receiver/TE signal beyond targets, yards, first downs, and routes. |
| `passing_cpoe` | YELLOW backtest-only | Prove predictive QB signal and avoid overfitting. |
| `target_share` | YELLOW backtest-only | Strong role signal, but must be backtested and source-policy approved. |
| `air_yards_share` | YELLOW backtest-only | Strong role signal, but can distort value if blended without context. |
| `wopr` | YELLOW backtest-only | Composite opportunity metric; requires proof before use. |
| `pacr` | YELLOW backtest-only | Efficiency/air-yards conversion metric; requires proof before use. |
| `racr` | YELLOW backtest-only | Efficiency/air-yards conversion metric; requires proof before use. |
| Advanced efficiency/share/expected/diff fields | YELLOW backtest-only | Must show incremental signal and stability before policy upgrade. |

## RED Blocked Fields And Categories

RED means blocked from model/ranking/private-value use in V1. Some fields may remain in raw local snapshots for audit only.

| Field/category | Status | Reason |
| --- | --- | --- |
| `fantasy_points` | RED blocked | Direct scoring output risks target leakage and circular modeling. |
| `fantasy_points_ppr` | RED blocked | Direct scoring output risks target leakage and circular modeling. |
| `headshot_url` for modeling | RED blocked | Identity/display asset, not football signal. |
| Penalties | RED blocked | No current policy that penalties are stable/useful for NWR dynasty value. |
| `misc_yards` | RED blocked | Ambiguous without stronger source semantics. |
| Most fumble recovery fields | RED blocked | High-noise event fields; audit/display only unless later proven. |
| Kicker detail buckets | RED blocked | Not relevant to current NWR format. |
| Defensive stats | RED blocked | Not relevant unless IDP is added. |
| 2-point conversion fields as predictive model inputs | RED blocked | Sparse/noisy event fields; display/audit only. |

## Missing Dataset Expansion Plan

The next safe implementation should expand raw/local-only nflverse pulls and display candidates. It must not approve model use.

1. Update the nflverse puller to include `rosters`.
2. Add `weekly_rosters`.
3. Add `participation`.
4. Add `opportunity`.
5. Preserve all outputs as local-only raw snapshots and display-only/latest-candidate packages.
6. Keep `latest_approved` manual-gated.
7. Do not approve private value, hidden ranking/sort, recommendations, simulations, or final draft decisions.

Candidate package expansions should remain under `stats_context` and clearly label `allowed_use` as display/stat context or backtest inventory only.

## Future Derived Feature Ideas

These are backtest-only ideas, not approved features:

- rolling 4-week targets
- rolling carries
- snap share trend
- route participation trend
- first downs per target
- first downs per carry
- first downs per reception
- yards per opportunity
- age/experience curve
- durability/games played
- RB receiving role
- WR air-yard role
- TE route/target role
- QB sack trend
- QB air-yard trend
- QB efficiency trend

Derived features must be created only in a backtest-only research package until Tim/Master/QA approves a source policy upgrade.

## Backtest Plan

Backtests must stay isolated from private value and Mock Draft.

Required rules:

- No private-value integration.
- No `veteran_private_values` mutation.
- No Mock Draft recommendations.
- No hidden ranking or hidden sorting.
- No final draft-day decisions.
- No app wiring.
- No deployment.

Backtest target:

- Evaluate next-season and next-8-week NWR scoring outcomes.
- Evaluate by QB/RB/WR/TE separately.
- Compare baseline kept fields vs expanded volume/usage vs advanced fields.
- Measure RMSE, MAE, and rank correlation.
- Determine incremental signal beyond simple usage/counting stats.
- Flag instability, overfitting, missingness, and position-specific failure modes.
- Require Tim/Master/QA approval before any model/private-value use.

Backtest tiers:

1. Baseline display fields: attempts, completions, yards, TD/INT, carries, targets, receptions, first downs, snap counts.
2. Expanded volume/role fields: games played, air yards, YAC, sacks, fumbles, return role, rosters/weekly_rosters metadata, participation, opportunity.
3. Advanced fields: EPA, CPOE, target share, air-yards share, WOPR, PACR, RACR, expected/diff fields.

Any advanced-field win must be proven out of sample and reviewed before moving from YELLOW to any future GREEN model-candidate status.

## Recommended Implementation Order

1. Expand nflverse puller to missing datasets: `rosters`, `weekly_rosters`, `participation`, `opportunity`.
2. Expand normalizer display candidates for GREEN low-risk fields.
3. Create a backtest-only feature inventory package/report.
4. Run historical backtest against next-season and next-8-week NWR scoring outcomes.
5. Review results by position and field group.
6. Only then propose model/private-value integration, if the evidence supports it.

## Recommended Next Prompt

```text
You are Master/Main HQ for Niners War Room.

Implement nflverse dataset expansion V1 for display-only/latest_candidate context.

Add local-only puller/normalizer support for rosters, weekly_rosters, participation, and opportunity datasets. Do not approve model use. Do not update latest_approved. Do not touch Mock Draft, Rookie, Drop Decision, Outcome, Deployment V2, Trading Lab, or QA/Data Hygiene. Do not run simulations or deploy.

Keep all new fields display-only or backtest-inventory-only according to NWR_NFL_STATS_FIELD_POLICY_V1. Validate row counts, headers, quarantined fields, and no private-value/ADP/market leakage. Return package candidates, skipped datasets, warnings, and remaining gates.
```

## Master Verdict

GREEN for field policy documentation.

YELLOW for implementation because missing datasets and backtests remain.

RED for any attempt to use nflverse fields as private value, hidden rank/sort, recommendations, simulations, or final draft-day decisions before Tim/Master/QA approval.
