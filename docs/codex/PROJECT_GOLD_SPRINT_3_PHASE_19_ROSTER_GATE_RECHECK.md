# Project Gold Sprint 3 / Phase 19: Roster Decision Gate Recheck

Last reviewed: 2026-05-14

This checkpoint re-runs the roster, draft, and final money-decision gates after Sprint 3
cleanup. It does not change formulas, import paid data, or mark draft/final readiness.

## Result

| gate | status |
|---|---|
| Roster Decisions Ready | Roster Decisions Ready |
| Draft Ready | Draft Pool Needs Data |
| Final Money Decisions Ready | Needs Data |

Roster decisions can now be reviewed for pre-declaration drop/shop thinking. Draft and
final money decisions remain blocked until the real draftable pool is loaded and the Draft
UX gate passes.

## Export

Checkpoint folder:

`local_exports/model_audits/sprint3_phase19_roster_gate_recheck_20260514`

Files:

| file | purpose |
|---|---|
| `manifest.json` | gate badges, pass/fail booleans, row counts, and active paths |
| `pre_decision_checklist_summary.csv` | compact roster/draft/final status row |
| `pre_decision_checklist_rows.csv` | checklist rows shown in Model Lab |
| `roster_decision_summary.csv` | roster-only gate summary |
| `roster_decision_gate_rows.csv` | roster-only requirements and status |
| `final_calibration_gate_summary.csv` | final gate summary |
| `final_calibration_gate_rows.csv` | final gate requirements and blockers |
| `remaining_blockers.csv` | non-ready rows from the pre-decision checklist |

## Roster Gate Details

Roster gate status: **ready**

| requirement | status | detail |
|---|---|---|
| Current rosters loaded | ready | 24 roster rows loaded for the selected team. |
| League ranks loaded | ready | 24 selected-roster players have league-rank coverage. |
| Stats-first veteran outputs present | ready | 1039 stats-first veteran output rows are available. |
| Lifecycle/model separation pass | ready | Established veterans do not score draft-capital prior in receipts. |
| Critical source coverage passes | ready | No selected-roster critical source bucket gaps are blocking roster decisions. |
| Identity audit passes | ready | Selected-roster identity joins pass. |
| Young bridge receipts visible | ready | 10 selected-roster young bridge players show bridge receipts. |
| My-roster outlier review resolved/accepted | ready | No unresolved selected-roster review-required outliers remain. |

## Pre-Decision Checklist

Pre-declaration checklist status: **ready**

| check | status | detail |
|---|---|---|
| Roster data | ready | 24 roster rows loaded for the selected team. |
| League ranks | ready | 24 selected-roster players have league-rank coverage. |
| Lifecycle audit | ready | Young bridge and established-veteran lifecycle lanes pass. |
| Source coverage | ready | Critical thresholds pass; optional accepted gaps retain confidence penalties. |
| Identity audit | ready | 232 player identity joins pass. |
| Named sanity fixtures | ready | 14 sanity scenarios pass. |
| Outlier review | ready | No unresolved review-required ranking outliers remain. |
| Young bridge receipts | ready | 10 selected-roster young bridge players show bridge receipts. |
| My team receipt review | ready | 24 selected-roster players have visible receipt rows. |

## Remaining Draft/Final Blockers

These do not block pre-declaration roster decisions. They block draft readiness and final
money-decision readiness.

| blocker | why it matters | next patch |
|---|---|---|
| Draft Pool Loaded | The mixed offline draft board must use real rookies, free agents, manual draftables, and later released veterans, while excluding protected roster players. | Load real rookie and free-agent draftable pools before draft-board labels or final draft freeze. Official released veterans can be added later when declarations are available. |
| Draft UX Smoke Pass | Rankings and Draft Board cannot be final until a combined rookie/veteran available pool exists. | Fix the Rankings/Draft Board contract after the draft pool is loaded. |

Final calibration gate details:

- `real_draft_pool_loaded`: blocked because rookies and free agents are not loaded.
- `draft_ux_smoke_pass`: blocked because no combined rookie/veteran available pool rows
  were detected.
- All other final gates are ready.

## What This Means

Use the app for:

- pre-declaration Niners roster review
- forced top-five release review
- bubble/shop/cut inspection
- receipt-based player audits

Do not use it yet for:

- final draft board ranking
- live/mock draft confidence
- final freeze
- final money-decision badge

## Next Best Patch

Sprint 4 should start with the real draftable pool:

1. Load current-year rookie draftables.
2. Load Sleeper free agents or a manual free-agent draftable file.
3. Keep official released veterans empty until declarations exist.
4. Rebuild Rankings and Draft Board from that available pool.
5. Re-run the draft/final gates.

## Verification

Full static check passed:

`656 passed`

The repeated `Access is denied` warnings are from temp pytest-directory scans after the
successful static check and do not indicate test failure.
