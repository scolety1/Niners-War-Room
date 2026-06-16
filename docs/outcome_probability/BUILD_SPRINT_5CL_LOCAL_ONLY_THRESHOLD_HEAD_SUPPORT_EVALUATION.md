# Sprint 5CL: Local-Only Threshold-Head Support Evaluation

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_INTERNAL_ONLY_SUPPORT_COUNTS_NO_MODELING`

Sprint type: `THRESHOLD_SUPPORT_EVALUATION_NO_MODELING_NO_RELEASE`

## 1. Scope

Sprint 5CL evaluated support counts for candidate future outcome threshold heads using the GREEN Sprint 5CK-R2 consolidated 2010-2019 historical readiness inventory.

This sprint did not train models, fit calibration, score current players, create probabilities, create exact percentages, create coarse bands, create app-readable outputs, wire app display, alter rankings/sorting, create hidden sort keys, touch rookie files, edit `data/`, edit raw source data, or create promoted artifacts.

## 2. Local-Only Export

Created local-only export:

`local_exports/outcome_probability/sprint_5cl_threshold_head_support_evaluation/`

Created local-only files:

| File | Purpose | App-readable? |
| --- | --- | --- |
| `metadata_sprint_5cl.json` | support-count verdict, head lists, release-blocker flags | no |
| `threshold_head_support_evaluation.csv` | eligible/positive/negative/blocked counts by head | no |
| `README_SPRINT_5CL.md` | local support summary | no |

All 5CL exports are internal-only and not app-readable.

## 3. Candidate Heads Evaluated

Candidate heads evaluated:

- QB: Top 6, Top 12, Top 18, Top 24
- RB: Top 6, Top 12, Top 24, Top 36, Top 48
- WR: Top 6, Top 12, Top 24, Top 36, Top 48
- TE: Top 3, Top 6, Top 12, Top 18, Top 24

Canonical repo head names are preserved in the support table below.

## 4. Support Count Results

| Head | Canonical head | Eligible rows | Positive labels | Negative labels | Position blocked rows | Seasons | Sparse seasons | Result |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| QB Top 6 | `same_year_qb_t6` | 553 | 56 | 497 | 184 | 10 | 10 | YELLOW |
| QB Top 12 | `same_year_qb_t12` | 553 | 112 | 441 | 184 | 10 | 1 | GREEN |
| QB Top 18 | `same_year_qb_t18` | 553 | 168 | 385 | 184 | 10 | 0 | GREEN |
| QB Top 24 | `same_year_qb_t24` | 553 | 216 | 337 | 184 | 10 | 0 | GREEN |
| RB Top 6 | `same_year_rb_t6` | 989 | 53 | 936 | 378 | 10 | 10 | YELLOW |
| RB Top 12 | `same_year_rb_t12` | 989 | 106 | 883 | 378 | 10 | 2 | GREEN |
| RB Top 24 | `same_year_rb_t24` | 989 | 210 | 779 | 378 | 10 | 0 | GREEN |
| RB Top 36 | `same_year_rb_t36` | 989 | 305 | 684 | 378 | 10 | 0 | GREEN |
| RB Top 48 | `same_year_rb_t48` | 989 | 396 | 593 | 378 | 10 | 0 | GREEN |
| WR Top 6 | `same_year_wr_t6` | 1432 | 58 | 1374 | 555 | 10 | 10 | YELLOW |
| WR Top 12 | `same_year_wr_t12` | 1432 | 115 | 1317 | 555 | 10 | 0 | GREEN |
| WR Top 24 | `same_year_wr_t24` | 1432 | 221 | 1211 | 555 | 10 | 0 | GREEN |
| WR Top 36 | `same_year_wr_t36` | 1432 | 330 | 1102 | 555 | 10 | 0 | GREEN |
| WR Top 48 | `same_year_wr_t48` | 1432 | 433 | 999 | 555 | 10 | 0 | GREEN |
| TE Top 3 | `same_year_te_t3` | 827 | 29 | 798 | 306 | 10 | 10 | YELLOW |
| TE Top 6 | `same_year_te_t6` | 827 | 57 | 770 | 306 | 10 | 10 | YELLOW |
| TE Top 12 | `same_year_te_t12` | 827 | 113 | 714 | 306 | 10 | 0 | GREEN |
| TE Top 18 | `same_year_te_t18` | 827 | 162 | 665 | 306 | 10 | 0 | GREEN |
| TE Top 24 | `same_year_te_t24` | 827 | 210 | 617 | 306 | 10 | 0 | GREEN |

All results are counts only. No rates, probabilities, percentages, or bands were computed.

## 5. GREEN Support Heads

The following heads are viable for a future local shadow modeling evaluation only, subject to separate HQ approval:

- `same_year_qb_t12`
- `same_year_qb_t18`
- `same_year_qb_t24`
- `same_year_rb_t12`
- `same_year_rb_t24`
- `same_year_rb_t36`
- `same_year_rb_t48`
- `same_year_wr_t12`
- `same_year_wr_t24`
- `same_year_wr_t36`
- `same_year_wr_t48`
- `same_year_te_t12`
- `same_year_te_t18`
- `same_year_te_t24`

These GREEN labels do not approve model training. They only show enough count support to propose a future local shadow modeling experiment.

## 6. YELLOW Constrained Heads

The following heads remain constrained and require HQ limits before any future shadow modeling proposal:

- `same_year_qb_t6`
- `same_year_rb_t6`
- `same_year_wr_t6`
- `same_year_te_t3`
- `same_year_te_t6`

These heads are constrained because they have sparse-season support patterns even though they have nonzero positives and negatives across the historical window.

## 7. RED Blocked Heads

No evaluated candidate head received a RED support label in 5CL.

This does not mean any head is release-ready. All heads remain blocked from user-facing display and production use.

## 8. Release Stance

Model training remains blocked.

Probabilities remain blocked.

Exact percentages remain blocked.

Coarse bands remain blocked.

App wiring remains blocked.

Rankings/sorting and hidden sort keys remain blocked.

Promoted artifacts remain blocked.

No app-readable probability, band, or status output was created.

## 9. Recommendation

5CL recommendation: GREEN for internal support-count evaluation.

The next safe sprint is Sprint 5CM, a docs-only Phase 4 evaluation/display gate contract plan. Future local shadow modeling may be proposed next as a later HQ-gated sprint, but it must not be run by 5CL or 5CM.

## 10. Checks

Checks run:

- `python scripts\outcome_probability\audit_sprint_5cl_threshold_head_support_evaluation.py` passed
- `python -m py_compile scripts\outcome_probability\audit_sprint_5cl_threshold_head_support_evaluation.py` passed
- `git diff --check` passed

Ruff was not run because it is optional and no package installation is allowed. Pytest was not required because no production code or tests changed.
