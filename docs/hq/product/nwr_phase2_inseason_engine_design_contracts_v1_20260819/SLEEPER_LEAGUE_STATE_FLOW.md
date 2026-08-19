# Sleeper league-state flow

`league ID → settings/scoring → users → rosters → starters/bench/IR/taxi → transactions → traded picks → rostered IDs → unrostered pool`.

The Redraft waiver layer joins the pool to weekly/ROS evidence and owner needs. The Dynasty stash layer joins it to existing dynasty authority, age/lifecycle and role signals. Sleeper remains read-only: no lineup, waiver, trade, or add/drop write operations.
