# QB/TE Context Balance v2 Production Patch Proposal - 2026-06-09

Proposal only. No implementation or promotion occurred.

## Selected v2 Candidate
`qb_context_balance_te_upper_band_guard_v2`

## Hypothesis
A revised QB/TE discipline patch can preserve the improved 1QB QB behavior from v1 while allowing source-safe elite TE exceptions in no-TE-premium.

## Why v1 Was Revised
v1 improved QB shape but compressed all TEs out of the top 25, including elite private-evidence rows. That was likely too blunt for dynasty review.

## Why v2 Is Safer
- Selected classification: `candidate_promising_for_human_review`.
- Top 25 mix: {'WR': 11, 'RB': 10, 'TE': 2, 'QB': 2}.
- TE exception gates passed/blocked: 4/28.
- TE exception behavior is driven by private component receipts, confidence/trust, and warnings.
- RB/WR scores remain unchanged.

## Production Files Likely Affected Later
- `src/services/model_v4_qb_te_current_value_service.py`
- `src/services/model_v4_current_value_checkpoint_service.py`, if additional discipline receipts are exposed
- `src/services/full_board_current_value_export_service.py`, only for routing/readback

## Tests Required Later
- QB top-10/top-25 1QB shape check using private outputs only.
- TE elite-exception receipt gate check.
- TE age/status caution check.
- RB/WR score unchanged check.
- My Team movement explainability check.
- Sentinel and contamination checks.
- Full-board 232 scored QB/RB/WR/TE and 8 hidden kickers check.

## Output Files That Would Change If Approved Later
- `qb_te_current_value_review_rows.csv`
- `qb_te_current_value_component_rows.csv`
- `qb_te_current_value_warnings.csv`
- `current_player_value_full_board_review_rows.csv`
- `full_player_board_value_review_rows.csv`
- follow-up movement/sanity/readiness reports

## Rollback Plan
Revert the production patch commit and regenerate active Rankings through the safe pipeline. Do not copy shadow CSVs into active output paths.

## Promotion Gate Checklist
- User approval before patching.
- No shadow CSV promotion.
- Production pipeline recomputes outputs.
- Source/lineage/sentinel/contamination gates pass.
- External/human review approves movement.
- Decision Board remains blocked until patched Rankings are re-audited.

## Failure Modes
- TE exception gate under-corrects no-premium and lets TEs dominate again.
- TE exception gate over-corrects and buries young elite TE profiles.
- QB compression still leaves elite QB collapse rows unexplained.
- Trust/source warnings become cleaner without source repair.
- Market/league/display-only context leaks into score behavior.

## Human Approval Required
Human approval is required before any production patch. Decision Board remains blocked.
