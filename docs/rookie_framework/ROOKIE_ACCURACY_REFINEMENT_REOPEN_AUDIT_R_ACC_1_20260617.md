# Rookie Accuracy Refinement Reopen Audit R-ACC-1

Date: 2026-06-17

Status: docs-only reopen audit for controlled accuracy refinement and early-pick tuning review.

## Scope

Rookie HQ is reopened only for a controlled accuracy-refinement and early-pick risk plan. This audit does not change the model, formula, board order, data files, local exports, production rankings, Outcome files, veteran/model_v4 files outside this Rookie repo, or app artifacts.

## Current Frozen State

- Formula unchanged: `cfbd_enriched_baseline_v1_1`
- Board order unchanged and frozen.
- Rookie artifacts remain local/manual-use inputs only.
- Rookie artifacts are not production/app rankings.
- ADP/market remains display-only and must not affect NWR private value.
- Final kit quality was GREEN.
- Manual draft trust was YELLOW because display-only fields still contain `needs_data`.

CSV confirmation from the final Mock Draft rookie input:

- 54 of 54 rows have `formula_name = cfbd_enriched_baseline_v1_1`.
- 54 of 54 rows have `board_order_frozen = yes`.

## Final Artifact Paths Found

Final post-fill kit directory:

- `local_exports/rookie_framework/final_post_fill_runway_20260616/`

Current final artifacts:

- Preview: `local_exports/rookie_framework/final_post_fill_runway_20260616/preview/index.html`
- Final manual board: `local_exports/rookie_framework/final_post_fill_runway_20260616/rookie_2026_final_manual_draft_board_post_fill_runway_20260616.csv`
- Mock Draft rookie input: `local_exports/rookie_framework/final_post_fill_runway_20260616/rookie_2026_mock_draft_input_20260616.csv`
- Missing-data templates: `local_exports/rookie_framework/final_post_fill_runway_20260616/missing_data_templates/`

Missing-data templates found:

- `rookie_missing_adp_market_template_20260616.csv`
- `rookie_missing_nfl_team_template_20260616.csv`
- `rookie_missing_age_dob_template_20260616.csv`
- `rookie_missing_depth_chart_role_template_20260616.csv`

## Needs Data Summary

Current display-field coverage:

| Field | Populated Rows | `needs_data` Rows | Accuracy Impact |
|---|---:|---:|---|
| `ADP / Market` | 46 | 8 | Display-only market context; must not affect private score. |
| `NFL Team` | 46 | 8 | Display/manual context for draft room and role review. |
| `Age` | 27 | 27 | Manual risk context, especially early-pick age and late-breakout checks. |
| `Depth Chart / Role` | 11 | 43 | Main manual-trust gap; role must be reviewed before high-cost picks. |
| `NFL Draft Capital` | 54 | 0 | Fully populated display context. |

These fields affect display completeness and manual draft trust only in the current frozen kit. They do not change `cfbd_enriched_baseline_v1_1`, private model score, or frozen board order.

The most important current manual-trust issue is depth chart / role coverage. In the top early tier, only Jeremiyah Love has a populated role display; the remaining Tier 1 players show `needs_data` role prompts. That does not invalidate the board, but it means early picks still need manual role confirmation before draft-room action.

## Early-Pick Decision Tier

The current top early-pick decision tier is `Tier 1 - Priority Targets`, with 9 players:

