# Formula Gauntlet No-Code Tournament Design Scaffold V1

## Verdict

`GREEN_FORMULA_GAUNTLET_DESIGN_SCAFFOLD_READY`

## Clear Answer

The Formula Gauntlet framework is now scaffolded as a no-code tournament design contract, but no tournament is allowed yet. The current accepted readiness level remains `READY_FOR_COMPONENT_SIGNAL_INGESTION_ONLY`, so this packet defines future tournament classes, required gates, input contracts, reporting schemas, advancement rules, and blocked actions without running any formula search, tuning, scoring, optimization, or ranking change.

## Current HQ Baseline

- Remote branch: `origin/work/hq-parallel-control`
- Current remote HQ head verified at lane start: `b25157c1dfe065f4d1f181c8e26a32fddce5cd66`
- Remote movement inspected from prior readiness context head `07864a51c83a7befe7a0cc5221c235a41063bd88` to current head.
- Movement result: docs-only route-feed provider outreach review under `docs/hq/historical_fantasy_data/provider_outreach_route_feed_response_review_v1_20260709/`.
- Dangerous path conflicts found: none.

## What This Packet Does

This packet prepares Formula Gauntlet for a future moment when Data Hygiene and Master HQ clear the required data/source/receipt gates. It defines:

- Tournament classes that may exist later.
- Required labels, receipts, baselines, coverage, leakage checks, and missingness checks.
- Output schemas for future tournament scorecards.
- Advancement rules.
- Blocked-action policy.
- Data Hygiene dependencies.
- Master HQ approval gates.

## What This Packet Does Not Do

- No formula tournament was run.
- No weights were tuned.
- No candidate formula was created.
- No winner was selected.
- No source was promoted.
- No rankings changed.
- No model/app/runtime behavior changed.
- No production accuracy claim was made.

## Tournament Classes Defined

| Class | Current Status | Future Purpose |
| --- | --- | --- |
| PYF anchor comparison | Design only | Ensure every candidate is compared against prior-year finish / prior-year points. |
| Position-specific challenger | Design only | Allow separate QB/RB/WR/TE review after source and label gates clear. |
| Sparse-history guardrail challenger | Design only | Test low-history and low-games harm before advancement. |
| Low-games failure-mode challenger | Design only | Prevent candidates from hiding injury/availability and partial-season failure. |
| Review-only component signal tournament | Design only | Compare admitted review-only components only after Master HQ opens execution. |
| Route/YPRR/TPRR tournament | Blocked future class | Requires Route Recovery / source admission and denominator proof. |
| Exact Model v4 replay tournament | Blocked future class | Requires exact historical Model v4 receipt chain recovery. |

## Data Hygiene Dependencies

Formula Gauntlet remains dependent on Data Hygiene for:

1. Historical label quality review.
2. Canonical identity join audit.
3. Source/use-gate matrix by field and family.
4. Missingness policy that separates true zero from unknown.
5. Leakage/as-of safety checks.
6. Sparse-history and low-games slice definitions.
7. Exact receipt recovery status for `checkpoint_review_score`, `position_specific_review_score`, lifecycle/age/role/confidence, and WR/QB v2 overlay chain.

## PYF Anchor Policy

PYF remains the champion baseline. A future candidate cannot advance unless it beats or clearly contextualizes PYF overall, by position, and on low-games/sparse-history slices. If a candidate fails PYF, it may remain review-only evidence but cannot become a winner, production input, or ranking change.

## Advancement Rules Summary

A future candidate cannot advance unless it:

- Beats or explicitly contextualizes PYF.
- Reports position-level metrics.
- Does not collapse on sparse-history or low-games slices.
- Reports prior-production-decline false positives.
- Passes leakage/as-of checks.
- Documents source/use-gate status.
- Has reproducible input receipts.
- Has no hidden production/runtime/ranking effect.
- Receives Master HQ review before execution and before any later promotion discussion.

## Minimum Requirements Before Formula Gauntlet Can Run

Before any Formula Gauntlet tournament can run, NWR needs:

- Master HQ approval for the specific tournament class.
- Data Hygiene clearance for labels, identity, source gates, missingness, and leakage.
- Frozen benchmark contract with labels, seasons, positions, baselines, metrics, and eligible universe.
- PYF baseline included as anchor.
- Source receipts and component receipts for every input.
- Explicit blocked-input list.
- Review-only artifact destination.
- No production side effects.

## Recommendation

Recommended next lane:

`Data Hygiene Historical Label / Identity / Source Gate Closure V1`

Formula Gauntlet should wait. After Data Hygiene clears enough gates, Master HQ can open a narrow review-only tournament execution lane using this scaffold as the contract.
