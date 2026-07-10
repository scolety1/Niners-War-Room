# PFR RB Broken Tackle Blockers and Caveats

- The source starts in 2018, so it does not support full 2013-2025 historical formula coverage.
- The join uses normalized player name plus source feature season because the Formula Data Mart uses GSIS-style `player_id` while the PFR source uses `pfr_id`.
- Multi-team PFR rows were handled by preferring `2TM` total rows; this avoids duplicate player-season sidecar keys.
- `pfr_rush_brk_tkl__per_attempt` is diagnostic only.
- Values are RB-only and review-only.
- PFR is not production-approved.
- Broad PFR, PFR QB passing, PFF Elusive Rating, and `nwr_elusive_proxy_review_only` remain blocked.
- Any future formula candidate must compare against PYF, rushing volume, prior touches, and multi-year production.
