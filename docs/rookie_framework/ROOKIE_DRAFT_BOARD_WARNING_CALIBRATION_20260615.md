# Rookie Draft Board Warning Calibration

Date: 2026-06-16

Lane: Rookie framework only

## Executive Verdict

- Calibration quality: GREEN
- Draft-use clarity: GREEN
- Manual draft trust: YELLOW
- Anti-cheat/leakage: GREEN
- Main ranking formula changed: no
- Board order changed: no

This pass repairs the draft-room labels after the draft-capital trap overlay flagged 45 of the top 54 players. The calibrated board keeps `cfbd_enriched_baseline_v1_1` as the main ranking model and keeps the existing model rank order unchanged. It separates model target tier from draft action and trap/caution severity so Tim can see who the model likes without confusing warning priority for target priority.

No tuning, v2 formula, production ranking, private score change, app wiring, Streamlit file, Outcome file, veteran file, probability, band, hidden sort key, or promoted artifact was created.

## Inputs Reviewed

- `docs/rookie_framework/ROOKIE_DRAFT_CAPITAL_TRAP_GUARD_OVERLAY_20260615.md`
- `docs/rookie_framework/ROOKIE_CURRENT_2026_TOP36_DRAFT_DECISION_REVIEW_20260615.md`
- `docs/rookie_framework/ROOKIE_CURRENT_2026_BOARD_SANITY_AUDIT_20260615.md`
- `docs/rookie_framework/ROOKIE_MODEL_CEILING_TUNING_OPPORTUNITY_AUDIT_20260615.md`
- `local_exports/rookie_framework/draft_capital_trap_guard_overlay_20260615/draft_capital_trap_guard_final_draft_board_20260615.csv`
- `local_exports/rookie_framework/draft_capital_trap_guard_overlay_20260615/draft_capital_trap_guard_top54_overlay_20260615.csv`
- `local_exports/rookie_framework/current_2026_feature_aware_rescore_candidate_20260615/current_2026_feature_aware_candidate_board_20260615.csv`

## Files Created

- `scripts/rookie_framework/build_draft_board_warning_calibration.py`
- `tests/test_draft_board_warning_calibration.py`
- `docs/rookie_framework/ROOKIE_DRAFT_BOARD_WARNING_CALIBRATION_20260615.md`

## Local-Only Exports

Created under `local_exports/rookie_framework/draft_board_warning_calibration_20260615/`:

- `rookie_2026_final_manual_draft_board_warning_calibrated_20260615.csv`
- `rookie_2026_top_model_targets_20260615.csv`
- `rookie_2026_highest_warning_priority_20260615.csv`
- `rookie_2026_warning_calibration_changes_20260615.csv`
- `rookie_2026_position_lists_warning_calibrated_20260615.csv`
- `rookie_2026_tier_summary_warning_calibrated_20260615.csv`
- `rookie_2026_warning_calibration_verdicts_20260615.csv`
- `README_ROOKIE_DRAFT_BOARD_WARNING_CALIBRATION_20260615.md`

Final draft-room board:

- `local_exports/rookie_framework/draft_board_warning_calibration_20260615/rookie_2026_final_manual_draft_board_warning_calibrated_20260615.csv`

These exports are local-only and must not be committed.

## Severity Counts

Top-54 calibrated board:

| Severity | Count |
|---|---:|
| none | 7 |
| soft_note | 15 |
| manual_review | 26 |
| critical_trap_guard | 6 |

The previous overlay had 42 hard manual-review rows and 3 manual-review rows. This calibration keeps underlying risk visible but reserves `critical_trap_guard` for the highest-priority stop signs.

## Target Tiers

| Target Tier | Players | None | Soft Note | Manual Review | Critical |
|---|---:|---:|---:|---:|---:|
| tier_1_priority_target | 9 | 7 | 2 | 0 | 0 |
| tier_2_strong_consider | 15 | 0 | 0 | 12 | 3 |
| tier_3_value_fit | 12 | 0 | 6 | 6 | 0 |
| tier_4_manual_upside | 18 | 0 | 7 | 8 | 3 |

This is the key usability fix: target tier and warning severity are now separate. A Tier 1 target can have a soft note. A Tier 2 player can be a model strong-consider and still be a manual hold if the trap risk is too high.

## Top Model Targets

The top model-target view is rank ordered and remains separate from the warning-priority view.

| Rank | Player | Pos | Tier | Draft Action | Severity |
|---:|---|---|---|---|---|
| 1 | Jeremiyah Love | RB | tier_1_priority_target | target | none |
| 2 | Makai Lemon | WR | tier_1_priority_target | target | none |
| 3 | Carnell Tate | WR | tier_1_priority_target | target | none |
| 4 | KC Concepcion | WR | tier_1_priority_target | target | none |
| 5 | Jadarian Price | RB | tier_1_priority_target | target | none |
| 6 | Denzel Boston | WR | tier_1_priority_target | target | none |
| 7 | Germie Bernard | WR | tier_1_priority_target | target | none |
| 8 | Chris Bell | WR | tier_1_priority_target | target | soft_note |
| 9 | Zachariah Branch | WR | tier_1_priority_target | target | soft_note |
| 10 | Antonio Williams | WR | tier_2_strong_consider | manual_hold | critical_trap_guard |
| 11 | Jonah Coleman | RB | tier_2_strong_consider | consider_at_value | manual_review |
| 12 | Skyler Bell | WR | tier_2_strong_consider | consider_at_value | manual_review |
| 13 | Brenen Thompson | WR | tier_2_strong_consider | consider_at_value | manual_review |
| 14 | Elijah Sarratt | WR | tier_2_strong_consider | consider_at_value | manual_review |
| 15 | Emmett Johnson | RB | tier_2_strong_consider | consider_at_value | manual_review |
| 16 | Kaytron Allen | RB | tier_2_strong_consider | consider_at_value | manual_review |
| 17 | Adam Randall | RB | tier_2_strong_consider | consider_at_value | manual_review |
| 18 | Josh Cameron | WR | tier_2_strong_consider | consider_at_value | manual_review |
| 19 | Nicholas Singleton | RB | tier_2_strong_consider | consider_at_value | manual_review |
| 20 | Barion Brown | WR | tier_2_strong_consider | manual_hold | critical_trap_guard |
| 21 | Demond Claiborne | RB | tier_2_strong_consider | consider_at_value | manual_review |
| 22 | Lewis Bond | WR | tier_2_strong_consider | consider_at_value | manual_review |
| 23 | J'Mari Taylor | RB | tier_2_strong_consider | consider_at_value | manual_review |
| 24 | Kentrel Bullock | RB | tier_2_strong_consider | manual_hold | critical_trap_guard |

