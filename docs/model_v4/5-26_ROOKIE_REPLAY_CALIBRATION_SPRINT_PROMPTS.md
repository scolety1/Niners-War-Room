# 5-26 Rookie Replay Calibration Sprint Prompts

## Goal

Use the audit consensus to repair the rookie replay judge and prepare safe calibration work without tuning formulas blindly.

The next sprint should answer:

> Is the rookie model genuinely finding signal, or is it mostly being seduced by college production/team share?

## Working Verdict

Do not bail yet. Do not tune formulas yet.

The audits and deep research agree:

- The model is likely viable.
- The backtest/replay infrastructure needed repair first.
- NFL Draft capital should be the base-rate anchor.
- College production/team share should modify the profile, not override premium capital by default.
- Day 3 outliers should remain visible as tail bets, not safe first-round alternatives.
- 2021-2023 are the mature evaluation years.
- 2024 is partial.
- 2025 is rookie-year-only shadow context.

---

# Stage 1: Mature Replay Miss-Pattern Report

## Prompt

Model v4.3.6 / Mature Rookie Replay Miss-Pattern Report

Goal:
Analyze mature 2021-2023 historical rookie replay rows to identify repeated model miss patterns before changing formulas.

Current state:
- v4.3.5 added Fantasy-Relevant Replay Pool, broad/strict/difference-maker labels, and outcome maturity.
- Outcome labels are display-only.
- Formula weights must not change yet.

Tasks:
1. Load:
   - local_exports/model_v4/historical_rookie_tuning/latest/historical_rookie_tuning_board_rows.csv
   - local_exports/model_v4/historical_rookie_tuning/latest/historical_rookie_tuning_component_rows.csv
   - local_exports/model_v4/historical_rookie_tuning/latest/historical_rookie_tuning_summary_rows.csv
2. Filter primary analysis to:
   - Draft Year in 2021, 2022, 2023
   - Fantasy-Relevant Replay Pool == True
   - Outcome Maturity == three_year_window_available
3. Produce miss-pattern groups:
   - high-ranked misses
   - low-ranked strict-starter hits
   - low-ranked difference-makers
   - first-round WR underranks
   - late-capital production false positives
   - day-three RB hits worth preserving
   - TE overpromotion/underpromotion
   - QB overpromotion/underpromotion
   - low-evidence overpromotion
4. For each row include:
   - player
   - draft year
   - position
   - rank
   - draft round / pick
   - final score
   - production score
   - College Team Share
   - NFL Draft Pick Signal
   - athletic score
   - confidence cap
   - outcome category
   - strict starter hit
   - difference maker
   - likely miss cause
   - recommended action type: formula_candidate / data_candidate / label_candidate / acceptable_edge
5. Produce:
   - local_exports/model_v4/historical_rookie_tuning/latest/mature_miss_pattern_rows.csv
   - local_exports/model_v4/historical_rookie_tuning/latest/mature_miss_pattern_summary.csv
   - docs/model_v4/MODEL_V4_3_6_MATURE_REPLAY_MISS_PATTERN_REPORT.md
6. Do not tune formulas.
7. Do not change active rankings, My Team, War Board, readiness gates, or app promotion.
8. Run focused tests and Ruff.

Constraints:
No formula tuning.
No consensus-copying.
No market/ADP/projection leakage.
2024/2025 may be mentioned only as immature shadow context.

---

# Stage 2: Baseline Comparison

## Prompt

Model v4.3.6 / Rookie Replay Baseline Comparison

Goal:
Compare the current rookie model against simple baselines before deciding whether formula tuning is justified.

Tasks:
1. Use mature 2021-2023 Fantasy-Relevant Replay Pool rows only for primary evaluation.
2. Build baseline scores:
   - draft_capital_only
   - production_team_share_only
   - simple_hybrid_capital_plus_production
   - current_model_score
3. Evaluate each baseline by:
   - Top 5 broad hit rate
   - Top 10 broad hit rate
   - Top 20 broad hit rate
   - Top 5 strict starter hit rate
   - Top 10 strict starter hit rate
   - Top 20 strict starter hit rate
   - difference-maker capture rate
   - by-position capture
4. Produce:
   - rookie_replay_baseline_comparison_rows.csv
   - rookie_replay_baseline_summary.csv
   - rookie_replay_by_position_baseline_summary.csv
   - docs/model_v4/MODEL_V4_3_6_ROOKIE_REPLAY_BASELINE_COMPARISON.md
