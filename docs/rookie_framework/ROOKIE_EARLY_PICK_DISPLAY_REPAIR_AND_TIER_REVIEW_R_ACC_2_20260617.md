# Rookie Early-Pick Display Repair And Tier Review R-ACC-2

Date: 2026-06-17

Verdict: YELLOW for manual early-pick use.

R-ACC-2 improves 1.03 / 1.04 review confidence by separating clear early-pick options from verify-first and hold profiles. It does not make the early-pick board GREEN because depth chart / role context remains missing for 8 of 9 Tier 1 players and for Antonio Williams at the Tier 2 boundary.

## What R-ACC-2 Did

- Committed the approved R-ACC-1 docs-only audit before starting R-ACC-2.
- Inspected the frozen final manual board and Mock Draft rookie input.
- Confirmed `cfbd_enriched_baseline_v1_1` and frozen board order remain intact.
- Audited Tier 1 Priority Targets plus Antonio Williams.
- Built local-only manual-use exports for display gaps, proposed repair inputs, early-pick review, 1.03 / 1.04 decision support, top-15 trap guard review, and Tim input requests.
- Preserved ADP/market as display-only context.

## What R-ACC-2 Did Not Do

- Did not change the formula.
- Did not change board order.
- Did not change private/model scores.
- Did not overwrite frozen final board artifacts.
- Did not create probabilities, new bands, hidden sort keys, or promoted artifacts.
- Did not touch app, Streamlit, Outcome, veteran, or model_v4 production files.
- Did not use ADP, public rankings, projections, trade calculators, or market values as private/model inputs.
- Did not commit R-ACC-2 work.

## Commands Run

- `Get-Location`
- `git branch --show-current`
- `git status --short`
- `git log --oneline -12`
- `git add -- docs/rookie_framework/ROOKIE_ACCURACY_REFINEMENT_REOPEN_AUDIT_R_ACC_1_20260617.md`
- `git diff --cached --name-only`
- `git commit -m "Document rookie accuracy refinement reopen audit R-ACC-1"`
- `git rev-parse --short HEAD`
- `git diff --cached --name-only`
- `Import-Csv local_exports/rookie_framework/final_post_fill_runway_20260616/rookie_2026_final_manual_draft_board_post_fill_runway_20260616.csv`
- `Import-Csv local_exports/rookie_framework/final_post_fill_runway_20260616/rookie_2026_mock_draft_input_20260616.csv`
- `Get-ChildItem local_exports/rookie_framework/final_post_fill_runway_20260616/missing_data_templates`
- `Get-Content docs/rookie_framework/ROOKIE_ACCURACY_REFINEMENT_REOPEN_AUDIT_R_ACC_1_20260617.md`
- `rg -n "Tier 1|Antonio Williams|critical_trap_guard|manual_hold|1\\.03|1\\.04|non-PPR|first-down|depth chart|role|school|source" docs/rookie_framework local_exports/rookie_framework -g "*.md" -g "*.csv"`
- `Import-Csv local_exports/rookie_framework/current_2026_cfbd_feature_ingestion_20260615/current_2026_feature_ingested_manual_board_20260615.csv`
- `Import-Csv local_exports/rookie_framework/current_2026_feature_aware_rescore_candidate_20260615/current_2026_feature_aware_candidate_board_20260615.csv`
- Inline Python stdlib CSV generation for the R-ACC-2 local-only export packet.

Some broad read commands timed out while scanning large export trees, but the targeted final board, mock input, and feature-context reads completed and drove the audit.

## Files Inspected

- `docs/rookie_framework/ROOKIE_ACCURACY_REFINEMENT_REOPEN_AUDIT_R_ACC_1_20260617.md`
- `docs/rookie_framework/ROOKIE_CURRENT_2026_TOP36_DRAFT_DECISION_REVIEW_20260615.md`
- `docs/rookie_framework/ROOKIE_DRAFT_CAPITAL_TRAP_GUARD_OVERLAY_20260615.md`
- `docs/rookie_framework/ROOKIE_MODEL_CEILING_TUNING_OPPORTUNITY_AUDIT_20260615.md`
- `docs/rookie_framework/ROOKIE_MODEL_TUNING_RUNWAY_V1_1_20260615.md`
- `local_exports/rookie_framework/final_post_fill_runway_20260616/rookie_2026_final_manual_draft_board_post_fill_runway_20260616.csv`
- `local_exports/rookie_framework/final_post_fill_runway_20260616/rookie_2026_mock_draft_input_20260616.csv`
- `local_exports/rookie_framework/final_post_fill_runway_20260616/missing_data_templates/`
- `local_exports/rookie_framework/current_2026_cfbd_feature_ingestion_20260615/current_2026_feature_ingested_manual_board_20260615.csv`
- `local_exports/rookie_framework/current_2026_feature_aware_rescore_candidate_20260615/current_2026_feature_aware_candidate_board_20260615.csv`

