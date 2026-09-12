# NWR Release Gate Checklist

Built by Worker 3 (P0-3, `upgrade/nwr-post-ui-product-v1-20260912`, 2026-09-12) as
the first repeatable, real (non-mocked) release gate for the NWR desktop app.
Previous freezes (`NWR_UI_EXPANSION_FREEZE_V1.md` and predecessors) validated
the frontend with mocked `window.fetch` and Vite dev builds only -- never a
real backend process, never a packaged app. This gate closes that gap.

Two things are checked, and reported **separately** -- never blended into one
verdict:

1. **PACKAGING GATE** -- can a full native Tauri bundle actually be built in
   this environment?
2. **BRIDGE SMOKE** -- does a real production frontend build, talking to the
   real Python backend process over real loopback HTTP, actually work,
   end to end, for every major surface?

A "packaging blocked, bridge passes" result is a valid, common, and useful
outcome -- do not read it as a blanket failure.

## Quick start

```powershell
# Fast default: isolated local profile, no native build attempt (~30-60s)
powershell -File desktop/scripts/nwr_release_gate_smoke.ps1

# Full pass: real read-only Sleeper league + a native build attempt
powershell -File desktop/scripts/nwr_release_gate_smoke.ps1 `
    -AttemptNativeBuild `
    -SleeperLeagueId 1312983576827920384 -SleeperUsername scolety
```

The script:

- Never merges/pushes/deploys anything.
- Never bypasses `check:resources` (the owner-privacy/resource-allowlist
  guard) to force a native build through.
- Never touches a real, live/active Sleeper draft, roster, or lineup -- the
  one Sleeper call it can make (`POST /api/v1/redraft/sleeper/import`) is
  documented in the codebase itself as `"Explicit, read-only Sleeper import
  into the isolated Redraft store."` (`src/application/desktop_facade.py`),
  and the script independently verifies this with a real before/after
  byte-comparison of `league`/`rosters`/`users` fetched directly from
  `api.sleeper.app`.
- Writes a full JSON report to
  `local_exports/release_gate/<UTC timestamp>/release_gate_report.json`
  (gitignored -- inspect locally, do not expect it to appear in `git status`).
- Cleans up every process it started (backend + vite preview), including a
  port-based fallback kill for Windows process-tree survivors.

## What "PASS" looks like

### Packaging gate

- `check:resources` exit code 0 -> native `tauri:build` is attempted (only
  with `-AttemptNativeBuild`) and its own exit code is the real verdict.
- `cargo check` (run unconditionally, bundles nothing) exit code 0 confirms
  the Rust/Tauri toolchain itself is sound, independent of the resource gate.

