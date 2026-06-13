# Sprint 5BD Constrained/Ordinal Threshold Model Design

## 1. Executive Verdict

Verdict: `CONSTRAINED_ORDINAL_DESIGN_READY_FOR_INTERNAL_PROTOTYPE`

Sprint 5BD defines the next internal model-design path for NWR threshold probabilities after Sprint 5BC showed that post-hoc clamping can remove RB/WR monotonicity violations but invalidates prior calibration claims for the repaired values.

The recommended path is an internal-only cumulative/ordinal or shared constrained-threshold prototype. The goal is to make monotonicity a model property, not a release-time patch. This design does not approve app display, exact percentages, player-facing bands, rankings/sorting, app-readable probability tables, fake probabilities, or promoted model artifacts.

Current release state:

- Exact percentages remain blocked.
- App wiring remains blocked.
- Rankings and sorting remain blocked.
- Player-facing bands remain blocked.
- Coarse-band research may continue only as quarantined internal research.
- No head is app-ready.

## 2. Inputs And Artifacts Reviewed

Reviewed prior sprint findings:

- Sprint 5BB threshold semantics contract:
  - Thresholds mean "top-N-or-better."
  - RB/WR chains must satisfy `P(T6) <= P(T12) <= P(T24) <= P(T36) <= P(T48)`.
- Sprint 5BC monotonic repair prototype comparison:
  - RB raw: 3 violations across 3 players, max gap `0.012790`.
  - WR raw: 27 violations across 15 players, max gap `0.002894`.
  - Post-hoc clamping benchmark: 0 adjacent-pair violations after repair.
  - Clamped outputs require fresh calibration validation.
  - Clamping remains an internal benchmark only.

No model was trained in Sprint 5BD. No probability or band output was generated.

## 3. Current Blocker Summary

The current blocker is not only monotonicity. It is the full release-gate stack:

- Raw independent threshold heads can contradict top-N-or-better semantics.
- Post-hoc clamping fixes ordering in the benchmark but changes output values.
- Repaired values invalidate prior calibration claims and require fresh validation.
- Sparse top-threshold heads remain fragile, especially T6-style heads.
- Partial coverage remains unresolved for blocked/waived players.
- Coarse bands are research-only and not app-approved.
- No probability output may be app-readable, hidden-sortable, or player-facing.

Therefore, the next safe step is an internal prototype that compares constrained threshold designs against the independent-head and clamping baselines while preserving all guardrails.

## 4. Candidate Path Comparison Table

| Candidate path | Implementation complexity | Sample-size risk | Calibration risk | Monotonicity guarantee | Interpretability | Leakage/schema risk | Coverage risk | Sparse-head handling | Coarse-band research support | Could ever be app-safe after future validation? |
|---|---|---|---|---|---|---|---|---|---|---|
| Post-hoc clamping benchmark | Low | Low direct implementation risk; inherits model support limits | High unless recalibrated after repair | Guaranteed on clamped output only | High; easy to explain as threshold-order enforcement | Low if applied only to legal internal outputs | Does not solve missing/blocked player coverage | Does not solve sparse labels; only repairs output order | Useful as internal benchmark | Possible only as part of a validated calibrated pipeline, not standalone |
| Cumulative/ordinal threshold model | Medium to high | Medium; rare top thresholds still need careful pooling/regularization | Medium; must calibrate jointly and by head | Strong if probabilities are derived from nested cumulative structure | Good if documented as top-N-or-better cumulative outcomes | Low if feature whitelist and split discipline hold | Does not solve coverage alone | Better than independent heads if it shares information across thresholds | Strong internal research candidate | Yes, but only after full validation and release gates |
| Shared constrained-threshold approach | Medium | Medium; shared base can help sparse heads but may underfit threshold differences | Medium; threshold intercepts/constraints need calibration audit | Strong if constraints are enforced; otherwise must be audited | Moderate to good | Low if no forbidden features enter | Does not solve coverage alone | Potentially useful via shared base model and threshold-specific intercepts | Strong internal research candidate | Yes, but only after full validation and release gates |
| Abstention/no-display path | Low | Lowest | Lowest because nothing is displayed | Guaranteed by not displaying unsafe outputs | Very high; conservative and easy to audit | Lowest | Avoids coverage overclaim | Handles sparse heads by withholding output | Allows research to continue without display pressure | Already safest app posture, but does not release probabilities |

## 5. Recommended Model Path

Recommended path: `CUMULATIVE_OR_SHARED_CONSTRAINED_INTERNAL_PROTOTYPE`

Sprint 5BE should prototype a constrained threshold design internally, comparing:

1. Raw independent heads baseline.
2. Post-hoc clamping benchmark.
3. Cumulative/ordinal threshold model.
4. Shared constrained-threshold model.
5. Abstention/no-display policy for sparse or unstable heads.

Preferred design principles:

