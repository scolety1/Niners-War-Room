# Build Sprint 5AX: Blocked Player Importance Audit

## Verdict

`REPAIR_TOP_PRIORITY_IDENTITIES_FIRST`

Sprint 5AX audited the 172 veteran identity rows that remained blocked after
Sprint 5AW. The audit found that most blocked rows are low-priority available
depth, but the blocked set still includes three critical ranked/rostered players
and two additional important rostered players.

Partial internal threshold training on the 520 ready veteran rows should not
start yet unless HQ explicitly waives the top-priority coverage gap.

This sprint did not train models, create probabilities, create fake
probabilities, create app-readable probability tables, wire probabilities into
the app, change rankings/sorting, create decision automation, promote artifacts,
push, or deploy.

## Local Outputs

Local-only exports were written under:

`local_exports/outcome_probability/sprint_5ax_blocked_player_importance_audit/`

Created files:

- `blocked_player_importance_audit.csv`
- `top_identity_repair_candidates.csv`
- `partial_training_coverage_policy.csv`
- `manual_review_priority_queue.csv`
- `summary_sprint_5ax.json`
- `README_SPRINT_5AX.md`

Tracked report:

`docs/outcome_probability/BUILD_SPRINT_5AX_BLOCKED_PLAYER_IMPORTANCE_AUDIT.md`

## Audit Inputs

The audit used local NWR context only:

- Sprint 5AW manual review queue:
  `local_exports/outcome_probability/sprint_5aw_2026_identity_repair/identity_manual_review_queue.csv`
- Current player board:
  `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv`
- Current league rosters:
  `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks_draft_pool_20260508_213233/fact_rosters.csv`
- Available veterans:
  `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks_draft_pool_20260508_213233/fact_available_veterans.csv`
- Official ranking display context:
  `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks_draft_pool_20260508_213233/fact_official_rankings.csv`
- Current player dimension/status rows:
  `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks_draft_pool_20260508_213233/dim_players.csv`
- Recovered Sleeper player status rows:
  `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks_draft_pool_20260508_213233/draft_pool_downloads/sleeper_players_nfl.csv`

The audit used board/rank/status fields only to classify importance and manual
repair priority. It did not use those fields as threshold probability training
features.

Forbidden probability/model inputs were not used. The audit did not use ADP,
public projections, public rankings as prediction features, market values, trade
values, prior fantasy draft history, RotoWire
rankings/projections/outlooks/values, legacy `private_score`, same-season final
stats, label supplement sources, or outcome model outputs as prediction
features.

## Classification Policy

Blocked veteran rows were classified into:

- `critical_repair_before_training`
- `important_but_can_train_partial`
- `low_priority_depth`
- `inactive_or_irrelevant`
- `ambiguous_manual_review`

Critical rows include Niners roster players and high-visibility ranked/rostered
players. Important rows include other rostered or visible players that matter
but do not alone imply a full coverage stop. Position-mismatch rows without
high-visibility signals remain manual review. Available depth rows without
current board/player-card visibility are low priority.

## Results

Total blocked veteran rows:

`172`

Classification counts:

| Classification | Rows |
| --- | ---: |
| `critical_repair_before_training` | 3 |
| `important_but_can_train_partial` | 2 |
| `low_priority_depth` | 163 |
| `inactive_or_irrelevant` | 0 |
| `ambiguous_manual_review` | 4 |

Context counts:

| Signal | Rows |
| --- | ---: |
| Rostered blocked rows | 5 |
| Niners roster blocked rows | 1 |
| App/player-card blocked rows | 5 |

All 172 blocked rows had recovered Sleeper `Active` / `active=True` local
status. The low-priority classification means low board/player-card relevance,
not verified retirement or inactivity.

## Top 25 Repair Candidates

