# Roster Decision Sanity Audit

Date: 2026-05-12

Active pack: `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks`

Audit output: `local_exports/roster_decision_sanity_audit_preview.csv`

## Scope

This pass audits the Niners roster board for pre-declaration decisions. It checks the active visible scores against lifecycle assignment, model value, keep priority, cut risk, young-player bridge contribution, receipt drivers, source coverage, identity confidence, warnings, and outlier status.

No formula weights were changed in this pass.

## High-Level Result

The visible My Team rows are synced to active stats-first preview outputs, not the neutral placeholder backup. Identity confidence is ready for the selected roster players reviewed here. Lifecycle assignment is also broadly correct: Brian Thomas, Luther Burden, De'Von Achane, Kaleb Johnson, Brenton Strange, Jayden Higgins, Chase Brown, Xavier Worthy, and similar early-career players are being treated as `Young NFL Bridge` assets rather than pure veterans.

The roster is still review-only because several important rows depend on young-player bridge priors and incomplete optional evidence. The main remaining trust issues are source coverage confidence, market-reference gaps, and conservative action bucket thresholds, not a stale-output bug.

## Specific Player Checks

| player | current bucket | audit read |
|---|---|---|
| Brian Thomas | Core Holds | Strongest Niners roster row in this audit. Young bridge lifecycle is correct. Coverage is usable with confidence drag. |
| Luther Burden | Forced-Release Decision | Correctly treated as a young bridge player and the current required top-five release candidate. Low confidence and review coverage mean this should be inspected before acting. |
| De'Von Achane | Bubble Players | Young bridge lifecycle is correct. Market reference is neutral/missing, so Model vs Market is not actionable yet. |
| Lamar Jackson | Shop Candidates | Identity and coverage are ready. The low action bucket is driven by LVE 1QB/QB replacement suppression, not stale output. This is a model-policy review item if the user disagrees. |
| Kaleb Johnson | Shop Candidates | Young bridge lifecycle is correct, but coverage is review-level and confidence is low. Do not treat the current row as final without source review. |
| Brenton Strange | Bench/Stash | Young bridge lifecycle is correct. TE no-premium suppression is the main negative driver. |
| Daniel Jones | Bench/Stash | Established veteran, identity ready. QB replacement suppression drives the drop-level bucket. |
| Jayden Higgins | Shop Candidates | Young bridge lifecycle is correct, but review coverage and low confidence keep this from decision-ready use. |

## Supported Patch From This Audit

Compact receipts now prioritize `private_lve_value` driver rows and keep trade/liquidity rows out of the first-view "top drivers" list when private model rows are available. This fixes a display trust issue where market/liquidity could appear as if it were driving the private model value. Full raw receipts still remain available in Advanced views.

## Remaining Review Items

- Low-confidence young bridge rows need source review before money decisions.
- Market-reference gaps should stay visible as trade/liquidity limitations, not private-value blockers.
- The action buckets are conservative. A player can be valuable and still appear as `bubble` or `shop` if keep priority and cut risk do not clear the hard thresholds.
- Lamar Jackson's low roster action bucket is a deliberate 1QB/no-premium-style structural suppression. That should be reviewed as a model-policy question, not silently tuned.

## Current Recommendation

Use My Team for inventory and audit review only. The forced-release row is useful as a current model hypothesis, but the app should remain review-only until source coverage, named sanity fixtures, and outlier acceptance gates pass.
