# Sprint 5BO: Grouped Calibration Package Adversarial Audit

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_INTERNAL_AUDIT_ONLY`

Release stance: `BLOCKED_FOR_RELEASE_DISPLAY_AND_SORTING`

## Scope

This audit reviews the Sprint 5BN grouped calibration local package and audit plan. The package remains research-only and must not be interpreted as a release, app display, coarse-band display, sorting signal, or promoted model artifact.

Audited evidence:

- `docs/outcome_probability/BUILD_SPRINT_5BN_GROUPED_CALIBRATION_LOCAL_PACKAGE_AUDIT_PLAN.md`
- `local_exports/outcome_probability/sprint_5bn_grouped_calibration_local_package/`
- Prior Outcome docs from Sprints 5BI through 5BM as needed for continuity.

Local export files reviewed:

- `artifact_quarantine_audit.csv`
- `excluded_group_policy.csv`
- `grouped_abstention_decisions.csv`
- `grouped_calibration_bins.csv`
- `grouped_calibration_summary.csv`
- `metadata_sprint_5bn.json`
- `README_SPRINT_5BN.md`

## Artifact Quarantine Result

Verdict: `PASS`

The 5BN package is confined to:

`local_exports/outcome_probability/sprint_5bn_grouped_calibration_local_package/`

The artifact quarantine audit records:

| Gate | Status | Result |
| --- | --- | --- |
| Output folder scope | pass | Local export only |
| App-readable probability or band table | pass | No app path written; every row marks `app_readable=no` |
| Rankings/sorting output | pass | Every row sets `sort_allowed=no` and `ranking_use_allowed=no` |
| Promoted artifact | pass | Only CSV, JSON, and README local research exports exist |

No app-readable probability table, band table, release table, model artifact, or promoted artifact was created.

## App And Import Isolation

Verdict: `PASS`

Searches for the 5BN package name and package file identifiers across `app`, `src`, `scripts`, `tests`, and `docs` found references only in the 5BN documentation. No app page, player-card component, release service, app loader, service import, hidden sort key, ranking path, or sorting path references the 5BN local package.

The package remains non-imported and non-app-readable.

## Inclusion And Exclusion Audit

Verdict: `PASS`

The included groups match the 5BM/5BN candidate list:

| Included group | Label |
| --- | --- |
| `rb_upper_t36_t48_grouped` | RB T36/T48 grouped |
| `rb_broad_t24_t36_t48_grouped` | RB T24/T36/T48 grouped |
| `pooled_rb_wr_t24` | RB+WR pooled T24 |
| `pooled_rb_wr_t36` | RB+WR pooled T36 |
| `broad_rb_wr_t24_t36_t48_grouped` | RB/WR T24/T36/T48 grouped broad diagnostic |

The explicit exclusions are honored:

| Excluded item | Audit result |
| --- | --- |
| RB T6 | excluded as sparse T6 head |
| WR T6 | excluded as sparse T6 head |
| Pooled T6 | excluded as sparse |
| T12 individual/pooled release research | excluded and context-only |
| WR-only broad groups | excluded as unstable |
| Pooled T48 | excluded for validation large-gap failure |

No unexpected group, threshold, pooled T6, T12 release research, WR-only broad group, or pooled T48 candidate appears in the included package decisions.

## Stability And Abstention Recheck

Verdict: `PASS_INTERNAL_DIAGNOSTIC_ONLY`

The 5BN package uses 2-bin grouped calibration diagnostics. Every included group has validation and test rows, all rows are marked `internal_only_not_app_readable`, and all release flags remain blocked.

| Group | Validation rows/events | Validation max gap | Test rows/events | Test max gap | Abstention result |
| --- | ---: | ---: | ---: | ---: | --- |
| RB T36/T48 grouped | 212 / 75 | 0.060899 | 196 / 78 | 0.131621 | internal diagnostic candidate only |
| RB T24/T36/T48 grouped | 318 / 97 | 0.023135 | 294 / 100 | 0.092922 | internal diagnostic candidate only |
| RB+WR pooled T24 | 260 / 43 | 0.064447 | 261 / 43 | 0.064878 | internal diagnostic candidate only |
| RB+WR pooled T36 | 260 / 63 | 0.098118 | 261 / 65 | 0.089684 | internal diagnostic candidate only |
| RB/WR T24/T36/T48 grouped broad diagnostic | 780 / 188 | 0.102027 | 783 / 194 | 0.103564 | internal diagnostic candidate only |

All five groups pass the 5BN internal grouped diagnostic screen. This does not make any group release-ready. The package correctly preserves `release_status=blocked_not_release_ready`, `exact_percentage_display_allowed=no`, `coarse_band_display_allowed=no`, `sort_allowed=no`, `ranking_use_allowed=no`, and `app_readable=no`.

## Semantic-Risk Audit

Verdict: `PASS_WITH_RELEASE_BLOCK_REQUIRED`

Semantic-risk disclosures are present and appropriate:

- RB T36/T48 grouped blends adjacent RB threshold semantics.
- RB T24/T36/T48 grouped blends broader RB threshold semantics.
- RB+WR pooled T24 and pooled T36 can hide position-specific calibration differences.
- The broad RB/WR T24/T36/T48 diagnostic pools both positions and thresholds and carries the highest interpretability risk.

These disclosures support internal diagnostics only. They do not support player-facing exact percentages, coarse bands, sorting, ranking, or release-service use.

## Rookie And Population Isolation

Verdict: `PASS`

No rookie framework files were touched by 5BN, and the 5BN package does not create rookie probabilities or score rookies through veteran heads. Package candidates are limited to veteran RB/WR grouped calibration diagnostics.

## Release And Display Gate

Verdict: `BLOCKED`

The following remain blocked after audit:

| Gate | Status |
| --- | --- |
| Exact percentage display | blocked |
| Coarse-band display | blocked |
| App wiring | blocked |
| Rankings/sorting | blocked |
| Hidden sort keys | blocked |
| Player-card display | blocked |
| Release service/app loader | blocked |
| Promoted artifacts | blocked |
| Rookie framework work | blocked |

No candidate group is release-ready. The only safe next use is internal adversarial review of the grouped diagnostic policy and continued research on whether grouped calibration can be made interpretable without becoming misleading.

## Final Audit Conclusion

Sprint 5BO audit verdict: `GREEN_INTERNAL_AUDIT_ONLY`

The 5BN grouped calibration local package is properly quarantined, internally labeled, non-app-readable, non-sortable, and blocked from release. Candidate inclusions and exclusions match the approved 5BM/5BN scope. Stability and abstention claims are supported for internal diagnostics, but semantic risk remains too high for player-facing display.

Final gate label:

`GROUPED_CALIBRATION_PACKAGE_AUDITED_INTERNAL_ONLY_RELEASE_BLOCKED`
