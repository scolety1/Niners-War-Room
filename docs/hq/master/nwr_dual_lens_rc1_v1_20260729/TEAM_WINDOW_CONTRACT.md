# Team Window contract

Team Window is not a learned formula and does not claim a universally optimal
preset. Each admitted source score is clipped to its current scored-universe
5th/95th percentiles and min-max normalized to 0–100. Team Window score is:

`win_now_weight × normalized_win_now + dynasty_weight × normalized_dynasty`

The initial presets are Contending 75/25, Balanced 50/50, and Rebuilding 25/75.
Both source scores, source ranks, normalized scores, and weights must remain
visible. If either lens is missing, Team Window is missing; there is no
Finished V1 or other hidden fallback. Raw ranks are never blended.
