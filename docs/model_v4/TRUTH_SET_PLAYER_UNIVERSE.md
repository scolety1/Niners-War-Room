# Model v4 Truth Set Player Universe

Created: 2026-05-16

This file defines the broad player universe for Model v4 truth-set fixtures. It
does not rank, score, promote, or tune players. It only identifies which players
must be represented when Phase 2 builds sanity fixtures, receipt expectations,
and source-coverage checks.

Machine-readable file:

- `docs/model_v4/TRUTH_SET_PLAYER_UNIVERSE.csv`

Authoritative context:

- `docs/model_v4/PHASE_1_CHECKPOINT.md`
- `docs/model_v4/LEAGUE_RULES_LOCK.md`
- `docs/model_v4/OFFSEASON_RANKING_SHEET_LOCK.md`
- `docs/model_v4/FOOTBALL_SANITY_BELIEFS.md`
- `docs/model_v4/FEATURE_SOURCE_CONTRACT.md`

## Scope

The universe contains 80 players, the upper end of the requested 60-80 player
range. The goal is to catch structural model mistakes before formula work starts:

- Niners roster and required top-five release mechanics
- elite RB and WR tier sanity
- RB/WR cross-position balance
- young NFL bridge handling
- aging-player dropoff behavior
- 1QB suppression
- no-premium TE suppression
- low-confidence/source-gap behavior
- incoming-rookie draft-room separation

## Group Counts

| Group | Count | Purpose |
| --- | ---: | --- |
| `niners_roster` | 24 | Full locked Niners roster from the March 31 ranking sheet. |
| `elite_rb_control` | 9 | Elite and high-end RB tier checks. |
| `young_bridge_rb_control` | 1 | Young RB with limited NFL evidence control. |
| `aging_rb_control` | 2 | Veteran RB age and workload-fragility controls. |
| `elite_wr_control` | 9 | Elite and high-end WR tier checks. |
| `young_bridge_wr_control` | 3 | Young WR draft-prior plus NFL-evidence controls. |
| `wr_comparison_control` | 4 | Mid/high WR comparisons including JSN vs Tee style checks. |
| `aging_wr_control` | 7 | Age/dropoff and old-WR-vs-young-RB controls. |
| `qb_control` | 6 | 1QB suppression and elite-QB exception checks. |
| `te_control` | 6 | No-premium TE suppression and elite-TE exception checks. |
| `low_confidence_source_gap_control` | 4 | Low-confidence or source-gap behavior checks. |
| `incoming_rookie_draft_room` | 5 | Draft-room lifecycle separation checks. |

## Critical Niners Rows

The locked `Roster's League-Rank Top Five` must appear in every roster-decision
fixture family:

1. De'Von Achane
2. Lamar Jackson
3. Chase Brown
4. Luther Burden
5. Brian Thomas Jr.

Those players are marked `critical` because they define the required top-five
release pool and because several are known model stress cases. Their inclusion
does not imply an expected ranking; it means any Model v4 roster decision must
show receipt-backed reasoning for them.

## Lifecycle Expectations

The CSV uses these expected lifecycle labels:

- `incoming_rookie`
- `year_one_nfl_bridge`
- `year_two_nfl_bridge`
- `year_three_nfl_bridge`
- `established_veteran`

Lifecycle labels are expectations for fixture construction. They are not scoring
inputs by themselves. Phase 2 fixture work should flag mismatches as review
failures, not as manual overrides.

## Source Priority

| Priority | Meaning |
| --- | --- |
| `critical` | Must be included in named fixtures or gate-facing review reports. |
| `high` | Important for position or roster sanity coverage. |
| `medium` | Useful structural control but less central to Niners decisions. |
| `review` | Expected to expose source gaps or draft-room uncertainty. |

## Phase 2A Guardrails

- No formulas were changed.
- No player values were generated.
- No legacy rankings were promoted.
- Incoming rookies are included only for draft-room lifecycle separation.
- League rank remains rule context only.
- Market data remains trade context only.
- Missing route metrics remain an expected source-gap issue.

## Next Step

Phase 2B should convert this universe and `FOOTBALL_SANITY_BELIEFS.md` into
review-only sanity fixtures. Fixture failures should create review findings and
receipt requirements, not hard-coded ranking overrides.
