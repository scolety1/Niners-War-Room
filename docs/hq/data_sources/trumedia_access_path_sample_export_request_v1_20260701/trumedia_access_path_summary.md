# TruMedia Access Path Summary

Verdict: `YELLOW_ACCESS_POSSIBLE_LICENSE_REQUIRED_SAMPLE_EXPORT_REQUEST_ONLY`

TruMedia access appears possible only through a legitimate enterprise/team/media route, not a public self-service data feed. NWR should contact TruMedia and ask about `NFL Advanced Analytics`, `NFL API`, the data warehouse or an evaluation-only partner export. No TruMedia system should be accessed, no login should be attempted, and no API key should be requested or used until TruMedia explicitly approves access and rights.

## Core Questions

| Question | Current answer |
|---|---|
| Is access likely enterprise/team/media-only? | Yes. TruMedia publicly positions its products for teams, media clients, and partners. Its terms require a Customer License or written authorization before using the services. |
| Is there a public signup, trial, demo, or contact route? | No public self-service signup was found. A public contact path exists: `info@trumedianetworks.com`; TruMedia's teams page says demo/trial inquiries should be emailed. |
| What product should NWR ask about? | Ask about `NFL Advanced Analytics` plus `NFL API` or a data warehouse/partner export. `NFL Core` may be useful for play-by-play, but the desired route/tracking/coverage fields are more likely tied to Advanced Analytics, API, warehouse, or partner data. |
| Does TruMedia likely expose routes/run, TPRR, YPRR, alignment, separation, tracking, coverage, matchup, and play tags? | Likely for many of these families, but not admitted. TruMedia says football data includes player tracking, tagging, advanced modeling, third-party data, UI metrics, and API access. Public media examples also cite TruMedia for routes, yards per route, route type, alignment, coverage, and target separation. Exact exportable NFL fields must be confirmed by TruMedia. |
| Can exports include GSIS/PFF/Sleeper IDs? | GSIS and PFF IDs appear plausible through a partner path, but not confirmed for TruMedia NFL exports. SkillCorner publicly describes American football data delivered through API or TruMedia front-end integration and formatted with PFF and GSIS IDs. Sleeper IDs are not indicated publicly and should be requested only as an optional join/crosswalk question. |
| What seasons and grains are available? | Public TruMedia pages say NFL Core compares teams and players across seasons; public media references cite TruMedia databases reaching back to 2000 for some stats; SkillCorner cites 10 seasons for its American football data. NFL-specific export grains are unknown. Ask for play, player-play, player-game, player-week, and player-season availability. |
| Can NWR store derived artifacts locally? | Unknown. This must be explicitly licensed. TruMedia's public terms restrict use of content files unless documentation or a Customer License allows it, and the warehouse page references access controls tied to third-party licensing rights. |
| Can NWR use the data for private fantasy/dynasty formula research? | Unknown and not safe to assume. Ask TruMedia for written approval covering private, non-public, non-commercial fantasy/dynasty formula research, including derived artifacts and no redistribution. |
| What sample export is enough for source admission? | A rights-cleared sample should include a schema dictionary, license/use note, identity columns, zero/missing semantics, as-of timestamp, and enough rows across player-week and player-play grains to test coverage, joins, and route denominators. Recommended minimum: two recent full regular seasons of player-week pass-catcher usage plus 8 representative games of player-play route/coverage/tracking detail. |
| What fields should be requested first? | Player IDs, season/week/game/play IDs, routes run, route type if available, targets, receiving yards, air yards/depth, YAC, alignment, snap participation, coverage type, matchup/defender fields, separation/tracking fields if available, red-zone/inside-10/inside-5 context, explicit zero/missing semantics, export timestamp, and data license/use note. |

## Likely Access Route

1. Email `info@trumedianetworks.com` with NWR's evaluation use case.
2. Ask whether NWR should evaluate `NFL Advanced Analytics`, `NFL API`, the data warehouse, or a partner-export workflow.
3. Request a demo or evaluation call before any API credentials.
4. Request a sample export as CSV/Parquet with a schema dictionary and written use rights.
5. Keep all resulting data `review_only` until a separate NWR source-admission lane approves the source.

## Non-Admission Statement

This packet does not admit TruMedia as source truth. It does not approve model use, training use, rankings, app wiring, hidden sort, recommendations, formula tuning, or production behavior.

