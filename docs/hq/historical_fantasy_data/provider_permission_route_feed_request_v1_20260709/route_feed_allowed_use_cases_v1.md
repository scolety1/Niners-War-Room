# Route Feed Allowed Use Cases V1

## Current Use Status

No route feed is admitted. The current status for true `routes_run`, YPRR, and TPRR is production-blocked.

## Allowed In This Packet

Allowed:

- define minimum feed requirements
- prepare provider questions
- prepare email templates
- list contractable fallback providers
- define blocker checklist
- define future source-admission evidence requirements
- preserve no-production-use gate

Not allowed:

- scrape provider pages
- ingest provider route rows
- copy raw proprietary route data into repo
- calculate production YPRR or TPRR
- alter model formulas
- alter rankings
- alter app/runtime/UI behavior
- promote source truth
- approve name-only joins

## Future Internal Use Cases To Request From Provider

Ask providers to explicitly permit or deny:

1. internal storage of raw `routes_run`
2. internal historical research using raw `routes_run`
3. internal computation of derived YPRR and TPRR
4. internal display of raw route counts
5. internal display of derived YPRR/TPRR
6. production model use after separate NWR admission
7. production rankings use after separate NWR admission
8. audit/backtest use
9. cache retention for reproducibility
10. schema/version/checksum retention

## Use Cases To Keep Blocked Unless Provider Allows

Keep blocked unless explicitly licensed:

- public redistribution of raw route data
- public redistribution of derived route metrics
- committing raw route datasets to git
- sharing raw provider files outside authorized NWR users
- using private-account pages or paid exports outside contract terms
- model/ranking integration
- UI display

## Source Admission Gate

Even if a provider grants permission, NWR still needs a separate source-admission lane to verify:

- license terms
- retrieval reproducibility
- row grain
- field dictionary
- identity crosswalk
- season/position coverage
- missingness
- provenance/checksum support
- retention restrictions

Until that lane passes, true routes/YPRR/TPRR remain blocked.
