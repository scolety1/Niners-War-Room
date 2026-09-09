# NWR Overnight V3 — Lane 2 report: in-season buildout (non-blocked capabilities)

Branch: `overnight/lane2-inseason-buildout-20260909`, based on `a72500a6`. Canonical `main` untouched.

Per the prior capability-inventory archaeology, this lane built only the 4 items confirmed NOT blocked on a
missing data source (Start/Sit, Waivers-for-skill-positions, Trades, ROS, Matchups, SoS, Playoff Odds all
remain genuinely `DEPENDENCY_BLOCKED` on a governed weekly-projection model / live standings store that does
not exist anywhere in this codebase — left untouched, as instructed).

**Authorship note**: Codex implemented all 4 items (602 lines across 9 files) but was killed by the same
real host-memory shortage documented in the Lane 1 report before it could write tests or a report. The
implementation itself was coherent and complete; the remaining verification and test-writing was finished
directly, the same way as Lane 1.

## 1. Free Agents (general, not just K/DST)

`sleeper_free_agent_pool()` (`src/services/fantasypros_kdst_consensus_service.py`) generalizes the existing
`sleeper_rostered_player_ids()` primitive across all fantasy positions (previously hard-restricted to K/DST
only). Cross-matches against existing NWR rankings by identity when available; explicitly `UNRANKED` (never
fabricated) when not. New route `GET /api/v1/redraft/free-agents` → `desktop_facade.redraft_free_agents()`.
Frontend: `FreeAgentsPage` (`desktop/apps/redraft/src/pages.tsx`), route `/free-agents`.

## 2. Roster/League Sync (recurring, not one-shot)

`resync_sleeper_redraft_profile()` (`src/services/sleeper_redraft_owner_service.py`) re-pulls a Sleeper
league/roster and persists a fresh roster snapshot into the same receipt the one-shot import already used —
read-only against Sleeper (`writeBehavior: "NO_SLEEPER_WRITES"`), rejects non-Sleeper profiles by design
(no live resync source exists for ESPN/local profiles). New route
`POST /api/v1/redraft/profiles/{id}/sleeper-resync`. Frontend: a "Refresh from Sleeper" control on
`ProfilePage`, shown only for `provider === "sleeper"` profiles.

## 3. Opponent Rosters

`sleeper_opponent_rosters()` (same service file as free agents) exposes the per-team roster data the K/DST
streamer was already fetching live and discarding — no new data source. Excludes the owner's own roster,
resolves public team identity (team name → display name → username → `Roster {id}` fallback), reports
unresolved player IDs rather than silently dropping them. New route `GET /api/v1/redraft/opponent-rosters`.
Frontend: `OpponentRostersPage`, route `/opponent-rosters`.

## 4. Weekly League Home