| Priority | Player | Pos | Team | Classification | NWR Rank | League Rank | Source pool |
| ---: | --- | --- | --- | --- | ---: | ---: | --- |
| 1 | Brandon Aiyuk | WR | SF | `critical_repair_before_training` | 84 | 98 | `rostered_player` |
| 2 | Joe Mixon | RB |  | `critical_repair_before_training` | 97 | 142 | `rostered_player` |
| 3 | Tank Dell | WR | HOU | `critical_repair_before_training` | 113 | 177 | `rostered_player` |
| 4 | Jonathon Brooks | RB | CAR | `important_but_can_train_partial` | 227 | 176 | `rostered_player` |
| 5 | MarShawn Lloyd | RB | GB | `important_but_can_train_partial` | 228 | 255 | `rostered_player` |
| 6 | Reggie Gilliam | RB | NE | `ambiguous_manual_review` |  |  | `available_veteran` |
| 7 | Brady Russell | TE | SEA | `ambiguous_manual_review` |  |  | `available_veteran` |
| 8 | Bo Melton | WR | GB | `ambiguous_manual_review` |  |  | `available_veteran` |
| 9 | Velus Jones | WR | SEA | `ambiguous_manual_review` |  |  | `available_veteran` |
| 10 | Aaron Bailey | QB | BAL | `low_priority_depth` |  |  | `available_veteran` |
| 11 | Bailey Zappe | QB | NYJ | `low_priority_depth` |  |  | `available_veteran` |
| 12 | Cam Miller | QB | MIA | `low_priority_depth` |  |  | `available_veteran` |
| 13 | Carter Bradley | QB | JAX | `low_priority_depth` |  |  | `available_veteran` |
| 14 | Case Keenum | QB | CHI | `low_priority_depth` |  |  | `available_veteran` |
| 15 | Connor Bazelak | QB | TB | `low_priority_depth` |  |  | `available_veteran` |
| 16 | Deshaun Watson | QB | CLE | `low_priority_depth` |  |  | `available_veteran` |
| 17 | DJ Uiagalelei | QB | LAC | `low_priority_depth` |  |  | `available_veteran` |
| 18 | Garrett Greene | QB | TB | `low_priority_depth` |  |  | `available_veteran` |
| 19 | Graham Mertz | QB | HOU | `low_priority_depth` |  |  | `available_veteran` |
| 20 | Hendon Hooker | QB | TEN | `low_priority_depth` |  |  | `available_veteran` |
| 21 | Jalen Morton | QB | IND | `low_priority_depth` |  |  | `available_veteran` |
| 22 | Kurtis Rourke | QB | SF | `low_priority_depth` |  |  | `available_veteran` |
| 23 | Kyle McCord | QB | GB | `low_priority_depth` |  |  | `available_veteran` |
| 24 | Nick Schuessler | QB | PIT | `low_priority_depth` |  |  | `available_veteran` |
| 25 | Sam Ehlinger | QB | DEN | `low_priority_depth` |  |  | `available_veteran` |

## Partial Training Decision

Partial internal threshold training on the 520 ready veteran rows is not
acceptable as the next default step.

Reason:

- Brandon Aiyuk is a blocked Niners roster/player-card row.
- Joe Mixon and Tank Dell are blocked ranked rostered/player-card rows.
- Jonathon Brooks and MarShawn Lloyd are additional blocked rostered/player-card
  rows.
- The remaining 163 low-priority depth rows are not individually blocking, but
  the top five rostered rows should be repaired or explicitly waived first.

Decision:

`no_not_before_critical_repairs_or_explicit_hq_waiver`

## Next Sprint

Sprint 5AY threshold model evaluation should not start automatically from this
state.

Next safe work:

1. Repair the top-priority identities for Brandon Aiyuk, Joe Mixon, Tank Dell,
   Jonathon Brooks, and MarShawn Lloyd.
2. Resolve or consciously waive the four position-mismatch rows: Reggie Gilliam,
   Brady Russell, Bo Melton, and Velus Jones.
3. Re-run Sprint 5AX after repairs or HQ waiver.

## Confirmed Non-Actions

- No probabilities were created.
- No fake probabilities were created.
- No calibrated probabilities were created.
- No app probabilities were created.
- No app-readable probability tables were created.
- No app wiring was changed.
- No rankings or sorting were changed.
- No decision automation was created.
- No model artifacts were promoted.
- No push or deploy occurred.
