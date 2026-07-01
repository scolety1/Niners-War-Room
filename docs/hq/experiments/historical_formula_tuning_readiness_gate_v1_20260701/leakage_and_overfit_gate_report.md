# Leakage And Overfit Gate Report

Leakage status: controlled for a future limited review-only search.

Evidence:

- Feature season N and target season N+1 lag is preserved for every row.
- Target outcomes are carried as target-only fields.
- Source Contract V1 marks market, ADP, vendor, projection, rank, current-only context, route proxy families, and ambiguous red-zone attempts as blocked.
- V3 canonical columns do not contain routes, TPRR, YPRR, route proxies, `rz_att`, market, ADP, vendor, projection, injury, depth, or schedule fields.

Overfit controls for the next phase:

- Use the fixed split policy.
- Predeclare candidate families.
- Use validation for selection and holdout for final review.
- Require position-level stability.
- Report negative and mixed results.
- Do not keep searching after holdout failure.

This report does not approve production tuning.
