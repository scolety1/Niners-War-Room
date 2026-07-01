# Candidate Formula Recommendation Packet

Verdict: `NO_TUNING_READY_CANDIDATE`

Best validation candidate by aggregate MAE: `prior_ppg_times_games_sqrt`.

Why it is not tuning-ready:

- Validation lift did not convert into full holdout stability.
- Holdout Top-N and/or Spearman did not beat the frozen `v1_baseline`.
- Red-zone incremental value was not established.
- Core Usage Dataset V1 still lacks admitted N to N+1 target overlap.

Future human review may inspect `prior_ppg_times_games_sqrt` as a conservative point-error hypothesis, but it must not be wired into NWR formulas, rankings, hidden sort, recommendations, app behavior, source truth, or runtime logic.
