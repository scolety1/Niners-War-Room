# Sprint 5BN Grouped Calibration Local Package and Audit Plan

## 1. Executive verdict

Verdict: `GROUPED_CALIBRATION_LOCAL_PACKAGE_INTERNAL_ONLY_AUDIT_NEXT`

Sprint 5BN created an internal-only grouped calibration local package based on the 5BM research findings. The package includes only grouped candidates that 5BM identified as plausible internal diagnostics. All outputs remain local-only, not app-readable, not player-facing, not sortable, and blocked for release.

No grouped candidate is release-ready. The package is suitable only for adversarial audit and future internal diagnostic policy work.

Release stance remains unchanged:

- Exact percentages remain blocked.
- Coarse bands remain blocked.
- App wiring remains blocked.
- Rankings/sorting remain blocked.
- Promoted artifacts remain blocked.

## 2. Evidence reviewed

Documents reviewed:

- `docs/outcome_probability/BUILD_SPRINT_5BI_INTERNAL_HOLDOUT_CALIBRATION_PACKAGE.md`
- `docs/outcome_probability/BUILD_SPRINT_5BJ_5BI_HOLDOUT_CALIBRATION_AUDIT.md`
- `docs/outcome_probability/BUILD_SPRINT_5BK_CALIBRATION_INSTABILITY_ROOT_CAUSE.md`
- `docs/outcome_probability/BUILD_SPRINT_5BL_CALIBRATION_BIN_SENSITIVITY_ABSTENTION_POLICY.md`
- `docs/outcome_probability/BUILD_SPRINT_5BM_THRESHOLD_GROUPING_POOLED_CALIBRATION_RESEARCH.md`

Local-only input evidence:

- `local_exports/outcome_probability/sprint_5bi_internal_holdout_calibration_package/holdout_predictions_internal_only.csv`

## 3. Local-only package created

Package path:

`local_exports/outcome_probability/sprint_5bn_grouped_calibration_local_package/`

Files created:

- `artifact_quarantine_audit.csv`
- `excluded_group_policy.csv`
- `grouped_abstention_decisions.csv`
- `grouped_calibration_bins.csv`
- `grouped_calibration_summary.csv`
- `metadata_sprint_5bn.json`
- `README_SPRINT_5BN.md`

All outputs are marked:

- `output_scope=internal_only_not_app_readable`
- `app_release_status=blocked_not_app_readable`
- `exact_percentage_display_allowed=no`
- `coarse_band_display_allowed=no`
- `sort_allowed=no`
- `ranking_use_allowed=no`
- `app_readable=no`

These local exports must not be committed.

## 4. Candidate groups included

Included groups:

| Group ID | Label | Positions | Thresholds | Purpose |
|---|---|---|---|---|
| `rb_upper_t36_t48_grouped` | RB T36/T48 grouped | RB | T36/T48 | strongest upper RB grouped diagnostic |
| `rb_broad_t24_t36_t48_grouped` | RB T24/T36/T48 grouped | RB | T24/T36/T48 | broad RB grouped diagnostic |
| `pooled_rb_wr_t24` | RB+WR pooled T24 | RB/WR | T24 | same-threshold cross-position diagnostic |
| `pooled_rb_wr_t36` | RB+WR pooled T36 | RB/WR | T36 | same-threshold cross-position diagnostic |
| `broad_rb_wr_t24_t36_t48_grouped` | RB/WR T24/T36/T48 grouped | RB/WR | T24/T36/T48 | broad pooled diagnostic with high semantic risk |

## 5. Candidate groups excluded

Excluded groups:

| Excluded group | Reason |
|---|---|
| RB T6 | sparse T6 head under 5BL |
| WR T6 | sparse T6 head under 5BL |
| Pooled T6 | pooled T6 remains sparse |
| T12 individual/pooled release research | T12 remains abstain/context-only |
| WR-only broad groups | WR-only grouped candidates remain unstable |
| Pooled T48 | validation large-gap failure |

These exclusions must remain in force until additional legal data or a separate HQ-approved research sprint changes the evidence.

## 6. Stability and abstention summary

All included candidates passed the 2-bin internal diagnostic screen on both validation and test. This is not a release gate.

