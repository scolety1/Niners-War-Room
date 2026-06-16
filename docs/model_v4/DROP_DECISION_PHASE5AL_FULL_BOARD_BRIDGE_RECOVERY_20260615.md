# Drop Decision Phase 5AL-R Full-Board Bridge Recovery - 2026-06-15

## Classification

Overall: YELLOW

Phase 5A human-review usability: GREEN

Full-board bridge evidence quality: YELLOW, materially improved

Phase 5B status: CLOSED / NOT OPENED

This rerun advanced beyond Phase 5AK. The missing full-board bridge artifacts now exist locally in the expected ignored `local_exports` paths, and the Dynasty Rankings / full-board QA bridge now covers the 240-row active board with 232 scored QB/RB/WR/TE rows. Remaining YELLOW caveats are limited to a from-scratch exporter failure and a stale adjacent test expectation.

This report creates no final or implied drop recommendation, no ranked or sorted drop-candidate list, no probabilities, and no outcome bands.

## Lane Proof

- Repo: `C:\Users\smcol\Documents\Vacation\Niners-War-Room-drop-decision`
- Branch: `work/drop-decision-day-review`
- HEAD: `7f614a0087f803869a46ea5ecd04444eefe17c2d`
- Remote branch hash: `7f614a0087f803869a46ea5ecd04444eefe17c2d`
- Local/remote match: yes

Initial uncommitted docs-only context:

- `docs/model_v4/DROP_DECISION_PHASE5AK_DYNASTY_RANKINGS_EVIDENCE_GAP_AUDIT_20260615.md`
- `docs/model_v4/DROP_DECISION_PHASE5AL_DYNASTY_FULL_BOARD_BRIDGE_RECOVERY_20260616.md`

## Consumer And Builder Paths

Dynasty Rankings consumer:

- `app/pages/05_rankings.py` reads `DEFAULT_FULL_PLAYER_BOARD_ROWS` through `FULL_BOARD_VALUE_ROWS`.
- `src/services/player_board_score_service.py` prefers `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv` when present.

Expected bridge paths:

- `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv`
- `local_exports/model_v4/current_value/latest/current_player_value_full_board_review_rows.csv`

Builder path inspected:

- `scripts/build_model_v4_full_board_rankings_exports.py`
- `src/services/full_board_current_value_export_service.py`
- `src/services/full_player_board_value_service.py`

The app and service copy state that market, league, ADP, consensus, projection, startup, and trade-calculator context remain display-only and are not private value inputs.

## Recovery Search

Exact local sibling artifacts were found under:

