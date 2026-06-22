# NWR Historical Cross-Asset Tuning - 2026-06-22

## Final Verdict: YELLOW

This pass produced a safer **review-only tuned cross-asset candidate layer**, but it did **not** find a clean historical dropped-veteran-versus-rookie panel. The output is useful for tomorrow as a human-review aid and for a future app overlay, but it should not replace the frozen Final Draft Board V1, Dynasty Rank, latest_candidate, or latest_approved.

## What Historical Data Was Available

The strongest row-level historical data found was the internal rookie replay fixture covering the 2022-2024 rookie classes: `C:\NWR\Niners-War-Room\sample_data\historical_rookie_replay\pre_draft_prospect_inputs.csv` plus `C:\NWR\Niners-War-Room\sample_data\historical_rookie_replay\post_draft_outcomes.csv`. It contains 60 rookie/prospect rows with future Year 1, Year 2, Year 3, best LVE PPG, Top-24 seasons, and hit labels.

Key supporting reports were also found:

- `docs/model_v4/MODEL_V4_3_6_ROOKIE_REPLAY_BASELINE_COMPARISON.md`: reports 128 mature fantasy-relevant replay rows and shows draft-capital-only beat the then-current rookie model in aggregate Top-20 broad and strict starter hit rates.
- `docs/model_v4/MODEL_V4_3_6_MATURE_REPLAY_MISS_PATTERN_REPORT.md`: reports 32 strict starter and 22 difference-maker outcomes, with patterns including first-round WR underranks, QB overpromotion/underpromotion, high-ranked misses, and low-evidence overpromotion.
- `docs/model_v4/VETERAN_AGE_WINDOW_AUDIT_20260605.md`: supports age-window warnings and older-veteran caution.
- `docs/model_v4/QB_1QB_DISCIPLINE_REPORT_20260605.md`: supports discounting non-elite QBs in 10-team 1QB.

## What Could Not Be Validated

No approved/internal historical artifact was found that cleanly joins all of these at a historical draft date:

- a rookie board,
- a dropped/available veteran pool,
- league roster/keeper/drop state,
- comparable cross-asset pre-draft values,
- and future fantasy outcomes.

Because of that, this run used historical rookie replay plus current internal dynasty/veteran evidence to tune a candidate formula. It is **evidence-informed**, not a fully backtested production model.

The companion proxy dataset `historical_dropped_veteran_proxy_cohorts.csv` was also created for sensitivity testing. It contains 96 rows: 12 current verified drop-shape rows and 84 proxy/synthetic veteran benchmark rows. These rows must be used only as low-weight stress tests, not as verified historical training labels.

## Formula Before vs After

The emergency app formula correctly identified that rookie scores and dropped-veteran values came from different bases, but it still left some young established veterans vulnerable to being compared against raw prospect-scale scores. This tuned layer changes the posture:

- increases the weight of internal full-dynasty anchors for established veterans,
- maps rookie rank/tier to a 0-100 percentile-style crosswalk instead of raw score comparison,
- strengthens draft-capital/role evidence as rookie support,
- increases uncertainty penalties for needs_data/manual-review/UNKNOWN/team-role gaps,
- discounts QBs more in 10-team 1QB,
- treats unsupported Outcome as confidence uncertainty, not a value zero,
- keeps ADP at zero internal weight and display-only.

Full component weights are in `tuned_cross_asset_formula_weights.csv`.

## Historical Evidence for Rookie vs Veteran Comparison

From the 60 rookie replay rows, 24 rows had hit-like labels and 9 rows had at least two Top-24 seasons by the available proxy. The evidence supports these practical rules:

- Strong RB/WR rookie profiles can beat low-evidence veterans when draft capital and role evidence are clear.
- A top prospect should not automatically beat a young established dynasty-scored WR unless the prospect has elite draft/role evidence.
- Rookie QBs should be discounted in 10-team 1QB unless the path is clearly elite or their replacement gap is large.
- TE outcomes are slow and volatile; avoid both burying and over-promoting TEs from one signal.
- Manual-review and needs_data flags should lower confidence more than the emergency layer did.

## Position-Specific Findings

### QB in 1QB

QB is de-emphasized. Young QB upside can matter, but mid/non-elite QBs are poor cross-asset bets in a 10-team 1QB draft unless the board has already exhausted RB/WR/TE value.

### RB

RB has near-term scarcity and first-down scoring relevance, but age/role volatility is sharp. Strong rookie RBs remain attractive; older or uncertain veterans require role clarity.

### WR

Young established WRs with internal dynasty anchors should beat many prospects. This is the most important correction versus the misleading raw rookie/prospect score display.

### TE

