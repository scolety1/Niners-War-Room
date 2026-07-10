# Formula Temporal Validation Framework and Prospective 2026 Challenger Freeze V1

## PRE-REGISTRATION LOCK

**Lock version:** `V1_20260710`  
**Lock effective timestamp:** `2026-07-10T22:34:06Z`  
**Repository base:** `c8c798cf0987a4ddc10dc7668a494e7569bfe960`  
**Accepted controlling audit commit:** `dce5131d77f9fb671bdf6141650677d2a3444641`  
**Accepted temporal correction commit:** `a7c738446a8b9481545119eea778a5fb3a314b66`  
**Lane branch:** `work/formula-temporal-validation-prospective-2026-challenger-freeze-v1-20260710`  
**Status:** `LOCKED_BEFORE_ANY_SCORED_ROLLING_ORIGIN`

This file freezes the complete experiment specification before any historical rolling-origin score is generated. Once `PRE_REGISTRATION_HASH.txt` records this file's SHA-256, this file is immutable. Any necessary departure must be appended to `DEVIATION_LEDGER.csv`. A material departure invalidates V1; results must be discarded and a new version preregistered before rescoring.

All 2013–2025 results are `RETROSPECTIVE_TEMPORAL_VALIDATION_WITH_PRIOR_SELECTION_CAVEATS`. They may screen stability and architecture; they cannot independently prove production superiority. The Formula Mart's row-level `training_allowed=false` and `model_use_allowed=false` stamps remain controlling for production. This HQ-authorized lane fits the new candidate only for bounded review-only temporal validation.

## 1. Controlling evidence and non-reexecution rule

The accepted Formula Accuracy Reassessment is not rerun. These values and interpretations are controlling:

- PYF: `0.741285` ranking-aligned and `0.693350` pooled raw-score.
- Exact `GAUNTLET_081`: `0.754604` ranking-aligned and `0.708315` pooled raw-score.
- Ranking-aligned and pooled raw-score scoreboards answer different questions.
- The former 70/20/10 ranking proxy is retired as a Formula Gauntlet comparator.
- The earlier fixed ridge diagnostic failed its positional-stability gate.
- No historical result is fresh, untouched, or production proof.

## 2. Candidate registry lock

Exactly three historical candidates will be scored. No grid, alternate penalty, alternate lambda, blend, tree model, boosted model, fallback feature set, replacement model, or post-result variant is permitted.

### 2.1 Baseline: `PYF`

- Role: controlling baseline.
- Historical raw score: Formula Mart `pyf_prior_nwr_points`.
- 2026 raw score: admitted completed-feature input `prior_nwr_points`.
- Direction: higher raw score is better.
- Fit: none.
- Eligibility: a row is valid when identity, season, position, score, and required outcome fields for the applicable evaluation are valid.

### 2.2 Locked legacy comparator: `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE`

- Role: fixed legacy research reference; never eligible to become the newly discovered challenger.
- Historical base score: Formula Mart `prior_3yr_weighted_nwr_points` exactly as executed by the accepted Gauntlet runner.
- Modifier: multiply the base by `0.98` if `age_bucket == age_32_plus` **or** `lifecycle_bucket == late_career_10_plus`; otherwise multiply by `1.00`.
- Direction: higher raw score is better.
- Fit: none at any origin.
- Required identity join: exact `(player_id, target season, position)` to the age/lifecycle sidecar. Missing or conflicting identity/age-lifecycle status invalidates the row; it is not inferred by name.
- Prior-selection caveat: the candidate was selected using full-history evidence through 2025. Rolling results are stability diagnostics, not an untouched proof.

The registry alias `three_60_30_10` is semantically inaccurate. The accepted runner returns `prior_3yr_weighted_nwr_points` directly. The accepted Mart builder derives that field using weights `0.60/0.25/0.15` over N-1/N-2/N-3 and renormalizes over present years. V1 locks the accepted field-execution behavior, not a newly reconstructed 60/30/10 formula.

