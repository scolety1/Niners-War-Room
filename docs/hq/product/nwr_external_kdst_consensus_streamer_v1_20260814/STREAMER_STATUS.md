# K/DST Streamer status

The existing Desktop Redraft app now exposes **Weekly Tools → K/DST Streamer**. After the owner supplies an authorized key, it reads weekly FantasyPros K/DST ECR and the existing read-only Sleeper endpoints for league rosters and NFL players.

Availability is resolved only when normalized public name, position, and team all match; unmatched Sleeper IDs are disclosed. Each row is one of `START`, `HOLD`, `ROSTERED_ELSEWHERE`, `ADD`, or `ALTERNATIVE`; `ADD` is the best available ECR row, not an NWR score. No schedule, weather, betting, injury, or hidden weighting is used.

The streamer makes no Sleeper or FantasyPros write request. Weeks are intentionally distinct snapshots; they are not averaged.
