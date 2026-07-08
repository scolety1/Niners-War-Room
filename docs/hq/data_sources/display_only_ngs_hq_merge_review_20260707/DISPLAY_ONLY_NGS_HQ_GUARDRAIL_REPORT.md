# Display-Only NGS HQ Guardrail Report

Guardrail result: PASS

Confirmed preserved:

- No production rankings formula change.
- No default rankings sort change.
- No hidden sort.
- No recommendation, winner, verdict, boost, trade decision, or draft decision logic.
- No NGS model approval.
- No NGS source-truth promotion.
- No PFR, ESPN QBR, FTN, PFF, ffopportunity, routes, route participation, TPRR, YPRR, rz_att, exact PFF Elusive Rating, or nwr_elusive_proxy_review_only UI activation.
- No Trading Lab, Live Draft / Mock Draft, or Rankings preset changes.
- Identity-review rows remain hidden by default.
- Name-fallback rows are not approved.
- Missing or thresholded NGS values are not zero-forced.

Review notes:

- Guardrail scan hits in runtime were negative labels such as "not used in rankings" and "do not create a winner, recommendation, verdict, boost, score, hidden sort, ranking change, trade decision, or draft decision."
- Blocked metric scan hits in docs are blocked-list documentation and do not activate those families.
- Data Health mentions blocked families only as blocked/deferred context.
