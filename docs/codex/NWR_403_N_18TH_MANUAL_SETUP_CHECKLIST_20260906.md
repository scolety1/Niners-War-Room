# 403 N 18th and friends — MANUAL SETUP CHECKLIST

Real league (ESPN ID `1009373442`, draft 2026-09-07 19:00 EDT / 17:00 America/Denver). Settings could not be retrieved programmatically (private ESPN league, no accessible credentials) — fill these in from `fantasy.espn.com/football/league/settings?leagueId=1009373442`, then profile creation takes under 2 minutes using the app's existing manual setup (no new tooling needed).

```
TEAM COUNT:      ____
SCORING:         [ ] Standard   [ ] Half-PPR   [ ] PPR   [ ] Custom (describe: ______)
QB:              ____
RB:              ____
WR:              ____
TE:              ____
FLEX:            ____
SUPERFLEX/OP:    ____
K:               ____ (0 if none)
DST:             ____ (0 if none)
BENCH:           ____
IR:              ____   -- NOTE: NWR's roster schema has no IR slot concept at all (confirmed,
                            not just unused) -- this doesn't block draft-time use (nothing is
                            ever drafted directly to IR), but a full IR count won't be
                            reflected in the app if you want that documented.
ROUNDS:          ____
SNAKE/LINEAR:    [ ] Snake   [ ] Other (NWR only supports snake or auction profiles; "linear"
                                        isn't a distinct concept here -- flag if this league is
                                        genuinely non-snake)
DRAFT SLOT:      ____ (if ESPN has assigned one yet)
```

## How to enter this once you have the values (existing app flow, not new)

1. Launch the app (same launcher as always).
2. Create a profile from the closest built-in preset (e.g. "12-team PPR" or "10-team Standard") — this takes one click and gives you a real, valid starting profile.
3. Edit it with the exact real values above via the profile-edit screen (the same "Edit League" flow already used for KHA/Fantasy Gamers) — team count, scoring, every roster slot, bench, rounds, draft slot.
4. If K and/or DST are non-zero: also enable **Practical Mode** on the same edit screen (a real gap found and fixed today — this toggle now works for any manually-configured league, not just Sleeper imports).
5. Save. That's the real, live "403 N 18th and friends" profile — separate from KHA, Fantasy Gamers, and today's temporary QA profile; nothing about creating it touches any other league's data.

No ESPN importer was built and none is needed for this — the manual path above is the same real, existing mechanism used for every other league in this install.
