# External Research

- [Joe Bryant's public VBD principles](https://www.footballguys.com/article/bryant_vbd?article=bryant_vbd)
  establish projection-to-league-scoring followed by position-relative baselines, and explicitly
  note that team count, starters, rounds, and FLEX change the baseline.
- [PFF's VBD retrospective](https://www.pff.com/news/fantasy-a-value-based-drafting-retrospective-of-2011-part-1)
  describes replacement as league-specific rather than raw points alone.
- [Sleeper's public API contract](https://docs.sleeper.com/) exposes league scoring settings and
  roster positions as separate fields, supporting the profile contract without importing ranks.
- [nflfastR's public scoring aggregation source](https://github.com/nflverse/nflfastR/blob/master/R/aggregate_game_stats.R)
  demonstrates reproducible standard and PPR scoring components from public stats.
- [ffopportunity](https://github.com/ffverse/ffopportunity) documents public expected-fantasy-point
  opportunity models. NWR cites the concept but does not import its model or results.
- [nflreadr's public data interfaces](https://github.com/nflverse/nflreadr/blob/main/R/data.R)
  document public player stats, IDs, rankings, and expected-opportunity datasets. Proprietary
  rankings are not ground truth here.

Method decision: use deterministic league scoring plus simulated lineup/bench demand and visible
uncertainty. ADP remains optional context only. Auction conversion is deferred until a governed
budget/value contract is validated.
