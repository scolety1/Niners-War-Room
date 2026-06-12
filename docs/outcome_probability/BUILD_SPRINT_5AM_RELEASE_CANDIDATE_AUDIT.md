# Build Sprint 5AM Release-Candidate Audit

## Verdict

`KEEP_STATUS_ONLY_RECOMMENDED`

Same-year outcome outputs have enough internal aggregate support to keep researching future app-safe labels, but they are not stable enough for release of exact probabilities, probability bands, rankings, sorting, or decision automation. Any future label path must remain non-sortable, player-card-only, and separately approved by HQ.

## Scope

Question audited: Are same-year outcome outputs stable enough to even consider future coarse, non-sortable labels or bands on the player detail card?

This audit is not a release. It did not train a model, fit calibration, create app probabilities, create calibrated probabilities, create player-facing probabilities, create rankings, change sorting, create decision automation, promote artifacts, push, or deploy.

## Evidence Reviewed

- Sprint 5AC overnight handoff.
- Sprint 5AD internal calibration audit.
- Sprint 5AE internal calibration adversarial audit.
- Sprint 5AF release gate status contract.
- Sprint 5AG release gate adversarial audit.
- Sprint 5AH status-only display adapter.
- Sprint 5AI status-only display audit.
- Sprint 5AJ player detail wiring.
- Sprint 5AK player detail adversarial audit.
- Sprint 5AL status-only app checkpoint.
- `src/services/nwr_outcome_release_gate_service.py`
- `src/services/nwr_outcome_status_display_service.py`
- `src/services/player_detail_card_service.py`
- Relevant focused tests.

## Target Findings

| Target | Internal data support | Validation/calibration warnings | Exact probability release | Coarse label path | Misinterpretation risk | Recommended state |
| --- | --- | --- | --- | --- | --- | --- |
| `same_year_difference_maker` | Aggregate same-year internal support exists in the expanded 2020-2024 package. | Sparse/zero-event bin risk and no released calibration layer. | Blocked. | Consider research only after more validation and display-gate work. | High, because users may read any label as draft advice. | `keep_status_only` |
| `same_year_starter` | Aggregate same-year internal support exists and is part of the monotonicity chain. | Calibration stability is not release-ready; monotonicity must pass before any future release. | Blocked. | Could be considered later as non-sortable text only. | Medium-high, because "starter" can sound actionable. | `consider_coarse_labels_later` |
| `same_year_useful` | Aggregate same-year internal support exists and is likely the broadest support bucket. | Calibration and bin stability remain insufficient for release. | Blocked. | Best candidate for later coarse-label research, not release. | Medium, but still probability-like if phrased poorly. | `consider_coarse_labels_later` |
| `same_year_replacement_or_bust` | Aggregate same-year internal support exists, but framing is more negative/actionable. | Needs stronger validation, copy review, and leakage review before display. | Blocked. | Research only; avoid app label until UX risk is reduced. | High, because "bust" can imply cut/avoid advice. | `needs_more_validation` |

## Release-Candidate Assessment

Current support is internal-only. Sprint 5AD found same-year outcomes usable for aggregate calibration discussion, but not for production/app release. Sprint 5AE confirmed those claims were not overstated. Sprint 5AF/5AG require all release gates, an explicit release payload, monotonic same-year checks, and HQ approval before any app-facing probability-like output.

Exact percentages remain blocked. Probability bands remain blocked. Coarse labels are not approved for the app now. They may be researched later only if they are non-sortable, player-card-only, guarded by final leakage/display-gate review, and worded so users do not treat them as odds, ranks, or recommendations.

## Required Evidence Before Any Future Coarse Label

- Fresh validation evidence for each same-year target.
- Calibration stability evidence that does not rely on sparse bins.
- Final leakage audit.
- Confidence/display gate.
- Copy and UX review that confirms labels do not imply odds or advice.
- Documentation/model-card gate.
- Operational safety gate.
- HQ approval.
- Monotonicity check: `difference_maker <= starter <= useful`.
- Explicit sort/ranking block.

## Blocked

- Exact percentages.
- Calibrated probabilities.
- Player-facing probability numbers.
- Probability bands.
- Hidden sortable values.
- Ranking or sorting by outcome model output.
- Decision automation.
- App-readable probability tables.
- Promoted or released model artifacts.
- `next_year_starter`, multi-year targets, and hazard windows.

## Local Exports

Local-only exports were written under:

`local_exports/outcome_probability/sprint_5am_release_candidate_audit/`

## Recommendation

Keep status-only for now. Future coarse labels can be researched, but not displayed, until validation, calibration stability, leakage, display-gate, monotonicity, and HQ approval gates pass.
