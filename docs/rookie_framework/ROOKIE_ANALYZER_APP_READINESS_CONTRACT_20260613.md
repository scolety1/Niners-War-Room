# Rookie Analyzer App Readiness Contract - 2026-06-13

## Executive Verdict

Verdict: GREEN for contract-only planning.

No app implementation is approved. No Streamlit/app files may be edited by this stage. Current analyzer, simulation, and candidate exports remain local-only and must keep `app_ready=no` or `app_read_allowed=no`.

## Potential Future UI Fields

If HQ later approves app integration, a rookie analyzer view may display:

- `analyzer_rank`
- `analyzer_group`
- `player`
- `position`
- `school`
- `pick_zone`
- `production_ready_status`
- `tag_summary`
- `source_confidence`
- `warnings`
- `blockers`
- `remaining_gaps`
- `best_pick_fit`
- `fit_1_03`
- `fit_1_04`
- `fit_2_04`
- `fit_2_08`
- `fit_5_04`
- `trade_down_signal`
- `emergency_stop_signal`
- `draft_only_if`
- `do_not_draft_if`
- `why_ranked_here`
- `why_not_higher`
- `why_not_lower`

These fields must be labeled as analyzer/review context, not production rankings or private scores.

## Warning Display Requirements

Any future UI must show warnings prominently:

- `rankable_with_warning` must never look like clean `ready`.
- `manual_review_required` must show the manual decision before the row can be used.
- `blocked` and `unavailable` rows must be visually non-actionable.
- Injury flags must remain visible.
- Source caveats must remain visible.
- Remaining gaps must remain visible.
- `1.03` must show trade-down/manual-review/no-player-cleared when unsupported.
- Emergency-stop rows must be obvious.

Warnings must not be hidden in collapsed-only UI by default.

## Feature Flag Recommendation

If app work is later approved, use a rookie-only feature flag:

- default: off;
- scope: rookie analyzer only;
- no effect on veteran models;
- no effect on production rankings;
- no effect on private scores;
- no probabilities or bands;
- easy rollback by disabling the flag.

Suggested flag name for a later approved task:

`ROOKIE_ANALYZER_V03_ENABLED`

This contract does not create the flag.

## Rollback Plan

Before future app implementation:

1. Confirm clean git status except explicitly allowed files.
2. Rebuild review board, shadow ranking, production candidate, analyzer, and simulation exports.
3. Record row counts and marker checks.
4. Confirm `data/` and `local_exports/` are not staged.

If implementation fails before commit:

1. Stop immediately.
2. Do not stage app files.
3. Disable or remove any local config change.
4. Re-run strict builders and direct harnesses.
5. Write a blocker checkpoint.

If a later implementation commit is rejected:

1. Revert only the approved app-integration commit.
2. Rebuild local exports.
3. Re-run strict builders and direct harnesses.
4. Confirm production rankings, private scores, probabilities, bands, outcome files, veteran files, `data/`, and `local_exports/` are clean/uncommitted.

## Files Likely Touched In Future App Integration

Only after explicit HQ approval, a future app implementation might touch:

- a new rookie analyzer adapter;
- a new rookie analyzer view or panel;
- tests for that adapter/view;
- a feature-flag/config file if explicitly named;
- docs that explain the UI behavior.

The future prompt must name exact files. If a file is not named, do not touch it.

## Files Not To Touch

Unless a later HQ-approved prompt explicitly names them, do not touch:

- Streamlit/app files;
- production ranking files;
- private-score files;
- formula files;
- probability files;
- band files;
- Outcome Columns HQ files;
- veteran outcome-head files;
- `data/`;
- committed `local_exports/`;
- active app-readable model artifacts.

## Tests Required Before Any Future App Integration

A future implementation must include tests that prove:

- the feature flag defaults off;
- analyzer output is not shown when the flag is off;
- warnings are visible when the flag is on;
- `rankable_with_warning` remains distinct from `ready`;
- `manual_review_required`, `blocked`, and `unavailable` remain visually distinct;
- `1.03` remains no-player-cleared/trade-down/manual-review when unsupported;
- no probabilities or bands are displayed;
- no veteran outcome-head output is imported;
- no production ranking/private-score files are modified;
- `data/` and `local_exports/` are not committed.

## Explicit Non-Approvals

This contract does not approve:

- app implementation;
- Streamlit wiring;
- production ranking replacement;
- private-score changes;
- rookie probabilities;
- rookie probability bands;
- veteran outcome heads;
- outcome columns;
- market/rank/projection/ADP/trade-value contamination.

## Next Gate

Stage 9 may proceed to final adversarial audit if validation remains GREEN.
