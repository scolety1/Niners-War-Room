# Flaim Integration Cycle (2026-09-19) — LEDGER

Worker 1. Branch `upgrade/nwr-prospective-outcomes-v1-20260914`, worktree
`C:\NWR\prospective-outcomes-v1`. This is a NEW ledger for this cycle — do
not conflate with `docs/codex/connection_update_20260919/LEDGER.md` (the
prior, separate pass this cycle builds directly on) or
`docs/codex/sunday_readiness_20260920/LEDGER.md` (the earlier cycle whose
guard patterns this pass reuses conventions from).

### Methodology key

- **INSPECTED CODE** — read directly from the repo, this pass.
- **ACTUAL TEST RESULT** — a real command/test run, this pass.
- **LIVE OBSERVATION** — a real running process/filesystem read, observed
  directly this pass.
- **INFERENCE** — a conclusion drawn from the above, explicitly labeled.

---

## 1. State verification — LIVE OBSERVATION

- **Starting HEAD:** `ca080a2eec737647a226f078f2347eafd21d245f`, branch
  `upgrade/nwr-prospective-outcomes-v1-20260914`, `git status` clean at
  pass start (matched the dispatch brief exactly; no newer work to
  preserve).
- **Redraft dev instance:** RUNNING. Backend `python scripts/
  run_nwr_desktop_api.py --host 127.0.0.1 --port 18742 --mode redraft
  --repo-root C:/NWR/prospective-outcomes-v1` (pid `44000`), preview
  `vite preview --port 1422 --strictPort` (pid `11932`, `C:\Program
  Files\nodejs\node.exe`) — both real, listening
  (`netstat -ano` confirmed `127.0.0.1:1422`/`127.0.0.1:18742` LISTENING
  under those exact pids), and both match the pids the prior
  `connection_update_20260919` cycle's Worker 2/3 left running with their
  missing-projection fix already live — i.e. these are the SAME processes,
  not restarted, machine did not reboot in the interim.
- **Dynasty dev instance:** RUNNING — **newly confirmed this pass** (not
  documented by the prior cycle, which only touched Redraft). Backend
  `python scripts/run_nwr_desktop_api.py --host 127.0.0.1 --port 18741
  --mode dynasty --repo-root C:/NWR/prospective-outcomes-v1` (pid
  `46892`), preview `vite preview --port 1421 --strictPort` (pid `37692`,
  bare `node`) — both real, listening
  (`127.0.0.1:1421`/`127.0.0.1:18741` LISTENING).
