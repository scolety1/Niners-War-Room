# League History Confirmed Events Summary

## Current Confirmed Hard Events

No actual 2026 draft-log rows or Sleeper trade-history rows have been imported yet.

## Confirmed Evidence Inputs

| Evidence | Status | Notes |
| --- | --- | --- |
| LVE Rosters 061326 PDF attachment pointer | Confirmed source pointer | Treated as review evidence for roster/free-agent context. It is not proof of historical drop status by itself. |
| Gmail metadata search queue | Confirmed metadata exists | Metadata-only. Not actual event truth until reviewed against hard inputs. |
| Existing historical drop reconstruction | Existing repo artifact | Contains actual/inferred/proxy classes. Proxy and inferred rows require upgrade review before training use. |

## Not Confirmed

- Actual 2026 draft order and selections.
- Accepted Sleeper trade history rows.
- Final owner/team/Sleeper roster-ID mapping.
- Brian Thomas Jr. actual drop/unprotected/free-agent status from the ambiguous top-5 phrase.

## Model Use

All current league-history cleanup rows remain:

- `model_use_allowed=no`
- `training_allowed=no`
- `sensitivity_only=yes`

until hard evidence and a separate approval lane promote them.
