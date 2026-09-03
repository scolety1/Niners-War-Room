# Catch-up mode — contract (section 5)

Not implemented this wave. Per section 5's own instruction ("If full
catch-up UI is too broad: deliver a safe prototype + contract. Do not
delay rapid capture/event-ledger readiness for cosmetic catch-up work"),
this wave prioritized the two Saturday-critical items (rapid capture,
event ledger) that catch-up mode's own flow actually depends on — see
below. This is the contract for the next pass.

## Why catch-up mode builds on, not alongside, this wave's work

Catch-up mode's core mechanic — "map several pasted names sequentially to
the correct pick slots" — is exactly the FILL GAP operation from the event
ledger (`fill_gap_pick`, shipped this wave), applied N times with an
identity-resolution and confirmation step in front of it. It also needs
`globalPickSearchRows` (shipped this wave) as its per-name resolver. There
was nothing to safely build catch-up mode ON before this wave.

## Replay fixture: the 35 uncaptured KHA tail picks

`sample_data/kha_real_draft_2026/RECONCILIATION_LEDGER.csv`,
classification `NO_LIVE_RECORD` — the 35 real picks (rounds 10-12) after
the live capture stopped. This is the exact real-world shape catch-up
mode exists for: the operator fell behind, live capture ended, and the
tail needs to be entered from the real recap in one batch rather than
one-by-one.

Verified today, read-only: all 35 rows have a non-empty
`recap_player_name`, correctly identified in `official_recap_192picks_clean.csv`
(the replay-truth source). No additional identity work is needed to build
the catch-up fixture once the feature exists — this data is already the
right shape (`overall_pick, round, pick_in_round, team_slot, team_name,
player_name, nfl_team, position`).

## Contract for the next pass

**Input**: multi-line paste, one player name per line (platform copy/paste
formats vary — ESPN/Sleeper/Yahoo recap exports differ in whitespace and
whether team/position are inline; the parser must tolerate at least plain
names, one per line, and should not assume a specific platform's format
without testing against a real export from that platform).

**Resolution**: each pasted name resolves through the same
`globalPickSearchRows`-style matching used for rapid capture (name
substring against the ranked + manual asset pool), mapped **sequentially**
to the current draft position's next N unresolved/upcoming slots — not
by asking the operator to specify a pick number per name.

**Preview, not silent commit**: every resolution shows the matched player
before anything is written. An ambiguous match (multiple candidates, or a
name below some confidence threshold) blocks that line from auto-applying
— matches section 15's identity-registry rule ("AI may propose candidate
matches. AI cannot silently admit ambiguous identity") applied to a
different surface.

**Apply**: on confirmation, each resolved line becomes one `fill_gap_pick`
(or, if the target slot already exists in the live-synced tail with a
wrong player, one `replace_pick`) call — reusing the event ledger
verbatim, not a parallel write path.

**Acceptance test** (once implemented): paste the 35 real KHA tail player
names in real recap order, confirm all 35 resolve unambiguously against
the real KHA player universe + manual K/DST/unmodeled-skill-player pool
(all three now shipped), apply, and confirm the resulting board matches
`official_recap_192picks_clean.csv` picks 158-192 exactly.

## What is NOT deferred

The dependencies (global search, event ledger, K/DST + missing-player
representation) are done and tested. What remains is UI/paste-parsing
work and the ambiguity-blocking logic — bounded, but real work, correctly
sequenced behind what this wave actually shipped rather than attempted in
parallel with it.
