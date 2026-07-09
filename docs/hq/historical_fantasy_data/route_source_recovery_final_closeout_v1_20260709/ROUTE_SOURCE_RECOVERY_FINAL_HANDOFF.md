# Route Source Recovery Final Handoff

## Verdict

`YELLOW_ROUTE_SOURCE_RECOVERY_CLOSED_PENDING_PROVIDER_PERMISSION_NO_SOURCE_ADMITTED`

The route/YPRR/TPRR recovery lane is closed pending provider permission, paid license, or a new legal public source. No source was admitted.

## Final Status

- `routes_run`: not obtained in admissible form.
- true YPRR: blocked.
- true TPRR: blocked.
- GREEN route denominator candidates: 0.
- Source admissions: 0.
- Confirmed outreach sent: no.
- Confirmed provider response captured: no.

## Preserved Leads

Best preserved leads:

1. ESPN / Disney / ESPN Analytics because prior probes found `rtm_routes`-style route fields and stable identity fields, but permission/export/API gates remain unresolved.
2. SumerSports because WR/TE route columns are visible and prior probes found route-like fields, including RB payload-only signals, but permission/export/API and identity gates remain unresolved.
3. PlayerProfiler public pages as RB display leads only, not aggregate data.
4. Commercial or official providers as contractable leads only: PFF, SIS, Sportradar, commercial FTN, FantasyPoints Data, ETR, Rotoviz, SportsDataIO, and official NFL NGS access.

## What Remains Blocked

- public-safe `routes_run`
- true YPRR
- true TPRR
- production model or formula use
- rankings use
- app/runtime/UI use
- source registry/source-truth promotion
- proxy relabeling as true routes
- name-only joins as approved identity

## Reopen Conditions

Reopen only if:

1. a provider grants usable permission or license,
2. a stable legal API/export is found,
3. a separate source-admission lane validates identity, coverage, reproducibility, missingness, provenance, and decision-date safety.

## Handoff Instruction

Do not continue broad route searching. The next meaningful work is either provider-response review, contract/licensing review, or source-admission validation if a legal route feed appears.
