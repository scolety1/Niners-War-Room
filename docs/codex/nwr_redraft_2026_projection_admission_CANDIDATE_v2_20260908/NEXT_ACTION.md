# Next action

Owner must review and explicitly approve or reject:

- Model: `NWR_REDRAFT_2026_STATUS_FILTERED_PRIOR_SEASON_PERSISTENCE_V1`
- Candidate CSV: `CANDIDATE_PROJECTION_SNAPSHOT.csv`
- SHA-256: `15001fc47cc0d039a3ffdd8211f16aae44ca5bb1136fa9e9919ef6ab4309d1c9`
- Governance candidate: `NWR_DATA_GOVERNANCE.json`

Approval must name the owner/approver and timestamp, and authorize conversion from
`GOVERNANCE_PENDING` / `MODEL_VALIDATED_REVIEW_ONLY` to the engine's admitted statuses. After that,
regenerate and hash the final CSV, bind an `APPROVED_FOR_REDRAFT_V1` receipt to the final hash, run
the installer, browser suite, independent adoption, and HQ gates.

For the owner's first real draft, also provide exact league team count, roster slots, scoring,
bonuses, draft type/slot, keepers, auction budget, and roster limits. No upcoming league placeholder
was treated as configured.
