# Player Compare Display-Only NGS Runtime Gate

Gate: `REVIEW_ONLY_NGS_CONTEXT`.

Allowed:

- Side-by-side public NGS context for selected Player Compare rows.
- Safe identity chain only: selected NWR `player_id` to tracked NFLVerse player-context artifact to GSIS ID to tracked V2 NGS feature panel.
- Unavailable/thresholded display when identity or public NGS thresholding blocks a value.

Blocked:

- Rankings formula changes.
- Default sort or hidden sort.
- Winner, recommendation, verdict, boost, score, trade decision, or draft decision.
- Model-approved or source-truth language.
- Name-fallback identity approval.
- PFR, ESPN QBR, FTN, PFF, ffopportunity UI use, routes, TPRR, YPRR, `rz_att`, exact PFF Elusive Rating, or `nwr_elusive_proxy_review_only`.