For 2026 only, construct the same base deterministically from N-1=2025, N-2=2024, and N-3=2023 NWR points using weights `0.60/0.25/0.15`, dropping unavailable older years and dividing by the sum of weights that remain. N-1 is required. Apply the same `0.98` late guard using age as of 2026-09-01 and lifecycle years since draft/rookie year. No missing older year is copied from another year.

### 2.3 New candidate: `POSITION_SPECIFIC_RIDGE_ALPHA_1_V1`

- Role: the only candidate eligible for `PROSPECTIVE_2026_REVIEW_ONLY_CHALLENGER`.
- Model family: position-specific regularized linear regression (ridge).
- Supported positions: QB, RB, WR, TE only.
- Unsupported positions: K, DEF/DST, FB, and every other position; reason `POSITION_OUTSIDE_FROZEN_QB_RB_WR_TE_SCOPE`.
- Separate fits: one model for every `(target season origin, position)`; no pooled-position fit.
- Target: `label_next_nwr_points` in raw NWR points; higher is better.
- Intercept: yes, unpenalized.
- Regularization parameter: `alpha = 1.0` under the normalized objective
  `(1/n) * ||y - X beta||^2 + 1.0 * ||beta_nonintercept||^2`.
- Required solve: `beta = solve(X_design' X_design + n * diag(0,1,...,1), X_design' y)` using NumPy `linalg.solve`.
- Runtime: bundled Python 3.12.13 and NumPy 2.3.5. If this exact implementation is unavailable or the solve fails, the affected origin blocks the implementation. No pseudoinverse, package substitution, or different model is permitted.

#### Frozen numeric feature list

Every position uses these five common features, in this exact order:

1. `pyf_prior_nwr_points`
2. `pyf_prior_nwr_ppg`
3. `prior_opportunities`
4. `prior_games`
5. `age`

Position-specific features follow, in this exact order:

- QB: `prior_passing_attempts`, `prior_passing_yards`, `prior_passing_td`, `prior_passing_first_downs`.
- RB: `prior_touches`, `prior_carries`, `prior_rushing_yards`, `prior_rushing_first_downs`.
- WR: `prior_targets`, `prior_receptions`, `prior_receiving_yards`, `prior_receiving_first_downs`.
- TE: `prior_targets`, `prior_receptions`, `prior_receiving_yards`, `prior_receiving_first_downs`.

No sparse-history flag, low-games flag, role/archetype field, confidence field, current-season context, market field, proprietary current component, or outcome-derived field is a model input.

#### Frozen transformations and preprocessing

- Numeric transformation: identity only; no log, winsorization, clipping, polynomial, interaction, or age bucket feature.
- Missingness indicators: append one binary indicator for every numeric feature, in the same order; `1` means the original value was unavailable/non-finite and `0` means observed.
- Imputation: for each origin/position/feature, calculate the arithmetic mean from finite training values only. Impute missing training and scored values with that training mean.
- Standardization: after imputation, subtract the training mean and divide by the population standard deviation (`ddof=0`) fitted from training rows only.
- A zero training standard deviation is replaced with `1.0`.
- If a numeric feature has no finite training value, the origin is blocked; no default is substituted.
- After mean imputation, an originally missing numeric value has standardized value exactly `0.0`. This deliberately corrects the earlier diagnostic implementation defect; the defective implementation is not another candidate.
- Missingness indicators are not centered or scaled.
- Target is not standardized.
- Design-column order: intercept, standardized numeric features in frozen order, missingness indicators in frozen order.

## 3. Rolling-origin construction lock