| Group | Validation rows/events | Validation max gap | Test rows/events | Test max gap | Abstention result |
|---|---:|---:|---:|---:|---|
| RB T36/T48 grouped | 212 / 75 | 0.060899 | 196 / 78 | 0.131621 | internal diagnostic candidate only |
| RB T24/T36/T48 grouped | 318 / 97 | 0.023135 | 294 / 100 | 0.092922 | internal diagnostic candidate only |
| RB+WR pooled T24 | 260 / 43 | 0.064447 | 261 / 43 | 0.064878 | internal diagnostic candidate only |
| RB+WR pooled T36 | 260 / 63 | 0.098118 | 261 / 65 | 0.089684 | internal diagnostic candidate only |
| RB/WR T24/T36/T48 grouped | 780 / 188 | 0.102027 | 783 / 194 | 0.103564 | internal diagnostic candidate only |

All candidates remain:

- blocked for exact percentages
- blocked for coarse bands
- blocked for app display
- blocked for sorting/ranking use
- blocked for promotion

## 7. Semantic-risk notes

Grouped calibration improves aggregate stability by pooling evidence, but it weakens player-facing interpretability.

| Group | Semantic risk |
|---|---|
| RB T36/T48 grouped | Blends top-36 and top-48 RB threshold semantics. |
| RB T24/T36/T48 grouped | Blends top-24/top-36/top-48 RB semantics. |
| RB+WR pooled T24 | Pools RB and WR at the same threshold and can hide position-specific calibration differences. |
| RB+WR pooled T36 | Pools RB and WR at the same threshold and can hide position-specific calibration differences. |
| RB/WR T24/T36/T48 grouped | Pools positions and thresholds; highest interpretability risk. |

Any future display proposal would need to prove these grouped diagnostics cannot be mistaken for exact probabilities, individual threshold probabilities, rankings, or draft recommendations.

## 8. Artifact quarantine result

Quarantine result: pass.

| Gate | Status | Evidence |
|---|---|---|
| Output folder scope | pass | `local_exports/outcome_probability/sprint_5bn_grouped_calibration_local_package/` |
| App-readable probability or band table | pass | no app path written; every row marks `app_readable=no` |
| Rankings/sorting output | pass | every row sets `sort_allowed=no` and `ranking_use_allowed=no` |
| Promoted artifact | pass | only CSV/JSON/README local research exports are written |

No app wiring, app loader, player card, ranking/sorting, release service, rookie framework, or promoted artifact was changed.

## 9. Adversarial audit plan

Recommended adversarial audit checks for the 5BN package:

1. Verify generated files exist only under the 5BN local export path.
2. Verify every row is marked `internal_only_not_app_readable`.
3. Verify every row sets display, app, sorting, and ranking flags to `no`.
4. Verify no app, Streamlit, player-card, ranking, sorting, or release path imports the package.
5. Verify excluded groups are absent from grouped summary and bin exports.
6. Verify T6 is excluded from all candidate groups.
7. Verify T12 is not used for release research.
8. Verify WR-only broad groups are absent.
9. Verify pooled T48 is absent.
10. Recompute validation/test bin stability from `holdout_predictions_internal_only.csv`.
11. Confirm each included group passes only as an internal 2-bin diagnostic candidate.
12. Confirm no candidate is described as release-ready.
13. Confirm grouped semantics are not represented as player-facing exact threshold probabilities.
14. Confirm pooled RB/WR candidates disclose position-masking risk.
15. Confirm no exact percentages, coarse bands, app wiring, rankings/sorting, or promoted artifacts are created.

## 10. Release-gate implications

No release gate is passed.

The grouped package is useful because it identifies candidate families for future internal diagnostics. It does not provide a safe player-facing probability surface.

Still blocked:

- exact percentages
- coarse bands
- app wiring
- rankings/sorting
- promoted artifacts

## 11. Recommended next safe sprint

Recommended next sprint: `Sprint 5BO - Grouped Calibration Package Adversarial Audit`

Scope:

- Audit the 5BN local-only package.
- Recompute grouped bin stability independently.
- Verify exclusions and quarantine.
- Decide whether grouped diagnostics should continue to policy design or whether the lane should pivot to larger historical universe feasibility.

Alternative:

- `Sprint 5BO - More Seasons / Larger Historical Universe Feasibility`

If HQ wants data breadth before more grouped calibration work, this is the safer alternate path.

## 12. Final gate label

Final gate label: `GROUPED_CALIBRATION_LOCAL_PACKAGE_INTERNAL_ONLY_AUDIT_NEXT`

Meaning:

- 5BN local-only grouped package was created.
- Included groups pass internal 2-bin diagnostics.
- Excluded groups remain blocked or abstained.
- Semantic risk remains material.
- No candidate is release-ready.
- Exact percentages remain blocked.
- Coarse bands remain blocked.
- App wiring remains blocked.
- Rankings/sorting remain blocked.
- Promoted artifacts remain blocked.
