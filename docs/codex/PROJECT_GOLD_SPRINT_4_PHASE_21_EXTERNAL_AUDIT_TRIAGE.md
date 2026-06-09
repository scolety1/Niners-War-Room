# Project Gold Sprint 4 / Phase 21: External Audit Triage

Last reviewed: 2026-05-14

Input report:

`C:\Users\codex-agent\Downloads\Model audit process.docx`

Current audit packet checked:

`local_exports/model_audits/sprint3_phase20_independent_model_audit_packet_20260514`

This triage verifies the external audit findings against the current packet and code. It
does not change formulas, scores, readiness labels, or gate behavior.

## Executive Read

The external audit is useful and mostly points at the right future work, but some findings
mix up three different scopes:

1. **Roster-declaration readiness**: currently ready for review.
2. **Draft readiness**: still blocked because the real rookie/free-agent/released-veteran
   draft pool is not loaded.
3. **Global model-universe hygiene**: still has gaps, stale/proxy inputs, and accepted
   outlier/source-gap audit rows that should remain visible.

The most important Sprint 4 work is not a formula rewrite. It is:

- clarify top-five language,
- make confidence/source weakness more obvious,
- add movement reasons,
- reconcile source gaps by decision scope,
- keep baseline projections and route/participation gaps visibly limited.

## Verified Counts

| item | current value | triage note |
|---|---:|---|
| Full active ranking rows | 1,039 | Broad model universe, not all roster-decision-relevant. |
| Current source coverage rows | 1,039 | Includes many non-rostered/deep universe rows. |
| Critical missing source rows | 136 | True globally; not blocking current Niners roster gate. |
| Source rows marked `blocks_decision_ready` | 136 | True globally; draft/final concern. |
| Outlier rows | 2,994 | True raw count; most are low/medium audit prompts. |
| Accepted outlier rows | 348 | True. Current gate reports no unresolved review-required ranking outliers. |
| Projection status: local baseline | 689 | True global weakness. |
| Projection status: missing | 350 | True global weakness. |
| Age source status | 1,039 `derived_real_data` | Age data is present; blank warnings usually mean no warning applied. |
| Blank age warning | 656 | Not the same as missing age data. |
| Blank age interaction flags | 744 | Not the same as missing age data; may still need clearer UI. |
| Roster Decisions Ready | true | Current roster gate passes. |
| Draft Ready | false | Blocked by missing real draft pool and Draft UX contract. |
| Final Money Ready | false | Correctly blocked. |

## Triage Table

