# Formula Gauntlet Advancement Rules

## Current Status

No candidate can advance in this lane because no tournament was run. These rules are for future lanes only.

## Rule 1: PYF Anchor Must Be Beaten Or Explained

Every candidate must compare against PYF. A candidate can advance only if it:

- beats PYF overall and by position, or
- clearly contextualizes where it does not beat PYF and wins a predeclared narrow slice without causing broader harm.

A candidate that fails PYF can remain review-only evidence, but it cannot be a winner, production formula, ranking change, model-use source, or app behavior change.

## Rule 2: Position-Level Reporting Is Mandatory

No pooled-only candidate can advance. Future reports must show QB, RB, WR, and TE separately unless the tournament class is explicitly single-position.

## Rule 3: Sparse-History And Low-Games Harm Must Not Increase

Candidates must report sparse-history and low-games deltas against PYF. A candidate that improves average correlation while making sparse-history or low-games errors worse is held or rejected.

## Rule 4: Known Failure Modes Must Be Reported

Every future tournament must report at least:

- prior-production decline false positives
- sparse-history misses
- low-games / availability misses
- rookie / second-year misses where supported
- RB role-change misses
- WR breakout misses
- TE volatility misses
- missing key component receipt misses

## Rule 5: Leakage And Source Gates Must Pass

Every candidate input must pass the HQ1 source receipt-chain standard:

- We have the information.
- We know where it came from.
- It is reliable enough for the intended review use.
- Its status is documented.
- It can be reproduced.
- It can be tested historically without current/future leakage.

Any leakage failure blocks advancement.

## Rule 6: Reproducibility Is Required

Every input must have receipts, hashes or deterministic source references, row counts, column counts, coverage, identity joins, missingness policy, and rebuild instructions.

## Rule 7: No Hidden Production Effect

Advancement cannot mutate:

- production rankings
- model weights
- default sort
- hidden sort
- app/runtime behavior
- source registry
- source truth
- recommendation, draft, trade, verdict, or boost logic

## Rule 8: Master HQ Review Is Required

Advancement out of evidence review requires a separate Master HQ review lane. Promotion requires a later, explicit human approval lane and cannot be bundled with tournament execution.
