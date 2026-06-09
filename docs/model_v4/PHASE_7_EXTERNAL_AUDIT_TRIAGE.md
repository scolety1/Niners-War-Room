# Phase 7 External Audit Triage

Source audit: `C:\Users\codex-agent\Downloads\Dynasty Fantasy Football Audit.docx`

Status: review-only. No formulas, app surfaces, or readiness gates were changed by this triage.

## Executive Verdict

The external audit is not clean enough to accept wholesale. It contains several high-impact false positives against the actual Phase 6 packet, including incorrect claims that the packet omitted Phase 5/Phase 6A files and that major veteran players have near-zero values due to missing all evidence.

However, the audit did identify two real promotion blockers:

1. Incoming rookies can show `strong` confidence despite having no usable evidence.
2. QB suppression is probably still too weak or too binary for a 10-team 1QB league, especially because elite QBs remain comparable to top RB/WR assets and Lamar Jackson is a Niners top-five-rule player.

Decision: do not promote v4 into the app yet. Run one focused Phase 7 repair pass before app promotion planning.

## What The Audit Got Wrong

| Claim | Local Verification | Classification |
| --- | --- | --- |
| Packet lacks Phase 5 checkpoint and Phase 6A formula patch summary. | False. The zip contains `01_phase5_checkpoint/PHASE_5_CHECKPOINT.md`, `02_formula_patch/PHASE_6A_FORMULA_PATCH_PASS.md`, formula configs, and movement audits. | False positive |
| Formula version still reports `model_v4_review_only_0.1.0`. | False for the Phase 6 preview. `v4_preview_outputs.csv` reports `model_v4_review_only_0.2.0`. | False positive |
| Saquon Barkley, Derrick Henry, George Kittle, Travis Kelce, Mark Andrews, and Sam LaPorta have near-zero values because all evidence is missing. | False. Phase 6 preview values are Saquon 76.234, Henry 71.223, Kittle 49.714, Kelce 42.139, Andrews 41.037, LaPorta 39.227. Their unavailable section is projection, not all evidence. | False positive |
| TE suppression wipes out elite TEs when evidence is absent. | Mostly false. Elite TE values are not near zero, though projection gaps remain visible. McBride 58.960 and Bowers 57.249 survive the no-premium layer. | False positive / accepted limitation |

The likely cause is that the audit read the wrong table, mixed packet versions, or inferred from stale values. These claims should not drive source repair or formula tuning.

## What The Audit Got Right

| Finding | Classification | Severity | Why It Matters |
| --- | --- | --- | --- |
| Incoming rookies can show `strong` confidence with missing production, first-down, usage, snap, projection, age, and young-prior evidence. | Confirmed bug | High | Strong confidence must never mean "we have no evidence." This would be misleading on draft surfaces. |
| Incoming rookies need either a review-only prospect prior or exclusion from active decision gates until rookie data exists. | Likely bug / policy gap | Medium | Draft readiness cannot be trusted if incoming rookies are zeroed while confidence is strong. |
| QB suppression is likely too weak or too binary. | Formula concern | High | Josh Allen 69.240 and Lamar Jackson 67.218 remain comparable to elite WRs; Lamar is on the Niners and affects roster-release analysis. |
| WR/RB balance remains worth monitoring because route metrics are unavailable and first-down projections are estimated. | Source gap accepted limitation / formula concern | Medium | This does not automatically prove a formula bug, but it should stay under review after the QB/confidence patch. |
| Missing/proxy evidence is visible in receipts and warnings. | Already handled | Info | This is a strength of v4 and should be preserved. |
| Market/liquidity and league-rank separation are required. | Already handled | Info | Phase 6 named review already marks this ready. |

## Local Verification Notes

The current Phase 6 preview values for audit-disputed players are:

