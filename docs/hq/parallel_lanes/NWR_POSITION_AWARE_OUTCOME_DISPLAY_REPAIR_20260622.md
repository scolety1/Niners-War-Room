# NWR Position-Aware Outcome Display Repair - 2026-06-22

## Final Verdict

GREEN.

Current approved Outcome probabilities remain display-only. This repair changes only the Streamlit display logic for Dynasty Rankings / Player Board and Player Compare. It does not generate new Outcome probabilities, revive horizon columns, mutate the frozen board, change ranks, change model/value logic, or wire Outcome into Live Draft Room as a default table feature.

## Position Applicability Rules

Approved current Outcome heads:

| Position | Applicable Outcome Heads |
|---|---|
| QB | QB T12 |
| RB | RB T12, RB T24 |
| WR | WR T12, WR T24, WR T36 |
| TE | TE T12 |

Display rules:

- Same-position supported value: show the approved percentage.
- Same-position missing value: show `Not enough information`.
- Wrong-position value in all-outcome/advanced mode: show `N/A`.
- Wrong-position values are hidden in default position-applicable mode when practical.
- Outcome columns remain display-only and do not drive rank, sort, model value, private value, Mock Draft logic, or draft advice.

## Before / After

Before:

- Dynasty Rankings could show all seven Outcome columns at once.
- Wrong-position empty heads displayed as `Not enough information`, creating a noisy table full of irrelevant missing cells.
- Player Compare showed raw lane prop context rather than a player-specific Outcome view.

After:

- Dynasty Rankings has an `Outcome columns` selector:
  - `Position-applicable only` default.
  - `All outcome columns`.
  - `Hide`.
- Position-applicable mode keeps the table focused on heads relevant to the currently displayed positions.
- All-outcome mode still works for diagnostics, but wrong-position heads render as `N/A`.
- Player Compare now has a position-aware `Outcome Context` block with a visible display-only label and a `Show all Outcome columns` advanced toggle.
- Live Draft Room remains uncluttered by Outcome heads.

## Dynasty Rankings Proof

Browser-checked:

- URL: `http://127.0.0.1:8501/rankings`
- Page rendered without Traceback/ImportError.
- `Outcome columns` control visible.
- Default mode visible as `Position-applicable only`.
- Display-only caption visible.
- Visible heads caption rendered:
  `QB T12 (Display-Only), RB T12 (Display-Only), RB T24 (Display-Only), WR T12 (Display-Only), WR T24 (Display-Only), WR T36 (Display-Only), TE T12 (Display-Only)` when all positions are included.

Focused service tests verified:

- WR-selected display resolves to WR T12 / WR T24 / WR T36.
- RB-selected display resolves to RB T12 / RB T24.
- QB-selected display resolves to QB T12.
- TE-selected display resolves to TE T12.
- Hide mode removes Outcome heads and Outcome availability from the display frame.
- All-outcome mode renders wrong-position values as `N/A`.

## Player Compare Proof

Browser-checked:

- URL: `http://127.0.0.1:8501/player-compare`
- Selected players: Zay Flowers and Chris Olave.
- `Outcome Context` block rendered.
- Display-only label rendered.
- Visible heads caption rendered:
  `WR T12 (Display-Only), WR T24 (Display-Only), WR T36 (Display-Only)`.
- Wrong-position heads are hidden by default.
- Advanced toggle `Show all Outcome columns` remains available for diagnostic use.

## Live Draft Non-Clutter Proof

Browser-checked:

- URL: `http://127.0.0.1:8501/live-draft-room`
- Page rendered without Traceback/ImportError.
- Frozen board signal still showed 66 rows.
- Source/diagnostics remained collapsed.
- Default Live Draft Room page text did not contain QB/RB/WR/TE Outcome heads.
- Recent Live Draft behavior was not intentionally changed by this repair.

## Future Horizon Taxonomy Note

No 2026, 2027, or 5-year horizon Outcome columns were implemented here.

Future horizon Outcome work should be a separate candidate lane. The preferred taxonomy should be calendar-year based, for example:

- 2026 T12 probability.
- 2027 T12 probability.
- Optional later-year or 5-year summary probabilities.

No approved app-readable horizon artifact exists yet, so tomorrow's app should not display fabricated 2026/2027/5-year probabilities.

## Files Changed

- `app/pages/20_final_board_v1.py`
- `app/pages/22_player_compare_v1.py`
- `src/services/draft_day_app_v1_service.py`
- `tests/test_draft_day_app_v1_service.py`
- `docs/hq/parallel_lanes/NWR_POSITION_AWARE_OUTCOME_DISPLAY_REPAIR_20260622.md`

## Tests And Smoke

Passed:

- `python -m pytest tests/test_draft_day_app_v1_service.py`
  - 20 passed.
- `python -m ruff check app/pages/20_final_board_v1.py app/pages/22_player_compare_v1.py src/services/draft_day_app_v1_service.py tests/test_draft_day_app_v1_service.py`
- `git diff --check`
- Browser smoke:
  - `/rankings`
  - `/player-compare`
  - `/live-draft-room`
  - `/mock-draft`
  - `/trading-lab`

Guardrails confirmed:

- Frozen board remains 66 rows.
- Pinned hash unchanged:
  `5780156F09FBDA61FB906715C7341DB1B6D320C8D8EFA588070F19C4C50F45CE`
- No `C:\NWR_SHARED_DATA` files tracked.
- No raw vendor CSVs or prediction dumps tracked.
- latest_candidate/latest_approved paths were not created or updated.

## Remaining YELLOW / RED

YELLOW:

- Current Outcome support remains partial.
- Frozen-board support remains 12/66.
- 2026/2027/5-year horizon Outcomes remain future planning only.

RED:

- None found in this repair.
