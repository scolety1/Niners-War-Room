# Status/Risk Live Intake Path — V1 (2026-09-08)

**Context:** NWR class-time autonomous hardening directive, Section 6.

## Real gap found

The backend intake contract `add_verified_status_override()`
(`src/services/current_player_status_overrides_service.py`) already exists, already enforces
real validation (kind in the real disclosed set, at least one cited source, real ISO dates, no
silently-stacked duplicate player), and its READ side
(`load_status_overrides`/`apply_status_overrides_to_ranking`) was already wired live into both
real ranking call sites (`_redraft_ranking_for_profile`, `redraft_bootstrap`, verified directly
in `desktop_facade.py`). But the WRITE side was **not reachable from any facade method, HTTP
route, or GUI control** -- the only way to add a new real, verified event was to hand-edit the
committed JSON config file directly, bypassing the contract's own validation entirely.

## Real taxonomy note (honest correction of the directive's own assumption)

The directive's Section 6 text names a 9-value event taxonomy (`OUT_FOR_SEASON`,
`SHORT_TERM_INJURY`, `PUP_NFI`, `ADMINISTRATIVE_EXEMPT`, `SUSPENSION`, `RELEASED`,
`FREE_AGENT`, `TRADE`, `ROLE_CHANGE`). The real, existing, already-tested backend contract
uses a different, simpler, real taxonomy: `SEASON_OUT`, `NOT_WITH_TEAM`, `TEAM_CORRECTION`
(module docstring explains why: distinct real reasons matter for disclosure, but the
downstream recommendation effect only needs two buckets -- "zero automatic value" and "team
field correction"). Per this whole project's own no-fabrication discipline, this fix wires
the **real** contract as-is rather than inventing the richer, never-actually-built taxonomy
the directive assumed existed.

## Fix

Added two methods to `DesktopBackendFacade` (`src/application/desktop_facade.py`):

- `list_player_status_overrides()` -- thin read-only listing of the currently-active
  overrides (previously only visible by opening the JSON file by hand).
- `submit_player_status_override(...)` -- wraps `add_verified_status_override` as-is (no new
  validation invented, no existing validation loosened); a rejected submission
  (`StatusOverrideIntakeError`) surfaces as `FacadeError("STATUS_OVERRIDE_REJECTED", ..., status=422)`
  with the real, specific reason, not a generic failure. Gated to `redraft` mode, consistent
  with the module's own explicit design intent (a current-status correction must never reach
  historical/dynasty evaluation). Once written, the very next live ranking build picks it up
  automatically -- no separate wiring needed, since the read side already runs at both real
  call sites.

## What remains (honestly disclosed, not built this pass)

A compact owner-facing UI surface (a small form or player-action control, per the directive's
own "not another giant control panel" instruction) to call `submit_player_status_override`
from the Draft Room. Given the scope of the remaining directive sections and this session's
time budget, this pass delivers the real, tested, functional **backend ingestion path** --
the actual missing piece that made every owner-facing surface impossible -- and stops there.
The next concrete step is a minimal frontend form (player id/name, kind dropdown constrained
to the 3 real kinds, reason, source URL, effective date) wired to this facade method.

## Tests

5 new tests in `tests/test_status_override_intake_facade.py` (uses an isolated fixture config
file under `tmp_path`, never the real committed overrides file): real submission + listing,
uncited-event rejection, duplicate-player rejection, mode-gating, and listing against a
pre-seeded real fixture entry. All pass. Full regression across the 3 related test files (22
tests) clean; `test_desktop_application_api.py` shows the exact known 5 pre-existing failures,
unchanged (per `nwr-draft-upgrade-hq-baseline-failures` project memory).

## Status

Section 6: **DONE (backend intake path)**, frontend surface flagged as the remaining step.
