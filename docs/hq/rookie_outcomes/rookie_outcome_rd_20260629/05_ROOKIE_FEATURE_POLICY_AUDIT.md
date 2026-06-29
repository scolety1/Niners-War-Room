# Rookie Feature Policy Audit - 2026-06-29

## Verdict

No rookie feature family is approved for active rookie outcome modeling in this lane.

Some features are useful review-only candidates, but every candidate needs either identity approval, source approval, label validation, or a model-input promotion gate.

## Machine-Readable Output

Created:

`docs/hq/rookie_outcomes/rookie_outcome_rd_20260629/rookie_feature_policy_matrix.csv`

Rows: 16 feature families.

## Classification Summary

| Policy Status | Count |
|---|---:|
| review_only | 9 |
| blocked | 6 |
| blocked_for_model | 1 |

## Review-Only Candidate Families

- draft capital
- age
- size / height / weight
- college production
- final-year production
- career production
- team strength / conference
- recruiting context
- NFL landing spot

These may become future review evidence only after their source and identity gates are satisfied.

## Blocked Families

- age-adjusted production
- market share / dominator
- transfer count / timeline
- early declare / experience
- combine / pro day
- rookie news / training camp

These are blocked because approved structured sources were not found or because the data would require vendor/news/scrape/manual rumor workflows.

## Market / ADP / DynastyProcess

Market, ADP, and DynastyProcess context may exist elsewhere as display-only context.

They remain blocked for:

- rookie outcome target truth
- model input
- hidden sort
- rookie probability generation
- trade value
- pick value

## CFBD Policy

CFBD production and identity rows remain:

- review-only
- not model input
- not training truth
- not source truth

`approved_by_human=false` prevents promotion.

## Missing Data Policy

Missing feature values must stay missing or `Not enough information`.

They must not become:

- zero
- average
- clean
- healthy
- low risk
- failed outcome

## Safe Conclusion

The best next step is not modeling. It is a human/source approval workflow for identity, draft capital, and historical labels.
