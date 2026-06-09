# Phase 10U Renewed Pre-Formula Audit Prompt

You are a senior external/pro auditor reviewing a repaired local-first dynasty
fantasy football data spine before formula implementation begins.

Project context:

- Model v4 is for a 10-team, 1QB, non-PPR dynasty league with rushing and
  receiving first-down scoring.
- This is a pre-formula audit. Do not tune formulas, propose player rankings,
  or assume formula implementation has begun.
- The prior external audit found focused issues around workout zero placeholders,
  current-prospect formula admission, source-lane labels for college production,
  and CFBD source-status clarity.
- Phases 10Q, 10R, 10S, and 10T were completed to repair and recheck those
  issues.

Please verify:

1. Workout zero-placeholder repair:
   - Impossible workout/pro-day zeros are missing/null rather than poor athletic
     evidence.
   - `workout_metric_zero_placeholder_repaired` and
     `workout_metric_missing_after_zero_repair` are visible where appropriate.
   - No workout zero placeholder can drive prospect-prior value.

2. Prospect formula-admission hardening:
   - `prospect_current_feature_matrix.csv` has `formula_identity_admitted` and
     `excluded_reason`.
   - Review-only prospects have `formula_identity_admitted = False`.
   - Review-only prospects have populated `excluded_reason`.
   - `admitted_prospect_current_feature_matrix.csv` contains only admitted
     prospects.
   - The admitted prospect feature count matches the admitted identity spine.
   - Formula loaders should be able to fail closed on rows without
     `formula_identity_admitted == True`.

3. Source-lane correctness:
   - College production is `prospect_prior_evidence`, not generic
     `scoring_evidence`.
   - College market share is `prospect_prior_evidence`.
   - NFL production remains scoring evidence where appropriate.
   - CFBD/source statuses clearly distinguish redistribution-limited but
     formula-admitted-after-validation data from source-limited
     not-formula-admitted data.

4. First-down and return admitted views:
   - First-down admitted views are matched-only and direct imported real data.
   - Missing/ambiguous first-down joins are not silently admitted.
   - Return admitted view is matched-only.
   - Return production remains direct scoring evidence only, not a major talent
     or role signal.

5. Historical backtest safety:
   - Historical rookie rows do not contain post-draft college evidence.
   - Duplicate-name college contamination remains quarantined.
   - Historical rows do not include market/projection/post-hoc leakage.

6. Leakage and source-limited restrictions:
   - ADP, rankings, cheat sheets, mock drafts, big boards, market context,
     league rank, and imported projections are excluded from private football
     value lanes.
   - Source-limited combine/pro-day evidence cannot drive private value.
   - Missing data is not converted to zero, average, or positive evidence.
   - Warning/source-coverage matrices expose remaining risks clearly.

7. Final readiness:
   - Decide whether formula implementation can begin after this packet, or
     whether more identity/source/documentation repair is needed.

Output format:

- Start with a one-paragraph verdict.
- Then provide a triage table with severity, issue, affected files, and action.
- For each issue, include evidence from packet files, likely cause, and
  recommended next action.
- Separate formula/data issues from documentation-only issues.
- End with exactly one verdict:
  - `ready for formula implementation`
  - `ready after minor documentation cleanup`
  - `needs focused identity/source repair`
  - `needs source replacement`
  - `not ready for formula work`

Important constraints:

- Do not recommend formula tuning in this audit.
- Do not treat Deep Research reports as player evidence; they are formula-design
  guidance only.
- Do not treat market/ranking/projection data as private football value.
- Do not require raw paid/source files for this audit. They are intentionally
  excluded unless redistribution is explicitly safe.
