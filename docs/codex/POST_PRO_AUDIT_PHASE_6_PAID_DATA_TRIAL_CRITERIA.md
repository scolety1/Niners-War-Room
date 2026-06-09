# Post-Pro Audit Phase 6: Paid Data Trial Criteria

Status: planning only. No subscription, purchase, scraping, provider API wiring,
or model-score promotion is part of this phase.

## Goal

Run a small, controlled paid-data trial to learn whether a provider can solve the
model's actual evidence gaps: route/participation, target earning, RB workload,
red-zone/goal-line role, injury reliability, and clean projection exports.

The trial must stay local-first and preview-only.

## Saved Trial Templates

- Sample players:
  `templates/real_data_inputs/paid_data_trial/paid_data_trial_sample_players.csv`
- Required paid fields:
  `templates/real_data_inputs/paid_data_trial/paid_data_trial_required_fields.csv`
- Provider comparison:
  `templates/real_data_inputs/paid_data_trial/paid_data_trial_provider_comparison.csv`
- Acceptance criteria:
  `templates/real_data_inputs/paid_data_trial/paid_data_trial_acceptance_criteria.csv`

## Sample Set

Use the full 40-player Truth Set when possible. If a provider has request limits,
use the first 20 `minimum_20` players from the sample template.

### Minimum 20

This set covers Niners roster decisions, disputed WR/RB balances, elite anchors,
young-player bridge controls, 1QB suppression, and no-TE-premium behavior:

| player | position | reason |
|---|---|---|
| Lamar Jackson | QB | Niners roster / elite-rushing QB control |
| Brian Thomas Jr. | WR | Niners roster young WR |
| De'Von Achane | RB | Niners roster young RB |
| Luther Burden | WR | Niners roster young bridge |
| Kaleb Johnson | RB | Niners roster young bridge |
| Jayden Higgins | WR | Niners roster young bridge |
| Jaxon Smith-Njigba | WR | WR ranking dispute control |
| Tee Higgins | WR | WR ranking dispute control |
| Chase Brown | RB | RB workload control |
| Brenton Strange | TE | Niners roster TE control |
| Kyren Williams | RB | RB role vs dynasty control |
| Bijan Robinson | RB | elite RB anchor |
| Jahmyr Gibbs | RB | elite young RB anchor |
| Justin Jefferson | WR | elite WR anchor |
| Ja'Marr Chase | WR | elite WR anchor |
| CeeDee Lamb | WR | elite WR anchor |
| Amon-Ra St. Brown | WR | elite WR anchor |
| Puka Nacua | WR | elite WR anchor |
| Brock Bowers | TE | elite TE / no-premium control |
| Josh Allen | QB | elite QB / 1QB control |

The full 40 adds missing-projection controls, team-mismatch controls, older RB/WR
controls, young WR/TE controls, and incoming-rookie controls.

## Required Paid-Data Fields

The first trial should prioritize fields that free/public data cannot reliably
provide:

| bucket | required fields |
|---|---|
| Route/usage | routes run, route participation, snap share |
| Target earning | target share, targets per route run |
| Efficiency | yards per route run |
| RB workload | RB opportunity share, weighted opportunities |
| Scoring role | red-zone usage, goal-line usage |
| Injury | current injury status, practice status if available, injury history |
| Projections | games, starts where applicable, passing/rushing/receiving stat projections |
| Identity/source | provider player ID, name, team, position, export date, source/terms reference |

Fields must be numeric where they represent metrics. Prose workload notes are
review-only and cannot become model evidence.

## Provider Comparison Fields

Every provider trial should record:

- provider
- export format
- API/CSV/XLS access
- player ID fields
- mapping method to Sleeper/nflverse/GSIS/PFR
- cost or quoted tier
- update frequency
- terms/licensing allowance for local personal analysis
- fields available
- sample coverage
- missing fields
- trial recommendation

## Providers To Compare

| provider | first thing to test | why |
|---|---|---|
| Fantasy Points Data Suite | routes, route share, target share, TPRR, YPRR, red-zone/goal-line usage | best chance to fix role/usage evidence if export is legal |
| PFF+ | routes run, YPRR, advanced usage CSV export | strong route/YPRR fallback if API is not needed |
| FantasyData | snap/target/red-zone/projection/injury API or CSV/XLS | budget broad-data fallback |
| SportsDataIO | projections, injuries, depth charts, player IDs, red-zone data | stable API fallback if cost is justified |
| FantasyPros | projection fields only | useful projection sanity source, not a role/usage solution |

Do not use any provider that requires forbidden scraping.

## Acceptance Criteria

A provider passes only if all of these are true:

1. Legal export/API terms allow local personal analysis or written permission is
   available.
2. No forbidden scraping is required.
3. Field names are stable across at least two exports/pulls.
4. Numeric fields parse cleanly; blanks are allowed when the provider does not
   offer that field.
5. At least 95% of sample players map cleanly to Sleeper/nflverse identity.
6. No high-value sample player has ambiguous identity.
7. The provider improves at least one real gap, preferably route/usage.
8. Trial rows can be displayed in player receipts with raw value, source date,
   source status, and warning status.
9. Trial rows remain in `local_exports/paid_data_trials/...` and do not mutate
   active data packs or active rankings.
10. Cost-to-edge is reasonable enough to justify a larger trial.

## Trial Output Folder

When a provider sample arrives, store it under:

`local_exports/paid_data_trials/<provider>/<trial_id>/`

Expected files:

- raw provider export
- normalized provider trial CSV
- provider field coverage report
- identity mapping report
- source terms note
- trial validation summary
- receipt preview
- recommendation note

## Pass / Continue / Reject

| verdict | meaning |
|---|---|
| `reject` | terms, fields, identity, or cost fail the sample |
| `keep_testing` | useful fields exist but mapping/terms/coverage need one more sample |
| `candidate_subscription` | sample clearly fills critical gaps and passes export rules |
| `defer` | useful later, but not needed before roster decisions |

## Recommendation

Start with one route/usage trial, not a broad expensive API subscription.

Best first ask:

1. Fantasy Points Data Suite if legal CSV/API export exists.
2. PFF+ if manual CSV export is easier and terms allow local use.
3. FantasyData/SportsDataIO only if route data fails or if projections/injuries
   become the bigger gap.

Keep market and generic dynasty rank providers out of private/model value. They
can help trade/liquidity surfaces later, but they will not fix the scoring brain.
