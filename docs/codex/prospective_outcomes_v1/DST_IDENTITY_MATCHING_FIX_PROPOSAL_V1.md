# DST identity-matching fix proposal (ready-to-execute, NOT applied this pass)

Status: **PROPOSAL ONLY**. Not executed by Worker 9 (this pass). Touching
`src/services/fantasypros_kdst_consensus_service.py` is outside Prospective
Outcomes V1's own stated hard-boundary discipline (this cycle's own files are
the outcome-evaluation layer, not the K/DST *recommendation* service) --
per the owner's explicit, repeated instruction, this cycle does not build a
challenger just because time is available, and does not touch a shared,
already-relied-upon recommendation service without explicit, separately
scoped authorization. This document exists so a FUTURE, explicitly-scoped
session can execute the fix in minutes rather than re-discovering it.

Originally found and documented (not fixed) by Worker 7 (Work Unit 17,
K/DST Prospective Benchmark). Independently re-confirmed live twice more
this pass (Worker 9): once via a direct backend re-read of the source, once
by reproducing the bug live in the real, running desktop app UI against the
real Fantasy Gamers Sleeper league (see LEDGER.md Worker 9 entry, Work Unit
21).

## 1. Exact root cause

File: `src/services/fantasypros_kdst_consensus_service.py`
Function: `sleeper_streamer_actions` (line ~131-182 as of this pass's HEAD).

```python
key = _identity(player.get("full_name") or player.get("search_full_name"), position, player.get("team"))
```

Sleeper's own `players/nfl` catalog gives **DST entries `first_name`/
`last_name` only** -- never `full_name` or `search_full_name`. For every
real Sleeper DST roster entry, both `player.get("full_name")` and
`player.get("search_full_name")` evaluate to `None`, so `_identity(None,
"DST", team)` runs with `name=None` -- `_identity`'s own body (line
~382-386) casefolds/strips `str(name or "")`, gets an empty
`normalized_name`, and its own guard (`if not normalized_name or ...: return
("", "", "")`) short-circuits to the literal degenerate key `("", "", "")`
-- confirmed by direct re-read of `_identity` this pass, not inferred.
`provider_ids.get(("", "", ""))` then returns `None` for every real DST
roster entry (no real FantasyPros row ever legitimately produces that same
degenerate key, since a DST's own `row.player_name` is always a real,
non-empty team name like `"Jacksonville Jaguars"`), so `provider_id is
None` and the entry falls to `unmatched.add(...)` every time.

