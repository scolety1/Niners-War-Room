# Routes Run Hardening V1 Handoff

## Verdict

`YELLOW_ROUTE_DENOMINATOR_LEADS_REMAIN_BLOCKED`

No source reached `GREEN_ROUTE_DENOMINATOR_CANDIDATE`.

## Source Status

| Source | Status | Why |
| --- | --- | --- |
| SumerSports WR/TE | `YELLOW_ROUTE_DENOMINATOR_LEAD` | Visible route columns and 2022-2025 payload fields, but no permission-safe API/export/license or NWR ID crosswalk. |
| SumerSports RB | `YELLOW_ROUTE_DENOMINATOR_LEAD` | Route fields observed in payload for 2022-2025, but not visible and not confirmed as supported/licensable. |
| ESPN Receiver Scores | `YELLOW_ROUTE_DENOMINATOR_LEAD` | Actual `rtm_routes` and GSIS IDs observed for 2017-2025, but client object is undocumented and Disney terms block dataset extraction without permission. |

## Production Gate

Do not use any output from this packet as production source truth.

Still blocked:

- true `routes_run`
- YPRR from recovered route counts
- TPRR from recovered route counts
- model/rankings/formula use
- app/runtime/UI use
- source-truth promotion
- hidden sort/recommendation/verdict/boost logic

## Recommended Next Lane

Run `Provider Permission and Contractable Route Feed Request V1`.

Priority order:

1. ESPN/Disney route feed permission because `gsis_id` makes identity risk lower if permission is granted.
2. SumerSports route feed permission because WR/TE/RB route payload fields appear to exist for 2022-2025, including RB payload-only fields.

Required next-lane artifacts:

1. Provider contact/permission memo.
2. Terms/license analysis by counsel or designated source-admission owner.
3. Supported feed/export/API proof.
4. Field dictionary.
5. Identity crosswalk audit.
6. Missingness and eligibility audit.
7. Source-retention and reproducibility policy.
8. Explicit no-production-use gate until admitted.

## Carry-Forward Caveats

- Sumer WR/TE denominators are closer to admission technically, but not legally or operationally.
- Sumer RB denominator is a lead, not a safe feed, because fields are payload-only.
- ESPN is closer on identity and historical depth, but blocked by terms and undocumented-feed status.
- True routes/YPRR/TPRR remain production-blocked.
