# NWR_SATURDAY_PURE_CANDIDATE_V1

Local candidate only. No push/merge/deploy performed or proposed by this
document.

## Exact identity

- Worktree: `C:\Users\codex-agent\orca\workspaces\Niners-War-Room\draft-upgrade-hq`
- Branch: `work/nwr-draft-upgrade-hq-v1-20260903`
- HEAD: `4ae5ce6b16a95ea3d8bf0c7cced6de65ff65972f`
- Tree: `bf6d5e1dd49278e20027f74b0876fc3a76f88622`
- Rollback point (prior wave's accepted foundation): `fb393025e46b74a596ffcfcda6b67bbe07171cbc`
- Commits this wave: 7 (`5da27306` rapid capture through `4ae5ce6b` docs), all
  on top of `fb393025`, working tree clean.
- Player-universe SHA (as installed): `e483caaedc236140bcdfeccdd759bf8726a4b231bbaf3e9fdc461873d3921c25`
  (`current.manifest.json`, 608 rows) — **`valid_until: 2026-09-03`, i.e.
  today.** This snapshot needs a fresh install before a real Saturday
  draft regardless of anything in this wave; flagging now so it isn't
  discovered live.
- Algorithm identity: `REDRAFT_AUTHORITY_LABEL = "REDRAFT V1 - REVIEW"`,
  `MODEL_FAMILY = "R2_FLEX_AWARE_REPLACEMENT"` (`redraft_engine_v1_service.py`,
  unchanged this wave).

## What's in this candidate (independently verified safe draft-operational changes only)

1. Checkpoint root fix (prior wave, carried forward).
2. Global pick search + keyboard-first RECORD NEXT PICK box (rapid
   capture) — tested against all 23 real KHA SEARCH_FAILURE picks.
3. K/DST representable via search (13/14 historical picks; the 14th is a
   confirmed separate stale-roster-data issue, not a search gap) +
   missing-skill-player manual assets (5/5 historical picks, plus 9 more
   pre-emptively).
4. Position-max legality in Suggestions (mechanical filter, no ranking
   formula change).
5. Event-sourced pick corrections: REPLACE PICK / CLEAR PICK / FILL GAP /
   UNDO, tested against the full acceptance matrix (various distances,
   collisions, reopen persistence).

None of these touch `generate_rankings()`, `calculate_replacement_levels()`,
or any other live scoring formula. All are additive/mechanical or fix a
concrete, evidenced bug.

## What's in this branch but explicitly NOT decision authority

`src/services/shadow_numeric_authorities_service.py` and its tests
(Team Score / Championship Equity / Pick Score / look-ahead prototype).
Independently verified this wave (grep-based review) to be imported
nowhere outside its own tests — not reachable from `desktop_facade.py` or
any frontend page. Safe to ship in the candidate as inert code; must not
be exposed to the owner as advice without an explicit, separate decision
to do so and a SHADOW/RESEARCH label on every surfaced value.

## Regression status

Backend: 104 passed / 5 pre-existing-and-unrelated failures (verified
identical across every run this session, in `test_desktop_application_api.py`,
touching no file this wave or the prior one modified — missing hermetic
bootstrap data and an unrelated import-name assertion).
Frontend: `tsc -b` clean, `vitest run` 20/20, `vite build` (redraft app)
clean.

## Rollback

`git reset --hard fb393025e46b74a596ffcfcda6b67bbe07171cbc` returns to the
prior wave's accepted state if anything in this candidate needs to be
backed out before Saturday. Not performed — this document only records
the rollback point.
