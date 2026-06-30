# NFLVerse Player Context Guardrail Report

Guardrail flags valid: `true`
`ff_rankings` blocked and unused: `true`

No app behavior, Rankings behavior, Player Compare behavior, Trading Lab behavior, model logic, rank logic, source truth, hidden sort, trade value, pick value, `latest_candidate`, or `latest_approved` is changed by this lane.

The service may read approved local NFLVerse cache only while building tracked derived docs artifacts. App pages must consume the tracked CSVs or a repo-backed service layer, not raw shared-cache files.

## Approved Identity Binding Apply - 2026-06-30

Applied rows: `41`
Remaining gated rows: `13`

This apply changed only tracked docs/CSV review artifacts. It did not change app pages, Rankings, Player Compare, Trading Lab, Development Lab, Draft Room, model logic, rank logic, source truth, hidden sort, trade value, pick value, latest pointers, frozen board artifacts, runtime JSON, raw/shared/cache/local_exports, or secrets.

Kentrel Bullock and Jamal Haynes remain gated as `Not enough information` / needs binding review. Non-approved, pending, keep-blocked, ambiguous, or unbound rows were not exposed as safe context.