## Files Changed

Committed before R-ACC-2:

- `docs/rookie_framework/ROOKIE_ACCURACY_REFINEMENT_REOPEN_AUDIT_R_ACC_1_20260617.md`

Created for R-ACC-2 and left uncommitted:

- `docs/rookie_framework/ROOKIE_EARLY_PICK_DISPLAY_REPAIR_AND_TIER_REVIEW_R_ACC_2_20260617.md`
- `local_exports/rookie_framework/r_acc_2_early_pick_display_repair_20260617/README_R_ACC_2_EARLY_PICK_DISPLAY_REPAIR_20260617.md`
- `local_exports/rookie_framework/r_acc_2_early_pick_display_repair_20260617/rookie_tier1_context_gap_audit_20260617.csv`
- `local_exports/rookie_framework/r_acc_2_early_pick_display_repair_20260617/rookie_display_data_repair_candidates_20260617.csv`
- `local_exports/rookie_framework/r_acc_2_early_pick_display_repair_20260617/rookie_display_data_repair_log_20260617.csv`
- `local_exports/rookie_framework/r_acc_2_early_pick_display_repair_20260617/rookie_early_pick_manual_tier_review_20260617.csv`
- `local_exports/rookie_framework/r_acc_2_early_pick_display_repair_20260617/rookie_103_104_decision_matrix_20260617.csv`
- `local_exports/rookie_framework/r_acc_2_early_pick_display_repair_20260617/rookie_top15_trap_guard_review_20260617.csv`
- `local_exports/rookie_framework/r_acc_2_early_pick_display_repair_20260617/rookie_missing_input_request_for_tim_20260617.csv`

## Display Repair Result

No display fields were directly repaired in the frozen board or mock input.

Reason: Tier 1 plus Antonio already have ADP/market display, NFL team, age, and draft capital populated. The remaining early-pick display gap is Depth Chart / Role for 9 players, and no existing local source-safe artifact contained a direct NFL depth-chart role value that could safely replace `needs_data`.

Repair candidates were created instead:

- `rookie_display_data_repair_candidates_20260617.csv`
- 9 rows, all for `Depth Chart / Role`
- Action: keep `needs_data`; request Tim/source-safe role evidence

Repair log:

- `rookie_display_data_repair_log_20260617.csv`
- Records that no direct repair was applied.

## Open Display / Manual-Trust Gaps

For Tier 1 plus Antonio Williams:

| Player | Rank | Open Gap |
|---|---:|---|
| Jeremiyah Love | 1 | none in display fields |
| Makai Lemon | 2 | Depth Chart / Role |
| Carnell Tate | 3 | Depth Chart / Role |
| KC Concepcion | 4 | Depth Chart / Role |
| Jadarian Price | 5 | Depth Chart / Role |
| Denzel Boston | 6 | Depth Chart / Role |
| Germie Bernard | 7 | Depth Chart / Role |
| Chris Bell | 8 | Depth Chart / Role |
| Zachariah Branch | 9 | Depth Chart / Role |
| Antonio Williams | 10 | Depth Chart / Role |

## Tier 1 Player Review

Jeremiyah Love, RB, Notre Dame, rank 1:

- Appeal: elite source-safe CFBD production plus strong share context; round 1 pick 3; populated role display.
- Trap risk: moderate bust-risk display and remaining RB first-down/goal-line/pass-pro/injury evidence questions.
- Scoring fit: best current profile for non-PPR and first-down scoring because RB first-down and goal-line paths are directly valuable.
- Manual recommendation: 1.03 viable and 1.04 viable, high/manual-only confidence.

Makai Lemon, WR, USC, rank 2:

