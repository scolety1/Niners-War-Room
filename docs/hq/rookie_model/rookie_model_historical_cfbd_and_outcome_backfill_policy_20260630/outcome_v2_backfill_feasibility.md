# Outcome V2 Backfill Feasibility

## Verdict

`YELLOW_BACKFILL_FEASIBLE_WITH_SOURCE_POLICY_AND_LABEL_ONLY_PIPELINE`

Backfilling 2000-2011 labels appears technically feasible with `nflreadpy.load_player_stats`,
but it is not safe to build or promote in this lane. The current tracked/shared Outcome V2 rookie
label source starts at `2012` and ends at `2024`. Any 2000-2011
backfill must be a separate label-only pipeline with explicit scoring, identity, and censoring
approval.

## Current Label Coverage By Class

| draft_year | drafted_fantasy_position_count | rookie_year_label_available_count | five_y_label_available_count | missing_label_count | rookie_label_pct |
| --- | --- | --- | --- | --- | --- |
| 2000 | 81 | 0 | 0 | 81 | 0.0% |
| 2001 | 76 | 0 | 0 | 76 | 0.0% |
| 2002 | 95 | 0 | 0 | 95 | 0.0% |
| 2003 | 76 | 0 | 0 | 76 | 0.0% |
| 2004 | 80 | 0 | 0 | 80 | 0.0% |
| 2005 | 77 | 0 | 0 | 77 | 0.0% |
| 2006 | 75 | 0 | 0 | 75 | 0.0% |
| 2007 | 80 | 0 | 0 | 80 | 0.0% |
| 2008 | 87 | 0 | 0 | 87 | 0.0% |
| 2009 | 87 | 0 | 0 | 87 | 0.0% |
| 2010 | 78 | 0 | 0 | 78 | 0.0% |
| 2011 | 82 | 0 | 0 | 82 | 0.0% |
| 2012 | 77 | 62 | 69 | 8 | 80.5% |
| 2013 | 80 | 55 | 69 | 11 | 68.8% |
| 2014 | 77 | 58 | 65 | 12 | 75.3% |
| 2015 | 79 | 59 | 70 | 9 | 74.7% |
| 2016 | 77 | 58 | 64 | 13 | 75.3% |
| 2017 | 83 | 62 | 73 | 10 | 74.7% |
| 2018 | 83 | 61 | 75 | 8 | 73.5% |
| 2019 | 80 | 64 | 70 | 10 | 80.0% |
| 2020 | 78 | 66 | 75 | 3 | 84.6% |
| 2021 | 75 | 68 | 0 | 3 | 90.7% |
| 2022 | 79 | 71 | 0 | 2 | 89.9% |
| 2023 | 80 | 68 | 0 | 6 | 85.0% |
| 2024 | 77 | 66 | 0 | 11 | 85.7% |

## Current Label Coverage By Position

| position | drafted_fantasy_position_count | outcome_v2_label_count | combine_match_count | approved_cfbd_identity_count | outcome_label_pct |
| --- | --- | --- | --- | --- | --- |
| QB | 304 | 123 | 269 | 0 | 40.5% |
| RB | 514 | 246 | 447 | 0 | 47.9% |
| TE | 367 | 167 | 308 | 0 | 45.5% |
| WR | 814 | 383 | 697 | 0 | 47.1% |

## Source Needed For League-Scoring Fantasy Outcomes

The needed source is factual player-season NFL statistics with NWR league scoring fields. The
installed `nflreadpy.load_player_stats(seasons, summary_level="reg")` loader can read 2000, 2011,
and 2012 regular-season rows in this environment. The probed columns include passing, rushing, and
receiving first downs: `True`.

That means nflverse player stats can likely produce candidate label rows for 2000-2011, including
the exact first-down scoring mode, if and only if the future lane validates:

- GSIS/player ID stability for older seasons.
- NWR scoring formula parity with existing Outcome V2 labels.
- Missing player-season interpretation without zero-filling unknowns.
- Position eligibility and positional finish semantics.
- Censoring/window completeness for rookie, 2Y, 3Y, and 5Y horizons.

## Known Blockers

- Current Outcome V2 rookie label artifact has `0/974` labels for 2000-2011 drafted QB/RB/WR/TE.
- Missing season rows must not become misses or zero fantasy points without a source policy.
- Older player IDs and name/team aliases require deterministic joins; PFR/CFB names are not enough.
- UDFA/non-drafted prospects are outside the drafted-player source universe.
- No backfilled labels are approved for model input or app wiring.

## Leakage Safeguards

- Labels are evaluation targets only.
- Outcome fields cannot be joined into pre-draft or post-draft feature tables.
- Any derived hit/miss must be timestamped to the evaluation horizon and kept out of prediction
  features.
- Incomplete windows must remain `INCOMPLETE_WINDOW_NOT_FAILURE`.

## Recommended Label-Only Pipeline Design

1. Build a separate shared-data candidate artifact from nflverse player stats for 2000-2011.
2. Recompute NWR league scoring from source stat fields, including first downs.
3. Join to drafted QB/RB/WR/TE rows by GSIS/player stats ID first, PFR only as a review queue.
4. Produce rookie, 2Y, 3Y, and 5Y labels with explicit censoring.
5. Compare 2012 overlap labels against current Outcome V2 as a parity test before accepting
   2000-2011 labels.
6. Keep all outputs review-only until a separate approval gate.

This lane did not build the backfill.
