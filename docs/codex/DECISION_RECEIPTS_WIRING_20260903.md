# Decision receipts — wired into NWR PURE owner picks (section 18)

Code: `build_and_append_owner_decision_receipt` (`nwr_pure_experiment_service.py`),
wired into `DesktopBackendFacade.mark_redraft_player` and
`replace_redraft_pick`/`clear_redraft_pick`/`fill_redraft_pick_gap`
(`desktop_facade.py`). Route: `POST .../draft/<id>/pick` gains an
optional `emergencyOverride` body field; `api-client.markDrafted` gains
an optional third parameter.

## What happens now on a real owner pick

When `profile.nwr_pure_experimental` is `True` and the owner records a
pick through the live Draft Room (`mark_redraft_player` →
`owner_pick_and_advance`), the facade **first** calls
`build_and_append_owner_decision_receipt`, which assembles and appends a
real, immutable `DecisionReceipt` (pick number/round/owner slot, the
owner's real roster-before, a real `team_score_before` computed via the
existing SHADOW `optimal_starting_lineup_value`, and the selected
player) to `nwr_pure_experiments/<profile_id>/decisions.jsonl` — **before**
the pick itself is recorded. If that write fails, the pick is rejected
(`FacadeError NWR_PURE_DECISION_RECEIPT_FAILED`) and nothing is
recorded — matching the directive's "do not silently proceed with an
unlogged experimental decision." The **only** sanctioned bypass is an
explicit `emergency_override=True` (or `emergencyOverride: true` over
HTTP), which proceeds anyway and reports
`nwrPureDecisionReceiptSkipped` in the response so the skip is visible,
never silent.

`decision_policy` is honestly `OWNER_OVERRIDE`, not `OPTIMIZER`: no
optimizer-driven Suggestions surface exists in the owner-facing UI yet
(`docs/codex/DRAFT_ROOM_V2_UI_CONTRACT_20260903.md`). Claiming
`OPTIMIZER` before that UI exists would misrepresent what actually chose
the pick — the owner always picks through the existing search UI today;
the receipt records real SHADOW context (`team_score_before`,
`roster_before`) alongside that fact, not as the deciding input.

## Corrections never rewrite an original receipt

`replace_redraft_pick`/`clear_redraft_pick`/`fill_redraft_pick_gap` each
append a `ReceiptCorrectionRecord` to `corrections.jsonl` (referencing
the corrected `pick_number`, never touching `decisions.jsonl`) when NWR
PURE mode is on. This is deliberately **best-effort** (a write failure
here never blocks the correction itself) — unlike the original pick,
which section 18 explicitly requires to block on a receipt failure, a
correction is usually the owner *fixing* a mistake, and blocking that on
a secondary audit-log write failing would be a worse outcome than a
missing correction-record entry.

## Tests

`tests/test_desktop_application_api.py`, 5 new (81/81 passing across
the three files exercised, same 5 pre-existing baseline failures
unaffected): a real pick writes exactly one receipt with the right
fields; NWR PURE off writes none; a fresh facade against the same store
sees the identical receipt after "restart"; a correction appends exactly
one `ReceiptCorrectionRecord` while leaving the original receipt
byte-for-byte unchanged; and the block/emergency-override behavior
(receipt-write failure blocks the pick, `emergency_override=True` is the
only way through, and the skip is reported, never silent).
