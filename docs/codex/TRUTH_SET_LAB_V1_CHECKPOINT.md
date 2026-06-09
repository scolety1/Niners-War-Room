# Truth Set Lab v1 Checkpoint

Date: 2026-05-15

Status: Review-only. Active rankings remain unchanged. No roster, draft, or money-decision gate is unlocked by this checkpoint.

Checkpoint decision: Truth Set Lab v1 improved the evidence pipeline, but it did not produce enough clean data to trust the rankings as decision-ready. The safest path is to keep the app review-only, fix the failed source exports, and rerun the same audit loop with cleaner production and role/usage data before touching formulas.

## Purpose

Truth Set Lab v1 tested whether targeted agent-collected data for 40 important players could safely improve the Niners War Room model. The answer is: yes for auditability and limited preview improvements, no for final trust yet.

The trial produced useful projection and young-player bridge preview inputs, but it also proved that the model still needs cleaner production, route/usage, injury, and market data before formula changes should be trusted.

## Six Intake Summary

| source | coverage | verdict | usable now | notes |
|---|---:|---|---|---|
| injury | 40/40 | preview-only | limited context only | Only 7 rows have sourced evidence. 33 healthy/active rows lack source URLs and cannot boost durability or confidence. |
| trade liquidity | 40/40 rows, 5 populated | usable now for trade context only | yes, but sparse | Five FantasyCalc-style values are usable for liquidity context. Missing market cannot create fake edge. |
| role/usage | 40/40 | preview-only / needs cleanup | no automatic scoring | WR/TE fields are promising, but 15 malformed rows and 27 uncertainty markers block model import. RB workload text is rejected as numeric evidence. |
| projections | 40/40 | usable after derivation | yes, after recompute | Raw projected stat columns are useful. Supplied points are rejected because they appear to use non-LVE scoring. First-down projections are missing. |
| production | 40/40 | rejected / needs re-export | no | Field alignment is unsafe: inconsistent row widths, embedded URL/source text, and uncertain numeric markers. This cannot feed production scoring. |
| young-player prior | 20/23 expected young rows | usable after derivation / preview-only | partially | Draft year/round/pick can drive preview bridge prior. College/testing context remains display/review only. Jahmyr Gibbs, Ashton Jeanty, and Brock Bowers are missing. |

## Import Eligibility

| status | sources / field groups |
|---|---|
| usable now | Populated trade-liquidity rows, but only for trade/liquidity context. |
| usable after derivation | Projection stat columns after recomputing LVE points; young-player draft year/round/pick after deriving draft-capital prior. |
| preview-only | Injury context, WR/TE role usage, young college/testing context, missing market/projection notes. |
| rejected | Supplied projection point totals, all current production stat columns, unsafe RB workload text as numeric evidence. |
| need re-export | Production data; RB role/workload usage; ideally role/route data with strict numeric fields. |

## Model Impact

Two preview paths were created:

