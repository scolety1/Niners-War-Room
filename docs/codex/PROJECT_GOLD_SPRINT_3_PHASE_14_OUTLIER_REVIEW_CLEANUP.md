# Project Gold Sprint 3 / Phase 14: Outlier Review Cleanup

Date: 2026-05-14

## Starting Point

The Sprint 3 Phase 13 checklist had one remaining review row:

- `232 lower-severity review-required outliers remain; 116 outliers have audited acceptance rows.`

There were no unresolved high-severity or blocking outliers in the active backlog.

## Findings

All 232 unresolved rows were medium-severity `stale_source_data` rows.

The unresolved backlog split into:

- `79` stale injury/player-metadata rows
- `153` stale market/replaceability/player-metadata rows

The market/replaceability rows were being bucketed as `True Ranking Weirdness`. That was too alarming for the actual issue, because these rows were stale optional market/context sources, not evidence that a private football rank was broken.

## Code Patch

Updated stale-source bucket classification so stale market, FantasyCalc, DynastyProcess, replaceability, and liquidity sources are treated as `Missing Market Reference` instead of `True Ranking Weirdness`.

This is a classification fix only. It does not change formulas or player scores.

## Acceptance Rows

Added audited acceptance rows for the 232 lower-severity stale-source outliers in:

`local_exports/active_veteran_model_public_sources/model_outlier_acceptances.csv`

Acceptance policy:

- Scores unchanged.
- Review status only.
- Market remains isolated from private Model Value.
- Injury data was not invented.
- Stale-source context remains visible in audit outputs.

## Recheck Result

Updated outlier state:

- Total outliers: `398`
- Review-required outliers: `348`
- Accepted review-required outliers: `348`
- Unresolved review-required outliers: `0`
- Invalid acceptance rows: `0`

Updated checklist:

- Roster Decisions: `Roster Decisions Ready`
- Draft Ready: `Draft Pool Needs Data`
- Final Money Decisions: `Needs Data`
- Blocked rows: `0`
- Review rows: `0`
- Ready rows: `9`

## Exports

Outlier review export:

`local_exports/model_audits/sprint3_phase14_outlier_review_cleanup_20260514`

Fresh audit packet:

`local_exports/model_audits/sprint3_phase14_model_audit_packet_20260514`

## Remaining Boundary

This clears pre-declaration roster-decision blockers. It does not make the draft room or final money decisions ready because the draft pool still needs official released veterans and final draft inputs.
