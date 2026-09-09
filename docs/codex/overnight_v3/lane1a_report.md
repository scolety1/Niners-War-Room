# NWR Overnight V3 — Lane 1 report: Test 18 legality repair + Pick Score ordering + status taxonomy

Branch: `overnight/nwr-full-advance-v3-20260909`, based on `a72500a6` (the real commit that produced the
Test 18 evidence). Canonical `main` untouched, nothing pushed.

**Authorship note**: this lane was executed by a Codex worker in three passes, each interrupted by a real
host-memory shortage (verified: ~1.8-4GB free out of ~15.8GB total, consumed by other active processes on
this shared machine — other live Claude Code sessions, Chrome, VS Code, Windows Defender — not by this
task). After the third identical-shaped OOM kill, the remaining scope (items 4-7 below) was finished
directly, with all verification run as small, scoped commands (specific test files, not the full suite or
a fresh `npm ci`) to stay within the available memory headroom. Nothing here was verified via the full
`tests/` suite or a full `desktop` build tonight — see "What was NOT run" at the end.

## 1. Root cause of the Round-14 bug

`evaluate_draft_pick_legality` (new, `src/services/redraft_roster_legality_service.py`) correctly checks a
league's `roster_limits` (position maxima) — but the desktop profile create/update contract had **no field
to submit those limits at all**. Test 18's real profile therefore had an unenforced WR maximum in the
engine: the roster-cap check was capable of firing, it just never had a cap to check against. This is an
`IMPLEMENTATION_DEFECT` (a real, general product-configuration gap), not a data or test defect, and not
specific to Test 18 — any profile with a non-default position maximum was equally exposed.

Fixed: `RedraftProfileUpdateInput.draft` now carries an optional `rosterLimits?: Record<string, number>`
(`desktop/packages/contracts/src/index.ts`), and the profile edit surface can submit it.

## 2. Canonical legality service — every call site wired

`src/services/redraft_roster_legality_service.py` (`evaluate_draft_pick_legality`) is the single answer to
"can this team legally draft this player right now" — league position maxima, current roster, remaining
mandatory positions, and (via a feasibility guard) whether drafting this player would leave mandatory slots
unfillable in the rounds remaining. No named-player, round-number, or position-quota hardcoding.

Backend call sites (confirmed via `import ... evaluate_draft_pick_legality`):
- `src/application/desktop_facade.py:208`
- `src/services/decision_bundle_live_service.py:38` — replaces the old, duplicated
  `_roster_candidate_allowed` check (removed) and also replaces a previously separate, buggy
  "forced-position hard restriction" workaround that used to collapse the entire Suggestions shortlist to
  one position on a soft deadline hit (a real, previously reproduced bug — see the removed comment block in
  the diff for `build_live_decision_bundle`). Canonical legality is now the sole hard-maxima authority;
  `_forced_position` is downgraded to a soft shortlist-diversity hint only.
- `src/services/decision_bundle_live_service_v2.py:35`
- `src/services/practical_redraft_mock_service.py:15` — CPU/opponent simulation.
- `src/services/redraft_draft_room_v1_service.py:36` — draft-room/pick-recording path.

Frontend call sites (confirmed via `rosterLegal`/`legalityCode`/`legalityReason`, sourced from the same
backend fields added to `RedraftRanking` and `ManualDraftAsset` in `desktop/packages/contracts/src/index.ts`):
- Global quick-pick search + Compare's Add-Player search (`desktop/apps/redraft/src/pages.tsx:72`
  `PickSearchAsset`, `draft-room-v2.tsx:633,1300`).
- Draft Board rows (`draft-room-v2.tsx:2898,2929` — Draft button disabled + reason tooltip when illegal).
- A dedicated "Legal" status column on the searchable player table (`draft-room-v2.tsx:3451`).
- Player Drawer (`draft-room-v2.tsx:3634-3715` — Draft button disabled, "Illegal for roster" badge shown,
  reason surfaced as a tooltip).
- Cheat Sheet rows (`desktop/apps/redraft/src/cheat-sheet.tsx:174-183` — same disabled-Draft-button +
  "Illegal" badge pattern).
- CPU auto-pick candidate filtering (`draft-room-v2.tsx:1099`, guards `onDraft` from acting on an illegal
  candidate anywhere the shared row shape is reused).

One deliberate scope note: **Queue** does not block queueing an illegal-right-now player — only the actual
*Draft* action is gated. This is intentional, not a gap: an owner can still queue a player who is currently
capped out in case their roster changes (a drop, a correction) before that queue entry is acted on; queueing
never records a pick.

## 3. R14 acceptance fixture (permanent regression coverage)