- Historical target-season universe: 2013–2025 Formula Mart rows.
- Earliest supported scored origin: target season 2015.
- Scored origins: every target season 2015 through 2025 inclusive, subject only to hard source/identity/runtime gates.
- Independent target seasons expected: 11.
- For target season T, training includes only rows with target season `< T`.
- A position/origin fit requires at least 100 labeled training rows and at least two distinct earlier target seasons.
- A scored season-position metric requires at least 20 valid rows on its defined population.
- Feature season for a scored origin is T-1. No T or later fact may enter its features.
- Imputation, scaling, coefficients, and every learned value are fitted inside the origin on its training rows only.
- Future origins cannot influence earlier origins.
- Outcomes are joined to a prediction ledger only after origin predictions and their canonical hash are frozen.
- Exact legacy candidates do not fit; they still receive origin registry records and prediction hashes.
- Current-only data cannot be backfilled into a historical origin.

## 4. Identity, eligibility, duplicates, labels, and ranks

### 4.1 Historical identity and duplicates

- Shared identity key: `(target_season, position, player_id)` using the admitted GSIS-style `player_id`.
- `substrate_row_id` is the stable provenance guard.
- A duplicate historical identity key is a hard source/identity failure.
- Normalized name is never an identity key or fallback.
- Position must match exactly.

### 4.2 2026 identity and duplicates

- Use exact `player_id_gsis` from the admitted completed-feature input.
- Collapse only exact-identical duplicate player rows under the existing source policy.
- Any non-exact duplicate blocks the affected snapshot; do not choose by name.
- DynastyProcess DOB/draft joins use exact GSIS ID, prefer exact position where duplicate source rows exist, then nonmissing DOB and draft year. Conflicting DOB values hard-fail the player.
- Never zero-fill or infer a missing player-week/source row.

### 4.3 Historical player eligibility

A row is evaluation-eligible when:

- position is QB/RB/WR/TE;
- target season and feature season satisfy N→N+1;
- exact identity and provenance fields are nonempty and unique;
- Formula Mart leakage and as-of statuses pass;
- `label_next_nwr_points` and `label_next_position_finish` are finite;
- the applicable candidate can generate a finite score under its frozen rules.

The ridge may impute individual frozen numeric inputs under the locked preprocessing rule. Candidate-specific score invalidity remains visible and is never silently dropped from coverage reporting.

### 4.4 Target direction and actual label

- Ridge fitting target: raw `label_next_nwr_points`, higher is better.
- Evaluation truth: `label_next_position_finish`, lower is better.
- Canonical actual-startable status is recomputed as `actual finish <= cutoff`, where cutoffs are QB 10, RB 30, WR 40, TE 12.
- Formula Mart `label_startable_hit` is retained only for an audit mismatch check because its embedded cutoffs differ; it is not gate truth.

### 4.5 Prediction rank and ties

- Within each target-season/position/evaluation-population group, sort by raw score descending, then `player_id` descending, then `substrate_row_id` descending.
- Assign unique ordinal ranks `1..n` in that order.
- Shared-row ranks are recomputed on the shared population; full-population ranks remain separate.
- Correlation helper ranks use average ranks for any numeric ties.
- Spearman is Pearson correlation of average ranks.
- Kendall is tau-a: concordant minus discordant pairs divided by all `n(n-1)/2` pairs; a tie contributes zero to the numerator and remains in the denominator.

## 5. Shared-row and coverage evaluation lock

For every origin, position, and non-PYF candidate:

### 5.1 Primary comparative evaluation

- Use the exact intersection of rows scored validly by PYF and that candidate.
- The intersection key is `(target_season, position, player_id)`.
- Recompute both candidate and PYF ranks on this identical intersection.
- Record PYF-valid rows, candidate-valid rows, shared rows, rows lost by PYF, rows lost by the candidate, and every material exclusion reason.
- Candidate-minus-PYF correlation deltas come only from this shared-row evaluation.

### 5.2 Full-coverage evaluation

- Separately rank and evaluate each candidate on its complete valid eligible population.
- Report eligible universe, valid score rows, invalid score rows, coverage proportion, feature missingness, and exclusion reasons.
- Never combine shared-row and full-coverage numbers in one metric column or headline.
- A candidate cannot pass by excluding difficult rows.

## 6. Metric lock

### 6.1 Required group and balanced metrics

On every valid `(target season, position)` group, report Spearman and Kendall tau-a. Then report:

