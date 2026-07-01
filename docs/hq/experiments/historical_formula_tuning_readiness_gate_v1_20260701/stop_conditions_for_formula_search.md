# Stop Conditions For Formula Search

Stop the next candidate-search lane immediately if any condition occurs:

- V3 substrate row count differs from 5,518 without a new HQ-approved artifact.
- N to N+1 lag fails for any row.
- Identity joins are no longer complete.
- A candidate uses a blocked feature family.
- A candidate fills null-fenced missing values with zero.
- A candidate uses current-only roster/status/injury/depth/schedule context.
- A candidate uses market, ADP, vendor, projection, rank, hidden-sort, or recommendation fields as source truth.
- A candidate uses routes, TPRR, YPRR, route proxies, red-zone sidecar fields, or `rz_att`.
- A candidate requires production app/model/rank/service/runtime edits.
- Validation improves but holdout fails position-specific hit-rate or rank stability.
- Any artifact implies production approval.

Stopping means return to HQ with a blocker report; do not continue searching around the failed guardrail.