| Rank | Player | Pos | Draft Action | Warning Severity | Current Role Display |
|---:|---|---|---|---|---|
| 1 | Jeremiyah Love | RB | target | none | `RB_PREMIUM_THREE_DOWN|RB_RECEIVING_BACK` |
| 2 | Makai Lemon | WR | target | none | `needs_data: nfl_depth_chart_target_earning_role` |
| 3 | Carnell Tate | WR | target | none | `needs_data: nfl_depth_chart_target_earning_role` |
| 4 | KC Concepcion | WR | target | none | `needs_data: nfl_depth_chart_target_earning_role` |
| 5 | Jadarian Price | RB | target | none | `needs_data: nfl_depth_chart_rush_goal_line_first_down_role` |
| 6 | Denzel Boston | WR | target | none | `needs_data: nfl_depth_chart_target_earning_role` |
| 7 | Germie Bernard | WR | target | none | `needs_data: nfl_depth_chart_target_earning_role` |
| 8 | Chris Bell | WR | target | soft_note | `needs_data: nfl_depth_chart_target_earning_role` |
| 9 | Zachariah Branch | WR | target | soft_note | `needs_data: nfl_depth_chart_target_earning_role` |

Immediate Tier 2 boundary names also matter for early-pick risk because they may enter the same draft window when Tier 1 dries up:

- Antonio Williams, rank 10, `manual_hold`, `critical_trap_guard`, very-high bust risk band, role `needs_data`.
- Jonah Coleman, rank 11, `consider_at_value`, `manual_review`, high bust risk band, role populated as `RB_PREMIUM_THREE_DOWN`.
- Skyler Bell, rank 12, `consider_at_value`, `manual_review`, lower bust risk band, role populated as `WR_TRUE_ALPHA_TARGET_EARNER`.

## Evidence That Matters Most For Early-Pick Accuracy

The next accuracy work should focus on whether the frozen top tier is safe to draft at premium cost, not on reordering the board yet.

Draft capital:

- Confirm actual NFL draft slot, team investment, and whether draft capital supports premium rookie pick cost.
- Treat round/pick corrections as factual repairs.
- Treat changing how draft capital is weighted as a formula change, which remains blocked in R-ACC-1.

Age:

- Complete missing ages and DOBs where source-safe.
- Use age as manual context for breakout timing, older-prospect discount, and class-relative risk.
- Do not convert age completion into a new hidden score or rank key.

Production profile:

- Preserve the existing CFBD-enriched production view.
- Review top-tier players whose rank depends on production strength but whose role or source context is incomplete.
- For WRs, prioritize target earning, YPRR-style efficiency context, route role, separation/press evidence, and first-down target conversion.
- For RBs, prioritize early-down usage, receiving role, short-yardage conversion, goal-line path, missed tackle creation, and first-down rushing/receiving context.

Athletic profile:

- Add only source-safe factual context where available.
- Use it as a manual risk note, especially for players with role ambiguity or late draft capital.
- Do not create a new athleticism multiplier or hidden sort key in this sprint.

Early depth chart / role:

- This is the largest current display gap and the most decision-relevant early-pick evidence.
- For WRs, confirm target-earning path, route participation path, target competition, slot/outside fit, and whether the NFL team has a credible early snaps path.
- For RBs, confirm early-down path, receiving path, pass-protection trust, goal-line path, and short-yardage/first-down utility.

Team context:

- Confirm NFL team for remaining `needs_data` rows.
- Review offensive environment, incumbent competition, draft investment, coaching usage tendencies where source-safe, and whether the landing spot creates an actionable opportunity or a buried profile.
- Keep team context as manual evidence unless a later approved sprint explicitly proposes a formula change.

Injury/off-field flags:

- Preserve visible warning/manual fields.
- Upgrade player-specific risk notes when factual corrections clarify injury/source/off-field context.
- Do not hide or dilute existing manual-hold and trap-guard warnings.

Positional scarcity in this league format:

- Keep scarcity as manual draft-room context, not a private-score input in this sprint.
- Prioritize RB roles with first-down/goal-line utility and WRs with real target-earning paths because early picks have high opportunity cost.

Non-PPR / first-down fit:

- For RBs, first-down rushing/receiving conversion, short-yardage success, and goal-line role matter more than empty receiving volume.
- For WRs, target quality, first-down conversion, route role, and credible full-time target earning matter more than pure PPR volume assumptions.
- Any future formula change for non-PPR or first-down fit must be pre-registered and separately approved.

## Factual Corrections Versus Model Changes

