# Phase 3H Formula Review Patch Pass

This pass reviewed the Phase 3F sanity fixture dry run and the Phase 3G named-player audit. It keeps Model v4 review-only and applies only supported fixes.

## Summary

- Formula weight changes: none
- Formula config changes: none
- Active rankings changed: no
- Review-only status retained: yes
- V4 preview regenerated: yes
- Sanity fixture dry run rerun: yes
- Named-player review rerun: yes

## Classification

| Issue | Classification | Patch |
| --- | --- | --- |
| Elite WR tier checks below threshold | data issue / missing source | no formula patch |
| JSN top-tier check below threshold | data issue / missing source | no formula patch |
| Puka core-tier check below threshold | data issue / missing source | no formula patch |
| RB vs WR named-player balance review | data issue / missing source | no formula patch |
| Luther/Kaleb weak-confidence bridge rows | missing source | no formula patch |
| Positive warning rows displayed as negative drivers | receipt issue | patched report wording |
| QB suppression | acceptable model disagreement | no patch |
| TE suppression | acceptable model disagreement | no patch |
| Aging veteran dropoff | acceptable model disagreement | no patch |
| Market / league-rank separation | acceptable model disagreement | no patch |

## Patch Applied

The named-player report previously filled `top_negative_receipt_drivers` with warning/caution rows when there were no negative component contributions. That was technically useful but misleading. The report now explicitly says:

`No negative component contributions; caution rows: ...`

or:

`No negative component contributions; lowest contributions: ...`

This is a receipt/reporting fix only. It does not change component calculators, formula weights, preview scores, rankings, gates, or active app outputs.

## Why No Formula Patch

The Phase 3F and Phase 3G football concerns are not yet proven formula bugs. They trace to missing or incomplete evidence:

- true route metrics remain unavailable and proxy-only
- first-down projections are missing
- young year-one players lack NFL production / usage / snap evidence
- several elite WR checks are near threshold but receipt evidence does not prove a bad component weight

Changing weights here would be "make the rankings look right" tuning. The correct next step is to inspect source/receipt gaps for WR production, usage, projection, and route proxies before applying formula movement.

## Regenerated Outputs

- `local_exports/model_v4/review_only_latest/v4_preview_outputs.csv`
- `docs/model_v4/PHASE_3_SANITY_FIXTURE_DRY_RUN.csv`
- `docs/model_v4/PHASE_3_SANITY_FIXTURE_DRY_RUN.md`
- `docs/model_v4/PHASE_3_NAMED_PLAYER_REVIEW.csv`
- `docs/model_v4/PHASE_3_NAMED_PLAYER_REVIEW.md`

Current rerun status:

- Sanity fixtures: 29 total, 26 ready, 3 review, 0 blocked
- Named-player review: 19 matched, 0 missing, 2 inspection review rows
- Decision-ready unlocked: false
- Score changes applied: false

## Next Recommended Phase

Phase 3I should be a WR evidence audit before formula tuning:

- JSN, Puka, CeeDee, Tee, Brian Thomas Jr., Malik Nabers
- compare production, first-down fit, usage, projection, snap proxy, route-unavailable warnings
- decide whether the WR issue is data/source coverage, normalization, or a real formula imbalance
- no weight change until that audit produces a fixture-backed formula issue
