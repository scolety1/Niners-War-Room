# Rookie Historical Feature-Family Availability Audit - 2026-06-15

## 1. Executive Verdict

This pass audited local source-safe historical feature-family availability before another tuning pass.

Verdicts:

- Historical feature availability: YELLOW
- Leakage safety: GREEN
- Join feasibility: YELLOW
- Immediate backfill readiness: YELLOW
- Tuning readiness after audit: RED for immediate tuning; YELLOW after feature backfill/QA

The rookie lane has useful local feature sources, but the historical pool is uneven. Current 2026 and 2021-2023 have meaningful feature coverage through RotoWire CFB stats/targets/team context, workout/combine data, and existing evidence matrices. The 2010-2019 expanded historical pool still lacks local college production, target earning, injury, and role/archetype sources. Another tuning run should wait until the safe feature backfill is built and validated.

No tuning was run. No v2 board was created. No app, production, Outcome, veteran, probability, band, hidden sort key, or promoted artifact work occurred.

## 2. Local Source Inventory

Source inventory rows exported: 12.

Best local candidates found:

| Source | Rows | Years | Classification | Recommended Action |
|---|---:|---|---|---|
| `nflverse_draft_picks` | 12,927 | 1980-2026 | allowed feature, with career columns quarantined | use now |
| `rotowire_cfb_stats_all` | 50,198 | 2020-2025 | allowed feature | backfill candidate |
| `rotowire_cfb_targets_all` | 12,979 | 2020-2025 | allowed feature, rank column quarantined | backfill candidate |
| `rotowire_cfb_advanced_team_stats_all` | 825 | 2020-2025 | allowed feature | backfill candidate |
| `combine_skill_positions_all` | 5,094 | 2006-2026 | allowed feature, grades/projections quarantined | backfill candidate |
| `rotowire_workout_stats` | 2,097 | 1969-2026 | allowed feature | backfill candidate |
| `rotowire_cfb_injury_report_2026` | 326 | 2026 | allowed feature | backfill candidate |
| `historical_rookie_backtest_feature_matrix` | 395 | 2021-2025 | allowed feature matrix | backfill candidate |
| `admitted_prospect_current_feature_matrix` | 211 | 2026 | allowed feature matrix | backfill candidate |

Display-only / label-only sources:

- `rotowire_rookie_rankings_2026`: display-only; rank/market-like context is not private score.
- `draft_ranking_model_v1`: current manual board output; not a historical feature source.
- `expanded_historical_labels_v2`: evaluation labels only.

## 3. Column Safety

Column audit rows exported: 304.

Safety rules applied:

- Draft round/pick are allowed features.
- Age at draft is an allowed feature if source-safe.
- Player names, aliases, IDs, school, NFL team, and draft year are identity/display/grouping/QA only.
- Draft-source career/future columns are blocked, including `w_av`, `car_av`, `dr_av`, `allpro`, `probowls`, `seasons_started`, future NFL stat totals, and games.
- RotoWire CFB `rank` is blocked/display-only; raw targets, receptions, yards, TDs, team target percent, and team context fields are allowed if time-safe.
- Combine/workout raw measurements are allowed, but prospect grades, projections, and comparisons are blocked/display-only.
- Outcome labels are evaluation-only.

Leakage safety verdict: GREEN because unsafe columns are identified and quarantined before backfill.

## 4. Join Feasibility

Join feasibility rows exported: 12.

Key results:

| Source | Join Method | Attempted | Joined | Confidence | Repair Needed |
|---|---|---:|---:|---|---|
| `nflverse_draft_picks` | draft year + pick + position | 1,099 | 1,078 | high | no |
| `rotowire_cfb_stats_all` | normalized name + position + final college season | 1,310 | 416 | low | yes |
| `rotowire_cfb_targets_all` | normalized name + position + final college season | 1,310 | 350 | low | yes |
| `combine_skill_positions_all` | normalized name + position + draft year | 1,310 | 1,155 | medium | yes |
| `rotowire_workout_stats` | normalized name + position + draft year | 1,310 | 995 | medium | yes |
| `historical_rookie_backtest_feature_matrix` | historical prospect key | 235 | 235 | high | no |
| `admitted_prospect_current_feature_matrix` | current matrix | 211 | 211 | high | no |

Interpretation:

- CFB stats/targets are valuable but cover 2020-2025, so they mostly help 2021-2023 historical validation plus 2026 current prospects. They do not solve 2010-2019.
- Combine/workout sources have broad coverage but need name/position/year deduplication and source/license acceptance before private scoring use.
- Existing historical/current feature matrices are already joined, but only cover 2021-2025 historical and 2026 current.

