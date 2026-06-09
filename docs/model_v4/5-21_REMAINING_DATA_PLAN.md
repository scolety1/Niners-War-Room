# 5-21 Remaining Data Plan

This is the non-formula backlog from the May 21 audits. The model is safe for human decision review; these items are about reducing manual interpretation and improving confidence.

## Route, Target, And Snap Evidence

Current status:
- The model already warns when route, target, or snap data is missing or review-only.
- Missing route/snap data is not filled with zero or treated as negative evidence.
- Player Board now surfaces these warnings in Manual Review Notes and the Audit Watchlist.

Useful future source fields:
- routes run
- route participation
- target share
- targets per route run
- first-read target share, if licensed and reliable
- snap share by week or season
- pass-block rate for TEs, if available

Admission rule:
- Use only licensed or otherwise allowed exports with player identity resolved.
- Do not estimate route metrics and label them as real.
- Keep review-only route context out of private football value until admitted by the formula contract.

## Age And Injury Metadata

Current status:
- Aging and rushing-age warnings are visible for manual review.
- Missing DOB/injury evidence is not invented.
- Player Board now has a Veteran And Rushing-Age Review surface.

Useful future source fields:
- exact date of birth
- historical games missed
- injury type and recurrence buckets
- year-by-year workload
- QB rushing-volume trend by age

Admission rule:
- Age/injury metadata can inform lifecycle and confidence only after source and identity checks.
- Do not apply hidden manual penalties without receipts.

## TE No-Premium Interpretation

Current status:
- TE values are no-premium VORP values.
- The model may still show useful TE values when the replacement gap is real.
- Player Board now has a TE No-Premium Review surface so these rows are not mistaken for TE-premium values.

Manual review:
- Check Brock Bowers, Travis Kelce, and George Kittle against no-premium replacement context.
- Do not treat TE score as a premium unless league scoring changes.

## First-Down And Return Gaps

Current status:
- First-down evidence uses admitted matched views.
- Partial first-down evidence is surfaced as confidence/manual-review context.
- Return evidence remains direct scoring only, not a talent signal.

Future improvement:
- Add more direct first-down seasons if available.
- Keep estimates clearly labeled as estimates if they are ever used in a review layer.

## Market Context

Current status:
- League rank and ADP normalize to 0-100 for review context only.
- Partial market context now gets a `partial_market_context_review` label instead of normal watch labels.
- Market Gap does not write back into Model Value.

Manual review:
- Treat Market Signals as a disagreement finder, not a trade command.
