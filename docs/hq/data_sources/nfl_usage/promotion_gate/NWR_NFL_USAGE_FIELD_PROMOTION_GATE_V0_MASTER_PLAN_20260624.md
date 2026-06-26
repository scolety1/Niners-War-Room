# NFL Usage Field Promotion Gate V0 Master Plan

Generated for the NFL Usage Evidence Layer V0 promotion/backtest gate.

## Scope

This lane classifies existing public NFL usage evidence into display-only candidates, research-only fields, blocked/licensed gaps, and future model-candidate possibilities. It does not wire fields into rankings, Drafting Mode, Player Compare, Trading Lab, Post-Draft, Cheat Sheets, hidden sorts, or model features.

## Promotion Statuses

- RESEARCH_ONLY
- DISPLAY_ONLY_CANDIDATE
- APPROVED_DISPLAY_ONLY_CONTEXT
- CANDIDATE_MODEL_FEATURE_PENDING_BACKTEST
- MODEL_CANDIDATE_PENDING_MANUAL_REVIEW
- BLOCKED_LICENSED_DATA_GAP
- BLOCKED_UNSAFE
- BACKTEST_BLOCKED_INSUFFICIENT_LABELS
- BACKTEST_BLOCKED_INSUFFICIENT_COVERAGE
- BACKTEST_FAILED_NON_ADDITIVE

## Allowed Decisions

- Mark safe factual usage counts as display-only context after coverage/leakage checks.
- Mark fields as research-only when semantics, coverage, or missingness remain unresolved.
- Mark true routes run, true TPRR, and true YPRR as licensed-data gaps until an exact approved source exists.
- Run coverage, leakage, and display-context diagnostics from committed summary artifacts.

## Banned Decisions

- No model input activation.
- No decision-page wiring.
- No Dynasty Rank, Final Board Rank, tier, frozen board, pinned snapshot, latest_candidate, or latest_approved mutation.
- No market, ADP, DynastyProcess, projection, vendor, or RotoWire target truth.
- No CFBD or college/prospect evidence in this lane.

## Target And Label Audit Requirements

Targets must be approved future outcome labels or timestamped league-state facts for the specific task. Display props, current rankings, market values, ADP, DynastyProcess, projections, inferred/proxy drops, and missing Outcome rows are not target truth.

## Feature Window Requirements

The default predictive window is season N features predicting season N+1 targets. In-season research requires explicit pre-target cutoffs. Full current-season stats cannot predict the same full-season target.

## Leakage Checks

The gate blocks future stats, post-cutoff updates, market/rank/projection fields, target labels as features, route-proxy overclaims, and denominator drift.

## Display-Only Approval Requirements

Display-only context must be factual or clearly derived, have safe coverage status, carry visible caveats where needed, and retain `model_input_allowed=no` and `app_wiring_allowed=no`.

## Model-Candidate Requirements

No field becomes a model input in this lane. A future model-candidate proposal requires historical coverage, walk-forward ablation, baseline comparison, missingness sensitivity, manual review, and a separate integration gate.

## CFBD Separation

CFBD belongs to a separate College/Rookie Evidence Layer lane. This NFL usage gate uses only pro/NFL usage evidence after players enter the league.

## Stop Conditions

Stop and fail closed if target labels are insufficient, coverage is insufficient, leakage checks fail, raw data would be tracked, or any app/model/rank/source-truth file would be mutated outside the hidden review page.

## Validation Checklist

- CSV load validation.
- Focused pytest.
- Ruff on touched Python.
- Python compile on touched Python.
- `git diff --check`.
- Confirm no raw/shared/local/runtime files tracked.
- Confirm no CFBD files changed.
- Confirm protected board/source-truth/model files unchanged.

## Commit And Push Policy

Commit and push only GREEN/YELLOW-safe artifacts with blocked behavior documented and all flags off.