5. State whether current model is:
   - better than draft capital only
   - worse than draft capital only
   - only better in certain positions
   - inconclusive
6. Do not tune formulas yet.
7. Run focused tests and Ruff.

Constraints:
No formula tuning.
No app promotion.
No active ranking changes.
Market-only baseline can be documented as future work, but market data must not drive private value.

---

# Stage 3: Calibration Candidate Plan

## Prompt

Model v4.3.6 / Rookie Calibration Candidate Plan

Goal:
Convert miss-pattern and baseline evidence into safe candidate formula tests without applying them yet.

Tasks:
1. Read:
   - mature_miss_pattern_summary.csv
   - rookie_replay_baseline_summary.csv
   - docs/model_v4/MODEL_V4_3_5_DEEP_RESEARCH_ROOKIE_CALIBRATION_INTAKE.md
   - docs/model_v4/MODEL_V4_3_5_SECOND_ROOKIE_REPLAY_AUDIT_INTAKE.md
   - docs/model_v4/MODEL_V4_3_5_THIRD_ROOKIE_REPLAY_AUDIT_INTAKE.md
2. Define candidate formula tests:
   - stronger Day 3 WR skepticism
   - first-round WR floor refinement
   - RB receiving/workhorse modifier
   - no-premium TE cap refinement
   - 1QB QB cap check
   - stricter low-evidence confidence cap
3. For each candidate include:
   - reason
   - evidence rows
   - expected impact
   - risks
   - players likely affected
   - pass/fail criteria
4. Produce:
   - rookie_calibration_candidate_tests.csv
   - docs/model_v4/MODEL_V4_3_6_ROOKIE_CALIBRATION_CANDIDATE_PLAN.md
5. Do not implement candidate tests yet unless explicitly approved after review.

Constraints:
No formula tuning.
No consensus-copying.
Preserve useful model weirdness.

---

# Stage 4: Optional Shadow Formula Experiment

## Prompt

Model v4.3.7 / Rookie Shadow Formula Experiment

Goal:
Run controlled shadow formula variants against mature 2021-2023 replay rows without replacing the current model.

Only run this after Stage 1-3 outputs are reviewed.

Tasks:
1. Implement shadow-only formula variants:
   - current_model
   - capital_anchor_variant
   - confidence_cap_variant
   - day_three_wr_skepticism_variant
   - te_no_premium_cap_variant
   - combined_conservative_variant
2. Evaluate each against:
   - mature 2021-2023 fantasy-relevant replay pool
   - 2024 partial shadow
   - 2025 rookie-year shadow
3. Produce:
   - rookie_shadow_formula_variant_rows.csv
   - rookie_shadow_formula_variant_summary.csv
   - rookie_shadow_formula_player_movement.csv
   - docs/model_v4/MODEL_V4_3_7_ROOKIE_SHADOW_FORMULA_EXPERIMENT.md
4. Do not promote any variant.
5. Do not change current Draft Room rankings.

Constraints:
Shadow-only.
No active app promotion.
No My Team or War Board changes.
No readiness unlock.

---

# 8-Hour Solo Work Plan

Best use of unattended coding time:

1. Complete Stage 1.
2. Complete Stage 2.
3. Complete Stage 3.
4. Package a review packet.
5. Stop before Stage 4 unless explicitly approved.

Expected end state after 8 hours:

- We should know whether the model beats draft-capital-only in mature replay rows.
- We should know which miss patterns are real versus noise.
- We should have a safe candidate plan for tuning.
- We should not have changed active rankings.

---

# 2-Hour Human Refinement Plan

When the user returns:

1. Review miss-pattern summary first.
2. Review baseline comparison second.
3. Decide whether current model has enough edge to keep.
4. Choose which candidate formula tests are allowed.
5. Only then run Stage 4 shadow experiments.

Human review questions:

- Are we comfortable treating Day 3 WR production spikes as tail bets?
- Is Carnell Tate-style Round 1 capital getting enough floor?
- Are RB receiving/workhorse profiles being preserved?
- Are QBs and TEs boring enough for this league format?
- Does the model beat draft capital-only where it should?

---

# End Goal For This Sprint

The end goal is not final rookie rankings.

The end goal is a confident decision:

- keep current formula mostly intact,
- run targeted shadow formula tests,
- or pause rookie model use until more evidence is admitted.