- Macro Spearman/Kendall: equal mean across all valid season-position groups.
- Position-balanced: first average group values across seasons within each of QB/RB/WR/TE, then give the four position means equal weight. All four positions are required.
- Season-balanced: first average the four positions within each season, then give each valid complete season equal weight. All four positions are required per season.
- Secondary micro: pooled Spearman over the already within-season-position prediction ranks and actual finishes across all scored rows. This is not the sole or primary gate.
- Candidate-minus-PYF delta by origin/season: equal mean of the four shared-row season-position Spearman deltas.
- Candidate-minus-PYF delta by position: equal mean across scored seasons.
- Leave-one-season-out stability: recompute the two balanced headline aggregates after omitting one frozen scored season; no model is refitted.

With a complete 11×4 grid, the arithmetic macro, position-balanced, and season-balanced means are algebraically equal; V1 will disclose this rather than manufacture different weights.

### 6.2 Top-K lock

Canonical position thresholds:

- QB: K=12.
- RB: K=12 and 24.
- WR: K=12, 24, and 36.
- TE: K=12.

For each valid group/population/K:

- hit count: predicted rank `<= K` and actual finish `<= K`;
- precision: hit count divided by predicted top-K count;
- recall: hit count divided by actual top-K count;
- metric unavailable if population `n < K`.

### 6.3 Canonical false-positive and false-negative lock

Startable cutoffs `C`: QB 10, RB 30, WR 40, TE 12.

- False positive: predicted rank `<= C` and actual finish `> C`.
- Severe false positive: predicted rank `<= C/2` and actual finish `> 1.5*C`.
- False negative: predicted rank `> C` and actual finish `<= C`.
- Severe false negative: predicted rank `> 1.5*C` and actual finish `<= C/2`.
- Net severe misses: severe FP + severe FN.

The severe definition is the canonical red-team definition, not the looser earlier diagnostic definition. New counts are therefore not presented as directly comparable to that diagnostic's counts.

## 7. Uncertainty lock

- Unit of independence: target season, not player row.
- Primary uncertainty inputs: paired candidate-minus-PYF season deltas, where each season delta is the equal mean of its four position deltas.
- Method: season-cluster bootstrap with replacement, 10,000 draws, deterministic NumPy RNG seed `20260710`.
- Interval: two-sided 95% percentile interval using the 2.5th and 97.5th percentiles.
- The same complete-season resamples are used for position-balanced and season-balanced summaries; with a complete grid the intervals may coincide.
- Minimum seasons for the uncertainty gate: 5.
- No player-row bootstrap, normal-theory player-row confidence interval, or claim of formal certainty is permitted.
- The exact number of independent scored seasons and the limitation of a small season count must be prominent.

## 8. Mechanical historical stability gate

`POSITION_SPECIFIC_RIDGE_ALPHA_1_V1` becomes a `PROSPECTIVE_2026_REVIEW_ONLY_CHALLENGER` only if every gate below passes. No aggregate gain compensates for any failure.

1. **Headline improvement:** both shared-row position-balanced Spearman delta and shared-row season-balanced Spearman delta versus PYF are strictly `> 0`.
2. **Not isolated to one season:** at least two target seasons have season delta `> 0`, and every leave-one-season-out position-balanced and season-balanced delta is strictly `> 0`.
3. **No material repeated position regression:** fail if any position has season-position Spearman delta `< -0.005` in two or more distinct seasons, or if that position's aggregate delta is `< -0.005`.
4. **No material severe-FP increase:** on paired shared rows, fail if challenger severe-FP count exceeds PYF overall or in any one position. Threshold is zero additional severe FPs. A severe-FN reduction cannot offset failure.
5. **No favorable coverage reduction:** fail if the challenger loses any row that PYF scores validly in any supported season-position group, or if challenger aggregate full-population coverage is below PYF coverage.
6. **Uncertainty review:** require at least five independent target seasons; the lower 95% season-cluster bootstrap bound must be strictly `> 0` for both balanced headline deltas; and the minimum leave-one-season-out headline delta must be strictly `> 0`.
7. **Source, leakage, identity, and runtime:** all source/as-of/leakage gates pass; no duplicate/identity failure; no blocked/current-only/proprietary input; every planned origin uses the exact locked implementation.

