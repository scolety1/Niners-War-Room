# Sprint 5ED - Local-Only Current Player Probability Dry Run

## Purpose

Sprint 5ED runs a quarantined local-only current-player probability dry run for the heads approved by 5EA through 5EC. This sprint creates local evidence only. It does not create app-readable output, UI/source display wiring, rankings/sorting fields, hidden sort keys, promoted artifacts, pushes, deploys, or releases.

## Inputs

| Input | Path |
| --- | --- |
| Rankings player pool evidence | `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv` |
| Current-player feature snapshots | `local_exports/outcome_probability/sprint_5aw_2026_identity_repair/current_2026_veteran_feature_snapshots_after_identity_repair.csv` |
| Historical feature/label training rows | Local 2010-2019 feature/label packages used by the Phase 5 harness |
| Modeling helper | `scripts/outcome_probability/run_sprint_5ct_phase5_candidate_modeling_harness.py` |

The dry run used the existing low-complexity logistic routine from the Phase 5 historical harness and the approved prior-completed-season feature allowlist. It trained no production model artifact and serialized no model object.

## Local-Only Outputs

Local-only evidence was written under:

`local_exports/outcome_probability/phase10_numeric_probability_display_runway/sprint_5ed_current_player_probability_dry_run/`

Files:

- `current_player_probability_dry_run.csv`
- `current_player_probability_dry_run_summary.json`
- `README.md`

These files are quarantined evidence only. They are not app-readable generated outputs and must not be committed.

## Approved Heads Emitted

Approved local dry-run heads:

- `qb_t12`
- `rb_t12`
- `rb_t24`
- `wr_t12`
- `wr_t24`
- `wr_t36`
- `te_t12`

`rb_t24` was included because Sprint 5EC explicitly upgraded it to GREEN for local-only dry-run inclusion. It remains blocked for app display until later gates pass.

## Player Pool And Join Result

| Metric | Count |
| --- | ---: |
| Rankings pool rows | 240 |
| Joined rows with at least one dry-run probability | 227 |
| Unavailable rows | 13 |

Position coverage:

| Position | Rows | Probability rows |
| --- | ---: | ---: |
| QB | 28 | 28 |
| RB | 79 | 76 |
| WR | 93 | 91 |
| TE | 32 | 32 |
| K | 8 | 0 |

Unavailable reasons:

| Reason | Count |
| --- | ---: |
| `missing_feature_snapshot` | 5 |
| `unsupported_position` | 8 |

No rookie rows were present in the observed Rankings pool. If rookies appear later, they must remain unavailable for veteran heads.

## Probability Range Checks

All emitted local-only probabilities were bounded between 0 and 1.

| Head | Rows | Min | Max |
| --- | ---: | ---: | ---: |
| `qb_t12` | 28 | 0.159153 | 0.817291 |
| `rb_t12` | 76 | 0.046747 | 0.726800 |
| `rb_t24` | 76 | 0.051962 | 0.859554 |
| `wr_t12` | 91 | 0.046274 | 0.645436 |
| `wr_t24` | 91 | 0.046449 | 0.863616 |
| `wr_t36` | 91 | 0.054992 | 0.933313 |
| `te_t12` | 32 | 0.089123 | 0.847874 |

These are local audit units only, not app display percentages.

## Missing-Feature And Unsupported-Player Handling

Rows without ready feature snapshots were marked unavailable. Kickers were marked unavailable as unsupported. Unavailable rows did not receive fake `0%` values.

The local evidence includes `outcome_probability_status` and `unavailable_reason` for audit. These are not ranking/sorting fields and are not app-readable outputs.

## Rookies And Unsupported Players

Rookies remain blocked from veteran heads. K rows remain unsupported. Future app-readable artifacts, if ever approved, must preserve fail-closed unavailable behavior for rookies, kickers, unsupported positions, and missing-feature rows.

## Quarantine And No-Wiring Confirmation

Sprint 5ED did not create:

- app-readable generated output;
- app UI/source display wiring;
- exact app display percentages;
- coarse display bands;
- rankings/sorting fields;
- hidden sort keys;
- promoted artifacts;
- production model artifacts;
- committed local exports.

## Recommendation

Verdict: GREEN for Sprint 5EE numeric probability artifact audit and human-review sample.

The dry run produced bounded local-only probability evidence for the approved head set, including explicitly gated `rb_t24`, and preserved unavailable handling for unsupported or missing-feature rows. The next sprint must audit this artifact before any app-readable artifact or display contract can be proposed.
