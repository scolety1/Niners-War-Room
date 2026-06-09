# Legacy-vs-Current Sentinel Expansion

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: expand the Keenan Allen and Darius Slayton legacy leak sentinel into a
larger comparison-only list of active-pack veteran-engine scores that could
mislead if they were ever surfaced as primary Player Board Model Value.

This report does not change source routing, formulas, active data packs,
generated outputs, rankings, app promotion, or UI state.

## Source Pair

Legacy comparison source:

- Path: `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks/model_outputs.csv`
- Legacy source column: `private_score`
- Legacy source model version: `veteran_lve_stats_first_v1_0_0`
- Required lineage treatment: `legacy_active_pack`
- Allowed use: comparison-only legacy context
- Blocked use: primary review score, default sort, review label, summary tile

Current primary source:

- Path:
  `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv`
- Current primary column: `checkpoint_review_score`
- Required lineage treatment: `review_v4_current_player`
- Allowed use: `review_only_current_value_checkpoint`
- Blocked use: `do_not_use_as_final_ranking_or_roster_recommendation`

## Selection Rule

Rows S01-S23 are the largest matched active-pack-minus-current score spreads
among players present in both sources. Rows S24-S25 are mandatory known
sentinels from the repair handoff:

- Keenan Allen legacy active-pack `private_score` = `82.4` must remain
  comparison-only.
- Darius Slayton legacy active-pack `private_score` = `78.88` must remain
  comparison-only and fail closed because no current Model v4 checkpoint row is
  present.

## Sentinel Rows

| ID | Player | Pos | Active-Pack Row | Legacy Active-Pack Score | Current CSV Rank | Current Primary Score | Legacy-Current Spread | Current Status | Quarantine Reason |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| S01 | Jayden Daniels | QB | 29 | 95.70 | 78 | 8.9902 | 86.7098 | high_confidence_metadata | 1QB cap/warning |
| S02 | Sam LaPorta | TE | 41 | 93.45 | 71 | 24.2632 | 69.1868 | usable_with_confidence_cap | no-premium TE cap/warning; source gap warning |
| S03 | T.J. Hockenson | TE | 154 | 77.00 | 76 | 13.7788 | 63.2212 | usable_with_confidence_cap | no-premium TE cap/warning; source gap warning |
| S04 | Malik Nabers | WR | 9 | 93.26 | 46 | 30.4824 | 62.7776 | usable_with_confidence_cap | source gap warning |
| S05 | Garrett Wilson | WR | 8 | 93.82 | 39 | 31.5335 | 62.2865 | usable_with_confidence_cap | source gap warning |
| S06 | Joe Burrow | QB | 184 | 73.85 | 77 | 11.9641 | 61.8859 | usable_with_confidence_cap | 1QB cap/warning; source gap warning |
| S07 | Brandon Aiyuk | WR | 57 | 87.03 | 53 | 25.4061 | 61.6239 | usable_with_confidence_cap | source gap warning |
| S08 | Brock Purdy | QB | 138 | 81.86 | 75 | 21.3779 | 60.4821 | usable_with_confidence_cap | 1QB cap/warning; source gap warning |
| S09 | George Kittle | TE | 62 | 90.21 | 70 | 32.0994 | 58.1106 | usable_with_confidence_cap | no-premium TE cap/warning; source gap warning |
| S10 | Jalen Coker | WR | 81 | 80.01 | 54 | 22.2108 | 57.7992 | usable_with_confidence_cap | source gap warning |
| S11 | Mike Evans | WR | 60 | 85.58 | 40 | 28.4015 | 57.1785 | capped_review_required | identity/team warning; source gap warning |
| S12 | Jakobi Meyers | WR | 40 | 87.97 | 38 | 31.5686 | 56.4014 | capped_review_required | identity/team warning; source gap warning |
| S13 | Tank Dell | WR | 74 | 83.62 | 43 | 27.2878 | 56.3322 | capped_review_required | source gap warning |
| S14 | Ricky Pearsall | WR | 71 | 82.14 | 51 | 25.9408 | 56.1992 | capped_review_required | source gap warning |
| S15 | Lamar Jackson | QB | 24 | 96.24 | 68 | 40.3535 | 55.8865 | high_confidence_metadata | 1QB cap/warning |
| S16 | Jerry Jeudy | WR | 55 | 85.64 | 41 | 31.1199 | 54.5201 | usable_with_confidence_cap | source gap warning |
| S17 | Xavier Worthy | WR | 68 | 82.45 | 45 | 27.9883 | 54.4617 | usable_with_confidence_cap | source gap warning |
| S18 | Romeo Doubs | WR | 54 | 85.72 | 35 | 31.3334 | 54.3866 | capped_review_required | identity/team warning; source gap warning |
| S19 | Cooper Kupp | WR | 93 | 78.12 | 47 | 26.4622 | 51.6578 | capped_review_required | identity/team warning; source gap warning |
| S20 | Mark Andrews | TE | 172 | 74.60 | 73 | 23.1327 | 51.4673 | usable_with_confidence_cap | no-premium TE cap/warning; source gap warning |
| S21 | Jayden Higgins | WR | 100 | 75.65 | 50 | 25.2852 | 50.3648 | usable_with_confidence_cap | source gap warning |
| S22 | Brenton Strange | TE | 180 | 73.06 | 72 | 23.1507 | 49.9093 | usable_with_confidence_cap | no-premium TE cap/warning; source gap warning |
| S23 | Quentin Johnston | WR | 58 | 85.13 | 33 | 35.5788 | 49.5512 | usable_with_confidence_cap | source gap warning |
| S24 | Keenan Allen | WR | 78 | 82.40 | 30 | 41.6097 | 40.7903 | capped_review_required | identity/team warning; source gap warning |
| S25 | Darius Slayton | WR | 88 | 78.88 | missing | blank | n/a | manual_required_no_model_v4_current_player | missing current checkpoint row; source gap warning |

## Required Interpretation

- The `Legacy Active-Pack Score` column is not a primary value.
- The `Legacy Active-Pack Score` column is not a ranking value.
- The `Legacy Active-Pack Score` column is not a recommendation signal.
- `veteran_lve_stats_first_v1_0_0` must be treated as `legacy_active_pack`.
- Missing current checkpoint rows must fail closed with manual review required,
  not fall back to active-pack `private_score`.
- Large spreads are evidence for human audit and later formula-candidate
  discussion only. They are not proof that either source is football-correct.

## Existing Sentinel Tests To Preserve

The existing Player Board sentinel tests should continue to prove:

- Keenan Allen current primary score is `41.6097`, sourced from
  `checkpoint_review_score`.
- Keenan Allen legacy active-pack score is `82.4`, comparison-only.
- Darius Slayton legacy active-pack score is `78.88`, comparison-only.
- Darius Slayton has no primary review score when no Model v4 current-player row
  exists.

## Non-Goals

- Do not tune 1QB caps, no-premium TE caps, age curves, replacement formulas, or
  any other model formula from this report.
- Do not change source-routing behavior from this report.
- Do not import market, ADP, rankings, projections, consensus, startup, or
  trade-calculator data into private value.
- Do not convert these rows into trade, cut, keep, draft, buy, sell, defer, or
  target recommendations.
