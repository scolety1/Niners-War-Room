# Build Sprint 5AX-R: Top-Priority Identity Repair

## Verdict

`READY_WITH_WAIVERS_FOR_5AY`

Sprint 5AX-R reviewed only the five top-priority blocked veteran rows identified
in Sprint 5AX:

1. Brandon Aiyuk
2. Joe Mixon
3. Tank Dell
4. Jonathon Brooks
5. MarShawn Lloyd

All five players have high-confidence identity evidence from trusted bridge and
exact-id sources. None of the five candidate GSIS ids appear in the 2025
nflverse player-stats source, so no new ready prior-season feature snapshots
were created. The five rows are explicitly waived for partial internal threshold
evaluation only and remain excluded from the ready feature snapshot population.

This sprint did not create probabilities, fake probabilities, app probabilities,
app-readable probability tables, threshold model training, app wiring,
rankings/sorting changes, decision automation, promoted artifacts, push, or
deploy.

## Local Outputs

Local-only exports were written under:

`local_exports/outcome_probability/sprint_5axr_top_priority_identity_repair/`

Created files:

- `top_priority_identity_repair_decisions.csv`
- `top_priority_identity_source_evidence.csv`
- `current_2026_veteran_feature_snapshots_after_priority_repair.csv`
- `coverage_after_priority_identity_repair.csv`
- `remaining_critical_identity_blockers.csv`
- `summary_sprint_5axr.json`
- `README_SPRINT_5AXR.md`

Tracked report:

`docs/outcome_probability/BUILD_SPRINT_5AXR_TOP_PRIORITY_IDENTITY_REPAIR.md`

## Inputs Inspected

The audit inspected local NWR sources only:

- Sprint 5AW feature snapshot and repair-candidate exports.
- Sprint 5AX blocked-player importance audit.
- Current rosters and Niners roster context.
- Current rankings board/display context.
- Sleeper NFL players export.
- `sleeper_nflverse_identity_bridge.csv`.
- Active-roster identity review.
- `dynastyprocess_db_playerids.csv`.
- 2025 nflverse raw and player-season stats.
- Canonical player identity crosswalk.
- Model v4 current/full-board context rows.

Model outputs, rankings, ADP, projections, market values, trade values,
RotoWire rankings/projections/outlooks/values, legacy `private_score`, and
same-season final stats were not used as prediction features or as identity
matching proof.

## Match Policy

Accepted identity evidence:

- `exact_id_match`
- `trusted_bridge_match`
- high-confidence name/position/team consistency with no ambiguity

Rejected identity evidence:

- low-confidence name-only matching
- ambiguous matching
- ranking/projection/ADP/market/trade/private-score based matching
- model-output based matching

## Player Decisions

| Player | Pos | Sleeper ID | Candidate GSIS | 2025 stats row | Team/position consistency | Match method | Confidence | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Brandon Aiyuk | WR | `6803` | `00-0036261` | No | Position consistent; SF context consistent | `trusted_bridge_match|exact_id_match` | High | `waive_for_partial_training` |
| Joe Mixon | RB | `4018` | `00-0033897` | No | Position consistent; current-team field blank/FA context not identity-conflicting | `trusted_bridge_match|exact_id_match` | High | `waive_for_partial_training` |
| Tank Dell | WR | `9502` | `00-0038977` | No | Position consistent; HOU context consistent | `trusted_bridge_match|exact_id_match` | High | `waive_for_partial_training` |
| Jonathon Brooks | RB | `11583` | `00-0039344` | No | Position consistent; CAR context consistent | `trusted_bridge_match|exact_id_match` | High | `waive_for_partial_training` |
| MarShawn Lloyd | RB | `11581` | `00-0039811` | No | Position consistent; GB/GBP context consistent | `trusted_bridge_match|exact_id_match` | High | `waive_for_partial_training` |

Decision reason for all five:

Identity is resolved strongly enough for the top-priority blocker decision, but
the 2025 nflverse factual player-stats rows are absent. The sprint therefore
does not fabricate prior-season features or mark these rows ready. It waives
them from partial internal threshold evaluation with an explicit coverage
warning.

## Evidence Summary

Identity evidence used for all five:

- Sleeper roster/player id context matched the current source id.
- `sleeper_nflverse_identity_bridge.csv` provided trusted matched GSIS ids.
- Active-roster identity review corroborated the bridge.
- `dynastyprocess_db_playerids.csv` provided exact Sleeper-to-GSIS id mappings.
- Canonical crosswalk corroborated the GSIS ids.

2025 stats evidence:

- `player_stats_2025_player_season.csv`: no rows for any of the five candidate
  GSIS ids.
- `player_stats_2025.csv`: no raw weekly rows for any of the five candidate
  GSIS ids.

The absence of a factual 2025 stats row was treated as a hard feature-snapshot
gap, not as a license to create zero or placeholder production.

## Coverage After Priority Repair

| Metric | Value |
| --- | ---: |
| Prior ready veteran rows | 520 |
| Top-priority players reviewed | 5 |
| Newly repaired ready feature rows | 0 |
| Waived for partial training | 5 |
| New ready veteran rows | 520 |
| Still blocked feature snapshot rows | 172 |
| Critical identity blockers remaining | 0 |

Partial internal threshold evaluation can proceed only as:

`yes_internal_only_with_top_priority_waivers_and_coverage_warning`

## Remaining Critical Blockers

No critical identity blockers remain after the explicit waiver pass.

The waived players still do not have ready 2026 veteran feature snapshots because
the required 2025 factual stats rows are absent. They must remain excluded from
partial internal threshold evaluation.

## 5AY Decision

Sprint 5AY partial threshold model evaluation may start next if HQ accepts the
top-priority waivers and the coverage warning.

Allowed next state:

- Internal-only threshold evaluation.
- 520 ready veteran feature rows only.
- Waived players excluded.
- Rookies remain separate.
- K rows remain not applicable.

Still blocked:

- App probabilities.
- App-readable probability tables.
- Rankings/sorting changes.
- Player-facing percentages or bands.
- Promoted model artifacts.

## Confirmed Non-Actions

- No probabilities were created.
- No fake probabilities were created.
- No calibrated probabilities were created.
- No app probabilities were created.
- No app-readable probability tables were created.
- No threshold model training was run.
- No app wiring was changed.
- No rankings or sorting were changed.
- No decision automation was created.
- No model artifacts were promoted.
- No push or deploy occurred.
