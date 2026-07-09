# Formula Gauntlet Blockers and Minimum Requirements

## Highest Blockers

1. Exact Model v4 historical replay is still blocked.
   - Missing season-by-season `checkpoint_review_score`.
   - Missing `position_specific_review_score`.
   - Missing lifecycle, age, role, and confidence receipts.
   - Missing WR/QB v2 candidate-overlay receipt chain.

2. Partial signals did not beat PYF.
   - Best non-PYF component-source signals failed PYF in QB, RB, WR, and TE.
   - This blocks any claim that the current component pool is ready for formula tournaments.

3. Source gates remain review-only or blocked.
   - The partial replay inputs are review-only/proxy-safe.
   - NFLVerse 2024-2025 candidate sources are review-only, not production/model-use.
   - PFR advanced stats remain identity unsafe in the source admission matrix.
   - Route/YPRR/TPRR remain blocked without approved artifact request and denominator proof.

4. Sparse-history and prior-production-decline risks are material.
   - Sparse-history rows: `1,453` (`26.3%`).
   - Prior-production decline false positives: `572` (`10.4%`).

5. No approved tournament score exists.
   - The partial replay benchmark did not invent a Model v4 score.
   - Formula Gauntlet must not create weights or formulas until a separate tournament contract is approved.

## Minimum Requirements Before Full Formula Gauntlet

- Exact or approved historical score/component receipt chain.
- Approved feature-season input receipts with source/use gates.
- Season-by-season decision-date safety checks.
- Identity-safe joins with no name-only fallback.
- PYF champion baseline and position-level baseline ladder.
- Sparse-history and rookie policy.
- Prior-production-decline harm test.
- Position-specific coverage thresholds.
- Leakage guardrail validation.
- Review-only artifact destination and no-production-promotion guardrail.

## Minimum Requirements Before Position-Scoped Review-Only Tournaments

- Human approval that position-scoped tournaments may run despite exact Model v4 replay being blocked.
- Explicit candidate formula contract with no production promotion.
- PYF and PPG baselines for that position.
- Position-specific missingness threshold.
- Position-specific sparse-history and decline false-positive checks.
- Source-gate list of allowed fields.

Current state does not satisfy these requirements.
