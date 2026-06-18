# Rookie Top-15 Trap Guard Audit R-ACC-5

Date: 2026-06-17

Verdict: YELLOW for manual top-15 draft use.

R-ACC-5 audits the frozen top 15 rookie board for manual draft traps in this league format: 10-team dynasty/keeper hybrid, 1QB, non-PPR, no superflex, no TE premium, and rush/rec first downs matter. This audit does not change formula, board order, private scores, rankings, probabilities, bands, hidden sort keys, or promoted artifacts.

## Top-15 Frozen Candidate List

Source: `local_exports/rookie_framework/final_post_fill_runway_20260616/rookie_2026_final_manual_draft_board_post_fill_runway_20260616.csv`

1. Jeremiyah Love
2. Makai Lemon
3. Carnell Tate
4. KC Concepcion
5. Jadarian Price
6. Denzel Boston
7. Germie Bernard
8. Chris Bell
9. Zachariah Branch
10. Antonio Williams
11. Jonah Coleman
12. Skyler Bell
13. Brenen Thompson
14. Elijah Sarratt
15. Emmett Johnson

## Trap Categories Used

- Role uncertainty
- Depth-chart uncertainty
- Injury/availability
- Non-PPR fragility
- First-down scoring mismatch
- 1QB devaluation issue
- Production-context concern
- Competition/team context concern
- Manual hold
- Critical trap guard
- Missing evidence

These categories are manual review labels only. They are not hidden sort keys and do not reorder the board.

## Top 5 Safest Manual Targets

1. Jeremiyah Love: safest current premium profile because role display is populated and the board already supports 1.03 / 1.04 manual use after health/role sanity check.
2. Makai Lemon: safer than most non-Love WR options only if target-earning role is verified.
3. KC Concepcion: viable 1.04 candidate only after target-role verification.
4. Carnell Tate: draft capital is strong, but he remains verify-first because bust/source risk is high.
5. Jadarian Price: RB scarcity helps the manual case, but only if first-down/goal-line role evidence is confirmed.

This list is a manual safety view, not a new ranking. Only Jeremiyah Love is currently clear enough for premium use without new role evidence.

## Top 5 Verify-First Targets

1. Makai Lemon: needs role/depth-chart and target-earning confirmation.
2. Carnell Tate: needs role/source/injury confirmation despite premium draft capital.
3. KC Concepcion: needs target-earning and first-down role confirmation.
4. Jadarian Price: needs early-down, goal-line, first-down, and pass-pro role confirmation.
5. Denzel Boston: needs role evidence before leaving trade-down range.

## Top 5 Trap / Hold Candidates

1. Antonio Williams: `manual_hold`, `critical_trap_guard`, very-high bust risk, missing role evidence.
2. Carnell Tate: very-high bust risk and low source confidence make him the highest-ranked verify-first trap candidate.
3. Jadarian Price: RB scarcity can tempt a premium pick, but role evidence is not filled.
4. Brenen Thompson: top-15 fallback with manual review and missing role.
5. Elijah Sarratt: top-15 fallback with manual review and missing role.

## Category Notes

Role uncertainty:

- Present for most Tier 1 WRs and Antonio Williams because `Depth Chart / Role` remains `needs_data`.

Depth-chart uncertainty:

- Material for Makai Lemon, Carnell Tate, KC Concepcion, Jadarian Price, Denzel Boston, Germie Bernard, Chris Bell, Zachariah Branch, Antonio Williams, Brenen Thompson, and Elijah Sarratt.

Injury/availability:

- Must remain a draft-day check for every premium option.
- Carnell Tate and Antonio Williams carry source/injury review context in prior notes.

Non-PPR fragility:

- Most WRs need target quality and first-down conversion evidence, not reception volume.
- Gadget or low-aDOT roles should push players toward trade-down/hold unless first-down value is clear.

First-down scoring mismatch:

- WRs need credible first-down target roles.
- RBs need early-down, goal-line, receiving first-down, and short-yardage context.

1QB devaluation:

- No QB is in the top-15 review group, and this format gives no superflex boost.

Production-context concern:

- Very-high bust risk, low source confidence, or "no standout CFBD edge" notes increase manual caution.

Competition/team context:

- Missing role evidence means team competition is not cleared for most early-pick candidates.

Manual hold / critical trap guard:

- Antonio Williams is the key top-15 hard stop until cleared.

## Why This Does Not Change Formula Or Board Order

R-ACC-5 reads the frozen top 15 and attaches manual caution language. It does not edit the board, recalculate any score, change `cfbd_enriched_baseline_v1_1`, change rank/order, or promote any artifact.

## How Tim Should Use This On Draft Day

- Use Jeremiyah Love as the cleanest current 1.03 / 1.04 option.
- Treat Makai Lemon, Carnell Tate, KC Concepcion, and Jadarian Price as verify-first candidates.
- Treat Denzel Boston through Emmett Johnson as trade-down or fallback review names unless role evidence improves.
- Keep Antonio Williams on hold until the trap-guard question is answered.
- Use ADP/market only for price and availability pressure.

## Do Not Use For Production/App

This audit is local/manual-use only. Do not wire it into the app, production rankings, Outcome files, veteran/model_v4 files, probability systems, or hidden sort keys.

## Next Best Codex Prompt

Proceed to R-ACC-6 for a read-only formula sensitivity and scoring-fit audit. Do not change the formula without a separate gate.