- Appeal: elite source-safe CFBD production plus strong share context; round 1 pick 20.
- Trap risk: role/depth chart is missing and route/separation/first-down target evidence remains incomplete.
- Scoring fit: target quality and first-down earning matter more than empty reception volume.
- Manual recommendation: 1.04 viable after role verification; 1.03 only if Tim clears target-earning path.

Carnell Tate, WR, Ohio State, rank 3:

- Appeal: round 1 pick 4 and strong source-safe CFBD production profile.
- Trap risk: very-high bust risk, low source confidence, and missing role/depth chart context.
- Scoring fit: needs proof that the NFL role supports first-down target earning, not just draft capital.
- Manual recommendation: verify-first for 1.03 / 1.04.

KC Concepcion, WR, Texas A&M, rank 4:

- Appeal: strong CFBD production profile and round 1 pick 24.
- Trap risk: missing role/depth chart context and unresolved target-earning evidence.
- Scoring fit: useful if his NFL role supports quality targets and first-down conversion.
- Manual recommendation: 1.04 viable after role verification; 1.03 only if Tim clears target-earning path.

Jadarian Price, RB, Notre Dame, rank 5:

- Appeal: round 1 pick 32 and RB scarcity in non-PPR/first-down scoring.
- Trap risk: high bust-risk display and missing early-down, first-down, goal-line, receiving, and pass-pro role evidence.
- Scoring fit: could matter if he has goal-line/first-down utility; otherwise the profile is not clear enough for a premium pick.
- Manual recommendation: trade-down or verify-first.

Denzel Boston, WR, Washington, rank 6:

- Appeal: strong CFBD production profile and round 2 draft capital.
- Trap risk: missing target-earning role and route/first-down evidence gaps.
- Scoring fit: needs quality-target proof for non-PPR.
- Manual recommendation: trade-down / late-1st review, not clear for 1.03 or 1.04 today.

Germie Bernard, WR, Alabama, rank 7:

- Appeal: strong CFBD production profile and round 2 draft capital.
- Trap risk: role/depth chart missing, plus target-route evidence gaps.
- Scoring fit: useful only if target quality and first-down path are real.
- Manual recommendation: trade-down / late-1st review.

Chris Bell, WR, Louisville, rank 8:

- Appeal: elite source-safe CFBD production plus strong share context.
- Trap risk: round 3 draft capital, soft note, and missing role/depth chart.
- Scoring fit: needs target-earning evidence before premium pick use.
- Manual recommendation: trade-down / late-1st review.

Zachariah Branch, WR, Georgia, rank 9:

- Appeal: strong CFBD production profile.
- Trap risk: round 3 draft capital, soft note, and missing role/depth chart.
- Scoring fit: must prove target quality and first-down role.
- Manual recommendation: trade-down / late-1st review.

## Antonio Williams Boundary Risk

Antonio Williams, WR, Clemson, rank 10:

- Tier: Tier 2 - Strong Considers.
- Draft action: `manual_hold`.
- Warning: `critical_trap_guard`.
- Appeal: still near the early-pick boundary in the frozen order.
- Trap risk: very-high bust-risk display, round 3 pick 71, no standout CFBD edge in the final board note, and missing role/depth chart context.
- Manual recommendation: hold. Do not treat as 1.03 or 1.04 viable until Tim clears the trap-guard question with source-safe role and target-earning evidence.

## 1.03 / 1.04 Decision Matrix Summary

| Player | Rank | Pick Fit | Confidence | 1.03 Today | 1.04 Today |
|---|---:|---|---|---|---|
| Jeremiyah Love | 1 | 1.03 viable; 1.04 viable | high/manual-only | yes, verify health/role on draft day | yes, verify health/role on draft day |
| Makai Lemon | 2 | 1.04 viable after role verification; 1.03 only after target-path clearance | medium/manual-only | no, verify role first | verify-first |
| Carnell Tate | 3 | verify-first; premium draft capital but high bust/source risk | medium/manual-only | no | verify-first |
| KC Concepcion | 4 | 1.04 viable after role verification; 1.03 only after target-path clearance | medium/manual-only | no | verify-first |
| Jadarian Price | 5 | trade-down or verify-first | medium/manual-only | no | verify-first |
| Denzel Boston | 6 | trade-down / late-1st review | low/manual-only | no | no |
| Germie Bernard | 7 | trade-down / late-1st review | low/manual-only | no | no |
| Chris Bell | 8 | trade-down / late-1st review | low/manual-only | no | no |
| Zachariah Branch | 9 | trade-down / late-1st review | low/manual-only | no | no |
| Antonio Williams | 10 | hold | low/manual-only | no | no |

