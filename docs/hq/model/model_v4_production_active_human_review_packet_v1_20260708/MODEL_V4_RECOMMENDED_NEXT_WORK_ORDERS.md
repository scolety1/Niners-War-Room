# Model v4 Recommended Next Work Orders

## Single Safest Next Lane

`Formula/app-label correction packet`

Objective: decide whether the app-visible board label should be corrected to a precise candidate/review-only label now that the board is exactly reproducible.

Allowed scope:
- Review-only label/status documentation.
- Tests or guardrail checks proving no score, rank, formula, default sort, hidden sort, source status, recommendation, draft/trade logic, or app behavior changes beyond explicitly approved label wording.

Blocked scope:
- Production-active approval.
- Formula tuning.
- Ranking output changes.
- Source promotion.
- Benchmarking.

Gate required: human approval before any app-visible wording change.

Safe to run now: yes, if kept strictly label/status-review scoped.

## Work Order 2: Historical Component Receipt Backfill

Objective: create season-by-season, decision-date-safe Model v4 component receipts for historical replay.

Files likely involved:
- Prior replay substrate packet.
- Current exact rebuild receipt chain.
- Historical fantasy finish foundation docs.
- Source-gate docs for every component.

Data needed:
- Historical component rows.
- Historical lifecycle/age sidecars.
- Historical confidence/missingness matrices.
- Historical first-down and return scoring receipts.

Metric to produce:
- Receipt coverage by season, position, component, and source-gate status.

Gate required:
- Source-admission and leakage-safety review.

Safe to run now:
- Partially; receipt mapping is safe, but backfill needs careful source-gate review.

## Work Order 3: Exact Historical Replay Benchmark

Objective: measure the exact Model v4 formula against historical outcomes only after receipt coverage is sufficient.

Files likely involved:
- Historical component receipt backfill output.
- Production Rankings Backtest V1 harness.
- Historical finish labels.

Data needed:
- Decision-date-safe Y-1 inputs.
- Next-season labels.
- Position-specific thresholds for the 10-team 1QB non-PPR first-down league.

Metric to produce:
- Rank MAE, RMSE, Spearman, Top-N hit rates, startable precision, position-level results, and prior-year baseline comparison.

Gate required:
- Leakage review and human approval.

Safe to run now:
- No. Exact replay remains blocked until historical receipts exist.

## Work Order 4: Production-Active Approval Lane

Objective: decide whether to promote a reproducible and historically evaluated board or formula to production-active status.

Files likely involved:
- Human review packet.
- Exact historical replay benchmark.
- Source-gate approvals.
- App-label and ranking-surface status docs.

Data needed:
- Exact replay benchmark results.
- Source gate approvals.
- Human approval record.

Metric to produce:
- Production readiness decision with explicit approve/deny/defer status.

Gate required:
- Human approval.

Safe to run now:
- No. It should wait for at least app-label review and preferably exact historical replay.

## Work Order 5: Reproducible Board Generation Policy

Objective: require future current-board builds to preserve inputs, hashes, source manifests, receipt chains, and sidecar caveat files.

Files likely involved:
- Model v4 rebuild docs.
- Source receipt-chain standard docs.
- Current board generation docs.

Data needed:
- Current exact rebuild source trace.
- Required receipt field standards.

Metric to produce:
- Future board build completeness checklist and pass/fail manifest.

Gate required:
- Human review for operational policy adoption.

Safe to run now:
- Yes, if docs-only.