| Player | DAV | Confidence | Unavailable Sections |
| --- | ---: | --- | --- |
| Saquon Barkley | 76.234 | review | projection |
| Derrick Henry | 71.223 | review | projection |
| George Kittle | 49.714 | review | projection |
| Travis Kelce | 42.139 | review | projection |
| Mark Andrews | 41.037 | review | projection |
| Sam LaPorta | 39.227 | review | projection |
| Josh Allen | 69.240 | usable | none |
| Lamar Jackson | 67.218 | usable | none |
| Daniel Jones | 42.046 | usable | none |

Incoming rookie confidence issue:

| Player | Position | DAV | Confidence | Unavailable Sections |
| --- | --- | ---: | --- | --- |
| Fernando Mendoza | QB | 1.440 | strong | production, first-down scoring fit, usage, snap proxy, projection, age/dropoff, young-player prior |
| Jeremiyah Love | RB | 0.000 | strong | production, first-down scoring fit, usage, snap proxy, projection, age/dropoff, young-player prior |
| Carnell Tate | WR | 0.000 | strong | production, first-down scoring fit, usage, snap proxy, projection, age/dropoff, young-player prior |
| Jordyn Tyson | WR | 0.000 | strong | production, first-down scoring fit, usage, snap proxy, projection, age/dropoff, young-player prior |
| Kenyon Sadiq | TE | 0.800 | strong | production, first-down scoring fit, usage, snap proxy, projection, age/dropoff, young-player prior |

This is a real bug. The values can be review-only, but the confidence label cannot be `strong`.

## Promotion Impact

V4 should not move to app promotion planning until the focused repair pass is complete.

The blockers are:

| Blocker | Type | Blocks Roster Decisions? | Blocks Draft/Final? | Required Fix |
| --- | --- | --- | --- | --- |
| Incoming rookie no-data rows show strong confidence. | Confidence blocker | No immediate Niners roster blocker, unless incoming rookies are compared to roster decisions. | Yes | Confidence rule and fixture patch. |
| Incoming rookie prospect prior policy is incomplete. | Data/policy blocker | No immediate roster blocker. | Yes | Define review-only rookie prior or exclude from promoted draft surfaces until available. |
| QB suppression needs targeted review. | Formula concern | Yes, because Lamar Jackson is a Niners top-five-rule player. | Yes | Targeted replacement-value patch and stronger sanity fixture. |
| Phase 6 external audit contains false positives. | Process blocker | Indirect | Indirect | Keep local verification discipline; do not patch false claims. |

## Recommended Phase 7 Patch List

1. Patch confidence rules so rows with no scoring evidence cannot show `strong`.
2. Add incoming-rookie confidence fixtures:
   - no production + no projection + no young prior cannot be `strong`
   - incoming rookie missing evidence should be `weak` or `review`
3. Define the incoming-rookie prior policy:
   - either load prospect prior evidence before draft surfaces
   - or exclude incoming rookies from app promotion gates until rookie board data exists
4. Run a targeted QB replacement-value formula review:
   - compare Josh Allen, Lamar Jackson, Jalen Hurts, Jayden Daniels, Joe Burrow, Patrick Mahomes, Brock Purdy, Caleb Williams, Daniel Jones
   - ensure elite rushing QBs retain value
   - ensure QBs do not outrank core RB/WR assets without receipt-backed justification
5. Strengthen QB sanity fixtures:
   - elite QB versus elite WR tier
   - replaceable QB versus flex-relevant RB/WR
   - Niners Lamar forced-release sensitivity
6. Regenerate v4 preview.
7. Re-run Phase 6-style movement audit, sanity fixtures, and named player review.
8. Only then reconsider app promotion planning.

## Final Decision

Verdict: needs a focused formula/confidence repair pass before app promotion planning.

This is not an architecture redesign signal. It is not a broad source-data failure. The external audit's most severe veteran-data claims are false against the actual Phase 6 packet.

The next work should be narrow:

- incoming-rookie confidence and prior policy
- QB replacement-value suppression
- fixture strengthening
- regenerated review-only preview

Do not do another broad model rebuild.
