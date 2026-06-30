# Rankings NFLVerse Status Copy Refresh

Verdict target: `GREEN_RANKINGS_NFLVERSE_STATUS_COPY_REFRESHED`

This lane refreshes only the Dynasty Rankings Dataset Refresh / Outcome Status
panel copy after the tracked NFLVerse player context display artifact rebuild.

## Updated Status

- Dataset-level NFLVerse refresh-health remains GREEN through the centralized
  tracked refresh-health contract.
- The row-level NFLVerse player context display artifact exists and is rebuilt.
- Artifact rows: 294.
- Safe display rows: 281.
- Gated rows: 13.
- Newly activated bound rows from the rebuild: 41.
- The remaining 13 rows stay gated as Needs identity review / Not enough
  information.

## Guardrails

NFLVerse context remains display-only/review-only. This lane does not use
NFLVerse for Dynasty Rank, model input, source truth, hidden sort, trade value,
pick value, recommendations, injury risk, or medical projection.

Missing or gated values remain `Not enough information`; they are not converted
to healthy, clean, zero, no-role, approved, or low-risk values.

No NFLVerse artifact, rank artifact, frozen board artifact, pinned snapshot,
latest candidate, latest approved, model logic, route, table sort, or filter
logic was changed.
