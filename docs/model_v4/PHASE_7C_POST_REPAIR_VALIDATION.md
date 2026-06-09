# Phase 7C Post-Repair Validation

Created: 2026-05-16

This validation checks whether Phase 7B fixed the confirmed external-audit
issues without promoting v4 into the active app. V4 remains review-only. No
readiness gate was unlocked.

## Re-run Summary

| Artifact | Result |
| --- | --- |
| `PHASE_7C_SANITY_FIXTURE_RESULTS.csv` | 31 ready, 0 review, 0 blocked |
| `PHASE_7C_NAMED_PLAYER_REVIEW.csv` | 19 matched, 0 missing |
| `PHASE_7C_MOVEMENT_AUDIT.csv` | 68 meaningful movements, 10 large movements, 0 unexpected movements |
| Active app rankings | unchanged |
| Decision-ready unlocked | false |

## Incoming Rookie Confidence

Phase 7B fixed the confirmed confidence bug. Incoming rookies with missing
production, first-down, usage, snap, projection, age, and young-prior evidence
no longer show `strong` confidence.

| Player | Position | Dynasty Asset Value | Confidence | Confidence Label | Validation |
| --- | --- | ---: | ---: | --- | --- |
| Fernando Mendoza | QB | 0.00 | 45.0 | weak | fixed |
| Jeremiyah Love | RB | 0.00 | 45.0 | weak | fixed |
| Carnell Tate | WR | 0.00 | 45.0 | weak | fixed |
| Jordyn Tyson | WR | 0.00 | 45.0 | weak | fixed |
| Kenyon Sadiq | TE | 0.80 | 45.0 | weak | fixed |

The receipt/warning path is visible through
`incoming_rookie_missing_evidence_confidence_cap`, along with the missing
evidence warnings for production, first-downs, usage, snap, projection, age, and
young-player prior.

## Incoming Rookie Prior Policy

Policy is now explicit in `MODEL_V4_FORMULA_CONFIG.json` and the Phase 7B repair
notes:

- Incoming rookies may use only sourced draft/prospect/rookie-board evidence.
- If sourced prospect evidence is missing, the row remains weak/review.
- The model does not invent prospect scores or treat missing NFL evidence as
  neutral certainty.

## QB Before/After Repair

Phase 7B converted QB suppression from a positive superflex-style boost into a
1QB replacement guard. The movement is receipt-backed through the
`position_scarcity_suppression` component and the changed QB config lane.

| Player | Phase 6 Value | Phase 7C Value | Delta | Phase 6 Confidence | Phase 7C Confidence | Validation |
| --- | ---: | ---: | ---: | --- | --- | --- |
| Josh Allen | 69.24 | 46.16 | -23.08 | usable | review | appropriate 1QB suppression |
| Lamar Jackson | 67.22 | 44.76 | -22.46 | usable | review | appropriate 1QB suppression |
| Jalen Hurts | 66.78 | 40.29 | -26.49 | review | weak | appropriate 1QB suppression plus projection gap |
| Jayden Daniels | 57.36 | 37.61 | -19.75 | review | weak | appropriate 1QB suppression |
| Joe Burrow | 50.36 | 31.41 | -18.95 | review | weak | appropriate confidence/missing-data suppression |
| Patrick Mahomes | 45.37 | 27.90 | -17.48 | review | weak | appropriate confidence/missing-data suppression |
| Brock Purdy | 45.71 | 30.50 | -15.22 | review | weak | appropriate 1QB suppression |
| Caleb Williams | missing | missing | n/a | n/a | n/a | data/truth-set gap |
| Daniel Jones | 42.05 | 29.20 | -12.85 | usable | review | appropriate 1QB suppression |

The requested Caleb Williams comparison could not run because Caleb Williams is
not currently present in the v4 preview outputs. This is a data/truth-set gap,
not a formula finding.

## Remaining Issue Classification

| Issue | Classification | Impact | Next Action |
| --- | --- | --- | --- |
| Caleb Williams missing from current v4 preview | data blocker for this audit slice | Cannot validate that named QB control until he is added/mapped. | Add Caleb Williams to the truth-set/player universe if he is needed as an ongoing QB control. |
| Luther Burden weak/blocked in named review | source limitation | Young WR has insufficient sourced evidence in the current v4 preview. | Keep review-only until rookie/prospect source data is available. |
| Kaleb Johnson weak/blocked in named review | source limitation | Young RB prior remains contained and unsupported rows are not trusted. | Keep review-only until sourced rookie/prospect/NFL evidence exists. |
| Keenan Allen weak in named review | source limitation / confidence warning | Aging veteran value remains review-only with missing/weak projection context. | Do not promote without source-backed current projection/role evidence. |
| Large movement rows in movement audit | acceptable receipt-backed movement | All large movements are explained by QB suppression or confidence/missing-data handling. | No patch needed unless external audit disputes a specific receipt. |

## Verdict

Phase 7B fixed the confirmed incoming-rookie confidence and QB inflation issues
without creating new unexpected movement. The v4 review-only preview is cleaner
and more internally consistent, but it should not be promoted yet because:

- Caleb Williams is missing from the requested QB validation set.
- Young-player rows such as Luther Burden and Kaleb Johnson still need sourced
  prospect/rookie-board evidence before they can be trusted.
- Keenan Allen remains weak-confidence due source limitations.

Recommended next step: either add the missing QB control and run a small Phase
7D source/control patch, or package the Phase 7C artifacts for a focused
external re-audit.
