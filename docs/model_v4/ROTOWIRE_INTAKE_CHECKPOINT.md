# RotoWire Intake Checkpoint

Date: 2026-05-17

## Verdict

The RotoWire manual-export intake spine is working and is now the best local
source package for Model v4. It should replace the earlier rejected/manual
stat tables and supersede the FantasyPros-only stats-first layer as the primary
historical evidence source.

This checkpoint does not promote any app rankings or readiness gates.

## Raw Archive

Raw user exports are preserved under:

`local_exports/model_v4/raw_user_exports/rotowire_manual`

The rookie/prospect upload staging area is:

`local_exports/model_v4/raw_user_exports/rookie_manual/incoming`

## Intake Outputs

Generated under:

`local_exports/model_v4/rotowire_intake/latest`

| Output | Rows / status |
| --- | ---: |
| `rotowire_source_index.csv` | 128 files indexed |
| `rotowire_source_index_summary.csv` | 103 active canonical files, 25 inactive duplicate/sample files |
| `rotowire_schema_catalog.csv` | 37 stable schema groups |
| `rotowire_player_stats_clean_rows.csv` | 19,520 player-stat rows |
| `rotowire_role_usage_clean_rows.csv` | 9,083 role/usage rows |
| `rotowire_context_clean_rows.csv` | 5,777 context rows |
| `rotowire_truth_set_identity_coverage.csv` | 80 / 80 truth-set players covered |
| `rotowire_evidence_rows.csv` | 640 component evidence rows |
| `rotowire_evidence_coverage.csv` | 75 covered, 5 review |

## Evidence Lanes

Scoring-allowed or scoring-allowed-with-confidence-penalty:

- historical passing/rushing/receiving player stats
- RotoWire snap counts
- target-leader rows
- receiver alignment
- TE route data
- licensed receiving route metrics from RotoWire advanced receiving exports
- red-zone passing/rushing/receiving data

Context-only / review-only:

- RotoWire projections
- injuries
- depth charts
- ADP, cheat sheets, and rankings context
- team context and offensive-line context
- combine/workout data

Forbidden from private football value:

- market/ADP
- league rank
- unsourced injury absence as healthy evidence
- projections as core value

## Review Coverage

The only truth-set players still in review coverage are incoming rookies with
no NFL production or role usage history:

- Fernando Mendoza
- Jeremiyah Love
- Carnell Tate
- Jordyn Tyson
- Kenyon Sadiq

This is expected. They need a separate rookie/prospect evidence layer, not fake
NFL production.

## Important Fix Made

QB role usage is now marked `not_applicable`, not missing. QBs are not penalized
for lacking RB/WR/TE snap-target-route role buckets.

## Guardrails Confirmed

- Active app rankings unchanged.
- My Team unchanged.
- War Board unchanged.
- No readiness gate unlocked.
- Raw exports remain immutable.
- RotoWire data is local licensed user-export evidence and should not be
  redistributed in public audit packets.

