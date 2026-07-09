# Routes Run Identity Crosswalk Risk V1

## Summary

Identity risk remains a hard admission gate. A route denominator source cannot be admitted through name-only joins because route counts would be used to derive YPRR and TPRR if later admitted.

## Sumer Identity Risk

Observed identity field:

- `sumerPlayerId`

Risk status: medium/high.

Why:

- `sumerPlayerId` appears to be stable enough to be useful as a provider key.
- No Sumer ID dictionary or public crosswalk to GSIS, ESPN ID, nflverse ID, or NWR canonical ID was found.
- No team/week/game-level identity contract was found.
- Name/team/season matching is not approved.

Sumer could become identity-safe only if a future lane receives an official ID dictionary or builds a verified crosswalk against admitted IDs with collision and missingness audits.

## ESPN Identity Risk

Observed identity fields:

- `gsis_id`
- `dot_com_id`

Risk status: low/medium if permission is obtained.

Why:

- GSIS IDs are directly useful for NWR joins when the source itself is licensed/admitted.
- ESPN dot-com IDs provide a secondary provider identifier.
- The current blocker is not identity shape; it is permission, documented feed status, row grain, and eligibility/missingness.

## Name-Only Join Gate

Name-only joins remain explicitly blocked for all route-denominator work. A future admission lane must include:

- exact provider ID field documentation
- crosswalk to NWR canonical identity
- duplicate-name and same-season collision audit
- team/season validation against admitted roster or receiving data
- unmatched player report by season and position

## Current Identity Verdict

ESPN has the better identity shape. Sumer has a plausible provider ID but needs a crosswalk. Neither source is admitted; identity-readiness does not override licensing and reproducibility blockers.