TE should remain in the review set when internally supported, but outcomes are volatile and should not dominate best-available decisions unless confidence is high.

## Age Curve Findings

- RB: strongest age/role penalty once the player is older or the role is uncertain.
- WR: gentler curve; young established WRs get more benefit from dynasty anchor stability.
- TE: less age-sensitive than RB, but older role uncertainty still matters.
- QB: age is secondary to 1QB replacement economics and elite-vs-replaceable separation.

## Uncertainty / Manual Review Penalty Findings

The tuned candidate layer increases penalties for manual-review, needs_data, UNKNOWN team/role, caveat-heavy rows, and missing applicable Outcome. Missing Outcome remains `Not enough information`, not a zero.

## Current 2026 Draft-Pool Implications

The biggest practical change is that young established veterans should no longer be buried beneath prospects because the prospect score looks like a 90+ while the veteran score looks like a 50-60. The tuned layer preserves prospect upside but elevates comparable veteran anchors.

| player | pos | final_board_rank | emergency_candidate_rank | tuned_cross_asset_rank | tuned_cross_asset_value | direction_vs_frozen_rank | direction_vs_emergency_candidate_rank | confidence_band | main_reason_to_draft | main_reason_to_pass | human_review_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Jeremiyah Love | RB | 1 | 1 | 1 | 63.75 | similar to frozen | similar to emergency | Medium-low | Rookie/prospect upside remains visible after rank/tier crosswalk; consider if comfortable with uncertainty. | Confidence is limited by needs_data/manual-review/source caveats; do not treat score as final truth. | confidence_review|outcome_gap |
| Makai Lemon | WR | 2 | 4 | 2 | 59.1 | similar to frozen | similar to emergency | Medium-low | Rookie/prospect upside remains visible after rank/tier crosswalk; consider if comfortable with uncertainty. | Confidence is limited by needs_data/manual-review/source caveats; do not treat score as final truth. | confidence_review|outcome_gap |
| Carnell Tate | WR | 3 | 7 | 3 | 56.95 | similar to frozen | slightly changed vs emergency | Medium-low | Rookie/prospect upside remains visible after rank/tier crosswalk; consider if comfortable with uncertainty. | Confidence is limited by needs_data/manual-review/source caveats; do not treat score as final truth. | confidence_review|outcome_gap |
| KC Concepcion | WR | 4 | 8 | 4 | 54.8 | similar to frozen | slightly changed vs emergency | Medium-low | Rookie/prospect upside remains visible after rank/tier crosswalk; consider if comfortable with uncertainty. | Confidence is limited by needs_data/manual-review/source caveats; do not treat score as final truth. | confidence_review|outcome_gap |
| Jadarian Price | RB | 5 | 9 | 6 | 52.65 | similar to frozen | slightly changed vs emergency | Medium-low | Rookie/prospect upside remains visible after rank/tier crosswalk; consider if comfortable with uncertainty. | Confidence is limited by needs_data/manual-review/source caveats; do not treat score as final truth. | confidence_review|outcome_gap |
| Zay Flowers | WR | 31 | 2 | 10 | 46.47 | up meaningfully vs frozen | down vs emergency | Medium | Established WR anchor from internal dynasty score; safer comparison base than raw rookie/prospect score. | Passing is reasonable if roster construction or near-term role risk matters more than long-term upside. | outcome_gap |
| Chris Olave | WR | 34 | 3 | 11 | 44.46 | up meaningfully vs frozen | down vs emergency | Medium | Established WR anchor from internal dynasty score; safer comparison base than raw rookie/prospect score. | Passing is reasonable if roster construction or near-term role risk matters more than long-term upside. | outcome_gap |
| Jameson Williams | WR | 42 | 5 | 13 | 41.8 | up meaningfully vs frozen | down vs emergency | Medium | Established WR anchor from internal dynasty score; safer comparison base than raw rookie/prospect score. | Passing is reasonable if roster construction or near-term role risk matters more than long-term upside. | outcome_gap |
| Drake Maye | QB | 40 | 11 | 20 | 29.08 | up meaningfully vs frozen | down vs emergency | Low | Established QB anchor from internal dynasty score; safer comparison base than raw rookie/prospect score. | Confidence is limited by needs_data/manual-review/source caveats; do not treat score as final truth. | confidence_review|manual_review|outcome_gap |
| Jaylen Warren | RB | 54 | 19 | 24 | 22.06 | up meaningfully vs frozen | down vs emergency | Medium | Established RB anchor from internal dynasty score; safer comparison base than raw rookie/prospect score. | Passing is reasonable if roster construction or near-term role risk matters more than long-term upside. | outcome_gap |
| Rashee Rice | WR | 62 | 20 | 26 | 17.84 | up meaningfully vs frozen | down vs emergency | Medium | Established WR anchor from internal dynasty score; safer comparison base than raw rookie/prospect score. | Passing is reasonable if roster construction or near-term role risk matters more than long-term upside. | outcome_gap |
| Brian Thomas | WR | 63 | 22 | 28 | 16.99 | up meaningfully vs frozen | down vs emergency | Medium | Established WR anchor from internal dynasty score; safer comparison base than raw rookie/prospect score. | Passing is reasonable if roster construction or near-term role risk matters more than long-term upside. | outcome_gap |
| Dak Prescott | QB | 60 | 57 | 32 | 11.44 | up meaningfully vs frozen | up vs emergency | Low | Established QB anchor from internal dynasty score; safer comparison base than raw rookie/prospect score. | Confidence is limited by needs_data/manual-review/source caveats; do not treat score as final truth. | confidence_review|manual_review|outcome_gap |
| Keenan Allen | WR | 64 | 65 | 64 | 0.0 | similar to frozen | similar to emergency | Low | Established WR anchor from internal dynasty score; safer comparison base than raw rookie/prospect score. | Confidence is limited by needs_data/manual-review/source caveats; do not treat score as final truth. | confidence_review|manual_review|team_or_role_review|outcome_gap |
| Brock Purdy | QB | 65 | 63 | 65 | 0.0 | similar to frozen | similar to emergency | Medium | Established QB anchor from internal dynasty score; safer comparison base than raw rookie/prospect score. | 10-team 1QB format reduces cross-asset urgency unless the QB is clearly elite. | outcome_gap |
| Darren Waller | TE | 66 | 66 | 66 | 0.0 | similar to frozen | similar to emergency | Low | Established TE anchor from internal dynasty score; safer comparison base than raw rookie/prospect score. | Confidence is limited by needs_data/manual-review/source caveats; do not treat score as final truth. | confidence_review|manual_review|team_or_role_review|outcome_gap |

