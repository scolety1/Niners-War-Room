# NWR Outcome Horizon Plan Recovery - 2026-06-22

## Final Verdict

YELLOW.

The remembered 2026, 2027, and next-5-year Outcome columns were real as a plan/contract and legacy UI scaffold, but they were not present in the current approved app-readable Outcome artifact. The later Outcome lane narrowed the approved draft-day surface to a small display-only numeric artifact with seven position outcome heads. No safe approved horizon artifact was found for tomorrow.

This recovery did not generate new probabilities, wire anything into the app, mutate the frozen board, update latest files, or change source truth.

## Short Answer

The 2026/2027/5-year Outcome plan appears to have been:

- planned in the June 10 Outcome column integration contract,
- represented in legacy Rankings UI groups as 2026 Outcomes, 2027 Outcomes, and 5-Year Outcomes,
- supported in lower-level training/source-manifest scaffolding through horizon names such as `year_1` and `next_5y`,
- later blocked/deferred for release because the probability lane did not have safe enough coverage/calibration/label maturity for app-facing horizon probabilities,
- replaced for draft-day app use by the narrower approved numeric display artifact:
  `numeric_outcome_display_v1.csv`.

The current app should continue using only the approved current Outcome heads and show missing values as `Not enough information`.

## Evidence Table

| Source | Commit / Date | Relevant Plan Or Columns | Status |
|---|---:|---|---|
| `app/legacy_pages/05_rankings_legacy.py` | Current file; history includes `b410ab3` and `953053e` | Legacy UI groups: `2026 Outcomes`, `2027 Outcomes`, `5-Year Outcomes`; labels include `T6 2026`, `T12 2026`, `T24 2026`, `T36 2026`, `T48 2026`, `T6 2027`, `T12 2027`, `T24 2027`, `T36 2027`, `T48 2027`, `T6 5Y`, `T12 5Y`, `T24 5Y`, `T36 5Y`, `T48 5Y` | Planned / legacy UI scaffold, not current approved artifact |
| `tests/test_dynasty_rankings_page.py` | Current file; history includes `b410ab3` and `953053e` | Tests expect the legacy horizon labels above | Planned / legacy placeholder coverage |
| `docs/model_v4/OUTCOME_COLUMN_INTEGRATION_CONTRACT_20260610.md` | `bfc817a`, 2026-06-10 | Initial expected columns: `top_6_2026_prob`, `top_12_2026_prob`, `top_24_2026_prob`, `top_36_2026_prob`, `top_48_2026_prob`, `top_6_2027_prob`, `top_12_2027_prob`, `top_24_2027_prob`, `top_12_next_5y_prob`, `useful_starter_prob`, `bust_prob` | Planned integration contract, not found as an approved CSV/JSON output |
| `src/services/nwr_outcome_feature_snapshot_service.py` and related outcome tests | Current files | Horizon scaffolding such as `target_horizon="year_1"` and tests for `target_horizon="next_5y"` label availability dates | Internal design support, not app-facing release |
| `C:\NWR\Niners-War-Room-outcome\docs\outcome_probability\BUILD_SPRINT_5AQ_ACTUAL_PROBABILITY_RELEASE_CANDIDATE.md` | Outcome repo history includes `c3345ac`, 2026-06-12 | Verdict `BLOCKED_BY_2026_FEATURE_COVERAGE`; no exact 2026 app probabilities safe to release; `next_year_starter` blocked by validation/maturity limitations | Horizon/current-year probability release blocked at that stage |
| `C:\NWR\Niners-War-Room-outcome\docs\outcome_probability\BUILD_SPRINT_5Y_EXPANDED_CALIBRATION_READINESS.md` | Outcome repo history includes `74624f5`, 2026-06-12 | Expanded calibration readiness stayed internal; next-year support remained partial/censored; app percentage output was not created | Deferred to internal validation, not approved app surface |
| `C:\NWR\Niners-War-Room-outcome\docs\outcome_probability\BUILD_SPRINT_5EI_APP_READABLE_NUMERIC_ARTIFACT_CONTRACT_AND_GENERATOR.md` | Outcome repo history includes `545656a`, 2026-06-15 | Defines current app-readable artifact and approved heads: `qb_t12`, `rb_t12`, `rb_t24`, `wr_t12`, `wr_t24`, `wr_t36`, `te_t12`; blocked/unapproved heads absent | Approved narrowed Outcome display surface |
| `C:\NWR\Niners-War-Room-outcome\docs\outcome_probability\BUILD_SPRINT_5EM_R_FINAL_NUMERIC_APP_DISPLAY_READINESS_VERDICT.md` | Outcome repo, current docs | Confirms Rankings page wiring uses only `numeric_outcome_display_v1.csv`; no unapproved heads; display-only; no sort/rank/private-value use | Approved current app posture |
| `C:\NWR\Niners-War-Room-outcome\docs\outcome_probability\BUILD_SPRINT_5EO_NUMERIC_OUTCOME_DISPLAY_PR_MERGE_READINESS_REVIEW.md` | Outcome repo, current docs | Confirms approved heads only, no raw/sort/rank use | Approved current app posture |
| `C:\NWR\Niners-War-Room-outcome\app\generated\outcome_probability\numeric_outcome_display_v1.csv` | Current outcome repo artifact | 240 rows; columns listed below; no 2026/2027/5Y horizon columns | Current approved artifact |

## Current Approved Outcome Artifact

Path:

`C:\NWR\Niners-War-Room-outcome\app\generated\outcome_probability\numeric_outcome_display_v1.csv`

Expected hash referenced by the Streamlit app service:

