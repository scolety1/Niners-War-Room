# Next-Draft Final Blocker Closure — Section 8: Status/Ballers UI (bounded) V1

**Context:** Follow-up directive "NWR NEXT-DRAFT FINAL BLOCKER CLOSURE", section 8. Backend
paths existed (facade-level only) for status/risk intake and Ballers PDF/CSV import; none were
reachable from any HTTP route or GUI control. Scope constraint: "small owner UX only... do not
let these delay sections 1-6" (already satisfied) and "if not safely finishable: leave
backend-ready and clearly document the manual/current workflow."

## Investigation

Confirmed via grep that FOUR real facade methods existed with ZERO real wiring beyond the
Python layer: `import_udk_pdf_rankings`, `rollback_udk_position_rankings`,
`submit_player_status_override`, `list_player_status_overrides`. Closing any of them requires
three real layers: an HTTP route in `src/desktop_api/server.py`, a client method in
`desktop/packages/api-client/src/index.ts`, and frontend UI.

**Real, important finding while investigating the Ballers PDF path specifically**: the
facade's own `import_udk_pdf_rankings(pdf_path: str)` docstring claims it follows "the same
file-path convention as `import_udk_unmodeled_skill_assets`" -- but a direct grep confirmed
`import_udk_unmodeled_skill_assets` itself has ZERO callers anywhere outside its own module
(no HTTP route, no frontend reference at all). There is no live precedent anywhere in this
product for turning a browser-picked file into a real local filesystem path reachable by the
Python backend. Checked `desktop/apps/redraft/package.json` and grepped the frontend source for
any existing Tauri file-dialog usage (`@tauri-apps/plugin-dialog`, `open(`) -- none exists.
Building this from scratch would mean adding a new Tauri plugin dependency (npm package + Rust
crate + capabilities registration) with no existing pattern to reuse and no way to test it
through this session's own Chrome-based rendering harness (native file dialogs are not
Chrome-automatable). That is not "small, bounded, safe" work for this section.

## Scope decision

**Built (full stack, safe, bounded, tested):**

1. **UDK rollback-one-position.** `rollback_udk_position_rankings(profile_id, position)` takes
   no file at all -- just the position string to restore to its previous version. Wired:
   `POST /api/v1/redraft/udk/{profileId}/rollback` (`src/desktop_api/server.py`),
   `rollbackUdkPositionRankings()` (`api-client/src/index.ts`), and a "Roll back {position} to
   previous import" button next to the existing UDK source boundary-note in Cheat Sheets
   (`cheat-sheet.tsx`, wired from both the embedded Draft Room V2 tab and left as
   optional/undefined on the standalone `#/cheat-sheet` route, matching the existing
   `canRecordPick`/`onDraft` optional-prop precedent there).
2. **Status/risk intake -- read AND write.** Closes the real, disclosed section-2 gap (read
   side had zero UI) together with the write side (never reachable at all). Wired:
   `GET`/`POST /api/v1/redraft/status-overrides` (new route, no path parameter -- the real
   backend stores one shared, repo-committed list, not profile-scoped), `listPlayerStatus
   Overrides()`/`submitPlayerStatusOverride()` (`api-client/src/index.ts`), a new
   `PlayerStatusOverride` contract type (`contracts/src/index.ts`, mirrors the real backend
   shape exactly -- three real kinds, no "end date" field, since none exists in the real
   backend contract), and a new "Status / Risk" section in the Player Drawer showing any
   currently-active real override for the viewed player plus a compact submit form (event
   type, date, source(s), reason, and a conditional corrected-team field for
   `TEAM_CORRECTION`).

**Deliberately not built, per the directive's own sanctioned escape valve:** the Ballers PDF
import UI (file picker + preview + activate). Remains backend-ready exactly as before this
section (the facade method `import_udk_pdf_rankings` is real, tested, and callable) -- no new
HTTP route or client method was added for it either, since a route with zero real consumer
would be untested surface area, not "backend-ready" work. **Current/manual workflow**: the
owner's UDK PDF can be converted to the already-working CSV lane (`Import UDK CSV` control,
already live in Cheat Sheets), or the facade method can be invoked directly via a short Python
script (the same pattern this session's own Section 6 candidate-artifact build already used),
matching the project's existing offline-build-script precedent for governance-adjacent imports.

## Deviation from the directive's literal field list, disclosed

The directive asked for a status form with "player, event type, date, source, optional end
date." The real backend contract (`add_verified_status_override`,
`current_player_status_overrides_service.py`) has no end-date field -- confirmed by direct
inspection of the dataclass and validation function. This is the same real, disclosed gap
already recorded in `docs/codex/NWR_STATUS_RISK_INTAKE_PATH_V1_20260908.md` ("a richer taxonomy
was assumed in earlier planning but never actually built"). Per the directive's own instruction
not to invent new event kinds/fields, the shipped form uses exactly the real, existing fields
(player fixed to the drawer's own player, event type, date, reason, source(s), conditional
corrected-team) and omits the fabricated end-date field rather than faking one.

## Verification

- `desktop`: `npx tsc -b apps/dynasty/tsconfig.json apps/redraft/tsconfig.json` clean.
- `desktop`: `npm run test` (vitest) -- 142/142 passed (no regression; no new frontend unit
  test added this pass, since the new UI is a thin, directly-observable form/button with no
  behavior worth unit-testing beyond what typecheck already enforces -- covered instead by the
  real HTTP-route tests below).
- Python: 2 new tests in `tests/test_desktop_http_api.py`
  (`test_redraft_udk_rollback_route_accepts_a_position`,
  `test_status_overrides_routes_list_and_submit`) plus the full existing
  `tests/test_desktop_http_api.py` (40/40), `tests/test_status_override_intake_facade.py`, and
  `tests/test_udk_pdf_and_rollback_facade.py` suites -- all passed (48/48 combined).
- `tests/test_desktop_application_api.py`: unchanged 5/46 pre-existing baseline failures (see
  the repo's own baseline-failures memory), 41 passed -- no new failure introduced.
- Both real draft board files and the real owner `current.csv` re-verified byte-identical by
  hash before commit.

## Status

Section 8: **DONE, bounded.** UDK rollback and status/risk intake (read + write) are now real,
live, owner-reachable UI. Ballers PDF import UI is explicitly, honestly left backend-ready with
a documented current workaround, per the directive's own escape valve -- not force-built without
the missing Tauri file-dialog infrastructure this product does not yet have.