## Pick-Window Recommendations

The detailed pick-window table is in `pick_window_tuned_recommendations.csv`. Summary:

- **1.03 / 1.04:** Prioritize Jeremiyah Love if the human room still buys the prospect profile, but Zay Flowers and Chris Olave are now legitimate cross-asset comparisons rather than buried veteran afterthoughts.
- **1.09:** Jameson Williams, Makai Lemon, Carnell Tate, KC Concepcion, Jadarian Price, and Drake Maye are the main review pocket depending on roster need and risk appetite.
- **2.04 / 2.08:** Treat remaining young WR/RB values as preferable to uncertain older/low-confidence veterans; use the human-review flags aggressively.

ADP/range context remains display-only and should not override tuned candidate rank or frozen rank.

## Players Most Likely Over-Ranked Before Tuning

- Mid-tier rookies/prospects whose raw prospect score appeared directly comparable to veteran values.
- Uncertain/needs_data rookies without enough role evidence.
- QBs in 1QB if their upside was treated like a premium cross-asset need.

## Players Most Likely Under-Ranked Before Tuning

- Zay Flowers
- Chris Olave
- Jameson Williams
- Drake Maye as a watch item, though still QB-discounted
- Other young established veterans with full dynasty score anchors but low frozen-board treatment

## Should the Emergency App Formula Be Updated?

**Yes, but only as a review-only overlay.** The app should keep Final Board Rank visible and should label the tuned layer as candidate/review-only. The tuned layer is safer than the emergency layer for rookie-veteran comparison because it avoids raw score comparability and strengthens young veteran anchors.

## Safe App Integration Recommendation

If Master approves a follow-up app patch:

1. Load `tuned_candidate_app_overlay.csv` as a review-only overlay.
2. Add `Tuned Candidate Best Available` as an optional sort/view in Live Draft Room.
3. Keep Final Board Rank adjacent to Tuned Candidate Rank.
4. Keep ADP display-only and Outcome display-only.
5. Do not mutate frozen board, Dynasty Rank, latest_candidate, latest_approved, or pinned snapshot.

## Output Files

- `historical_data_inventory.csv`
- `historical_rookie_veteran_matchups.csv`
- `tuned_cross_asset_formula_weights.csv`
- `current_pool_tuned_cross_asset_review.csv`
- `pick_window_tuned_recommendations.csv`
- `tuned_candidate_app_overlay.csv`
- `historical_dropped_veteran_proxy_cohorts.csv`
- `NWR_HISTORICAL_DROPPED_VETERAN_PROXY_COHORTS_20260622.md`

## Guardrail Confirmation

No app files, frozen board files, latest_candidate/latest_approved files, pinned snapshot files, vendor CSVs, or raw prediction dumps were changed by this tuning pass.