`1fb63fec25f7893ed09004830c7eb4e5ed32c6622c08876849fb61a2e4826cb0`

Rows:

- total rows: 240
- available rows: 227
- unavailable rows: 13

Columns:

- `player_id`
- `player_display_name`
- `position`
- `outcome_status`
- `qb_t12_display_pct`
- `rb_t12_display_pct`
- `rb_t24_display_pct`
- `wr_t12_display_pct`
- `wr_t24_display_pct`
- `wr_t36_display_pct`
- `te_t12_display_pct`
- `unavailable_reason_public`
- `artifact_version`
- `source_evidence_version`
- `generated_at_utc`

Approved display heads:

- QB T12
- RB T12
- RB T24
- WR T12
- WR T24
- WR T36
- TE T12

Artifact metadata observed:

- `artifact_version`: `phase11_numeric_outcome_display_v1`
- `source_evidence_version`: `phase10_5ed_5ee_green_local_dry_run`
- `generated_at_utc`: `2026-06-16T00:04:56Z`

## Coverage Against Frozen 66-Player Board

The current approved artifact supports 12 of 66 frozen-board rows by player name and position.

Supported frozen-board rows:

| Final Board Rank | Player | Position |
|---:|---|---|
| 31 | Zay Flowers | WR |
| 34 | Chris Olave | WR |
| 40 | Drake Maye | QB |
| 42 | Jameson Williams | WR |
| 47 | Alec Pierce | WR |
| 54 | Jaylen Warren | RB |
| 60 | Dak Prescott | QB |
| 62 | Rashee Rice | WR |
| 63 | Brian Thomas | WR |
| 64 | Keenan Allen | WR |
| 65 | Brock Purdy | QB |
| 66 | Darren Waller | TE |

Unsupported frozen-board rows:

- 54 of 66 rows remain `Not enough information`.

## Whether Horizon Columns Exist Anywhere

No approved CSV/JSON artifact was found with the planned horizon columns:

- `top_6_2026_prob`
- `top_12_2026_prob`
- `top_24_2026_prob`
- `top_36_2026_prob`
- `top_48_2026_prob`
- `top_6_2027_prob`
- `top_12_2027_prob`
- `top_24_2027_prob`
- `top_12_next_5y_prob`
- `next_5y`
- `five_year`
- `year_1`
- `year_2`

The horizon language exists in contracts, tests, legacy page scaffolding, and internal training/source-manifest concepts. It was not found as a current approved app-readable output that can be safely used tomorrow.

## Why The Current App Only Has Current Outcome Columns

The current app is wired to the approved numeric display artifact from the Outcome repo. That artifact intentionally emits only the seven approved position outcome heads and blocks raw probability, sort, hidden, rank-delta, market, projection, ADP, trade, and other unsafe fragments.

The earlier horizon plan was broader than the released artifact. Outcome docs show that release readiness was constrained by feature coverage, calibration quality, label maturity, and future-window censoring. The later app contract chose a narrower, display-only release surface rather than shipping 2026/2027/5-year horizon probabilities.

## Safe To Use Tomorrow

Safe:

- The current approved display-only Outcome heads listed above.
- Missing Outcome cells shown exactly as `Not enough information`.
- Continued statement that Outcome columns are display-only and do not drive rank, hidden sort, model logic, private value, Mock Draft logic, or draft advice.

Not safe without a new approved release:

- 2026 probability columns.
- 2027 probability columns.
- next-5-year / 5-year horizon probability columns.
- Any generated horizon probability values.
- Any candidate-only, raw, audit, or local model output wired into the app.

## Human Decisions Needed

1. Decide whether to revive horizon Outcomes as a post-draft or future Outcome lane.
2. Approve a precise horizon taxonomy before implementation:
   - calendar-year outcomes such as 2026 and 2027,
   - relative horizons such as year 1, year 2, and next 5 years,
   - position thresholds such as T12/T24/T36/T48,
   - or role buckets such as starter/useful/bust.
3. Define release gates for horizon probabilities:
   - minimum coverage,
   - label maturity,
   - calibration quality,
   - backtest stability,
   - player-facing display copy,
   - and guardrail scans.
4. Decide whether horizon outputs are app display-only or separate diagnostics until validated.

## Recommended Future Prompt

Use a dedicated candidate lane, not the draft-day app lane:

> Run Outcome Horizon Refresh V0 as a candidate-only lane. Recover the June 10 horizon contract, evaluate whether approved internal historical labels can support 2026, 2027, year_1, year_2, and next_5y display-only probabilities, produce candidate coverage/calibration reports, and do not wire anything into the app or mutate approved artifacts. Missing unsupported values must remain `Not enough information`.

## Search Scope Confirmed

Searched:

- Main repo current files under `src`, `tests`, `docs`, `app`, `app/generated`, `local_exports`, and `docs/draft_day_exports`.
- Outcome repo current files under `src`, `tests`, `docs`, `app/generated`, and `local_exports`.
- Main repo git history using string search for horizon labels and planned column names.
- Outcome repo git history using string search for horizon labels, `next_year_starter`, and approved numeric artifact docs.
- Current CSV/JSON artifacts in both repos for planned horizon column names.

## Guardrail Confirmation

- No app code changed.
- No model code changed.
- No frozen board changed.
- No latest_candidate or latest_approved files changed.
- No pinned snapshot changed.
- No ranks changed.
- No new probabilities generated.
- No Outcome artifact wired into the app.
- No `C:\NWR_SHARED_DATA` contents tracked.
- No raw vendor CSVs or prediction dumps added.
- No push performed.
