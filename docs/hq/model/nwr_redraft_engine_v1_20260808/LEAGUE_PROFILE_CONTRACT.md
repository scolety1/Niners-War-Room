# League Profile Contract

Each versioned JSON profile contains identity (name, season, teams), starting roster (QB/RB/WR/TE,
FLEX, SUPERFLEX, K, DST, bench), scoring components, supported bonuses, TE premium, and draft
metadata (snake/auction, slot, rounds, keepers, roster limits, optional ADP flag, replacement
method). Built-in presets are templates only.

Profiles, the active-redraft pointer, projection snapshots, and profile draft boards live under
`NWR_REDRAFT_HOME` or ignored `local_exports/redraft_v1`. No dynasty settings or active-pack file
is read or written by profile operations. Projection installation additionally requires a
separately issued `NWR_DATA_GOVERNANCE` JSON receipt bound to the exact source SHA-256; the runtime
retains and revalidates both the receipt and install manifest.
