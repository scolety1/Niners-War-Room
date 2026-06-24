# NWR Unified Universe App-Wiring Readiness Gate - 2026-06-24

## Verdict

YELLOW overall. The unified player universe may remain visible in a dedicated
review-only surface, but it is not ready to become a default app source for Dynasty
Rankings, Drafting Mode, Cheat Sheets, Player Compare, Trading Lab, Post-Draft Mode,
or any model/rank workflow.

Readiness as of HEAD/source state before any RotoWire candidate repair integration.

Parallel caveat: a separate RotoWire candidate/source-repair lane may run concurrently.
If that lane later produces safe candidate repairs and Master integrates them, this
readiness gate may become stale and must be rerun or amended from the new source state.

## Snapshot

Source state:

- Base HEAD: `9924e6d60bd7e210f112a3887142fc37f47705e1`
- Consolidated rows: 368
- Remaining blocker rows: 271
- Missing player_id blockers: 5
- Missing age blockers: 16
- Age conflict blockers: 1
- Review-needed consolidated rows: 249
- All consolidated rows: `app_wiring_allowed=no`
- All consolidated rows: `model_input_allowed=no`
- App wiring status: blocked

Primary artifacts reviewed:

- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_consolidated_review.csv`
- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_remaining_blockers.csv`
- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_validation_report.csv`
- `docs/hq/model/NWR_UNIFIED_PLAYER_UNIVERSE_CONTRACT_V1_20260624.md`
- `docs/hq/model/NWR_UNIFIED_PLAYER_UNIVERSE_REVIEW_PAGE_20260624.md`

## Direct Answers

1. Can the unified universe be safely shown in app UI as review-only?

Yes, only in a clearly labeled Unified Universe Review page or equivalent debug/review
surface. It must remain hidden or non-default in primary decision workflows. The existing
review route is acceptable because it is inspection-only and does not drive rankings,
model inputs, Drafting Mode, or source truth.

2. Can it be safely added to Dynasty Rankings behind an explicit review-only toggle?

YELLOW at most. A future integration lane may add it behind an explicit review-only toggle
if the default remains the approved Dynasty Rankings source, the toggle is off by default,
blocked rows are excluded or loudly marked, and no unified field becomes a sort default,
rank override, source-truth replacement, or hidden sort key. Do not wire it now.

3. Can it be safely added to Drafting Mode cockpit?

No. RED/DEFER. Drafting Mode is an on-clock workflow, and the current unified universe still
has unresolved identity, age, review-needed, and rank-display blockers. It should not appear
in the cockpit until accepted display rules, row exclusions, and live-draft browser smoke are
complete.

4. Can it be safely used in Player Compare or Trading Lab?

No for default workflows. RED/DEFER except for a later manual, explicitly selected
review-context panel that does not compute advice, values, rank gaps, trade decisions, or
package recommendations. Do not wire it now.

5. What fields are allowed by default?

Allowed by default only in a review-only surface:

- `player_name`
- `position`
- `nfl_team`
- `player_type`
- `availability_status`
- `source_layers`
- `review_status`
- `data_quality_status`
- `manual_review_flag`
- `consolidation_status`
- `consolidation_confidence`
- `conflict_flags`
- `caveats`
- `app_wiring_allowed`
- `model_input_allowed`

Technical identity/source fields such as `player_id`, `canonical_universe_id`,
`source_row_ids`, and `source_files` may be shown in the review page or Data Health only,
not default decision tables.

6. What fields must be hidden?

Hidden by default from decision workflows:

- `player_id`
- `canonical_universe_id`
- `source_row_ids`
- `normalized_name`
- `source_files`
- `dynasty_rank`
- `rookie_rank`
- `frozen_baseline_rank`
- `candidate_rank`
- `unified_display_rank`
- `unified_display_rank_source`
- `tier`
- `tier_source`
- `outcome_context`
- `outcome_status`
- `dp_1qb_value`
- `dp_market_rank`
- `nwr_vs_market_gap`
- any duplicate, conflict, or join-confidence internals not rendered with warnings

These may be inspected in the review page, but must not become source truth, default sort,
hidden sort, model input, trade value, or final advice.

7. What warnings must appear?

Required warning copy or equivalent:

- `Unified Universe Review-Only: not rankings source truth, not model input, not Drafting Mode source.`
- `app_wiring_allowed=no and model_input_allowed=no in the current artifact.`
- `Do not treat unified_display_rank as Dynasty Rank, Candidate Rank, or Final Board Rank.`
- `Missing player IDs and missing ages are blockers; do not fabricate IDs or ages.`
- `Outcome, market, ADP, DynastyProcess, RotoWire, and vendor context are display-only unless later explicitly approved.`
- `Readiness as of HEAD/source state before any RotoWire candidate repair integration.`

8. Which rows must remain blocked?

All rows remain blocked from app wiring and model input right now because every row has
`app_wiring_allowed=no` and `model_input_allowed=no`.

Within a review-only surface, these rows must be loudly marked and excluded from any future
decision-page toggle until repaired or explicitly accepted:

- 5 missing player_id blockers.
- 16 missing age blockers.
- 1 age conflict blocker.
- 249 `REVIEW_NEEDED` consolidated rows.
- 249 manual-review rows.
- Any row with duplicate/conflict flags, low confidence, unsupported outcome, no market match
  used as a warning, or unresolved source caveats.

9. What would make the gate GREEN later?

Minimum GREEN requirements for a later app-wiring lane:

- Rerun this gate after any RotoWire/source-repair integration.
- Keep model input RED unless a separate model-governance lane explicitly approves otherwise.
- Resolve or explicitly quarantine all missing player_id blockers for app-visible rows.
- Resolve, source, or explicitly display-accept missing age blockers without fabricating ages.
- Resolve the age conflict blocker.
- Complete duplicate/consolidation review for app-visible rows.
- Approve a rank-display policy that keeps Dynasty Rank, Final Board Rank, Candidate Rank,
  rookie rank, and `unified_display_rank` visually and semantically separate.
- Add a service-layer loader that enforces blocked fields, row exclusions, and no hidden sort.
- Add Data Health visibility for artifact freshness, blocker counts, and source caveats.
- Add page-specific tests proving no rank/model/source-truth mutation.
- Browser-smoke every affected page with the toggle off by default and warnings visible.

## Page Recommendations

| Page | Recommendation |
| --- | --- |
| Unified Universe Review page | GREEN review-only. Keep hidden/advanced and inspection-only. |
| Dynasty Rankings | YELLOW/DEFER. Future explicit toggle only; never default. |
| Drafting Mode cockpit | RED/DEFER. Not safe for on-clock cockpit until rank/display rules are accepted. |
| Cheat Sheets | RED/DEFER. Do not mix into fast draft sheet until row exclusions and rank policy are stable. |
| Player Compare | RED/DEFER. Later manual review-context panel only. |
| Trading Lab | RED/DEFER. Later manual context only; no trade math or recommendation. |
| Post-Draft Mode | YELLOW/DEFER. Later recap/review context only after row caveats are visible. |
| Settings/Data Health | GREEN for health/blocker summary only; no decision table wiring. |

## Non-Negotiable Policies

- Do not wire unified universe into Dynasty Rankings in this lane.
- Do not wire unified universe into Drafting Mode in this lane.
- Do not change app behavior in this lane.
- Do not change model/rank logic.
- Do not mutate Frozen Final Draft Board V1.
- Do not change `final_board_rank`.
- Do not overwrite Dynasty Rank.
- Do not change tier assignments.
- Do not update `latest_candidate` or `latest_approved`.
- Do not mutate pinned snapshots.
- Do not fabricate player IDs, ages, rookie Dynasty Rank, or Outcome probabilities.
- Do not make DynastyProcess, RotoWire, market, ADP, or vendor sources source truth.
- Do not flip `model_input_allowed` or `app_wiring_allowed` to yes.

## Matrix

The page-level gate matrix is:

`docs/hq/model/unified_player_universe_v0/unified_player_universe_app_wiring_gate_matrix_20260624.csv`