**Known state as of 2026-09-12 (pre-existing, not caused by this shift):**
`check:resources` fails for the `redraft` app. The bundled
`NWR_DATA_GOVERNANCE.json` governance receipt legitimately records the real
owner's name in its own audit trail (`"approved_by"`/`"renewed_by"`), which
the same script's owner-privacy guard forbids in any bundled resource.
Confirmed pre-existing via `git diff --stat <shift-start-head> HEAD --
desktop/scripts desktop/apps/redraft/src-tauri/tauri.windows.conf.json`
(empty before Worker 3's own path-correctness fix, described below). This is
a real product/governance decision for the owner to make (e.g. a redacted
bundled copy vs. keeping the receipt out of the distributable bundle
entirely), not something this pass fixes.

Worker 3 did fix a related, separate bug while investigating this: the
Windows resource-bundle map (`desktop/apps/redraft/src-tauri/
tauri.windows.conf.json`) and its allowlist mirror
(`desktop/scripts/check-resource-allowlists.mjs`) still pointed at the OLD
608-row bundled seed (`docs/hq/model/
nwr_redraft_2026_rookie_projection_candidate_v1_20260809/...`) after
Worker 2's P0-2 migrated the runtime facade to the new Freeze V7 seed
(`docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/...`,
564 rows). A native build attempted before this fix would have bundled
stale, already-expired-approval seed data. Both files now correctly point
at Freeze V7 -- this did NOT unblock `check:resources` (the owner-marker
conflict above is separate and pre-existing on either seed generation), but
it fixes a real, disclosed staleness bug in the packaging manifest itself.

### Bridge smoke

All of the following should return HTTP 200 for a Sleeper-imported profile
with an active roster (real example used: "Fantasy Gamers", Sleeper league
`1312983576827920384`):

`bootstrap` (cold + warm), `sleeper_import`, `league_workspace_context`,
`my_roster`, `opponent_rosters`, `data_health`, `player_availability_status`,
`weekly_lineup`, `waivers`, `free_agents`, `trade_finder`.

For a **fresh local-preset profile with no roster/draft yet**, `my_roster`,
`opponent_rosters`, `weekly_lineup`, `waivers`, `free_agents`, and
`trade_finder` correctly return HTTP 409 (Conflict) -- this is the app being
honest that those surfaces need a real roster, not a bug.

**Known real bug (2026-09-12, disclosed, not fixed by this pass):**
`POST /api/v1/redraft/weekly-home-actions` (feeds the "Weekly Home" surface's
"NWR Actions" panel) returns HTTP 500 for a Sleeper-imported profile with an
active roster. Reproduced directly (not just via HTTP):

```
File "desktop_facade.py", line 4181, in redraft_weekly_home_actions
    for position, action_rows in kdst_payload.get("positions", {}).items():
AttributeError: 'list' object has no attribute 'items'
```

`DesktopBackendFacade.redraft_weekly_home_actions` still assumes
`redraft_kdst_streamer(...).data["positions"]` is a dict keyed by position;
it is actually a list of decision-envelope rows (confirmed live: `type(...)
is list`). The frontend degrades honestly (`"Command center unavailable --
The local NWR service did not respond in time."`), it does not fabricate
data -- but the panel never populates. Not reproduced against a fresh
local-preset profile with no roster (the STREAMER aggregation section is
likely only reached once a roster exists). Backend logic is out of scope for
this pass (verification/tooling only); flagged for the next worker with
backend budget.

## Manual UI checklist (the script covers the backend only)

The script proves the real HTTP bridge and real business logic end to end,
but does not drive a browser. For a full release, also confirm these
visually (Chrome DevTools MCP, or the packaged app once native build is
unblocked) against the vite-preview URL the script's `-KeepRunning` flag
leaves open (`http://127.0.0.1:1422` for redraft):

- [ ] League chooser (`#/leagues`) lists every profile and opens the active
      one via "Open workspace".
- [ ] Home / Weekly Home renders (note: "NWR Actions" panel will show the
      known degraded state above until the backend bug is fixed).
- [ ] Lineup / Start-Sit renders a real projected lineup (or an honest
      "unavailable for week N" message pre-season).
- [ ] Improve Team (Targets / Add-Drop / FAAB / Streamers / All Free Agents)
      renders real, ranked candidates.
- [ ] Trades (Analyze / Find Trades) renders; "Browse my roster" /
      "Browse opponent rosters" links resolve.
- [ ] Players (Rankings / Tiers / Compare / Market) shows the real governed
      board (564 rows as of the Freeze V7 seed) and the Player Drawer opens
      with real per-player detail on click.
- [ ] League (Overview / My Roster / Teams / Scoring / Settings / Sync) and
      Data Health render real, current freshness state per source.
- [ ] Draft Room shows a real not-yet-started board
      (`configured: false`, empty `picks`/`drafted`) -- **do not click
      "Start Draft"** during a release-gate pass against a real league.
- [ ] Full page reload (restart-equivalent) re-bootstraps and restores the
      active league.
- [ ] A cold deep link directly to a sub-route (e.g. `#/league/<id>/trades`)
      lands on that exact surface, not a default redirect.
- [ ] League switch (create/select a second profile, switch back) updates
      every surface's active-league context correctly.

All of the above were performed manually once, live, by Worker 3 against the
real Fantasy Gamers Sleeper league on 2026-09-12 -- see
`docs/codex/post_ui_v1/NWR_POST_UI_WORKDAY_LEDGER.md` for the full narrative
and exact findings.

## Safety notes for whoever re-runs this

- Only pass `-SleeperLeagueId`/`-SleeperUsername` for a league you are
  authorized to read (ask the owner if unsure which league is safe). Omit
  both to stay fully local/isolated.
- The script never calls any Sleeper write endpoint -- there isn't one:
  `src/services/sleeper_import_service.py`'s `SleeperHttpClient` only
  defines `get_json()` via `urllib.request.urlopen()` (GET, no `data=`
  payload). Verify this yourself with
  `grep -rniE "requests\.(post|put|patch|delete)|urlopen.*data=" src/ | grep -i sleeper`
  before trusting any future change to that file.
- The redraft data root defaults to `<repo_root>/local_exports/redraft_v1`
  (isolated per-worktree) unless `NWR_REDRAFT_HOME` is set -- it never
  touches the owner's real `%LOCALAPPDATA%\com.ninerswarroom.redraft`
  install.