- Dry run: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v1\reports\truth_set_model_dry_run_preview.csv`
- Controlled safe-input model preview: `C:\Dev\niners-war-room\local_exports\nflverse_model_previews\truth_set_safe_inputs_20260515T032635`

Safe preview summary:

| metric | value |
|---|---:|
| truth-set players | 40 |
| projection rows applied | 37 |
| young bridge rows applied | 17 |
| market context rows applied | 5 |
| rejected production rows | 40 |
| large value-change rows | 0 |
| active outputs overwritten | false |

The largest model-value moves were modest. The safe data mostly nudged values, not reshaped the board:

| player | direction | interpretation |
|---|---|---|
| Bijan Robinson | up | Recomputed projection supports elite RB treatment. |
| Jahmyr Gibbs | up | Projection supports strong RB value, but young-prior row is still missing. |
| De'Von Achane | up | Projection supports him more than the base model did. |
| Chase Brown | up | Projection improves him, but not into a core elite tier. |
| Kaleb Johnson | down | Safe data does not support a blind young-RB boost. |
| Luther Burden | down | Bridge prior alone is not enough without stronger projected/NFL evidence. |
| Jayden Higgins | down | Same issue as Luther: early-career prior does not replace NFL/projection evidence. |
| Josh Allen | up | Projection improves QB value, but 1QB suppression remains directionally intact. |

This is useful. It suggests the Truth Set safe fields are not causing chaos, but also that they are not enough to fix all model trust concerns.

## What Helped

1. Projection recomputation worked.

The projection stat columns became usable only after rejecting the supplied fantasy points and recomputing no-PPR LVE points. This gave cleaner evidence for 37 players.

Post-Pro estimator update: a separate first-down projection estimator preview now
derives broad position-level first-down rates from local nflverse weekly stats.
It produced 37 `estimated_from_history` rows and 3
`missing_first_down_projection` rows, but it remains preview-only and does not
change active projection scoring.

2. Young bridge prior became auditable.

Draft-capital prior can now be previewed without applying it to established veterans or faking missing players.

3. Market isolation held.

Trade liquidity rows were kept out of private/model value and remained trade context only.

4. Rejected data stayed rejected.

The pipeline now explicitly logs rejected production fields, rejected supplied projection points, and rejected unsafe RB workload text.

## What Failed

1. Production data failed.

This is the biggest miss. The production export cannot be trusted because stat columns are not safely aligned. It needs a strict re-export before it can help the model.

2. Role/usage data is not model-ready.

WR/TE route data looks promising, but extraction issues and uncertainty markers block automatic import. RB workload data is especially unusable because text was placed where numeric fields were needed.

3. Injury data is weak.

The report mostly says players are healthy without source URLs. That is not evidence of durability. Sourced injury rows are useful for review, not confidence boosts.

4. Market data is too sparse.

Only 5 of 40 players have populated market values. That is fine for a tiny test but too sparse for a real trade-edge board.

5. Young bridge coverage is incomplete.

Jahmyr Gibbs, Ashton Jeanty, and Brock Bowers are missing from the young-prior report even though they are important controls.

## Remaining Data Gaps

### Production

Status: blocking gap.

Need a corrected strict CSV export with stable row width, exact header, no embedded URLs in stat fields, no question marks in numeric fields, and one row per truth-set player.

Post-Pro validation update: a strict production intake validator now exists. The current raw export still rejects with 30 malformed-width rows, 22 numeric-error rows, 7 uncertain-marker rows, 30 embedded-url rows, and 35 source-separation rows. The current clean/rejection metadata file also rejects because it is not the strict production schema.

### First-Down Projection Estimates

Status: preview-only design layer.

The estimator report is available at
`local_exports/truth_set_lab/v1/reports/first_down_projection_estimator_preview.csv`.
It uses historical position rates from local nflverse weekly player stats, but
does not feed active scoring. This is useful for seeing the size of the missing
first-down projection gap. It should not be promoted until player-specific or
role-specific rates are validated.

### Role/Usage

Status: high-value gap.

Need clean numeric fields for route participation, routes run, target share, TPRR, YPRR, snap share, RB carries, RB target share, opportunity share, red-zone touches, and goal-line touches.

Post-Pro validation update: a strict role/usage intake validator now exists. The current role/usage file still rejects with a header mismatch, 40 malformed-width rows under the strict schema, 26 uncertainty-marker rows, and 3 prose-in-numeric-field rows. It remains preview/review only.

### Route Participation

Status: likely paid-data candidate.

Free/public sources may not reliably provide true route data. This is probably one of the fields most worth paying for if we want an edge.

### Injuries

Status: review/context gap.

Need sourced injury history/current status. Unsourced healthy labels should stay neutral and should not raise confidence.

### Market Liquidity

Status: optional trade-context gap.

Market does not belong in private value, but a broader market export would improve buy/sell and model-vs-market surfaces.

### Young Bridge Prior

Status: partial gap.

The draft-capital gap-fill rows for Jahmyr Gibbs, Ashton Jeanty, and Brock Bowers are now present. They include factual draft year, round, pick, team, and source URL only. College production/testing context should remain display-only until verified.

## Recommendation

### Continue With Free/Public Data?

Yes, but only for structured sources and only where fields are clean. Free/public data is still useful for projections, baseline production from nflverse, IDs, age/bio, first-down scoring, and basic injury context.

### Request Corrected Data-Agent Exports?

Yes. This is the best next move. The production re-export should be first because production is core model evidence. Role/usage should be second, with strict numeric-only columns.

### Trial Paid Data?

Yes, but not yet as a subscription commitment. The best paid trial would target route participation, routes run, TPRR, YPRR, red-zone/goal-line usage, and injury/projection exports. A 20-40 player sample is enough to judge whether the provider solves real gaps.

Post-Pro paid trial criteria update: the exact 40-player sample, 20-player
minimum subset, required fields, provider comparison template, and acceptance
criteria are now saved under
`templates/real_data_inputs/paid_data_trial/` and documented in
`docs/codex/POST_PRO_AUDIT_PHASE_6_PAID_DATA_TRIAL_CRITERIA.md`.

### Rebuild Formulas Now?

No. Do not rebuild formulas until cleaner production and role/usage evidence exists. The safe-input preview showed no catastrophic movement, so the next bottleneck is data quality, not blind formula surgery.

## Source Verdict Matrix

| source | use in private/model value now | use after derivation | trade/context use | rejected / blocked use |
|---|---|---|---|---|
| injury | no | no | sourced injury notes only | unsourced healthy rows cannot boost confidence |
| trade liquidity | no | no | yes, populated rows only | missing market cannot create fake edge |
| role/usage | no | possible after strict re-export | review notes only | RB workload text and uncertain/malformed rows |
| projections | no direct import | yes, after LVE recompute | source coverage context | supplied fantasy point totals |
| production | no | no, until re-exported | none | all current stat columns |
| young-player prior | no direct import | yes, draft capital prior preview for eligible young players | receipt/context | established-veteran draft capital scoring |

## Next Steps

1. Request corrected production export from the data agent using the strict CSV schema now documented in `TRUTH_SET_LAB_V1_PRODUCTION_STRICT_VALIDATION.md`.
2. Request corrected role/usage export with the strict numeric schema now documented in `TRUTH_SET_LAB_V1_ROLE_USAGE_STRICT_VALIDATION.md`.
3. Young-prior controls for Jahmyr Gibbs, Ashton Jeanty, and Brock Bowers have been filled with factual draft-capital rows.
4. Projection team-mismatch/source-quality flags are now present in preview rows and source logs.
5. Missing-projection-but-high-active-value checks are now available in the projection recompute layer.
6. Use the first-down estimator as preview-only audit context, not active scoring.
7. Re-run Truth Set Lab after corrected production and role/usage exports arrive.
8. Perform focused JSN vs Tee, RB/WR balance, and young-bridge audits using clean production plus role data.
9. Trial paid data only if corrected free/public exports still cannot supply route participation, TPRR, RB opportunity, and injury reliability.
10. If testing paid data, use the Post-Pro Phase 6 sample and acceptance templates before any provider fields enter preview imports.
11. Consider formula changes only after the clean-data audit identifies fixture-backed formula problems.

## Do Not Do Yet

- Do not promote the safe-input preview into active model outputs.
- Do not use the rejected production file for scoring.
- Do not let supplied projection point totals bypass LVE recomputation.
- Do not let sparse market rows affect private/model value.
- Do not use unsourced healthy injury rows to raise confidence.
- Do not rebuild formulas until production and role/usage truth are cleaner.

## Final Decision

Truth Set Lab v1 was worth doing. It improved the pipeline and revealed real failure modes. It did not produce enough clean evidence to make the model decision-ready.

Keep rankings review-only until formal gates pass.

## v2 Preview Rerun

Post-Pro Phase 7 generated a clean Truth Set Lab v2 preview rerun:

- Preview folder: `local_exports/nflverse_model_previews/truth_set_lab_v2_preview_20260515T045827`
- Projection rows applied: 37
- Young bridge rows applied: 20
- Market context rows applied: 5
- Production validation status: `rejected`
- Role/usage validation status: `rejected`
- Movement rows vs v1: 40
- Active rankings overwritten: `false`

The v2 rerun confirms the same core conclusion: projection recompute and young
bridge gap fills are usable for preview, but production and role/usage remain
blocked until corrected exports pass validation.
