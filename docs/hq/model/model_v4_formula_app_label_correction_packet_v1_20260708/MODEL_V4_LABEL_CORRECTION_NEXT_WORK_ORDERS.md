# Model v4 Label Correction Next Work Orders

## Recommended Next Lane

`App-visible label correction implementation lane`

Objective:

Implement only human-approved display/status wording for the current Model v4 board.

Likely files:

- `app/pages/20_final_board_v1.py`
- `src/services/draft_day_app_v1_service.py`
- Possibly `docs/hq/rankings/statistic_analysis_v0_20260630/*` if docs-only wording is updated in the same lane.

Data needed:

- This label correction packet.
- Human approval for exact wording.

Metric to produce:

- App/display wording diff.
- Protected-path scan proving no score, rank, formula, source status, or sort behavior changed.

Gate required:

- Human approval.

Safe to run now:

- Yes, if strictly scoped to label wording and backed by tests/scans.

## Alternative Lane 1: Artifact Status-Field Correction Lane

Objective:

Update only review artifact status fields such as board-level status, row-level `allowed_use`, rebuild verification status, and production approval status.

Gate required:

- Human approval, because changing `allowed_use` fields can be mistaken for promotion.

Safe to run now:

- Only if no runtime app paths or ranking values are changed.

## Alternative Lane 2: Docs-Only Label / Status Update Lane

Objective:

Update older docs that still say "approved rankings artifact" or "approved NWR score" to the new review-board terminology.

Gate required:

- Light review.

Safe to run now:

- Yes, if docs-only.

## Not Recommended As Immediate Next Lane

### Production-Active Approval Lane

Blocked because:

- Historical accuracy remains unapproved.
- Exact historical replay remains blocked.
- Prior proxy did not beat prior-year finish overall.

### Historical Replay Benchmark Lane

Blocked because:

- Season-by-season Model v4 component receipts are not yet available.

### Formula Tuning Lane

Blocked because:

- This is a terminology/control-plane issue, not a model-improvement lane.