`C:\Users\smcol\Documents\Vacation\Niners-War-Room\local_exports\model_v4\current_value\latest\`

| Artifact | Candidate rows | Recovery decision |
| --- | ---: | --- |
| `current_player_value_full_board_review_rows.csv` | 232 | Copied into the Drop Decision lane because schema matched the expected current-value full-board checkpoint and all 232 rows carried checkpoint scores. |
| `full_player_board_value_review_rows.csv` | 240 | Not copied directly because the sibling version included extra candidate-mode columns. A canonical Drop Decision full-player-board artifact was regenerated from the recovered current-value checkpoint instead. |

Candidate-mode artifact found but not copied:

- `local_exports/model_v4/current_value/candidates/wr_qb_v2/full_player_board_value_review_rows.csv`

## Recovered / Regenerated Artifacts

| Artifact | Status | Path | Rows | Schema match | Local-only |
| --- | --- | --- | ---: | --- | --- |
| Full-board current-value checkpoint | recovered from admitted local sibling artifact | `local_exports/model_v4/current_value/latest/current_player_value_full_board_review_rows.csv` | 232 | yes | ignored / untracked |
| Full player board review rows | regenerated locally from recovered checkpoint and active local data pack | `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv` | 240 | yes | ignored / untracked |
| Missing score repair queue | regenerated local support artifact | `local_exports/model_v4/current_value/latest/full_board_missing_score_repair_queue.csv` | 8 | support-only | ignored / untracked |

Full-board bridge counts:

- active board rows: 240
- QB/RB/WR/TE rows: 232
- primary scored rows: 232
- fail-closed source-repair rows: 8
- Niners roster rows covered: 24
- market or league primary scores used: 0
- legacy active-pack primary scores used: 0

## Bridge Coverage

After recovery:

- roster state rows covered by full board: 24 of 24
- Decision Board roster-context rows covered by full board: 24 of 24
- pressure rows covered by roster bridge: 24 of 24
- opportunity-cost rows covered by roster bridge: 24 of 24
- trade-away rows covered by roster bridge: 24 of 24
- roster-pressure human-review cards covered by roster bridge: 24 of 24

No forbidden final recommendation, probability, outcome-band, app-readable recommendation, final-action, or ranked-drop output columns were detected in the recovered/regenerated bridge artifacts.

## Regeneration Caveat

The full-player-board artifact can be regenerated safely once the recovered full-board current-value checkpoint exists. The from-scratch current-value exporter is still not clean in this lane:

```text
tests/test_full_board_current_value_export_service.py
```

Current result:

- 2 failed
- exporter produces 232 rows but 0 checkpoint-scored rows in isolated test output

Exact HQ / engineering request:

- Repair or clarify the `write_full_board_current_value_export` prerequisite/path contract so it can produce `current_player_value_full_board_review_rows.csv` with 232 scored rows from admitted local sources in this lane.
- Preserve the rule that market, league, ADP, projection, trade-calculator, and legacy active-pack fields cannot become private value formula inputs.

## Identity QA

| Label pair | Status | Finding | Action needed |
| --- | --- | --- | --- |
| Brian Thomas / Brian Thomas Jr. | GREEN for bridge QA | Recovered full-board and current-value checkpoint map the roster label to `nfl:brianthomas:WR`; the sibling dynasty-asset display label includes `Jr.`. | Optional HQ display-label confirmation only. |
| Oronde Gadsden / Oronde Gadsden II | GREEN for bridge QA | Recovered full-board and current-value checkpoint map the roster label to `nfl:orondegadsden:TE`; the sibling dynasty-asset display label includes `II`. | Optional HQ display-label confirmation only. |

These identity findings are neutral data-quality findings only. They are not roster-action guidance.

## Tests And Smokes

Passed:

- `tests/test_full_player_board_value_service.py`: 6 passed
- `tests/test_player_board_score_service.py`: 8 passed
- `tests/test_model_v4_phase5_clean_display_language.py`: 6 passed
- `tests/test_navigation_compression.py`: 12 passed on rerun after clearing a generated bytecode cache file
- `tests/test_model_v4_human_decision_review_prep_service.py`: 4 passed
- `tests/test_model_v4_roster_opportunity_cost_service.py`: 6 passed
- `tests/test_decision_board_coherence_audit.py`: 5 passed
- `python -m py_compile app/pages/08_june15_review.py app/navigation.py`: passed
- `python -m py_compile` on inspected services: passed

YELLOW caveats:

- `tests/test_full_board_current_value_export_service.py`: 2 failed because isolated from-scratch exporter output has 0 scored checkpoint rows.
- `tests/test_non_formula_sanity_fixtures.py`: 6 passed, 1 failed because it still expects the old fallback `checkpoint_review_score` source column; with the recovered full-board artifact present, `tests/test_player_board_score_service.py` confirms the canonical source is `nwr_dynasty_score`.

## Safe-Use Rules

Use the recovered bridge only for Phase 5A display-only QA, coverage checks, identity-gap checks, and human-review context.

Do not use it for:

- final or implied drop recommendations
- cut/keep decisions
- sorted or ranked drop-candidate lists
- probabilities or outcome bands
- app-readable recommendation outputs
- promoted artifacts
- Phase 5B decision-support mode

## Conclusion

This was a true Phase 5AL-R recovery run, not a repeat of Phase 5AK. The missing full-board bridge artifacts were recovered/regenerated locally enough to restore Dynasty Rankings / full-board QA coverage for Phase 5A human review. Evidence quality remains YELLOW until the from-scratch current-value exporter and stale adjacent fixture are repaired or explicitly accepted.

No commit, push, deploy, merge, staging, `data/` or `local_exports` commit, Phase 5B opening, final/implied recommendation, drop-candidate sorting/ranking, probability/band output, promoted artifact, rookie framework edit, or external/ranking/projection source use occurred.
