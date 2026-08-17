# Data Flow Architecture

## Shared league state

`Sleeper league + scoring + rosters + drafts + transactions → SleeperReadAdapter → hashed snapshots → LeagueWorkspace / LeagueAvailability`

Sleeper owns platform facts. NWR owns identity projection, local caching and decisions. No platform writes.

## Redraft draft recommendation

`Redraft projection snapshot → scoring engine → NWR rank/value`

`ADP snapshot → expected pick/dispersion`

`draft events → availability + team rosters + current/next pick`

`NWR value + ADP timing + roster need + position tier/run → recommendation evidence`

Rank authority and timing remain separate. CPU events sample ADP/history, not NWR rank. Optional model text receives a bounded read-only evidence packet.

## Weekly lineup / waiver / streamer

`Sleeper roster + legal slots + weekly projection snapshot → legal lineup optimizer`

`Sleeper unrostered pool + optimizer + ROS/weekly evidence → add/drop marginal value`

`waiver pool + position-specific consensus/schedule evidence → QB/TE/K/DST streamer view`

Missing/stale sources suppress unsupported recommendations. The owner executes changes.

## Dynasty trade

`Finished V1 + Rookie Review + Outcome V3 + Unified Research + Market + roster/picks → Trade Decision Assistant → accept/counter/reject evidence`

Trade Finder searches candidate counterparties/packages but calls the same assistant. It does not create a new score.
