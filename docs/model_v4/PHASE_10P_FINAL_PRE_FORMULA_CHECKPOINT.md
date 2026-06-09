# Phase 10P Final Pre-Formula Checkpoint

Date: 2026-05-17

## Superseded Traceability Note

This Phase 10P checkpoint is preserved as the pre-10Q/10R audit handoff and is
superseded by:

- `docs/model_v4/PHASE_10Q_WORKOUT_MISSINGNESS_AND_SOURCE_LANE_REPAIR.md`
- `docs/model_v4/PHASE_10R_PROSPECT_FORMULA_ADMISSION_HARDENING.md`
- `docs/model_v4/PHASE_10N_EVIDENCE_ADMISSION_RECHECK.md`

The audit found focused source/admission issues after this checkpoint. Those
repairs are complete:

- Workout zero placeholders are repaired to missing values with explicit warning
  codes.
- `college_production` and `college_market_share` are prospect-prior evidence.
- CFBD source status is redistribution-limited but formula-admitted after
  validation.
- `admitted_prospect_current_feature_matrix.csv` is the formula-facing prospect
  matrix.
- Current prospects: 232.
- Admitted prospect identities: 211.
- Admitted prospect feature rows: 211.
- Review-only prospects: 21.
- Phase 10N now runs 14 checks with 0 issues.
- Current status: `ready_for_formula_design_review`.

## Purpose

Phase 10P reviews the completed pre-formula data spine after Phase 10M identity admission repair, Phase 10N evidence admission recheck, and Phase 10O research-to-formula requirements lock. This checkpoint decides whether Model v4 is ready for an external pre-formula audit.

This is not a formula design phase. It does not calculate scores, final rankings, roster decisions, or app-facing values.

## Verdict

**Ready for pro audit.**

The data spine is ready to be audited externally before formula work begins. It is not yet cleared for formula implementation or app promotion. The next step should be the external pre-formula audit, with formula design blocked until that audit returns a pass or actionable repairs are completed.

## Source Inventory Status

Phase 10A source inventory is complete enough for audit review.

| Metric | Value |
| --- | ---: |
| Total inventoried files | 640 |
| Raw files hash-frozen | 502 |
| Processed/generated files recorded | 138 |
| Files allowed for private value after validation | 413 |
| Context/projection/market files excluded from private value | 24 |
| Files without nearby README/MANIFEST | 111 |
| Issues logged | 397 |
| High-severity issues | 10 |
| Medium-severity issues | 310 |

Important status:

- Raw/source files were hash-frozen.
- Paid/source raw files are preserved locally and should not be redistributed unless permitted.
- Market, ranking, ADP, and projection files are present but excluded from private football value.
- Third-party combine/pro-day data remains source-limited because local downloaded files did not include a license.
- These source inventory issues are governance items for audit visibility, not formula-facing admissions.

## First-Down Admitted Views

Phase 10B first-down canonicalization is complete and produced matched-only admitted views.

| Metric | Value |
| --- | ---: |
| Canonical rushing rows | 350 |
| Canonical receiving rows | 575 |
| Imported real-data rows | 925 |
| Admitted rushing rows | 334 |
| Admitted receiving rows | 539 |
| Missing joins | 23 |
| Ambiguous joins | 29 |

Important status:

- 2024 rushing missing header was inferred and documented.
- 2024 receiving repeated header row was removed.
- 2025 receiving exact duplicate rows were removed.
- Formula-facing first-down views include matched joins only.
- Ambiguous and missing joins remain outside admitted views.
- First downs are marked as imported real data where admitted.

## Return Admitted View

Phase 10C return canonicalization is complete and produced a matched-only admitted return scoring view.

| Metric | Value |
| --- | ---: |
| Canonical return rows | 302 |
| Imported real-data rows | 302 |
| Admitted return rows | 241 |
| Missing joins | 53 |
| Ambiguous joins | 8 |
| Total return yards in canonical data | 87,959 |
| Total return TDs in canonical data | 34 |
| Total return LVE points if used | 3,067.98 |

Important status:

- Return data remains direct scoring evidence only.
- Return data is explicitly not admitted as a major talent or role signal.
- Formula-facing return view includes matched joins only.
- Return scoring role is `small_direct_return_scoring_evidence_not_talent_signal`.

## Prospect Identity Admission Status

Phase 10M repaired the current-prospect identity layer and regenerated the evidence matrices.

| Metric | Value |
| --- | ---: |
| Current prospects | 232 |
| Admitted current prospect identities | 211 |
| Review-only current prospect identities | 21 |
| Admission notes rows | 232 |
| Historical rookie backtest rows | 395 |
| Source coverage rows | 3,927 |
| Warning rows | 1,602 |

Important status:

- Current-prospect formula admission is explicit.
- Review-only current prospects are excluded from formula-admitted identity spine.
- `Nick Singleton` is explicitly aliased to `Nicholas Singleton` after source alignment.
- Generic source `player_id` values are namespaced so CFBD and RotoWire IDs cannot collide.
- Recruiting positions no longer veto admission by themselves.
- Transfer and current-college mismatches remain quarantined unless source compatibility is clear.

