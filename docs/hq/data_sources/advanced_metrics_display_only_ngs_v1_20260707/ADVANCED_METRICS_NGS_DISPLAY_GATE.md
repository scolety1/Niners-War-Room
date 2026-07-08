# Advanced Metrics NGS Display Gate

NGS display is allowed only as review-only context.

Required gate language:

`Review-only NGS context. Not model input. Not source truth. Not rankings. Public NGS thresholding may hide low-volume players.`

Display rules:

- Use only safe GSIS/nflverse-ID joined rows.
- Hide identity-review rows by default.
- Never approve name-only fallback joins.
- Never sort the main board or rankings by NGS.
- Never show score, grade, recommendation, verdict, boost, trade advice, draft advice, or pick advice.
- Show sample size or coverage when available.
- Do not include PFR, ESPN QBR, FTN, PFF, ffopportunity, routes, TPRR, YPRR, `rz_att`, or elusive proxy in this NGS display scope.