Safe factual corrections:

- Correct a player name, position, NFL team, draft slot, age/DOB, factual injury/off-field note, or role/depth chart note.
- Fill a `needs_data` display field with source-safe evidence.
- Improve a player-specific manual risk note while keeping the rank, formula, and draft action unchanged unless separately approved.
- Update missing-data templates or a docs-only manual review packet in a later approved sprint.

True model/formula changes:

- Changing `cfbd_enriched_baseline_v1_1` weights or feature definitions.
- Recomputing private score or rank.
- Changing board order.
- Adding a new role, age, athletic, market, or scarcity score.
- Adding probabilities, new bands, hidden sort keys, or promoted artifacts.
- Using ADP/market as private value.

Only the factual-correction lane is safe without a later explicit approval.

## Safe Candidate Refinement Lanes

1. Factual-data repair

Fill display-only `needs_data` for top-tier and early Tier 2 players first. Priority order: depth chart / role, age, NFL team, ADP/market display. Draft capital is already complete but should be corrected if a factual error is found.

2. Player-specific risk-note upgrade

Upgrade visible manual notes for early picks where source-safe role, injury, off-field, or team context changes the draft-room question. This should improve manual trust without changing board order or private score.

3. Manual tier-review packet

Create a docs or CSV packet for Tim that asks the early-pick questions player by player. The packet should separate "draftable at cost", "draftable only at discount", and "manual hold until cleared" as review language only, not as a new rank or promoted artifact.

4. Formula sensitivity audit

Run a docs-only or read-only audit that asks how sensitive top 12/top 24 decisions would be to specific pre-registered hypotheses. It should not create a new formula, new board, or new artifacts that look like rankings. Any later executable sensitivity work needs explicit sprint approval.

5. Early-pick bust-avoidance checklist

Build a checklist focused on avoiding premium-pick mistakes:

- Is draft capital strong enough for the cost?
- Is age within acceptable risk context?
- Is the production profile source-safe and not driven by one fragile signal?
- Is the athletic profile neutral or better for the role?
- Is there a credible early role path?
- Does the NFL team context support opportunity?
- Are injury/off-field/source flags cleared?
- Does position scarcity justify the cost?
- Does the profile fit non-PPR and first-down scoring?
- Is ADP/market being used only for price and availability pressure, not private value?

## Blocked In This Reopen Sprint

The following remain blocked:

- Formula change.
- Board reorder.
- App or production rankings.
- Probabilities or new bands.
- Hidden sort keys.
- Promoted artifacts.
- Outcome files.
- Veteran/model_v4 files outside this Rookie repo.
- ADP/market contaminating NWR private value.
- Any local export rebuild unless explicitly approved.
- Any staging or commit of `data/` or `local_exports/`.

## Recommended Next Safe Sprint

Recommended next sprint: `R-ACC-2 - Early-Pick Display Data Repair And Manual Tier Review Packet`.

Proposed scope:

- Docs plus optional manual-use CSV under an approved path only if Tim approves an export.
- No model logic changes.
- No board-order changes.
- No production/app integration.
- Fill or review source-safe depth chart / role and age evidence for Tier 1 plus ranks 10-12.
- Produce a player-by-player early-pick manual review packet that keeps `cfbd_enriched_baseline_v1_1` and frozen rank intact.
- Include an anti-cheat check confirming ADP/market remains display-only.

Recommended priority:

1. Tier 1 role repair, because 8 of 9 top-tier players currently need role/depth-chart display data.
2. Tier 1 and ranks 10-12 age/injury/source review.
3. Boundary review for Antonio Williams, Jonah Coleman, and Skyler Bell because those are the first early-pick alternatives after Tier 1.
4. Only after review, decide whether a separate `R-ACC-3` formula sensitivity audit should be authorized.

## R-ACC-1 Result

This sprint should end uncommitted for Rookie HQ review. The audit defines safe refinement lanes but does not change the formula, board order, production artifacts, data files, or existing board artifacts.
