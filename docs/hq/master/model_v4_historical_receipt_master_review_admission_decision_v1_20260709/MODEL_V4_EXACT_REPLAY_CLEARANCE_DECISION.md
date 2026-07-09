# Model v4 Exact Replay Clearance Decision

## Decision

Exact Model v4 historical replay is not cleared.

## Reason

The freeze/schema lane validated current-board equivalents, current-only sidecars, audit summaries, and partial/proxy historical coverage artifacts. It did not produce season-by-season exact historical equivalents for:

- `checkpoint_review_score`
- `position_specific_review_score`
- lifecycle/age/role/confidence receipts
- WR/QB v2 candidate overlay receipt chain
- exact transform/weight receipt chain
- route/YPRR/TPRR exact receipts
- return scoring receipts
- `shadow_model_v2_metrics`

## Allowed Use

The frozen artifacts may be used as evidence to describe current-board receipt semantics and to design future regeneration or component-test contracts.

## Not Allowed

- Exact Model v4 replay benchmark.
- Production accuracy claim.
- Production/model-use approval.
- Ranking integration.
- Treating current-only artifacts as historical receipts.
