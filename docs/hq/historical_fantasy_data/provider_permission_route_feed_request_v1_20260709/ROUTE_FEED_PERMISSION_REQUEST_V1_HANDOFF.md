# Route Feed Permission Request V1 Handoff

## Verdict

`YELLOW_CONTRACTABLE_ROUTE_FEED_SPEC_READY_NO_SOURCE_ADMITTED`

The packet is ready for provider outreach. It does not admit any source.

## Provider Targets

Primary:

1. ESPN / Disney / ESPN Analytics
2. SumerSports

Fallback contractable leads:

- PFF
- SIS
- Sportradar
- commercial FTN
- FantasyPoints Data
- Establish The Run
- Rotoviz
- SportsDataIO
- NFL Next Gen Stats official access

## Minimum Feed Fields

Required:

- `routes_run`
- player ID
- player name
- team
- season
- position
- provider/feed name
- source update timestamp

Preferred:

- GSIS ID
- ESPN ID
- provider player ID
- week
- game ID
- opponent
- targets
- receiving yards
- targets per route run
- yards per route run
- eligibility threshold
- coverage/missingness flag
- checksum or row hash

## Admission Status

No source was admitted. Sumer and ESPN remain `YELLOW_ROUTE_DENOMINATOR_LEAD`. Fallback commercial providers are contractable leads only.

True routes/YPRR/TPRR remain production-blocked.

## Next Lane

Recommended next lane: `Provider Outreach Execution and Route Feed Response Review V1`.

That lane should:

1. Send provider requests.
2. Capture responses without storing raw provider route data.
3. Review license and allowed-use terms.
4. Decide whether any response justifies a source-admission lane.
5. Keep all route/YPRR/TPRR production use blocked unless a later admission packet passes.

## Do Not Do

- Do not scrape.
- Do not ingest route data.
- Do not use private-account pages.
- Do not copy raw provider rows into git.
- Do not calculate production YPRR or TPRR.
- Do not alter model/rankings/formula/UI/runtime/source-truth paths.
- Do not approve name-only joins.
