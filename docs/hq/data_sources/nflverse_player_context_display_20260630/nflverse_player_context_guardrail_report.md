# NFLVerse Player Context Guardrail Report

Guardrail flags valid: `true`
`ff_rankings` blocked and unused: `true`

No app behavior, Rankings behavior, Player Compare behavior, Trading Lab behavior, model logic, rank logic, source truth, hidden sort, trade value, pick value, `latest_candidate`, or `latest_approved` is changed by this lane.

The service may read approved local NFLVerse cache only while building tracked derived docs artifacts. App pages must consume the tracked CSVs or a repo-backed service layer, not raw shared-cache files.