**Effect**: every real DST roster entry falls through to
`unmatched.add(str(sleeper_id))` (line ~167) instead of
`rostered.add(provider_id)`. The `rostered`/`owner`/`starters` sets that
`sleeper_streamer_actions` returns to `streamer_actions(...,
rostered_provider_ids=rostered, ...)` therefore **never contain any real
DST's provider id** -- every DST in the FantasyPros consensus is reported
`rosterStatus: "AVAILABLE"`, including a DST that is genuinely, actively
rostered and started (own real roster or any opponent's). The
differentiating "is this actually available" filter -- the one real value
NWR's own K/DST surface adds on top of naive published consensus order --
silently never fires for DST. It fires correctly for K, because Sleeper's K
catalog entries DO carry `full_name`.

**Three sibling functions in the SAME file already carry the fix this one
lacks** (confirmed by direct comparison this pass, matching Worker 7's own
finding):

```python
# sleeper_free_agent_pool, line ~230-232:
name = str(raw.get("full_name") or raw.get("search_full_name") or "").strip()
if position == "DST" and not name and team:
    name = f"{team} D/ST"

# a second, identical block at line ~310-313 (the other free-agent-pool
# builder in this same file)
```

`sleeper_streamer_actions` is the ONLY one of the four Sleeper-identity
functions in this file that omits the `if position == "DST" and not name
and team: name = f"{team} D/ST"` fallback.

## 2. Live re-confirmation this pass (Worker 9)

- Direct source re-read: confirmed line-for-line identical to Worker 7's
  original finding; the gap has not been touched since.
- Live UI reproduction (new this pass, not done by Worker 7): in the real,
  running desktop app (production `vite build` + real Python backend, real
  Fantasy Gamers Sleeper league `1312983576827920384`), the Streamers tab
  of Improve Team, after a real "Refresh K/DST ECR" click, rendered:
  `ADD Jacksonville Jaguars (DST) ... THIS WEEK AVAILABLE`. Jacksonville was
  the real, actual DST starter that week for at least one real roster in
  this league (matching Worker 7's own week-1 finding) -- so a genuinely
  rostered/started DST is visibly, functionally mislabeled `AVAILABLE` live
  in the product UI, not just in an isolated backend script.

## 3. Exact fix (mirrors the two already-proven sibling blocks verbatim)

```python
def sleeper_streamer_actions(
    rows: tuple[ConsensusRow, ...],
    *,
    rosters: object,
    players: object,
    owner_user_id: str,
) -> tuple[tuple[dict[str, str | int | None], ...], tuple[str, ...]]:
    ...
    for sleeper_id in roster.get("players") or []:
        player = players.get(str(sleeper_id))
        if not isinstance(player, Mapping):
            continue
        position = _sleeper_position(player.get("position"))
        if position not in SUPPORTED_POSITIONS:
            continue
        team = str(player.get("team") or "").upper().strip()
        name = str(player.get("full_name") or player.get("search_full_name") or "").strip()
        if position == "DST" and not name and team:
            name = f"{team} D/ST"
        key = _identity(name, position, team)
        ...
```

Concretely: replace the single line

```python
key = _identity(player.get("full_name") or player.get("search_full_name"), position, player.get("team"))
```

with the four lines above (compute `team` first since it is now reused,
compute `name` with the same DST fallback `sleeper_free_agent_pool` already
uses, then build `key` from `name`/`position`/`team`). No change to
`_identity`'s own signature or the two already-correct sibling functions.
No change to `streamer_actions` (the pure ECR-ordering function this one
calls into) or to any FantasyPros-side code (`_parse_consensus`,
`ConsensusRow`, `provider_status`) -- the provider side already reports a
real, non-empty DST `player_name`; only the Sleeper-side identity key was
missing its fallback.

## 4. Exact test to add

New test in `tests/test_fantasypros_kdst_consensus_service.py`, mirroring
the file's own existing `test_sleeper_roster_filter_requires_exact_public_
identity_and_preserves_start_state` (K case) but for a DST roster entry that
carries only `first_name`/`last_name` (the real Sleeper shape, not a
convenience `full_name` a test author might otherwise be tempted to add):

```python
def test_sleeper_dst_roster_entries_with_no_full_name_still_resolve_as_rostered() -> None:
    payload = {"players": [
        {"player_id": 1, "player_name": "Jacksonville Jaguars", "player_position_id": "DST", "player_team_id": "JAX", "rank_ecr": 1, "tier": 1},
        {"player_id": 2, "player_name": "Los Angeles Chargers", "player_position_id": "DST", "player_team_id": "LAC", "rank_ecr": 2, "tier": 1},
    ]}
    rows = _parse_consensus(payload, season=2026, week=1, position="DST")
    actions, unmatched = sleeper_streamer_actions(
        rows,
        rosters=[{"owner_id": "owner", "players": ["s1"], "starters": ["s1"]}],
        # The real Sleeper shape for a DST catalog entry: first_name/
        # last_name only, NEVER full_name/search_full_name -- deliberately
        # omitting full_name here is the whole point of this test.
        players={"s1": {"first_name": "Jacksonville", "last_name": "Jaguars", "position": "DST", "team": "JAX"}},
        owner_user_id="owner",
    )
    assert not unmatched, "A real DST roster entry with no full_name must still resolve to a known provider id."
    by_ecr = {value["ecr"]: value["recommendation"] for value in actions}
    assert by_ecr[1] == "START"          # Jacksonville: owner's own real starter
    assert by_ecr[2] == "ROSTERED_ELSEWHERE"  # LA Chargers must NOT show AVAILABLE once genuinely fixed
```

This test FAILS on the current (unfixed) code (`unmatched` would contain
`"s1"`, and both DSTs would report `"ADD"`/`"AVAILABLE"` instead of
`START`/`ROSTERED_ELSEWHERE`) and PASSES once the 4-line fix above is
applied -- a real, live-verifiable regression proof, not just a description.

## 5. Blast radius / who is affected

- `sleeper_streamer_actions` has exactly ONE real call site:
  `desktop_facade.py`'s `redraft_kdst_streamer` (confirmed by grep this
  pass and by Worker 7's own original finding). Fixing it changes ONLY the
  DST arm of that one endpoint's `rosterStatus` field -- K is already
  correct and untouched by this fix (the `if position == "DST"` guard means
  the K code path takes the exact same route it already does today: `name =
  str(player.get("full_name") or player.get("search_full_name") or
  "").strip()` unchanged, then falls through with no DST-only fallback
  applied).
- No change to any ranking, projection, Team Score, decision-engine, or
  Prospective Outcomes evaluation code. This is a pure identity-matching
  correctness fix inside the K/DST recommendation surface's own roster-
  availability filter -- it does not touch this cycle's own hard boundary
  (`marginal_roster_utility_v2`, `LeagueSnapshot`, `LeagueWorkspaceContext`,
  `lifecycle_resolver`, `DecisionResultEnvelope`,
  `PlayerAvailabilityStatus`) at all.
- Once fixed, a future re-run of `kdst_prospective_benchmark_v1_service.py`
  (Worker 7's own scaffolding, already real and reusable) would for the
  first time measure the DST arm's TRUE differentiated recommendation
  (rather than a value that always equals naive top-ECR consensus by
  construction) -- worth doing as a follow-up once this fix lands, not
  before.

## 6. Why this pass does not apply it

Per the owner's own standing instruction (repeated in this pass's own
directive, Work Unit 24): do not build a challenger, and by extension do
not make even a narrow correctness fix to a shared recommendation service,
just because time is available and the fix is well-understood. This fix is
outside the file set Prospective Outcomes V1 has established as its own
across all 9 workers (every file this cycle created or modified is listed
in the final ledger entry) -- `fantasypros_kdst_consensus_service.py` is a
live, shared, already-relied-upon recommendation service, not an outcome-
evaluation file. A future session explicitly scoped to K/DST recommendation
quality (not outcome evaluation) is the right place to execute this -- the
fix, the test, and the blast-radius analysis above are handed off complete
so that session can move directly to implementation and review.