## Unresolved Current Prospects

Twenty-one current prospects remain review-only.

| Review reason | Count |
| --- | ---: |
| insufficient_identity_support | 12 |
| position_conflict | 9 |

These are not hidden blockers. They are intentionally excluded from the admitted identity spine and must remain unavailable to formula loaders unless a later identity phase admits them with clear evidence.

## Historical Backtest Safety

The historical duplicate-name and post-draft college-evidence failure found by the external audit has been repaired.

Current safety status:

- Historical post-draft college evidence violations: 0
- Duplicate entity rows: 0
- Ambiguous join rows: 0
- Historical college evidence after draft year is now quarantined if detected.
- Same-name collision risks are surfaced as warnings instead of silently joined.

The historical rookie backtest matrix is therefore ready for external pre-formula audit, but not yet approved for formula training until that audit passes.

## Leakage Checks

Phase 10N ran 13 admission and leakage checks.

| Check family | Status |
| --- | --- |
| Required outputs present | pass |
| Duplicate entity rows | pass |
| Historical post-draft college evidence | pass |
| Private-lane market leakage | pass |
| Fake-zero missing evidence | pass |
| Review-only VORP namespace | pass |
| Source-limited combine private value | pass |
| Return direct scoring only | pass |
| First-down admitted views matched only | pass |
| Return admitted view matched only | pass |
| Source labels and receipts present | pass |
| Review-only prospects quarantined | pass |
| No formula scoring or rank generation | pass |

Phase 10N status:

- Checks run: 13
- Failed checks: 0
- Issues: 0
- Market leakage violations: 0
- Fake-zero missing violations: 0
- Formula scores calculated: False
- Final rankings calculated: False

Phase 10N also caught and removed two leakage leftovers before this checkpoint:

- `metric_rank` inside role-usage derived evidence
- recruiting `ranking` inside prospect-prior evidence

## Source Trust Contract

Phase 10F source trust contract remains the active field-lane policy.

Classification counts:

| Classification | Count |
| --- | ---: |
| context_only | 7 |
| derived_evidence | 7 |
| market_context_only | 6 |
| prospect_prior_evidence | 6 |
| rejected | 3 |
| scoring_evidence | 5 |
| source_limited | 2 |

Core locked rules:

- ADP, rankings, cheat sheets, mock drafts, and big boards are market or sanity context only.
- Imported projections and projected fantasy totals cannot directly drive private football value.
- League rank cannot drive Dynasty Asset Value.
- Market and liquidity remain separate from private football value.
- Missing data remains missing/unavailable/review; it cannot become zero or average evidence.
- Source-limited data must stay review-only until provenance and licensing are accepted.

## Deep Research Requirements Lock

Phase 10O converted the preserved Deep Research and audit reports into a formula requirements lock at:

`docs/model_v4/PHASE_10O_FORMULA_REQUIREMENTS_LOCK.md`

Locked formula-design requirements include:

- RBs are short-window, role, first-down, red-zone, and age-fragility assets.
- WRs are target-earning, route, YPRR, air-yard, first-down, and age-curve assets.
- QBs must be valued through 10-team 1QB VORP, with rushing-age caution.
- TEs receive no structural TE premium; route and target dominance must create the VORP gap.
- Rookie/prospect scoring must be separate from veteran NFL evidence.
- Draft capital is a strong starting prior but decays after NFL evidence arrives.
- First downs are core scoring evidence when directly sourced.
- Return scoring is direct scoring evidence only and must be capped as a talent signal.
- Market, rankings, projections, and consensus remain excluded from private value.
- Missing evidence triggers confidence caps and warnings, never positive evidence.

Research remains formula-design guidance only. It is not player evidence.

## Remaining Blockers

No blocker prevents an external pre-formula audit.

Remaining non-blocking audit items:

- 21 current prospects remain review-only and must stay quarantined.
- Third-party combine/pro-day data remains source-limited until license/source status is accepted or replaced.
- 111 inventoried files lack nearby README/MANIFEST notes, though they are hash-frozen.
- 1,602 warning rows remain in the evidence matrix output; these are expected audit visibility rows, not hidden pass/fail blockers.
- Formula implementation remains blocked until external pre-formula audit passes.

## Safety Confirmations

- No formulas were implemented in this phase.
- No formula scores were calculated.
- No final rankings were calculated.
- No active rankings were changed by Phase 10P.
- My Team was not changed by Phase 10P.
- War Board was not changed by Phase 10P.
- No readiness gates were unlocked.
- No app promotion was performed.
- Phase 10P created this checkpoint document only.

## External Audit Ask

The pro auditor should verify:

- whether the admitted evidence spine is clean enough for formula work
- whether the remaining 21 current prospects are properly quarantined
- whether first-down and return admitted views are safe and matched-only
- whether source-limited combine/pro-day data is truly unable to drive private value
- whether market/rank/projection fields remain excluded from private football value
- whether the Deep Research requirements lock is complete enough for formula design
- whether any source, identity, or documentation blocker remains before formula implementation

## Final Status

Model v4 is ready for external pre-formula audit.

Formula design remains blocked unless the next audit passes or its repair items are completed.