## Highest Warning Priority

Warning priority is not target priority. These are the rows Tim should pause on first.

Critical warning-priority rows:

- Antonio Williams: premium-window rank with high bust risk and no standout CFBD edge.
- Barion Brown: premium-window rank with high bust risk and no standout CFBD edge.
- Kentrel Bullock: missing draft-capital context in the top 24 with fragility flags.
- Deion Burks: very late draft-capital profile with weak support signals.
- Braylon James: missing or unmatched current evidence can make the rank unreliable.
- Chip Trayanum: missing or unmatched current evidence can make the rank unreliable.
- Jam Miller: outside top-54 focus hold; unavailable/source-limited/unmatched current CFBD identity.
- Jaydn Ott: outside top-54 focus hold; unavailable/source-limited/unmatched current CFBD identity.

Important manual-review rows include Jonah Coleman, Skyler Bell, Brenen Thompson, Elijah Sarratt, Emmett Johnson, Kaytron Allen, Adam Randall, Josh Cameron, Nicholas Singleton, Demond Claiborne, Lewis Bond, J'Mari Taylor, Kejon Owens, Sieh Bangura, Robert Henry Jr., Jacob De Jesus, Dominic Richardson, Devin Voisin, Roman Hemby, Barika Kpeenu, Jordyn Tyson, and Eli Stowers.

## Focus Player Notes

- Jeremiyah Love: top model target; no trap severity from this pass, but existing injury/source manual review still matters.
- Makai Lemon: top model target; no trap severity from this pass.
- Carnell Tate: top model target; no trap severity from this pass, but prior injury/source sanity check remains.
- KC Concepcion: top model target; no trap severity from this pass.
- Jadarian Price: top model target; no trap severity from this pass.
- Denzel Boston: top model target; no trap severity from this pass.
- Germie Bernard: top model target; no trap severity from this pass.
- Chris Bell: target with `soft_note`; do not let the note hide target status.
- Zachariah Branch: target with `soft_note`; do not let the note hide target status.
- Antonio Williams: strong-consider by model rank, but `critical_trap_guard`; manual hold.
- Jonah Coleman: strong-consider at value; manual review for price/role.
- Barion Brown: strong-consider by model rank, but `critical_trap_guard`; manual hold.
- Kentrel Bullock: strong-consider by model rank, but `critical_trap_guard`; manual hold.
- Jordyn Tyson: manual-upside hold; injury/source manual review remains the key issue.
- Jam Miller: outside top-54 hold/avoid unless price collapses and identity/evidence is repaired.
- Jaydn Ott: outside top-54 hold/avoid unless price collapses and identity/evidence is repaired.

## Draft-Room Semantics

Use these meanings:

- `target`: model likes the player; draft if the board and room fit.
- `strong_consider`: draft-window player; do not confuse caution with a downgrade by itself.
- `consider_at_value`: useful player, but price discipline matters.
- `wait_for_discount`: let the room discount the player before acting.
- `manual_hold`: stop until Tim answers the manual question.
- `avoid_unless_price_collapses`: not model-cleared for normal draft use.

Trap severity meanings:

- `none`: no specific draft-capital-trap warning beyond normal rookie uncertainty.
- `soft_note`: context is preserved but should not stop draft use.
- `manual_review`: meaningful caution; Tim should check the manual question.
- `critical_trap_guard`: strongest warning; do not draft from rank alone.

## Anti-Cheat / Leakage Audit

- Main model remains `cfbd_enriched_baseline_v1_1`: PASS
- Main board order unchanged: PASS
- No broad weight tuning: PASS
- No v2 formula: PASS
- ADP/market not used as private score input: PASS
- No probabilities or bands: PASS
- No Outcome, production, private-score, app, Streamlit, veteran, hidden sort key, or promoted artifact files touched: PASS
- Top model targets and highest warning priority are separate views: PASS

## Validation Commands

- `git status --short`
- `git branch --show-current`
- `git rev-parse HEAD`
- `python -m py_compile scripts\rookie_framework\build_draft_board_warning_calibration.py tests\test_draft_board_warning_calibration.py`
- `python tests\test_draft_board_warning_calibration.py`
- `python scripts\rookie_framework\build_draft_board_warning_calibration.py`
- `git diff --check`
- `python -m pytest tests\test_draft_board_warning_calibration.py -q`

Result: direct calibration harness, calibration export build, upstream trap-overlay harness, and `git diff --check` passed. `pytest` was unavailable in the active Python environment (`No module named pytest`), so the direct harness result was used.

## Final Recommendation

Use the warning-calibrated board as the draft-room sheet. The next rookie-only task should be manual resolution of the `critical_trap_guard` players, not another scoring or tuning pass.