Candidate-selection rule: the ridge is the sole eligible new candidate. If all seven gates pass, freeze it once for 2026. If any gate fails, do not create `PROSPECTIVE_2026_CHALLENGER_FREEZE.csv`; record the absent artifact in the manifest and gate decision. `GAUNTLET_081` cannot be selected as the new challenger regardless of its historical result.

## 9. Prospective 2026 snapshot cutoff and freeze lock

### 9.1 Common cutoff

- Common snapshot freeze timestamp: `2026-07-10T22:34:06Z`.
- Prediction target: 2026 season, feature season 2025.
- All snapshots are review-only tracking artifacts.
- Inputs may have different original source dates; each difference must be recorded with source path, source-as-of description, and SHA-256.
- No 2026 outcome may enter a score, feature, fit, preprocessing statistic, coefficient, rank, or eligibility decision.

### 9.2 Required baselines regardless of ridge result

Freeze in `PROSPECTIVE_2026_BASELINE_FREEZE.csv`:

- PYF using the admitted completed-feature input.
- Exact `GAUNTLET_081` using the locked normalized-present multiyear construction and late guard.
- The exact current app-visible/current-board review artifact as a separately caveated comparator. Do not rebuild or approximate it. Preserve its original `nwr_rank`, `nwr_dynasty_score`, `score_as_of_date`, and review-only status. Its current-information and proprietary-component advantage makes it non-equivalent to the receipt-safe controlled formulas.

The controlled 2026 source universe will retain both score-valid and null-fenced rows after exact-duplicate collapse so coverage loss is visible. The current-board comparator retains its own exact source population.

### 9.3 Conditional ridge freeze

If and only if every historical stability gate passes:

- Fit one final model per supported position using all valid historical target-season rows 2013–2025.
- Fit imputation, scaling, and coefficients from those historical rows only under the locked specification.
- Score the admitted 2026 completed-feature population.
- Create `PROSPECTIVE_2026_CHALLENGER_FREEZE.csv` and label the model `PROSPECTIVE_2026_REVIEW_ONLY_CHALLENGER`.

If the ridge fails, its 2026 challenger file must not exist.

### 9.4 Immutable contents and corrections

For every frozen controlled prediction, record the freeze timestamp, feature cutoff, source dates, source hashes, Formula Mart hash, sidecar hashes, exact player ID, eligibility, raw feature values, imputed values, missingness indicators, model/formula version, coefficients or coefficient hash, raw score, within-position rank, any research overall rank, status, and prediction-file hash in the manifest/ledgers. The exact board comparator records its native fields and caveats rather than fabricated controlled-model features.

Once created and hashed, prediction files are immutable. A correction requires a separately versioned snapshot and retention of V1. Frozen predictions may not be updated after outcomes begin.

## 10. Outcome-evaluation and use restrictions

Future actual 2026 outcomes are required before any final accuracy claim. The future contract will compare frozen PYF, frozen exact legacy formula, the frozen ridge only if eligible, and the separately caveated current-board comparator using position metrics, top-K decisions, severe misses, coverage, and identity-safe joins.

Production/model-use remains blocked. Rankings integration remains blocked. App/runtime changes remain blocked. Source promotion remains blocked. These predictions cannot become hidden recommendations, sort logic, or automatic player decisions. No push is authorized.

## 11. Hashing and execution order

1. Write this complete lock.
2. Compute its SHA-256 and record it in `PRE_REGISTRATION_HASH.txt`.
3. Verify the hash immediately before scoring.
4. Generate and hash origin predictions before outcome joins.
5. Never modify this lock after step 2.
6. Append nonmaterial execution notes to `DEVIATION_LEDGER.csv`; stop and invalidate V1 on any material deviation.