## 5. Feature-Family Matrix

Feature families available now or with repair:

- Draft capital: available now for 2010-2023 and 2026.
- Age at draft: available now historically through draft source; DOB/early-declare still missing.
- College production: available with join repair for 2021-2023 and 2026.
- College target earning / receiving role: available with join repair for 2021-2023 and 2026; highest-value WR feature found locally.
- Team context / market-share denominators: available with join repair for 2021-2023 and 2026.
- Combine/athletic testing: available with join repair for 2010-2023 and 2026.
- RotoWire workout testing: available with join repair for 2016-2023 and 2026.
- Current injury flags: available for 2026 only.

Not found locally:

- 2010-2019 college production and target/share data.
- 2010-2023 pre-draft injury history.
- Historical rookie ADP/market overlay.
- Route/YPRR/advanced charting.
- Full early-declare/DOB/class file.
- Historical time-safe landing spot / opportunity context.

## 6. Best Available Feature Families

Best for immediate safe backfill:

1. Draft round/pick and age from `nflverse_draft_picks`, with career columns quarantined.
2. 2021-2023 plus 2026 CFB production from `rotowire_cfb_stats_all`.
3. 2021-2023 plus 2026 target earning from `rotowire_cfb_targets_all`.
4. Team context denominators from `rotowire_cfb_advanced_team_stats_all`.
5. Athletic testing from `combine_skill_positions_all` and `rotowire_workout_stats`, after duplicate/source-license review.
6. 2026 current injury flags from `rotowire_cfb_injury_report_2026`.

Best for WR star capture:

- Target earning / target share / receiving production is the best local feature family found, but only for 2021-2023 and 2026.
- Route/YPRR/advanced charting was not found and would likely be the biggest missing WR star-capture upgrade.

Best for bust avoidance:

- Pre-draft injury flags and warning evidence would likely help most, but historical 2010-2023 injury files were not found.
- Combine/workout plus role/production context can help, but should not be treated as a substitute for injury/history warnings.

## 7. What Tim Should Provide

Priority 1:

- `college_player_season_stats_2010_2026.csv`: player-season college production for QB/RB/WR/TE, including games, passing, rushing, receiving, targets if available.
- `historical_targets_market_share_2010_2026.csv`: targets, receptions, receiving yards, receiving TDs, team targets or target share.
- `rookie_age_early_declare_2010_2026.csv`: DOB or age at draft, college class, early declare flag.
- `pre_draft_injury_flags_2010_2026.csv`: injury type, date/season, severity, known-pre-draft flag.

Priority 2:

- Clean licensed combine/athletic testing file for 2010-2026.
- Historical rookie ADP as display-only value overlay.

Priority 3:

- Structured factual scouting notes with `known_pre_draft=yes/no`, avoiding ranks, projections, comps, and hindsight blurbs as scoring inputs.

Paid/proprietary data is okay only if Tim already has the right to use it locally.

## 8. Recommended Backfill Plan

1. Backfill draft age and draft capital from `nflverse_draft_picks`.
2. Backfill 2021-2023 plus 2026 CFB production/targets/team context from local RotoWire files.
3. Backfill combine/workout athletic testing after source/license and duplicate-key QA.
4. Backfill 2026 current injury flags as current-only warning context.
5. Pause tuning until the feature backfill matrix is validated.

Immediate backfill readiness: YELLOW. There is enough to build a safe backfill candidate, but not enough for a full 2010-2023 richer tuning run.

## 9. Anti-Cheat / Leakage Audit

PASS - Player names, aliases, IDs, school, NFL team, and draft year are not direct scoring/tuning features.

PASS - Outcome labels are evaluation-only and not feature construction.

PASS - ADP/market/public rankings/projections/trade calculators remain display-only or quarantined.

PASS - Draft file career/future columns remain quarantined.

PASS - Future NFL stats are labels only, never features.

PASS - No player-specific boosts or penalties.

PASS - No team/school/year-specific boosts or penalties.

PASS - No v2 board or tuning created in this audit.

## 10. Tuning Decision

Do not run another tuning pass yet.

The next rookie-only task should be a tracked historical feature backfill proposal/build, not tuning. The first safe build should create a local-only feature backfill candidate for:

- draft age + draft capital;
- 2021-2023 and 2026 CFB production;
- 2021-2023 and 2026 target earning;
- team context denominators;
- combine/workout athletic profile with duplicate/source-license warnings;
- 2026 current injury flags as warnings only.

The backfill should explicitly mark 2010-2019 college production/target gaps and keep ADP/market display-only.