## Scoring-Format Fit Notes

This league format is 1QB, non-PPR, first-down scoring.

- RBs benefit when the profile supports early-down, goal-line, short-yardage, and first-down conversion roles.
- RB receiving matters only if it creates first downs or durable snap access, not empty PPR volume.
- WRs need target quality, route stability, target earning, and first-down conversion proof.
- Empty reception volume, public ADP, and market heat should not move private value.
- Position scarcity matters manually, but it was not turned into a new score or hidden sort key.

## Trap-Guard Notes

- Antonio Williams is the main premium-zone trap guard: rank 10, `manual_hold`, `critical_trap_guard`.
- Carnell Tate has premium draft capital and rank 3, but carries very-high bust risk and low source confidence in the supporting source context.
- Jadarian Price has RB scarcity appeal but a material role gap and high bust-risk display.
- Chris Bell and Zachariah Branch are Tier 1 names with round 3 draft capital and soft notes, making them trade-down or late-1st review profiles until role evidence is stronger.

## Do Not Use For Production/App

Do not wire this packet into production rankings, Streamlit/app surfaces, Outcome files, veteran boards, or private-score model_v4 artifacts. The R-ACC-2 exports are local/manual-use review aids only. They are not promoted artifacts and they are not a new ranking board.

## How Tim Should Use This On Draft Day

1. Treat Jeremiyah Love as the only current high-confidence 1.03 / 1.04 option, pending ordinary draft-day health and role sanity checks.
2. Treat Makai Lemon, Carnell Tate, KC Concepcion, and Jadarian Price as verify-first candidates for 1.04 or trade-down paths.
3. Do not use Denzel Boston, Germie Bernard, Chris Bell, Zachariah Branch, or Antonio Williams at 1.03 / 1.04 without new source-safe role evidence.
4. Use ADP/market only for price and availability pressure.
5. Before selecting any missing-role player, answer the depth-chart / role question in the player row.

## What Tim Needs To Provide Next

For Makai Lemon, Carnell Tate, KC Concepcion, Denzel Boston, Germie Bernard, Chris Bell, Zachariah Branch, and Antonio Williams:

- NFL depth chart role.
- Target-earning path.
- Route participation path.
- Separation/press or target-quality evidence.
- First-down target conversion context.
- Current health/status context.

For Jadarian Price:

- NFL depth chart role.
- Early-down role path.
- Goal-line/short-yardage role.
- First-down rushing/receiving evidence.
- Pass-pro trust.
- Current health/status context.

## Coverage Check

- Mock Draft rookie input row count: 54.
- Formula guard: 54 of 54 rows remain `cfbd_enriched_baseline_v1_1`.
- Board-order guard: 54 of 54 rows remain `board_order_frozen = yes`.
- Frozen final board was not overwritten.
- Private/model score was not changed.
- No production/app artifact was promoted.

Early-pick-relevant top-15 players outside Tier 1:

- Antonio Williams: outside Tier 1 because he is Tier 2 with `manual_hold` and `critical_trap_guard`.
- Jonah Coleman: Tier 2, `manual_review`, late draft capital, role populated but still a price/role confirmation profile.
- Skyler Bell: Tier 2, `manual_review`, role populated but late draft capital.
- Brenen Thompson: Tier 2, `manual_review`, missing role.
- Elijah Sarratt: Tier 2, `manual_review`, missing role.
- Emmett Johnson: Tier 2, `manual_review`, late draft capital despite useful RB role display.

## Next Best Codex Prompt

Run `R-ACC-3 - Source-Safe Early-Pick Role Intake And No-Reorder Review`.

Suggested scope:

- Ingest Tim-provided role/depth-chart evidence for Tier 1 plus Antonio Williams.
- Fill only display/manual-trust fields.
- Keep `cfbd_enriched_baseline_v1_1`.
- Keep board order frozen.
- Produce a revised manual review packet only, not a new ranking.
- Confirm ADP/market remains display-only.

## R-ACC-2 Closeout

R-ACC-2 should remain uncommitted for Rookie HQ review. The R-ACC-1 commit is the only commit made in this sprint sequence.