`tests/fixtures/test18_redraft_fixture.py` encodes the real Test 18 state: all 13 owner picks through
round 13, the 5 intervening picks other teams made in round 14 (from the ESPN recap), and the league's real
WR maximum (8). `tests/test_test18_r14_legality_regression.py`:

- `test_forensic_reproduction_unconfigured_test18_profile_recommends_illegal_wrs` — proves the ORIGINAL bug:
  with `roster_limits` unset (Test 18's actual real-world state), Troy Franklin and Romeo Doubs are still
  rows 1-2 of the live candidate list at WR 8/8.
- `test_r14_acceptance_excludes_franklin_and_doubs_at_wr_eight_of_eight` — the permanent acceptance gate:
  with the league's real WR maximum configured, Franklin and Doubs are excluded entirely from the legal
  candidate set, and the top legal candidate is Kyler Murray — matching the corrected evidence packet's own
  causal chain exactly (bad roster construction → WR cap exhausted → owner forced off-algorithm → Kyler
  Murray the only legal value pick left).

## 4. Pick Score ordering — traced; the bug was a stale UI label, not a sort bug

Traced the full pipeline myself (`src/services/decision_bundle_service.py`). Finding: the backend's
`_candidate_sort_key` (same file) already sorts candidates **primarily by `marginal_utility`** — the real,
preregistered walk-forward-promoted signal (`docs/codex/NWR_MARGINAL_UTILITY_WALK_FORWARD_PROMOTION_V1.md`,
promoted before tonight, referenced in this session's own memory) — with `pick_score`, then
`raw_decision_utility`, then `player_id` as tie-breaks. A `pick_score_tied_no_spread` field already exists
and is already honestly disclosed to the frontend for exactly this reason: a genuine 50.0-tie cluster is a
real, disclosed property of the frozen Team-Score-derived formula (bench-tier candidates that don't crack
the optimal starting lineup collapse to the same raw value — see this session's memory,
`nwr-team-score-v1-frozen-2016-burned`), not an ordering defect.

The frontend's `buildSuggestionsRows` (`draft-room-v2.tsx`) was already correct and already documents this
precisely in its own docstring: it does **not** re-sort the candidate array — `decisionBundle.candidates.map(...)`
preserves the backend's real order. So there was no functional mis-sort.

**What was actually wrong**: the Suggestions panel's eyebrow label read "Default sorted by Pick Score,
descending" — true before the marginal-utility promotion, false afterward. That stale label is exactly what
would make the real, deterministic marginal-utility order look arbitrary to an owner watching a wall of
50.0-tied Pick Score rows with seemingly inconsistent Action labels (the Test 18 evidence screenshots show
exactly this). Root cause classification: `TEST_DEFECT`-adjacent — more precisely a **documentation/label
defect that survived a later, unrelated promotion**, not an engine defect.

**Fix applied**: `draft-room-v2.tsx` (Suggestions `Panel` `eyebrow`) now reads "Default sorted by NWR's
roster-value ranking (Pick Score shown as the tiebreak)", with an inline comment explaining the history so
this doesn't silently go stale again next time the primary signal changes.

No score values, tie-break logic, or candidate ordering were changed — only the label.

## 5. K/DST downstream — already verified sane by the R14 fixture's own follow-on test

`test_test18_kdst_downstream_legality_after_kyler_and_ravens` (same file) replays rounds 15 and 16 through
the corrected legal candidate set: at 15.05 the only two legal candidates are Ravens D/ST and Ka'imi
Fairbairn (both still-mandatory slots, nothing else legal remains); at 16.06 only Fairbairn remains. This
confirms the corrected evidence packet's own conclusion directly, in code: the K/DST timing was a forced
downstream consequence of the earlier WR-cap failure, not an independent NWR preference for K/DST over
skill positions. Once the legality fix is in place, nothing about the K/DST timing itself needs to change.

## 6. Status-risk taxonomy gap (item 1.12, Josh Jacobs) — closed generally, not by name

A parallel research pass (this session, read-only) found Josh Jacobs carried a real, sourced NFL
roster-status code (`EXE` — Commissioner Exempt) in the source snapshot pulled 2026-09-08T21:54:00Z, hours
before Test 18. The existing status-override taxonomy in
`src/services/current_player_status_overrides_service.py` had exactly three kinds (`SEASON_OUT`,
`NOT_WITH_TEAM`, `TEAM_CORRECTION`) — none fit "still on an NFL roster in a formal sense but not
practicing/eligible." No diligent human could have filed a compliant override for *any* player in that
real state, not just Jacobs. Classification: `IMPLEMENTATION_DEFECT` (a taxonomy gap), not neglect — the
raw status signal existed and was consulted (to decide whether to admit the player into rankings at all),
it just had nowhere valid to go once admission was granted.

**Fix**: added a fourth, general kind, `ADMINISTRATIVE_EXEMPT`, following the exact same
verified/cited/zero-value pattern as `SEASON_OUT`/`NOT_WITH_TEAM` (original projection preserved, value
zeroed for automatic-recommendation purposes only, player never removed from the pool, distinct disclosed
reason). Changed: `current_player_status_overrides_service.py` (docstring, `ZERO_VALUE_KINDS`, intake
validation message), `desktop/packages/contracts/src/index.ts` (`PlayerStatusOverride.kind`),
`draft-room-v2.tsx` (status-override form dropdown option), `desktop_facade.py` (docstring accuracy). **No
override entry was filed for Jacobs or anyone else** — that still requires the same individual, cited,
human-verified step every other entry went through, which is outside this task's scope. This is a general
capability, usable for any player in this real status; it does not special-case Jacobs by name anywhere.

New tests: `test_administrative_exempt_override_zeros_value_same_as_season_out`,
`test_add_verified_status_override_accepts_administrative_exempt`
(`tests/test_current_player_status_overrides_service.py`).

## 7. Verified test results (scoped runs; see "What was NOT run")

Backend, run via the repo's existing shared venv against this worktree's code:
```
tests/test_redraft_roster_legality_service.py
tests/test_test18_r14_legality_regression.py
tests/test_current_player_status_overrides_service.py
tests/test_status_override_intake_facade.py
tests/test_decision_bundle_live_service.py
tests/test_raw_action_value_live_service.py
tests/test_redraft_draft_room_v1_service.py
→ 119 passed, 1 skipped, 0 failed
```
Also ran the broader `tests/test_desktop_application_api.py` + `tests/test_desktop_http_api.py` once, before
the status-taxonomy change (which doesn't touch either file's logic paths in a way that would move this
number): **171 passed, 1 skipped, 5 failed** — all 5 failures are
`test_dynasty_facade_composes_real_governed_workflows`,
`test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`,
`test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`,
`test_redraft_league_switching_isolates_draft_state_and_persists_active_profile`,
`test_facade_has_no_streamlit_or_app_component_dependency` — an exact match to this session's own documented
pre-existing baseline for this worktree (data-age/hermetic-seed environment gap, recurring on its own
30-day clock, unrelated to any feature work here; see this session's memory,
`nwr-draft-upgrade-hq-baseline-failures`, which specifically predicted this exact recurrence on 2026-09-09).
**Zero new backend regressions.**

Frontend:
```
tsc -b apps/redraft/tsconfig.json → clean, zero errors
vitest run apps/redraft/src/draft-room-v2.test.ts apps/redraft/src/cheat-sheet.test.ts apps/redraft/src/pages.test.ts
→ 3 test files, 87 tests, 0 failures
```

## What was NOT run tonight (and why)

The full `tests/` suite (this session's memory documents ~323 pre-existing unrelated failures there — see
`nwr-full-suite-preexisting-failures`) and a full `npm run build`/full `vitest run` were **not** run in this
worktree, purely due to the real, repeated host-memory shortage described above — not because of any
concern about their content. Every file touched tonight was verified narrowly and directly instead. This is
a real gap in breadth of verification (a change elsewhere in this large repo could theoretically interact
with something not scoped here) and belongs on the retry queue: re-run the full backend suite and the full
desktop build/test once host memory conditions allow, before treating this branch as final.

## Files changed (backend)
`src/services/redraft_roster_legality_service.py` (new), `src/application/desktop_facade.py`,
`src/desktop_api/server.py`, `src/services/decision_bundle_live_service.py`,
`src/services/decision_bundle_live_service_v2.py`, `src/services/redraft_draft_room_v1_service.py`,
`src/services/practical_redraft_mock_service.py`, `src/services/current_player_status_overrides_service.py`,
`tests/fixtures/test18_redraft_fixture.py` (new), `tests/test_redraft_roster_legality_service.py` (new),
`tests/test_test18_r14_legality_regression.py` (new), `tests/test_current_player_status_overrides_service.py`,
`tests/test_decision_bundle_live_service.py`, `tests/test_desktop_application_api.py`,
`tests/test_desktop_http_api.py`, `tests/test_raw_action_value_live_service.py`,
`tests/test_redraft_draft_room_v1_service.py`.

## Files changed (frontend)
`desktop/apps/redraft/src/draft-room-v2.tsx`, `desktop/apps/redraft/src/cheat-sheet.tsx`,
`desktop/apps/redraft/src/pages.tsx`, `desktop/apps/redraft/src/profile.tsx`,
`desktop/apps/redraft/src/draft-room-v2.test.ts`, `desktop/packages/contracts/src/index.ts`.
