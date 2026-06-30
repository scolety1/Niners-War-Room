# Label Source Partition Policy

Outcome labels and display comparisons are separated by family.

## Outcome V2 Exact Verified First-Down Labels

These are the current historical label/evaluation target for drafted-only review artifacts. They remain review-only unless a later gate explicitly promotes them. They may be used to audit historical outcome windows, but they are not input features.

## model_v4 RotoWire-Derived Labels

The model_v4 label path is local/vendor-derived display comparison material. It is not source truth, model input, or training truth. It remains display-only and local-path dependent.

## nflverse player_stats-Derived Labels

This is a future sidecar comparison candidate only. Because the refresh-health packet has not landed on the target branch, this family is `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN`. Even after refresh-health, player_stats-derived labels need parity checks and an explicit label-spec gate.

## CFBD

CFBD production is not NFL outcome truth. It remains identity/college context only and requires human-approved identity links before any stronger use.

## Missing Labels and Incomplete Windows

Missing labels are `Not enough information`. Incomplete future windows are right-censored. Neither becomes a failure, zero, false, no-hit label, or active rookie probability.