- **Data roots — INSPECTED CODE + LIVE OBSERVATION.** Neither process's
  command line sets `NWR_REDRAFT_HOME`/`NWR_DYNASTY_HOME` explicitly; both
  were launched with `--repo-root C:/NWR/prospective-outcomes-v1` only.
  `redraft_engine_v1_service.py` (`redraft_store_root`) reads
  `NWR_REDRAFT_HOME` from the environment and falls back to
  `<repo_root>/local_exports/redraft_v1` when unset — confirmed this is
  the real, live data root for the running Redraft instance:
  `C:\NWR\prospective-outcomes-v1\local_exports\redraft_v1\`. Dynasty
  follows the analogous documented convention
  (`local_exports/dynasty_v1/`, per `desktop_facade.py`'s own docstring
  at the dynasty-root constructor argument). **This worktree's
  `local_exports/` is fully isolated from the owner's real AppData
  install** (`AppData\Local\com.ninerswarroom.redraft`, per this saga's
  own prior finding) — nothing this pass did touches the real install.
- **Backup — LIVE OBSERVATION.** Before any of this pass's own work,
  created a fresh, full, timestamped copy of the entire `local_exports/`
  tree: `local_exports.backup-20260919T233737Z/` (UTC timestamp,
  following this saga's established convention — two prior backups from
  earlier workers, `local_exports.backup-20260917T224444Z/` and
  `local_exports.backup-20260918T230905Z/`, were left untouched
  alongside it). This pass did not, in the end, write anything into
  `local_exports/` itself (see section 4 — no profile/receipt/snapshot
  file was created or modified), but the backup was taken first as
  required regardless.
- **Pre-existing untracked files left untouched, not created by this
  pass:** `.worker2_backend.log`, `.worker2_backend.log.err`,
  `.worker2_preview.log`, `.worker2_preview.log.err` (log files for the
  still-running pids 44000/11932 above), and both prior
  `local_exports.backup-*` directories.

## 2. Reopened governance restriction — narrow, owner-authorized

Read the July packet in full this pass
(`docs/hq/master/fantasy_plugin_research_canonicalization_closeout_v1_20260711/`
— `SANITIZED_EXECUTIVE_VERDICT.md`, `MANUAL_PLUGIN_OPERATING_GUIDE.md`,
`PROVIDER_CHANGE_REENTRY_GATE.md`, `EXTERNAL_SIGNAL_GOVERNANCE_BOUNDARY.md`,
`SOURCE_USE_RIGHTS_AND_PRIVACY_BOUNDARY.md`,
`PLUGIN_CAPABILITY_SUMMARY.csv`, `INTEGRATION_DECISION_MATRIX.csv` — not
paraphrased from memory or from the prior `connection_update_20260919`
ledger's own summary of it, though that summary was independently
consistent with the full read).

**New packet, additive only, does not edit/delete the July packet:**
`docs/hq/master/flaim_scoped_capability_reauthorization_v1_20260919/`
— three files:

- `OWNER_AUTHORIZATION_AND_JULY_FINDINGS_RECORD.md` — the owner's
  authorization quoted verbatim (dated 2026-09-19, relayed via this
  cycle's dispatch brief), the July findings it responds to preserved
  accurately (with direct quotes/close paraphrase from the July packet's
  own text, not reconstructed from memory), and an explicit accounting of
  which July capability rows *don't* name identity/roster/lineup as
  unsafe (the textual basis for the owner's "should not automatically
  prevent... identity, roster, or lineup" clause).
- `CAPABILITY_AUTHORIZATION_MAP.md` — the operative table: every
  capability NWR could plausibly source from Flaim, its exact July
  finding, its status (`ALLOWED` / `ALLOWED once individually verified` /
  `CONSTRAINED` / `CONSTRAINED — NOT ENABLED` / `EXPLICITLY UNCHANGED —
  still BLOCKED`), and its binding constraint. Also maps this
  authorization to the specific one of July's eight named reentry
  triggers it satisfies (`PROVIDER_CHANGE_REENTRY_GATE.md`'s "Written
  persistent-use, display, and retention permission" — the owner's own
  dated grant, a rights-side trigger, distinct from the other seven
  provider-side triggers, none of which are claimed).
- `MANIFEST.json` — lightweight index with SHA-256 hashes of the two
  content files, following the July packet's own manifest convention.

**Verdict recorded:**
`SCOPED_READ_ONLY_CAPABILITY_AUTHORIZATION_GRANTED_FOR_IDENTITY_ROSTER_LINEUP_SETTINGS_ONLY`.

**What is now ALLOWED (individually, per capability, not a blanket
unblock):** verified league identity; owner/team roster-slot mapping
(carrying forward July's own "not independently verified against
same-time native truth" caveat); roster membership snapshot (must carry a
retrieval timestamp); lineup/slot eligibility (once verified per-league,
with an explicit completeness flag); scoring settings (with an explicit
`COMPLETE`/`PARTIAL`/`UNKNOWN` flag, same discipline the existing Sleeper
receipt already uses via `scoring_reconciliation`/`unsupported_scoring`).

**What remains CONSTRAINED or explicitly unchanged/BLOCKED:** standings
(display-only-with-disclosure at most, never authoritative — and this
pass's snapshot schema, section 3, does not even model a standings field
yet, deliberately going further than "constrained display" to "not yet
representable at all"); transaction direction / waiver-claim / add-drop /
trade-side reconstruction (constrained AND not enabled — doubly blocked,
by July's own finding and independently by this project's standing "no
provider writes" rule); available-player pool (must carry an explicit
`BOUNDED`/`NONE` flag, never `COMPLETE` — the new snapshot loader
(section 3) actively *rejects* a `COMPLETE` claim as a data error, not
merely discourages it); Flaim's/FantasyBot's own computed judgments
(rankings, trade opinions, a disagreement panel) — **entirely untouched**
by this authorization, still governed by `EXTERNAL_SIGNAL_GOVERNANCE_
BOUNDARY.md` at 0% production influence, since this authorization concerns
only raw factual data conduits, never plugin-computed analysis.

**Confirmed:** the July packet's 17 files were not modified (`git status`
after this pass shows zero changes anywhere under
`fantasy_plugin_research_canonicalization_closeout_v1_20260711/`).

## 3. Capability-check architecture — DESIGNED AND BUILT (pure, not yet wired into any live guard)

### 3a. What exists today (INSPECTED CODE, unchanged this pass)

The Sunday Readiness cycle's Worker 3 finding was independently
re-confirmed by re-reading the code this pass, not re-tested live (no
code changed that would affect it): `data.activeProfile?.provider ===
"sleeper"` gates Weekly Home/Start-Sit/Improve Team/Trades/etc. across
23 call sites in `desktop/apps/redraft/src/` (`in-season.tsx` ×7,
`improve-team.tsx`, `pages.tsx` ×4, `trades.tsx` ×2, `league.tsx` ×2,
`league-context.ts` ×2, `attention-center.ts` ×2,
`adp-providers.tsx`, `profile.tsx`). The backend's parallel pattern:
`desktop_facade.py`'s `redraft_kdst_streamer` (~line 2794) reads
`self.redraft_root / "sleeper_imports" / f"{selected.profile_id}.json"`
directly and raises `KDST_STREAMER_SLEEPER_CONTEXT_REQUIRED` (HTTP 409,
"The active profile has no valid Sleeper import receipt...") on any
`OSError`/`ValueError`/`KeyError`/`TypeError` from that lookup.

### 3b. New pure backend module — `src/services/league_capability_service.py`

Provider-agnostic `LeagueCapabilities` frozen dataclass:
`has_verified_identity: bool`, `has_roster_data: bool`,
`has_lineup_eligibility: bool`,
`has_scoring_settings: "COMPLETE"|"PARTIAL"|"UNKNOWN"`,
`has_available_player_pool: "COMPLETE"|"BOUNDED"|"NONE"`,
`has_standings: "DISCLOSED_NON_AUTHORITATIVE"|"NONE"`,
`transaction_direction: "NOT_ENABLED"` (literal type with only one legal
value today, kept explicit rather than omitted so the constraint is
visible to a future reviewer, not silently absent), `retrieved_at_utc: str
| None`, `provider_as_of_utc: str | None` (kept genuinely distinct —
never backfilled from the other), `disclosures: tuple[str, ...]`.

Three real functions, all pure (no I/O):

- `capabilities_from_sleeper_receipt(receipt)` — derives real capability
  flags from this codebase's EXISTING, ALREADY-WRITTEN Sleeper import
  receipt shape (`league`, `owner`, `roster_snapshot`, `roster_positions`,
  `scoring_reconciliation`, `unsupported_scoring` — read directly from a
  real receipt file, `local_exports/redraft_v1/sleeper_imports/
  6687d2b3aa21450ea0fc9e1792d461ff.json`, to confirm the shape this pass
  modeled against is the real one, not an assumed one). Deliberately
  reports `has_available_player_pool="NONE"` even for a real, live-capable
  Sleeper league, with an explicit code comment explaining why: that
  receipt file never carries the free-agent pool (it's fetched live,
  per-request, by a separate code path this function doesn't model) — an
  honest gap documented rather than silently wrong.
- `capabilities_from_espn_flaim_snapshot(snapshot)` — derives capability
  flags from the new `EspnFlaimSnapshot` type (section 3c). Always
  reports `has_standings="NONE"` — not merely constrained-if-present, but
  never modeled as present at all, since the schema itself carries no
  standings field.
- `capabilities_for_profile(*, sleeper_receipt=None, espn_snapshot=None)`
  — the intended future call-site entry point. **Verified by an explicit
  test (`test_dispatch_does_not_inspect_a_provider_string_at_all`) that
  its signature has no `provider` parameter at all** — capabilities are
  computed strictly from real receipt/snapshot presence. Returns
  `NO_CAPABILITIES` (everything False/NONE/UNKNOWN) when neither is
  available, never a guess.

### 3c. New pure backend module — `src/services/espn_flaim_snapshot_service.py`

This is also the snapshot-import DESIGN the task asked for (see section 4
below — same module covers both).

- `EspnFlaimSnapshot` frozen dataclass: `profile_id`,
  `provider_league_id`, `league_name`, `season`, `team_count`,
  `owner_team_id`, `owner_team_name`, `roster: tuple[EspnRosterPlayer,
  ...]` (each with `provider_player_id`, `player_name`, `position`,
  `team`, `slot: "STARTER"|"BENCH"|"RESERVE"`), `scoring_settings:
  tuple[EspnScoringSetting, ...]` (each with `espn_setting_name`,
  `value`, `nwr_setting: str | None`), `scoring_completeness`,
  `available_player_pool: tuple[EspnAvailablePlayer, ...]`,
  `available_player_pool_coverage`,
  `available_player_pool_bound_description: str | None`,
  `retrieved_at_utc: str` (required, never defaulted),
  `provider_as_of_utc: str | None` (explicitly optional — most Flaim
  records won't have one, per July's own finding), `source` (defaults to
  a clear provenance string).
- `parse_espn_flaim_snapshot(raw: dict) -> EspnFlaimSnapshot` — validates
  every required field with a specific `EspnFlaimSnapshotError` message
  per missing/malformed field (never silently defaults an identity or
  retrieval field). **Actively rejects
  `available_player_pool_coverage == "COMPLETE"`** as a hard error, not
  merely a discouraged state — directly enforcing the July audit's own
  free-agent finding at the parser level, with a pointer to
  `CAPABILITY_AUTHORIZATION_MAP.md` in the error message itself.
- `espn_flaim_snapshot_path(redraft_root, profile_id)` — storage
  location convention: `local_exports/redraft_v1/espn_flaim_snapshots/
  <profile_id>.json`, an exact mirror of the existing, real
  `local_exports/redraft_v1/sleeper_imports/<profile_id>.json`
  convention (confirmed by directly inspecting that existing directory
  this pass).
- `load_espn_flaim_snapshot(redraft_root, profile_id)` — returns `None`
  (not an error) when no snapshot file exists yet, which is the correct,
  honest state for every real profile as of this pass; raises
  `EspnFlaimSnapshotError` for a present-but-malformed file rather than
  silently treating corruption as absence.

### 3d. Frontend contract type — `desktop/packages/contracts/src/index.ts`

Added `LeagueCapabilities` interface (plus its literal-union field types)
mirroring the Python dataclass field-for-field, with a header comment
explicitly stating this is design-only: no backend endpoint serializes it
yet, no frontend call site reads it yet. `npm run typecheck`
(`desktop/`) confirmed clean after the addition — **ACTUAL TEST RESULT.**

### 3e. What was deliberately NOT wired this pass, and why

None of the 23 frontend `provider === "sleeper"` call sites, and neither
of the backend's Sleeper-receipt-shaped 409 guards
(`redraft_kdst_streamer` and the analogous checks elsewhere in
`desktop_facade.py`), were modified. Reasons, explicit:

1. **No real ESPN/Flaim snapshot exists yet** to test an end-to-end
   rewiring against (Flaim OAuth is still pending in the coordinating
   session — see section 5). Rewiring a live guard without a real second
   data shape to verify against would be untested by construction.
2. **The dispatch brief's own explicit instruction**: "avoid a broad
   framework rewrite... this should feel like a natural evolution of the
   existing guard." Touching 23+ frontend call sites and multiple backend
   409 branches in one pass, for a capability model that has no real
   consumer yet, would be exactly the broad rewrite the brief warned
   against.
3. The pure backend module (3b/3c) and the contract type (3d) are
   deliberately built so that a LATER worker — once a real ESPN snapshot
   exists — can wire ONE call site at a time (e.g. start with the K/DST
   streamer's 409, the exact guard the brief cited as the anti-pattern
   exemplar) using `capabilities_for_profile(...)` instead of a provider
   string check, verify it against real data, and repeat — "these tools
   light up naturally without another guard-hunting pass," per the brief,
   because the guard-hunting (finding all 23+ sites, documented above in
   3a) is already done.

## 4. Snapshot-import design — SCHEMA + LOADER BUILT, REFRESH PROCESS DOCUMENTED AS A SKELETON SCRIPT (not functional — no Flaim access)

- **Schema:** `EspnFlaimSnapshot` (section 3c) — captures league identity,
  owner/team mapping, roster with starter/bench/reserve classification,
  scoring settings with an explicit completeness flag, available-player
  pool with an explicit coverage flag (`COMPLETE` structurally
  unreachable — the loader rejects it), and a retrieval timestamp kept
  genuinely distinct from any provider-published as-of timestamp.
- **Storage location:** `local_exports/redraft_v1/espn_flaim_snapshots/
  <profile_id>.json`, mirroring the existing, real Sleeper receipt
  convention exactly (verified against the real directory this pass, not
  assumed).
- **Refresh process:** `scripts/refresh_espn_flaim_snapshot.py` — a real
  file, with a real argparse CLI (`--profile-id`, `--redraft-root`), that
  documents the full intended real process in its module docstring (which
  Flaim MCP tools to call per the July audit's own inventory —
  `get_league_info`/`get_roster`/`get_free_agents`, explicitly NOT
  `get_standings`/`get_transactions`, which remain constrained/not
  enabled — how to transform the result into the documented schema, how
  to validate it, and exactly where to write it) and then **raises
  `NotImplementedError` with a specific, actionable message** rather than
  doing nothing silently or fabricating output. **ACTUAL TEST RESULT:**
  ran `python scripts/refresh_espn_flaim_snapshot.py --profile-id
  test123` this pass — raised the documented `NotImplementedError`
  cleanly, printing the intended output path
  (`local_exports\redraft_v1\espn_flaim_snapshots\test123.json`) and a
  pointer back to this ledger, confirming the skeleton is real code that
  runs (not a syntax error) and fails loudly and specifically rather than
  silently.

## 5. Explicitly NOT done this pass (per hard task boundaries)

- No Flaim MCP tool was called by this worker (this worker has no Flaim
  access — only the coordinating session does, pending the owner's OAuth
  login, per the dispatch brief).
- No real ESPN/Flaim snapshot file was created anywhere — the synthetic
  fixtures used in the new tests (section 6) are explicitly labeled
  `SYNTHETIC` in their own test data and are never written to
  `local_exports/`.
- No existing profile (KHA `fb1c49402c7644a99120197d41344bbb.json`, 403 N
  18th `4b4a990faf124ce7a5d612537ba5943b.json`, or any other) was created
  or modified — confirmed via `git status`/directory listing showing zero
  changes under `local_exports/redraft_v1/profiles/`.
- The owner's specific league-ID reconciliation table was not touched —
  correctly left for a later worker with real, verified Flaim data.
- `marginal_roster_utility_v2`, governed Redraft valuation, and Dynasty's
  `governed_asset_registry_service.py` valuation computation were not
  touched (confirmed: this pass's only `src/services/` additions are the
  two new files listed in section 7, both new, neither imported by nor
  importing from any governed-valuation module).

## 6. Tests — ACTUAL TEST RESULT

New, all passing:

- `tests/test_league_capability_service.py` — 16 tests: dispatcher
  behavior (no-receipt/no-snapshot returns `NO_CAPABILITIES`, no
  `provider` parameter exists at all), Sleeper-receipt-derived
  capabilities (real-shaped receipt → identity/roster/lineup/complete
  scoring; unsupported scoring → `PARTIAL`; missing `league` block → no
  identity; empty roster → no roster/lineup; no scoring block at all →
  `UNKNOWN`; dispatch prefers Sleeper receipt when both present),
  ESPN/Flaim-snapshot-derived capabilities (round-trip of the documented
  schema; partial scoring + no-standings; bounded pool surfaces its bound
  description; empty roster → no roster/lineup; dispatch to ESPN snapshot
  when no Sleeper receipt).
- `tests/test_espn_flaim_snapshot_service.py` — 4 tests: storage-path
  convention matches the Sleeper mirror exactly; `load_...` returns
  `None` (not an error) when no file exists yet; a real synthetic
  snapshot file round-trips through the loader; a malformed file raises a
  specific `EspnFlaimSnapshotError`, not a silent default.

Combined: **20/20 passed**
(`python -m pytest tests/test_league_capability_service.py
tests/test_espn_flaim_snapshot_service.py -q`).

Regression, run this pass:

- Targeted related suites (`test_league_capability_service.py`,
  `test_espn_flaim_snapshot_service.py`,
  `test_weekly_lineup_optimizer_service.py`,
  `test_start_sit_confidence_missing_projection.py`,
  `test_waiver_engine_service.py`,
  `test_desktop_facade_architecture_wiring.py`): **90 passed, 0 failed.**
- `tests/test_desktop_application_api.py`: **4 failed, 46 passed** —
  confirmed BYTE-IDENTICAL to the prior `connection_update_20260919`
  cycle's own stash-verified pre-existing baseline
  (`test_dynasty_facade_composes_real_governed_workflows`,
  `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`,
  `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`,
  `test_facade_has_no_streamlit_or_app_component_dependency`). No new
  failure introduced.
- `npx vitest run` (`desktop/`): **30 files, 503 tests, all passed** —
  identical count to the prior cycle's own documented baseline, confirming
  the new `LeagueCapabilities` TS type addition broke nothing.
- `npm run typecheck` (`desktop/`): clean, zero errors.
- `docs/codex/prospective_outcomes_v1/multi_league_scale_v1/
  frontend_bench_results.json` was regenerated by the `vitest run` above
  (same documented timing-noise pattern the prior cycle already
  identified) — reverted with `git checkout --`, not part of this
  pass's commit.

## FILES CHANGED THIS PASS

- `docs/hq/master/flaim_scoped_capability_reauthorization_v1_20260919/`
  (new directory) — `OWNER_AUTHORIZATION_AND_JULY_FINDINGS_RECORD.md`,
  `CAPABILITY_AUTHORIZATION_MAP.md`, `MANIFEST.json`.
- `src/services/league_capability_service.py` (new) — capability model +
  dispatcher, pure, not yet called by any facade/endpoint.
- `src/services/espn_flaim_snapshot_service.py` (new) — ESPN/Flaim
  snapshot schema + validating loader + storage-path convention, pure,
  not yet called by any facade/endpoint.
- `scripts/refresh_espn_flaim_snapshot.py` (new) — documented,
  non-functional refresh-process skeleton (raises `NotImplementedError`
  with a specific message; real implementation requires real Flaim
  access this worker does not have).
- `desktop/packages/contracts/src/index.ts` — added `LeagueCapabilities`
  type + supporting literal-union types (design-only, additive, not
  consumed anywhere yet).
- `tests/test_league_capability_service.py` (new) — 16 tests.
- `tests/test_espn_flaim_snapshot_service.py` (new) — 4 tests.
- `docs/codex/flaim_integration_20260919/LEDGER.md` (new — this file).

**Not committed, deliberately untracked (backup/scratch, following this
saga's established convention):**
`local_exports.backup-20260919T233737Z/` (this pass's pre-work backup).

**Not touched:** `local_exports/` itself (no profile, receipt, or
snapshot file was created/modified anywhere under it), the July packet's
17 files, `.worker2_*` logs, the other two `local_exports.backup-*`
directories.

## OPEN ISSUES FOR NEXT WORKER

1. **Flaim OAuth status is the hard gate for everything downstream of
   this pass.** This worker has no way to check whether the coordinating
   session's `claude mcp login flaim` has completed — that state lives
   outside this worktree/process entirely. Check with the coordinating
   session directly before assuming a real Flaim fetch is possible.
2. **Once a real Flaim connection exists**, the next real step is: pick
   one real ESPN profile (KHA or 403 N 18th), call Flaim's
   `get_league_info`/`get_roster` (NOT `get_standings`/
   `get_transactions`, per `CAPABILITY_AUTHORIZATION_MAP.md`), transform
   the real response into the `EspnFlaimSnapshot` schema (section 3c),
   validate it with `parse_espn_flaim_snapshot`, and write it to
   `local_exports/redraft_v1/espn_flaim_snapshots/<profile_id>.json` —
   the exact process `scripts/refresh_espn_flaim_snapshot.py`'s docstring
   already documents. This should be done by whichever session actually
   holds live Flaim MCP access, not by spawning another access-less
   worker to re-attempt it.
3. **Do not set the owner's league-ID table into either existing ESPN
   profile's `provider_league_id`** without a real, verified fetch
   confirming the match — this pass correctly left both profiles
   untouched, matching the prior cycle's own KHA finding (genuinely
   `UNDETERMINED`, `1298250946` unverified against anything in this
   codebase) and 403 N 18th finding (the owner-supplied ID already
   matches the existing native-install receipt, but the profile JSON
   itself still has `provider_league_id: null`).
4. **Wiring the capability model into a live guard is the next
   architecture step, not done this pass.** Once a real snapshot exists
   for at least one profile, the lowest-risk first wire-up is the K/DST
   streamer's `redraft_kdst_streamer` 409 (`desktop_facade.py` ~line
   2794) — replace its direct `sleeper_imports/<id>.json` read-and-except
   with a call to `capabilities_for_profile(sleeper_receipt=...,
   espn_snapshot=load_espn_flaim_snapshot(self.redraft_root,
   selected.profile_id))`, checking `has_roster_data` (the actual
   capability that endpoint needs) instead of "did a Sleeper receipt
   parse". Verify against BOTH a real Sleeper profile (regression: must
   keep working exactly as before) and the new real ESPN snapshot before
   touching any other call site.
5. **Both dev process pairs (Redraft pid 44000/11932, Dynasty pid
   46892/37692) were left running, untouched, with none of this pass's
   backend changes requiring a restart** (nothing in
   `league_capability_service.py`/`espn_flaim_snapshot_service.py` is
   imported by any currently-executing request path yet). A future
   worker that DOES wire a live guard should verify whether these
   processes need a restart to pick up the change (Python's dev server
   here does not appear to auto-reload — confirm before assuming).
6. **Do not push.** Per this cycle's instructions, a later worker pushes
   once everything is verified. This pass's commit sits on top of
   `ca080a2e`.
