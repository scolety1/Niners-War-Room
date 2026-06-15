# Sprint 5CV: Candidate Model Calibration And Sanity Audit

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_CANDIDATE_MODEL_SANITY_AUDIT`

Sprint type: `AUDIT_ONLY_NO_PRODUCTION_NO_DISPLAY`

## 1. Scope

Sprint 5CV audited the Sprint 5CU local-only candidate model outputs for calibration, leakage, support, baseline comparison, and football sanity. This sprint did not train new production models, run current-player inference, create production model artifacts, serialize models, create app-readable outputs, create exact display percentages, create coarse bands, wire app display, alter rankings/sorting, create hidden sort keys, create promoted artifacts, touch rookie files, edit or commit `data/`, stage or commit `local_exports/`, push, or deploy.

No audit script was required. No new local-only export was created.

## 2. Audited Evidence

5CV inspected:

- `docs/outcome_probability/BUILD_SPRINT_5CU_LOCAL_ONLY_CANDIDATE_MODEL_EVALUATION.md`
- `scripts/outcome_probability/run_sprint_5ct_phase5_candidate_modeling_harness.py`
- `local_exports/outcome_probability/sprint_5cu_phase5_local_candidate_model_evaluation/head_candidate_verdicts.csv`
- `local_exports/outcome_probability/sprint_5cu_phase5_local_candidate_model_evaluation/aggregate_metrics_by_head_fold_method.csv`
- `local_exports/outcome_probability/sprint_5cu_phase5_local_candidate_model_evaluation/feature_quarantine_audit.csv`
- `local_exports/outcome_probability/sprint_5cu_phase5_local_candidate_model_evaluation/metadata.json`

All inspected outputs remain local-only.

## 3. Leakage And Output Audit

Leakage audit result: pass.

5CU used only source-safe prior completed-season features:

- prior completed-season games and availability fields
- prior completed-season passing/rushing/receiving yards
- prior completed-season rushing/receiving first downs
- prior completed-season receptions
- prior NWR finish rank
- prior NWR PPG

Forbidden feature failures: 0.

The harness did not use target-year labels as features, same-season final stats as preseason features, current-player inputs, fantasy totals, EPA, WOPR/RACR/PACR/Dakota, target-share fields, ADP, projections, public rankings, market/trade values, RotoWire values, prior fantasy draft history, or legacy `private_score`.

Output quarantine result: pass.

5CU metadata confirms:

- current-player inference performed: false
- row-level predictions exported: false
- app-readable outputs created: false
- serialized model artifacts created: false
- production model artifacts created: false
- exact display percentages created: false
- coarse display bands created: false
- app wiring created: false
- rankings/sorting created: false
- hidden sort keys created: false
- promoted artifacts created: false

## 4. Calibration And Baseline Audit

| Head | Mean AUC | Mean Brier | Base Brier | Mean log loss | Base log loss | Thin calibration bins | 5CU verdict | 5CV verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `qb_t12` | 0.863968 | 0.122189 | 0.168098 | 0.378853 | 0.519141 | 6 | accept | accept |
| `qb_t18` | 0.867506 | 0.140331 | 0.217129 | 0.422201 | 0.625984 | 11 | caution | caution |
| `qb_t24` | 0.888251 | 0.133844 | 0.243236 | 0.419866 | 0.679627 | 9 | caution | caution |
| `rb_t12` | 0.857595 | 0.074577 | 0.091526 | 0.271993 | 0.329510 | 7 | accept | accept |
| `rb_t24` | 0.833113 | 0.120540 | 0.161677 | 0.387880 | 0.504422 | 7 | caution | caution |
| `wr_t12` | 0.911960 | 0.057528 | 0.072386 | 0.219716 | 0.275268 | 4 | accept | accept |
| `wr_t24` | 0.871147 | 0.091423 | 0.127764 | 0.310583 | 0.423411 | 6 | accept | accept |
| `wr_t36` | 0.861316 | 0.116724 | 0.173047 | 0.376227 | 0.530253 | 4 | accept | accept |
| `te_t12` | 0.881903 | 0.083483 | 0.116241 | 0.289116 | 0.394461 | 8 | accept | accept |
| `te_t18` | 0.858787 | 0.106301 | 0.151129 | 0.350109 | 0.479938 | 11 | caution | caution |
| `te_t24` | 0.853641 | 0.125014 | 0.185089 | 0.395475 | 0.557124 | 10 | caution | caution |

Baseline comparison result: pass.

Every evaluated head improved mean Brier and mean log loss versus the base-rate baseline. The caution heads remain caution primarily because of thin calibration bins or weaker aggregate profile relative to the strongest candidates.

## 5. Support And Sanity Audit

Support result: pass for continued human review.

Every evaluated head had four rolling historical holdout folds. Deferred heads and blocked heads were not evaluated as candidates.

Football sanity result: pass with cautions.

Accepted heads are position/threshold combinations with plausible semantics for a conservative candidate set. Caution heads require human review because broader or deeper thresholds can create display-semantics risk and because thin calibration bins make exact values unsafe.

No head looks too good to be true in a way that suggests leakage; strong metrics align with prior completed-season production features.

## 6. Final 5CV Head Tiers

Accepted conservative candidate set:

- `qb_t12`
- `rb_t12`
- `wr_t12`
- `wr_t24`
- `wr_t36`
- `te_t12`

Caution heads:

- `qb_t18`
- `qb_t24`
- `rb_t24`
- `te_t18`
- `te_t24`

Rejected heads: none from the 5CU evaluated set.

Deferred heads that remain excluded:

- `rb_t36`
- `rb_t48`
- `wr_t48`

Blocked heads that remain excluded:

- `qb_t6`
- `rb_t6`
- `wr_t6`
- `te_t3`
- `te_t6`

## 7. Recommendation

5CV recommendation: GREEN.

The accepted conservative candidate set is suitable for a human review packet. The caution heads should be included in the review packet as caution-only and should not advance to any production proposal without stronger calibration evidence.

5CW is approved to run next.

## 8. Release Stance

Current-player probabilities remain blocked.

Exact display percentages remain blocked.

Coarse bands remain blocked.

App-readable outputs remain blocked.

Production model artifacts remain blocked.

App wiring remains blocked.

Rankings/sorting and hidden sort keys remain blocked.

Promoted artifacts remain blocked.

## 9. Checks

Checks run:

- local-only 5CU evidence audit completed
- `git diff --check` passed

No Python files changed in 5CV, so `python -m py_compile`, Ruff, and pytest are not required.
