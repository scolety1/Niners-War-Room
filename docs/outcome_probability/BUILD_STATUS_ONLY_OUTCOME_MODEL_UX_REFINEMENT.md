# Build Status-Only Outcome Model UX Refinement

## Verdict

`STATUS_ONLY_UX_REFINEMENT_READY_FOR_MANUAL_REVIEW`

The player detail card keeps the status-only **Outcome Model Status** section, but the detailed status table is now collapsed by default under `Outcome status details`. The guardrail copy remains visible above the expander:

`Outcome model is in development. No probabilities are released yet.`

## Scope

This is a UX-only refinement after the Sprint 5AM through 5AP audit bundle:

- Sprint 5AM: `KEEP_STATUS_ONLY_RECOMMENDED`
- Sprint 5AN: `STATUS_ONLY_UX_PASS_WITH_RECOMMENDATIONS`
- Sprint 5AO: `DISPLAY_GATE_AUDIT_PASS`
- Sprint 5AP: `STATUS_ONLY_KEEP_RECOMMENDED`

The only addressed issue is visual density. No model, ranking, release-gate, or probability logic changed.

## Change Made

Updated `app/components/player_detail_card.py` so:

- `Outcome Model Status` remains visible.
- The guardrail copy remains visible.
- The detailed `Outcome` / `Status` / `Help` table is inside a collapsed Streamlit expander.
- The table still renders only text columns.

## Safety Contract Preserved

Still blocked:

- real app probabilities
- percentages
- probability bands
- hidden sortable values
- rankings or sorting by outcome model output
- decision automation
- internal model output consumption
- app-readable probability tables
- promoted or released model artifacts
- push/deploy

Service tests continue to verify:

- same-year rows show `In development`
- `next_year_starter` shows `Blocked by release gate`
- kicker rows are `Not applicable`
- `probability_value is None`
- `probability_band is None`
- `sortable_value is None`
- `is_numeric is False`
- `is_released is False`

## Manual Review Target

Open a QB/RB/WR/TE player detail card and confirm:

1. `Outcome Model Status` appears.
2. The no-probabilities guardrail copy is visible without expanding anything.
3. The detailed status rows are available only inside `Outcome status details`.
4. The table remains text-only.
5. Rankings and sorting behavior are unchanged.

## Recommendation

Ready for manual app review. Keep this player-card-only unless HQ explicitly approves a later UX or release-scope change.