`LeagueHomePage` (`pages.tsx`) surfaces what's real today (Data Health status, the K/DST streamer with a
week selector, the top of the new free-agent pool, links to the full Free Agents / Opponent Rosters views)
and explicitly labels Start/Sit, skill-position waivers, and Trades as "Coming soon — blocked on
[reason]" via `WEEKLY_HOME_BLOCKED_CAPABILITIES` — never a silent omission or a fabricated recommendation.
Registered as the new landing route (see integration note below for a real conflict this creates with
Lane 3's own routing change).

## A real bug found and fixed: mojibake in the new UI text

All new user-facing strings in `pages.tsx` and `profile.tsx` (middle dots, em dashes, an ellipsis — e.g.
"AVAILABLE · all fantasy positions") were corrupted to `Â·` / `â€”` / `â€¦` — a UTF-8-written/Latin-1-read
round-trip encoding bug, confirmed absent from the same file at the shared base commit (`a72500a6`), so
introduced by this lane's own edits, not pre-existing. Root cause classification: `IMPLEMENTATION_DEFECT`
(a real, user-visible display bug — every owner viewing these new pages would have seen garbled text).
Fixed with a precise, whole-file UTF-8 read/replace/write (not a lossy per-character shell filter), verified
byte-for-byte clean afterward (`grep -c` for the three known-bad sequences → 0 in both files) and confirmed
`tsc -b` and the existing frontend test suite still pass afterward.

## Verified test results (scoped)

Backend, run via the repo's shared venv against this worktree's code:
```
tests/test_fantasypros_kdst_consensus_service.py  (4 pre-existing + 6 new)
tests/test_sleeper_redraft_owner_service.py       (4 pre-existing + 3 new)
→ 17 passed, 0 failed
```
New tests added (none existed for this lane's functions before tonight):
`test_sleeper_free_agent_pool_excludes_rostered_inactive_and_incomplete_rows`,
`test_sleeper_free_agent_pool_attaches_real_ranking_by_identity_never_invents_one`,
`test_sleeper_free_agent_pool_rejects_malformed_players_payload`,
`test_sleeper_opponent_rosters_excludes_the_owner_and_resolves_public_identity`,
`test_sleeper_opponent_rosters_reports_unresolved_players_without_dropping_them`,
`test_sleeper_opponent_rosters_rejects_malformed_rosters_payload`,
`test_resync_refreshes_the_stored_roster_snapshot_without_any_sleeper_write`,
`test_resync_records_unresolved_players_without_dropping_them`,
`test_resync_rejects_a_non_sleeper_profile`.

Also ran `tests/test_desktop_application_api.py` + `tests/test_desktop_http_api.py`: **89 passed, 5 failed**
— the exact same 5 pre-existing baseline failures documented in the Lane 1 report (data-age/hermetic-seed
environment gap, unrelated to this lane). Zero new backend regressions.

Frontend: `tsc -b apps/redraft/tsconfig.json` clean (after fixing a stale-workspace-symlink issue in this
worktree's own `node_modules` — see below); `vitest run` on `pages.test.ts`, `adp-providers.test.ts`,
`bootstrap-guard.test.ts` → 3 files, 19 tests, 0 failures. No new component-render tests were added for the
3 new page components (`FreeAgentsPage`, `OpponentRostersPage`, `LeagueHomePage`) — this codebase's existing
test convention is unit-testing pure data-preparation functions (e.g. `buildSuggestionsRows`), not full
component rendering, and none of these 3 pages contain non-trivial pure logic beyond thin API-call wrapping
already covered indirectly by the backend service tests above.

**Environment note**: this worktree's `node_modules/@nwr/{contracts,api-client,...}` had been populated by
copying another worktree's `node_modules` wholesale (an earlier attempt to avoid a slow `npm ci` reinstall
under the same memory pressure documented in the Lane 1 report) — that copy dereferenced npm workspace
symlinks, silently shadowing this worktree's own package sources with a stale, unrelated worktree's version
and producing real but misleading "no exported member" TypeScript errors. Fixed by replacing the copied
directories with real symlinks back to this worktree's own `packages/*`/`apps/*`, then re-verified clean.
Flagging this because the same fix was independently needed and applied in the Lane 1 worktree.

## Deliberately NOT built (per the archaeology's own findings, unchanged)

Start/Sit, Weekly Lineup (live/weekly), Waiver Wire (skill positions), FAAB, Add/Drop, Trade Finder, Weekly
Projections, ROS Projections, Matchups, Strength of Schedule, Playoff Odds, live-standings Championship
Equity. Trade Analysis exists and is real, but only in the separate Dynasty app
(`/api/v1/dynasty/trades/evaluate`) — left untouched; wiring dynasty/keeper-window trade logic into weekly
Redraft trades is a real, separate design decision, not attempted tonight.

## Integration note for the overnight candidate branch

This lane's `RedraftApp.tsx` changes route `"/"` unconditionally to the new `/league-home`. Lane 3's own
`RedraftApp.tsx` changes route `"/"` to `/leagues` (the new league chooser) when no profile is active, and
to `/draft-room-v2` otherwise. These conflict and must be reconciled at integration time — the evident
correct merge is: no active profile → `/leagues` (Lane 3's chooser); active profile → `/league-home` (this
lane's weekly home), replacing Lane 3's `/draft-room-v2` default. Flagged here rather than resolved
unilaterally inside this isolated worktree, per the mission's own integration policy.
