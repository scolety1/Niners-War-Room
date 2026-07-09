# Formula Gauntlet Data Readiness Gate V1

## Verdict

`YELLOW_FORMULA_GAUNTLET_DATA_READY_FOR_EVIDENCE_INGESTION_ONLY`

## Clear Answer

The current NWR data is not ready for Formula Gauntlet formula tournaments. It is ready for review-only evidence ingestion, source/use-gate mapping, and guardrail design. Exact Model v4 historical replay is still blocked, no partial Model v4 score was predeclared or invented, and the partial benchmark showed that the best non-PYF component signals did not beat PYF in QB, RB, WR, or TE.

Readiness level:

`READY_FOR_COMPONENT_SIGNAL_INGESTION_ONLY`

Formula Gauntlet should remain blocked from challenger tournaments, formula search, tuning, weight optimization, model promotion, or production-label claims until exact or approved historical receipt coverage improves and candidate signals can beat the PYF anchor under leakage-safe tests.

## Evidence Summary

| Evidence Layer | Current Finding | Formula Gauntlet Impact |
| --- | --- | --- |
| Exact current-board rebuild | Current app-visible board hash reproduced exactly; `checkpoint_review_score` and `nwr_dynasty_score` reconciled for the current board. | Proves current-board reproducibility only. It does not prove historical accuracy or tournament readiness. |
| Historical component receipts | `42,933` review-only partial receipt rows exist for seasons `2013-2025` across QB/RB/WR/TE. | Supports component signal inventory and guardrail design, not exact Model v4 replay. |
| Exact historical replay | Still blocked by missing season-by-season `checkpoint_review_score`, `position_specific_review_score`, lifecycle/age/role/confidence receipts, and WR/QB v2 overlay receipts. | Blocks exact Model v4 tournaments and production accuracy claims. |
| Partial historical replay benchmark | `5,518` rows, `83` review-only partial component-source signals, `0` leakage guardrail errors. | Useful evidence, but not enough for formula tournaments because no score was predeclared and non-PYF signals did not beat PYF. |
| PYF comparison | Best non-PYF signal failed to beat PYF in all positions. | PYF must remain the champion anchor baseline. |
| Miss patterns | Prior-production decline false positives: `572` rows (`10.4%`); sparse-history rows: `1,453` rows (`26.3%`). | Any future Gauntlet must include decline and sparse-history guardrails before candidate formulas can be trusted. |

## Exact Model v4 Replay Status

Exact Model v4 historical replay is not available. The current-board rebuild proves the current hash-pinned candidate board can be reproduced, but the historical season-by-season receipt chain remains missing. Formula Gauntlet must not treat Model v4 as historically replayed.

The missing exact replay chain includes:

- `checkpoint_review_score`
- `position_specific_review_score`
- lifecycle, age, role, and confidence receipts
- WR/QB v2 candidate-overlay receipts
- exact historical `nwr_dynasty_score` and rank receipts

## Benchmark Dataset Sufficiency

The current benchmark evidence is sufficient for:

- Component-level signal review.
- Evidence ingestion into the Formula Gauntlet backlog.
- Baseline and guardrail design.
- Miss-pattern taxonomy work.

The current benchmark evidence is not sufficient for:

- Full formula tournaments.
- Position-scoped formula tournaments.
- Candidate weight optimization.
- Champion formula selection.
- Production-active model claims.
- Source promotion.

The `5,518` benchmark rows and `42,933` partial receipt rows are valuable, but they are partial/proxy-safe, review-only receipts. They do not contain an approved formula score and do not cover the exact historical Model v4 checkpoint chain.

## Label Quality

The available benchmark labels are usable for review-only component signal tests:

- `next_nwr_points`
- `next_nwr_ppg`
- `next_position_finish`
- `startable_hit`
- `startable_bucket`

They are not enough by themselves to authorize formula tournaments because the main blocker is not label absence. The blocker is the missing exact historical formula receipt chain plus review-only source admission status for many inputs.

Sparse-history and rookie-like slices remain especially caveated. Sparse-history rows accounted for `1,453` rows (`26.3%`) in the partial replay benchmark, so Formula Gauntlet must not optimize a formula without explicit sparse-history gates.

## PYF Anchor Decision

PYF must remain the anchor baseline. In the accepted partial replay benchmark, the best non-PYF component signal did not beat PYF in any position:

| Position | Best Non-PYF Signal | Spearman | PYF Baseline | Beat PYF? |
| --- | --- | ---: | ---: | --- |
| QB | `prior_passing_yards` | `0.683` | `0.712` | No |
| RB | `prior_rushing_yards` | `0.628` | `0.633` | No |
| WR | `prior_receiving_yards` | `0.683` | `0.691` | No |
| TE | `prior_receiving_yards` | `0.691` | `0.701` | No |

Future candidates must be compared against PYF overall, by position, and on low-games/sparse-history slices. A candidate that fails PYF may still remain review-only evidence, but it must not be promoted or treated as an improvement.

## Formula Gauntlet Readiness Level

`READY_FOR_COMPONENT_SIGNAL_INGESTION_ONLY`

Allowed now:

- Import accepted evidence summaries into the Formula Gauntlet backlog.
- Design tournament guardrails.
- Define minimum data requirements.
- Design PYF comparison contracts.
- Design sparse-history and decline false-positive checks.

Blocked now:

- Full formula tournaments.
- Position-scoped candidate formula tournaments.
- Broad formula search.
- Weight tuning or optimization.
- Candidate champion selection.
- Formula activation.
- Production app/ranking/source changes.

## Minimum Requirements Before Full Formula Gauntlet

Before full Formula Gauntlet can safely run, NWR needs:

1. Exact or approved historical component receipts for the Model v4-like score chain.
2. Season-by-season `checkpoint_review_score` and `position_specific_review_score` receipts or a separate approved challenger-score contract.
3. Source-gated, decision-date-safe input families with explicit model-use or review-only tournament permission.
4. PYF baseline as required champion comparator.
5. Position-level coverage thresholds for QB/RB/WR/TE.
6. Sparse-history, rookie, low-games, injury/availability, and prior-production-decline guardrails.
7. Leakage checks proving no current/future data enters historical inputs.
8. Identity-join proof and no name-only joins.
9. A no-promotion rule: tournament results remain review-only until a separate human approval lane.

## Recommendation

Recommended next lane:

`Formula Gauntlet Evidence Ingestion and Guardrail Contract V1`

That lane should ingest the partial replay evidence into the dedicated Formula Gauntlet chat as context, create a guardrail contract, and prepare future tournament criteria without running a tournament.

Do not run a Formula Gauntlet tournament yet.