| finding | classification | severity | roster-decision impact | draft/final impact | affected files/pages | verification | recommended action |
|---|---|---:|---|---|---|---|---|
| 136 players have critical missing production/role/projection sources. | source gap | high | Low for current Niners roster; roster gate passes selected-team critical coverage. | High for draft/final because full universe contains blocked rows. | `source_coverage_rows.csv`, Model Lab > Coverage | Confirmed globally: 136 rows have critical missing buckets / `blocks_decision_ready`. | Phase 26 should split source gaps by roster-critical, draft-critical, final-money-critical, optional accepted, and paid-data candidate. |
| Many raw outlier rows remain while only 348 are accepted. | false positive / model policy decision | medium | Low; current roster outlier gate passes. | Medium; raw outlier count should remain visible for audit. | `outlier_rows.csv`, `outlier_acceptance_rows.csv`, Model Lab > Outliers | Confirmed 2,994 raw outlier rows and 348 accepted rows, but current gate says no unresolved review-required ranking outliers remain. | Keep raw outliers visible. Phase 26/29 should explain accepted vs review-required vs informational outliers more clearly. |
| Local baseline or missing projections are common. | source gap | high | Medium; usable for roster review only because baseline projections remain marked and confidence penalties stay visible. | High; not enough for draft/final confidence. | `normalized_feature_rows.csv`, receipts, Model Lab > Coverage | Confirmed 689 local baseline projection rows and 350 missing projection rows globally. | Phase 27 should harden projection baseline labels: “local baseline, not forecast.” Paid projection import remains future work. |
| Age warning and age interaction flag blanks mean age/dropoff is missing. | false positive plus future improvement | low | Low; current `age_source_status` is derived real data for 1,039 rows. | Medium; age/dropoff UI can still be clearer. | `normalized_feature_rows.csv`, receipts | Confirmed age source exists. Blank warnings generally mean no warning triggered, not missing age data. | Phase 24 should translate blank warning/flag fields to “no active age warning.” Future paid/manual injury-age work can improve nuance. |
| Confidence can look too high for weak or missing source data. | likely bug / source-quality issue | high | Medium; current Niners gate passes, but user trust depends on confidence matching data quality. | High; global confidence should be sharper before final decisions. | confidence services, War Board, My Team receipts | Confirmed 11 global critical-missing rows still show confidence above 40; current confidence system also has rebuilt-confidence logic that may not be front-and-center everywhere. | Phase 23 should export a confidence mismatch audit and patch only systematic mismatches. Phase 24 should add plain-English confidence labels. |
| Manual outlier/source-gap acceptances may silently alter scores. | mostly false positive / transparency issue | medium | Low if scores are unchanged; medium if users cannot see acceptance meaning. | Medium for final audit trust. | `model_outlier_acceptances.csv`, `source_coverage_gap_acceptances.csv`, final gate services | Verified acceptances are gate/audit mechanisms. Source gap acceptances require `confidence_penalty_retained=true`; final gate text says accepted gaps retain confidence penalties. | Phase 26 should document accepted gaps as “accepted risk, score unchanged, penalty retained.” Do not alter scoring from acceptance rows. |
| Top-five release labels are misaligned because league rank 10/31/35/56/66 are not league ranks 1-5. | terminology/UI issue | high | High user-confusion risk, but not a confirmed logic bug. | Medium; draft/final should inherit clearer language. | My Team, forced-release comparison, docs, tests | External auditor misunderstood LVE top five. It means the five highest league-ranked players on that roster, not league ranks 1-5 overall. Current top-five rows are the Niners roster’s five lowest numeric league ranks. | Phase 22 should rename to “Roster’s League-Rank Top Five” and add help text that league rank is a rule/availability signal, not quality. |
| Movement vs Sprint 2 lacks movement reasons. | future improvement | medium | Low for current roster decisions; helpful for trust. | Medium for external audit repeatability. | `movement_vs_sprint2_checkpoint.csv`, audit packet exporter | Confirmed current movement file includes deltas but no explanatory `movement_reason`. | Phase 25 should add `movement_reason`, magnitude bucket, and unknown medium/large movement review. |
| Young NFL bridge prior may be too small or too generous. | model policy decision | medium | Medium for young Niners players, but not proven as a bug by this audit. | Medium for future draft/keeper trust. | bridge receipts, young-player review | Audit raised a modeling concern but did not prove a defective coefficient. Named sanity fixtures currently pass. | Do not tune blindly. Keep under Phase 23/29 audit; only change if receipt-backed mismatch appears. |
| Generic market/trade data should be ingested to fix missing features. | model policy decision / partially rejected | low | Low; market is intentionally not private football value. | Medium for Trade Lab only. | market isolation docs, Trade Lab, receipts | Current model policy intentionally keeps market out of private/model value. Missing market is optional/trade-only. | Do not prioritize market data over route/projection sources. Keep market as liquidity/context only. |
| Identity all mapped via GSIS/Sleeper may exclude rookies or non-GSIS players. | source gap / future improvement | medium | Low for current roster gate; current selected-roster identity passes. | High for draft pool because incoming rookies/free agents need real draftable pool handling. | identity bridge, Draft Board, Rankings | Current packet: selected roster identity passes; draft pool still blocked. | Sprint 5 or draft-pool phase should add rookie/free-agent identity fallback/manual review before draft readiness. |
| Final draft pool and Draft UX are blocked. | confirmed bug/gap, already known | high | None for pre-declaration roster decisions. | High; blocks draft/final readiness. | final gate, Rankings, Draft Board | Confirmed `real_draft_pool_loaded` and `draft_ux_smoke_pass` are blocked. | Next product sprint should load real rookies/free agents and rebuild available draft pool before final freeze. |
| Wide receivers ranking high is surprising but data-supported. | no action / model policy observation | low | No direct blocker. | No direct blocker. | War Board, rankings | Audit considered it plausible for this format. | Keep receipt review available; do not tune just to match generic dynasty rankings. |
| QB/TE suppression is appropriate. | no action / positive validation | low | No direct blocker. | No direct blocker. | formula outputs, rankings | Audit agrees with 1QB/no-TE-premium suppression direction. | Preserve current policy unless future receipts prove over-suppression. |

## Confirmed Work For Sprint 4

These audit items should become Sprint 4 implementation work:

1. **Top-five rule language reconciliation**
   - Rename user-facing language to “Roster’s League-Rank Top Five.”
   - Explain it means the five highest league-ranked players on that roster.
   - Keep league rank separate from player quality.

2. **Confidence calibration audit**
   - Export confidence mismatch rows.
   - Patch only systematic confidence/data-quality mismatch.
   - Make low-data players look uncertain in the UI.

3. **Confidence UI and warning language**
   - Translate confidence to plain English.
   - Explain local baseline, missing route/participation, stale production, and accepted gaps.

4. **Movement reason tracking**
   - Add `movement_reason`.
   - Flag unknown medium/large movement.

5. **Source gap reconciliation**
   - Split gaps by roster-critical, draft-critical, final-critical, optional accepted, and paid-data candidate.
   - Keep accepted gaps visible and penalized.

6. **Projection baseline guardrail**
   - Make “local baseline, not forecast” visible wherever projections are shown.

7. **Route/participation data gap gate**
   - Make missing route/usage data explicit as the top paid/free data upgrade target.

## Items Not To Do From This Audit

- Do not treat all 2,994 outlier rows as blockers.
- Do not treat league ranks 10/31/35/56/66 as proof the top-five rule is broken.
- Do not let market data fix private/model value.
- Do not increase young-player draft-capital weight without receipt-backed evidence.
- Do not call draft/final ready until the real draft pool is loaded.

## Readiness State After Triage

| readiness | status |
|---|---|
| Roster decisions | Ready for review |
| Draft decisions | Blocked |
| Final money decisions | Blocked |

No readiness labels were changed in this phase.
