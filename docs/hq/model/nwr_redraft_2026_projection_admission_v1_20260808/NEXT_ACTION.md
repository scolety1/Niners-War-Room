# Next action

Owner must review and explicitly approve or reject:

- Model: `NWR_REDRAFT_2026_STATUS_FILTERED_PRIOR_SEASON_PERSISTENCE_V1`
- Candidate CSV: `CANDIDATE_PROJECTION_SNAPSHOT.csv`
- SHA-256: `94306d2934f6eb3ee6d1f4c2ee41428c84f8479fbea68c736ebd16c3c7780837`
- Governance candidate: `NWR_DATA_GOVERNANCE.json`

Approval must name the owner/approver and timestamp, and authorize conversion from
`GOVERNANCE_PENDING` / `MODEL_VALIDATED_REVIEW_ONLY` to the engine's admitted statuses. After that,
regenerate and hash the final CSV, bind an `APPROVED_FOR_REDRAFT_V1` receipt to the final hash, run
the installer, browser suite, independent adoption, and HQ gates.

For the owner's first real draft, also provide exact league team count, roster slots, scoring,
bonuses, draft type/slot, keepers, auction budget, and roster limits. No upcoming league placeholder
was treated as configured.
