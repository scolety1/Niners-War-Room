# Build Sprint 5AW: 2026 Identity Repair

## Verdict

`PARTIAL_READY_FOR_INTERNAL_TRAINING_WITH_COVERAGE_WARNING`

Sprint 5AW repaired a small number of 2026 veteran identity rows and rebuilt the
local-only veteran feature snapshot coverage export. The repair pass increased
ready veteran feature snapshots from 517 to 520, while 172 modeled veteran rows
remain blocked for identity/manual review.

This sprint did not create probabilities, fake probabilities, calibrated
probabilities, app probabilities, app wiring, rankings/sorting changes,
decision automation, app-readable probability tables, promoted artifacts, push,
or deploy.

## Local Outputs

Local-only exports were written under:

`local_exports/outcome_probability/sprint_5aw_2026_identity_repair/`

Created files:

- `identity_source_inventory.csv`
- `identity_repair_candidates.csv`
- `identity_repair_decisions.csv`
- `current_2026_veteran_feature_snapshots_after_identity_repair.csv`
- `current_2026_veteran_feature_coverage_after_identity_repair.csv`
- `identity_manual_review_queue.csv`
- `remaining_veteran_feature_blockers.csv`
- `summary_sprint_5aw.json`
- `README_SPRINT_5AW.md`

Tracked report:

`docs/outcome_probability/BUILD_SPRINT_5AW_2026_IDENTITY_REPAIR.md`

## Identity Sources Inspected

The repair audit inspected the restored/current local identity sources needed
for a strict 2026 veteran identity pass:

| Source | Rows |
| --- | ---: |
| Current rosters | 240 |
| Available veterans | 460 |
| Rookie draftables | 80 |
| Sprint 5AV identity audit | 692 |
| Sprint 5AV veteran snapshots | 692 |
| Sleeper/nflverse identity bridge | 3,989 |
| Active-roster identity review | 232 |
| dynastyprocess player ids | 12,440 |
| Sleeper NFL players | 12,103 |
| nflverse identity map | 232 |
| Canonical player identity crosswalk | 110,023 |
| nflverse players | 24,966 |
| Full-board identity/team repair audit | 61 |
| 2025 player-season stats | 2,020 |

Forbidden sources and fields were not used for prediction features or repair
decisions. The audit did not use ADP, public rankings, projections, market
values, trade values, prior fantasy draft history, RotoWire
rankings/projections/outlooks/values, legacy `private_score`, model outputs, or
same-season final stats as prediction features.

## Repair Policy

Accepted repair classes:

- `exact_id_match`
- `trusted_bridge_match`
- `high_confidence_name_position_team_match`

Blocked or review-only classes:

- `ambiguous_manual_review`
- `unmatched`
- `blocked_position_mismatch`
- `blocked_missing_dob_age`
- `not_applicable`

Name/position/team matching was accepted only when the candidate was unique
enough for a conservative identity repair and did not introduce a conflicting
position. Ambiguous and unmatched rows remain out of the ready feature snapshot
set.

## Repair Decisions

Decision counts:

| Decision | Rows |
| --- | ---: |
| `accept_high_confidence_name_position_team_match` | 3 |
| `blocked_position_mismatch` | 4 |
| `unmatched` | 168 |

Accepted repairs:

| Player | Pos | Current source id | GSIS id | Repair source |
| --- | --- | --- | --- | --- |
| Keleki Latu | TE | `12765` | `00-0040363` | `2025_stats_exact_name_position_team` |
| Zaire Mitchell-Paden | TE | `8799` | `00-0037340` | `2025_stats_exact_name_position_team` |
| Quentin Skinner | WR | `12907` | `00-0040406` | `2025_stats_exact_name_position_team` |

These three rows were previously blocked by missing legal age identity metadata.
The accepted repairs used the 2025 stats exact name/position/team candidate and
nflverse identity metadata. No low-confidence name-only matches were silently
accepted.

## Feature Snapshot Rebuild

The local-only feature snapshot export was rebuilt after accepted repairs:

`current_2026_veteran_feature_snapshots_after_identity_repair.csv`

Coverage after repair:

| Metric | Count |
| --- | ---: |
| Modeled veteran QB/RB/WR/TE rows | 692 |
| Previous ready veteran rows | 517 |
| New ready veteran rows | 520 |
| Newly repaired rows | 3 |
| Still blocked veteran rows | 172 |
| Manual review queue rows | 172 |
| Rookie rows separated | 80 |

Snapshot rows remain local-only and contain legal prior-season 2025 veteran
features using the Sprint 5AV renamed schema and `REG_ONLY` policy. They do not
contain probabilities, ranks/sort instructions, app display values, model
scores, or model artifacts.

## Remaining Blockers

Remaining blocker counts:

| Blocker | Rows |
| --- | ---: |
| `unmatched` | 168 |
| `blocked_position_mismatch` | 4 |

The manual review queue contains 172 rows. No ambiguous rows were accepted
silently. These rows require manual identity review or an explicit HQ policy
decision before they can be used as ready veteran feature snapshots.

## Rookie Path

Rookies remain separate from the veteran prior-season feature snapshot layer:

- Rookie rows: 80.
- Rookie rows were not forced through veteran prior-season features.
- Rookie model design remains a separate future path.

## 5AX Decision

Sprint 5AX threshold model training should not start as a clean full-coverage
training sprint yet.

Threshold model training can start next only as internal partial-coverage
training with an explicit coverage warning and HQ approval.

Why:

- The veteran feature snapshot layer improved from 517 to 520 ready rows.
- Coverage remains incomplete: 172 of 692 modeled veteran rows are still
  blocked.
- The remaining blockers are identity/manual-review problems, not model-release
  problems that can be solved by displaying probabilities.

Recommended next step:

Either complete manual identity review for the 172 blocked veteran rows or get
HQ approval for partial-coverage internal training before starting 5AX.

## Confirmed Non-Actions

- No probabilities were created.
- No fake probabilities were created.
- No calibrated probabilities were created.
- No app probabilities were created.
- No app wiring was changed.
- No rankings or sorting were changed.
- No decision automation was created.
- No app-readable probability tables were created.
- No model artifacts were promoted.
- No push or deploy occurred.