- Preserve the 5BB top-N-or-better semantics.
- Enforce or prove `P(T6) <= P(T12) <= P(T24) <= P(T36) <= P(T48)` for RB/WR.
- Share information across thresholds to reduce independent-head contradictions.
- Keep sparse heads regularized and explicitly audited.
- Treat monotonicity as necessary but not sufficient.
- Keep all outputs internal-only, local-only, non-app-readable, and non-promoted.

The cumulative/ordinal path is the most semantically aligned. A shared constrained-threshold path is also viable if it explicitly enforces threshold ordering and is easier to implement with current tooling.

## 6. Validation Plan Required Before Release

No future release discussion should start until all of the following are complete:

1. Split discipline
   - Preserve historical train/validation/test separation.
   - Do not fit repair, calibration, bands, or thresholds on current 2026 player rows.

2. Feature legality
   - Use only the approved renamed preseason/prior-season feature schema.
   - Exclude ADP, public rankings, projections, consensus, market values, trade calculators, prior fantasy draft history, RotoWire rankings/projections/outlooks/values, legacy `private_score`, same-season final stats as preseason features, and label supplement sources as prediction features.

3. Monotonicity gate
   - Check every player, position, and adjacent threshold pair.
   - Report raw and repaired violations.
   - Require zero violations for any displayed head chain.

4. Calibration gate
   - Recompute calibration after any model or repair change.
   - Audit calibration by position/head and by bins.
   - Compare repaired outputs to baseline and empirical rates.

5. Performance gate
   - Report Brier/log-loss or appropriate proper scoring metrics.
   - Compare to empirical baselines and independent-head baselines.
   - Ensure improvements do not hide calibration failures.

6. Sparse-head gate
   - Separately audit T6/T3-style rare heads.
   - Permit abstention when support is not enough.

7. Coverage gate
   - Confirm blocked players remain unscored unless valid features are available.
   - Keep waived players unscored unless a future coverage sprint resolves them.
   - Keep rookies on a separate path.
   - Keep kickers not applicable.

8. App-output gate
   - Confirm no app-readable probability or band outputs exist.
   - Confirm no hidden sort keys, rankings effects, or decision automation.
   - Confirm no promoted model artifact exists.

9. Display gate
   - Run only after model, calibration, coverage, leakage, and app-output gates pass.
   - Exact percentages and coarse bands require separate display approval.

## 7. App And Output Quarantine Requirements

All future prototype outputs must remain:

- local-only
- uncommitted unless explicitly approved as a report
- not app-readable
- not player-facing
- not used for rankings
- not used for sorting
- not used for decision automation
- not packaged as promoted model artifacts

Prototype outputs must include explicit flags or documentation stating:

- `output_scope=internal_only_not_released`
- `app_release_status=blocked_not_app_readable`
- `sort_allowed=no`
- `ranking_use_allowed=no`
- `exact_percentage_display_allowed=no`
- `coarse_band_display_allowed=no`

No waiver, rookie, kicker, or blocked row may be forced through an incompatible scoring path. No missing player may receive fake or placeholder probabilities.

## 8. Risks And Failure Modes

Key risks:

- A monotonic model can still be poorly calibrated.
- Clamping can hide model instability rather than solve it.
- Sparse top thresholds can produce unstable calibration or misleading confidence.
- Shared constraints can underfit true threshold differences.
- Coarse bands can appear safer than exact percentages while still being miscalibrated.
- Partial coverage can make any app-facing release misleading.
- Internal outputs can become risky if copied into app-readable tables.
- Hidden sort keys or ranking effects would violate the current release gate.

Failure modes that should stop a future prototype:

- Any forbidden feature enters the model path.
- Any current-year label or same-season final stat is used as a preseason feature.
- Any model output is written into app code or app data.
- Any promoted artifact is created without explicit approval.
- Any hidden ranking/sorting field is created.
- Any blocked, waived, rookie, or kicker row is scored through the wrong path.
- Any exact percentage or band is presented as player-facing.

## 9. Next Safe Sprint Recommendation

Recommended next sprint: `Sprint 5BE - Internal Constrained Threshold Prototype`

Safe scope:

- Build a local-only constrained/ordinal prototype if feasible.
- Compare it to raw independent heads and post-hoc clamping.
- Re-run monotonicity, calibration, sparse-head, coverage, leakage, and app-output audits.
- Produce local-only research exports and a tracked report.

Explicitly out of scope for 5BE:

- app wiring
- app-readable probability tables
- player-facing percentages
- player-facing bands
- rankings/sorting changes
- decision automation
- promoted model artifacts
- fake probabilities
- forced scoring of blocked, waived, rookie, or kicker rows

## 10. Final Gate Label

Final gate label: `CONSTRAINED_ORDINAL_DESIGN_READY_FOR_INTERNAL_PROTOTYPE`

Meaning:

- The constrained/ordinal design is ready for an internal prototype sprint.
- No release model was trained.
- No app-readable probability or band output was created.
- No promoted artifact was created.
- Exact percentages remain blocked.
- App wiring remains blocked.
- Coarse-band research remains internal-only.
- No head is app-ready.
