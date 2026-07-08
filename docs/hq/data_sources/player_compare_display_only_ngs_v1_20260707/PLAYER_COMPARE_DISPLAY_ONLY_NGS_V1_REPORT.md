# Player Compare Display-Only NGS Context V1

Verdict target: GREEN_PLAYER_COMPARE_DISPLAY_ONLY_NGS_IMPLEMENTED.

This lane adds the existing `REVIEW_ONLY_NGS_CONTEXT` gate to Player Compare. It reuses the curated NGS display fields from the Development Lab/Data Health lane and reads only tracked review artifacts.

Runtime behavior:

- Adds a `Review-only NGS Context` Player Compare tab.
- Shows side-by-side NGS values only when the selected player has a safe NWR player ID to GSIS bridge and a public NGS value in the tracked V2 feature panel.
- Shows unavailable/thresholded when the safe identity chain or public NGS coverage is missing.
- Does not convert missing NGS to zero.
- Does not create a winner, recommendation, verdict, boost, score, hidden sort, rank change, trade decision, draft decision, model feature, or source-truth promotion.

Blocked families remain blocked: PFR, ESPN QBR, FTN, PFF, ffopportunity UI use, routes, route participation, TPRR, YPRR, `rz_att`, exact PFF Elusive Rating, and `nwr_elusive_proxy_review_only`.
